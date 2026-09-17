# Reality Check — Benchmarking Against Published US Healthcare Statistics
### Healthcare Intelligence Platform

Every recommendation so far has been computed from the dataset itself. This
report goes one step further and asks: **how does this synthetic dataset
compare to how the real US healthcare system actually looks?** Every figure
below is a published statistic from a named public source — nothing here is
estimated. Full source list and machine-readable comparison:
[`scripts/06_reality_benchmark.py`](../scripts/06_reality_benchmark.py) →
[`data/model/real_world_benchmarks.json`](../data/model/real_world_benchmarks.json).

## 1. Length of stay — directly comparable, and the gap is real

| | Platform | Real US average |
|---|---|---|
| Average length of stay | **15.5 days** | **~4.5–5.2 days** |

Sources: [Definitive Healthcare, 2023 analysis of 4,405 US hospitals](https://www.definitivehc.com/resources/healthcare-insights/average-length-stay-hospital).

Platform stays run **~3x longer** than reality. The dataset's Length of Stay
looks drawn from something close to a uniform distribution across the full
1–30 day range, rather than the strongly right-skewed, mostly-short-stay
pattern real hospitals show (most admissions resolve in a few days; a small
minority run long).

## 2. Cost per stay-day — closer than expected, with an important caveat

| | Platform | Real US average |
|---|---|---|
| Billing per stay-day | **$3,399** | **$3,132** (hospital-reported expense per day) |

Source: [KFF, Hospital Expenses per Adjusted Inpatient Day, 2023 AHA Annual Survey](https://www.kff.org/health-costs/state-indicator/expenses-per-inpatient-day/).

These land within 9% of each other — but they're not quite measuring the
same thing. KFF's figure is a hospital's own reported **expense**; the
platform's Billing Amount is described as a **charge**. In real revenue-
cycle data, billed charges routinely run several multiples above a
hospital's actual cost (the well-documented "chargemaster markup" effect).
If Billing Amount is meant to represent charges, the realistic per-day
figure would be considerably *higher* than $3,132 — meaning the platform's
apparent realism here is likely coincidental, not evidence the field models
real billing behavior.

## 3. Admission channel — the starkest gap in the dataset

| | Platform | Real US pattern |
|---|---|---|
| Emergency-type admissions | **32.94%** (of an even 3-way split) | **~70%** of inpatient admissions now originate through the ED |

Sources: [ACEP Now / NHAMCS trend analysis](https://www.acepnow.com/article/latest-data-reveal-the-eds-role-as-hospital-admission-gatekeeper/2/) (ED share of admissions, up from 58% ~14 years ago); [CDC FastStats](https://www.cdc.gov/nchs/fastats/emergency-department.htm) (11.5% of the 155.4M annual ED visits result in admission).

This is the clearest synthetic-data signature in the whole platform. Real
hospitals lean heavily on the emergency department as their dominant intake
channel. The platform splits Elective/Urgent/Emergency almost perfectly
evenly (33.6% / 33.5% / 32.9%) — the fingerprint of a random category
draw, not a modeled admission pathway.

## 4. Insurance market structure — real markets are lopsided, this one isn't

Source: [US Census Bureau, Health Insurance Coverage in the United States: 2023](https://www.census.gov/library/publications/2024/demo/p60-284.html) (8.0% uninsured); [KFF](https://www.kff.org/tag/employer-sponsored-health-insurance/) (employer-sponsored insurance covers ~154M nonelderly Americans; Medicare Advantage covers ~33M of ~65M Medicare beneficiaries).

The platform's 5 payers split admissions within a **0.58 percentage-point**
band of each other (19.68%–20.26%, essentially 20% each). The real US
market looks nothing like this: employer-sponsored coverage alone dwarfs
any single payer here, Medicare/Medicaid have their own distinct
enrollment dynamics, and roughly 8% of the population carries no coverage
at all — a category this dataset doesn't represent.

## 5. Disease mix — not a fair comparison, but instructive anyway

The platform's 6 medical conditions are each ~16.5–16.8% of admissions —
i.e., engineered to near-perfect equality. Real population prevalence is
**not** equal, and this isn't really the same metric (admission-mix among 6
preselected conditions vs. population-wide prevalence) — but the contrast
is worth seeing:

| Condition | Platform admission share | Real US prevalence |
|---|---|---|
| Hypertension | 16.64% | **47.7%** ([CDC/NCHS Data Brief No. 511](https://www.cdc.gov/nchs/data/databriefs/db511.pdf)) |
| Obesity | 16.64% | **40.3%** ([CDC/NCHS Data Brief No. 508](https://www.cdc.gov/nchs/products/databriefs/db508.htm)) |
| Cancer | 16.63% | **39.2%** lifetime diagnosis risk ([NCI SEER](https://seer.cancer.gov/statfacts/html/all.html)) |
| Arthritis | 16.78% | **22.7%** ([CDC MMWR Vital Signs](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5687192/)) |
| Diabetes | 16.76% | **15.8%** ([CDC/NCHS Data Brief No. 516](https://www.cdc.gov/nchs/data/databriefs/db516.pdf)) |
| Asthma | 16.54% | **7.7%** ([CDC FastStats](https://www.cdc.gov/nchs/fastats/asthma.htm)) |

Real prevalence spans a **6x range** (7.7% to 47.7%). The platform's spans
0.24 points. That gap — not the individual numbers — is the finding.

## What this means for how the platform should be read

None of this invalidates the earlier modules — Modules 1-8 correctly
describe *what this dataset contains*. This report adds the layer those
modules can't provide on their own: *how far the dataset is from the real
system it represents*. For a portfolio or demo context, that's a feature —
it shows the analysis can tell the difference between "the data says X" and
"reality is X," which is exactly the discipline a real deployment would
need. Recommendation for any future iteration: if realism matters more than
demonstration, replace Length of Stay, Admission Type, and Insurance
Provider with distributions sampled from the cited real-world shapes rather
than uniform draws.
