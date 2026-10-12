# Financial Fraud Risk Detection

Educational web app that estimates the fraud risk of a financial transaction
using a machine learning ensemble (XGBoost + Random Forest).

**Demo only** - not connected to real banking, payment credentials, or live
transaction blocking. All datasets are synthetic demonstration data.

Project status: **Phase 15 of 15** (complete).

## Quick start (Windows / PowerShell)

```powershell
# Backend
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --reload        # API at http://localhost:8000, docs at /docs

# Frontend (second terminal)
cd frontend
npm install
npm run dev                      # React at http://localhost:5173
```

If `venv\Scripts\Activate.ps1` is blocked by the execution policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Tests

```powershell
cd backend
pytest tests
```

## Database (Phase 4)

SQLite via SQLAlchemy. Tables are created automatically when the API
starts, or manually:

```powershell
cd backend
venv\Scripts\Activate.ps1
python -m api.database        # creates backend/fraud_detection.db
```

Inspect the database with [DB Browser for SQLite](https://sqlitebrowser.org/)
or from the Python REPL:

```powershell
venv\Scripts\python.exe
>>> import sqlite3
>>> con = sqlite3.connect("fraud_detection.db")
>>> print([r[0] for r in con.execute("select name from sqlite_master where type='table'")])
```

## Demo account sign-in

Open **Sign in** in the frontend to sign in with an email and password or
create an account with a username, email, and password. The API provides
`POST /api/auth/register`, `POST /api/auth/login`, and `GET /api/auth/me`.
The frontend keeps the returned token in the current browser tab's
`sessionStorage`.

Set a private, random `SECRET_KEY` in `backend/.env` for tokens that remain
valid across API restarts; `backend/.env.example` is only a template. If no
key is configured, the API creates an ephemeral key at startup, so existing
tokens stop working after a restart. This demo sign-in does **not** protect
the other application routes or associate saved analyses with an account.

## Machine learning data (Phase 5)

The project uses a **synthetic demonstration dataset** (no real labelled
dataset was supplied). It is generated deterministically:

```powershell
cd backend
venv\Scripts\Activate.ps1
python -m ml.generate_synthetic_data    # writes data/synthetic_transactions.csv
python -m ml.inspect_dataset            # prints schema, missing values, class balance
```

Schema: 10 numeric features + 1 categorical feature (`category`),
target `is_fraud` (~4% fraud rate). `transaction_id` and `timestamp`
are identifier/metadata columns and are excluded from model features.

**Reminder:** performance on this synthetic data is NOT evidence of
real-world fraud detection effectiveness.

## Train the models (Phase 6)

```powershell
cd backend
venv\Scripts\Activate.ps1
python -m ml.train_model
```

Trains Random Forest + XGBoost (class-weighted for the ~4% fraud
rate), evaluates both and the 0.65/0.35 ensemble on the held-out
test set only, saves fitted artifacts to `backend/models/` (joblib),
writes metrics to `backend/data/model_metrics.json`, and plots the
confusion matrix + precision-recall curves to `backend/data/evaluation/`.

## Analyze one transaction (Phase 7)

With the API running (`uvicorn main:app --reload`), the
interactive docs at http://localhost:8000/docs list every
endpoint. Example:

```powershell
curl.exe -X POST http://localhost:8000/api/predict `
  -H "Content-Type: application/json" `
  -d '{"amount": 250.0, "category": "electronics", "transaction_hour": 2, "day_of_week": 1, "merchant_risk_score": 80.0, "distance_from_home": 45.5, "is_foreign": true, "is_card_present": false, "previous_transactions_today": 3, "account_age_days": 30, "failed_attempts_24h": 2}'
```

Returns the fraud probability, 0-100 risk score, risk category,
predicted class, and a disclaimer that the result is a model
estimate. Also available: `GET /api/model/status` (are the
trained artifacts present?) and `GET /api/model/metrics`
(genuine training metrics).

## Batch analysis (Phase 9)

Upload a CSV of transactions (same columns as the dataset
schema) via the Batch Analysis page, or the API:

- `POST /api/dataset/upload` - validate + preview (row count,
  columns, sample rows, valid/invalid row counts)
- `POST /api/predict/batch` - analyze every valid row,
  report invalid rows with reasons, persist results
- `GET /api/dataset/sample` - download the synthetic sample CSV

Limits: 10 MB and 10,000 rows per file. Partially invalid
files: valid rows are analyzed, invalid rows are skipped and
reported. Duplicate or missing transaction references are
regenerated (the count is reported in the response).

## Project layout

- `backend/` - FastAPI app, SQLAlchemy models, ML pipeline, tests
  - `main.py` - app entry point (health check, CORS, DB init, routers)
  - `api/database.py` - engine, session factory, `init_db()`
  - `api/models.py` - User, Transaction, Prediction, AuditEvent
  - `api/schemas.py` - Pydantic request/response schemas
  - `api/model_service.py` - lazy joblib artifact loading + ensemble
  - `api/dataset_service.py` - shared CSV parsing + row validation
  - `api/predict_routes.py` - POST /api/predict
  - `api/batch_routes.py` - POST /api/predict/batch
  - `api/model_routes.py` - GET /api/model/status, /api/model/metrics
  - `api/dataset_routes.py` - POST /api/dataset/upload, GET /api/dataset/sample
  - `ml/` - dataset generation, preprocessing, training, risk math
- `frontend/` - React + Vite dashboard
  - `src/components/Layout.jsx` - sidebar navigation shell
  - `src/components/RiskBar.jsx` - 0-100 risk gauge
  - `src/pages/Dashboard.jsx` - live backend status
  - `src/pages/AnalyzePage.jsx` - transaction form + result
  - `src/pages/BatchPage.jsx` - CSV upload, preview, batch results
  - `src/pages/TransactionHistoryPage.jsx` - paginated saved analyses and details
  - `src/pages/ModelPerformancePage.jsx` - measured test metrics and model status
  - `src/pages/AboutPage.jsx` - project guide, safety notes, and API reference
  - `src/pages/LoginPage.jsx` - demo account registration and sign-in
  - `src/services/api.js` - API client
- `docs/` - architecture, API documentation, testing report (added in later phases)
