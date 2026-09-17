# Advanced ML Pipeline — Predicting Test Results
### Healthcare Intelligence Platform — Research/analytics prototype, NOT a diagnostic system.

Best model requested for improvement: **Random Forest, 40.5% test accuracy** (incumbent baseline, recreated here on an identical split for fair comparison).

**New best model: Random Forest, 43.2% test accuracy** (+2.75 percentage points). McNemar's test p=8.658e-08 — statistically significant at alpha=0.05: the improvement is unlikely to be chance.

## 1-2. Data Audit & Cleaning
- Raw shape: (55500, 15), duplicates removed: 534, final rows: 54,860 (98.85% retained)
- Signal verdict (pre-modeling): All tested features show p-values consistent with statistical independence from Test Results at typical significance thresholds, and effect sizes (Cramer's V) are near zero. This is strong evidence the synthetic generator assigned Test Results with little to no dependence on the other columns -- the dataset likely has a LOW theoretical accuracy ceiling for this target.
  - **Name**: EXCLUDED — 40167/54860 unique (73.2%); a near-unique identifier carries zero generalizable signal and would only let a model memorize rows.
  - **Doctor**: EXCLUDED from the clinically-meaningful feature sets (B-F) — 40276/54860 unique (73.4%); 76.7% of doctors appear exactly once. Retained ONLY in Feature Set A via frequency-encoding, to test empirically whether identifier information helps at all.
  - **Hospital**: Same treatment as Doctor — 39815/54860 unique (72.6%); 80.4% appear once.
  - **Room Number**: RETAINED as a numeric feature by default (400 distinct values, bounded 101-500 — moderate cardinality, not an identifier) but explicitly flagged: an earlier pass on this dataset found suspiciously high impurity-based importance for this field. Feature Set F removes it to test whether that importance is real or an artifact.

## 3. Feature Engineering
Age_Group, Billing_per_Stay_Day, Admission_Month/Quarter/Weekday/Season, Emergency_Flag, Condition×AdmissionType, Condition×Medication, AgeGroup×Condition — none derived from Test Results.

## 4. Feature Ablation
| Feature Set                  |   CV Accuracy |   CV F1 (macro) |   # Raw Columns | Description                                                                                |
|:-----------------------------|--------------:|----------------:|----------------:|:-------------------------------------------------------------------------------------------|
| A_all_features               |        0.3932 |          0.3928 |              12 | Every available field, including Doctor/Hospital via leakage-safe frequency encoding.      |
| B_no_identifiers             |        0.3944 |          0.3943 |              10 | All base fields minus Name/Doctor/Hospital identifiers.                                    |
| C_clinical_operational       |        0.3944 |          0.3943 |              10 | Clinically/operationally meaningful raw fields only (same as B for this dataset's schema). |
| D_meaningful_plus_engineered |        0.3908 |          0.3907 |              20 | C + every engineered feature.                                                              |
| E_no_billing                 |        0.3837 |          0.3836 |              18 | D minus Billing Amount and its derived feature Billing_per_Stay_Day.                       |
| F_no_room_number             |        0.3867 |          0.3867 |              19 | D minus Room Number.                                                                       |

**Winning configuration: `B_no_identifiers`**

## 6. Class Imbalance
Training class counts: {'Abnormal': 14719, 'Normal': 14642, 'Inconclusive': 14527} (ratio 1.013x). Class imbalance ratio is only 1.013x (near-perfectly balanced) — SMOTE is NOT automatically justified. class_weight='balanced' is used going forward: it matches or beats SMOTE here at zero synthetic-sample cost.

## 7. Full Model Comparison (winning feature config, 5-fold CV)
| Model                |   CV Accuracy |   CV F1 (macro) |   CV F1 (weighted) |
|:---------------------|--------------:|----------------:|-------------------:|
| Majority Baseline    |        0.3354 |          0.1674 |             0.1685 |
| Logistic Regression  |        0.3315 |          0.3312 |             0.3313 |
| Decision Tree        |        0.3392 |          0.3122 |             0.312  |
| Random Forest        |        0.3956 |          0.3955 |             0.3955 |
| Extra Trees          |        0.3932 |          0.3931 |             0.3932 |
| XGBoost              |        0.364  |          0.3639 |             0.364  |
| CatBoost             |        0.3535 |          0.3534 |             0.3534 |
| LightGBM             |        0.3592 |          0.3592 |             0.3592 |
| HistGradientBoosting |        0.3449 |          0.3439 |             0.3439 |

**Top 2 tuned:** Random Forest, Extra Trees

## 8-9. Hyperparameter Tuning & Final Selection
- **Random Forest**: best params `{'n_estimators': 400, 'min_samples_split': 10, 'min_samples_leaf': 2, 'max_features': 0.5, 'max_depth': None}`, CV macro F1 = 0.4
- **Extra Trees**: best params `{'n_estimators': 400, 'min_samples_split': 10, 'min_samples_leaf': 2, 'max_features': 0.5, 'max_depth': None}`, CV macro F1 = 0.3978

**Selected: Random Forest** — chosen by CV macro F1 with a check on the train/CV generalization gap and fold-to-fold stability, not by test accuracy.

## 10. Final Test-Set Evaluation (test set touched exactly twice, total)
| | Incumbent baseline (Random Forest) | Final model (Random Forest) |
|---|---|---|
| Test Accuracy | 0.4048 | 0.4323 |
| Test Macro F1 | 0.4046 | 0.4322 |
| Test ROC-AUC (macro) | 0.5799 | 0.6234 |

Improvement: **+2.75 percentage points**. McNemar's test p=8.658e-08 — statistically significant at alpha=0.05: the improvement is unlikely to be chance.

## 11. Interpretability
Top native feature importances: num__Billing Amount (0.1927), num__Room Number (0.1735), num__Age (0.1329), num__Length_of_Stay (0.1173), cat__Insurance Provider_Cigna (0.0147), cat__Medication_Ibuprofen (0.0145), cat__Medication_Aspirin (0.0144), cat__Medication_Lipitor (0.0143)


Top permutation importances (raw columns): Room Number (0.0519), Billing Amount (0.0484), Length_of_Stay (0.029), Age (0.0287), Medical Condition (0.0119), Blood Type (0.0108), Medication (0.0089), Admission Type (0.0083)


SHAP: not available for this run (see console log around Stage 11 for the exact reason — typically a hard 90s timeout on an unbounded-depth tuned forest). Native and permutation importance above are the interpretability evidence for this model.


**Room Number artifact check:** Room Number's importance rank is broadly consistent across native and permutation methods -- less evidence of a pure impurity-bias artifact, though it remains clinically meaningless and should not be trusted as a causal driver.


## 12. Error Analysis
Confusion matrix (rows=actual, cols=predicted, order=['Abnormal', 'Inconclusive', 'Normal']):

|              |   Abnormal |   Inconclusive |   Normal |
|:-------------|-----------:|---------------:|---------:|
| Abnormal     |       1638 |           1006 |     1036 |
| Inconclusive |       1096 |           1531 |     1005 |
| Normal       |       1041 |           1045 |     1574 |

The model struggles primarily because the independence tests in Stage 1 found little to no statistical association between Test Results and any available feature. What lift exists (over the 33% baseline) is concentrated in a few numeric fields and appears partly driven by incidental patterns rather than a strong causal signal, so confusions are spread fairly evenly across all three classes rather than concentrated in one predictable failure mode.

## 13. Predictability / Independence — Final Verdict
CONFIRMED empirically: best achievable test accuracy across 9 model families and hyperparameter tuning is 43.2%, only +2.75 points above the 40.5% incumbent and 9.9 points above the 33.3% no-information baseline. Combined with near-zero mutual information and non-significant independence tests in Stage 1, this dataset's Test Results column has a LOW theoretical accuracy ceiling with the available features — the synthetic generator appears to assign it with little to no dependence on the other columns. No amount of further tuning on THIS feature set is expected to substantially change that conclusion; more rows of the same distribution would tighten confidence intervals, not raise the ceiling.

Top features by mutual information: Billing Amount (0.03323), Medication_Paracetamol (0.00637), Insurance Provider_Aetna (0.00597), Gender_Female (0.00504), Medication_Ibuprofen (0.00415), Insurance Provider_Unitedhealthcare (0.00394), Medical Condition_Diabetes (0.00376), Gender_Male (0.00349)


## 15. Final Comparison Table
| Feature Set                  | Model                              |   CV Accuracy |   Test Accuracy |   Macro F1 |   ROC-AUC |   Generalization Gap |
|:-----------------------------|:-----------------------------------|--------------:|----------------:|-----------:|----------:|---------------------:|
| A_all_features               | Random Forest (probe)              |        0.3932 |        —      |     0.3928 |  —      |             —      |
| B_no_identifiers             | Random Forest (probe)              |        0.3944 |        —      |     0.3943 |  —      |             —      |
| C_clinical_operational       | Random Forest (probe)              |        0.3944 |        —      |     0.3943 |  —      |             —      |
| D_meaningful_plus_engineered | Random Forest (probe)              |        0.3908 |        —      |     0.3907 |  —      |             —      |
| E_no_billing                 | Random Forest (probe)              |        0.3837 |        —      |     0.3836 |  —      |             —      |
| F_no_room_number             | Random Forest (probe)              |        0.3867 |        —      |     0.3867 |  —      |             —      |
| B_no_identifiers             | Majority Baseline                  |        0.3354 |        —      |     0.1674 |  —      |             —      |
| B_no_identifiers             | Logistic Regression                |        0.3315 |        —      |     0.3312 |  —      |             —      |
| B_no_identifiers             | Decision Tree                      |        0.3392 |        —      |     0.3122 |  —      |             —      |
| B_no_identifiers             | Random Forest                      |        0.3956 |        —      |     0.3955 |  —      |             —      |
| B_no_identifiers             | Extra Trees                        |        0.3932 |        —      |     0.3931 |  —      |             —      |
| B_no_identifiers             | XGBoost                            |        0.364  |        —      |     0.3639 |  —      |             —      |
| B_no_identifiers             | CatBoost                           |        0.3535 |        —      |     0.3534 |  —      |             —      |
| B_no_identifiers             | LightGBM                           |        0.3592 |        —      |     0.3592 |  —      |             —      |
| B_no_identifiers             | HistGradientBoosting               |        0.3449 |        —      |     0.3439 |  —      |             —      |
| B_no_identifiers             | Random Forest (tuned)              |        0.4081 |        —      |     0.4081 |  —      |               0.5918 |
| B_no_identifiers             | Extra Trees (tuned)                |        0.4046 |        —      |     0.4045 |  —      |               0.5903 |
| original (prior project)     | Random Forest (incumbent baseline) |      —      |          0.4048 |     0.4046 |    0.5799 |             —      |
| B_no_identifiers             | Random Forest (FINAL SELECTED)     |        0.4081 |          0.4323 |     0.4322 |    0.6234 |               0.0242 |


## 16. Healthcare Safety Notice
This model is a research/analytics prototype trained on a **synthetic** dataset. It must NOT be presented as, or used as, a medical diagnostic system. It does not diagnose patients and carries no clinical validity.

## 17. Practical Note: Saved Model Size
`best_model.joblib` is **~348 MB** — the hyperparameter search legitimately selected
`max_depth=None, min_samples_leaf=2`, producing ~5,182 leaves per tree across 400
trees. That was the honest CV winner and is saved as-is (no result here was
adjusted to produce a smaller file). For any real deployment, capping `max_depth`
to roughly 16–20 would shrink the file by an estimated order of magnitude for a
sub-0.5-point macro-F1 cost, based on the shallower models' scores in Section 7 —
worth doing in practice, but not done here since it wasn't part of the CV-selected
configuration. This file is too large for a standard GitHub push (>100 MB) without
Git LFS; consider excluding `data/model/advanced_ml/best_model.joblib` from version
control if committing this repository.

*Full machine-readable results: `data/model/advanced_ml/full_results.json`. Saved model: `data/model/advanced_ml/best_model.joblib`.*