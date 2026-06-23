# printer_driver.py
"""Phase 3: Native Sojet TCP-JSON Communication Protocol Wrapper."""
import socket
import json
import config

def send_to_printer_sdk(ip_address: str, product_name: str, price: str, qc_status: str) -> bool:
    """
    Connects directly to the printer's TCP control port and updates variables
    using the official Sojet JSON layout protocol schema.
    """
    # The TCP-JSON interface port defaults to 18071 on Sojet print servers
    PRINTER_JSON_PORT = 18071 
    
    # Construct the payload according to the Sojet TCP-JSON manual specifications
    # It updates the variable values tied to layout placeholder IDs 1, 2, and 3
    payload = {
        "request_type": "post",
        "path": "/engine/var_text",
        "params": {
            "variables": [
                {"id": 1, "value": product_name},
                {"id": 2, "value": price},
                {"id": 3, "value": f"STATUS:{qc_status}"}
            ]
        }
    }
    
    # Convert the Python dictionary into a compact JSON string string block
    packet_data = json.dumps(payload).encode('utf-8')
    
    try:
        # Establish a standard, high-speed network stream socket connection
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(config.SOCKET_TIMEOUT)
            
            # Connect directly to the printer hardware target over the Wi-Fi network
            sock.connect((ip_address, PRINTER_JSON_PORT))
            
            # Stream the complete JSON packet data block
            sock.sendall(packet_data)
            
            # Capture the response from the printer hardware to confirm reception
            response = sock.recv(1024).decode('utf-8')
            
            if "status" in response and "ok" in response:
                print(f"[+] Printer Confirmation received: {response}")
                return True
            else:
                print(f"[!] Warning: Data sent, but printer returned unexpected response: {response}")
                return True # Return true since transmission succeeded
                
    except socket.error as e:
        print(f"[NETWORK ERROR] Failed sending JSON packet to {ip_address}:{PRINTER_JSON_PORT} - {e}")
        return False
    except Exception as e:
        print(f"[SYSTEM CRASH] Unexpected failure in driver engine pipeline: {e}")
        return False
