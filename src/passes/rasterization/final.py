from src.settings import *
from src.fullscreen_quad import *


def _compute_uniforms():
    return {
        # Fragment Shader Uniforms
        # ------------------------
        "exposure": settings.post_processing.exposure
    }


def _set_uniforms(prog, uniform_dict):
    for uniform, value in uniform_dict.items():
        if isinstance(value, bytes):
            prog[uniform].write(value)
        else:
            prog[uniform].value = value


class FinalPass:
    def __init__(self, ctx, shader, raster_state):
        self.shader = shader
        self.raster_state = raster_state
        self.quad = FullScreenQuad(ctx, shader)

    def render(self):
        # Draw to screen
        self.raster_state.raster_color_tex.use(location=0)

        uniform_dict = _compute_uniforms()
        _set_uniforms(self.shader.prog, uniform_dict)

        self.shader.set_tonemap(settings.post_processing.tonemap)

        self.quad.draw()
