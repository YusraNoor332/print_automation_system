# printer_driver.py
"""Phase 3: Raw TCP socket controllers and communication error handling."""
import socket
import config

def send_to_printer(ip_address: str, packet: bytes) -> bool:
    """
    Opens a high-speed TCP socket stream to the printer hardware,
    transmits the byte packet, and closes immediately to free the channel.
    """
    port = config.PRINTER_PORT
    timeout = config.SOCKET_TIMEOUT
    
    try:
        # Create a raw socket with IPv4 and TCP stream
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Enforce strict socket timeouts to prevent factory line stalling
            sock.settimeout(timeout)
            
            # Connect directly to the printer's static IP on port 9100
            sock.connect((ip_address, port))
            
            # Stream the compiled byte array into the hardware print buffer
            sock.sendall(packet)
            
            # Successful transmission
            return True
            
    except socket.timeout:
        print(f"Error: Connection to printer {ip_address}:{port} timed out.")
        return False
    except socket.error as e:
        print(f"Error: Network socket failure for {ip_address}:{port} - {e}")
        return False
    except Exception as e:
        print(f"Error: Unexpected failure during print dispatch: {e}")
        return False
