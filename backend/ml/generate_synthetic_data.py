"""Generate a SYNTHETIC transaction dataset for development (Phase 5).

IMPORTANT - DEMONSTRATION DATA ONLY:
- This dataset is fake. It contains NO real customer records, no PII,
  no card or account numbers.
- Model performance on this data is NOT evidence of real-world fraud
  detection effectiveness.
- Deterministic: the same seed always produces the same dataset.

Usage (from the backend/ folder):
    python -m ml.generate_synthetic_data

Output: data/synthetic_transactions.csv

Schema (every feature below is known at prediction time, so there is
no data leakage; transaction_id and timestamp are identifier/metadata
columns and are excluded from model features in ml/preprocess.py):
- transaction_id: unique reference (identifier)
- timestamp: transaction date-time (metadata)
- amount: transaction amount
- category: merchant category (categorical)
- transaction_hour: hour of day, 0-23
- day_of_week: 0=Monday .. 6=Sunday
- merchant_risk_score: 0-100
- distance_from_home: km between merchant and home location
- is_foreign: 1 = different country
- is_card_present: 1 = chip/swipe, 0 = online or keyed entry
- previous_transactions_today: count
- account_age_days: account age in days
- failed_attempts_24h: failed transactions in the last 24 hours
- is_fraud: target label (1 = fraud, 0 = legitimate)
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_ROWS = 6000
FRAUD_RATE = 0.04
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "synthetic_transactions.csv"
)

CATEGORIES = [
    "groceries",
    "electronics",
    "dining",
    "travel",
    "entertainment",
    "healthcare",
    "utilities",
    "other",
]
CATEGORY_WEIGHTS = [0.24, 0.10, 0.18, 0.08, 0.12, 0.08, 0.12, 0.08]

# Base date for generated timestamps (today, so the data looks recent).
BASE_DATE = pd.Timestamp("2026-10-09")


def _legitimate_rows(rng, n):
    """Legitimate transactions: typical amounts, daytime, mostly domestic."""
    return pd.DataFrame(
        {
            "amount": np.clip(
                np.exp(rng.normal(np.log(60), 0.8, n)), 1, 2000
            ).round(2),
            "category": rng.choice(CATEGORIES, n, p=CATEGORY_WEIGHTS),
            "transaction_hour": np.clip(
                rng.normal(14, 4.5, n), 0, 23
            ).astype(int),
            "day_of_week": rng.integers(0, 7, n),
            "merchant_risk_score": np.clip(
                rng.normal(25, 12, n), 0, 100
            ).round(1),
            "distance_from_home": np.exp(rng.normal(1.5, 0.7, n)).round(2),
            "is_foreign": (rng.random(n) < 0.05).astype(int),
            "is_card_present": (rng.random(n) < 0.75).astype(int),
            "previous_transactions_today": rng.poisson(2, n),
            "account_age_days": rng.integers(30, 3000, n),
            "failed_attempts_24h": rng.poisson(0.1, n),
        }
    )


def _fraud_rows(rng, n):
    """Fraudulent transactions: larger amounts, night hours, riskier patterns."""
    return pd.DataFrame(
        {
            "amount": np.clip(
                np.exp(rng.normal(np.log(220), 0.9, n)), 1, 5000
            ).round(2),
            "category": rng.choice(CATEGORIES, n, p=CATEGORY_WEIGHTS),
            "transaction_hour": np.clip(
                rng.normal(2, 2.5, n), 0, 23
            ).astype(int),
            "day_of_week": rng.integers(0, 7, n),
            "merchant_risk_score": np.clip(
                rng.normal(65, 18, n), 0, 100
            ).round(1),
            "distance_from_home": np.exp(rng.normal(3.2, 0.8, n)).round(2),
            "is_foreign": (rng.random(n) < 0.45).astype(int),
            "is_card_present": (rng.random(n) < 0.25).astype(int),
            "previous_transactions_today": rng.poisson(4, n),
            "account_age_days": rng.integers(1, 600, n),
            "failed_attempts_24h": rng.poisson(1.2, n),
        }
    )


def generate(n_rows=N_ROWS, fraud_rate=FRAUD_RATE, seed=SEED):
    """Generate the synthetic dataset as a DataFrame."""
    rng = np.random.default_rng(seed)
    n_fraud = int(round(n_rows * fraud_rate))
    n_legit = n_rows - n_fraud

    df = pd.concat(
        [_legitimate_rows(rng, n_legit), _fraud_rows(rng, n_fraud)],
        ignore_index=True,
    )
    df["is_fraud"] = [0] * n_legit + [1] * n_fraud

    # Timestamps: a random day in the last 180 days at the generated hour.
    days_ago = rng.integers(0, 180, n_rows)
    df["timestamp"] = [
        (BASE_DATE - pd.Timedelta(days=int(d))) + pd.Timedelta(hours=int(h))
        for d, h in zip(days_ago, df["transaction_hour"])
    ]

    df["transaction_id"] = [f"TXN-{i:06d}" for i in range(n_rows)]

    # Shuffle so fraud rows are not grouped at the end.
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    columns = [
        "transaction_id",
        "timestamp",
        "amount",
        "category",
        "transaction_hour",
        "day_of_week",
        "merchant_risk_score",
        "distance_from_home",
        "is_foreign",
        "is_card_present",
        "previous_transactions_today",
        "account_age_days",
        "failed_attempts_24h",
        "is_fraud",
    ]
    return df[columns]


def main():
    df = generate()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    n_fraud = int(df["is_fraud"].sum())
    print(f"Wrote {len(df)} rows to {OUTPUT_PATH}")
    print(f"Fraud cases: {n_fraud} ({n_fraud / len(df):.2%})")
    print("NOTE: this is SYNTHETIC demonstration data, not real transactions.")


if __name__ == "__main__":
    main()
