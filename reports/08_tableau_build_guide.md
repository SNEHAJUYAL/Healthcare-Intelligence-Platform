# Tableau Build Guide
### Healthcare Intelligence Platform

This is a step-by-step guide to building the real `.twbx` Tableau workbook from
this project's star schema — the same 9 dashboards already prototyped in
`dashboard/console.html`, now for actual Tableau Desktop/Public.

Every KPI value below is the **known-correct** number from
`data/model/module_metrics.json` — use them to sanity-check your build as you
go. If your Tableau number doesn't match, the relationship or filter is wrong
somewhere, not the source data.

---

## 1. Files you need

All in `data/model/`:

```
fact_admissions.csv        the fact table — one row per admission (54,860 rows)
dim_patient.csv            patient_id, Name, Age, Gender, Blood Type, Age Group, Senior Citizen Flag
dim_hospital.csv           hospital_id, Hospital
dim_doctor.csv             doctor_id, Doctor
dim_condition.csv          condition_id, Medical Condition
dim_insurance.csv          insurance_id, Insurance Provider
dim_medication.csv         medication_id, Medication
dim_admission_type.csv     admission_type_id, Admission Type
dim_date.csv               date_id (YYYYMMDD int), date, year, quarter, month, month_name, weekday, is_weekend
```

`fact_admissions.csv` columns: `admission_id, patient_id, hospital_id, doctor_id,
condition_id, insurance_id, medication_id, admission_type_id, admission_date_id,
discharge_date_id, billing_amount, length_of_stay, room_number, test_results,
emergency_flag, high_billing_flag, long_stay_flag, high_utilization_indicator,
peak_admission_period, billing_category, billing_per_stay_day`

**Tip**: copy all 9 CSVs into one folder and open that folder in Tableau (`Connect
→ Text File → More... → select folder`) rather than adding files one at a time —
Tableau will list every sheet and you build relationships from there.

---

## 2. Connect and build relationships

Use Tableau's **Relationships** canvas (the default when you drag a second
table onto the canvas next to the first) — not legacy inner/left Joins. Relationships
keep each table at its native grain, which matters here because `dim_patient`
(54,838 rows) and `fact_admissions` (54,860 rows) are *not* 1:1.

Drag `fact_admissions` onto the canvas first, then drag each dimension table
next to it and set the relationship key:

| Fact column | Dimension table | Dimension key |
|---|---|---|
| `hospital_id` | dim_hospital | `hospital_id` |
| `doctor_id` | dim_doctor | `doctor_id` |
| `condition_id` | dim_condition | `condition_id` |
| `insurance_id` | dim_insurance | `insurance_id` |
| `medication_id` | dim_medication | `medication_id` |
| `admission_type_id` | dim_admission_type | `admission_type_id` |
| `patient_id` | dim_patient | `patient_id` |

**The one tricky part — dates.** `fact_admissions` has *two* date foreign keys
(`admission_date_id`, `discharge_date_id`) both pointing at the *same*
`dim_date.date_id`. Tableau needs two separate logical copies of `dim_date` for
this (a "role-playing dimension"):

1. Drag `dim_date` onto the canvas, relate it via `admission_date_id = date_id`. Double-click its name in the canvas and rename it **"Admission Date"**.
2. Drag `dim_date` onto the canvas **a second time** (Tableau treats each drag as a new logical table even from the same file), relate it via `discharge_date_id = date_id`. Rename this instance **"Discharge Date"**.

Use the "Admission Date" copy for every trend/seasonality chart in this
project — that's what all the module numbers below are built on.

---

## 3. Build the 9 dashboards

For each dashboard: sheet name, chart type, shelf placement, and the number to
validate against.

### Dashboard 1 — Executive Overview
| Sheet | Type | Rows/Columns | Validate against |
|---|---|---|---|
| KPI: Total Patients | Text/BigNumber | `COUNTD([admission_id])` | **54,860** |
| KPI: Total Billing | Text/BigNumber | `SUM([billing_amount])` | **$1,404,121,601.31** |
| KPI: Avg Billing | Text/BigNumber | `AVG([billing_amount])` | **$25,594.63** |
| KPI: Avg Length of Stay | Text/BigNumber | `AVG([length_of_stay])` | **15.50 days** |
| Admission Trend | Line | Columns: `Admission Date` (Month/Year, continuous) · Rows: `COUNTD([admission_id])` | Aug 2020 peak ≈ 1,002; exclude the last partial month (2024-05, only 212 records) |
| Revenue Trend | Line | Columns: `Admission Date` (Month/Year) · Rows: `SUM([billing_amount])` | Same partial-month caveat |
| Top Conditions | Horizontal Bar | Rows: `[Medical Condition]` · Columns: `COUNTD([admission_id])`, sorted desc | Arthritis highest at **9,207** |

**Emergency %** calculated field: `SUM(IF [Admission Type]="Emergency" THEN 1 ELSE 0 END) / COUNTD([admission_id])` → **32.94%**
**Abnormal Test %** calculated field: `SUM(IF [test_results]="Abnormal" THEN 1 ELSE 0 END) / COUNTD([admission_id])` → **33.54%**

### Dashboard 2 — Hospital Performance
Filter every sheet to hospitals with `{FIXED [Hospital]: COUNTD([admission_id])} > 1` (7,789 of 39,815 hospitals qualify) — otherwise you're ranking single-admission "hospitals," which is meaningless noise.
| Sheet | Type | Validate against |
|---|---|---|
| Top by Volume | Bar, `[Hospital]` × `COUNTD([admission_id])` | "Llc Smith" highest at **44** |
| Top by Revenue | Bar, `[Hospital]` × `SUM([billing_amount])` | "Johnson Plc" highest at **$1,081,477.31** |

### Dashboard 3 — Financial Intelligence
| Sheet | Type | Validate against |
|---|---|---|
| Revenue by Condition | Bar, `[Medical Condition]` × `SUM([billing_amount])` | All 6 within **$229.9M–$236.5M** — expect a nearly flat bar chart |
| Revenue by Insurance | Bar, `[Insurance Provider]` × `SUM([billing_amount])` | All 5 within **$276.5M–$284.3M** |
| Revenue by Admission Type | Bar, `[Admission Type]` × `SUM([billing_amount])` | All 3 within **$461.7M–$473.2M** |
| High-Billing Cases | KPI | `COUNTD` filtered to `[high_billing_flag]="Yes"` | **5,486** (10.0%) |
| LOS vs. Billing | Scatter | `[length_of_stay]` × `[billing_amount]` | Trend line should be nearly flat — r = **-0.0048** |

### Dashboard 4 — Insurance Intelligence
| Sheet | Type | Validate against |
|---|---|---|
| Provider Volume | Bar, `[Insurance Provider]` × `COUNTD([admission_id])` | Cigna highest at **11,115** |
| Provider Avg Billing | Bar, `[Insurance Provider]` × `AVG([billing_amount])` | All within **$25,459–$25,678** |

*Label this dashboard "payer pattern analysis" — `billing_amount` is a recorded charge, not a confirmed paid claim (see `DOCUMENTATION.md` Section 21).*

### Dashboard 5 — Doctor Analytics
Same volume filter as Dashboard 2, applied to `[Doctor]` instead — restrict to the 9,384 doctors with `COUNTD([admission_id]) > 1`.
| Sheet | Type | Validate against |
|---|---|---|
| Top by Volume | Bar, `[Doctor]` × `COUNTD([admission_id])` | "Michael Smith" highest at **27** |

### Dashboard 6 — Patient Intelligence
| Sheet | Type | Validate against |
|---|---|---|
| Age Group Distribution | Bar, `[Age Group]` × `COUNTD([admission_id])` | Senior (66+) highest at **16,064** (29.3%) |
| Gender Split | Pie/Bar | Male **50.03%** / Female **49.97%** |
| Avg LOS by Condition | Bar, `[Medical Condition]` × `AVG([length_of_stay])` | All 6 within **15.4–15.7 days** |

### Dashboard 7 — Resource Planning
| Sheet | Type | Validate against |
|---|---|---|
| Admissions by Month | Bar, `Admission Date` (Month, discrete) × `COUNTD([admission_id])` | Peak: **Aug 4,777 / Jul 4,762 / Jan 4,646** |
| Long-Stay Cases | KPI, filtered to `[long_stay_flag]="Yes"` | **5,520** (10.06%) |

*Label every metric here a "capacity-demand proxy" — there's no real bed-occupancy field in this dataset.*

### Dashboard 8 — Predictive Analytics
This dashboard doesn't come from the star schema — it visualizes
`data/model/advanced_ml/full_results.json` and `comparison_table.csv`
(the outputs of `scripts/08_advanced_ml_pipeline.py`). Import
`comparison_table.csv` as its own data source and build:
| Sheet | Type | Validate against |
|---|---|---|
| Model Comparison | Bar, `[Model]` × `[CV Accuracy]`, split by `[Feature Set]` | Final model **Random Forest**, test accuracy **43.2%** |
| Confusion Matrix | Highlight table (hardcode the 3×3 from the report — Tableau can't compute this natively from row-level fact data without the model's predictions attached) | See `reports/06_advanced_ml_pipeline.md` §12 |

### Dashboard 9 — Executive Recommendations
No chart — a formatted text table. Copy the 8 rows from
`reports/03_business_recommendations.md` directly; add a colored shape
(red/amber/green) per Priority column for visual scanning.

---

## 4. Useful Tableau calculated fields

```
// % of Total Billing (table calc, drop onto Label + right-click → Add Table Calculation → Percent of Total)
SUM([billing_amount])

// High-Billing flag as a filter-friendly boolean (if you prefer not to trust the string field directly)
[billing_amount] >= {FIXED : PERCENTILE([billing_amount], 0.9)}

// Repeat-volume filter for Hospital/Doctor dashboards
{FIXED [Hospital] : COUNTD([admission_id])} > 1
```

---

## 5. Design consistency with the existing dashboard

If you want the Tableau workbook to visually match `dashboard/console.html`:
- **Accent color**: `#1c7d8c` (teal) for primary series, `#4d6b8a` (slate blue) for secondary.
- **Font**: Tableau doesn't support custom web fonts natively, but "Tableau Book"/"Tableau Semibold" on a light `#eef1f2` background is the closest built-in match to the console's tone.
- **KPI tiles**: use Tableau's "Text" worksheet type with a large number format and a small caption below, mirroring the console's KPI cards.

---

## 6. Validation checklist before calling it done

Run through these once your workbook is built — every one is a known-correct number from this project's own pipeline output:

- [ ] Total Patients = 54,860
- [ ] Total Billing = $1,404,121,601.31
- [ ] Average Billing = $25,594.63
- [ ] Average Length of Stay = 15.50 days
- [ ] Emergency % = 32.94%
- [ ] Hospitals on record = 39,815 (only 7,789 with >1 admission)
- [ ] Doctors on record = 40,276 (only 9,384 with >1 admission)
- [ ] Top condition by volume = Arthritis (9,207)
- [ ] High-Billing case count = 5,486 (10.0%)
- [ ] Long-Stay case count = 5,520 (10.06%)

If all ten match, your relationships are set up correctly and the rest of the
workbook will be trustworthy too.
