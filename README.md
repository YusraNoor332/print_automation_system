# Haier Open-Architecture Print Automation System

This system serves as a vendor-independent middleware platform for handheld Thermal Inkjet (TIJ) printer control on active appliance assembly lines. It intercepts barcode scans via a high-speed FastAPI listener, queries the Haier SQL Database for product specifications, and translates the data into raw byte packets formatted for the Sojet/MoTix hardware.

---

## 1. Project Setup & Prerequisites

This system is built entirely on an open Python architecture. It requires **Python 3.10+**.

### Virtual Environment Setup
Before running the system, ensure the dependencies are installed. Open a PowerShell terminal and run:

```powershell
cd C:\Users\HP\print_automation_system\haier_printing_system
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 2. Configuration & IP Patching

Before starting the server, you must tell the system where the databases and physical printers are located on the factory network. 

Open the **`config.py`** file and update the following settings:

### A. Database Connection
Update the `DB_SERVER`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` variables to point to your live Microsoft SQL Server.
```python
DB_SERVER = "10.0.0.50"  # Example SQL Server IP
```

### B. Hardware Printer IPs
Map the logical Printer IDs (which are sent by the barcode scanners) to the **Static IPv4 Addresses** assigned to the physical MoTix printers.
```python
PRINTER_IP_MAP = {
    "LINE_1_PRINTER_A": "192.168.1.55",  # Replace with the actual IP of Printer A
    "LINE_1_PRINTER_B": "192.168.1.56",
}
```

---

## 3. Running the System

To start the central automation dashboard and background listener, simply run:

```powershell
cd C:\Users\HP\print_automation_system\haier_printing_system
.\venv\Scripts\python main.py
```
*The dark-mode PyQt6 dashboard will open natively, and the FastAPI server will boot silently in the background on port `8000`.*

---

## 4. Hardware Scanner Setup

The MoTix handheld printers must be configured to send their barcode scans to the computer running this Python application.

1. Open PowerShell and run `ipconfig` to find your computer's IPv4 address (e.g., `192.168.1.20`).
2. Go to the physical MoTix printer's touchscreen settings menu.
3. Locate the Webhook / API Integration settings.
4. Set the destination URL to: `http://192.168.1.20:8000/scan` (replace with your actual IP).
5. Ensure the printer is set to send a `POST` request.

When the operator pulls the trigger, the scan will route to your computer, and the dashboard will instantly light up and execute the print command.

---

## 5. Testing with the Mock Database

If you want to test the physical printers but do not have a live SQL Server running, you can enable the Mock Database mode.

1. Open **`database.py`**.
2. Change `MOCK_MODE = True` at the top of the file.
3. Start the system (`python main.py`).
4. Scan a barcode containing the exact string **`HR-FRIDGE-001`**. 

The system will bypass the SQL server, load a hardcoded dummy product ("Haier Refrigerator Pro"), and successfully send the print command to the hardware. Remember to switch `MOCK_MODE = False` before going live on the factory floor!
