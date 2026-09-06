"""Defaults, slider bounds und Presets für die Constraint-Programming-Demo."""

DEFAULT_N_ITEMS = 6
DEFAULT_CAPACITY_FRACTION = 0.5
DEFAULT_CORRELATION = 0.0
DEFAULT_N_INCOMPATIBLE_PAIRS = 2
DEFAULT_SEED = 7

N_ITEMS_MIN, N_ITEMS_MAX = 3, 18
CAPACITY_FRACTION_MIN, CAPACITY_FRACTION_MAX = 0.2, 0.8
CORRELATION_MIN, CORRELATION_MAX = 0.0, 1.0
N_INCOMPATIBLE_PAIRS_MIN, N_INCOMPATIBLE_PAIRS_MAX = 0, 6

WEIGHT_RANGE = (5, 30)
VALUE_BASE_RANGE = (5, 30)
VALUE_NOISE_RANGE = (-8, 8)

MAX_NODES_EXPLORED = 200_000
MAX_NODES_RENDERED = 800

# OR-Tools-Referenzlauf: harte Zeitgrenze, damit ein Preset niemals hängt.
ORTOOLS_TIME_LIMIT_SECONDS = 10.0

PRESETS = {
    "Reines Rucksack (0 Regeln, Propagation hilft schon etwas)": {
        "n_items": 8, "capacity_fraction": 0.5, "correlation": 0.0,
        "n_incompatible_pairs": 0, "seed": 7,
    },
    "Wenige Regeln, großer Unterschied": {
        "n_items": 8, "capacity_fraction": 0.5, "correlation": 0.0,
        "n_incompatible_pairs": 3, "seed": 7,
    },
    "Mehr Pakete, mehr Regeln": {
        "n_items": 14, "capacity_fraction": 0.5, "correlation": 0.2,
        "n_incompatible_pairs": 5, "seed": 3,
    },
}
