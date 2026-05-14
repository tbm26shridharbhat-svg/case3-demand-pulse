"""Pull Mumbai daily weather Jan-Mar 2025 from Open-Meteo (free, no API key) and
commit it as data/mumbai_weather_2025q1.csv. Run once; the CSV becomes the
source of truth for Notebook 08's exogenous features. Avoids network dependency
during notebook execution / CI.
"""
from __future__ import annotations
import pandas as pd
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "mumbai_weather_2025q1.csv"

# Mumbai coords
LAT, LON = 19.0760, 72.8777

URL = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": LAT,
    "longitude": LON,
    "start_date": "2025-01-01",
    "end_date": "2025-03-31",
    "daily": ",".join([
        "temperature_2m_max", "temperature_2m_min",
        "precipitation_sum", "rain_sum",
        "wind_speed_10m_max",
    ]),
    "timezone": "Asia/Kolkata",
}

print(f"Fetching Mumbai weather {params['start_date']} → {params['end_date']} from Open-Meteo Archive…")
r = requests.get(URL, params=params, timeout=30)
r.raise_for_status()
j = r.json()

df = pd.DataFrame(j["daily"])
df["date"] = pd.to_datetime(df.pop("time"))
df = df[["date"] + [c for c in df.columns if c != "date"]]
df.to_csv(OUT, index=False)

print(f"Wrote {OUT}  ({len(df)} days)")
print(df.head(7).to_string(index=False))
print(f"\nRange: temp min {df.temperature_2m_min.min()}°C → max {df.temperature_2m_max.max()}°C")
print(f"Total precipitation: {df.precipitation_sum.sum():.1f}mm")
print(f"Days with rain (precip > 1mm): {(df.precipitation_sum > 1).sum()}")
