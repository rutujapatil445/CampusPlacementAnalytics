"""
Application Tracking & Placement Offer Management Module

Manages:
1. Student campus drive application submission & eligibility validation
2. Multi-stage selection workflow status updates (Applied -> Shortlisted -> Assessment -> Interview -> Offered)
3. Application withdrawal
4. Final placement offer logging & CTC tracking
5. Student placement & application summary aggregator
"""

from datetime import date
from config.database import fetch_one, fetch_all, execute_query, get_connection
from modules.student_manager import get_student_by_id
from modules.company_manager import get_drive_by_id
from modules.eligibility_engine import evaluate_student_eligibility

VALID_STATUSES = [
    "Eligible", "Applied", "Shortlisted", "Assessment", 
    "Interview", "Offered", "Accepted", "Rejected", "Withdrawn"
]


# ==============================================================================
# 1. APPLICATION MANAGEMENT
# ==============================================================================

def apply_for_drive(student_id: int, drive_id: int, bypass_eligibility: bool = False) -> dict:
    """
    Submits a new campus drive application for a student.
    
    Validations:
    - Student & Drive presence
    - Duplicate application check (uk_student_drive)
    - Eligibility evaluation (Unless bypass_eligibility is True)
    """
    if not student_id or not drive_id:
        return {"success": False, "message": "Student ID and Drive ID are required.", "application_id": None}

    student = get_student_by_id(student_id)
    if not student:
        return {"success": False, "message": "Student not found.", "application_id": None}

    drive = get_drive_by_id(drive_id)
    if not drive:
        return {"success": False, "message": "Campus drive not found.", "application_id": None}

    existing = fetch_one("SELECT application_id, status FROM applications WHERE student_id = %s AND drive_id = %s;", (student_id, drive_id))
    if existing:
        return {"success": False, "message": f"Student has already applied for this drive (Status: {existing['status']}).", "application_id": existing["application_id"]}

    # Check eligibility unless explicitly bypassed
    if not bypass_eligibility:
        eval_res = evaluate_student_eligibility(student_id, drive_id)
        if not eval_res["is_eligible"]:
            reasons_str = "; ".join(eval_res["reasons"])
            return {
                "success": False,
                "message": f"Student does not meet eligibility criteria: {reasons_str}",
                "application_id": None,
                "eligibility_reasons": eval_res["reasons"]
            }

    try:
        today_str = date.today().strftime("%Y-%m-%d")
        sql = """
            INSERT INTO applications (student_id, drive_id, application_date, status)
            VALUES (%s, %s, %s, 'Applied');
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (student_id, drive_id, today_str))
        conn.commit()
        new_app_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return {"success": True, "message": "Application submitted successfully.", "application_id": new_app_id}

    except Exception as e:
        return {"success": False, "message": f"Database error: {e}", "application_id": None}


def get_application_by_id(application_id: int) -> dict:
    """Fetches a specific application with joined student and drive details."""
    sql = """
        SELECT a.*, 
               s.first_name, s.last_name, s.roll_number, s.dept_id,
               d.job_title, d.company_id, d.academic_year, d.drive_date,
               c.company_name, c.industry_sector
        FROM applications a
        JOIN students s ON a.student_id = s.student_id
        JOIN campus_drives d ON a.drive_id = d.drive_id
        JOIN companies c ON d.company_id = c.company_id
        WHERE a.application_id = %s;
    """
    return fetch_one(sql, (application_id,))


def get_student_applications(student_id: int) -> list:
    """Fetches all applications submitted by a specific student."""
    sql = """
        SELECT a.*, 
               d.job_title, d.company_id, d.academic_year, d.drive_date,
               c.company_name, c.industry_sector,
               dr.ctc_lpa
        FROM applications a
        JOIN campus_drives d ON a.drive_id = d.drive_id
        JOIN companies c ON d.company_id = c.company_id
        LEFT JOIN drive_requirements dr ON d.drive_id = dr.drive_id
        WHERE a.student_id = %s
        ORDER BY a.application_date DESC;
    """
    return fetch_all(sql, (student_id,))


def get_drive_applications(drive_id: int, status_filter: str = None) -> list:
    """Fetches all student applications submitted for a specific campus drive."""
    sql = """
        SELECT a.*, 
               s.first_name, s.last_name, s.roll_number, s.dept_id, s.passing_year,
               dept.dept_name, dept.dept_code,
               ar.current_cgpa, ar.total_active_backlogs
        FROM applications a
        JOIN students s ON a.student_id = s.student_id
        JOIN departments dept ON s.dept_id = dept.dept_id
        LEFT JOIN academic_records ar ON s.student_id = ar.student_id
        WHERE a.drive_id = %s
    """
    params = [drive_id]

    if status_filter:
        sql += " AND a.status = %s"
        params.append(status_filter.strip().capitalize())

    sql += " ORDER BY a.application_date DESC;"
    return fetch_all(sql, tuple(params))


def update_application_status(application_id: int, new_status: str) -> dict:
    """Updates the selection workflow status of an application."""
    app = get_application_by_id(application_id)
    if not app:
        return {"success": False, "message": "Application not found."}

    st_clean = new_status.strip().capitalize() if new_status else ""
    if st_clean not in VALID_STATUSES:
        return {"success": False, "message": f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}."}

    try:
        sql = "UPDATE applications SET status = %s WHERE application_id = %s;"
        execute_query(sql, (st_clean, application_id))
        return {"success": True, "message": f"Application status updated to '{st_clean}'."}
    except Exception as e:
        return {"success": False, "message": f"Update failed: {e}"}


def withdraw_application(application_id: int) -> dict:
    """Withdraws a student application."""
    return update_application_status(application_id, "Withdrawn")


# ==============================================================================
# 2. PLACEMENT OFFER MANAGEMENT
# ==============================================================================

def record_placement_offer(
    application_id: int,
    offered_ctc: float,
    offer_letter_date: str = None,
    acceptance_status: str = "Accepted"
) -> dict:
    """
    Records a final job placement offer resulting from an application.
    
    Validations:
    - Application existence
    - Offered CTC > 0.0
    - Acceptance status in ['Accepted', 'Declined', 'Pending']
    """
    if not application_id:
        return {"success": False, "message": "Application ID is required.", "placement_id": None}

    if offered_ctc <= 0.0:
        return {"success": False, "message": "Offered CTC in LPA must be greater than 0.", "placement_id": None}

    acc_status = acceptance_status.strip().capitalize() if acceptance_status else "Accepted"
    if acc_status not in ["Accepted", "Declined", "Pending"]:
        return {"success": False, "message": "Acceptance status must be Accepted, Declined, or Pending.", "placement_id": None}

    app = get_application_by_id(application_id)
    if not app:
        return {"success": False, "message": "Application not found.", "placement_id": None}

    student_id = app["student_id"]
    drive_id = app["drive_id"]
    offer_date = offer_letter_date if offer_letter_date else date.today().strftime("%Y-%m-%d")

    try:
        # Update application status to Offered if not already Offered or Accepted
        if app["status"] not in ["Offered", "Accepted"]:
            update_application_status(application_id, "Offered")

        # Check if placement record already exists for this application
        existing = fetch_one("SELECT placement_id FROM placements WHERE application_id = %s;", (application_id,))

        if existing:
            # Update existing placement
            p_id = existing["placement_id"]
            sql = """
                UPDATE placements 
                SET offered_ctc = %s, offer_letter_date = %s, acceptance_status = %s 
                WHERE placement_id = %s;
            """
            execute_query(sql, (offered_ctc, offer_date, acc_status, p_id))
            return {"success": True, "message": "Placement offer updated successfully.", "placement_id": p_id}

        # Insert new placement record
        sql = """
            INSERT INTO placements (student_id, drive_id, application_id, offered_ctc, offer_letter_date, acceptance_status)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (student_id, drive_id, application_id, offered_ctc, offer_date, acc_status))
        conn.commit()
        new_placement_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return {"success": True, "message": "Placement offer recorded successfully.", "placement_id": new_placement_id}

    except Exception as e:
        return {"success": False, "message": f"Database error: {e}", "placement_id": None}


def get_placement_record(placement_id: int = None, application_id: int = None) -> dict:
    """Fetches placement offer details by placement_id or application_id."""
    if placement_id:
        sql = """
            SELECT p.*, 
                   s.first_name, s.last_name, s.roll_number, s.dept_id,
                   d.job_title, d.company_id, c.company_name, c.industry_sector
            FROM placements p
            JOIN students s ON p.student_id = s.student_id
            JOIN campus_drives d ON p.drive_id = d.drive_id
            JOIN companies c ON d.company_id = c.company_id
            WHERE p.placement_id = %s;
        """
        return fetch_one(sql, (placement_id,))

    if application_id:
        sql = """
            SELECT p.*, 
                   s.first_name, s.last_name, s.roll_number, s.dept_id,
                   d.job_title, d.company_id, c.company_name, c.industry_sector
            FROM placements p
            JOIN students s ON p.student_id = s.student_id
            JOIN campus_drives d ON p.drive_id = d.drive_id
            JOIN companies c ON d.company_id = c.company_id
            WHERE p.application_id = %s;
        """
        return fetch_one(sql, (application_id,))

    return None


def get_all_placements(academic_year: int = None, dept_id: int = None) -> list:
    """Fetches all verified placement records with optional filters."""
    sql = """
        SELECT p.*, 
               s.first_name, s.last_name, s.roll_number, s.dept_id,
               dept.dept_name, dept.dept_code,
               d.job_title, d.company_id, d.academic_year,
               c.company_name, c.industry_sector
        FROM placements p
        JOIN students s ON p.student_id = s.student_id
        JOIN departments dept ON s.dept_id = dept.dept_id
        JOIN campus_drives d ON p.drive_id = d.drive_id
        JOIN companies c ON d.company_id = c.company_id
    """
    conditions = []
    params = []

    if academic_year:
        conditions.append("d.academic_year = %s")
        params.append(academic_year)
    if dept_id:
        conditions.append("s.dept_id = %s")
        params.append(dept_id)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY p.offered_ctc DESC;"
    return fetch_all(sql, tuple(params))


def get_student_placement_summary(student_id: int) -> dict:
    """
    Aggregates student application history and placement status.
    """
    applications = get_student_applications(student_id)
    
    status_counts = {}
    for app in applications:
        st = app["status"]
        status_counts[st] = status_counts.get(st, 0) + 1

    # Fetch placement offer if accepted/offered
    placements = fetch_all("SELECT * FROM placements WHERE student_id = %s ORDER BY offered_ctc DESC;", (student_id,))
    is_placed = len(placements) > 0

    return {
        "student_id": student_id,
        "is_placed": is_placed,
        "total_applications": len(applications),
        "status_counts": status_counts,
        "applications": applications,
        "placements": placements
    }
