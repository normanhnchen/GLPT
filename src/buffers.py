import numpy

from src.dtypes import *
from src.settings import *



class CameraBuffer:
    def __init__(self, camera):
        camera_dtype = np.dtype([
            ("pos", *vec3),
            ("aperture", f4),
            ("front", *vec3),
            ("focusDist", f4),
            ("up", *vec3),
            ("autoFocus", f4),
            ("right", *vec3),
            ("fov", f4)
        ])
        
        camera_data = np.zeros(1, dtype=camera_dtype)

        camera_data["aperture"] = post_process_settings.aperture
        camera_data["focusDist"] = post_process_settings.focus_dist
        camera_data["autoFocus"] = post_process_settings.auto_focus

        self.camera = camera
        self.camera_dtype = camera_dtype
        self.camera_data = camera_data
    
    def update_data(self):
        self.camera_data["pos"] = self.camera.pos
        self.camera_data["front"] = self.camera.front
        self.camera_data["up"] = self.camera.up
        self.camera_data["right"] = self.camera.right
        self.camera_data["fov"] = self.camera.fov

        self.camera_buffer.write(self.camera_data.tobytes())
    
    def bind(self, ctx, loc):
        self.camera_buffer = ctx.buffer(self.camera_data.tobytes())
        self.camera_buffer.bind_to_storage_buffer(loc)


class MaterialBuffer:
    def __init__(self, scene):
        material_dtype = np.dtype([
            ("baseCol", *vec3),
            ("alpha", f4),
            ("emissive", *vec3),
            ("metallic", f4),
            ("roughness", f4),
            ("ao", f4),
            # Settings
            ("alphaMode", i4), # 0=OPAQUE, 1=MASK, or 2=BLEND
            ("alphaCutoff", f4),
            ("doubleSided", i4),
            # Flags
            ("hasEmission", i4),
            ("hasBaseColTex", i4),
            ("hasEmissiveTex", i4),
            ("hasRoughTex", i4),
            ("hasMetalTex", i4),
            ("hasNormalTex", i4),
            ("hasOcclTex", i4),
            # Texture IDs
            ("baseTexId", i4),
            ("emissiveTexId", i4),
            ("roughTexId", i4),
            ("metalTexId", i4),
            ("normalTexId", i4),
            ("occlTexId", i4),
            ("emissiveStrength", f4),
            ("transmission", f4),
            ("ior", f4),
            ("pad1", f4),
            ("pad2", f4),
            ("pad3", f4)
        ])

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
            extensions = mat.extensions

            KHR_materials_emissive_strength = extensions.get("KHR_materials_emissive_strength")
            if KHR_materials_emissive_strength:
                material_data[i]["emissiveStrength"] = KHR_materials_emissive_strength["emissiveStrength"]
            else:
                material_data[i]["emissiveStrength"] = 0.0

            KHR_materials_transmission = extensions.get("KHR_materials_transmission")
            if KHR_materials_transmission:
                material_data[i]["transmission"] = KHR_materials_transmission["transmissionFactor"]
            else:
                material_data[i]["transmission"] = set_f4(0.0)

            KHR_materials_ior = extensions.get("KHR_materials_ior")
            if KHR_materials_ior:
                material_data[i]["ior"] = KHR_materials_ior["ior"]
            else:
                material_data[i]["ior"] = set_f4(1.5)
        
        self.material_dtype = material_dtype
        self.material_data = material_data
    
    def bind(self, ctx, loc):
        self.material_buffer = ctx.buffer(self.material_data.tobytes())
        self.material_buffer.bind_to_storage_buffer(loc)


class LightBuffer:
    def __init__(self, scene):
        light_dtype = np.dtype([
            ("col", *vec3),
            ("type", i4), # Point: 0, directional: 1, spot: 2
            ("pos", *vec3),
            ("intensity", f4),
            ("dir", *vec3),
            ("range", f4),
            ("isSpot", i4),
            ("innerConeAngle", f4), # Radians
            ("outerConeAngle", f4), # Radians
            ("pad1", f4)
        ])

        # Ensure there is atleast a buffer size
        buffer_size = max(1, scene.num_lights)

        light_data = np.zeros(buffer_size, dtype=light_dtype)

        for i, light in enumerate(scene.lights):
            light_type = light["type"]
            if light_type == "directional":
                light_data[i]["type"] = 1
            elif light_type == "spot":
                light_data[i]["type"] = 2
            else:
                light_data[i]["type"] = 0

            light_data[i]["col"]       = light["color"]
            light_data[i]["intensity"] = light["intensity"]
            light_data[i]["range"]     = light["range"]

            spot = light["spot"]
            if spot:
                light_data[i]["isSpot"] = 1
                light_data[i]["innerConeAngle"] = spot["innerConeAngle"]
                light_data[i]["outerConeAngle"] = spot["outerConeAngle"]
            else:
                light_data[i]["isSpot"] = 0
            
            # Convert to list then array as they are glm.vec3 objects
            light_data[i]["pos"] = np.array(list(light["position"]))
            light_data[i]["dir"] = np.array(list(light["direction"]))
        
        self.light_dtype = light_dtype
        self.light_data = light_data
    
    def bind(self, ctx, loc):
        self.light_buffer = ctx.buffer(self.light_data.tobytes())
        self.light_buffer.bind_to_storage_buffer(loc)


class TriangleBuffer:
    def __init__(self, material_buffer, scene):
        vertex_dtype = np.dtype([
            ("pos", *vec3),
            ("pad1", f4),
            ("uv", *vec2),
            ("pad2", *vec2),
            ("normal", *vec3),
            ("pad3", f4),
            ("tangent", *vec3),
            ("pad4", f4),
            ("bitangent", *vec3),
            ("pad5", f4),
        ])

        triangle_dtype = np.dtype([
            ("v0", vertex_dtype), ("v1", vertex_dtype), ("v2", vertex_dtype),
            ("mat", material_buffer.material_dtype),
        ])

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

        triangle_data["v0"]["normal"] = scene.normals[idx0]
        triangle_data["v1"]["normal"] = scene.normals[idx1]
        triangle_data["v2"]["normal"] = scene.normals[idx2]

        triangle_data["v0"]["tangent"] = scene.tangents[idx0]
        triangle_data["v1"]["tangent"] = scene.tangents[idx1]
        triangle_data["v2"]["tangent"] = scene.tangents[idx2]

        triangle_data["v0"]["bitangent"] = scene.bitangents[idx0]
        triangle_data["v1"]["bitangent"] = scene.bitangents[idx1]
        triangle_data["v2"]["bitangent"] = scene.bitangents[idx2]

        triangle_data["mat"] = material_buffer.material_data[scene.material_ids]

        self.vertex_dtype = vertex_dtype
        self.triangle_dtype = triangle_dtype
        self.triangle_data = triangle_data

    def bind(self, ctx, loc):
        self.triangle_buffer = ctx.buffer(self.triangle_data.tobytes())
        self.triangle_buffer.bind_to_storage_buffer(loc)


class BVHNodeBuffer:
    def __init__(self, scene):
        bvh_node_dtype = np.dtype([
            ("aabbMin", *vec3),
            ("leftChildIdx", i4),
            ("aabbMax", *vec3),
            ("rightChildIdx", i4),
            ("firstTriIdx", i4),
            ("triCount", i4),
            ("isLeaf", i4),
            ("pad1", f4)
        ])
        
        bvh_node_data = np.zeros(scene.num_bvh_nodes, bvh_node_dtype)

        for i in range(scene.num_bvh_nodes):
            bvh_node_data[i]["aabbMin"] = scene.bvh.aabb_mins[i]
            bvh_node_data[i]["aabbMax"] = scene.bvh.aabb_maxs[i]
            bvh_node_data[i]["leftChildIdx"] = scene.bvh.left_child_indices[i]
            bvh_node_data[i]["rightChildIdx"] = scene.bvh.right_child_indices[i]
            bvh_node_data[i]["firstTriIdx"] = scene.bvh.first_tri_indices[i]
            bvh_node_data[i]["triCount"] = scene.bvh.tri_counts[i]
            bvh_node_data[i]["isLeaf"] = scene.bvh.is_leafs[i]
        
        self.bvh_node_dtype = bvh_node_dtype
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
