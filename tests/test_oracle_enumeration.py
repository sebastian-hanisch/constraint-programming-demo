"""Unabhängiges Orakel: reine Aufzählung aller 2^n Belegungen (ohne Propagation, ohne Suchbaum).

Prüft (1) den Optimalwert samt Zulässigkeit der gelieferten Auswahl, (2) die angezeigte Kennzahl
"Automatisch ausgeschlossen (Kapazität)": jeder dort gezählte Ausschluss muss wirklich nicht mehr
in die Restkapazität passen, und die Kennzahl darf nicht in jedem Lauf 0 sein (früher: Status
`prune_infeasible`, der strukturell nie auftrat)."""

import itertools
import random

from csp_evaluation import compute_stats, stats_up_to_step
from csp_scenario import KnapsackInstance, generate_instance
from csp_solver import solve


def _enumerate_best(instance):
    best, count = 0, 0
    for sel in itertools.product((0, 1), repeat=instance.n_items):
        if sum(w * s for w, s in zip(instance.weights, sel)) > instance.capacity:
            continue
        if any(sel[i] and sel[j] for i, j in instance.incompatible_pairs):
            continue
        count += 1
        best = max(best, sum(v * s for v, s in zip(instance.values, sel)))
    return best, count


def _random_instance(rng):
    n = rng.randint(1, 9)
    weights = tuple(rng.randint(1, 10) for _ in range(n))
    values = tuple(rng.randint(1, 10) for _ in range(n))  # viele Gleichstände
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    chosen = tuple(sorted(rng.sample(pairs, rng.randint(0, min(len(pairs), 4)))))
    return KnapsackInstance(weights, values, rng.randint(1, sum(weights)), 0.0, chosen)


def test_best_value_and_selection_match_full_enumeration():
    rng = random.Random(42)
    for _ in range(200):
        inst = _random_instance(rng)
        res = solve(inst)
        best, _count = _enumerate_best(inst)
        sel = res.best_selection
        assert res.best_value == best, inst
        assert sum(v for v, s in zip(inst.values, sel) if s) == res.best_value
        assert sum(w for w, s in zip(inst.weights, sel) if s) <= inst.capacity
        assert not any(sel[i] and sel[j] for i, j in inst.incompatible_pairs)


def test_capacity_exclusions_are_real_and_not_always_zero():
    rng = random.Random(7)
    total = 0
    for _ in range(100):
        inst = _random_instance(rng)
        res = solve(inst)
        for node in res.nodes:
            for i in node.capacity_exclusions:
                assert i != node.item_index
                assert inst.weights[i] + node.weight > inst.capacity, (inst, node)
            assert not set(node.capacity_exclusions) & set(node.incompatibility_exclusions)
        total += compute_stats(res)["capacity_exclusions"]
        last = len(res.nodes) - 1
        assert stats_up_to_step(res, last)["capacity_exclusions"] == compute_stats(res)["capacity_exclusions"]
    assert total > 0


def test_preset_like_instance_shows_capacity_exclusions():
    inst = generate_instance(8, 0.5, 0.0, 0, 7)
    assert compute_stats(solve(inst))["capacity_exclusions"] > 0
