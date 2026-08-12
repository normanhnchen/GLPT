import numpy as np
from pathlib import Path
import json
import random
import cv2
import os
import time
from glfw.GLFW import *
import sys
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

from src.dtypes import *
from src.settings import *
from src.camera import *
from src.bvh_builder import *
from src.buffer_loading import *


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

    def _release_saved_buffers(self):
        if self.saved_combined is not None:
            self.saved_combined.release()
        if self.saved_albedo is not None:
            self.saved_albedo.release()
        if self.saved_normal is not None:
            self.saved_normal.release()
        if self.saved_depth is not None:
            self.saved_depth.release()

    def _release_active_buffers(self):
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
        arr = np.frombuffer(data, dtype=f4)
        # Reshape to OpenGL convention (H, W, C)
        arr = arr.reshape(h, w, c)

        return arr

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

    def complete(self):
        self.render_complete = True
        self.should_view_saved = True


class DebugState:
    def __init__(self):
        # combined: 0, albedo: 1, normal: 2, depth: 3, direct: 4, indirect: 5
        self.mode = 0

    def reset(self):
        self.mode = 0


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
        self.debug = DebugState()
    
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


class FinalOutputState:
    def __init__(self, ctx):
        self.ctx = ctx

        self._create_active_buffers()

    def _create_active_buffers(self):
        self.output_tex = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.output_fbo = self.ctx.framebuffer(
            color_attachments=[self.output_tex]
        )
    
    def _release_active_buffers(self):
        self.output_tex.release()
        self.output_fbo.release()
    
    def resize(self):
        self._release_active_buffers()
        self._create_active_buffers()

    def get_ndarray(self):
        data = self.output_tex.read()
        w, h = self.output_tex.size
        c = self.output_tex.components

        # Convert to numpy array
        arr = np.frombuffer(data, dtype=f4)
        # Reshape to OpenGL convention (H, W, C)
        arr = arr.reshape(h, w, c)

        return arr


class ExportState:
    def __init__(self, pt_state, final_output_state):
        self.pt_state = pt_state
        self.final_output_state = final_output_state
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
        
        renders_dir = Path(file_paths.renders)
        export_path = self._get_next_png_path(renders_dir, "render")

        # Save to .png file
        self._export_png(export_path, img_arr)
    
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

    def _export_png(self, export_path, img_arr):
            # Convert to expected uint8 range (0-255)
            img_arr = np.clip(img_arr, 0.0, 1.0)
            img_arr = (img_arr * 255).astype(np.uint8)

            # Convert image to BGR as OpenCV expects BGR order
            img = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
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


class BVHState:
    def __init__(self, ctx, scene):
        self.ctx = ctx
        self.scene = scene

        self.ready = False
        self.built = False
        self.builder = None

    def background_build(self):
        self.builder = BVHBackgroundBuilder(self.scene)
        self.bvh_built = False

    def build(self):
        self.scene.build_bvh()
        self.bvh_built = True

    def update(self, bvh_node_loc, tri_indices_loc, bvh_depths_loc):
        if self.ready:
            return

        if self.builder is not None and self.builder.is_done:
            self.bvh_built = True
            self.builder = None
        
        if self.bvh_built:
            print("Creating BVH buffers...")

            bvh_node_buffer = BVHNodeBuffer(self.scene)
            tri_indices_buffer = TriangleIndicesBuffer(self.scene)
            bvh_depths_buffer = BVHDepthsBuffer(self.scene)

            bvh_node_buffer.bind(self.ctx, bvh_node_loc)
            tri_indices_buffer.bind(self.ctx, tri_indices_loc)
            bvh_depths_buffer.bind(self.ctx, bvh_depths_loc)

            self.ready = True

            print("Path tracing is ready")


class CameraCaptureState:
    def __init__(self, scene_state, camera):
        self.scene_state = scene_state
        self.camera = camera
        self.camera_buffer = None
        self.states = {self._key(f):[] for f in self.scene_state.scene_files}
        self.curr_state_idx = 0
        self.browse_idx = 0

        self._load_states()

    def set_camera_buffer(self, camera_buffer):
        self.camera_buffer = camera_buffer

    def _key(self, scene_file):
        return Path(scene_file).name

    def _get_key(self):
        scene_file = self.scene_state.scene_files[self.scene_state.curr_scene_idx]
        return self._key(scene_file)
    
    def _load_states(self):
        try:
            with open(file_paths.camera_capture_states) as f:
                loaded = json.load(f)
        except:
            pass

        # Rebuild to add new scenes and remove stale keys
        self.states = {
            self._key(f): loaded.get(self._key(f), [])
            for f in self.scene_state.scene_files
        }

    def _get_scene_captures(self):
        return self.states[self._get_key()]

    def _load_state(self, state):
        self.camera.load_state(state)
        self.camera_buffer.update_data()

    def _write(self):
        with open(file_paths.camera_capture_states, "w") as f:
            json.dump(self.states, f, indent=2, sort_keys=True)

    def save_state(self):
        key = self._get_key()
        self.states[key].append(self.camera.get_state())
        self.browse_idx = len(self.states[key]) - 1
        self._write()
    
    def load_next_state(self):
        while True:
            captures = self._get_scene_captures()

            if self.curr_state_idx < len(captures):
                self._load_state(captures[self.curr_state_idx])
                self.curr_state_idx += 1
                return
            
            self.scene_state.next_scene()

            if self.scene_state.ai_training_finished:
                return
            
            self.curr_state_idx = 0

    def view_current(self):
        captures = self._get_scene_captures()
        if captures:
            self._load_state(captures[self.browse_idx])

    def next_capture(self):
        captures = self._get_scene_captures()
        if not captures:
            return
        self.browse_idx = (self.browse_idx + 1) % len(captures)
        self._load_state(captures[self.browse_idx])

    def previous_capture(self):
        captures = self._get_scene_captures()
        if not captures:
            return
        self.browse_idx = (self.browse_idx - 1) % len(captures)
        self._load_state(captures[self.browse_idx])

    def delete_current(self):
        captures = self._get_scene_captures()
        if not captures:
            return

        captures.pop(self.browse_idx)
        self._write()

        if not captures:
            self.browse_idx = 0
            return

        self.browse_idx = min(self.browse_idx, len(captures) - 1)


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

    def cap_fps(self, target_fps):
        target_duration = 1 / target_fps
        # Target time when the target_fps is reached
        target_time = self.frame_start + target_duration

        # Sleep/wait until the target_time is reached
        while True:
            remaining_time = target_time - time.perf_counter()

            if remaining_time <= 0:
                break
            
            # Sleep for the majority of the time to save CPU resources
            if remaining_time > 0.001:
                # Sleep for half of the remaining time
                # This methods allow sleeping precision as remaining time approaches zero
                sleep_time = remaining_time * 0.5
                time.sleep(sleep_time)
            
            # Wait until the target time is reached
            else:
                pass


class GlfwWindow:
    def __init__(self):
        self.window = None
        self.need_resize = False

    def create(self, title):
        if not glfwInit():
            return "Failed to initialize GLFW"
    
        glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4)
        glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 6)
        glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)
        # Apple system required config
        if sys.platform == "darwin":
            glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE)
        
        window = glfwCreateWindow(screen.width, screen.height, title, None, None)
    
        if not window:
            return "Failed to create GLFW window"

        self.window = window
        
        glfwMakeContextCurrent(window)
        if screen.vsync == True:
            glfwSwapInterval(1)
        else:
            glfwSwapInterval(0)

    def set_title(self, title):
        glfwSetWindowTitle(self.window, title)

    def resize(self, width, height):
        width = max(1, int(width))
        height = max(1, int(height))

        screen.width = width
        screen.height = height
        screen.resolution = [width, height]
        self.aspect_ratio = screen.width / max(screen.height, 1)

        self.need_resize = True

    def should_close(self):
        return glfwWindowShouldClose(self.window)

    def shutdown(self):
        glfwTerminate()

    def swap(self):
        glfwSwapBuffers(self.window)

    def disable_cursor(self):
        glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)

    def enable_cursor(self):
        glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)

    def poll(self):
        glfwPollEvents()


class InputState:
    def __init__(self, glfw_window, imgui_state):
        self.glfw_window = glfw_window
        self.imgui_state = imgui_state

        self.first_mouse = True
        self.last_x = screen.width / 2
        self.last_y = screen.height / 2
        self.middle_mouse_down = False

    def begin_drag(self):
        self.middle_mouse_down = True
        self.first_mouse = True

    def end_drag(self):
        self.middle_mouse_down = False

    def drag_delta(self, xpos, ypos):
        if self.first_mouse:
            self.last_x, self.last_y = xpos, ypos
            self.first_mouse = False
        
        xoffset = xpos - self.last_x
        # Reversed since y-coordinates go from bottom to top
        yoffset = self.last_y - ypos
        self.last_x, self.last_y = xpos, ypos

        return xoffset, yoffset

    def _pressed(self, key):
        return glfwGetKey(self.glfw_window.window, key) == GLFW_PRESS

    def process_input(self, delta_time, camera):
        if self.imgui_state.want_text_input():
            return
        
        if render_settings.render_mode == "path_tracing":
            return
        
        if self._pressed(GLFW_KEY_W):
            camera.process_keyboard(CameraMovement.FORWARD, delta_time)
        if self._pressed(GLFW_KEY_S):
            camera.process_keyboard(CameraMovement.BACKWARD, delta_time)
        if self._pressed(GLFW_KEY_A):
            camera.process_keyboard(CameraMovement.LEFT, delta_time)
        if self._pressed(GLFW_KEY_D):
            camera.process_keyboard(CameraMovement.RIGHT, delta_time)
        if self._pressed(GLFW_KEY_SPACE):
            camera.process_keyboard(CameraMovement.UP, delta_time)
        if self._pressed(GLFW_KEY_LEFT_SHIFT):
            camera.process_keyboard(CameraMovement.DOWN, delta_time)


class UIState:
    def __init__(self):
        self.settings_window = False

    def toggle_settings(self):
        self.settings_window = not self.settings_window


class ImguiState:
    def __init__(self):
        self.impl = None

    def create(self, window):
        imgui.create_context()
        self.impl = GlfwRenderer(window)

    def want_capture_mouse(self):
        return imgui.get_io().want_capture_mouse

    def want_text_input(self):
        return imgui.get_io().want_text_input

    def begin_frame(self):
        self.impl.process_inputs()
        imgui.new_frame()

    def end_frame(self):
        imgui.render()
        self.impl.render(imgui.get_draw_data())

    def shutdown(self):
        self.impl.shutdown()

    def forward_mouse(self, window, xpos, ypos):
        if hasattr(self.impl, "mouse_callback"):
            self.impl.mouse_callback(window, xpos, ypos)

    def forward_key(self, window, key, scancode, action, mods):
        if hasattr(self.impl, "keyboard_callback"):
            self.impl.keyboard_callback(window, key, scancode, action, mods)

    def forward_mouse_button(self, window, button, action, mods):
        if hasattr(self.impl, "mouse_button_callback"):
            self.impl.mouse_button_callback(window, button, action, mods)

    def forward_scroll(self, window, xoffset, yoffset):
        if hasattr(self.impl, "scroll_callback"):
            self.impl.scroll_callback(window, xoffset, yoffset)


class GlfwCallbackState:
    def __init__(self, glfw_window, input_state, ui_state, imgui_state, camera):
        self.glfw_window = glfw_window
        self.input_state = input_state
        self.ui_state = ui_state
        self.imgui_state = imgui_state
        self.camera = camera

    def set_callbacks(self):
        window = self.glfw_window.window
        glfwSetCursorPosCallback(window, self._mouse_callback)
        glfwSetScrollCallback(window, self._scroll_callback)
        glfwSetMouseButtonCallback(window, self._mouse_button_callback)
        glfwSetKeyCallback(window, self._key_callback)
        glfwSetFramebufferSizeCallback(window, self._framebuffer_size_callback)
        glfwSetWindowSizeLimits(window, 400, 300, GLFW_DONT_CARE, GLFW_DONT_CARE)

    def _framebuffer_size_callback(self, window, width, height):
        self.glfw_window.resize(width, height)

    def _key_callback(self, window, key, scancode, action, mods):
        self.imgui_state.forward_key(window, key, scancode, action, mods)

        if key == GLFW_KEY_ESCAPE and action == GLFW_PRESS:
            self.ui_state.toggle_settings()

    def _mouse_button_callback(self, window, button, action, mods):
        self.imgui_state.forward_mouse_button(window, button, action, mods)
        
        if self.imgui_state.want_capture_mouse():
            return

        if render_settings.render_mode == "path_tracing":
            return

        if button == GLFW_MOUSE_BUTTON_MIDDLE:
            if action == GLFW_PRESS:
                self.input_state.begin_drag()
                self.glfw_window.disable_cursor()
                
            elif action == GLFW_RELEASE:
                self.input_state.end_drag()
                self.glfw_window.enable_cursor()

    def _mouse_callback(self, window, xpos, ypos):
        self.imgui_state.forward_mouse(window, xpos, ypos)
        
        if self.imgui_state.want_capture_mouse():
            return

        if render_settings.render_mode == "path_tracing":
            return

        if self.input_state.middle_mouse_down:
            xoffset, yoffset = self.input_state.drag_delta(xpos, ypos)

            self.camera.process_mouse_movement(xoffset, yoffset)

    def _scroll_callback(self, window, xoffset, yoffset):
        self.imgui_state.forward_scroll(window, xoffset, yoffset)
        
        if self.imgui_state.want_capture_mouse():
            return
        
        if render_settings.render_mode == "path_tracing":
            return

        self.camera.process_mouse_scroll(yoffset)
