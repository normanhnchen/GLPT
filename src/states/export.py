import os
import numpy as np
from pathlib import Path
import cv2

from src.settings import settings


# Required as OpenCV disables EXR support by default
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"


# See 9.4 Rendering
class ExportState:
    def __init__(self, pt_state, final_output_state):
        self.pt_state = pt_state
        self.final_output_state = final_output_state
        self.noisy = None
        self.target = None
    
    def auto_save_training_renders(self):
        total_samples = self.pt_state.rendering.total_samples

        if self.noisy is None and total_samples >= settings.ai_training.rendering.noisy_samples:
            self.noisy = {
                "combined": self.pt_state.framebuffers.get_ndarray_combined(),
                "albedo": self.pt_state.framebuffers.get_ndarray_albedo(),
                "normal": self.pt_state.framebuffers.get_ndarray_normal(),
                "depth": self.pt_state.framebuffers.get_ndarray_depth()
            }
        
        if self.noisy is not None and total_samples >= settings.path_tracing.max_samples:
            self.target = self.pt_state.framebuffers.get_ndarray_combined()
        
        if self.noisy is not None and self.target is not None:
            self._export_training_noisy(self.noisy)
            self._export_training_target(self.target)

            self.noisy = None
            self.target = None

    def _get_next_exr_path(self, path, prefix):
        counter = 0
        while True:
            file_path = path / f"{prefix}_{counter}.exr"
            if not file_path.exists():
                return file_path
            counter += 1

    def _get_next_png_path(self, path, prefix):
        counter = 0
        while True:
            file_path = path / f"{prefix}_{counter}.png"
            if not file_path.exists():
                return file_path
            counter += 1
        
    def export_render(self):
        # Drop alpha channel
        img_arr = self.final_output_state.get_ndarray()[:, :, :3]
        
        # Flip image vertically
        # OpenGL is bottom-up, image is top-down
        img_arr = np.flipud(img_arr)
        
        renders_dir = Path(settings.file_paths.renders)
        export_path = self._get_next_png_path(renders_dir, "render")

        # Save to .png file
        self._export_png(export_path, img_arr)
    
    def _export_training_noisy(self, noisy):
        combined_array = noisy["combined"]
        albedo_array = noisy["albedo"]
        normal_array = noisy["normal"]
        depth_array = noisy["depth"]
        direct_emissive_array = noisy["direct_emissive"]
        
        # Flip image vertically
        # OpenGL is bottom-up, EXR is top-down
        combined_array = np.flipud(combined_array)
        albedo_array = np.flipud(albedo_array)
        normal_array = np.flipud(normal_array)
        depth_array = np.flipud(depth_array)
        direct_emissive_array = np.flipud(direct_emissive_array)
        
        combined_dir = Path(settings.file_paths.ai_training.combined_renders)
        albedo_dir = Path(settings.file_paths.ai_training.albedo_renders)
        normal_dir = Path(settings.file_paths.ai_training.normal_renders)
        depth_dir = Path(settings.file_paths.ai_training.depth_renders)
        direct_emissive_dir = Path(settings.file_paths.ai_training.direct_emissive_renders)

        combined_path = self._get_next_exr_path(combined_dir, "combined")
        albedo_path = self._get_next_exr_path(albedo_dir, "albedo")
        normal_path = self._get_next_exr_path(normal_dir, "normal")
        depth_path = self._get_next_exr_path(depth_dir, "depth")
        direct_emissive_path = self._get_next_exr_path(direct_emissive_dir, "direct_emissive")

        # Save to .exr files
        self._export_exr(combined_path, combined_array)
        self._export_exr(albedo_path, albedo_array)
        self._export_exr(normal_path, normal_array)
        self._export_exr(depth_path, depth_array)
        self._export_exr(direct_emissive_path, direct_emissive_array)
    
    def _export_training_target(self, target):
        target_array = target
        
        # Flip image vertically
        # OpenGL is bottom-up, EXR is top-down
        target_array = np.flipud(target_array)
        
        targets_dir = Path(settings.file_paths.ai_training.target_renders)
        target_path = self._get_next_exr_path(targets_dir, "target")

        # Save to .exr file
        self._export_exr(target_path, target_array)
    
    def _export_exr(self, export_path, img_arr):
        # Convert image to BGR as OpenCV expects BGR order
        img = cv2.cvtColor(img_arr.astype(np.float32), cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(export_path), img)

    def _export_png(self, export_path, img_arr):
            # Convert to expected uint8 range (0-255)
            img_arr = np.clip(img_arr, 0.0, 1.0)
            img_arr = (img_arr * 255).astype(np.uint8)

            # Convert image to BGR as OpenCV expects BGR order
            img = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(export_path), img)

