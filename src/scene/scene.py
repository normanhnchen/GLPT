import trimesh
import numpy as np
import pygltflib
import glm
from pathlib import Path

from src.settings import settings
from src.dtypes import *
from src.buffers import light_dtype
from src.scene.materials import Material


class Scene:
    def __init__(self, scene_path):
        self.scene_path = scene_path
        self.scene_name = Path(scene_path).stem

    def build(self):
        scene = trimesh.load(self.scene_path)

        all_extensions, all_lights = self._get_extensions()

        all_vertices = []
        all_triangles = []
        all_centroids = []
        all_normals = []
        all_uvs = []
        all_material_ids = []
        
        material_dict = {}
        materials = []

        self.base_color_textures = []
        self.emissive_textures = []
        self.roughness_textures = []
        self.metallic_textures = []
        self.normal_textures = []
        self.occlusion_textures = []

        vertex_offset = 0

        # Iterate through all scene geometries
        for _, node_name in enumerate(scene.graph.nodes_geometry):
            transform, geometry_name = scene.graph[node_name]
            mesh = scene.geometry[geometry_name]

            # Convert mesh data to world space
            mesh.apply_transform(transform)

            if hasattr(mesh.visual, "material") and mesh.visual.material is not None:
                trimesh_material = mesh.visual.material
            else:
                trimesh_material = None
            
            mat_name = getattr(trimesh_material, "name", None)
            mat_extensions = all_extensions.get(mat_name)

            mat_key = mat_name if mat_name is not None else id(trimesh_material)
        
            if mat_key not in material_dict:
                material = Material(trimesh_material, mat_extensions)

                material.base_color_tex_id = self._get_texture_id(material.base_color_tex, self.base_color_textures)
                material.emissive_tex_id = self._get_texture_id(material.emissive_tex, self.emissive_textures)
                material.roughness_tex_id = self._get_texture_id(material.roughness_tex, self.roughness_textures)
                material.metallic_tex_id = self._get_texture_id(material.metallic_tex, self.metallic_textures)
                material.normal_tex_id = self._get_texture_id(material.normal_tex, self.normal_textures)
                material.occlusion_tex_id = self._get_texture_id(material.occlusion_tex, self.occlusion_textures)

                material_dict[mat_key] = material
                materials.append(material)
                
            mat_id = materials.index(material_dict[mat_key])

            vertices = mesh.vertices
            centroids = mesh.triangles_center
            normals = mesh.vertex_normals
            faces = mesh.faces
            if hasattr(mesh.visual, "uv") and mesh.visual.uv is not None and len(mesh.visual.uv) == len(vertices):
                uvs = mesh.visual.uv
                # Flip uvs
                # glTF defines uvs increasing downwards
                # OpenGL defines uvs increasing upwards
                uvs[:, 1] = 1.0 - uvs[:, 1]
            else:
                uvs = np.zeros((len(vertices), 2), dtype=f4)

            global_faces = faces + vertex_offset

            mesh_material_ids = np.full(len(faces), mat_id, dtype=i4)

            all_vertices.append(vertices)
            all_triangles.append(global_faces)
            all_centroids.append(centroids)
            all_normals.append(normals)
            all_uvs.append(uvs)
            all_material_ids.append(mesh_material_ids)

            vertex_offset += len(vertices)
        
        self.vertices = np.vstack(all_vertices).astype(f4)
        self.triangles = np.vstack(all_triangles).astype(i4)
        self.centroids = np.concatenate(all_centroids).astype(f4)
        self.normals = np.vstack(all_normals).astype(f4)
        self.uvs = np.vstack(all_uvs).astype(f4)
        self.material_ids = np.concatenate(all_material_ids).astype(i4)
        self.materials = np.array(materials)

        self._compute_tangents()

        def to_array(tex_list):
            width, height = settings.rendering.texture_size
            if not tex_list:
                return np.zeros((0, height, width, 4), dtype=np.uint8)
            arr = np.zeros((len(tex_list), height, width, 4), dtype=np.uint8)
            for i, tex in enumerate(tex_list):
                arr[i] = tex.image
            return arr
        
        self.base_color_textures = to_array(self.base_color_textures)
        self.emissive_textures = to_array(self.emissive_textures)
        self.roughness_textures = to_array(self.roughness_textures)
        self.metallic_textures = to_array(self.metallic_textures)
        self.normal_textures = to_array(self.normal_textures)
        self.occlusion_textures = to_array(self.occlusion_textures)

        self.num_triangles = len(self.triangles)
        self.num_materials = len(self.materials)

        self.lights = all_lights

        self.hdri = None

        self.num_lights = len(self.lights)

        self._find_emissive_triangles()
        self._find_finite_lights()

        scene_min = np.min(self.vertices, axis=0)
        scene_max = np.max(self.vertices, axis=0)
        self.extent = np.linalg.norm(scene_max - scene_min)

        self.bvh = None
        self.num_bvh_nodes = None

    def _calculate_triangle_areas(self, vertices, indices):
        v0 = vertices[indices][:, 0]
        v1 = vertices[indices][:, 1]
        v2 = vertices[indices][:, 2]

        e1 = v1 - v0
        e2 = v2 - v0

        cross = np.cross(e1, e2)

        areas = 0.5 * np.linalg.norm(cross, axis=1)
        return areas

    def _find_emissive_triangles(self):
        mat_has_emission = np.array([bool(mat.has_emission) for mat in self.materials])
        triangle_has_emission = mat_has_emission[self.material_ids]
        self.emissive_triangle_indices = np.where(triangle_has_emission)[0]
        self.num_emissive_triangles = len(self.emissive_triangle_indices)
        emissive_triangle_areas = self._calculate_triangle_areas(
            self.vertices,
            self.triangles[self.emissive_triangle_indices]
        )
        self.triangle_areas = np.full(self.num_triangles, -1, dtype=f4)
        self.triangle_areas[self.emissive_triangle_indices] = emissive_triangle_areas

        mat_emissive_rgb = np.array([mat.emissive_color * mat.emissive_strength for mat in self.materials])
        luminance = mat_emissive_rgb @ np.array([0.2126, 0.7152, 0.0722])
        power = luminance[self.material_ids[self.emissive_triangle_indices]] * emissive_triangle_areas

        self.area_light_p, self.area_light_q, self.area_light_alias = self._build_alias_table(power)

    def _find_finite_lights(self):
        light_is_finite = self.lights["type"] != 1
        finite_indices = np.where(light_is_finite)[0]

        self.num_finite_lights = len(finite_indices)

        if self.num_finite_lights == 0:
            self.finite_light_indices = np.zeros(0, dtype=i4)
            self.finite_light_p = np.zeros(0, dtype=f4)
            self.finite_light_q = np.zeros(0, dtype=f4)
            self.finite_light_alias = np.zeros(0, dtype=i4)
            return

        col = self.lights["col"][finite_indices]
        intensity = self.lights["intensity"][finite_indices] * settings.lumens_to_watts
        luminance = (col[:, 0] * 0.2126 + col[:, 1] * 0.7152 + col[:, 2] * 0.0722) * intensity

        # https://www.pbr-book.org/3ed-2018/Light_Sources/Point_Lights#
        # Power emitted by the light source
        # Found by integrating over the sphere of directions
        power = 4 * np.pi * luminance

        p, q, alias = self._build_alias_table(power)

        self.finite_light_indices = finite_indices.astype(i4)
        self.finite_light_p = p
        self.finite_light_q = q
        self.finite_light_alias = alias
    
    # See 7.4 Power Sampling
    def _build_alias_table(self, weights):
        n = len(weights)
        weights = np.asarray(weights, dtype=np.float64)
        total = weights.sum()

        p = np.zeros(n, dtype=np.float64)
        q = np.zeros(n, dtype=np.float64)
        alias = np.full(n, -1, dtype=np.int32)

        p[:] = weights / total

        under = []
        over = []
        for i in range(n):
            p_hat = p[i] * n
            if (p_hat < 1):
                under.append((p_hat, i))
            else:
                over.append((p_hat, i))

        while under and over:
            un_p_hat, un_i = under.pop()
            ov_p_hat, ov_i = over.pop()

            q[un_i] = un_p_hat
            alias[un_i] = ov_i

            p_excess = un_p_hat + ov_p_hat - 1
            if (p_excess < 1):
                under.append((p_excess, ov_i))
            else:
                over.append((p_excess, ov_i))

        for _, i in over:
            q[i] = 1
            alias[i] = -1
        for _, i in under:
            q[i] = 1
            alias[i] = -1

        return p.astype(f4), q.astype(f4), alias
    
    # Logic for parsing GLB files assisted by AI
    def _get_extensions(self):
        gltf = pygltflib.GLTF2().load(self.scene_path)

        material_extensions = {}
        for mat in gltf.materials:
            name = mat.name
            exts = mat.extensions
            if name and exts:
                material_extensions[name] = exts
        
        lights = self._build_lights(gltf)
        
        lights = np.array(lights, dtype=light_dtype)
        
        return material_extensions, lights

    def _build_lights(self, gltf):
        extensions = gltf.extensions or {}
        lights_ext = extensions.get("KHR_lights_punctual", {})
        raw_lights = lights_ext.get("lights", [])

        lights = []
        for node in gltf.nodes:
            node_ext = (node.extensions or {}).get("KHR_lights_punctual")
            if not node_ext:
                continue

            light_def = raw_lights[node_ext["light"]]

            t = node.translation or [0, 0, 0]
            r = node.rotation or [0, 0, 0, 1]

            # Convert from a quaternion direction to a cartesian direction
            position  = glm.vec3(*t)
            direction = glm.normalize(glm.vec3(
                glm.mat4_cast(glm.quat(r[3], r[0], r[1], r[2])) * glm.vec4(0, 0, -1, 0)
            ))

            light_type_str = light_def.get("type", "point")
            type_id = {"point": 0, "directional": 1, "spot": 2}[light_type_str]
            spot = light_def.get("spot", {})

            intensity = light_def.get("intensity", 1) * settings.lumens_to_watts

            lights.append((
                light_def.get("color", [1, 1, 1]),
                type_id,
                list(position),
                intensity,
                list(direction),
                light_def.get("range", 0),
                1 if spot else 0,
                spot.get("innerConeAngle", 0),
                spot.get("outerConeAngle", 0),
                0
            ))

        return lights
        
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
        
        v0 = vertices[triangles[:, 0]]
        v1 = vertices[triangles[:, 1]]
        v2 = vertices[triangles[:, 2]]
        uv0 = uvs[triangles[:, 0]]
        uv1 = uvs[triangles[:, 1]]
        uv2 = uvs[triangles[:, 2]]

        edge1 = v1 - v0
        edge2 = v2 - v0
        delta_uv1 = uv1 - uv0
        delta_uv2 = uv2 - uv0

        det = delta_uv1[:, 0] * delta_uv2[:, 1] - delta_uv2[:, 0] * delta_uv1[:, 1]

        # Find the inverse determinahnt
        # Prevent division by zero
        f = np.divide(1, det, out=np.zeros_like(det), where=np.abs(det) > 1e-6)

        tangent = f[:, None] * (delta_uv2[:, 1, None] * edge1 - delta_uv1[:, 1, None] * edge2)
        bitangent = f[:, None] * (-delta_uv2[:, 0, None] * edge1 + delta_uv1[:, 0, None] * edge2)

        self.tangents = np.zeros_like(self.vertices)
        self.bitangents = np.zeros_like(self.vertices)

        # Acculumate onto vertices
        np.add.at(self.tangents, self.triangles.flatten(), np.repeat(tangent, 3, axis=0))
        np.add.at(self.bitangents, self.triangles.flatten(), np.repeat(bitangent, 3, axis=0))
        
        # Normalize to get unit vectors
        # Add small offset to prevent division by zero
        self.tangents /= np.linalg.norm(self.tangents, axis=1, keepdims=True) + 1e-6
        self.bitangents /= np.linalg.norm(self.bitangents, axis=1, keepdims=True) + 1e-6

        # Gram-Schmidt process
        # Re-orthogonalize TBN vectors to be mutually perpendicular

        # Re-orthogonalize T with respect to N
        self.tangents -= np.sum(self.tangents * self.normals, axis=1, keepdims=True) * self.normals
        # Add small offset to prevent division by zero
        self.tangents /= np.linalg.norm(self.tangents, axis=1, keepdims=True) + 1e-6

        # Retrieve perpendicular vector B with the cross product of T and N
        self.bitangents = np.cross(self.tangents, self.normals)

    def strip_material_images(self):
        for mat in self.materials:
            for tex in mat.textures:
                tex.image = None

    def create_texture_arrays(self, ctx):
        self.texture_arrays = {}

        def build_array(tex_list, name):
            if tex_list is None:
                return
            
            data = bytearray()
            for img in tex_list:
                data.extend(img.tobytes())
            
            width, height = settings.rendering.texture_size
                
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
        
    def release_all(self):
        for tex_array in self.texture_arrays.keys():
            self.texture_arrays[tex_array].release()
        if self.hdri is not None:
            self.hdri.release()

    def snapshot_original_materials(self):
        """
        Create a snapshot of the original materials before scrambling.
        Only used for AI training.
        """
        
        for mat in self.materials:
            mat.snapshot_original()

    # See 9.4 Rendering
    def scramble_materials(self):
        """
        Randomize all scene material properties and textures.
        Only used for AI training.
        """

        num_base_color = len(self.base_color_textures)
        num_roughness = len(self.roughness_textures)
        num_metallic = len(self.metallic_textures)
        num_normal = len(self.normal_textures)

        for mat in self.materials:
            mat.scramble()

            # Base color texture randomization
            if num_base_color > 0:
                if np.random.rand() < 0.5:
                    mat.base_color_tex_id = set_i4(np.random.randint(0, num_base_color))
                    mat.has_base_color_tex = set_i4(1)
                else:
                    mat.base_color_tex_id = set_i4(-1)
                    mat.has_base_color_tex = set_i4(0)

            # Roughness texture randomization
            if num_roughness > 0:
                if np.random.rand() < 0.5: 
                    mat.roughness_tex_id = set_i4(np.random.randint(0, num_roughness))
                    mat.has_roughness_tex = set_i4(1)
                else:
                    mat.roughness_tex_id = set_i4(-1)
                    mat.has_roughness_tex = set_i4(0)

            # Metallic texture randomization
            if num_metallic > 0:
                if np.random.rand() < 0.5: 
                    mat.metallic_tex_id = set_i4(np.random.randint(0, num_metallic))
                    mat.has_metallic_tex = set_i4(1)
                else:
                    mat.metallic_tex_id = set_i4(-1)
                    mat.has_metallic_tex = set_i4(0)

            # Normal map randomization
            if num_normal > 0:
                if np.random.rand() < 0.5:
                    mat.normal_tex_id = set_i4(np.random.randint(0, num_normal))
                    mat.has_normal_tex = set_i4(1)
                else:
                    mat.normal_tex_id = set_i4(-1)
                    mat.has_normal_tex = set_i4(0)

        # Rebuild alias tables for light sampling based on newly scrambled emission values
        self._find_emissive_triangles()

