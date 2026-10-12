"""Transaction history and detail endpoints (Phase 11).

GET /api/transactions - list transactions (optionally filtered by user)
GET /api/transactions/{id} - get a single transaction with its prediction
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import Transaction, Prediction

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("")
def list_transactions(
    db: Session = Depends(get_db),
    user_id: int | None = Query(default=None, description="Filter by user ID"),
    skip: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=50, ge=1, le=500, description="Page size"),
):
    """List transactions, optionally filtered by user.

    Returns basic transaction info without the full JSON features blob
    unless explicitly requested, to keep list responses lightweight.
    """
    query = db.query(Transaction)

    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)

    total = query.count()

    transactions = query.order_by(Transaction.transaction_timestamp.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

    transaction_ids = [txn.id for txn in transactions]
    latest_predictions = {}
    if transaction_ids:
        predictions = (
            db.query(Prediction)
            .filter(Prediction.transaction_id.in_(transaction_ids))
            .order_by(Prediction.created_at.desc(), Prediction.id.desc())
            .all()
        )
        for prediction in predictions:
            latest_predictions.setdefault(prediction.transaction_id, prediction)

    result = []
    for txn in transactions:
        # Include a preview of features (first 3 keys) to keep the list useful
        features = txn.features or {}
        features_preview = {
            k: v for k, v in list(features.items())[:3]
        }
        result.append(
            {
                "id": txn.id,
                "transaction_reference": txn.transaction_reference,
                "transaction_timestamp": txn.transaction_timestamp.isoformat()
                if txn.transaction_timestamp
                else None,
                "user_id": txn.user_id,
                "features_preview": features_preview,
                "created_at": txn.created_at.isoformat() if txn.created_at else None,
                "prediction": (
                    {
                        "fraud_probability": prediction.fraud_probability,
                        "risk_score": prediction.risk_score,
                        "risk_category": prediction.risk_category,
                        "predicted_class": prediction.predicted_class,
                    }
                    if (prediction := latest_predictions.get(txn.id))
                    else None
                ),
            }
        )

    return {"total": total, "skip": skip, "limit": limit, "items": result}


@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: int = Path(..., description="Transaction ID"),
    db: Session = Depends(get_db),
):
    """Get a single transaction with its associated prediction.

    Returns the full transaction record including the features JSON,
    plus the latest prediction (most recent by created_at).
    """
    txn = db.get(Transaction, transaction_id)
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Fetch the latest prediction for this transaction
    prediction = (
        db.query(Prediction)
        .filter(Prediction.transaction_id == txn.id)
        .order_by(Prediction.created_at.desc(), Prediction.id.desc())
        .first()
    )

    features = txn.features or {}

    result = {
        "id": txn.id,
        "transaction_reference": txn.transaction_reference,
        "transaction_timestamp": (
            txn.transaction_timestamp.isoformat()
            if txn.transaction_timestamp
            else None
        ),
        "user_id": txn.user_id,
        "features": features,
        "created_at": txn.created_at.isoformat() if txn.created_at else None,
        "prediction": {
            "id": prediction.id if prediction else None,
            "fraud_probability": prediction.fraud_probability if prediction else None,
            "risk_score": prediction.risk_score if prediction else None,
            "risk_category": prediction.risk_category if prediction else None,
            "predicted_class": prediction.predicted_class if prediction else None,
            "model_version": prediction.model_version if prediction else None,
            "created_at": prediction.created_at.isoformat() if prediction else None,
        }
        if prediction
        else None,
    }

    return result