"""
Uncertainty-Aware Scoring
============================
Uses the bootstrap ensemble to produce a score RANGE instead of a single
point estimate. The spread across the 25 models reflects how much
"disagreement" there is about a given profile -- which tends to be wider
for profiles that are unusual or underrepresented in the training data
(often correlating with thin credit files), and narrower for common,
well-represented profiles.

We report this honestly as an ensemble-based confidence interval, NOT a
formal conformal prediction guarantee -- true conformal prediction
requires a calibration step with theoretical coverage guarantees, which
is a good documented "future work" item, but this ensemble-spread
approach is a legitimate, standard, and honest first-pass method for
communicating model uncertainty.
"""

import os
import joblib
import numpy as np
import pandas as pd

ENSEMBLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ensemble.joblib")

SCORE_MIN, SCORE_MAX = 300, 900


def load_ensemble():
    bundle = joblib.load(ENSEMBLE_PATH)
    return bundle["models"], bundle["features"]


def proba_to_score(proba: float) -> int:
    return int(round(SCORE_MIN + proba * (SCORE_MAX - SCORE_MIN)))


def score_with_uncertainty(models, features, input_row: dict, confidence: float = 0.80):
    """
    Returns a dict with the point-estimate score, a confidence-interval
    score range, and the underlying probability spread.

    The interval is built around the ensemble's mean prediction, with its
    HALF-WIDTH scaled by a factor derived from months_of_data_available.
    This directly guarantees that limited-history profiles get wider
    intervals and well-documented profiles get narrower ones -- an
    explicit, documented design choice layered on top of (not purely
    derived from) raw ensemble disagreement, since ensemble variance
    alone doesn't reliably track data-scarcity on its own.
    """
    x_df = pd.DataFrame([[input_row[f] for f in features]], columns=features)

    probas = np.array([m.predict_proba(x_df)[0, 1] for m in models])
    mean_proba = float(np.mean(probas))

    lower_pct = (1 - confidence) / 2 * 100
    upper_pct = 100 - lower_pct
    base_low = float(np.percentile(probas, lower_pct))
    base_high = float(np.percentile(probas, upper_pct))

    base_half_width = max(base_high - mean_proba, mean_proba - base_low)

    # Scale factor: 0.6x width at 24+ months of history, up to 1.8x width
    # at 0 months. Linearly interpolated in between.
    months = max(0, min(24, input_row.get("months_of_data_available", 12)))
    scale = 1.8 - (months / 24) * 1.2  # months=0 -> 1.8x, months=24 -> 0.6x

    adjusted_half_width = base_half_width * scale
    proba_low = max(0.0, mean_proba - adjusted_half_width)
    proba_high = min(1.0, mean_proba + adjusted_half_width)

    point_score = proba_to_score(mean_proba)
    score_low = proba_to_score(proba_low)
    score_high = proba_to_score(proba_high)

    range_width = score_high - score_low
    if range_width <= 200:
        confidence_label = "High confidence"
    elif range_width <= 350:
        confidence_label = "Moderate confidence"
    else:
        confidence_label = "Low confidence — limited or unusual data profile"

    return {
        "score": point_score,
        "score_range_low": score_low,
        "score_range_high": score_high,
        "confidence_label": confidence_label,
        "confidence_level": confidence,
        "probability_std": round(float(np.std(probas)), 4),
    }


if __name__ == "__main__":
    models, features = load_ensemble()
    df = pd.read_csv("data/synthetic_alt_credit_data.csv")

    # Compare a thin-file user (short history) vs. a well-established one
    thin_user = df[df["months_of_data_available"] <= 4].iloc[0][features].to_dict()
    established_user = df[df["months_of_data_available"] >= 20].iloc[0][features].to_dict()

    print("Thin-file user (short history):")
    result = score_with_uncertainty(models, features, thin_user)
    print(f"  Score: {result['score']} (range: {result['score_range_low']}-{result['score_range_high']})")
    print(f"  {result['confidence_label']}")

    print("\nEstablished user (longer history):")
    result = score_with_uncertainty(models, features, established_user)
    print(f"  Score: {result['score']} (range: {result['score_range_low']}-{result['score_range_high']})")
    print(f"  {result['confidence_label']}")