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
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/tbm26shridharbhat-svg/case3-demand-pulse",
        "Report a bug": "https://github.com/tbm26shridharbhat-svg/case3-demand-pulse/issues",
        "About": "Demand Pulse — Case 3 surge-policy investigation. "
                 "See README.md for the analytical story.",
    },
)

# ---------- mobile-first responsive CSS ----------
# Streamlit auto-stacks columns below ~640px; this CSS tightens type, spacing,
# and table behaviour so every one of the 10 dashboard pages reads cleanly on
# a 375px-wide phone (iPhone SE / smaller Android). Verified at:
#   - 375 × 667 (mobile portrait)
#   - 768 × 1024 (tablet portrait)
#   - 1440 × 900 (desktop)
st.markdown("""
<style>
/* Tables horizontal scroll on narrow viewports */
.stDataFrame, .stTable { overflow-x: auto !important; }

/* Plotly charts get a sensible minimum height on mobile */
.js-plotly-plot { min-height: 320px; }

/* Narrow phones — tighten spacing and shrink display type */
@media (max-width: 640px) {
  .main .block-container {
    padding-top: 1.0rem !important;
    padding-bottom: 2rem !important;
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
  }
  .stApp h1 { font-size: 1.5rem !important; line-height: 1.3 !important; }
  .stApp h2 { font-size: 1.2rem !important; }
  .stApp h3 { font-size: 1.05rem !important; }
  [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
  [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }

  /* Sidebar — narrower on mobile, less cramped nav */
  [data-testid="stSidebar"] { min-width: 240px !important; max-width: 280px !important; }
}

/* Tablet refinements */
@media (min-width: 641px) and (max-width: 1024px) {
  .stApp h1 { font-size: 1.85rem !important; }
  [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
}

/* Print-friendly view (Cmd+P → Save as PDF works cleanly) */
@media print {
  [data-testid="stSidebar"], header, footer { display: none !important; }
  .main .block-container { max-width: 100% !important; padding: 0.5cm !important; }
  .stPlotlyChart { page-break-inside: avoid; }
}
</style>
""", unsafe_allow_html=True)


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
     "Causal — propensity-score matching",
     "7-Day Forecast",
     "Per-City Forecasts",
     "A/B Test Simulator"],
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
The current surge policy is **mostly aligned with demand**: **{1 - waste.n_surge.sum() / total_surge_orders:.1%}**
of surge spend fires *outside* the WASTE class (below-median demand AND above-median surge fire rate).
The wasteful **{waste.n_surge.sum() / total_surge_orders:.1%}** is small ({int(waste.n_surge.sum())} surge events
over 90 days), recoverable through rule edits enumerated in the *Surge Waste & Supply Gap* tab.

The **larger lever is the dinner-ramp at hour 18**: peak-level demand (3,683 pooled orders/hour) currently
sees surge in only **5.7%** of cases versus **52.1%** at hour 19. Recommendation: A/B test a hour-18 surge
boost in one city's weekday window before national rollout — with **delivery time as a primary outcome**
(see *Sanity Check* tab for why).

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
# Page 6b — Causal sanity (PSM)
# ===========================================================
elif page == "Causal — propensity-score matching":
    st.title("Surge → delivery time: the matched estimate")
    st.caption("Notebook 06 §2. Hour-exact propensity-score matching with bootstrap 95% CI.")

    try:
        psm = pd.read_csv(OUT / "psm_results.csv")
    except FileNotFoundError:
        st.warning("Run Notebook 06 first to generate outputs/psm_results.csv.")
        st.stop()

    primary = psm[psm.estimator == "hour_exact_psm"].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Matched ATT", f"{primary.estimate_min:+.2f} min",
              delta=f"n={int(primary.n_pairs):,} pairs", delta_color="off")
    c2.metric("95% CI low", f"{primary.ci_low:+.2f} min")
    c3.metric("95% CI high", f"{primary.ci_high:+.2f} min",
              delta="includes zero" if primary.ci_low <= 0 <= primary.ci_high else "excludes zero",
              delta_color="off")

    st.info(
        "Hour-exact PSM matches each surge order to a non-surge order at the **same hour**, "
        "then within hour uses propensity from city + cuisine + weekend + log(value). "
        "The 95% bootstrap CI **straddles zero** — we cannot reject the null that surge "
        "has no effect on delivery time in the matched population."
    )

    st.subheader("All four estimates side by side")
    st.dataframe(
        psm[["estimator", "estimate_min", "ci_low", "ci_high", "n_pairs", "notes"]]
           .rename(columns={"estimate_min": "Δ delivery (min)",
                            "ci_low": "CI low", "ci_high": "CI high",
                            "n_pairs": "matched pairs"})
           .style.format({"Δ delivery (min)": "{:+.3f}",
                          "CI low": "{:+.3f}",
                          "CI high": "{:+.3f}"}, na_rep="—"),
        use_container_width=True, hide_index=True,
    )

    st.subheader("Per-hour matched diagnostic")
    st.caption("Match rate and matched delta per hour. Peak hours (12, 13, 19, 20, 21) drive the aggregate.")
    try:
        per_hour = pd.read_csv(OUT / "psm_per_hour.csv")
        fig = px.bar(per_hour, x="hour", y="mean_diff",
                     color="mean_diff",
                     color_continuous_scale=[(0, "#1f77b4"), (0.5, "#cccccc"), (1, "#d62728")],
                     labels={"mean_diff": "matched Δ delivery (min, surge − no-surge)",
                             "hour": "hour of day"},
                     height=380,
                     hover_data=["n_treated", "n_matched", "match_rate_%"])
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(per_hour, use_container_width=True, hide_index=True)
    except FileNotFoundError:
        st.caption("Per-hour breakdown not available.")


# ===========================================================
# Page 7 — Forecast (Mumbai)
# ===========================================================
elif page == "7-Day Forecast":
    st.title("7-Day Forecast — Mumbai")
    st.caption("Daily order count, Holt-Winters (weekly seasonality). MAPE on walk-forward backtest.")

    history = (df[df.city == "Mumbai"].groupby("date").size().rename("orders")
                 .to_frame())
    history.index = pd.DatetimeIndex(history.index, freq="D")

    try:
        fc = pd.read_csv(OUT / "forecast.csv", parse_dates=["date"])
    except FileNotFoundError:
        st.warning("Run Notebook 04 first to generate outputs/forecast.csv.")
        st.stop()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=history.index, y=history.orders,
                             mode="lines", name="actual",
                             line=dict(color="black")))
    fig.add_trace(go.Scatter(x=fc.date, y=fc.forecast_orders,
                             mode="lines+markers", name="forecast",
                             line=dict(color=COLORS["WASTE"], width=3, dash="dash")))
    fig.update_layout(xaxis_title="date", yaxis_title="orders", height=440)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("MAPE on walk-forward backtest (3 windows × 7 days) — Mumbai")
    st.code("""
seasonal_naive   pooled = 10.49%   weekday = 10.93%   weekend = 9.39%
holt_winters     pooled =  7.14%   weekday =  7.96%   weekend = 5.08%   ← shipped
sarima           pooled =  7.86%   weekday =  8.95%   weekend = 5.14%
""")
    st.markdown("""
**Why Mumbai, not the largest city.** Bangalore is largest by volume (10,776 orders) but produced
HW MAPE of 9.08%; Mumbai (10,022 orders) produced 7.14%. We pick on backtest evidence, not headline volume.

**Why not exotic.** The brief explicitly de-prioritises model sophistication. Holt-Winters beats
seasonal-naïve by **32% relative MAPE** and is one line of pickle to ship. Notebook 04 documents
the 5 production monitors we'd put around it on day one.
""")


# ===========================================================
# Page 8 — Per-city forecasts (Tier 1.4)
# ===========================================================
elif page == "Per-City Forecasts":
    st.title("Per-City Forecasts — does the model generalise?")
    st.caption("Notebook 04 §7. Holt-Winters fit on every city, walk-forward MAPE compared to seasonal-naïve.")

    try:
        per_city = pd.read_csv(OUT / "per_city_mape.csv")
        forecasts = pd.read_csv(OUT / "per_city_forecasts.csv", parse_dates=["date"])
    except FileNotFoundError:
        st.warning("Run Notebook 04 to generate outputs/per_city_mape.csv.")
        st.stop()

    wins = (per_city.HW_beats_naive_ > 0).sum() if False else (per_city["HW_beats_naive_%"] > 0).sum()
    losses = len(per_city) - wins
    c1, c2, c3 = st.columns(3)
    c1.metric("HW beats naïve", f"{wins} / {len(per_city)} cities")
    c2.metric("Best — lowest HW MAPE", per_city.iloc[0].city,
              delta=f"{per_city.iloc[0]['HW_MAPE_%']:.2f}%", delta_color="off")
    worst = per_city.iloc[-1]
    c3.metric("Worst", worst.city,
              delta=f"{worst['HW_MAPE_%']:.2f}% vs {worst['naive_MAPE_%']:.2f}% naïve",
              delta_color="inverse" if worst["HW_beats_naive_%"] < 0 else "off")

    st.subheader("MAPE comparison — ordered by HW performance")
    st.dataframe(
        per_city.style.format({
            "mean/day": "{:.1f}", "std/day": "{:.2f}",
            "naive_MAPE_%": "{:.2f}", "HW_MAPE_%": "{:.2f}",
            "HW_weekday_%": "{:.2f}", "HW_weekend_%": "{:.2f}",
            "HW_beats_naive_%": "{:+.1f}",
        }),
        use_container_width=True, hide_index=True,
    )

    st.markdown("""
**The headline finding.** Holt-Winters beats the seasonal-naïve baseline in **6 of 7 cities**.
The one exception is **Kolkata**, where HW is 0.5% *worse* than the baseline — the
city's low volume (~44 orders/day) and weekend outlier pattern (Notebook 03) destabilise the model.
**Ship the seasonal-naïve baseline for Kolkata; ship HW everywhere else.** This is a per-city
deployment decision, not a single-model decision.
""")

    st.subheader("April 1–7 forecasts — every city")
    fc_wide = forecasts.pivot(index="date", columns="city", values="forecast_orders")
    fig = go.Figure()
    for city in fc_wide.columns:
        fig.add_trace(go.Scatter(x=fc_wide.index, y=fc_wide[city],
                                 mode="lines+markers", name=city, line=dict(width=3)))
    fig.update_layout(
        title="7-day forecast trajectories, all cities",
        xaxis_title="date", yaxis_title="forecast orders/day",
        height=460,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        fc_wide.round(0).astype(int),
        use_container_width=True,
    )


# ===========================================================
# Page 10 — A/B Test Simulator (Tier 2 #1)
# ===========================================================
elif page == "A/B Test Simulator":
    from scipy import stats as _stats

    st.title("A/B Test Simulator")
    st.caption(
        "Notebook 07's power analysis, made interactive. Plug in your test parameters; "
        "the simulator tells you required sample size, achievable power, and runs a "
        "1,000-trial Monte Carlo to show how the test will actually behave."
    )

    st.subheader("Inputs")
    c1, c2, c3 = st.columns(3)
    with c1:
        baseline_acc = st.slider("Baseline acceptance rate", 0.50, 0.95, 0.80, 0.01,
                                 help="What % of orders currently get accepted by riders.")
        lift_pp = st.slider("Expected lift (pp)", 0.01, 0.20, 0.04, 0.005,
                            help="Hypothesised improvement, in percentage points.")
    with c2:
        orders_per_day = st.number_input("Orders/day in the test window",
                                         min_value=1, max_value=10000, value=17, step=1,
                                         help="Mumbai hour-18 7-day window: ~17 orders/day. "
                                              "Default matches Notebook 07.")
        duration_days = st.slider("Test duration (days)", 7, 90, 14, 1)
    with c3:
        alpha = st.select_slider("α (Bonferroni-corrected)",
                                 options=[0.05, 0.025, 0.0167, 0.01, 0.005],
                                 value=0.0167,
                                 help="0.0167 = 0.05 / 3 outcomes (Bonferroni).")
        target_power = st.slider("Target power", 0.50, 0.95, 0.80, 0.05)

    treated_acc = min(baseline_acc + lift_pp, 0.999)
    n_per_arm = int(orders_per_day * duration_days / 2)

    # === Required N (closed form) ===
    z_alpha = _stats.norm.ppf(1 - alpha / 2)
    z_beta = _stats.norm.ppf(target_power)
    p_bar = (baseline_acc + treated_acc) / 2
    required_n = int(np.ceil(((z_alpha * np.sqrt(2 * p_bar * (1 - p_bar)) +
                               z_beta * np.sqrt(baseline_acc * (1 - baseline_acc) +
                                                treated_acc * (1 - treated_acc))) / lift_pp) ** 2))

    # === Achieved power at the configured N ===
    se = np.sqrt(baseline_acc * (1 - baseline_acc) / n_per_arm +
                 treated_acc * (1 - treated_acc) / n_per_arm)
    z_obs_thresh = (treated_acc - baseline_acc) / se
    achieved = float(_stats.norm.cdf(z_obs_thresh - z_alpha))

    days_for_required = int(np.ceil(2 * required_n / orders_per_day))

    st.subheader("Results")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Required N / arm", f"{required_n:,}",
              delta=f"for {target_power:.0%} power", delta_color="off")
    r2.metric("Achieved N / arm at {} days".format(duration_days), f"{n_per_arm:,}",
              delta=f"{'✓ enough' if n_per_arm >= required_n else '✗ short'}",
              delta_color="normal" if n_per_arm >= required_n else "inverse")
    r3.metric("Achieved power", f"{achieved:.1%}",
              delta=f"vs target {target_power:.0%}",
              delta_color="normal" if achieved >= target_power else "inverse")
    r4.metric("Days needed for full power",
              f"{days_for_required}" if days_for_required < 365 * 5 else "5y+",
              delta="at current order rate", delta_color="off")

    if achieved < target_power:
        st.warning(
            f"**Test is under-powered.** With {n_per_arm:,} orders/arm at α={alpha}, "
            f"power to detect a +{lift_pp:.0%} lift is only **{achieved:.1%}** "
            f"— far below the {target_power:.0%} target. Options: extend duration "
            f"to **{days_for_required} days**, increase the per-day order rate, "
            f"or accept a lower MDE."
        )
    else:
        st.success(
            f"**Test has adequate power.** {n_per_arm:,} orders/arm achieves "
            f"**{achieved:.1%}** power vs the {target_power:.0%} target."
        )

    st.divider()

    # === Power curve as a function of lift ===
    st.subheader("Power curve at the configured sample size")
    lifts = np.linspace(0.005, 0.20, 80)
    powers = []
    for lf in lifts:
        t = min(baseline_acc + lf, 0.999)
        s = np.sqrt(baseline_acc * (1 - baseline_acc) / n_per_arm +
                    t * (1 - t) / n_per_arm)
        powers.append(float(_stats.norm.cdf((t - baseline_acc) / s - z_alpha)))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=lifts * 100, y=powers, mode="lines",
                             line=dict(color=COLORS["WASTE"], width=3),
                             name="achieved power"))
    fig.add_hline(y=target_power, line=dict(color="black", dash="dash", width=2),
                  annotation_text=f"target {target_power:.0%}", annotation_position="bottom right")
    fig.add_vline(x=lift_pp * 100, line=dict(color=COLORS["SUPPLY_GAP"], dash="dot", width=2),
                  annotation_text=f"your target lift = +{lift_pp:.0%}",
                  annotation_position="top right")
    fig.update_layout(
        title=f"Power vs lift, at N={n_per_arm:,} per arm and α={alpha}",
        xaxis_title="lift (percentage points)", yaxis_title="achieved power",
        xaxis=dict(tickformat=".0f", ticksuffix="pp"),
        yaxis=dict(tickformat=".0%", range=[0, 1]),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

    # === Monte Carlo: 1,000 simulated trials ===
    st.divider()
    st.subheader("Monte Carlo — 1,000 simulated trials at your settings")

    rng = np.random.default_rng(42)
    n_trials = 1000
    p_values = np.empty(n_trials)
    effect_estimates = np.empty(n_trials)

    for i in range(n_trials):
        c_sample = rng.binomial(1, baseline_acc, n_per_arm)
        t_sample = rng.binomial(1, treated_acc, n_per_arm)
        p_c = c_sample.mean()
        p_t = t_sample.mean()
        p_pool = (c_sample.sum() + t_sample.sum()) / (2 * n_per_arm)
        se_test = np.sqrt(p_pool * (1 - p_pool) * (2 / n_per_arm))
        if se_test > 0:
            z = (p_t - p_c) / se_test
            p_values[i] = 2 * (1 - _stats.norm.cdf(abs(z)))
        else:
            p_values[i] = 1.0
        effect_estimates[i] = p_t - p_c

    detection_rate = (p_values < alpha).mean()

    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Trials where p < α", f"{int((p_values < alpha).sum()):,} / {n_trials:,}",
               delta=f"{detection_rate:.1%} detection rate", delta_color="off")
    cc2.metric("Mean estimated lift", f"{effect_estimates.mean() * 100:+.2f}pp",
               delta=f"true: +{lift_pp * 100:.1f}pp", delta_color="off")
    cc3.metric("Std of effect estimate", f"{effect_estimates.std() * 100:.2f}pp",
               delta="Monte Carlo noise", delta_color="off")

    sim_fig = go.Figure()
    sim_fig.add_trace(go.Histogram(x=effect_estimates * 100, nbinsx=40,
                                   marker=dict(color=COLORS["SUPPLY_GAP"]),
                                   opacity=0.85, name="estimated lift"))
    sim_fig.add_vline(x=lift_pp * 100, line=dict(color=COLORS["WASTE"], width=3),
                      annotation_text=f"true effect +{lift_pp * 100:.1f}pp",
                      annotation_position="top right")
    sim_fig.add_vline(x=0, line=dict(color="black", dash="dot"),
                      annotation_text="null = 0", annotation_position="top left")
    sim_fig.update_layout(
        title="Distribution of estimated lifts across 1,000 simulated trials",
        xaxis_title="estimated lift (percentage points)",
        yaxis_title="trials", height=420,
    )
    st.plotly_chart(sim_fig, use_container_width=True)

    st.info(
        "**How to read this.** The histogram shows where the test would land if you "
        "ran it 1,000 times. The wider the spread, the noisier the estimate — so if "
        "the histogram extends through zero, plenty of trials will fail to reject the "
        "null even when the true effect is non-zero. That's what 'under-powered' means "
        "visually."
    )

    st.divider()
    st.subheader("Recommended next step based on these inputs")
    if achieved >= target_power:
        st.markdown(
            f"- **Ship the test as configured.** {duration_days} days at the current "
            f"order rate gives you {achieved:.0%} power. Pre-register the +{lift_pp:.0%} "
            f"lift target before day 0."
        )
    elif days_for_required <= 90:
        st.markdown(
            f"- **Extend to {days_for_required} days.** Same scope, same arms — just "
            f"more time. Reaches {target_power:.0%} power."
        )
    else:
        st.markdown(
            f"- **The test as configured is structurally under-powered.** Even running "
            f"for {days_for_required} days hits {target_power:.0%} power. Three honest options:\n"
            f"  1. **Pivot the primary outcome** to delivery time (continuous, lower variance, "
            f"     much higher power per observation — see Notebook 07 §3).\n"
            f"  2. **Widen the test scope** — multi-city, wider hour window. 3× order rate "
            f"     ≈ 1/3 the duration.\n"
            f"  3. **Accept a larger MDE.** Detecting a +{(lift_pp * 1.5) * 100:.0f}pp lift "
            f"     instead of +{lift_pp * 100:.0f}pp roughly halves the required N."
        )

    st.divider()
    st.subheader("Forecast table (April 1–7, 2025)")
    st.dataframe(fc.assign(forecast_orders=lambda d: d.forecast_orders.round(0).astype(int)),
                 hide_index=True, use_container_width=True)
