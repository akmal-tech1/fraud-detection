"""Train and evaluate the fraud detection models (Phase 6).

Usage (from the backend/ folder):
    python -m ml.train_model

Pipeline:
1. Load the dataset and separate features from the target.
2. Stratified train/test split (20% test).
3. Fit the preprocessor on the TRAINING split only.
4. Train Random Forest and XGBoost. Class imbalance (~4% fraud)
   is handled with class_weight / scale_pos_weight applied to
   training data only.
5. Evaluate each model AND the weighted ensemble on the held-out
   TEST set only (never on training data).
6. Save fitted models and the preprocessor with joblib.
7. Write metrics to data/model_metrics.json and evaluation plots
   to data/evaluation/ (used by the Model Performance page).

Ensemble: 0.65 * xgboost_probability + 0.35 * random_forest_probability
(fraud-class probabilities). The weights are INITIAL PROJECT SETTINGS,
not proven optimal - see ml/risk.py for the tuning approach.

Probability calibration is NOT applied in v1: raw model
probabilities are used. If calibrated probabilities are required,
evaluate CalibratedClassifierCV on training-only validation data
first - do not assume probabilities are well calibrated.

Isolation Forest is deliberately NOT included: the project spec
marks it optional, and this unsupervised method produces anomaly
scores, not fraud probabilities. Listed as a future enhancement.

NOTE: the dataset is synthetic. Metrics produced here describe
demonstration data only and are NOT evidence of real-world fraud
detection effectiveness.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")  # no display server needed (terminal/CI friendly)

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from xgboost import XGBClassifier

from ml.preprocess import (
    DATASET_PATH,
    build_preprocessor,
    get_train_test_split,
    load_dataset,
    separate_features_and_target,
)
from ml.risk import (
    PREDICTION_THRESHOLD,
    RANDOM_FOREST_WEIGHT,
    XGBOOST_WEIGHT,
    ensemble_probability,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "models"
EVALUATION_DIR = BACKEND_DIR / "data" / "evaluation"
METRICS_PATH = BACKEND_DIR / "data" / "model_metrics.json"
MODEL_VERSION = "0.1.0"


def classification_metrics(y_true, probabilities):
    """Metrics for a model's fraud-class probabilities.

    Accuracy/precision/recall/F1 use PREDICTION_THRESHOLD for the
    binary decision; ROC-AUC uses the probabilities directly.
    """
    predictions = (probabilities >= PREDICTION_THRESHOLD).astype(int)
    return {
        "accuracy": round(float(accuracy_score(y_true, predictions)), 4),
        "precision": round(
            float(precision_score(y_true, predictions, zero_division=0)), 4
        ),
        "recall": round(
            float(recall_score(y_true, predictions, zero_division=0)), 4
        ),
        "f1": round(float(f1_score(y_true, predictions, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 4),
    }


def plot_confusion_matrix(y_true, probabilities, path):
    cm = confusion_matrix(
        y_true, (probabilities >= PREDICTION_THRESHOLD).astype(int)
    )
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        xticklabels=["Legitimate", "Fraud"],
        yticklabels=["Legitimate", "Fraud"],
        ax=ax,
    )
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    ax.set_title("Confusion matrix - held-out test set")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def plot_precision_recall_curves(y_true, curves, path):
    """curves: list of (name, fraud-class probabilities)."""
    prevalence = float(np.mean(y_true))
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for name, probabilities in curves:
        precision, recall, _ = precision_recall_curve(y_true, probabilities)
        average_precision = average_precision_score(y_true, probabilities)
        ax.plot(
            recall, precision, label=f"{name} (AP = {average_precision:.3f})"
        )
    ax.axhline(
        prevalence,
        linestyle="--",
        color="gray",
        label=f"Baseline (fraud rate = {prevalence:.2%})",
    )
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-recall curves - held-out test set")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main():
    # 1-2. Load, separate features/target, stratified split.
    df = load_dataset()
    X, y = separate_features_and_target(df)
    X_train, X_test, y_train, y_test = get_train_test_split(X, y)

    # 3. Preprocessing fitted on the TRAINING split only.
    preprocessor = build_preprocessor()
    X_train_enc = preprocessor.fit_transform(X_train)
    X_test_enc = preprocessor.transform(X_test)

    # 4. Train. Imbalance handling: class weights (training data only).
    n_legit = int((y_train == 0).sum())
    n_fraud = int((y_train == 1).sum())
    random_forest = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    xgboost = XGBClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=4,
        scale_pos_weight=n_legit / n_fraud,
        random_state=42,
        eval_metric="logloss",
    )
    random_forest.fit(X_train_enc, y_train)
    xgboost.fit(X_train_enc, y_train)

    # 5. Evaluate on the held-out test set only.
    rf_proba = random_forest.predict_proba(X_test_enc)[:, 1]
    xgb_proba = xgboost.predict_proba(X_test_enc)[:, 1]
    ensemble_proba = ensemble_probability(xgb_proba, rf_proba)

    metrics = {
        "model_version": MODEL_VERSION,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "prediction_threshold": PREDICTION_THRESHOLD,
        "ensemble_weights": {
            "xgboost": XGBOOST_WEIGHT,
            "random_forest": RANDOM_FOREST_WEIGHT,
        },
        "dataset": {
            "path": str(DATASET_PATH),
            "synthetic": True,
            "rows": int(len(df)),
            "fraud_cases": int(y.sum()),
            "fraud_rate": round(float(y.mean()), 4),
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
        },
        "models": {
            "random_forest": classification_metrics(y_test, rf_proba),
            "xgboost": classification_metrics(y_test, xgb_proba),
            "ensemble": {
                **classification_metrics(y_test, ensemble_proba),
                "average_precision": round(
                    float(
                        average_precision_score(y_test, ensemble_proba)
                    ),
                    4,
                ),
                "confusion_matrix": confusion_matrix(
                    y_test,
                    (ensemble_proba >= PREDICTION_THRESHOLD).astype(int),
                ).tolist(),
            },
        },
        "notes": [
            "Metrics are computed on the held-out test set only.",
            "Class imbalance (about 4% fraud) is handled with class weights / scale_pos_weight on training data only.",
            "The dataset is synthetic: these metrics are NOT evidence of real-world effectiveness.",
            "Precision = fraction of flagged transactions that are truly fraud; recall = fraction of frauds caught. A false positive flags a legitimate transaction; a false negative misses a fraud.",
        ],
    }

    # 6. Save fitted artifacts with joblib.
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(random_forest, MODELS_DIR / "random_forest.joblib")
    joblib.dump(xgboost, MODELS_DIR / "xgboost.joblib")
    joblib.dump(preprocessor, MODELS_DIR / "preprocessor.joblib")

    # 7. Evaluation plots and metrics file.
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    plot_confusion_matrix(
        y_test, ensemble_proba, EVALUATION_DIR / "confusion_matrix.png"
    )
    plot_precision_recall_curves(
        y_test,
        [
            ("Random Forest", rf_proba),
            ("XGBoost", xgb_proba),
            ("Ensemble", ensemble_proba),
        ],
        EVALUATION_DIR / "precision_recall_curve.png",
    )
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))

    # Console summary.
    print(
        f"Dataset: {len(df)} rows ({metrics['dataset']['fraud_rate']:.2%} fraud)"
    )
    print(f"Split: {len(X_train)} train / {len(X_test)} test (stratified)")
    for name in ("random_forest", "xgboost", "ensemble"):
        m = metrics["models"][name]
        print(
            f"{name:15s} precision={m['precision']:.3f} "
            f"recall={m['recall']:.3f} f1={m['f1']:.3f} "
            f"roc_auc={m['roc_auc']:.3f}"
        )
    print(f"Artifacts saved to {MODELS_DIR}")
    print(f"Metrics written to {METRICS_PATH}")
    print("NOTE: synthetic demonstration data - not real-world effectiveness.")


if __name__ == "__main__":
    main()
