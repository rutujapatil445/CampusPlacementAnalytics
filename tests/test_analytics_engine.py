"""
Placement Analytics Engine Unit & Integration Test Suite

Tests:
1. Overall institutional placement statistics
2. Department-wise placement rate & CTC metrics
3. Company recruiter hiring statistics
4. Drive application funnel statistics
5. Compensation package distribution (Average, Min, Max, Median)
6. Skill supply vs demand frequency statistics
7. Readiness band vs placement outcome analysis
8. Invalid drive ID edge case handling
"""

import os
import sys

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.analytics_engine import (
    get_overall_placement_stats,
    get_department_placement_stats,
    get_company_placement_stats,
    get_drive_application_stats,
    get_package_statistics,
    get_skill_demand_stats,
    get_readiness_placement_analysis
)


def test_overall_placement_stats():
    print("Test 1: Overall Institutional Placement Stats...", end=" ")
    stats = get_overall_placement_stats()
    assert isinstance(stats, dict)
    assert stats["total_students"] >= 150
    assert stats["total_companies"] >= 12
    assert stats["total_drives"] >= 15
    assert 0.0 <= stats["placement_percentage"] <= 100.0
    assert stats["average_ctc_lpa"] > 0.0
    print("PASSED")


def test_department_placement_stats():
    print("Test 2: Department-wise Placement Analytics...", end=" ")
    dept_stats = get_department_placement_stats()
    assert isinstance(dept_stats, list)
    assert len(dept_stats) >= 6
    assert "dept_name" in dept_stats[0]
    assert "placement_percentage" in dept_stats[0]
    print("PASSED")


def test_company_placement_stats():
    print("Test 3: Company-wise Recruiter Statistics...", end=" ")
    comp_stats = get_company_placement_stats()
    assert isinstance(comp_stats, list)
    assert len(comp_stats) >= 12
    assert "company_name" in comp_stats[0]
    print("PASSED")


def test_drive_application_stats():
    print("Test 4: Drive Application Funnel Statistics...", end=" ")
    drive_stats = get_drive_application_stats(drive_id=1)
    assert isinstance(drive_stats, dict)
    assert "total_applicants" in drive_stats
    assert "status_breakdown" in drive_stats

    # Invalid drive check
    inv_stats = get_drive_application_stats(drive_id=999999)
    assert "error" in inv_stats
    print("PASSED")


def test_package_statistics():
    print("Test 5: Compensation Package Distribution...", end=" ")
    pkg = get_package_statistics()
    assert isinstance(pkg, dict)
    assert pkg["total_offers"] > 0
    assert pkg["lowest_ctc"] <= pkg["average_ctc"] <= pkg["highest_ctc"]
    assert pkg["lowest_ctc"] <= pkg["median_ctc"] <= pkg["highest_ctc"]
    print("PASSED")


def test_skill_demand_stats():
    print("Test 6: Skill Supply vs Demand Frequency Stats...", end=" ")
    skills_stat = get_skill_demand_stats()
    assert isinstance(skills_stat, list)
    assert len(skills_stat) >= 25
    assert "student_count" in skills_stat[0]
    assert "drive_count" in skills_stat[0]
    print("PASSED")


def test_readiness_placement_analysis():
    print("Test 7: Readiness Band vs Placement Outcome Analysis...", end=" ")
    readiness_stats = get_readiness_placement_analysis()
    assert isinstance(readiness_stats, list)
    print("PASSED")


def run_all_tests():
    print("=" * 60)
    print("Phase 7: Placement Analytics Engine Test Suite")
    print("=" * 60)

    test_overall_placement_stats()
    test_department_placement_stats()
    test_company_placement_stats()
    test_drive_application_stats()
    test_package_statistics()
    test_skill_demand_stats()
    test_readiness_placement_analysis()

    print("=" * 60)
    print("[ALL PASSED] Placement Analytics Engine verified successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
