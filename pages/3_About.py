import streamlit as st
from app import apply_theme
#apply_theme()

st.title("ℹ️ About this Dashboard")
st.markdown("---")

st.write(
    """
    This dashboard is built with **Streamlit** to provide a Power BI-style interface.  

    **Features planned:**
    - Live KPI tracking  
    - Maps with patrol areas  
    - Incident reporting & uploads  
    - ML model integration for predictions  
    """
)
