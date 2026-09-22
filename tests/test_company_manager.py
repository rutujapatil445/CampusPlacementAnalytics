"""
Company & Campus Drive Manager Unit & Integration Test Suite

Tests all 25 items requested for Phase 6B:
- Company CRUD & search operations
- Campus Drive CRUD & search operations
- Academic Requirements management (CGPA, SSC/HSC %, backlogs, CTC)
- Eligible Department mappings
- Required Skill mappings
- Drive details summary aggregator
- Input & Foreign key validations
- Teardown cleanup of temporary test companies/drives
"""

import os
import sys

# Ensure parent project path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.database import execute_query, fetch_one
from modules.student_manager import get_all_departments
from modules.portfolio_manager import get_all_skills
from modules.company_manager import (
    create_company,
    get_company_by_id,
    get_all_companies,
    search_companies,
    update_company,
    delete_company,
    create_drive,
    get_drive_by_id,
    get_all_drives,
    search_drives,
    update_drive,
    delete_drive,
    get_drive_requirements,
    set_drive_requirements,
    update_drive_requirements,
    get_drive_departments,
    add_drive_department,
    remove_drive_department,
    set_drive_departments,
    get_drive_skills,
    add_drive_skill,
    remove_drive_skill,
    set_drive_skills,
    get_drive_details
)

TEST_COMPANY_NAME = "Test Company Systems 99"
TEST_DRIVE_TITLE = "Test Systems Software Trainee (2026)"


def cleanup_test_data():
    """Removes temporary test company and cascaded drives."""
    try:
        comp = fetch_one("SELECT company_id FROM companies WHERE company_name = %s;", (TEST_COMPANY_NAME,))
        if comp:
            execute_query("DELETE FROM companies WHERE company_id = %s;", (comp["company_id"],))
    except Exception as e:
        print(f"[NOTE] Test cleanup exception: {e}")


def test_company_crud_and_search():
    print("Test 1-5: Company CRUD & Search Operations...", end=" ")
    cleanup_test_data()

    # 1. Create company
    c_res = create_company(TEST_COMPANY_NAME, "Software R&D", "https://testcomp99.demo", "hr@testcomp99.demo")
    assert c_res["success"] is True, f"Failed to create company: {c_res['message']}"
    comp_id = c_res["company_id"]

    # 2. Retrieve company
    comp = get_company_by_id(comp_id)
    assert comp is not None and comp["company_name"] == TEST_COMPANY_NAME

    # 3. Update company
    up_res = update_company(comp_id, industry_sector="Artificial Intelligence")
    assert up_res["success"] is True
    assert get_company_by_id(comp_id)["industry_sector"] == "Artificial Intelligence"

    # 4. Search company
    search_res = search_companies("Test Company Systems")
    assert len(search_res) > 0 and search_res[0]["company_id"] == comp_id

    # 5. Existing companies check (No corruption of sample companies)
    all_comps = get_all_companies()
    assert len(all_comps) >= 12, f"Expected at least 12 sample companies, found {len(all_comps)}."

    print("PASSED")
    return comp_id


def test_campus_drive_crud_and_search(comp_id):
    print("Test 6-10: Campus Drive CRUD & Search Operations...", end=" ")

    # 6. Create drive
    d_res = create_drive(comp_id, TEST_DRIVE_TITLE, 2026, "2026-10-15", status="Upcoming")
    assert d_res["success"] is True, f"Failed to create drive: {d_res['message']}"
    drive_id = d_res["drive_id"]

    # 7. Retrieve drive
    drive = get_drive_by_id(drive_id)
    assert drive is not None and drive["job_title"] == TEST_DRIVE_TITLE
    assert drive["company_name"] == TEST_COMPANY_NAME

    # 8. Update drive
    up_d = update_drive(drive_id, status="Ongoing", job_title="Senior Software Trainee (2026)")
    assert up_d["success"] is True
    assert get_drive_by_id(drive_id)["status"] == "Ongoing"

    # 9. Search/filter drives
    s_drives = search_drives("Senior Software Trainee")
    assert len(s_drives) > 0 and s_drives[0]["drive_id"] == drive_id

    # 10. Existing drives check
    all_d = get_all_drives()
    assert len(all_d) >= 15, f"Expected at least 15 sample drives, found {len(all_d)}."

    print("PASSED")
    return drive_id


def test_drive_requirements(drive_id):
    print("Test 11-13: Drive Requirements Management...", end=" ")

    # 11. Create/Set requirements
    r_res = set_drive_requirements(
        drive_id=drive_id,
        min_cgpa=7.00,
        min_ssc_pct=65.00,
        min_hsc_pct=65.00,
        max_active_backlogs=0,
        max_gap_years=1,
        ctc_lpa=12.50
    )
    assert r_res["success"] is True, f"Failed to set requirements: {r_res['message']}"

    # 12. Retrieve requirements
    reqs = get_drive_requirements(drive_id)
    assert reqs is not None
    assert float(reqs["min_cgpa"]) == 7.00
    assert float(reqs["ctc_lpa"]) == 12.50

    # 13. Update requirements
    up_r = update_drive_requirements(drive_id, ctc_lpa=14.00, min_cgpa=7.50)
    assert up_r["success"] is True
    updated_req = get_drive_requirements(drive_id)
    assert float(updated_req["ctc_lpa"]) == 14.00
    assert float(updated_req["min_cgpa"]) == 7.50

    print("PASSED")


def test_drive_department_mappings(drive_id):
    print("Test 14-16: Drive Department Mappings...", end=" ")
    depts = get_all_departments()
    dept1 = depts[0]["dept_id"]
    dept2 = depts[1]["dept_id"]

    # 14. Add department to drive
    a_dept1 = add_drive_department(drive_id, dept1)
    assert a_dept1["success"] is True
    a_dept2 = add_drive_department(drive_id, dept2)
    assert a_dept2["success"] is True

    # 15. Retrieve drive departments
    d_depts = get_drive_departments(drive_id)
    assert len(d_depts) == 2

    # 16. Remove department from drive
    r_dept = remove_drive_department(drive_id, dept1)
    assert r_dept["success"] is True
    assert len(get_drive_departments(drive_id)) == 1

    print("PASSED")


def test_drive_skill_mappings(drive_id):
    print("Test 17-19: Drive Skill Mappings...", end=" ")
    skills = get_all_skills()
    s1 = skills[0]["skill_id"]
    s2 = skills[1]["skill_id"]

    # 17. Add required skill
    a_s1 = add_drive_skill(drive_id, s1, min_proficiency="Advanced", is_mandatory=True)
    assert a_s1["success"] is True
    a_s2 = add_drive_skill(drive_id, s2, min_proficiency="Intermediate", is_mandatory=False)
    assert a_s2["success"] is True

    # 18. Retrieve drive skills
    d_skills = get_drive_skills(drive_id)
    assert len(d_skills) == 2

    # 19. Remove required skill
    r_skill = remove_drive_skill(drive_id, s1)
    assert r_skill["success"] is True
    assert len(get_drive_skills(drive_id)) == 1

    # Aggregator check (Test 7)
    details = get_drive_details(drive_id)
    assert details["drive"] is not None
    assert details["requirements"] is not None
    assert len(details["departments"]) == 1
    assert len(details["skills"]) == 1

    print("PASSED")


def test_validations_and_edge_cases(comp_id, drive_id):
    print("Test 20-25: Validations & Invalid ID Edge Cases...", end=" ")
    INVALID_ID = 999999

    # 20. Invalid company ID
    assert get_company_by_id(INVALID_ID) is None
    assert create_drive(INVALID_ID, "Job", 2026, "2026-10-01")["success"] is False

    # 21. Invalid drive ID
    assert get_drive_by_id(INVALID_ID) is None
    assert set_drive_requirements(INVALID_ID)["success"] is False

    # 22. Invalid department ID
    assert add_drive_department(drive_id, INVALID_ID)["success"] is False

    # 23. Invalid skill ID
    assert add_drive_skill(drive_id, INVALID_ID)["success"] is False

    # 24. Duplicate mapping validation
    depts = get_all_departments()
    valid_dept_id = depts[1]["dept_id"] # dept2 is currently added
    dup_dept = add_drive_department(drive_id, valid_dept_id)
    assert dup_dept["success"] is False and "already eligible" in dup_dept["message"].lower()

    # 25. Required field validation & negative checks
    empty_comp = create_company("")
    assert empty_comp["success"] is False and "required" in empty_comp["message"].lower()

    invalid_cgpa = set_drive_requirements(drive_id, min_cgpa=12.0)
    assert invalid_cgpa["success"] is False and "cgpa" in invalid_cgpa["message"].lower()

    invalid_ctc = set_drive_requirements(drive_id, ctc_lpa=0.0)
    assert invalid_ctc["success"] is False and "ctc" in invalid_ctc["message"].lower()

    print("PASSED")


def run_all_tests():
    print("=" * 60)
    print("Phase 6B: Company & Campus Drive Management Test Suite")
    print("=" * 60)

    comp_id = None
    drive_id = None

    try:
        comp_id = test_company_crud_and_search()
        drive_id = test_campus_drive_crud_and_search(comp_id)
        test_drive_requirements(drive_id)
        test_drive_department_mappings(drive_id)
        test_drive_skill_mappings(drive_id)
        test_validations_and_edge_cases(comp_id, drive_id)

        # Clean up temporary test records (Test 5 & 10)
        assert delete_drive(drive_id)["success"] is True
        assert delete_company(comp_id)["success"] is True
        print("Cleanup: Temporary drive and company deleted successfully.")

        print("=" * 60)
        print("[ALL PASSED] Company & Campus Drive Management module verified successfully!")
        print("=" * 60)

    finally:
        cleanup_test_data()


if __name__ == "__main__":
    run_all_tests()
