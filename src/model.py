import trimesh
import numpy as np

from src.dtypes import *


class Material:
    def __init__(self, trimesh_material):
        self.alpha_mode = getattr(trimesh_material, "alphaMode", "OPAQUE")
        self.alpha_cutoff = getattr(trimesh_material, "alphaCutoff", 0.5)
        self.double_sided = bool(getattr(trimesh_material, "doubleSided", False))

        base_color = getattr(trimesh_material, "baseColorFactor", None)
        emissive_color = getattr(trimesh_material, "emissiveFactor", None)
        roughness = getattr(trimesh_material, "roughnessFactor", None)
        metallic = getattr(trimesh_material, "metallicFactor", None)

        self.base_color_texture = getattr(trimesh_material, "baseColorTexture", None)
        self.emissive_texture = getattr(trimesh_material, "emissiveTexture", None)
        self.normal_texture = getattr(trimesh_material, "normalTexture", None)
        self.occlusion_texture = getattr(trimesh_material, "occlusionTexture", None)

        metallic_roughness_texture = getattr(trimesh_material, "metallicRoughnessTexture", None)
        
        self.roughness_texture = None
        self.metallic_texture = None

        # Unpack metallic roughness texture
        if metallic_roughness_texture is not None:
            r, g, b = metallic_roughness_texture.split()
            self.roughness_texture = g
            self.metallic_texture = b

        if base_color is not None:
            self.base_color = self._color_to_vec3(trimesh_material.baseColorFactor)
        else:
            # Set default color
            self.base_color = np.array([0.8, 0.8, 0.8], dtype=f4)
        
        if emissive_color is not None:
            self.emissive_color = self._color_to_vec3(trimesh_material.emissiveFactor)
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
        self.has_base_color_tex = set_i4(1) if self.base_color_texture is not None else set_i4(0)
        self.has_emissive_tex = set_i4(1) if self.emissive_texture is not None else set_i4(0)
        self.has_roughness_tex = set_i4(1) if self.roughness_texture is not None else set_i4(0)
        self.has_metallic_tex = set_i4(1) if self.metallic_texture is not None else set_i4(0)
        self.has_normal_tex = set_i4(1) if self.normal_texture is not None else set_i4(0)
        self.has_occlusion_tex = set_i4(1) if self.occlusion_texture is not None else set_i4(0) 

        self.base_color_tex_id = set_i4(-1)
        self.emissive_tex_id = set_i4(-1)
        self.roughness_tex_id = set_i4(-1)
        self.metallic_tex_id = set_i4(-1)
        self.normal_tex_id = set_i4(-1)
        self.occlusion_tex_id = set_i4(-1)
    
    def _color_to_vec3(self, color):
        color = np.asarray(color[:3], dtype=f4)
        if np.max(color) > 1.0:
            # Convert to float rgb
            color = color / 255
        return color


class Scene:
    def __init__(self, file_path):
        scene = trimesh.load(file_path)

        all_vertices = []
        all_triangles = []
        all_uvs = []
        all_material_ids = []
        
        materials_list = []
        materials = []

        self.textures = []

        vertex_offset = 0

        # Iterate through all scene geometries
        for node_name in scene.graph.nodes_geometry:
            transform, geometry_name = scene.graph[node_name]
            mesh = scene.geometry[geometry_name]

            # Convert mesh data to world space
            mesh.apply_transform(transform)

            trimesh_material = mesh.visual.material
            material = Material(trimesh_material)

            material.base_color_tex_id = self._get_texture_id(material.base_color_texture)
            material.emissive_tex_id = self._get_texture_id(material.emissive_texture)
            material.roughness_tex_id = self._get_texture_id(material.roughness_texture)
            material.metallic_tex_id = self._get_texture_id(material.metallic_texture)
            material.normal_tex_id = self._get_texture_id(material.normal_texture)
            material.occlusion_tex_id = self._get_texture_id(material.occlusion_texture)
            
            if material not in materials_list:
                materials_list.append(material)
                materials.append(material)
                
            mat_id = materials_list.index(material)

            vertices = mesh.vertices
            faces = mesh.faces
            uvs = mesh.visual.uv

            global_faces = faces + vertex_offset

            mesh_material_ids = np.full(len(faces), mat_id, dtype=i4)

            all_vertices.append(vertices)
            all_triangles.append(global_faces)
            all_uvs.append(uvs)
            all_material_ids.append(mesh_material_ids)

            vertex_offset += len(vertices)
        
        self.vertices = np.vstack(all_vertices).astype(f4)
        self.triangles = np.vstack(all_triangles).astype(i4)
        self.uvs = np.vstack(all_uvs).astype(f4)
        self.material_ids = np.concatenate(all_material_ids).astype(i4)
        self.materials = np.array(materials)

        self.num_triangles = len(self.triangles)
        self.num_materials = len(self.materials)
    
    def _get_texture_id(self, tex):
        if tex is None:
            return set_i4(-1)
        
        if tex not in self.textures:
            self.textures.append(tex)
        
        return set_i4(self.textures.index(tex))
