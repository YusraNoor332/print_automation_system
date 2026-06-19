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
    printer_id: str
    serial_barcode: str

@app.post("/scan")
def handle_scan(payload: ScanPayload):
    """
    Ingress endpoint that receives physical scan payloads from the factory floor.
    """
    printer_id = payload.printer_id
    serial = payload.serial_barcode
    
    # Alert GUI
    system_signals.log_event.emit(f"[*] Received scan: {serial} from {printer_id}")
    
    # 1. Fetch from Database
    product_data = db.get_product_details(serial)
    if not product_data:
        system_signals.log_event.emit(f"[!] Invalid serial: {serial} not found in database.")
        db.log_scanned_item(serial, "FAILED_DB", printer_id)
        raise HTTPException(status_code=404, detail="Serial not found")
        
    system_signals.log_event.emit(f"[+] DB Match: {product_data['Product_Name']} (${product_data['Price']})")
    
    # 2. Build Print Packet
    try:
        packet = build_print_packet(product_data)
    except Exception as e:
        system_signals.log_event.emit(f"[!] Packet generation failed: {e}")
        db.log_scanned_item(serial, "FAILED_BUILD", printer_id)
        raise HTTPException(status_code=500, detail="Packet generation failed")
    
    # 3. Dispatch to Hardware
    target_ip = config.PRINTER_IP_MAP.get(printer_id)
    if not target_ip:
        system_signals.log_event.emit(f"[!] Unknown printer ID: {printer_id}")
        db.log_scanned_item(serial, "FAILED_IP", printer_id)
        raise HTTPException(status_code=400, detail="Unknown printer ID")
        
    success = send_to_printer(target_ip, packet)
    
    # 4. Log and Update GUI
    if success:
        system_signals.log_event.emit(f"[+] Printed successfully to {printer_id} ({target_ip})")
        system_signals.printer_status.emit(printer_id, "ONLINE")
        db.log_scanned_item(serial, "PRINTED", printer_id)
        return {"status": "success"}
    else:
        system_signals.log_event.emit(f"[!] Print transmission failed for {printer_id}")
        system_signals.printer_status.emit(printer_id, "ERROR")
        db.log_scanned_item(serial, "FAILED_PRINT", printer_id)
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

