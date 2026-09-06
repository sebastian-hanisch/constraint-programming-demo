"""Klassisches Branch & Bound auf demselben erweiterten Problem (mit
Kompatibilitätspaaren), aber mit branch-bound-demos EIGENER `weak_bound`-Formel -
die die Kompatibilitätsregeln gar nicht kennt. Verletzungen werden deshalb erst am
Blatt geprüft (dort verworfen, nie als neuer bester Fund akzeptiert), NIE durch
vorzeitiges Abschneiden eines ganzen Astes. Zeigt konkret, wie viele zum Scheitern
verurteilte Äste B&B ohne Propagation trotzdem vollständig durchsucht - die
Vergleichsgröße für csp_solver.solve()."""

from csp_constants import MAX_NODES_EXPLORED


def _ratio_order(instance):
    return sorted(range(instance.n_items), key=lambda i: instance.values[i] / instance.weights[i], reverse=True)


def _weak_bound(instance, order, depth, current_value):
    return current_value + sum(instance.values[idx] for idx in order[depth:])


def _is_compatible(instance, selection):
    return all(not (selection[i] and selection[j]) for i, j in instance.incompatible_pairs)


def solve_bnb_reference(instance, max_nodes=MAX_NODES_EXPLORED):
    order = _ratio_order(instance)
    n = instance.n_items
    best = {"value": 0, "selection": [False] * n}
    nodes = {"count": 1}  # zählt die Wurzel mit, wie in branch-bound-demo
    truncated = {"flag": False}

    def explore(depth, weight, value, decisions):
        if depth == n:
            if value > best["value"] and _is_compatible(instance, decisions):
                best["value"] = value
                best["selection"] = list(decisions)
            return

        item = order[depth]
        w, v = instance.weights[item], instance.values[item]
        for decision in (True, False):
            if truncated["flag"] or nodes["count"] >= max_nodes:
                truncated["flag"] = True
                return
            nodes["count"] += 1

            new_weight = weight + (w if decision else 0)
            new_value = value + (v if decision else 0)
            if decision and new_weight > instance.capacity:
                continue

            bound = _weak_bound(instance, order, depth + 1, new_value)
            if bound <= best["value"]:
                continue

            new_decisions = list(decisions)
            new_decisions[item] = decision
            explore(depth + 1, new_weight, new_value, new_decisions)

    explore(0, 0, 0, [False] * n)

    return best["value"], tuple(best["selection"]), nodes["count"], truncated["flag"]
