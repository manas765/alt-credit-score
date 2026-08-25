# Alt-Credit Ledger — Alternative Credit Scoring for Thin-File Users

A creditworthiness assessment tool for people without a formal credit
history — built from alternative data (utility payments, wallet activity,
subscription consistency, employment stability) instead of a traditional
bureau file.

## The problem

An estimated 160M+ people in India have little to no formal credit
history — gig workers, homemakers, students, and daily-wage earners who
are financially active but invisible to bureaus like CIBIL. Being
"credit invisible" isn't the same as being uncreditworthy, but without a
score, these individuals are locked out of formal lending and have no way
to prove their reliability to a lender or landlord.

Most public tools in this space (CIBIL's own simulator, Paisabazaar,
CreditMantri, etc.) simulate changes to an *existing* score. None of them
address people who have no score to begin with, and none give users a way
to *prove* an alternative assessment to a third party who doesn't have
bureau access.

## What this project does

1. **Scores creditworthiness from alternative data** using a gradient-boosted
   model (XGBoost) trained on utility, subscription, wallet, employment,
   and rent-payment signals.
2. **Explains every score** using SHAP (TreeExplainer), showing exactly
   which factors pushed the score up or down — not a black box.
3. **Data-Gap Coach** — the core differentiator. For each data source a
   user hasn't provided (e.g. no linked rent history), the model estimates
   the potential score uplift from adding it, so the tool tells users
   what to do next, not just where they stand.
4. **Proof-of-Creditworthiness export** — the second differentiator. Users
   can generate a clean, shareable document (with print/PDF support)
   summarizing their score, strengths, weaknesses, and improvement paths
   — something they could realistically hand to a local lender or
   landlord who lacks bureau access.

## Why this is different from "another CIBIL score project"

Most portfolio projects in this space simulate an existing score. This
project instead targets the credit-invisible population directly, and
goes beyond scoring to (a) explain *why*, (b) coach *what to add next*,
and (c) produce something *shareable* — turning a passive number into an
actionable, evidence-generating tool.

## Methodology & honest disclosures

**Data is synthetic.** There is no public dataset of real Indian alt-data
(utility payments, wallet transactions, rent history) linked to real
credit outcomes — this data is proprietary to bureaus, telcos, and banks.
`data/generate_data.py` generates a synthetic dataset with directionally
realistic, documented assumptions (see the docstring in that file for the
rationale behind each feature). This is disclosed openly rather than
implying the data is real, and the app's UI carries the same disclaimer
on every score/proof output.

**Model choice.** XGBoost was chosen for native tree-based
explainability support (SHAP TreeExplainer) and because it's standard for
tabular classification tasks like this. A logistic regression baseline
was also trained for comparison — see [Model performance](#model-performance)
below for the honest result.

**Explainability.** SHAP values are computed per-prediction via
`TreeExplainer`, showing each feature's contribution to a given score
rather than only reporting global feature importance.

## Model performance

| Model | ROC-AUC |
|---|---|
| XGBoost (primary) | ~0.70 |
| Logistic Regression (baseline) | ~0.71 |

The baseline logistic regression performs comparably to XGBoost on this
feature set. This is an honest, reported finding, not a bug — linear
models are often competitive on tabular data with a modest number of
features. XGBoost was retained for its native explainability support
(SHAP), which matters more for this use case than a marginal accuracy
difference. Full metrics are in `backend/metrics.json`.

## Bias / fairness audit

`backend/bias_audit.py` checks model accuracy and AUC across
`education_level` and `employment_stability_months` bands (the two
features in the dataset most likely to act as proxies for socioeconomic
background).

**Findings:** Accuracy varied by ~2.5 points and AUC by ~4.4 points
across education bands — a relatively tight spread. Across employment
stability bands, the 12–24 month band showed a modest dip in both
accuracy and AUC relative to other bands, worth further investigation
with real (non-synthetic) data before any real deployment.

This is a first-pass diagnostic appropriate for a portfolio project, not
a formal fairness certification. A production system would need a more
rigorous framework (e.g. demographic parity, equalized odds) and
domain/legal review.

## Architecture



## Running it locally

**Backend:**
```bash
python -m venv venv
venv\Scripts\Activate.ps1   # or source venv/bin/activate on Mac/Linux
pip install -r requirements.txt
python data/generate_data.py
python backend/train_model.py
python backend/app.py
```

**Frontend** (separate terminal):
```bash
cd frontend
npm install
npm run dev
```

**Tests:**
```bash
pytest backend/tests/ -v
```

## Limitations & future work

- **No persistence** — every score is stateless; no accounts or history
  over time. A "verified 6-month track record" is a stronger proof
  document than a one-off snapshot.
- **No deployment yet** — currently runs locally only.
- **Single train/test split** — no cross-validation or confidence
  intervals on the reported AUC.
- **Synthetic data only** — a real version would need a partnership with
  an alt-data provider or a proxy real-world dataset (e.g. Kaggle's
  Home Credit Default Risk).
- **Fairness audit is a first pass** — see caveats above.

## Disclaimer

This is a demonstration project built on synthetic data. It is not a
real credit bureau, is not regulated, and scores generated by this tool
should not be treated as equivalent to a formal credit report.



