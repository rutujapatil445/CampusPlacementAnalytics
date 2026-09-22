"""
Database Connection & Query Execution Helper Module

Flow Architecture:
Python Application -> mysql-connector-python Driver -> Parameterized SQL Query -> MySQL Server -> Result Payload

Functions:
- get_connection(): Opens connection to MySQL database server.
- execute_query(): Executes INSERT, UPDATE, or DELETE queries with automatic transaction commit.
- fetch_one(): Executes SELECT query and returns a single record dictionary.
- fetch_all(): Executes SELECT query and returns a list of record dictionaries.
"""

import mysql.connector
from mysql.connector import Error
from config.settings import (
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DATABASE
)


def get_connection():
    """
    Establishes a connection to the MySQL database server.
    
    Flow:
    1. Reads host, port, user, password, and database from config.settings
    2. Calls mysql.connector.connect()
    3. Returns active MySQLConnection object
    
    Returns:
        mysql.connector.connection.MySQLConnection: Active database connection instance.
        
    Raises:
        Error: If connection parameters are invalid or MySQL server is unreachable.
    """
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        return connection
    except Error as e:
        print(f"[ERROR] Database connection failed: {e}")
        raise


def execute_query(sql: str, params: tuple = None) -> int:
    """
    Executes an INSERT, UPDATE, or DELETE query on MySQL.
    
    Flow:
    1. Obtain connection from get_connection()
    2. Create cursor instance
    3. Execute query with parameterized tuple to prevent SQL Injection
    4. Commit transaction
    5. Clean up by closing cursor and returning connection to pool
    
    Args:
        sql (str): SQL statement with %s placeholders.
        params (tuple, optional): Tuple of values to bind to SQL query.
        
    Returns:
        int: Number of affected database rows.
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(sql, params or ())
        connection.commit()
        return cursor.rowcount
    except Error as e:
        if connection:
            connection.rollback()
        print(f"[ERROR] Query execution failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def fetch_one(sql: str, params: tuple = None) -> dict:
    """
    Executes a SELECT query and returns a single matching record dictionary.
    
    Args:
        sql (str): SELECT SQL query statement with %s placeholders.
        params (tuple, optional): Parameter values tuple.
        
    Returns:
        dict or None: Single record dictionary (column_name: value) or None if no result.
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        result = cursor.fetchone()
        return result
    except Error as e:
        print(f"[ERROR] fetch_one query failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def fetch_all(sql: str, params: tuple = None) -> list:
    """
    Executes a SELECT query and returns all matching record dictionaries as a list.
    
    Args:
        sql (str): SELECT SQL query statement with %s placeholders.
        params (tuple, optional): Parameter values tuple.
        
    Returns:
        list: List of record dictionaries.
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"[ERROR] fetch_all query failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
