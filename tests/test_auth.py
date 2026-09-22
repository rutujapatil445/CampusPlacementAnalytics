"""
Authentication Unit & Integration Test Suite

Tests:
1. Password hashing & hash verification (Werkzeug pbkdf2:sha256)
2. Successful user registration
3. Duplicate email registration prevention
4. Successful user login
5. Invalid password login failure
6. Unknown email login failure
7. Input validation (email format, empty fields, password mismatch, weak password)
8. UserSession state helper methods
9. Automatic database cleanup of test user record
"""

import os
import sys

# Ensure parent path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.database import execute_query, fetch_one
from modules.auth import (
    hash_password,
    verify_password,
    validate_email_format,
    register_user,
    login_user,
    UserSession
)

# Test User Data
TEST_EMAIL = "auth_unit_test_student@campus.edu"
TEST_PASS = "SecureTestPass123"


def cleanup_test_user():
    """Helper function to remove test user record from database."""
    try:
        execute_query("DELETE FROM users WHERE email = %s;", (TEST_EMAIL,))
    except Exception as e:
        print(f"[NOTE] Test cleanup exception: {e}")


def test_password_hashing():
    print("Test 1: Password Hashing & Verification...", end=" ")
    pwd = "MySecretPassword123"
    hashed = hash_password(pwd)
    
    assert hashed != pwd, "Hashed password must not equal plain text."
    assert verify_password(hashed, pwd) is True, "Valid password verification failed."
    assert verify_password(hashed, "WrongPassword") is False, "Invalid password passed verification."
    print("PASSED")


def test_email_validation():
    print("Test 2: Email Format Validation...", end=" ")
    assert validate_email_format("student@campus.edu") is True
    assert validate_email_format("invalid.email.com") is False
    assert validate_email_format("") is False
    assert validate_email_format(None) is False
    print("PASSED")


def test_registration_flow():
    print("Test 3: User Registration Flow...", end=" ")
    cleanup_test_user() # Ensure clean state

    # Step A: Register new test user
    res = register_user(TEST_EMAIL, TEST_PASS, TEST_PASS, role="STUDENT")
    assert res["success"] is True, f"Registration failed: {res['message']}"
    assert res["user_id"] is not None, "Registered user_id must not be None."

    # Step B: Test Duplicate Registration
    dup_res = register_user(TEST_EMAIL, TEST_PASS, TEST_PASS, role="STUDENT")
    assert dup_res["success"] is False, "Duplicate registration should have failed."
    assert "already exists" in dup_res["message"].lower()
    print("PASSED")


def test_login_flow():
    print("Test 4: User Login Authentication Flow...", end=" ")
    
    # Step A: Successful Login
    login_res = login_user(TEST_EMAIL, TEST_PASS)
    assert login_res["success"] is True, f"Valid login failed: {login_res['message']}"
    assert login_res["user"]["email"] == TEST_EMAIL
    assert login_res["user"]["role"] == "STUDENT"

    # Step B: Wrong Password Login
    wrong_pass_res = login_user(TEST_EMAIL, "WrongPassword999")
    assert wrong_pass_res["success"] is False
    assert "invalid" in wrong_pass_res["message"].lower()

    # Step C: Non-existent User Login
    unknown_user_res = login_user("nonexistent.user999@campus.edu", TEST_PASS)
    assert unknown_user_res["success"] is False
    assert "invalid" in unknown_user_res["message"].lower()
    print("PASSED")


def test_input_validations():
    print("Test 5: Registration Input Validations...", end=" ")
    
    # Empty fields
    res1 = register_user("", "pass123", "pass123")
    assert res1["success"] is False and "email is required" in res1["message"].lower()

    # Password mismatch
    res2 = register_user("new_test@campus.edu", "pass123", "different123")
    assert res2["success"] is False and "do not match" in res2["message"].lower()

    # Weak password
    res3 = register_user("new_test@campus.edu", "123", "123")
    assert res3["success"] is False and "at least 6 characters" in res3["message"].lower()

    # Invalid email format
    res4 = register_user("not_an_email", "pass123", "pass123")
    assert res4["success"] is False and "invalid email" in res4["message"].lower()
    print("PASSED")


def test_user_session():
    print("Test 6: UserSession Helper State...", end=" ")
    session = UserSession()
    assert session.is_authenticated() is False
    assert session.get_role() == ""

    session.login({"user_id": 99, "email": TEST_EMAIL, "role": "STUDENT"})
    assert session.is_authenticated() is True
    assert session.is_student() is True
    assert session.is_admin() is False

    session.logout()
    assert session.is_authenticated() is False
    print("PASSED")


def run_all_tests():
    print("=" * 60)
    print("Phase 4: Authentication & User Registration Test Suite")
    print("=" * 60)

    try:
        test_password_hashing()
        test_email_validation()
        test_registration_flow()
        test_login_flow()
        test_input_validations()
        test_user_session()

        print("=" * 60)
        print("[ALL PASSED] Authentication module verified successfully!")
        print("=" * 60)

    finally:
        # Guarantee database cleanup
        cleanup_test_user()


if __name__ == "__main__":
    run_all_tests()
