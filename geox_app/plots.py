"""Show GeoX matplotlib figures in Streamlit."""

from __future__ import annotations

import matplotlib.pyplot as plt
import meridian_geox as geox
import streamlit as st


def show_design_plots(design: geox.Design) -> None:
    plt.close("all")
    geox.plot_design(design)
    for num in plt.get_fignums():
        fig = plt.figure(num)
        st.pyplot(fig, width="stretch")
    plt.close("all")


def show_analysis_plots(result: geox.AnalysisResult) -> None:
    plt.close("all")
    geox.plot_analysis(result)
    for num in plt.get_fignums():
        fig = plt.figure(num)
        st.pyplot(fig, width="stretch")
    plt.close("all")
