"""
Reality Check — Benchmarking the Synthetic Dataset Against Published US Healthcare Statistics
Healthcare Intelligence Platform

Every number in REAL_WORLD is a published figure from a named public source
(CDC/NCHS, AHRQ/HCUP, KFF, US Census Bureau, NCI SEER) with a citation URL.
Nothing here is estimated or fabricated. The comparison against the
platform's own computed metrics (module_metrics.json) is included where the
two are genuinely measuring the same thing (length of stay, cost per day);
where the metrics are conceptually different (population disease
prevalence vs. share-of-admissions among 6 preselected conditions), the
script says so explicitly rather than forcing a false equivalence.

Sources (accessed 2026-09):
  - AHRQ HCUP Statistical Briefs                 https://hcup-us.ahrq.gov/reports/statbriefs/sbtopic.jsp
  - KFF, Hospital Expenses per Adjusted Inpatient Day (2023 AHA Annual Survey)
                                                  https://www.kff.org/health-costs/state-indicator/expenses-per-inpatient-day/
  - Definitive Healthcare, Average Length of Stay (2023 analysis, 4,405 US hospitals)
                                                  https://www.definitivehc.com/resources/healthcare-insights/average-length-stay-hospital
  - CDC/NCHS Data Brief No. 516 (Nov 2024) — Diabetes prevalence
                                                  https://www.cdc.gov/nchs/data/databriefs/db516.pdf
  - CDC/NCHS Data Brief No. 511 (Oct 2024) — Hypertension prevalence
                                                  https://www.cdc.gov/nchs/data/databriefs/db511.pdf
  - CDC/NCHS Data Brief No. 508 — Obesity prevalence
                                                  https://www.cdc.gov/nchs/products/databriefs/db508.htm
  - CDC FastStats / American Lung Association — Current asthma prevalence
                                                  https://www.cdc.gov/nchs/fastats/asthma.htm
                                                  https://www.lung.org/research/trends-in-lung-disease/asthma-trends-brief/current-demographics
  - CDC MMWR Vital Signs (2013-2015, most recent national estimate) — Arthritis prevalence
                                                  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5687192/
  - NCI SEER Cancer Stat Facts (2021-2023) — Lifetime cancer diagnosis risk
                                                  https://seer.cancer.gov/statfacts/html/all.html
  - US Census Bureau, Health Insurance Coverage in the United States: 2023
                                                  https://www.census.gov/library/publications/2024/demo/p60-284.html
  - KFF, Employer Health Benefits / Medicare Advantage enrollment (2024)
                                                  https://www.kff.org/tag/employer-sponsored-health-insurance/
                                                  https://www.kff.org/medicare/health-insurer-financial-performance/
  - CDC FastStats — Emergency Department Visits (155.4M ED visits, 11.5% admitted)
                                                  https://www.cdc.gov/nchs/fastats/emergency-department.htm
  - ACEP Now / NHAMCS trend analysis — ED as hospital-admission gateway (~70% of admissions via ED, up from 58%)
                                                  https://www.acepnow.com/article/latest-data-reveal-the-eds-role-as-hospital-admission-gatekeeper/2/
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

with open(BASE / "data" / "model" / "module_metrics.json") as f:
    M = json.load(f)

REAL_WORLD = {
    "length_of_stay_days": {
        "value": 4.8, "range": [4.5, 5.2],
        "source": "Definitive Healthcare (2023, 4,405 US hospitals) / AHA-era HCUP estimate (2022)",
        "url": "https://www.definitivehc.com/resources/healthcare-insights/average-length-stay-hospital",
    },
    "cost_per_inpatient_day_usd": {
        "value": 3132,
        "source": "KFF analysis of 2023 American Hospital Association Annual Survey",
        "url": "https://www.kff.org/health-costs/state-indicator/expenses-per-inpatient-day/",
        "note": "Hospital-reported expense per day, not a billed charge — charges are typically marked up well above cost.",
    },
    "uninsured_rate_pct": {
        "value": 8.0,
        "source": "US Census Bureau, Health Insurance Coverage in the United States: 2023",
        "url": "https://www.census.gov/library/publications/2024/demo/p60-284.html",
    },
    "ed_share_of_admissions_pct": {
        "value": 70,
        "source": "ACEP Now / NHAMCS trend analysis — share of inpatient admissions originating in the ED, up from 58% ~14 years earlier",
        "url": "https://www.acepnow.com/article/latest-data-reveal-the-eds-role-as-hospital-admission-gatekeeper/2/",
    },
    "ed_visits_resulting_in_admission_pct": {
        "value": 11.5,
        "source": "CDC FastStats — Emergency Department Visits (17.8M of 155.4M ED visits admitted)",
        "url": "https://www.cdc.gov/nchs/fastats/emergency-department.htm",
    },
    "disease_prevalence_pct": {
        "Hypertension": {"value": 47.7, "source": "CDC/NCHS Data Brief No. 511 (Aug 2021-Aug 2023)", "url": "https://www.cdc.gov/nchs/data/databriefs/db511.pdf"},
        "Obesity": {"value": 40.3, "source": "CDC/NCHS Data Brief No. 508 (Aug 2021-Aug 2023)", "url": "https://www.cdc.gov/nchs/products/databriefs/db508.htm"},
        "Arthritis": {"value": 22.7, "source": "CDC MMWR Vital Signs (2013-2015, most recent national estimate)", "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5687192/"},
        "Diabetes": {"value": 15.8, "source": "CDC/NCHS Data Brief No. 516 (2023 data, total diagnosed+undiagnosed)", "url": "https://www.cdc.gov/nchs/data/databriefs/db516.pdf"},
        "Cancer": {"value": 39.2, "source": "NCI SEER (2021-2023) — LIFETIME diagnosis risk, not point-in-time prevalence", "url": "https://seer.cancer.gov/statfacts/html/all.html"},
        "Asthma": {"value": 7.7, "source": "CDC FastStats / American Lung Association", "url": "https://www.cdc.gov/nchs/fastats/asthma.htm"},
    },
}

k = M["executive"]["kpis"]
platform_los = k["avg_length_of_stay"]
platform_cost_per_day = M["financial"]["avg_billing_per_stay_day"]
platform_emergency_pct = k["emergency_admission_pct"]

condition_admission_mix = {c["label"]: round(c["value"] / k["total_patients"] * 100, 2)
                           for c in M["executive"]["top_conditions"]}
insurance_mix = {p["Insurance Provider"]: round(p["patient_volume"] / k["total_patients"] * 100, 2)
                  for p in M["insurance"]["provider_summary"]}

comparison = {
    "length_of_stay": {
        "platform_days": platform_los,
        "real_world_days": REAL_WORLD["length_of_stay_days"]["value"],
        "real_world_range": REAL_WORLD["length_of_stay_days"]["range"],
        "ratio": round(platform_los / REAL_WORLD["length_of_stay_days"]["value"], 2),
        "interpretation": (
            "Platform average length of stay is ~3x the real-world US average. The dataset draws "
            "Length of Stay from what looks like a uniform 1-30 day distribution rather than the "
            "right-skewed, mostly-short-stay distribution real hospitals show."
        ),
    },
    "cost_per_stay_day": {
        "platform_usd": platform_cost_per_day,
        "real_world_usd": REAL_WORLD["cost_per_inpatient_day_usd"]["value"],
        "ratio": round(platform_cost_per_day / REAL_WORLD["cost_per_inpatient_day_usd"]["value"], 2),
        "interpretation": (
            "Platform billing-per-stay-day ($3,399) sits within 9% of the real US average hospital "
            "EXPENSE per day ($3,132) -- but the platform field is a billed charge, and charges "
            "typically run several multiples above a hospital's own reported cost in real revenue-"
            "cycle data. If 'Billing Amount' is meant to represent charges rather than cost, the "
            "realistic figure would be considerably higher than $3,132/day, not roughly equal to it."
        ),
    },
    "admission_channel_mix": {
        "platform_emergency_pct": platform_emergency_pct,
        "real_world_ed_share_of_admissions_pct": REAL_WORLD["ed_share_of_admissions_pct"]["value"],
        "interpretation": (
            "Real US hospitals now admit roughly 70% of inpatients through the ED. The platform's "
            "Admission Type is split almost exactly evenly across Elective/Urgent/Emergency (~33% "
            "each) -- a signature of uniform-random category assignment, not a modeled admission "
            "pathway."
        ),
    },
    "insurance_market_structure": {
        "platform_mix_pct": insurance_mix,
        "platform_spread_pct_points": round(max(insurance_mix.values()) - min(insurance_mix.values()), 2),
        "real_world_note": (
            "Employer-sponsored insurance alone covers ~154M nonelderly Americans (KFF), Medicare "
            "Advantage covers ~33M of ~65M Medicare beneficiaries (KFF), and 8.0% of the population "
            "is uninsured (US Census, 2023) -- a highly uneven market structure."
        ),
        "interpretation": (
            f"The platform's 5 payers split admissions within a {round(max(insurance_mix.values()) - min(insurance_mix.values()), 2)}-point "
            "band of each other (~20% each) -- consistent with uniform-random assignment, not a "
            "modeled insurance market where employer plans and Medicare dominate unevenly and ~8% "
            "of the population carries no coverage at all."
        ),
    },
    "disease_admission_mix_vs_population_prevalence": {
        "note": (
            "NOT a like-for-like comparison -- the platform figure is each condition's share of "
            "admissions among 6 preselected conditions; the real-world figure is population-wide "
            "point (or lifetime, for cancer) prevalence. Shown side by side only to illustrate that "
            "real prevalence varies more than 6x across conditions (7.7% asthma to 47.7% "
            "hypertension) while the platform's 6 conditions are engineered to near-perfect "
            "equality (16.5%-16.8% each)."
        ),
        "platform_admission_mix_pct": condition_admission_mix,
        "real_world_prevalence_pct": {k2: v["value"] for k2, v in REAL_WORLD["disease_prevalence_pct"].items()},
    },
}

output = {"real_world_sources": REAL_WORLD, "comparison": comparison}
OUT = BASE / "data" / "model" / "real_world_benchmarks.json"
OUT.write_text(json.dumps(output, indent=2))
print(f"Wrote reality-check benchmarks -> {OUT}")
for section, body in comparison.items():
    print(f"\n[{section}]")
    print(body.get("interpretation", body.get("note", "")))
