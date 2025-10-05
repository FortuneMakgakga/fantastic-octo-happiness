# ndaka_app/models/train_hijacking_risk.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib, json
from pathlib import Path
from ndaka_app.utils.data_loader import load_csv

MODEL_DIR = Path("ndaka_app/models")

def main():
    incidents = load_csv("incidents.csv", parse_dates=["date"])

    # Filter hijacking-related
    hijack = incidents[incidents["incident_type"].str.contains("Hijacking|Theft", case=False, na=False)]
    hijack["week"] = hijack["date"].dt.to_period("W").apply(lambda r: r.start_time)
    agg = hijack.groupby(["client_id", "week"]).size().reset_index(name="hijack_count")

    agg["target"] = (agg["hijack_count"] > 0).astype(int)

    X = agg[["hijack_count"]]
    y = agg["target"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_DIR / "hijacking_risk.pkl")
    json.dump(list(X.columns), open(MODEL_DIR / "hijacking_risk_features.json", "w"))

    print("✅ Hijacking risk model trained and saved.")

if __name__ == "__main__":
    main()
