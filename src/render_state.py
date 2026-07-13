import numpy as np
import warnings
# Disable warning from imageio of deprecated pkg_resources
warnings.filterwarnings("ignore", module="imageio")
import imageio.v3 as iio
from pathlib import Path
import json

from src.dtypes import *
from src.settings import *


class PTState:
    def __init__(self, ctx):
        self.ctx = ctx
        self.combined_pass = ctx.texture(screen.resolution, 4, dtype=f4)
        self.albedo_pass = ctx.texture(screen.resolution, 4, dtype=f4)
        self.normal_pass = ctx.texture(screen.resolution, 4, dtype=f4)
        self.depth_pass = ctx.texture(screen.resolution, 4, dtype=f4)
        self.saved_combined = None
        self.saved_albedo = None
        self.saved_normal = None
        self.saved_depth = None
        self.saved_denoised = None

        # Current tile position in pixels
        self.curr_tile_x = 0
        self.curr_tile_y = 0
        # Apply ceiling function
        # Allows the compute shader to reach the entire screen
        self.tile_width = (screen.width + render_settings.tiles_x - 1) // render_settings.tiles_x
        self.tile_height = (screen.height + render_settings.tiles_y - 1) // render_settings.tiles_y

        self.render_complete = False
        self.view_saved = False
        self.should_render = False
        self.should_denoise = False
        self.total_samples = 0
        # "off", "albedo", "normal", "depth"
        self.debug_mode = "off"
    
    def resize(self):
        self.combined_pass.release()
        self.albedo_pass.release()
        self.normal_pass.release()
        self.depth_pass.release()

        self.combined_pass = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.albedo_pass = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.normal_pass = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.depth_pass = self.ctx.texture(screen.resolution, 4, dtype=f4)

        self.combined_pass.write(np.zeros((*screen.resolution, 4), dtype=f4))
        self.albedo_pass.write(np.zeros((*screen.resolution, 4), dtype=f4))
        self.normal_pass.write(np.zeros((*screen.resolution, 4), dtype=f4))
        self.depth_pass.write(np.zeros((*screen.resolution, 4), dtype=f4))

        self.total_samples = 0
        self.render_complete = False

        # Reset tiling
        self.curr_tile_x = 0
        self.curr_tile_y = 0

        # Recalculate tile sizes
        self.tile_width = (screen.width + render_settings.tiles_x - 1) // render_settings.tiles_x
        self.tile_height = (screen.height + render_settings.tiles_y - 1) // render_settings.tiles_y
    
    def start_render(self, camera_buffer):
        render_settings.render_mode = "path_tracing"

        camera_buffer.update_data()

        self.total_samples = 0
        self.should_render = True
        self.render_complete = False
        
        # Reset tiling
        self.curr_tile_x = 0
        self.curr_tile_y = 0

        # Reset accumulation buffers
        self.combined_pass.write(np.zeros((*screen.resolution, 4), dtype=f4))
        self.albedo_pass.write(np.zeros((*screen.resolution, 4), dtype=f4))
        self.normal_pass.write(np.zeros((*screen.resolution, 4), dtype=f4))
        self.depth_pass.write(np.zeros((*screen.resolution, 4), dtype=f4))
    
    def save_render(self):
        if self.saved_combined is not None:
            self.saved_combined.release()
        if self.saved_albedo is not None:
            self.saved_albedo.release()
        if self.saved_normal is not None:
            self.saved_normal.release()
        if self.saved_depth is not None:
            self.saved_depth.release()
        
        self.saved_combined = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.saved_albedo = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.saved_normal = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.saved_depth = self.ctx.texture(screen.resolution, 4, dtype=f4)

        self.saved_combined.write(self.combined_pass.read())
        self.saved_albedo.write(self.albedo_pass.read())
        self.saved_normal.write(self.normal_pass.read())
        self.saved_depth.write(self.depth_pass.read())

        self.render_complete = True
        self.view_saved = True
    
    def denoise(self, ai_denoiser):
        if self.saved_denoised is None:
            self.saved_denoised = self.ctx.texture(screen.resolution, 3, dtype=f4)
            ai_denoiser.denoise(self.saved_combined, self.saved_albedo, self.saved_normal, self.saved_depth, self.saved_denoised)
    
    def restart_render(self):
        self.total_samples = 0
        self.render_complete = False
        self.view_saved = False
        self.should_denoise = False
        self.should_render = True
        self.debug_mode = "off"

        # Reset tiling
        self.curr_tile_x = 0
        self.curr_tile_y = 0
        # Apply ceiling function
        # Allows the compute shader to reach the entire screen
        self.tile_width = (screen.width + render_settings.tiles_x - 1) // render_settings.tiles_x
        self.tile_height = (screen.height + render_settings.tiles_y - 1) // render_settings.tiles_y
        
        # Reset accumulation buffers
        self.combined_pass.write(np.zeros((*screen.resolution, 4), dtype=f4))
        self.albedo_pass.write(np.zeros((*screen.resolution, 4), dtype=f4))
        self.normal_pass.write(np.zeros((*screen.resolution, 4), dtype=f4))
        self.depth_pass.write(np.zeros((*screen.resolution, 4), dtype=f4))


class RasterState:
    def __init__(self, ctx):
        self.ctx = ctx
        self.raster_color_tex = ctx.texture(screen.resolution, 4, dtype=f4)
        self.raster_depth_texture = ctx.depth_texture(screen.resolution)
        self.raster_fbo = ctx.framebuffer(
            color_attachments=[self.raster_color_tex],
            depth_attachment=self.raster_depth_texture
        )
    
    def resize(self):
        self.raster_color_tex.release()
        self.raster_depth_texture.release()
        self.raster_fbo.release()

        self.raster_color_tex = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.raster_depth_texture = self.ctx.depth_texture(screen.resolution)
        self.raster_fbo = self.ctx.framebuffer(
            color_attachments=[self.raster_color_tex],
            depth_attachment=self.raster_depth_texture
        )


class PostProcessState:
    def __init__(self):
        self.tonemap = post_process_settings.tonemap
        self.dof_enabled = False
        self.aperture = 0
        self.focus_dist = 10


class ExportState:
    def __init__(self, pt_state):
        self.pt_state = pt_state
        self.noisy_saved = False
        self.target_saved = True
    
    def auto_save_training_renders(self):
        if self.pt_state.total_samples == 32:
            self.noisy_saved = True
        if self.pt_state.total_samples == 4096:
            self.target_saved = True
        
        if self.noisy_saved and self.target_saved:
            self._export_training_noisy()
            self._export_training_target()

    def _get_next_exr_path(self, path, prefix):
        counter = 0
        while True:
            file_path = path / f"{prefix}_{counter}.exr"
            if not file_path.exists():
                return file_path
            counter += 1
        
    def export_render(self):
        combined_data = self.pt_state.combined_pass.read()
        combined_width, combined_height = self.pt_state.combined_pass.size
        combined_channels = self.pt_state.combined_pass.components

        # Convert to numpy array
        combined_array = np.frombuffer(combined_data, dtype=f4)

        # Reshape to OpenGL convention (H, W, C)
        combined_array = combined_array.reshape(combined_height, combined_width, combined_channels)
        
        # Flip image vertically
        # OpenGL is bottom-up, EXR is top-down
        combined_array = np.flipud(combined_array)
        
        renders_dir = Path(file_paths.ai_training_renders)
        combined_path = self._get_next_exr_path(renders_dir / "combined", "combined")

        # Save to .exr file
        iio.imwrite(combined_path, combined_array)
    
    def _export_training_noisy(self):
        combined_data = self.pt_state.combined_pass.read()
        combined_width, combined_height = self.pt_state.combined_pass.size
        combined_channels = self.pt_state.combined_pass.components

        albedo_data = self.pt_state.albedo_pass.read()
        albedo_width, albedo_height = self.pt_state.albedo_pass.size
        albedo_channels = self.pt_state.albedo_pass.components
        
        normal_data = self.pt_state.normal_pass.read()
        normal_width, normal_height = self.pt_state.normal_pass.size
        normal_channels = self.pt_state.normal_pass.components

        depth_data = self.pt_state.depth_pass.read()
        depth_width, depth_height = self.pt_state.depth_pass.size
        depth_channels = self.pt_state.depth_pass.components

        # Convert to numpy arrays
        combined_array = np.frombuffer(combined_data, dtype=f4)
        albedo_array = np.frombuffer(albedo_data, dtype = f4)
        normal_array = np.frombuffer(normal_data, dtype = f4)
        depth_array = np.frombuffer(depth_data, dtype = f4)

        # Reshape to OpenGL convention (H, W, C)
        combined_array = combined_array.reshape(combined_height, combined_width, combined_channels)
        albedo_array = albedo_array.reshape(albedo_height, albedo_width, albedo_channels)
        normal_array = normal_array.reshape(normal_height, normal_width, normal_channels)
        depth_array = depth_array.reshape(depth_height, depth_width, depth_channels)
        
        # Flip image vertically
        # OpenGL is bottom-up, EXR is top-down
        combined_array = np.flipud(combined_array)
        albedo_array = np.flipud(albedo_array)
        normal_array = np.flipud(normal_array)
        depth_array = np.flipud(depth_array)
        
        renders_dir = Path(file_paths.ai_training_renders)
        combined_path = self._get_next_exr_path(renders_dir / "combined", "combined")
        albedo_path = self._get_next_exr_path(renders_dir / "albedo", "albedo")
        normal_path = self._get_next_exr_path(renders_dir / "normal", "normal")
        depth_path = self._get_next_exr_path(renders_dir / "depth", "depth")

        # Save to .exr files
        iio.imwrite(combined_path, combined_array)
        iio.imwrite(albedo_path, albedo_array)
        iio.imwrite(normal_path, normal_array)
        iio.imwrite(depth_path, depth_array)
    
    def _export_training_target(self):
        target_data = self.pt_state.combined_pass.read()
        target_width, target_height = self.pt_state.combined_pass.size
        target_channels = self.pt_state.combined_pass.components

        # Convert to numpy array
        target_array = np.frombuffer(target_data, dtype=f4)

        # Reshape to OpenGL convention (H, W, C)
        target_array = target_array.reshape(target_height, target_width, target_channels)
        
        # Flip image vertically
        # OpenGL is bottom-up, EXR is top-down
        target_array = np.flipud(target_array)
        
        renders_dir = Path(file_paths.ai_training_renders)
        target_path = self._get_next_exr_path(renders_dir / "target", "target")

        # Save to .exr file
        iio.imwrite(target_path, target_array)
    

class CameraCaptureState:
    def __init__(self, camera):
        self.camera = camera
        self.scenes_path = Path(file_paths.ai_training_scenes)
        self.scene_files = [scene for scene in self.scenes_path.iterdir()]

        self.curr_scene_idx = 0

        self.camera_capture_states = {scene_file:{} for scene_file in self.scene_files}

    def save_state(self, scene_file):
        state = self.camera.get_state()
        
        scene_captures = self.camera_capture_states[str(scene_file)]
        scene_capture_count = len(scene_captures)
        scene_captures[scene_capture_count] = state

        with open(file_paths.camera_capture_states, "w") as file:
            json.dump(self.camera_capture_states, file)
