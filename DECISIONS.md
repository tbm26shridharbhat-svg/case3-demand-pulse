# Decisions Log — Case 3

## Assumptions I made

1. **Surge cost = ₹20 per surge-applied order.** The dataset has a binary `surge_applied` flag but no cost field. ₹20 is the typical range on Indian aggregators (₹15–₹25). The notebook and the dashboard both expose this as a single variable so the Ops Head can swap her real cost in and re-run.
2. **Day-bucket = `weekend` (Sat/Sun) vs `weekday`.** Three- or four-way bucketing was considered, but with 50k orders / 90 days / 7 cities, finer buckets fall below ~50 orders/cell and statistical noise dominates.
3. **"Low demand" means bottom-50% within the same city.** Mumbai's bottom-half is not Pune's top-half. Normalising globally would have penalised smaller cities for being small, not for being miscalibrated. This is the most consequential analysis choice in Notebook 02.
4. **Forecast city = Mumbai.** Among the top-3 cities by volume (Bangalore 10,776, Mumbai 10,022, Delhi 8,171), Mumbai produced the lowest walk-forward MAPE on a fair head-to-head: Holt-Winters pooled MAPE of **7.14%** vs Delhi's 8.61% and Bangalore's 9.08%. Notebook 03 already concluded that demand shape generalises across cities, so the choice was non-consequential to the policy recommendations — picked on backtest evidence rather than headline volume.
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
- **Confidence intervals in the dashboard.** Point forecasts are easier to act on; CIs are noise in an Ops Head conversation. Two lines of code away if needed.
- **Restaurant-level targeting.** The supplied dataset shows uniform volume across the 800 restaurants (top-100 own only 15% — a synthetic-data tell, flagged in Notebook 05 §2). Restaurant-level cuts cannot be shipped from this data and are deferred until real production logs are available.
- **A fully causal claim on surge → delivery time.** Notebook 06 closes the gap as far as observational data permits (hour-exact PSM with bootstrap CI). Unobservable confounders remain — most plausibly distance-to-drop, rider-density-at-pickup, kitchen-prep latency. The follow-up A/B in Slide 5 Action 4 is the only thing that turns observation into evidence.

## What I added beyond the brief

The brief asks for: notebook, deck, exec summary, forecast CSV. Those are required. Below the line, I shipped four more things because the analysis pushed me there:

- **Notebook 06 — hour-exact propensity-score matching** with bootstrap CI on the surge → delivery question. Turns NB05's qualitative within-peak observation into a formal matched ATT of **+0.13 min, 95% CI [−0.19, +0.46]** across 11,937 pairs. Includes a standard-PSM cautionary tale (biased to +0.65 by cross-hour matches) so the methodological choice is defensible.
- **Notebook 07 — A/B power analysis + pre-registration**. Caught that the original recommended +3pp acceptance threshold is severely under-powered at the dataset's volume. Pivoted to delivery-time-primary, acceptance-descriptive, with a verbatim pre-registration document ready to commit to the experiment platform on day 0.
- **Notebook 04 §7 — per-city Holt-Winters generalisation**. Holt-Winters wins 6/7 cities; **Kolkata is the exception** (HW worse than seasonal-naïve by 0.5%). Production rule that fell out: per-city model deployment, with Kolkata on the naïve baseline.
- **Notebook 08 — SARIMAX with holiday + weather exog features**. Drops Mumbai SARIMA MAPE from 7.86% to 7.61%. Holt-Winters at 7.14% still wins overall — holiday flag worth shipping, weather feed deferred until monsoon data.
- **Reproducibility layer**: `audit_truth.json` (98-key lock), `scripts/canonical_audit.py --verify`, 18 pytest tests, GitHub Actions CI. Any code change that drifts a number breaks the build.

## What I'd do differently with another day

- **Spatial dimension.** The dataset has restaurant_id but no lat/lon. With even a coarse geo, the "supply gap" finding becomes 10× more actionable (which neighbourhoods in Mumbai are gap-hot at hour 18?).
- **Propensity-score-weighted regression as a robustness check on Notebook 06.** Hour-exact matching + within-hour propensity is one estimator; an IPTW-weighted regression with the same covariates would be a useful second opinion. I'd expect the same answer.
- **Productionise the dashboard** with proper auth (Streamlit Cloud + Google SSO) rather than the free HF Spaces deployment, so it can be the durable companion to a Monday-morning ops meeting.
- **Cuisine substitution analysis.** If we suppress surge for one cuisine, does demand shift to another? The dataset has enough cuisine variety to test this; I didn't have time to set up the conditional analysis carefully.

## What I'd actually say in a meeting

The decisions log above is the polished version. Here's the same content in the voice I'd use if you asked me to walk through this over coffee — less tidy, more honest.

- **On the WASTE class definition.** The bottom-50%-demand-AND-top-50%-surge cell definition is conservative. A wider definition ("any surge in below-median demand cells") would have given me a ₹10.6k / 90d headline number instead of ₹7,860 — and for a moment I wanted that bigger number because bigger numbers tell better stories. I caught the impulse. The class definition stayed.
- **On dropping the cohort hypothesis.** I genuinely walked in believing a tier system would win. The maximum pairwise distance came back at 0.052 and I sat with that for a while. Publishing a null result is rare in case studies because the implicit incentive is to make every angle "work." This one mattered more honestly null than fake-tiered.
- **On Mumbai instead of Bangalore.** Embarrassing. I assumed Mumbai was the biggest city for the forecast and only found out it was third when the audit script printed volumes. The fix was to re-run on all three top cities and pick on backtest evidence (Mumbai won). The audit lock paid for itself the day it was written.
- **On the PSM call.** Standard PSM gave +1.31 min and I knew it was wrong before I knew why. Hour-exact matching brought it to +0.13 min. The lesson — *propensity overlap doesn't mean comparable units* — is one I'll carry into the next causal analysis I do.
- **On the A/B test pivot.** The original deck draft promised an acceptance-rate lift the dataset can't statistically support at 14 days. Discovering this in the power analysis was uncomfortable; rewriting the recommendation around delivery-time-primary turned out to be the stronger story anyway. Real-world Swiggy-scale data wouldn't have this constraint at all, but on this dataset the recommendation has to respect the maths.
- **On the AI use.** I used Claude Code throughout — for scaffolding, prose review, and the audit infrastructure. Every analytical decision is mine and I can defend any of them on the call. The disclosure block below is deliberate, not boilerplate.

## AI assistant usage (full disclosure, per the brief's FAQ)

What Claude Code did:
- Scaffolded the notebook-builder pattern (`nbformat`-driven, one Python script per notebook). The cell *structure* is templated; the prose inside each cell is mine, edited and re-edited.
- Wrote initial Streamlit page wiring (page routing, the `@st.cache_data` pattern, layout boilerplate). All page content, copy, and analytical computations are mine.
- Polished prose in README, exec_summary, and the deck markdown. I edited every paragraph.
- Wrote the audit-lock script and the pytest harness from my spec. I review every assertion.
- Generated the deck slides via Claude Design, from a prompt I wrote and iterated on. Each slide's content (numbers, words, layout intent) was specified by me before generation.

What I did:
- Every analytical decision — the reframe of the brief, the within-city percentile choice, the WASTE class definition, killing the cohort hypothesis honestly, the choice to lead with the supply-gap finding rather than overstate waste, the Mumbai-not-Bangalore switch on backtest evidence, the hour-exact PSM choice over standard PSM, pivoting the A/B to delivery-time-primary on power-analysis grounds, the per-city Kolkata exception.
- The verification work — running `canonical_audit.py` and cross-referencing every number in every document until 98 keys reconciled.
- The voice of the writeup (`STORY.md`, `NOTES.md`, this document's "What I'd actually say in a meeting" section).
- The Q&A defence: I can walk through any notebook line-by-line on the demo call without re-reading it.

If the panel wants to verify ownership on any specific decision, I'm happy to talk through the trade-off in real time.
