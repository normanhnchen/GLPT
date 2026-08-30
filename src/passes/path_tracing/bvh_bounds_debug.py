import numpy as np
import moderngl

from src.settings import settings
from src.dtypes import *


def _compute_uniforms(scene, camera):
    return {
        # Vertex Shader Uniforms
        # ------------------------
        "view": camera.get_view().to_bytes(),
        "projection": camera.get_perspective().to_bytes(),
        # Fragment Shader Uniforms
        # ------------------------
        "bvhViewLayer": settings.debug.bvh.view_layer,
        "bvhViewDepth": settings.debug.bvh.view_depth,
        "bvhMaxNodeDepth": scene.bvh.max_depth,
        "bvhColorMode": settings.debug.bvh.color_mode
    }


def _set_uniforms(prog, uniform_dict):
    for uniform, value in uniform_dict.items():
        if isinstance(value, bytes):
            prog[uniform].write(value)
        else:
            prog[uniform].value = value


class BVHBoundsGeometry:
    def __init__(self, ctx, scene, shader):
        self.scene = scene

        vertices = np.array([
            # Bottom square
            0, 0, 0,  1, 0, 0,
            1, 0, 0,  1, 0, 1,
            1, 0, 1,  0, 0, 1,
            0, 0, 1,  0, 0, 0,
            # Top square
            0, 1, 0,  1, 1, 0,
            1, 1, 0,  1, 1, 1,
            1, 1, 1,  0, 1, 1,
            0, 1, 1,  0, 1, 0,
            # Connecting vertical pillars
            0, 0, 0,  0, 1, 0,
            1, 0, 0,  1, 1, 0,
            1, 0, 1,  1, 1, 1,
            0, 0, 1,  0, 1, 1
        ], dtype=f4)

        cube_vbo = ctx.buffer(vertices.tobytes())

        self.cube_vao = ctx.vertex_array(
            shader.prog,
            [
                (
                    cube_vbo,
                    "3f",
                    "aPos"
                )
            ]
        )

    def draw(self):
        self.cube_vao.render(moderngl.LINES, instances=self.scene.num_bvh_nodes)


class BVHBoundsDebugPass:
    def __init__(self, ctx, scene, camera, shader):
        self.shader = shader
        self.scene = scene
        self.camera = camera
        self.bvh_bounds_geometry = BVHBoundsGeometry(ctx, scene, shader)

    def render(self):
        uniform_dict = _compute_uniforms(self.scene, self.camera)
        _set_uniforms(self.shader.prog, uniform_dict)

        self.bvh_bounds_geometry.draw()
