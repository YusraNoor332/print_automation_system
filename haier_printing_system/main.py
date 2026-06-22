# main.py
"""System Coordinator: Orchestrates cross-module asynchronous data flow."""
import sys
import threading
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import config
from database import db
from packet_builder import build_print_packet
from printer_driver import send_to_printer
from gui import QApplication, MainWindow, system_signals

app = FastAPI(title="Haier Print Automation Listener")

class ScanPayload(BaseModel):
    printer_id: str  # This should be the MachineSerial from Haier_Machine
    serial_barcode: str # This should be the ProductSku from Haier_Product

@app.post("/scan")
def handle_scan(payload: ScanPayload):
    """
    Ingress endpoint that receives physical scan payloads from the factory floor.
    """
    machine_serial = payload.printer_id
    product_sku = payload.serial_barcode
    
    # Alert GUI
    system_signals.log_event.emit(f"[*] Received scan: {product_sku} from Machine {machine_serial}")
    
    # 1. Fetch Printer IP & Port dynamically from Database
    machine_data = db.get_machine_details(machine_serial)
    if not machine_data:
        system_signals.log_event.emit(f"[!] Unknown Machine Serial: {machine_serial}")
        raise HTTPException(status_code=400, detail="Unknown Machine Serial")
        
    target_ip = machine_data['PrinterIp']
    target_port = machine_data['PrinterPort']
    
    # 2. Fetch Product from Database
    product_data = db.get_product_details(product_sku)
    if not product_data:
        system_signals.log_event.emit(f"[!] Invalid SKU: {product_sku} not found in database.")
        raise HTTPException(status_code=404, detail="SKU not found")
        
    system_signals.log_event.emit(f"[+] DB Match: {product_data['ProductName']} ({product_data['ProductPrice']})")
    
    # 3. Build Print Packet
    try:
        packet = build_print_packet(product_data)
    except Exception as e:
        system_signals.log_event.emit(f"[!] Packet generation failed: {e}")
        raise HTTPException(status_code=500, detail="Packet generation failed")
    
    # 4. Dispatch to Hardware
    success = send_to_printer(target_ip, target_port, packet)
    
    # 5. Log and Update GUI
    if success:
        system_signals.log_event.emit(f"[+] Printed successfully to {target_ip}:{target_port}")
        system_signals.printer_status.emit(machine_serial, "ONLINE")
        return {"status": "success"}
    else:
        system_signals.log_event.emit(f"[!] Print transmission failed for {target_ip}:{target_port}")
        system_signals.printer_status.emit(machine_serial, "ERROR")
        raise HTTPException(status_code=503, detail="Printer network failure")

def run_fastapi():
    """Runs the FastAPI server in a background thread."""
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT, log_level="error")

def start_system():
    # 1. Start the FastAPI ASGI server in a daemon thread so it doesn't block GUI
    api_thread = threading.Thread(target=run_fastapi, daemon=True)
    api_thread.start()
    
    # 2. Start the PyQt6 Native UI loop on the main thread
    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # System waits here until GUI is closed
    sys.exit(qt_app.exec())

if __name__ == "__main__":
    start_system()

