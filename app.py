import streamlit as st

# Load custom CSS
#with open("assets/style.css") as f:
    #st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

import streamlit as st
import plotly.io as pio
import plotly.express as px

#------------------------------------------------------------------------------
# THEME MANAGEMENT
#import streamlit as st
#import plotly.io as pio

#def apply_theme():
#    """Apply global light/dark theme styling and configure Plotly templates."""
#    theme = st.session_state.get("theme", "Dark")
#
#    if theme == "Dark":
#        # -----------------------------
#        # STREAMLIT UI
#        # -----------------------------
#        st.markdown(
#            """
#            <style>
#            .stApp {
#                background-color: #1e1e1e;
#                color: white;
#            }
#            [data-testid="stSidebar"] {
#                background-color: #2b2b2b;
#                color: white;
#            }
#            h1, h2, h3, h4, h5, h6, p, span, div {
#                color: white !important;
#            }
#            .stMetric, .stDataFrame, .stPlotlyChart {
#                color: white;
#            }
#            </style>
#            """,
#            unsafe_allow_html=True,
#        )
#
#        # -----------------------------
#        # PLOTLY CONFIG (Dark Theme)
#        # -----------------------------
#        pio.templates.default = "plotly_dark"
#        pio.templates["custom_dark"] = pio.templates["plotly_dark"]
#        pio.templates["custom_dark"].layout.update(
#            paper_bgcolor="#1e1e1e",
#            plot_bgcolor="#1e1e1e",
#            font=dict(color="white", size=14),
#            title=dict(font=dict(color="white")),
#        )
#
#    else:
#        # -----------------------------
#        # STREAMLIT UI
#        # -----------------------------
#        st.markdown(
#            """
#            <style>
#            .stApp {
#                background-color: #f4f4f4;
#                color: #1c1c1c;
#            }
#            [data-testid="stSidebar"] {
#                background-color: #ffffff;
#                color: black;
#            }
#            h1, h2, h3, h4, h5, h6, p, span, div {
#                color: #1c1c1c !important;
#            }
#            </style>
#            """,
#            unsafe_allow_html=True,
#        )
#
#        # -----------------------------
#        # PLOTLY CONFIG (Light Theme)
#        # -----------------------------
#        pio.templates.default = "plotly_white"
#        pio.templates["custom_light"] = pio.templates["plotly_white"]
#        pio.templates["custom_light"].layout.update(
#            paper_bgcolor="#f4f4f4",
#            plot_bgcolor="#f4f4f4",
#            font=dict(color="#1c1c1c", size=14),
#            title=dict(font=dict(color="#1c1c1c")),
#        )
#
## Initialize session state for theme
## Initialize theme in session
#if "theme" not in st.session_state:
#    st.session_state["theme"] = "Dark"
#
#st.sidebar.write("### 🌓 Theme Switcher")
#theme_choice = st.sidebar.radio(
#    "Choose theme:", ["Dark", "Light"],
#    index=0 if st.session_state["theme"] == "Dark" else 1
#)
#st.session_state["theme"] = theme_choice
#
## Apply global styles + Plotly themes
#apply_theme()
#------------------------------------------------------------------------------


# Sidebar
st.sidebar.image("assets/logo.png", width=120)
st.sidebar.title("Navigation")
st.sidebar.markdown("Use the menu to switch pages ➡️")

# Landing Page
st.markdown('<div class="landing-container">', unsafe_allow_html=True)

st.title("📊 PowerBI-Style Streamlit Dashboard")
st.markdown("---")

st.subheader("Welcome")
st.write(
    """
    This is a placeholder dashboard built in **Streamlit**, styled to look closer
    to **Power BI reports**.  

    Navigate on the left to view:
    - Overview
    - Reports
    - About
    """
)

st.markdown("### Key Metrics")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="kpi-card"><h3>Total Incidents</h3><p>1,245</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="kpi-card"><h3>Resolved Cases</h3><p>980</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="kpi-card"><h3>Active Patrols</h3><p>34</p></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # Close landing-container
