import numpy as np
from pathlib import Path
import json
import random
import cv2
import os

from src.dtypes import *
from src.settings import *


# Required as OpenCV disables EXR support by default
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"


class FramebufferState:
    def __init__(self, ctx):
        self.ctx = ctx
        
        self.combined_pass = ctx.texture(screen.resolution, 4, dtype=f4)
        self.albedo_pass = ctx.texture(screen.resolution, 4, dtype=f4)
        self.normal_pass = ctx.texture(screen.resolution, 4, dtype=f4)
        self.depth_pass = ctx.texture(screen.resolution, 4, dtype=f4)

        self._clear_active_buffers()

        self.saved_combined = None
        self.saved_albedo = None
        self.saved_normal = None
        self.saved_depth = None

    def _clear_active_buffers(self):
        zeros = np.zeros((*screen.resolution, 4), dtype=f4)
        self.combined_pass.write(zeros)
        self.albedo_pass.write(zeros)
        self.normal_pass.write(zeros)
        self.depth_pass.write(zeros)

    def _release_saved_buffers(self):
        if self.saved_combined is not None:
            self.saved_combined.release()
        if self.saved_albedo is not None:
            self.saved_albedo.release()
        if self.saved_normal is not None:
            self.saved_normal.release()
        if self.saved_depth is not None:
            self.saved_depth.release()
    
    def reset(self):
        self.combined_pass = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.albedo_pass = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.normal_pass = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.depth_pass = self.ctx.texture(screen.resolution, 4, dtype=f4)

        self._clear_active_buffers()

    def save(self):
        self._release_saved_buffers()
        
        self.saved_combined = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.saved_albedo = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.saved_normal = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.saved_depth = self.ctx.texture(screen.resolution, 4, dtype=f4)

        self.saved_combined.write(self.combined_pass.read())
        self.saved_albedo.write(self.albedo_pass.read())
        self.saved_normal.write(self.normal_pass.read())
        self.saved_depth.write(self.depth_pass.read())


class RenderTilerState:
    def __init__(self):
        # Current tile position in pixels
        self.curr_tile_x = 0
        self.curr_tile_y = 0
        
        # Apply ceiling function
        # Allows the compute shader to reach the entire screen
        self.tile_width = (screen.width + render_settings.tiles_x - 1) // render_settings.tiles_x
        self.tile_height = (screen.height + render_settings.tiles_y - 1) // render_settings.tiles_y

        self.frame_finished = False

    def reset(self):
        # Reset tiling position
        self.curr_tile_x = 0
        self.curr_tile_y = 0

        # Recalculate tile sizes
        self.tile_width = (screen.width + render_settings.tiles_x - 1) // render_settings.tiles_x
        self.tile_height = (screen.height + render_settings.tiles_y - 1) // render_settings.tiles_y

    def advance(self):
        self.curr_tile_x += self.tile_width
        if self.curr_tile_x > screen.width:
            self.curr_tile_x = 0
            self.curr_tile_y += self.tile_height
        
        if self.curr_tile_y > screen.height:
            self.curr_tile_y = 0
            self.frame_finished = True
        else:
            self.frame_finished = False


class RenderProgressState:
    def __init__(self):
        self.total_samples = 0
        self.render_complete = False
        self.view_saved = False
        self.should_render = False
        self.should_denoise = False
        # "off", "albedo", "normal", "depth"
        self.debug_mode = "off"

    def start(self):
        self.should_render = True

    def stop_render(self):
        self.should_render = False

    def continue_render(self):
        self.should_render = True

    def reset(self):
        self.total_samples = 0
        self.render_complete = False
        self.view_saved = False
        self.should_render = False
        self.should_denoise = False
        # "off", "albedo", "normal", "depth"
        self.debug_mode = "off"

    def complete(self):
        self.render_complete = True
        self.view_saved = True


class PTState:
    def __init__(self, ctx):
        self.ctx = ctx
        self.framebuffers = FramebufferState(ctx)
        self.tiles = RenderTilerState()
        self.rendering = RenderProgressState()
    
    def reset(self):
        self.framebuffers.reset()
        self.tiles.reset()
        self.rendering.reset()


class DenoiseState:
    def __init__(self, ctx):
        self.ctx = ctx
        self.saved_denoised = None

    def _release_buffer(self):
        if self.saved_denoised is not None:
            self.saved_denoised.release()

    def denoise(self, ai_denoiser, combined, albedo, normal, depth):
        self.saved_denoised = self.ctx.texture(screen.resolution, 3, dtype=f4)
        ai_denoiser.denoise(combined, albedo, normal, depth, self.denoised)


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
        self.target_saved = False
    
    def auto_save_training_renders(self):
        if self.pt_state.total_samples == 8:
            self.noisy_saved = True
        if self.pt_state.total_samples == pt_settings.max_samples:
            self.target_saved = True
        
        if self.noisy_saved and self.target_saved:
            self._export_training_noisy()
            self._export_training_target()

            self.noisy_saved = False
            self.target_saved = False

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
        self._export_exr(combined_path, combined_array)
    
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
        self._export_exr(combined_path, combined_array)
        self._export_exr(albedo_path, albedo_array)
        self._export_exr(normal_path, normal_array)
        self._export_exr(depth_path, depth_array)
    
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
        self._export_exr(target_path, target_array)
    
    def _export_exr(export_path, img_arr):
        # Convert image to BGR as OpenCV expects BGR order
        img = cv2.cvtColor(img_arr.astype(np.float32), cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(export_path), img)


class SceneState:
    def __init__(self):
        self.scenes_path = Path(file_paths.ai_training_scenes)
        self.scene_files = [scene for scene in self.scenes_path.iterdir()]
        self.num_scenes = len(self.scene_files)
        self.curr_scene_idx = 0
        self.curr_scene_file = self.scene_files[self.curr_scene_idx]

        self.hdris_path = Path(file_paths.ai_training_hdris)
        self.hdri_files = [hdri for hdri in self.hdris_path.iterdir()]
        random.shuffle(self.hdri_files)
        self.num_hdris = len(self.hdri_files)
        self.curr_hdri_idx = 0
        self.curr_hdri_file = self.hdri_files[self.curr_hdri_idx]

        self.changed_scene = False
        self.ai_training_finished = False
    
    def next_scene(self):
        if self.curr_scene_idx < self.num_scenes - 1:
            self.curr_scene_idx += 1
            self.curr_scene_file = self.scene_files[self.curr_scene_idx]
            
            # Wrap back to the first HDRI once we've cycled through all of them
            self.curr_hdri_idx = (self.curr_hdri_idx + 1) % self.num_hdris
            self.curr_hdri_file = self.hdri_files[self.curr_hdri_idx]

            self.changed_scene = True
        
        else:
            self.ai_training_finished = True
    
    def previous_scene(self):
        if self.curr_scene_idx > 0:
            self.curr_scene_idx -= 1
            self.curr_scene_file = self.scene_files[self.curr_scene_idx]

            # Wrap back to the last HDRI if we go below the first one
            self.curr_hdri_idx = (self.curr_hdri_idx - 1) % self.num_hdris
            self.curr_hdri_file = self.hdri_files[self.curr_hdri_idx]

            self.changed_scene = True


class CameraCaptureState:
    def __init__(self, scene_state, camera):
        self.scene_state = scene_state
        self.camera = camera
        self.states = {str(scene_file):{} for scene_file in self.scene_state.scene_files}
        self.curr_state_idx = 0

        self._load_states()
    
    def _load_states(self):
        try:
            with open(file_paths.camera_capture_states) as f:
                self.states = json.load(f)
        except:
            pass

    def save_state(self):
        scene_file = self.scene_state.scene_files[self.scene_state.curr_scene_idx]
        state = self.camera.get_state()
        
        scene_captures = self.states[str(scene_file)]
        num_scene_captures = len(scene_captures)
        scene_captures[str(num_scene_captures)] = state

        with open(file_paths.camera_capture_states, "w") as f:
            json.dump(self.states, f)
    
    def remove_state(self):
        # Remove the last captured state from the current scene

        scene_file = self.scene_state.scene_files[self.scene_state.curr_scene_idx]
        scene_captures = self.states[str(scene_file)]
        scene_captures.popitem()

        with open(file_paths.camera_capture_states, "w") as f:
            json.dump(self.states, f)
    
    def load_next_state(self):
        scene_file = self.scene_state.scene_files[self.scene_state.curr_scene_idx]
        scene_captures = self.states[str(scene_file)]
        num_scene_captures = len(scene_captures)

        if num_scene_captures - self.curr_state_idx:
            self.camera.load_state(scene_captures[str(self.curr_state_idx)])
            self.curr_state_idx += 1
            return
        
        self.scene_state.next_scene()

        if self.scene_state.ai_training_finished:
            return
        
        self.curr_state_idx = 0
        self.load_next_state()
