"""Generate a representative Mumbai Q1 2025 weather panel and the Indian
holiday calendar. Saved as CSVs in data/ so the augmented forecast in
Notebook 08 has deterministic, network-free exogenous features.

Methodology disclosed in Notebook 08: in production, this slot is filled
with real IMD (India Meteorological Department) data, joined on date.
The shape of the weather panel — daily temperatures, precipitation,
holiday flag — is what NB08's SARIMAX consumes; the synthetic version
follows the climatology of Mumbai Q1 (dry, 18–33°C) so the model has
realistic variance to work with.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RNG = np.random.default_rng(42)

dates = pd.date_range("2025-01-01", "2025-03-31", freq="D")
n = len(dates)
day_of_year = dates.dayofyear.values

# Mumbai Q1 climatology (deterministic seasonal + small daily noise):
#   - Tmax climbs from ~30°C in early Jan to ~33°C by end of March
#   - Tmin climbs from ~18°C to ~24°C over the same window
#   - Precipitation is very sparse; Q1 is the dry season
tmax = 30.0 + (day_of_year - 1) * (3.0 / 89.0) + RNG.normal(0, 1.2, n)
tmin = 18.0 + (day_of_year - 1) * (6.0 / 89.0) + RNG.normal(0, 1.5, n)
# Force tmin < tmax always
tmin = np.minimum(tmin, tmax - 4.0)

# Precipitation: ~3 rainy events across the quarter (Q1 is dry season)
precip = np.zeros(n)
rain_days = RNG.choice(n, size=3, replace=False)
precip[rain_days] = RNG.exponential(scale=8.0, size=3)
precip = precip.round(1)

# Wind: mild, 8-18 km/h typical
wind = 12.0 + RNG.normal(0, 2.5, n)
wind = np.clip(wind, 5.0, 25.0)

weather = pd.DataFrame({
    "date": dates.date,
    "temperature_max_c": tmax.round(1),
    "temperature_min_c": tmin.round(1),
    "precipitation_mm": precip,
    "wind_speed_kmh": wind.round(1),
})
weather.to_csv(ROOT / "data" / "mumbai_weather_2025q1.csv", index=False)
print(f"Wrote weather: {len(weather)} days  ·  "
      f"tmax {tmax.min():.1f}–{tmax.max():.1f}°C  ·  "
      f"{(precip > 1).sum()} rainy days  ·  total precip {precip.sum():.1f}mm")

# Indian holidays Q1 2025 (the policy-relevant set)
holidays = pd.DataFrame([
    {"date": "2025-01-14", "name": "Makar Sankranti",     "tier": "regional"},
    {"date": "2025-01-26", "name": "Republic Day",         "tier": "national"},
    {"date": "2025-02-26", "name": "Maha Shivaratri",      "tier": "national"},
    {"date": "2025-03-14", "name": "Holi",                 "tier": "national"},
])
holidays["date"] = pd.to_datetime(holidays.date).dt.date
holidays.to_csv(ROOT / "data" / "india_holidays_2025q1.csv", index=False)
print(f"Wrote holidays: {len(holidays)} entries")
print(holidays.to_string(index=False))
