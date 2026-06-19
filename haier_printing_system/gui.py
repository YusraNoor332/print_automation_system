# gui.py
"""Interface Layer: Native PyQt6 desktop layout and log feed panels."""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QTextEdit, QLabel, QPushButton, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, QObject, Qt
from PyQt6.QtGui import QColor, QPalette

class SignalEmitter(QObject):
    """Safely bridges background FastAPI threads to the main GUI thread."""
    log_event = pyqtSignal(str)
    # Status event: printer_id, status_color (e.g., 'ONLINE' or 'ERROR')
    printer_status = pyqtSignal(str, str)

# Global emitter instance to be imported by main.py
system_signals = SignalEmitter()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Haier Print Automation Dashboard")
        self.resize(800, 600)
        
        # Connect signals
        system_signals.log_event.connect(self.append_log)
        system_signals.printer_status.connect(self.update_printer_status)
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Top Panel: Status Indicators
        status_group = QGroupBox("Printer Connectivity")
        status_layout = QHBoxLayout()
        
        self.status_labels = {}
        for printer_id in ["LINE_1_PRINTER_A", "LINE_1_PRINTER_B"]:
            lbl = QLabel(f"{printer_id}: OFFLINE")
            lbl.setStyleSheet("color: white; background-color: gray; padding: 5px; border-radius: 3px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_labels[printer_id] = lbl
            status_layout.addWidget(lbl)
            
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # Middle Panel: Activity Log
        log_group = QGroupBox("Live Activity Log")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        # Apply dark mode style for industrial feel
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # Bottom Panel: Controls
        control_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.log_output.clear)
        control_layout.addStretch()
        control_layout.addWidget(clear_btn)
        main_layout.addLayout(control_layout)

    def append_log(self, message: str):
        self.log_output.append(message)

    def update_printer_status(self, printer_id: str, status: str):
        if printer_id in self.status_labels:
            lbl = self.status_labels[printer_id]
            if status == "ONLINE":
                lbl.setText(f"{printer_id}: ONLINE")
                lbl.setStyleSheet("color: white; background-color: green; padding: 5px; border-radius: 3px;")
            elif status == "ERROR":
                lbl.setText(f"{printer_id}: ERROR")
                lbl.setStyleSheet("color: white; background-color: red; padding: 5px; border-radius: 3px;")
            else:
                lbl.setText(f"{printer_id}: OFFLINE")
                lbl.setStyleSheet("color: white; background-color: gray; padding: 5px; border-radius: 3px;")
