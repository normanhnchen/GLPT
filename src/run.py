import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QProgressBar, QScrollArea,
    QHBoxLayout, QLabel, QPushButton, QSlider, QCheckBox, QStackedWidget, QSpinBox,
    QDialog, QListWidget, QListWidgetItem, QFileDialog, QLineEdit, QToolButton, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal
from pathlib import Path

from src.settings import *
from src.model import *
import src.renderer as renderer
import src.ai.training.renderer as ai_training_renderer


APP_STYLESHEET = """
QWidget {
    background-color: #1e1f22;
    color: #ffffff;
    font-weight: bold;
}

QLabel#titleLabel {
    font-size: 96px;
}

QLabel#defaultLabel {
    font-size: 16px;
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

AI_TRAINING_STYLESHEET = """
QWidget {
    background-color: #1e1f22;
    color: #ffffff;
    font-weight: bold;
}

QPushButton {
    background-color: #4c79a6;
    font-size: 32px;
    border-radius: 8px;
    padding: 16px 4px;
}

QPushButton:hover {
    background-color: #7ca4cc;
}
"""

COLLAPSIBLE_SECTION_STYLESHEET = """
QToolButton#titleLabel {
    font-size: 24px;
    border: none;
}

QScrollArea {
    border: none;
}
"""

SCENE_SETTINGS_WIDTH = 200
AI_TRAINING_WIDTH = 400
MENU_WIDTH = 300

NO_HDRI = object()


class CollapsibleSection(QWidget):
    def __init__(self, title, width=None):
        super().__init__()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.toggle_button = QToolButton(self)
        self.toggle_button.setText(title)
        self.toggle_button.setObjectName("titleLabel")
        if width:
            self.toggle_button.setFixedWidth(width)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.clicked.connect(self.toggle)

        self.content_widget = QWidget(self)
        self.content_widget.setVisible(False)

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.main_layout.addWidget(self.toggle_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.main_layout.addWidget(self.content_widget)

    def toggle(self, checked):
        if checked:
            self.toggle_button.setArrowType(Qt.ArrowType.DownArrow)
        else:
            self.toggle_button.setArrowType(Qt.ArrowType.RightArrow)

        self.content_widget.setVisible(checked)

    def add_content_widget(self, widget):
        self.content_layout.addWidget(widget)


class IntSpinBox(QWidget):
    def __init__(self, label, min, max, default_val):
        super().__init__()

        self.box_layout = QHBoxLayout(self)

        self.label = QLabel(label)

        self.spin_box = QSpinBox()
        self.spin_box.setRange(min, max)
        self.spin_box.setValue(default_val)

        self.label.setBuddy(self.spin_box)

        self.box_layout.addWidget(self.label)
        self.box_layout.addWidget(self.spin_box)


class SceneSelector(QWidget):
    def __init__(self, label):
        super().__init__()

        self.selected_path = None

        self.main_layout = QVBoxLayout(self)

        self.label = QLabel(label)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("defaultLabel")

        self.box_layout = QHBoxLayout()

        self.import_button = QPushButton("Import")
        self.import_button.clicked.connect(self.browse)
        self.import_button.setFixedWidth(SCENE_SETTINGS_WIDTH)

        self.existing_combo = QComboBox()
        self.existing_combo.setFixedWidth(SCENE_SETTINGS_WIDTH)
        self.existing_combo.currentIndexChanged.connect(self._select_existing)

        self.box_layout.addWidget(self.existing_combo)
        self.box_layout.addWidget(self.import_button)

        self.main_layout.addWidget(self.label)
        self.main_layout.addLayout(self.box_layout)

        self.refresh_existing()

    def refresh_existing(self):
        model_paths = sorted(settings.file_paths.scenes.glob("*.glb"))

        self.existing_combo.blockSignals(True)
        self.existing_combo.clear() # Remove old entries
        self.existing_combo.addItem("Select existing", None)
        for model_path in model_paths:
            self.existing_combo.addItem(model_path.name, model_path)
        self.existing_combo.blockSignals(False)

    def _select_existing(self, idx):
        model_path = self.existing_combo.itemData(idx)

        if model_path is not None:
            self.selected_path = model_path

    def select_path(self, path):
        for i in range(self.existing_combo.count()):
            if self.existing_combo.itemData(i) == path:
                self.existing_combo.setCurrentIndex(i)
                return

        self.selected_path = path

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import File", "", "glTF Files (*.gltf *.glb)")
        if path:
            dst_path = import_model(path)
            self.selected_path = dst_path
            self.refresh_existing()
            self.select_path(dst_path)


class HDRISelector(QWidget):
    def __init__(self, label):
        super().__init__()

        self.selected_path = None

        self.main_layout = QVBoxLayout(self)

        self.label = QLabel(label)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("defaultLabel")

        self.box_layout = QHBoxLayout()

        self.import_button = QPushButton("Import")
        self.import_button.clicked.connect(self.browse)
        self.import_button.setFixedWidth(SCENE_SETTINGS_WIDTH)

        self.existing_combo = QComboBox()
        self.existing_combo.setFixedWidth(SCENE_SETTINGS_WIDTH)
        self.existing_combo.currentIndexChanged.connect(self._select_existing)

        self.box_layout.addWidget(self.existing_combo)
        self.box_layout.addWidget(self.import_button)

        self.main_layout.addWidget(self.label)
        self.main_layout.addLayout(self.box_layout)

        self.refresh_existing()

    def refresh_existing(self):
        hdri_paths = sorted(settings.file_paths.hdris.glob("*.exr"))

        self.existing_combo.blockSignals(True)
        self.existing_combo.clear() # Remove old entries
        self.existing_combo.addItem("Select existing", None)
        for hdri_path in hdri_paths:
            self.existing_combo.addItem(hdri_path.name, hdri_path)
        self.existing_combo.addItem("None", NO_HDRI)
        self.existing_combo.blockSignals(False)

    def _select_existing(self, idx):
        hdri_path = self.existing_combo.itemData(idx)

        if hdri_path is not None:
            if hdri_path == NO_HDRI:
                self.selected_path = False
            else:
                self.selected_path = hdri_path

    def select_path(self, path):
        for i in range(self.existing_combo.count()):
            if self.existing_combo.itemData(i) == path:
                self.existing_combo.setCurrentIndex(i)
                return

        self.selected_path = path
    
    def browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import File", "", "EXR Files (*.exr)")
        if path:
            dst_path = import_model(path)
            self.selected_path = dst_path
            self.refresh_existing()
            self.select_path(dst_path)


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Settings")
        self.resize(600, 400)

        self.init_settings()

    def init_settings(self):
        settings_layout = QHBoxLayout(self)
        settings_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.pages = QStackedWidget()

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(150)
        self.sidebar.currentRowChanged.connect(self.pages.setCurrentIndex)
        # Select the first item by default
        self.sidebar.setCurrentRow(0)

        settings_layout.addWidget(self.sidebar)
        settings_layout.addWidget(self.pages)
        
        self.init_scene()

    def init_scene(self):
        self.sidebar.addItem("Scene Settings")

        page = QWidget()
        box_layout = QVBoxLayout(page)
        box_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Scene Settings")
        title.setObjectName("titleLabel")

        self.texture_size_layout = QHBoxLayout()
        self.texture_size_width_spin_box = IntSpinBox("Texture Size", 1, 16384, settings.rendering.texture_size[0])
        self.texture_size_height_spin_box = IntSpinBox("Texture Size", 1, 16384, settings.rendering.texture_size[1])

        self.texture_size_label = QLabel("Texture Size")
        self.texture_size_label.setObjectName("defaultLabel")

        self.scene_selector = SceneSelector("Scene File")
        self.hdri_selector = HDRISelector("HDRI File")

        self.texture_size_layout.addWidget(self.texture_size_width_spin_box, alignment=Qt.AlignmentFlag.AlignCenter)
        self.texture_size_layout.addWidget(self.texture_size_height_spin_box, alignment=Qt.AlignmentFlag.AlignCenter)

        box_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.pages.addWidget(page)
        box_layout.addWidget(self.scene_selector)
        box_layout.addWidget(self.hdri_selector)
        box_layout.addWidget(self.texture_size_label, alignment=Qt.AlignmentFlag.AlignCenter)
        box_layout.addLayout(self.texture_size_layout)
        box_layout.addSpacing(20)
        box_layout.addWidget(self.init_bvh(), alignment=Qt.AlignmentFlag.AlignJustify)

    def init_bvh(self):
        section = CollapsibleSection("Advanced", SCENE_SETTINGS_WIDTH)
        section.setStyleSheet(COLLAPSIBLE_SECTION_STYLESHEET)

        # BVH Settings
        # ------------
        self.sah_bins_spin_box = IntSpinBox("SAH Bins", 1, 64, settings.bvh.sah_bins)
        self.max_leaf_size_spin_box = IntSpinBox("Max Leaf Size", 1, 64, settings.bvh.max_leaf_size)

        section.add_content_widget(self.sah_bins_spin_box)
        section.add_content_widget(self.max_leaf_size_spin_box)

        return section

    def apply_to_settings(self):
        if self.scene_selector.selected_path is not None:
            settings.file_paths.scene = self.scene_selector.selected_path

        if self.hdri_selector.selected_path is not None:
            settings.file_paths.hdri = self.hdri_selector.selected_path

        settings.rendering.texture_size[0] = self.texture_size_width_spin_box.spin_box.value()
        settings.rendering.texture_size[1] = self.texture_size_height_spin_box.spin_box.value()

        settings.bvh.sah_bins = self.sah_bins_spin_box.spin_box.value()
        settings.bvh.max_leaf_size = self.max_leaf_size_spin_box.spin_box.value()


class AITrainingDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Training")
        self.resize(600, 400)

        self.init_buttons()

    def init_buttons(self):
        buttons_layout = QVBoxLayout(self)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        camera_setup_button = QPushButton("Camera Setup Mode")
        camera_setup_button.setFixedWidth(AI_TRAINING_WIDTH)
        camera_setup_button.clicked.connect(self.run_camera_setup)

        auto_rendering_button = QPushButton("Auto Rendering Mode")
        auto_rendering_button.setFixedWidth(AI_TRAINING_WIDTH)
        auto_rendering_button.clicked.connect(self.run_auto_render)

        buttons_layout.addWidget(camera_setup_button)
        buttons_layout.addWidget(auto_rendering_button)

    def run_camera_setup(self):
        settings.ai_training.mode = "camera_setup"
        settings.rendering.mode = "rasterization"
        QApplication.instance().quit()

    def run_auto_render(self):
        settings.ai_training.mode = "render"
        settings.rendering.mode = "path_tracing"
        QApplication.instance().quit()


class LoadWorker(QThread):
    progress = Signal(int, str)
    finished_loading = Signal(object, object, object, object) # Scene, AIDenoiser, Camera, buffer (dict)
    failed = Signal(str)

    def run(self):
        try:
            scene, ai_denoiser, camera, buffers = renderer.preload_scene_data(progress_callback=self.progress.emit)
        
        except Exception as e:
            self.failed.emit(str(e))
            return

        self.finished_loading.emit(scene, ai_denoiser, camera, buffers)


class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GLPT")
        self.resize(1080, 720)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_menu()
        self.init_launcher()

        self.stacked_widget.setCurrentWidget(self.menu_widget)

        self.pending_run_data = None
    
    def init_menu(self):
        self.menu_widget = QWidget()
        box_layout = QVBoxLayout(self.menu_widget)
        box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.settings_dialog = None
        self.ai_training_dialog = None

        title = QLabel("GLPT")
        title.setObjectName("titleLabel")

        run_button = QPushButton("Run")
        run_button.setFixedWidth(MENU_WIDTH)
        run_button.clicked.connect(self.run)

        settings_button = QPushButton("Settings")
        settings_button.setFixedWidth(MENU_WIDTH)
        settings_button.clicked.connect(self.open_settings)

        ai_training_button = QPushButton("AI Training")
        ai_training_button.setFixedWidth(MENU_WIDTH)
        ai_training_button.clicked.connect(self.open_ai_training)

        box_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        box_layout.addSpacing(50)
        box_layout.addWidget(run_button, alignment=Qt.AlignmentFlag.AlignCenter)
        box_layout.addWidget(settings_button, alignment=Qt.AlignmentFlag.AlignCenter)
        box_layout.addWidget(ai_training_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stacked_widget.addWidget(self.menu_widget)

    def init_launcher(self):
        self.loading_widget = QWidget()
        self.loading_layout = QVBoxLayout(self.loading_widget)
        self.loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)

        self.loading_label = QLabel("Loading...")
        self.loading_label.setObjectName("defaultLabel")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.loading_layout.addWidget(self.loading_label)
        self.loading_layout.addWidget(self.progress_bar)

        self.stacked_widget.addWidget(self.loading_widget)

    def run(self):
        settings.ai_training.mode = "off"
        self.save_user_settings()

        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        self.stacked_widget.setCurrentWidget(self.loading_widget)

        self.worker = LoadWorker()
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_loading.connect(self.on_finished_loading)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()
    
    def save_user_settings(self):
        if self.settings_dialog is not None:
            self.settings_dialog.apply_to_settings()

        settings.export_user_settings()
    
    def on_progress(self, percent, message):
        self.progress_bar.setValue(percent)
        self.loading_label.setText(message)

    def on_finished_loading(self, scene, ai_denoiser, camera, buffers):
        # Make sure the OS thread has actually finished
        self.worker.wait()
        self.pending_run_data = (scene, ai_denoiser, camera, buffers)
        self.close()
        QApplication.instance().quit()

    def on_failed(self, error_message):
        self.loading_label.setText(f"Failed to load: {error_message}")

    def open_ai_training(self):
        """Open an AI training dialog window in a way which doesn't block the main application."""

        if not self.ai_training_dialog:
            self.ai_training_dialog = AITrainingDialog()

        self.ai_training_dialog.setStyleSheet(AI_TRAINING_STYLESHEET)

        self.ai_training_dialog.show()
        # Bring AI training dialog to the front
        self.ai_training_dialog.raise_()
        self.ai_training_dialog.activateWindow()

    def open_settings(self):
        """Open a settings dialog window in a way which doesn't block the main application."""

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

    app.exec()

    if launcher.pending_run_data is not None:
        scene, ai_denoiser, camera, buffers = launcher.pending_run_data
        renderer.run_app(scene, ai_denoiser, camera, buffers)

    if settings.ai_training.mode == "camera_setup" or settings.ai_training.mode == "render":
        ai_training_renderer.run_app()


if __name__ == "__main__":
    main()
