"""
TPO Admin Portal Views Module

Implements Admin Dashboard UI tabs:
1. Executive Placement Dashboard (Macro KPIs & Department Bar Charts)
2. Company & Campus Drive Manager (Create Drives, Set Eligibility Criteria)
3. Student Master Registry (Search & Filter 150+ Student Profiles)
4. Application Funnel & Placement Offer Logger
5. Skill Demand & Salary Analytics
6. ML Model Diagnostics & Retraining Panel
"""

import streamlit as st
import pandas as pd

from modules.student_manager import get_all_students, get_all_departments, get_student_by_id
from modules.company_manager import (
    get_all_companies,
    create_company,
    get_all_drives,
    create_drive,
    get_drive_details,
    set_drive_requirements,
    add_drive_department,
    add_drive_skill
)
from modules.portfolio_manager import get_all_skills
from modules.application_manager import (
    get_drive_applications,
    update_application_status,
    record_placement_offer
)
from modules.analytics_engine import (
    get_overall_placement_stats,
    get_department_placement_stats,
    get_company_placement_stats,
    get_package_statistics,
    get_skill_demand_stats,
    get_readiness_placement_analysis
)
from modules.ml_model import get_model_metrics, get_feature_importance, train_model
from ui.components import (
    render_header,
    render_kpi_card,
    render_bar_chart,
    render_donut_chart
)


def render_admin_dashboard(user: dict):
    """Main rendering entry point for logged-in TPO Admin users."""
    st.sidebar.markdown(f"**Admin:** {user['email']}")
    st.sidebar.markdown("**Role:** TPO Administrator")

    tabs = st.tabs([
        "📈 Executive Dashboard",
        "🏢 Companies & Drives",
        "📋 Student Registry",
        "📑 Applications & Offers",
        "📊 Skill & Package Analytics",
        "🤖 ML Diagnostics"
    ])

    with tabs[0]:
        render_executive_dashboard_tab()

    with tabs[1]:
        render_company_and_drives_tab()

    with tabs[2]:
        render_student_registry_tab()

    with tabs[3]:
        render_applications_and_offers_tab()

    with tabs[4]:
        render_analytics_tab()

    with tabs[5]:
        render_ml_diagnostics_tab()


def render_executive_dashboard_tab():
    """Renders Macro KPI cards and institutional placement charts."""
    render_header("Training & Placement Executive Dashboard", "Macro institutional placement metrics & department performance")

    stats = get_overall_placement_stats()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_kpi_card("Total Students", str(stats["total_students"]), "Registered Candidates", icon="👨‍🎓")
    with col2:
        render_kpi_card("Placed Students", str(stats["placed_students"]), f"{stats['placement_percentage']}% Placed", icon="🎉")
    with col3:
        render_kpi_card("Placement Rate", f"{stats['placement_percentage']}%", "Success Rate", icon="📈")
    with col4:
        render_kpi_card("Average Package", f"₹{stats['average_ctc_lpa']} LPA", "Mean CTC Offered", icon="💰")
    with col5:
        render_kpi_card("Active Companies", str(stats["total_companies"]), f"{stats['total_drives']} Drives", icon="🏢")

    st.write("---")

    c1, c2 = st.columns(2)
    with c1:
        dept_data = get_department_placement_stats()
        if dept_data:
            df_dept = pd.DataFrame(dept_data)
            render_bar_chart(
                df_dept,
                x_col="dept_code",
                y_col="placement_percentage",
                title="Department Placement Success Rate (%)"
            )
    with c2:
        df_outcome = pd.DataFrame([
            {"Status": "Placed", "Count": stats["placed_students"]},
            {"Status": "Unplaced", "Count": stats["unplaced_students"]}
        ])
        render_donut_chart(df_outcome, names_col="Status", values_col="Count", title="Overall Placement Outcome Distribution")


def render_company_and_drives_tab():
    """Renders Company and Campus Drive Management forms."""
    render_header("Company & Campus Drive Manager", "Post new drives and set academic eligibility requirements")

    c_tabs = st.tabs(["🏢 Recruiter Companies", "🎯 Post Campus Drive", "⚙️ Drive Requirements"])

    # 1. COMPANIES
    with c_tabs[0]:
        st.markdown("#### Registered Companies")
        comps = get_all_companies()
        if comps:
            df_comps = pd.DataFrame(comps)[["company_id", "company_name", "industry_sector", "website", "hr_contact_email"]]
            st.dataframe(df_comps, use_container_width=True)

        with st.expander("➕ Add New Recruiter Company"):
            with st.form("add_company_form"):
                c_name = st.text_input("Company Name")
                c_sec = st.text_input("Industry Sector (e.g. IT, FinTech)")
                c_web = st.text_input("Website URL")
                c_email = st.text_input("HR Contact Email")
                if st.form_submit_button("Create Company"):
                    res = create_company(c_name, c_sec, c_web, c_email)
                    if res["success"]:
                        st.success("Company added!")
                        st.rerun()
                    else:
                        st.error(res["message"])

    # 2. CAMPUS DRIVES
    with c_tabs[1]:
        st.markdown("#### Campus Placement Drives")
        drives = get_all_drives()
        if drives:
            df_drives = pd.DataFrame(drives)[["drive_id", "company_name", "job_title", "academic_year", "drive_date", "status"]]
            st.dataframe(df_drives, use_container_width=True)

        with st.expander("➕ Post New Campus Drive"):
            comps = get_all_companies()
            if not comps:
                st.info("No recruiter companies registered yet. Please add a company first.")
            else:
                comp_opts = {c["company_name"]: c["company_id"] for c in comps}
                with st.form("add_drive_form"):
                    d_comp = st.selectbox("Company", list(comp_opts.keys()))
                    d_title = st.text_input("Job Title / Role")
                    d_year = st.number_input("Academic Year", min_value=2020, max_value=2030, value=2026)
                    d_date = st.text_input("Drive Date (YYYY-MM-DD)", value="2026-10-15")
                    d_status = st.selectbox("Status", ["Upcoming", "Ongoing", "Completed", "Cancelled"])
                    if st.form_submit_button("Post Drive"):
                        comp_id = comp_opts[d_comp]
                        res = create_drive(comp_id, d_title, d_year, d_date, d_status)
                        if res["success"]:
                            st.success("Campus Drive posted!")
                            st.rerun()
                        else:
                            st.error(res["message"])

    # 3. DRIVE REQUIREMENTS
    with c_tabs[2]:
        st.markdown("#### Set Drive Eligibility Benchmarks")
        drives = get_all_drives()
        if not drives:
            st.info("No active drives to configure.")
            return

        drive_opts = {f"{d['company_name']} - {d['job_title']} (ID:{d['drive_id']})": d["drive_id"] for d in drives}
        selected_drive_name = st.selectbox("Select Campus Drive to Configure", list(drive_opts.keys()))
        selected_drive_id = drive_opts[selected_drive_name]

        dt_details = get_drive_details(selected_drive_id)
        current_req = dt_details["requirements"] or {}

        with st.form("drive_req_form"):
            c1, c2 = st.columns(2)
            with c1:
                min_cgpa = st.number_input("Min CGPA Required", min_value=0.0, max_value=10.0, value=float(current_req.get("min_cgpa", 6.0)))
                min_ssc = st.number_input("Min SSC % Required", min_value=0.0, max_value=100.0, value=float(current_req.get("min_ssc_pct", 60.0)))
                min_hsc = st.number_input("Min HSC/Diploma % Required", min_value=0.0, max_value=100.0, value=float(current_req.get("min_hsc_pct", 60.0)))
            with c2:
                max_backlogs = st.number_input("Max Active Backlogs Allowed", min_value=0, value=int(current_req.get("max_active_backlogs", 0)))
                max_gap = st.number_input("Max Gap Years Allowed", min_value=0, value=int(current_req.get("max_gap_years", 0)))
                ctc = st.number_input("Offered CTC (LPA)", min_value=0.1, value=float(current_req.get("ctc_lpa", 8.0)))

            if st.form_submit_button("Save Drive Requirements"):
                res = set_drive_requirements(selected_drive_id, min_cgpa, min_ssc, min_hsc, max_backlogs, max_gap, ctc)
                if res["success"]:
                    st.success("Eligibility requirements updated!")
                    st.rerun()
                else:
                    st.error(res["message"])


def render_student_registry_tab():
    """Renders Student Master Registry with filters."""
    render_header("Student Master Registry", "Search and filter registered student candidates")

    depts = get_all_departments()
    dept_filter_opts = {"All Departments": None}
    dept_filter_opts.update({d["dept_name"]: d["dept_id"] for d in depts})

    c1, c2 = st.columns(2)
    with c1:
        selected_dept_label = st.selectbox("Filter by Department", list(dept_filter_opts.keys()))
    with c2:
        search_query = st.text_input("Search Candidate (Name, Roll No, Email)")

    selected_dept_id = dept_filter_opts[selected_dept_label]
    students = get_all_students(dept_id=selected_dept_id)

    if search_query.strip():
        sq = search_query.lower()
        students = [
            s for s in students 
            if sq in s["first_name"].lower() or sq in s["last_name"].lower() or sq in s["roll_number"].lower() or sq in s["email"].lower()
        ]

    st.write(f"Showing **{len(students)}** student candidate(s).")
    if students:
        df_students = pd.DataFrame(students)[["student_id", "roll_number", "first_name", "last_name", "dept_name", "gender", "passing_year", "email"]]
        st.dataframe(df_students, use_container_width=True)


def render_applications_and_offers_tab():
    """Renders Drive Application Status Funnel and Placement Logger."""
    render_header("Applications & Placement Offers", "Manage selection status pipeline and log verified offers")

    drives = get_all_drives()
    if not drives:
        st.info("No active drives.")
        return

    drive_opts = {f"{d['company_name']} - {d['job_title']} (ID:{d['drive_id']})": d["drive_id"] for d in drives}
    selected_drive_label = st.selectbox("Select Drive", list(drive_opts.keys()), key="admin_app_drive_select")
    selected_drive_id = drive_opts[selected_drive_label]

    apps = get_drive_applications(selected_drive_id)
    st.write(f"Total Applications Received: **{len(apps)}**")

    if apps:
        for app in apps:
            app_id = app["application_id"]
            with st.expander(f"👤 {app['first_name']} {app['last_name']} (`{app['roll_number']}`) — Status: {app['status']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Department:** {app['dept_name']}")
                    st.write(f"**CGPA:** {app.get('current_cgpa') or 'N/A'}")
                    st.write(f"**Application Date:** {app['application_date']}")
                with c2:
                    new_status = st.selectbox(
                        "Update Status",
                        ["Applied", "Shortlisted", "Assessment", "Interview", "Offered", "Accepted", "Rejected", "Withdrawn"],
                        index=["Applied", "Shortlisted", "Assessment", "Interview", "Offered", "Accepted", "Rejected", "Withdrawn"].index(app["status"]) if app["status"] in ["Applied", "Shortlisted", "Assessment", "Interview", "Offered", "Accepted", "Rejected", "Withdrawn"] else 0,
                        key=f"status_select_{app_id}"
                    )
                    if st.button("Update Status", key=f"btn_up_status_{app_id}"):
                        update_application_status(app_id, new_status)
                        st.rerun()

                # Offer Logger
                if new_status in ["Offered", "Accepted"]:
                    st.write("---")
                    st.markdown("##### 💰 Log Placement Offer Details")
                    with st.form(f"log_offer_form_{app_id}"):
                        ctc = st.number_input("Offered CTC (LPA)", min_value=0.1, value=8.5)
                        acc = st.selectbox("Acceptance Status", ["Accepted", "Pending", "Declined"])
                        if st.form_submit_button("Record Offer"):
                            res = record_placement_offer(app_id, ctc, acceptance_status=acc)
                            if res["success"]:
                                st.success("Placement offer recorded!")
                                st.rerun()
                            else:
                                st.error(res["message"])


def render_analytics_tab():
    """Renders Skill Demand Statistics and Salary Package Distributions."""
    render_header("Skill & Salary Analytics", "Market skill supply vs. demand frequency and compensation distributions")

    st.markdown("### 💰 Compensation Package Statistics (CTC LPA)")
    pkg = get_package_statistics()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Total Placement Offers", str(pkg["total_offers"]), "Verified Offers", icon="📜")
    with c2:
        render_kpi_card("Average Package", f"₹{pkg['average_ctc']} LPA", "Mean CTC", icon="💰")
    with c3:
        render_kpi_card("Median Package", f"₹{pkg['median_ctc']} LPA", "50th Percentile", icon="📊")
    with c4:
        render_kpi_card("Highest Package", f"₹{pkg['highest_ctc']} LPA", "Peak Offer", icon="🚀")

    st.write("---")
    st.markdown("### 💡 Skill Supply vs Market Demand Frequency")
    skills_stat = get_skill_demand_stats()
    if skills_stat:
        df_skills = pd.DataFrame(skills_stat)[["skill_name", "skill_category", "student_count", "drive_count"]]
        render_bar_chart(
            df_skills.head(15),
            x_col="skill_name",
            y_col="drive_count",
            title="Top 15 Most Demanded Skills by Campus Drives"
        )
        st.dataframe(df_skills, use_container_width=True)


def render_ml_diagnostics_tab():
    """Renders Machine Learning Model Evaluation Metrics & Retraining Panel."""
    render_header("Machine Learning Model Diagnostics", "Evaluate model accuracy, precision, recall, confusion matrix & retraining")

    metrics = get_model_metrics()
    if not metrics:
        st.warning("ML Model metrics not loaded.")
        return

    st.markdown(f"### Model Architecture: `{metrics.get('model_type', 'Logistic Regression').upper()}`")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_kpi_card("Accuracy", f"{metrics.get('accuracy', 0.0)*100:.1f}%", "Test Set Accuracy", icon="🎯")
    with c2:
        render_kpi_card("Precision", f"{metrics.get('precision', 0.0)*100:.1f}%", "Positive Predictive Value", icon="🎯")
    with c3:
        render_kpi_card("Recall", f"{metrics.get('recall', 0.0)*100:.1f}%", "True Positive Rate", icon="🔍")
    with c4:
        render_kpi_card("F1-Score", f"{metrics.get('f1_score', 0.0):.4f}", "Harmonic Mean", icon="⚖️")
    with c5:
        render_kpi_card("ROC-AUC", f"{metrics.get('roc_auc', 0.0):.4f}", "Area Under Curve", icon="📈")

    st.write("---")

    col_cm, col_imp = st.columns(2)
    with col_cm:
        st.markdown("#### 🧩 Confusion Matrix")
        cm = metrics.get("confusion_matrix", [[0, 0], [0, 0]])
        df_cm = pd.DataFrame(
            cm,
            index=["Actual Unplaced", "Actual Placed"],
            columns=["Predicted Unplaced", "Predicted Placed"]
        )
        st.dataframe(df_cm, use_container_width=True)
        st.caption("• **Accuracy**: Proportion of overall correct classifications.")
        st.caption("• **Precision**: Ratio of true placed predictions to all predicted placed.")
        st.caption("• **Recall**: Ratio of true placed predictions to actual placed candidates.")

    with col_imp:
        st.markdown("#### 🔍 Model Feature Importance / Coefficients")
        imps = get_feature_importance()
        if imps:
            df_imp = pd.DataFrame(imps)
            render_bar_chart(df_imp, x_col="feature", y_col="importance", title="Feature Coefficients (Model Input Drivers)")

    st.write("---")
    st.markdown("#### 🔄 Retrain Machine Learning Model")
    col_sel, col_btn = st.columns([2, 1])
    with col_sel:
        m_type = st.selectbox("Select Model Algorithm", ["logistic", "random_forest"])
    with col_btn:
        st.write("")
        st.write("")
        if st.button("Retrain Model"):
            res = train_model(m_type)
            if res["success"]:
                st.success("Model retrained successfully!")
                st.rerun()
            else:
                st.error(res["message"])
