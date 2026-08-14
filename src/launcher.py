import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGroupBox,
    QHBoxLayout, QLabel, QPushButton, QSlider, QCheckBox, QStackedWidget,
    QDialog,
)
from PySide6.QtCore import Qt


STYLESHEET = """
QWidget {
    background-color: #1e1f22;
    color: #ffffff;
    font-weight: bold;
}

QLabel#titleLabel {
    font-size: 96px;
}

QPushButton {
    background-color: #4c79a6;
    font-size: 36px;
    border-radius: 8px;
    padding: 16px 4px;
}

QPushButton:hover {
    background-color: #7ca4cc;
}
"""


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.resize(600, 400)

        self.init_settings()

    def init_settings(self):
        pass


class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GLPT")
        self.resize(1080, 720)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_menu()

        self.stacked_widget.addWidget(self.menu_widget)
    
    def init_menu(self):
        self.menu_widget = QWidget()
        layout = QVBoxLayout(self.menu_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.settings_dialog = None

        title = QLabel("GLPT")
        title.setObjectName("titleLabel")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(50)

        button_run = QPushButton("Run")
        button_run.setFixedWidth(300)
        button_run.clicked.connect(self.run)
        layout.addWidget(button_run, alignment=Qt.AlignmentFlag.AlignCenter)

        button_settings = QPushButton("Settings")
        button_settings.setFixedWidth(300)
        button_settings.clicked.connect(self.open_settings)
        layout.addWidget(button_settings, alignment=Qt.AlignmentFlag.AlignCenter)

    def run(self):
        print(0)

    def open_settings(self):
        """
        Open a settings dialog window in a way which doesn't block the main application.
        """

        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog()

        self.settings_dialog.show()
        # Bring settings dialog to the front
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()



def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    launcher = Launcher()
    launcher.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
