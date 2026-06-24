"""
Pull-Response Scan Engine — built around the confirmed printer protocol.

CONFIRMED PROTOCOL (from tcp_scan_receiver.py diagnostic):
  - Printer sends ZERO bytes on each connection
  - Printer connects exactly 3 times per refresh cycle (one per dynamic_text field)
  - Connection order is FIXED: ProductName → Price → Status → repeat
  - Whatever we respond with becomes that field's content on the printer
  - The physical scanner fills S.Print independently via the hardware port
  - A print is triggered when the operator scans a barcode

Our role:
  1. Run a TCP server on port 8443
  2. For each incoming connection, respond with the correct field value
  3. A background monitor watches /engine/real for new barcodes
  4. When a new barcode appears in S.Print → DB lookup → update response cache
"""
import time
import socket
import json
import threading
from typing import Optional, Dict, Any

from database import db
from gui import system_signals

# How often (seconds) to query /engine/real to detect new barcodes.
# We also trigger a check on every ProductName connection (conn % 3 == 0).
MONITOR_INTERVAL = 1.0

# Throttle: don't query /engine/real more than once every N seconds
# during the field-response handler (prevents hammering on each connection).
REAL_THROTTLE = 0.5


class PrinterPollingEngine:
    def __init__(self, machine_serial: str = "740307"):
        self.machine_serial = machine_serial
        self.is_running     = False
        self._server_thread = None
        self._monitor_thread= None
        self._lock          = threading.Lock()

        # ── Field response cache ──────────────────────────────────────
        # These three strings are sent to the printer for each field.
        # They are updated whenever a new barcode is detected in S.Print.
        self._resp_product_name = ""
        self._resp_price        = ""
        self._resp_status       = ""

        # ── Barcode tracking ──────────────────────────────────────────
        self._last_barcode     = ""          # last barcode we processed
        self._last_real_time   = 0.0        # last time we queried /engine/real

        # ── Connection counter ────────────────────────────────────────
        # Determines which field each incoming connection maps to:
        #   counter % 3 == 0  →  ProductName  (+ triggers /engine/real check)
        #   counter % 3 == 1  →  Price
        #   counter % 3 == 2  →  Status
        self._conn_counter = 0

        # ── Printer target (cached from DB on start) ──────────────────
        self._printer_ip   = "192.168.137.200"
        self._printer_port = 9944

    # ──────────────────────────────────────────────────────────────────
    # Public lifecycle
    # ──────────────────────────────────────────────────────────────────

    def start(self):
        if self.is_running:
            return
        self.is_running = True

        # Fetch printer IP from DB at startup
        machine = db.get_machine_details(self.machine_serial)
        if machine:
            self._printer_ip = machine.get("PrinterIp", self._printer_ip)

        self._server_thread = threading.Thread(
            target=self._field_server_loop, daemon=True, name="FieldServer"
        )
        self._server_thread.start()

        self._monitor_thread = threading.Thread(
            target=self._status_monitor_loop, daemon=True, name="StatusMonitor"
        )
        self._monitor_thread.start()

        system_signals.log_event.emit(
            "[*] Scan Engine started — listening on port 8443 for printer field requests."
        )

    def stop(self):
        self.is_running = False
        if self._server_thread:
            self._server_thread.join(timeout=3.0)
        system_signals.log_event.emit("[*] Scan Engine stopped.")

    # ──────────────────────────────────────────────────────────────────
    # TCP field-response server  (port 8443)
    # ──────────────────────────────────────────────────────────────────

    def _field_server_loop(self):
        """
        Listens for connections from the printer.
        Each connection = a request for one field's content.
        The printer makes 3 connections per refresh cycle in fixed order.
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.settimeout(1.0)
        try:
            server.bind(("0.0.0.0", 8443))
            server.listen(20)
        except OSError as e:
            system_signals.log_event.emit(f"[!] Cannot bind port 8443: {e}")
            return

        while self.is_running:
            try:
                client, addr = server.accept()
            except socket.timeout:
                continue
            except Exception as e:
                if self.is_running:
                    print(f"[SERVER ERR] {e}")
                continue

            threading.Thread(
                target=self._respond_to_field_request,
                args=(client,),
                daemon=True
            ).start()

        server.close()

    def _respond_to_field_request(self, client_sock: socket.socket):
        """
        Handle one field-data request from the printer.

        Protocol confirmed:
          - Printer sends 0 bytes
          - We respond with the field content as a plain string + \\r\\n
          - The printer uses our response verbatim as the field value
        """
        with client_sock:
            # Drain any bytes (confirmed empty, but guard just in case)
            client_sock.settimeout(0.3)
            try:
                client_sock.recv(4096)
            except socket.timeout:
                pass

            # ── Determine which field this connection maps to ──────────
            with self._lock:
                field_idx = self._conn_counter % 3
                self._conn_counter += 1

            # ── On ProductName connection: check for new scan ──────────
            # Only query /engine/real if enough time has passed (throttle).
            if field_idx == 0:
                self._maybe_refresh_cache()

            # ── Read current cached response ───────────────────────────
            with self._lock:
                if field_idx == 0:
                    content = self._resp_product_name
                elif field_idx == 1:
                    content = self._resp_price
                else:
                    content = self._resp_status

            # ── Respond with field content ─────────────────────────────
            try:
                client_sock.sendall((content + "\r\n").encode("utf-8"))
            except Exception as e:
                print(f"[SEND ERR] {e}")

    # ──────────────────────────────────────────────────────────────────
    # Cache refresh — reads S.Print from /engine/real
    # ──────────────────────────────────────────────────────────────────

    def _maybe_refresh_cache(self):
        """
        Throttled: queries /engine/real at most once per REAL_THROTTLE seconds.
        If S.Print has a new barcode, triggers a DB lookup and updates the cache.
        """
        now = time.time()
        with self._lock:
            if now - self._last_real_time < REAL_THROTTLE:
                return
            self._last_real_time = now

        # TCP query — done WITHOUT holding the lock
        real = self._tcp_query(self._printer_ip, self._printer_port, {
            "request_type": "get",
            "path": "/engine/real"
        })
        if not real or real.get("status") != "ok":
            return

        self._process_real_dump(real)

    def _process_real_dump(self, real: Dict[str, Any]):
        """Extract barcode from /engine/real and update cache if changed."""
        SCAN_NAMES = {"S.Print", "SPrint", "s.print", "sprint"}
        barcode = ""
        for item in real.get("source_info", []):
            if item.get("name", "") in SCAN_NAMES:
                barcode = item.get("content", "").strip()
                break

        with self._lock:
            if barcode == self._last_barcode:
                return          # nothing changed
            prev = self._last_barcode
            self._last_barcode = barcode

        if not barcode:
            system_signals.log_event.emit("[~] Scanner cleared. Ready for next scan.")
            return

        # New barcode detected
        system_signals.log_event.emit(f"[*] Scan detected: '{barcode}'")

        product = db.get_product_details(barcode)
        if not product:
            system_signals.log_event.emit(
                f"[!] No database record for: '{barcode}'"
            )
            with self._lock:
                self._resp_product_name = ""
                self._resp_price        = ""
                self._resp_status       = ""
            return

        name   = product["ProductName"]
        price  = str(product["ProductPrice"])
        status = str(product["ProductStatus"])

        with self._lock:
            self._resp_product_name = name
            self._resp_price        = price
            self._resp_status       = status

        system_signals.log_event.emit(
            f"[+] Cache updated → Name: {name}  |  Price: {price}  |  Status: {status}"
        )

    # ──────────────────────────────────────────────────────────────────
    # Status monitor — periodic /engine/real check + GUI status dot
    # ──────────────────────────────────────────────────────────────────

    def _status_monitor_loop(self):
        """Checks printer connectivity every second and detects new barcodes."""
        while self.is_running:
            real = self._tcp_query(self._printer_ip, self._printer_port, {
                "request_type": "get",
                "path": "/engine/real"
            })
            if real and real.get("status") == "ok":
                system_signals.printer_status.emit(self.machine_serial, "ONLINE")
                # Update last_real_time so the field-handler throttle stays fresh
                with self._lock:
                    self._last_real_time = time.time()
                self._process_real_dump(real)
            else:
                system_signals.printer_status.emit(self.machine_serial, "OFFLINE")
                system_signals.log_event.emit("[!] Printer OFFLINE — retrying in 1s...")

            time.sleep(MONITOR_INTERVAL)

    # ──────────────────────────────────────────────────────────────────
    # Shared TCP helper
    # ──────────────────────────────────────────────────────────────────

    def _tcp_query(self, ip: str, port: int, payload: Dict[str, Any],
                   timeout: float = 2.0) -> Optional[Dict[str, Any]]:
        """Send a JSON command over raw TCP and return the parsed response."""
        packet = (json.dumps(payload) + "\r\n").encode("utf-8")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((ip, port))
                sock.sendall(packet)
                buf = b""
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                    if buf.endswith(b"\r\n") or buf.endswith(b"\n"):
                        break
                return json.loads(buf.decode("utf-8"))
        except Exception:
            return None


# Global singleton — imported by main.py
polling_engine = PrinterPollingEngine(machine_serial="740307")