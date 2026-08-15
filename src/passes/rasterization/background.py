import moderngl

from src.dtypes import *
from src.settings import *


def _compute_uniforms(camera):
    return {
        # Vertex Shader Uniforms
        # ------------------------
        "view": camera.get_view().to_bytes(),
        "projection": camera.get_perspective().to_bytes(),
        # Fragment Shader Uniforms
        # ------------------------
        "hdriExposure": settings.post_processing.hdri_exposure
    }


def _set_uniforms(prog, uniform_dict):
    for uniform, value in uniform_dict.items():
        if isinstance(value, bytes):
            prog[uniform].write(value)
        else:
            prog[uniform].value = value



class BGGeometry:
    def __init__(self, ctx, bg_shader):
        cubemap_data = np.array([
            -1, -1, -1,   -1, -1,  1,   -1,  1,  1,
            -1, -1, -1,   -1,  1,  1,   -1,  1, -1,

            1, -1,  1,    1, -1, -1,    1,  1, -1,
            1, -1,  1,    1,  1, -1,    1,  1,  1,

            -1, -1, -1,    1, -1, -1,    1, -1,  1,
            -1, -1, -1,    1, -1,  1,   -1, -1,  1,

            -1,  1,  1,    1,  1,  1,    1,  1, -1,
            -1,  1,  1,    1,  1, -1,   -1,  1, -1,

            1, -1, -1,   -1, -1, -1,   -1,  1, -1,
            1, -1, -1,   -1,  1, -1,    1,  1, -1,

            -1, -1,  1,    1, -1,  1,    1,  1,  1,
            -1, -1,  1,    1,  1,  1,   -1,  1,  1,
        ], dtype=f4)

        bg_vbo = ctx.buffer(cubemap_data.tobytes())

        bg_vao = ctx.vertex_array(
            bg_shader.prog,
            [
                (
                    bg_vbo,
                    "3f",
                    "aPos"
                )
            ]
        )

        self.bg_data = cubemap_data
        self.bg_vbo = bg_vbo
        self.bg_vao = bg_vao
    
    def draw(self):
        self.bg_vao.render(moderngl.TRIANGLES)



class BackgroundPass:
    def __init__(self, ctx, camera, bg_shader):
        self.ctx = ctx
        self.camera = camera
        self.shader = bg_shader
        self.bg_geometry = BGGeometry(ctx, bg_shader)

    def render(self):
        uniform_dict = _compute_uniforms(self.camera)
        _set_uniforms(self.shader.prog, uniform_dict)
        
        self.ctx.depth_func = "<="

        self.bg_geometry.draw()
