"""SQLAlchemy ORM models (Phase 4).

Schema decisions (documented deviations from the project spec):
- Transaction.features is a JSON column. The real dataset schema is
  inspected in Phase 5, so individual feature columns are NOT invented
  here. Frequently used features may be promoted to real columns then.
- Transaction.user_id is an addition to the spec's model list: it enables
  per-user authorization in Phase 12. It is nullable so system/batch
  analyses without a signed-in user still work.
- Prediction.transaction_id is NOT unique: a transaction may be
  re-analyzed (e.g., with a newer model version), and each analysis is
  kept as its own Prediction row.
- All timestamps are stored as UTC-aware values.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    transaction_reference: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    transaction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    features: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="transaction"
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("transactions.id"), nullable=True
    )
    transaction: Mapped[Transaction | None] = relationship(
        back_populates="predictions"
    )
    model_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unknown"
    )
    fraud_probability: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    risk_score: Mapped[int] = mapped_column(nullable=False)
    risk_category: Mapped[str] = mapped_column(String(20), nullable=False)
    predicted_class: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "fraud_probability >= 0 AND fraud_probability <= 1",
            name="probability_range",
        ),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="risk_score_range"),
        CheckConstraint(
            "risk_category IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="valid_risk_category",
        ),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )
    user: Mapped[User] = relationship(back_populates="audit_events")