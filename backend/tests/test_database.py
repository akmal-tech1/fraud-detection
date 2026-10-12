"""Phase 4 tests: ORM models and database persistence.

Each test uses its own temporary SQLite file so tests never touch the
real development database (backend/fraud_detection.db).
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from api.database import Base, migrate_legacy_schema
from api.models import AuditEvent, Prediction, Transaction, User


@pytest.fixture()
def db_session(tmp_path):
    """Session backed by a fresh temporary SQLite database."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _make_transaction(reference="TXN-DEMO-001"):
    return Transaction(
        transaction_reference=reference,
        transaction_timestamp=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        features={"amount": 250.0, "category": "electronics"},
    )


def test_transaction_and_prediction_persistence(db_session):
    prediction = Prediction(
        transaction=_make_transaction(),
        fraud_probability=0.87,
        risk_score=87,
        risk_category="CRITICAL",
        predicted_class="fraud",
        model_version="0.1.0",
    )
    db_session.add(prediction)
    db_session.commit()

    loaded = db_session.query(Prediction).filter_by(risk_category="CRITICAL").one()
    assert loaded.risk_score == 87
    assert loaded.fraud_probability == 0.87
    assert loaded.transaction.transaction_reference == "TXN-DEMO-001"
    assert loaded.transaction.features["amount"] == 250.0


def test_legacy_transaction_schema_migrates_without_losing_predictions(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE transactions ("
            "id INTEGER PRIMARY KEY, user_id INTEGER, amount FLOAT NOT NULL, "
            "type VARCHAR(50) NOT NULL, category VARCHAR(50) NOT NULL, "
            "features JSON NOT NULL, timestamp VARCHAR(50) NOT NULL, "
            "transaction_id VARCHAR(100) NOT NULL)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE predictions ("
            "id INTEGER PRIMARY KEY, transaction_id VARCHAR(100) NOT NULL, "
            "model_version VARCHAR(50) NOT NULL, probability FLOAT NOT NULL, "
            "risk_score INTEGER NOT NULL, risk_category VARCHAR(20) NOT NULL, "
            "predicted_class VARCHAR(20) NOT NULL)"
        )
        connection.exec_driver_sql(
            "INSERT INTO transactions VALUES "
            "(1, NULL, 250.0, 'card', 'electronics', "
            "'{\"amount\": 250, \"category\": \"electronics\"}', "
            "'2026-01-01T12:00:00+00:00', 'TXN-LEGACY-001')"
        )
        connection.exec_driver_sql(
            "INSERT INTO predictions VALUES "
            "(1, 'TXN-LEGACY-001', '0.1.0', 0.87, 87, 'CRITICAL', 'fraud')"
        )

    migrate_legacy_schema(engine)
    migrate_legacy_schema(engine)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        prediction = session.query(Prediction).one()
        assert prediction.transaction.transaction_reference == "TXN-LEGACY-001"
        assert prediction.fraud_probability == 0.87
        assert prediction.transaction.features["amount"] == 250
    finally:
        session.close()
        engine.dispose()


def test_legacy_users_receive_unique_usernames(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy_users.db'}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE users ("
            "id INTEGER PRIMARY KEY, email VARCHAR(255) NOT NULL, "
            "password_hash VARCHAR(255) NOT NULL, role VARCHAR(20) NOT NULL, "
            "created_at DATETIME NOT NULL)"
        )
        connection.exec_driver_sql(
            "INSERT INTO users VALUES "
            "(1, 'student@example.com', 'hash-1', 'user', '2026-01-01'), "
            "(2, 'student@example.org', 'hash-2', 'user', '2026-01-01')"
        )

    migrate_legacy_schema(engine)
    Base.metadata.create_all(bind=engine)
    with engine.connect() as connection:
        usernames = connection.exec_driver_sql(
            "SELECT username FROM users ORDER BY id"
        ).scalars().all()
    assert usernames == ["student", "student-2"]
    engine.dispose()


def test_user_and_audit_event_persistence(db_session):
    user = User(
        username="demo_user",
        email="demo@example.com",
        password_hash="hashed_value",
        role="user",
    )
    db_session.add(user)
    db_session.add(AuditEvent(user=user, event_type="login"))
    db_session.commit()

    loaded = db_session.query(AuditEvent).filter_by(event_type="login").one()
    assert loaded.user.email == "demo@example.com"


def test_duplicate_email_rejected(db_session):
    db_session.add(
        User(username="first_user", email="same@example.com", password_hash="a")
    )
    db_session.commit()
    db_session.add(
        User(username="second_user", email="same@example.com", password_hash="b")
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_risk_score_bounds_enforced(db_session):
    db_session.add(_make_transaction())
    db_session.commit()
    tx = db_session.query(Transaction).one()
    db_session.add(
        Prediction(
            transaction=tx,
            risk_score=101,
            risk_category="CRITICAL",
            predicted_class="fraud",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_invalid_risk_category_rejected(db_session):
    db_session.add(_make_transaction())
    db_session.commit()
    tx = db_session.query(Transaction).one()
    db_session.add(
        Prediction(
            transaction=tx,
            risk_score=50,
            risk_category="EXTREME",
            predicted_class="fraud",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
