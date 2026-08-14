import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QSlider, QCheckBox, QStackedWidget
)
from PySide6.QtCore import Qt


STYLESHEET = """
QWidget {
    background-color: #1e1f22;
    color: #ffffff;
    font-weight: bold;
}

QLabel#titleLabel {
    font-size: 48px;
}

QPushButton {
    background-color: #4c79a6;
    font-size: 24px;
    border-radius: 8px;
    padding: 8px 0px;
}
"""

class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GLPT")
        self.resize(1080, 720)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self._init_menu_screen()

        self.stacked_widget.addWidget(self.menu_widget)
    
    def _init_menu_screen(self):
        self.menu_widget = QWidget()
        layout = QVBoxLayout(self.menu_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("GLPT")
        title.setObjectName("titleLabel")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(50)

        button_run = QPushButton("Run")
        button_run.setFixedWidth(200)
        button_run.clicked.connect(self._on_button_run)
        layout.addWidget(button_run, alignment=Qt.AlignmentFlag.AlignCenter)

    def _on_button_run(self):
        print(0)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    launcher = Launcher()
    launcher.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
