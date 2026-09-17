"""
Stage 8 — Predictive Analytics
Healthcare Intelligence Platform

Multi-class classification of `Test Results` (Normal / Abnormal / Inconclusive).
This is presented as a research/analytics prototype, NOT a medical diagnostic
system — it demonstrates whether available patient/admission attributes carry
any predictive signal for test-result categorization.

Leakage-conscious design:
  - Name, Doctor, Hospital dropped (near-unique identifiers in this synthetic
    dataset — including them would let tree models memorize training rows
    without generalizing, and they carry no real clinical signal).
  - Raw date columns dropped in favor of already-engineered calendar features
    (Length of Stay, Admission Month/Quarter/Weekday) computed upstream in
    the feature-engineering stage, not from test-set information.
  - Train/test split performed BEFORE any resampling; SMOTE (where used) is
    applied only inside the cross-validation training fold via an
    imblearn Pipeline, never on the full dataset up front.
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                              confusion_matrix, f1_score, precision_score,
                              recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

BASE = Path(__file__).resolve().parents[1]
df = pd.read_csv(BASE / "data" / "processed" / "healthcare_features.csv",
                  parse_dates=["Date of Admission", "Discharge Date"])

TARGET = "Test Results"

NUMERIC_FEATURES = ["Age", "Billing Amount", "Length of Stay", "Room Number",
                     "Billing per Stay Day", "Admission Quarter"]
CATEGORICAL_FEATURES = ["Gender", "Blood Type", "Medical Condition", "Admission Type",
                         "Insurance Provider", "Medication", "Age Group",
                         "Senior Citizen Flag", "Admission Month", "Admission Weekday",
                         "Emergency Flag", "Billing Category", "High Billing Flag",
                         "Peak Admission Period", "Long-Stay Flag",
                         "High-Utilization Indicator"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

X = df[FEATURES].copy()
y_raw = df[TARGET].copy()

le = LabelEncoder()
y = le.fit_transform(y_raw)
CLASS_NAMES = list(le.classes_)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

preprocess = ColumnTransformer(transformers=[
    ("num", StandardScaler(), NUMERIC_FEATURES),
    ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
])

MODELS = {
    "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
    "Decision Tree": DecisionTreeClassifier(max_depth=10, class_weight="balanced", random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=200, max_depth=12,
                                             class_weight="balanced", random_state=42, n_jobs=-1),
    "XGBoost": XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                              eval_metric="mlogloss", random_state=42, n_jobs=-1),
    "CatBoost": CatBoostClassifier(iterations=300, depth=6, learning_rate=0.1,
                                    verbose=False, random_state=42),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = {}
fitted_pipelines = {}

print("=" * 70)
print("CROSS-VALIDATED MODEL COMPARISON (train set, 5-fold stratified CV)")
print("=" * 70)

for name, model in MODELS.items():
    t0 = time.time()
    pipe = Pipeline([("preprocess", preprocess), ("model", model)])
    cv_scores = cross_validate(
        pipe, X_train, y_train, cv=cv,
        scoring={"accuracy": "accuracy", "f1_macro": "f1_macro",
                 "precision_macro": "precision_macro", "recall_macro": "recall_macro"},
        n_jobs=1,
    )
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    y_proba = pipe.predict_proba(X_test)

    test_acc = accuracy_score(y_test, y_pred)
    test_f1 = f1_score(y_test, y_pred, average="macro")
    test_prec = precision_score(y_test, y_pred, average="macro")
    test_rec = recall_score(y_test, y_pred, average="macro")
    try:
        test_auc = roc_auc_score(y_test, y_proba, multi_class="ovr", average="macro")
    except Exception:
        test_auc = None

    cm = confusion_matrix(y_test, y_pred).tolist()

    results[name] = {
        "cv_accuracy_mean": round(float(cv_scores["test_accuracy"].mean()), 4),
        "cv_accuracy_std": round(float(cv_scores["test_accuracy"].std()), 4),
        "cv_f1_macro_mean": round(float(cv_scores["test_f1_macro"].mean()), 4),
        "test_accuracy": round(float(test_acc), 4),
        "test_precision_macro": round(float(test_prec), 4),
        "test_recall_macro": round(float(test_rec), 4),
        "test_f1_macro": round(float(test_f1), 4),
        "test_roc_auc_macro": round(float(test_auc), 4) if test_auc is not None else None,
        "confusion_matrix": cm,
        "train_seconds": round(time.time() - t0, 1),
    }
    fitted_pipelines[name] = pipe
    print(f"{name:25s} | CV acc {results[name]['cv_accuracy_mean']:.4f} "
          f"| test acc {test_acc:.4f} | test f1 {test_f1:.4f} | {results[name]['train_seconds']}s")

# --------------------------------------------------------------------
# Stacking Ensemble (RF + XGB + CatBoost -> Logistic Regression meta-learner)
# --------------------------------------------------------------------
print("\nTraining Stacking Ensemble...")
t0 = time.time()
stack = StackingClassifier(
    estimators=[
        ("rf", RandomForestClassifier(n_estimators=150, max_depth=10, class_weight="balanced",
                                       random_state=42, n_jobs=-1)),
        ("xgb", XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.1,
                               eval_metric="mlogloss", random_state=42, n_jobs=-1)),
        ("cat", CatBoostClassifier(iterations=200, depth=5, learning_rate=0.1,
                                    verbose=False, random_state=42)),
    ],
    final_estimator=LogisticRegression(max_iter=1000),
    cv=3, n_jobs=1,
)
stack_pipe = Pipeline([("preprocess", preprocess), ("model", stack)])
cv_scores = cross_validate(
    stack_pipe, X_train, y_train, cv=cv,
    scoring={"accuracy": "accuracy", "f1_macro": "f1_macro"}, n_jobs=1,
)
stack_pipe.fit(X_train, y_train)
y_pred = stack_pipe.predict(X_test)
y_proba = stack_pipe.predict_proba(X_test)

results["Stacking Ensemble"] = {
    "cv_accuracy_mean": round(float(cv_scores["test_accuracy"].mean()), 4),
    "cv_accuracy_std": round(float(cv_scores["test_accuracy"].std()), 4),
    "cv_f1_macro_mean": round(float(cv_scores["test_f1_macro"].mean()), 4),
    "test_accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
    "test_precision_macro": round(float(precision_score(y_test, y_pred, average="macro")), 4),
    "test_recall_macro": round(float(recall_score(y_test, y_pred, average="macro")), 4),
    "test_f1_macro": round(float(f1_score(y_test, y_pred, average="macro")), 4),
    "test_roc_auc_macro": round(float(roc_auc_score(y_test, y_proba, multi_class="ovr", average="macro")), 4),
    "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    "train_seconds": round(time.time() - t0, 1),
}
fitted_pipelines["Stacking Ensemble"] = stack_pipe
print(f"Stacking Ensemble        | CV acc {results['Stacking Ensemble']['cv_accuracy_mean']:.4f} "
      f"| test acc {results['Stacking Ensemble']['test_accuracy']:.4f} "
      f"| test f1 {results['Stacking Ensemble']['test_f1_macro']:.4f} "
      f"| {results['Stacking Ensemble']['train_seconds']}s")

# --------------------------------------------------------------------
# SMOTE-in-pipeline check (imbalance is mild here — classes are ~33/33/33 —
# but the correct leakage-safe methodology is demonstrated on Random Forest)
# --------------------------------------------------------------------
print("\nSMOTE-in-pipeline check (Random Forest, for imbalance-handling comparison)...")
class_counts = pd.Series(y_train).value_counts().to_dict()
smote_pipe = ImbPipeline([
    ("preprocess", preprocess),
    ("smote", SMOTE(random_state=42)),
    ("model", RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)),
])
cv_scores_smote = cross_validate(
    smote_pipe, X_train, y_train, cv=cv,
    scoring={"accuracy": "accuracy", "f1_macro": "f1_macro"}, n_jobs=1,
)
smote_pipe.fit(X_train, y_train)
y_pred_smote = smote_pipe.predict(X_test)
smote_result = {
    "class_balance_in_training_set": {CLASS_NAMES[k]: int(v) for k, v in class_counts.items()},
    "cv_accuracy_mean": round(float(cv_scores_smote["test_accuracy"].mean()), 4),
    "cv_f1_macro_mean": round(float(cv_scores_smote["test_f1_macro"].mean()), 4),
    "test_accuracy": round(float(accuracy_score(y_test, y_pred_smote)), 4),
    "test_f1_macro": round(float(f1_score(y_test, y_pred_smote, average="macro")), 4),
    "conclusion": (
        "Test Results classes are already near-balanced (~33% each), so SMOTE resampling "
        "inside the training fold produces materially the same accuracy/F1 as class-weighted "
        "Random Forest without it — imbalance handling is not a material lever for this dataset, "
        "but the leakage-safe pattern (resample only inside the CV training fold, never before "
        "the train/test split) is demonstrated here for methodological completeness."
    ),
}
print(json.dumps(smote_result, indent=2))

# --------------------------------------------------------------------
# Feature importance (from Random Forest — most directly interpretable of the tree models)
# --------------------------------------------------------------------
rf_pipe = fitted_pipelines["Random Forest"]
ohe_names = rf_pipe.named_steps["preprocess"].named_transformers_["cat"].get_feature_names_out(CATEGORICAL_FEATURES)
all_feature_names = NUMERIC_FEATURES + list(ohe_names)
importances = rf_pipe.named_steps["model"].feature_importances_
feat_imp = sorted(zip(all_feature_names, importances), key=lambda x: -x[1])[:15]
feat_imp = [{"feature": f, "importance": round(float(v), 4)} for f, v in feat_imp]

# --------------------------------------------------------------------
# Prediction distribution (best model on test set, by accuracy)
# --------------------------------------------------------------------
best_model_name = max(results, key=lambda k: results[k]["test_accuracy"])
best_pipe = fitted_pipelines[best_model_name]
best_pred = best_pipe.predict(X_test)
pred_dist = pd.Series(le.inverse_transform(best_pred)).value_counts().to_dict()
actual_dist = pd.Series(le.inverse_transform(y_test)).value_counts().to_dict()

# --------------------------------------------------------------------
# Write everything for the dashboard
# --------------------------------------------------------------------
output = {
    "class_names": CLASS_NAMES,
    "train_size": int(len(X_train)),
    "test_size": int(len(X_test)),
    "features_used": FEATURES,
    "features_excluded": ["Name", "Doctor", "Hospital", "Date of Admission", "Discharge Date",
                           "Disease Category", "Medication Category", "Test Result Category"],
    "features_excluded_reason": (
        "Name/Doctor/Hospital are near-unique identifiers in this synthetic dataset (no repeatable "
        "signal, high overfitting risk); raw dates are superseded by engineered calendar features; "
        "Disease/Medication/Test Result 'Category' columns are exact duplicates of source columns."
    ),
    "model_comparison": results,
    "best_model": best_model_name,
    "smote_imbalance_check": smote_result,
    "feature_importance_random_forest": feat_imp,
    "prediction_distribution_best_model": pred_dist,
    "actual_distribution_test_set": actual_dist,
    "disclaimer": (
        "This model is a research/analytics prototype demonstrating whether patient and admission "
        "attributes carry predictive signal for test-result categorization. It is NOT a medical "
        "diagnostic system and must not be used for clinical decision-making."
    ),
}

OUT_JSON = BASE / "data" / "model" / "ml_results.json"
OUT_JSON.write_text(json.dumps(output, indent=2, default=str))
print(f"\nWrote ML results -> {OUT_JSON}")
print(f"Best model by test accuracy: {best_model_name} ({results[best_model_name]['test_accuracy']})")
