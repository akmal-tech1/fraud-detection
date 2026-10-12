"""Phase 1 tests: API status and health check."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_returns_api_info():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Financial Fraud Risk Detection API"
    assert "docs" in data


def test_health_check_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_allows_127_loopback_frontend():
    response = client.get(
        "/api/health",
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_dashboard_summary_returns_database_statistics():
    response = client.get("/api/model/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert {
        "total_transactions",
        "total_predictions",
        "fraud_count",
        "legitimate_count",
        "risk_distribution",
        "score_min",
        "score_max",
    } <= data.keys()
    if data["total_predictions"] == 0:
        assert data["score_min"] == 0
        assert data["score_max"] == 100


def test_transaction_history_returns_database_records():
    response = client.get("/api/transactions")
    assert response.status_code == 200
    assert {"total", "skip", "limit", "items"} <= response.json().keys()
