"""
Student Portfolio Management Module

Provides reusable functions for managing a student's:
1. Technical & Soft Skills inventory
2. Projects portfolio
3. Industrial Internships
4. Certifications
5. Portfolio summary aggregator
"""

from config.database import fetch_one, fetch_all, execute_query, get_connection
from modules.student_manager import get_student_by_id

# ==============================================================================
# 1. SKILLS MANAGEMENT
# ==============================================================================

def get_all_skills(category: str = None) -> list:
    """Fetches all master skills, optionally filtered by category."""
    if category:
        sql = "SELECT skill_id, skill_name, skill_category FROM skills WHERE skill_category = %s ORDER BY skill_name ASC;"
        return fetch_all(sql, (category,))
    sql = "SELECT skill_id, skill_name, skill_category FROM skills ORDER BY skill_name ASC;"
    return fetch_all(sql)


def search_skills(query_str: str) -> list:
    """Searches master skill catalog by skill name or category."""
    if not query_str or not query_str.strip():
        return get_all_skills()
    term = f"%{query_str.strip()}%"
    sql = """
        SELECT skill_id, skill_name, skill_category 
        FROM skills 
        WHERE skill_name LIKE %s OR skill_category LIKE %s 
        ORDER BY skill_name ASC;
    """
    return fetch_all(sql, (term, term))


def get_student_skills(student_id: int) -> list:
    """Fetches all skills tagged to a specific student with proficiency levels."""
    sql = """
        SELECT ss.id, ss.student_id, ss.skill_id, ss.proficiency_level, s.skill_name, s.skill_category
        FROM student_skills ss
        JOIN skills s ON ss.skill_id = s.skill_id
        WHERE ss.student_id = %s
        ORDER BY s.skill_name ASC;
    """
    return fetch_all(sql, (student_id,))


def add_student_skill(student_id: int, skill_id: int, proficiency_level: str = "Intermediate") -> dict:
    """Adds a skill to a student with a proficiency level ('Beginner', 'Intermediate', 'Advanced')."""
    if not student_id or not skill_id:
        return {"success": False, "message": "Student ID and Skill ID are required.", "id": None}

    prof = proficiency_level.strip().capitalize() if proficiency_level else "Intermediate"
    if prof not in ["Beginner", "Intermediate", "Advanced"]:
        return {"success": False, "message": "Proficiency level must be Beginner, Intermediate, or Advanced.", "id": None}

    student = get_student_by_id(student_id)
    if not student:
        return {"success": False, "message": "Student not found.", "id": None}

    skill = fetch_one("SELECT skill_id FROM skills WHERE skill_id = %s;", (skill_id,))
    if not skill:
        return {"success": False, "message": "Skill not found in catalog.", "id": None}

    existing = fetch_one("SELECT id FROM student_skills WHERE student_id = %s AND skill_id = %s;", (student_id, skill_id))
    if existing:
        sql = "UPDATE student_skills SET proficiency_level = %s WHERE id = %s;"
        execute_query(sql, (prof, existing["id"]))
        return {"success": True, "message": "Student skill proficiency updated.", "id": existing["id"]}

    try:
        sql = "INSERT INTO student_skills (student_id, skill_id, proficiency_level) VALUES (%s, %s, %s);"
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (student_id, skill_id, prof))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return {"success": True, "message": "Skill added to student profile.", "id": new_id}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}", "id": None}


def remove_student_skill(student_id: int, skill_id: int) -> dict:
    """Removes a skill from a student profile."""
    existing = fetch_one("SELECT id FROM student_skills WHERE student_id = %s AND skill_id = %s;", (student_id, skill_id))
    if not existing:
        return {"success": False, "message": "Student skill record not found."}

    try:
        execute_query("DELETE FROM student_skills WHERE student_id = %s AND skill_id = %s;", (student_id, skill_id))
        return {"success": True, "message": "Skill removed from student profile."}
    except Exception as e:
        return {"success": False, "message": f"Delete failed: {e}"}


# ==============================================================================
# 2. PROJECT MANAGEMENT
# ==============================================================================

def create_project(
    student_id: int,
    title: str,
    domain: str = None,
    description: str = None,
    github_url: str = None,
    duration_months: int = 1
) -> dict:
    """Creates a new project record for a student."""
    title = title.strip() if title else ""
    if not student_id or not title:
        return {"success": False, "message": "Student ID and Project Title are required.", "project_id": None}

    if duration_months <= 0:
        return {"success": False, "message": "Duration in months must be greater than 0.", "project_id": None}

    student = get_student_by_id(student_id)
    if not student:
        return {"success": False, "message": "Student not found.", "project_id": None}

    try:
        sql = """
            INSERT INTO projects (student_id, title, domain, description, github_url, duration_months)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (student_id, title, domain, description, github_url, duration_months))
        conn.commit()
        new_project_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return {"success": True, "message": "Project created successfully.", "project_id": new_project_id}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}", "project_id": None}


def get_student_projects(student_id: int) -> list:
    """Fetches all project records for a student."""
    sql = "SELECT * FROM projects WHERE student_id = %s ORDER BY project_id DESC;"
    return fetch_all(sql, (student_id,))


def get_project_by_id(project_id: int) -> dict:
    """Fetches a specific project by project_id."""
    sql = "SELECT * FROM projects WHERE project_id = %s;"
    return fetch_one(sql, (project_id,))


def update_project(
    project_id: int,
    title: str = None,
    domain: str = None,
    description: str = None,
    github_url: str = None,
    duration_months: int = None
) -> dict:
    """Updates an existing project record."""
    project = get_project_by_id(project_id)
    if not project:
        return {"success": False, "message": "Project not found."}

    updates = []
    params = []

    if title is not None:
        title_clean = title.strip()
        if not title_clean:
            return {"success": False, "message": "Project title cannot be empty."}
        updates.append("title = %s")
        params.append(title_clean)

    if domain is not None:
        updates.append("domain = %s")
        params.append(domain.strip() if domain else None)

    if description is not None:
        updates.append("description = %s")
        params.append(description.strip() if description else None)

    if github_url is not None:
        updates.append("github_url = %s")
        params.append(github_url.strip() if github_url else None)

    if duration_months is not None:
        if duration_months <= 0:
            return {"success": False, "message": "Duration in months must be greater than 0."}
        updates.append("duration_months = %s")
        params.append(duration_months)

    if not updates:
        return {"success": True, "message": "No changes specified."}

    params.append(project_id)
    sql = f"UPDATE projects SET {', '.join(updates)} WHERE project_id = %s;"

    try:
        execute_query(sql, tuple(params))
        return {"success": True, "message": "Project updated successfully."}
    except Exception as e:
        return {"success": False, "message": f"Update failed: {e}"}


def delete_project(project_id: int) -> dict:
    """Deletes a project record by ID."""
    project = get_project_by_id(project_id)
    if not project:
        return {"success": False, "message": "Project not found."}

    try:
        execute_query("DELETE FROM projects WHERE project_id = %s;", (project_id,))
        return {"success": True, "message": "Project deleted successfully."}
    except Exception as e:
        return {"success": False, "message": f"Delete failed: {e}"}


# ==============================================================================
# 3. INTERNSHIP MANAGEMENT
# ==============================================================================

def create_internship(
    student_id: int,
    company_name: str,
    role: str,
    duration_months: int,
    certificate_url: str = None
) -> dict:
    """Creates a new internship record for a student."""
    company_name = company_name.strip() if company_name else ""
    role = role.strip() if role else ""

    if not student_id or not company_name or not role:
        return {"success": False, "message": "Student ID, Company Name, and Role are required.", "internship_id": None}

    if duration_months <= 0:
        return {"success": False, "message": "Duration in months must be greater than 0.", "internship_id": None}

    student = get_student_by_id(student_id)
    if not student:
        return {"success": False, "message": "Student not found.", "internship_id": None}

    try:
        sql = """
            INSERT INTO internships (student_id, company_name, role, duration_months, certificate_url)
            VALUES (%s, %s, %s, %s, %s);
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (student_id, company_name, role, duration_months, certificate_url))
        conn.commit()
        new_internship_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return {"success": True, "message": "Internship created successfully.", "internship_id": new_internship_id}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}", "internship_id": None}


def get_student_internships(student_id: int) -> list:
    """Fetches all internship records for a student."""
    sql = "SELECT * FROM internships WHERE student_id = %s ORDER BY internship_id DESC;"
    return fetch_all(sql, (student_id,))


def get_internship_by_id(internship_id: int) -> dict:
    """Fetches a specific internship by internship_id."""
    sql = "SELECT * FROM internships WHERE internship_id = %s;"
    return fetch_one(sql, (internship_id,))


def update_internship(
    internship_id: int,
    company_name: str = None,
    role: str = None,
    duration_months: int = None,
    certificate_url: str = None
) -> dict:
    """Updates an existing internship record."""
    internship = get_internship_by_id(internship_id)
    if not internship:
        return {"success": False, "message": "Internship not found."}

    updates = []
    params = []

    if company_name is not None:
        comp_clean = company_name.strip()
        if not comp_clean:
            return {"success": False, "message": "Company name cannot be empty."}
        updates.append("company_name = %s")
        params.append(comp_clean)

    if role is not None:
        role_clean = role.strip()
        if not role_clean:
            return {"success": False, "message": "Role cannot be empty."}
        updates.append("role = %s")
        params.append(role_clean)

    if duration_months is not None:
        if duration_months <= 0:
            return {"success": False, "message": "Duration in months must be greater than 0."}
        updates.append("duration_months = %s")
        params.append(duration_months)

    if certificate_url is not None:
        updates.append("certificate_url = %s")
        params.append(certificate_url.strip() if certificate_url else None)

    if not updates:
        return {"success": True, "message": "No changes specified."}

    params.append(internship_id)
    sql = f"UPDATE internships SET {', '.join(updates)} WHERE internship_id = %s;"

    try:
        execute_query(sql, tuple(params))
        return {"success": True, "message": "Internship updated successfully."}
    except Exception as e:
        return {"success": False, "message": f"Update failed: {e}"}


def delete_internship(internship_id: int) -> dict:
    """Deletes an internship record by ID."""
    internship = get_internship_by_id(internship_id)
    if not internship:
        return {"success": False, "message": "Internship not found."}

    try:
        execute_query("DELETE FROM internships WHERE internship_id = %s;", (internship_id,))
        return {"success": True, "message": "Internship deleted successfully."}
    except Exception as e:
        return {"success": False, "message": f"Delete failed: {e}"}


# ==============================================================================
# 4. CERTIFICATION MANAGEMENT
# ==============================================================================

def create_certification(
    student_id: int,
    title: str,
    issuing_organization: str,
    issue_date: str = None
) -> dict:
    """Creates a new certification record for a student."""
    title = title.strip() if title else ""
    issuing_organization = issuing_organization.strip() if issuing_organization else ""

    if not student_id or not title or not issuing_organization:
        return {"success": False, "message": "Student ID, Title, and Issuing Organization are required.", "cert_id": None}

    student = get_student_by_id(student_id)
    if not student:
        return {"success": False, "message": "Student not found.", "cert_id": None}

    try:
        sql = """
            INSERT INTO certifications (student_id, title, issuing_organization, issue_date)
            VALUES (%s, %s, %s, %s);
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (student_id, title, issuing_organization, issue_date))
        conn.commit()
        new_cert_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return {"success": True, "message": "Certification created successfully.", "cert_id": new_cert_id}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}", "cert_id": None}


def get_student_certifications(student_id: int) -> list:
    """Fetches all certification records for a student."""
    sql = "SELECT * FROM certifications WHERE student_id = %s ORDER BY cert_id DESC;"
    return fetch_all(sql, (student_id,))


def get_certification_by_id(cert_id: int) -> dict:
    """Fetches a specific certification by cert_id."""
    sql = "SELECT * FROM certifications WHERE cert_id = %s;"
    return fetch_one(sql, (cert_id,))


def update_certification(
    cert_id: int,
    title: str = None,
    issuing_organization: str = None,
    issue_date: str = None
) -> dict:
    """Updates an existing certification record."""
    cert = get_certification_by_id(cert_id)
    if not cert:
        return {"success": False, "message": "Certification not found."}

    updates = []
    params = []

    if title is not None:
        title_clean = title.strip()
        if not title_clean:
            return {"success": False, "message": "Title cannot be empty."}
        updates.append("title = %s")
        params.append(title_clean)

    if issuing_organization is not None:
        org_clean = issuing_organization.strip()
        if not org_clean:
            return {"success": False, "message": "Issuing organization cannot be empty."}
        updates.append("issuing_organization = %s")
        params.append(org_clean)

    if issue_date is not None:
        updates.append("issue_date = %s")
        params.append(issue_date if issue_date else None)

    if not updates:
        return {"success": True, "message": "No changes specified."}

    params.append(cert_id)
    sql = f"UPDATE certifications SET {', '.join(updates)} WHERE cert_id = %s;"

    try:
        execute_query(sql, tuple(params))
        return {"success": True, "message": "Certification updated successfully."}
    except Exception as e:
        return {"success": False, "message": f"Update failed: {e}"}


def delete_certification(cert_id: int) -> dict:
    """Deletes a certification record by ID."""
    cert = get_certification_by_id(cert_id)
    if not cert:
        return {"success": False, "message": "Certification not found."}

    try:
        execute_query("DELETE FROM certifications WHERE cert_id = %s;", (cert_id,))
        return {"success": True, "message": "Certification deleted successfully."}
    except Exception as e:
        return {"success": False, "message": f"Delete failed: {e}"}


# ==============================================================================
# 5. STUDENT PORTFOLIO SUMMARY AGGREGATOR
# ==============================================================================

def get_student_portfolio_summary(student_id: int) -> dict:
    """
    Aggregates a complete portfolio summary for a student.
    
    Returns:
        dict: {
            "student": dict or None,
            "skills_count": int,
            "projects_count": int,
            "internships_count": int,
            "certifications_count": int,
            "skills": list of dicts,
            "projects": list of dicts,
            "internships": list of dicts,
            "certifications": list of dicts
        }
    """
    student = get_student_by_id(student_id)
    skills = get_student_skills(student_id)
    projects = get_student_projects(student_id)
    internships = get_student_internships(student_id)
    certifications = get_student_certifications(student_id)

    return {
        "student": student,
        "skills_count": len(skills),
        "projects_count": len(projects),
        "internships_count": len(internships),
        "certifications_count": len(certifications),
        "skills": skills,
        "projects": projects,
        "internships": internships,
        "certifications": certifications
    }
