"""
Stage 4 — Feature Engineering
Healthcare Intelligence Platform

Reads the cleaned dataset and derives business-relevant features used by
both the analytical data model / dashboards and the ML pipeline.
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
IN_PATH = BASE / "data" / "processed" / "healthcare_cleaned.csv"
OUT_PATH = BASE / "data" / "processed" / "healthcare_features.csv"

df = pd.read_csv(IN_PATH, parse_dates=["Date of Admission", "Discharge Date"])

# ---------------- Patient Features ----------------
df["Age Group"] = pd.cut(
    df["Age"], bins=[-1, 12, 19, 35, 50, 65, 200],
    labels=["Child (0-12)", "Teen (13-19)", "Young Adult (20-35)",
            "Adult (36-50)", "Middle Age (51-65)", "Senior (66+)"]
)
df["Senior Citizen Flag"] = np.where(df["Age"] >= 65, "Yes", "No")
df["Gender Category"] = df["Gender"]

# ---------------- Admission Features ----------------
df["Length of Stay"] = (df["Discharge Date"] - df["Date of Admission"]).dt.days.clip(lower=0)
df["Admission Month"] = df["Date of Admission"].dt.month_name()
df["Admission Year"] = df["Date of Admission"].dt.year
df["Admission Quarter"] = df["Date of Admission"].dt.quarter
df["Admission Weekday"] = df["Date of Admission"].dt.day_name()
df["Emergency Flag"] = np.where(df["Admission Type"] == "Emergency", "Yes", "No")

# ---------------- Financial Features ----------------
billing_q = df["Billing Amount"].quantile([0.33, 0.66]).values
def billing_category(x):
    if x <= billing_q[0]:
        return "Low"
    elif x <= billing_q[1]:
        return "Medium"
    return "High"
df["Billing Category"] = df["Billing Amount"].apply(billing_category)

high_billing_threshold = df["Billing Amount"].quantile(0.90)
df["High Billing Flag"] = np.where(df["Billing Amount"] >= high_billing_threshold, "Yes", "No")
df["Billing per Stay Day"] = df["Billing Amount"] / df["Length of Stay"].replace(0, 1)

# ---------------- Medical Features ----------------
df["Disease Category"] = df["Medical Condition"]
df["Medication Category"] = df["Medication"]
df["Test Result Category"] = df["Test Results"]

# ---------------- Operational Features ----------------
peak_months = df["Admission Month"].value_counts().nlargest(3).index.tolist()
df["Peak Admission Period"] = np.where(df["Admission Month"].isin(peak_months), "Yes", "No")

long_stay_threshold = df["Length of Stay"].quantile(0.90)
df["Long-Stay Flag"] = np.where(df["Length of Stay"] >= long_stay_threshold, "Yes", "No")

df["High-Utilization Indicator"] = np.where(
    (df["Long-Stay Flag"] == "Yes") | (df["High Billing Flag"] == "Yes"), "Yes", "No"
)

df.to_csv(OUT_PATH, index=False)

print("Feature engineering complete.")
print(f"Peak admission months (top 3 by volume): {peak_months}")
print(f"High billing threshold (90th pct): {high_billing_threshold:,.2f}")
print(f"Long-stay threshold (90th pct, days): {long_stay_threshold:.1f}")
print(f"Output columns: {list(df.columns)}")
print(f"Wrote featured dataset -> {OUT_PATH}  shape={df.shape}")
