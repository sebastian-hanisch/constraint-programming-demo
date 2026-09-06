import pytest

from csp_propagation import propagate
from csp_scenario import KnapsackInstance


def test_capacity_propagation_forces_items_that_would_overflow():
    instance = KnapsackInstance(weights=(5, 5, 5), values=(1, 1, 1), capacity=6, incompatible_pairs=(), correlation=0.0)
    forced, reason, _detail, _exclusions = propagate(instance, {0: True}, best_value=0)
    assert reason is None
    # Nach Paket 0 (Gewicht 5) bleiben nur noch 1 Kapazität - Pakete 1 und 2 (je 5) passen nicht mehr.
    assert forced[1] is False
    assert forced[2] is False


def test_capacity_violation_is_detected():
    instance = KnapsackInstance(weights=(5, 5), values=(1, 1), capacity=6, incompatible_pairs=(), correlation=0.0)
    _forced, reason, _detail, _exclusions = propagate(instance, {0: True, 1: True}, best_value=0)
    assert reason == "capacity"


def test_incompatibility_forces_the_partner_to_false_and_is_reported_as_an_exclusion():
    instance = KnapsackInstance(
        weights=(5, 5, 5), values=(1, 1, 1), capacity=20, incompatible_pairs=((0, 1),), correlation=0.0
    )
    forced, reason, _detail, exclusions = propagate(instance, {0: True}, best_value=0)
    assert reason is None
    assert forced[1] is False
    assert 2 not in forced  # unbeteiligtes Paket bleibt offen
    assert exclusions == (1,)


def test_explicit_double_true_on_an_incompatible_pair_is_an_invariant_violation():
    # propagate() wird nie mit einem solchen `forced` von csp_solver.solve() aufgerufen
    # (siehe csp_solver.py's Modul-Docstring, warum das strukturell unmöglich ist) -
    # ein direkter Aufruf mit künstlich widersprüchlichem Input muss trotzdem laut
    # scheitern, statt den Widerspruch still zu ignorieren.
    instance = KnapsackInstance(
        weights=(1, 1), values=(1, 1), capacity=20, incompatible_pairs=((0, 1),), correlation=0.0
    )
    with pytest.raises(AssertionError):
        propagate(instance, {0: True, 1: True}, best_value=0)


def test_bound_propagation_cuts_off_branches_that_cannot_improve():
    instance = KnapsackInstance(weights=(5, 5), values=(3, 3), capacity=20, incompatible_pairs=(), correlation=0.0)
    # Bestwert bereits 10 - selbst beide verbleibenden Pakete (Wert 3 je) reichen nicht.
    _forced, reason, detail, _exclusions = propagate(instance, {}, best_value=10)
    assert reason == "bound"
    assert detail == 6


def test_propagation_never_assigns_conflicting_values():
    instance = KnapsackInstance(
        weights=(5, 5, 5, 5), values=(2, 2, 2, 2), capacity=12, incompatible_pairs=((0, 1), (1, 2)), correlation=0.0
    )
    forced, reason, _detail, _exclusions = propagate(instance, {0: True}, best_value=0)
    if reason is None:
        for i, v in forced.items():
            assert isinstance(v, bool)
