"""
Student Profile & Academic Management Module

Provides helper functions for:
1. Department master list retrieval
2. Student profile CRUD & search operations
3. Overall academic records management (SSC %, HSC/Diploma %, CGPA, backlogs)
4. Semester-by-semester performance tracking (Semesters 1-8)
5. Comprehensive student academic summary aggregation
"""

from config.database import fetch_one, fetch_all, execute_query, get_connection

# ==============================================================================
# 1. DEPARTMENT HELPERS
# ==============================================================================

def get_all_departments() -> list:
    """Returns list of all academic departments."""
    sql = "SELECT dept_id, dept_name, dept_code FROM departments ORDER BY dept_id ASC;"
    return fetch_all(sql)


# ==============================================================================
# 2. STUDENT PROFILE MANAGEMENT
# ==============================================================================

def create_student(
    user_id: int,
    roll_number: str,
    first_name: str,
    last_name: str,
    dept_id: int,
    gender: str,
    passing_year: int,
    phone: str = None
) -> dict:
    """
    Creates a new student profile linked to an existing user_id.
    
    Validations:
    - User ID and Dept ID presence & existence
    - Roll number uniqueness
    - Gender must be 'Male', 'Female', or 'Other'
    - Passing year must be valid integer
    """
    roll_number = roll_number.strip() if roll_number else ""
    first_name = first_name.strip() if first_name else ""
    last_name = last_name.strip() if last_name else ""
    gender = gender.strip().capitalize() if gender else ""

    if not user_id or not roll_number or not first_name or not last_name or not dept_id or not gender or not passing_year:
        return {"success": False, "message": "All required profile fields must be provided.", "student_id": None}

    if gender not in ["Male", "Female", "Other"]:
        return {"success": False, "message": "Gender must be 'Male', 'Female', or 'Other'.", "student_id": None}

    if passing_year < 2000 or passing_year > 2100:
        return {"success": False, "message": "Invalid passing year specified.", "student_id": None}

    try:
        # Check user existence & duplicate student profile
        existing_profile = fetch_one("SELECT student_id FROM students WHERE user_id = %s;", (user_id,))
        if existing_profile:
            return {"success": False, "message": "A student profile already exists for this user.", "student_id": None}

        # Check duplicate roll number
        dup_roll = fetch_one("SELECT student_id FROM students WHERE roll_number = %s;", (roll_number,))
        if dup_roll:
            return {"success": False, "message": f"Roll number '{roll_number}' is already registered.", "student_id": None}

        # Check department existence
        dept = fetch_one("SELECT dept_id FROM departments WHERE dept_id = %s;", (dept_id,))
        if not dept:
            return {"success": False, "message": "Invalid department ID specified.", "student_id": None}

        sql = """
            INSERT INTO students (user_id, roll_number, first_name, last_name, dept_id, gender, phone, passing_year)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (user_id, roll_number, first_name, last_name, dept_id, gender, phone, passing_year))
        conn.commit()
        new_student_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return {"success": True, "message": "Student profile created successfully.", "student_id": new_student_id}

    except Exception as e:
        print(f"[ERROR] create_student failed: {e}")
        return {"success": False, "message": f"Database error: {e}", "student_id": None}


def get_student_by_id(student_id: int) -> dict:
    """Fetches a student profile with department and user details by student_id."""
    sql = """
        SELECT s.*, d.dept_name, d.dept_code, u.email
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        JOIN users u ON s.user_id = u.user_id
        WHERE s.student_id = %s;
    """
    return fetch_one(sql, (student_id,))


def get_student_by_user_id(user_id: int) -> dict:
    """Fetches a student profile with department and user details by user_id."""
    sql = """
        SELECT s.*, d.dept_name, d.dept_code, u.email
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        JOIN users u ON s.user_id = u.user_id
        WHERE s.user_id = %s;
    """
    return fetch_one(sql, (user_id,))


def get_all_students(dept_id: int = None, passing_year: int = None) -> list:
    """Fetches all student profiles with optional department and passing year filters."""
    sql = """
        SELECT s.*, d.dept_name, d.dept_code, u.email
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        JOIN users u ON s.user_id = u.user_id
    """
    params = []
    conditions = []

    if dept_id:
        conditions.append("s.dept_id = %s")
        params.append(dept_id)
    if passing_year:
        conditions.append("s.passing_year = %s")
        params.append(passing_year)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY s.student_id ASC;"
    return fetch_all(sql, tuple(params))


def update_student(
    student_id: int,
    first_name: str = None,
    last_name: str = None,
    dept_id: int = None,
    gender: str = None,
    phone: str = None,
    passing_year: int = None
) -> dict:
    """Updates selected fields for an existing student profile."""
    student = get_student_by_id(student_id)
    if not student:
        return {"success": False, "message": "Student not found."}

    updates = []
    params = []

    if first_name is not None and first_name.strip():
        updates.append("first_name = %s")
        params.append(first_name.strip())
    if last_name is not None and last_name.strip():
        updates.append("last_name = %s")
        params.append(last_name.strip())
    if dept_id is not None:
        dept = fetch_one("SELECT dept_id FROM departments WHERE dept_id = %s;", (dept_id,))
        if not dept:
            return {"success": False, "message": "Invalid department ID."}
        updates.append("dept_id = %s")
        params.append(dept_id)
    if gender is not None:
        gender_cap = gender.strip().capitalize()
        if gender_cap not in ["Male", "Female", "Other"]:
            return {"success": False, "message": "Gender must be Male, Female, or Other."}
        updates.append("gender = %s")
        params.append(gender_cap)
    if phone is not None:
        updates.append("phone = %s")
        params.append(phone.strip())
    if passing_year is not None:
        if passing_year < 2000 or passing_year > 2100:
            return {"success": False, "message": "Invalid passing year."}
        updates.append("passing_year = %s")
        params.append(passing_year)

    if not updates:
        return {"success": True, "message": "No changes specified."}

    params.append(student_id)
    sql = f"UPDATE students SET {', '.join(updates)} WHERE student_id = %s;"

    try:
        execute_query(sql, tuple(params))
        return {"success": True, "message": "Student profile updated successfully."}
    except Exception as e:
        return {"success": False, "message": f"Update failed: {e}"}


def delete_student(student_id: int) -> dict:
    """Deletes a student profile by ID."""
    student = get_student_by_id(student_id)
    if not student:
        return {"success": False, "message": "Student not found."}

    try:
        execute_query("DELETE FROM students WHERE student_id = %s;", (student_id,))
        return {"success": True, "message": "Student profile deleted successfully."}
    except Exception as e:
        return {"success": False, "message": f"Delete failed: {e}"}


def search_students(query_str: str) -> list:
    """Searches students by name, roll number, or email."""
    if not query_str or not query_str.strip():
        return get_all_students()

    term = f"%{query_str.strip()}%"
    sql = """
        SELECT s.*, d.dept_name, d.dept_code, u.email
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        JOIN users u ON s.user_id = u.user_id
        WHERE s.first_name LIKE %s 
           OR s.last_name LIKE %s 
           OR s.roll_number LIKE %s 
           OR u.email LIKE %s
        ORDER BY s.student_id ASC;
    """
    return fetch_all(sql, (term, term, term, term))


# ==============================================================================
# 3. ACADEMIC RECORDS MANAGEMENT
# ==============================================================================

def get_academic_record(student_id: int) -> dict:
    """Fetches the academic record summary for a student."""
    sql = "SELECT * FROM academic_records WHERE student_id = %s;"
    return fetch_one(sql, (student_id,))


def create_academic_record(
    student_id: int,
    ssc_percentage: float,
    current_cgpa: float,
    hsc_percentage: float = None,
    diploma_percentage: float = None,
    total_active_backlogs: int = 0,
    total_dead_backlogs: int = 0,
    gap_years: int = 0
) -> dict:
    """Creates a new academic record for a student."""
    if not student_id:
        return {"success": False, "message": "Student ID is required."}

    # Percentage and CGPA Validations
    if ssc_percentage < 0.0 or ssc_percentage > 100.0:
        return {"success": False, "message": "SSC percentage must be between 0 and 100."}

    if hsc_percentage is not None and (hsc_percentage < 0.0 or hsc_percentage > 100.0):
        return {"success": False, "message": "HSC percentage must be between 0 and 100."}

    if diploma_percentage is not None and (diploma_percentage < 0.0 or diploma_percentage > 100.0):
        return {"success": False, "message": "Diploma percentage must be between 0 and 100."}

    if current_cgpa < 0.0 or current_cgpa > 10.0:
        return {"success": False, "message": "CGPA must be between 0.0 and 10.0."}

    if total_active_backlogs < 0 or total_dead_backlogs < 0 or gap_years < 0:
        return {"success": False, "message": "Backlogs and gap years cannot be negative."}

    try:
        existing = get_academic_record(student_id)
        if existing:
            return {"success": False, "message": "Academic record already exists for this student."}

        sql = """
            INSERT INTO academic_records 
            (student_id, ssc_percentage, hsc_percentage, diploma_percentage, current_cgpa, total_active_backlogs, total_dead_backlogs, gap_years)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        execute_query(sql, (student_id, ssc_percentage, hsc_percentage, diploma_percentage, current_cgpa, total_active_backlogs, total_dead_backlogs, gap_years))
        return {"success": True, "message": "Academic record created successfully."}

    except Exception as e:
        return {"success": False, "message": f"Database error: {e}"}


def update_academic_record(
    student_id: int,
    ssc_percentage: float = None,
    current_cgpa: float = None,
    hsc_percentage: float = None,
    diploma_percentage: float = None,
    total_active_backlogs: int = None,
    total_dead_backlogs: int = None,
    gap_years: int = None
) -> dict:
    """Updates an existing student academic record."""
    record = get_academic_record(student_id)
    if not record:
        return {"success": False, "message": "Academic record not found for student."}

    updates = []
    params = []

    if ssc_percentage is not None:
        if ssc_percentage < 0.0 or ssc_percentage > 100.0:
            return {"success": False, "message": "SSC percentage must be between 0 and 100."}
        updates.append("ssc_percentage = %s")
        params.append(ssc_percentage)

    if hsc_percentage is not None:
        if hsc_percentage < 0.0 or hsc_percentage > 100.0:
            return {"success": False, "message": "HSC percentage must be between 0 and 100."}
        updates.append("hsc_percentage = %s")
        params.append(hsc_percentage)

    if diploma_percentage is not None:
        if diploma_percentage < 0.0 or diploma_percentage > 100.0:
            return {"success": False, "message": "Diploma percentage must be between 0 and 100."}
        updates.append("diploma_percentage = %s")
        params.append(diploma_percentage)

    if current_cgpa is not None:
        if current_cgpa < 0.0 or current_cgpa > 10.0:
            return {"success": False, "message": "CGPA must be between 0.0 and 10.0."}
        updates.append("current_cgpa = %s")
        params.append(current_cgpa)

    if total_active_backlogs is not None:
        if total_active_backlogs < 0:
            return {"success": False, "message": "Active backlogs cannot be negative."}
        updates.append("total_active_backlogs = %s")
        params.append(total_active_backlogs)

    if total_dead_backlogs is not None:
        if total_dead_backlogs < 0:
            return {"success": False, "message": "Dead backlogs cannot be negative."}
        updates.append("total_dead_backlogs = %s")
        params.append(total_dead_backlogs)

    if gap_years is not None:
        if gap_years < 0:
            return {"success": False, "message": "Gap years cannot be negative."}
        updates.append("gap_years = %s")
        params.append(gap_years)

    if not updates:
        return {"success": True, "message": "No changes specified."}

    params.append(student_id)
    sql = f"UPDATE academic_records SET {', '.join(updates)} WHERE student_id = %s;"

    try:
        execute_query(sql, tuple(params))
        return {"success": True, "message": "Academic record updated successfully."}
    except Exception as e:
        return {"success": False, "message": f"Update failed: {e}"}


def save_academic_details(
    student_id: int,
    ssc_percentage: float,
    current_cgpa: float,
    hsc_percentage: float = None,
    diploma_percentage: float = None,
    total_active_backlogs: int = 0,
    total_dead_backlogs: int = 0,
    gap_years: int = 0,
    dept_id: int = None,
    passing_year: int = None
) -> dict:
    """
    Saves or updates academic details for a student.
    Creates an academic record if none exists, otherwise updates existing record.
    Also updates dept_id and passing_year in the student profile if provided.
    """
    if not student_id:
        return {"success": False, "message": "Student ID is required."}

    student = get_student_by_id(student_id)
    if not student:
        return {"success": False, "message": "Student profile not found."}

    # Range Validations
    if ssc_percentage < 0.0 or ssc_percentage > 100.0:
        return {"success": False, "message": "SSC percentage must be between 0 and 100."}

    if hsc_percentage is not None and (hsc_percentage < 0.0 or hsc_percentage > 100.0):
        return {"success": False, "message": "HSC percentage must be between 0 and 100."}

    if diploma_percentage is not None and (diploma_percentage < 0.0 or diploma_percentage > 100.0):
        return {"success": False, "message": "Diploma percentage must be between 0 and 100."}

    if current_cgpa < 0.0 or current_cgpa > 10.0:
        return {"success": False, "message": "CGPA must be between 0.0 and 10.0."}

    if total_active_backlogs < 0 or total_dead_backlogs < 0 or gap_years < 0:
        return {"success": False, "message": "Backlogs and gap years cannot be negative."}

    # Update student profile dept_id and passing_year if provided
    if dept_id is not None or passing_year is not None:
        up_res = update_student(student_id, dept_id=dept_id, passing_year=passing_year)
        if not up_res["success"]:
            return up_res

    # Check existing academic record
    existing = get_academic_record(student_id)
    if existing:
        return update_academic_record(
            student_id=student_id,
            ssc_percentage=ssc_percentage,
            current_cgpa=current_cgpa,
            hsc_percentage=hsc_percentage,
            diploma_percentage=diploma_percentage,
            total_active_backlogs=total_active_backlogs,
            total_dead_backlogs=total_dead_backlogs,
            gap_years=gap_years
        )
    else:
        return create_academic_record(
            student_id=student_id,
            ssc_percentage=ssc_percentage,
            current_cgpa=current_cgpa,
            hsc_percentage=hsc_percentage,
            diploma_percentage=diploma_percentage,
            total_active_backlogs=total_active_backlogs,
            total_dead_backlogs=total_dead_backlogs,
            gap_years=gap_years
        )


# ==============================================================================
# 4. SEMESTER RECORDS MANAGEMENT
# ==============================================================================


def get_semester_records(student_id: int) -> list:
    """Fetches list of all semester performance records for a student ordered by semester_number."""
    sql = "SELECT * FROM semester_records WHERE student_id = %s ORDER BY semester_number ASC;"
    return fetch_all(sql, (student_id,))


def add_semester_record(
    student_id: int,
    semester_number: int,
    sgpa: float,
    cgpa: float,
    active_backlogs: int = 0,
    dead_backlogs: int = 0
) -> dict:
    """Adds a new semester performance record for a student."""
    if not student_id or not semester_number:
        return {"success": False, "message": "Student ID and Semester Number are required."}

    if semester_number < 1 or semester_number > 8:
        return {"success": False, "message": "Semester number must be between 1 and 8."}

    if sgpa < 0.0 or sgpa > 10.0 or cgpa < 0.0 or cgpa > 10.0:
        return {"success": False, "message": "SGPA and CGPA must be between 0.0 and 10.0."}

    if active_backlogs < 0 or dead_backlogs < 0:
        return {"success": False, "message": "Backlogs cannot be negative."}

    try:
        # Check duplicate semester number
        dup = fetch_one("SELECT semester_id FROM semester_records WHERE student_id = %s AND semester_number = %s;", (student_id, semester_number))
        if dup:
            return {"success": False, "message": f"Record for semester {semester_number} already exists."}

        sql = """
            INSERT INTO semester_records (student_id, semester_number, sgpa, cgpa, active_backlogs, dead_backlogs)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        execute_query(sql, (student_id, semester_number, sgpa, cgpa, active_backlogs, dead_backlogs))
        return {"success": True, "message": f"Semester {semester_number} record added successfully."}

    except Exception as e:
        return {"success": False, "message": f"Database error: {e}"}


def update_semester_record(
    student_id: int,
    semester_number: int,
    sgpa: float = None,
    cgpa: float = None,
    active_backlogs: int = None,
    dead_backlogs: int = None
) -> dict:
    """Updates SGPA, CGPA, or backlog fields for an existing semester record."""
    record = fetch_one("SELECT * FROM semester_records WHERE student_id = %s AND semester_number = %s;", (student_id, semester_number))
    if not record:
        return {"success": False, "message": f"Semester {semester_number} record not found."}

    updates = []
    params = []

    if sgpa is not None:
        if sgpa < 0.0 or sgpa > 10.0:
            return {"success": False, "message": "SGPA must be between 0.0 and 10.0."}
        updates.append("sgpa = %s")
        params.append(sgpa)

    if cgpa is not None:
        if cgpa < 0.0 or cgpa > 10.0:
            return {"success": False, "message": "CGPA must be between 0.0 and 10.0."}
        updates.append("cgpa = %s")
        params.append(cgpa)

    if active_backlogs is not None:
        if active_backlogs < 0:
            return {"success": False, "message": "Active backlogs cannot be negative."}
        updates.append("active_backlogs = %s")
        params.append(active_backlogs)

    if dead_backlogs is not None:
        if dead_backlogs < 0:
            return {"success": False, "message": "Dead backlogs cannot be negative."}
        updates.append("dead_backlogs = %s")
        params.append(dead_backlogs)

    if not updates:
        return {"success": True, "message": "No changes specified."}

    params.extend([student_id, semester_number])
    sql = f"UPDATE semester_records SET {', '.join(updates)} WHERE student_id = %s AND semester_number = %s;"

    try:
        execute_query(sql, tuple(params))
        return {"success": True, "message": f"Semester {semester_number} record updated successfully."}
    except Exception as e:
        return {"success": False, "message": f"Update failed: {e}"}


# ==============================================================================
# 5. ACADEMIC SUMMARY AGGREGATION
# ==============================================================================

def get_student_academic_summary(student_id: int) -> dict:
    """
    Aggregates student profile, academic record summary, and semester history.
    
    Returns:
        dict: {
            "student": dict or None,
            "academic_record": dict or None,
            "semester_records": list of dicts,
            "latest_sgpa": float or None,
            "semester_count": int
        }
    """
    student = get_student_by_id(student_id)
    academic_record = get_academic_record(student_id)
    semester_records = get_semester_records(student_id)

    latest_sgpa = None
    if semester_records:
        latest_sgpa = float(semester_records[-1]["sgpa"])

    return {
        "student": student,
        "academic_record": academic_record,
        "semester_records": semester_records,
        "latest_sgpa": latest_sgpa,
        "semester_count": len(semester_records)
    }
