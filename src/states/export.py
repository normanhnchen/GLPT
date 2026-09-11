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
        self.target_diffuse = None
        self.target_specular = None
    
    def auto_save_training_renders(self):
        total_samples = self.pt_state.rendering.total_samples

        if self.noisy is None and total_samples >= settings.ai_training.rendering.noisy_samples:
            self.noisy = {
                "diffuse": self.pt_state.framebuffers.get_ndarray_diffuse(),
                "specular": self.pt_state.framebuffers.get_ndarray_specular(),
                "albedo": self.pt_state.framebuffers.get_ndarray_albedo(),
                "normal": self.pt_state.framebuffers.get_ndarray_normal(),
                "depth": self.pt_state.framebuffers.get_ndarray_depth()
            }
        
        if self.noisy is not None and total_samples >= settings.path_tracing.max_samples:
            self.target_diffuse = self.pt_state.framebuffers.get_ndarray_diffuse()
            self.target_specular = self.pt_state.framebuffers.get_ndarray_specular()
        
        if self.noisy is not None:
            if self.target_diffuse is not None and self.target_specular is not None:
                self._export_training_noisy(self.noisy)
                self._export_training_target_diffuse(self.target_diffuse)
                self._export_training_target_specular(self.target_specular)

                self.noisy = None
                self.target_diffuse = None
                self.target_specular = None

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
        diffuse_array = noisy["diffuse"]
        specular_array = noisy["specular"]
        albedo_array = noisy["albedo"]
        normal_array = noisy["normal"]
        depth_array = noisy["depth"]
        
        # Flip image vertically
        # OpenGL is bottom-up, EXR is top-down
        diffuse_array = np.flipud(diffuse_array)
        specular_array = np.flipud(specular_array)
        albedo_array = np.flipud(albedo_array)
        normal_array = np.flipud(normal_array)
        depth_array = np.flipud(depth_array)
        
        diffuse_dir = Path(settings.file_paths.ai_training.diffuse_renders)
        specular_dir = Path(settings.file_paths.ai_training.specular_renders)
        albedo_dir = Path(settings.file_paths.ai_training.albedo_renders)
        normal_dir = Path(settings.file_paths.ai_training.normal_renders)
        depth_dir = Path(settings.file_paths.ai_training.depth_renders)

        diffuse_path = self._get_next_exr_path(diffuse_dir, "diffuse")
        specular_path = self._get_next_exr_path(specular_dir, "specular")
        albedo_path = self._get_next_exr_path(albedo_dir, "albedo")
        normal_path = self._get_next_exr_path(normal_dir, "normal")
        depth_path = self._get_next_exr_path(depth_dir, "depth")

        # Save to .exr files
        self._export_exr(diffuse_path, diffuse_array)
        self._export_exr(specular_path, specular_array)
        self._export_exr(albedo_path, albedo_array)
        self._export_exr(normal_path, normal_array)
        self._export_exr(depth_path, depth_array)
    
    def _export_training_target_diffuse(self, target_diffuse):
        target_diffuse_array = target_diffuse
        
        # Flip image vertically
        # OpenGL is bottom-up, EXR is top-down
        target_diffuse_array = np.flipud(target_diffuse_array)
        
        target_diffuse_dir = Path(settings.file_paths.ai_training.target_diffuse_renders)
        target_diffuse_path = self._get_next_exr_path(target_diffuse_dir, "target_diffuse")

        # Save to .exr file
        self._export_exr(target_diffuse_path, target_diffuse_array)

    def _export_training_target_specular(self, target_specular):
        target_specular_array = target_specular
        
        # Flip image vertically
        # OpenGL is bottom-up, EXR is top-down
        target_specular_array = np.flipud(target_specular_array)
        
        target_specular_dir = Path(settings.file_paths.ai_training.target_specular_renders)
        target_specular_path = self._get_next_exr_path(target_specular_dir, "target_specular")

        # Save to .exr file
        self._export_exr(target_specular_path, target_specular_array)
    
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

