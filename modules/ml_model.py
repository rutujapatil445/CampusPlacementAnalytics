"""
Machine Learning Placement Likelihood Model Module

Provides a transparent, reproducible binary classification pipeline (Logistic Regression / Random Forest)
to estimate historical-data-driven placement probabilities.

Pipeline Steps:
1. Feature Extraction: Pre-placement academic, portfolio, & readiness score metrics
2. Data Leakage Prevention: Excludes post-placement attributes (CTC, company, offer status)
3. Preprocessing & Scaling: Standardisation using StandardScaler inside a Scikit-learn Pipeline
4. Model Evaluation: Accuracy, Precision, Recall, F1-Score, ROC-AUC & Confusion Matrix
5. Persistence: Joblib serialization to 'models/placement_model.joblib'
6. Inference: Single-student placement probability prediction with transparent disclaimer
"""

import os
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)

from config.database import fetch_one, fetch_all
from modules.student_manager import get_all_students, get_student_by_id, get_academic_record
from modules.portfolio_manager import (
    get_student_skills,
    get_student_projects,
    get_student_internships,
    get_student_certifications
)
from modules.readiness_engine import calculate_readiness_score

# Default path for model serialization
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
MODEL_FILE_PATH = os.path.join(MODEL_DIR, "placement_model.joblib")
METRICS_FILE_PATH = os.path.join(MODEL_DIR, "model_metrics.joblib")

# Feature Column Names (Pre-placement metrics only)
FEATURE_COLUMNS = [
    "current_cgpa",
    "ssc_percentage",
    "hsc_percentage",
    "total_active_backlogs",
    "total_dead_backlogs",
    "gap_years",
    "skills_count",
    "advanced_skills_count",
    "projects_count",
    "internships_count",
    "certifications_count",
    "readiness_score"
]

# Global cache for in-memory model reuse
_TRAINED_MODEL_CACHE = None
_MODEL_METRICS_CACHE = None


# ==============================================================================
# 1. FEATURE EXTRACTION & DATA LEAKAGE PREVENTION
# ==============================================================================

def extract_student_feature_row(student_id: int) -> dict:
    """
    Extracts pre-placement candidate feature vector for a single student.
    
    Data Leakage Prevention Note:
    - Excludes post-placement features such as 'company_id', 'offered_ctc', 'drive_id',
      or application selection status.
    """
    acad = get_academic_record(student_id)
    if not acad:
        return None

    cgpa = float(acad.get("current_cgpa", 6.0))
    ssc = float(acad.get("ssc_percentage", 60.0))
    hsc = float(acad["hsc_percentage"]) if acad.get("hsc_percentage") is not None else (
        float(acad["diploma_percentage"]) if acad.get("diploma_percentage") is not None else ssc
    )
    active_backlogs = int(acad.get("total_active_backlogs", 0))
    dead_backlogs = int(acad.get("total_dead_backlogs", 0))
    gap = int(acad.get("gap_years", 0))

    skills = get_student_skills(student_id)
    skills_count = len(skills)
    adv_skills_count = sum(1 for s in skills if s.get("proficiency_level") == "Advanced")

    projects_count = len(get_student_projects(student_id))
    internships_count = len(get_student_internships(student_id))
    certs_count = len(get_student_certifications(student_id))

    readiness = calculate_readiness_score(student_id)
    readiness_score = float(readiness.get("total_score", 50.0))

    return {
        "student_id": student_id,
        "current_cgpa": cgpa,
        "ssc_percentage": ssc,
        "hsc_percentage": hsc,
        "total_active_backlogs": active_backlogs,
        "total_dead_backlogs": dead_backlogs,
        "gap_years": gap,
        "skills_count": skills_count,
        "advanced_skills_count": adv_skills_count,
        "projects_count": projects_count,
        "internships_count": internships_count,
        "certifications_count": certs_count,
        "readiness_score": readiness_score
    }


def prepare_training_data() -> tuple:
    """
    Queries database and constructs training dataset (X, y).
    Target 'y': 1 if student has an accepted/pending offer in 'placements', 0 otherwise.
    
    Returns:
        tuple: (X_dataframe, y_series, feature_names_list)
    """
    all_students = get_all_students()
    if not all_students:
        return pd.DataFrame(), pd.Series(dtype=int), FEATURE_COLUMNS

    # Fetch set of placed student_ids
    placed_query = "SELECT DISTINCT student_id FROM placements WHERE acceptance_status IN ('Accepted', 'Pending');"
    placed_records = fetch_all(placed_query)
    placed_student_ids = {r["student_id"] for r in placed_records}

    rows = []
    targets = []

    for s in all_students:
        s_id = s["student_id"]
        feat_dict = extract_student_feature_row(s_id)
        if feat_dict:
            rows.append(feat_dict)
            targets.append(1 if s_id in placed_student_ids else 0)

    df = pd.DataFrame(rows)
    X = df[FEATURE_COLUMNS].fillna(0.0)
    y = pd.Series(targets, name="placed")

    return X, y, FEATURE_COLUMNS


# ==============================================================================
# 2. MODEL TRAINING & EVALUATION
# ==============================================================================

def train_model(model_type: str = "logistic", test_size: float = 0.2, random_state: int = 42) -> dict:
    """
    Trains binary classification model pipeline and evaluates test set metrics.
    
    Args:
        model_type (str): 'logistic' (LogisticRegression) or 'random_forest' (RandomForestClassifier).
        test_size (float): Proportion of test split (default 0.2).
        random_state (int): Reproducibility seed.
        
    Returns:
        dict: Training report with model metrics.
    """
    global _TRAINED_MODEL_CACHE, _MODEL_METRICS_CACHE

    X, y, feature_names = prepare_training_data()
    if len(X) < 10:
        return {"success": False, "message": "Insufficient data records for machine learning training."}

    # Stratified Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y if len(np.unique(y)) > 1 else None
    )

    # Scikit-learn Pipeline construction
    if model_type.lower() == "random_forest":
        pipeline = Pipeline([
            ("classifier", RandomForestClassifier(n_estimators=100, random_state=random_state))
        ])
    else:
        # Default: Logistic Regression with StandardScaler
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=random_state, max_iter=1000))
        ])

    # Model Fitting
    pipeline.fit(X_train, y_train)

    # Model Evaluation on Test Set
    y_pred = pipeline.predict(X_test)
    
    # Probability prediction if supported
    if hasattr(pipeline, "predict_proba"):
        y_prob = pipeline.predict_proba(X_test)[:, 1]
        try:
            roc_auc = round(float(roc_auc_score(y_test, y_prob)), 4)
        except ValueError:
            roc_auc = 0.5
    else:
        roc_auc = 0.5

    acc = round(float(accuracy_score(y_test, y_pred)), 4)
    prec = round(float(precision_score(y_test, y_pred, zero_division=0)), 4)
    rec = round(float(recall_score(y_test, y_pred, zero_division=0)), 4)
    f1 = round(float(f1_score(y_test, y_pred, zero_division=0)), 4)
    cm = confusion_matrix(y_test, y_pred).tolist()

    metrics = {
        "model_type": model_type,
        "total_samples": len(X),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "confusion_matrix": cm,
        "feature_names": feature_names
    }

    # Cache in memory & persist to disk
    _TRAINED_MODEL_CACHE = pipeline
    _MODEL_METRICS_CACHE = metrics
    save_model(pipeline, metrics)

    return {
        "success": True,
        "message": f"Model trained successfully ({model_type.upper()}).",
        "metrics": metrics
    }


# ==============================================================================
# 3. MODEL PERSISTENCE
# ==============================================================================

def save_model(model=None, metrics: dict = None, filepath: str = None) -> bool:
    """Saves trained Scikit-learn model pipeline and metrics to disk."""
    save_path = filepath if filepath else MODEL_FILE_PATH
    metrics_path = METRICS_FILE_PATH

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    target_model = model if model else _TRAINED_MODEL_CACHE
    target_metrics = metrics if metrics else _MODEL_METRICS_CACHE

    if not target_model:
        return False

    try:
        joblib.dump(target_model, save_path)
        if target_metrics:
            joblib.dump(target_metrics, metrics_path)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save model: {e}")
        return False


def load_model(filepath: str = None):
    """Loads saved Scikit-learn model pipeline from disk."""
    global _TRAINED_MODEL_CACHE, _MODEL_METRICS_CACHE

    save_path = filepath if filepath else MODEL_FILE_PATH
    metrics_path = METRICS_FILE_PATH

    if _TRAINED_MODEL_CACHE is not None:
        return _TRAINED_MODEL_CACHE

    if os.path.exists(save_path):
        try:
            _TRAINED_MODEL_CACHE = joblib.load(save_path)
            if os.path.exists(metrics_path):
                _MODEL_METRICS_CACHE = joblib.load(metrics_path)
            return _TRAINED_MODEL_CACHE
        except Exception as e:
            print(f"[NOTE] Model load exception: {e}")

    # Train fresh model if file does not exist
    train_res = train_model("logistic")
    if train_res.get("success"):
        return _TRAINED_MODEL_CACHE
    return None


# ==============================================================================
# 4. INFERENCE & PREDICTION
# ==============================================================================

def predict_placement(student_id: int) -> dict:
    """
    Estimates placement likelihood probability for a student using trained ML model.
    
    Returns:
        dict: {
            "student_id": int,
            "prediction": int (1 or 0),
            "prediction_label": "Placed" | "Not Placed",
            "probability": float (0.0 to 1.0),
            "disclaimer": str
        }
    """
    student = get_student_by_id(student_id)
    if not student:
        return {"error": "Student not found.", "student_id": student_id}

    model = load_model()
    if not model:
        return {"error": "ML model not trained or available.", "student_id": student_id}

    feat_dict = extract_student_feature_row(student_id)
    if not feat_dict:
        return {"error": "Academic record missing for student.", "student_id": student_id}

    # Convert to DataFrame matching feature column names
    X_single = pd.DataFrame([feat_dict])[FEATURE_COLUMNS]

    try:
        pred_class = int(model.predict(X_single)[0])
        prob = float(model.predict_proba(X_single)[0][1]) if hasattr(model, "predict_proba") else 0.5
        prob = round(min(1.0, max(0.0, prob)), 4)

        return {
            "student_id": student_id,
            "prediction": pred_class,
            "prediction_label": "Placed" if pred_class == 1 else "Not Placed",
            "probability": prob,
            "probability_percentage": f"{round(prob * 100, 2)}%",
            "disclaimer": "Model-estimated placement likelihood based on historical training data."
        }
    except Exception as e:
        return {"error": f"Prediction failed: {e}", "student_id": student_id}


# ==============================================================================
# 5. METRICS & FEATURE IMPORTANCE
# ==============================================================================

def get_model_metrics() -> dict:
    """Returns saved evaluation metrics for the trained model."""
    global _MODEL_METRICS_CACHE
    if _MODEL_METRICS_CACHE:
        return _MODEL_METRICS_CACHE

    if os.path.exists(METRICS_FILE_PATH):
        try:
            _MODEL_METRICS_CACHE = joblib.load(METRICS_FILE_PATH)
            return _MODEL_METRICS_CACHE
        except Exception:
            pass

    # Train model if metrics not loaded
    train_res = train_model("logistic")
    return train_res.get("metrics", {})


def get_feature_importance() -> list:
    """
    Extracts model feature importances/coefficients for interpretation.
    
    Returns:
        list of dicts: [{"feature": str, "importance": float}]
    """
    model = load_model()
    if not model:
        return []

    try:
        classifier = model.named_steps["classifier"]
        
        if hasattr(classifier, "coef_"):
            importances = classifier.coef_[0]
        elif hasattr(classifier, "feature_importances_"):
            importances = classifier.feature_importances_
        else:
            return []

        results = []
        for name, imp in zip(FEATURE_COLUMNS, importances):
            results.append({
                "feature": name,
                "importance": round(float(imp), 4)
            })

        results.sort(key=lambda x: abs(x["importance"]), reverse=True)
        return results

    except Exception as e:
        print(f"[ERROR] get_feature_importance failed: {e}")
        return []
