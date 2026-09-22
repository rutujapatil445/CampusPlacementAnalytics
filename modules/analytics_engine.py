"""
Placement Analytics Engine Module

Provides descriptive SQL/Python analytics:
1. Macro Placement Overview (Total Students, Placed %, Average & Highest CTC)
2. Department-wise Placement & Performance Breakdown
3. Recruiter Company Hiring Statistics
4. Drive Application Pipeline Metrics
5. Salary / Compensation Package Distribution (Average, Min, Max, Median)
6. Skill Supply vs Market Demand Frequency Analysis
7. Readiness Score vs Placement Outcome Analysis
"""

from config.database import fetch_one, fetch_all


def get_overall_placement_stats() -> dict:
    """
    Computes macro placement metrics across the institution.
    """
    # Total students count
    st_count = fetch_one("SELECT COUNT(*) AS cnt FROM students;").get("cnt", 0)

    # Total placed students (distinct student_id with Accepted or Pending placement)
    placed_query = "SELECT COUNT(DISTINCT student_id) AS cnt FROM placements WHERE acceptance_status IN ('Accepted', 'Pending');"
    placed_count = fetch_one(placed_query).get("cnt", 0)

    # Company, drive & application metrics
    comp_count = fetch_one("SELECT COUNT(*) AS cnt FROM companies;").get("cnt", 0)
    drive_count = fetch_one("SELECT COUNT(*) AS cnt FROM campus_drives;").get("cnt", 0)
    app_count = fetch_one("SELECT COUNT(*) AS cnt FROM applications;").get("cnt", 0)

    # CTC statistics
    ctc_stats = fetch_one("SELECT AVG(offered_ctc) AS avg_ctc, MAX(offered_ctc) AS max_ctc FROM placements;")
    avg_ctc = round(float(ctc_stats["avg_ctc"]), 2) if ctc_stats and ctc_stats["avg_ctc"] else 0.0
    max_ctc = round(float(ctc_stats["max_ctc"]), 2) if ctc_stats and ctc_stats["max_ctc"] else 0.0

    placement_pct = round((placed_count / st_count) * 100.0, 2) if st_count > 0 else 0.0

    return {
        "total_students": st_count,
        "placed_students": placed_count,
        "unplaced_students": max(0, st_count - placed_count),
        "placement_percentage": placement_pct,
        "total_companies": comp_count,
        "total_drives": drive_count,
        "total_applications": app_count,
        "average_ctc_lpa": avg_ctc,
        "highest_ctc_lpa": max_ctc
    }


def get_department_placement_stats() -> list:
    """
    Computes placement rate, CGPA, and CTC stats grouped by Department.
    """
    sql = """
        SELECT 
            d.dept_id,
            d.dept_name,
            d.dept_code,
            COUNT(DISTINCT s.student_id) AS total_students,
            COUNT(DISTINCT p.student_id) AS placed_students,
            ROUND(AVG(ar.current_cgpa), 2) AS avg_cgpa,
            ROUND(AVG(p.offered_ctc), 2) AS avg_ctc,
            ROUND(MAX(p.offered_ctc), 2) AS max_ctc
        FROM departments d
        LEFT JOIN students s ON d.dept_id = s.dept_id
        LEFT JOIN academic_records ar ON s.student_id = ar.student_id
        LEFT JOIN placements p ON s.student_id = p.student_id AND p.acceptance_status IN ('Accepted', 'Pending')
        GROUP BY d.dept_id, d.dept_name, d.dept_code
        ORDER BY d.dept_id ASC;
    """
    results = fetch_all(sql)
    for r in results:
        tot = r["total_students"]
        placed = r["placed_students"]
        r["placement_percentage"] = round((placed / tot) * 100.0, 2) if tot > 0 else 0.0
        r["avg_cgpa"] = float(r["avg_cgpa"]) if r["avg_cgpa"] is not None else 0.0
        r["avg_ctc"] = float(r["avg_ctc"]) if r["avg_ctc"] is not None else 0.0
        r["max_ctc"] = float(r["max_ctc"]) if r["max_ctc"] is not None else 0.0

    return results


def get_company_placement_stats() -> list:
    """
    Computes drive volume, application count, and hiring outcome per company.
    """
    sql = """
        SELECT 
            c.company_id,
            c.company_name,
            c.industry_sector,
            COUNT(DISTINCT cd.drive_id) AS total_drives,
            COUNT(DISTINCT a.application_id) AS total_applications,
            COUNT(DISTINCT p.placement_id) AS total_offers,
            ROUND(AVG(p.offered_ctc), 2) AS avg_ctc,
            ROUND(MAX(p.offered_ctc), 2) AS max_ctc
        FROM companies c
        LEFT JOIN campus_drives cd ON c.company_id = cd.company_id
        LEFT JOIN applications a ON cd.drive_id = a.drive_id
        LEFT JOIN placements p ON cd.drive_id = p.drive_id
        GROUP BY c.company_id, c.company_name, c.industry_sector
        ORDER BY total_offers DESC, company_name ASC;
    """
    results = fetch_all(sql)
    for r in results:
        r["avg_ctc"] = float(r["avg_ctc"]) if r["avg_ctc"] is not None else 0.0
        r["max_ctc"] = float(r["max_ctc"]) if r["max_ctc"] is not None else 0.0
    return results


def get_drive_application_stats(drive_id: int) -> dict:
    """
    Computes application funnel metrics for a single campus drive.
    """
    drive_sql = """
        SELECT cd.drive_id, cd.job_title, cd.academic_year, c.company_name 
        FROM campus_drives cd 
        JOIN companies c ON cd.company_id = c.company_id 
        WHERE cd.drive_id = %s;
    """
    drive_info = fetch_one(drive_sql, (drive_id,))
    if not drive_info:
        return {"error": "Drive not found."}

    apps = fetch_all("SELECT status FROM applications WHERE drive_id = %s;", (drive_id,))
    
    status_counts = {}
    for a in apps:
        st = a["status"]
        status_counts[st] = status_counts.get(st, 0) + 1

    placements_count = fetch_one("SELECT COUNT(*) AS cnt FROM placements WHERE drive_id = %s;", (drive_id,)).get("cnt", 0)

    return {
        "drive_id": drive_id,
        "job_title": drive_info["job_title"],
        "company_name": drive_info["company_name"],
        "total_applicants": len(apps),
        "status_breakdown": status_counts,
        "total_placed": placements_count
    }


def get_package_statistics() -> dict:
    """
    Calculates salary/compensation distribution statistics across all placements.
    """
    sql = """
        SELECT 
            COUNT(*) AS total_offers,
            ROUND(AVG(offered_ctc), 2) AS average_ctc,
            ROUND(MIN(offered_ctc), 2) AS lowest_ctc,
            ROUND(MAX(offered_ctc), 2) AS highest_ctc
        FROM placements;
    """
    res = fetch_one(sql)
    if not res or not res["total_offers"]:
        return {
            "total_offers": 0,
            "average_ctc": 0.0,
            "lowest_ctc": 0.0,
            "highest_ctc": 0.0,
            "median_ctc": 0.0
        }

    # Compute Median CTC
    ctcs = fetch_all("SELECT offered_ctc FROM placements ORDER BY offered_ctc ASC;")
    ctc_list = [float(item["offered_ctc"]) for item in ctcs]
    n = len(ctc_list)
    if n % 2 == 1:
        median_ctc = ctc_list[n // 2]
    else:
        median_ctc = (ctc_list[n // 2 - 1] + ctc_list[n // 2]) / 2.0

    return {
        "total_offers": res["total_offers"],
        "average_ctc": float(res["average_ctc"]),
        "lowest_ctc": float(res["lowest_ctc"]),
        "highest_ctc": float(res["highest_ctc"]),
        "median_ctc": round(median_ctc, 2)
    }


def get_skill_demand_stats() -> list:
    """
    Computes skill supply (student proficiency) vs market demand (campus drive requirements).
    """
    sql = """
        SELECT 
            s.skill_id,
            s.skill_name,
            s.skill_category,
            COUNT(DISTINCT ss.student_id) AS student_count,
            COUNT(DISTINCT ds.drive_id) AS drive_count
        FROM skills s
        LEFT JOIN student_skills ss ON s.skill_id = ss.skill_id
        LEFT JOIN drive_skills ds ON s.skill_id = ds.skill_id
        GROUP BY s.skill_id, s.skill_name, s.skill_category
        ORDER BY drive_count DESC, student_count DESC;
    """
    return fetch_all(sql)


def get_readiness_placement_analysis() -> list:
    """
    Descriptive analysis comparing saved readiness score evaluation bands against placement outcomes.
    """
    sql = """
        SELECT 
            CASE 
                WHEN re.overall_score >= 90.0 THEN '90-100 (Excellent)'
                WHEN re.overall_score >= 75.0 THEN '75-89 (Very Good)'
                WHEN re.overall_score >= 60.0 THEN '60-74 (Good)'
                WHEN re.overall_score >= 40.0 THEN '40-59 (Developing)'
                ELSE '0-39 (Needs Improvement)'
            END AS readiness_band,
            COUNT(DISTINCT s.student_id) AS total_students,
            COUNT(DISTINCT p.student_id) AS placed_students
        FROM students s
        LEFT JOIN (
            SELECT student_id, overall_score 
            FROM readiness_evaluations 
            WHERE (student_id, evaluation_id) IN (
                SELECT student_id, MAX(evaluation_id) 
                FROM readiness_evaluations 
                GROUP BY student_id
            )
        ) re ON s.student_id = re.student_id
        LEFT JOIN placements p ON s.student_id = p.student_id AND p.acceptance_status IN ('Accepted', 'Pending')
        GROUP BY readiness_band
        ORDER BY readiness_band DESC;
    """
    results = fetch_all(sql)
    for r in results:
        tot = r["total_students"]
        placed = r["placed_students"]
        r["placement_percentage"] = round((placed / tot) * 100.0, 2) if tot > 0 else 0.0

    return results
