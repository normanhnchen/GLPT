import moderngl
import numpy as np

from src.dtypes import *
from src.settings import settings


def _compute_uniforms(scene, camera):
    return {
        # Vertex Shader Uniforms
        # ----------------------
        "view": camera.get_view().to_bytes(),
        "projection": camera.get_perspective().to_bytes(),
        # Fragment Shader Uniforms
        # ------------------------
        "numLights": set_i4(scene.num_lights),
        "cameraPos": camera.pos,
    }


def _set_uniforms(prog, uniform_dict):
    for uniform, value in uniform_dict.items():
        if isinstance(value, bytes):
            prog[uniform].write(value)
        else:
            prog[uniform].value = value


class PBRGeometry:
    def __init__(self, ctx, scene, pbr_shader):
        vertices = scene.vertices[scene.triangles]
        uvs = scene.uvs[scene.triangles]
        normals = scene.normals[scene.triangles]
        tangents = scene.tangents[scene.triangles]
        bitangents = scene.bitangents[scene.triangles]
        ids = np.repeat(scene.material_ids, 3)

        vertices = vertices.reshape(-1, 3)
        uvs = uvs.reshape(-1, 2)
        normals = normals.reshape(-1, 3)
        tangents = tangents.reshape(-1, 3)
        bitangents = bitangents.reshape(-1, 3)
        ids = ids.reshape(-1,)

        pbr_dtype = np.dtype([
            ("pos", *vec3),
            ("uv", *vec2),
            ("normal", *vec3),
            ("tangent", *vec3),
            ("bitangent", *vec3),
            ("matId", i4)
        ])

        pbr_data = np.zeros(len(vertices), dtype=pbr_dtype)

        pbr_data["pos"] = vertices
        pbr_data["uv"] = uvs
        pbr_data["normal"] = normals
        pbr_data["tangent"] = tangents
        pbr_data["bitangent"] = bitangents
        pbr_data["matId"] = ids

        pbr_vbo = ctx.buffer(pbr_data.tobytes())

        pbr_vao = ctx.vertex_array(
            pbr_shader.prog,
            [
                (
                    pbr_vbo,
                    "3f 2f 3f 3f 3f 1i",
                    "aPos", "aTexCoords", "aNormal", "aTangent", "aBitangent", "aMatId"
                )
            ]
        )

        self.pbr_data = pbr_data
        self.pbr_vao = pbr_vao

    def draw(self):
        self.pbr_vao.render(moderngl.TRIANGLES)


class PBRPass:
    def __init__(self, ctx, scene, camera, pbr_shader):
        self.ctx = ctx
        self.scene = scene
        self.camera = camera
        self.pbr_shader = pbr_shader
        self.pbr_geometry = PBRGeometry(ctx, scene, pbr_shader)

    def render(self):
        uniform_dict = _compute_uniforms(self.scene, self.camera)
        _set_uniforms(self.pbr_shader.prog, uniform_dict)

        self.ctx.depth_func = "<"

        self.pbr_geometry.draw()
