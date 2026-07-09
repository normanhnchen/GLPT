import numpy as np
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
