import streamlit as st

import meridian_geox as geox

from geox_app.design import build_constraints, build_design_config
from geox_app.plots import show_design_plots

st.header("Compare")
st.caption(
    "**Compare** re-runs several `DesignConfig`s on the same pretest panel "
    "(`compare_designs`) — e.g. random vs stratified, or 14 vs 30 days. "
    "**Concatenate** only merges DesignSets you already computed (last Design "
    "run plus this comparison) and re-ranks them. SDID is not available in GeoX "
    "1.0.0, so methodology is TBR on every arm."
)

df = st.session_state.get("design_df")
if df is None:
    st.info("Save a design panel on Data first.")
    st.stop()

preset = st.segmented_control(
    "Preset",
    options=["assignment", "duration"],
    format_func=lambda x: "Random vs stratified" if x == "assignment" else "14 vs 30 days",
    key="compare_preset",
    help="Each arm is a full design search on the same pretest panel.",
)
if preset is None:
    preset = "assignment"

n_keep = st.number_input(
    "Designs to keep after ranking",
    min_value=2,
    max_value=20,
    value=8,
    help="Top N after combining the two configs.",
)
n_cand = st.number_input(
    "n_candidates per config",
    min_value=200,
    max_value=20_000,
    value=2_000,
    step=100,
    help="Keep this modest; comparison runs two searches.",
)

mode = st.session_state.get("study_mode") or "single"
cell_types = {"cell_1": "HOLDBACK"}
if mode == "multi":
    cell_types = {"cell_1": "GO_DARK", "cell_2": "HEAVY_UP"}

constraints = build_constraints(
    excluded_geos=set(),
    included_control_geos=set(),
    excluded_dates=set(),
    budget_constraint=None,
    max_conversions_percent=0.3,
)


def _cfg(days: int, assignment: str) -> geox.DesignConfig:
    return build_design_config(
        duration_days=days,
        cell_types=cell_types,
        assignment=assignment,
        cpic=1.0,
        design_output_count=5,
        alpha=0.10,
        power=0.80,
        n_candidates=int(n_cand),
        n_ranked_candidates=min(40, int(n_cand)),
        min_r2=0.8,
        seed=42,
    )


if st.button("Run comparison", type="primary", icon=":material/play_arrow:"):
    if preset == "assignment":
        reqs = [
            (_cfg(30, "RANDOM"), constraints),
            (_cfg(30, "STRATIFIED_SAMPLING"), constraints),
        ]
    else:
        reqs = [
            (_cfg(14, "STRATIFIED_SAMPLING"), constraints),
            (_cfg(30, "STRATIFIED_SAMPLING"), constraints),
        ]
    with st.spinner("Running compare_designs (each config is a full search)."):
        try:
            compared = geox.compare_designs(df, reqs, design_output_count=int(n_keep))
        except Exception as exc:
            st.exception(exc)
            st.stop()
    st.session_state.comparison_set = compared

compared = st.session_state.get("comparison_set")
if compared is not None:
    st.subheader("Comparison ranking")
    st.dataframe(compared.design_metrics, width="stretch")
    cid = str(compared.design_metrics["design_id"].iloc[0])
    pick = st.selectbox("Inspect design", list(compared.designs.keys()), index=0, key="cmp_id")
    show_design_plots(compared.designs[pick])

st.divider()
st.subheader("Concatenate")
st.caption(
    "Merge the Design page `DesignSet` with the comparison `DesignSet` and take "
    "the top N by the library ranker."
)
if st.button("Concatenate last design + comparison", icon=":material/merge:"):
    sets = []
    if st.session_state.get("design_set") is not None:
        sets.append(st.session_state.design_set)
    if st.session_state.get("comparison_set") is not None:
        sets.append(st.session_state.comparison_set)
    if len(sets) < 2:
        st.warning("Need both a Design run and a Compare run.")
    else:
        try:
            st.session_state.concat_set = geox.concat_design_reports(
                sets, design_output_count=int(n_keep)
            )
        except Exception as exc:
            st.exception(exc)

concat = st.session_state.get("concat_set")
if concat is not None:
    st.dataframe(concat.design_metrics, width="stretch")
