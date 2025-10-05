# ndaka_app/models/train_strike_nowcast.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib, json
from pathlib import Path
from ndaka_app.utils.data_loader import load_csv
from ndaka_app.utils import features

MODEL_DIR = Path("ndaka_app/models")

def main():
    strikes = load_csv("strike_events.csv", parse_dates=["date"])
    df = features.build_strike_features(strikes)

    df["target"] = (df["strike_count"] > 0).astype(int)

    X = df[["strike_count"]]
    y = df["target"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_DIR / "strike_nowcast.pkl")
    json.dump(list(X.columns), open(MODEL_DIR / "strike_nowcast_features.json", "w"))

    print("✅ Strike nowcast model trained and saved.")

if __name__ == "__main__":
    main()
