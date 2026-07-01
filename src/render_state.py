import numpy as np
from src.dtypes import *
from src.settings import *


class PTState:
    def __init__(self, ctx):
        self.ctx = ctx
        self.compute_tex = ctx.texture(screen.resolution, 4, dtype=f4)
        self.saved_render = None

        # Current tile top left position in pixels
        self.curr_tile_x = 0
        self.curr_tile_y = 0
        # Apply ceiling function
        # Allows the compute shader to reach the entire screen
        self.tile_width = (screen.width + render_settings.tiles_x - 1) // render_settings.tiles_x
        self.tile_height = (screen.height + render_settings.tiles_y - 1) // render_settings.tiles_y

        self.render_complete = False
        self.view_saved = False
        self.should_render = False
        self.total_samples = 0
    
    def resize(self):
        self.compute_tex.release()

        self.compute_tex = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.compute_tex.write(np.zeros((*screen.resolution, 4), dtype=f4))

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

        # Reset accumulation buffer
        self.compute_tex.write(np.zeros((*screen.resolution, 4), dtype=f4))
    
    def save_render(self):
        if self.saved_render is not None:
            self.saved_render.release()
        self.saved_render = self.ctx.texture(screen.resolution, 4, dtype=f4)
        self.saved_render.write(self.compute_tex.read())

        self.render_complete = True
        self.view_saved = True
    

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
