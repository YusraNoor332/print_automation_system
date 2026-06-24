import socket
import json

PRINTER_IP = "192.168.137.200"
PRINTER_PORT = 9944

print("[*] Retrieving real-time printer memory and source_info...")

payload = {
    "request_type": "get",
    "path": "/engine/real"
}

json_string = json.dumps(payload) + "\r\n"
packet_data = json_string.encode('utf-8')

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(2.0)
        sock.connect((PRINTER_IP, PRINTER_PORT))
        sock.sendall(packet_data)
        response = sock.recv(4096).decode('utf-8').strip()
        
        print("\n[Raw Printer Memory Dump]")
        print(response)
        
        try:
            data = json.loads(response)
            if "source_info" in data:
                print("\n[ACTIVE VARIABLES DETECTED ON PRINTER]:")
                for item in data["source_info"]:
                    print(f" -> NAME: '{item.get('name')}', ID: {item.get('id')}, TYPE: {item.get('type')}, CONTENT: '{item.get('content')}'")
            else:
                print("\n[!] No 'source_info' found in the active print job. Is the message empty?")
        except:
            pass

except Exception as e:
    print(f"Error: {e}")
