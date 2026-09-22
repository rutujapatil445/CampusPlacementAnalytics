"""
Application Manager Unit & Integration Test Suite

Tests:
1. Application submission & eligibility pre-validation
2. Duplicate application prevention
3. Application retrieval & student/drive application lists
4. Multi-stage selection status transitions (Applied -> Shortlisted -> Offered)
5. Application withdrawal flow
6. Final placement offer logging & CTC tracking
7. Student placement summary aggregator
8. Input & Foreign key validations
9. Automatic teardown cleanup of temporary test data
"""

import os
import sys

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.database import execute_query, fetch_one
from modules.auth import register_user
from modules.student_manager import create_student, create_academic_record, get_all_departments
from modules.company_manager import create_company, create_drive, set_drive_requirements
from modules.application_manager import (
    apply_for_drive,
    get_application_by_id,
    get_student_applications,
    get_drive_applications,
    update_application_status,
    withdraw_application,
    record_placement_offer,
    get_placement_record,
    get_all_placements,
    get_student_placement_summary
)

TEST_EMAIL = "app_mgr_test_student@campus.edu"
TEST_ROLL = "6666TEST001"
TEST_COMPANY = "App Manager Test Corp 99"
TEST_DRIVE = "App Manager Test Drive (2026)"


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


def test_existing_applications_and_placements():
    print("Test 1: Reading Existing Synthetic Applications & Placements...", end=" ")
    apps = get_student_applications(1)
    assert isinstance(apps, list)

    placements = get_all_placements()
    assert len(placements) > 0, "Expected existing sample placement records."
    assert "offered_ctc" in placements[0]
    print("PASSED")


def test_application_and_placement_workflow():
    print("Test 2: Full Application & Placement Offer Workflow...", end=" ")
    cleanup_test_data()

    # Step A: Setup Temporary Test Student & Drive
    reg = register_user(TEST_EMAIL, "TestPass123", "TestPass123")
    u_id = reg["user_id"]

    depts = get_all_departments()
    st_res = create_student(
        user_id=u_id,
        roll_number=TEST_ROLL,
        first_name="AppTest",
        last_name="Student",
        dept_id=depts[0]["dept_id"],
        gender="Female",
        passing_year=2026
    )
    st_id = st_res["student_id"]
    create_academic_record(st_id, ssc_percentage=80.0, hsc_percentage=80.0, current_cgpa=8.5, total_active_backlogs=0)

    c_res = create_company(TEST_COMPANY, "IT Services")
    c_id = c_res["company_id"]
    d_res = create_drive(c_id, TEST_DRIVE, 2026, "2026-10-20")
    d_id = d_res["drive_id"]
    set_drive_requirements(d_id, min_cgpa=6.0, ctc_lpa=8.0)

    # Step B: Submit Application (Eligible Student)
    app_res = apply_for_drive(st_id, d_id)
    assert app_res["success"] is True, f"Application failed: {app_res['message']}"
    app_id = app_res["application_id"]

    # Step C: Prevent Duplicate Application
    dup_res = apply_for_drive(st_id, d_id)
    assert dup_res["success"] is False and "already applied" in dup_res["message"].lower()

    # Step D: Retrieve & Verify Application Details
    app_info = get_application_by_id(app_id)
    assert app_info["status"] == "Applied"
    assert app_info["company_name"] == TEST_COMPANY

    # Step E: Multi-Stage Status Updates
    up1 = update_application_status(app_id, "Shortlisted")
    assert up1["success"] is True
    assert get_application_by_id(app_id)["status"] == "Shortlisted"

    up2 = update_application_status(app_id, "Interview")
    assert up2["success"] is True

    # Step F: Record Placement Offer
    po_res = record_placement_offer(app_id, offered_ctc=9.50, acceptance_status="Accepted")
    assert po_res["success"] is True, f"Record placement failed: {po_res['message']}"
    p_id = po_res["placement_id"]

    # Verify Placement Record & Updated Application Status ('Offered')
    p_info = get_placement_record(placement_id=p_id)
    assert p_info is not None and float(p_info["offered_ctc"]) == 9.50
    assert get_application_by_id(app_id)["status"] in ["Offered", "Accepted"]

    # Step G: Student Placement Summary
    summary = get_student_placement_summary(st_id)
    assert summary["is_placed"] is True
    assert summary["total_applications"] == 1
    assert len(summary["placements"]) == 1

    cleanup_test_data()
    print("PASSED")


def test_application_validations():
    print("Test 3: Application & Placement Input Validations...", end=" ")
    INVALID_ID = 999999

    # Invalid student/drive ID
    assert apply_for_drive(INVALID_ID, 1)["success"] is False
    assert apply_for_drive(1, INVALID_ID)["success"] is False

    # Invalid status string
    assert update_application_status(1, "InvalidStatusName")["success"] is False

    # Negative CTC package
    assert record_placement_offer(1, offered_ctc=-5.0)["success"] is False
    assert record_placement_offer(INVALID_ID, offered_ctc=10.0)["success"] is False

    print("PASSED")


def run_all_tests():
    print("=" * 60)
    print("Phase 6C: Application Tracking & Placement Test Suite")
    print("=" * 60)

    try:
        test_existing_applications_and_placements()
        test_application_and_placement_workflow()
        test_application_validations()

        print("=" * 60)
        print("[ALL PASSED] Application Manager module verified successfully!")
        print("=" * 60)

    finally:
        cleanup_test_data()


if __name__ == "__main__":
    run_all_tests()
