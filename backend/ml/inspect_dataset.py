"""Inspect the dataset (Phase 5, steps 1-2 of the ML design).

Usage (from the backend/ folder):
    python -m ml.inspect_dataset

Prints columns, data types, missing values, duplicate rows, and the
target distribution. The preprocessing pipeline in ml/preprocess.py
is adapted to THIS inspected schema - never assume columns without
inspecting the actual file.
"""

from ml.preprocess import DATASET_PATH, TARGET_COLUMN, load_dataset


def inspect(df) -> dict:
    """Return key dataset statistics as a dictionary."""
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "fraud_cases": int(df[TARGET_COLUMN].sum()),
        "fraud_rate": float(df[TARGET_COLUMN].mean()),
    }


def main():
    df = load_dataset()
    print(f"Dataset: {DATASET_PATH}")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n")

    print("Columns and data types:")
    print(df.dtypes.to_string())

    print("\nMissing values per column:")
    print(df.isna().sum().to_string())

    print(f"\nDuplicate rows: {df.duplicated().sum()}")

    print("\nTarget distribution:")
    print(df[TARGET_COLUMN].value_counts().to_string())
    print(f"Fraud rate: {df[TARGET_COLUMN].mean():.2%}")

    print("\nNumeric feature summary:")
    print(df.describe().to_string())


if __name__ == "__main__":
    main()
