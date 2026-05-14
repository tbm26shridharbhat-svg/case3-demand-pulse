# Decisions Log — Case 3

## Assumptions I made

1. **Surge cost = ₹20 per surge-applied order.** The dataset has a binary `surge_applied` flag but no cost field. ₹20 is the typical range on Indian aggregators (₹15–₹25). The notebook and the dashboard both expose this as a single variable so the Ops Head can swap her real cost in and re-run.
2. **Day-bucket = `weekend` (Sat/Sun) vs `weekday`.** Three- or four-way bucketing was considered, but with 50k orders / 90 days / 7 cities, finer buckets fall below ~50 orders/cell and statistical noise dominates.
3. **"Low demand" means bottom-50% within the same city.** Mumbai's bottom-half is not Pune's top-half. Normalising globally would have penalised smaller cities for being small, not for being miscalibrated. This is the most consequential analysis choice in Notebook 02.
4. **Forecast city = Delhi.** Largest by volume → most stable signal. Notebook 03 concluded the demand shape generalises across cities, so Delhi was sufficient for the brief's "at least one city" ask.
5. **Forecast horizon = 7 days, daily resolution.** Daily was the honest call given 90 days of training data ≈ 13 weekly cycles. Hourly stretch goal de-scoped.
6. **Baseline = seasonal-naive (y_t = y_{t-7}).** Anything we ship must beat this; otherwise the data has no signal beyond the weekly cycle.

## Trade-offs

| Choice | Alternative considered | Why I picked this |
|---|---|---|
| **Cell granularity (city, day-bucket, hour)** | Per-day-of-week × hour (1,176 cells) | Finer buckets had ~40 orders/cell on average → noisy. Day-bucket gives ~150 orders/cell, statistically defensible. |
| **Within-city percentile rank** | Global percentile rank | Within-city is the only honest normalisation. Mumbai's slowest hour out-trades Pune's busiest by raw count; using global rank would mis-label Pune's peak as low-demand. |
| **Hierarchical clustering (Ward)** | K-means with k=3 | 14 vectors is too small for k-means to be trustworthy. Hierarchical gives us a dendrogram we can defend visually, and a silhouette score we can read honestly. |
| **Holt-Winters as the shipped forecaster** | SARIMA(1,1,1)(1,1,1,7); Prophet | Holt-Winters won the pooled MAPE (8.61% vs SARIMA's 8.97%) on a 3-window walk-forward backtest. One line of pickle to ship. Prophet excluded — Python 3.14 builds are flaky and the gain doesn't justify the dependency risk. |
| **Plotly over Matplotlib** | Matplotlib | Plotly's interactive output embeds directly into Streamlit. The notebook → dashboard hand-off becomes near-zero-cost. |
| **Honest null result in Notebook 03** | Force k=2 clustering and tell a cohort story anyway | The data does not support a cohort story. Fabricating one would have been a worse demo than the honest one. |

## What I de-scoped and why

- **Hourly forecast.** Brief allowed hourly *or* daily. With 90 days of data, the hourly SARIMA would have huge confidence intervals and the daily model is what the Ops Head actually wants for staffing decisions. Documented in Notebook 04.
- **A/B test design memo.** The recommendation surfaces an A/B but doesn't carry it to a formal MDE / sample-size memo. ~2 hours of focused work; reserved for the second case.
- **Per-city forecasts for all 7 cities.** Notebook 03's null result justified single-city scope: the demand shapes generalise.
- **Holiday / weather features.** Adding holiday flags would have moved daily MAPE by perhaps 1–2 percentage points. The production-monitoring plan in Notebook 04 covers the gap operationally (suppress alarms on holiday weeks).
- **Confidence intervals in the dashboard.** Point forecasts are easier to act on; CIs are noise in an Ops Head conversation. Two lines of code away if needed.

## What I'd do differently with another day

- **Per-city Holt-Winters in parallel, served via a model-registry pattern.** Just to prove the generalisation claim from Notebook 03 with real numbers.
- **A causal-style analysis on existing surge fire events** — does surge actually reduce delivery-time-min in the data, or is it just labeled noise? Even a simple matched-pairs comparison would be a useful sanity check on whether the policy is buying what it thinks it's buying.
- **Spatial dimension.** The dataset has restaurant_id but no lat/lon. With even a coarse geo, the "supply gap" finding becomes 10x more actionable (which neighbourhoods in Delhi are gap-hot at hour 18?).
- **Productionise the dashboard** with proper auth (Streamlit Cloud + Google SSO) rather than the free HF Spaces deployment, so it can be the durable companion to a Monday-morning ops meeting.

## AI assistant usage (for transparency, per the brief's FAQ)

I used Claude Code to scaffold the notebook builder pattern (`nbformat`-driven), write the initial Streamlit page wiring, and review the notebook narratives. Every analytical decision — cell granularity, percentile-rank framing, the honest call on the cohort null result, the choice to lead with the supply-gap finding rather than overstate waste — was mine, and I can defend any line of code or argument on a video walkthrough.
