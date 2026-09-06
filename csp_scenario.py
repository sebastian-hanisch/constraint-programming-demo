"""Zufällige 0/1-Rucksack-Instanzen für die Constraint-Programming-Demo - dieselbe
Grundfamilie wie in branch-bound-demo, erweitert um `incompatible_pairs`: zufällige
"höchstens eines von beiden"-Regeln zwischen Paketpaaren. Diese Regel ist eine
logische Nebenbedingung, die eine LP-Relaxierung (wie in branch-bound-demo) nicht
ausdrücken kann - genau die Lücke, die Constraint-Propagation in dieser Demo
schließt."""

from dataclasses import dataclass

import numpy as np

from csp_constants import VALUE_BASE_RANGE, VALUE_NOISE_RANGE, WEIGHT_RANGE


@dataclass(frozen=True)
class KnapsackInstance:
    weights: tuple
    values: tuple
    capacity: int
    correlation: float
    incompatible_pairs: tuple  # Tupel von (i, j)-Paaren, i < j

    @property
    def n_items(self):
        return len(self.weights)


def _generate_incompatible_pairs(rng, n_items, count):
    if n_items < 2 or count <= 0:
        return ()
    all_pairs = [(i, j) for i in range(n_items) for j in range(i + 1, n_items)]
    count = min(count, len(all_pairs))
    chosen = rng.choice(len(all_pairs), size=count, replace=False)
    return tuple(sorted(all_pairs[i] for i in chosen))


def generate_instance(n_items, capacity_fraction, correlation, n_incompatible_pairs, seed):
    rng = np.random.default_rng(seed)
    weights = rng.integers(WEIGHT_RANGE[0], WEIGHT_RANGE[1] + 1, size=n_items)
    uncorrelated_value = rng.integers(VALUE_BASE_RANGE[0], VALUE_BASE_RANGE[1] + 1, size=n_items)
    noise = rng.integers(VALUE_NOISE_RANGE[0], VALUE_NOISE_RANGE[1] + 1, size=n_items)
    correlated_value = weights + noise
    values = np.round((1 - correlation) * uncorrelated_value + correlation * correlated_value)
    values = np.maximum(values, 1).astype(int)
    capacity = max(1, round(capacity_fraction * weights.sum()))
    incompatible_pairs = _generate_incompatible_pairs(rng, n_items, n_incompatible_pairs)
    return KnapsackInstance(
        weights=tuple(int(w) for w in weights),
        values=tuple(int(v) for v in values),
        capacity=int(capacity),
        correlation=correlation,
        incompatible_pairs=incompatible_pairs,
    )
