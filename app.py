# ===========================================
# app.py — Ndaka Security Command Dashboard
# ===========================================

import streamlit as st
import datetime
import os
import base64
# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Ndaka Security Command Dashboard",
    page_icon="",
    layout="wide",
)

# ---------- LOAD LOGO ----------
logo_path = os.path.join("assets", "logo.png")

# ---------- HEADER ----------
import base64

# ---------- HEADER ----------
def get_base64_logo(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

if os.path.exists(logo_path):
    logo_base64 = get_base64_logo(logo_path)
    st.markdown(
        f"""
        <div style='text-align: center; margin-top: -30px; margin-bottom: 20px;'>
            <img src='data:image/png;base64,{logo_base64}' width='300' alt='Ndaka Security Logo'>
        </div>
        """,
        unsafe_allow_html=True
    )

# Title + Subtitle (centered under logo)
st.markdown(
    """
    <h1 style='text-align: center; color: white;'>
        🚔 Ndaka Security Command Dashboard
    </h1>
    <h4 style='text-align: center; color: #cccccc;'>
        Integrating AI-Powered Vehicle Intelligence, Maps, KPIs & Live Operations
    </h4>
    """,
    unsafe_allow_html=True
)

# Date row (centered)
st.markdown(
    f"<p style='text-align: center; color: #aaaaaa;'>Date: {datetime.date.today().strftime('%A, %d %B %Y')}</p>",
    unsafe_allow_html=True
)

st.markdown("---")


# ---------- KPI CARDS ----------
st.markdown("### 📊 System Overview")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("🚗 Vehicles Analyzed", "56", "+4 since yesterday")
kpi2.metric("🧾 Reports Generated", "8")
kpi3.metric("📍 Active Patrol Areas", "12")
kpi4.metric("🔴 Live Incidents", "3")
kpi5.metric("🤖 Avg AI Confidence", "86%")

st.markdown("---")

# ---------- QUICK ACCESS ----------
st.markdown("### 🧭 Quick Navigation")

col1, col2, col3, col4 = st.columns(4)
col1.page_link("pages/2_Map.py", label="🗺️ Map")
col2.page_link("pages/3_KPI.py", label="📈 KPI Dashboard")
col3.page_link("pages/4_Live_Feed.py", label="🔴 Live Feed")
col4.page_link("pages/5_Vehicle_Intelligence.py", label="🚘 Vehicle Intelligence")

st.markdown("---")

# ---------- SYSTEM OVERVIEW ----------
st.markdown("### 🧠 About This Platform")
st.write("""
The **Ndaka Security Command Dashboard** provides a unified interface for monitoring vehicle-related intelligence,
mapping patrol coverage, viewing performance analytics, and tracking live operational activity in real time.

**Modules:**
- 🚘 **Vehicle Intelligence** — AI-powered vehicle and plate detection.
- 🗺️ **Map** — View operational coverage, offices, and incidents.
- 📈 **KPI Dashboard** — Key metrics and trend analytics.
- 🔴 **Live Feed** — Real-time monitoring of ongoing incidents.
""")

st.info("Use the navigation buttons above to explore each module.")

st.markdown("---")

# ---------- OPTIONAL RECENT ACTIVITY (static sample) ----------
st.markdown("### 🕒 Recent Activity (Sample)")
st.dataframe(
    {
        "Time": [
            "2025-10-06 01:22",
            "2025-10-06 01:58",
            "2025-10-06 02:00",
        ],
        "Event": [
            "Vehicle Detected (Volkswagen Sedan)",
            "Plate BVJ563B Recognized",
            "Vehicle Report Generated",
        ],
        "Source": ["Roboflow", "Plate Recognizer", "PDF Export"],
        "Confidence": ["85.3%", "82.2%", "—"],
    }
)

# ---------- FOOTER ----------
st.markdown("---")
st.caption(
    """
    **Built by Thapelo Raphala**, Data Scientist, 
    **Fortune Makgakga**, Data Analyst
    🧩 *Umuzi x Ndaka Security Project*
    © 2025 Ndaka Security (Pty) Ltd. All Rights Reserved.
    """
)
