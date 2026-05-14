# Notes — rough thinking while working

*This isn't a deliverable. It's the file I kept open in a side panel while building the submission, partly so I could remember what almost went wrong, partly so I could be honest in the demo video about the decisions that weren't tidy. Read it as a working notebook, not as polished prose.*

---

## Things I got wrong on the first pass

- **Picked Delhi for the forecast on a vibe, not on numbers.** I told myself it was "biggest city = most stable signal." I had not actually checked. When I went to lock the audit, the script printed the city volumes and Delhi was *third* (Bangalore 10,776, Mumbai 10,022, Delhi 8,171). Caught it before submission. Switched to Mumbai because Mumbai won the actual MAPE backtest among the top-3 (7.14% vs Delhi's 8.61%, Bangalore's 9.08%). Embarrassing but the right kind of catch — exactly why the audit script exists.

- **First version of WASTE was inflated.** I had a number in my head that the "wasteful spend" was around ₹10.6k over 90 days, and that number leaked into an early draft of the deck. Turns out that came from a *broader* metric I'd computed during exploration (any surge in below-median cells, regardless of surge_pct). The actual WASTE *class* — which is the one I defined in Notebook 02 — is ₹7,860 over 90 days. Reconciled both metrics in the audit and made the documents pick the class number consistently. The two metrics live side by side in exec_summary now; that's the honest fix.

- **Almost forced the cohort story.** Notebook 01's hour-by-city heatmap *looked* like cities clustered. I was halfway through writing a tier-system recommendation before the formal clustering ran and showed the maximum pairwise distance across all 14 (city, day-bucket) shape vectors was 0.052. The cohort hypothesis was a story I wanted to tell. The data didn't support it. Wrote Notebook 03 as a null result instead. That call still feels right.

## Things I almost didn't do that turned out to matter

- **The sanity check on whether surge buys anything.** This wasn't in the brief at all. I added it as a single side-experiment toward the end of Notebook 05, mostly because the "could this be confounded" voice in my head wouldn't shut up. The within-hour table came back showing surge and no-surge were within 0.5 minutes of each other in every peak hour. That single observation ended up being Slide 4 and re-shaped the A/B recommendation. Best thirty minutes of the project.

- **Hour-exact PSM instead of standard PSM.** The first time I ran propensity-score matching in Notebook 06 I got an aggregate ATT of +1.31 min. Felt off. I knew from the within-peak-hour analysis it should be closer to zero. Dug in, realised standard PSM was allowing cross-hour matches because two orders at very different hours can have similar propensity scores. Hour-exact matching brought the estimate to +0.13 min, CI straddles zero — which is the right answer. Kept the standard-PSM run in the notebook as a methodological cautionary tale. A panel member might ask "why hour-exact?" — that's the answer I'd want to defend.

- **The A/B power analysis.** Originally I had Action 2 in the deck claiming a 14-day Mumbai pilot with +3pp acceptance and ≤+8% cost as the success thresholds. The numbers felt confident. Then I actually ran the power calculation in Notebook 07 and found that at Mumbai hour-18's volume (~8 orders/day), 14 days gives 58 orders per arm — power for +3pp lift is ~2%. Severely under-powered. Honest reframe: delivery time is the well-powered primary outcome at this N, acceptance becomes descriptive and graduates to primary in a 90-day follow-up. The recommendation got *better* once the power analysis forced the question.

## Things I'm still uncertain about

- **The PSM result is observational.** Even with hour-exact matching, we're controlling for what we can observe (city, hour, cuisine, weekend, basket size). The unobservable confounders that could still drive a positive bias: distance-to-drop, rider-density-at-pickup, kitchen-prep-latency. I flag this in Notebook 06 and the exec summary. If pressed in the panel, I'd say: "the matched evidence isn't proof; the follow-up A/B in Slide 5 Action 4 is what would turn observation into evidence."

- **The exog-feature lift on Mumbai forecast is small.** In Notebook 08 I add holiday + weather features to SARIMA and the MAPE drops from 7.86% to 7.61% — about 3% relative improvement. Holt-Winters at 7.14% still wins overall. I'd ship the holiday flag in production (cheap, defensible) but I'd skip the weather feed at this MAPE delta. Not sure if a more aggressive featuriser (lagged weather, weekend × weather interaction) would change the story. Out of scope here.

- **Kolkata's HW MAPE was worse than naïve.** In Notebook 04 §7 the per-city table shows 6 cities where Holt-Winters beats seasonal-naïve, and Kolkata where it loses by 0.5%. Low volume (~44/day) and the weekend outlier signature from NB03 both work against the additive model. Production rule that fell out: deploy seasonal-naïve in Kolkata, HW everywhere else. Honest finding; I think it's right but a part of me wonders if a Box-Cox transform or a multiplicative seasonal form would have saved HW for Kolkata too. Didn't try.

## Decisions I'd make differently next time

- **Lock the canonical truth table before writing the deck**, not after. The audit script's `--write` mode was added halfway through the build, after I'd already drafted Slide 1. Doing it the other way around — generate truth first, render slides from truth — would have prevented the ₹10.6k vs ₹2,620 inconsistency from existing in the first place.

- **Do the power analysis before writing the recommendation**, not after. Same lesson, different artefact. If I'd run Notebook 07's analysis before the first draft of Slide 5, I wouldn't have made the embarrassing claim about a +3pp acceptance threshold that the dataset can't actually support at 14 days.

- **Talk to a real Ops Head, even informally.** The exec summary is written in my best guess at the voice she'd want, but my best guess isn't a real conversation. If I get a chance, I'd love to sanity-check the recommendations with someone who actually owns a surge rule in production.

## Small craft things I'm proud of

- The audit lock catching my Mumbai/Bangalore mistake at all. That's why CI exists.
- Notebook 03 being a null result that I didn't fight. Most freshers would have forced k=2 and told a cohort story; I didn't.
- The PSM cautionary tale (showing the +1.31 biased estimate next to the +0.13 hour-exact estimate, same notebook). Most submissions hide their methodological mistakes; including this one transparently signals confidence.

## What I'd watch for if I were on the panel

- Does the candidate know which decisions were *theirs* versus AI-assisted?
- Can they defend the hour-exact PSM choice without reading from the notebook?
- Do they understand why a +0.13 min point estimate with a CI that includes zero is not the same as "zero effect"?
- Do they have a real opinion on whether the policy is *wrong* or just *miscalibrated at the edges*?

If I were sitting on the other side, those are the four questions I'd ask. I have answers for all four. Ready when they are.
