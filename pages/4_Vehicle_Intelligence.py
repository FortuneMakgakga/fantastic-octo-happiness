import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import datetime
import requests
import os
from dotenv import load_dotenv
#from app import apply_theme
#apply_theme()

# ---------------------------
# Load API Keys from .env
# ---------------------------
load_dotenv()
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
PLATE_API_KEY = os.getenv("PLATERECOGNIZER_API_KEY")

# Your trained Roboflow model details
PROJECT = "my-first-project-pagfk"   # update with your project slug
MODEL = "7"                          # update with your model version

API_URL_PLATE = "https://api.platerecognizer.com/v1/plate-reader/"

# ---------------------------
# Plate Recognizer API
# ---------------------------
def detect_plate(image_file):
    if not PLATE_API_KEY:
        st.error("⚠️ Plate Recognizer API key not found in .env")
        return "Unknown"

    image_file.seek(0)  # reset pointer
    headers = {"Authorization": f"Token {PLATE_API_KEY}"}
    files = {"upload": image_file}

    response = requests.post(API_URL_PLATE, headers=headers, files=files)
    if response.status_code in [200, 201]:
        data = response.json()
        if data.get("results"):
            return data["results"][0]["plate"].upper()
    elif response.status_code == 403:
        st.warning("⚠️ Plate Recognizer returned 403 (bad key/quota/empty file).")
    return "Unknown"

# ---------------------------
# Roboflow Vehicle Detection API
# ---------------------------
def detect_vehicle_with_roboflow(image_file, debug=False):
    if not ROBOFLOW_API_KEY:
        st.error("⚠️ Roboflow API key not found in .env")
        return []

    url = f"https://detect.roboflow.com/{PROJECT}/{MODEL}?api_key={ROBOFLOW_API_KEY}"

    image_file.seek(0)  # reset pointer
    resp = requests.post(url, files={"file": image_file})

    if resp.status_code in [200, 201]:
        data = resp.json()
        if debug:
            st.json(data)

        plate_number = detect_plate(image_file)

        results = []
        for prediction in data.get("predictions", []):
            results.append({
                "plate": plate_number,
                "confidence": f"{prediction['confidence']*100:.1f}%",
                "vehicle_type": prediction.get("class", "Vehicle"),
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "location": "Unknown"
            })
        return results
    else:
        st.error(f"Roboflow API Error: {resp.status_code} - {resp.text}")
        return []

# ---------------------------
# Vehicle Intelligence Page
# ---------------------------
def vehicle_intelligence_page():
    st.title("🚔 Vehicle Intelligence")
    st.write("AI-powered **Vehicle + License Plate Recognition** (Roboflow + Plate Recognizer)")

    uploaded_file = st.file_uploader("📤 Upload an image (jpg/png) to analyze", type=["jpg", "png"])

    detections = []
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        detections = detect_vehicle_with_roboflow(uploaded_file)

    if detections:
        st.markdown("---")
        st.subheader("✅ Detection Results")

        # KPI summary cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Vehicles Detected", len(detections))
        with col2:
            st.metric("Plates Detected", len([d for d in detections if d['plate'] != "Unknown"]))
        with col3:
            st.metric("Last Scan", detections[0]["time"])

        # Styled DataFrame
        df = pd.DataFrame(detections)
        st.dataframe(df.style.set_properties(**{
            "text-align": "center"
        }).set_table_styles([{
            'selector': 'th',
            'props': [('text-align', 'center'), ('background-color', '#0078d7'), ('color', 'white')]
        }]))

        # Detection Cards (NEW UI)
        st.subheader("🎴 Detection Cards")
        for det in detections:
            conf_val = float(det['confidence'].replace('%',''))
            if conf_val >= 80:
                conf_color = "limegreen"
            elif conf_val >= 50:
                conf_color = "orange"
            else:
                conf_color = "red"

            st.markdown(f"""
            <div style="padding:15px; border-radius:10px; margin-bottom:10px;
                        background-color:#1e1e1e; border:1px solid #444;">
                <h3 style="color:#00ffcc;">Plate: {det['plate']}</h3>
                <p><b>Vehicle:</b> {det['vehicle_type']}</p>
                <p><b>Confidence:</b> <span style="color:{conf_color}; font-weight:bold;">
                    {det['confidence']}</span></p>
                <p><b>Time:</b> {det['time']}</p>
                <p><b>Location:</b> {det['location']}</p>
            </div>
            """, unsafe_allow_html=True)

        # Map display
        st.subheader("🗺️ Geospatial View (Demo)")
        m = folium.Map(location=[-26.2041, 28.0473], zoom_start=10)
        for det in detections:
            folium.Marker(
                [-26.2041, 28.0473],
                popup=f"Plate: {det['plate']}<br>Type: {det['vehicle_type']}<br>Confidence: {det['confidence']}"
            ).add_to(m)
        st_folium(m, width=700, height=500)

        # Alerts
        st.subheader("⚠️ Alerts")
        blacklist = ["XYZ123GP", "ABC456GP"]
        flagged = [d for d in detections if d["plate"] in blacklist]
        if flagged:
            st.error(f"🚨 Blacklisted vehicle detected: {', '.join([d['plate'] for d in flagged])}")
        else:
            st.success("✅ No blacklisted vehicles found.")

# ---------------------------
# Run Standalone
# ---------------------------
if __name__ == "__main__":
    vehicle_intelligence_page()
