import torch
from torch.utils.data import Dataset, DataLoader
import warnings
# Disable warning from imageio of deprecated pkg_resources
warnings.filterwarnings("ignore", module="imageio")
import imageio.v3 as iio
import random

from src.settings import *
from src.network import *


# https://dl.acm.org/doi/10.1145/3072959.3073708


def exr_to_tensor(exr_path, keep_channels=None):
    # Copy the original as it is not writable (PyTorch requirement)
    img_arr = iio.imread(exr_path).copy()

    # Create 1d array from the texture data
    t = torch.from_numpy(img_arr).float()
    # Reshape from EXR to 3d tensor PyTorch convention (C, H, W)
    t = t.permute(2, 0, 1).contiguous()
    
    if keep_channels is not None:
        t = t[:keep_channels]

    return t


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
        combined = exr_to_tensor(self.combined_path / f"combined_{idx}.exr", keep_channels=3)
        albedo = exr_to_tensor(self.albedo_path / f"albedo_{idx}.exr", keep_channels=3)
        normal = exr_to_tensor(self.normal_path / f"normal_{idx}.exr", keep_channels=3)
        depth = exr_to_tensor(self.depth_path / f"depth_{idx}.exr", keep_channels=1)
        target = exr_to_tensor(self.target_path / f"target_{idx}.exr", keep_channels=3)

        x = torch.cat([combined, albedo, normal, depth])

        _, h, w = x.shape

        top = random.randint(0, h - self.patch_size)
        bottom = top + self.patch_size
        left = random.randint(0, w - self.patch_size)
        right = left + self.patch_size

        x = x[:, top:bottom, left:right]
        target = target[:, top:bottom, left:right]

        return x, target


train_dataset = DenoiseDataset(file_paths.ai_training_renders)
train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True)

denoiser = KPCN().to(AI_DEVICE)
optim = torch.optim.Adam(denoiser.parameters(), lr=1e-4)
criterion = nn.L1Loss()

epochs = 100

try:
    checkpoint = torch.load("src/denoiser/checkpoint.pt", map_location=AI_DEVICE)
    denoiser.load_state_dict(checkpoint["model_state_dict"])
    optim.load_state_dict(checkpoint["optimizer_state_dict"])
    starting_epoch = checkpoint["epoch"] + 1
    print(f"Resumed from epoch {starting_epoch}")
except FileNotFoundError:
    starting_epoch = 0

for epoch in range(starting_epoch, epochs):
    avg_loss = 0
    for x, target in train_loader:
        x = x.to(AI_DEVICE)
        combined = x[:, :3].to(AI_DEVICE)
        target = target.to(AI_DEVICE)

        optim.zero_grad()
        prediction = denoiser(x, combined)
        loss = criterion(prediction, target)
        loss.backward()
        optim.step()

        avg_loss += loss.item() / len(train_loader)
    
    checkpoint = {
        "epoch": epoch,
        "model_state_dict": denoiser.state_dict(),
        "optimizer_state_dict": optim.state_dict(),
        "loss": avg_loss
    }

    print(f"Epoch: {epoch} | Loss: {avg_loss}")

    torch.save(checkpoint, "src/denoiser/checkpoint.pt")

