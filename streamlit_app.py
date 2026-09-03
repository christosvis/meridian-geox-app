import matplotlib

matplotlib.use("Agg")

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geox_app.state import init_state

st.set_page_config(
    page_title="Meridian GeoX App",
    page_icon=":material/map:",
    layout="wide",
)

init_state()

pages = {
    "Workflow": [
        st.Page("app_pages/data.py", title="Data", icon=":material/upload_file:"),
        st.Page("app_pages/design.py", title="Design", icon=":material/architecture:"),
        st.Page("app_pages/analysis.py", title="Analysis", icon=":material/insights:"),
        st.Page("app_pages/compare.py", title="Compare", icon=":material/compare_arrows:"),
    ]
}

page = st.navigation(pages, position="sidebar")
st.title("Meridian GeoX App")
st.caption("Made by Christos Visvardis · [visvardis.com](https://visvardis.com/)")
page.run()
