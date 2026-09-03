import meridian_geox as geox
import streamlit as st

from geox_app.design import (
    assignment_table,
    build_budget,
    build_constraints,
    build_design_config,
    parse_dates,
    parse_geo_set,
    run_design,
)
from geox_app.help_text import (
    ASSIGNMENT_HELP,
    CPIC_FEASIBILITY,
    INTERVENTION,
    QUALITY_CHECKS_URL,
    SDID_NOTE,
    TYPES_OF_EXPERIMENTS_URL,
)
from geox_app.persist import ROOT, save_design, save_latest
from geox_app.plots import show_design_plots
from geox_app.quality import render_quality_result

st.header("Design")
st.caption(
    "`run_design` searches stratified (or random) splits, filters on out-of-sample "
    "R² and A/A, then ranks by MDE. Budget in the table is **required experiment "
    "spend change**, not national baseline. "
    f"[Data validation and quality checks]({QUALITY_CHECKS_URL})."
)
st.caption(SDID_NOTE)

df = st.session_state.get("design_df")
if df is None:
    st.info("Save a design panel on Data first.")
    st.stop()

st.subheader("Experiment")
mode = st.segmented_control(
    "Study type",
    options=["single", "multi"],
    format_func=lambda x: "Single cell" if x == "single" else "Multi cell",
    key="study_mode",
    help="Set this here if you skipped it on Data. Multi-cell shows one budget card per arm.",
)
if mode is None:
    mode = "single"
n_cells = 1
if mode == "multi":
    n_cells = int(
        st.number_input(
            "Number of treatment cells",
            min_value=2,
            max_value=4,
            value=2,
            step=1,
            key="n_cells",
            help="Each cell is a treatment arm with its own type and budget. They share one control group.",
        )
    )

cell_names = [f"cell_{i}" for i in range(1, n_cells + 1)]
cell_types = {}
duration = st.number_input(
    "Duration (days)",
    min_value=7,
    max_value=90,
    value=30,
    step=1,
    help="Length of the in-market test. Pretest data should be about 3× this long.",
)
type_keys = ["HOLDBACK", "GO_DARK", "HEAVY_UP"]
cols = st.columns(n_cells)
for i, cell in enumerate(cell_names):
    with cols[i]:
        default = "HOLDBACK" if n_cells == 1 else ("GO_DARK" if i == 0 else "HEAVY_UP")
        cell_types[cell] = st.selectbox(
            f"{cell} type",
            type_keys,
            index=type_keys.index(default),
            format_func=lambda k: INTERVENTION[k]["label"],
            key=f"type_{cell}",
            help=(
                "Holdback: new spend vs a holdout. Go-dark: shut off existing spend "
                "in treatment. Heavy-up: extra spend vs BAU. Details in the box below."
            ),
        )

chosen_kinds = list(dict.fromkeys(cell_types.values()))
for kind in chosen_kinds:
    spec = INTERVENTION[kind]
    st.info(
        f"**{spec['label']}** — {spec['summary']}\n\n"
        f"{spec['setup']}\n\n"
        f"[Types of experiments]({TYPES_OF_EXPERIMENTS_URL})"
    )

assignment = st.selectbox(
    "Geo assignment",
    ["STRATIFIED_SAMPLING", "RANDOM"],
    format_func=lambda x: "Stratified sampling" if x == "STRATIFIED_SAMPLING" else "Random",
    help=ASSIGNMENT_HELP,
)
alpha = st.number_input(
    "Alpha",
    min_value=0.01,
    max_value=0.2,
    value=0.10,
    step=0.01,
    help="Significance level for two-sided tests. GeoX default is 0.10 (not 0.05).",
)
power = st.number_input(
    "Target power",
    min_value=0.5,
    max_value=0.99,
    value=0.80,
    step=0.05,
    help="Probability of detecting the MDE when it is real. 0.80 is the usual target.",
)
output_n = st.number_input(
    "Designs to keep",
    min_value=1,
    max_value=20,
    value=5,
    step=1,
    help="How many ranked candidates to return after search and quality filters.",
)

st.subheader("Budget and CpIC")
st.caption(
    "One card per treatment cell. **CpIC is only for holdback** (sizes new-campaign "
    "spend as MDE × CpIC). Go-dark / heavy-up use a **budget %** instead, not CpIC. "
    "Holdback: optional spend cap. Heavy-up: positive fraction of baseline (1.0 = +100%). "
    "Go-dark: negative fraction (−1.0 = full shutoff)."
)
if n_cells == 1:
    st.warning(
        "Only one cell is shown because study type is **single cell**. Switch to "
        "**Multi cell** above to set type and budget for cell_2, cell_3, …"
    )
budgets = {}
cpic_vals = {}
for cell, kind in cell_types.items():
    with st.container(border=True):
        st.markdown(f"**{cell} · {INTERVENTION[kind]['label']}**")
        if kind == "HOLDBACK":
            cpic_vals[cell] = st.number_input(
                "Cost per incremental conversion (CpIC)",
                min_value=0.0,
                value=1.0,
                key=f"cpic_{cell}",
                help=(
                    "Expected cost per incremental conversion (1 / target iROAS if the "
                    "KPI is revenue). Used to size holdback budget as MDE × CpIC."
                ),
            )
            cap = st.number_input(
                "Budget cap (optional, 0 = none)",
                min_value=0.0,
                value=500000.0,
                key=f"cap_{cell}",
                help="Maximum new-campaign spend allowed in the holdback design search.",
            )
            b = build_budget("HOLDBACK", cap if cap > 0 else None, None)
            if b is not None:
                budgets[cell] = b
        elif kind == "HEAVY_UP":
            pct = st.number_input(
                "Spend increase (fraction of baseline)",
                value=1.0,
                key=f"pct_{cell}",
                help="1.0 = +100% vs historical spend in treatment geos. Must be positive.",
            )
            budgets[cell] = build_budget("HEAVY_UP", None, pct)
        else:
            pct = st.number_input(
                "Spend reduction (negative fraction)",
                value=-1.0,
                key=f"pct_{cell}",
                help="−1.0 = full shutoff; −0.5 = 50% dim. Must be negative.",
            )
            budgets[cell] = build_budget("GO_DARK", None, pct)

st.subheader("Constraints")
max_vol = st.slider(
    "Max treatment conversion share",
    0.05,
    0.9,
    0.30,
    0.05,
    help=(
        "Cap on treatment-group share of conversion volume (all treatment cells "
        "combined in multi-cell). Default 0.30."
    ),
)
excl_geos = st.text_area(
    "Excluded geos (comma-separated)",
    value="",
    height=70,
    help="Geos left out of treatment and control (concurrent tests, launches, etc.).",
)
incl_ctrl = st.text_area(
    "Force into control (comma-separated)",
    value="",
    height=70,
    help="Geos that must stay in the control pool.",
)
excl_dates = st.text_area(
    "Excluded dates YYYY-MM-DD (comma-separated)",
    value="",
    height=70,
    help="Drop these dates from the pretest used for design.",
)
q1, q2 = st.columns(2)
with q1:
    drop_empty = st.checkbox(
        "Drop geos with no response",
        value=True,
        help="If off, you still see flagged geos in quality checks and can exclude them manually.",
    )
with q2:
    drop_outliers = st.checkbox(
        "Drop outlier dates",
        value=True,
        help="If off, outlier dates are reported but kept unless you list them under excluded dates.",
    )

with st.expander("Search budget (slow if large)"):
    match_colab = st.checkbox(
        "Colab-scale search (100,000 candidates, 100 fully scored)",
        value=False,
        help=(
            "Matches the single-cell Colab / library defaults. Slow on a laptop. "
            "Needed if you want the same ranked splits (and later the same analysis plots) "
            "as the notebook on Google’s sample."
        ),
    )
    if match_colab:
        n_cand, n_rank = 100_000, 100
        st.caption("Using Colab `n_candidates=100_000` and `n_ranked_candidates=100`.")
    else:
        st.caption("Interactive default is 5,000 candidates / 50 fully scored.")
        n_cand = st.number_input(
            "n_candidates",
            min_value=200,
            max_value=100_000,
            value=5_000,
            step=100,
            help="Size of the random/stratified candidate pool before R² filtering. Colab: 100,000.",
        )
        n_rank = st.number_input(
            "n_ranked_candidates",
            min_value=10,
            max_value=500,
            value=50,
            step=10,
            help="How many candidates get full MDE / A/A scoring. Colab: 100.",
        )
    min_r2 = st.number_input(
        "min_r2",
        min_value=0.0,
        max_value=1.0,
        value=0.8,
        step=0.05,
        help="Minimum out-of-sample R² on the validation split. Default 0.8.",
    )
    seed = st.number_input(
        "Seed",
        min_value=0,
        value=42,
        step=1,
        help="RNG seed for candidate generation (reproducible splits).",
    )

cpic_arg: float | dict[str, float]
if n_cells == 1:
    cpic_arg = next(iter(cpic_vals.values()), 1.0)
else:
    cpic_arg = cpic_vals if cpic_vals else 1.0

budget_arg = None
if n_cells == 1 and budgets:
    budget_arg = next(iter(budgets.values()))
elif budgets:
    budget_arg = budgets

preview, run = st.columns(2)
with preview:
    do_preview = st.button("Preview quality checks", icon=":material/fact_check:")
with run:
    do_run = st.button("Run design", type="primary", icon=":material/play_arrow:")

if do_preview or do_run:
    config = build_design_config(
        duration_days=int(duration),
        cell_types=cell_types,
        assignment=assignment,
        cpic=cpic_arg,
        design_output_count=int(output_n),
        alpha=float(alpha),
        power=float(power),
        n_candidates=int(n_cand),
        n_ranked_candidates=int(n_rank),
        min_r2=float(min_r2),
        seed=int(seed),
    )
    quality_cfg = geox.QualityCheckConfig(
        exclude_geos_no_response=drop_empty,
        exclude_outlier_dates=drop_outliers,
    )
    if do_preview:
        try:
            preview_qc = geox.check_design_data_quality(df, config, quality_cfg)
        except Exception as exc:
            st.exception(exc)
        else:
            st.session_state.preview_quality = preview_qc
    if do_run:
        constraints = build_constraints(
            excluded_geos=parse_geo_set(excl_geos),
            included_control_geos=parse_geo_set(incl_ctrl),
            excluded_dates=parse_dates(excl_dates),
            budget_constraint=budget_arg,
            max_conversions_percent=float(max_vol),
        )
        with st.spinner("Searching designs (JAX). First run compiles; this can take minutes."):
            try:
                design_set = run_design(
                    df,
                    config,
                    constraints,
                    exclude_geos_no_response=drop_empty,
                    exclude_outlier_dates=drop_outliers,
                )
            except Exception as exc:
                st.exception(exc)
                st.stop()
        st.session_state.design_set = design_set
        if design_set.design_metrics is not None and not design_set.design_metrics.empty:
            st.session_state.selected_design_id = str(
                design_set.design_metrics["design_id"].iloc[0]
            )
            st.session_state.selected_design = design_set.designs[
                st.session_state.selected_design_id
            ]
            st.session_state.design_json = st.session_state.selected_design.export_to_json()
            save_latest(st.session_state.selected_design)
            st.session_state._latest_design_id = st.session_state.selected_design_id
        st.session_state.analysis_result = None

if st.session_state.get("preview_quality") is not None:
    render_quality_result(
        st.session_state.preview_quality,
        phase="design",
        title="Pre-search quality preview",
    )

design_set = st.session_state.get("design_set")
if design_set is None:
    st.stop()

metrics = design_set.design_metrics
st.subheader("Ranked designs")
st.dataframe(metrics, width="stretch")

ids = [str(x) for x in metrics["design_id"].tolist()] if not metrics.empty else []
if not ids:
    st.warning("No designs passed filters. Loosen min R², volume cap, or raise n_candidates.")
    st.stop()

chosen = st.selectbox(
    "Selected design",
    ids,
    index=ids.index(st.session_state.selected_design_id)
    if st.session_state.selected_design_id in ids
    else 0,
    help="Top row is the library rank. Pick another ID to inspect assignment and implied CpIC.",
)
st.session_state.selected_design_id = chosen
st.session_state.selected_design = design_set.designs[chosen]
st.session_state.design_json = st.session_state.selected_design.export_to_json()
if st.session_state.get("_latest_design_id") != chosen:
    save_latest(st.session_state.selected_design)
    st.session_state._latest_design_id = chosen

design = st.session_state.selected_design
for cell, per in design.designs.items():
    st.metric(f"Implied CpIC · {cell}", f"{per.design_implied_cpic:,.3f}")

st.info(CPIC_FEASIBILITY)

render_quality_result(
    design.quality_check_result,
    phase="design",
    title="Quality checks (selected design)",
)

st.subheader("Assignment")
st.dataframe(assignment_table(design), width="stretch")

st.subheader("Pre-test fit")
show_design_plots(design)

st.subheader("Save design")
st.caption(
    "Writes JSON under `outputs/designs/` so Analysis can load it without a download. "
    "The current selection is also stored as `_latest.json`."
)
save_name = st.text_input(
    "Library name",
    value=f"design_{chosen[:8]}",
    help="Saved as outputs/designs/<name>.json. Overwrites a file with the same name.",
)
if st.button("Save to library", icon=":material/save:"):
    path = save_design(design, save_name)
    st.success(f"Saved `{path.relative_to(ROOT)}`. Analysis can load it from the library.")

st.download_button(
    "Download design JSON",
    data=st.session_state.design_json,
    file_name=f"geox_design_{chosen[:8]}.json",
    mime="application/json",
    icon=":material/download:",
    help="Optional export. Analysis can use the local library instead.",
)
