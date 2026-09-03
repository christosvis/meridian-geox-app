"""Render GeoX QualityCheckResult the same way as the Colab."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from geox_app.help_text import QUALITY_INTRO


def render_quality_result(qc, *, phase: str, title: str | None = None) -> None:
    st.subheader(title or "Quality checks")
    st.caption(
        f"{phase.capitalize()} phase — same object as Colab "
        f"`selected_design.quality_check_result` / `analysis_result.quality_check_result`."
    )
    with st.expander("What these checks do"):
        st.markdown(QUALITY_INTRO)

    if qc is None:
        st.info("No quality check result available.")
        return

    geos = sorted(qc.outlier_geos) if qc.outlier_geos else []
    dates = sorted(qc.outlier_dates) if qc.outlier_dates else []
    c1, c2 = st.columns(2)
    c1.metric("Outlier geos", "none" if not geos else str(len(geos)))
    c2.metric("Outlier dates", "none" if not dates else str(len(dates)))
    if geos:
        st.write("Outlier geos")
        st.dataframe(pd.DataFrame({"location": geos}), width="stretch")
    if dates:
        st.write("Outlier dates")
        st.dataframe(
            pd.DataFrame({"date": [pd.Timestamp(d).date() for d in dates]}),
            width="stretch",
        )

    metrics = qc.quality_metrics
    if metrics is None or metrics.empty:
        st.success("No data quality issues identified.")
        return
    st.dataframe(metrics, width="stretch")
