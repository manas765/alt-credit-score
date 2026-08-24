"""
Data-Gap Coach
==============
For thin-file users, the useful question isn't just "what's my score" --
it's "what's the highest-leverage piece of missing data I could add to
improve it." This module simulates that: for each data source the user
hasn't provided, it estimates the score uplift if they added a *realistic
good-case* value for that source, based on population data.

This deliberately does NOT promise an exact number ("add rent data, gain
exactly 40 points") -- alt-data scoring in the real world doesn't work
that precisely, and promising false precision here would be misleading.
Instead we give a directional, honestly-hedged estimate.
"""

import joblib
import pandas as pd
import numpy as np

MODEL_PATH = "backend/model.joblib"
DATA_PATH = "data/synthetic_alt_credit_data.csv"

# Which features represent "data sources" a user might not have linked yet,
# and the companion flag (if any) indicating whether they have it.
# For features without an explicit flag, we treat "at population minimum"
# as the not-provided proxy (a reasonable stand-in for this demo).
DATA_SOURCES = {
    "rent_payment_punctuality": {
        "label": "Rent payment history",
        "flag_feature": "has_rent_data",
    },
    "subscription_payment_consistency": {
        "label": "Subscription/recurring payment history",
        "flag_feature": None,
    },
    "utility_payment_punctuality_score": {
        "label": "Utility bill payment history",
        "flag_feature": None,
    },
}

GOOD_CASE_PERCENTILE = 0.75  # "good, achievable" value = 75th percentile of population


def load_model():
    bundle = joblib.load(MODEL_PATH)
    return bundle["model"], bundle["features"]


def proba_to_score(proba, score_min=300, score_max=900):
    return int(round(score_min + proba * (score_max - score_min)))


def suggest_data_gaps(model, features, input_row: dict, background_df: pd.DataFrame):
    """
    Returns a list of suggestions, sorted by estimated score uplift,
    for data sources the user appears not to have provided.
    """
    x_df = pd.DataFrame([[input_row[f] for f in features]], columns=features)
    base_proba = model.predict_proba(x_df)[0, 1]
    base_score = proba_to_score(base_proba)

    suggestions = []

    for feat, meta in DATA_SOURCES.items():
        flag = meta["flag_feature"]
        is_missing = False

        if flag is not None:
            is_missing = input_row.get(flag, 1) == 0
        else:
            # No explicit flag: treat "at/near population minimum" as a
            # proxy for "this data source looks unlinked/very thin."
            pop_min = background_df[feat].quantile(0.05)
            is_missing = input_row[feat] <= pop_min

        if not is_missing:
            continue

        good_case_value = background_df[feat].quantile(GOOD_CASE_PERCENTILE)

        hypothetical = x_df.copy()
        hypothetical.iloc[0, features.index(feat)] = good_case_value
        if flag is not None and flag in features:
            hypothetical.iloc[0, features.index(flag)] = 1

        new_proba = model.predict_proba(hypothetical)[0, 1]
        new_score = proba_to_score(new_proba)
        uplift = new_score - base_score

        if uplift > 0:
            suggestions.append({
                "data_source": meta["label"],
                "feature": feat,
                "estimated_score_uplift": uplift,
                "current_score": base_score,
                "potential_score": new_score,
                "note": (
                    "Estimate based on reaching a typical strong value for "
                    "this data source (75th percentile of comparable users). "
                    "Actual impact will vary."
                ),
            })

    suggestions.sort(key=lambda s: s["estimated_score_uplift"], reverse=True)
    return suggestions


if __name__ == "__main__":
    model, features = load_model()
    df = pd.read_csv(DATA_PATH)

    # Pick a thin-file-looking sample user: no rent data
    sample = df[df["has_rent_data"] == 0].iloc[0][features].to_dict()

    suggestions = suggest_data_gaps(model, features, sample, df)

    print("Data-gap suggestions for sample thin-file user:\n")
    if not suggestions:
        print("No significant gaps detected for this user.")
    for s in suggestions:
        print(f"  {s['data_source']}: +{s['estimated_score_uplift']} points "
              f"({s['current_score']} -> {s['potential_score']})")
        print(f"    {s['note']}\n")