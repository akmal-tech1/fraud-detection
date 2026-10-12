"""Risk score calculation (Phase 6).

Single source of truth for the risk math, shared by model training,
evaluation, and the prediction API so the thresholds can never drift
between components.

    ensemble_probability = 0.65 * xgb_prob + 0.35 * rf_prob
    risk_score           = round(ensemble_probability * 100)

Categories (project spec):
    LOW      0-39
    MEDIUM   40-59
    HIGH     60-79
    CRITICAL 80-100

IMPORTANT: the score is an ESTIMATED MODEL RISK, not a certainty
that a transaction is fraudulent.

Concept note: `predicted_class` (fraud/legitimate) uses a 0.5
probability threshold, while the risk score is a 0-100 band. A
transaction can therefore be MEDIUM risk (40-59) and still be
predicted legitimate. The two concepts are deliberately different.
"""

# Ensemble weights: INITIAL PROJECT SETTINGS, not proven optimal.
# How to validate/tune them: evaluate candidate weight pairs on
# training-only validation data (e.g., grid search maximizing
# fraud-class F1, or precision at a fixed recall), then update
# these values and document the result here.
XGBOOST_WEIGHT = 0.65
RANDOM_FOREST_WEIGHT = 0.35

RISK_CATEGORIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

# Threshold for the binary fraud/legitimate class decision.
# Deliberately separate from the 0-100 risk score bands: a
# transaction can be MEDIUM risk (40-59) and still be
# predicted legitimate (probability < 0.5).
PREDICTION_THRESHOLD = 0.5


def ensemble_probability(xgb_prob, rf_prob):
    """Weighted ensemble of fraud-CLASS probabilities (not labels)."""
    return XGBOOST_WEIGHT * xgb_prob + RANDOM_FOREST_WEIGHT * rf_prob


def risk_score(probability):
    """Convert an ensemble fraud probability to a 0-100 score."""
    return int(round(probability * 100))


def risk_category(score):
    """Map a 0-100 risk score to LOW / MEDIUM / HIGH / CRITICAL."""
    if score < 40:
        return "LOW"
    if score < 60:
        return "MEDIUM"
    if score < 80:
        return "HIGH"
    return "CRITICAL"


def classify(probability):
    """Full pipeline: ensemble probability -> (risk_score, category)."""
    score = risk_score(probability)
    return score, risk_category(score)
