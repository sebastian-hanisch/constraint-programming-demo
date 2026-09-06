"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Button (Standardmuster aus
dem OR-Demo-Portfolio, siehe branch-bound-demo/bb_presets.py)."""

import math
import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import csp_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


SETTING_SPECS = {
    "n_items_slider": SettingSpec("n", int, C.DEFAULT_N_ITEMS, C.N_ITEMS_MIN, C.N_ITEMS_MAX),
    "capacity_fraction_slider": SettingSpec(
        "cap", float, C.DEFAULT_CAPACITY_FRACTION, C.CAPACITY_FRACTION_MIN, C.CAPACITY_FRACTION_MAX
    ),
    "correlation_slider": SettingSpec("corr", float, C.DEFAULT_CORRELATION, C.CORRELATION_MIN, C.CORRELATION_MAX),
    "n_incompatible_pairs_slider": SettingSpec(
        "pairs", int, C.DEFAULT_N_INCOMPATIBLE_PAIRS, C.N_INCOMPATIBLE_PAIRS_MIN, C.N_INCOMPATIBLE_PAIRS_MAX
    ),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, 2_000_000_000),
}


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default
    if "force_regen" not in st.session_state:
        st.session_state["force_regen"] = False


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if isinstance(value, float) and not math.isfinite(value):
                    continue
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
                st.session_state[state_key] = value
            except (ValueError, TypeError):
                pass
    st.session_state["permalink_loaded"] = True


def sync_query_params(n_items, capacity_fraction, correlation, n_incompatible_pairs, seed):
    try:
        st.query_params["n"] = str(int(n_items))
        st.query_params["cap"] = str(capacity_fraction)
        st.query_params["corr"] = str(correlation)
        st.query_params["pairs"] = str(int(n_incompatible_pairs))
        st.query_params["seed"] = str(int(seed))
    except Exception:
        pass


def apply_preset(name):
    p = C.PRESETS[name]
    st.session_state["n_items_slider"] = p["n_items"]
    st.session_state["capacity_fraction_slider"] = p["capacity_fraction"]
    st.session_state["correlation_slider"] = p["correlation"]
    st.session_state["n_incompatible_pairs_slider"] = p["n_incompatible_pairs"]
    st.session_state["seed_input"] = p["seed"]
    st.session_state["force_regen"] = True


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, 2_000_000_000)
    st.session_state["force_regen"] = True
