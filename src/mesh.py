import numpy as np
import pyassimp

from src.dtypes import *


MAX_BONE_INFLUENCE = 4

vertex_dtype = np.dtype([
    ("position", *vec3),
    ("normal", *vec3),
    ("tex_coords", *vec2),
    ("tangent", *vec3),
    ("bitanget", *vec3),
    ("bone_ids", *(vec(i4, MAX_BONE_INFLUENCE))),
    ("weights", *(vec(f4, MAX_BONE_INFLUENCE)))
])


class Mesh:
    def __init__(self, vertices, indices, textures):
        self.vertices = vertices
        self.indices = indices
        self.textures = textures

    def setup_mesh(self, ctx, prog, *args):
        self.vbo = ctx.buffer(self.vertices.astype(vertex_dtype))
        self.ebo = ctx.buffer(self.indices.astype(u4))

        self.vao = ctx.vertex_array(
            prog,
            [
                [
                    self.vbo,
                    f"3f 3f 2f 3f 3f {MAX_BONE_INFLUENCE}i {MAX_BONE_INFLUENCE}f",
                    *args
                ],
                self.ebo
            ]
        )
