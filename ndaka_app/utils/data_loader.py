# ndaka_app/utils/data_loader.py
from pathlib import Path
import os
import pandas as pd

# Default dataset directory (Ndaka v2)
DATA_DIR = Path(os.getenv("NDK_DATA_DIR", "assets/data/ndaka_v2"))

def load_csv(name: str, parse_dates=None) -> pd.DataFrame:
    """Load a CSV file from the Ndaka v2 dataset."""
    return pd.read_csv(DATA_DIR / name, parse_dates=parse_dates)

def load_csv(name, parse_dates=None):
    df = pd.read_csv(DATA_DIR / name)
    # Custom handling for strikes
    if name == "strike_events.csv":
        df["start"] = pd.to_datetime(df["start"], errors="coerce")
        df["end"] = pd.to_datetime(df["end"], errors="coerce")
        df = df.rename(columns={"start": "date"})
    else:
        # Auto-parse any column with "date" in the name
        for col in df.columns:
            if "date" in col.lower():
                df[col] = pd.to_datetime(df[col], errors="coerce")
    return df
