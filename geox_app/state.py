"""Session state for the GeoX Streamlit app."""

from __future__ import annotations

import streamlit as st

DEFAULTS = {
    "study_mode": "single",  # single | multi
    "design_df": None,
    "analysis_df": None,
    "design_source": None,
    "analysis_source": None,
    "design_set": None,
    "selected_design_id": None,
    "selected_design": None,
    "design_json": None,
    "analysis_result": None,
    "analysis_result_cooldown": None,
    "comparison_set": None,
    "concat_set": None,
}


def init_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)


def clear_downstream_of_data() -> None:
    for key in (
        "design_set",
        "selected_design_id",
        "selected_design",
        "design_json",
        "analysis_result",
        "analysis_result_cooldown",
        "comparison_set",
        "concat_set",
        "preview_quality",
        "preview_analysis_quality",
    ):
        st.session_state[key] = None
