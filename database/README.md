# Database Foundation Documentation: Predictive Campus Placement Analytics System

## Database Overview
- **Database Name**: `campus_placement_db`
- **Database Engine**: MySQL 8.0+ (InnoDB Storage Engine)
- **Character Set**: `utf8mb4` (Collation: `utf8mb4_unicode_ci`)

The database foundation provides a normalized, high-performance relational schema supporting student portfolio management, dynamic campus drive eligibility matching, multi-criteria application tracking, placement reporting, and explainable placement-readiness score history.

---

## Table Summary & Entity Purpose

| # | Table Name | Purpose / Function | Key Constraints |
| :--- | :--- | :--- | :--- |
| **1** | `users` | System login accounts, hashed passwords, roles (`STUDENT`, `ADMIN`). | `UNIQUE(email)` |
| **2** | `departments` | Master academic branches/departments (COMP, IT, ENTC, etc.). | `UNIQUE(dept_name, dept_code)` |
| **3** | `students` | Core student profile details linked 1-to-1 with a user login. | `UNIQUE(user_id, roll_number)` |
| **4** | `academic_records` | Summary of 10th/12th/Diploma percentages, current CGPA, backlogs & gap years. | `UNIQUE(student_id)`, `CGPA 0-10`, `% 0-100` |
| **5** | `semester_records` | Semester-by-semester SGPA, CGPA, and backlog history (Semesters 1 to 8). | `UNIQUE(student_id, semester_number)` |
| **6** | `skills` | Master skill catalog categorized into Programming, DB, Core CS, Web, Data/AI, etc. | `UNIQUE(skill_name)` |
| **7** | `student_skills` | Dynamic skills tagged by students with proficiency levels (Beginner, Inter, Adv). | `UNIQUE(student_id, skill_id)` |
| **8** | `projects` | Academic and personal projects with domain descriptions and GitHub links. | `duration_months > 0` |
| **9** | `internships` | Industrial training and internship experience logs. | `duration_months > 0` |
| **10** | `certifications` | Professional skill certifications earned by students. | Foreign Key -> `students` |
| **11** | `companies` | Directory of corporate recruiters and industry sectors. | `UNIQUE(company_name)` |
| **12** | `campus_drives` | Specific recruitment drives conducted by companies for an academic year. | Foreign Key -> `companies` |
| **13** | `drive_requirements` | Dynamic eligibility benchmarks (Min CGPA, Min %, Max backlogs, CTC). | `UNIQUE(drive_id)` |
| **14** | `drive_departments` | Junction table defining eligible academic departments for a drive. | `UNIQUE(drive_id, dept_id)` |
| **15** | `drive_skills` | Junction table defining required technical skills for a drive. | `UNIQUE(drive_id, skill_id)` |
| **16** | `applications` | Student drive applications and multi-stage hiring selection status. | `UNIQUE(student_id, drive_id)` |
| **17** | `placements` | Final job offer records resulting from successful applications. | `UNIQUE(application_id)` |
| **18** | `readiness_evaluations` | Historical log of rule-based placement readiness evaluations over time. | `overall_score 0-100` |

---

## Database Credentials Setup

1. Copy the environment configuration template:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` with your local MySQL credentials:
   ```env
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_actual_mysql_password
   MYSQL_DATABASE=campus_placement_db
   ```

---

## Execution Guide

### Step 1: Create Database Schema (`schema.sql`)

Execute `schema.sql` via MySQL Command Line Client or PyCharm / MySQL Workbench:

**Option A: Using MySQL Command Line**
```bash
mysql -u root -p < database/schema.sql
```

**Option B: Inside MySQL Client / Workbench**
```sql
SOURCE database/schema.sql;
```

---

### Step 2: Generate & Populate Synthetic Sample Data

**Option A: Run Python Generator Script (Automatic)**
```bash
python database/generate_sample_data.py
```
*Note: If `mysql-connector-python` is installed and credentials in `.env` are valid, data is directly inserted into MySQL. Additionally, `database/seed_data.sql` is generated.*

**Option B: Execute `seed_data.sql` directly in MySQL**
```bash
mysql -u root -p campus_placement_db < database/seed_data.sql
```

---

## Expected Sample Data Volume

The synthetic dataset generates realistic, safe test data:
- **Users & Students**: 150 Student Profiles + 1 TPO Admin User
- **Departments**: 6 Academic Branches (COMP, IT, ENTC, MECH, ELEC, CIVIL)
- **Skills**: 30 Master Skills across 7 Categories
- **Companies**: 12 Recruiter Companies
- **Campus Drives**: ~20 Active/Completed Campus Drives
- **Applications**: ~450 Application Records across various selection statuses
- **Placements**: ~50+ Verified Placement Offer Records
- **Readiness Logs**: 150 Historical Placement Readiness Scorecard Records

---

## Verification SQL Queries

Run the following queries to verify schema and data setup:

```sql
USE campus_placement_db;

-- 1. Check all 18 tables created
SHOW TABLES;

-- 2. Verify student registry count
SELECT COUNT(*) AS total_students FROM students;

-- 3. Verify company and drive counts
SELECT COUNT(*) AS total_companies FROM companies;
SELECT COUNT(*) AS total_drives FROM campus_drives;

-- 4. Verify applications & placement offer counts
SELECT status, COUNT(*) AS application_count 
FROM applications 
GROUP BY status;

SELECT COUNT(*) AS total_placements, AVG(offered_ctc) AS avg_package_lpa 
FROM placements;

-- 5. Verify readiness evaluations log
SELECT COUNT(*) AS readiness_eval_records, AVG(overall_score) AS avg_readiness_score 
FROM readiness_evaluations;
```
