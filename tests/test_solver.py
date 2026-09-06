import pytest

from csp_bnb_reference import solve_bnb_reference
from csp_bruteforce import solve_bruteforce
from csp_constants import PRESETS
from csp_ortools_reference import solve_with_ortools
from csp_scenario import KnapsackInstance, generate_instance
from csp_solver import solve


def _is_compatible(instance, selection):
    return all(not (selection[i] and selection[j]) for i, j in instance.incompatible_pairs)


def test_matches_hand_computed_tiny_instance_without_pairs():
    instance = KnapsackInstance(weights=(2, 3, 4, 5), values=(3, 4, 5, 6), capacity=5, correlation=0.0, incompatible_pairs=())
    result = solve(instance)
    assert result.best_value == 7
    assert result.best_selection == (True, True, False, False)


def test_solution_always_respects_capacity_and_incompatibility():
    for seed in range(20):
        instance = generate_instance(
            n_items=9, capacity_fraction=0.5, correlation=seed % 5 / 4, n_incompatible_pairs=3, seed=seed
        )
        result = solve(instance)
        weight = sum(w for w, take in zip(instance.weights, result.best_selection) if take)
        assert weight <= instance.capacity, f"seed={seed}"
        assert _is_compatible(instance, result.best_selection), f"seed={seed}"


def test_matches_bruteforce_across_random_instances_with_pairs():
    for seed in range(25):
        instance = generate_instance(
            n_items=9, capacity_fraction=0.5, correlation=seed % 5 / 4, n_incompatible_pairs=2, seed=seed
        )
        result = solve(instance)
        true_best, _ = solve_bruteforce(instance)
        assert result.best_value == true_best, f"seed={seed}"


def test_matches_ortools_across_random_instances():
    for seed in range(10):
        instance = generate_instance(
            n_items=10, capacity_fraction=0.5, correlation=0.3, n_incompatible_pairs=3, seed=seed
        )
        result = solve(instance)
        ortools_result = solve_with_ortools(instance)
        assert ortools_result["proven_optimal"]
        assert result.best_value == ortools_result["best_value"], f"seed={seed}"


def test_propagation_search_never_needs_more_nodes_than_plain_bnb():
    # Propagation kann Äste nur FRÜHER abschneiden als die reine schwache Bound
    # (dieselbe Formel, siehe csp_bnb_reference) - nie mehr Knoten.
    for seed in range(15):
        instance = generate_instance(
            n_items=9, capacity_fraction=0.5, correlation=0.2, n_incompatible_pairs=3, seed=seed
        )
        csp_result = solve(instance)
        _bnb_value, _bnb_sel, bnb_nodes, _truncated = solve_bnb_reference(instance)
        assert len(csp_result.nodes) <= bnb_nodes, f"seed={seed}"


def test_zero_incompatible_pairs_still_beats_bnb_reference_via_capacity_alone():
    # Überraschung beim Kalibrieren, nicht vorab angenommen: SELBST ganz ohne
    # Kompatibilitätsregeln braucht csp_solver deutlich weniger Knoten als
    # csp_bnb_reference. Grund: Kapazitäts-Propagation zwingt mehrere noch offene
    # Pakete auf einen Schlag auf False, sobald sie nicht mehr passen - während
    # csp_bnb_reference jedes einzeln "ausprobieren" muss (ein eigener Knoten pro
    # Paket, das sich als zu schwer herausstellt). Kompatibilitätsregeln kommen in
    # den anderen Presets NOCH oben drauf, sind aber nicht die einzige Quelle des
    # Vorteils.
    for seed in range(10):
        instance = generate_instance(
            n_items=8, capacity_fraction=0.5, correlation=0.0, n_incompatible_pairs=0, seed=seed
        )
        csp_result = solve(instance)
        _bnb_value, _bnb_sel, bnb_nodes, _truncated = solve_bnb_reference(instance)
        assert len(csp_result.nodes) < bnb_nodes, f"seed={seed}"


def test_incompatibility_exclusions_are_tracked_and_nonzero_when_rules_exist():
    # Ersetzt den (unerreichbaren) prune_incompatible-Status: der Nutzen der
    # Kompatibilitätsregeln zeigt sich als kumulierte Ausschluss-Zahl über den
    # gesamten Suchbaum, nicht als eigener Pruning-Grund.
    found_nonzero = False
    for seed in range(15):
        instance = generate_instance(
            n_items=9, capacity_fraction=0.5, correlation=0.2, n_incompatible_pairs=3, seed=seed
        )
        result = solve(instance)
        total_exclusions = sum(len(node.incompatibility_exclusions) for node in result.nodes)
        assert total_exclusions >= 0
        if total_exclusions > 0:
            found_nonzero = True
    assert found_nonzero, "keine Instanz zeigte automatische Kompatibilitäts-Ausschlüsse - Testdaten anpassen"


def test_no_node_ever_has_the_removed_incompatible_status():
    for seed in range(10):
        instance = generate_instance(
            n_items=9, capacity_fraction=0.5, correlation=0.2, n_incompatible_pairs=3, seed=seed
        )
        result = solve(instance)
        assert all(node.status != "prune_incompatible" for node in result.nodes)


def test_max_nodes_cap_is_honored_and_flagged_as_truncated():
    instance = generate_instance(n_items=16, capacity_fraction=0.5, correlation=0.9, n_incompatible_pairs=1, seed=1)
    result = solve(instance, max_nodes=50)
    assert len(result.nodes) <= 50 + 2
    assert result.truncated


@pytest.mark.parametrize("name", list(PRESETS.keys()))
def test_presets_solve_correctly(name):
    instance = generate_instance(**PRESETS[name])
    result = solve(instance)
    true_best, _ = solve_bruteforce(instance)
    assert result.best_value == true_best
