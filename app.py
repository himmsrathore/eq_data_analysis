"""Emergency Quota (HO / EQ) Analysis - Indian Railways 2025-26. Two screens:

  1. EQ Utilization        - month x train x class and day x train (views/eq_utilization.py)
  2. Class-wise Day Analysis - day x train x class from the HO Quota Report (views/class_daywise.py)

Run:
    python -m streamlit run app.py
"""
import streamlit as st

from common import inject_css

st.set_page_config(page_title="Emergency Quota Analysis", layout="wide")
inject_css()

nav = st.navigation(
    [
        st.Page("views/eq_utilization.py", title="EQ Utilization", icon=":material/insights:", default=True),
        st.Page("views/class_daywise.py", title="Class-wise Day Analysis", icon=":material/calendar_view_month:",
                url_path="class-daywise"),
    ],
    position="top",
)
nav.run()
