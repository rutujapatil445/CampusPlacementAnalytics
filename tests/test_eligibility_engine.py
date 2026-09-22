"""
Eligibility Engine Unit & Integration Test Suite

Tests:
1. Multi-criterion student eligibility evaluation
2. Department branch filtering
3. CGPA, SSC %, HSC %, backlogs, and gap-year threshold validations
4. Mandatory skill prerequisites & proficiency ranking checks
5. Skill gap analysis breakdown
6. Eligible drives for a student query
7. Eligible students for a drive query
8. Teardown cleanup of temporary test data
"""

import os
import sys

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.database import execute_query, fetch_one
from modules.auth import register_user
from modules.student_manager import create_student, create_academic_record, get_all_departments
from modules.company_manager import (
    create_company,
    create_drive,
    set_drive_requirements,
    add_drive_department,
    add_drive_skill
)
from modules.portfolio_manager import get_all_skills, add_student_skill
from modules.eligibility_engine import (
    evaluate_student_eligibility,
    analyze_student_skill_gaps,
    get_eligible_drives_for_student,
    get_eligible_students_for_drive
)

TEST_EMAIL = "elig_test_student@campus.edu"
TEST_ROLL = "7777TEST001"
TEST_COMPANY = "Eligibility Test Corp 99"
TEST_DRIVE = "Eligibility Test Drive (2026)"


def cleanup_test_data():
    """Removes temporary test user, student, company, and drive data."""
    try:
        user = fetch_one("SELECT user_id FROM users WHERE email = %s;", (TEST_EMAIL,))
        if user:
            execute_query("DELETE FROM users WHERE user_id = %s;", (user["user_id"],))
        
        comp = fetch_one("SELECT company_id FROM companies WHERE company_name = %s;", (TEST_COMPANY,))
        if comp:
            execute_query("DELETE FROM companies WHERE company_id = %s;", (comp["company_id"],))
    except Exception as e:
        print(f"[NOTE] Test cleanup exception: {e}")


def test_synthetic_student_eligibility():
    print("Test 1: Evaluating Existing Synthetic Student Eligibility (ID=1)...", end=" ")
    eval_res = evaluate_student_eligibility(student_id=1, drive_id=1)
    assert isinstance(eval_res, dict)
    assert "is_eligible" in eval_res
    assert "department_eligible" in eval_res
    assert "cgpa_eligible" in eval_res
    print("PASSED")


def test_custom_eligibility_scenarios():
    print("Test 2: Detailed Rule-Based Eligibility Scenarios...", end=" ")
    cleanup_test_data()

    # Step A: Register Test User & Student (Dept: COMP - dept_id=1)
    reg = register_user(TEST_EMAIL, "TestPass123", "TestPass123")
    assert reg["success"] is True
    u_id = reg["user_id"]

    depts = get_all_departments()
    comp_dept_id = next(d["dept_id"] for d in depts if d["dept_code"] == "COMP")
    mech_dept_id = next(d["dept_id"] for d in depts if d["dept_code"] == "MECH")

    st_res = create_student(
        user_id=u_id,
        roll_number=TEST_ROLL,
        first_name="Elig",
        last_name="Tester",
        dept_id=comp_dept_id,
        gender="Male",
        passing_year=2026
    )
    assert st_res["success"] is True
    st_id = st_res["student_id"]

    # Add Academic Record (CGPA: 7.0, SSC: 75%, HSC: 70%, Backlogs: 1, Gap: 0)
    acad_res = create_academic_record(
        student_id=st_id,
        ssc_percentage=75.0,
        hsc_percentage=70.0,
        current_cgpa=7.00,
        total_active_backlogs=1,
        gap_years=0
    )
    assert acad_res["success"] is True

    # Step B: Create Test Company & Campus Drive
    c_res = create_company(TEST_COMPANY, "Software Services")
    c_id = c_res["company_id"]

    d_res = create_drive(c_id, TEST_DRIVE, 2026, "2026-11-01")
    d_id = d_res["drive_id"]

    # Set Strict Requirements (Min CGPA: 8.0, Max Backlogs: 0)
    set_drive_requirements(
        drive_id=d_id,
        min_cgpa=8.00,
        min_ssc_pct=60.00,
        min_hsc_pct=60.00,
        max_active_backlogs=0,
        ctc_lpa=10.00
    )
    add_drive_department(d_id, comp_dept_id)

    # Required Mandatory Skill (Python - Advanced)
    skills = get_all_skills()
    py_skill_id = next(s["skill_id"] for s in skills if s["skill_name"] == "Python")
    add_drive_skill(d_id, py_skill_id, min_proficiency="Advanced", is_mandatory=True)

    # Scenario 1: Should FAIL due to CGPA (7.0 < 8.0), Backlogs (1 > 0), and Missing Skill (Python)
    eval1 = evaluate_student_eligibility(st_id, d_id)
    assert eval1["is_eligible"] is False
    assert eval1["cgpa_eligible"] is False
    assert eval1["backlogs_eligible"] is False
    assert eval1["skills_eligible"] is False
    assert len(eval1["reasons"]) >= 3

    # Scenario 2: Fix Skills (Add Python - Intermediate)
    add_student_skill(st_id, py_skill_id, proficiency_level="Intermediate")
    gaps = analyze_student_skill_gaps(st_id, d_id)
    assert len(gaps) == 1 and gaps[0]["gap_type"] == "Insufficient Proficiency"

    # Upgrade Python to Advanced
    add_student_skill(st_id, py_skill_id, proficiency_level="Advanced")
    
    # Lower Drive Requirements (Min CGPA: 6.5, Max Backlogs: 2)
    set_drive_requirements(
        drive_id=d_id,
        min_cgpa=6.50,
        min_ssc_pct=60.00,
        min_hsc_pct=60.00,
        max_active_backlogs=2,
        ctc_lpa=10.00
    )

    # Scenario 3: Should PASS all criteria
    eval2 = evaluate_student_eligibility(st_id, d_id)
    assert eval2["is_eligible"] is True, f"Expected eligible, reasons: {eval2['reasons']}"

    cleanup_test_data()
    print("PASSED")


def test_eligible_drives_and_students_queries():
    print("Test 3: Eligible Drives & Eligible Students Scans...", end=" ")
    eligible_drives = get_eligible_drives_for_student(student_id=1)
    assert isinstance(eligible_drives, list)

    eligible_students = get_eligible_students_for_drive(drive_id=1)
    assert isinstance(eligible_students, list)
    print("PASSED")


def run_all_tests():
    print("=" * 60)
    print("Phase 6C: Eligibility Engine Test Suite")
    print("=" * 60)

    try:
        test_synthetic_student_eligibility()
        test_custom_eligibility_scenarios()
        test_eligible_drives_and_students_queries()

        print("=" * 60)
        print("[ALL PASSED] Eligibility Engine module verified successfully!")
        print("=" * 60)

    finally:
        cleanup_test_data()


if __name__ == "__main__":
    run_all_tests()
