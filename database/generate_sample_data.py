"""
Predictive Campus Placement Analytics System
Synthetic Data Generator Script

This script generates realistic, safe synthetic sample data for:
- 150 Students across 6 Departments
- 30 Technical & Soft Skills
- 12 Companies & 20 Campus Drives
- Drive Requirements, Eligible Departments & Required Skills
- Academic & Semester Records (Semesters 1-6)
- Student Skills, Projects, Internships & Certifications
- Applications, Placements & Readiness Evaluations

Output:
1. Directly inserts data into MySQL if DB connection parameters are configured.
2. Generates 'database/seed_data.sql' as a fallback SQL file for direct execution.
"""

import os
import random
import sys
from datetime import date, timedelta
from werkzeug.security import generate_password_hash


# Check for dotenv package to load credentials if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# DB Configuration from Environment Variables with Defaults
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "campus_placement_db")

# Deterministic Seed for Reproducible Data Generation
random.seed(42)

# ==============================================================================
# SAMPLE MASTER DATA DEFINITIONS
# ==============================================================================

DEPARTMENTS = [
    ("Computer Engineering", "COMP"),
    ("Information Technology", "IT"),
    ("Electronics & Telecommunication", "ENTC"),
    ("Mechanical Engineering", "MECH"),
    ("Electrical Engineering", "ELEC"),
    ("Civil Engineering", "CIVIL")
]

SKILLS = [
    # Programming
    ("Python", "Programming"),
    ("Java", "Programming"),
    ("C++", "Programming"),
    ("JavaScript", "Programming"),
    # Database
    ("MySQL", "Database"),
    ("SQL", "Database"),
    ("MongoDB", "Database"),
    # Core CS
    ("DSA", "Core CS"),
    ("OOP", "Core CS"),
    ("DBMS", "Core CS"),
    ("Operating Systems", "Core CS"),
    ("Computer Networks", "Core CS"),
    # Web
    ("HTML", "Web"),
    ("CSS", "Web"),
    ("React", "Web"),
    ("Node.js", "Web"),
    ("Express.js", "Web"),
    ("REST API", "Web"),
    # Data/AI
    ("Pandas", "Data/AI"),
    ("NumPy", "Data/AI"),
    ("Matplotlib", "Data/AI"),
    ("Seaborn", "Data/AI"),
    ("Machine Learning", "Data/AI"),
    # Cloud/Tools
    ("AWS", "Cloud/Tools"),
    ("Docker", "Cloud/Tools"),
    ("Git", "Cloud/Tools"),
    ("GitHub", "Cloud/Tools"),
    ("Kubernetes", "Cloud/Tools"),
    # Soft Skills
    ("Communication", "Soft Skills"),
    ("Problem Solving", "Soft Skills"),
    ("Teamwork", "Soft Skills")
]

COMPANIES = [
    ("TechNova Solutions", "IT & Software Services", "https://technova.demo.com", "careers@technova.demo.com"),
    ("DataSphere Labs", "Data Analytics & AI", "https://datasphere.demo.com", "hr@datasphere.demo.com"),
    ("CloudBridge Technologies", "Cloud Computing & DevOps", "https://cloudbridge.demo.com", "jobs@cloudbridge.demo.com"),
    ("InnovateX Systems", "Enterprise Software", "https://innovatex.demo.com", "recruitment@innovatex.demo.com"),
    ("FinEdge Analytics", "FinTech & Banking", "https://finedge.demo.com", "talent@finedge.demo.com"),
    ("CodeCraft Technologies", "Product Engineering", "https://codecraft.demo.com", "careers@codecraft.demo.com"),
    ("NextGen Digital", "Digital Transformation", "https://nextgendigital.demo.com", "hr@nextgendigital.demo.com"),
    ("AIWorks Labs", "Machine Learning & Robotics", "https://aiworks.demo.com", "careers@aiworks.demo.com"),
    ("CoreMatrix Engineering", "Industrial Automation", "https://corematrix.demo.com", "recruitment@corematrix.demo.com"),
    ("CyberShield Systems", "Cybersecurity Services", "https://cybershield.demo.com", "talent@cybershield.demo.com"),
    ("QuantumBytes", "Software R&D", "https://quantumbytes.demo.com", "hr@quantumbytes.demo.com"),
    ("Apex Global", "Consulting & IT Services", "https://apexglobal.demo.com", "careers@apexglobal.demo.com")
]

FIRST_NAMES = [
    "Aarav", "Ananya", "Rohan", "Priya", "Aditya", "Neha", "Rahul", "Pooja", "Vikram", "Sneha",
    "Siddharth", "Kavya", "Amit", "Riya", "Yash", "Tanvi", "Karan", "Shreya", "Nikhil", "Isha",
    "Dev", "Meera", "Varun", "Anushka", "Arjun", "Diya", "Harsh", "Simran", "Pranav", "Bhakti",
    "Akash", "Aditi", "Manish", "Swati", "Gaurav", "Nisha", "Sanket", "Ruchika", "Omkar", "Payal",
    "Chetan", "Mansi", "Tejas", "Shruti", "Kunal", "Divya", "Abhishek", "Aishwarya", "Sameer", "Preeti"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patil", "Deshmukh", "Joshi", "Kulkarni", "Gupta", "Mehta", "Shah", "Rao",
    "Nair", "Pawar", "Chavan", "Singh", "Kumar", "Agarwal", "Bhat", "Shinde", "More", "Gaikwad",
    "Jadhav", "Mishra", "Pandey", "Thakur", "Reddy", "Choudhury", "Das", "Sen", "Roy", "Banerjee"
]

DRIVE_TITLES = [
    ("Software Development Engineer", [1, 2], ["Python", "Java", "DSA", "SQL"], 6.5, 7.0, 18.0),
    ("Data Analyst", [1, 2, 3], ["Python", "SQL", "Pandas", "Matplotlib"], 6.0, 5.5, 12.0),
    ("Graduate Engineer Trainee - IT", [1, 2, 3, 4, 5, 6], ["C++", "Java", "OOP", "DBMS"], 6.0, 4.5, 8.0),
    ("Cloud Operations Engineer", [1, 2, 3, 5], ["AWS", "Linux", "Docker", "Computer Networks"], 6.5, 6.0, 14.0),
    ("Full Stack Web Developer", [1, 2], ["JavaScript", "HTML", "CSS", "React", "Node.js"], 7.0, 8.0, 22.0),
    ("Associate QA Automation Engineer", [1, 2, 3], ["Java", "Python", "SQL"], 6.0, 5.0, 9.5),
    ("Machine Learning Engineer", [1, 2], ["Python", "Machine Learning", "Pandas", "NumPy", "DSA"], 7.5, 9.0, 25.0),
    ("Cybersecurity Analyst", [1, 2, 3], ["Computer Networks", "Operating Systems", "Python"], 6.5, 7.5, 16.0),
    ("FinTech Systems Trainee", [1, 2, 5], ["Java", "SQL", "Problem Solving"], 6.5, 6.5, 11.0),
    ("Embedded Software Engineer", [1, 3, 5], ["C++", "Operating Systems", "DSA"], 6.5, 7.0, 13.5),
    ("Business Technology Analyst", [1, 2, 3, 4, 5, 6], ["Communication", "Problem Solving", "SQL"], 6.0, 6.0, 10.0),
    ("Backend API Developer", [1, 2], ["Python", "REST API", "MySQL", "Docker"], 7.0, 8.5, 20.0)
]

def generate_sql_statements():
    """Generates synthetic data SQL insert commands."""
    sql_lines = []
    sql_lines.append("-- ==============================================================================")
    sql_lines.append("-- Synthetic Sample Data Seed Script for campus_placement_db")
    sql_lines.append("-- ==============================================================================\n")
    sql_lines.append("USE campus_placement_db;\n")
    sql_lines.append("SET FOREIGN_KEY_CHECKS = 0;\n")

    # 1. DEPARTMENTS
    sql_lines.append("-- 1. Insert Departments")
    for dept_name, dept_code in DEPARTMENTS:
        sql_lines.append(f"INSERT INTO departments (dept_name, dept_code) VALUES ('{dept_name}', '{dept_code}');")
    sql_lines.append("")

    # 2. SKILLS
    sql_lines.append("-- 2. Insert Master Skills")
    for skill_name, category in SKILLS:
        sql_lines.append(f"INSERT INTO skills (skill_name, skill_category) VALUES ('{skill_name}', '{category}');")
    sql_lines.append("")

    # 3. COMPANIES
    sql_lines.append("-- 3. Insert Companies")
    for name, sector, web, email in COMPANIES:
        sql_lines.append(f"INSERT INTO companies (company_name, industry_sector, website, hr_contact_email) VALUES ('{name}', '{sector}', '{web}', '{email}');")
    sql_lines.append("")

    # 4. USERS & STUDENTS & ACADEMICS
    sql_lines.append("-- 4. Insert Admin User")
    admin_hash = generate_password_hash("Admin@123", method="pbkdf2:sha256")
    sql_lines.append(f"INSERT INTO users (email, password_hash, role) VALUES ('tpo.admin@campus.edu', '{admin_hash}', 'ADMIN');\n")


    sql_lines.append("-- 5. Insert 150 Student Users, Profiles, Academics & Semester History")
    num_students = 150
    student_pass_hash = "pbkdf2:sha256:600000$student_salt$hash_example_student_pass"

    for i in range(1, num_students + 1):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        email = f"student{i:03d}.{fn.lower()}@campus.edu"
        roll = f"2022COMP{i:03d}" if i <= 50 else (f"2022IT{i:03d}" if i <= 80 else f"2022DEPT{i:03d}")
        dept_id = random.randint(1, 6)
        gender = random.choice(["Male", "Female"])
        phone = f"98765{i:05d}"
        passing_year = 2026

        # User insert (user_id will be i + 1 because admin is user_id 1)
        sql_lines.append(f"INSERT INTO users (email, password_hash, role) VALUES ('{email}', '{student_pass_hash}', 'STUDENT');")
        sql_lines.append(f"INSERT INTO students (user_id, roll_number, first_name, last_name, dept_id, gender, phone, passing_year) VALUES ({i + 1}, '{roll}', '{fn}', '{ln}', {dept_id}, '{gender}', '{phone}', {passing_year});")

        # Academic record metrics
        ssc = round(random.uniform(55.0, 95.0), 2)
        is_diploma = random.random() < 0.15
        hsc = "NULL" if is_diploma else str(round(random.uniform(55.0, 95.0), 2))
        diploma = str(round(random.uniform(60.0, 92.0), 2)) if is_diploma else "NULL"
        cgpa = round(random.uniform(5.5, 9.8), 2)
        active_backlogs = 0 if cgpa > 7.5 else random.choice([0, 0, 0, 1, 2])
        dead_backlogs = 0 if active_backlogs == 0 else random.choice([0, 1])
        gap_years = 0 if random.random() > 0.1 else 1

        sql_lines.append(f"INSERT INTO academic_records (student_id, ssc_percentage, hsc_percentage, diploma_percentage, current_cgpa, total_active_backlogs, total_dead_backlogs, gap_years) VALUES ({i}, {ssc}, {hsc}, {diploma}, {cgpa}, {active_backlogs}, {dead_backlogs}, {gap_years});")

        # Semester records (Sem 1 to Sem 6)
        running_cgpa = 6.0
        for sem in range(1, 7):
            sgpa = round(min(10.0, max(4.0, cgpa + random.uniform(-0.8, 0.8))), 2)
            running_cgpa = round((running_cgpa * (sem - 1) + sgpa) / sem, 2)
            sem_backlogs = 0 if sgpa >= 6.5 else random.choice([0, 1])
            sql_lines.append(f"INSERT INTO semester_records (student_id, semester_number, sgpa, cgpa, active_backlogs, dead_backlogs) VALUES ({i}, {sem}, {sgpa}, {running_cgpa}, {sem_backlogs}, 0);")

        # Student skills (Assign 3 to 7 skills per student)
        student_skill_ids = random.sample(range(1, len(SKILLS) + 1), k=random.randint(3, 7))
        for s_id in student_skill_ids:
            prof = random.choice(["Beginner", "Intermediate", "Advanced"])
            sql_lines.append(f"INSERT INTO student_skills (student_id, skill_id, proficiency_level) VALUES ({i}, {s_id}, '{prof}');")

        # Projects (1 to 3 projects)
        for p_idx in range(1, random.randint(2, 4)):
            domain = random.choice(["Web Development", "Machine Learning", "Cloud Infrastructure", "Database Management", "Mobile App"])
            p_title = f"{domain} System - Phase {p_idx}"
            sql_lines.append(f"INSERT INTO projects (student_id, title, domain, description, github_url, duration_months) VALUES ({i}, '{p_title}', '{domain}', 'Developed high-performance scalable solution using modern stack.', 'https://github.com/student{i}/{domain.lower().replace(' ', '-')}', {random.randint(1, 4)});")

        # Internships (50% probability)
        if random.random() > 0.5:
            comp_name = random.choice(COMPANIES)[0]
            sql_lines.append(f"INSERT INTO internships (student_id, company_name, role, duration_months, certificate_url) VALUES ({i}, '{comp_name}', 'Software Intern', {random.randint(2, 6)}, 'https://certificates.demo.com/intern/{i}');")

        # Certifications (60% probability)
        if random.random() > 0.4:
            c_org = random.choice(["AWS Academy", "Coursera", "NPTEL", "Oracle", "Microsoft"])
            sql_lines.append(f"INSERT INTO certifications (student_id, title, issuing_organization, issue_date) VALUES ({i}, 'Certified Developer Specialist', '{c_org}', '2025-06-15');")

    sql_lines.append("")

    # 6. CAMPUS DRIVES, REQUIREMENTS, DEPARTMENTS & SKILLS
    sql_lines.append("-- 6. Insert Campus Drives, Requirements, Eligible Depts & Required Skills")
    drive_id = 1
    for comp_id in range(1, len(COMPANIES) + 1):
        # Create 1 or 2 drives per company
        for d_count in range(1, random.randint(2, 3)):
            drive_info = random.choice(DRIVE_TITLES)
            job_title = f"{drive_info[0]} ({2026})"
            acad_year = 2026
            drive_date = date(2026, random.randint(1, 11), random.randint(1, 28)).strftime("%Y-%m-%d")
            status = random.choice(["Completed", "Completed", "Ongoing", "Upcoming"])

            sql_lines.append(f"INSERT INTO campus_drives (drive_id, company_id, job_title, academic_year, drive_date, status) VALUES ({drive_id}, {comp_id}, '{job_title}', {acad_year}, '{drive_date}', '{status}');")

            # Requirements
            min_cgpa = drive_info[3]
            ctc = drive_info[5]
            sql_lines.append(f"INSERT INTO drive_requirements (drive_id, min_cgpa, min_ssc_pct, min_hsc_pct, max_active_backlogs, max_gap_years, ctc_lpa) VALUES ({drive_id}, {min_cgpa}, 60.00, 60.00, 0, 1, {ctc});")

            # Eligible Departments
            for dept_id in drive_info[1]:
                sql_lines.append(f"INSERT INTO drive_departments (drive_id, dept_id) VALUES ({drive_id}, {dept_id});")

            # Required Skills
            for req_skill_name in drive_info[2]:
                # Find skill_id
                s_id = next((idx + 1 for idx, s in enumerate(SKILLS) if s[0] == req_skill_name), 1)
                sql_lines.append(f"INSERT INTO drive_skills (drive_id, skill_id, min_proficiency, is_mandatory) VALUES ({drive_id}, {s_id}, 'Intermediate', 1);")

            drive_id += 1

    sql_lines.append("")

    # 7. APPLICATIONS & PLACEMENTS
    sql_lines.append("-- 7. Insert Applications & Placements")
    total_drives = drive_id - 1
    app_id = 1

    for s_id in range(1, num_students + 1):
        # Select 2 to 5 random drives to apply for
        applied_drives = random.sample(range(1, total_drives + 1), k=random.randint(2, 5))
        is_already_placed = False

        for d_id in applied_drives:
            app_date = "2026-02-10"
            
            # Determine application status
            if not is_already_placed and random.random() < 0.35:
                status = "Offered"
                is_already_placed = True
            else:
                status = random.choice(["Applied", "Shortlisted", "Assessment", "Interview", "Rejected", "Withdrawn"])

            sql_lines.append(f"INSERT INTO applications (application_id, student_id, drive_id, application_date, status) VALUES ({app_id}, {s_id}, {d_id}, '{app_date}', '{status}');")

            if status == "Offered":
                # Create corresponding Placement record
                ctc_offered = round(random.uniform(6.0, 22.0), 2)
                sql_lines.append(f"INSERT INTO placements (student_id, drive_id, application_id, offered_ctc, offer_letter_date, acceptance_status) VALUES ({s_id}, {d_id}, {app_id}, {ctc_offered}, '2026-03-01', 'Accepted');")

            app_id += 1

    sql_lines.append("")

    # 8. READINESS EVALUATIONS
    sql_lines.append("-- 8. Insert Readiness Score Evaluation Logs")
    for s_id in range(1, num_students + 1):
        # Compute synthetic readiness scores
        acad_score = round(random.uniform(18.0, 34.0), 2)
        skill_score = round(random.uniform(15.0, 28.0), 2)
        proj_score = round(random.uniform(8.0, 15.0), 2)
        intern_score = round(random.uniform(0.0, 10.0), 2)
        cert_score = round(random.uniform(0.0, 10.0), 2)
        overall = round(acad_score + skill_score + proj_score + intern_score + cert_score, 2)

        sql_lines.append(f"INSERT INTO readiness_evaluations (student_id, academic_year, overall_score, academic_score, skill_score, project_score, internship_score, certification_score) VALUES ({s_id}, 2026, {overall}, {acad_score}, {skill_score}, {proj_score}, {intern_score}, {cert_score});")

    sql_lines.append("\nSET FOREIGN_KEY_CHECKS = 1;")
    sql_lines.append("-- Seed script execution completed successfully.")
    return sql_lines


def write_seed_file():
    """Writes seed_data.sql file in database/ folder."""
    lines = generate_sql_statements()
    seed_file_path = os.path.join(os.path.dirname(__file__), "seed_data.sql")
    with open(seed_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[SUCCESS] Synthetic dataset SQL generated successfully at: {seed_file_path}")


def try_direct_mysql_insert():
    """Attempts direct insert to MySQL database if driver is available."""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()
        print(f"[INFO] Connected to MySQL database '{MYSQL_DATABASE}' successfully. Seeding data...")

        # Read generated SQL lines
        lines = generate_sql_statements()
        sql_script = "\n".join(lines)
        
        # Execute multi-statement SQL script
        for statement in sql_script.split(";"):
            stmt = statement.strip()
            if stmt and not stmt.startswith("--"):
                cursor.execute(stmt)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("[SUCCESS] Direct MySQL database seeding completed successfully!")
    except Exception as e:
        print(f"[NOTE] Direct MySQL insertion skipped ({e}).")
        print("[INFO] Fallback 'database/seed_data.sql' file created for manual execution.")


if __name__ == "__main__":
    print("==========================================================================")
    print("Predictive Campus Placement Analytics System - Synthetic Data Generator")
    print("==========================================================================")
    write_seed_file()
    try_direct_mysql_insert()
