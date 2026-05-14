# Submission Notes — Case 3

## Known issues / honest caveats

- **Live demo:** deployed to Hugging Face Spaces · <https://shridharbhat820-demand-pulse.hf.space>  ·  Space page: <https://huggingface.co/spaces/shridharbhat820/demand-pulse>.
- **Deck PDF** is the canonical artifact submitted alongside this repo. Generated via Claude Design from the prompt in `deck_prompt_v3_densify.md` (since removed); design system + numbers documented in `AUDIT.md` for traceability.
- **Demo video link** — to be added at the top of README.md once recorded (Loom/YouTube unlisted).

## What the panel should look at first

1. `exec_summary.md` — the one-page Ops Head deliverable.
2. `notebooks/05_deeper_cuts.ipynb` §4 — the surge-vs-delivery-time sanity check. **The single highest-signal section of the submission.**
3. `notebooks/02_surge_waste.ipynb` — the main analytical bet (waste vs supply-gap framing).
4. `notebooks/03_city_cohorts.ipynb` — the honest null result, demonstrates the discipline to publish what the data actually says.
5. Streamlit dashboard — the "play with cuts" stretch goal; 7 pages.

## What's most worth challenging in a Q&A

- **The surge-vs-delivery-time finding is observational, not causal.** A skeptical reviewer could argue surge selects "hard" orders (e.g. higher-effort restaurants). The honest defence is in Notebook 05 §4: I'd run a propensity-score or matched-pairs analysis given another day, but the follow-up A/B is the right way to convert observation into evidence.
- **The ₹20 surge-cost assumption.** It's a single variable, swap it in the sidebar of the dashboard.
- **The within-city percentile rank.** Switching to global rank would produce different waste cells but I'd defend the within-city choice strongly.
- **Daily forecast vs hourly.** Hourly is doable with this data but adds noise without improving the operational decision the Ops Head needs to make.
- **The hour-18 recommendation is a hypothesis.** The A/B test is the way to validate it; I don't claim it's a guaranteed lift.
- **Synthetic-data tells.** Restaurant volume distribution is uniform — flagged in Notebook 05 §2 — and cuisine surge rates are suspiciously identical (23–25% across all 9). If the panel wants to push, I'd say: the policy findings (hour-18, cohorts) operate on aggregate temporal cuts and are unlikely to be artefacts; the restaurant-level and cuisine-level surge findings should be re-validated on real production logs.
