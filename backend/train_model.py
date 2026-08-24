"""
Train the Alternative Credit Scoring model using XGBoost, with a
Logistic Regression baseline for comparison.
"""

import json
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score,
    classification_report,
    confusion_matrix,
    brier_score_loss,
)

DATA_PATH = "data/synthetic_alt_credit_data.csv"
MODEL_OUT = "backend/model.joblib"
METRICS_OUT = "backend/metrics.json"

FEATURE_COLS = [
    "utility_payment_punctuality_score",
    "wallet_txn_regularity",
    "wallet_avg_monthly_txn_count",
    "subscription_payment_consistency",
    "employment_stability_months",
    "education_level",
    "avg_monthly_income_proxy",
    "rent_payment_punctuality",
    "has_rent_data",
    "months_of_data_available",
]
TARGET_COL = "creditworthy"


def main():
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # ---- Main model: real XGBoost ----
    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        reg_lambda=0.1,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, y_proba)
    brier = brier_score_loss(y_test, y_proba)
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred).tolist()

    print(f"ROC-AUC: {auc:.4f}")
    print(f"Brier score (lower=better calibration): {brier:.4f}")
    print(classification_report(y_test, y_pred))
    print("Confusion matrix:\n", np.array(cm))

    # ---- Baseline: Logistic Regression ----
    baseline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    baseline.fit(X_train, y_train)
    baseline_auc = roc_auc_score(y_test, baseline.predict_proba(X_test)[:, 1])
    print(f"\nBaseline Logistic Regression ROC-AUC: {baseline_auc:.4f}")

    # ---- Save artifacts ----
    joblib.dump({"model": model, "features": FEATURE_COLS}, MODEL_OUT)

    metrics = {
        "roc_auc": auc,
        "brier_score": brier,
        "baseline_logreg_roc_auc": baseline_auc,
        "classification_report": report,
        "confusion_matrix": cm,
        "n_train": len(X_train),
        "n_test": len(X_test),
    }
    with open(METRICS_OUT, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nSaved model -> {MODEL_OUT}")
    print(f"Saved metrics -> {METRICS_OUT}")


if __name__ == "__main__":
    main()