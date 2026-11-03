import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
)
class FlowstateWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flowstate")
        self.resize(460, 640)


app = QApplication(sys.argv)
window = FlowstateWindow()
window.show()
sys.exit(app.exec())
