import time

from src.settings import settings
from src.dtypes import *


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
        self.combined = self.ctx.texture(settings.screen.resolution, 4, dtype=f4)
        self.albedo = self.ctx.texture(settings.screen.resolution, 4, dtype=f4)
        self.normal = self.ctx.texture(settings.screen.resolution, 4, dtype=f4)
        self.depth = self.ctx.texture(settings.screen.resolution, 4, dtype=f4)
    
    def _create_saved_buffers(self):
        self.saved_combined = self.ctx.texture(settings.screen.resolution, 4, dtype=f4)
        self.saved_albedo = self.ctx.texture(settings.screen.resolution, 4, dtype=f4)
        self.saved_normal = self.ctx.texture(settings.screen.resolution, 4, dtype=f4)
        self.saved_depth = self.ctx.texture(settings.screen.resolution, 4, dtype=f4)

    def _clear_active_buffers(self):
        zeros = np.zeros((*settings.screen.resolution, 4), dtype=f4)
        self.combined.write(zeros)
        self.albedo.write(zeros)
        self.normal.write(zeros)
        self.depth.write(zeros)
        self.direct_emissive.write(zeros)

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


class TileState:
    def __init__(self):
        # Current tile position in pixels
        self.curr_tile_x = 0
        self.curr_tile_y = 0
        
        # Apply ceiling function
        # Allows the compute shader to reach the entire screen
        self.tile_width = (settings.screen.width + settings.rendering.tiles.x - 1) // settings.rendering.tiles.x
        self.tile_height = (settings.screen.height + settings.rendering.tiles.y - 1) // settings.rendering.tiles.y

        self.frame_finished = False

    def reset(self):
        # Reset tiling position
        self.curr_tile_x = 0
        self.curr_tile_y = 0

        # Recalculate tile sizes
        self.tile_width = (settings.screen.width + settings.rendering.tiles.x - 1) // settings.rendering.tiles.x
        self.tile_height = (settings.screen.height + settings.rendering.tiles.y - 1) // settings.rendering.tiles.y

    def advance(self):
        self.curr_tile_x += self.tile_width
        if self.curr_tile_x > settings.screen.width:
            self.curr_tile_x = 0
            self.curr_tile_y += self.tile_height
        
        if self.curr_tile_y > settings.screen.height:
            self.curr_tile_y = 0
            self.frame_finished = True
        else:
            self.frame_finished = False


class RenderState:
    def __init__(self):
        self.total_samples = 0
        self.render_complete = False
        self.should_view_saved = False
        self.should_render = False

        self.render_start_time = None
        self.render_end_time = None
        self.render_time = None

    def start(self):
        self.should_render = True
        self.render_start_time = time.perf_counter()

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
        self.render_end_time = time.perf_counter()
        self.render_time = self.render_end_time - self.render_start_time


class DebugState:
    def __init__(self):
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
            self.saved_denoised = self.ctx.texture(settings.screen.resolution, 3, dtype=f4)
            ai_denoiser.denoise(combined, albedo, normal, depth, self.saved_denoised)

    def reset(self):
        self._release_buffer()
        self.saved_denoised = None
        self.should_denoise = False


class PTState:
    def __init__(self, ctx):
        self.ctx = ctx
        self.framebuffers = FramebufferState(ctx)
        self.tiles = TileState()
        self.rendering = RenderState()
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

        samples_left = settings.path_tracing.max_samples - self.rendering.total_samples
        if samples_left < settings.path_tracing.spp:
            self.rendering.total_samples += samples_left
        else:
            self.rendering.total_samples += settings.path_tracing.spp

        if self.rendering.total_samples >= settings.path_tracing.max_samples:
            self.framebuffers.save()
            self.rendering.complete()

    def denoise(self, ai_denoiser):
        self.denoising.denoise(
            ai_denoiser,
            self.framebuffers.saved_combined,
            self.framebuffers.saved_albedo,
            self.framebuffers.saved_normal,
            self.framebuffers.saved_depth
        )


class RasterState:
    def __init__(self, ctx):
        self.ctx = ctx

        self._create_active_buffers()

    def _create_active_buffers(self):
        self.raster_color_tex = self.ctx.texture(settings.screen.resolution, 4, dtype=f4)
        self.raster_depth_texture = self.ctx.depth_texture(settings.screen.resolution)
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
        self.output_tex = self.ctx.texture(settings.screen.resolution, 4, dtype=f4)
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
