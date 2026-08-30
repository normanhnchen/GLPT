import torch
from torch.utils.data import Dataset, DataLoader, Subset
import torch.nn as nn
import cv2
import os
import random
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QProgressBar, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QThread, Signal
import pyqtgraph as pg
import numpy as np
from pathlib import Path

from src.settings import settings
from src.ai.denoiser.network import KPCN


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

MENU_WIDTH = 300

# Number of random grid patches sampled per validation image per epoch
NUM_VAL_SAMPLES_PER_IMAGE = 4


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
    def __init__(self, renders_path, patch_size=256, is_validation=False):
        self.combined_path = renders_path / "combined/"
        self.albedo_path = renders_path / "albedo/"
        self.normal_path = renders_path / "normal/"
        self.depth_path = renders_path / "depth/"
        self.target_path = renders_path / "target/"

        self.num_samples = sum(1 for item in self.combined_path.iterdir() if item.is_file())
        self.patch_size = patch_size

        self.is_validation = is_validation

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

        if self.is_validation:
            x_patches = []
            target_patches = []

            _, h, w = x.shape

            # Loop across the image vertically and horizontally in patch_size steps
            # Split the image into a grid of patch_size chunks for parallelized
            # validation across image patches
            for y in range(0, h - self.patch_size + 1, self.patch_size):
                for x_coord in range(0, w - self.patch_size + 1, self.patch_size):

                    # Crop current image patch
                    x_crop = x[:, y : y + self.patch_size, x_coord : x_coord + self.patch_size]
                    t_crop = target[:, y : y + self.patch_size, x_coord : x_coord + self.patch_size]
                    
                    x_patches.append(x_crop)
                    target_patches.append(t_crop)

            # shape: (num patches, channels, batch_size, batch_size)
            x = torch.stack(x_patches)
            target = torch.stack(target_patches)

        else:
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
    loss_update = Signal(int, float, float)

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
        full_dataset_train = DenoiseDataset(settings.file_paths.ai_training.renders, is_validation=False)
        full_dataset_val = DenoiseDataset(settings.file_paths.ai_training.renders, is_validation=True)

        # Split 10% of the dataset to be validation cases
        val_size = max(1, int(0.1 * len(full_dataset_val)))

        gen = torch.Generator().manual_seed(999)
        indices = torch.randperm(len(full_dataset_train), generator=gen).tolist()

        train_dataset = Subset(full_dataset_train, indices[val_size:])
        val_dataset = Subset(full_dataset_val, indices[:val_size])

        train_loader = DataLoader(
            train_dataset,
            batch_size=4,
            shuffle=True,
            # Parallelize data loading across worker processes
            num_workers=4,
            # Apply fast CPU -> GPU transfer
            pin_memory=True,
            # Keep workers alive between epochs
            persistent_workers=True
        )
        val_loader = DataLoader(val_dataset, batch_size=1, shuffle=False)

        # Cache validation data
        # Validation is static and repeated across epochs
        val_x_cache = []
        val_target_cache = []
        for x_grid, target_grid in val_loader:
            val_x_cache.append(x_grid.squeeze(0))
            val_target_cache.append(target_grid.squeeze(0))

        # Tell the progress bar the maximum epoch value
        self.setup_progress.emit(settings.ai_training.training.epochs)

        # See 9.5 Training
        # ----------------
        try:
            checkpoint = torch.load(settings.file_paths.denoiser.checkpoint, map_location=settings.pytorch_device)
            denoiser.load_state_dict(checkpoint["model_state_dict"])
            optim.load_state_dict(checkpoint["optimizer_state_dict"])
            starting_epoch = checkpoint["epoch"] + 1

            self.progress.emit(starting_epoch) 
            self.status.emit(f"Resumed at epoch {starting_epoch}...")

            if "train_history" in checkpoint and "val_history" in checkpoint:
                train_history = checkpoint["train_history"]
                val_history = checkpoint["val_history"]
                
                # Plot the previous saved graph values
                for e, (t_loss, v_loss) in enumerate(zip(train_history, val_history)):
                    self.loss_update.emit(e, t_loss, v_loss)
                
            else:
                train_history = []
                val_history = []

        except FileNotFoundError:
            starting_epoch = 0
            train_history = []
            val_history = []

        for epoch in range(starting_epoch, settings.ai_training.training.epochs):
            if self.should_close:
                break

            # Training loop
            # See 9.5 Training
            # ----------------
            denoiser.train()
            epoch_loss = 0
            total_train_samples = 0
            for x, target in train_loader:
                if self.should_close:
                    break
                
                x = x.to(settings.pytorch_device)
                target = target.to(settings.pytorch_device)
                x, target = _preprocess(x, target)
                combined = x[:, :3].to(settings.pytorch_device)

                optim.zero_grad()
                prediction = denoiser(x, combined)
                loss = criterion(prediction, target)
                loss.backward()
                optim.step()

                # Multiply the loss value by the number of batches
                epoch_loss += loss.item() * x.size(0)
                
                total_train_samples += x.size(0)

            if self.should_close:
                break

            # Divide by the total samples processed across all batches
            epoch_loss = epoch_loss / max(1, total_train_samples)
            
            # Validation loop
            # ---------------
            denoiser.eval()
            val_loss = 0
            total_val_patches = 0
            with torch.no_grad():
                for x_grid, target_grid in zip(val_x_cache, val_target_cache):
                    if self.should_close:
                        break

                    # Remove batch dimension
                    # (num batches, num patches, channels, batch_size, batch_size)
                    # -> (num patches, channels, batch_size, batch_size)
                    x_grid = x_grid.squeeze(0)
                    target_grid = target_grid.squeeze(0)
 
                    # Randomly sample a few image patches instead
                    num_patches = x_grid.size(0)
                    k = min(NUM_VAL_SAMPLES_PER_IMAGE, num_patches)
                    patch_indices = torch.randperm(num_patches)[:k]
 
                    x = x_grid[patch_indices].to(settings.pytorch_device)
                    target = target_grid[patch_indices].to(settings.pytorch_device)
 
                    x, target = _preprocess(x, target)
                    combined = x[:, :3].to(settings.pytorch_device)
 
                    prediction = denoiser(x, combined)
 
                    # Multiply the validation loss by the number of patches
                    val_loss += criterion(prediction, target).item() * x.size(0)
 
                    total_val_patches += x.size(0)
            
            if self.should_close:
                break

            # Divide by the total patches processed across all validation images
            val_loss = val_loss / max(1, total_val_patches)

            # Update the text label
            status_text = f"Epoch: {epoch} / {settings.ai_training.training.epochs}"
            self.status.emit(status_text)

            self.loss_update.emit(epoch, epoch_loss, val_loss)

            # Update the progress bar (epoch + 1 to fill the progress bar completely on the last one)
            self.progress.emit(epoch + 1)

            train_history.append(epoch_loss)
            val_history.append(val_loss)
            
            curr_checkpoint = {
                "epoch": epoch,
                "model_state_dict": denoiser.state_dict(),
                "optimizer_state_dict": optim.state_dict(),
                "loss": epoch_loss,
                "train_history": train_history,
                "val_history": val_history
            }

            save_checkpoint(curr_checkpoint, settings.file_paths.denoiser.checkpoint)

        self.status.emit("Training Complete!")


class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Training")
        self.resize(1080, 720)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title = QLabel("AI Training")
        self.title.setObjectName("titleLabel")

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.on_start)
        self.start_button.setFixedWidth(MENU_WIDTH)

        self.main_layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.worker = None

    def on_start(self):
        # Remove widgets
        # --------------
        self.main_layout.removeWidget(self.title)
        self.main_layout.removeWidget(self.start_button)
        # Remove from memory
        # ------------------
        self.title.deleteLater()
        self.start_button.deleteLater()

        self.status_label = QLabel("Preparing dataset...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("defaultLabel")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(50)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setStyleSheet(APP_STYLESHEET)
        self.plot_widget.setTitle("Loss Graph")
        self.plot_widget.setLabel("left", "Loss")
        self.plot_widget.setLabel("bottom", "Epoch")
        self.plot_widget.addLegend()
        self.plot_widget.setLogMode(x=False, y=True)
        self.plot_widget.setXRange(0, settings.ai_training.training.epochs)
        self.plot_widget.getViewBox().setLimits(xMin=0, xMax=settings.ai_training.training.epochs)

        self.epochs_data = []
        self.train_loss_data = []
        self.val_loss_data = []

        train_pen = pg.mkPen(color="#4d89c580", width=2)
        val_pen = pg.mkPen(color="#ffffff80", width=2)

        # Set anchor to be directly right of the graph line with breathing room space to the right
        anchor = (-0.1, 0.5)
        self.train_tip_label = pg.TextItem(color="#7ca4cc", anchor=anchor)
        self.val_tip_label = pg.TextItem(color="#ffffff", anchor=anchor)

        self.plot_widget.addItem(self.train_tip_label)
        self.plot_widget.addItem(self.val_tip_label)

        self.train_line = self.plot_widget.plot(pen=train_pen, name="Train Loss")
        self.val_line = self.plot_widget.plot(pen=val_pen, name="Val Loss")

        self.main_layout.addWidget(self.status_label)
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(self.plot_widget)

        self.worker = WorkerThread()

        self.worker.status.connect(self.status_label.setText)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.setup_progress.connect(self.progress_bar.setMaximum)
        self.worker.loss_update.connect(self.update_plot)

        self.worker.start()

    def update_plot(self, epoch, train_loss, val_loss):
        self.epochs_data.append(epoch)
        self.train_loss_data.append(train_loss)
        self.val_loss_data.append(val_loss)

        self.train_tip_label.setText(f"{train_loss:.6f}")
        self.val_tip_label.setText(f"{val_loss:.6f}")

        # The plot is logarithmic, so convert y coordinates to log10
        self.train_tip_label.setPos(epoch, np.log10(max(train_loss, 1e-8)))
        self.val_tip_label.setPos(epoch, np.log10(max(val_loss, 1e-8)))

        self.train_line.setData(self.epochs_data, self.train_loss_data)
        self.val_line.setData(self.epochs_data, self.val_loss_data)

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
denoiser = KPCN().to(settings.pytorch_device)
optim = torch.optim.Adam(denoiser.parameters(), lr=1e-4)
criterion = nn.L1Loss()

def run_app():
    app = QApplication.instance()

    if app is None:
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
