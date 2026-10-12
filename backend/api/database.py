"""Database engine, session factory, and initialization (Phase 4).

SQLite for development. The connection string is configurable via the
DATABASE_URL environment variable (see backend/.env.example), e.g.:
    DATABASE_URL=sqlite:///./fraud_detection.db
"""

import os
import json
import re
from datetime import datetime, timezone

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from api.models import Base, Prediction, Transaction

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fraud_detection.db")

# SQLite needs check_same_thread=False because FastAPI may handle
# requests from multiple threads.
_engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    _engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_args)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


def migrate_legacy_schema(bind=engine) -> None:
    """Upgrade legacy SQLite tables while preserving their stored rows."""
    if bind.dialect.name != "sqlite":
        return

    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "users" in tables:
        user_columns = {
            column["name"] for column in inspector.get_columns("users")
        }
        with bind.begin() as connection:
            if "username" not in user_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN username VARCHAR(50)"
                )
            users = connection.execute(
                text("SELECT id, email, username FROM users ORDER BY id")
            ).mappings().all()
            used_usernames = set()
            for user in users:
                existing = (user["username"] or "").strip().lower()
                if not re.fullmatch(r"[a-z0-9_.-]{3,50}", existing):
                    local_part = user["email"].split("@", 1)[0].lower()
                    existing = re.sub(r"[^a-z0-9_.-]", "-", local_part)[:50]
                    if len(existing) < 3:
                        existing = f"user{user['id']}"
                base = existing
                suffix = 2
                while existing in used_usernames:
                    ending = f"-{suffix}"
                    existing = f"{base[:50 - len(ending)]}{ending}"
                    suffix += 1
                used_usernames.add(existing)
                connection.execute(
                    text("UPDATE users SET username = :username WHERE id = :id"),
                    {"username": existing, "id": user["id"]},
                )
            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username "
                "ON users (username)"
            )

    if not {"transactions", "predictions"} <= tables:
        return

    transaction_columns = {
        column["name"] for column in inspector.get_columns("transactions")
    }
    prediction_columns = {
        column["name"] for column in inspector.get_columns("predictions")
    }
    if (
        "transaction_reference" in transaction_columns
        and "fraud_probability" in prediction_columns
    ):
        return
    if not {"transaction_id", "timestamp", "features"} <= transaction_columns:
        raise RuntimeError("Unrecognized transactions schema; database was not changed.")
    if not {"transaction_id", "probability"} <= prediction_columns:
        raise RuntimeError("Unrecognized predictions schema; database was not changed.")

    with bind.begin() as connection:
        old_transactions = connection.execute(
            text("SELECT * FROM transactions")
        ).mappings().all()
        old_predictions = connection.execute(
            text("SELECT * FROM predictions")
        ).mappings().all()

        connection.exec_driver_sql(
            "ALTER TABLE predictions RENAME TO predictions_legacy"
        )
        connection.exec_driver_sql(
            "ALTER TABLE transactions RENAME TO transactions_legacy"
        )
        Transaction.__table__.create(connection)
        Prediction.__table__.create(connection)

        transaction_ids = {}
        migrated_transactions = []
        for row in old_transactions:
            reference = row["transaction_id"]
            if reference in transaction_ids:
                raise RuntimeError(
                    "Duplicate legacy transaction references prevent a safe migration."
                )
            timestamp_value = row["timestamp"]
            if isinstance(timestamp_value, str):
                try:
                    timestamp_value = datetime.fromisoformat(
                        timestamp_value.replace("Z", "+00:00")
                    )
                except ValueError:
                    timestamp_value = None
            if timestamp_value is None:
                timestamp_value = datetime.now(timezone.utc)

            features = row["features"]
            if isinstance(features, str):
                try:
                    features = json.loads(features)
                except json.JSONDecodeError:
                    features = {"legacy_features": features}
            if not isinstance(features, dict):
                features = {"legacy_features": features}
            features.setdefault("amount", row["amount"])
            features.setdefault("category", row["category"])
            if row["type"] is not None:
                features.setdefault("legacy_type", row["type"])

            transaction_ids[reference] = row["id"]
            migrated_transactions.append(
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "transaction_reference": reference,
                    "transaction_timestamp": timestamp_value,
                    "features": features,
                    "created_at": timestamp_value,
                }
            )

        if migrated_transactions:
            connection.execute(
                Transaction.__table__.insert(), migrated_transactions
            )

        migrated_predictions = []
        for row in old_predictions:
            migrated_predictions.append(
                {
                    "id": row["id"],
                    "transaction_id": transaction_ids.get(row["transaction_id"]),
                    "model_version": row["model_version"],
                    "fraud_probability": row["probability"],
                    "risk_score": row["risk_score"],
                    "risk_category": row["risk_category"],
                    "predicted_class": row["predicted_class"],
                    "created_at": datetime.now(timezone.utc),
                }
            )
        if migrated_predictions:
            connection.execute(Prediction.__table__.insert(), migrated_predictions)

        connection.exec_driver_sql("DROP TABLE predictions_legacy")
        connection.exec_driver_sql("DROP TABLE transactions_legacy")


def init_db() -> None:
    """Create all tables. Safe to call repeatedly.

    Called automatically on app startup (FastAPI lifespan in main.py)
    and manually via:  python -m api.database
    """
    migrate_legacy_schema(engine)
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yields a session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized: {DATABASE_URL}")
