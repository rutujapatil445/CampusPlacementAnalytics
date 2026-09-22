"""
Readiness Engine Unit & Integration Test Suite

Tests:
1. Valid student readiness calculation (student_id = 1)
2. Invalid student ID handling
3. Academic score component calculation
4. Skills score component calculation
5. Projects score component calculation
6. Internship score component calculation
7. Certification score component calculation
8. Score bounds validation (0 to 100)
9. Readiness level classification bands
10. Explainable readiness breakdown with strengths & improvements
11. Saving evaluation logs to 'readiness_evaluations'
12. Retrieving latest evaluation log
13. Teardown cleanup of test data
"""

import os
import sys

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.database import execute_query, fetch_one
from modules.readiness_engine import (
    calculate_academic_score,
    calculate_skills_score,
    calculate_projects_score,
    calculate_internships_score,
    calculate_certifications_score,
    get_readiness_level,
    calculate_readiness_score,
    get_readiness_breakdown,
    save_readiness_evaluation,
    get_latest_readiness_evaluation
)


def test_score_components_synthetic_student():
    print("Test 1: Score Component Calculations (Student ID=1)...", end=" ")
    acad = calculate_academic_score(1)
    assert 0.0 <= acad["score"] <= 35.0

    skill = calculate_skills_score(1)
    assert 0.0 <= skill["score"] <= 30.0

    proj = calculate_projects_score(1)
    assert 0.0 <= proj["score"] <= 15.0

    intern = calculate_internships_score(1)
    assert 0.0 <= intern["score"] <= 10.0

    cert = calculate_certifications_score(1)
    assert 0.0 <= cert["score"] <= 10.0
    print("PASSED")


def test_composite_readiness_and_bounds():
    print("Test 2: Composite Readiness Calculation & Bounds Check...", end=" ")
    res = calculate_readiness_score(1)
    assert res["student_id"] == 1
    assert 0.0 <= res["total_score"] <= 100.0
    assert res["readiness_level"] in ["Needs Improvement", "Developing", "Good", "Very Good", "Excellent"]
    print("PASSED")


def test_invalid_student_id():
    print("Test 3: Invalid Student ID Handling...", end=" ")
    res = calculate_readiness_score(999999)
    assert res["total_score"] == 0.0
    assert "error" in res
    print("PASSED")


def test_readiness_level_classification():
    print("Test 4: Readiness Level Classification Bands...", end=" ")
    assert get_readiness_level(95.0) == "Excellent"
    assert get_readiness_level(80.0) == "Very Good"
    assert get_readiness_level(68.0) == "Good"
    assert get_readiness_level(50.0) == "Developing"
    assert get_readiness_level(25.0) == "Needs Improvement"
    print("PASSED")


def test_readiness_breakdown():
    print("Test 5: Explainable Readiness Breakdown & Recommendations...", end=" ")
    bd = get_readiness_breakdown(1)
    assert "total_score" in bd
    assert "readiness_level" in bd
    assert "components" in bd
    assert isinstance(bd["strengths"], list)
    assert isinstance(bd["improvements"], list)
    print("PASSED")


def test_save_and_retrieve_evaluation():
    print("Test 6: Persistence in 'readiness_evaluations'...", end=" ")
    save_res = save_readiness_evaluation(student_id=1, academic_year=2026)
    assert save_res["success"] is True
    eval_id = save_res["evaluation_id"]
    assert eval_id is not None

    latest = get_latest_readiness_evaluation(1)
    assert latest is not None
    assert latest["evaluation_id"] == eval_id
    assert float(latest["overall_score"]) == save_res["overall_score"]

    # Cleanup test evaluation record
    execute_query("DELETE FROM readiness_evaluations WHERE evaluation_id = %s;", (eval_id,))
    print("PASSED")


def run_all_tests():
    print("=" * 60)
    print("Phase 7: Explainable Readiness Engine Test Suite")
    print("=" * 60)

    test_score_components_synthetic_student()
    test_composite_readiness_and_bounds()
    test_invalid_student_id()
    test_readiness_level_classification()
    test_readiness_breakdown()
    test_save_and_retrieve_evaluation()

    print("=" * 60)
    print("[ALL PASSED] Explainable Readiness Engine verified successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
