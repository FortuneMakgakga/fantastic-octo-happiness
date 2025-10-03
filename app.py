import streamlit as st

# Load custom CSS
#with open("assets/style.css") as f:
    #st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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
