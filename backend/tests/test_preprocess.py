"""Phase 5 tests: dataset loading, feature separation, splitting, preprocessing."""

import numpy as np
import pytest

from ml.preprocess import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
    build_preprocessor,
    get_train_test_split,
    load_dataset,
    separate_features_and_target,
)


@pytest.fixture(scope="module")
def dataset():
    return load_dataset()


def test_dataset_has_required_schema(dataset):
    expected = {
        "transaction_id",
        "timestamp",
        TARGET_COLUMN,
        *CATEGORICAL_FEATURES,
        *NUMERIC_FEATURES,
    }
    assert expected.issubset(set(dataset.columns))


def test_dataset_has_no_missing_values(dataset):
    assert dataset.isna().sum().sum() == 0


def test_feature_separation_drops_identifiers_and_target(dataset):
    X, y = separate_features_and_target(dataset)
    assert "transaction_id" not in X.columns
    assert "timestamp" not in X.columns
    assert TARGET_COLUMN not in X.columns
    assert len(X) == len(y) == len(dataset)
    assert set(y.unique()) == {0, 1}


def test_stratified_split_preserves_class_ratio(dataset):
    X, y = separate_features_and_target(dataset)
    X_train, X_test, y_train, y_test = get_train_test_split(X, y)
    assert len(X_train) + len(X_test) == len(X)
    # Stratified split keeps roughly the same fraud rate in both sets.
    assert abs(y_train.mean() - y.mean()) < 0.01
    assert abs(y_test.mean() - y.mean()) < 0.01
    # No row leakage between the splits.
    assert set(X_train.index).isdisjoint(X_test.index)


def test_preprocessor_transforms_train_and_test(dataset):
    X, y = separate_features_and_target(dataset)
    X_train, X_test, _, _ = get_train_test_split(X, y)
    preprocessor = build_preprocessor()
    X_train_enc = preprocessor.fit_transform(X_train)
    X_test_enc = preprocessor.transform(X_test)
    assert X_train_enc.shape[0] == len(X_train)
    assert X_test_enc.shape[0] == len(X_test)
    assert X_train_enc.shape[1] == X_test_enc.shape[1]
    assert not np.isnan(X_train_enc).any()


def test_preprocessor_handles_unknown_category(dataset):
    X, y = separate_features_and_target(dataset)
    X_train, X_test, _, _ = get_train_test_split(X, y)
    preprocessor = build_preprocessor()
    preprocessor.fit(X_train)
    X_unknown = X_test.iloc[:5].copy()
    X_unknown["category"] = "brand_new_category"
    X_enc = preprocessor.transform(X_unknown)  # must not raise
    assert X_enc.shape[0] == 5
