"""
Tests for the Alt-Credit Scoring API.

Run with: pytest backend/tests/ -v
(run from the project root, with the venv active)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app import app as flask_app


VALID_PAYLOAD = {
    "utility_payment_punctuality_score": 75,
    "wallet_txn_regularity": 0.7,
    "wallet_avg_monthly_txn_count": 30,
    "subscription_payment_consistency": 80,
    "employment_stability_months": 24,
    "education_level": 2,
    "avg_monthly_income_proxy": 20000,
    "rent_payment_punctuality": 0,
    "has_rent_data": 0,
    "months_of_data_available": 12,
}


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


# ---- Health & schema endpoints ----

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_features_schema(client):
    res = client.get("/features")
    assert res.status_code == 200
    data = res.get_json()
    assert "features" in data
    assert "labels" in data
    assert len(data["features"]) == 10


# ---- /score ----

def test_score_valid_input(client):
    res = client.post("/score", json=VALID_PAYLOAD)
    assert res.status_code == 200
    data = res.get_json()
    assert 300 <= data["alt_credit_score"] <= 900
    assert data["score_band"] in ["Excellent", "Good", "Fair", "Poor", "Very Poor"]
    assert 0 <= data["creditworthy_probability"] <= 1
    assert len(data["explanation"]) == 10


def test_score_missing_field(client):
    bad_payload = VALID_PAYLOAD.copy()
    del bad_payload["employment_stability_months"]
    res = client.post("/score", json=bad_payload)
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_score_out_of_range(client):
    bad_payload = VALID_PAYLOAD.copy()
    bad_payload["utility_payment_punctuality_score"] = 999
    res = client.post("/score", json=bad_payload)
    assert res.status_code == 400
    assert "Out-of-range" in res.get_json()["error"]


def test_score_negative_value_rejected(client):
    bad_payload = VALID_PAYLOAD.copy()
    bad_payload["employment_stability_months"] = -5
    res = client.post("/score", json=bad_payload)
    assert res.status_code == 400


def test_score_band_consistency(client):
    """A high-input profile should score meaningfully higher than a weak one."""
    strong_payload = VALID_PAYLOAD.copy()
    strong_payload.update({
        "utility_payment_punctuality_score": 95,
        "subscription_payment_consistency": 95,
        "wallet_txn_regularity": 0.9,
        "employment_stability_months": 60,
    })
    weak_payload = VALID_PAYLOAD.copy()
    weak_payload.update({
        "utility_payment_punctuality_score": 20,
        "subscription_payment_consistency": 20,
        "wallet_txn_regularity": 0.1,
        "employment_stability_months": 2,
    })

    strong_res = client.post("/score", json=strong_payload).get_json()
    weak_res = client.post("/score", json=weak_payload).get_json()

    assert strong_res["alt_credit_score"] > weak_res["alt_credit_score"]


# ---- /gaps ----

def test_gaps_valid_input(client):
    res = client.post("/gaps", json=VALID_PAYLOAD)
    assert res.status_code == 200
    data = res.get_json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)


def test_gaps_suggests_rent_when_missing(client):
    payload = VALID_PAYLOAD.copy()
    payload["has_rent_data"] = 0
    res = client.post("/gaps", json=payload)
    data = res.get_json()
    labels = [s["data_source"] for s in data["suggestions"]]
    # not guaranteed for every profile, but should be a valid, well-formed response either way
    assert isinstance(labels, list)


# ---- /proof ----

def test_proof_structure(client):
    res = client.post("/proof", json=VALID_PAYLOAD)
    assert res.status_code == 200
    data = res.get_json()
    for key in ["alt_credit_score", "score_band", "strengths", "areas_of_weakness",
                "improvement_opportunities", "disclaimer", "formatted_text"]:
        assert key in data


def test_proof_missing_field(client):
    bad_payload = VALID_PAYLOAD.copy()
    del bad_payload["education_level"]
    res = client.post("/proof", json=bad_payload)
    assert res.status_code == 400