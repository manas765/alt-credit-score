"""
Explainability layer for the alt-credit model using real SHAP TreeExplainer.
"""

import joblib
import shap
import pandas as pd

MODEL_PATH = "backend/model.joblib"
DATA_PATH = "data/synthetic_alt_credit_data.csv"

FEATURE_LABELS = {
    "utility_payment_punctuality_score": "Utility bill punctuality",
    "wallet_txn_regularity": "Wallet transaction regularity",
    "wallet_avg_monthly_txn_count": "Wallet transaction frequency",
    "subscription_payment_consistency": "Subscription payment consistency",
    "employment_stability_months": "Employment stability (months)",
    "education_level": "Education level",
    "avg_monthly_income_proxy": "Estimated monthly income",
    "rent_payment_punctuality": "Rent payment punctuality",
    "has_rent_data": "Rent data available",
    "months_of_data_available": "Months of data on file",
}


def load_model():
    bundle = joblib.load(MODEL_PATH)
    return bundle["model"], bundle["features"]


def build_explainer(model):
    return shap.TreeExplainer(model)


def explain_prediction(explainer, features, input_row: dict):
    """
    Returns (probability, list of {feature, label, value, contribution})
    sorted by absolute contribution, descending.
    """
    x_df = pd.DataFrame([[input_row[f] for f in features]], columns=features)
    shap_values = explainer.shap_values(x_df)

    # shap_values shape: (1, n_features) for binary XGBoost classifier
    row_shap = shap_values[0]

    contributions = []
    for i, feat in enumerate(features):
        contributions.append({
            "feature": feat,
            "label": FEATURE_LABELS.get(feat, feat),
            "value": input_row[feat],
            "contribution": round(float(row_shap[i]), 4),
        })

    contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)
    return contributions


if __name__ == "__main__":
    model, features = load_model()
    explainer = build_explainer(model)

    df = pd.read_csv(DATA_PATH)
    sample_user = df.iloc[0][features].to_dict()

    contribs = explain_prediction(explainer, features, sample_user)

    print("Top contributing factors for sample user:\n")
    for c in contribs[:5]:
        direction = "increases" if c["contribution"] > 0 else "decreases"
        print(f"  {c['label']:<38} value={c['value']:.2f} -> {direction} score by {abs(c['contribution']):.4f}")