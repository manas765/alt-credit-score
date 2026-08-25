"""
Alt-Credit Scoring API
=======================
Endpoints:
  GET  /health   - health check
  GET  /features - list of expected input fields (for building a form)
  POST /score    - returns score + band + SHAP explanation
  POST /gaps     - returns data-gap coaching suggestions
  POST /proof    - returns full proof-of-creditworthiness document
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

from explain import load_model, build_explainer, explain_prediction, FEATURE_LABELS
from gap_coach import suggest_data_gaps, proba_to_score
from proof_export import generate_proof, format_proof_as_text

app = Flask(__name__)
CORS(app)

MODEL, FEATURES = load_model()
EXPLAINER = build_explainer(MODEL)
BACKGROUND_DF = pd.read_csv("data/synthetic_alt_credit_data.csv")

SCORE_MIN, SCORE_MAX = 300, 900


def band_for_score(score: int) -> str:
    if score >= 750:
        return "Excellent"
    if score >= 700:
        return "Good"
    if score >= 650:
        return "Fair"
    if score >= 550:
        return "Poor"
    return "Very Poor"


FIELD_RANGES = {
    "utility_payment_punctuality_score": (0, 100),
    "wallet_txn_regularity": (0, 1),
    "wallet_avg_monthly_txn_count": (0, 500),
    "subscription_payment_consistency": (0, 100),
    "employment_stability_months": (0, 600),
    "education_level": (0, 3),
    "avg_monthly_income_proxy": (0, 5_000_000),
    "rent_payment_punctuality": (0, 100),
    "has_rent_data": (0, 1),
    "months_of_data_available": (0, 600),
}


def validate_and_parse(payload):
    missing = [f for f in FEATURES if f not in payload]
    if missing:
        return None, f"Missing fields: {missing}"

    try:
        input_row = {f: float(payload[f]) for f in FEATURES}
    except (TypeError, ValueError) as e:
        return None, f"Invalid input values: {e}"

    out_of_range = []
    for f, val in input_row.items():
        lo, hi = FIELD_RANGES[f]
        if val < lo or val > hi:
            out_of_range.append(f"{f} must be between {lo} and {hi} (got {val})")

    if out_of_range:
        return None, "Out-of-range values: " + "; ".join(out_of_range)

    return input_row, None


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/features", methods=["GET"])
def features():
    return jsonify({"features": FEATURES, "labels": FEATURE_LABELS})


@app.route("/score", methods=["POST"])
def score():
    payload = request.get_json(force=True)
    input_row, error = validate_and_parse(payload)
    if error:
        return jsonify({"error": error}), 400

    x_df = pd.DataFrame([[input_row[f] for f in FEATURES]], columns=FEATURES)
    proba = MODEL.predict_proba(x_df)[0, 1]
    alt_score = int(round(SCORE_MIN + proba * (SCORE_MAX - SCORE_MIN)))

    contributions = explain_prediction(EXPLAINER, FEATURES, input_row)

    return jsonify({
        "alt_credit_score": alt_score,
        "score_band": band_for_score(alt_score),
        "creditworthy_probability": round(float(proba), 4),
        "explanation": contributions,
        "disclaimer": (
            "This score is generated from a model trained on SYNTHETIC data "
            "for demonstration purposes and does not reflect a real "
            "creditworthiness assessment."
        ),
    })


@app.route("/gaps", methods=["POST"])
def gaps():
    payload = request.get_json(force=True)
    input_row, error = validate_and_parse(payload)
    if error:
        return jsonify({"error": error}), 400

    suggestions = suggest_data_gaps(MODEL, FEATURES, input_row, BACKGROUND_DF)
    return jsonify({"suggestions": suggestions})


@app.route("/proof", methods=["POST"])
def proof():
    payload = request.get_json(force=True)
    input_row, error = validate_and_parse(payload)
    if error:
        return jsonify({"error": error}), 400

    user_label = payload.get("user_label", "Applicant")
    proof_doc = generate_proof(MODEL, FEATURES, EXPLAINER, input_row, BACKGROUND_DF, user_label)
    proof_doc["formatted_text"] = format_proof_as_text(proof_doc)

    return jsonify(proof_doc)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)