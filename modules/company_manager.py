"""
Company & Campus Drive Management Module

Provides reusable functions for managing:
1. Recruiter Companies directory
2. Campus Placement Drives
3. Drive Eligibility Requirements (CGPA, SSC/HSC %, Backlogs, CTC)
4. Drive Eligible Departments mapping
5. Drive Required Skills mapping
6. Complete Drive Details aggregator
"""

from config.database import fetch_one, fetch_all, execute_query, get_connection

# ==============================================================================
# 1. COMPANY MANAGEMENT
# ==============================================================================

def create_company(
    company_name: str,
    industry_sector: str = None,
    website: str = None,
    hr_contact_email: str = None
) -> dict:
    """Creates a new recruiter company record."""
    company_name = company_name.strip() if company_name else ""
    if not company_name:
        return {"success": False, "message": "Company name is required.", "company_id": None}

    try:
        existing = fetch_one("SELECT company_id FROM companies WHERE company_name = %s;", (company_name,))
        if existing:
            return {"success": False, "message": f"Company '{company_name}' already exists.", "company_id": None}

        sql = """
            INSERT INTO companies (company_name, industry_sector, website, hr_contact_email)
            VALUES (%s, %s, %s, %s);
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (company_name, industry_sector, website, hr_contact_email))
        conn.commit()
        new_company_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return {"success": True, "message": "Company created successfully.", "company_id": new_company_id}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}", "company_id": None}


def get_company_by_id(company_id: int) -> dict:
    """Fetches a company record by company_id."""
    sql = "SELECT * FROM companies WHERE company_id = %s;"
    return fetch_one(sql, (company_id,))


def get_all_companies() -> list:
    """Fetches all recruiter companies ordered by name."""
    sql = "SELECT * FROM companies ORDER BY company_name ASC;"
    return fetch_all(sql)


def search_companies(query_str: str) -> list:
    """Searches companies by name or industry sector."""
    if not query_str or not query_str.strip():
        return get_all_companies()
    term = f"%{query_str.strip()}%"
    sql = """
        SELECT * FROM companies 
        WHERE company_name LIKE %s OR industry_sector LIKE %s 
        ORDER BY company_name ASC;
    """
    return fetch_all(sql, (term, term))


def update_company(
    company_id: int,
    company_name: str = None,
    industry_sector: str = None,
    website: str = None,
    hr_contact_email: str = None
) -> dict:
    """Updates an existing company record."""
    company = get_company_by_id(company_id)
    if not company:
        return {"success": False, "message": "Company not found."}

    updates = []
    params = []

    if company_name is not None:
        comp_clean = company_name.strip()
        if not comp_clean:
            return {"success": False, "message": "Company name cannot be empty."}
        dup = fetch_one("SELECT company_id FROM companies WHERE company_name = %s AND company_id != %s;", (comp_clean, company_id))
        if dup:
            return {"success": False, "message": f"Another company with name '{comp_clean}' already exists."}
        updates.append("company_name = %s")
        params.append(comp_clean)

    if industry_sector is not None:
        updates.append("industry_sector = %s")
        params.append(industry_sector.strip() if industry_sector else None)

    if website is not None:
        updates.append("website = %s")
        params.append(website.strip() if website else None)

    if hr_contact_email is not None:
        updates.append("hr_contact_email = %s")
        params.append(hr_contact_email.strip() if hr_contact_email else None)

    if not updates:
        return {"success": True, "message": "No changes specified."}

    params.append(company_id)
    sql = f"UPDATE companies SET {', '.join(updates)} WHERE company_id = %s;"

    try:
        execute_query(sql, tuple(params))
        return {"success": True, "message": "Company updated successfully."}
    except Exception as e:
        return {"success": False, "message": f"Update failed: {e}"}


def delete_company(company_id: int) -> dict:
    """Deletes a company record by ID."""
    company = get_company_by_id(company_id)
    if not company:
        return {"success": False, "message": "Company not found."}

    try:
        execute_query("DELETE FROM companies WHERE company_id = %s;", (company_id,))
        return {"success": True, "message": "Company deleted successfully."}
    except Exception as e:
        return {"success": False, "message": f"Delete failed: {e}"}


# ==============================================================================
# 2. CAMPUS DRIVE MANAGEMENT
# ==============================================================================

def create_drive(
    company_id: int,
    job_title: str,
    academic_year: int,
    drive_date: str,
    status: str = "Upcoming"
) -> dict:
    """Creates a new campus placement drive record."""
    job_title = job_title.strip() if job_title else ""
    status_cap = status.strip().capitalize() if status else "Upcoming"

    if not company_id or not job_title or not academic_year or not drive_date:
        return {"success": False, "message": "Company ID, Job Title, Academic Year, and Drive Date are required.", "drive_id": None}

    if status_cap not in ["Upcoming", "Ongoing", "Completed", "Cancelled"]:
        return {"success": False, "message": "Status must be Upcoming, Ongoing, Completed, or Cancelled.", "drive_id": None}

    company = get_company_by_id(company_id)
    if not company:
        return {"success": False, "message": "Company not found.", "drive_id": None}

    try:
        sql = """
            INSERT INTO campus_drives (company_id, job_title, academic_year, drive_date, status)
            VALUES (%s, %s, %s, %s, %s);
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (company_id, job_title, academic_year, drive_date, status_cap))
        conn.commit()
        new_drive_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return {"success": True, "message": "Campus drive created successfully.", "drive_id": new_drive_id}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}", "drive_id": None}


def get_drive_by_id(drive_id: int) -> dict:
    """Fetches a campus drive by drive_id with company name details."""
    sql = """
        SELECT d.*, c.company_name, c.industry_sector
        FROM campus_drives d
        JOIN companies c ON d.company_id = c.company_id
        WHERE d.drive_id = %s;
    """
    return fetch_one(sql, (drive_id,))


def get_all_drives(company_id: int = None, academic_year: int = None, status: str = None) -> list:
    """Fetches all campus drives with company details and optional filters."""
    sql = """
        SELECT d.*, c.company_name, c.industry_sector
        FROM campus_drives d
        JOIN companies c ON d.company_id = c.company_id
    """
    conditions = []
    params = []

    if company_id:
        conditions.append("d.company_id = %s")
        params.append(company_id)
    if academic_year:
        conditions.append("d.academic_year = %s")
        params.append(academic_year)
    if status:
        conditions.append("d.status = %s")
        params.append(status.strip().capitalize())

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY d.drive_date DESC;"
    return fetch_all(sql, tuple(params))


def search_drives(query_str: str) -> list:
    """Searches campus drives by job title or company name."""
    if not query_str or not query_str.strip():
        return get_all_drives()
    term = f"%{query_str.strip()}%"
    sql = """
        SELECT d.*, c.company_name, c.industry_sector
        FROM campus_drives d
        JOIN companies c ON d.company_id = c.company_id
        WHERE d.job_title LIKE %s OR c.company_name LIKE %s
        ORDER BY d.drive_date DESC;
    """
    return fetch_all(sql, (term, term))


def update_drive(
    drive_id: int,
    company_id: int = None,
    job_title: str = None,
    academic_year: int = None,
    drive_date: str = None,
    status: str = None
) -> dict:
    """Updates an existing campus drive record."""
    drive = get_drive_by_id(drive_id)
    if not drive:
        return {"success": False, "message": "Campus drive not found."}

    updates = []
    params = []

    if company_id is not None:
        comp = get_company_by_id(company_id)
        if not comp:
            return {"success": False, "message": "Company not found."}
        updates.append("company_id = %s")
        params.append(company_id)

    if job_title is not None:
        jt_clean = job_title.strip()
        if not jt_clean:
            return {"success": False, "message": "Job title cannot be empty."}
        updates.append("job_title = %s")
        params.append(jt_clean)

    if academic_year is not None:
        updates.append("academic_year = %s")
        params.append(academic_year)

    if drive_date is not None:
        updates.append("drive_date = %s")
        params.append(drive_date)

    if status is not None:
        st_clean = status.strip().capitalize()
        if st_clean not in ["Upcoming", "Ongoing", "Completed", "Cancelled"]:
            return {"success": False, "message": "Status must be Upcoming, Ongoing, Completed, or Cancelled."}
        updates.append("status = %s")
        params.append(st_clean)

    if not updates:
        return {"success": True, "message": "No changes specified."}

    params.append(drive_id)
    sql = f"UPDATE campus_drives SET {', '.join(updates)} WHERE drive_id = %s;"

    try:
        execute_query(sql, tuple(params))
        return {"success": True, "message": "Campus drive updated successfully."}
    except Exception as e:
        return {"success": False, "message": f"Update failed: {e}"}


def delete_drive(drive_id: int) -> dict:
    """Deletes a campus drive record by ID."""
    drive = get_drive_by_id(drive_id)
    if not drive:
        return {"success": False, "message": "Campus drive not found."}

    try:
        execute_query("DELETE FROM campus_drives WHERE drive_id = %s;", (drive_id,))
        return {"success": True, "message": "Campus drive deleted successfully."}
    except Exception as e:
        return {"success": False, "message": f"Delete failed: {e}"}


# ==============================================================================
# 3. DRIVE REQUIREMENTS MANAGEMENT
# ==============================================================================

def get_drive_requirements(drive_id: int) -> dict:
    """Fetches eligibility requirements associated with a campus drive."""
    sql = "SELECT * FROM drive_requirements WHERE drive_id = %s;"
    return fetch_one(sql, (drive_id,))


def set_drive_requirements(
    drive_id: int,
    min_cgpa: float = 6.00,
    min_ssc_pct: float = 60.00,
    min_hsc_pct: float = 60.00,
    max_active_backlogs: int = 0,
    max_gap_years: int = 0,
    ctc_lpa: float = 6.00
) -> dict:
    """Sets or creates eligibility requirements for a campus drive."""
    if not drive_id:
        return {"success": False, "message": "Drive ID is required."}

    if min_cgpa < 0.0 or min_cgpa > 10.0:
        return {"success": False, "message": "Minimum CGPA must be between 0.0 and 10.0."}

    if min_ssc_pct < 0.0 or min_ssc_pct > 100.0 or min_hsc_pct < 0.0 or min_hsc_pct > 100.0:
        return {"success": False, "message": "Percentages must be between 0 and 100."}

    if max_active_backlogs < 0 or max_gap_years < 0:
        return {"success": False, "message": "Backlogs and gap years cannot be negative."}

    if ctc_lpa <= 0.0:
        return {"success": False, "message": "CTC package in LPA must be greater than 0."}

    drive = get_drive_by_id(drive_id)
    if not drive:
        return {"success": False, "message": "Campus drive not found."}

    try:
        existing = get_drive_requirements(drive_id)
        if existing:
            # Update existing requirement
            return update_drive_requirements(
                drive_id=drive_id,
                min_cgpa=min_cgpa,
                min_ssc_pct=min_ssc_pct,
                min_hsc_pct=min_hsc_pct,
                max_active_backlogs=max_active_backlogs,
                max_gap_years=max_gap_years,
                ctc_lpa=ctc_lpa
            )

        sql = """
            INSERT INTO drive_requirements (drive_id, min_cgpa, min_ssc_pct, min_hsc_pct, max_active_backlogs, max_gap_years, ctc_lpa)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        execute_query(sql, (drive_id, min_cgpa, min_ssc_pct, min_hsc_pct, max_active_backlogs, max_gap_years, ctc_lpa))
        return {"success": True, "message": "Drive requirements set successfully."}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}"}


def update_drive_requirements(
    drive_id: int,
    min_cgpa: float = None,
    min_ssc_pct: float = None,
    min_hsc_pct: float = None,
    max_active_backlogs: int = None,
    max_gap_years: int = None,
    ctc_lpa: float = None
) -> dict:
    """Updates selected requirement fields for a drive."""
    req = get_drive_requirements(drive_id)
    if not req:
        return {"success": False, "message": "Drive requirements not found."}

    updates = []
    params = []

    if min_cgpa is not None:
        if min_cgpa < 0.0 or min_cgpa > 10.0:
            return {"success": False, "message": "Minimum CGPA must be between 0.0 and 10.0."}
        updates.append("min_cgpa = %s")
        params.append(min_cgpa)

    if min_ssc_pct is not None:
        if min_ssc_pct < 0.0 or min_ssc_pct > 100.0:
            return {"success": False, "message": "Minimum SSC % must be between 0 and 100."}
        updates.append("min_ssc_pct = %s")
        params.append(min_ssc_pct)

    if min_hsc_pct is not None:
        if min_hsc_pct < 0.0 or min_hsc_pct > 100.0:
            return {"success": False, "message": "Minimum HSC % must be between 0 and 100."}
        updates.append("min_hsc_pct = %s")
        params.append(min_hsc_pct)

    if max_active_backlogs is not None:
        if max_active_backlogs < 0:
            return {"success": False, "message": "Max active backlogs cannot be negative."}
        updates.append("max_active_backlogs = %s")
        params.append(max_active_backlogs)

    if max_gap_years is not None:
        if max_gap_years < 0:
            return {"success": False, "message": "Max gap years cannot be negative."}
        updates.append("max_gap_years = %s")
        params.append(max_gap_years)

    if ctc_lpa is not None:
        if ctc_lpa <= 0.0:
            return {"success": False, "message": "CTC package in LPA must be greater than 0."}
        updates.append("ctc_lpa = %s")
        params.append(ctc_lpa)

    if not updates:
        return {"success": True, "message": "No changes specified."}

    params.append(drive_id)
    sql = f"UPDATE drive_requirements SET {', '.join(updates)} WHERE drive_id = %s;"

    try:
        execute_query(sql, tuple(params))
        return {"success": True, "message": "Drive requirements updated successfully."}
    except Exception as e:
        return {"success": False, "message": f"Update failed: {e}"}


# ==============================================================================
# 4. DRIVE DEPARTMENTS MAPPING
# ==============================================================================

def get_drive_departments(drive_id: int) -> list:
    """Fetches all eligible academic departments for a drive."""
    sql = """
        SELECT dd.id, dd.drive_id, dd.dept_id, d.dept_name, d.dept_code
        FROM drive_departments dd
        JOIN departments d ON dd.dept_id = d.dept_id
        WHERE dd.drive_id = %s
        ORDER BY d.dept_name ASC;
    """
    return fetch_all(sql, (drive_id,))


def add_drive_department(drive_id: int, dept_id: int) -> dict:
    """Adds an eligible department to a campus drive."""
    if not drive_id or not dept_id:
        return {"success": False, "message": "Drive ID and Dept ID are required."}

    drive = get_drive_by_id(drive_id)
    if not drive:
        return {"success": False, "message": "Campus drive not found."}

    dept = fetch_one("SELECT dept_id FROM departments WHERE dept_id = %s;", (dept_id,))
    if not dept:
        return {"success": False, "message": "Department not found."}

    existing = fetch_one("SELECT id FROM drive_departments WHERE drive_id = %s AND dept_id = %s;", (drive_id, dept_id))
    if existing:
        return {"success": False, "message": "Department is already eligible for this drive."}

    try:
        sql = "INSERT INTO drive_departments (drive_id, dept_id) VALUES (%s, %s);"
        execute_query(sql, (drive_id, dept_id))
        return {"success": True, "message": "Department added to drive eligibility."}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}"}


def remove_drive_department(drive_id: int, dept_id: int) -> dict:
    """Removes an eligible department from a campus drive."""
    existing = fetch_one("SELECT id FROM drive_departments WHERE drive_id = %s AND dept_id = %s;", (drive_id, dept_id))
    if not existing:
        return {"success": False, "message": "Drive department mapping not found."}

    try:
        execute_query("DELETE FROM drive_departments WHERE drive_id = %s AND dept_id = %s;", (drive_id, dept_id))
        return {"success": True, "message": "Department removed from drive eligibility."}
    except Exception as e:
        return {"success": False, "message": f"Delete failed: {e}"}


def set_drive_departments(drive_id: int, dept_ids: list) -> dict:
    """Bulk replaces eligible departments for a drive."""
    drive = get_drive_by_id(drive_id)
    if not drive:
        return {"success": False, "message": "Campus drive not found."}

    try:
        execute_query("DELETE FROM drive_departments WHERE drive_id = %s;", (drive_id,))
        for d_id in dept_ids:
            add_drive_department(drive_id, d_id)
        return {"success": True, "message": "Eligible departments set successfully."}
    except Exception as e:
        return {"success": False, "message": f"Bulk set failed: {e}"}


# ==============================================================================
# 5. DRIVE SKILLS MAPPING
# ==============================================================================

def get_drive_skills(drive_id: int) -> list:
    """Fetches all technical skills required for a campus drive."""
    sql = """
        SELECT ds.id, ds.drive_id, ds.skill_id, ds.min_proficiency, ds.is_mandatory, s.skill_name, s.skill_category
        FROM drive_skills ds
        JOIN skills s ON ds.skill_id = s.skill_id
        WHERE ds.drive_id = %s
        ORDER BY s.skill_name ASC;
    """
    return fetch_all(sql, (drive_id,))


def add_drive_skill(
    drive_id: int,
    skill_id: int,
    min_proficiency: str = "Intermediate",
    is_mandatory: bool = True
) -> dict:
    """Adds a required skill to a campus drive."""
    if not drive_id or not skill_id:
        return {"success": False, "message": "Drive ID and Skill ID are required."}

    prof = min_proficiency.strip().capitalize() if min_proficiency else "Intermediate"
    if prof not in ["Beginner", "Intermediate", "Advanced"]:
        return {"success": False, "message": "Proficiency level must be Beginner, Intermediate, or Advanced."}

    drive = get_drive_by_id(drive_id)
    if not drive:
        return {"success": False, "message": "Campus drive not found."}

    skill = fetch_one("SELECT skill_id FROM skills WHERE skill_id = %s;", (skill_id,))
    if not skill:
        return {"success": False, "message": "Skill not found in catalog."}

    existing = fetch_one("SELECT id FROM drive_skills WHERE drive_id = %s AND skill_id = %s;", (drive_id, skill_id))
    if existing:
        return {"success": False, "message": "Skill is already added to this drive."}

    try:
        sql = "INSERT INTO drive_skills (drive_id, skill_id, min_proficiency, is_mandatory) VALUES (%s, %s, %s, %s);"
        execute_query(sql, (drive_id, skill_id, prof, bool(is_mandatory)))
        return {"success": True, "message": "Skill added to drive requirements."}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}"}


def remove_drive_skill(drive_id: int, skill_id: int) -> dict:
    """Removes a required skill from a campus drive."""
    existing = fetch_one("SELECT id FROM drive_skills WHERE drive_id = %s AND skill_id = %s;", (drive_id, skill_id))
    if not existing:
        return {"success": False, "message": "Drive skill mapping not found."}

    try:
        execute_query("DELETE FROM drive_skills WHERE drive_id = %s AND skill_id = %s;", (drive_id, skill_id))
        return {"success": True, "message": "Skill removed from drive requirements."}
    except Exception as e:
        return {"success": False, "message": f"Delete failed: {e}"}


def set_drive_skills(drive_id: int, skill_ids: list) -> dict:
    """Bulk replaces required skills for a drive."""
    drive = get_drive_by_id(drive_id)
    if not drive:
        return {"success": False, "message": "Campus drive not found."}

    try:
        execute_query("DELETE FROM drive_skills WHERE drive_id = %s;", (drive_id,))
        for s_id in skill_ids:
            add_drive_skill(drive_id, s_id)
        return {"success": True, "message": "Required skills set successfully."}
    except Exception as e:
        return {"success": False, "message": f"Bulk set failed: {e}"}


# ==============================================================================
# 6. DRIVE DETAILS AGGREGATOR
# ==============================================================================

def get_drive_details(drive_id: int) -> dict:
    """
    Aggregates complete information for a campus placement drive.
    
    Returns:
        dict: {
            "drive": dict or None,
            "requirements": dict or None,
            "departments": list of dicts,
            "skills": list of dicts
        }
    """
    drive = get_drive_by_id(drive_id)
    requirements = get_drive_requirements(drive_id)
    departments = get_drive_departments(drive_id)
    skills = get_drive_skills(drive_id)

    return {
        "drive": drive,
        "requirements": requirements,
        "departments": departments,
        "skills": skills
    }
