import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGroupBox,
    QHBoxLayout, QLabel, QPushButton, QSlider, QCheckBox, QStackedWidget,
    QDialog, QListWidget, QListWidgetItem, QFileDialog, QLineEdit
)
from PySide6.QtCore import Qt
from pathlib import Path

from src.settings import *


APP_STYLESHEET = """
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

SETTINGS_STYLESHEET = """
QWidget {
    background-color: #1e1f22;
    color: #ffffff;
    font-weight: bold;
}

QLabel#titleLabel {
    font-size: 32px;
}

QPushButton {
    background-color: #4c79a6;
    font-size: 16px;
    border-radius: 8px;
    padding: 8px 0px;
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
        settings_layout = QHBoxLayout(self)
        settings_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(150)

        self.pages = QStackedWidget()

        settings_layout.addWidget(self.sidebar)
        settings_layout.addWidget(self.pages)

        self.sidebar.currentRowChanged.connect(self.pages.setCurrentIndex)
        
        self.init_general()
        self.init_scene()
        self.init_video()

        # Select the first item by default
        self.sidebar.setCurrentRow(0)

    def init_general(self):
        self.sidebar.addItem("General")

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("General Settings")
        title.setObjectName("titleLabel")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.pages.addWidget(page)

    def init_scene(self):
        self.sidebar.addItem("Scene Settings")

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Scene Settings")
        title.setObjectName("titleLabel")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.pages.addWidget(page)

        scene_path_edit = QLineEdit()
        scene_path_edit.setText(settings.file_paths.scene.name)
        scene_path_edit.setFixedWidth(200)
        scene_path_label = QLabel("Selected Scene:")

        layout.addWidget(scene_path_label)
        layout.addWidget(scene_path_edit)

        scene_file_button = QPushButton("Browse")
        scene_file_button.setFixedWidth(200)
        scene_file_button.clicked.connect(self.browse_scene_file)

        layout.addWidget(scene_file_button)

    def init_video(self):
        self.sidebar.addItem("Video Settings")

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Video Settings")
        title.setObjectName("titleLabel")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.pages.addWidget(page)

    def browse_scene_file(self):
        QFileDialog.getOpenFileName(self, "Select Scene File", "")


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

        run_button = QPushButton("Run")
        run_button.setFixedWidth(300)
        run_button.clicked.connect(self.run)
        layout.addWidget(run_button, alignment=Qt.AlignmentFlag.AlignCenter)

        settings_button = QPushButton("Settings")
        settings_button.setFixedWidth(300)
        settings_button.clicked.connect(self.open_settings)
        layout.addWidget(settings_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def run(self):
        print(0)

    def open_settings(self):
        """
        Open a settings dialog window in a way which doesn't block the main application.
        """

        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog()

        self.settings_dialog.setStyleSheet(SETTINGS_STYLESHEET)

        self.settings_dialog.show()
        # Bring settings dialog to the front
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()



def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    launcher = Launcher()
    launcher.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
