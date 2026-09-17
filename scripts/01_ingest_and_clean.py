"""
Stage 1 & 2 — Data Ingestion + Data Cleaning
Healthcare Intelligence Platform

Reads the raw synthetic healthcare dataset, produces a data-quality
assessment report, cleans it, and writes the clean analytical dataset.
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw" / "healthcare_dataset.csv"
CLEAN_OUT = BASE / "data" / "processed" / "healthcare_cleaned.csv"
REPORT_OUT = BASE / "reports" / "01_data_quality_report.md"

VALID_TEST_RESULTS = {"Normal", "Abnormal", "Inconclusive"}
VALID_GENDER = {"Male", "Female"}
VALID_ADMISSION_TYPE = {"Elective", "Emergency", "Urgent"}

# ---------------------------------------------------------------- STAGE 1
df = pd.read_csv(RAW)

report_lines = []
report_lines.append("# Stage 1 — Data Quality Assessment Report\n")
report_lines.append(f"- Rows: **{df.shape[0]:,}**")
report_lines.append(f"- Columns: **{df.shape[1]}**\n")

report_lines.append("## Dtypes (as loaded)\n")
report_lines.append("```\n" + df.dtypes.to_string() + "\n```\n")

n_dupes = df.duplicated().sum()
report_lines.append(f"## Duplicates\nFully duplicated rows: **{n_dupes}**\n")

report_lines.append("## Missing Values\n")
nulls = df.isnull().sum()
report_lines.append("```\n" + nulls.to_string() + "\n```\n")

report_lines.append("## Categorical Cardinality\n")
cat_cols = ["Gender", "Blood Type", "Medical Condition", "Doctor", "Hospital",
            "Insurance Provider", "Admission Type", "Medication", "Test Results"]
for c in cat_cols:
    report_lines.append(f"- **{c}**: {df[c].nunique():,} unique values")
report_lines.append("")

report_lines.append("## Casing Inconsistency Check (Name field sample)\n")
report_lines.append("```\n" + df["Name"].head(5).to_string() + "\n```\n")
report_lines.append("Name field uses inconsistent/random casing (e.g. 'Bobby JacksOn') — requires standardization.\n")

report_lines.append("## Target Variable Distribution — Test Results\n")
report_lines.append("```\n" + df["Test Results"].value_counts(dropna=False).to_string() + "\n```\n")
invalid_targets = df[~df["Test Results"].isin(VALID_TEST_RESULTS)]
report_lines.append(f"Invalid/unexpected target classes found: **{len(invalid_targets)}**\n")

report_lines.append("## Date Field Parse Check\n")
d1 = pd.to_datetime(df["Date of Admission"], errors="coerce")
d2 = pd.to_datetime(df["Discharge Date"], errors="coerce")
report_lines.append(f"- Unparseable 'Date of Admission': **{d1.isna().sum()}**")
report_lines.append(f"- Unparseable 'Discharge Date': **{d2.isna().sum()}**")
neg_stay = (d2 < d1).sum()
report_lines.append(f"- Records where Discharge Date < Date of Admission (invalid stay): **{neg_stay}**\n")

report_lines.append("## Numerical Field Sanity Checks\n")
report_lines.append(f"- Age range: {df['Age'].min()} to {df['Age'].max()}")
report_lines.append(f"- Age < 0 or > 110: **{((df['Age'] < 0) | (df['Age'] > 110)).sum()}**")
report_lines.append(f"- Billing Amount range: {df['Billing Amount'].min():.2f} to {df['Billing Amount'].max():.2f}")
report_lines.append(f"- Billing Amount <= 0 (invalid/negative charge): **{(df['Billing Amount'] <= 0).sum()}**")
report_lines.append(f"- Room Number range: {df['Room Number'].min()} to {df['Room Number'].max()}\n")

report_lines.append("## Categorical Validity Checks\n")
bad_gender = df[~df["Gender"].isin(VALID_GENDER)]
bad_admtype = df[~df["Admission Type"].isin(VALID_ADMISSION_TYPE)]
report_lines.append(f"- Gender values outside {VALID_GENDER}: **{len(bad_gender)}**")
report_lines.append(f"- Admission Type values outside {VALID_ADMISSION_TYPE}: **{len(bad_admtype)}**\n")

report_lines.append("## Outlier Investigation Note\n")
q1, q3 = df["Billing Amount"].quantile([0.25, 0.75])
iqr = q3 - q1
upper = q3 + 1.5 * iqr
n_high = (df["Billing Amount"] > upper).sum()
report_lines.append(
    f"IQR-based upper fence for Billing Amount is {upper:,.2f}; {n_high:,} records exceed it. "
    "These are treated as legitimate high-cost cases (not removed) — billing amount is continuous, "
    "synthetic, and shows no impossible values (no negatives, no extreme age outliers found), so no "
    "statistical trimming is applied. High-billing cases are instead flagged via a 'High Billing Flag' "
    "feature for analysis rather than deleted.\n"
)

REPORT_OUT.write_text("\n".join(report_lines))
print(f"Wrote data quality report -> {REPORT_OUT}")

# ---------------------------------------------------------------- STAGE 2 — CLEANING
clean = df.copy()

# 1. Standardize text casing
clean["Name"] = clean["Name"].str.strip().str.title()
for c in ["Gender", "Medical Condition", "Insurance Provider", "Admission Type",
          "Medication", "Test Results", "Doctor", "Hospital"]:
    clean[c] = clean[c].astype(str).str.strip().str.title()
clean["Blood Type"] = clean["Blood Type"].astype(str).str.strip().str.upper()

# 2. Parse dates
clean["Date of Admission"] = pd.to_datetime(clean["Date of Admission"], errors="coerce")
clean["Discharge Date"] = pd.to_datetime(clean["Discharge Date"], errors="coerce")

# 3. Drop unparseable dates and invalid stay records (Discharge < Admission)
before = len(clean)
clean = clean[clean["Date of Admission"].notna() & clean["Discharge Date"].notna()]
clean = clean[clean["Discharge Date"] >= clean["Date of Admission"]]
dropped_dates = before - len(clean)

# 4. Drop exact duplicate rows
before = len(clean)
clean = clean.drop_duplicates()
dropped_dupes = before - len(clean)

# 5. Validate target variable — keep only the 3 valid classes
before = len(clean)
clean = clean[clean["Test Results"].isin(VALID_TEST_RESULTS)]
dropped_target = before - len(clean)

# 6. Validate Gender / Admission Type against known categories
before = len(clean)
clean = clean[clean["Gender"].isin(VALID_GENDER)]
clean = clean[clean["Admission Type"].isin(VALID_ADMISSION_TYPE)]
dropped_cat = before - len(clean)

# 7. Numerical validity — Age must be plausible, Billing Amount must be positive
before = len(clean)
clean = clean[(clean["Age"] >= 0) & (clean["Age"] <= 110)]
clean = clean[clean["Billing Amount"] > 0]
dropped_num = before - len(clean)

# 8. Reset index
clean = clean.reset_index(drop=True)

clean.to_csv(CLEAN_OUT, index=False)

summary = f"""
## Stage 2 — Cleaning Summary
- Starting rows: {df.shape[0]:,}
- Dropped (unparseable/invalid date range): {dropped_dates:,}
- Dropped (exact duplicates): {dropped_dupes:,}
- Dropped (invalid Test Results class): {dropped_target:,}
- Dropped (invalid Gender/Admission Type): {dropped_cat:,}
- Dropped (invalid Age/Billing Amount): {dropped_num:,}
- **Final clean rows: {clean.shape[0]:,}**
- Retention rate: {clean.shape[0] / df.shape[0] * 100:.2f}%
"""
with open(REPORT_OUT, "a") as f:
    f.write(summary)

print(summary)
print(f"Wrote cleaned dataset -> {CLEAN_OUT}")
