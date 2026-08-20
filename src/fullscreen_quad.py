import moderngl

from src.dtypes import *


class FullScreenQuad:
    def __init__(self, ctx, shader):
        # Full-screen quad
        self.quad_buffer = ctx.buffer(np.array([
            # Vertices    # TexCoords
            -1.0,  1.0,   0.0, 1.0,
            -1.0, -1.0,   0.0, 0.0,
            1.0,  1.0,   1.0, 1.0,
            1.0, -1.0,   1.0, 0.0,
        ], dtype=f4))

        self.vao = ctx.vertex_array(
            shader.prog,
            [
                (self.quad_buffer, "2f 2f", "aPos", "aTexCoords")
            ]
        )

    def draw(self):
        self.vao.render(moderngl.TRIANGLE_STRIP)