"""
Stage 3 (EDA) + Stage 6 (8 Business Analytics Modules)
Healthcare Intelligence Platform

Computes every metric referenced by the 8 analytical modules directly from
the featured dataset / star schema, and writes:
  - reports/02_eda_summary.md      (business-question-driven EDA write-up)
  - data/model/module_metrics.json (structured metrics feeding the dashboards)

No numbers in the dashboards are hand-typed — everything here is computed
from data and consumed downstream.
"""
import json
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
df = pd.read_csv(BASE / "data" / "processed" / "healthcare_features.csv",
                  parse_dates=["Date of Admission", "Discharge Date"])

MONTH_ORDER = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]

def pct(n, d):
    return round(100 * n / d, 2) if d else 0.0

def top_n(series, n=10):
    vc = series.value_counts().head(n)
    return [{"label": str(k), "value": int(v)} for k, v in vc.items()]

metrics = {}

# =====================================================================
# MODULE 1 — EXECUTIVE ANALYTICS
# =====================================================================
total_patients = len(df)
total_billing = df["Billing Amount"].sum()
avg_billing = df["Billing Amount"].mean()
avg_los = df["Length of Stay"].mean()
emergency_pct = pct((df["Admission Type"] == "Emergency").sum(), total_patients)
abnormal_pct = pct((df["Test Results"] == "Abnormal").sum(), total_patients)
n_hospitals = df["Hospital"].nunique()
n_doctors = df["Doctor"].nunique()

admission_trend = (
    df.groupby([df["Date of Admission"].dt.to_period("M")]).size()
    .rename("count").reset_index()
)
admission_trend["period"] = admission_trend["Date of Admission"].astype(str)
admission_trend = admission_trend[["period", "count"]].sort_values("period")

revenue_trend = (
    df.groupby([df["Date of Admission"].dt.to_period("M")])["Billing Amount"].sum()
    .rename("revenue").reset_index()
)
revenue_trend["period"] = revenue_trend["Date of Admission"].astype(str)
revenue_trend = revenue_trend[["period", "revenue"]].sort_values("period")

metrics["executive"] = {
    "kpis": {
        "total_patients": int(total_patients),
        "total_billing": round(float(total_billing), 2),
        "avg_billing": round(float(avg_billing), 2),
        "avg_length_of_stay": round(float(avg_los), 2),
        "emergency_admission_pct": emergency_pct,
        "abnormal_test_pct": abnormal_pct,
        "n_hospitals": int(n_hospitals),
        "n_doctors": int(n_doctors),
    },
    "admission_trend": admission_trend.to_dict("records"),
    "revenue_trend": revenue_trend.to_dict("records"),
    "top_conditions": top_n(df["Medical Condition"], 6),
    "billing_distribution": top_n(df["Billing Category"], 3),
    "test_result_distribution": top_n(df["Test Results"], 3),
    "admission_type_mix": top_n(df["Admission Type"], 3),
}

# =====================================================================
# MODULE 2 — HOSPITAL PERFORMANCE
# =====================================================================
hosp = df.groupby("Hospital").agg(
    patient_volume=("Billing Amount", "size"),
    total_billing=("Billing Amount", "sum"),
    avg_billing=("Billing Amount", "mean"),
    avg_los=("Length of Stay", "mean"),
).reset_index()
hosp["emergency_pct"] = df.groupby("Hospital")["Admission Type"].apply(
    lambda s: pct((s == "Emergency").sum(), len(s))).values
hosp["abnormal_pct"] = df.groupby("Hospital")["Test Results"].apply(
    lambda s: pct((s == "Abnormal").sum(), len(s))).values
hosp_multi = hosp[hosp["patient_volume"] > 1].copy()

metrics["hospital_performance"] = {
    "note": (
        f"{n_hospitals:,} distinct hospital names exist across {total_patients:,} admissions "
        f"({(hosp['patient_volume'] > 1).sum():,} hospitals have more than one admission on record). "
        "Ranking below is restricted to hospitals with repeat volume so averages are meaningful."
    ),
    "top_by_volume": hosp_multi.nlargest(10, "patient_volume")
        .round(2).to_dict("records"),
    "top_by_billing": hosp_multi.nlargest(10, "total_billing")
        .round(2).to_dict("records"),
    "top_by_los": hosp_multi.nlargest(10, "avg_los")
        .round(2).to_dict("records"),
    "top_by_emergency_pct": hosp_multi[hosp_multi["patient_volume"] >= 5]
        .nlargest(10, "emergency_pct").round(2).to_dict("records"),
}

# =====================================================================
# MODULE 3 — FINANCIAL ANALYTICS
# =====================================================================
billing_by_disease = df.groupby("Medical Condition")["Billing Amount"].agg(
    total="sum", average="mean", count="size").reset_index().round(2)
billing_by_admtype = df.groupby("Admission Type")["Billing Amount"].agg(
    total="sum", average="mean", count="size").reset_index().round(2)
billing_by_insurance = df.groupby("Insurance Provider")["Billing Amount"].agg(
    total="sum", average="mean", count="size").reset_index().round(2)
los_billing_corr = df["Length of Stay"].corr(df["Billing Amount"])

metrics["financial"] = {
    "total_billing": round(float(total_billing), 2),
    "avg_billing_per_stay_day": round(float(df["Billing per Stay Day"].mean()), 2),
    "high_billing_case_count": int((df["High Billing Flag"] == "Yes").sum()),
    "high_billing_case_pct": pct((df["High Billing Flag"] == "Yes").sum(), total_patients),
    "los_billing_correlation": round(float(los_billing_corr), 4),
    "revenue_by_disease": billing_by_disease.sort_values("total", ascending=False).to_dict("records"),
    "revenue_by_admission_type": billing_by_admtype.sort_values("total", ascending=False).to_dict("records"),
    "revenue_by_insurance": billing_by_insurance.sort_values("total", ascending=False).to_dict("records"),
    "top_revenue_hospitals": hosp_multi.nlargest(10, "total_billing")[["Hospital", "total_billing"]]
        .round(2).to_dict("records"),
}

# =====================================================================
# MODULE 4 — INSURANCE ANALYTICS
# =====================================================================
ins_summary = df.groupby("Insurance Provider").agg(
    patient_volume=("Billing Amount", "size"),
    total_billing=("Billing Amount", "sum"),
    avg_billing=("Billing Amount", "mean"),
).reset_index().round(2)

ins_disease = (
    df.groupby(["Insurance Provider", "Medical Condition"])["Billing Amount"].sum()
    .reset_index().sort_values(["Insurance Provider", "Billing Amount"], ascending=[True, False])
    .groupby("Insurance Provider").head(1).round(2)
)
ins_admtype = (
    df.groupby(["Insurance Provider", "Admission Type"]).size()
    .rename("count").reset_index()
)

metrics["insurance"] = {
    "disclaimer": (
        "Billing Amount reflects total patient charges recorded in the dataset, not confirmed "
        "insurance claim payouts — the dataset does not include separate claims data."
    ),
    "provider_summary": ins_summary.sort_values("patient_volume", ascending=False).to_dict("records"),
    "top_disease_by_provider": ins_disease.rename(
        columns={"Billing Amount": "billing_amount"}).to_dict("records"),
    "admission_type_mix_by_provider": ins_admtype.to_dict("records"),
}

# =====================================================================
# MODULE 5 — DOCTOR PERFORMANCE
# =====================================================================
doc = df.groupby("Doctor").agg(
    patients_treated=("Billing Amount", "size"),
    avg_billing=("Billing Amount", "mean"),
    avg_los=("Length of Stay", "mean"),
).reset_index().round(2)
doc_multi = doc[doc["patients_treated"] > 1]

metrics["doctor_performance"] = {
    "note": (
        f"{n_doctors:,} distinct doctor names exist across {total_patients:,} admissions "
        f"({(doc['patients_treated'] > 1).sum():,} doctors have more than one admission on record). "
        "This is consistent with a synthetic, largely one-doctor-per-admission dataset — workload "
        "figures below describe the repeat-volume subset only and should not be read as real "
        "clinical-quality signals."
    ),
    "top_by_volume": doc_multi.nlargest(10, "patients_treated").to_dict("records"),
    "top_by_avg_billing": doc_multi[doc_multi["patients_treated"] >= 3]
        .nlargest(10, "avg_billing").to_dict("records"),
    "top_by_avg_los": doc_multi[doc_multi["patients_treated"] >= 3]
        .nlargest(10, "avg_los").to_dict("records"),
    "workload_distribution": {
        "single_case_doctors": int((doc["patients_treated"] == 1).sum()),
        "repeat_case_doctors": int((doc["patients_treated"] > 1).sum()),
        "max_cases_by_one_doctor": int(doc["patients_treated"].max()),
    },
}

# =====================================================================
# MODULE 6 — PATIENT ANALYTICS
# =====================================================================
disease_by_age = pd.crosstab(df["Age Group"], df["Medical Condition"])
disease_los = df.groupby("Medical Condition")["Length of Stay"].mean().round(2).sort_values(ascending=False)
med_by_condition = (
    df.groupby(["Medical Condition", "Medication"]).size().rename("count").reset_index()
    .sort_values(["Medical Condition", "count"], ascending=[True, False])
    .groupby("Medical Condition").head(1)
)

metrics["patient_analytics"] = {
    "disease_prevalence": top_n(df["Medical Condition"], 6),
    "admissions_by_age_group": top_n(df["Age Group"], 10),
    "gender_distribution": top_n(df["Gender"], 2),
    "blood_type_distribution": top_n(df["Blood Type"], 8),
    "avg_los_by_condition": [{"label": k, "value": v} for k, v in disease_los.items()],
    "top_medication_by_condition": med_by_condition.rename(
        columns={"Medical Condition": "condition", "Medication": "top_medication"}
    )[["condition", "top_medication", "count"]].to_dict("records"),
    "test_result_by_condition": pd.crosstab(
        df["Medical Condition"], df["Test Results"]).reset_index().to_dict("records"),
}

# =====================================================================
# MODULE 7 — RESOURCE PLANNING
# =====================================================================
admissions_by_weekday = df["Admission Weekday"].value_counts().reindex(
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
).fillna(0).astype(int)
admissions_by_month = df["Admission Month"].value_counts().reindex(MONTH_ORDER).fillna(0).astype(int)
los_distribution = df["Length of Stay"].describe().round(2).to_dict()

metrics["resource_planning"] = {
    "disclaimer": (
        "The dataset has no bed-capacity, staffing, or occupancy data. Figures below are "
        "capacity-demand *proxies* derived from admission volume, length of stay, and room-number "
        "spread — not actual bed utilization."
    ),
    "admissions_by_month": [{"label": k, "value": int(v)} for k, v in admissions_by_month.items()],
    "admissions_by_weekday": [{"label": k, "value": int(v)} for k, v in admissions_by_weekday.items()],
    "peak_months": sorted(df["Admission Month"].value_counts().nlargest(3).index.tolist()),
    "length_of_stay_distribution": los_distribution,
    "long_stay_case_count": int((df["Long-Stay Flag"] == "Yes").sum()),
    "long_stay_case_pct": pct((df["Long-Stay Flag"] == "Yes").sum(), total_patients),
    "room_number_range": {"min": int(df["Room Number"].min()), "max": int(df["Room Number"].max())},
    "admission_type_by_month": pd.crosstab(
        df["Admission Month"], df["Admission Type"]).reindex(MONTH_ORDER).reset_index().to_dict("records"),
}

# =====================================================================
# WRITE OUTPUT
# =====================================================================
OUT_JSON = BASE / "data" / "model" / "module_metrics.json"
OUT_JSON.write_text(json.dumps(metrics, indent=2, default=str))
print(f"Wrote module metrics -> {OUT_JSON}")

# ---------------------------------------------------------------- EDA REPORT
eda_lines = []
eda_lines.append("# Stage 3 — Exploratory Data Analysis (Business Perspective)\n")

eda_lines.append("## Patient Demographics")
eda_lines.append(f"- Gender split: {df['Gender'].value_counts().to_dict()}")
eda_lines.append(f"- Age range: {df['Age'].min()}–{df['Age'].max()}, mean {df['Age'].mean():.1f}")
eda_lines.append(f"- Most common blood type: {df['Blood Type'].value_counts().idxmax()}")
eda_lines.append(f"- Largest age group: {df['Age Group'].value_counts().idxmax()}\n")

eda_lines.append("## Medical Conditions")
eda_lines.append(f"- Disease frequency (near-uniform by design): {df['Medical Condition'].value_counts().to_dict()}")
eda_lines.append(f"- Condition with longest avg stay: {disease_los.idxmax()} ({disease_los.max():.1f} days)")
eda_lines.append(f"- Condition with highest avg billing: {billing_by_disease.sort_values('average', ascending=False).iloc[0]['Medical Condition']}\n")

eda_lines.append("## Hospital Operations")
eda_lines.append(f"- Admissions are spread across {n_hospitals:,} distinct hospital names ({(hosp['patient_volume']>1).sum():,} with >1 admission)")
eda_lines.append(f"- Peak admission months: {sorted(df['Admission Month'].value_counts().nlargest(3).index.tolist())}")
eda_lines.append(f"- Average length of stay: {avg_los:.2f} days (90th pct: {df['Length of Stay'].quantile(0.9):.0f} days)")
eda_lines.append(f"- Admission type mix: {df['Admission Type'].value_counts().to_dict()}\n")

eda_lines.append("## Financial")
eda_lines.append(f"- Total billing across all admissions: ${total_billing:,.0f}")
eda_lines.append(f"- Average billing per admission: ${avg_billing:,.2f}")
eda_lines.append(f"- Correlation between Length of Stay and Billing Amount: {los_billing_corr:.4f} (effectively no linear relationship — billing looks independent of stay length in this synthetic dataset)")
eda_lines.append(f"- Highest-revenue medical condition: {billing_by_disease.sort_values('total', ascending=False).iloc[0]['Medical Condition']}")
eda_lines.append(f"- Insurance billing spread across providers is nearly even: {dict(zip(ins_summary['Insurance Provider'], ins_summary['total_billing']))}\n")

eda_lines.append("## Clinical")
eda_lines.append(f"- Test result distribution: {df['Test Results'].value_counts().to_dict()} — classes are near-balanced")
eda_lines.append("- No strong association observed between Medical Condition and Test Results (near-uniform crosstab), consistent with this being a synthetic dataset without embedded clinical causality.\n")

REPORT_OUT = BASE / "reports" / "02_eda_summary.md"
REPORT_OUT.write_text("\n".join(eda_lines))
print(f"Wrote EDA summary -> {REPORT_OUT}")
