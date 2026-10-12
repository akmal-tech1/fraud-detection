"""Phase 6 tests: risk score math and category boundaries.

The project spec requires exact boundary behaviour:
0 and 39 -> LOW, 40 and 59 -> MEDIUM, 60 and 79 -> HIGH,
80 and 100 -> CRITICAL.
"""

import pytest

from ml.risk import (
    RANDOM_FOREST_WEIGHT,
    XGBOOST_WEIGHT,
    classify,
    ensemble_probability,
    risk_category,
    risk_score,
)


@pytest.mark.parametrize(
    "probability,expected",
    [(0.0, 0), (0.01, 1), (0.25, 25), (0.5, 50), (0.75, 75), (1.0, 100)],
)
def test_risk_score_is_probability_times_100(probability, expected):
    assert risk_score(probability) == expected


def test_score_rounds_to_nearest_int():
    assert risk_score(0.123) == 12
    assert risk_score(0.987) == 99


@pytest.mark.parametrize(
    "score,expected",
    [
        (0, "LOW"),
        (39, "LOW"),
        (40, "MEDIUM"),
        (59, "MEDIUM"),
        (60, "HIGH"),
        (79, "HIGH"),
        (80, "CRITICAL"),
        (100, "CRITICAL"),
    ],
)
def test_risk_category_boundaries(score, expected):
    assert risk_category(score) == expected


def test_ensemble_weights_sum_to_one():
    assert XGBOOST_WEIGHT + RANDOM_FOREST_WEIGHT == pytest.approx(1.0)


def test_ensemble_uses_fraud_probabilities():
    # 0.65 * 1.0 + 0.35 * 0.0 = 0.65
    assert ensemble_probability(xgb_prob=1.0, rf_prob=0.0) == pytest.approx(0.65)
    # 0.65 * 0.0 + 0.35 * 1.0 = 0.35
    assert ensemble_probability(xgb_prob=0.0, rf_prob=1.0) == pytest.approx(0.35)
    # 0.65 * 0.8 + 0.35 * 0.4 = 0.66
    assert ensemble_probability(xgb_prob=0.8, rf_prob=0.4) == pytest.approx(0.66)


def test_classify_full_pipeline():
    assert classify(0.0) == (0, "LOW")
    assert classify(1.0) == (100, "CRITICAL")
    # 0.66 -> score 66 -> HIGH
    assert classify(0.66) == (66, "HIGH")
