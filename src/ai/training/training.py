import torch
from torch.utils.data import Dataset, DataLoader, random_split
import cv2
import os
import random
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QProgressBar, QScrollArea,
    QHBoxLayout, QLabel, QPushButton, QSlider, QCheckBox, QStackedWidget, QSpinBox,
    QDialog, QListWidget, QListWidgetItem, QFileDialog, QLineEdit, QToolButton, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal

from src.settings import *
from src.ai.denoiser.network import *


# Required as OpenCV disables EXR support by default
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"


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


def load_exr(path, nan=0, posinf=0, neginf=0):
    img = cv2.imread(str(path), cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
    # OpenCV loads as BGR, so convert to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # Remove possible NaNs to prevent it from propagating through the network
    img = np.nan_to_num(img, nan=nan, posinf=posinf, neginf=neginf)

    return img


def exr_to_tensor(exr_img, keep_channels=None):
    # Create 1d array from the texture data
    t = torch.from_numpy(exr_img).float()
    # Reshape from EXR to 3d tensor PyTorch convention (C, H, W)
    t = t.permute(2, 0, 1).contiguous()
    
    if keep_channels is not None:
        t = t[:keep_channels]

    return t


# See 9.5 Training
def save_checkpoint(checkpoint, path):
    """
    Saves to the checkpoing temp file then replaces the actual checkpoint file.
    Prevents file corruption when breaking in the terminal during the middle of a normal save.
    """

    path = Path(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")

    try:
        with tmp_path.open("wb") as f:
            torch.save(checkpoint, f)
        tmp_path.replace(path)
    
    except:
        tmp_path.unlink(missing_ok=True)
        raise


# See 9.5 Training
class DenoiseDataset(Dataset):
    def __init__(self, renders_path, patch_size=256):
        self.combined_path = renders_path / "combined/"
        self.albedo_path = renders_path / "albedo/"
        self.normal_path = renders_path / "normal/"
        self.depth_path = renders_path / "depth/"
        self.target_path = renders_path / "target/"

        self.num_samples = sum(1 for item in self.combined_path.iterdir() if item.is_file())
        self.patch_size = patch_size

    def __len__(self):
        return self.num_samples
    
    def __getitem__(self, idx):
        # Load EXR images from their paths
        # --------------------------------
        combined = load_exr(self.combined_path / f"combined_{idx}.exr")
        albedo = load_exr(self.albedo_path / f"albedo_{idx}.exr")
        normal = load_exr(self.normal_path / f"normal_{idx}.exr")
        depth = load_exr(self.depth_path / f"depth_{idx}.exr")
        target = load_exr(self.target_path / f"target_{idx}.exr")

        # Convert EXR images to PyTorch tensors
        # -------------------------------------
        combined = exr_to_tensor(combined, keep_channels=3)
        albedo = exr_to_tensor(albedo, keep_channels=3)
        normal = exr_to_tensor(normal, keep_channels=3)
        depth = exr_to_tensor(depth, keep_channels=1)
        target = exr_to_tensor(target, keep_channels=3)

        # Normalize depth via the inverse depth method
        depth = denoiser.normalize_depth(depth)

        x = torch.cat([combined, albedo, normal, depth])

        # Get random image patch
        # ----------------------
        _, h, w = x.shape

        top = random.randint(0, h - self.patch_size)
        bottom = top + self.patch_size
        left = random.randint(0, w - self.patch_size)
        right = left + self.patch_size

        x = x[:, top:bottom, left:right]
        target = target[:, top:bottom, left:right]

        x, target = self._augment(x, target)

        return x, target

    def _augment(self, x, target):
        k = random.randint(0, 3)
        if k > 0:
            x = torch.rot90(x, k, dims=[1, 2])
            target = torch.rot90(target, k, dims=[1, 2])
        
        return x, target


# See 9.5 Training
def _preprocess(x, target):
    combined = x[:, :3]
    albedo = x[:, 3:6]
    normal = x[:, 6:9]
    depth = x[:, 9:10]

    combined = denoiser.demodulate(combined, albedo)
    target = denoiser.demodulate(target, albedo)

    combined = denoiser.compress(combined)
    target = denoiser.compress(target)

    x = torch.cat([combined, albedo, normal, depth], dim=1)
    return x, target


class WorkerThread(QThread):
    progress = Signal(int)
    setup_progress = Signal(int)
    status = Signal(str)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.should_close = False

    def stop(self):
        self.should_close = True

    def run(self):
        try:
            self.train()
        except Exception as e:
            self.error.emit(str(e))

    def train(self):
        # See 9.5 Training
        # ----------------
        full_dataset = DenoiseDataset(settings.file_paths.ai_training.renders)
        # Split 10% of the dataset to be validation cases
        val_size = max(1, int(0.1 * len(full_dataset)))
        # Split the rest of the dataset to be train cases
        train_size = len(full_dataset) - val_size

        train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

        train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=4, shuffle=False)

        epochs = 300

        # Tell the progress bar that 300 is the maximum value
        self.setup_progress.emit(epochs)

        # See 9.5 Training
        # ----------------
        try:
            checkpoint = torch.load(settings.file_paths.denoiser.checkpoint, map_location=AI_DEVICE)
            denoiser.load_state_dict(checkpoint["model_state_dict"])
            optim.load_state_dict(checkpoint["optimizer_state_dict"])
            starting_epoch = checkpoint["epoch"] + 1

            self.progress.emit(starting_epoch) 
            self.status.emit(f"Resumed at epoch {starting_epoch}...")

        except FileNotFoundError:
            starting_epoch = 0

        for epoch in range(starting_epoch, epochs):
            if self.should_close:
                break

            # Training loop
            # See 9.5 Training
            # ----------------
            denoiser.train()
            epoch_loss = 0
            for x, target in train_loader:
                if self.should_close:
                    break
                
                x = x.to(AI_DEVICE)
                target = target.to(AI_DEVICE)
                x, target = _preprocess(x, target)
                combined = x[:, :3].to(AI_DEVICE)

                optim.zero_grad()
                prediction = denoiser(x, combined)
                loss = criterion(prediction, target)
                loss.backward()
                optim.step()

                epoch_loss += loss.item() / len(train_loader)

            if self.should_close:
                break
            
            # Validation loop
            # ---------------
            denoiser.eval()
            val_loss = 0
            with torch.no_grad():
                for x, target in val_loader:
                    if self.should_close:
                        break
                
                    x = x.to(AI_DEVICE)
                    target = target.to(AI_DEVICE)
                    x, target = _preprocess(x, target)
                    combined = x[:, :3].to(AI_DEVICE)

                    prediction = denoiser(x, combined)
                    
                    val_loss += criterion(prediction, target).item() / len(val_loader)
            
            if self.should_close:
                break

            # Update the text label
            status_text = f"Epoch: {epoch} | Epoch Loss: {epoch_loss:.6f} | Val Loss: {val_loss:.6f}"
            self.status.emit(status_text)

            # Update the progress bar (epoch + 1 to fill the progress bar completely on the last one)
            self.progress.emit(epoch + 1)
            
            curr_checkpoint = {
                "epoch": epoch,
                "model_state_dict": denoiser.state_dict(),
                "optimizer_state_dict": optim.state_dict(),
                "loss": epoch_loss
            }

            save_checkpoint(curr_checkpoint, settings.file_paths.denoiser.checkpoint)

        self.status.emit("Training Complete!")


class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Training")
        self.resize(400, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.on_start)

        self.main_layout.addWidget(self.start_button)

        self.worker = None

    def on_start(self):
        # Remove the start button
        self.main_layout.removeWidget(self.start_button)
        # Remove from memory
        self.start_button.deleteLater()

        status_label = QLabel("Preparing dataset...")
        
        progress_bar = QProgressBar()
        progress_bar.setValue(0)

        self.main_layout.addWidget(status_label)
        self.main_layout.addWidget(progress_bar)

        self.worker = WorkerThread()

        self.worker.status.connect(status_label.setText)
        self.worker.progress.connect(progress_bar.setValue)
        self.worker.setup_progress.connect(progress_bar.setMaximum)

        self.worker.start()

    def closeEvent(self, event):
        """
        Called automatically when the user closes the window.
        Safely terminates worker threads when terminating the program before they finish.
        """
        if self.worker and self.worker.isRunning():
            # Break the training loop
            self.worker.stop()
            # Block until the thread finishes shutting down
            self.worker.wait()
        # Close the window
        event.accept()


# Initialize globally so the dataset can access it
denoiser = KPCN().to(AI_DEVICE)
optim = torch.optim.Adam(denoiser.parameters(), lr=1e-4)
criterion = nn.L1Loss()

def run_app():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    launcher = Launcher()
    launcher.show()

    app.exec()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    launcher = Launcher()
    launcher.show()

    app.exec()


if __name__ == "__main__":
    main()
