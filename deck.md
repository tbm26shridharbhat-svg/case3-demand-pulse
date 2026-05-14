---
marp: true
theme: default
paginate: true
size: 16:9
header: 'Demand Pulse · Case 3'
footer: 'Confidential · for the Ops Head'
style: |
  section { font-family: -apple-system, "Helvetica Neue", sans-serif; font-size: 24px; }
  h1 { color: #0b3d91; }
  h2 { color: #0b3d91; }
  strong { color: #d62728; }
  table { font-size: 21px; }
  .small { font-size: 18px; color: #666; }
---

# Surge policy — honestly read

### Where we're over-paying, where we're under-firing, and the question nobody asked

50,000 orders · 7 cities · 9 cuisines · Jan–Mar 2025

<br>

<span class="small">Investigation · 1 working day · solo</span>

---

## 1.  The question, re-stated

> The Ops Head's brief: *"we're over-paying surge in hours that aren't actually peak"*

We re-framed this as a **three-sided** question:

- **Where is surge firing when it shouldn't?** → wasteful spend
- **Where is surge not firing when it should?** → supply gap
- **Is the surge that IS firing actually doing anything?** → sanity check ← *the slide nobody saw coming*

The whole investigation hangs on putting rupee numbers on the first two and an honest answer on the third.

---

## 2.  Approach

| Step | Decision | Why |
|---|---|---|
| Slice | (city, day-bucket, hour) → 336 cells | ~150 orders/cell, statistically honest |
| Rank | **Within-city** percentile of demand & surge | Mumbai's slow hour ≠ Pune's busy hour |
| Classify | WASTE / SUPPLY_GAP / ALIGNED | Defensible to a non-analyst |
| Forecast | Holt-Winters daily, walk-forward MAPE | Beats seasonal-naïve by 22%, one line to ship |
| Test cohorts | Hierarchical clustering on demand shape | Null result is also a result |
| **Sanity check** | **Within-hour surge vs no-surge delivery time** | **Is the policy buying speed?** |

---

## 3.  Three findings on the data, before the punchline

- **WASTE is small.** ~96% of surge spend fires in above-median-demand cells. Recoverable waste = **₹3.5k/month** at ₹20 per surge order. Cleanable; not the headline.
- **SUPPLY GAP is real.** Hour 18 sees 3,683 pooled orders — peak-level demand — at only **5.7%** surge vs **52%** at hour 19. Cuisine signature: **Beverages & North Indian** over-index there.
- **COHORTS — null result.** Tested. Rejected. Max pairwise distance across 14 (city, day-bucket) demand-shape vectors = **0.05**. Only Chennai-weekend and Kolkata-weekend deviate.

The next slide is the one that changes how Monday goes.

---

## 4.  The punchline — is surge buying anything?

**Within peak hours**, surge-applied orders and non-surge orders have **near-identical** delivery times.

| Hour | No-surge delivery | Surge delivery | Δ |
|---|---|---|---|
| 12 (lunch) | 43.77 min | 43.80 min | +0.03 |
| 13 (lunch) | 43.59 | 44.03 | +0.44 |
| 19 (dinner) | 43.73 | 43.90 | +0.17 |
| 20 (dinner) | 44.08 | 43.84 | −0.24 |
| 21 (dinner) | 43.48 | 43.89 | +0.41 |

Pooled, surge orders are **9% *slower*** than non-surge (confounded by hour, but the within-hour comparison removes the confound).

**The data does not support the assumption that surge is buying faster delivery.** This is observational, not causal — but it's a strong enough signal to redesign the A/B test.

---

## 5.  What to ship Monday

| # | Action | Risk | Evidence |
|---|---|---|---|
| 1 | Defuse top-10 WASTE cells | Low | Slide 3 |
| 2 | **A/B hour-18 surge boost in one city** — acceptance + **delivery time** + cost as outcomes | Medium — kill if delivery time doesn't fall | Slides 3, 4 |
| 3 | Late-night weekend surge extension for Chennai + Kolkata only | Low | Slide 3 |
| 4 | **Follow-up A/B**: *remove* surge from 5% of peak-hour orders, measure delivery time. If removal doesn't hurt → re-evaluate the whole envelope | High value, high decision risk | Slide 4 |

Forecast: Holt-Winters MAPE **8.6%** vs 11.0% baseline · April 1–7 Delhi committed to `outputs/forecast.csv`.

<br>

<span class="small">Repo · Dashboard · Notebooks · Exec Summary — links in README.md</span>
