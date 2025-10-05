import streamlit as st
import pandas as pd
import datetime as dt
import plotly.express as px
#from app import apply_theme
#apply_theme()

# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(page_title="Ndaka Live Feed", layout="wide")

# --------------------------
# LOAD DATA
# --------------------------
base_path = "assets/data/"
indaka_path = base_path + "ndaka_v2/"

# Incidents
incidents_ops = pd.read_csv(indaka_path + "incidents.csv")
incidents_assets = pd.read_csv(base_path + "incidents.csv")

# Fleet & Fuel
fuel_logs = pd.read_csv(indaka_path + "fuel_logs.csv", parse_dates=["date"])
telemetry = pd.read_csv(indaka_path + "vehicle_telemetry_daily.csv", parse_dates=["date"])

# Strikes
strikes = pd.read_csv(indaka_path + "strike_events.csv", parse_dates=["start", "end"])

# --------------------------
# CLEAN + MERGE INCIDENTS
# --------------------------
incidents_ops["date"] = pd.to_datetime(incidents_ops["date"], errors="coerce")
incidents_assets["date"] = pd.to_datetime(incidents_assets["date"], errors="coerce")

all_incidents = pd.concat([incidents_ops, incidents_assets], ignore_index=True)

# --------------------------
# KPI CALCULATIONS (7-day window)
# --------------------------
today = dt.date.today()
week_ago = today - dt.timedelta(days=7)

recent_incidents = all_incidents[
    (all_incidents["date"].dt.date >= week_ago) & (all_incidents["date"].dt.date <= today)
]

incidents_count = len(recent_incidents)
resolved_count = recent_incidents[
    recent_incidents["status"].str.lower().str.contains("resolved|solved", na=False)
].shape[0]

recent_fuel = fuel_logs[fuel_logs["date"].dt.date >= week_ago]["cost"].sum()
recent_cars = telemetry[telemetry["date"].dt.date >= week_ago]["car_id"].nunique()

# --------------------------
# KPI CARDS
# --------------------------
def kpi_card(title, value, good=True, currency=False):
    color = "#2ecc71" if good else "#e74c3c"  # green/red
    display_value = f"R {value:,.0f}" if currency else f"{value:,}"
    st.markdown(
        f"""
        <div style="background-color:{color}; padding:20px; border-radius:8px; 
                    text-align:center; margin:5px; color:white;">
            <h4>{title}</h4>
            <h2>{display_value}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

st.title("🚨 Live Feed & Risk Layers")

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Incidents (7d)", incidents_count, good=incidents_count < 500)
with col2:
    kpi_card("Resolved (7d)", resolved_count, good=resolved_count > 200)
with col3:
    kpi_card("Fuel Spend (7d)", recent_fuel, currency=True, good=False)
with col4:
    kpi_card("Active Cars (7d)", recent_cars, good=recent_cars > 50)

# --------------------------
# INCIDENT LOG
# --------------------------
st.subheader("Latest Incidents")
latest = all_incidents.sort_values("date", ascending=False).head(10)

def color_status(val):
    if isinstance(val, str):
        if "resolved" in val.lower() or "solved" in val.lower():
            return "background-color: #2ecc71; color: white;"
        elif "escalated" in val.lower() or "in progress" in val.lower() or "open" in val.lower():
            return "background-color: #e74c3c; color: white;"
        elif "investigation" in val.lower() or "reported" in val.lower():
            return "background-color: #95a5a6; color: white;"
    return ""

st.dataframe(
    latest[["date", "province", "incident_type", "status", "severity"]]
    .style.applymap(color_status, subset=["status"])
)

# --------------------------
# STRIKES
# --------------------------
st.subheader("Strikes")

active_strikes = strikes[
    (strikes["start"].dt.date <= today) & (strikes["end"].dt.date >= today)
]

if active_strikes.empty:
    st.info("No active or upcoming strikes in the next 7 days.")
else:
    st.dataframe(active_strikes)

# --------------------------
# FLEET TELEMETRY
# --------------------------
st.subheader("Fleet Telemetry")

today_telemetry = telemetry[telemetry["date"].dt.date == today]

if today_telemetry.empty:
    latest_date = telemetry["date"].max().date()
    st.warning(f"No telemetry for today. Showing latest available date: {latest_date}")
    today_telemetry = telemetry[telemetry["date"].dt.date == latest_date]

total_day = today_telemetry["km_day"].sum()
total_night = today_telemetry["km_night"].sum()

st.metric("Total Day KM", f"{total_day:,.1f} km")
st.metric("Total Night KM", f"{total_night:,.1f} km")

today_telemetry["total_km"] = today_telemetry["km_day"] + today_telemetry["km_night"]
top_cars = today_telemetry.sort_values("total_km", ascending=False).head(5)
st.dataframe(top_cars[["car_id", "km_day", "km_night", "total_km"]])
