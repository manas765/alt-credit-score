"""
Bias / Fairness Audit
=======================
Checks whether the model's predictions or errors skew meaningfully across
education_level and employment_stability_months bands. This does NOT
prove the model is fair in any legal/formal sense -- it's a first-pass
diagnostic appropriate for a portfolio project, on synthetic data. Real
deployment would need a much more rigorous fairness framework (e.g.
demographic parity, equalized odds, tested against real population data
with legal/domain expert review).

We report this analysis honestly regardless of outcome -- if the model
DOES show disparity, that's not a project failure. It's the point of
doing the audit, and it's an even stronger interview talking point:
"I found X, and here's how I would address it."
"""

import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score

MODEL_PATH = "backend/model.joblib"
DATA_PATH = "data/synthetic_alt_credit_data.csv"


def load_model():
    bundle = joblib.load(MODEL_PATH)
    return bundle["model"], bundle["features"]


def audit_by_group(model, features, df, group_col, bins=None, labels=None):
    print(f"\n{'='*60}")
    print(f"AUDIT: {group_col}")
    print(f"{'='*60}")

    work_df = df.copy()
    if bins is not None:
        work_df["_group"] = pd.cut(work_df[group_col], bins=bins, labels=labels)
    else:
        work_df["_group"] = work_df[group_col]

    X = work_df[features]
    y = work_df["creditworthy"]
    proba = model.predict_proba(X)[:, 1]
    work_df["_proba"] = proba
    work_df["_pred"] = (proba >= 0.5).astype(int)
    work_df["_correct"] = (work_df["_pred"] == y).astype(int)

    summary = work_df.groupby("_group", observed=True).agg(
        n=("_group", "count"),
        avg_predicted_proba=("_proba", "mean"),
        actual_positive_rate=("creditworthy", "mean"),
        accuracy=("_correct", "mean"),
    ).round(3)

    print(summary)

    # Per-group AUC where possible (needs both classes present)
    print("\nPer-group ROC-AUC (data permitting):")
    for grp in work_df["_group"].dropna().unique():
        sub = work_df[work_df["_group"] == grp]
        if sub["creditworthy"].nunique() == 2:
            auc = roc_auc_score(sub["creditworthy"], sub["_proba"])
            print(f"  {grp}: AUC = {auc:.3f}  (n={len(sub)})")
        else:
            print(f"  {grp}: insufficient class variation to compute AUC (n={len(sub)})")

    return summary


if __name__ == "__main__":
    model, features = load_model()
    df = pd.read_csv(DATA_PATH)

    # Audit 1: education level (already a discrete 0-3 scale)
    audit_by_group(model, features, df, "education_level")

    # Audit 2: employment stability, binned into bands
    audit_by_group(
        model, features, df, "employment_stability_months",
        bins=[-1, 6, 12, 24, 1000],
        labels=["0-6mo", "6-12mo", "12-24mo", "24mo+"]
    )