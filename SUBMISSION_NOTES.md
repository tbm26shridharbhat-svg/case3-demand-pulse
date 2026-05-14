# Submission Notes — Case 3

## Known issues / honest caveats

- **Live demo URL is a placeholder** in `README.md`. After Hugging Face Spaces deploy, swap `<https://your-app.huggingface.co/...>` into the README first line and re-commit.
- **Deck rendered from `deck.md`** using Marp. To re-render to PDF: `npx @marp-team/marp-cli@latest deck.md --pdf`. Background image references (`outputs/figures/02_*.html`) only render in Marp HTML mode — for PDF, screenshot the relevant figure and replace the image reference.
- **Demo video link** in `demo_video_link.txt` — replace placeholder with Loom/YouTube URL.

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
