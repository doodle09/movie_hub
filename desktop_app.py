import sys
from PyQt6.QtWidgets import QApplication
from database.db_setup import initialize_database
from gui.main_window import MainWindow
from utils.theme_engine import build_app_stylesheet

def main():
    print("[INFO] Starting MovieHub PyQt6 Desktop")
    
    # Ensure offline DB is active
    initialize_database()
    
    app = QApplication(sys.argv)
    
    # Apply our custom dark theme globally
    app.setStyleSheet(build_app_stylesheet())
    
    # Launch Main Window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
