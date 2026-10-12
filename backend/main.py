"""Financial Fraud Risk Detection API - entry point.

Phase 4: health check, CORS, and SQLite database initialization on startup.
Domain routers (auth, predict, transactions, model, dataset) are added in later phases.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load backend/.env before importing modules that read environment settings.
load_dotenv()

from api.database import init_db
from api.batch_routes import router as batch_router
from api.dataset_routes import router as dataset_router
from api.model_routes import router as model_router
from api.predict_routes import router as predict_router
from api.transaction_routes import router as transaction_router
from api.auth_routes import router as auth_router

@asynccontextmanager
async def lifespan(app):
    # Create database tables on startup (safe to call repeatedly).
    init_db()
    yield


app = FastAPI(
    title="Financial Fraud Risk Detection API",
    version="0.1.0",
    description=(
        "Educational fraud-risk assessment API. "
        "Demo only - not connected to real banking or payment systems."
    ),
    lifespan=lifespan,
)

# CORS: allowed origins are configurable (comma-separated) via ALLOWED_ORIGINS.
# Default: the Vite React development server.
_allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
allowed_origins = [
    origin.strip() for origin in _allowed_origins.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Domain routers (logically grouped endpoints).
app.include_router(predict_router)
app.include_router(batch_router)
app.include_router(model_router)
app.include_router(dataset_router)
app.include_router(transaction_router)
app.include_router(auth_router)


@app.get("/")
def root():
    """API status with a link to the interactive documentation."""
    return {
        "name": "Financial Fraud Risk Detection API",
        "version": app.version,
        "docs": "/docs",
    }


@app.get("/api/health")
def health_check():
    """Health check used by the frontend and the test suite."""
    return {"status": "ok"}
