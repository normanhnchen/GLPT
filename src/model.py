import trimesh
import numpy as np

from src.dtypes import *


class Texture:
    def __init__(self, pil_image):
        if pil_image is None:
            self.is_empty = True
            self.data = None
            return
            
        self.is_empty = False
        self._original_image = pil_image
        self.image = pil_image.convert("RGBA")
        self.data = self.image.tobytes()
    
    def resize(self, width, height):
        if self.is_empty:
            return
        self.image = self._original_image.resize((width, height)).convert("RGBA")
        self.data = self.image.tobytes()


class Material:
    def __init__(self, trimesh_material):
        self.alpha_mode = getattr(trimesh_material, "alphaMode", "OPAQUE")
        self.alpha_cutoff = getattr(trimesh_material, "alphaCutoff", 0.5)
        self.double_sided = bool(getattr(trimesh_material, "doubleSided", False))

        base_color = getattr(trimesh_material, "baseColorFactor", None)
        emissive_color = getattr(trimesh_material, "emissiveFactor", None)
        roughness = getattr(trimesh_material, "roughnessFactor", None)
        metallic = getattr(trimesh_material, "metallicFactor", None)

        base_color_tex = getattr(trimesh_material, "baseColorTexture", None)
        emissive_tex = getattr(trimesh_material, "emissiveTexture", None)
        normal_tex = getattr(trimesh_material, "normalTexture", None)
        occlusion_tex = getattr(trimesh_material, "occlusionTexture", None)

        metallic_roughness_texture = getattr(trimesh_material, "metallicRoughnessTexture", None)
        
        roughness_tex = None
        metallic_tex = None

        # Unpack metallic roughness texture
        if metallic_roughness_texture is not None:
            channels = metallic_roughness_texture.split()
            roughness_tex = channels[1] # Green channel
            metallic_tex = channels[2] # Blue channel
        
        self.base_color_tex = Texture(base_color_tex)
        self.emissive_tex = Texture(emissive_tex)
        self.roughness_tex = Texture(roughness_tex)
        self.metallic_tex = Texture(metallic_tex)
        self.normal_tex = Texture(normal_tex)
        self.occlusion_tex = Texture(occlusion_tex)

        self.textures = [
            self.base_color_tex,
            self.emissive_tex,
            self.roughness_tex,
            self.metallic_tex,
            self.normal_tex,
            self.occlusion_tex
        ]

        if base_color is not None:
            self.base_color = self._to_float_rgb(trimesh_material.baseColorFactor)
        else:
            # Set default color
            self.base_color = np.array([0.8, 0.8, 0.8, 1.0], dtype=f4)
        
        if emissive_color is not None:
            self.emissive_color = self._to_float_rgb(trimesh_material.emissiveFactor)
            self.has_emission = set_i4(1)
        else:
            # Set to no emission 
            self.emissive_color = np.array([-1, -1, -1], dtype=f4)
            self.has_emission = set_i4(0)

        if roughness is not None:
            self.roughness = set_f4(trimesh_material.roughnessFactor)
        else:
            # Set default roughness
            self.roughness = set_f4(0.8)
        
        if metallic is not None:
            self.metallic = set_f4(trimesh_material.metallicFactor)
        else:
            # Set to no metallic
            self.metallic = set_f4(0)
        
        self.has_emission = set_i4(1) if emissive_color is not None else set_i4(0)
        self.has_base_color_tex = set_i4(0) if self.base_color_tex.is_empty else set_i4(1)
        self.has_emissive_tex = set_i4(0) if self.emissive_tex.is_empty else set_i4(1)
        self.has_roughness_tex = set_i4(0) if self.roughness_tex.is_empty else set_i4(1)
        self.has_metallic_tex = set_i4(0) if self.metallic_tex.is_empty else set_i4(1)
        self.has_normal_tex = set_i4(0) if self.normal_tex.is_empty else set_i4(1)
        self.has_occlusion_tex = set_i4(0) if self.occlusion_tex.is_empty else set_i4(1)

        self.base_color_tex_id = set_i4(-1)
        self.emissive_tex_id = set_i4(-1)
        self.roughness_tex_id = set_i4(-1)
        self.metallic_tex_id = set_i4(-1)
        self.normal_tex_id = set_i4(-1)
        self.occlusion_tex_id = set_i4(-1)
    
    def _to_float_rgb(self, color):
        color = np.asarray(color, dtype=f4)
        if np.max(color) > 1.0:
            # Convert to float RGB
            return color / 255
        return color


class Scene:
    def __init__(self, file_path):
        scene = trimesh.load(file_path)

        all_vertices = []
        all_triangles = []
        all_normals = []
        all_faces = []
        all_uvs = []
        all_material_ids = []
        
        materials_list = []
        materials = []

        self.base_color_textures = []
        self.emissive_textures = []
        self.roughness_textures = []
        self.metallic_textures = []
        self.normal_textures = []
        self.occlusion_textures = []

        vertex_offset = 0

        # Iterate through all scene geometries
        for node_name in scene.graph.nodes_geometry:
            transform, geometry_name = scene.graph[node_name]
            mesh = scene.geometry[geometry_name]

            # Convert mesh data to world space
            mesh.apply_transform(transform)

            trimesh_material = mesh.visual.material
            material = Material(trimesh_material)

            material.base_color_tex_id = self._get_texture_id(material.base_color_tex, self.base_color_textures)
            material.emissive_tex_id = self._get_texture_id(material.emissive_tex, self.emissive_textures)
            material.roughness_tex_id = self._get_texture_id(material.roughness_tex, self.roughness_textures)
            material.metallic_tex_id = self._get_texture_id(material.metallic_tex, self.metallic_textures)
            material.normal_tex_id = self._get_texture_id(material.normal_tex, self.normal_textures)
            material.occlusion_tex_id = self._get_texture_id(material.occlusion_tex, self.occlusion_textures)

            if material not in materials_list:
                materials_list.append(material)
                materials.append(material)
                
            mat_id = materials_list.index(material)

            vertices = mesh.vertices
            normals = mesh.vertex_normals
            faces = mesh.faces
            uvs = mesh.visual.uv

            global_faces = faces + vertex_offset

            mesh_material_ids = np.full(len(faces), mat_id, dtype=i4)

            all_vertices.append(vertices)
            all_triangles.append(global_faces)
            all_normals.append(normals)
            all_faces.append(faces)
            all_uvs.append(uvs)
            all_material_ids.append(mesh_material_ids)

            vertex_offset += len(vertices)
        
        self.vertices = np.vstack(all_vertices).astype(f4)
        self.triangles = np.vstack(all_triangles).astype(i4)
        self.normals = np.vstack(all_normals).astype(f4)
        self.faces = np.vstack(all_faces).astype(f4)
        self.uvs = np.vstack(all_uvs).astype(f4)
        self.material_ids = np.concatenate(all_material_ids).astype(i4)
        self.materials = np.array(materials)

        self._compute_tangents()

        self.mgl_texture_arrays = {}

        self.num_triangles = len(self.triangles)
        self.num_materials = len(self.materials)
    
    def _get_texture_id(self, tex, tex_list):
        if tex.is_empty:
            return set_i4(-1)
        
        if tex not in tex_list:
            tex_list.append(tex)
            return set_i4(len(tex_list) - 1)
        
        return set_i4(tex_list.index(tex))

    # https://learnopengl.com/Advanced-Lighting/Normal-Mapping
    def _compute_tangents(self):
        vertices = self.vertices
        triangles = self.triangles
        uvs = self.uvs

        self.tangents = np.zeros_like(vertices)
        self.bitangents = np.zeros_like(vertices)

        for face in triangles:
            idx0, idx1, idx2 = face

            v0, v1, v2 = vertices[idx0], vertices[idx1], vertices[idx2]
            uv0, uv1, uv2 = uvs[idx0], uvs[idx1], uvs[idx2]

            edge1 = v1 - v0
            edge2 = v2 - v0
            delta_uv1 = uv1 - uv0
            delta_uv2 = uv2 - uv0

            det = (delta_uv1[0] * delta_uv2[1] - delta_uv2[0] * delta_uv1[1])
            
            # Prevent division by zero
            if abs(det) < 1e-6:
                continue
                
            f = 1 / det

            tangent = f * (delta_uv2[1] * edge1 - delta_uv1[1] * edge2)
            bitangent = f * (-delta_uv2[0] * edge1 + delta_uv1[0] * edge2)

            # Accumulate onto vertices
            for idx in face:
                self.tangents[idx] += tangent
                self.bitangents[idx] += bitangent
        
        # Normalize to get unit vectors
        # Add small offset to prevent division by zero
        self.tangents /= np.linalg.norm(self.tangents, axis=1, keepdims=True) + 1e-6
        self.bitangents /= np.linalg.norm(self.bitangents, axis=1, keepdims=True) + 1e-6

        # Gram-Schmidt process
        # Re-orthogonalize TBN vectors to be mutually perpendicular
        for i in range(len(self.vertices)):
            T = self.tangents[i]
            N = self.normals[i]

            # Re-orthogonalize T with respect to N
            T = T - np.dot(T, N) * N
            # Add small offset to prevent division by zero
            T /= np.linalg.norm(T) + 1e-6

            # Retrieve perpendicular vector B with the cross product of T and N
            B = np.cross(T, N)

            self.tangents[i] = T
            self.bitangents[i] = B

    def create_texture_arrays(self, ctx, width, height):
        self.texture_arrays = {}

        def build_array(tex_list, name):
            if not tex_list:
                return
            
            data = bytearray()
            for tex in tex_list:
                tex.resize(width, height)
                data.extend(tex.data)
                
            self.texture_arrays[name] = ctx.texture_array(
                size=(width, height, len(tex_list)),
                components=4,
                data=data
            )

        build_array(self.base_color_textures, "base_color")
        build_array(self.emissive_textures, "emissive")
        build_array(self.roughness_textures, "roughness")
        build_array(self.metallic_textures, "metallic")
        build_array(self.normal_textures, "normal")
        build_array(self.occlusion_textures, "occlusion")
    
    def bind_texture_arrays(
            self,
            base_color_tex_loc = 0,
            emissive_tex_loc = 1,
            roughness_tex_loc = 2,
            metallic_tex_loc = 3,
            normal_tex_loc = 4,
            occlusion_tex_loc = 5
        ):

        if "base_color" in self.texture_arrays:
            self.texture_arrays["base_color"].use(location=base_color_tex_loc)

        if "emissive" in self.texture_arrays:
            self.texture_arrays["emissive"].use(location=emissive_tex_loc)
            
        if "roughness" in self.texture_arrays:
            self.texture_arrays["roughness"].use(location=roughness_tex_loc)
            
        if "metallic" in self.texture_arrays:
            self.texture_arrays["metallic"].use(location=metallic_tex_loc)
            
        if "normal" in self.texture_arrays:
            self.texture_arrays["normal"].use(location=normal_tex_loc)
            
        if "occlusion" in self.texture_arrays:
            self.texture_arrays["occlusion"].use(location=occlusion_tex_loc)
