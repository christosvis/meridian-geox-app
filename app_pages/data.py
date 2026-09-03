import streamlit as st

from geox_app.data import (
    apply_mapping,
    guess_column,
    load_csv,
    load_sample,
    panel_summary,
)
from geox_app.help_text import STUDY_TYPE_HELP, TYPES_OF_EXPERIMENTS_URL
from geox_app.state import clear_downstream_of_data

st.header("Data")
st.caption(
    "Pretest panel for design (at least ~3× test length). Analysis needs pretest "
    "**plus** the test window. Columns: `date`, `location`, `conversions`; "
    "`spend` for go-dark / heavy-up; `spend_cell_1`, `spend_cell_2`, … for multi-cell."
)

mode = st.segmented_control(
    "Study type",
    options=["single", "multi"],
    format_func=lambda x: "Single cell" if x == "single" else "Multi cell",
    key="study_mode",
    help="Single cell is more powerful for one tactic. Multi-cell shares one control across arms.",
)
if mode is None:
    mode = "single"

st.info(
    f"{STUDY_TYPE_HELP[mode]} "
    f"[Types of experiments]({TYPES_OF_EXPERIMENTS_URL})"
)

n_cells = 1
if mode == "multi":
    n_cells = st.number_input(
        "Number of treatment cells",
        min_value=2,
        max_value=4,
        value=2,
        step=1,
        key="n_cells",
        help="Each cell is a treatment arm. All arms share one control group.",
    )

st.divider()


def _map_panel(raw, key_prefix: str, n_cells: int, mode: str):
    cols = list(raw.columns)
    none_opts = ["(none)"] + cols
    date_col = st.selectbox(
        "Date",
        cols,
        index=max(0, cols.index(guess_column(cols, "date") or cols[0])),
        key=f"{key_prefix}_date",
        help="Daily date column (`YYYY-MM-DD`).",
    )
    loc_col = st.selectbox(
        "Location",
        cols,
        index=max(0, cols.index(guess_column(cols, "location", "geo", "city") or cols[0])),
        key=f"{key_prefix}_loc",
        help="Geo unit (city, DMA, etc.). Must match between design and analysis.",
    )
    conv_col = st.selectbox(
        "Conversions / KPI",
        cols,
        index=max(
            0,
            cols.index(
                guess_column(cols, "conversions", "conversion", "gov", "revenue")
                or cols[0]
            ),
        ),
        key=f"{key_prefix}_conv",
        help="Business-as-usual outcome (conversions or revenue). Shared across cells in multi-cell.",
    )
    spend_col = None
    spend_cells = {}
    if mode == "single":
        guess = guess_column(cols, "spend")
        spend_choice = st.selectbox(
            "Spend (optional; required for go-dark / heavy-up)",
            none_opts,
            index=none_opts.index(guess) if guess else 0,
            key=f"{key_prefix}_spend",
            help="Historical campaign spend in each geo. Holdback can omit this.",
        )
        if spend_choice != "(none)":
            spend_col = spend_choice
    else:
        for i in range(1, int(n_cells) + 1):
            cell = f"cell_{i}"
            guess = guess_column(cols, f"spend_cell_{i}", "spend")
            choice = st.selectbox(
                f"Spend {cell} (optional)",
                none_opts,
                index=none_opts.index(guess) if guess in none_opts else 0,
                key=f"{key_prefix}_spend_{cell}",
                help=(
                    "Spend for this cell’s intervention. Same values across cells if "
                    "they modify one campaign; different columns if they are different publishers."
                ),
            )
            if choice != "(none)":
                spend_cells[cell] = choice
    mapped = apply_mapping(
        raw,
        date_col=date_col,
        location_col=loc_col,
        conversions_col=conv_col,
        spend_col=spend_col,
        spend_cell_cols=spend_cells or None,
    )
    return mapped


tab_design, tab_analysis = st.tabs(["Design panel (pretest)", "Analysis panel (pre + test)"])

with tab_design:
    src = st.segmented_control(
        "Source",
        options=["sample", "upload"],
        format_func=lambda x: "Google sample" if x == "sample" else "Upload CSV",
        key="design_src_ctrl",
        help="Google Colab sample, or your own geo-day CSV.",
    )
    raw = None
    if src in (None, "sample"):
        kind = "single_design" if mode == "single" else "multi_design"
        st.write(
            "Google Colab design CSV. Sample holdback uses `spend`; multi-cell sample "
            "is go-dark + heavy-up with `spend_cell_1` / `spend_cell_2`."
        )
        if st.button("Load design sample", type="primary", icon=":material/dataset:"):
            raw = load_sample(kind)
            st.session_state["_design_raw"] = raw
            st.session_state.design_source = kind
            clear_downstream_of_data()
        raw = st.session_state.get("_design_raw")
    else:
        uploaded = st.file_uploader("Design CSV", type=["csv"], key="design_upload")
        if uploaded is not None:
            raw = load_csv(uploaded)
            st.session_state["_design_raw"] = raw
            st.session_state.design_source = "upload"
            clear_downstream_of_data()
        else:
            raw = st.session_state.get("_design_raw")

    if raw is None:
        st.info("Load a sample or upload a CSV.")
    else:
        st.dataframe(raw.head(8), width="stretch")
        mapped = _map_panel(raw, "design", n_cells, mode)
        if st.button("Save design panel", icon=":material/check:", key="save_design_panel"):
            st.session_state.design_df = mapped
            clear_downstream_of_data()
            st.success("Design panel saved. Open Design to run `run_design`.")
        if st.session_state.design_df is not None:
            s = panel_summary(st.session_state.design_df)
            st.metric("Geos", f"{s['geos']:,}")
            c1, c2, c3 = st.columns(3)
            c1.caption(f"{s['rows']:,} rows · {s['dates']} dates")
            c2.caption(f"{s['start'].date()} → {s['end'].date()}")
            c3.caption(f"KPI nulls: {s['conversion_nulls']}")

with tab_analysis:
    src_a = st.segmented_control(
        "Source",
        options=["sample", "upload"],
        format_func=lambda x: "Google sample" if x == "sample" else "Upload CSV",
        key="analysis_src_ctrl",
        help="Must include pretest and the test window used on the Analysis page.",
    )
    raw_a = None
    if src_a == "sample":
        kind = "single_analysis" if mode == "single" else "multi_analysis"
        st.write(
            "Google analysis CSV includes pretest and the test window "
            "(sample test: 2020-04-01 to 2020-04-30)."
        )
        if st.button("Load analysis sample", type="primary", icon=":material/dataset:", key="load_an"):
            raw_a = load_sample(kind)
            st.session_state["_analysis_raw"] = raw_a
            st.session_state.analysis_source = kind
            st.session_state.analysis_result = None
            st.session_state.analysis_df = None
        raw_a = st.session_state.get("_analysis_raw")
    else:
        uploaded_a = st.file_uploader("Analysis CSV", type=["csv"], key="analysis_upload")
        if uploaded_a is not None:
            raw_a = load_csv(uploaded_a)
            st.session_state["_analysis_raw"] = raw_a
            st.session_state.analysis_source = "upload"
            st.session_state.analysis_result = None
        else:
            raw_a = st.session_state.get("_analysis_raw")

    if raw_a is None:
        st.info("Load the post-test panel when you are ready to analyze.")
    else:
        st.dataframe(raw_a.head(8), width="stretch")
        mapped_a = _map_panel(raw_a, "analysis", n_cells, mode)
        if st.button("Save analysis panel", icon=":material/check:", key="save_an_panel"):
            st.session_state.analysis_df = mapped_a
            st.session_state.analysis_result = None
            st.success("Analysis panel saved.")
        if st.session_state.analysis_df is not None:
            s = panel_summary(st.session_state.analysis_df)
            st.caption(
                f"{s['geos']:,} geos · {s['start'].date()} → {s['end'].date()} · "
                f"{s['rows']:,} rows"
            )
