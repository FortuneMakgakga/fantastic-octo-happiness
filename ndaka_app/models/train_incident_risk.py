# ndaka_app/models/train_incident_risk.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib, json
from pathlib import Path
from ndaka_app.utils.data_loader import load_csv
from ndaka_app.utils import features

MODEL_DIR = Path("ndaka_app/models")

def main():
    incidents = load_csv("incidents.csv", parse_dates=["date"])
    df = features.build_incident_features(incidents)

    # Binary label: incident next week
    df["target"] = (df["incident_count"] > 0).astype(int)

    X = df[["incident_count"]]
    y = df["target"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_DIR / "incident_risk.pkl")
    json.dump(list(X.columns), open(MODEL_DIR / "incident_risk_features.json", "w"))

    print("✅ Incident risk model trained and saved.")

if __name__ == "__main__":
    main()
