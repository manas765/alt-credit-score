"""
AI Assistant for Score Explanation
=====================================
Uses Groq's free-tier LLM API to answer user questions about their OWN
score, grounded in the real, already-computed SHAP explanation and gap
coaching data -- the model is never asked to invent numbers or make
credit decisions. It only translates data we've already computed into
plain language and answers follow-up questions about it.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a friendly, plain-language assistant embedded in \
an alternative credit scoring tool called "Alt-Credit Ledger," aimed at \
people (often young, first-time earners) with little or no formal credit \
history in India.

Your ONLY job is to help the user understand THEIR OWN score result, \
using the real data provided to you below. Rules you must follow:
- NEVER invent numbers, factors, or scores that are not in the provided data.
- NEVER give real financial/legal/lending advice beyond what the data shows.
- NEVER claim to be a substitute for a real financial advisor or bureau.
- Use simple, everyday words a complete beginner would understand — avoid \
jargon, and briefly explain any financial term you must use.
- Keep the whole answer under 200 words, and always finish your final \
sentence — never trail off.
- You may use a short Markdown table to lay out factors clearly when it \
helps (e.g. Factor | Effect), but keep any surrounding explanation in \
plain conversational sentences, not bullet points.
- If asked something outside this score's data, say you can only discuss \
this score result, not general financial advice.
"""


def build_context(score_data: dict) -> str:
    """Turns the score/explanation/gaps data into a compact text block
    the model can ground its answers in."""
    lines = [
        f"User's alt-credit score: {score_data.get('alt_credit_score')} "
        f"({score_data.get('score_band')})",
    ]

    if "range" in score_data and score_data["range"]:
        r = score_data["range"]
        lines.append(
            f"Likely range: {r.get('score_range_low')}-{r.get('score_range_high')} "
            f"({r.get('confidence_label')})"
        )

    lines.append("\nTop factors:")
    for factor in score_data.get("explanation", [])[:6]:
        direction = "helps" if factor["contribution"] > 0 else "hurts"
        lines.append(
            f"- {factor['label']} (value: {factor['value']}, {factor['trust_level']}) "
            f"{direction} the score"
        )

    if score_data.get("gaps"):
        lines.append("\nWays to improve:")
        for g in score_data["gaps"]:
            lines.append(f"- Add {g['data_source']}: potential +{g['estimated_score_uplift']} points")

    return "\n".join(lines)


def ask_assistant(score_data: dict, user_question: str) -> str:
    context = build_context(score_data)

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"Here is this user's score data:\n\n{context}"},
            {"role": "user", "content": user_question},
        ],
        temperature=0.4,
        max_tokens=800,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    # Quick manual test with fake sample data
    sample_score_data = {
        "alt_credit_score": 652,
        "score_band": "Fair",
        "range": {"score_range_low": 541, "score_range_high": 746, "confidence_label": "Moderate confidence"},
        "explanation": [
            {"label": "Wallet transaction regularity", "value": 0.5, "contribution": 0.12, "trust_level": "verifiable"},
            {"label": "Utility bill punctuality", "value": 70.0, "contribution": -0.03, "trust_level": "verifiable"},
        ],
        "gaps": [
            {"data_source": "Rent payment history", "estimated_score_uplift": 27},
        ],
    }

    answer = ask_assistant(sample_score_data, "Why is my score only 652? Is that bad?")
    print("Assistant response:\n")
    print(answer)