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


class PBRPass:
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


class BGPass:
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
