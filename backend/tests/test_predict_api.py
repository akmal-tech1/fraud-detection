"""Phase 7 tests: single-transaction prediction API.

Covers the project spec's testing requirements:
- valid and invalid transaction requests
- missing model files (graceful failure)
- database persistence
- duplicate transaction references
- model status and metrics endpoints

Tests use a temporary SQLite database and the real trained
artifacts (overridden only where a test needs to simulate
missing artifacts).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from api.database import Base, get_db
from api.model_service import (
    DEFAULT_MODELS_DIR,
    ModelService,
    get_model_service,
)
from api.models import Prediction

VALID_PAYLOAD = {
    "amount": 250.0,
    "category": "electronics",
    "transaction_hour": 2,
    "day_of_week": 1,
    "merchant_risk_score": 80.0,
    "distance_from_home": 45.5,
    "is_foreign": True,
    "is_card_present": False,
    "previous_transactions_today": 3,
    "account_age_days": 30,
    "failed_attempts_24h": 2,
}


@pytest.fixture()
def client_and_session(tmp_path):
    """TestClient with an isolated database and the real model artifacts."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    session = TestSession()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, session
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()


def test_predict_valid_transaction(client_and_session):
    client, session = client_and_session
    response = client.post("/api/predict", json=VALID_PAYLOAD)
    assert response.status_code == 200

    data = response.json()
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_category"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert 0.0 <= data["fraud_probability"] <= 1.0
    assert data["predicted_class"] in ("fraud", "legitimate")
    assert data["model_version"]
    assert data["disclaimer"]

    # The crafted payload has strong fraud signals (night hour, high
    # merchant risk, far from home, foreign, card-not-present, new
    # account, recent failed attempts), so the trained ensemble
    # should flag it as fraud with a HIGH or CRITICAL score.
    assert data["predicted_class"] == "fraud"
    assert data["risk_score"] >= 60

    # The result must be persisted in the database.
    prediction = (
        session.query(Prediction).order_by(Prediction.id.desc()).first()
    )
    assert prediction is not None
    assert prediction.risk_score == data["risk_score"]
    assert prediction.risk_category == data["risk_category"]
    assert prediction.predicted_class == data["predicted_class"]
    assert (
        prediction.transaction.transaction_reference
        == data["transaction_reference"]
    )

    history = client.get("/api/transactions", params={"skip": 0, "limit": 1})
    assert history.status_code == 200
    history_data = history.json()
    assert history_data["total"] == 1
    assert len(history_data["items"]) == 1
    history_item = history_data["items"][0]
    assert history_item["transaction_reference"] == data["transaction_reference"]
    assert history_item["prediction"]["risk_score"] == data["risk_score"]

    details = client.get(f"/api/transactions/{history_item['id']}")
    assert details.status_code == 200
    assert details.json()["features"]["amount"] == VALID_PAYLOAD["amount"]
    assert details.json()["prediction"]["risk_category"] == data["risk_category"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"amount": 0},
        {"amount": -10},
        {"category": "spaceships"},
        {"transaction_hour": 24},
        {"transaction_hour": -1},
        {"day_of_week": 7},
        {"merchant_risk_score": 101},
        {"distance_from_home": -0.5},
        {"account_age_days": -1},
        {"previous_transactions_today": -2},
    ],
)
def test_predict_invalid_transaction_rejected(client_and_session, overrides):
    client, _ = client_and_session
    payload = {**VALID_PAYLOAD, **overrides}
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 422


def test_predict_missing_field_rejected(client_and_session):
    client, _ = client_and_session
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "amount"}
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 422


def test_predict_without_model_artifacts_fails_gracefully(
    client_and_session, tmp_path
):
    client, _ = client_and_session
    # Simulate missing artifacts with an empty models directory.
    app.dependency_overrides[get_model_service] = lambda: ModelService(
        str(tmp_path)
    )
    try:
        response = client.post("/api/predict", json=VALID_PAYLOAD)
        assert response.status_code == 503
        assert "model" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_model_service, None)


def test_duplicate_transaction_reference_conflict(client_and_session):
    client, _ = client_and_session
    payload = {**VALID_PAYLOAD, "transaction_reference": "TXN-UNIQUE-001"}
    first = client.post("/api/predict", json=payload)
    assert first.status_code == 200
    second = client.post("/api/predict", json=payload)
    assert second.status_code == 409


def test_model_status_reports_availability(client_and_session):
    client, _ = client_and_session
    response = client.get("/api/model/status")
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is True
    assert data["artifacts"]["xgboost"] is True
    assert data["ensemble_weights"] == {"xgboost": 0.65, "random_forest": 0.35}


def test_model_status_without_artifacts(client_and_session, tmp_path):
    client, _ = client_and_session
    app.dependency_overrides[get_model_service] = lambda: ModelService(
        str(tmp_path)
    )
    try:
        response = client.get("/api/model/status")
        assert response.status_code == 200
        assert response.json()["available"] is False
    finally:
        app.dependency_overrides.pop(get_model_service, None)


def test_model_metrics_endpoint(client_and_session):
    client, _ = client_and_session
    response = client.get("/api/model/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["model_version"]
    assert data["dataset"]["synthetic"] is True
    assert "ensemble" in data["models"]
    assert "confusion_matrix" in data["models"]["ensemble"]
