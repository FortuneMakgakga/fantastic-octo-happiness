import streamlit as st
import pandas as pd
import plotly.express as px
import datetime as dt
#from app import apply_theme
#apply_theme()



# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(page_title="Ndaka KPI Dashboard", layout="wide")
# --------------------------
# LOAD DATA
# --------------------------
base_path = "assets/data/"
indaka_path = base_path + "ndaka_v2/"

# Incidents
incidents_ops = pd.read_csv(indaka_path + "incidents.csv")
incidents_assets = pd.read_csv(base_path + "incidents.csv")

# Fleet & Fuel
fleet = pd.read_csv(indaka_path + "fleet.csv")
fuel_logs = pd.read_csv(indaka_path + "fuel_logs.csv", parse_dates=["date"])
telemetry = pd.read_csv(indaka_path + "vehicle_telemetry_daily.csv", parse_dates=["date"])

# Business Assets
assets = pd.read_csv(base_path + "assets.csv")
properties = pd.read_csv(base_path + "properties.csv")

# --------------------------
# CLEAN + MERGE
# --------------------------
# Normalize dates
incidents_ops["date"] = pd.to_datetime(incidents_ops["date"], errors="coerce")
incidents_assets["date"] = pd.to_datetime(incidents_assets["date"], errors="coerce")

# Merge incidents
all_incidents = pd.concat([incidents_ops, incidents_assets], ignore_index=True)

# KPI Calculations
total_incidents = len(all_incidents)
resolved_incidents = all_incidents[all_incidents["status"].str.lower().str.contains("resolved")].shape[0]
resolved_rate = (resolved_incidents / total_incidents) * 100 if total_incidents > 0 else 0

active_cars = telemetry["car_id"].nunique()
total_cars = fleet["car_id"].nunique()

total_fuel_spend = fuel_logs["cost"].sum()
assets_value = assets["insured_value"].sum()

# Trend vs last month
today = dt.date.today()
this_month = today.month
last_month = (today - pd.DateOffset(months=1)).month

this_month_incidents = all_incidents[all_incidents["date"].dt.month == this_month].shape[0]
last_month_incidents = all_incidents[all_incidents["date"].dt.month == last_month].shape[0]

incident_trend = "▲" if this_month_incidents > last_month_incidents else "▼"

# --------------------------
# KPI CARDS (Top Row)
# --------------------------
def kpi_card(title, value, trend=None, good=True, currency=False):
    color = "green" if good else "red"
    display_value = f"R {value:,.0f}" if currency else f"{value:,.0f}" if isinstance(value,(int,float)) else value
    st.markdown(
        f"""
        <div style="background-color:{color}; padding:20px; border-radius:8px; text-align:center; margin:5px; color:white;">
            <h4>{title}</h4>
            <h2>{display_value} {trend if trend else ""}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

st.title("📊 KPI Dashboard")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    kpi_card("Total Incidents", total_incidents, trend=incident_trend, good=this_month_incidents <= last_month_incidents)
with col2:
    kpi_card("Resolved Rate", f"{resolved_rate:.1f}%", good=resolved_rate >= 50)
with col3:
    kpi_card("Active Fleet", f"{active_cars}/{total_cars}", good=active_cars/total_cars >= 0.8)
with col4:
    kpi_card("Total Fuel Spend", total_fuel_spend, currency=True, good=False) # show red by default
with col5:
    kpi_card("Assets Protected Value", assets_value, currency=True, good=True)

# --------------------------
# INCIDENTS OVERVIEW
# --------------------------
st.subheader("Incidents Overview")

col6, col7 = st.columns(2)

# By Type
if "incident_type" in all_incidents.columns:
    incidents_by_type = all_incidents["incident_type"].value_counts().reset_index()
    incidents_by_type.columns = ["Incident Type", "Count"]
    fig_type = px.bar(incidents_by_type, x="Incident Type", y="Count", title="Incidents by Type", text_auto=True)
    col6.plotly_chart(fig_type, use_container_width=True)

# By Severity
if "severity" in all_incidents.columns:
    severity_split = all_incidents["severity"].value_counts().reset_index()
    severity_split.columns = ["Severity", "Count"]
    fig_severity = px.pie(severity_split, names="Severity", values="Count", title="Incident Severity Split")
    col7.plotly_chart(fig_severity, use_container_width=True)

# --------------------------
# RISK DIMENSIONS
# --------------------------
st.subheader("Risk by Sector and Province")

col8, col9 = st.columns(2)

# By Sector
if "sector" in all_incidents.columns:
    sector_counts = all_incidents["sector"].value_counts().reset_index()
    sector_counts.columns = ["Sector", "Count"]
    fig_sector = px.bar(sector_counts, x="Sector", y="Count", title="Incidents by Sector", text_auto=True)
    col8.plotly_chart(fig_sector, use_container_width=True)

# By Province
if "province" in all_incidents.columns:
    prov_counts = all_incidents["province"].value_counts().reset_index()
    prov_counts.columns = ["Province", "Count"]
    fig_prov = px.bar(prov_counts, x="Province", y="Count", title="Incidents by Province", text_auto=True)
    col9.plotly_chart(fig_prov, use_container_width=True)

# --------------------------
# FLEET & FUEL
# --------------------------
st.subheader("Fleet & Fuel Metrics")

col10, col11 = st.columns(2)

# Fuel Spend Over Time
fuel_logs["week"] = fuel_logs["date"].dt.to_period("W").apply(lambda r: r.start_time)
weekly_fuel = fuel_logs.groupby("week")["cost"].sum().reset_index()
fig_fuel = px.line(weekly_fuel, x="week", y="cost", title="Fuel Spend Over Time", markers=True)
col10.plotly_chart(fig_fuel, use_container_width=True)

# Avg km/day vs km/night
if not telemetry.empty:
    avg_km = telemetry[["km_day", "km_night"]].mean()
    col11.metric("Avg KM (Day)", f"{avg_km['km_day']:.1f} km")
    col11.metric("Avg KM (Night)", f"{avg_km['km_night']:.1f} km")

# --------------------------
# ASSETS AT RISK (use richer dataset only)
# --------------------------
# st.subheader("Top 5 High-Value Properties with Most Incidents")

# # Clean column names
# incidents_assets.columns = incidents_assets.columns.str.strip().str.lower()
# properties.columns = properties.columns.str.strip().str.lower()
# assets.columns = assets.columns.str.strip().str.lower()

# # Use root incidents dataset for property/asset linkage
# if "property_id" in incidents_assets.columns:
#     inc_props = incidents_assets.merge(properties, on="property_id", how="left") \
#                                 .merge(assets, on="property_id", how="left")

#     if not inc_props.empty:
#         risky_props = (
#             inc_props.groupby(["property_id", "property_name", "province"], dropna=False)
#             .agg(incidents=("id","count"), insured_value=("insured_value","sum"))
#             .reset_index()
#             .sort_values(by=["insured_value","incidents"], ascending=False)
#             .head(5)
#         )

#         st.dataframe(risky_props)
#     else:
#         st.info("No property-linked incidents available yet.")

# --------------------------
# FOOTER
# --------------------------
st.markdown("---")
st.markdown("Developed by Xcorp | Data Source: Ndaka Operations & Assets Data")