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
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.csv")
PROPERTIES_FILE = os.path.join(DATA_DIR, "properties.csv")
ASSETS_FILE = os.path.join(DATA_DIR, "assets.csv")
INCIDENTS_FILE = os.path.join(DATA_DIR, "incidents.csv")
COVERAGE_FILE = os.path.join(DATA_DIR, "coverage.geojson")

# --- Load Data ---
clients_df = pd.read_csv(CLIENTS_FILE)
properties_df = pd.read_csv(PROPERTIES_FILE)
assets_df = pd.read_csv(ASSETS_FILE)
incidents_df = pd.read_csv(INCIDENTS_FILE)

# Clean incident dates
incidents_df["date"] = pd.to_datetime(incidents_df["date"], errors="coerce")
incidents_df["dt"] = pd.to_datetime(
    incidents_df["date"].dt.strftime("%Y-%m-%d") + " " + incidents_df["time"].fillna("00:00"),
    errors="coerce"
)

coverage_geojson = None
if os.path.exists(COVERAGE_FILE):
    with open(COVERAGE_FILE, "r", encoding="utf-8") as f:
        coverage_geojson = json.load(f)

# --- Layout ---
st.title("🗺️ Ndaka Security – Operations, Assets & Incidents")

left, right = st.columns([2,1])

# --- Right panel: KPIs + filters ---
with right:
    st.subheader("📊 KPI Dashboard")
    st.metric("Total Incidents", len(incidents_df))
    st.metric("Solved", (incidents_df["status"].str.lower()=="solved").sum())
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
    show_props = st.checkbox("Show Properties", True)
    show_assets = st.checkbox("Show Assets", False)
    show_incidents = st.checkbox("Show Incidents", True)
    show_heat = st.checkbox("Show Heatmap", True)
    show_cov = st.checkbox("Show Coverage", True)

# --- Apply filters ---
idf = incidents_df.copy()
if province != "All": idf = idf[idf["province"]==province]
if town != "All": idf = idf[idf["town"]==town]
if itype != "All": idf = idf[idf["incident_type"]==itype]
if status != "All": idf = idf[idf["status"]==status]

# --- Map ---
with left:
    m = folium.Map(location=[-28.5, 24.7], zoom_start=6, tiles="OpenStreetMap")

    # Properties
    if show_props:
        fg = folium.FeatureGroup("Properties")
        for _, pr in properties_df.iterrows():
            folium.Marker(
                [pr["lat"], pr["lon"]],
                popup=f"<b>{pr['property_name']}</b><br>{pr['town']} ({pr['sector']})"
            ).add_to(fg)
        fg.add_to(m)

    # Assets
    if show_assets:
        for _, a in assets_df.iterrows():
            pr = properties_df[properties_df["property_id"]==a["property_id"]].iloc[0]
            folium.CircleMarker(
                [pr["lat"], pr["lon"]],
                radius=4,
                color="purple",
                fill=True,
                fill_opacity=0.6,
                popup=f"{a['asset_type']} ({a['criticality']}) – R{a['insured_value']:,}"
            ).add_to(m)

    # Incidents
    if show_incidents and not idf.empty:
        cl = MarkerCluster(name="Incidents")
        for _, r in idf.iterrows():
            color = "red" if r["severity"]=="High" else "orange" if r["severity"] in ["Medium","Semi-High"] else "green"
            folium.CircleMarker(
                [r["lat"], r["lon"]],
                radius=6,
                color=color,
                fill=True,
                fill_opacity=0.8,
                popup=f"<b>{r['title']}</b><br>{r['town']}, {r['province']}<br>Status: {r['status']}<br>Notes: {r['notes']}"
            ).add_to(cl)
        cl.add_to(m)

    # Heatmap
    if show_heat and not idf.empty:
        pts = idf[["lat","lon"]].dropna().values.tolist()
        if len(pts) > 1:
            HeatMap(pts, radius=20, blur=15).add_to(m)

    # Coverage
    if show_cov and coverage_geojson:
        folium.GeoJson(coverage_geojson, name="Coverage").add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width=None, height=700)

# --- Incident Feed ---
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
                "Retail","Commercial","Industrial","Governmental","Residential",
                "Community","VIP","Strikes & Crowd Control","Transit Incident"
            ])
            incident_type = st.text_input("Incident type", "Robbery")
            severity = st.selectbox("Severity", ["Low","Medium","Semi-High","High"])
            status = st.selectbox("Status", ["Reported","Under investigation","In pursuit","Open","Searching","Solved"])

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
        # generate new ID
        if not incidents_df.empty:
            new_id = int(incidents_df["id"].max()) + 1
        else:
            new_id = 1001

        # mark as transit if outside core provinces
        OPERATING_PROVINCES = {"Gauteng","Free State","Mpumalanga","North West","Limpopo"}
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
