"""Pydantic schemas for request and response validation (Phase 7).

The transaction input fields mirror the dataset schema inspected
in Phase 5 (ml/preprocess.py) - the API accepts exactly the
features the models were trained on, nothing more.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from ml.generate_synthetic_data import CATEGORIES

# The category field only accepts the real categories from the
# dataset schema (Literal[*CATEGORIES] unpacks the list).
CategoryLiteral = Literal[*CATEGORIES]

DISCLAIMER = (
    "This is an estimated model risk score produced by a "
    "demonstration model trained on SYNTHETIC data. It is not "
    "a determination that the transaction is fraudulent, and it "
    "must not be used to block or judge real transactions."
)


class TransactionInput(BaseModel):
    """One transaction to analyze. Fields match the model feature schema."""

    transaction_reference: str | None = Field(
        default=None,
        max_length=64,
        description="Optional reference. Generated if not provided.",
    )
    transaction_timestamp: datetime | None = Field(
        default=None,
        description="Optional transaction time. Defaults to now (UTC).",
    )
    amount: float = Field(gt=0, le=1_000_000, description="Transaction amount.")
    category: CategoryLiteral = Field(description="Merchant category.")
    transaction_hour: int = Field(ge=0, le=23, description="Hour of day, 0-23.")
    day_of_week: int = Field(ge=0, le=6, description="0=Monday .. 6=Sunday.")
    merchant_risk_score: float = Field(ge=0, le=100)
    distance_from_home: float = Field(ge=0, description="Distance in km.")
    is_foreign: bool = Field(description="1 = different country.")
    is_card_present: bool = Field(description="1 = chip/swipe, 0 = online/keyed.")
    previous_transactions_today: int = Field(ge=0)
    account_age_days: int = Field(ge=0)
    failed_attempts_24h: int = Field(ge=0)

    def features_dict(self) -> dict:
        """Only the 11 model features (identifiers excluded)."""
        return self.model_dump(exclude={"transaction_reference", "transaction_timestamp"})


class PredictionResponse(BaseModel):
    """Result of a single-transaction analysis."""

    transaction_reference: str
    transaction_timestamp: datetime | None
    fraud_probability: float = Field(ge=0, le=1)
    risk_score: int = Field(ge=0, le=100)
    risk_category: str
    predicted_class: str
    model_version: str
    features: dict
    disclaimer: str


class ModelStatusResponse(BaseModel):
    """Whether the trained model artifacts are available."""

    available: bool
    model_version: str
    training_date: str | None
    models_dir: str
    artifacts: dict
    ensemble_weights: dict


class DatasetPreview(BaseModel):
    """Preview of an uploaded CSV dataset (no predictions)."""

    filename: str
    size_bytes: int
    row_count: int
    column_count: int
    columns: list[str]
    sample_rows: list[dict]
    valid_rows: int
    invalid_rows: int


class InvalidRow(BaseModel):
    """One CSV row that failed validation."""

    row_number: int
    errors: list[str]


class BatchResultItem(BaseModel):
    """One analyzed transaction in a batch result."""

    transaction_reference: str
    fraud_probability: float = Field(ge=0, le=1)
    risk_score: int = Field(ge=0, le=100)
    risk_category: str
    predicted_class: str


class BatchPredictionResponse(BaseModel):
    """Summary and per-row results of a batch analysis.

    Partially invalid files: valid rows are analyzed and
    reported in `predictions`; invalid rows are listed in
    `invalid` with their CSV line number and reasons.
    """

    total_rows: int
    valid_rows: int
    invalid_rows: int
    invalid: list[InvalidRow]
    category_counts: dict
    predictions: list[BatchResultItem]
    references_regenerated: int
    disclaimer: str


class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_.-]+$",
        description="Username; letters, numbers, dots, underscores, and hyphens.",
    )
    email: str = Field(
        min_length=6,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        description="User email address",
    )
    password: str = Field(min_length=8, description="User password")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: str = Field(min_length=1, max_length=254, description="User email address")
    password: str = Field(description="User password")


class UserResponse(BaseModel):
    """Schema for user response (excluding password)."""
    id: int
    username: str
    email: str
    role: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload."""
    sub: str  # user email
    exp: datetime
    iat: datetime
    role: str | None = None
