import trimesh
import numpy as np

from src.dtypes import *


class Scene:
    def __init__(self, file_path):
        scene = trimesh.load(file_path)

        all_vertices = []
        all_triangles = []
        all_uvs = []
        all_material_ids = []
        
        materials_list = []
        material_colors = []

        vertex_offset = 0

        # Iterate through all scene geometries
        for node_name in scene.graph.nodes_geometry:
            transform, geometry_name = scene.graph[node_name]
            mesh = scene.geometry[geometry_name]

            # Convert mesh data to world space
            mesh.apply_transform(transform)

            current_material = mesh.visual.material
            
            if current_material not in materials_list:
                materials_list.append(current_material)
                if hasattr(current_material, "baseColorFactor") and current_material.baseColorFactor is not None:
                    raw_color = current_material.baseColorFactor[:3]
                elif hasattr(current_material, "main_color") and current_material.main_color is not None:
                    raw_color = np.array(current_material.main_color[:3], dtype=np.float32)
                    if raw_color.max() > 1.0:
                        raw_color /= 255.0
                else:
                    # Set default color
                    raw_color = np.array([0.8, 0.8, 0.8], dtype=np.float32)
                material_colors.append(raw_color)
                
            mat_id = materials_list.index(current_material)

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
        self.material_colors = np.vstack(material_colors).astype(f4)

        self.num_triangles = len(self.triangles)
