"""
Stage 5 — Analytical Data Model (Star Schema)
Healthcare Intelligence Platform

Builds a Patient/Admission fact table plus conformed dimensions from the
featured dataset. Output CSVs are designed to be loaded directly into
Tableau (or any BI tool) as a star schema.
"""
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
IN_PATH = BASE / "data" / "processed" / "healthcare_features.csv"
MODEL_DIR = BASE / "data" / "model"
MODEL_DIR.mkdir(exist_ok=True)

df = pd.read_csv(IN_PATH, parse_dates=["Date of Admission", "Discharge Date"])
df["admission_id"] = df.index + 1

def make_dim(col, id_name):
    vals = sorted(df[col].dropna().unique())
    dim = pd.DataFrame({id_name: range(1, len(vals) + 1), col: vals})
    return dim

dim_hospital = make_dim("Hospital", "hospital_id")
dim_doctor = make_dim("Doctor", "doctor_id")
dim_condition = make_dim("Medical Condition", "condition_id")
dim_insurance = make_dim("Insurance Provider", "insurance_id")
dim_medication = make_dim("Medication", "medication_id")
dim_admission_type = make_dim("Admission Type", "admission_type_id")

# Patient dimension — synthetic dataset has no patient ID, so a patient
# "identity" is approximated from Name + Age + Gender + Blood Type.
patient_cols = ["Name", "Age", "Gender", "Blood Type", "Age Group", "Senior Citizen Flag"]
dim_patient = df[patient_cols].drop_duplicates().reset_index(drop=True)
dim_patient["patient_id"] = dim_patient.index + 1
dim_patient = dim_patient[["patient_id"] + patient_cols]

# Date dimension — covers every admission and discharge date observed
all_dates = pd.to_datetime(pd.concat([df["Date of Admission"], df["Discharge Date"]]).unique())
dim_date = pd.DataFrame({"date": sorted(all_dates)})
dim_date["date_id"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
dim_date["year"] = dim_date["date"].dt.year
dim_date["quarter"] = dim_date["date"].dt.quarter
dim_date["month"] = dim_date["date"].dt.month
dim_date["month_name"] = dim_date["date"].dt.month_name()
dim_date["weekday"] = dim_date["date"].dt.day_name()
dim_date["is_weekend"] = dim_date["date"].dt.dayofweek.isin([5, 6])
dim_date = dim_date[["date_id", "date", "year", "quarter", "month", "month_name", "weekday", "is_weekend"]]

# ---------------- Fact table ----------------
fact = df.merge(dim_patient, on=patient_cols, how="left") \
         .merge(dim_hospital, on="Hospital", how="left") \
         .merge(dim_doctor, on="Doctor", how="left") \
         .merge(dim_condition, on="Medical Condition", how="left") \
         .merge(dim_insurance, on="Insurance Provider", how="left") \
         .merge(dim_medication, on="Medication", how="left") \
         .merge(dim_admission_type, on="Admission Type", how="left")

fact["admission_date_id"] = fact["Date of Admission"].dt.strftime("%Y%m%d").astype(int)
fact["discharge_date_id"] = fact["Discharge Date"].dt.strftime("%Y%m%d").astype(int)

fact_cols = [
    "admission_id", "patient_id", "hospital_id", "doctor_id", "condition_id",
    "insurance_id", "medication_id", "admission_type_id",
    "admission_date_id", "discharge_date_id",
    "Billing Amount", "Length of Stay", "Room Number", "Test Results",
    "Emergency Flag", "High Billing Flag", "Long-Stay Flag",
    "High-Utilization Indicator", "Peak Admission Period",
    "Billing Category", "Billing per Stay Day",
]
fact_admissions = fact[fact_cols].rename(columns={
    "Billing Amount": "billing_amount", "Length of Stay": "length_of_stay",
    "Room Number": "room_number", "Test Results": "test_results",
    "Emergency Flag": "emergency_flag", "High Billing Flag": "high_billing_flag",
    "Long-Stay Flag": "long_stay_flag", "High-Utilization Indicator": "high_utilization_indicator",
    "Peak Admission Period": "peak_admission_period", "Billing Category": "billing_category",
    "Billing per Stay Day": "billing_per_stay_day",
})

fact_admissions.to_csv(MODEL_DIR / "fact_admissions.csv", index=False)
dim_patient.to_csv(MODEL_DIR / "dim_patient.csv", index=False)
dim_hospital.to_csv(MODEL_DIR / "dim_hospital.csv", index=False)
dim_doctor.to_csv(MODEL_DIR / "dim_doctor.csv", index=False)
dim_condition.to_csv(MODEL_DIR / "dim_condition.csv", index=False)
dim_insurance.to_csv(MODEL_DIR / "dim_insurance.csv", index=False)
dim_medication.to_csv(MODEL_DIR / "dim_medication.csv", index=False)
dim_admission_type.to_csv(MODEL_DIR / "dim_admission_type.csv", index=False)
dim_date.to_csv(MODEL_DIR / "dim_date.csv", index=False)

print("Star schema written to data/model/:")
for name, d in [("fact_admissions", fact_admissions), ("dim_patient", dim_patient),
                ("dim_hospital", dim_hospital), ("dim_doctor", dim_doctor),
                ("dim_condition", dim_condition), ("dim_insurance", dim_insurance),
                ("dim_medication", dim_medication), ("dim_admission_type", dim_admission_type),
                ("dim_date", dim_date)]:
    print(f"  {name}: {d.shape}")
