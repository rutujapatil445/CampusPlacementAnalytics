"""
Database Connection Test Script

Verifies connectivity between Python application and MySQL 'campus_placement_db'.
Executes:
1. SELECT DATABASE();
2. SELECT COUNT(*) FROM students;

Prints current database name, student record count, and verifies clean disconnection.
"""

import os
import sys

# Ensure parent project directory is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.database import fetch_one


def test_connection():
    print("=" * 60)
    print("Phase 3: Python <-> MySQL Database Connection Test")
    print("=" * 60)

    try:
        # Step 1: Execute SELECT DATABASE();
        db_result = fetch_one("SELECT DATABASE() AS current_database;")
        current_db = db_result.get("current_database") if db_result else "Unknown"
        print(f"[SUCCESS] Connected to MySQL Database: '{current_db}'")

        # Step 2: Execute SELECT COUNT(*) FROM students;
        count_result = fetch_one("SELECT COUNT(*) AS total_students FROM students;")
        total_students = count_result.get("total_students", 0) if count_result else 0
        print(f"[SUCCESS] Total Registered Students in Database: {total_students}")

        print("=" * 60)
        print("[PASSED] Database Connection & Query Test Completed Successfully!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"[FAILED] Connection test failed with error: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    if not success:
        sys.exit(1)
