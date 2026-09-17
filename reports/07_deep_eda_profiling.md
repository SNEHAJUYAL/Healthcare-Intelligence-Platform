# Deep EDA & Data Profiling
### Healthcare Intelligence Platform

This report goes beyond `01_data_quality_report.md` and `02_eda_summary.md` — every categorical field is tested for statistical uniformity, every numeric field is profiled for distribution shape, outliers are checked with three independent methods, and repeat identities are separated into genuine repeat admissions vs. true near-duplicates.

## 1. Column Profile

**Numeric fields:**

| Column         |       Min |     P25 |   Median |     Mean |     P75 |     Max |      Std |    Skew |   Kurtosis | Shape                                                       |
|:---------------|----------:|--------:|---------:|---------:|--------:|--------:|---------:|--------:|-----------:|:------------------------------------------------------------|
| Age            |  13       |    35   |     52   |    51.53 |    68   |    89   |    19.61 | -0.0058 |    -1.1861 | Approximately UNIFORM (excess kurtosis near -1.2, low skew) |
| Billing Amount |   9.23879 | 13299.7 |  25593.9 | 25594.6  | 37847.1 | 52764.3 | 14175.9  |  0      |    -1.1922 | Approximately UNIFORM (excess kurtosis near -1.2, low skew) |
| Room Number    | 101       |   202   |    302   |   301.11 |   400   |   500   |   115.22 | -0.0109 |    -1.1932 | Approximately UNIFORM (excess kurtosis near -1.2, low skew) |
| Length of Stay |   1       |     8   |     15   |    15.5  |    23   |    30   |     8.66 |  0.0028 |    -1.2055 | Approximately UNIFORM (excess kurtosis near -1.2, low skew) |


**Categorical fields:**

| Column             |   Unique Values |   Top Value Share % |
|:-------------------|----------------:|--------------------:|
| Gender             |               2 |               50.03 |
| Blood Type         |               8 |               12.54 |
| Medical Condition  |               6 |               16.78 |
| Insurance Provider |               5 |               20.26 |
| Admission Type     |               3 |               33.61 |
| Medication         |               5 |               20.08 |
| Test Results       |               3 |               33.54 |


**Identifier fields (excluded from ML features):**

| Column   |   Unique Values |   Cardinality Ratio |   % Appearing Exactly Once |
|:---------|----------------:|--------------------:|---------------------------:|
| Name     |           40167 |              0.7322 |                      76.67 |
| Doctor   |           40276 |              0.7342 |                      76.7  |
| Hospital |           39815 |              0.7258 |                      80.44 |


**Date fields:**

| Column            |   Unique Values |
|:------------------|----------------:|
| Date of Admission |            1827 |
| Discharge Date    |            1856 |


## 2. Uniformity (Goodness-of-Fit) Tests

For each categorical field, a chi-square goodness-of-fit test against a perfectly uniform distribution (every category equally likely). This is the rigorous version of the 'near-equal counts' observation made throughout the project.

| Field              |   Categories |   Chi2 |   p-value | Max Deviation from Uniform   | Verdict                                                                                               |
|:-------------------|-------------:|-------:|----------:|:-----------------------------|:------------------------------------------------------------------------------------------------------|
| Gender             |            2 |  0.026 |  0.871118 | 0.07%                        | Statistically indistinguishable from uniform (p > 0.05) -- consistent with random category assignment |
| Blood Type         |            8 |  0.973 |  0.995258 | 0.36%                        | Statistically indistinguishable from uniform (p > 0.05) -- consistent with random category assignment |
| Medical Condition  |            6 |  1.34  |  0.930771 | 0.7%                         | Statistically indistinguishable from uniform (p > 0.05) -- consistent with random category assignment |
| Admission Type     |            3 |  4.044 |  0.132414 | 0.82%                        | Statistically indistinguishable from uniform (p > 0.05) -- consistent with random category assignment |
| Insurance Provider |            5 |  5.072 |  0.280007 | 1.3%                         | Statistically indistinguishable from uniform (p > 0.05) -- consistent with random category assignment |
| Medication         |            5 |  0.495 |  0.974031 | 0.42%                        | Statistically indistinguishable from uniform (p > 0.05) -- consistent with random category assignment |
| Test Results       |            3 |  1.594 |  0.450633 | 0.61%                        | Statistically indistinguishable from uniform (p > 0.05) -- consistent with random category assignment |


## 3. Correlation & Association

**Numeric (Pearson):**

|                |     Age |   Billing Amount |   Room Number |   Length of Stay |
|:---------------|--------:|-----------------:|--------------:|-----------------:|
| Age            |  1      |          -0.0033 |       -0.0003 |           0.008  |
| Billing Amount | -0.0033 |           1      |       -0.0037 |          -0.0048 |
| Room Number    | -0.0003 |          -0.0037 |        1      |          -0.0046 |
| Length of Stay |  0.008  |          -0.0048 |       -0.0046 |           1      |


Strongest numeric pair: `('Age', 'Length of Stay')` — r = 0.0080 (negligible).


**Categorical (Cramer's V):**

|                    |   Gender |   Blood Type |   Medical Condition |   Admission Type |   Insurance Provider |   Medication |
|:-------------------|---------:|-------------:|--------------------:|-----------------:|---------------------:|-------------:|
| Gender             |   1      |       0.0161 |              0.0046 |           0.0134 |               0.0078 |       0.0105 |
| Blood Type         |   0.0161 |       1      |              0.0114 |           0.0117 |               0.0123 |       0.0113 |
| Medical Condition  |   0.0046 |       0.0114 |              1      |           0.0125 |               0.0083 |       0.0098 |
| Admission Type     |   0.0134 |       0.0117 |              0.0125 |           1      |               0.0127 |       0.0073 |
| Insurance Provider |   0.0078 |       0.0123 |              0.0083 |           0.0127 |               1      |       0.0069 |
| Medication         |   0.0105 |       0.0113 |              0.0098 |           0.0073 |               0.0069 |       1      |


Strongest categorical pair: `('Gender', 'Blood Type')` — V = 0.0161 (negligible; 0 = no association, 1 = perfect association). Every field in this dataset is essentially independent of every other field, not just independent of Test Results.


## 4. Outlier Detection — Three Methods Compared

| Column         |   IQR Method |   Z-Score Method |   Both Agree |
|:---------------|-------------:|-----------------:|-------------:|
| Billing Amount |            0 |                0 |            0 |
| Age            |            0 |                0 |            0 |
| Length of Stay |            0 |                0 |            0 |

IQR and Z-score flag ZERO outliers on all three columns -- a direct consequence of each being approximately uniform over a bounded range (Section 1), which has no long tail for either rule to catch. Isolation Forest is fit once, jointly, across all three columns (multivariate) with contamination=0.02, which by construction flags the 1098 MOST-isolated rows (1098/54860 = 2.00%, matching the requested 2% quantile almost exactly) -- this is a forced quantile cut, not a discovered anomaly count, and should not be read as '1,098 real anomalies exist'. Together, all three methods agree: there is no genuine outlier population in this dataset, consistent with this project's earlier decision not to blindly trim extreme values.


## 5. Duplicate / Repeat-Identity Deep Dive

- Exact duplicate rows removed during cleaning: **534**
- (Name, Age, Gender, Blood Type) identities appearing more than once: **22**
- Of those, genuine repeat admissions (other fields differ): **22**
- Of those, still fully identical elsewhere (near-duplicate): **0**

22 (Name, Age, Gender, Blood Type) combinations appear more than once. 22 of those have differing admission details (condition, dates, billing, etc.) -- these read as the SAME synthetic identity reused across independent, distinct admission records (expected in a randomly generated dataset with a finite name pool), not as duplicate data entry. Only 0 groups have fully identical other fields as well, and those would already have been caught by the exact-duplicate-row removal in Stage 2 cleaning.


## 6. What Kind of Healthcare Dataset Is This?

This is admission-level, tabular, cross-sectional SYNTHETIC data -- structurally similar to a simplified hospital Admission-Discharge-Transfer (ADT) feed or a claims summary extract, but without the longitudinal patient history a real Electronic Health Record (EHR) system carries, the clinical granularity of a disease registry (e.g. a cancer or diabetes registry with lab values and staging), or the survey-sampling design of population data like NHANES. The uniformity tests above are the tell: real EHR/claims/registry data is never this evenly distributed across categories -- see reports/04_reality_check.md and 05_external_data_sources.md for the real-world comparison. Studying this dataset is useful for learning the MECHANICS of healthcare analytics (cleaning, feature engineering, star schemas, leakage-safe ML) but not for learning what real clinical data distributions look like -- that requires the real, skewed statistics cited elsewhere in this project.


## Bottom Line

Every axis of this profiling exercise points the same direction as the earlier independence tests in the ML pipeline: this dataset's categorical fields are statistically uniform (7/7 fields indistinguishable from random assignment), its numeric fields show negligible correlation with each other, and its 'outliers' are ordinary tail values rather than multivariate anomalies. This is a well-behaved, internally-consistent SYNTHETIC dataset — excellent for practicing the full data-analysis and ML-engineering workflow end to end, and explicitly not a substitute for real clinical data when the goal is learning what real healthcare distributions look like.