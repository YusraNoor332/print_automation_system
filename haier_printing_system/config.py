# config.py
"""Centralized configuration variables and MSSQL credentials."""
import os

# --- MSSQL Database Configuration ---
# If your SSMS server has a specific instance name (e.g., DESKTOP-XXXXX\SQLEXPRESS), 
# change "localhost" to that exact server name string.
DB_SERVER = os.getenv("DB_SERVER", "localhost\SQLEXPRESS")
DB_NAME = os.getenv("DB_NAME", "DBHaierApp")
DB_DRIVER = os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")

# --- Authentication Configuration ---
# Set this to True if you login to SSMS using Windows Authentication (No password needed).
# Set to False if your senior gave you a specific SQL Server User ID and Password.
USE_WINDOWS_AUTH = True  

if USE_WINDOWS_AUTH:
    MSSQL_CONN_STRING = (
        f"DRIVER={DB_DRIVER};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"Trusted_Connection=yes;"
    )
else:
    DB_USER = os.getenv("DB_USER", "HaierServiceAccount")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Password123")
    MSSQL_CONN_STRING = (
        f"DRIVER={DB_DRIVER};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
    )

# --- Hardware Configuration ---
PRINTER_PORT = 18107  # Default fallback port if database lookup fails
SOCKET_TIMEOUT = 3.0  # Seconds to wait before dropping a frozen connection

# --- System Configuration ---
API_HOST = "0.0.0.0"  # Allows devices on the local Wi-Fi subnet to send scan payloads
API_PORT = 8000