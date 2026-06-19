# config.py
"""Centralized configuration variables, MSSQL credentials, and Static IPs."""
import os

# --- MSSQL Database Configuration ---
DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_NAME = os.getenv("DB_NAME", "HaierPrintAutomation")
DB_USER = os.getenv("DB_USER", "HaierServiceAccount")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Password123")
DB_DRIVER = os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")

MSSQL_CONN_STRING = (
    f"DRIVER={DB_DRIVER};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};"
)

# --- Hardware Configuration ---
PRINTER_IP_MAP = {
    "LINE_1_PRINTER_A": "192.168.10.101",
    "LINE_1_PRINTER_B": "192.168.10.102",
}
PRINTER_PORT = 9100
SOCKET_TIMEOUT = 3.0  # seconds

# --- System Configuration ---
API_HOST = "0.0.0.0"
API_PORT = 8000
