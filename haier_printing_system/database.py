# database.py
"""Phase 1: Production MSSQL connection engine mapping directly to SSMS DBHaierApp."""
import pyodbc
from contextlib import contextmanager
from typing import Dict, Any, Optional
import config

MOCK_MODE = False

class DatabaseManager:
    def __init__(self):
        self.conn_string = config.MSSQL_CONN_STRING
        # Enable enterprise connection pooling
        pyodbc.pooling = True
        
    @contextmanager
    def get_connection(self):
        """Context manager for safe MSSQL connection handling via the local pool."""
        conn = None
        try:
            conn = pyodbc.connect(self.conn_string, timeout=5)
            yield conn
        except pyodbc.Error as e:
            print(f"[DATABASE ERROR] Failed connecting to SSMS DBHaierApp: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _clean_price_string(self, raw_price_str: Optional[str]) -> str:
        """
        Helper method to extract the final summary Rs. amount from Haier's pricing string.
        Example: 'RP.  45,763 + ST 8,237 = Rs.54,000' -> 'Rs.54,000'
        """
        if not raw_price_str:
            return "Rs.0"
        if "Rs." in raw_price_str:
            return f"Rs.{raw_price_str.split('Rs.')[-1].strip()}"
        return raw_price_str

    def get_machine_details(self, machine_serial: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves scanner and printer IPs from the Haier_Machine table.
        Assumes the incoming scanner request 'printer_id' is the MachineSerial.
        """
        if MOCK_MODE:
            if machine_serial == "740307":
                return {
                    "PrinterIp": "192.168.0.124",
                    "PrinterPort": 18107
                }
            # Fallback for old mock testing
            return {
                "PrinterIp": "127.0.0.1",
                "PrinterPort": 9100
            }
        query = """
            SELECT PrinterIp, PrinterPort
            FROM dbo.Haier_Machine
            WHERE MachineSerial = ? AND MachineStatus = 'active'
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (machine_serial,))
                row = cursor.fetchone()
                if row:
                    return {
                        "PrinterIp": row[0],
                        "PrinterPort": int(row[1]) if row[1] else 18107
                    }
                return None
        except pyodbc.Error as e:
            print(f"[SQL ERROR] Machine lookup failed for serial {machine_serial}: {e}")
            return None

    def get_product_details(self, serial_barcode: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves product parameters based on the scanned serial barcode (ProductSku) from SSMS.
        """
        if MOCK_MODE:
            if serial_barcode == "HRF-186EBS":
                return {
                    "ProductName": "HRF-186EBS",
                    "ProductPrice": "Rs.54,000",
                    "ProductStatus": "active"
                }
            return None

        query = """
            SELECT ProductName, ProductPrice, ProductStatus
            FROM dbo.Haier_Product
            WHERE ProductSku = ? AND ProductStatus = 'active'
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (serial_barcode,))
                row = cursor.fetchone()
                
                if row:
                    raw_price = row[1]
                    return {
                        "ProductName": row[0],
                        # Pass the clean version (Rs.54,000) straight to your packet builder
                        "ProductPrice": self._clean_price_string(raw_price),
                        "ProductStatus": row[2]
                    }
                return None
        except pyodbc.Error as e:
            print(f"[SQL ERROR] Product lookup failed for SKU {serial_barcode}: {e}")
            return None

    def log_scanned_item(self, serial_barcode: str, status: str, printer_id: str) -> bool:
        """
        No logging table schema is currently available in DBHaierApp.
        Bypassing SQL logging write operations; logs are handled via application runtime stream.
        """
        return True

# Singleton instance for the application to use
db = DatabaseManager()