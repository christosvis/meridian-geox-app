import pandas as pd
import streamlit as st

import meridian_geox as geox

from geox_app.analysis import (
    analysis_config,
    estimate_frame,
    preview_analysis_quality,
    run_analysis,
)
from geox_app.help_text import QUALITY_CHECKS_URL, PRIORS_DOCS
from geox_app.persist import latest_path, list_saved_designs, load_design, save_analysis_pickle
from geox_app.plots import show_analysis_plots
from geox_app.priors import (
    calibration_snippet,
    cells_frame,
    experiment_payload,
    payload_json,
)
from geox_app.quality import render_quality_result
from geox_app.windows import cooldown_end, window_label


def _render_result(result, *, title: str, window: str, channel_name: str) -> None:
    st.subheader(title)
    for cell, metrics in result.results.items():
        st.markdown(f"**{cell}**")
        frame = estimate_frame(metrics)
        st.dataframe(frame, width="stretch")
        if metrics.descriptive_metrics and metrics.descriptive_metrics.estimated_bau_spend is not None:
            st.caption(
                f"Estimated BAU spend (cell + control geos, not national): "
                f"{metrics.descriptive_metrics.estimated_bau_spend:,.0f}"
            )
        st.write("Cumulative lift (head)")
        st.dataframe(metrics.cumulative_lift.head(8), width="stretch")
        if metrics.cumulative_icpd is not None:
            st.write("Cumulative iCPD (head)")
            st.dataframe(metrics.cumulative_icpd.head(8), width="stretch")

    render_quality_result(
        result.quality_check_result,
        phase="analysis",
        title=f"Quality checks ({window})",
    )
    st.write("Plots")
    st.caption(
        "These are `geox.plot_analysis` — same function as the Colab. A large "
        "level shift after the test start only appears if **this design’s "
        "treatment geos** are the ones that actually received the intervention "
        "in the panel. The Google sample Colab also excludes geo `105`, uses "
        "`n_candidates=100_000` (library default), and `n_placebo_candidates="
        "100_000` / `n_top_placebos=500`. The app defaults to a smaller search "
        "and placebo pool, so the split (and these charts) will not match Colab "
        "unless you turn on Colab-scale settings on Design and Analysis."
    )
    show_analysis_plots(result)

    payload = experiment_payload(result, window=window, channel_name=channel_name)
    st.markdown("**Meridian ROI priors**")
    st.markdown(
        "You can use the code below if you want to calibrate priors in Meridian "
        "MMM based on this experiment result. It feeds iCPD, spend, and dates into "
        f"[CalibrationBuilder]({PRIORS_DOCS}). Holdback matches Meridian’s "
        "zero-spend ROI estimand better than go-dark/heavy-up."
    )
    st.dataframe(cells_frame(payload), width="stretch")
    snippet = calibration_snippet(payload)
    st.code(snippet, language="python")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download prior JSON",
            data=payload_json(payload),
            file_name=f"meridian_roi_priors_{window}.json",
            mime="application/json",
            key=f"dl_priors_json_{window}",
        )
    with c2:
        st.download_button(
            "Download CalibrationBuilder snippet",
            data=snippet,
            file_name=f"meridian_calibration_{window}.py",
            mime="text/x-python",
            key=f"dl_priors_py_{window}",
        )

st.header("Analysis")
st.caption(
    "Post-test TBR with design-aware placebos. A result is inconclusive if the "
    "confidence interval includes zero. iCPD is iROAS when the KPI is revenue. "
    f"[Data validation and quality checks]({QUALITY_CHECKS_URL}) run on the "
    "**pretest** window only."
)

st.subheader("Design to analyze")
saved = list_saved_designs()
latest = latest_path()
library_labels = {}
if latest is not None:
    library_labels["Latest (from Design page)"] = latest
for path in saved:
    library_labels[path.stem] = path

default_source = "library" if library_labels else "session"
source = st.radio(
    "Load design from",
    options=["library", "session", "upload"],
    index=["library", "session", "upload"].index(default_source),
    format_func=lambda x: {
        "library": "Local library (outputs/designs)",
        "session": "This session (last Design run)",
        "upload": "Upload JSON",
    }[x],
    horizontal=True,
    help="Save a named design on the Design page to reuse it here after a restart.",
)

design = None
if source == "library":
    if not library_labels:
        st.warning("No files in `outputs/designs/` yet. Save a design on the Design page.")
    else:
        pick = st.selectbox(
            "Saved design",
            list(library_labels.keys()),
            help="Named files plus `_latest.json` from the last Design selection.",
        )
        if st.button("Load saved design", icon=":material/folder_open:"):
            design = load_design(library_labels[pick])
            st.session_state.selected_design = design
            st.session_state.design_json = design.export_to_json()
            st.success(f"Loaded {pick}.")
        elif st.session_state.get("selected_design") is not None:
            design = st.session_state.selected_design
elif source == "upload":
    uploaded_json = st.file_uploader(
        "Design JSON",
        type=["json"],
        help="GeoX `Design.export_to_json()` file.",
    )
    if uploaded_json is not None:
        design = geox.Design.load_from_json(uploaded_json.getvalue().decode("utf-8"))
        st.session_state.selected_design = design
        st.session_state.design_json = design.export_to_json()
else:
    design = st.session_state.get("selected_design")
    if design is None and st.session_state.get("design_json"):
        design = geox.Design.load_from_json(st.session_state.design_json)
        st.session_state.selected_design = design

if design is None:
    st.info("Run Design and save to the library, keep this session, or upload JSON.")
    st.stop()

df = st.session_state.get("analysis_df")
if df is None:
    st.info("Save an analysis panel on Data (pretest + test dates).")
    st.stop()

min_d = df["date"].min().date()
max_d = df["date"].max().date()
default_start = pd.Timestamp("2020-04-01").date()
default_end = pd.Timestamp("2020-04-30").date()
if not (min_d <= default_start <= max_d):
    default_end = max_d
    default_start = (pd.Timestamp(max_d) - pd.Timedelta(days=29)).date()
    if default_start < min_d:
        default_start = min_d

c1, c2, c3 = st.columns(3)
with c1:
    start = st.date_input(
        "Analysis start",
        value=default_start,
        help="First day of the in-market test window (inclusive).",
    )
with c2:
    end = st.date_input(
        "Analysis end",
        value=default_end,
        help="Last day of the in-market test window (inclusive). Cooldown days are added below.",
    )
with c3:
    use_pretest_end = st.checkbox(
        "Set pretest end explicitly",
        value=False,
        help="If off, all dates before analysis start are pretest.",
    )
pretest_end = None
if use_pretest_end:
    pretest_end = st.date_input(
        "Pretest end (strictly before start)",
        value=(pd.Timestamp(start) - pd.Timedelta(days=1)).date(),
        help="Must be strictly before analysis start.",
    )

cooldown_days = st.number_input(
    "Cooldown days after test end",
    min_value=0,
    max_value=90,
    value=0,
    step=1,
    help=(
        "GeoX 1.0.0 has no cooldown field. We extend `analysis_end_date` so TBR "
        "treats cooldown days as still-treated vs BAU control. 0 = test window only."
    ),
)
also_cooldown = False
if cooldown_days > 0:
    also_cooldown = st.checkbox(
        "Also estimate test + cooldown (second analyze run)",
        value=True,
        help="Keeps the test-only result and runs a second TBR on the longer window.",
    )

channel_name = st.text_input(
    "Meridian channel name for prior export",
    value="geo_experiment_channel",
    help="Passed into CalibrationBuilder as the paid-media channel to calibrate.",
)

drop_outliers = st.checkbox(
    "Drop pretest outlier dates",
    value=True,
    help="Geos excluded at design time are always dropped. This only affects date outliers.",
)
with st.expander("Placebo search"):
    match_colab_pl = st.checkbox(
        "Colab-scale placebos (100,000 candidates, 500 top)",
        value=False,
        help=(
            "Library / Colab defaults. Much slower. Affects confidence bands; "
            "the pointwise lift still depends on which geos were treated in the design."
        ),
    )
    if match_colab_pl:
        n_pl, n_top = 100_000, 500
        st.caption("Using Colab `n_placebo_candidates=100_000` and `n_top_placebos=500`.")
    else:
        st.caption("Interactive default is 5,000 candidates / 100 top placebos.")
        n_pl = st.number_input(
            "n_placebo_candidates",
            min_value=200,
            max_value=100_000,
            value=5_000,
            step=100,
            help="Design-aware placebo pool size. Colab omits this field (library default 100,000).",
        )
        n_top = st.number_input(
            "n_top_placebos",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            help="How many valid placebos are kept for the null distribution. Colab default 500.",
        )

preview, run = st.columns(2)
with preview:
    do_preview = st.button("Preview quality checks", icon=":material/fact_check:")
with run:
    do_run = st.button("Run analysis", type="primary", icon=":material/play_arrow:")

if do_preview or do_run:
    cfg = analysis_config(
        design,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        pretest_end=pd.Timestamp(pretest_end) if pretest_end is not None else None,
        n_placebo_candidates=int(n_pl),
        n_top_placebos=int(n_top),
    )
    if do_preview:
        try:
            st.session_state.preview_analysis_quality = preview_analysis_quality(
                df,
                cfg,
                exclude_outlier_dates=drop_outliers,
            )
        except Exception as exc:
            st.exception(exc)
    if do_run:
        jobs = [("test_only", pd.Timestamp(end))]
        if cooldown_days > 0 and also_cooldown:
            jobs.append(
                (
                    window_label(include_cooldown=True, cooldown_days=int(cooldown_days)),
                    cooldown_end(end, int(cooldown_days)),
                )
            )
        elif cooldown_days > 0:
            jobs = [
                (
                    window_label(include_cooldown=True, cooldown_days=int(cooldown_days)),
                    cooldown_end(end, int(cooldown_days)),
                )
            ]
        with st.spinner("Analyzing (placebo inference). First JAX compile is slow."):
            try:
                primary = None
                cooldown_result = None
                for label, stop in jobs:
                    result = run_analysis(
                        df,
                        design,
                        start=pd.Timestamp(start),
                        end=stop,
                        pretest_end=pd.Timestamp(pretest_end) if pretest_end is not None else None,
                        exclude_outlier_dates=drop_outliers,
                        n_placebo_candidates=int(n_pl),
                        n_top_placebos=int(n_top),
                    )
                    if label == "test_only":
                        primary = result
                    else:
                        cooldown_result = result
                        if primary is None:
                            primary = result
            except Exception as exc:
                st.exception(exc)
                st.stop()
        st.session_state.analysis_result = primary
        st.session_state.analysis_result_cooldown = cooldown_result
        save_analysis_pickle(primary, name="_latest")
        if cooldown_result is not None:
            save_analysis_pickle(cooldown_result, name="cooldown")

if st.session_state.get("preview_analysis_quality") is not None:
    render_quality_result(
        st.session_state.preview_analysis_quality,
        phase="analysis",
        title="Pre-analysis quality preview",
    )

result = st.session_state.get("analysis_result")
if result is None:
    st.stop()

cfg_dates = result.analysis_config
primary_window = window_label(
    include_cooldown=int(cooldown_days) > 0 and not also_cooldown,
    cooldown_days=int(cooldown_days),
)
_render_result(
    result,
    title=(
        f"Analysis window {pd.Timestamp(cfg_dates.analysis_start_date).date()} → "
        f"{pd.Timestamp(cfg_dates.analysis_end_date).date()}"
    ),
    window=primary_window,
    channel_name=channel_name,
)

cooldown_result = st.session_state.get("analysis_result_cooldown")
if cooldown_result is not None:
    cd_window = window_label(
        include_cooldown=True,
        cooldown_days=int(cooldown_days),
    )
    _render_result(
        cooldown_result,
        title=f"Test + {int(cooldown_days)}-day cooldown",
        window=cd_window,
        channel_name=channel_name,
    )
