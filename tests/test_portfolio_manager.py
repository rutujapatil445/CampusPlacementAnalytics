"""
Portfolio Manager Unit & Integration Test Suite

Tests:
1. Retrieve master skills catalog
2. Retrieve skills for existing synthetic student (ID=1)
3. Add and remove student skill
4. Create, Read, Update, Delete Project
5. Create, Read, Update, Delete Internship
6. Create, Read, Update, Delete Certification
7. Portfolio summary aggregator
8. Invalid student ID & input validations
9. Automatic teardown hook cleaning up temporary test user data
"""

import os
import sys

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.database import execute_query, fetch_one
from modules.auth import register_user
from modules.student_manager import create_student, get_all_departments
from modules.portfolio_manager import (
    get_all_skills,
    search_skills,
    get_student_skills,
    add_student_skill,
    remove_student_skill,
    create_project,
    get_student_projects,
    get_project_by_id,
    update_project,
    delete_project,
    create_internship,
    get_student_internships,
    get_internship_by_id,
    update_internship,
    delete_internship,
    create_certification,
    get_student_certifications,
    get_certification_by_id,
    update_certification,
    delete_certification,
    get_student_portfolio_summary
)

TEST_USER_EMAIL = "portfolio_unit_test@campus.edu"
TEST_ROLL = "8888TEST001"


def cleanup_test_data():
    """Removes temporary test user and cascaded student portfolio data."""
    try:
        user = fetch_one("SELECT user_id FROM users WHERE email = %s;", (TEST_USER_EMAIL,))
        if user:
            execute_query("DELETE FROM users WHERE user_id = %s;", (user["user_id"],))
    except Exception as e:
        print(f"[NOTE] Test cleanup exception: {e}")


def test_master_skills_catalog():
    print("Test 1: Master Skills Catalog Retrieval...", end=" ")
    skills = get_all_skills()
    assert len(skills) >= 25, f"Expected at least 25 master skills, found {len(skills)}."
    
    prog_skills = get_all_skills(category="Programming")
    assert len(prog_skills) > 0, "Programming category skills should not be empty."

    search_res = search_skills("Python")
    assert len(search_res) > 0, "Skill search for 'Python' returned no results."
    print("PASSED")


def test_existing_student_portfolio():
    print("Test 2: Reading Existing Student Portfolio (ID=1)...", end=" ")
    skills = get_student_skills(1)
    assert isinstance(skills, list)

    projects = get_student_projects(1)
    assert isinstance(projects, list)

    summary = get_student_portfolio_summary(1)
    assert summary["student"] is not None
    assert summary["skills_count"] == len(skills)
    assert summary["projects_count"] == len(projects)
    print("PASSED")


def test_temporary_portfolio_crud_flow():
    print("Test 3: Full Portfolio CRUD Cycle on Temporary Test Student...", end=" ")
    cleanup_test_data()

    # Step A: Setup temporary student
    reg = register_user(TEST_USER_EMAIL, "TestPass123", "TestPass123")
    assert reg["success"] is True
    test_user_id = reg["user_id"]

    depts = get_all_departments()
    st_res = create_student(
        user_id=test_user_id,
        roll_number=TEST_ROLL,
        first_name="Portfolio",
        last_name="Tester",
        dept_id=depts[0]["dept_id"],
        gender="Female",
        passing_year=2026
    )
    assert st_res["success"] is True
    test_student_id = st_res["student_id"]

    # Step B: Skills CRUD
    all_skills = get_all_skills()
    test_skill_id = all_skills[0]["skill_id"]
    
    add_s = add_student_skill(test_student_id, test_skill_id, proficiency_level="Advanced")
    assert add_s["success"] is True
    st_skills = get_student_skills(test_student_id)
    assert len(st_skills) == 1 and st_skills[0]["proficiency_level"] == "Advanced"

    # Step C: Projects CRUD
    p_res = create_project(
        student_id=test_student_id,
        title="Test Portfolio Web App",
        domain="Web Development",
        description="A comprehensive web dashboard solution.",
        github_url="https://github.com/test/app",
        duration_months=2
    )
    assert p_res["success"] is True
    test_project_id = p_res["project_id"]

    p_item = get_project_by_id(test_project_id)
    assert p_item["title"] == "Test Portfolio Web App"

    up_p = update_project(test_project_id, title="Updated Web App")
    assert up_p["success"] is True
    assert get_project_by_id(test_project_id)["title"] == "Updated Web App"

    # Step D: Internships CRUD
    i_res = create_internship(
        student_id=test_student_id,
        company_name="TechNova Demo",
        role="Software Engineering Intern",
        duration_months=3,
        certificate_url="https://demo.com/cert/1"
    )
    assert i_res["success"] is True
    test_internship_id = i_res["internship_id"]

    i_item = get_internship_by_id(test_internship_id)
    assert i_item["company_name"] == "TechNova Demo"

    up_i = update_internship(test_internship_id, role="Senior Intern")
    assert up_i["success"] is True
    assert get_internship_by_id(test_internship_id)["role"] == "Senior Intern"

    # Step E: Certifications CRUD
    c_res = create_certification(
        student_id=test_student_id,
        title="Certified Cloud Architect",
        issuing_organization="AWS Academy",
        issue_date="2025-08-01"
    )
    assert c_res["success"] is True
    test_cert_id = c_res["cert_id"]

    c_item = get_certification_by_id(test_cert_id)
    assert c_item["title"] == "Certified Cloud Architect"

    up_c = update_certification(test_cert_id, title="AWS Certified Solutions Architect")
    assert up_c["success"] is True
    assert get_certification_by_id(test_cert_id)["title"] == "AWS Certified Solutions Architect"

    # Step F: Verify Portfolio Summary
    summary = get_student_portfolio_summary(test_student_id)
    assert summary["skills_count"] == 1
    assert summary["projects_count"] == 1
    assert summary["internships_count"] == 1
    assert summary["certifications_count"] == 1

    # Step G: Delete records
    assert delete_project(test_project_id)["success"] is True
    assert delete_internship(test_internship_id)["success"] is True
    assert delete_certification(test_cert_id)["success"] is True
    assert remove_student_skill(test_student_id, test_skill_id)["success"] is True

    cleanup_test_data()
    print("PASSED")


def test_portfolio_validations():
    print("Test 4: Input & Foreign Key Validations...", end=" ")
    INVALID_ID = 999999

    # Non-existent student
    s_err = add_student_skill(INVALID_ID, 1)
    assert s_err["success"] is False and "not found" in s_err["message"].lower()

    p_err = create_project(INVALID_ID, "Title")
    assert p_err["success"] is False and "not found" in p_err["message"].lower()

    i_err = create_internship(INVALID_ID, "Company", "Role", 2)
    assert i_err["success"] is False and "not found" in i_err["message"].lower()

    c_err = create_certification(INVALID_ID, "Title", "Org")
    assert c_err["success"] is False and "not found" in c_err["message"].lower()

    # Invalid project duration <= 0
    dur_err = create_project(1, "Title", duration_months=0)
    assert dur_err["success"] is False and "greater than 0" in dur_err["message"].lower()

    # Empty required fields
    title_err = create_project(1, "")
    assert title_err["success"] is False and "required" in title_err["message"].lower()

    print("PASSED")


def run_all_tests():
    print("=" * 60)
    print("Phase 6A: Student Portfolio Management Test Suite")
    print("=" * 60)

    try:
        test_master_skills_catalog()
        test_existing_student_portfolio()
        test_temporary_portfolio_crud_flow()
        test_portfolio_validations()

        print("=" * 60)
        print("[ALL PASSED] Student Portfolio Management module verified successfully!")
        print("=" * 60)

    finally:
        cleanup_test_data()


if __name__ == "__main__":
    run_all_tests()
