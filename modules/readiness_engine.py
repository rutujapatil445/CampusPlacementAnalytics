"""
Explainable Rule-Based Placement Readiness Engine

Calculates a transparent 100-point Placement Readiness Score:
1. Academic Score (Max 35 points) - CGPA, SSC/HSC %, Backlogs, Gap years
2. Skills Score (Max 30 points) - Skill count, category coverage, proficiency levels
3. Projects Score (Max 15 points) - Project volume, domain diversity, GitHub links
4. Internships Score (Max 10 points) - Internship count & duration
5. Certifications Score (Max 10 points) - Verified certifications count

Outputs descriptive readiness level bands:
- 0 to 39.99: Needs Improvement
- 40 to 59.99: Developing
- 60 to 74.99: Good
- 75 to 89.99: Very Good
- 90 to 100.0: Excellent

Provides detailed strengths & actionable improvement suggestions.
Saves audit logs to 'readiness_evaluations' table.
"""

from config.database import fetch_one, fetch_all, execute_query, get_connection
from modules.student_manager import get_student_by_id, get_academic_record
from modules.portfolio_manager import (
    get_student_skills,
    get_student_projects,
    get_student_internships,
    get_student_certifications
)


def calculate_academic_score(student_id: int) -> dict:
    """
    Calculates Academic Score out of 35 points.
    Formula: Base CGPA score (35 max) minus backlog & gap year penalties.
    """
    acad = get_academic_record(student_id)
    if not acad:
        return {"score": 0.0, "details": "No academic record found."}

    cgpa = float(acad["current_cgpa"])
    active_backlogs = int(acad["total_active_backlogs"])
    gap_years = int(acad["gap_years"])

    # Base score proportional to CGPA (0.0 - 10.0 -> 0 - 35)
    base_score = (cgpa / 10.0) * 35.0

    # Penalties
    backlog_penalty = active_backlogs * 2.5
    gap_penalty = gap_years * 1.5

    final_score = max(0.0, min(35.0, base_score - backlog_penalty - gap_penalty))
    
    return {
        "score": round(final_score, 2),
        "cgpa": cgpa,
        "base_score": round(base_score, 2),
        "active_backlogs": active_backlogs,
        "backlog_penalty": backlog_penalty,
        "gap_years": gap_years,
        "gap_penalty": gap_penalty
    }


def calculate_skills_score(student_id: int) -> dict:
    """
    Calculates Skills Score out of 30 points.
    Evaluates skill count, proficiency levels, and category coverage.
    """
    skills = get_student_skills(student_id)
    if not skills:
        return {"score": 0.0, "skills_count": 0, "categories_covered": 0}

    points = 0.0
    categories = set()

    for s in skills:
        prof = s.get("proficiency_level", "Intermediate")
        categories.add(s.get("skill_category", ""))
        
        if prof == "Advanced":
            points += 4.0
        elif prof == "Intermediate":
            points += 2.5
        else: # Beginner
            points += 1.0

    # Category coverage bonus (+1.0 per unique technical category up to +4.0)
    category_bonus = min(4.0, len(categories) * 1.0)
    total = points + category_bonus
    final_score = min(30.0, total)

    return {
        "score": round(final_score, 2),
        "skills_count": len(skills),
        "categories_covered": len(categories),
        "category_bonus": category_bonus
    }


def calculate_projects_score(student_id: int) -> dict:
    """
    Calculates Projects Score out of 15 points.
    Evaluates project volume and GitHub repository links.
    """
    projects = get_student_projects(student_id)
    count = len(projects)

    if count == 0:
        return {"score": 0.0, "projects_count": 0}

    # Volume points
    if count == 1:
        base = 6.0
    elif count == 2:
        base = 11.0
    else: # 3+ projects
        base = 14.0

    # GitHub link bonus (+0.5 per project with link)
    github_bonus = sum(0.5 for p in projects if p.get("github_url"))
    final_score = min(15.0, base + github_bonus)

    return {
        "score": round(final_score, 2),
        "projects_count": count,
        "github_bonus": github_bonus
    }


def calculate_internships_score(student_id: int) -> dict:
    """
    Calculates Internships Score out of 10 points.
    Evaluates internship count and total experience duration.
    """
    internships = get_student_internships(student_id)
    count = len(internships)

    if count == 0:
        return {"score": 0.0, "internships_count": 0, "total_duration_months": 0}

    if count == 1:
        base = 6.0
    else: # 2+ internships
        base = 9.0

    # Duration bonus (+0.25 per month of experience)
    total_months = sum(int(i.get("duration_months", 1)) for i in internships)
    duration_bonus = min(2.0, total_months * 0.25)
    final_score = min(10.0, base + duration_bonus)

    return {
        "score": round(final_score, 2),
        "internships_count": count,
        "total_duration_months": total_months
    }


def calculate_certifications_score(student_id: int) -> dict:
    """
    Calculates Certifications Score out of 10 points.
    Evaluates verified professional certifications.
    """
    certs = get_student_certifications(student_id)
    count = len(certs)

    if count == 0:
        return {"score": 0.0, "certifications_count": 0}

    if count == 1:
        final_score = 5.0
    elif count == 2:
        final_score = 8.5
    else: # 3+ certifications
        final_score = 10.0

    return {
        "score": round(final_score, 2),
        "certifications_count": count
    }


def get_readiness_level(total_score: float) -> str:
    """Classifies readiness score into 5 descriptive student bands."""
    if total_score >= 90.0:
        return "Excellent"
    elif total_score >= 75.0:
        return "Very Good"
    elif total_score >= 60.0:
        return "Good"
    elif total_score >= 40.0:
        return "Developing"
    else:
        return "Needs Improvement"


def calculate_readiness_score(student_id: int) -> dict:
    """
    Calculates composite Placement Readiness Score (0 to 100 points) for a student.
    
    Returns:
        dict: {
            "student_id": int,
            "academic_score": float (max 35.0),
            "skill_score": float (max 30.0),
            "project_score": float (max 15.0),
            "internship_score": float (max 10.0),
            "certification_score": float (max 10.0),
            "total_score": float (max 100.0),
            "readiness_level": str,
            "academic_details": dict,
            "skill_details": dict,
            "project_details": dict,
            "internship_details": dict,
            "certification_details": dict
        }
    """
    student = get_student_by_id(student_id)
    if not student:
        return {
            "student_id": student_id,
            "academic_score": 0.0,
            "skill_score": 0.0,
            "project_score": 0.0,
            "internship_score": 0.0,
            "certification_score": 0.0,
            "total_score": 0.0,
            "readiness_level": "Needs Improvement",
            "error": "Student not found."
        }

    acad_res = calculate_academic_score(student_id)
    skill_res = calculate_skills_score(student_id)
    proj_res = calculate_projects_score(student_id)
    intern_res = calculate_internships_score(student_id)
    cert_res = calculate_certifications_score(student_id)

    acad_score = float(acad_res["score"])
    skill_score = float(skill_res["score"])
    proj_score = float(proj_res["score"])
    intern_score = float(intern_res["score"])
    cert_score = float(cert_res["score"])

    total = acad_score + skill_score + proj_score + intern_score + cert_score
    total_score = round(min(100.0, max(0.0, total)), 2)
    level = get_readiness_level(total_score)

    return {
        "student_id": student_id,
        "academic_score": acad_score,
        "skill_score": skill_score,
        "project_score": proj_score,
        "internship_score": intern_score,
        "certification_score": cert_score,
        "total_score": total_score,
        "readiness_level": level,
        "academic_details": acad_res,
        "skill_details": skill_res,
        "project_details": proj_res,
        "internship_details": intern_res,
        "certification_details": cert_res
    }


def get_readiness_breakdown(student_id: int) -> dict:
    """
    Generates an explainable breakdown of the student's readiness score,
    identifying key strengths and actionable areas for improvement.
    """
    res = calculate_readiness_score(student_id)
    if "error" in res:
        return res

    strengths = []
    improvements = []

    # Academic evaluation
    acad_score = res["academic_score"]
    acad_det = res["academic_details"]
    if acad_score >= 28.0:
        strengths.append(f"Strong Academic Performance (CGPA: {acad_det.get('cgpa', 0.0):.2f})")
    elif acad_score < 21.0:
        improvements.append("Improve CGPA above 7.5 to unlock Tier-1 placement eligibility.")

    if acad_det.get("active_backlogs", 0) > 0:
        improvements.append(f"Clear {acad_det['active_backlogs']} active backlog(s) immediately.")

    # Skills evaluation
    skill_score = res["skill_score"]
    skill_det = res["skill_details"]
    if skill_score >= 22.0:
        strengths.append(f"Diverse Technical Skillset ({skill_det.get('skills_count', 0)} skills tagged)")
    else:
        improvements.append("Add Core CS skills (DSA, SQL, OOP) and upgrade proficiency to Advanced.")

    # Projects evaluation
    proj_score = res["project_score"]
    proj_det = res["project_details"]
    if proj_score >= 11.0:
        strengths.append(f"Solid Project Portfolio ({proj_det.get('projects_count', 0)} projects completed)")
    else:
        improvements.append("Build at least 2 full-stack or domain projects with GitHub documentation.")

    # Internships evaluation
    intern_score = res["internship_score"]
    intern_det = res["internship_details"]
    if intern_score >= 6.0:
        strengths.append(f"Practical Industry Experience ({intern_det.get('internships_count', 0)} internship completed)")
    else:
        improvements.append("Target a 2+ month summer internship to gain industrial domain experience.")

    # Certifications evaluation
    cert_score = res["certification_score"]
    cert_det = res["certification_details"]
    if cert_score >= 5.0:
        strengths.append(f"Verified Certifications ({cert_det.get('certifications_count', 0)} earned)")
    else:
        improvements.append("Earn 1+ recognized professional certification (e.g., AWS, Coursera, NPTEL).")

    return {
        "student_id": student_id,
        "total_score": res["total_score"],
        "readiness_level": res["readiness_level"],
        "components": {
            "academic": {"score": acad_score, "max": 35.0},
            "skills": {"score": skill_score, "max": 30.0},
            "projects": {"score": proj_score, "max": 15.0},
            "internships": {"score": intern_score, "max": 10.0},
            "certifications": {"score": cert_score, "max": 10.0}
        },
        "strengths": strengths,
        "improvements": improvements
    }


def save_readiness_evaluation(student_id: int, academic_year: int = None) -> dict:
    """
    Calculates current readiness score and persists an evaluation log to 'readiness_evaluations'.
    """
    student = get_student_by_id(student_id)
    if not student:
        return {"success": False, "message": "Student not found.", "evaluation_id": None}

    eval_year = academic_year if academic_year else int(student.get("passing_year", 2026))
    score_res = calculate_readiness_score(student_id)

    try:
        sql = """
            INSERT INTO readiness_evaluations 
            (student_id, academic_year, overall_score, academic_score, skill_score, project_score, internship_score, certification_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (
            student_id,
            eval_year,
            score_res["total_score"],
            score_res["academic_score"],
            score_res["skill_score"],
            score_res["project_score"],
            score_res["internship_score"],
            score_res["certification_score"]
        ))
        conn.commit()
        new_eval_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return {
            "success": True,
            "message": "Readiness evaluation saved successfully.",
            "evaluation_id": new_eval_id,
            "overall_score": score_res["total_score"],
            "readiness_level": score_res["readiness_level"]
        }

    except Exception as e:
        return {"success": False, "message": f"Database error: {e}", "evaluation_id": None}


def get_latest_readiness_evaluation(student_id: int) -> dict:
    """Fetches the most recent saved readiness evaluation log for a student."""
    sql = "SELECT * FROM readiness_evaluations WHERE student_id = %s ORDER BY evaluation_id DESC LIMIT 1;"
    return fetch_one(sql, (student_id,))
