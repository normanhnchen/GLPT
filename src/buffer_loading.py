from src.dtypes import *
from src.settings import *
from src.buffers import *


class CameraBuffer:
    def __init__(self, camera):
        camera_data = np.zeros(1, dtype=camera_dtype)

        camera_data["aperture"] = post_process_settings.aperture
        camera_data["focusDist"] = post_process_settings.focus_dist
        camera_data["autoFocus"] = post_process_settings.auto_focus

        self.camera = camera
        self.camera_data = camera_data
    
    def update_data(self):
        self.camera_data["pos"] = self.camera.pos
        self.camera_data["front"] = self.camera.front
        self.camera_data["up"] = self.camera.up
        self.camera_data["right"] = self.camera.right
        self.camera_data["fov"] = self.camera.fov
        self.camera_data["aperture"] = post_process_settings.aperture
        self.camera_data["focusDist"] = post_process_settings.focus_dist
        self.camera_data["autoFocus"] = post_process_settings.auto_focus

        self.camera_buffer.write(self.camera_data.tobytes())
    
    def bind(self, ctx, loc):
        self.camera_buffer = ctx.buffer(self.camera_data.tobytes())
        self.camera_buffer.bind_to_storage_buffer(loc)


class MaterialBuffer:
    def __init__(self, scene):
        material_data = np.zeros(scene.num_materials, dtype=material_dtype)

        for i, mat in enumerate(scene.materials):
            material_data[i]["baseCol"] = mat.base_color[:3]
            material_data[i]["alpha"] = mat.base_color[-1]
            material_data[i]["roughness"] = mat.roughness
            material_data[i]["emissive"] = mat.emissive_color
            material_data[i]["metallic"] = mat.metallic
            # Ambient occlusion is changed only from material textures
            # Set default to 1.0 for a fully lit material
            material_data[i]["ao"] = set_f4(1)

            material_data[i]["alphaMode"] = mat.alpha_mode
            material_data[i]["alphaCutoff"] = mat.alpha_cutoff
            material_data[i]["doubleSided"] = mat.double_sided

            # Flags
            material_data[i]["hasEmission"] = mat.has_emission
            material_data[i]["hasBaseColTex"] = mat.has_base_color_tex
            material_data[i]["hasEmissiveTex"] = mat.has_emissive_tex
            material_data[i]["hasRoughTex"] = mat.has_roughness_tex
            material_data[i]["hasMetalTex"] = mat.has_metallic_tex
            material_data[i]["hasNormalTex"] = mat.has_normal_tex
            material_data[i]["hasOcclTex"] = mat.has_occlusion_tex
            
            # Texture IDs
            material_data[i]["baseTexId"] = mat.base_color_tex_id
            material_data[i]["emissiveTexId"] = mat.emissive_tex_id
            material_data[i]["roughTexId"] = mat.roughness_tex_id
            material_data[i]["metalTexId"] = mat.metallic_tex_id
            material_data[i]["normalTexId"] = mat.normal_tex_id
            material_data[i]["occlTexId"] = mat.occlusion_tex_id
            
            # glTF extensions
            # ---------------
            material_data[i]["emissiveStrength"] = mat.emissive_strength
            material_data[i]["transmission"] = mat.transmission
            material_data[i]["ior"] = mat.ior
        
        self.material_data = material_data
    
    def bind(self, ctx, loc):
        self.material_buffer = ctx.buffer(self.material_data.tobytes())
        self.material_buffer.bind_to_storage_buffer(loc)


class LightBuffer:
    def __init__(self, scene):
        # Ensure there is atleast a buffer size
        buffer_size = max(1, scene.num_lights)

        light_data = np.zeros(buffer_size, dtype=light_dtype)
        light_data[:scene.num_lights] = scene.lights
        
        self.light_data = light_data
    
    def bind(self, ctx, loc):
        self.light_buffer = ctx.buffer(self.light_data.tobytes())
        self.light_buffer.bind_to_storage_buffer(loc)


class TriangleBuffer:
    def __init__(self, scene):
        triangle_data = np.zeros(scene.num_triangles, dtype=triangle_dtype)
        
        idx0 = scene.triangles[:, 0]
        idx1 = scene.triangles[:, 1]
        idx2 = scene.triangles[:, 2]

        triangle_data["v0"]["pos"] = scene.vertices[idx0]
        triangle_data["v1"]["pos"] = scene.vertices[idx1]
        triangle_data["v2"]["pos"] = scene.vertices[idx2]

        triangle_data["v0"]["uv"] = scene.uvs[idx0]
        triangle_data["v1"]["uv"] = scene.uvs[idx1]
        triangle_data["v2"]["uv"] = scene.uvs[idx2]

        triangle_data["v0"]["n"] = scene.normals[idx0]
        triangle_data["v1"]["n"] = scene.normals[idx1]
        triangle_data["v2"]["n"] = scene.normals[idx2]

        triangle_data["v0"]["dpdu"] = scene.tangents[idx0]
        triangle_data["v1"]["dpdu"] = scene.tangents[idx1]
        triangle_data["v2"]["dpdu"] = scene.tangents[idx2]

        triangle_data["v0"]["dpdv"] = scene.bitangents[idx0]
        triangle_data["v1"]["dpdv"] = scene.bitangents[idx1]
        triangle_data["v2"]["dpdv"] = scene.bitangents[idx2]

        triangle_data["matId"] = scene.material_ids

        triangle_data["area"] = scene.triangle_areas

        self.triangle_data = triangle_data

    def bind(self, ctx, loc):
        self.triangle_buffer = ctx.buffer(self.triangle_data.tobytes())
        self.triangle_buffer.bind_to_storage_buffer(loc)


class BVHNodeBuffer:
    def __init__(self, scene):
        bvh_node_data = np.zeros(scene.num_bvh_nodes, dtype=bvh_node_dtype)

        for i in range(scene.num_bvh_nodes):
            bvh_node_data[i]["aabbMin"] = scene.bvh.aabb_mins[i]
            bvh_node_data[i]["aabbMax"] = scene.bvh.aabb_maxs[i]
            bvh_node_data[i]["leftChildId"] = scene.bvh.left_child_indices[i]
            bvh_node_data[i]["rightChildId"] = scene.bvh.right_child_indices[i]
            bvh_node_data[i]["firstTriId"] = scene.bvh.first_tri_indices[i]
            bvh_node_data[i]["triCount"] = scene.bvh.tri_counts[i]
            bvh_node_data[i]["isLeaf"] = scene.bvh.is_leafs[i]
        
        self.bvh_node_data = bvh_node_data
    
    def bind(self, ctx, loc):
        self.bvh_node_buffer = ctx.buffer(self.bvh_node_data.tobytes())
        self.bvh_node_buffer.bind_to_storage_buffer(loc)


class TriangleIndicesBuffer:
    def __init__(self, scene):
        self.tri_indices_data = scene.bvh.tri_indices.astype(i4)
    
    def bind(self, ctx, loc):
        self.tri_indices_buffer = ctx.buffer(self.tri_indices_data.tobytes())
        self.tri_indices_buffer.bind_to_storage_buffer(loc)

class EmissiveTrianglesBuffer:
    def __init__(self, scene):
        # Ensure there is atleast a buffer size
        num_emissive_triangles = max(scene.num_emissive_triangles, 1)
        
        emissive_triangles_data = np.zeros(num_emissive_triangles, dtype=emissive_triangles_dtype)

        if scene.num_emissive_triangles > 0:
            emissive_triangles_data["triId"][:scene.num_emissive_triangles] = scene.emissive_triangle_indices

        self.emissive_triangles_data = emissive_triangles_data

    def bind(self, ctx, loc):
        self.emissive_triangles_buffer = ctx.buffer(self.emissive_triangles_data.tobytes())
        self.emissive_triangles_buffer.bind_to_storage_buffer(loc)
