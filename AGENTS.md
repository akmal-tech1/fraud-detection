# AGENTS.md

## Project
Greenfield **Financial Fraud Risk Detection** web app (student internship demo). React + Vite + JavaScript frontend, FastAPI + SQLAlchemy backend, SQLite database, scikit-learn/XGBoost ML pipeline. This folder is the project root AND the git repository — `backend/`, `frontend/`, `docs/` live directly in it. The full 18-section spec was given in the kickoff conversation and is NOT in the repo — ask the user to re-share it, or save it as `docs/PROJECT_SPEC.md`; until then this file is the source of truth.

## Non-negotiable rules (easy to get wrong)
- Educational demo only: never connect real banking accounts, process real payment credentials, or block real transactions.
- Risk math (test boundaries 0, 39, 40, 59, 60, 79, 80, 100):
  - `risk_score = round(ensemble_probability * 100)`
  - LOW 0–39, MEDIUM 40–59, HIGH 60–79, CRITICAL 80–100
- Ensemble: `0.65 * xgb_fraud_prob + 0.35 * rf_fraud_prob` — fraud-CLASS probabilities, never labels. Weights are initial project settings, not proven optimal; document how to tune them on training-only validation data.
- Never invent dataset columns. Inspect the actual CSV first and adapt preprocessing to its real schema. Training and prediction must share ONE identical feature schema.
- Class imbalance handling (class weights or resampling) applies to TRAINING data only; stratified split; evaluate only on the held-out test set; prioritize fraud-class precision/recall — never claim effectiveness from accuracy alone.
- No hardcoded admin passwords or secrets anywhere. Secrets via env vars; commit `.env.example` placeholders only. Never commit `.env`, `venv/`, `*.db`, or large model artifacts.
- Dashboard stats and charts must come from real DB queries/analyses — no hardcoded numbers, fake charts, or simulated records. Never fabricate metrics or claim tests passed unless actually run.
- Synthetic sample data must be clearly labeled demonstration data; its performance is never evidence of real-world effectiveness. No PII, card numbers, or credentials in any dataset.
- Risk UI: consistent colors per category but never color alone — always pair with text labels.

## Stack (pin versions in `backend/requirements.txt`)
- Backend: Python, FastAPI, Uvicorn, Pydantic, SQLAlchemy ORM, python-jose (JWT, only if auth is built), joblib for model artifacts.
- ML: pandas, numpy, scikit-learn, xgboost, imbalanced-learn, matplotlib, seaborn; optional Isolation Forest.
- Frontend: React + Vite + plain JavaScript (NOT TypeScript), react-router-dom v7 (BrowserRouter/Routes/NavLink), Recharts, fetch. Scaffold: `npm create vite@latest frontend -- --template react`. `src/` contains `components/Layout.jsx` (sidebar shell), `components/RiskBar.jsx` (0-100 risk gauge), `pages/Dashboard.jsx` (live backend status), `pages/AnalyzePage.jsx` (transaction form + result), `pages/PlaceholderPage.jsx`, `services/api.js` (API client reading `VITE_API_BASE_URL`).

## Layout & API
- Structure: `backend/` (`main.py`, `api/` routers by domain, `ml/`, `data/`, `models/`, `tests/`), `frontend/src/` (`components/`, `pages/`, `services/`, `hooks/`, `styles/`), `docs/`. No empty files claiming finished features.
- Endpoints: `GET /`, `GET /api/health`, `POST /api/predict`, `POST /api/predict/batch`, `GET /api/model/status`, `GET /api/model/metrics`, `POST /api/dataset/upload`, `GET /api/dataset/sample` are IMPLEMENTED (Phase 9). Still to build: `POST /api/auth/register|login` (Phase 12), `GET /api/dashboard/summary` (Phase 10), `GET /api/transactions` + `GET /api/transactions/{id}` (Phase 11). Use Pydantic schemas for all I/O; return proper HTTP errors; interactive docs at `/docs`.
- Joblib-save fitted models AND preprocessors to `backend/models/`; `GET /api/model/status` reports availability; prediction endpoints must fail gracefully when artifacts are missing (covered by tests).
- Database: SQLite at `backend/fraud_detection.db` (override via `DATABASE_URL` env). Tables auto-created on app startup (FastAPI lifespan → `init_db()`) or manually via `python -m api.database`. Inspect with DB Browser for SQLite or the Python REPL (`import sqlite3; sqlite3.connect("fraud_detection.db")`). `Transaction.features` is intentionally a JSON column — the real feature schema is fixed in Phase 5; `Transaction.user_id` is a deliberate spec addition for Phase 12 per-user authorization (nullable for system/batch jobs).
- Dataset (Phase 5): `backend/data/synthetic_transactions.csv`, synthetic demo data only (6,000 rows, ~4% fraud, seed 42 → deterministic). Regenerate: `python -m ml.generate_synthetic_data`; inspect: `python -m ml.inspect_dataset`. Feature schema lives in `ml/preprocess.py` (10 numeric + `category` categorical; `transaction_id`/`timestamp` excluded as identifier/metadata). Any real dataset supplied later must be inspected first and the schema re-derived — do not assume this schema carries over.
- Model training (Phase 6): `python -m ml.train_model` → joblib artifacts in `backend/models/` (`random_forest.joblib`, `xgboost.joblib`, `preprocessor.joblib`), genuine metrics in `backend/data/model_metrics.json`, plots in `backend/data/evaluation/`. `ml/risk.py` is the SINGLE SOURCE OF TRUTH for score/category math AND `PREDICTION_THRESHOLD` (0.5, the fraud/legitimate class boundary) — never duplicate thresholds elsewhere. Ensemble weights 0.65/0.35 are initial settings (tuning approach documented in `ml/risk.py`). Isolation Forest and probability calibration are deliberately NOT in v1 (spec marks them optional) — future enhancements. `predicted_class` uses the 0.5 threshold; a transaction can be MEDIUM risk (40–59) yet predicted legitimate — score band and binary class are different concepts.
- Prediction API (Phase 7): `POST /api/predict` (Pydantic-validated input mirroring the Phase 5 feature schema; applies the SAME fitted preprocessor; saves Transaction+Prediction to SQLite; returns probability, score, category, class, disclaimer). `GET /api/model/status` lazily checks joblib artifacts (app starts even without them; predict returns HTTP 503 when missing). `GET /api/model/metrics` serves `data/model_metrics.json` (404 with a hint if absent). Artifact dir overridable via `MODELS_DIR` env. Tests override FastAPI dependencies (`app.dependency_overrides`) — no monkeypatching.
- Batch & dataset (Phase 9): shared CSV logic in `api/dataset_service.py` (`parse_csv`, `validate_rows` — every row validated against the SAME `TransactionInput` schema as the single-predict API; `transaction_id`/`timestamp` columns are mapped to API field names). `POST /api/dataset/upload` → preview with valid/invalid row counts (400 bad extension/columns, 413 over 10 MB). `POST /api/predict/batch` → vectorized ensemble over valid rows, persists results, reports invalid rows with CSV line numbers (partially invalid files are partially processed), regenerates missing/duplicate references (count reported, never silent), 400 if no valid rows or over 10,000 rows. `GET /api/dataset/sample` serves the synthetic CSV with an X-Dataset-Note header. Frontend builds download CSVs client-side as Blobs (no server temp files).

## Commands (Windows PowerShell)
- venv: `python -m venv backend\venv`, activate `backend\venv\Scripts\Activate.ps1`; if execution policy blocks it: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
- Backend: from `backend/` run `uvicorn main:app --reload`
- Frontend: `npm create vite@latest`, `npm install`, `npm run dev` (default http://localhost:5173 — configure CORS and `VITE_API_BASE_URL` accordingly)
- Tests: from `backend/` run `pytest tests`. Quirk: starlette TestClient prints a harmless `httpx`→`httpx2` deprecation warning; tests still pass.
- Live HTTP checks: use `curl.exe -s -i` (NOT `Invoke-WebRequest` — it fails with "NonInteractive mode" in automated PowerShell sessions; or add `-UseBasicParsing`). For JSON POST bodies, the reliable method is a payload file: write the JSON to a temp file, then `curl.exe -d "@$env:TEMP\payload.json"` — inline JSON quoting gets mangled by nested shell layers.
- Final deliverable zip (user wants the project zipped), from the repo root (Windows 10+ bsdtar; `-a` infers zip format from the extension): `tar -a -cf ..\Financial-Fraud-Detection.zip --exclude=.git --exclude=venv --exclude=node_modules --exclude=.env --exclude=*.db --exclude=*.joblib *`
- Verified working on this machine (2026-10-09): Python 3.14.5, Node 24.15.0, npm 11.12.1, Git 2.53.0. Full stack installed WITH cp314 wheels: fastapi 0.143.0, uvicorn 0.54.0, pydantic 2.14.0, sqlalchemy 2.1.4, pandas 3.0.6, numpy 2.5.3, scikit-learn 1.9.1, xgboost 3.4.1, imbalanced-learn 0.14.2, bcrypt 5.0.0, python-jose 3.5.0, pytest 9.1.1, vite 8.3.4, react 19.2.8. Only if a future package lacks a cp314 wheel: install Python 3.12 from python.org and recreate the venv with `py -3.12 -m venv backend\venv`.

## Working method
- 15 phases (env/structure → minimal FastAPI → React skeleton → DB models → dataset inspection → training/eval → single predict → analysis form → CSV batch → dashboard → history/details → auth → tests → UI polish → docs/GitHub). ONE phase at a time; give a verification checklist before advancing.
- Every code block: exact file path, say whether to CREATE or REPLACE, complete runnable contents (no fragments). Never silently remove existing functionality. Keep imports, routes, schemas, models, and frontend API calls consistent.
- Beginner-friendly explanations; troubleshoot from the actual error message; explain commands and expected output.
- If a feature depends on missing info (e.g., a real labelled dataset), state exactly what is needed and provide a synthetic sample only as a fallback.

## Resolved decisions (kickoff, 2026-10-09)
- Dataset: SYNTHETIC demo data only (no real labelled dataset supplied). Generate it in Phase 5 via a script; clearly label it demonstration data.
- Auth: INCLUDED in v1 — register/login with JWT (python-jose), password hashing with bcrypt directly (passlib is NOT used: it breaks with bcrypt>=4.1), protected routes. Demo admin account configured via env vars only, never hardcoded.
