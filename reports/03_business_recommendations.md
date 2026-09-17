# Stage 9 — Business Recommendations
### Healthcare Intelligence Platform

These recommendations are derived directly from the computed metrics in
`data/model/module_metrics.json` and `data/model/ml_results.json` — nothing
here is asserted without a number behind it. A first, important finding
threads through all of them:

> **This is a synthetic dataset with almost no embedded causal structure.**
> Disease frequency, average billing per condition, insurance-provider
> billing, admission-type mix, weekday admissions, and test-result
> distribution are all statistically flat (within ~1-3% of each other across
> categories). The honest analytical takeaway is *not* to manufacture
> insight where none exists, but to report clearly which patterns ARE real
> (capacity concentration, repeat-entity workload, tail-risk billing/stay
> populations) and which are not (diagnosis-driven cost variation,
> payer-driven billing variation, day-of-week demand variation).

| # | Finding | Business Impact | Recommendation | Priority |
|---|---------|------------------|-----------------|----------|
| 1 | Average billing per medical condition is nearly identical (\$25.2K–\$25.9K across all 6 conditions) — condition alone does not explain cost variation. | Finance cannot use "high-cost disease" framing to target cost containment; the real cost driver is elsewhere. | Investigate cost drivers beyond diagnosis code — length-of-stay tail, room/admission-type combinations, or procedure-level detail not present in this dataset. | Medium |
| 2 | 10% of admissions (5,486 cases) are "High Billing" (≥90th percentile, ≥\$45,168), together representing a disproportionate share of the \$1.40B total billed. | A small case tail drives outsized revenue/cost exposure. | Route the High-Billing Flag into finance's case-review queue; audit this tail for coding accuracy and collections risk before it's treated as routine revenue. | High |
| 3 | Admissions peak in August, July, and January (each ~3-4% above the monthly average of ~4,565); every other month sits within a narrow band. | Modest but real seasonal demand pressure in summer and the new year. | Bias elective-admission scheduling and staffing rosters away from Jul/Aug/Jan where possible; use these three months as the capacity-planning stress case. | High |
| 4 | 10% of admissions (5,520 cases) are "Long-Stay" (≥90th percentile, ≥28 days out of a 1–30 day range), consuming a disproportionate share of bed-days. | Long-stay cases are the primary capacity-demand lever, not average-case volume. | Build a discharge-bottleneck review specifically for the Long-Stay cohort; even a 2-day reduction in this subgroup frees meaningful capacity platform-wide. | High |
| 5 | Doctor and hospital workload is extremely concentrated at the low end: 30,892 of 40,276 doctors (77%) and the majority of 39,815 hospitals appear only once in the data; a small repeat-volume subset (9,384 doctors, 7,789 hospitals) carries all measurable multi-case workload, topping out at 44 admissions for one hospital and 27 for one doctor. | Aggregate "workload" reporting is meaningless outside this repeat-volume subset — it would otherwise flatter or penalize entities based on one data point. | Restrict doctor/hospital benchmarking dashboards to the repeat-volume cohort (≥3–5 cases) and label single-case entities explicitly as non-comparable, rather than ranking them. | Medium |
| 6 | Insurance-provider billing is nearly uniform (\$25.46K–\$25.68K average, five providers within a 1% band); admission-type mix per provider is likewise even. | No provider shows a distinct cost or utilization profile in this data. | Do not build payer-mix strategy on this dataset's billing patterns; if payer strategy is a live priority, source actual claims/reimbursement data rather than gross billing. | Low |
| 7 | Length of Stay and Billing Amount are statistically uncorrelated (r = -0.005). | Billing is not simply a function of how long a patient stays — confirms condition/day-rate assumptions shouldn't be baked into forecasting models. | Model billing and length-of-stay as separate forecasting targets rather than deriving one from the other. | Medium |
| 8 | Test Results (Normal/Abnormal/Inconclusive) are near-perfectly balanced (33.5%/33.4%/33.1%). Best model (Random Forest) reaches 40.7% test accuracy / ROC-AUC 0.58 — a real but modest lift over the 33% no-information baseline; Logistic Regression and Decision Tree stay at baseline. Feature importance is led by Room Number, Billing Amount, and Billing per Stay Day — a known artifact of impurity-based importance favoring high-cardinality numeric fields, not proof of a causal driver. | The available attributes carry weak, not zero, predictive signal — too weak and too numerically-driven to support any clinical claim. | Treat this as a research prototype only; do not deploy as risk scoring. If earlier-prioritization is a real goal, add genuine clinical inputs (vitals, labs, history) and re-run with permutation (not impurity-based) importance. | Medium |

## Reading this table

Findings 2, 3, 4, and 5 are the actionable, real signals in this dataset —
all four are tail/concentration effects (a subset of cases or entities
driving outsized load), which is exactly the kind of pattern operational and
capacity teams should act on. Findings 1, 6, and 7 are documented absence-
of-pattern results — equally valid output from the analysis, and important
to state plainly rather than dress up as insight. Finding 8 lands in
between: a modest, real predictive lift (Random Forest, 40.7% accuracy vs.
33% baseline) exists but is driven by numeric fields that impurity-based
importance is known to overweight — reporting that nuance honestly is more
valuable than either overselling the model or dismissing it as pure noise.
See `data/model/ml_results.json` for the full model comparison.
