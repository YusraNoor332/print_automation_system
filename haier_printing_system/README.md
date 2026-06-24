# Haier Print Automation System

Automated label printing system for Haier production lines.
Integrates a MoTix inkjet printer with a SQL Server product database.

## How It Works

```
Operator scans barcode on printer
        ↓
Printer fills S.Print field from physical scanner
        ↓
Printer connects to PC (port 8443) — 3x for each dynamic field
        ↓
Our server responds with field content per connection:
  Conn 1 → ProductName  (e.g. "HR-66B")
  Conn 2 → Price        (e.g. "Rs.33,500")
  Conn 3 → Status       (e.g. "active")
        ↓
Printer updates fields + prints label
        ↓
S.Print clears → ready for next scan
```

## Printer Template: HAIER_SCAN

| Field | Type | Config |
|---|---|---|
| S.Print | Scanner | Hardware scanner input |
| ProductName | Dynamic Text | Server OFF, Host: 192.168.137.1, Port: 8443 |
| Price | Dynamic Text | Server OFF, Host: 192.168.137.1, Port: 8443 |
| Status | Dynamic Text | Server OFF, Host: 192.168.137.1, Port: 8443 |

## Running the System

```powershell
cd haier_printing_system
.\venv\Scripts\python main.py
```

The GUI will open. The status dot turns **green** when the printer is online.
Scan a barcode — fields update and the label prints automatically.

## Files

| File | Purpose |
|---|---|
| `main.py` | Entry point — starts polling engine + GUI |
| `polling_manager.py` | TCP server on port 8443 + scan detection engine |
| `database.py` | SQL Server connection + product/machine lookups |
| `gui.py` | PyQt6 dashboard with live activity log |
| `config.py` | IP addresses, ports, DB connection string |
| `get_real.py` | Diagnostic: dumps current printer memory state |

## Printer Protocol (Confirmed)

- **Port 9944** — Read-only monitoring API (`/engine/real`)
- **Port 8443** — Our TCP server. Printer connects here to fetch field values.
  - Printer sends: **0 bytes** (nothing)
  - We respond: plain string + `\r\n` (used verbatim as field content)
  - Pattern: 3 connections per cycle → ProductName, Price, Status (fixed order)

## Database

- Server: `192.168.137.1`
- Table: `dbo.Haier_Product`
- Lookup column: `ProductCode` (matches physical barcode label)

## Requirements

```
pyodbc
PyQt6
```
