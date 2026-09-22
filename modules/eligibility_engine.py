"""
Eligibility Engine Module

Deterministic, rule-based eligibility evaluation engine that checks student profiles
and academic records against campus drive criteria:
1. Academic Department eligibility (drive_departments)
2. Academic benchmarks (min_cgpa, min_ssc_pct, min_hsc_pct, max_active_backlogs, max_gap_years)
3. Mandatory skill prerequisites & proficiency levels (drive_skills vs. student_skills)
"""

from config.database import fetch_one, fetch_all
from modules.student_manager import get_student_by_id, get_academic_record, get_all_students
from modules.company_manager import (
    get_drive_by_id,
    get_drive_requirements,
    get_drive_departments,
    get_drive_skills,
    get_all_drives
)
from modules.portfolio_manager import get_student_skills

# Proficiency Level Rankings for comparison
PROFICIENCY_RANK = {
    "Beginner": 1,
    "Intermediate": 2,
    "Advanced": 3
}


def analyze_student_skill_gaps(student_id: int, drive_id: int) -> list:
    """
    Compares required drive skills against student's possessed skills.
    
    Returns:
        list of dicts detailing missing skills or proficiency gaps:
        [
            {
                "skill_id": int,
                "skill_name": str,
                "required_proficiency": str,
                "student_proficiency": str or "Missing",
                "is_mandatory": bool,
                "gap_type": "Missing Skill" | "Insufficient Proficiency"
            }
        ]
    """
    req_skills = get_drive_skills(drive_id)
    if not req_skills:
        return []

    st_skills = get_student_skills(student_id)

    # Create mapping of student skill_id -> proficiency_level
    st_skill_map = {s["skill_id"]: s["proficiency_level"] for s in st_skills}

    gaps = []
    for req in req_skills:
        skill_id = req["skill_id"]
        req_prof = req["min_proficiency"]
        req_prof_rank = PROFICIENCY_RANK.get(req_prof, 2)
        is_mandatory = bool(req["is_mandatory"])

        if skill_id not in st_skill_map:
            gaps.append({
                "skill_id": skill_id,
                "skill_name": req["skill_name"],
                "required_proficiency": req_prof,
                "student_proficiency": "Missing",
                "is_mandatory": is_mandatory,
                "gap_type": "Missing Skill"
            })
        else:
            st_prof = st_skill_map[skill_id]
            st_prof_rank = PROFICIENCY_RANK.get(st_prof, 1)

            if st_prof_rank < req_prof_rank:
                gaps.append({
                    "skill_id": skill_id,
                    "skill_name": req["skill_name"],
                    "required_proficiency": req_prof,
                    "student_proficiency": st_prof,
                    "is_mandatory": is_mandatory,
                    "gap_type": "Insufficient Proficiency"
                })

    return gaps


def evaluate_student_eligibility(student_id: int, drive_id: int) -> dict:
    """
    Evaluates whether a student satisfies all dynamic criteria for a campus drive.
    
    Returns:
        dict: {
            "is_eligible": bool,
            "student_id": int,
            "drive_id": int,
            "reasons": list of str (rejection reasons if any),
            "department_eligible": bool,
            "cgpa_eligible": bool,
            "ssc_eligible": bool,
            "hsc_eligible": bool,
            "backlogs_eligible": bool,
            "gap_years_eligible": bool,
            "skills_eligible": bool,
            "missing_mandatory_skills": list of str,
            "skill_gaps": list of dicts
        }
    """
    reasons = []

    # 1. Fetch Student & Academic Data
    student = get_student_by_id(student_id)
    if not student:
        return {
            "is_eligible": False,
            "student_id": student_id,
            "drive_id": drive_id,
            "reasons": ["Student record not found."],
            "department_eligible": False,
            "cgpa_eligible": False,
            "ssc_eligible": False,
            "hsc_eligible": False,
            "backlogs_eligible": False,
            "gap_years_eligible": False,
            "skills_eligible": False,
            "missing_mandatory_skills": [],
            "skill_gaps": []
        }

    acad = get_academic_record(student_id)
    if not acad:
        return {
            "is_eligible": False,
            "student_id": student_id,
            "drive_id": drive_id,
            "reasons": ["Student academic record not found."],
            "department_eligible": False,
            "cgpa_eligible": False,
            "ssc_eligible": False,
            "hsc_eligible": False,
            "backlogs_eligible": False,
            "gap_years_eligible": False,
            "skills_eligible": False,
            "missing_mandatory_skills": [],
            "skill_gaps": []
        }

    # 2. Fetch Drive & Requirements Data
    drive = get_drive_by_id(drive_id)
    if not drive:
        return {
            "is_eligible": False,
            "student_id": student_id,
            "drive_id": drive_id,
            "reasons": ["Campus drive not found."],
            "department_eligible": False,
            "cgpa_eligible": False,
            "ssc_eligible": False,
            "hsc_eligible": False,
            "backlogs_eligible": False,
            "gap_years_eligible": False,
            "skills_eligible": False,
            "missing_mandatory_skills": [],
            "skill_gaps": []
        }

    reqs = get_drive_requirements(drive_id)
    eligible_depts = get_drive_departments(drive_id)

    # 3. Check Department Eligibility
    dept_eligible = True
    if eligible_depts:
        allowed_dept_ids = {d["dept_id"] for d in eligible_depts}
        if student["dept_id"] not in allowed_dept_ids:
            dept_eligible = False
            reasons.append(f"Department '{student['dept_name']}' is not eligible for this drive.")

    # 4. Check Academic Marks & CGPA Criteria
    cgpa_eligible = True
    ssc_eligible = True
    hsc_eligible = True
    backlogs_eligible = True
    gap_years_eligible = True

    if reqs:
        min_cgpa = float(reqs["min_cgpa"])
        min_ssc = float(reqs["min_ssc_pct"])
        min_hsc = float(reqs["min_hsc_pct"])
        max_backlogs = int(reqs["max_active_backlogs"])
        max_gap = int(reqs["max_gap_years"])

        # CGPA Check
        st_cgpa = float(acad["current_cgpa"])
        if st_cgpa < min_cgpa:
            cgpa_eligible = False
            reasons.append(f"Current CGPA ({st_cgpa:.2f}) is below minimum requirement ({min_cgpa:.2f}).")

        # SSC % Check
        st_ssc = float(acad["ssc_percentage"])
        if st_ssc < min_ssc:
            ssc_eligible = False
            reasons.append(f"SSC percentage ({st_ssc:.2f}%) is below minimum requirement ({min_ssc:.2f}%).")

        # HSC / Diploma % Check
        if acad["hsc_percentage"] is not None:
            st_hsc = float(acad["hsc_percentage"])
        elif acad["diploma_percentage"] is not None:
            st_hsc = float(acad["diploma_percentage"])
        else:
            st_hsc = float(acad["ssc_percentage"])

        if st_hsc < min_hsc:
            hsc_eligible = False
            reasons.append(f"HSC/Diploma percentage ({st_hsc:.2f}%) is below minimum requirement ({min_hsc:.2f}%).")

        # Active Backlogs Check
        st_backlogs = int(acad["total_active_backlogs"])
        if st_backlogs > max_backlogs:
            backlogs_eligible = False
            reasons.append(f"Active backlogs ({st_backlogs}) exceeds maximum allowed ({max_backlogs}).")

        # Gap Years Check
        st_gap = int(acad["gap_years"])
        if st_gap > max_gap:
            gap_years_eligible = False
            reasons.append(f"Gap years ({st_gap}) exceeds maximum allowed ({max_gap}).")

    # 5. Check Skill Prerequisites
    skill_gaps = analyze_student_skill_gaps(student_id, drive_id)
    missing_mandatory = [g["skill_name"] for g in skill_gaps if g["is_mandatory"]]

    skills_eligible = len(missing_mandatory) == 0
    if not skills_eligible:
        reasons.append(f"Missing mandatory skill(s): {', '.join(missing_mandatory)}.")

    is_overall_eligible = (
        dept_eligible and
        cgpa_eligible and
        ssc_eligible and
        hsc_eligible and
        backlogs_eligible and
        gap_years_eligible and
        skills_eligible
    )

    return {
        "is_eligible": is_overall_eligible,
        "student_id": student_id,
        "drive_id": drive_id,
        "reasons": reasons,
        "department_eligible": dept_eligible,
        "cgpa_eligible": cgpa_eligible,
        "ssc_eligible": ssc_eligible,
        "hsc_eligible": hsc_eligible,
        "backlogs_eligible": backlogs_eligible,
        "gap_years_eligible": gap_years_eligible,
        "skills_eligible": skills_eligible,
        "missing_mandatory_skills": missing_mandatory,
        "skill_gaps": skill_gaps
    }


def get_eligible_drives_for_student(student_id: int) -> list:
    """
    Returns list of all campus drives for which the specified student is eligible.
    """
    all_drives = get_all_drives()
    eligible_drives = []

    for d in all_drives:
        eval_res = evaluate_student_eligibility(student_id, d["drive_id"])
        if eval_res["is_eligible"]:
            d_copy = dict(d)
            d_copy["eligibility_details"] = eval_res
            eligible_drives.append(d_copy)

    return eligible_drives


def get_eligible_students_for_drive(drive_id: int) -> list:
    """
    Returns list of all students who satisfy eligibility criteria for a specific drive.
    """
    all_students = get_all_students()
    eligible_students = []

    for s in all_students:
        eval_res = evaluate_student_eligibility(s["student_id"], drive_id)
        if eval_res["is_eligible"]:
            s_copy = dict(s)
            s_copy["eligibility_details"] = eval_res
            eligible_students.append(s_copy)

    return eligible_students
