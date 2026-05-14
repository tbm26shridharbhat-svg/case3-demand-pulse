"""
Demand Pulse — interactive companion to the Notebook submission.

Usage (local):
    streamlit run app/streamlit_app.py
"""
from __future__ import annotations
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "orders.csv"
OUT = ROOT / "outputs"

SURGE_COST_DEFAULT = 20  # ₹ per surge-applied order, swappable in sidebar

st.set_page_config(
    page_title="Demand Pulse · Surge Policy",
    page_icon="📈",
    layout="wide",
)


# ---------- data loading ----------
@st.cache_data
def load_orders() -> pd.DataFrame:
    df = pd.read_csv(DATA, parse_dates=["timestamp"])
    df["hour"] = df.timestamp.dt.hour
    df["dow_num"] = df.timestamp.dt.dayofweek
    df["day_bucket"] = np.where(df.dow_num >= 5, "weekend", "weekday")
    df["date"] = df.timestamp.dt.normalize()
    return df


@st.cache_data
def build_cells(df: pd.DataFrame) -> pd.DataFrame:
    cell = (df.groupby(["city", "day_bucket", "hour"])
              .agg(n_orders=("order_id", "size"),
                   n_surge=("surge_applied", "sum"),
                   avg_value=("order_value", "mean"))
              .reset_index())
    cell["surge_rate"] = cell.n_surge / cell.n_orders
    cell["demand_pct_within_city"] = (cell.groupby("city").n_orders
                                           .rank(pct=True, method="average"))
    cell["surge_pct_within_city"] = (cell.groupby("city").surge_rate
                                          .rank(pct=True, method="average"))

    def classify(r):
        if r.demand_pct_within_city <= 0.50 and r.surge_pct_within_city >= 0.50:
            return "WASTE"
        if r.demand_pct_within_city >= 0.75 and r.surge_pct_within_city <= 0.50:
            return "SUPPLY_GAP"
        return "ALIGNED"

    cell["class"] = cell.apply(classify, axis=1)
    return cell


df = load_orders()
cells = build_cells(df)


# ---------- sidebar ----------
st.sidebar.title("Demand Pulse")
st.sidebar.caption(
    "Companion dashboard for the surge-policy investigation. "
    "Every number in the slide deck and exec summary can be reproduced here."
)
st.sidebar.divider()

page = st.sidebar.radio(
    "Page",
    ["TL;DR for the Ops Head",
     "Policy Alignment Map",
     "Surge Waste & Supply Gap (cells)",
     "City Patterns",
     "Cuisine Cuts",
     "Sanity Check — is surge buying speed?",
     "7-Day Forecast"],
)

st.sidebar.divider()
surge_cost = st.sidebar.number_input(
    "Surge cost per order (₹)",
    min_value=1, max_value=200, value=SURGE_COST_DEFAULT, step=1,
    help="Ops Head's real number plugs in here. Default ₹20 is a stated assumption."
)


# ---------- helper ----------
COLORS = {"WASTE": "#d62728", "SUPPLY_GAP": "#1f77b4", "ALIGNED": "#cccccc"}
CLS_NUM = {"ALIGNED": 0, "SUPPLY_GAP": 1, "WASTE": 2}


def fmt_inr(n: float) -> str:
    if abs(n) >= 1e7: return f"₹{n / 1e7:.2f} cr"
    if abs(n) >= 1e5: return f"₹{n / 1e5:.2f} lakh"
    return f"₹{n:,.0f}"


# ===========================================================
# Page 1 — TL;DR
# ===========================================================
if page == "TL;DR for the Ops Head":
    st.title("Surge Policy — Honest Read")
    st.caption("Jan–Mar 2025 · 50,000 orders · 7 cities · 9 cuisines · 800 restaurants")

    total_surge_orders = int(df.surge_applied.sum())
    waste = cells[cells["class"] == "WASTE"]
    gap = cells[cells["class"] == "SUPPLY_GAP"]
    aligned_top = cells[(cells["class"] == "ALIGNED") &
                        (cells.demand_pct_within_city >= 0.75)]
    target_rate = aligned_top.surge_rate.mean()
    extra_surge = (gap.n_orders * (target_rate - gap.surge_rate)).clip(lower=0).sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total surge orders (90d)", f"{total_surge_orders:,}")
    c2.metric("Surge spend (90d)", fmt_inr(total_surge_orders * surge_cost))
    c3.metric("Wasted spend (90d)",
              fmt_inr(int(waste.n_surge.sum()) * surge_cost),
              delta=f"{waste.n_surge.sum() / total_surge_orders:.1%} of envelope",
              delta_color="inverse")
    c4.metric("Supply-gap reinvestment (90d)",
              fmt_inr(int(extra_surge) * surge_cost),
              delta=f"{len(gap)} cells under-served")

    st.divider()

    st.subheader("The headline")
    st.markdown(f"""
The current surge policy is **mostly aligned with demand**: ~{1 - waste.n_surge.sum() / total_surge_orders:.0%}
of surge spend fires in above-median-demand cells within each city. The wasteful **{waste.n_surge.sum() / total_surge_orders:.1%}**
is recoverable through small rule edits and is enumerated in the *Surge Waste & Supply Gap* tab.

The **larger lever is the dinner-ramp at hour 18**: peak-level demand (~3,683 pooled orders/hour) currently
sees surge in only **5.7%** of cases versus **52%** at hour 19. Recommendation: A/B test a hour-18 surge
boost in one city's weekday window before national rollout.

Two specific weekend cells deviate from the national pattern (Chennai weekend, Kolkata weekend) — they
run a flatter, later peak. Ship a small late-night extension for those two only; do **not** build a
tier-based system. See *City Patterns* tab for the null-result analysis that backs this.
""")

    st.divider()

    st.subheader("Pooled hour-of-day: demand vs surge fire rate")
    hr = df.groupby("hour").agg(n_orders=("order_id", "size"),
                                n_surge=("surge_applied", "sum"))
    hr["demand_share"] = hr.n_orders / hr.n_orders.sum()
    hr["surge_rate"] = hr.n_surge / hr.n_orders

    fig = go.Figure()
    fig.add_trace(go.Bar(x=hr.index, y=hr.demand_share, name="demand share",
                         marker=dict(color="#cccccc"), opacity=0.7))
    fig.add_trace(go.Scatter(x=hr.index, y=hr.surge_rate, name="surge fire rate",
                             mode="lines+markers",
                             line=dict(color=COLORS["WASTE"], width=3), yaxis="y2"))
    fig.update_layout(
        xaxis=dict(title="hour of day", dtick=2),
        yaxis=dict(title="demand share", tickformat=".1%"),
        yaxis2=dict(title="surge fire rate", tickformat=".0%",
                    overlaying="y", side="right"),
        height=440, legend=dict(orientation="h", y=1.12),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Hour 18 is the gap: peak-level demand bar, but the surge line is on the floor.")


# ===========================================================
# Page 2 — Alignment Map
# ===========================================================
elif page == "Policy Alignment Map":
    st.title("Policy Alignment — every (city, day-bucket, hour) cell")
    st.caption("Each dot is one cell. Quadrants are the policy story.")

    cities = ["(all)"] + sorted(df.city.unique())
    bucket = st.radio("Day bucket", ["both", "weekday", "weekend"], horizontal=True)
    city_pick = st.selectbox("City filter", cities)

    sub = cells.copy()
    if bucket != "both": sub = sub[sub.day_bucket == bucket]
    if city_pick != "(all)": sub = sub[sub.city == city_pick]

    fig = px.scatter(
        sub, x="demand_pct_within_city", y="surge_pct_within_city",
        color="class", color_discrete_map=COLORS,
        hover_data=["city", "day_bucket", "hour", "n_orders", "surge_rate"],
        labels={"demand_pct_within_city": "demand percentile (within city)",
                "surge_pct_within_city":  "surge fire-rate percentile (within city)"},
        height=520,
    )
    fig.add_shape(type="line", x0=0, y0=0, x1=1, y1=1,
                  line=dict(dash="dot", color="black"))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Heatmaps — surge fire rate per (city, hour)")
    for b in (["weekday", "weekend"] if bucket == "both" else [bucket]):
        sub_b = cells[cells.day_bucket == b].copy()
        sub_b["class_num"] = sub_b["class"].map(CLS_NUM)
        pivot_c = sub_b.pivot(index="hour", columns="city", values="class_num")
        pivot_r = sub_b.pivot(index="hour", columns="city", values="surge_rate")
        fig = go.Figure(data=go.Heatmap(
            z=pivot_c.values, x=pivot_c.columns, y=pivot_c.index,
            colorscale=[[0, "#eeeeee"], [0.5, COLORS["SUPPLY_GAP"]], [1, COLORS["WASTE"]]],
            zmin=0, zmax=2, showscale=False,
            text=(pivot_r.values * 100).round(1),
            texttemplate="%{text}%",
        ))
        fig.update_layout(title=f"{b.capitalize()}",
                          height=580, yaxis=dict(autorange="reversed", dtick=1),
                          xaxis_title="city", yaxis_title="hour")
        st.plotly_chart(fig, use_container_width=True)


# ===========================================================
# Page 3 — Waste & Gap cells
# ===========================================================
elif page == "Surge Waste & Supply Gap (cells)":
    st.title("Cells to act on")

    waste = cells[cells["class"] == "WASTE"].copy()
    waste["wasted_inr"] = waste.n_surge * surge_cost
    waste = waste.sort_values("wasted_inr", ascending=False)

    gap = cells[cells["class"] == "SUPPLY_GAP"].copy()
    aligned_top = cells[(cells["class"] == "ALIGNED") &
                        (cells.demand_pct_within_city >= 0.75)]
    target = aligned_top.surge_rate.mean()
    gap["extra_surge"] = (gap.n_orders * (target - gap.surge_rate)).clip(lower=0)
    gap["gap_spend_inr"] = gap.extra_surge * surge_cost
    gap = gap.sort_values("gap_spend_inr", ascending=False)

    c1, c2 = st.columns(2)
    c1.metric("Total WASTE (90d)", fmt_inr(waste.wasted_inr.sum()),
              delta=f"{int(waste.n_surge.sum()):,} surge orders to defuse",
              delta_color="off")
    c2.metric("Total SUPPLY-GAP reinvestment (90d)",
              fmt_inr(gap.gap_spend_inr.sum()),
              delta=f"target {target:.0%} surge rate in gap cells",
              delta_color="off")

    st.divider()
    tab1, tab2 = st.tabs(["WASTE — defuse first", "SUPPLY-GAP — invest first"])
    with tab1:
        st.dataframe(
            waste[["city", "day_bucket", "hour", "n_orders", "n_surge",
                   "surge_rate", "wasted_inr"]]
              .rename(columns={"n_orders": "orders", "n_surge": "surge_orders",
                               "wasted_inr": "waste (₹)"})
              .style.format({"surge_rate": "{:.1%}", "waste (₹)": "{:,.0f}"}),
            use_container_width=True,
        )
    with tab2:
        st.dataframe(
            gap[["city", "day_bucket", "hour", "n_orders", "surge_rate",
                 "extra_surge", "gap_spend_inr"]]
              .rename(columns={"n_orders": "orders",
                               "extra_surge": "extra surge orders needed",
                               "gap_spend_inr": "investment (₹)"})
              .style.format({"surge_rate": "{:.1%}",
                             "extra surge orders needed": "{:,.0f}",
                             "investment (₹)": "{:,.0f}"}),
            use_container_width=True,
        )


# ===========================================================
# Page 4 — City Patterns
# ===========================================================
elif page == "City Patterns":
    st.title("City Cohorts — a null result we trust")
    st.caption("All 14 (city, day-bucket) demand curves are statistically near-identical "
               "except Chennai-weekend and Kolkata-weekend.")

    shape = (df.groupby(["city", "day_bucket", "hour"]).size()
               .unstack("hour", fill_value=0))
    shape_norm = shape.div(shape.sum(axis=1), axis=0)

    fig = go.Figure()
    outliers = {("Chennai", "weekend"), ("Kolkata", "weekend")}
    for idx, row in shape_norm.iterrows():
        is_out = idx in outliers
        fig.add_trace(go.Scatter(
            x=list(range(24)), y=row.values,
            mode="lines+markers" if is_out else "lines",
            name=f"{idx[0]} ({idx[1]})" + (" — outlier" if is_out else ""),
            line=dict(width=3 if is_out else 1.4,
                      color="#d62728" if is_out and idx[0] == "Chennai"
                          else "#1f77b4" if is_out
                          else None),
            opacity=1.0 if is_out else 0.35,
        ))
    fig.update_layout(title="All 14 (city, day-bucket) demand-share curves",
                      xaxis_title="hour of day", yaxis_title="share",
                      xaxis=dict(dtick=2), yaxis=dict(tickformat=".1%"),
                      height=480)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
**What the dashboard shows.** Hide everything except the two outliers — they run a flatter, later
peak with mass extending past 22:00 on weekends. The other 12 curves are visually indistinguishable.

**Recommendation falling out:** ship the national policy edits from the *Waste & Gap* tab + a
small late-night weekend extension for Chennai and Kolkata only. Do not build cohort-tier rules.
""")


# ===========================================================
# Page 5 — Cuisine cuts
# ===========================================================
elif page == "Cuisine Cuts":
    st.title("Cuisine — does it change the recommendation?")
    st.caption("Notebook 05 §1. Cuisine volume is flat (~11% share each), but the dinner ramp-up has a cuisine signature.")

    cuisine_summary = (df.groupby("cuisine")
                         .agg(orders=("order_id", "size"),
                              surge_rate=("surge_applied", "mean"),
                              avg_value=("order_value", "mean"),
                              avg_delivery=("delivery_time_min", "mean"))
                         .sort_values("orders", ascending=False))
    cuisine_summary["share_%"] = (cuisine_summary.orders /
                                  cuisine_summary.orders.sum() * 100).round(1)

    st.subheader("Volume, surge rate, basket size, delivery time — per cuisine")
    st.dataframe(
        cuisine_summary.reset_index().style.format({
            "surge_rate": "{:.1%}", "avg_value": "₹{:.0f}",
            "avg_delivery": "{:.1f} min", "share_%": "{:.1f}%"}),
        use_container_width=True, hide_index=True,
    )

    st.divider()
    st.subheader("Who drives hour-18?")
    st.caption("Cuisine share at hour 18 vs overall share. Positive lift = the cuisine over-indexes at 6pm.")
    hr18 = df[df.hour == 18].cuisine.value_counts(normalize=True) * 100
    allsh = df.cuisine.value_counts(normalize=True) * 100
    lift = (hr18 - allsh).round(2).sort_values(ascending=False).reset_index()
    lift.columns = ["cuisine", "lift_pp"]

    fig = px.bar(lift, x="cuisine", y="lift_pp", height=380,
                 labels={"lift_pp": "share lift at hour 18 (percentage points)"},
                 color="lift_pp",
                 color_continuous_scale=[(0, "#1f77b4"), (0.5, "#cccccc"), (1, "#d62728")])
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("**Beverages and North Indian over-index** at hour 18 — they're the dinner-ramp signature. "
                "The hour-18 A/B test should stratify acceptance metrics by cuisine to confirm the boost lands there.")

    st.divider()
    st.subheader("AOV by cuisine")
    aov = df.groupby("cuisine").order_value.mean().sort_values(ascending=False).reset_index()
    fig = px.bar(aov, x="cuisine", y="order_value", height=360,
                 labels={"order_value": "AOV (₹)"},
                 color="order_value", color_continuous_scale="Blues")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("Sit-down style (Continental, Italian) carries ₹500+ AOV; snack-style (Beverages, Desserts) trails ~₹170.")


# ===========================================================
# Page 6 — Sanity check on surge
# ===========================================================
elif page == "Sanity Check — is surge buying speed?":
    st.title("Is the surge policy actually buying faster delivery?")
    st.caption("Notebook 05 §4. The most consequential finding of this investigation.")

    s1 = df[df.surge_applied == 1].delivery_time_min.mean()
    s0 = df[df.surge_applied == 0].delivery_time_min.mean()
    c1, c2, c3 = st.columns(3)
    c1.metric("Mean delivery, surge orders", f"{s1:.2f} min")
    c2.metric("Mean delivery, non-surge orders", f"{s0:.2f} min")
    c3.metric("Pooled difference", f"{s1 - s0:+.2f} min",
              delta=f"{(s1/s0 - 1)*100:+.1f}%", delta_color="inverse")

    st.warning(
        "**Pooled, surge orders are ~9% slower than non-surge orders.** "
        "Pooling is confounded by hour (surge fires in busy hours, which are slower for everyone). "
        "The honest comparison is *within-hour*, below."
    )

    ph = df.groupby(["hour", "surge_applied"]).delivery_time_min.mean().unstack().round(2)
    ph.columns = ["no_surge", "surge"]
    ph["diff_min"] = (ph.surge - ph.no_surge).round(2)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ph.index, y=ph.no_surge, mode="lines+markers",
                             name="no surge", line=dict(color="#1f77b4", width=3)))
    fig.add_trace(go.Scatter(x=ph.index, y=ph.surge, mode="lines+markers",
                             name="surge applied", line=dict(color="#d62728", width=3)))
    fig.update_layout(
        title="Within-hour delivery-time comparison",
        xaxis_title="hour of day", yaxis_title="mean delivery time (min)",
        xaxis=dict(dtick=2), height=460,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Within-hour difference table")
    st.dataframe(ph.reset_index().style.format(
        {"no_surge": "{:.2f}", "surge": "{:.2f}", "diff_min": "{:+.2f}"}),
        use_container_width=True, hide_index=True,
    )

    st.markdown("""
### The honest read

- **During peak hours (12, 13, 19, 20, 21):** surge and non-surge orders have **near-identical** mean delivery time.
  The surge incentive does not translate to a measurable speedup at the times surge actually fires.
- **During off-peak hours:** surge orders are **slower** — by up to 8 min at hour 0.

This is **observational, not causal** — surge fires deterministically by hour, so we cannot recover the
counterfactual. But the data does **not** support the assumption that surge is buying faster delivery.

### Consequence for the hour-18 A/B test

Re-design with delivery time as a primary outcome:

| Metric | Win condition |
|---|---|
| Rider acceptance rate, hour-18 window | ≥ +3 percentage points |
| **Mean delivery time, hour-18 window** | **No worse than baseline, ideally −1 min** |
| Total incentive cost per delivered order | ≤ +8% |

If the boost lifts acceptance but not delivery time, **pre-register a follow-up A/B that *removes* surge
from a small slice of peak-hour orders.** If removal doesn't hurt, the entire surge envelope is worth re-evaluating.
""")


# ===========================================================
# Page 7 — Forecast
# ===========================================================
elif page == "7-Day Forecast":
    st.title("7-Day Forecast — Delhi")
    st.caption("Daily order count, Holt-Winters (weekly seasonality). MAPE on walk-forward backtest.")

    delhi = (df[df.city == "Delhi"].groupby("date").size().rename("orders")
               .to_frame())
    delhi.index = pd.DatetimeIndex(delhi.index, freq="D")

    try:
        fc = pd.read_csv(OUT / "forecast.csv", parse_dates=["date"])
    except FileNotFoundError:
        st.warning("Run Notebook 04 first to generate outputs/forecast.csv.")
        st.stop()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=delhi.index, y=delhi.orders,
                             mode="lines", name="actual",
                             line=dict(color="black")))
    fig.add_trace(go.Scatter(x=fc.date, y=fc.forecast_orders,
                             mode="lines+markers", name="forecast",
                             line=dict(color=COLORS["WASTE"], width=3, dash="dash")))
    fig.update_layout(xaxis_title="date", yaxis_title="orders", height=440)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("MAPE on walk-forward backtest (3 windows × 7 days)")
    st.code("""
seasonal_naive   pooled = 11.01%   weekday = 11.82%   weekend = 8.98%
holt_winters     pooled =  8.61%   weekday =  9.61%   weekend = 6.11%   ← shipped
sarima           pooled =  8.97%   weekday =  9.96%   weekend = 6.49%
""")
    st.markdown("""
**Why not exotic.** The brief explicitly de-prioritises model sophistication. Holt-Winters
beats seasonal-naïve by ~22% relative MAPE and is one line of pickle to ship. Notebook 04
documents the 5 production monitors we'd put around it on day one.
""")

    st.divider()
    st.subheader("Forecast table (April 1–7, 2025)")
    st.dataframe(fc.assign(forecast_orders=lambda d: d.forecast_orders.round(0).astype(int)),
                 hide_index=True, use_container_width=True)
