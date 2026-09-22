"""
Predictive Campus Placement Analytics System
Main Streamlit Web Application Entry Point

Run with:
    streamlit run ui/app.py
"""

import os
import sys

# Ensure parent project root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

from modules.auth import login_user, register_user
from ui.styles import inject_custom_css
from ui.student_views import render_student_dashboard
from ui.admin_views import render_admin_dashboard


def main():
    # Page Configuration
    st.set_page_config(
        page_title="Campus Placement Analytics",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inject Custom CSS Styling
    inject_custom_css()

    # Session State Initialization
    if "user" not in st.session_state:
        st.session_state["user"] = None

    # Router logic: If logged in, show portal; else show Login/Signup page
    user = st.session_state["user"]

    if user is None:
        render_authentication_page()
    else:
        render_portal_header(user)
        if user["role"] == "ADMIN":
            render_admin_dashboard(user)
        else:
            render_student_dashboard(user)


def render_portal_header(user: dict):
    """Renders top header banner and sidebar logout option."""
    st.sidebar.markdown("<div class='sidebar-brand'>🎓 Campus Placement Analytics</div>", unsafe_allow_html=True)
    st.sidebar.write(f"Logged in as: **{user['email']}**")
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state["user"] = None
        st.rerun()


def render_authentication_page():
    """Renders Login & Account Registration View."""
    st.markdown("<h1 style='text-align: center; color: #4F46E5;'>🎓 Predictive Campus Placement Analytics System</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Student Portfolio Management, Dynamic Eligibility Matching, Placement Readiness & Analytics Portal</p>", unsafe_allow_html=True)
    st.write("---")

    _, col_login, _ = st.columns([1, 2, 1])

    with col_login:
        auth_tab = st.tabs(["👨‍🎓 Student Login", "🛠️ TPO / Admin Login", "📝 Student Signup"])

        # 1. STUDENT LOGIN FORM
        with auth_tab[0]:
            st.markdown("### Student Login")
            with st.form("student_login_form"):
                email = st.text_input("Student Email Address", placeholder="e.g. student001.aarav@campus.edu")
                password = st.text_input("Password", type="password", key="student_pass_input")
                submitted = st.form_submit_button("Sign In as Student", use_container_width=True)

                if submitted:
                    res = login_user(email, password)
                    if res["success"]:
                        st.session_state["user"] = res["user"]
                        st.success("Login successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error(res["message"])

        # 2. TPO / ADMIN LOGIN FORM
        with auth_tab[1]:
            st.markdown("### TPO / Admin Login")
            with st.form("admin_login_form"):
                admin_email = st.text_input("TPO / Admin Email Address", placeholder="e.g. tpo.admin@campus.edu")
                admin_password = st.text_input("Password", type="password", key="admin_pass_input")
                submitted_admin = st.form_submit_button("Sign In as TPO Admin", use_container_width=True)

                if submitted_admin:
                    res = login_user(admin_email, admin_password)
                    if res["success"]:
                        if res["user"]["role"] != "ADMIN":
                            st.error("❌ Access Denied: This account does not have TPO/Admin privileges. Please use Student Login.")
                        else:
                            st.session_state["user"] = res["user"]
                            st.success("TPO Admin login successful! Redirecting...")
                            st.rerun()
                    else:
                        st.error(res["message"])

        # 3. STUDENT SIGNUP FORM
        with auth_tab[2]:
            st.markdown("### Student Account Registration")
            with st.form("signup_form"):
                reg_email = st.text_input("Email Address", placeholder="student.name@campus.edu")
                reg_pass = st.text_input("Password (min 6 chars)", type="password", key="signup_pass_input")
                reg_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm_pass_input")
                submitted_reg = st.form_submit_button("Create Account", use_container_width=True)

                if submitted_reg:
                    res = register_user(reg_email, reg_pass, reg_confirm, role="STUDENT")
                    if res["success"]:
                        st.success("Account created successfully! Please log in.")
                    else:
                        st.error(res["message"])

        st.write("")
        st.caption("💡 **Note**: Passwords are securely hashed using PBKDF2:SHA256 algorithm.")




if __name__ == "__main__":
    main()
#C:\Users\HP\PycharmProjects\.venv\Scripts\python.exe -m streamlit run C:\Users\HP\PycharmProjects\CampusPlacementAnalytics\ui\app.py