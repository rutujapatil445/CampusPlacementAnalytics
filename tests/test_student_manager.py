"""
Student Manager Unit & Integration Test Suite

Tests:
1. Department retrieval
2. Fetching existing synthetic student details (student_id = 1)
3. Searching student records
4. Reading academic record and semester records
5. Academic summary aggregation
6. Full student & academic record CRUD flow using a temporary test record
7. Input validations (invalid CGPA, percentages > 100, invalid semester numbers)
8. Automatic database cleanup of temporary test data
"""

import os
import sys

# Add parent project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.database import execute_query, fetch_one
from modules.auth import register_user
from modules.student_manager import (
    get_all_departments,
    create_student,
    get_student_by_id,
    get_student_by_user_id,
    get_all_students,
    update_student,
    delete_student,
    search_students,
    get_academic_record,
    create_academic_record,
    update_academic_record,
    get_semester_records,
    add_semester_record,
    update_semester_record,
    get_student_academic_summary
)

TEST_USER_EMAIL = "student_mgr_test@campus.edu"
TEST_ROLL = "9999TEST001"


def cleanup_test_data():
    """Removes test user and cascaded student profile data."""
    try:
        user = fetch_one("SELECT user_id FROM users WHERE email = %s;", (TEST_USER_EMAIL,))
        if user:
            execute_query("DELETE FROM users WHERE user_id = %s;", (user["user_id"],))
    except Exception as e:
        print(f"[NOTE] Test cleanup exception: {e}")


def test_department_retrieval():
    print("Test 1: Department Retrieval...", end=" ")
    depts = get_all_departments()
    assert len(depts) >= 6, f"Expected at least 6 departments, found {len(depts)}."
    assert "dept_name" in depts[0] and "dept_code" in depts[0]
    print("PASSED")


def test_existing_student_queries():
    print("Test 2: Reading Existing Synthetic Student (ID=1)...", end=" ")
    student = get_student_by_id(1)
    assert student is not None, "Student ID 1 should exist in synthetic dataset."
    assert "dept_name" in student and "email" in student

    all_students = get_all_students()
    assert len(all_students) >= 150, f"Expected 150 students, found {len(all_students)}."

    search_res = search_students("2022COMP")
    assert len(search_res) > 0, "Search by roll number prefix returned no results."
    print("PASSED")


def test_existing_academic_and_semester_records():
    print("Test 3: Reading Academic & Semester Records (ID=1)...", end=" ")
    academic = get_academic_record(1)
    assert academic is not None, "Academic record for student ID 1 missing."
    assert 0.0 <= float(academic["current_cgpa"]) <= 10.0

    semesters = get_semester_records(1)
    assert len(semesters) > 0, "Semester records for student ID 1 missing."
    assert semesters[0]["semester_number"] == 1

    summary = get_student_academic_summary(1)
    assert summary["student"] is not None
    assert summary["academic_record"] is not None
    assert summary["semester_count"] == len(semesters)
    print("PASSED")


def test_temporary_student_crud_and_academics():
    print("Test 4: Temporary Student & Academic CRUD Flow...", end=" ")
    cleanup_test_data()

    # Step A: Register User
    reg = register_user(TEST_USER_EMAIL, "TestPass123", "TestPass123")
    assert reg["success"] is True
    test_user_id = reg["user_id"]

    # Step B: Create Student Profile
    depts = get_all_departments()
    test_dept_id = depts[0]["dept_id"]
    create_res = create_student(
        user_id=test_user_id,
        roll_number=TEST_ROLL,
        first_name="Unit",
        last_name="Tester",
        dept_id=test_dept_id,
        gender="Male",
        passing_year=2026,
        phone="9998887770"
    )
    assert create_res["success"] is True, f"Failed to create student: {create_res['message']}"
    test_student_id = create_res["student_id"]

    # Step C: Update Student Profile
    up_res = update_student(test_student_id, first_name="UpdatedUnit")
    assert up_res["success"] is True
    updated_student = get_student_by_id(test_student_id)
    assert updated_student["first_name"] == "UpdatedUnit"

    # Step D: Create Academic Record
    acad_res = create_academic_record(
        student_id=test_student_id,
        ssc_percentage=85.5,
        hsc_percentage=82.0,
        current_cgpa=8.45,
        total_active_backlogs=0,
        gap_years=0
    )
    assert acad_res["success"] is True

    # Step E: Add Semester Record
    sem_res = add_semester_record(
        student_id=test_student_id,
        semester_number=1,
        sgpa=8.2,
        cgpa=8.2,
        active_backlogs=0
    )
    assert sem_res["success"] is True

    # Step F: Delete Student Profile
    del_res = delete_student(test_student_id)
    assert del_res["success"] is True
    assert get_student_by_id(test_student_id) is None

    cleanup_test_data()
    print("PASSED")


def test_academic_validations():
    print("Test 5: Academic & Semester Validations...", end=" ")
    
    # Invalid CGPA > 10
    acad_err1 = create_academic_record(student_id=99999, ssc_percentage=80.0, current_cgpa=11.5)
    assert acad_err1["success"] is False and "cgpa" in acad_err1["message"].lower()

    # Invalid SSC Percentage > 100
    acad_err2 = create_academic_record(student_id=99999, ssc_percentage=105.0, current_cgpa=8.0)
    assert acad_err2["success"] is False and "ssc" in acad_err2["message"].lower()

    # Invalid Semester Number > 8
    sem_err1 = add_semester_record(student_id=99999, semester_number=9, sgpa=8.0, cgpa=8.0)
    assert sem_err1["success"] is False and "semester number" in sem_err1["message"].lower()
    print("PASSED")


def run_all_tests():
    print("=" * 60)
    print("Phase 5: Student Profile & Academic Management Test Suite")
    print("=" * 60)

    try:
        test_department_retrieval()
        test_existing_student_queries()
        test_existing_academic_and_semester_records()
        test_temporary_student_crud_and_academics()
        test_academic_validations()

        print("=" * 60)
        print("[ALL PASSED] Student & Academic Management module verified successfully!")
        print("=" * 60)

    finally:
        cleanup_test_data()


if __name__ == "__main__":
    run_all_tests()
