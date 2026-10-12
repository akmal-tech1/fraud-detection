"""CSV dataset parsing and validation (Phase 9).

Shared by the upload/preview and batch prediction endpoints
so a CSV is validated exactly the same way in both places.

Validation rules:
- file must be a CSV, at most MAX_UPLOAD_BYTES
- required feature columns must be present
- every row is validated against the TransactionInput
  schema (the same schema the single-transaction API uses)

Partially invalid files are supported: valid rows are
analyzed, invalid rows are reported with their row number
and reasons.
"""

import csv
import io
import math

import pandas as pd
from pydantic import ValidationError

from api.schemas import TransactionInput
from ml.preprocess import CATEGORICAL_FEATURES, NUMERIC_FEATURES

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_BATCH_ROWS = 10000

REQUIRED_COLUMNS = set(CATEGORICAL_FEATURES + NUMERIC_FEATURES)

# The dataset uses "transaction_id" and "timestamp"; the API
# schema uses "transaction_reference" and "transaction_timestamp".
REFERENCE_COLUMNS = ("transaction_reference", "transaction_id")


def parse_csv(content: bytes) -> pd.DataFrame:
    """Parse CSV bytes. Raises ValueError on failure."""
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise ValueError(
            f"Could not parse the file as CSV: {exc}"
        ) from exc
    if df.empty:
        raise ValueError("The CSV file contains no data rows.")
    return df


def check_required_columns(df: pd.DataFrame) -> list[str]:
    """Return the missing required columns (empty list = OK)."""
    return sorted(REQUIRED_COLUMNS - set(df.columns))


def reference_column(df: pd.DataFrame) -> str | None:
    """The column holding the transaction reference, if any."""
    for name in REFERENCE_COLUMNS:
        if name in df.columns:
            return name
    return None


def _to_python(value):
    """Convert numpy scalars to plain Python types so
    Pydantic validation accepts them."""
    if hasattr(value, "item"):
        return value.item()
    return value


def _normalize_row(row_dict: dict) -> dict:
    """Map dataset column names to API field names."""
    if (
        "transaction_id" in row_dict
        and "transaction_reference" not in row_dict
    ):
        row_dict["transaction_reference"] = row_dict.pop(
            "transaction_id"
        )
    if (
        "timestamp" in row_dict
        and "transaction_timestamp" not in row_dict
    ):
        row_dict["transaction_timestamp"] = row_dict.pop("timestamp")
    return row_dict


def validate_rows(df: pd.DataFrame):
    """Validate every row against the transaction schema.

    Returns (valid_payloads, invalid_rows):
    - valid_payloads: list of TransactionInput
    - invalid_rows: list of {"row_number", "errors"}
      (row_number is the 1-based line number in the CSV,
      counting the header as line 1)
    """
    valid_payloads = []
    invalid_rows = []
    for index, row in df.iterrows():
        # Empty CSV cells arrive as NaN; dropping them turns
        # them into "field required" validation errors.
        row_dict = {
            key: _to_python(value)
            for key, value in row.items()
            if not (isinstance(value, float) and math.isnan(value))
        }
        row_dict = _normalize_row(row_dict)
        try:
            valid_payloads.append(
                TransactionInput.model_validate(row_dict)
            )
        except ValidationError as exc:
            errors = [
                "{}: {}".format(
                    ".".join(str(part) for part in error["loc"])
                    or "row",
                    error["msg"],
                )
                for error in exc.errors()
            ]
            invalid_rows.append(
                {
                    "row_number": index + 2,
                    "errors": errors,
                }
            )
    return valid_payloads, invalid_rows


def format_bytes(size: int) -> str:
    """Human-readable file size."""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def csv_sample(rows: list[dict]) -> bytes:
    """Build a small CSV in memory (used by tests)."""
    if not rows:
        return b""
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")
