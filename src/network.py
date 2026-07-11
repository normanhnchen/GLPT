import torch
import torch.nn as nn
import numpy as np
from src.dtypes import *


class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()

        # 3x3 convolutions
        # Padding of 1 to keep the output the same size
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        # inplace=true to overwrite tensor; optimization
        self.relu1 = nn.ReLU(inplace=True)
        self.relu2 = nn.ReLU(inplace=True)

        self.net = nn.Sequential(
            self.conv1,
            self.relu1,
            self.conv2,
            self.relu2
        )
    
    def forward(self, x):
        return self.net(x)


class EncoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()

        # kernel_size=2 and stride=2 to downsample by 2 times
        self.down = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv = ConvBlock(in_channels, out_channels)
    
    def forward(self, x):
        return self.conv(self.down(x))


class DecoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()

        # kernel_size=2 and stride=2 to upsample by 2 times
        self.up = nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2)
        self.conv = ConvBlock(in_channels, out_channels)
    
    def forward(self, x, skip_connection):
        x = self.up(x)

        # Apply padding if needed to prevent shape mismatches
        # when concatenating with the skip connection
        delta_height = skip_connection.shape[2] - x.shape[2]
        delta_width = skip_connection.shape[3] - x.shape[3]
        if delta_height != 0 or delta_width != 0:
            pad = nn.ReplicationPad2d([
                delta_width // 2, # Left
                delta_width - delta_width // 2, # Right
                delta_height // 2, # Top
                delta_height - delta_height // 2 # Bottom
            ])
            x = pad(x)
        
        # Concatenate UNet skip connection
        x = torch.cat([x, skip_connection], dim=1)
        return self.conv(x)


class UNet(nn.Module):
    def __init__(self, in_channels=10, out_channels=3):
        super().__init__()

        self.conv_in = ConvBlock(in_channels, 64)

        # Encoder
        # -------
        self.e1 = EncoderBlock(64, 128)
        self.e2 = EncoderBlock(128, 256)
        self.e3 = EncoderBlock(256, 512)
        self.e4 = EncoderBlock(512, 1024)

        # Decoder
        self.d1 = DecoderBlock(1024, 512)
        self.d2 = DecoderBlock(512, 256)
        self.d3 = DecoderBlock(256, 128)
        self.d4 = DecoderBlock(128, 64)

        # kernel_size=1 to reduce the 64 feature channels without reducing the image size
        self.conv_out = nn.Conv2d(64, out_channels, kernel_size=1)
    
    def forward(self, combined, albedo, normal, depth):
        # Convert from OpenGL textures to torch tensors
        combined = self.tex_to_tensor(combined, keep_channels=3) # RGBA -> RGB
        albedo = self.tex_to_tensor(albedo, keep_channels=3) # RGBA -> RGB
        normal = self.tex_to_tensor(normal, keep_channels=3) # RGBA -> RGB
        depth = self.tex_to_tensor(depth, keep_channels=1) # RGBA -> R

        # 10 channels
        x = torch.cat([combined, albedo, normal, depth], dim=1)

        x0 = self.conv_in(x)
        x1 = self.e1(x0)
        x2 = self.e2(x1)
        x3 = self.e3(x2)
        x4 = self.e4(x3)

        x5 = self.d1(x4, x3)
        x6 = self.d2(x5, x2)
        x7 = self.d3(x6, x1)
        x8 = self.d4(x7, x0)

        return self.conv_out(x8)

    def denoise(self, combined, albedo, normal, depth, denoised):
        with torch.no_grad():
            self.eval()
            output = self.forward(combined, albedo, normal, depth)
            return self.tensor_to_tex(output, denoised)

    def tex_to_tensor(self, tex, keep_channels=None):
        # bytearray() to copy the original as it is not writable (PyTorch requirement)
        data = bytearray(tex.read())
        width, height = tex.size
        channels = tex.components
        
        # Create 1d array from the texture data
        t = torch.frombuffer(data, dtype=torch.float32)
        # Reshape to OpenGL convention (H, W, C)
        t = t.reshape(height, width, channels)
        # Reshape to 3d tensor PyTorch convention (C, H, W)
        t = t.permute(2, 0, 1).contiguous()
        
        if keep_channels is not None:
            t = t[:keep_channels]
        
        # Add batch dimension (C, H, W) -> (B, C, H, W) with B = 1
        t = t.unsqueeze(0)

        return t
    
    def tensor_to_tex(self, tensor, denoised_tex):
        # Reshape to OpenGL texture data (H, W, C)
        t = tensor.squeeze(0) # Remove batch dimension
        
        t = t.permute(1, 2, 0).contiguous()
        
        data = t.numpy().tobytes()
        denoised_tex.write(data)
    
    def img_arr_to_tensor(self, img_arr, keep_channels=None):
        channels = img_arr.components
        
        # Create 1d array from the texture data
        t = torch.from_numpy(img_arr)
        # Reshape to 3d tensor PyTorch convention (C, H, W)
        t = t.permute(2, 0, 1).contiguous()
        
        if keep_channels is not None:
            t = t[:keep_channels]
        
        # Add batch dimension (C, H, W) -> (B, C, H, W) with B = 1
        t = t.unsqueeze(0)

        return t
