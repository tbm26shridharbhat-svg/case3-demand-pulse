# Demand Pulse — Executive Summary

**For:** Ops Head · **From:** Case 3 investigation · **Date:** see repo commit log · **Read time:** 4 minutes

---

## The question, re-stated

You asked: *"Where are we over-paying surge during hours that aren't actually peak?"*

We re-read this as: *"Where is the current surge policy firing when it shouldn't, and where is it failing to fire when it should?"* — because the gap on **both** sides is the rupee question.

## Three things to act on Monday

### 1.  Don't change the lunch/dinner schedule. It mostly works.

96% of your surge spend fires in **above-median-demand cells** within each city. The current policy looks like a binary "surge ON at 12–13 (lunch) and 19–21 (dinner), ~5% everywhere else," and the data agrees with that structure. There is ~₹3.5k/month of pure waste — small (4% of envelope), cleanable through targeted rule edits per `outputs/top_waste_cells.csv`, **but not where the real money is.**

### 2.  Fix the dinner ramp-up at hour 18 — A/B test in one city first.

**Hour 18 (6pm) sees 3,683 pooled orders per hour-bucket** — peak-level demand, between hour 17's 1,832 and hour 19's 5,586. Surge fires there in only **5.7%** of cases versus **52%** at hour 19. This is the single biggest supply-gap signal in the dataset.

**Recommended test:** raise weekday hour-18 surge fire rate from ~6% to ~30% in **one city** (we'd pick Mumbai or Bangalore for traffic volume) for 14 days. Pre-register two success metrics:

| Metric | Pre-test | Win condition |
|---|---|---|
| Rider acceptance rate in hour-18 window | ~current baseline | ≥ +3 percentage points |
| Total cost per delivered order in window | ~current baseline | ≤ +8% |

If both metrics clear, roll to all 7 cities. If only the cost moves, **kill the test** — the gap is structural, not solvable with incentives.

Estimated additional surge spend in pilot city × 14 days at ₹20/order: small four-figure rupees. The decision quality is far above the spend.

### 3.  Ship a tiny weekend extension for Chennai and Kolkata only — that's it.

We hypothesised that cities cluster into demand-shape cohorts and would benefit from tier-specific schedules. **The data did not support this hypothesis.** Across all 14 (city, day-bucket) demand-share vectors, the maximum pairwise distance is ~0.05 — they are statistically indistinguishable. The only real deviation: **Chennai weekends and Kolkata weekends run a flatter, later peak**, with mass extending past 22:00.

Recommendation: keep current surge active until 23:00 on Saturdays and Sundays in **Chennai and Kolkata only**. Three rule edits total. No tier system. No model.

---

## Forecast (Delhi, Apr 1–7)

Daily order count, Holt-Winters with weekly seasonality:

| Date | Forecast | Day |
|---|---|---|
| Apr 1 (Tue) | 95 | weekday |
| Apr 2 (Wed) | 91 | weekday |
| Apr 3 (Thu) | 89 | weekday |
| Apr 4 (Fri) | 90 | weekday |
| Apr 5 (Sat) | 91 | **weekend** |
| Apr 6 (Sun) | 91 | **weekend** |
| Apr 7 (Mon) | 84 | weekday |

**Accuracy (3-window walk-forward backtest):**

| Model | Pooled MAPE | Weekday | Weekend |
|---|---|---|---|
| Seasonal-naive (baseline) | 11.0% | 11.8% | 9.0% |
| Holt-Winters (**shipped**) | **8.6%** | **9.6%** | **6.1%** |
| SARIMA | 9.0% | 10.0% | 6.5% |

Holt-Winters beats the seasonal-naive baseline by ~22% relative. Production monitors for this model are listed in Notebook 04, §6 — five concrete alarms, all fit in a single Airflow DAG.

---

## What this analysis explicitly does not claim

- We do not claim the policy is broken. **It mostly works.**
- We do not claim the cohort thesis is real. **We tested it and rejected it.** This simplifies your action set rather than complicates it.
- The rupee waste number assumes **₹20 per surge order**. If your real number is different, the magnitude scales linearly; the *share* (4% of envelope) is unit-free.
- The hour-18 recommendation is a **hypothesis**, not a guaranteed win. The A/B test is the way to find out without putting national spend at risk.

---

## Where to look in the repo

- **The number** — `outputs/cells.csv` has every (city, day-bucket, hour) cell classified.
- **The 10 cells to defuse first** — `outputs/top_waste_cells.csv`.
- **The 10 cells to invest in first** — `outputs/top_gap_cells.csv`.
- **The forecast** — `outputs/forecast.csv` (Apr 1–7, Delhi, daily).
- **Interactive view** — Streamlit dashboard, link in `README.md`.
