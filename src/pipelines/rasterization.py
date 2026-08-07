from src.passes.rasterization.background import *
from src.passes.rasterization.pbr import *
from src.passes.rasterization.final import *


class RasterizationPipeline:
    def __init__(self, ctx, scene, camera, raster_state, frag_shaders, frag_quad):
        self.ctx = ctx
        self.raster_state = raster_state
        self.bg_pass = BackgroundPass(ctx, camera, frag_shaders.bg)
        self.pbr_pass = PBRPass(ctx, scene, camera, frag_shaders.pbr)
        self.final_pass = FinalPass(frag_shaders.final, raster_state, frag_quad)

    def render(self):
        self.bg_pass.render()
        self.pbr_pass.render()
        self.ctx.screen.use()
        self.raster_state.raster_color_tex.use(location=0)
        self.final_pass.render()
