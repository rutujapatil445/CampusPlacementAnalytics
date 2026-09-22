"""
Application Configuration Settings

Loads environment variables from .env file using python-dotenv.
Provides database connection parameters to config/database.py.
"""

import os
from dotenv import load_dotenv

# Load variables from .env file into environment
load_dotenv()

# MySQL Database Connection Credentials
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "campus_placement_db")
