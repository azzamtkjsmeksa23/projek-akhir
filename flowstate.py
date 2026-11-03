import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
)
class FlowstateWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flowstate")
        self.resize(460, 640)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        row = QHBoxLayout()

        self.task_input = QLineEdit()
        self.task_input.setPlaceHolderText("What u want to do?")
        self.task_input.returnPressed.connect(self.add_task)

        self.add_button = QPushButton("AddTask")
        self.add_button.clicked.connect(self.add_task)

        row.addWidget(self.task_input)
        row.addWidget(self.add_button)
        layout.addLayout(row)

        self.task_list = QListWidget()
        self.task_list.itemChanged.connect(self.update_progress)
        layout.addWidget(self.task_list)

        self.remove_button = QPushButton("Remove?")
        self.remove_button.clicked.connect(self.remove_task)
        layout.addWidget(self.remove_button)

        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)
        self.update_progress

    def add_task(self):
        text = self.task_input.text().strip()
        if text == "":
            return

        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCHeckState(Qt.Unchecked)
        self.task_list.addItem(item)

        self.task_input.clear()
        self.update_progress()

    def remove_task(self):
        for item in self.task_list.selectedItems():
            row = self.task_list.row(item)
            self.task_list.takeItem(row)
        self.update_progress()

    def done_count(self):
        """Count how many tasks are ticked."""
        count = 0
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item.checkState() == Qt.Checked:
                count += 1
        return count

    def update_progress(self, item=None):
        total = self.task_list.count()
        self.progress_label.setText(f"{self.done_count()} of {total} task done")


app = QApplication(sys.argv)
window = FlowstateWindow()
window.show()
sys.exit(app.exec())
