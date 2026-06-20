import trimesh
import numpy as np

from src.dtypes import *


class Material:
    def __init__(self, trimesh_material):
        if hasattr(trimesh_material, "baseColorFactor") and trimesh_material.baseColorFactor is not None:
            self.base_color = self._color_to_vec3(trimesh_material.baseColorFactor)
        else:
            # Set default color
            self.base_color = np.array([0.8, 0.8, 0.8], dtype=f4)
        
        if hasattr(trimesh_material, "emissiveFactor") and trimesh_material.emissiveFactor is not None:
            self.emissive_color = self._color_to_vec3(trimesh_material.emissiveFactor)
            self.has_emission = set_i4(1)
        else:
            # Set to no emission 
            self.emissive_color = np.array([-1, -1, -1], dtype=f4)
            self.has_emission = set_i4(0)

        if hasattr(trimesh_material, "roughnessFactor") and trimesh_material.roughnessFactor is not None:
            self.roughness = set_f4(trimesh_material.roughnessFactor)
        else:
            # Set default roughness
            self.roughness = set_f4(0.8)
    
    def _color_to_vec3(self, color):
        color = np.asarray(color[:3], dtype=f4)
        if np.max(color) > 1.0:
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

        vertex_offset = 0

        # Iterate through all scene geometries
        for node_name in scene.graph.nodes_geometry:
            transform, geometry_name = scene.graph[node_name]
            mesh = scene.geometry[geometry_name]

            # Convert mesh data to world space
            mesh.apply_transform(transform)

            trimesh_material = mesh.visual.material
            material = Material(trimesh_material)
            
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
