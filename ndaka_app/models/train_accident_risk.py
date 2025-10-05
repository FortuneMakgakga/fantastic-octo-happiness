# ndaka_app/models/train_accident_risk.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib, json
from pathlib import Path
from ndaka_app.utils.data_loader import load_csv
from ndaka_app.utils import features

MODEL_DIR = Path("ndaka_app/models")

def main():
    tele = load_csv("vehicle_telemetry_daily.csv", parse_dates=["date"])
    df = features.build_vehicle_features(tele)

    # Label: accident if km_night > threshold (simulated)
    df["target"] = (df["km_night"] > 200).astype(int)

    X = df[["km_day", "km_night"]]
    y = df["target"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_DIR / "accident_risk.pkl")
    json.dump(list(X.columns), open(MODEL_DIR / "accident_risk_features.json", "w"))

    print("✅ Accident risk model trained and saved.")

if __name__ == "__main__":
    main()
