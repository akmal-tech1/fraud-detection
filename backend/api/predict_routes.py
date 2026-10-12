"""Prediction endpoints (Phase 7).

POST /api/predict - analyze one transaction:
1. Validate the input (Pydantic schema).
2. Apply the same preprocessing used during training.
3. Generate the ensemble fraud probability.
4. Convert to a 0-100 risk score and category (ml/risk.py).
5. Save the transaction and prediction to the database.
6. Return the result with a model-estimate disclaimer.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api import schemas
from api.database import get_db
from api.model_service import (
    ModelNotAvailableError,
    get_model_service,
)
from api.models import Prediction, Transaction
from ml.risk import PREDICTION_THRESHOLD, classify

router = APIRouter(prefix="/api", tags=["predictions"])


@router.post("/predict", response_model=schemas.PredictionResponse)
def predict_transaction(
    payload: schemas.TransactionInput,
    db: Session = Depends(get_db),
    model_service=Depends(get_model_service),
):
    # 2-3. Preprocess + ensemble prediction.
    try:
        fraud_probability = model_service.predict(payload.features_dict())
    except ModelNotAvailableError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Trained model artifacts are not available. "
                "Ask the administrator to run: python -m ml.train_model"
            ),
        )

    # 4. Risk score and category (single source of truth: ml/risk.py).
    risk_score, risk_category = classify(fraud_probability)
    predicted_class = (
        "fraud"
        if fraud_probability >= PREDICTION_THRESHOLD
        else "legitimate"
    )

    # 5. Persist the transaction and the prediction.
    reference = (
        payload.transaction_reference
        or f"TXN-{uuid.uuid4().hex[:12].upper()}"
    )
    timestamp = payload.transaction_timestamp or datetime.now(
        timezone.utc
    )
    features = payload.features_dict()

    transaction = Transaction(
        transaction_reference=reference,
        transaction_timestamp=timestamp,
        features=features,
    )
    prediction = Prediction(
        transaction=transaction,
        fraud_probability=round(fraud_probability, 6),
        risk_score=risk_score,
        risk_category=risk_category,
        predicted_class=predicted_class,
        model_version=model_service.model_version(),
    )
    try:
        db.add(transaction)
        db.add(prediction)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"Transaction reference '{reference}' already exists. "
                "Provide a unique reference or omit it to generate one."
            ),
        )
    except Exception:
        db.rollback()
        # Do not expose internal exception details to the client.
        raise HTTPException(
            status_code=500,
            detail="Could not save the analysis result.",
        )

    # 6. Return the result.
    return schemas.PredictionResponse(
        transaction_reference=reference,
        transaction_timestamp=timestamp,
        fraud_probability=round(fraud_probability, 6),
        risk_score=risk_score,
        risk_category=risk_category,
        predicted_class=predicted_class,
        model_version=model_service.model_version(),
        features=features,
        disclaimer=schemas.DISCLAIMER,
    )
