"""
Proof-of-Creditworthiness Export
===================================
Generates a clean, shareable summary a thin-file user could hand to a
local lender, landlord, or NBFC that doesn't have bureau access --
turning "here's my score" into "here's evidence I'm reliable."

Deliberately plain-language and honest about what this is: a
demonstration-grade alternative assessment, not a bureau-recognized
credit report. That distinction matters and should never be blurred,
even in a portfolio project.
"""
import os
import json
from datetime import datetime

from explain import load_model, build_explainer, explain_prediction
from gap_coach import suggest_data_gaps, proba_to_score
import pandas as pd

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "synthetic_alt_credit_data.csv")


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


def generate_proof(model, features, explainer, input_row: dict, background_df: pd.DataFrame, user_label: str = "Applicant"):
    x_df = pd.DataFrame([[input_row[f] for f in features]], columns=features)
    proba = model.predict_proba(x_df)[0, 1]
    score = proba_to_score(proba)
    band = band_for_score(score)

    contributions = explain_prediction(explainer, features, input_row)
    top_positive = [c for c in contributions if c["contribution"] > 0][:3]
    top_negative = [c for c in contributions if c["contribution"] < 0][:3]

    gap_suggestions = suggest_data_gaps(model, features, input_row, background_df)

    proof = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "subject": user_label,
        "alt_credit_score": score,
        "score_band": band,
        "score_range": "300-900 (alternative-data scale, not a bureau score)",
        "strengths": [
            {"factor": c["label"], "detail": f"value: {c['value']:.2f}"} for c in top_positive
        ],
        "areas_of_weakness": [
            {"factor": c["label"], "detail": f"value: {c['value']:.2f}"} for c in top_negative
        ],
        "improvement_opportunities": [
            {
                "data_source": s["data_source"],
                "potential_uplift": f"+{s['estimated_score_uplift']} points",
            }
            for s in gap_suggestions
        ],
        "disclaimer": (
            "This is an ALTERNATIVE creditworthiness assessment generated from "
            "non-traditional data (utility, subscription, wallet, and rent "
            "payment patterns) using a demonstration model trained on synthetic "
            "data. It is NOT a CIBIL/bureau score, is not regulated, and should "
            "not be treated as equivalent to a formal credit report. It is "
            "intended to give thin-file individuals supporting evidence of "
            "reliability to share with lenders or landlords who lack access to "
            "formal bureau data."
        ),
    }

    return proof


def format_proof_as_text(proof: dict) -> str:
    lines = []
    lines.append("=" * 56)
    lines.append("  ALTERNATIVE CREDITWORTHINESS SUMMARY")
    lines.append("=" * 56)
    lines.append(f"  Generated: {proof['generated_at']}")
    lines.append(f"  Subject:   {proof['subject']}")
    lines.append("-" * 56)
    lines.append(f"  Score:  {proof['alt_credit_score']}  ({proof['score_band']})")
    lines.append(f"  Scale:  {proof['score_range']}")
    lines.append("-" * 56)

    lines.append("  Strengths:")
    for s in proof["strengths"]:
        lines.append(f"    + {s['factor']} ({s['detail']})")

    if proof["areas_of_weakness"]:
        lines.append("  Areas of weakness:")
        for w in proof["areas_of_weakness"]:
            lines.append(f"    - {w['factor']} ({w['detail']})")

    if proof["improvement_opportunities"]:
        lines.append("  Ways to improve:")
        for o in proof["improvement_opportunities"]:
            lines.append(f"    * Add {o['data_source']} -> {o['potential_uplift']}")

    lines.append("-" * 56)
    lines.append("  DISCLAIMER:")
    lines.append(f"  {proof['disclaimer']}")
    lines.append("=" * 56)

    return "\n".join(lines)


if __name__ == "__main__":
    model, features = load_model()
    explainer = build_explainer(model)
    df = pd.read_csv(DATA_PATH)

    sample = df[df["has_rent_data"] == 0].iloc[0][features].to_dict()

    proof = generate_proof(model, features, explainer, sample, df, user_label="Sample Applicant")
    print(format_proof_as_text(proof))

    SAMPLE_PROOF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_proof.json")
    with open(SAMPLE_PROOF_PATH, "w") as f:
        json.dump(proof, f, indent=2)
    print(f"\n\nSaved JSON version -> {SAMPLE_PROOF_PATH}")