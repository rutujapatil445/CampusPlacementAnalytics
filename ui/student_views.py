"""
Student Portal Views Module

Implements Student Dashboard UI tabs:
1. Overview & Profile Management
2. Skills, Projects, Internships & Certifications Portfolio
3. Campus Drives & Eligibility Matcher
4. Applications & Placements Tracker
5. Placement Readiness Score & ML Placement Probability Estimate
"""

import streamlit as st
import pandas as pd

from modules.student_manager import (
    get_student_by_user_id,
    create_student,
    update_student,
    get_academic_record,
    get_all_departments,
    get_student_academic_summary,
    save_academic_details
)
from modules.portfolio_manager import (
    get_all_skills,
    get_student_skills,
    add_student_skill,
    remove_student_skill,
    get_student_projects,
    create_project,
    delete_project,
    get_student_internships,
    create_internship,
    delete_internship,
    get_student_certifications,
    create_certification,
    delete_certification
)
from modules.company_manager import get_all_drives, get_drive_details
from modules.eligibility_engine import evaluate_student_eligibility
from modules.application_manager import (
    apply_for_drive,
    get_student_applications,
    get_student_placement_summary
)
from modules.readiness_engine import (
    calculate_readiness_score,
    get_readiness_breakdown,
    save_readiness_evaluation
)
from modules.ml_model import predict_placement
from ui.components import render_header, render_kpi_card, render_bar_chart


def render_student_dashboard(user: dict):
    """Main rendering entry point for logged-in Student users."""
    user_id = user["user_id"]
    student = get_student_by_user_id(user_id)

    # Handle First-Time Student Setup if profile doesn't exist yet
    if not student:
        st.warning("⚠️ Welcome! Please complete your student profile setup to access the portal.")
        render_first_time_profile_setup(user_id)
        return

    student_id = student["student_id"]
    st.sidebar.markdown(f"**Student:** {student['first_name']} {student['last_name']}")
    st.sidebar.markdown(f"**Roll No:** `{student['roll_number']}`")
    st.sidebar.markdown(f"**Dept:** {student['dept_code']}")

    tabs = st.tabs([
        "📌 Overview & Profile",
        "🎓 Skills & Portfolio",
        "🎯 Campus Drives & Eligibility",
        "📋 Applications & Offers",
        "📊 Readiness & ML Estimate"
    ])

    with tabs[0]:
        render_profile_tab(student)

    with tabs[1]:
        render_portfolio_tab(student_id)

    with tabs[2]:
        render_drives_tab(student_id)

    with tabs[3]:
        render_applications_tab(student_id)

    with tabs[4]:
        render_readiness_and_ml_tab(student_id)


def render_first_time_profile_setup(user_id: int):
    """Renders profile creation form for newly registered student accounts."""
    depts = get_all_departments()
    dept_options = {f"{d['dept_name']} ({d['dept_code']})": d["dept_id"] for d in depts}

    with st.form("first_time_student_form"):
        st.subheader("Student Profile Setup")
        c1, c2 = st.columns(2)
        with c1:
            roll = st.text_input("Roll Number", placeholder="e.g. 2026COMP001")
            fn = st.text_input("First Name")
            ln = st.text_input("Last Name")
        with c2:
            dept_name = st.selectbox("Department", list(dept_options.keys()))
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            pass_yr = st.number_input("Passing Year", min_value=2020, max_value=2030, value=2026)
            phone = st.text_input("Phone Number")

        submitted = st.form_submit_button("Save Profile")
        if submitted:
            dept_id = dept_options[dept_name]
            res = create_student(user_id, roll, fn, ln, dept_id, gender, pass_yr, phone)
            if res["success"]:
                st.success("Profile created successfully! Refreshing...")
                st.rerun()
            else:
                st.error(res["message"])


def render_profile_tab(student: dict):
    """Renders Student Overview & Profile Tab."""
    render_header(f"Welcome, {student['first_name']} {student['last_name']}!", f"Department of {student['dept_name']}")

    acad = get_academic_record(student["student_id"])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        cgpa_val = f"{acad['current_cgpa']:.2f}" if acad else "N/A"
        render_kpi_card("Current CGPA", cgpa_val, "Out of 10.00", icon="🎓")
    with col2:
        ssc_val = f"{acad['ssc_percentage']:.1f}%" if acad else "N/A"
        render_kpi_card("10th Percentage", ssc_val, "SSC Marks", icon="📜")
    with col3:
        backlogs_val = str(acad["total_active_backlogs"]) if acad else "0"
        render_kpi_card("Active Backlogs", backlogs_val, "Current Backlogs", icon="⚠️")
    with col4:
        pass_year = str(student["passing_year"])
        render_kpi_card("Graduation Year", pass_year, "Batch Year", icon="📅")

    st.write("---")
    st.markdown("### Profile Summary & Personal Details")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Full Name:** {student['first_name']} {student['last_name']}")
        st.write(f"**Roll Number:** `{student['roll_number']}`")
        st.write(f"**Email:** `{student['email']}`")
        st.write(f"**Gender:** {student['gender']}")
    with c2:
        st.write(f"**Department:** {student['dept_name']} ({student['dept_code']})")
        st.write(f"**Phone:** {student.get('phone') or 'Not provided'}")
        st.write(f"**Gap Years:** {acad.get('gap_years', 0) if acad else 0}")
        st.write(f"**Dead Backlogs:** {acad.get('total_dead_backlogs', 0) if acad else 0}")

    st.write("---")
    btn_label = "✏️ Edit Academic Details" if acad else "➕ Add Academic Details"
    with st.expander(btn_label):
        depts = get_all_departments()
        dept_options = {f"{d['dept_name']} ({d['dept_code']})": d["dept_id"] for d in depts}
        curr_dept_idx = 0
        for idx, (label, d_id) in enumerate(dept_options.items()):
            if d_id == student["dept_id"]:
                curr_dept_idx = idx
                break

        with st.form("edit_academic_details_form"):
            st.subheader("Academic Details Form")
            fc1, fc2 = st.columns(2)
            with fc1:
                f_ssc = st.number_input(
                    "10th / SSC Percentage (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(acad.get("ssc_percentage", 60.0)) if acad else 60.0,
                    step=0.1
                )
                f_hsc = st.number_input(
                    "12th / HSC Percentage (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(acad.get("hsc_percentage", 60.0)) if (acad and acad.get("hsc_percentage") is not None) else 60.0,
                    step=0.1
                )
                f_diploma = st.number_input(
                    "Diploma Aggregate Percentage (%) (0 if N/A)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(acad.get("diploma_percentage", 0.0)) if (acad and acad.get("diploma_percentage") is not None) else 0.0,
                    step=0.1
                )
                f_cgpa = st.number_input(
                    "Current CGPA (Out of 10.0)",
                    min_value=0.0,
                    max_value=10.0,
                    value=float(acad.get("current_cgpa", 7.0)) if acad else 7.0,
                    step=0.01
                )
            with fc2:
                f_active_backlogs = st.number_input(
                    "Total Active Backlogs",
                    min_value=0,
                    value=int(acad.get("total_active_backlogs", 0)) if acad else 0,
                    step=1
                )
                f_dead_backlogs = st.number_input(
                    "Total Dead Backlogs",
                    min_value=0,
                    value=int(acad.get("total_dead_backlogs", 0)) if acad else 0,
                    step=1
                )
                f_gap_years = st.number_input(
                    "Gap Years",
                    min_value=0,
                    value=int(acad.get("gap_years", 0)) if acad else 0,
                    step=1
                )
                f_pass_year = st.number_input(
                    "Passing / Graduation Year",
                    min_value=2020,
                    max_value=2030,
                    value=int(student.get("passing_year", 2026)),
                    step=1
                )
                f_dept_label = st.selectbox(
                    "Department / Branch",
                    list(dept_options.keys()),
                    index=curr_dept_idx
                )

            save_submitted = st.form_submit_button("Save Academic Details", use_container_width=True)
            if save_submitted:
                f_dept_id = dept_options[f_dept_label]
                diploma_val = f_diploma if f_diploma > 0 else None
                hsc_val = f_hsc if f_hsc > 0 else None

                res = save_academic_details(
                    student_id=student["student_id"],
                    ssc_percentage=f_ssc,
                    current_cgpa=f_cgpa,
                    hsc_percentage=hsc_val,
                    diploma_percentage=diploma_val,
                    total_active_backlogs=f_active_backlogs,
                    total_dead_backlogs=f_dead_backlogs,
                    gap_years=f_gap_years,
                    dept_id=f_dept_id,
                    passing_year=f_pass_year
                )
                if res["success"]:
                    st.success("Academic details saved successfully!")
                    st.rerun()
                else:
                    st.error(res["message"])



def render_portfolio_tab(student_id: int):
    """Renders Skills, Projects, Internships & Certifications Management Tab."""
    render_header("My Skills & Portfolio", "Manage your technical inventory and project credentials")

    p_tabs = st.tabs(["💡 Skills", "💻 Projects", "🏢 Internships", "📜 Certifications"])

    # 1. SKILLS
    with p_tabs[0]:
        st.markdown("#### My Technical Skills")
        st_skills = get_student_skills(student_id)
        
        if st_skills:
            df_skills = pd.DataFrame(st_skills)[["skill_name", "skill_category", "proficiency_level"]]
            st.dataframe(df_skills, use_container_width=True)
        else:
            st.info("No skills tagged yet.")

        st.markdown("##### Add New Skill")
        all_skills = get_all_skills()
        skill_opts = {f"{s['skill_name']} ({s['skill_category']})": s["skill_id"] for s in all_skills}
        
        with st.form("add_skill_form"):
            s_name = st.selectbox("Select Skill", list(skill_opts.keys()))
            s_prof = st.selectbox("Proficiency Level", ["Beginner", "Intermediate", "Advanced"])
            if st.form_submit_button("Add Skill"):
                s_id = skill_opts[s_name]
                res = add_student_skill(student_id, s_id, s_prof)
                if res["success"]:
                    st.success("Skill updated successfully!")
                    st.rerun()
                else:
                    st.error(res["message"])

    # 2. PROJECTS
    with p_tabs[1]:
        st.markdown("#### My Projects")
        projects = get_student_projects(student_id)
        if projects:
            for p in projects:
                with st.expander(f"📌 {p['title']} ({p.get('domain') or 'General'})"):
                    st.write(p.get("description") or "No description provided.")
                    st.write(f"**Duration:** {p['duration_months']} month(s)")
                    if p.get("github_url"):
                        st.markdown(f"[🔗 GitHub Repository]({p['github_url']})")
                    if st.button("Delete Project", key=f"del_proj_{p['project_id']}"):
                        delete_project(p['project_id'])
                        st.rerun()
        else:
            st.info("No projects recorded yet.")

        with st.expander("➕ Add New Project"):
            with st.form("add_project_form"):
                p_title = st.text_input("Project Title")
                p_domain = st.text_input("Domain (e.g. Web, ML, Cloud)")
                p_desc = st.text_area("Description")
                p_github = st.text_input("GitHub Repository URL")
                p_dur = st.number_input("Duration (Months)", min_value=1, value=1)
                if st.form_submit_button("Save Project"):
                    res = create_project(student_id, p_title, p_domain, p_desc, p_github, p_dur)
                    if res["success"]:
                        st.success("Project added!")
                        st.rerun()
                    else:
                        st.error(res["message"])

    # 3. INTERNSHIPS
    with p_tabs[2]:
        st.markdown("#### My Internships")
        internships = get_student_internships(student_id)
        if internships:
            for i in internships:
                with st.expander(f"🏢 {i['company_name']} - {i['role']}"):
                    st.write(f"**Duration:** {i['duration_months']} month(s)")
                    if i.get("certificate_url"):
                        st.markdown(f"[🔗 View Certificate]({i['certificate_url']})")
                    if st.button("Delete Internship", key=f"del_int_{i['internship_id']}"):
                        delete_internship(i['internship_id'])
                        st.rerun()
        else:
            st.info("No internships recorded yet.")

        with st.expander("➕ Add Internship"):
            with st.form("add_internship_form"):
                i_comp = st.text_input("Company Name")
                i_role = st.text_input("Role (e.g. Software Intern)")
                i_dur = st.number_input("Duration (Months)", min_value=1, value=2)
                i_cert = st.text_input("Certificate URL")
                if st.form_submit_button("Save Internship"):
                    res = create_internship(student_id, i_comp, i_role, i_dur, i_cert)
                    if res["success"]:
                        st.success("Internship added!")
                        st.rerun()
                    else:
                        st.error(res["message"])

    # 4. CERTIFICATIONS
    with p_tabs[3]:
        st.markdown("#### My Certifications")
        certs = get_student_certifications(student_id)
        if certs:
            for c in certs:
                c_col1, c_col2 = st.columns([3, 1])
                with c_col1:
                    st.write(f"📜 **{c['title']}** — *{c['issuing_organization']}* ({c.get('issue_date') or 'N/A'})")
                with c_col2:
                    if st.button("Delete", key=f"del_cert_{c['cert_id']}"):
                        delete_certification(c['cert_id'])
                        st.rerun()
        else:
            st.info("No certifications recorded yet.")

        with st.expander("➕ Add Certification"):
            with st.form("add_cert_form"):
                c_title = st.text_input("Certification Title")
                c_org = st.text_input("Issuing Organization (e.g. AWS, Coursera)")
                c_date = st.text_input("Issue Date (YYYY-MM-DD)", value="2025-06-01")
                if st.form_submit_button("Save Certification"):
                    res = create_certification(student_id, c_title, c_org, c_date)
                    if res["success"]:
                        st.success("Certification added!")
                        st.rerun()
                    else:
                        st.error(res["message"])


def render_drives_tab(student_id: int):
    """Renders Campus Drives & Real-Time Eligibility Matcher Tab."""
    render_header("Campus Recruitment Drives", "Check real-time eligibility and apply for active opportunities")

    drives = get_all_drives()
    active_drives = [d for d in drives if d.get("status") in ["Upcoming", "Ongoing"]] if drives else []

    if not active_drives:
        st.info("No active campus drives are available at the moment.")
        return

    student_apps = get_student_applications(student_id)
    applied_drive_ids = {a["drive_id"] for a in student_apps}

    eligible_drives = []
    ineligible_drives = []

    for d in active_drives:
        d_id = d["drive_id"]
        eval_res = evaluate_student_eligibility(student_id, d_id)
        if eval_res["is_eligible"]:
            eligible_drives.append((d, eval_res))
        else:
            ineligible_drives.append((d, eval_res))

    # SECTION 1: ELIGIBLE DRIVES
    st.markdown("### ✅ Eligible Companies / Drives")
    if not eligible_drives:
        st.info("No eligible campus drives are currently available.")
    else:
        for d, eval_res in eligible_drives:
            d_id = d["drive_id"]
            details = get_drive_details(d_id)
            reqs = details.get("requirements") or {}
            ctc_val = reqs.get("ctc_lpa")
            ctc_str = f"₹{ctc_val} LPA" if ctc_val else "Package TBD"

            with st.expander(f"🟢 {d['company_name']} — {d['job_title']} ({ctc_str})", expanded=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.write(f"**Company:** {d['company_name']}")
                    st.write(f"**Job / Role:** {d['job_title']}")
                    st.write(f"**Offered Package:** {ctc_str}")
                with c2:
                    st.write(f"**Drive Date:** {d['drive_date']}")
                    st.write(f"**Academic Year:** {d['academic_year']}")
                    st.write("**Eligibility Status:** ✅ Eligible")
                with c3:
                    st.write("")
                    if d_id in applied_drive_ids:
                        st.success("✅ Already Applied")
                    else:
                        if st.button("Apply Now", key=f"apply_{d_id}", use_container_width=True):
                            res = apply_for_drive(student_id, d_id)
                            if res["success"]:
                                st.success("Application submitted successfully!")
                                st.rerun()
                            else:
                                st.warning(res["message"])

    st.write("---")

    # SECTION 2: NOT ELIGIBLE DRIVES
    st.markdown("### ❌ Not Eligible Companies / Drives")
    if not ineligible_drives:
        st.caption("You are eligible for all active recruitment drives!")
    else:
        for d, eval_res in ineligible_drives:
            d_id = d["drive_id"]
            details = get_drive_details(d_id)
            reqs = details.get("requirements") or {}
            ctc_val = reqs.get("ctc_lpa")
            ctc_str = f"₹{ctc_val} LPA" if ctc_val else "Package TBD"

            with st.expander(f"🔴 {d['company_name']} — {d['job_title']} (❌ Not Eligible)"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Company:** {d['company_name']}")
                    st.write(f"**Job / Role:** {d['job_title']}")
                    st.write(f"**Drive Date:** {d['drive_date']}")
                    if reqs:
                        st.write(f"**Min CGPA Required:** {reqs.get('min_cgpa', 'N/A')} | **Max Backlogs:** {reqs.get('max_active_backlogs', 'N/A')}")
                with c2:
                    st.markdown("**❌ Reason(s) for Ineligibility:**")
                    for reason in eval_res["reasons"]:
                        st.markdown(f"• {reason}")



def render_applications_tab(student_id: int):
    """Renders Application Status Tracker & Placement Offer Details."""
    render_header("My Applications & Offers", "Track selection statuses and placement offer letters")

    summary = get_student_placement_summary(student_id)
    apps = summary["applications"]
    placements = summary["placements"]

    c1, c2, c3 = st.columns(3)
    with c1:
        render_kpi_card("Total Applied", str(summary["total_applications"]), "Drive Applications", icon="📑")
    with c2:
        is_p = "YES 🎉" if summary["is_placed"] else "NO"
        render_kpi_card("Placed Status", is_p, "Placement Status", icon="🎯")
    with c3:
        top_ctc = f"₹{placements[0]['offered_ctc']} LPA" if placements else "N/A"
        render_kpi_card("Offered CTC", top_ctc, "Package", icon="💰")

    st.write("---")
    st.markdown("### Submitted Drive Applications")
    if apps:
        df_apps = pd.DataFrame(apps)[["company_name", "job_title", "application_date", "status", "ctc_lpa"]]
        st.dataframe(df_apps, use_container_width=True)
    else:
        st.info("You have not applied for any campus drives yet.")


def render_readiness_and_ml_tab(student_id: int):
    """Renders Explainable Rule-Based Readiness Score & ML Estimated Placement Probability."""
    render_header("Placement Readiness & ML Estimate", "Rule-based candidate strength breakdown & probabilistic ML inference")

    # Save score evaluation log
    save_readiness_evaluation(student_id)
    bd = get_readiness_breakdown(student_id)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏆 Rule-Based Readiness Score")
        st.metric("Composite Readiness Score", f"{bd['total_score']} / 100", f"Level: {bd['readiness_level']}")
        
        # Sub-score progress bars
        comps = bd["components"]
        st.write(f"**Academic Score:** {comps['academic']['score']} / 35.0")
        st.progress(float(comps['academic']['score']) / 35.0)

        st.write(f"**Technical Skills Score:** {comps['skills']['score']} / 30.0")
        st.progress(float(comps['skills']['score']) / 30.0)

        st.write(f"**Projects Score:** {comps['projects']['score']} / 15.0")
        st.progress(float(comps['projects']['score']) / 15.0)

        st.write(f"**Internship Score:** {comps['internships']['score']} / 10.0")
        st.progress(float(comps['internships']['score']) / 10.0)

        st.write(f"**Certifications Score:** {comps['certifications']['score']} / 10.0")
        st.progress(float(comps['certifications']['score']) / 10.0)

    with col2:
        st.markdown("### 🤖 ML Estimated Placement Likelihood")
        
        # Call Phase 8A ML Inference engine
        ml_pred = predict_placement(student_id)

        if "error" not in ml_pred:
            prob_pct = ml_pred["probability_percentage"]
            prob_val = ml_pred["probability"]
            label = ml_pred["prediction_label"]

            st.metric("Model Estimated Probability", prob_pct, f"Classification: {label}")
            st.progress(prob_val)

            st.info(f"ℹ️ **Disclaimer**: {ml_pred['disclaimer']}")
        else:
            st.warning(ml_pred["error"])

    st.write("---")
    c_s, c_i = st.columns(2)
    with c_s:
        st.markdown("#### ✅ Identified Portfolio Strengths")
        if bd["strengths"]:
            for s in bd["strengths"]:
                st.write(f"• {s}")
        else:
            st.write("Keep building your portfolio to unlock key strengths!")

    with c_i:
        st.markdown("#### 💡 Actionable Improvement Recommendations")
        if bd["improvements"]:
            for imp in bd["improvements"]:
                st.write(f"• {imp}")
        else:
            st.write("Great job! Your profile meets high readiness benchmarks.")
