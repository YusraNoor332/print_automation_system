import unittest
from unittest.mock import patch, MagicMock
import socket
from printer_driver import send_to_printer

class TestPrinterDriver(unittest.TestCase):

    @patch('printer_driver.socket.socket')
    def test_send_to_printer_success(self, mock_socket_class):
        # Arrange
        mock_sock_instance = MagicMock()
        # Mock the context manager __enter__
        mock_socket_class.return_value.__enter__.return_value = mock_sock_instance
        
        test_ip = "192.168.10.101"
        test_packet = b'\x02PRT|10,10,12,"Test"\x03'
        
        # Act
        success = send_to_printer(test_ip, test_packet)
        
        # Assert
        self.assertTrue(success)
        mock_sock_instance.settimeout.assert_called_once()
        mock_sock_instance.connect.assert_called_once_with((test_ip, 9100))
        mock_sock_instance.sendall.assert_called_once_with(test_packet)

    @patch('printer_driver.socket.socket')
    def test_send_to_printer_timeout(self, mock_socket_class):
        # Arrange
        mock_sock_instance = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_sock_instance
        
        # Simulate a socket timeout during connect
        mock_sock_instance.connect.side_effect = socket.timeout("Timeout")
        
        # Act
        success = send_to_printer("192.168.10.101", b"TEST")
        
        # Assert
        self.assertFalse(success)

    @patch('printer_driver.socket.socket')
    def test_send_to_printer_connection_error(self, mock_socket_class):
        # Arrange
        mock_sock_instance = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_sock_instance
        
        # Simulate a connection refused error
        mock_sock_instance.connect.side_effect = ConnectionRefusedError("Connection refused")
        
        # Act
        success = send_to_printer("192.168.10.101", b"TEST")
        
        # Assert
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
