import numpy as np
from pathlib import Path
import json
import random
import cv2
import os
import time

from src.dtypes import *
from src.settings import *


# Required as OpenCV disables EXR support by default
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"


class FramebufferState:
    def __init__(self, ctx):
        self.ctx = ctx
        
        self._create_active_buffers()
        self._clear_active_buffers()

        self.saved_combined = None
        self.saved_albedo = None
        self.saved_normal = None
        self.saved_depth = None

    def _create_active_buffers(self):
        self.combined = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.albedo = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.normal = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.depth = self.ctx.texture(screen.resolution, 4, dtype=f4)
    
    def _create_saved_buffers(self):
        self.saved_combined = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.saved_albedo = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.saved_normal = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.saved_depth = self.ctx.texture(screen.resolution, 4, dtype=f4)

    def _clear_active_buffers(self):
        zeros = np.zeros((*screen.resolution, 4), dtype=f4)
        self.combined.write(zeros)
        self.albedo.write(zeros)
        self.normal.write(zeros)
        self.depth.write(zeros)

    def _release_active_buffers(self):
        if self.saved_combined is not None:
            self.saved_combined.release()
        if self.saved_albedo is not None:
            self.saved_albedo.release()
        if self.saved_normal is not None:
            self.saved_normal.release()
        if self.saved_depth is not None:
            self.saved_depth.release()

    def _release_saved_buffers(self):
        if self.combined is not None:
            self.combined.release()
        if self.albedo is not None:
            self.albedo.release()
        if self.normal is not None:
            self.normal.release()
        if self.depth is not None:
            self.depth.release()
    
    def reset(self):
        self._release_active_buffers()
        self._create_active_buffers()
        self._clear_active_buffers()

    def save(self):
        self._release_saved_buffers()
        self._create_saved_buffers()

        self.saved_combined.write(self.combined.read())
        self.saved_albedo.write(self.albedo.read())
        self.saved_normal.write(self.normal.read())
        self.saved_depth.write(self.depth.read())

    def bind_to_images(self, combined_loc=0, albedo_loc=1, normal_loc=2, depth_loc=3):
        self.combined.bind_to_image(combined_loc, read=True, write=True)
        self.albedo.bind_to_image(albedo_loc, read=True, write=True)
        self.normal.bind_to_image(normal_loc, read=True, write=True)
        self.depth.bind_to_image(depth_loc, read=True, write=True)

    def _get_ndarray(self, buffer):
        data = buffer.read()
        w, h = buffer.size
        c = buffer.components

        # Convert to numpy array
        IsADirectoryError = np.frombuffer(data, dtype=f4)
        # Reshape to OpenGL convention (H, W, C)
        IsADirectoryError = IsADirectoryError.reshape(h, w, c)

        return IsADirectoryError

    def get_ndarray_combined(self):
        return self._get_ndarray(self.combined)

    def get_ndarray_albedo(self):
        return self._get_ndarray(self.albedo)

    def get_ndarray_normal(self):
        return self._get_ndarray(self.normal)

    def get_ndarray_depth(self):
        return self._get_ndarray(self.depth)


class RenderState:
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
        self.should_view_saved = False
        self.should_render = False
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
        self.should_view_saved = False
        self.should_render = False
        # "off", "albedo", "normal", "depth"
        self.debug_mode = "off"

    def complete(self):
        self.render_complete = True
        self.should_view_saved = True


class DenoiseState:
    def __init__(self, ctx):
        self.ctx = ctx
        self.saved_denoised = None
        self.should_denoise = False

    def _release_buffer(self):
        if self.saved_denoised is not None:
            self.saved_denoised.release()

    def denoise(self, ai_denoiser, combined, albedo, normal, depth):
        if self.saved_denoised is None:
            self.saved_denoised = self.ctx.texture(screen.resolution, 3, dtype=f4)
            ai_denoiser.denoise(combined, albedo, normal, depth, self.saved_denoised)

    def reset(self):
        self._release_buffer()
        self.saved_denoised = None


class PTState:
    def __init__(self, ctx):
        self.ctx = ctx
        self.framebuffers = FramebufferState(ctx)
        self.tiles = RenderState()
        self.rendering = RenderProgressState()
        self.denoising = DenoiseState(ctx)
    
    def reset(self):
        self.framebuffers.reset()
        self.tiles.reset()
        self.rendering.reset()
        self.denoising.reset()

    def start_render(self):
        self.reset()
        self.rendering.start()

    def restart_render(self):
        self.reset()
        self.rendering.start()

    def stop_render(self):
        self.rendering.stop_render()

    def continue_render(self):
        self.rendering.continue_render()

    def cancel_render(self):
        self.rendering.reset()

    def advance_render(self):
        self.tiles.advance()
        if not self.tiles.frame_finished:
            return

        samples_left = pt_settings.max_samples - self.rendering.total_samples
        if samples_left < pt_settings.spp:
            self.rendering.total_samples += samples_left
        else:
            self.rendering.total_samples += pt_settings.spp

        if self.rendering.total_samples >= pt_settings.max_samples:
            self.framebuffers.save()
            self.rendering.complete()

    def denoise(self, ai_denoiser):
        self.denoising.denoise(
            ai_denoiser,
            self.framebuffers.saved_combined,
            self.framebuffers.saved_albedo,
            self.framebuffers.saved_normal,
            self.framebuffers.saved_depth,
        )


class RasterState:
    def __init__(self, ctx):
        self.ctx = ctx

        self._create_active_buffers()

    def _create_active_buffers(self):
        self.raster_color_tex = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.raster_depth_texture = self.ctx.depth_texture(screen.resolution)
        self.raster_fbo = self.ctx.framebuffer(
            color_attachments=[self.raster_color_tex],
            depth_attachment=self.raster_depth_texture
        )
    
    def _release_active_buffers(self):
        self.raster_color_tex.release()
        self.raster_depth_texture.release()
        self.raster_fbo.release()
    
    def resize(self):
        self._release_active_buffers()
        self._create_active_buffers()


class ExportState:
    def __init__(self, pt_state):
        self.pt_state = pt_state
        self.noisy = None
        self.target = None
    
    def auto_save_training_renders(self):
        total_samples = self.pt_state.rendering.total_samples

        if self.noisy is None and total_samples >= 8:
            self.noisy = {
                "combined": self.pt_state.framebuffers.get_ndarray_combined(),
                "albedo": self.pt_state.framebuffers.get_ndarray_albedo(),
                "normal": self.pt_state.framebuffers.get_ndarray_normal(),
                "depth": self.pt_state.framebuffers.get_ndarray_depth(),
            }
        
        if self.noisy is not None and total_samples >= pt_settings.max_samples:
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
        
    def export_render(self):
        combined_array = self.pt_state.framebuffers.get_ndarray_combined()
        
        # Flip image vertically
        # OpenGL is bottom-up, EXR is top-down
        combined_array = np.flipud(combined_array)
        
        renders_dir = Path(file_paths.ai_training_renders)
        combined_path = self._get_next_exr_path(renders_dir / "combined", "combined")

        # Save to .exr file
        self._export_exr(combined_path, combined_array)
    
    def _export_training_noisy(self, noisy):
        combined_array = noisy["combined"]
        albedo_array = noisy["albedo"]
        normal_array = noisy["normal"]
        depth_array = noisy["depth"]
        
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
    
    def _export_training_target(self, target):
        target_array = target
        
        # Flip image vertically
        # OpenGL is bottom-up, EXR is top-down
        target_array = np.flipud(target_array)
        
        renders_dir = Path(file_paths.ai_training_renders)
        target_path = self._get_next_exr_path(renders_dir / "target", "target")

        # Save to .exr file
        self._export_exr(target_path, target_array)
    
    def _export_exr(self, export_path, img_arr):
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


class FrameStatsState:
    def __init__(self):
        self.last_frame_start = 0
        self.avg_fps = 0
        self.stats_frame_count = 0
        self.stats_start_time = None
        self.frame_start = None
        self.delta_time = None

    def start_tracking(self):
        self.stats_start_time = time.perf_counter()
        self.last_frame_start = time.perf_counter()

    def track(self):
        self.frame_start = time.perf_counter()
        self.delta_time = self.frame_start - self.last_frame_start
        self.last_frame_start = self.frame_start

        stats_elapsed_time = time.perf_counter() - self.stats_start_time

        # Log stats every 0.5 seconds
        if stats_elapsed_time >= 0.5:
            # Calculate average FPS over the 0.5 second window
            self.avg_fps = self.stats_frame_count / stats_elapsed_time

            # Reset stats counters
            self.stats_start_time = time.perf_counter()
            self.stats_frame_count = 0

    def increment_frame_count(self):
        self.stats_frame_count += 1
