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
    def __init__(self, renders_path, patch_size=64, patches_per_image=1, is_validation=False):
        self.diffuse_path = renders_path / "diffuse/"
        self.specular_path = renders_path / "specular/"
        self.albedo_path = renders_path / "albedo/"
        self.normal_path = renders_path / "normal/"
        self.depth_path = renders_path / "depth/"
        self.target_diffuse_path = renders_path / "target_diffuse/"
        self.target_specular_path = renders_path / "target_specular/"

        self.diffuse_sq_path = renders_path / "diffuse_sq/"
        self.specular_sq_path = renders_path / "specular_sq/"
        self.albedo_sq_path = renders_path / "albedo_sq/"
        self.normal_sq_path = renders_path / "normal_sq/"
        self.depth_sq_path = renders_path / "depth_sq/"

        self.num_samples = sum(1 for item in self.diffuse_path.iterdir() if item.is_file())
        self.patch_size = patch_size
        self.patches_per_image = patches_per_image
        self.is_validation = is_validation

    def __len__(self):
        return self.num_samples
    
    def __getitem__(self, idx):
        # Load EXR images from their paths
        # --------------------------------
        diffuse = load_exr(self.diffuse_path / f"diffuse_{idx}.exr")
        specular = load_exr(self.specular_path / f"specular_{idx}.exr")
        albedo = load_exr(self.albedo_path / f"albedo_{idx}.exr")
        normal = load_exr(self.normal_path / f"normal_{idx}.exr")
        depth = load_exr(self.depth_path / f"depth_{idx}.exr")
        target_diffuse = load_exr(self.target_diffuse_path / f"target_diffuse_{idx}.exr")
        target_specular = load_exr(self.target_specular_path / f"target_specular_{idx}.exr")

        # Convert EXR images to PyTorch tensors
        # -------------------------------------
        diffuse_full = exr_to_tensor(diffuse, keep_channels=4)
        diffuse = diffuse_full[..., :3]
        specular = exr_to_tensor(specular, keep_channels=3)
        albedo = exr_to_tensor(albedo, keep_channels=3)
        normal = exr_to_tensor(normal, keep_channels=3)
        depth = exr_to_tensor(depth, keep_channels=1)
        target_diffuse = exr_to_tensor(target_diffuse, keep_channels=3)
        target_specular = exr_to_tensor(target_specular, keep_channels=3)

        diffuse_sq = exr_to_tensor(load_exr(self.diffuse_sq_path / f"diffuse_sq_{idx}.exr"), keep_channels=3)
        specular_sq = exr_to_tensor(load_exr(self.specular_sq_path / f"specular_sq_{idx}.exr"), keep_channels=3)
        albedo_sq = exr_to_tensor(load_exr(self.albedo_sq_path / f"albedo_sq_{idx}.exr"), keep_channels=3)
        normal_sq = exr_to_tensor(load_exr(self.normal_sq_path / f"normal_sq_{idx}.exr"), keep_channels=3)
        depth_sq_full = exr_to_tensor(load_exr(self.depth_sq_path / f"depth_sq_{idx}.exr"), keep_channels=2)
        depth_sq = depth_sq_full[0]

        # We saved the number of depth samples here on the shader side
        depth_samples = depth_sq_full[:, 1]
        # We saved the number of total samples here on the shader side
        total_samples = diffuse_full[..., 3]

        diffuse_variance = denoiser.calculate_variance(diffuse, diffuse_sq, total_samples)
        specular_variance = denoiser.calculate_variance(specular, specular_sq, total_samples)
        albedo_variance = denoiser.calculate_variance(albedo, albedo_sq, total_samples)
        normal_variance = denoiser.calculate_variance(normal, normal_sq, total_samples)
        depth_variance = denoiser.calculate_variance(depth, depth_sq, depth_samples)

        # Normalize depth via the inverse depth method
        depth = denoiser.normalize_depth(depth)

        x = torch.cat([
            diffuse,
            specular,
            albedo,
            normal,
            depth,
            diffuse_variance,
            specular_variance,
            albedo_variance, 
            normal_variance,
            depth_variance
        ])
        target = torch.cat([target_diffuse, target_specular])

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
            x_patches = []
            target_patches = []

            _, h, w = x.shape

            for _ in range(self.patches_per_image):
                # Get random image patch
                # ----------------------

                top = random.randint(0, h - self.patch_size)
                bottom = top + self.patch_size
                left = random.randint(0, w - self.patch_size)
                right = left + self.patch_size

                x_crop = x[:, top:bottom, left:right]
                target_crop = target[:, top:bottom, left:right]

                x_crop, target_crop = self._augment(x_crop, target_crop)

                x_patches.append(x_crop)
                target_patches.append(target_crop)

            x = torch.stack(x_patches)
            target = torch.stack(target_patches)
        
        return x, target

    def _augment(self, x, target):
        k = random.randint(0, 3)
        if k > 0:
            x = torch.rot90(x, k, dims=[1, 2])
            target = torch.rot90(target, k, dims=[1, 2])
        
        return x, target


# See 9.5 Training
def _preprocess(x, target):
    diffuse = x[:, :3]
    specular = x[:, 3:6]
    albedo = x[:, 6:9]
    normal = x[:, 9:12]
    depth = x[:, 12:13]
    diffuse_variance = x[:, 13:16]
    specular_variance = x[:, 16:19]
    albedo_variance = x[:, 19:22]
    normal_variance = x[:, 22:25]
    depth_variance = x[:, 25:26]

    # Taylor-approximation transformation per Bako et al.
    diffuse_variance /= (albedo + settings.ai_training.epsilon) ** 2
    # Add small offset to prevent division by zero
    specular_variance /= specular ** 2 + settings.ai_training.epsilon

    target_diffuse  = target[:, :3]
    target_specular = target[:, 3:6]

    diffuse_demodulated = denoiser.demodulate(diffuse, albedo)
    specular_linear = specular

    diffuse_compressed = denoiser.compress(diffuse_demodulated)
    specular_compressed = denoiser.compress(specular_linear)

    x = torch.cat([
        diffuse_compressed,
        specular_compressed,
        albedo,
        normal,
        depth,
        diffuse_variance,
        specular_variance,
        albedo_variance,
        normal_variance,
        depth_variance
    ], dim=1)

    target_linear = target_diffuse + target_specular

    target_diffuse_demodulated = denoiser.demodulate(target_diffuse, albedo)
    target_specular_compressed = denoiser.compress(target_specular)

    return x, diffuse_demodulated, specular_compressed, target_linear, target_diffuse_demodulated, target_specular_compressed


def _compute_loss(denoiser, x, diffuse_linear, specular_linear,
                   target_diffuse_demodulated, target_specular_compressed, target_linear,
                   is_pretrain):
    albedo = x[:, 6:9]

    diffuse_prediction, specular_prediction = denoiser(x, diffuse_linear, specular_linear)

    if is_pretrain:
        # Pretrain
        # Bako et al. Sec 5.2

        diffuse_loss = criterion(diffuse_prediction, target_diffuse_demodulated)
        specular_loss = criterion(specular_prediction, target_specular_compressed)
        return diffuse_loss + specular_loss
    
    else:
        # Fine-tune
        # Bako et al. Sec 4.3, Eq 4

        diffuse_final = denoiser.remodulate(diffuse_prediction, albedo)
        specular_final = denoiser.decompress(specular_prediction)
        prediction_linear = diffuse_final + specular_final

        return criterion(prediction_linear, target_linear)


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
            batch_size=5,
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

        # Precompute a fixed set of patches per validation image
        # so the same patches are used every epoch instead of stochastically sampled
        val_patch_indices_cache = []
        patch_gen = torch.Generator().manual_seed(9999)
        for x_grid in val_x_cache:
            num_patches = x_grid.size(0)
            k = min(NUM_VAL_SAMPLES_PER_IMAGE, num_patches)
            patch_indices = torch.randperm(num_patches, generator=patch_gen)[:k]
            val_patch_indices_cache.append(patch_indices)

        # Tell the progress bar the maximum epoch value
        self.setup_progress.emit(settings.ai_training.training.epochs)

        # See 9.5 Training
        # ----------------
        try:
            checkpoint = torch.load(settings.file_paths.denoiser.latest_checkpoint, map_location=settings.pytorch_device)
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

            best_val_loss = min(val_history) if val_history else torch.inf

        except FileNotFoundError:
            starting_epoch = 0
            train_history = []
            val_history = []
            best_val_loss = torch.inf

        for epoch in range(starting_epoch, settings.ai_training.training.epochs):
            if self.should_close:
                break

            is_pretrain = epoch < settings.ai_training.training.pretrain_epochs

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

                x = x.flatten(0, 1)
                target = target.flatten(0, 1)

                (x, diffuse_linear, specular_linear, target_linear,
                 target_diffuse_demod, target_specular_comp) = _preprocess(x, target)

                optim.zero_grad()

                loss = _compute_loss(
                    denoiser, x, diffuse_linear, specular_linear,
                    target_diffuse_demod, target_specular_comp, target_linear,
                    is_pretrain
                )
                
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
                for x_grid, target_grid, patch_indices in zip(val_x_cache, val_target_cache, val_patch_indices_cache):
                    if self.should_close:
                        break
 
                    x = x_grid[patch_indices].to(settings.pytorch_device)
                    target = target_grid[patch_indices].to(settings.pytorch_device)
 
                    (x, diffuse_linear, specular_linear, target_linear,
                     target_diffuse_demod, target_specular_comp) = _preprocess(x, target)

                    loss = _compute_loss(
                        denoiser, x, diffuse_linear, specular_linear,
                        target_diffuse_demod, target_specular_comp, target_linear,
                        is_pretrain
                    )
 
                    # Multiply the validation loss by the number of patches
                    val_loss += loss.item() * x.size(0)
 
                    total_val_patches += x.size(0)
            
            if self.should_close:
                break

            # Divide by the total patches processed across all validation images
            val_loss = val_loss / max(1, total_val_patches)

            # Update the text label
            if is_pretrain:
                status_text = f"[Pretraining] Epoch: {epoch} / {settings.ai_training.training.epochs - 1}"
            else:
                status_text = f"[Fine-Tuning] Epoch: {epoch} / {settings.ai_training.training.epochs - 1}"

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

            save_checkpoint(curr_checkpoint, settings.file_paths.denoiser.latest_checkpoint)

            if epoch == settings.ai_training.training.pretrain_epochs:
                best_val_loss = torch.inf
    
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                save_checkpoint(curr_checkpoint, settings.file_paths.denoiser.best_checkpoint)

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

        self.graph_layout = pg.GraphicsLayoutWidget()
        self.graph_layout.setStyleSheet(APP_STYLESHEET)

        # Top plot (Train)
        # ----------------
        self.train_plot = self.graph_layout.addPlot(title="Training Loss")
        self.train_plot.setLabel("left", "Loss")
        self.train_plot.addLegend()
        self.train_plot.setXRange(0, settings.ai_training.training.epochs)
        self.train_plot.getViewBox().setLimits(xMin=0, xMax=settings.ai_training.training.epochs)

        self.graph_layout.nextRow()

        # Bottom plot (Val)
        # -----------------
        self.val_plot = self.graph_layout.addPlot(title="Validation Loss")
        self.val_plot.setLabel("left", "Loss")
        self.val_plot.setLabel("bottom", "Epoch")
        self.val_plot.addLegend()
        self.val_plot.setXRange(0, settings.ai_training.training.epochs)
        self.val_plot.getViewBox().setLimits(xMin=0, xMax=settings.ai_training.training.epochs)
        
        # Link the x-axis of the validation and training plots
        self.val_plot.setXLink(self.train_plot)

        # Pretrain data
        self.pre_epochs = []
        self.pre_train_loss = []
        self.pre_val_loss = []

        # Fine-tune data
        self.ft_epochs = []
        self.ft_train_loss = []
        self.ft_val_loss = []

        # Pretrain pens
        train_pre_pen = pg.mkPen(color="#375c81ff", width=2)
        val_pre_pen = pg.mkPen(color="#6F6F6FFF", width=2)

        # Fine-tune pens
        train_ft_pen = pg.mkPen(color="#5e9fe0ff", width=2)
        val_ft_pen = pg.mkPen(color="#ffffffff", width=2)

        # Set anchor to be directly right of the graph line with breathing room space to the right
        anchor = (-0.1, 0.5)
        self.train_tip_label = pg.TextItem(color="#7ca4cc", anchor=anchor)
        self.val_tip_label = pg.TextItem(color="#ffffff", anchor=anchor)

        self.train_plot.addItem(self.train_tip_label)
        self.val_plot.addItem(self.val_tip_label)

        self.train_pre_line = self.train_plot.plot(pen=train_pre_pen, name="Train (Pretrain)")
        self.val_pre_line = self.val_plot.plot(pen=val_pre_pen, name="Val (Pretrain)")
        
        self.train_ft_line = self.train_plot.plot(pen=train_ft_pen, name="Train (Fine-Tune)")
        self.val_ft_line = self.val_plot.plot(pen=val_ft_pen, name="Val (Fine-Tune)")

        self.main_layout.addWidget(self.status_label)
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(self.graph_layout)

        self.worker = WorkerThread()

        self.worker.status.connect(self.status_label.setText)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.setup_progress.connect(self.progress_bar.setMaximum)
        self.worker.loss_update.connect(self.update_plot)
        self.worker.error.connect(self.status_label.setText)

        self.worker.start()

    def update_plot(self, epoch, train_loss, val_loss):
        # Update text labels
        self.train_tip_label.setText(f"{train_loss:.2e}")
        self.val_tip_label.setText(f"{val_loss:.2e}")
        self.train_tip_label.setPos(epoch, train_loss)
        self.val_tip_label.setPos(epoch, val_loss)

        # Pretrain phase
        if epoch <= settings.ai_training.training.pretrain_epochs - 1:
            self.pre_epochs.append(epoch)
            self.pre_train_loss.append(train_loss)
            self.pre_val_loss.append(val_loss)
            
            self.train_pre_line.setData(self.pre_epochs, self.pre_train_loss)
            self.val_pre_line.setData(self.pre_epochs, self.pre_val_loss)

        # Fine-tune phase
        if epoch > settings.ai_training.training.pretrain_epochs - 1:
            self.ft_epochs.append(epoch)
            self.ft_train_loss.append(train_loss)
            self.ft_val_loss.append(val_loss)
            
            self.train_ft_line.setData(self.ft_epochs, self.ft_train_loss)
            self.val_ft_line.setData(self.ft_epochs, self.ft_val_loss)

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
optim = torch.optim.Adam(denoiser.parameters(), lr=1e-5)
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
