import os
import datetime
import requests
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv
#from app import apply_theme
#apply_theme()
from io import BytesIO
from PIL import Image, ImageDraw

# ReportLab for PDFs
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image as RLImage
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


# =========================
# ENV / CONFIG
# =========================
load_dotenv()
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
PLATE_API_KEY = os.getenv("PLATERECOGNIZER_API_KEY")

MODEL_ENDPOINTS = {
    "RF-DETR v7 – My First Project": ("my-first-project-pagfk", "7"),
    "RF-DETR v9 – My First Project": ("my-first-project-pagfk", "9"),
    "RF-DETR v10 – My First Project (latest)": ("my-first-project-pagfk", "10"),
}

PLATE_URL = "https://api.platerecognizer.com/v1/plate-reader/"


# =========================
# HELPERS
# =========================
def _now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def bytes_to_pil(img_bytes: bytes) -> Image.Image:
    return Image.open(BytesIO(img_bytes)).convert("RGB")


def iou(a, b) -> float:
    xa1, ya1, xa2, ya2 = a["left"], a["top"], a["right"], a["bottom"]
    xb1, yb1, xb2, yb2 = b["left"], b["top"], b["right"], b["bottom"]
    inter_w = max(0, min(xa2, xb2) - max(xa1, xb1))
    inter_h = max(0, min(ya2, yb2) - max(ya1, yb1))
    inter = inter_w * inter_h
    area_a = (xa2 - xa1) * (ya2 - ya1)
    area_b = (xb2 - xb1) * (yb2 - yb1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


# =========================
# DICTIONARIES FOR MAKE / COLOR INFERENCE
# =========================
_COLOR_MAP = {
    "white": "White", "black": "Black", "silver": "Silver",
    "gray": "Gray", "grey": "Gray", "blue": "Blue", "red": "Red",
    "green": "Green", "yellow": "Yellow", "brown": "Brown",
    "beige": "Beige", "gold": "Gold", "orange": "Orange",
    "purple": "Purple", "maroon": "Maroon", "pink": "Pink",
    "cyan": "Cyan", "teal": "Teal",
}

_MAKE_MAP = {
    "toyota": "Toyota", "volkswagen": "Volkswagen", "vw": "Volkswagen",
    "bmw": "BMW", "lexus": "Lexus", "ford": "Ford", "honda": "Honda",
    "mercedes": "Mercedes", "benz": "Mercedes", "hyundai": "Hyundai",
    "kia": "Kia", "audi": "Audi", "nissan": "Nissan", "chevrolet": "Chevrolet",
    "isuzu": "Isuzu", "mazda": "Mazda", "suzuki": "Suzuki",
    "renault": "Renault", "peugeot": "Peugeot", "volvo": "Volvo",
    "range rover": "Land Rover", "land rover": "Land Rover",
}


# --- At the top of your script (below _MAKE_MAP) ---
_VALID_TYPES = {"sedan", "suv", "hatchback", "pickup", "truck", "van", "minibus", "bus", "bakkie","Taxi","taxi"}

def refine_vehicle_type(label: str) -> str:
    """Cleans Roboflow labels like 'Toyota Car' or 'Red SUV' to proper types."""
    if not label:
        return "Unknown"
    low = label.lower()
    for t in _VALID_TYPES:
        if t in low:
            return t.capitalize()
    # If label ends with 'car' or only says 'car', discard it
    if "car" in low:
        return "Unknown"
    return "Unknown"





def infer_color_from_label(label: str):
    if not label:
        return None
    low = label.lower()
    for k, v in _COLOR_MAP.items():
        if k in low:
            return v
    return None


def infer_make_from_label(label: str):
    if not label:
        return None
    low = label.lower()
    for k, v in [("range rover", "Land Rover"), ("land rover", "Land Rover")]:
        if k in low:
            return v
    for k, v in _MAKE_MAP.items():
        if k in low:
            return v
    return None


def clean_vehicle_fields(row):
    """
    Refine 'vehicle_type', 'vehicle_make', 'vehicle_color' based on mixed Roboflow labels.
    Example fixes:
      - 'Silver Car'  → Color=Silver, Make=Unknown, Type=Car
      - 'Toyota Van'  → Make=Toyota, Type=Van
    """
    vt = row["vehicle_type"].strip().title()
    make, color = row["vehicle_make"], row["vehicle_color"]

    tokens = vt.split()
    if len(tokens) == 2:
        first, second = tokens
        if first.lower() in [c.lower() for c in _COLOR_MAP.values()]:
            row["vehicle_color"] = first
            row["vehicle_type"] = second
            row["vehicle_make"] = "Unknown"
        elif first.lower() in [m.lower() for m in _MAKE_MAP.values()]:
            row["vehicle_make"] = first
            row["vehicle_type"] = second
        else:
            row["vehicle_type"] = second
    elif len(tokens) == 1:
        row["vehicle_type"] = tokens[0]
    else:
        row["vehicle_type"] = "Unknown"

    return row


# =========================
# API CALLS
# =========================
def roboflow_detect(img_bytes: bytes, project: str, model: str, conf: float):
    """Return vehicle predictions from Roboflow (green boxes)."""
    if not ROBOFLOW_API_KEY:
        st.error("⚠️ Missing ROBOFLOW_API_KEY in .env")
        return []

    url = f"https://detect.roboflow.com/{project}/{model}?api_key={ROBOFLOW_API_KEY}"
    files = {"file": ("image.jpg", img_bytes, "application/octet-stream")}
    resp = requests.post(url, files=files)

    preds = []
    if resp.status_code in (200, 201):
        data = resp.json()
        for p in data.get("predictions", []):
            c = float(p.get("confidence", 0.0))
            if c >= conf:
                x, y, w, h = p.get("x"), p.get("y"), p.get("width"), p.get("height")
                if None in (x, y, w, h):
                    continue
                preds.append({
                    "vehicle_type": p.get("class", "Vehicle"),
                    "confidence": c,
                    "x": x, "y": y, "width": w, "height": h,
                    "left": x - w/2, "top": y - h/2,
                    "right": x + w/2, "bottom": y + h/2,
                })
    else:
        st.error(f"Roboflow API Error: {resp.status_code} - {resp.text}")

    return preds


def plate_recognizer_detect(img_bytes: bytes):
    """Return plate + full vehicle info (type, color, make, model, boxes)."""
    if not PLATE_API_KEY:
        st.warning("ℹ️ No PLATERECOGNIZER_API_KEY set; plate results will be Unknown.")
        return []

    headers = {"Authorization": f"Token {PLATE_API_KEY}"}
    files = {"upload": ("image.jpg", img_bytes, "application/octet-stream")}
    resp = requests.post(PLATE_URL, headers=headers, files=files)

    results = []
    if resp.status_code in (200, 201):
        data = resp.json()
        for r in data.get("results", []):
            vehicle = r.get("vehicle", {}) or {}
            plate_box = r.get("box", {}) or {}
            vbox = vehicle.get("box", {}) or {}
            results.append({
                "plate": (r.get("plate") or "").upper() or "UNKNOWN",
                "score": float(r.get("score", 0.0)),
                "region": (r.get("region", {}) or {}).get("code", "Unknown").upper(),
                "plate_box": plate_box,
                "vehicle_box": vbox,
                "vehicle_type": vehicle.get("type", "Unknown"),
                "vehicle_color": vehicle.get("color", "Unknown"),
                "vehicle_make": vehicle.get("make", "Unknown"),
                "vehicle_model": vehicle.get("model", "Unknown"),
            })
    else:
        st.warning(f"Plate Recognizer Error: {resp.status_code}")
    return results


# =========================
# ANNOTATION
# =========================
def annotate_image(img_bytes: bytes, vehicles: list, plates: list) -> BytesIO:
    img = bytes_to_pil(img_bytes)
    draw = ImageDraw.Draw(img)

    for v in vehicles:
        left, top, right, bottom = v["left"], v["top"], v["right"], v["bottom"]
        draw.rectangle([left, top, right, bottom], outline="lime", width=3)
        draw.text((left, top - 12), f"{v['vehicle_type']} ({v['confidence']*100:.1f}%)", fill="lime")

    for p in plates:
        box = p.get("plate_box") or {}
        if not {"xmin", "ymin", "xmax", "ymax"} <= set(box.keys()):
            continue
        xmin, ymin, xmax, ymax = box["xmin"], box["ymin"], box["xmax"], box["ymax"]
        draw.rectangle([(xmin, ymin), (xmax, ymax)], outline="yellow", width=3)
        draw.text((xmin, ymin - 12), f"Plate: {p['plate']}", fill="yellow")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# =========================
# PDF GENERATION
# =========================
def generate_pdf_report(annotated_buf: BytesIO, rows: list):
    pdf_buf = BytesIO()
    doc = SimpleDocTemplate(pdf_buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        elements.append(RLImage(logo_path, width=90, height=50, hAlign="RIGHT"))

    elements.append(Paragraph("<b>Ndaka Vehicle Intelligence Report</b>", styles["Title"]))
    elements.append(Paragraph(f"Generated on {_now_str()}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Detection Summary", styles["Heading2"]))
    data = [["Plate", "Vehicle", "Color", "Make", "Model", "Confidence", "Time"]]
    for r in rows:
        data.append([
            r["plate"], r["vehicle_type"], r["vehicle_color"], r["vehicle_make"],
            r["vehicle_model"], r["confidence"], r["time"]
        ])

    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eeeeee")),
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#999999")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Visual Evidence", styles["Heading2"]))
    annotated_buf.seek(0)
    elements.append(RLImage(annotated_buf, width=400, height=300))

    doc.build(elements)
    pdf_buf.seek(0)
    return pdf_buf


# =========================
# MATCH VEHICLES ↔ PLATES
# =========================
def match_vehicles_to_plates(vehicles: list, plates: list):
    def pr_vehicle_box(p):
        vb = p.get("vehicle_box") or {}
        if {"xmin", "ymin", "xmax", "ymax"} <= set(vb.keys()):
            return {"left": vb["xmin"], "top": vb["ymin"], "right": vb["xmax"], "bottom": vb["ymax"]}
        return None

    matches = []
    used_plate_idx = set()

    for v in vehicles:
        best_idx, best_iou = None, 0.0
        vbox = {"left": v["left"], "top": v["top"], "right": v["right"], "bottom": v["bottom"]}
        for idx, p in enumerate(plates):
            pbox = pr_vehicle_box(p)
            if not pbox:
                continue
            score = iou(vbox, pbox)
            if score > best_iou and idx not in used_plate_idx:
                best_iou, best_idx = score, idx

        if best_idx is None and plates:
            remaining = [i for i in range(len(plates)) if i not in used_plate_idx]
            best_idx = remaining[0] if remaining else 0

        plate = plates[best_idx] if (plates and best_idx is not None) else {
            "plate": "UNKNOWN", "vehicle_type": "Unknown",
            "vehicle_color": "Unknown", "vehicle_make": "Unknown", "vehicle_model": "Unknown"
        }
        used_plate_idx.add(best_idx)

        pr_color = plate.get("vehicle_color") or "Unknown"
        pr_make = plate.get("vehicle_make") or "Unknown"

        rf_label = v["vehicle_type"]
        rf_color = infer_color_from_label(rf_label)
        rf_make = infer_make_from_label(rf_label)

        final_color = pr_color if pr_color != "Unknown" else (rf_color or "Unknown")
        final_make = pr_make if pr_make != "Unknown" else (rf_make or "Unknown")

        row = {
            "plate": plate.get("plate", "UNKNOWN"),
            "vehicle_type": refine_vehicle_type(v["vehicle_type"]),
            "vehicle_color": final_color,
            "vehicle_make": final_make,
            "vehicle_model": plate.get("vehicle_model", "Unknown"),
            "confidence": f"{v['confidence']*100:.1f}%",
            "time": _now_str(),
            "location": "Unknown",
        }
        matches.append(clean_vehicle_fields(row))
    return matches


# =========================
# STREAMLIT PAGE
# =========================
def vehicle_intelligence_page():
    st.title("🚔 Vehicle Intelligence")
    st.write("AI-powered **Vehicle + License Plate Recognition** (Roboflow + Plate Recognizer)")

    model_label = st.selectbox("Select Model Version", list(MODEL_ENDPOINTS.keys()))
    project, model = MODEL_ENDPOINTS[model_label]

    col1, col2 = st.columns([4, 1])
    with col1:
        conf_pct = st.slider(
            "Confidence Threshold", 5, 95, 50,
            help=("Adjust how confident the AI must be before labeling a vehicle.\n\n"
                  "• Lower → more detections\n• Higher → stricter matches.")
        )
    with col2:
        st.markdown("<span title='Confidence controls AI certainty'>ℹ️</span>", unsafe_allow_html=True)

    conf = conf_pct / 100.0

    up = st.file_uploader("📤 Upload an image (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if not up:
        return

    img_bytes = up.read()
    st.caption(f"Model: `{project}/{model}` | Confidence ≥ **{conf_pct}%**")
    st.image(img_bytes, caption="Uploaded Image", use_column_width=True)

    with st.spinner("Analyzing image…"):
        vehicles = roboflow_detect(img_bytes, project, model, conf)
        plates = plate_recognizer_detect(img_bytes)

    rows = match_vehicles_to_plates(vehicles, plates)

    st.markdown("---")
    st.subheader("✅ Detection Results")
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Vehicles Detected", len(vehicles))
    with k2:
        st.metric("Plates Detected", len(plates))
    with k3:
        st.metric("Last Scan", _now_str())

    if rows:
        df = pd.DataFrame(rows, columns=[
            "plate", "vehicle_type", "vehicle_color", "vehicle_make", "vehicle_model", "confidence", "time"
        ])
        st.dataframe(df)

        st.subheader("🎴 Detection Cards")
        for r in rows:
            conf_val = float(r["confidence"].replace("%", ""))
            conf_color = "limegreen" if conf_val >= 80 else "orange" if conf_val >= 50 else "red"
            st.markdown(f"""
            <div style='padding:15px; border-radius:10px; background:#1e1e1e; border:1px solid #444; margin-bottom:10px'>
                <h3 style='color:#00ffcc'>Plate: {r['plate']}</h3>
                <p><b>Vehicle:</b> {r['vehicle_type']} | <b>Color:</b> {r['vehicle_color']} | <b>Make:</b> {r['vehicle_make']} | <b>Model:</b> {r['vehicle_model']}</p>
                <p><b>Confidence:</b> <span style='color:{conf_color}'>{r['confidence']}</span></p>
                <p><b>Time:</b> {r['time']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📄 Generate Report")
    if st.button("Generate Report"):
        with st.spinner("Creating annotated image & PDF…"):
            annotated_buf = annotate_image(img_bytes, vehicles, plates)
            st.image(annotated_buf, caption="Annotated Detection Preview", use_column_width=True)
            pdf_buf = generate_pdf_report(annotated_buf, rows)

        st.download_button(
            label="📥 Download Detection Report (PDF)",
            data=pdf_buf,
            file_name=f"Vehicle_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )


if __name__ == "__main__":
    vehicle_intelligence_page()
