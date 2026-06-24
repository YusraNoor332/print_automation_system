"""
System Coordinator: Orchestrates cross-module data synchronization loops.
Launches the background reverse-polling thread and binds the local PyQt GUI engine.
"""
import sys
from gui import QApplication, MainWindow
from polling_manager import polling_engine

def start_system():
    """Initializes and runs the print automation system pipelines concurrently."""
    # 1. Start the high-frequency raw TCP socket reverse polling loop
    polling_engine.start()
    
    # 2. Hand over processing control directly to the native PyQt Graphical User Interface runtime
    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # Explicitly ensure background threads wind down gracefully upon desktop app termination
    try:
        sys.exit(qt_app.exec())
    finally:
        polling_engine.stop()

if __name__ == "__main__":
    start_system()