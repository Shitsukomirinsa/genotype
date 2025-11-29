# scripts/typing_game_pyside6.py
import sys
from PySide6.QtWidgets import QApplication
from src.game_ui import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
