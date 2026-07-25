import torch
import torch.nn as nn
from src.dtypes import *


# https://dl.acm.org/doi/10.1145/3072959.3073708


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
    
    def forward(self, x):
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


# Kernel Predicting Convolution Network
class KPCN(nn.Module):
    def __init__(self, in_channels=10, kernel_size=21):
        super().__init__()

        self.kernel_size = kernel_size
        self.unet = UNet(in_channels=in_channels, out_channels=kernel_size**2)
    
    def _pad_to_multiple(self, x, multiple=16):
        """
        Pads tensors on the right and bottom sides to a multiple to prevent
        size mismatches when concatenating skip connections.
        """

        _, _, h, w = x.shape

        pad_h = (multiple - (h % multiple)) % multiple
        pad_w = (multiple - (w % multiple)) % multiple

        if pad_h == 0 and pad_w == 0:
            return x
    
        pad = nn.ReflectionPad2d([
            0, # Left
            pad_w, # Right
            0, # Top
            pad_h, # Bottom
        ])
        
        return pad(x)
    
    def forward(self, x, combined):
        # Original spatial dimensions
        _, _, h, w = x.shape

        x = self._pad_to_multiple(x)
        combined = self._pad_to_multiple(combined)

        # (B, K*K, H, W)
        weights = self.unet(x)
        # Normalize
        weights = torch.softmax(weights, dim=1)
        combined = self._apply_kernel(weights, combined)

        return combined[:, :, :h, :w]
    
    def _apply_kernel(self, weights, combined):
        B, _, H, W = weights.shape
        K = self.kernel_size
        pad_size = K // 2

        # Pad for the kernel neighborhood around the edge pixels
        pad = nn.ReflectionPad2d([pad_size, pad_size, pad_size, pad_size])
        # (B, 3, H, W) -> # (B, 3, H+2*pad, W+2*pad)
        padded = pad(combined)
        
        # (B, 3, H+2*pad, W+2*pad) -> (B, 3*K*K, H*W)
        patches = nn.functional.unfold(padded, K)
        # (B, 3*K*K, H*W) -> (B, 3, K*K, H, W)
        patches = patches.view(B, 3, K * K, H, W)

        # Add batch dimension at index 1
        # (B, K*K, H, W) -> (B, 1, K*K, H, W)
        w = weights.unsqueeze(1)

        # Apply weights to the combined image RGB channels
        return (patches * w).sum(dim=2) # (B, 3, H, W)

    def denoise(self, combined, albedo, normal, depth, denoised):
        with torch.no_grad():
            self.eval()
            # Convert from OpenGL textures to torch tensors
            combined = self._tex_to_tensor(combined, keep_channels=3) # RGBA -> RGB
            albedo = self._tex_to_tensor(albedo, keep_channels=3) # RGBA -> RGB
            normal = self._tex_to_tensor(normal, keep_channels=3) # RGBA -> RGB
            depth = self._tex_to_tensor(depth, keep_channels=1) # RGBA -> R
            # 10 channels
            x = torch.cat([combined, albedo, normal, depth], dim=1)

            output = self(x, combined)
            return self._tensor_to_tex(output, denoised)
    
    def _tex_to_tensor(self, tex, keep_channels=None):
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
        
        # Add batch dimension at index 0 (C, H, W) -> (1, C, H, W)
        t = t.unsqueeze(0)

        return t
    
    def _tensor_to_tex(self, tensor, denoised_tex):
        # Reshape to OpenGL texture data (H, W, C)
        t = tensor.squeeze(0) # Remove batch dimension
        
        t = t.permute(1, 2, 0).contiguous()
        
        data = t.numpy().tobytes()
        denoised_tex.write(data)
