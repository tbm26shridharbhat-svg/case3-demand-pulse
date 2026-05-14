# Demand Pulse — Executive Summary

**For:** Ops Head · **From:** Case 3 investigation · **Date:** see repo commit log · **Read time:** 4 minutes

---

## The question, re-stated

You asked: *"Where are we over-paying surge during hours that aren't actually peak?"*

We re-read this as: *"Where is the current surge policy firing when it shouldn't, and where is it failing to fire when it should?"* — because the gap on **both** sides is the rupee question.

## Four things to act on Monday

### 1.  Don't change the lunch/dinner schedule. It mostly works.

95.5% of your surge spend fires in **above-median-demand cells** within each city. The current policy looks like a binary "surge ON at 12–13 (lunch) and 19–21 (dinner), ~5% everywhere else," and the data agrees with that structure.

Specifically, the **WASTE class** — cells that are below-median demand within their city *and* above-median surge fire rate — contains **393 surge events** over the 90-day window (**3.3% of the total 11,937 surge events**). At ₹20 per surge order that is **₹7,860 over 90 days, or ₹2,620/month**. Small. Cleanable through the rule edits in `outputs/top_waste_cells.csv`, **but not where the real money is.**

### 2.  Fix the dinner ramp-up at hour 18 — A/B test in one city first.

**Hour 18 (6pm) sees 3,683 pooled orders per hour-bucket** — peak-level demand, between hour 17's 1,832 and hour 19's 5,586. Surge fires there in only **5.7%** of cases versus **52%** at hour 19. This is the single biggest supply-gap signal in the dataset.

**Recommended test:** raise weekday hour-18 surge fire rate from ~6% to ~30% in **one city** (we'd pick Mumbai or Bangalore for traffic volume) for 14 days. Pre-register **three** success metrics — including delivery time, see §3 for why:

| Metric | Pre-test | Win condition |
|---|---|---|
| Rider acceptance rate, hour-18 window | baseline | ≥ +3 percentage points |
| **Mean delivery time, hour-18 window** | baseline | **No worse than baseline, ideally −1 min** |
| Total cost per delivered order in window | baseline | ≤ +8% |

If acceptance lifts but delivery time doesn't, **kill the test**. The gap is structural, not solvable with incentives.

Hour 18 over-indexes on **Beverages and North Indian** (+1.1pp, +0.9pp share lift). The A/B should stratify acceptance metrics by cuisine to confirm the boost lands on dinner-ramp cuisines as expected.

### 3.  Ask the bigger question: is the current peak-hour surge buying anything?

Notebook 05 §4 shows that **within peak hours, surge-applied orders and non-surge orders have near-identical delivery time** (within 0.5 min). Pooled, surge orders are 9% *slower* — and that's confounded by hour, but the within-hour comparison eliminates the confound. The data does **not** support the assumption that surge is buying faster delivery.

**Recommended follow-up A/B (after hour-18 test concludes):** remove surge from a small (~5%) random slice of peak-hour orders for 14 days. Outcome metric: mean delivery time and rider acceptance. **If removal doesn't hurt either metric, the entire surge envelope is worth re-evaluating.** This is observational evidence, not causal — but it's the strongest reason in the dataset to question the policy.

### 4.  Ship a tiny weekend extension for Chennai and Kolkata only — that's it.

We hypothesised that cities cluster into demand-shape cohorts and would benefit from tier-specific schedules. **The data did not support this hypothesis.** Across all 14 (city, day-bucket) demand-share vectors, the maximum pairwise distance is ~0.05 — they are statistically indistinguishable. The only real deviation: **Chennai weekends and Kolkata weekends run a flatter, later peak**, with mass extending past 22:00.

Recommendation: keep current surge active until 23:00 on Saturdays and Sundays in **Chennai and Kolkata only**. Three rule edits total. No tier system. No model.

---

## Forecast (Mumbai, Apr 1–7)

Daily order count, Holt-Winters with weekly seasonality. Mumbai was chosen because among the top-3 cities by volume (Bangalore 10,776, Mumbai 10,022, Delhi 8,171), Mumbai produced the **lowest walk-forward MAPE** on a fair comparison — see Notebook 04 §1 and §3 for the per-city table.

| Date | Forecast | Day |
|---|---|---|
| Apr 1 (Tue) | 110 | weekday |
| Apr 2 (Wed) | 109 | weekday |
| Apr 3 (Thu) | 106 | weekday |
| Apr 4 (Fri) | 106 | weekday |
| Apr 5 (Sat) | 107 | **weekend** |
| Apr 6 (Sun) | 111 | **weekend** |
| Apr 7 (Mon) | 108 | weekday |

**Accuracy (3-window walk-forward backtest, Mumbai):**

| Model | Pooled MAPE | Weekday | Weekend |
|---|---|---|---|
| Seasonal-naïve (baseline) | 10.5% | 10.9% | 9.4% |
| Holt-Winters (**shipped**) | **7.1%** | **8.0%** | **5.1%** |
| SARIMA | 7.9% | 9.0% | 5.1% |

Holt-Winters beats the seasonal-naïve baseline by **32% relative MAPE**. Production monitors for this model are listed in Notebook 04, §6 — five concrete alarms, all fit in a single Airflow DAG.

---

## What this analysis explicitly does not claim

- We do not claim the policy is broken. **It mostly works.**
- We do not claim the cohort thesis is real. **We tested it and rejected it.** This simplifies your action set rather than complicates it.
- The rupee waste number assumes **₹20 per surge order**. If your real number is different, the magnitude scales linearly; the *share* (3.3% of surge envelope, or 4.5% if you broaden "waste" to any surge in below-median-demand cells regardless of surge rate) is unit-free.
- The hour-18 recommendation is a **hypothesis**, not a guaranteed win. The A/B test is the way to find out without putting national spend at risk.
- The delivery-time finding (§3) is **observational, not causal**. Surge fires deterministically by hour, so we cannot recover the counterfactual from the data alone. The follow-up A/B is the way to convert this observation into evidence.
- Restaurant-level recommendations are **out of scope** because the supplied dataset shows uniform volume across all 800 restaurants (top-100 own only 15%). This pattern is unrealistic for production data and likely an artefact of synthetic generation. Re-do this analysis on real order logs and the top-restaurant cut becomes the most actionable lever in the deck.

---

## Where to look in the repo

- **The number** — `outputs/cells.csv` has every (city, day-bucket, hour) cell classified.
- **The 10 cells to defuse first** — `outputs/top_waste_cells.csv`.
- **The 10 cells to invest in first** — `outputs/top_gap_cells.csv`.
- **The surge sanity-check finding** — `notebooks/05_deeper_cuts.ipynb` §4.
- **Cuisine signal at hour 18** — `notebooks/05_deeper_cuts.ipynb` §1.2.
- **The forecast** — `outputs/forecast.csv` (Apr 1–7, Mumbai, daily).
- **Interactive view** — Streamlit dashboard (7 pages), link in `README.md`.
