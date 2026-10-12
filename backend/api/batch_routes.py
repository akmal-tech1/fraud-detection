"""Batch prediction endpoint (Phase 9).

POST /api/predict/batch - analyze every valid row of an
uploaded CSV with the ensemble and persist the results.

Partially invalid files: valid rows are analyzed, invalid
rows are reported with their CSV line number and reasons.
Transaction references are generated when missing and
regenerated when they would collide (within the batch or
with existing database records) - the count is reported,
never silent.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from api import schemas
from api.database import get_db
from api.dataset_service import (
    MAX_BATCH_ROWS,
    MAX_UPLOAD_BYTES,
    check_required_columns,
    format_bytes,
    parse_csv,
    validate_rows,
)
from api.model_service import (
    ModelNotAvailableError,
    get_model_service,
)
from api.models import Prediction, Transaction
from ml.risk import (
    PREDICTION_THRESHOLD,
    RISK_CATEGORIES,
    classify,
)

router = APIRouter(prefix="/api", tags=["predictions"])


@router.post("/predict/batch", response_model=schemas.BatchPredictionResponse)
async def predict_batch(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    model_service=Depends(get_model_service),
):
    """Analyze every valid row of an uploaded CSV."""
    # 1. File validation.
    if not file.filename or not file.filename.lower().endswith(
        ".csv"
    ):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are accepted.",
        )
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File too large ({format_bytes(len(content))}). "
                f"Maximum size is {format_bytes(MAX_UPLOAD_BYTES)}."
            ),
        )

    # 2. Parse and validate the schema.
    try:
        df = parse_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if len(df) > MAX_BATCH_ROWS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Too many rows ({len(df)}). "
                f"Maximum is {MAX_BATCH_ROWS} rows per batch."
            ),
        )
    missing = check_required_columns(df)
    if missing:
        raise HTTPException(
            status_code=400,
            detail="Missing required columns: " + ", ".join(missing),
        )

    # 3. Validate rows (partially invalid files are OK).
    valid_payloads, invalid_rows = validate_rows(df)
    if not valid_payloads:
        raise HTTPException(
            status_code=400,
            detail=(
                "No valid rows to analyze. "
                "Fix the validation errors and try again."
            ),
        )

    # 4. Ensemble prediction (vectorized: one transform,
    #    one predict_proba call per model).
    try:
        probabilities = model_service.predict_batch(
            [payload.features_dict() for payload in valid_payloads]
        )
    except ModelNotAvailableError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Trained model artifacts are not available. "
                "Ask the administrator to run: python -m ml.train_model"
            ),
        )

    # 5. Transaction references: generate when missing,
    #    regenerate on collision (batch-internal or database).
    references = [
        payload.transaction_reference
        or f"TXN-{uuid.uuid4().hex[:12].upper()}"
        for payload in valid_payloads
    ]
    existing = set()
    if references:
        existing = set(
            db.execute(
                select(Transaction.transaction_reference).where(
                    Transaction.transaction_reference.in_(references)
                )
            )
            .scalars()
            .all()
        )
    seen = set()
    final_references = []
    regenerated = 0
    for reference in references:
        if reference in existing or reference in seen:
            reference = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            regenerated += 1
        seen.add(reference)
        final_references.append(reference)

    # 6. Score, categorize, and persist every valid row.
    category_counts = {category: 0 for category in RISK_CATEGORIES}
    prediction_items = []
    for payload, reference, probability in zip(
        valid_payloads, final_references, probabilities
    ):
        fraud_probability = float(probability)
        risk_score_value, risk_category_value = classify(
            fraud_probability
        )
        predicted_class = (
            "fraud"
            if fraud_probability >= PREDICTION_THRESHOLD
            else "legitimate"
        )
        category_counts[risk_category_value] += 1

        transaction = Transaction(
            transaction_reference=reference,
            transaction_timestamp=payload.transaction_timestamp
            or datetime.now(timezone.utc),
            features=payload.features_dict(),
        )
        db.add(
            Prediction(
                transaction=transaction,
                fraud_probability=round(fraud_probability, 6),
                risk_score=risk_score_value,
                risk_category=risk_category_value,
                predicted_class=predicted_class,
                model_version=model_service.model_version(),
            )
        )
        prediction_items.append(
            schemas.BatchResultItem(
                transaction_reference=reference,
                fraud_probability=round(fraud_probability, 6),
                risk_score=risk_score_value,
                risk_category=risk_category_value,
                predicted_class=predicted_class,
            )
        )

    db.commit()

    # 7. Response with summary, per-row results, and the
    #    invalid-row report.
    return schemas.BatchPredictionResponse(
        total_rows=len(df),
        valid_rows=len(valid_payloads),
        invalid_rows=len(invalid_rows),
        invalid=invalid_rows,
        category_counts=category_counts,
        predictions=prediction_items,
        references_regenerated=regenerated,
        disclaimer=schemas.DISCLAIMER,
    )
