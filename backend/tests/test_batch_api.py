"""Phase 9 tests: CSV upload validation and batch prediction.

Covers the project spec's testing requirements:
- CSV validation (extension, columns, partial invalidity)
- Batch prediction (valid rows analyzed, invalid reported)
- Database persistence of batch results
- Missing model files (graceful failure)
- Sample dataset download
"""

import csv
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from api import batch_routes
from api.database import Base, get_db
from api.model_service import (
    ModelService,
    get_model_service,
)
from api.models import Prediction

CSV_FIELDS = [
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
]

VALID_ROW = {
    "amount": "100.0",
    "category": "groceries",
    "transaction_hour": "14",
    "day_of_week": "2",
    "merchant_risk_score": "20.0",
    "distance_from_home": "3.5",
    "is_foreign": "false",
    "is_card_present": "true",
    "previous_transactions_today": "1",
    "account_age_days": "800",
    "failed_attempts_24h": "0",
}

# amount must be > 0, so this row is invalid.
INVALID_ROW = {**VALID_ROW, "amount": "-5"}


def _csv_content(rows):
    """Build a CSV in memory from a list of dicts."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {field: row.get(field, "") for field in CSV_FIELDS}
        )
    return buffer.getvalue().encode("utf-8")


def _upload(filename, content):
    """Multipart file payload for TestClient."""
    return {"file": (filename, content, "text/csv")}


@pytest.fixture()
def client_and_session(tmp_path):
    """TestClient with an isolated database and the real
    trained model artifacts."""
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


def test_upload_valid_csv(client_and_session):
    client, _ = client_and_session
    content = _csv_content([VALID_ROW, VALID_ROW, VALID_ROW])
    response = client.post(
        "/api/dataset/upload", files=_upload("data.csv", content)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["row_count"] == 3
    assert data["valid_rows"] == 3
    assert data["invalid_rows"] == 0
    assert "amount" in data["columns"]
    assert len(data["sample_rows"]) == 3


def test_upload_rejects_non_csv_extension(client_and_session):
    client, _ = client_and_session
    content = _csv_content([VALID_ROW])
    response = client.post(
        "/api/dataset/upload", files=_upload("data.txt", content)
    )
    assert response.status_code == 400
    assert "CSV" in response.json()["detail"]


def test_upload_rejects_missing_columns(client_and_session):
    client, _ = client_and_session
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["amount"])
    writer.writeheader()
    writer.writerow({"amount": "10"})
    content = buffer.getvalue().encode("utf-8")
    response = client.post(
        "/api/dataset/upload", files=_upload("data.csv", content)
    )
    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]


def test_upload_reports_partially_invalid_rows(client_and_session):
    client, _ = client_and_session
    content = _csv_content([VALID_ROW, INVALID_ROW, VALID_ROW])
    response = client.post(
        "/api/dataset/upload", files=_upload("data.csv", content)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid_rows"] == 2
    assert data["invalid_rows"] == 1


def test_batch_predicts_valid_and_reports_invalid(client_and_session):
    client, session = client_and_session
    content = _csv_content([VALID_ROW, INVALID_ROW, VALID_ROW])
    response = client.post(
        "/api/predict/batch", files=_upload("data.csv", content)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 3
    assert data["valid_rows"] == 2
    assert data["invalid_rows"] == 1
    assert len(data["predictions"]) == 2
    # The invalid row is the second data row -> CSV line 3.
    assert data["invalid"][0]["row_number"] == 3
    assert "amount" in data["invalid"][0]["errors"][0].lower()
    assert sum(data["category_counts"].values()) == data["valid_rows"]
    for item in data["predictions"]:
        assert 0 <= item["risk_score"] <= 100
        assert item["risk_category"] in (
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        )
    # Results are persisted in the database.
    assert session.query(Prediction).count() == 2


def test_batch_all_invalid_rows_rejected(client_and_session):
    client, _ = client_and_session
    content = _csv_content([INVALID_ROW])
    response = client.post(
        "/api/predict/batch", files=_upload("data.csv", content)
    )
    assert response.status_code == 400
    assert "No valid rows" in response.json()["detail"]


def test_batch_rejects_too_many_rows(client_and_session, monkeypatch):
    client, _ = client_and_session
    monkeypatch.setattr(batch_routes, "MAX_BATCH_ROWS", 1)
    content = _csv_content([VALID_ROW, VALID_ROW])
    response = client.post(
        "/api/predict/batch", files=_upload("data.csv", content)
    )
    assert response.status_code == 400
    assert "Too many rows" in response.json()["detail"]


def test_batch_without_model_artifacts_fails_gracefully(
    client_and_session, tmp_path
):
    client, _ = client_and_session
    # Simulate missing artifacts with an empty models directory.
    app.dependency_overrides[get_model_service] = lambda: ModelService(
        str(tmp_path)
    )
    try:
        content = _csv_content([VALID_ROW])
        response = client.post(
            "/api/predict/batch",
            files=_upload("data.csv", content),
        )
        assert response.status_code == 503
        assert "model" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_model_service, None)


def test_sample_dataset_download(client_and_session):
    client, _ = client_and_session
    response = client.get("/api/dataset/sample")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text.startswith("transaction_id")
    # The sample must be clearly identifiable as synthetic.
    assert "synthetic" in response.headers.get(
        "content-disposition", ""
    ).lower()


def test_batch_dataset_columns_are_accepted(client_and_session):
    """The sample dataset uses transaction_id/timestamp column
    names; they must map to the API schema fields."""
    client, session = client_and_session
    content = (
        "transaction_id,timestamp,amount,category,"
        "transaction_hour,day_of_week,merchant_risk_score,"
        "distance_from_home,is_foreign,is_card_present,"
        "previous_transactions_today,account_age_days,"
        "failed_attempts_24h,is_fraud\n"
        "TXN-TEST-1,2026-10-01 10:30:00,75.5,dining,10,3,"
        "15.0,2.0,false,true,1,1200,0,0\n"
    )
    response = client.post(
        "/api/predict/batch", files=_upload("data.csv", content)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid_rows"] == 1
    assert data["predictions"][0]["transaction_reference"] == "TXN-TEST-1"
    # The original timestamp is preserved on the transaction.
    prediction = session.query(Prediction).first()
    assert prediction.transaction.transaction_reference == "TXN-TEST-1"
    assert prediction.transaction.features["amount"] == 75.5
