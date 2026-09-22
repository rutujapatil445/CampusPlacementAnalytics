-- ==============================================================================
-- Predictive Campus Placement Analytics System
-- Database Initialization DDL Script (MySQL 8.0+)
-- Database Name: campus_placement_db
-- Engine: InnoDB
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS campus_placement_db
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;

USE campus_placement_db;

-- Disable Foreign Key Checks temporarily for clean creation/recreation
SET FOREIGN_KEY_CHECKS = 0;

-- Drop tables in reverse dependency order if they exist
DROP TABLE IF EXISTS readiness_evaluations;
DROP TABLE IF EXISTS placements;
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS drive_skills;
DROP TABLE IF EXISTS drive_departments;
DROP TABLE IF EXISTS drive_requirements;
DROP TABLE IF EXISTS campus_drives;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS certifications;
DROP TABLE IF EXISTS internships;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS student_skills;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS semester_records;
DROP TABLE IF EXISTS academic_records;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- ==============================================================================
-- 1. USERS TABLE
-- Stores login accounts, hashed passwords, and system access roles.
-- ==============================================================================
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('STUDENT', 'ADMIN') NOT NULL DEFAULT 'STUDENT',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 2. DEPARTMENTS TABLE
-- Master table for academic branches/departments.
-- ==============================================================================
CREATE TABLE departments (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL UNIQUE,
    dept_code VARCHAR(10) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 3. STUDENTS TABLE
-- Core profile information for registered students.
-- ==============================================================================
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    roll_number VARCHAR(20) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    dept_id INT NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    phone VARCHAR(15) DEFAULT NULL,
    passing_year INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE RESTRICT,
    INDEX idx_students_dept (dept_id),
    INDEX idx_students_year (passing_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 4. ACADEMIC_RECORDS TABLE
-- Overall academic performance summary for a student.
-- ==============================================================================
CREATE TABLE academic_records (
    academic_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL UNIQUE,
    ssc_percentage DECIMAL(5,2) NOT NULL CHECK (ssc_percentage BETWEEN 0.00 AND 100.00),
    hsc_percentage DECIMAL(5,2) DEFAULT NULL CHECK (hsc_percentage IS NULL OR hsc_percentage BETWEEN 0.00 AND 100.00),
    diploma_percentage DECIMAL(5,2) DEFAULT NULL CHECK (diploma_percentage IS NULL OR diploma_percentage BETWEEN 0.00 AND 100.00),
    current_cgpa DECIMAL(4,2) NOT NULL CHECK (current_cgpa BETWEEN 0.00 AND 10.00),
    total_active_backlogs INT NOT NULL DEFAULT 0 CHECK (total_active_backlogs >= 0),
    total_dead_backlogs INT NOT NULL DEFAULT 0 CHECK (total_dead_backlogs >= 0),
    gap_years INT NOT NULL DEFAULT 0 CHECK (gap_years >= 0),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    INDEX idx_academics_cgpa (current_cgpa),
    INDEX idx_academics_backlogs (total_active_backlogs)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 5. SEMESTER_RECORDS TABLE
-- Semester-by-semester SGPA, CGPA, and backlog history.
-- ==============================================================================
CREATE TABLE semester_records (
    semester_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    semester_number INT NOT NULL CHECK (semester_number BETWEEN 1 AND 8),
    sgpa DECIMAL(4,2) NOT NULL CHECK (sgpa BETWEEN 0.00 AND 10.00),
    cgpa DECIMAL(4,2) NOT NULL CHECK (cgpa BETWEEN 0.00 AND 10.00),
    active_backlogs INT NOT NULL DEFAULT 0 CHECK (active_backlogs >= 0),
    dead_backlogs INT NOT NULL DEFAULT 0 CHECK (dead_backlogs >= 0),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT uk_student_semester UNIQUE (student_id, semester_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 6. SKILLS TABLE
-- Master repository of technical, core CS, web, data, and soft skills.
-- ==============================================================================
CREATE TABLE skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(50) NOT NULL UNIQUE,
    skill_category ENUM('Programming', 'Database', 'Core CS', 'Web', 'Data/AI', 'Cloud/Tools', 'Soft Skills') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 7. STUDENT_SKILLS TABLE
-- Dynamic skills tagged by students along with proficiency levels.
-- ==============================================================================
CREATE TABLE student_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    skill_id INT NOT NULL,
    proficiency_level ENUM('Beginner', 'Intermediate', 'Advanced') NOT NULL DEFAULT 'Intermediate',
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
    CONSTRAINT uk_student_skill UNIQUE (student_id, skill_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 8. PROJECTS TABLE
-- Academic & personal projects completed by students.
-- ==============================================================================
CREATE TABLE projects (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    domain VARCHAR(100) DEFAULT NULL,
    description TEXT DEFAULT NULL,
    github_url VARCHAR(255) DEFAULT NULL,
    duration_months INT NOT NULL DEFAULT 1 CHECK (duration_months > 0),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 9. INTERNSHIPS TABLE
-- Industrial training and internship experience records.
-- ==============================================================================
CREATE TABLE internships (
    internship_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    company_name VARCHAR(100) NOT NULL,
    role VARCHAR(100) NOT NULL,
    duration_months INT NOT NULL CHECK (duration_months > 0),
    certificate_url VARCHAR(255) DEFAULT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 10. CERTIFICATIONS TABLE
-- Professional skill certifications earned by students.
-- ==============================================================================
CREATE TABLE certifications (
    cert_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    issuing_organization VARCHAR(100) NOT NULL,
    issue_date DATE DEFAULT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 11. COMPANIES TABLE
-- Corporate recruiter directory.
-- ==============================================================================
CREATE TABLE companies (
    company_id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL UNIQUE,
    industry_sector VARCHAR(100) DEFAULT NULL,
    website VARCHAR(255) DEFAULT NULL,
    hr_contact_email VARCHAR(120) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 12. CAMPUS_DRIVES TABLE
-- Specific recruitment drives conducted by companies.
-- ==============================================================================
CREATE TABLE campus_drives (
    drive_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    academic_year INT NOT NULL,
    drive_date DATE NOT NULL,
    status ENUM('Upcoming', 'Ongoing', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Upcoming',
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
    INDEX idx_drives_year (academic_year),
    INDEX idx_drives_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 13. DRIVE_REQUIREMENTS TABLE
-- Eligibility criteria rules (CGPA, marks, backlogs, package) set for a drive.
-- ==============================================================================
CREATE TABLE drive_requirements (
    requirement_id INT AUTO_INCREMENT PRIMARY KEY,
    drive_id INT NOT NULL UNIQUE,
    min_cgpa DECIMAL(4,2) NOT NULL DEFAULT 6.00 CHECK (min_cgpa BETWEEN 0.00 AND 10.00),
    min_ssc_pct DECIMAL(5,2) NOT NULL DEFAULT 60.00 CHECK (min_ssc_pct BETWEEN 0.00 AND 100.00),
    min_hsc_pct DECIMAL(5,2) NOT NULL DEFAULT 60.00 CHECK (min_hsc_pct BETWEEN 0.00 AND 100.00),
    max_active_backlogs INT NOT NULL DEFAULT 0 CHECK (max_active_backlogs >= 0),
    max_gap_years INT NOT NULL DEFAULT 0 CHECK (max_gap_years >= 0),
    ctc_lpa DECIMAL(5,2) NOT NULL CHECK (ctc_lpa > 0.00),
    FOREIGN KEY (drive_id) REFERENCES campus_drives(drive_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 14. DRIVE_DEPARTMENTS TABLE
-- Junction table specifying which academic departments are eligible for a drive.
-- ==============================================================================
CREATE TABLE drive_departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    drive_id INT NOT NULL,
    dept_id INT NOT NULL,
    FOREIGN KEY (drive_id) REFERENCES campus_drives(drive_id) ON DELETE CASCADE,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE CASCADE,
    CONSTRAINT uk_drive_dept UNIQUE (drive_id, dept_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 15. DRIVE_SKILLS TABLE
-- Junction table mapping technical skills required by a campus drive.
-- ==============================================================================
CREATE TABLE drive_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    drive_id INT NOT NULL,
    skill_id INT NOT NULL,
    min_proficiency ENUM('Beginner', 'Intermediate', 'Advanced') NOT NULL DEFAULT 'Intermediate',
    is_mandatory BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (drive_id) REFERENCES campus_drives(drive_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
    CONSTRAINT uk_drive_skill UNIQUE (drive_id, skill_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 16. APPLICATIONS TABLE
-- Student applications submitted for campus drives & selection status tracking.
-- ==============================================================================
CREATE TABLE applications (
    application_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    drive_id INT NOT NULL,
    application_date DATE NOT NULL,
    status ENUM('Eligible', 'Applied', 'Shortlisted', 'Assessment', 'Interview', 'Offered', 'Accepted', 'Rejected', 'Withdrawn') NOT NULL DEFAULT 'Applied',
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (drive_id) REFERENCES campus_drives(drive_id) ON DELETE CASCADE,
    CONSTRAINT uk_student_drive UNIQUE (student_id, drive_id),
    INDEX idx_applications_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 17. PLACEMENTS TABLE
-- Final placement offer details resulting from successful drive applications.
-- ==============================================================================
CREATE TABLE placements (
    placement_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    drive_id INT NOT NULL,
    application_id INT NOT NULL UNIQUE,
    offered_ctc DECIMAL(5,2) NOT NULL CHECK (offered_ctc > 0.00),
    offer_letter_date DATE DEFAULT NULL,
    acceptance_status ENUM('Accepted', 'Declined', 'Pending') NOT NULL DEFAULT 'Accepted',
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (drive_id) REFERENCES campus_drives(drive_id) ON DELETE CASCADE,
    FOREIGN KEY (application_id) REFERENCES applications(application_id) ON DELETE CASCADE,
    INDEX idx_placements_ctc (offered_ctc)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================================
-- 18. READINESS_EVALUATIONS TABLE
-- Audit log of rule-based placement readiness score assessments over time.
-- ==============================================================================
CREATE TABLE readiness_evaluations (
    evaluation_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    academic_year INT NOT NULL,
    overall_score DECIMAL(5,2) NOT NULL CHECK (overall_score BETWEEN 0.00 AND 100.00),
    academic_score DECIMAL(5,2) NOT NULL CHECK (academic_score BETWEEN 0.00 AND 35.00),
    skill_score DECIMAL(5,2) NOT NULL CHECK (skill_score BETWEEN 0.00 AND 30.00),
    project_score DECIMAL(5,2) NOT NULL CHECK (project_score BETWEEN 0.00 AND 15.00),
    internship_score DECIMAL(5,2) NOT NULL CHECK (internship_score BETWEEN 0.00 AND 10.00),
    certification_score DECIMAL(5,2) NOT NULL CHECK (certification_score BETWEEN 0.00 AND 10.00),
    evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    INDEX idx_readiness_student (student_id),
    INDEX idx_readiness_score (overall_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
SELECT
    acceptance_status,
    COUNT(*) AS total
FROM placements
GROUP BY acceptance_status;

SELECT COUNT(DISTINCT student_id) AS placed_students
FROM placements
WHERE acceptance_status IN ('Accepted', 'Pending');

SELECT COUNT(*) AS total_students
FROM students;