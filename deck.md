---
marp: true
theme: default
paginate: true
size: 16:9
header: 'Demand Pulse · Case 3'
footer: 'Confidential · for the Ops Head'
style: |
  section { font-family: -apple-system, "Helvetica Neue", sans-serif; font-size: 26px; }
  h1 { color: #0b3d91; }
  h2 { color: #0b3d91; }
  strong { color: #d62728; }
  table { font-size: 22px; }
  .small { font-size: 18px; color: #666; }
---

# Surge policy — honestly read

### Where we're over-paying, where we're under-firing, and what to ship Monday

50,000 orders · 7 cities · 9 cuisines · Jan–Mar 2025

<br>

<span class="small">Investigation · 1 working day · solo</span>

---

## 1.  The question, re-stated

> The Ops Head's brief: *"we're over-paying surge in hours that aren't actually peak"*

We re-framed this as the **two-sided** question:

- **Where is surge firing when it shouldn't?** → wasteful spend
- **Where is surge not firing when it should?** → supply gap

The whole investigation hangs on putting a **rupee number on both sides**.

---

## 2.  Approach

| Step | Decision | Why |
|---|---|---|
| Slice | (city, day-bucket, hour) → 336 cells | ~150 orders/cell, statistically honest |
| Rank | **Within-city** percentile of demand & surge | Mumbai's slow hour ≠ Pune's busy hour |
| Classify | WASTE / SUPPLY_GAP / ALIGNED | Defensible to a non-analyst |
| Forecast | Holt-Winters daily, walk-forward MAPE | Beats seasonal-naive by 22%, one line to ship |
| Test cohorts | Hierarchical clustering on demand shape | Null result is also a result |

---

## 3.  The build — what the data shows

![bg right:50% w:600](outputs/figures/02_pooled_hour_demand_vs_surge.html)

- Grey bars = hourly demand share · Red line = surge fire rate
- **Hour 18 is the gap**: 3,683 orders/hour, but surge fires only **5.7%** vs **52%** at hour 19
- Lunch (12–13) and dinner (19–21) are well-aligned — current policy is mostly correct
- Cohort hypothesis tested → **rejected**: max pairwise distance across 14 demand-shape vectors = 0.05

---

## 4.  Outcome — three numbers and three actions

| Finding | Number | Action |
|---|---|---|
| WASTE (90d) | **₹10.6k** (~4% of envelope) | Defuse top-10 cells per CSV |
| SUPPLY GAP — hour 18 | **3,000+** extra surge orders needed | **A/B test one city** for 14 days |
| Cohort signal | Only Chennai-wknd, Kolkata-wknd | Late-night weekend extension only |

Forecast: **Holt-Winters MAPE 8.6%** (pooled) vs 11.0% baseline · April 1–7 forecast committed in `outputs/forecast.csv`.

---

## 5.  What's next

1. **Run the hour-18 A/B in one city** — pre-registered acceptance + cost-per-delivery metrics, kill condition baked in
2. **Two-line rule edit** for Chennai/Kolkata weekend late-night surge
3. **Ship the 5 production monitors** from Notebook 04 §6 around the forecast (daily MAPE alarm, holiday calendar, drift band, weekly backtest cron)
4. With another day: per-city forecasts, causal sanity check on whether surge actually reduces delivery time, neighbourhood-level supply gap if geo joins are available

<br>

<span class="small">Repo · Dashboard · Notebooks · Exec Summary — links in README.md</span>
