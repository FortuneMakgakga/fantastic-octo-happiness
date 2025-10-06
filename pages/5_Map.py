import os, csv, json, datetime as dt
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import MarkerCluster, HeatMap

# --- Page config ---
st.set_page_config(page_title="Ndaka – Map & Assets", layout="wide")

# --- Data paths ---
DATA_DIR = "assets/data"
DATA_OFF_DIR="assets/data/ndaka_v2"
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.csv")
PROPERTIES_FILE = os.path.join(DATA_DIR, "properties.csv")
ASSETS_FILE = os.path.join(DATA_DIR, "assets.csv")
INCIDENTS_FILE = os.path.join(DATA_DIR, "incidents.csv")
COVERAGE_FILE = os.path.join(DATA_DIR, "coverage.geojson")
OFFICES_FILE = os.path.join(DATA_OFF_DIR, "offices.csv")  # NEW

# --- Load Data ---
clients_df = pd.read_csv(CLIENTS_FILE)
properties_df = pd.read_csv(PROPERTIES_FILE)
assets_df = pd.read_csv(ASSETS_FILE)
incidents_df = pd.read_csv(INCIDENTS_FILE)
offices_df = pd.read_csv(OFFICES_FILE)  # NEW

# Light clean on offices (handle stray spaces / ensure numeric)
offices_df["province"] = offices_df["province"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
offices_df["latitude"] = pd.to_numeric(offices_df["latitude"], errors="coerce")
offices_df["longitude"] = pd.to_numeric(offices_df["longitude"], errors="coerce")

# Clean incident dates
incidents_df["date"] = pd.to_datetime(incidents_df["date"], errors="coerce")
incidents_df["dt"] = pd.to_datetime(
    incidents_df["date"].dt.strftime("%Y-%m-%d") + " " + incidents_df["time"].fillna("00:00"),
    errors="coerce"
)

# --- Load coverage ---
coverage_geojson = None
if os.path.exists(COVERAGE_FILE):
    with open(COVERAGE_FILE, "r", encoding="utf-8") as f:
        coverage_geojson = json.load(f)

# --- Layout ---
st.title("🗺️ Ndaka Security – Operations, Offices, Assets & Incidents")

left, right = st.columns([2, 1])

# --- Right panel: KPIs + filters ---
with right:
    st.subheader("🎯 Operations Overview")
    st.metric("Total Offices", len(offices_df))
    st.metric("Total Clients", len(clients_df))
    st.metric("Properties", len(properties_df))
    st.metric("Assets", len(assets_df))

    st.markdown("---")
    st.subheader("🔎 Filters")

    provinces = ["All"] + sorted(incidents_df["province"].dropna().unique().tolist())
    province = st.selectbox("Province", provinces, 0)

    towns = ["All"] + sorted(incidents_df["town"].dropna().unique().tolist())
    town = st.selectbox("Town", towns, 0)

    types = ["All"] + sorted(incidents_df["incident_type"].dropna().unique().tolist())
    itype = st.selectbox("Incident type", types, 0)

    statuses = ["All"] + sorted(incidents_df["status"].dropna().unique().tolist())
    status = st.selectbox("Status", statuses, 0)

    st.markdown("---")
    st.subheader("🗂️ Map Layers")
    show_offices = st.checkbox("Show Offices", True)     # NEW
    show_props   = st.checkbox("Show Properties", True)
    show_assets  = st.checkbox("Show Assets", True)
    show_incidents = st.checkbox("Show Incidents", True)
    show_heat    = st.checkbox("Show Heatmap", True)
    show_cov     = st.checkbox("Show Coverage", True)

# --- Apply filters (incidents) ---
idf = incidents_df.copy()
if province != "All":
    idf = idf[idf["province"] == province]
if town != "All":
    idf = idf[idf["town"] == town]
if itype != "All":
    idf = idf[idf["incident_type"] == itype]
if status != "All":
    idf = idf[idf["status"] == status]

# --- Map ---
with left:
    m = folium.Map(location=[-28.5, 24.7], zoom_start=6, tiles="cartodbpositron")

    # 🏢 Offices layer
    if show_offices:
        office_group = folium.FeatureGroup(name="Offices", show=True)
        offices_filtered = offices_df.copy()
        if province != "All":
            offices_filtered = offices_filtered[offices_filtered["province"] == province]

        for _, o in offices_filtered.iterrows():
            if pd.isna(o["latitude"]) or pd.isna(o["longitude"]):
                continue
            # Highlight HQ
            if "HQ" in str(o["office_name"]) or str(o["office_id"]).upper() == "NDK-JHB":
                folium.Marker(
                    [o["latitude"], o["longitude"]],
                    icon=folium.Icon(color="lightgray", icon="star", prefix="fa"),
                    tooltip=f"🏆 {o['office_name']} – Headquarters",
                    popup=(f"<b>🏆 {o['office_name']}</b><br>"
                           f"Office ID: {o['office_id']}<br>"
                           f"Province: {o['province']}<br>"
                           f"City: {o['city']}")
                ).add_to(office_group)
            else:
                folium.Marker(
                    [o["latitude"], o["longitude"]],
                    icon=folium.Icon(color="purple", icon="building", prefix="fa"),
                    tooltip=f"{o['office_name']} – {o['city']}",
                    popup=(f"<b>{o['office_name']}</b><br>"
                           f"Office ID: {o['office_id']}<br>"
                           f"Province: {o['province']}<br>"
                           f"City: {o['city']}")
                ).add_to(office_group)
        office_group.add_to(m)

    # 🏠 Properties layer
    if show_props:
        prop_group = folium.FeatureGroup(name="Properties", show=True)
        props_filtered = properties_df.copy()
        if province != "All":
            props_filtered = props_filtered[props_filtered["province"] == province]
        for _, pr in props_filtered.iterrows():
            folium.Marker(
                [pr["lat"], pr["lon"]],
                icon=folium.Icon(color="blue", icon="home", prefix="fa"),
                tooltip=f"{pr['property_name']} – {pr['town']}",
                popup=(f"<b>{pr['property_name']}</b><br>"
                       f"Sector: {pr['sector']}<br>"
                       f"Town: {pr['town']}<br>"
                       f"Notes: {pr['notes']}")
            ).add_to(prop_group)
        prop_group.add_to(m)

    # 💼 Assets layer
    if show_assets:
        asset_group = folium.FeatureGroup(name="Assets", show=True)
        color_map = {"High": "red", "Medium": "orange", "Low": "green"}
        assets_filtered = assets_df.copy()
        if province != "All":
            assets_filtered = assets_filtered.merge(
                properties_df[["property_id", "province"]], on="property_id", how="left"
            )
            assets_filtered = assets_filtered[assets_filtered["province"] == province]
        for _, a in assets_filtered.iterrows():
            pr = properties_df[properties_df["property_id"] == a["property_id"]].iloc[0]
            color = color_map.get(a["criticality"], "purple")
            folium.CircleMarker(
                [pr["lat"], pr["lon"]],
                radius=7 if a["criticality"] == "High" else 5 if a["criticality"] == "Medium" else 4,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=(f"<b>{a['asset_type']}</b><br>"
                       f"Criticality: {a['criticality']}<br>"
                       f"Insured Value: R{a['insured_value']:,}<br>"
                       f"Property: {pr['property_name']}")
            ).add_to(asset_group)
        asset_group.add_to(m)

    # 🚨 Incidents
    if show_incidents and not idf.empty:
        cl = MarkerCluster(name="Incidents")
        for _, r in idf.iterrows():
            color = "red" if r["severity"] == "High" else ("orange" if r["severity"] in ["Medium", "Semi-High"] else "green")
            folium.CircleMarker(
                [r["lat"], r["lon"]],
                radius=6,
                color=color,
                fill=True,
                fill_opacity=0.8,
                popup=(f"<b>{r['title']}</b><br>"
                       f"{r['town']}, {r['province']}<br>"
                       f"Status: {r['status']}<br>"
                       f"Notes: {r['notes']}<br>"
                       f"Sector: {r['sector']}")
            ).add_to(cl)
        cl.add_to(m)

    # 🔥 Heatmap
    if show_heat and not idf.empty:
        pts = idf[["lat", "lon"]].dropna().values.tolist()
        if len(pts) > 1:
            HeatMap(pts, radius=20, blur=15, name="Heatmap").add_to(m)

    # 🧭 Coverage (province-based filtering)
    if show_cov and coverage_geojson:
        coverage_group = folium.FeatureGroup(name="Coverage Area", show=True)
        filtered_features = []
        if province != "All":
            for feature in coverage_geojson["features"]:
                if feature["properties"].get("province") == province:
                    filtered_features.append(feature)
        else:
            filtered_features = coverage_geojson["features"]

        folium.GeoJson(
            {"type": "FeatureCollection", "features": filtered_features},
            name="Coverage Area",
            style_function=lambda x: {
                "fillColor": "#0078FF33",
                "color": "#004080",
                "weight": 2,
                "fillOpacity": 0.25
            },
            tooltip=folium.GeoJsonTooltip(fields=["province"], aliases=["Province:"])
        ).add_to(coverage_group)
        coverage_group.add_to(m)

    # 🧩 Layer control
    folium.LayerControl(collapsed=False, position="topright").add_to(m)
    st_folium(m, width=None, height=700)

# --- Incident Feed (RIGHT) ---
with right:
    st.subheader("📰 Recent Incidents")
    for _, r in idf.sort_values("dt", ascending=False).head(5).iterrows():
        st.markdown(
            f"""
**{r['title']}** – {r['status']} ({r['severity']})  
📍 {r['town']}, {r['province']}  
🕒 {r['date']} {r['time']}  
*{r['notes']}*
            """
        )

    st.markdown("---")
    st.subheader("➕ Add New Incident")

    with st.form("incident_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Title", "")
            sector = st.selectbox("Sector", [
                "Retail", "Commercial", "Industrial", "Governmental", "Residential",
                "Community", "VIP", "Strikes & Crowd Control", "Transit Incident"
            ])
            incident_type = st.text_input("Incident type", "Robbery")
            severity = st.selectbox("Severity", ["Low", "Medium", "Semi-High", "High"])
            status = st.selectbox("Status", [
                "Reported", "Under investigation", "In pursuit", "Open", "Searching", "Solved"
            ])
        with col2:
            province = st.text_input("Province", "Gauteng")
            town = st.text_input("Town", "Roodepoort")
            date = st.date_input("Date", dt.date.today())
            time = st.time_input("Time", dt.datetime.now().time().replace(second=0, microsecond=0))
            lat = st.number_input("Latitude", value=-26.136, format="%.6f")
            lon = st.number_input("Longitude", value=27.875, format="%.6f")
        notes = st.text_area("Notes", "Short description of incident")
        submitted = st.form_submit_button("Save Incident")

    if submitted:
        if not incidents_df.empty:
            new_id = int(incidents_df["id"].max()) + 1
        else:
            new_id = 1001
        OPERATING_PROVINCES = {"Gauteng", "Free State", "Mpumalanga", "North West", "Limpopo"}
        is_transit = province not in OPERATING_PROVINCES
        new_row = [
            new_id, title, sector, province, town, incident_type, severity, status,
            date.strftime("%Y-%m-%d"),
            time.strftime("%H:%M"),
            float(lat), float(lon),
            "", is_transit, notes
        ]
        with open(INCIDENTS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(new_row)
        st.success(f"✅ Incident '{title}' saved with ID {new_id}. Refresh to see it on the map.")

# --- Stakeholder Notes ---
with st.expander("ℹ️ Key Stakeholders & Functions"):
    st.markdown("""
- **Revona Govender (SHEQ Manager)** → Use KPIs + incident filters to monitor safety & compliance.  
- **Ntombi Sobayeni (Training & Transformation Manager)** → Track incident trends for staff training priorities.  
- **Thapelo Raphala (Data Scientist)** → Build predictive models (heatmaps, hotspot forecasting).  
- **Fortune Makgaka (Data Analyst)** → Drive dashboard insights & incident reporting.  
- **Executives/Clients** → View transparent coverage, assets, and incidents for decision-making & trust.
    """)
# -----------------------------
