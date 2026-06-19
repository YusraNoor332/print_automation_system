# database.py
"""Phase 1: MSSQL connection pool context manager & query modules."""
import pyodbc
from contextlib import contextmanager
from typing import Dict, Any, Optional

import config

# Set this to True to bypass the SQL Server and return dummy data for testing the printers
MOCK_MODE = True

class DatabaseManager:
    def __init__(self):
        self.conn_string = config.MSSQL_CONN_STRING
        # Enable ODBC connection pooling
        pyodbc.pooling = True
        
    @contextmanager
    def get_connection(self):
        """Context manager for safe MSSQL connection handling."""
        conn = None
        try:
            conn = pyodbc.connect(self.conn_string, timeout=5)
            yield conn
        except pyodbc.Error as e:
            print(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_product_details(self, serial_barcode: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves product parameters based on the scanned serial barcode.
        """
        if MOCK_MODE:
            if serial_barcode == "HR-FRIDGE-001":
                return {
                    "Product_Name": "Haier Refrigerator Pro (MOCK)",
                    "Price": 599.99,
                    "QC_Status": "PASS",
                    "Requirement_Specs": "Color: Silver, Size: Large"
                }
            return None

        query = """
            SELECT Product_Name, Price, QC_Status, Requirement_Specs
            FROM Products
            WHERE SerialBarcode = ?
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (serial_barcode,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "Product_Name": row[0],
                        "Price": float(row[1]) if row[1] is not None else None,
                        "QC_Status": row[2],
                        "Requirement_Specs": row[3]
                    }
                return None
        except pyodbc.Error as e:
            print(f"Query execution error: {e}")
            return None

    def log_scanned_item(self, serial_barcode: str, status: str, printer_id: str) -> bool:
        """
        Logs the scan event into the ScannedItemsLog table.
        """
        if MOCK_MODE:
            return True

        query = """
            INSERT INTO ScannedItemsLog (SerialBarcode, ScanTime, Status, PrinterID)
            VALUES (?, GETDATE(), ?, ?)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (serial_barcode, status, printer_id))
                conn.commit()
                return True
        except pyodbc.Error as e:
            print(f"Failed to log scanned item: {e}")
            return False

# Singleton instance for the application to use
db = DatabaseManager()

# =====================================================================
# Mock Schema Definition for Reference:
# =====================================================================
"""
CREATE TABLE Products (
    ProductID INT IDENTITY(1,1) PRIMARY KEY,
    SerialBarcode VARCHAR(50) UNIQUE NOT NULL,
    Product_Name VARCHAR(100) NOT NULL,
    Price DECIMAL(10, 2),
    QC_Status VARCHAR(20),
    Requirement_Specs NVARCHAR(MAX)
);

CREATE TABLE ScannedItemsLog (
    LogID INT IDENTITY(1,1) PRIMARY KEY,
    SerialBarcode VARCHAR(50) NOT NULL,
    ScanTime DATETIME NOT NULL,
    Status VARCHAR(20),
    PrinterID VARCHAR(50)
);

-- Mock Data Insertion:
-- INSERT INTO Products (SerialBarcode, Product_Name, Price, QC_Status, Requirement_Specs)
-- VALUES ('HR-FRIDGE-001', 'Haier Refrigerator Pro', 599.99, 'PASS', 'Color: Silver, Size: Large');
"""
