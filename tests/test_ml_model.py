"""
Machine Learning Model Unit & Integration Test Suite

Tests:
1. Training dataset generation & feature column structure
2. Target variable extraction (binary 1/0)
3. Train/test split & model training (Logistic Regression & Random Forest)
4. Evaluation metrics calculation (Accuracy, Precision, Recall, F1, ROC-AUC, CM)
5. Model saving & loading (joblib serialization)
6. Student placement inference for valid student (ID=1)
7. Invalid student ID edge case handling
8. Prediction probability bounds check (0.0 <= prob <= 1.0)
9. Feature importance extraction
"""

import os
import sys
import pandas as pd

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.ml_model import (
    prepare_training_data,
    train_model,
    save_model,
    load_model,
    predict_placement,
    get_model_metrics,
    get_feature_importance,
    FEATURE_COLUMNS
)


def test_dataset_preparation():
    print("Test 1: Dataset Generation & Feature Structure...", end=" ")
    X, y, feature_names = prepare_training_data()
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert len(X) >= 150, f"Expected at least 150 student samples, found {len(X)}."
    assert list(X.columns) == FEATURE_COLUMNS
    assert set(y.unique()).issubset({0, 1}), "Target y must be binary (0 or 1)."
    print("PASSED")


def test_model_training_and_evaluation():
    print("Test 2: Model Training & Evaluation Metrics...", end=" ")
    res = train_model("logistic", test_size=0.2, random_state=42)
    assert res["success"] is True, f"Training failed: {res.get('message')}"
    
    metrics = res["metrics"]
    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "roc_auc" in metrics
    assert "confusion_matrix" in metrics
    assert 0.0 <= metrics["accuracy"] <= 1.0
    print("PASSED")


def test_model_persistence():
    print("Test 3: Model Serialization & Deserialization...", end=" ")
    model = load_model()
    assert model is not None, "Loaded model must not be None."
    
    saved = save_model(model)
    assert saved is True, "save_model execution failed."
    print("PASSED")


def test_placement_inference():
    print("Test 4: Student Placement Inference (Student ID=1)...", end=" ")
    pred = predict_placement(1)
    assert isinstance(pred, dict)
    assert pred["student_id"] == 1
    assert pred["prediction"] in [0, 1]
    assert pred["prediction_label"] in ["Placed", "Not Placed"]
    assert 0.0 <= pred["probability"] <= 1.0
    assert "disclaimer" in pred
    print("PASSED")


def test_invalid_student_inference():
    print("Test 5: Invalid Student ID Inference...", end=" ")
    inv_pred = predict_placement(999999)
    assert "error" in inv_pred
    print("PASSED")


def test_feature_importance():
    print("Test 6: Feature Importance Extraction...", end=" ")
    importances = get_feature_importance()
    assert isinstance(importances, list)
    assert len(importances) == len(FEATURE_COLUMNS)
    assert "feature" in importances[0] and "importance" in importances[0]
    print("PASSED")


def run_all_tests():
    print("=" * 60)
    print("Phase 8A: Machine Learning Model Test Suite")
    print("=" * 60)

    test_dataset_preparation()
    test_model_training_and_evaluation()
    test_model_persistence()
    test_placement_inference()
    test_invalid_student_inference()
    test_feature_importance()

    print("=" * 60)
    print("[ALL PASSED] Machine Learning Model verified successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
