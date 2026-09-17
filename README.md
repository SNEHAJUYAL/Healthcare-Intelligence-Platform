# Healthcare Intelligence Platform

An end-to-end healthcare analytics solution built on a synthetic 55,500-row
patient/admission dataset — integrating operational intelligence, financial
analytics, insurance analysis, doctor and patient analytics, resource
planning, predictive modeling, and executive reporting.

**The point isn't the dataset — it's the framework**: `Healthcare Dataset →
Data Cleaning → Feature Engineering → Analytical Data Model → Business
Analytics → 8 Analytical Modules → Intelligence Layer → Executive Dashboard
→ Business Recommendations`, i.e. `Data → Insight → Prediction → Decision`,
not `Data → Chart → Model Accuracy`.

**New here?** [`DOCUMENTATION.md`](DOCUMENTATION.md) is the master reference —
every stage explained for a non-technical stakeholder, a Business Analyst, a
Data Analyst, a Data Scientist, and a technical interviewer simultaneously,
plus interview Q&A and summaries from 30 seconds to 5 minutes. This README
stays as the quick-start / file-index; DOCUMENTATION.md is the deep dive.

## Live artifacts

| Deliverable | What it is |
|---|---|
| **[Healthcare Intelligence Console](dashboard/console.html)** | 11-tab interactive dashboard (Tableau substitute) — every module's charts, tables, the full ML model comparison, a Reality Check tab, and a Global Context tab built from a real downloaded World Bank dataset — computed live from the embedded data. |
| **[Healthcare Intelligence Blueprint](dashboard/blueprint.html)** | 12-page architecture document (Figma substitute) — pipeline diagram, star schema, module cards, Tableau wireframes, ML pipeline diagram, recommendations, a Reality Check page, and a Global Context page. |

Open either `.html` file directly in a browser — both are self-contained,
no server or build step required.

## Repository layout

```
scripts/
  01_ingest_and_clean.py       Stage 1-2: ingestion, data-quality report, cleaning
  02_feature_engineering.py    Stage 4: derived patient/admission/financial/operational features
  03_analytical_data_model.py  Stage 5: star schema (fact + 8 dimensions)
  04_business_analytics.py     Stage 3 + 6: EDA summary + all 8 module metrics
  05_ml_pipeline.py            Stage 8: predictive analytics (Test Results classifier)
  06_reality_benchmark.py      Reality check: dataset vs. published real-world statistics
  07_external_worldbank_data.py  Fetches a real external dataset live from the World Bank API
  08_advanced_ml_pipeline.py   Rigorous 17-point ML pipeline: ablation, tuning, one held-out test eval
  09_deep_eda_profiling.py     Uniformity tests, correlation matrices, 3-method outlier comparison

data/
  raw/healthcare_dataset.csv          original 55,500-row source file
  processed/healthcare_cleaned.csv    54,860 rows after cleaning (98.85% retention)
  processed/healthcare_features.csv   cleaned data + 21 engineered features
  external/worldbank_health_indicators.csv  real World Bank dataset, 692 observations, 6 countries, 2000-2024
  model/fact_admissions.csv           star-schema fact table
  model/dim_*.csv                     8 conformed dimension tables
  model/module_metrics.json           every number behind the 8 dashboard modules
  model/ml_results.json               full model comparison, confusion matrices, feature importance
  model/real_world_benchmarks.json    sourced CDC/AHRQ/KFF/Census/SEER figures + computed comparison
  model/external_context.json         World Bank snapshot + US trend, ready for the dashboard
  model/eda_profile.json              full column/uniformity/correlation/outlier profile
  model/advanced_ml/full_results.json     every number behind the advanced ML report
  model/advanced_ml/comparison_table.csv  every feature-set x model combination tested
  model/advanced_ml/best_model.joblib     the tuned final model (~348 MB — see report note)

reports/
  01_data_quality_report.md       Stage 1 findings + Stage 2 cleaning log
  02_eda_summary.md               Stage 3 business-question-driven EDA
  03_business_recommendations.md  Stage 9 Finding → Impact → Recommendation → Priority
  04_reality_check.md             Dataset vs. real US healthcare statistics, fully cited
  05_external_data_sources.md     The World Bank dataset: what, why, and what it adds
  06_advanced_ml_pipeline.md      Ablation, tuning, single test eval — 40.5% → 43.2% accuracy
  07_deep_eda_profiling.md        Uniformity tests, correlation matrices, outlier comparison
  08_tableau_build_guide.md       Step-by-step: build a real .twbx from the star schema

dashboard/
  console.html      Tableau-substitute executive console (see above)
  blueprint.html     Figma-substitute architecture blueprint (see above)
```

## Reproducing the pipeline

```bash
pip install -r requirements.txt
python3 scripts/01_ingest_and_clean.py
python3 scripts/02_feature_engineering.py
python3 scripts/03_analytical_data_model.py
python3 scripts/04_business_analytics.py
python3 scripts/05_ml_pipeline.py
python3 scripts/06_reality_benchmark.py
python3 scripts/07_external_worldbank_data.py
python3 scripts/08_advanced_ml_pipeline.py
python3 scripts/09_deep_eda_profiling.py
```

Each script reads the previous stage's output and writes its own — run in
order. Steps 1-4 and 6 finish in seconds; step 5 (6-model comparison with
5-fold CV plus a stacking ensemble) takes several minutes on ~44K training
rows. Step 6 requires no internet access — its real-world figures are
hardcoded, sourced constants (see the file's docstring for citations); it
only recomputes the comparison against your own `module_metrics.json`.
**Step 7 does require internet access** — it calls the live World Bank API
and will produce slightly different numbers on re-run as the World Bank
revises recent-year estimates (expected behavior for a live external
source, not a bug). **Step 8 is the slow one** — feature ablation, a 9-model
comparison, and RandomizedSearchCV tuning on two model families takes
roughly 20 minutes on ~44K rows; it also saves a ~348 MB model file (see
the report's practical note before committing it to git). Step 9 finishes
in seconds.

## What the data actually shows

This is a **synthetic** dataset — disease frequency, insurance billing,
admission-type mix, and weekday admissions are all statistically flat across
categories (within 1-3% of each other). The analysis is built to report that
honestly rather than manufacture insight where none exists. The real,
actionable signals that *do* survive scrutiny:

- A 10% tail of admissions drives disproportionate billing and length-of-stay exposure (**High-Billing** and **Long-Stay** flags).
- Admissions peak modestly in **August, July, and January**.
- Hospital/doctor "workload" is only measurable for the ~15-20% of names with repeat admissions — the rest are single data points, not comparable entities.
- The Test Results classifier, after a full ablation + tuning pass across 9 model families (Random Forest, best), reaches **43.2% test accuracy** vs. a 33.3% no-information baseline — a statistically significant lift (McNemar's p=8.7e-08) over the untuned 40.5% incumbent, still driven mostly by numeric fields that impurity-based feature importance is known to overweight.

Full reasoning: [`reports/03_business_recommendations.md`](reports/03_business_recommendations.md). Full rigorous ML methodology: [`reports/06_advanced_ml_pipeline.md`](reports/06_advanced_ml_pipeline.md).

## Can more data raise that accuracy? A rigorous answer.

`reports/06_advanced_ml_pipeline.md` runs the full workflow a genuine
attempt to improve on 40.7% deserves: independence testing, 6 feature-set
ablations, a class-imbalance study, 9 model families, hyperparameter tuning
on the top 2, and exactly one held-out test evaluation. Result: **43.2%
test accuracy** (Random Forest, tuned) — a real, statistically significant
+2.75-point improvement, but not a breakthrough. The pre-modeling
independence tests explain why: every feature showed p > 0.13 and Cramér's
V < 0.011 against Test Results before any model was even trained — this
target has a **low theoretical ceiling** with the columns available. The
practical conclusion for "will more rows help": more of the *same*
distribution would tighten confidence intervals, not raise the ceiling —
real predictive lift here would require genuinely new columns (lab values,
vitals, ICD codes), not more volume of what's already here.

## Deep EDA & data profiling

Beyond the standard EDA, `reports/07_deep_eda_profiling.md` runs a
statistically rigorous profile of the whole dataset: a chi-square
goodness-of-fit test confirms **7/7 categorical fields are indistinguishable
from a uniform distribution** (p > 0.13 on every field), a full
correlation/association matrix shows every numeric and categorical field
pair is essentially uncorrelated (max |r| = 0.008, max Cramér's V = 0.016),
and three independent outlier-detection methods (IQR, Z-score, Isolation
Forest) agree there is no genuine outlier population — only ordinary tail
values of wide, bounded, uniform distributions. It also separates the 22
repeat "identities" in the data into genuine repeat admissions vs. true
near-duplicates (zero of the latter survive cleaning).

## Reality check: how synthetic is this, really?

To ground the platform against something outside itself, `reports/04_reality_check.md`
benchmarks it against **published US healthcare statistics** — CDC/NCHS, AHRQ/HCUP,
KFF, US Census Bureau, and NCI SEER, all cited by name and URL:

| Metric | Platform | Real world | Gap |
|---|---|---|---|
| Average length of stay | 15.5 days | ~4.5–5.2 days ([Definitive Healthcare](https://www.definitivehc.com/resources/healthcare-insights/average-length-stay-hospital)) | **3.2x longer** |
| Billing per stay-day | $3,399 | $3,132 ([KFF](https://www.kff.org/health-costs/state-indicator/expenses-per-inpatient-day/)) | 1.09x — but different units (charge vs. cost) |
| Emergency-channel share of admissions | 32.9% | ~70% of admissions arrive via the ED ([ACEP Now / NHAMCS](https://www.acepnow.com/article/latest-data-reveal-the-eds-role-as-hospital-admission-gatekeeper/2/)) | **largest gap** |
| Insurance payer spread | 19.7%–20.3% (near-uniform) | Employer-sponsored dominates; ~8% uninsured ([US Census](https://www.census.gov/library/publications/2024/demo/p60-284.html)) | structurally different |
| Disease admission mix | 16.5%–16.8% each | 7.7%–47.7% population prevalence (6x spread) | not a like-for-like metric, shown for contrast |

Length of stay and admission channel are the clearest synthetic-data
signatures in the dataset — both look drawn from uniform distributions
rather than the skewed shapes real hospitals produce. See the report for
full source links and the reasoning behind each row.

## A real external dataset, not just cited statistics

Beyond individually-cited figures, `scripts/07_external_worldbank_data.py`
pulls a genuine dataset live from the **World Bank Open Data API** (CC BY
4.0, no key required) and caches it at
[`data/external/worldbank_health_indicators.csv`](data/external/worldbank_health_indicators.csv)
— 692 real observations, 2000–2024, across the US and 5 peer countries.
Full detail: [`reports/05_external_data_sources.md`](reports/05_external_data_sources.md).

| Country | Hospital beds /1,000 | Physicians /1,000 | Health spend / capita | Health spend (% GDP) |
|---|---|---|---|---|
| United States | 2.68 | 3.68 | $13,473 | **16.7%** |
| Germany | 7.55 | **4.53** | $6,849 | 12.3% |
| Japan | **12.59** | 2.65 | $3,638 | 10.7% |
| France | 5.65 | 3.28 | $5,327 | 11.5% |
| Canada | 2.54 | 2.82 | $6,378 | 11.3% |
| United Kingdom | 2.42 | 3.30 | $5,860 | 11.1% |

This is national-level context, not a merged dimension table — the
platform's synthetic admissions have no country field to join on. But it
grounds two modules the dataset can't ground on its own: the US runs on
**roughly a fifth of Japan's hospital-bed capacity** per capita, and this
dataset's own $25,594 average billing per admission is **~1.9x the entire
annual per-capita US health spend** ($13,473) — a scale check worth keeping
in mind while reading Financial Intelligence and Resource Planning.

## Technology stack

Python (Pandas, NumPy) → Scikit-learn / XGBoost / CatBoost / imbalanced-learn
→ Tableau-ready CSV extracts → Git/GitHub.

## Limitations (by design)

- No bed-capacity, staffing, or occupancy data — resource-planning figures are **capacity-demand proxies**, not real utilization.
- Billing Amount is total patient charges, **not** confirmed insurance claim payouts.
- The predictive model is a research prototype, **not a medical diagnostic system**.
- Hospital/Doctor names are near-unique per admission in this synthetic dataset; workload benchmarking is restricted to the repeat-volume subset for that reason.

See [`dashboard/blueprint.html`](dashboard/blueprint.html) → *Page 10, Future Scope* for what real deployment would need to add, *Page 11, Reality Check* for the full benchmark comparison, and *Page 12, Global Context* for the World Bank comparison.
