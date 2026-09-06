"""Erschöpfender Referenzlöser - prüft Kapazität UND alle Kompatibilitätspaare,
unabhängig von Constraint-Propagation. Nur für kleine n_items praktikabel."""

from itertools import product


def solve_bruteforce(instance):
    best_value = 0
    best_selection = tuple(False for _ in range(instance.n_items))
    for selection in product([False, True], repeat=instance.n_items):
        weight = sum(w for w, take in zip(instance.weights, selection) if take)
        if weight > instance.capacity:
            continue
        if any(selection[i] and selection[j] for i, j in instance.incompatible_pairs):
            continue
        value = sum(v for v, take in zip(instance.values, selection) if take)
        if value > best_value:
            best_value = value
            best_selection = selection
    return best_value, best_selection
