# Architecture

A picture of how the moving parts connect, what gets persisted where, and which pipeline keeps the analysis honest.

## End-to-end flow

```mermaid
flowchart TB
    subgraph Source["📦 Source"]
        DATA[("data/orders.csv<br/>50k rows · Jan–Mar 2025")]
    end

    subgraph Notebooks["🧪 Notebooks (5 chapters + 2 additions)"]
        NB1["01 · EDA + reframe"]
        NB2["02 · Surge waste<br/>(WASTE / GAP / ALIGNED cells)"]
        NB3["03 · City cohorts<br/>(null result, honest)"]
        NB4["04 · Mumbai forecast<br/>(Holt-Winters, per-city §7)"]
        NB5["05 · Cuisine/AOV/delivery sanity"]
        NB6["06 · Hour-exact PSM<br/>(matched ATT + bootstrap CI)"]
        NB7["07 · A/B power + pre-reg"]
    end

    subgraph Outputs["💾 Outputs (committed CSVs)"]
        O1["cells.csv<br/>top_waste_cells.csv<br/>top_gap_cells.csv"]
        O2["forecast.csv<br/>per_city_mape.csv<br/>per_city_forecasts.csv"]
        O3["psm_results.csv<br/>psm_per_hour.csv"]
        O4["ab_power_analysis.csv"]
    end

    subgraph Dashboard["📊 Streamlit Dashboard · 9 pages"]
        D1["TL;DR · Policy map · Cells"]
        D2["City cohorts · Cuisine · Sanity"]
        D3["Causal (PSM) · Forecast · Per-city"]
    end

    subgraph Docs["📄 Submission docs"]
        DOC1["README.md (entry)<br/>exec_summary.md (Ops Head)<br/>deck.pdf (5 slides)"]
        DOC2["DECISIONS.md<br/>SUBMISSION_NOTES.md"]
        AUDIT["AUDIT.md<br/>+ audit_truth.json (96 keys, locked)"]
    end

    subgraph CICD["🔒 CI · reproducibility lock"]
        TESTS["pytest · 16 tests"]
        AUDIT_CHECK["canonical_audit.py --verify"]
        NB_RUN["papermill execute all notebooks"]
        SMOKE["Streamlit boot smoke"]
        CI_BADGE[("✅ green badge on README")]
    end

    subgraph Deploy["🚀 Deployment"]
        HF["HF Spaces · Docker · port 7860"]
        GH["GitHub · public repo"]
    end

    DATA --> NB1 & NB2 & NB3 & NB4 & NB5 & NB6 & NB7
    NB2 --> O1
    NB4 --> O2
    NB6 --> O3
    NB7 --> O4
    O1 & O2 & O3 & O4 --> D1 & D2 & D3
    D1 & D2 & D3 --> HF
    NB1 & NB2 & NB3 & NB4 & NB5 & NB6 & NB7 --> DOC1
    O1 & O2 & O3 & O4 --> AUDIT
    DATA --> AUDIT_CHECK
    AUDIT --> AUDIT_CHECK
    TESTS & AUDIT_CHECK & NB_RUN & SMOKE --> CI_BADGE
    DOC1 & DOC2 & AUDIT --> GH
    NB1 & D1 --> GH

    classDef src fill:#fde68a,stroke:#a16207,color:#000
    classDef nb fill:#dbeafe,stroke:#1d4ed8,color:#000
    classDef out fill:#fef3c7,stroke:#92400e,color:#000
    classDef dash fill:#e0e7ff,stroke:#4338ca,color:#000
    classDef doc fill:#f3f4f6,stroke:#374151,color:#000
    classDef ci fill:#d1fae5,stroke:#065f46,color:#000
    classDef deploy fill:#fce7f3,stroke:#9d174d,color:#000

    class DATA src
    class NB1,NB2,NB3,NB4,NB5,NB6,NB7 nb
    class O1,O2,O3,O4 out
    class D1,D2,D3 dash
    class DOC1,DOC2,AUDIT doc
    class TESTS,AUDIT_CHECK,NB_RUN,SMOKE,CI_BADGE ci
    class HF,GH deploy
```

## What each layer guarantees

**Source.** The 50k-row dataset is the single source of truth. Nothing else is ground.

**Notebooks.** Five plus two. Each is a self-contained chapter of the investigation. Every notebook builds figures inline (no external chart dependencies) and writes its primary findings to CSV in `outputs/`. Notebooks can be run in any order; they read the source CSV directly.

**Outputs.** Eight CSV files. These are the *contracted handoffs* between notebooks and downstream consumers — the docs reference them, the dashboard renders them, the audit reads them. Pinning them as files (not in-memory frames) lets the dashboard run without re-executing notebooks.

**Dashboard.** Nine pages, organised into three thematic groups. The dashboard reads from `data/` and `outputs/`, never re-derives findings — the goal is responsive interactivity, not duplicate computation.

**Docs.** Six markdown files. Each has a job. README is the entry; exec_summary is the Ops Head deliverable; DECISIONS/AUDIT/SUBMISSION_NOTES document the rigour.

**CI · reproducibility lock.** Four checks. Together they guarantee that no commit can drift a number, break a notebook, or ship a dashboard that doesn't boot.

**Deployment.** Two endpoints. HF Spaces serves the live dashboard via Docker on port 7860. GitHub serves the public source.

## The data contract

The notebooks expect `data/orders.csv` to satisfy these properties (asserted by `tests/test_data_quality.py`):

| Property | Value |
|---|---|
| Rows | exactly 50,000 |
| Date range | 2025-01-01 → 2025-03-31 |
| Cities | exactly 7: {Bangalore, Chennai, Delhi, Hyderabad, Kolkata, Mumbai, Pune} |
| Cuisines | exactly 9 |
| Restaurants | exactly 800 |
| Nulls | zero across all columns |
| Duplicate `order_id` | zero |
| Surge rate | within [23.4%, 24.4%] |
| Columns | `[order_id, timestamp, city, restaurant_id, cuisine, order_value, delivery_time_min, surge_applied]` |

If any of these fail, CI fails before the analysis even runs. The data contract is the foundation; everything else assumes it.

## The audit lock

`audit_truth.json` contains 96 key/value pairs covering every number quoted anywhere in the submission. The `scripts/canonical_audit.py --verify` mode recomputes all 96 from raw data and asserts they match — bit-exactly for integers, within tolerance for bootstrap CIs.

Any change to a notebook or a script that materially shifts a number breaks the build. To intentionally update a number: rerun `--write` to regenerate the lock, then commit both the lock and the change in the same PR. The reviewer sees both the intent and the impact.

This is what gives `AUDIT.md` its teeth.
