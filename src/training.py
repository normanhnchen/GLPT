import torch
from torch.utils.data import Dataset, DataLoader
import imageio.v3 as iio
from pathlib import Path


def exr_to_tensor(exr_path, keep_channels=None):
    # Copy the original as it is not writable (PyTorch requirement)
    img_arr = iio.imread(exr_path).copy()

    # Create 1d array from the texture data
    t = torch.from_numpy(img_arr)
    # Reshape from EXR to 3d tensor PyTorch convention (C, H, W)
    t = t.permute(2, 0, 1).contiguous()
    
    if keep_channels is not None:
        t = t[:keep_channels]

    return t


class DenoiseDataset(Dataset):
    def __init__(self, renders_path):
        self.combined_path = renders_path / "combined/"
        self.albedo_path = renders_path / "albedo/"
        self.normal_path = renders_path / "normal/"
        self.depth_path = renders_path / "depth/"
        self.target_path = renders_path / "target/"

        self.num_samples = sum(1 for item in self.combined_path.iterdir() if item.is_file())

    def __len__(self):
        return self.num_samples
    
    def __getitem__(self, idx):
        combined = exr_to_tensor(self.combined_path / f"combined_{idx}.exr", keep_channels=3)
        albedo = exr_to_tensor(self.albedo_path / f"albedo_{idx}.exr", keep_channels=3)
        normal = exr_to_tensor(self.normal_path / f"normal_{idx}.exr", keep_channels=3)
        depth = exr_to_tensor(self.depth_path / f"depth_{idx}.exr", keep_channels=1)
        target = exr_to_tensor(self.target_path / f"target_{idx}.exr", keep_channels=3)

        x = torch.cat([combined, albedo, normal, depth])

        return x, target
