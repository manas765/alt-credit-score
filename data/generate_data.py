"""
Synthetic Alternative Credit Data Generator
=============================================
METHODOLOGY NOTE:
There is no public dataset of real Indian alt-data (utility bill payments,
mobile wallet transactions, education/employment stability, subscription
payment history) linked to actual credit outcomes. Real versions of this
data are proprietary (bureaus, telcos, banks, alt-data fintechs).

This script generates a SYNTHETIC dataset with directionally realistic
assumptions -- NOT calibrated against real Indian population statistics.
This is disclosed openly in the README rather than implying real data.
"""

import numpy as np
import pandas as pd

RNG_SEED = 42
N_SAMPLES = 8000

rng = np.random.default_rng(RNG_SEED)


def generate_dataset(n=N_SAMPLES):
    employment_stability_months = rng.gamma(shape=2.0, scale=8, size=n).clip(0, 120)
    education_level = rng.choice([0, 1, 2, 3], size=n, p=[0.15, 0.40, 0.35, 0.10])
    months_of_data_available = rng.integers(3, 24, size=n)

    latent_responsibility = rng.normal(0, 1, size=n)

    utility_payment_punctuality_score = np.clip(
        70 + 12 * latent_responsibility + rng.normal(0, 8, size=n), 0, 100
    )
    subscription_payment_consistency = np.clip(
        65 + 15 * latent_responsibility + rng.normal(0, 10, size=n), 0, 100
    )
    rent_payment_punctuality = np.clip(
        68 + 13 * latent_responsibility + rng.normal(0, 9, size=n), 0, 100
    )
    has_rent_data = rng.choice([0, 1], size=n, p=[0.35, 0.65])
    rent_payment_punctuality = np.where(has_rent_data == 1, rent_payment_punctuality, 0)

    wallet_avg_monthly_txn_count = np.clip(
        rng.poisson(lam=25, size=n) + 3 * latent_responsibility, 1, None
    )
    wallet_txn_regularity = np.clip(
        0.5 + 0.15 * latent_responsibility + rng.normal(0, 0.15, size=n), 0, 1
    )

    avg_monthly_income_proxy = np.clip(
        15000
        + 4000 * latent_responsibility
        + 150 * employment_stability_months
        + rng.normal(0, 6000, size=n),
        4000,
        None,
    )

    df = pd.DataFrame({
        "utility_payment_punctuality_score": utility_payment_punctuality_score,
        "wallet_txn_regularity": wallet_txn_regularity,
        "wallet_avg_monthly_txn_count": wallet_avg_monthly_txn_count,
        "subscription_payment_consistency": subscription_payment_consistency,
        "employment_stability_months": employment_stability_months,
        "education_level": education_level,
        "avg_monthly_income_proxy": avg_monthly_income_proxy,
        "rent_payment_punctuality": rent_payment_punctuality,
        "has_rent_data": has_rent_data,
        "months_of_data_available": months_of_data_available,
    })

    # Interaction: irregular wallet activity + low employment stability = extra risk
    instability_interaction = np.where(
        (wallet_txn_regularity < 0.45) & (employment_stability_months < 12), 1.0, 0.0
    )

    z = (
        0.045 * (utility_payment_punctuality_score - 50)
        + 0.040 * (subscription_payment_consistency - 50)
        + 0.028 * (rent_payment_punctuality - 50) * has_rent_data
        + 0.020 * (employment_stability_months - 20)
        + 0.400 * (wallet_txn_regularity - 0.5) * 10
        + 0.00005 * (avg_monthly_income_proxy - 20000)
        + 0.12 * education_level
        - 3.2 * instability_interaction
        + rng.normal(0, 1.1, size=n)
    )
    prob_creditworthy = 1 / (1 + np.exp(-z / 3))
    df["creditworthy"] = rng.binomial(1, prob_creditworthy)

    return df


if __name__ == "__main__":
    df = generate_dataset()
    df.to_csv("data/synthetic_alt_credit_data.csv", index=False)
    print(f"Generated {len(df)} rows -> data/synthetic_alt_credit_data.csv")
    print("\nClass balance:")
    print(df["creditworthy"].value_counts(normalize=True))
    print("\nFeature summary:")
    print(df.describe().T[["mean", "std", "min", "max"]])