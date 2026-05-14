"""Export deck-ready PNGs of the hero figures.

Run from project root:
    source .venv/bin/activate
    python scripts/export_pngs.py

Writes 1920x1080 PNGs to outputs/figures/png/ that you can drag into
Claude Design (claude.ai) when generating the slide deck.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import warnings
from pathlib import Path
warnings.filterwarnings("ignore")
from statsmodels.tsa.holtwinters import ExponentialSmoothing

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "orders.csv"
PNG = ROOT / "outputs" / "figures" / "png"
PNG.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA, parse_dates=["timestamp"])
df["hour"] = df.timestamp.dt.hour
df["dow_num"] = df.timestamp.dt.dayofweek
df["day_bucket"] = np.where(df.dow_num >= 5, "weekend", "weekday")
df["date"] = df.timestamp.dt.normalize()

WASTE = "#d62728"
GAP = "#1f77b4"
GREY = "#cccccc"
DARK = "#0b3d91"

W, H = 1920, 1080


def save(fig: go.Figure, name: str, scale: int = 1):
    fig.update_layout(
        font=dict(family="Inter, -apple-system, Helvetica Neue, sans-serif", size=22),
        margin=dict(l=80, r=40, t=90, b=80),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.write_image(PNG / name, width=W, height=H, scale=scale)
    print(f"wrote {PNG / name}")


# ---------- Slide 3 hero: pooled hour-of-day demand vs surge -----------
hr = df.groupby("hour").agg(n_orders=("order_id", "size"),
                            n_surge=("surge_applied", "sum"))
hr["demand_share"] = hr.n_orders / hr.n_orders.sum()
hr["surge_rate"] = hr.n_surge / hr.n_orders

fig = go.Figure()
fig.add_trace(go.Bar(x=hr.index, y=hr.demand_share, name="demand share",
                     marker=dict(color=GREY), opacity=0.8))
fig.add_trace(go.Scatter(x=hr.index, y=hr.surge_rate, name="surge fire rate",
                         mode="lines+markers", line=dict(color=WASTE, width=5),
                         marker=dict(size=10), yaxis="y2"))
# Highlight hour-18 gap
fig.add_vrect(x0=17.5, x1=18.5, line_width=0, fillcolor=WASTE, opacity=0.10)
fig.add_annotation(x=18, y=0.075, ax=18, ay=0.05, xref="x", yref="y",
                   text="Hour 18 — peak demand, off-peak surge",
                   showarrow=True, arrowhead=2, font=dict(color=WASTE, size=20))
fig.update_layout(
    title=dict(text="Hour-of-day demand share (bars) vs surge fire rate (red line) — the policy mis-fires at hour 18",
               font=dict(size=26, color=DARK)),
    xaxis=dict(title="hour of day", dtick=1),
    yaxis=dict(title="demand share", tickformat=".1%"),
    yaxis2=dict(title="surge fire rate", tickformat=".0%", overlaying="y", side="right"),
    legend=dict(orientation="h", y=1.10),
    height=H, width=W,
)
save(fig, "slide3_pooled_hour.png")


# ---------- Slide 4 hero: within-hour delivery time surge vs no-surge -----------
ph = df.groupby(["hour", "surge_applied"]).delivery_time_min.mean().unstack().round(2)
ph.columns = ["ns", "s"]

fig = go.Figure()
fig.add_trace(go.Scatter(x=ph.index, y=ph.ns, mode="lines+markers",
                         name="no surge", line=dict(color=GAP, width=5),
                         marker=dict(size=10)))
fig.add_trace(go.Scatter(x=ph.index, y=ph.s, mode="lines+markers",
                         name="surge applied", line=dict(color=WASTE, width=5),
                         marker=dict(size=10)))
# Highlight peak windows where the two lines overlap
for x0, x1, label in [(11.5, 13.5, "Lunch peak"), (18.5, 21.5, "Dinner peak")]:
    fig.add_vrect(x0=x0, x1=x1, line_width=0, fillcolor=DARK, opacity=0.06)
    fig.add_annotation(x=(x0 + x1) / 2, y=45.5, xref="x", yref="y",
                       text=label + " — same delivery time",
                       showarrow=False, font=dict(color=DARK, size=18))
fig.update_layout(
    title=dict(text="Within-hour delivery time: surge orders vs non-surge orders",
               font=dict(size=26, color=DARK)),
    xaxis=dict(title="hour of day", dtick=1),
    yaxis=dict(title="mean delivery time (min)"),
    legend=dict(orientation="h", y=1.10),
    height=H, width=W,
)
save(fig, "slide4_delivery_sanity.png")


# ---------- Slide 3 supplement: cuisine hour-18 lift -----------
h18 = df[df.hour == 18].cuisine.value_counts(normalize=True) * 100
allsh = df.cuisine.value_counts(normalize=True) * 100
lift = (h18 - allsh).round(2).sort_values(ascending=False).reset_index()
lift.columns = ["cuisine", "lift_pp"]
fig = px.bar(lift, x="cuisine", y="lift_pp",
             color="lift_pp",
             color_continuous_scale=[(0, GAP), (0.5, GREY), (1, WASTE)],
             labels={"lift_pp": "share lift at hour 18 (percentage points)"})
fig.update_layout(
    title=dict(text="Cuisine share lift at hour 18 — Beverages & North Indian drive the dinner ramp-up",
               font=dict(size=26, color=DARK)),
    xaxis=dict(title=""),
    yaxis=dict(title="share lift (pp)"),
    coloraxis_showscale=False,
    height=H, width=W,
)
save(fig, "slide3_cuisine_lift.png")


# ---------- Slide 5: Mumbai forecast -----------
mumbai = df[df.city == "Mumbai"].groupby("date").size().rename("orders").to_frame()
mumbai.index = pd.DatetimeIndex(mumbai.index, freq="D")
m = ExponentialSmoothing(mumbai.orders, seasonal_periods=7, trend="add", seasonal="add").fit()
fc = m.forecast(7)
fc.index = pd.date_range(mumbai.index[-1] + pd.Timedelta(days=1), periods=7, freq="D")

# kaleido can't serialise pandas Timestamps directly — render via string x-axis
hist_x = mumbai.index.strftime("%Y-%m-%d").tolist()
fc_x = fc.index.strftime("%Y-%m-%d").tolist()

fig = go.Figure()
fig.add_trace(go.Scatter(x=hist_x, y=mumbai.orders.values,
                         mode="lines", name="actual (90 days)",
                         line=dict(color="black", width=3)))
fig.add_trace(go.Scatter(x=fc_x, y=fc.values,
                         mode="lines+markers", name="forecast (next 7 days)",
                         line=dict(color=WASTE, width=5, dash="dash"),
                         marker=dict(size=12)))
fig.add_vrect(x0=len(hist_x) - 0.5, x1=len(hist_x) + len(fc_x) - 0.5,
              line_width=0, fillcolor=WASTE, opacity=0.05)
fig.update_layout(
    title=dict(text="Mumbai — 90 days history + 7-day forecast · Holt-Winters MAPE 7.14% (vs naive 10.49%)",
               font=dict(size=26, color=DARK)),
    xaxis=dict(title="date", tickmode="auto", nticks=12),
    yaxis=dict(title="orders / day"),
    legend=dict(orientation="h", y=1.10),
    height=H, width=W,
)
save(fig, "slide5_forecast.png")


# ---------- Slide 3 supplement: cohort null result (all 14 curves overlaid) -----------
shape = df.groupby(["city", "day_bucket", "hour"]).size().unstack("hour", fill_value=0)
shape_n = shape.div(shape.sum(axis=1), axis=0)
outliers = {("Chennai", "weekend"), ("Kolkata", "weekend")}

fig = go.Figure()
for idx, row in shape_n.iterrows():
    is_out = idx in outliers
    color = WASTE if (is_out and idx[0] == "Chennai") else GAP if is_out else "#999"
    fig.add_trace(go.Scatter(x=list(range(24)), y=row.values,
                             mode="lines+markers" if is_out else "lines",
                             name=f"{idx[0]} ({idx[1]})" + (" — outlier" if is_out else ""),
                             line=dict(color=color, width=4 if is_out else 1.5),
                             marker=dict(size=8 if is_out else 4),
                             opacity=1.0 if is_out else 0.30))
fig.update_layout(
    title=dict(text="All 14 (city, day-bucket) demand curves — only Chennai-weekend and Kolkata-weekend deviate",
               font=dict(size=26, color=DARK)),
    xaxis=dict(title="hour of day", dtick=1),
    yaxis=dict(title="share of city-day volume", tickformat=".1%"),
    legend=dict(font=dict(size=14)),
    height=H, width=W,
)
save(fig, "slide3_cohort_curves.png")


print(f"\nDone. {len(list(PNG.glob('*.png')))} PNGs in {PNG}")
