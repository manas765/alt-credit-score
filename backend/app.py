
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd 

import os
from auth import sign_up, sign_in, get_user_from_token
from functools import wraps


from explain import load_model, build_explainer, explain_prediction, FEATURE_LABELS
from gap_coach import suggest_data_gaps, proba_to_score
from proof_export import generate_proof, format_proof_as_text
from uncertainty import load_ensemble, score_with_uncertainty
from ai_assistant import ask_assistant
from supabase_client import supabase_admin

app = Flask(__name__)
CORS(app)

MODEL, FEATURES = load_model()
ENSEMBLE_MODELS, ENSEMBLE_FEATURES = load_ensemble()
EXPLAINER = build_explainer(MODEL)
BACKGROUND_DF = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "synthetic_alt_credit_data.csv"))

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

def require_auth(f):
    """
    Decorator for routes that need a logged-in user. Reads the
    Authorization header, verifies the token with Supabase, and
    passes the real user_id into the route as a keyword argument.
    A request with no token, or an invalid one, is rejected before
    the route's own code ever runs.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ", 1)[1]
        user = get_user_from_token(token)
        if user is None:
            return jsonify({"error": "Invalid or expired session"}), 401

        return f(*args, user_id=user.id, **kwargs)
    return wrapper


@app.route("/auth/signup", methods=["POST"])
def signup():
    payload = request.get_json(force=True)
    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        result = sign_up(email, password)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "message": "Signup successful. Please log in.",
        "user_id": result.user.id if result.user else None,
    })


@app.route("/auth/login", methods=["POST"])
def login():
    payload = request.get_json(force=True)
    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        result = sign_in(email, password)
    except Exception as e:
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({
        "access_token": result.session.access_token,
        "user_id": result.user.id,
        "email": result.user.email,
    })


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
@require_auth
def score(user_id):
    payload = request.get_json(force=True)
    input_row, error = validate_and_parse(payload)
    if error:
        return jsonify({"error": error}), 400

    x_df = pd.DataFrame([[input_row[f] for f in FEATURES]], columns=FEATURES)
    proba = MODEL.predict_proba(x_df)[0, 1]
    alt_score = int(round(SCORE_MIN + proba * (SCORE_MAX - SCORE_MIN)))

    contributions = explain_prediction(EXPLAINER, FEATURES, input_row)

    insert_result = supabase_admin.table("scores").insert({
        "user_id": user_id,
        "input_data": input_row,
    }).execute()
    score_id = insert_result.data[0]["id"]

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
@require_auth
def gaps(user_id):
    payload = request.get_json(force=True)
    input_row, error = validate_and_parse(payload)
    if error:
        return jsonify({"error": error}), 400

    suggestions = suggest_data_gaps(MODEL, FEATURES, input_row, BACKGROUND_DF)
    return jsonify({"suggestions": suggestions})


@app.route("/proof", methods=["POST"])
@require_auth
def proof(user_id):
    payload = request.get_json(force=True)
    input_row, error = validate_and_parse(payload)
    if error:
        return jsonify({"error": error}), 400

    user_label = payload.get("user_label", "Applicant")
    proof_doc = generate_proof(MODEL, FEATURES, EXPLAINER, input_row, BACKGROUND_DF, user_label)
    proof_doc["formatted_text"] = format_proof_as_text(proof_doc)

    return jsonify(proof_doc)

@app.route("/chat", methods=["POST"])
@require_auth
def chat(user_id):
    payload = request.get_json(force=True)
    score_id = payload.get("score_id")
    question = payload.get("question")

    if not score_id or not question:
        return jsonify({"error": "Both 'score_id' and 'question' are required"}), 400

    result = supabase_admin.table("scores").select("*").eq("id", score_id).eq("user_id", user_id).execute()
    if not result.data:
        return jsonify({"error": "Unknown score_id, or it doesn't belong to you."}), 404

    input_row = result.data[0]["input_data"]

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