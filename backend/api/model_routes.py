"""Model status and metrics endpoints (Phase 7).

GET /api/model/status - whether the trained model artifacts
are available (so the frontend can show a clear state).
GET /api/model/metrics - the genuine metrics produced by
`python -m ml.train_model` (never fabricated).
GET /api/dashboard/summary - real transaction/prediction statistics
from the SQLite database (Phase 10).
"""

import json

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api import schemas
from api.models import Prediction, Transaction
from api.model_service import METRICS_PATH, get_model_service
from api.database import get_db

router = APIRouter(prefix="/api/model", tags=["model"])


@router.get("/status", response_model=schemas.ModelStatusResponse)
def model_status(model_service=Depends(get_model_service)):
    return model_service.status()


@router.get("/metrics")
def model_metrics():
    if not METRICS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Model metrics are not available. "
                "Run: python -m ml.train_model"
            ),
        )
    return json.loads(METRICS_PATH.read_text())


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    """Real dashboard statistics from the database.

    Every number comes from actual DB queries — no hardcoded values,
    no fake charts, no simulated records.
    """
    total_transactions = db.scalar(
        select(func.count()).select_from(Transaction)
    )

    total_predictions = db.scalar(
        select(func.count()).select_from(Prediction)
    )

    fraud_count = db.scalar(
        select(func.count())
        .select_from(Prediction)
        .where(Prediction.predicted_class == "fraud")
    )

    legitimate_count = total_predictions - fraud_count

    risk_distribution = dict(
        db.execute(
            select(Prediction.risk_category, func.count())
            .group_by(Prediction.risk_category)
        ).fetchall()
    )

    score_min_max = db.execute(
        select(func.min(Prediction.risk_score), func.max(Prediction.risk_score))
    ).one()

    return {
        "total_transactions": total_transactions,
        "total_predictions": total_predictions,
        "fraud_count": fraud_count,
        "legitimate_count": legitimate_count,
        "risk_distribution": risk_distribution,
        "score_min": score_min_max[0] if score_min_max[0] is not None else 0,
        "score_max": score_min_max[1] if score_min_max[1] is not None else 100,
    }
