"""Dataset upload and sample endpoints (Phase 9).

POST /api/dataset/upload - validate an uploaded CSV and
return a preview (row count, columns, sample rows, how
many rows are valid vs invalid). No predictions here.

GET /api/dataset/sample - download the documented sample
dataset (clearly labelled SYNTHETIC demonstration data).
"""

import math

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from api import schemas
from api.dataset_service import (
    MAX_UPLOAD_BYTES,
    check_required_columns,
    format_bytes,
    parse_csv,
    validate_rows,
)
from ml.preprocess import DATASET_PATH

router = APIRouter(prefix="/api", tags=["dataset"])


@router.post("/dataset/upload", response_model=schemas.DatasetPreview)
async def upload_dataset(file: UploadFile = File(...)):
    """Validate an uploaded CSV and return a preview."""
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

    try:
        df = parse_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    missing = check_required_columns(df)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                "Missing required columns: " + ", ".join(missing)
            ),
        )

    valid_payloads, invalid_rows = validate_rows(df)

    # JSON-safe sample rows (Timestamps -> ISO strings,
    # NaN -> None).
    sample = df.head(5).to_dict(orient="records")
    sample_rows = [
        {
            key: (
                value.isoformat()
                if hasattr(value, "isoformat")
                else (None if value is None or (
                    isinstance(value, float) and math.isnan(value)
                ) else value)
            )
            for key, value in row.items()
        }
        for row in sample
    ]

    return schemas.DatasetPreview(
        filename=file.filename,
        size_bytes=len(content),
        row_count=len(df),
        column_count=len(df.columns),
        columns=list(df.columns),
        sample_rows=sample_rows,
        valid_rows=len(valid_payloads),
        invalid_rows=len(invalid_rows),
    )


@router.get("/dataset/sample")
def download_sample_dataset():
    """Download the sample dataset.

    The file is SYNTHETIC demonstration data - the filename
    and the response header both say so.
    """
    if not DATASET_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Sample dataset not available. "
                "Run: python -m ml.generate_synthetic_data"
            ),
        )
    return FileResponse(
        DATASET_PATH,
        media_type="text/csv",
        filename=DATASET_PATH.name,
        headers={
            "X-Dataset-Note": (
                "SYNTHETIC demonstration data - "
                "not real transactions"
            )
        },
    )
