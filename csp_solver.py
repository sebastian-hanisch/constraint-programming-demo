"""Tiefensuche mit Constraint-Propagation an jedem Knoten - anders als
branch-bound-demo/bb_solver.py entspricht hier NICHT jede Suchbaum-Ebene fest einem
bestimmten Paket: Propagation kann Pakete "außer der Reihe" festlegen (z. B. wird ein
Paket, dessen Partner gerade aufgenommen wurde, sofort ausgeschlossen, egal an
welcher Position es in der Ratio-Reihenfolge steht). Jeder Verzweigungsschritt wählt
deshalb explizit das nächste NOCH UNENTSCHIEDENE Paket, statt stur der festen
Reihenfolge zu folgen.

Bewusst KEIN eigener "durch Kompatibilität unzulässig"-Knotenstatus: das wäre
naheliegend, aber bei dieser Suchreihenfolge strukturell unmöglich - sobald ein
Paket aufgenommen wird, schließt die Kompatibilitätsregel seinen Partner SOFORT aus
(siehe csp_propagation.py), bevor die Suche je versuchen könnte, beide gleichzeitig
zu wählen. Der Effekt der Regel zeigt sich stattdessen darin, dass jeder Knoten
zählt, wie viele Pakete SEINE EIGENE Propagation automatisch per Kompatibilität
ausgeschlossen hat (`Node.incompatibility_exclusions`) - kumuliert über den ganzen
Suchbaum eine ehrliche, tatsächlich beobachtbare Kennzahl für den Nutzen der Regel,
statt eines nie auslösenden Pruning-Grundes."""

from dataclasses import dataclass

from csp_constants import MAX_NODES_EXPLORED
from csp_propagation import propagate


def ratio_order(instance):
    return sorted(range(instance.n_items), key=lambda i: instance.values[i] / instance.weights[i], reverse=True)


@dataclass(frozen=True)
class Node:
    id: int
    parent_id: int
    depth: int  # Anzahl bislang entschiedener Pakete (nicht zwingend == Baumebene in Paket-Reihenfolge)
    item_index: int  # das EXPLIZIT verzweigte Paket, None für die Wurzel
    decision: bool  # True = aufgenommen, False = ausgelassen, None für die Wurzel
    weight: int
    value: int
    status: str  # root | branch | prune_bound | leaf_new_best | leaf_not_best
    detail: object  # zusätzliche Information zum Pruning-Grund (z. B. die erreichbare Summe)
    incompatibility_exclusions: tuple  # Pakete, die DIESER Knoten per Kompatibilität automatisch ausgeschlossen hat
    capacity_exclusions: tuple = ()  # Pakete, die DIESER Knoten per Kapazitäts-Propagation automatisch ausgeschlossen hat


@dataclass(frozen=True)
class SolveResult:
    best_value: int
    best_selection: tuple
    nodes: tuple
    incumbent_history: tuple
    truncated: bool
    order: tuple


def _capacity_exclusions(before, after, incompatibility_exclusions):
    """Pakete, die die Propagation zusätzlich zu `before` festgelegt hat und die NICHT per
    Kompatibilitätsregel ausgeschlossen wurden - also per Kapazitätsregel."""
    return tuple(sorted(i for i in after if i not in before and i not in incompatibility_exclusions))


def solve(instance, max_nodes=MAX_NODES_EXPLORED):
    order = ratio_order(instance)
    nodes = []
    incumbent_history = []
    best = {"value": 0, "selection": tuple(False for _ in range(instance.n_items))}
    truncated = {"flag": False}
    next_id = [0]

    def new_node(parent_id, depth, item_index, decision, weight, value, status, detail=None, exclusions=(),
                 capacity_exclusions=()):
        node = Node(next_id[0], parent_id, depth, item_index, decision, weight, value, status, detail, exclusions,
                    capacity_exclusions)
        next_id[0] += 1
        nodes.append(node)
        return node

    root_forced, _root_reason, _root_detail, root_exclusions = propagate(instance, {}, best["value"])
    root = new_node(None, len(root_forced), None, None, 0, 0, "root", exclusions=root_exclusions,
                    capacity_exclusions=_capacity_exclusions({}, root_forced, root_exclusions))

    def explore(node, forced):
        remaining = [i for i in order if i not in forced]
        if not remaining:
            return
        item = remaining[0]
        current_weight = sum(instance.weights[i] for i, v in forced.items() if v)
        current_value = sum(instance.values[i] for i, v in forced.items() if v)

        for decision in (True, False):
            if truncated["flag"] or len(nodes) >= max_nodes:
                truncated["flag"] = True
                return

            trial_forced = dict(forced)
            trial_forced[item] = decision
            new_weight = current_weight + (instance.weights[item] if decision else 0)
            new_value = current_value + (instance.values[item] if decision else 0)

            propagated, reason, detail, exclusions = propagate(instance, trial_forced, best["value"])

            # Strukturell unmöglich (wie bei der Kompatibilität, siehe Modul-Docstring): `item` ist
            # unentschieden, also hat der Fixpunkt des Elternknotens es nicht auf False gezwungen -
            # committed + w_item <= Kapazität. Ein eigener "Kapazität überschritten"-Status wäre
            # deshalb in jedem Lauf leer; die Propagation weist ihren Nutzen stattdessen als
            # `capacity_exclusions` aus.
            assert reason != "capacity", "Kapazitätsverletzung bei einer Entscheidung über ein unentschiedenes Paket"
            capacity_excl = _capacity_exclusions(trial_forced, propagated, exclusions)
            if reason == "bound":
                new_node(node.id, len(trial_forced), item, decision, new_weight, new_value, "prune_bound", detail,
                         exclusions, capacity_excl)
                continue

            final_weight = sum(instance.weights[i] for i, v in propagated.items() if v)
            final_value = sum(instance.values[i] for i, v in propagated.items() if v)
            remaining_after = [i for i in order if i not in propagated]

            if not remaining_after:
                is_new_best = final_value > best["value"]
                status = "leaf_new_best" if is_new_best else "leaf_not_best"
                child = new_node(node.id, len(propagated), item, decision, final_weight, final_value, status,
                                 exclusions=exclusions, capacity_exclusions=capacity_excl)
                if is_new_best:
                    best["value"] = final_value
                    best["selection"] = tuple(propagated.get(i, False) for i in range(instance.n_items))
                    incumbent_history.append((child.id, final_value))
                continue

            child = new_node(node.id, len(propagated), item, decision, final_weight, final_value, "branch",
                             exclusions=exclusions, capacity_exclusions=capacity_excl)
            explore(child, propagated)

    explore(root, root_forced)

    return SolveResult(
        best_value=best["value"],
        best_selection=best["selection"],
        nodes=tuple(nodes),
        incumbent_history=tuple(incumbent_history),
        truncated=truncated["flag"],
        order=tuple(order),
    )
