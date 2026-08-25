"""
Bootstrap Ensemble for Uncertainty-Aware Scoring
===================================================
Trains N XGBoost models, each on a different bootstrap resample of the
training data. At prediction time, we run all N models on the same input
and use the spread of their predictions as a confidence range -- wider
spread means the models disagree more, which is a reasonable proxy for
"the model is less sure about this kind of profile."

This also naturally correlates with data availability: profiles with
very short history (few analogous examples in training data) tend to
get less consistent predictions across the ensemble.
"""

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split

DATA_PATH = "data/synthetic_alt_credit_data.csv"
ENSEMBLE_OUT = "backend/ensemble.joblib"

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

N_MODELS = 25
RANDOM_SEED = 42


def main():
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )

    rng = np.random.default_rng(RANDOM_SEED)
    models = []

    print(f"Training {N_MODELS} bootstrap models...")
    for i in range(N_MODELS):
        # Bootstrap resample: sample len(X_train) rows WITH replacement
        idx = rng.integers(0, len(X_train), size=len(X_train))
        X_boot = X_train.iloc[idx]
        y_boot = y_train.iloc[idx]

        model = XGBClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            reg_lambda=0.1,
            eval_metric="logloss",
            random_state=RANDOM_SEED + i,  # vary seed too, for diversity
        )
        model.fit(X_boot, y_boot)
        models.append(model)

        if (i + 1) % 5 == 0:
            print(f"  {i + 1}/{N_MODELS} trained")

    joblib.dump({"models": models, "features": FEATURE_COLS}, ENSEMBLE_OUT)
    print(f"\nSaved ensemble of {N_MODELS} models -> {ENSEMBLE_OUT}")

    # Quick sanity check: how much do predictions actually vary on the test set?
    x_sample = X_test.iloc[[0]]
    probas = [m.predict_proba(x_sample)[0, 1] for m in models]
    print(f"\nSanity check on one test sample:")
    print(f"  Mean probability: {np.mean(probas):.3f}")
    print(f"  Std deviation:    {np.std(probas):.3f}")
    print(f"  Range (min-max):  {np.min(probas):.3f} - {np.max(probas):.3f}")


if __name__ == "__main__":
    main()