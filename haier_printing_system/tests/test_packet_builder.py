import unittest
from packet_builder import build_print_packet

class TestPacketBuilder(unittest.TestCase):

    def test_build_print_packet_success(self):
        dummy_data = {
            "Product_Name": "Haier Refrigerator Pro",
            "Price": 599.99,
            "QC_Status": "PASS",
            "Requirement_Specs": "Color: Silver, Size: Large"
        }
        
        packet = build_print_packet(dummy_data)
        
        # Verify packet type
        self.assertIsInstance(packet, bytes)
        
        # Verify packet structure (STX and ETX wrappers)
        self.assertTrue(packet.startswith(b'\x02'))
        self.assertTrue(packet.endswith(b'\x03'))
        
        # Verify content
        packet_str = packet.decode('utf-8')
        self.assertIn('PRT', packet_str)
        self.assertIn('10,10,12,"Haier Refrigerator Pro"', packet_str)
        self.assertIn('10,50,14,"$599.99"', packet_str)
        self.assertIn('10,90,16,"QC:PASS"', packet_str)

    def test_build_print_packet_empty(self):
        with self.assertRaises(ValueError):
            build_print_packet({})

if __name__ == '__main__':
    unittest.main()
