"""Model artifact loading and prediction service (Phase 7).

Loads the joblib artifacts saved by `python -m ml.train_model`
LAZILY: the API starts even when the artifacts are missing, and
prediction requests then fail gracefully with a clear error
(HTTP 503) instead of crashing the app.
"""

import json
import os
from pathlib import Path

import joblib
import pandas as pd
from xgboost import XGBClassifier  # noqa: F401 - type reference only

from ml.risk import (
    RANDOM_FOREST_WEIGHT,
    XGBOOST_WEIGHT,
    ensemble_probability,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODELS_DIR = BACKEND_DIR / "models"
METRICS_PATH = BACKEND_DIR / "data" / "model_metrics.json"

ARTIFACT_NAMES = ("preprocessor", "random_forest", "xgboost")


class ModelNotAvailableError(RuntimeError):
    """Raised when the trained model artifacts are missing."""


class ModelService:
    """Loads fitted models + preprocessor and runs the ensemble."""

    def __init__(self, models_dir):
        self._models_dir = Path(models_dir)
        self._preprocessor = None
        self._random_forest = None
        self._xgboost = None
        self._load_attempted = False

    def _load(self):
        """Load artifacts once. Missing files leave fields as None."""
        if self._load_attempted:
            return
        try:
            self._preprocessor = joblib.load(
                self._models_dir / "preprocessor.joblib"
            )
            self._random_forest = joblib.load(
                self._models_dir / "random_forest.joblib"
            )
            self._xgboost = joblib.load(
                self._models_dir / "xgboost.joblib"
            )
        except (FileNotFoundError, OSError):
            # Artifacts missing or unreadable: stay unavailable.
            self._preprocessor = None
            self._random_forest = None
            self._xgboost = None
        self._load_attempted = True

    @property
    def available(self) -> bool:
        self._load()
        return all(
            artifact is not None
            for artifact in (self._preprocessor, self._random_forest, self._xgboost)
        )

    def artifact_status(self) -> dict:
        return {
            name: (self._models_dir / f"{name}.joblib").exists()
            for name in ARTIFACT_NAMES
        }

    def predict(self, features: dict) -> float:
        """Return the ensemble fraud probability (0.0-1.0).

        Applies the SAME fitted preprocessing used during
        training, then the weighted ensemble:
        0.65 * xgboost_prob + 0.35 * random_forest_prob.
        """
        if not self.available:
            raise ModelNotAvailableError(
                "Trained model artifacts are not available."
            )
        X = pd.DataFrame([features])
        X_enc = self._preprocessor.transform(X)
        rf_proba = float(self._random_forest.predict_proba(X_enc)[:, 1][0])
        xgb_proba = float(self._xgboost.predict_proba(X_enc)[:, 1][0])
        return ensemble_probability(xgb_proba, rf_proba)

    def predict_batch(self, features_list: list):
        """Vectorized ensemble prediction for a batch.

        Returns a numpy array of fraud probabilities in the
        same order as features_list.
        """
        if not self.available:
            raise ModelNotAvailableError(
                "Trained model artifacts are not available."
            )
        X = pd.DataFrame(features_list)
        X_enc = self._preprocessor.transform(X)
        rf_proba = self._random_forest.predict_proba(X_enc)[:, 1]
        xgb_proba = self._xgboost.predict_proba(X_enc)[:, 1]
        return ensemble_probability(xgb_proba, rf_proba)

    def _metrics(self) -> dict:
        try:
            return json.loads(METRICS_PATH.read_text())
        except (OSError, json.JSONDecodeError):
            return {}

    def model_version(self) -> str:
        return self._metrics().get("model_version", "unknown")

    def training_date(self) -> str | None:
        return self._metrics().get("training_date")

    def status(self) -> dict:
        return {
            "available": self.available,
            "model_version": self.model_version(),
            "training_date": self.training_date(),
            "models_dir": str(self._models_dir),
            "artifacts": self.artifact_status(),
            "ensemble_weights": {
                "xgboost": XGBOOST_WEIGHT,
                "random_forest": RANDOM_FOREST_WEIGHT,
            },
        }


_service = None


def get_model_service() -> ModelService:
    """FastAPI dependency: one shared ModelService instance.

    The artifact directory can be overridden with the MODELS_DIR
    environment variable (useful for tests and administration).
    """
    global _service
    if _service is None:
        _service = ModelService(
            os.getenv("MODELS_DIR", str(DEFAULT_MODELS_DIR))
        )
    return _service
