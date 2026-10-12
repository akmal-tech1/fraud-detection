"""Dataset preparation and preprocessing (Phase 5).

The schema below is derived from INSPECTING the generated dataset
(ml/generate_synthetic_data.py), not assumed. Preprocessing objects
are fitted on the TRAINING split only - never on the full dataset.

Feature schema (10 numeric + 1 categorical):
- Numeric: amount, transaction_hour, day_of_week, merchant_risk_score,
  distance_from_home, is_foreign, is_card_present,
  previous_transactions_today, account_age_days, failed_attempts_24h
- Categorical: category (one-hot encoded)

Excluded from features:
- transaction_id: identifier, no predictive meaning
- timestamp: metadata (kept for dashboard time analysis); its signal
  is already captured by transaction_hour and day_of_week
- is_fraud: the target
"""

from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATASET_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "synthetic_transactions.csv"
)

TARGET_COLUMN = "is_fraud"
IDENTIFIER_COLUMNS = ["transaction_id"]
METADATA_COLUMNS = ["timestamp"]

CATEGORICAL_FEATURES = ["category"]
NUMERIC_FEATURES = [
    "amount",
    "transaction_hour",
    "day_of_week",
    "merchant_risk_score",
    "distance_from_home",
    "is_foreign",
    "is_card_present",
    "previous_transactions_today",
    "account_age_days",
    "failed_attempts_24h",
]


def load_dataset(path=DATASET_PATH) -> pd.DataFrame:
    """Load the dataset and verify the expected schema is present."""
    df = pd.read_csv(path)
    required = set(
        IDENTIFIER_COLUMNS
        + METADATA_COLUMNS
        + CATEGORICAL_FEATURES
        + NUMERIC_FEATURES
        + [TARGET_COLUMN]
    )
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Dataset is missing required columns: {sorted(missing)}"
        )
    return df


def separate_features_and_target(df):
    """Return (X, y): feature DataFrame and target Series.

    Identifiers, metadata, and the target column are excluded from X.
    """
    feature_columns = CATEGORICAL_FEATURES + NUMERIC_FEATURES
    X = df[feature_columns].copy()
    y = df[TARGET_COLUMN].copy()
    if y.nunique() < 2:
        raise ValueError(
            "Target column must contain both classes (0 and 1)."
        )
    return X, y


def get_train_test_split(X, y, test_size=0.2, seed=42):
    """Stratified split: the fraud/legitimate ratio is preserved
    in both the training and testing sets."""
    return train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )


def build_preprocessor():
    """Return an UNFITTED ColumnTransformer.

    Numeric features are standardized; the categorical feature is
    one-hot encoded (unknown categories at prediction time are
    ignored, not errors). Fit it on the TRAINING split only.
    """
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ],
        verbose_feature_names_out=False,
    )
