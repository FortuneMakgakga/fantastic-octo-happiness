# ndaka_app/utils/features.py
import pandas as pd

def build_incident_features(incidents: pd.DataFrame) -> pd.DataFrame:
    """Aggregate incident counts per client per week."""
    incidents["week"] = incidents["date"].dt.to_period("W").apply(lambda r: r.start_time)
    agg = incidents.groupby(["client_id", "week"]).size().reset_index(name="incident_count")
    return agg

def build_vehicle_features(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Aggregate telemetry (km_day/night) per car per week."""
    telemetry["week"] = telemetry["date"].dt.to_period("W").apply(lambda r: r.start_time)
    agg = telemetry.groupby(["car_id", "week"])[["km_day", "km_night"]].sum().reset_index()
    return agg

def build_strike_features(strikes: pd.DataFrame) -> pd.DataFrame:
    """Aggregate strike counts per province per week."""
    strikes["week"] = strikes["date"].dt.to_period("W").apply(lambda r: r.start_time)
    agg = strikes.groupby(["province", "week"]).size().reset_index(name="strike_count")
    return agg
