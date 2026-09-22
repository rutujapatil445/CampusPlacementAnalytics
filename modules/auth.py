"""
Authentication & User Registration Module

Flow:
1. User registration -> Validate inputs -> Check duplicate email -> Hash password -> Insert into 'users'
2. User login -> Validate inputs -> Fetch user by email -> Verify hashed password -> Return user info
3. UserSession -> Simple memory/session helper for tracking logged-in user state.
"""

import re
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import fetch_one, execute_query, get_connection

# Simple regex for email format validation
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


def validate_email_format(email: str) -> bool:
    """Checks if the email string matches standard email format."""
    if not email or not isinstance(email, str):
        return False
    return bool(re.match(EMAIL_REGEX, email.strip()))


def validate_password_strength(password: str) -> tuple:
    """
    Validates password length and non-emptiness.
    Returns (is_valid, error_message).
    """
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, ""


def hash_password(password: str) -> str:
    """Hashes plain-text password using Werkzeug's pbkdf2:sha256 algorithm."""
    return generate_password_hash(password, method="pbkdf2:sha256")


def verify_password(stored_hash: str, password: str) -> bool:
    """Verifies plain-text password against stored hash value."""
    if not stored_hash or not password:
        return False
    return check_password_hash(stored_hash, password)


def register_user(email: str, password: str, confirm_password: str, role: str = "STUDENT") -> dict:
    """
    Registers a new user account in the database.
    
    Validations:
    - Non-empty email, password, confirm_password
    - Valid email format
    - Password matching confirm_password
    - Password minimum length
    - Role must be 'STUDENT' or 'ADMIN' (Defaults to 'STUDENT')
    - Email uniqueness check against 'users' table
    
    Returns:
        dict: {"success": bool, "message": str, "user_id": int or None}
    """
    # 1. Clean inputs
    email = email.strip() if email else ""
    role = role.upper().strip() if role else "STUDENT"

    # 2. Input presence validation
    if not email:
        return {"success": False, "message": "Email is required.", "user_id": None}
    if not password:
        return {"success": False, "message": "Password is required.", "user_id": None}
    if not confirm_password:
        return {"success": False, "message": "Confirm password is required.", "user_id": None}

    # 3. Format validations
    if not validate_email_format(email):
        return {"success": False, "message": "Invalid email address format.", "user_id": None}

    if password != confirm_password:
        return {"success": False, "message": "Passwords do not match.", "user_id": None}

    is_valid_pwd, msg = validate_password_strength(password)
    if not is_valid_pwd:
        return {"success": False, "message": msg, "user_id": None}

    if role not in ["STUDENT", "ADMIN"]:
        return {"success": False, "message": "Invalid user role specified.", "user_id": None}

    try:
        # 4. Check duplicate email
        existing_user = fetch_one("SELECT user_id FROM users WHERE email = %s;", (email,))
        if existing_user:
            return {"success": False, "message": "An account with this email already exists.", "user_id": None}

        # 5. Hash password & Insert into database
        pwd_hash = hash_password(password)
        sql = "INSERT INTO users (email, password_hash, role, is_active) VALUES (%s, %s, %s, %s);"
        
        # Execute insert & get generated user_id
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (email, pwd_hash, role, True))
        conn.commit()
        new_user_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return {
            "success": True,
            "message": "User registered successfully.",
            "user_id": new_user_id
        }

    except Exception as e:
        print(f"[ERROR] register_user failed: {e}")
        return {"success": False, "message": f"Database error during registration: {e}", "user_id": None}


def login_user(email: str, password: str) -> dict:
    """
    Authenticates user login credentials against stored hashed passwords.
    
    Returns:
        dict: {"success": bool, "message": str, "user": dict or None}
    """
    email = email.strip() if email else ""
    
    if not email or not password:
        return {"success": False, "message": "Email and password are required.", "user": None}

    try:
        # Fetch user record by email
        sql = "SELECT user_id, email, password_hash, role, is_active FROM users WHERE email = %s;"
        user = fetch_one(sql, (email,))

        if not user:
            # Generic response prevents account enumeration security vulnerability
            return {"success": False, "message": "Invalid email or password.", "user": None}

        if not user.get("is_active", True):
            return {"success": False, "message": "Account is disabled. Please contact TPO admin.", "user": None}

        # Verify hashed password
        if not verify_password(user["password_hash"], password):
            return {"success": False, "message": "Invalid email or password.", "user": None}

        # Auth Success payload (excluding password hash)
        authenticated_user = {
            "user_id": user["user_id"],
            "email": user["email"],
            "role": user["role"]
        }
        return {
            "success": True,
            "message": "Login successful.",
            "user": authenticated_user
        }

    except Exception as e:
        print(f"[ERROR] login_user failed: {e}")
        return {"success": False, "message": f"Authentication error: {e}", "user": None}


class UserSession:
    """
    Simple session state wrapper for tracking current user session in Python memory.
    Structured to cleanly integrate with Streamlit session_state in later UI phases.
    """

    def __init__(self):
        self._current_user = None

    def login(self, user_dict: dict):
        """Sets active user session."""
        self._current_user = user_dict

    def logout(self):
        """Clears active user session."""
        self._current_user = None

    def is_authenticated(self) -> bool:
        """Returns True if user is logged in."""
        return self._current_user is not None

    def get_current_user(self) -> dict:
        """Returns logged-in user dictionary or None."""
        return self._current_user

    def get_role(self) -> str:
        """Returns role string ('STUDENT' or 'ADMIN') or empty string."""
        return self._current_user.get("role", "") if self._current_user else ""

    def is_admin(self) -> bool:
        """Returns True if current user is an Admin."""
        return self.get_role() == "ADMIN"

    def is_student(self) -> bool:
        """Returns True if current user is a Student."""
        return self.get_role() == "STUDENT"
