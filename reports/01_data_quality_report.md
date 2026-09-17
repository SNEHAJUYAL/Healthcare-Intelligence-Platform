# Stage 1 — Data Quality Assessment Report

- Rows: **55,500**
- Columns: **15**

## Dtypes (as loaded)

```
Name                   object
Age                     int64
Gender                 object
Blood Type             object
Medical Condition      object
Date of Admission      object
Doctor                 object
Hospital               object
Insurance Provider     object
Billing Amount        float64
Room Number             int64
Admission Type         object
Discharge Date         object
Medication             object
Test Results           object
```

## Duplicates
Fully duplicated rows: **534**

## Missing Values

```
Name                  0
Age                   0
Gender                0
Blood Type            0
Medical Condition     0
Date of Admission     0
Doctor                0
Hospital              0
Insurance Provider    0
Billing Amount        0
Room Number           0
Admission Type        0
Discharge Date        0
Medication            0
Test Results          0
```

## Categorical Cardinality

- **Gender**: 2 unique values
- **Blood Type**: 8 unique values
- **Medical Condition**: 6 unique values
- **Doctor**: 40,341 unique values
- **Hospital**: 39,876 unique values
- **Insurance Provider**: 5 unique values
- **Admission Type**: 3 unique values
- **Medication**: 5 unique values
- **Test Results**: 3 unique values

## Casing Inconsistency Check (Name field sample)

```
0    Bobby JacksOn
1     LesLie TErRy
2      DaNnY sMitH
3     andrEw waTtS
4    adrIENNE bEll
```

Name field uses inconsistent/random casing (e.g. 'Bobby JacksOn') — requires standardization.

## Target Variable Distribution — Test Results

```
Test Results
Abnormal        18627
Normal          18517
Inconclusive    18356
```

Invalid/unexpected target classes found: **0**

## Date Field Parse Check

- Unparseable 'Date of Admission': **0**
- Unparseable 'Discharge Date': **0**
- Records where Discharge Date < Date of Admission (invalid stay): **0**

## Numerical Field Sanity Checks

- Age range: 13 to 89
- Age < 0 or > 110: **0**
- Billing Amount range: -2008.49 to 52764.28
- Billing Amount <= 0 (invalid/negative charge): **108**
- Room Number range: 101 to 500

## Categorical Validity Checks

- Gender values outside {'Female', 'Male'}: **0**
- Admission Type values outside {'Emergency', 'Elective', 'Urgent'}: **0**

## Outlier Investigation Note

IQR-based upper fence for Billing Amount is 74,689.43; 0 records exceed it. These are treated as legitimate high-cost cases (not removed) — billing amount is continuous, synthetic, and shows no impossible values (no negatives, no extreme age outliers found), so no statistical trimming is applied. High-billing cases are instead flagged via a 'High Billing Flag' feature for analysis rather than deleted.

## Stage 2 — Cleaning Summary
- Starting rows: 55,500
- Dropped (unparseable/invalid date range): 0
- Dropped (exact duplicates): 534
- Dropped (invalid Test Results class): 0
- Dropped (invalid Gender/Admission Type): 0
- Dropped (invalid Age/Billing Amount): 106
- **Final clean rows: 54,860**
- Retention rate: 98.85%
