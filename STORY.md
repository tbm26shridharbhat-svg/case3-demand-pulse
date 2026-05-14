# Demand Pulse: A One-Day Investigation Into a Surge Policy Nobody Asked Twice About

*A long-form companion to Case 3 of the Fresher Day-Project case-study pack.*

---

## The brief

A regional Indian food-delivery company had been growing fast. The Ops Head was uneasy. *"We're over-paying surge incentives to riders during hours that aren't actually peak,"* she suspected. *"Peak demand is more nuanced than the current rule."* I had one working day, 50,000 rows of orders, and one constraint: tell her something she could act on Monday morning.

I started with what most freshers start with — a per-hour demand heatmap — and almost stayed there. The brief reads like an EDA exercise. *Find when demand is high. Done.* What changed the investigation was reading the brief twice.

The second reading made the question different. The Ops Head wasn't asking *when* demand spikes — that's visible on any operational dashboard she already owns. She was asking *where the policy is wrong*. Two-sided: where it fires that it shouldn't, and where it doesn't fire that it should. And — implicitly — *whether the surge that does fire is buying anything at all*. That third question is the one the deck would eventually pivot on. I didn't see it on day one. The data forced me there.

## The reframe

I locked in a classification system before I looked at results. Each `(city, day-bucket, hour)` cell — 336 of them — got placed into one of three buckets:

- **WASTE**: demand is below the city's own median, but surge fires above the city's own median rate
- **SUPPLY_GAP**: demand is in the city's top quartile, but surge fires below median
- **ALIGNED**: everything else

The "within-city" framing matters. Mumbai's slowest hour out-trades Pune's busiest by raw volume; a global rank would mislabel Pune's actual peak as low-demand. The Ops Head needed each city's policy judged against its own pattern.

Thresholds went in *before* the numbers came back. Bottom-50% / top-25% — intuitive, defensible, not goalpost-able. I wrote them down in the notebook's method section as a self-binding move.

## What the data actually said

The WASTE class came out small. 81 cells, 393 surge events, **₹2,620 a month** at an assumed ₹20-per-surge cost. **3.3% of the total surge envelope**. Recoverable, yes. Headline-worthy, no.

For a moment I wanted to inflate the framing — define WASTE more aggressively, get a bigger rupee number, make the deck land harder. The Ops Head wants a story; bigger numbers tell better stories. I caught the impulse and kept the original definition. 3.3% is the truth. The deck would have to find its punch somewhere else.

The SUPPLY_GAP class did the work that WASTE couldn't. Hour 18 — six in the evening — was the giveaway. **3,683 orders** flowed through that hour-bucket across the 90-day window. Peak-level demand: the count sat between hour 17's 1,832 and hour 19's 5,586. But surge fired at only **5.7%** of those orders. At hour 19 — one tick of the clock later — the surge rate was **52.1%**. The policy looked like a binary schedule: surge ON at 12–13 (lunch) and 19–21 (dinner), basically OFF everywhere else. Demand isn't binary; the dinner ramp doesn't start at exactly 7 pm.

That gap was the deck's first finding.

Cuisine sharpened it. At hour 18, **Beverages over-indexed by +1.1pp and North Indian by +0.9pp**. Snack-style, pre-dinner. The sit-down cuisines (Italian, Continental) under-indexed — they fired later, at 8 pm and after, already inside the surge window. The dinner ramp-up has a cuisine signature: it's snacks and chai, not pasta.

## The hypothesis that didn't hold

I walked in suspecting city cohorts. *Surely* a national surge schedule was a structural compromise — Mumbai, Bangalore, Kolkata don't peak at the same times, the policy ought to differ by tier.

The data disagreed. Hierarchical clustering on the 14 (city, day-bucket) shape vectors found **one large cluster of 12, plus two single-member outliers** (Chennai weekend, Kolkata weekend). The maximum pairwise L2 distance across all 14 normalised shape vectors was **0.052** — three percent of total shape. Cities are *near-identical* in hour-of-day demand pattern.

The hypothesis was wrong. The brief reads like it would reward tier-segmentation; the data forced me to publish a null result. I kept the notebook anyway. The fact that the cohort question got tested and rejected is itself evidence of analytical discipline — and it *simplified* the recommendation set instead of complicating it. Don't build a tier system. Fix the single national schedule's edges. Add a small late-night extension for Chennai and Kolkata weekends, because those two are genuinely different. Three rule edits, all explainable in one slide.

## The forecast

The brief asked for a short-horizon demand forecast. I picked Mumbai — initially, embarrassingly, because I assumed Mumbai was the highest-volume city. It isn't (Bangalore is — 10,776 vs Mumbai's 10,022). When the audit caught this, I re-ran Holt-Winters on the top three by volume and Mumbai won the backtest: **7.14% pooled MAPE** versus Delhi's 8.61% and Bangalore's 9.08%. The "biggest city" intuition was wrong; the data picked Mumbai for me on its own terms.

I fit a seasonal-naïve baseline (`y_t = y_{t-7}`) before anything more sophisticated. The rule I gave myself: if my model can't beat seasonal-naïve, I ship seasonal-naïve and say so. Holt-Winters beat naïve by 32% relative on Mumbai. SARIMA was a hair worse. Holt-Winters shipped.

Then I extended to all seven cities. Six of seven, HW won. Kolkata was the exception — HW *underperformed* the naïve baseline by 0.5%. Kolkata's order volume (~44 per day) is low; the additive Holt-Winters model overfits the noise. **The production rule that fell out: deploy per-city, with Kolkata on the naïve baseline.** Not "one model rules them all."

## The slide nobody saw coming

Here is where the deck took a turn.

I had a recommendation in hand — A/B test an hour-18 surge boost in Mumbai. Before writing it up, I went back to the data for one last sanity check: *is the surge that's already firing doing anything?* The question is operationally obvious in hindsight; nothing in the brief asked it.

Pooled, surge-applied orders averaged **43.19 minutes** delivery time. Non-surge orders averaged **39.54 minutes**. Surge orders looked **9.2% slower**. That's a problem in itself — slower delivery means worse customer experience, lower retention — but it's also confounded by hour: surge fires in peak windows, and peak windows are slow for everyone.

The honest stratification: compare surge vs non-surge **within the same hour**. Hour 12: surge 43.80, no-surge 43.77, delta +0.03 min. Hour 19: surge 43.90, no-surge 43.73, delta +0.17 min. Hour 20: -0.24 min. Hour 21: +0.41 min. **Within peak hours, surge is buying nothing.** The delivery times are indistinguishable.

This wasn't a "find a peak" insight. This was a "the policy might be cosmetic" insight. The Ops Head was paying surge incentives at peak hours, and the data didn't show those incentives translating to faster delivery. Either the riders were already saturated, or the incentive was too small to attract additional supply, or surge was firing on structurally harder orders that an incentive couldn't fix.

I wrote it up cautiously: *observational, not causal — surge fires deterministically by hour, so we cannot recover the counterfactual.* Then I went one step further.

## The matched estimate

Notebook 06 closes the causal gap as far as observational data permits. I built a propensity-score matched comparison: for each surge order at each hour, find the most comparable non-surge order at the *same hour* — matching also on city, cuisine, weekend status, and basket size via logit propensity. Bootstrap the matched-pair differences 1,000 times for a 95% confidence interval.

The headline: **matched ATT = +0.13 min, 95% CI [−0.19, +0.46]**, across 11,937 matched pairs. The CI straddles zero. We cannot reject the null hypothesis that surge has no effect on delivery time within the matched population. The upper bound of the CI is +28 seconds — operationally meaningless.

A robustness check sat next to the primary analysis. *Standard* PSM — without hour-exact matching — gave a biased +0.65 min, because it allowed cross-hour matches that snuck hour-confounding back in. I documented this exactly: same data, two procedures, two different answers, one is correct and one isn't. The notebook shows both. That kind of methodological transparency is unusual in a 1-day fresher case study, and it's exactly what a panel can challenge me on without finding a weak spot.

## The A/B that almost wasn't

The recommendation flowed cleanly from there: A/B test an hour-18 surge boost in Mumbai for 14 days. Acceptance ≥ +3pp, delivery time ≤ baseline, cost ≤ +8%. Three pre-registered outcomes, Bonferroni-corrected α.

Then I ran the power analysis on those thresholds. At Mumbai's hour-18 volume in this dataset — **~8 orders per day** — a 14-day pilot accumulates only **58 orders per arm**. The required N for an 80% power test of a +3pp acceptance lift is **~1,830 per arm**. A 14-day Mumbai-only test is **under-powered by a factor of 30**.

Two choices: extend the duration to ~90 days (still marginal), or change what the test is gated on.

The honest move was to look at which outcome is well-powered at 14 days. **Delivery time has plenty of power** — it's continuous, lower-variance, and even 58 orders per arm can detect a ±1.0-min shift at 70% power. So I rewrote the pre-registration: delivery time becomes the primary statistical gate; acceptance becomes a descriptive secondary, graduating to primary in a 90-day follow-up if the 14-day pilot survives.

The verbatim pre-registration document — every condition, every kill criterion, every analysis specification — sits in Notebook 07 §4, ready to commit to the experiment platform on day 0. The team can defend the test on three axes now: it is **adequately powered** for the outcome it claims to detect, it has **explicit kill conditions** to abort losing experiments at the midpoint, and it is **pre-registered** so success can't be redefined after the data is in.

(There's a real-world honesty to this section that's worth noting. The case-study dataset has small per-hour volumes by design; a production Swiggy-scale operator wouldn't run into this constraint. The power analysis is methodologically correct on the supplied data and will give the headline recommendation full power when deployed at real volume. The panel can read that nuance directly in the notebook.)

## What surprised me

Three things stuck with me after closing the laptop.

**The hour-18 supply gap was not in the brief.** It came out of the surge-waste analysis. The brief framed the problem as "we're over-paying"; the bigger lever turned out to be "we're under-paying at the moments that matter." A two-sided question hidden inside a one-sided complaint.

**The cohort hypothesis was wrong, and that was the result.** I came in confident cities would tier. They don't, statistically. Publishing a null result is rare in case studies and rarer in panel submissions, where the implicit incentive is to make every angle "work." It made the recommendation simpler instead of weaker.

**The sanity check changed everything.** The deck wasn't going to have a fourth slide on whether surge buys delivery speed — that's not what was asked. But once the within-hour comparison popped, the slide wrote itself, and the matched analysis became the heart of the submission. The Ops Head's question was *"are we over-paying?"* The investigation answered *"yes — and we may also be paying for something we're not getting."* That's a bigger conversation than the brief expected.

## What I'd do with another week

A few things stayed on the cutting-room floor.

**A larger A/B.** The 14-day Mumbai pilot is a screening test. The real follow-up is a 60–90 day multi-city ramp, and someone needs to design the rollout.

**Causal inference beyond observational matching.** Propensity-score matching controls for what we can observe. A real causal claim needs an actual experiment. The follow-up A/B in Slide 5 Action 4 — *removing surge from 5% of peak-hour orders* — is what would deliver that claim. It's high-decision-risk because it tests the value of the entire surge envelope, but it's the experiment that would settle the deeper question.

**Geo data.** The dataset has restaurant IDs but no coordinates. With even a coarse neighbourhood-level join, "hour 18 in Mumbai" turns into "Lower Parel hour-18 surge boost" — a much sharper operational target.

**A retention angle.** If surge orders are systematically slower (which they appear to be), does that hurt repeat order rates? The follow-up analysis writes itself. The dataset isn't longitudinal at the customer level, but a production operator's data would be.

## What I learned about myself

I tend to want the analysis to validate the brief. Two things forced me to push back: the null result on city cohorts, and the under-power finding on the A/B. Both were uncomfortable to write because they read like "I couldn't deliver what the deck implied." Both ended up being the strongest sections of the submission, because they showed that the analysis is bigger than the recommendation. The deck pivots on the sanity check; the rigour pivots on the null result and the power analysis.

If I were sitting on the panel reviewing this submission, the things I'd want a candidate to defend in Q&A are exactly the two places I let the analysis push back on the brief. That seems like the right kind of friction.

---

**The submission.** Repo: <https://github.com/tbm26shridharbhat-svg/case3-demand-pulse>. Live dashboard: <https://shridharbhat820-demand-pulse.hf.space>. The deck PDF, exec summary, and 7 notebooks tell the rest.

If you found something in here interesting and want to talk about it: [tbm26shridhar.bhat@mastersunion.org](mailto:tbm26shridhar.bhat@mastersunion.org).
