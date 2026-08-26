
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd 
import uuid
import os


from explain import load_model, build_explainer, explain_prediction, FEATURE_LABELS
from gap_coach import suggest_data_gaps, proba_to_score
from proof_export import generate_proof, format_proof_as_text
from uncertainty import load_ensemble, score_with_uncertainty
from ai_assistant import ask_assistant

app = Flask(__name__)
CORS(app)

MODEL, FEATURES = load_model()
ENSEMBLE_MODELS, ENSEMBLE_FEATURES = load_ensemble()
EXPLAINER = build_explainer(MODEL)
BACKGROUND_DF = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "synthetic_alt_credit_data.csv"))

SCORE_MIN, SCORE_MAX = 300, 900
SCORE_STORE = {}  # in-memory store: score_id -> validated input_row (swap for a real DB later)


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

@app.route("/score-range", methods=["POST"])
def score_range():
    payload = request.get_json(force=True)
    input_row, error = validate_and_parse(payload)
    if error:
        return jsonify({"error": error}), 400

    result = score_with_uncertainty(ENSEMBLE_MODELS, ENSEMBLE_FEATURES, input_row)

    return jsonify({
        **result,
        "disclaimer": (
            "This range reflects model uncertainty based on an ensemble of "
            "models and data availability, not a formal statistical "
            "guarantee. Generated from SYNTHETIC data for demonstration "
            "purposes."
        ),
    })
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

    score_id = str(uuid.uuid4())
    SCORE_STORE[score_id] = input_row

    return jsonify({
        "score_id": score_id,
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

@app.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json(force=True)

    score_id = payload.get("score_id")
    question = payload.get("question")

    if not score_id or not question:
        return jsonify({"error": "Both 'score_id' and 'question' are required"}), 400

    input_row = SCORE_STORE.get(score_id)
    if input_row is None:
        return jsonify({"error": "Unknown or expired score_id. Please generate a new score first."}), 404

    # Recompute everything fresh from the stored input — never trust
    # anything the client sends about the score itself.
    x_df = pd.DataFrame([[input_row[f] for f in FEATURES]], columns=FEATURES)
    proba = MODEL.predict_proba(x_df)[0, 1]
    alt_score = int(round(SCORE_MIN + proba * (SCORE_MAX - SCORE_MIN)))
    contributions = explain_prediction(EXPLAINER, FEATURES, input_row)
    gap_suggestions = suggest_data_gaps(MODEL, FEATURES, input_row, BACKGROUND_DF)
    range_result = score_with_uncertainty(ENSEMBLE_MODELS, ENSEMBLE_FEATURES, input_row)

    score_data = {
        "alt_credit_score": alt_score,
        "score_band": band_for_score(alt_score),
        "range": range_result,
        "explanation": contributions,
        "gaps": gap_suggestions,
    }

    try:
        answer = ask_assistant(score_data, question)
    except Exception as e:
        return jsonify({"error": f"Assistant is temporarily unavailable: {e}"}), 502

    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)