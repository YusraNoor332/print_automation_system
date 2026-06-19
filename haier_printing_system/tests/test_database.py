import unittest
from unittest.mock import patch, MagicMock
from database import DatabaseManager

class TestDatabaseManager(unittest.TestCase):

    @patch('database.pyodbc.connect')
    def test_get_product_details_success(self, mock_connect):
        # Arrange: Set up the mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # When cursor.fetchone() is called, return our mock row data
        mock_cursor.fetchone.return_value = ('Haier Refrigerator Pro', 599.99, 'PASS', 'Color: Silver, Size: Large')
        
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        db = DatabaseManager()
        
        # Act: Query with a dummy appliance serial number
        dummy_serial = 'HR-FRIDGE-001'
        result = db.get_product_details(dummy_serial)
        
        # Assert: Check that a clean Python dictionary was returned
        self.assertIsNotNone(result)
        self.assertEqual(result['Product_Name'], 'Haier Refrigerator Pro')
        self.assertEqual(result['Price'], 599.99)
        self.assertEqual(result['QC_Status'], 'PASS')
        self.assertEqual(result['Requirement_Specs'], 'Color: Silver, Size: Large')
        
        # Verify that the query was executed correctly with the dummy serial
        mock_cursor.execute.assert_called_once()
        args, kwargs = mock_cursor.execute.call_args
        self.assertIn(dummy_serial, args[1])
        
    @patch('database.pyodbc.connect')
    def test_get_product_details_not_found(self, mock_connect):
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # When item is not found, fetchone() returns None
        mock_cursor.fetchone.return_value = None
        
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        db = DatabaseManager()
        
        # Act
        result = db.get_product_details('UNKNOWN-001')
        
        # Assert
        self.assertIsNone(result)

    @patch('database.pyodbc.connect')
    def test_log_scanned_item_success(self, mock_connect):
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        db = DatabaseManager()
        
        # Act
        success = db.log_scanned_item('HR-FRIDGE-001', 'PRINTED', 'LINE_1_PRINTER_A')
        
        # Assert
        self.assertTrue(success)
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

if __name__ == '__main__':
    unittest.main()
