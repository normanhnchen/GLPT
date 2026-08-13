import trimesh
import numpy as np
import cv2
import pygltflib
import glm
import time
from pathlib import Path
import hashlib
import os

from src.settings import *
from src.dtypes import *
from src.bvh import *
from src.buffers import *


def _get_file_fingerprint(path, chunk_size=65536, max_chunks=32, digest_size=16):
    size = os.path.getsize(path)
    h = hashlib.blake2b(digest_size=digest_size)
    h.update(str(size).encode())

    # Apply ceiling division
    num_chunks = min(max_chunks, -(-size // chunk_size))

    with open(path, "rb") as f:
        if num_chunks * chunk_size >= size:
            # File is small enough; read
            h.update(f.read())
        else:
            stride = (size - chunk_size) / (num_chunks - 1) if num_chunks > 1 else 0
            for i in range(num_chunks):
                offset = int(i * stride)
                f.seek(offset)
                h.update(f.read(chunk_size))

    return h.hexdigest()


def remove_stale_cache(scenes_dir, cache_dir):
    scenes_dir = Path(scenes_dir).resolve()
    cache_dir = Path(cache_dir).resolve()

    valid_codes = []
    for scene_file in scenes_dir.rglob("*"):
        if scene_file.is_file():
            rel_path = scene_file.relative_to(ROOT_DIR)
            
            name = str(rel_path.parent / rel_path.stem).replace("/", "_").replace("\\", "_")
            fingerprint = _get_file_fingerprint(scene_file)

            valid_codes.append(f"{name}_{fingerprint}")

    for cache_file in cache_dir.glob("*"):
        stem = cache_file.stem
        for prefix in ("scene_", "bvh_"):
            if stem.startswith(prefix):
                code = stem[len(prefix):]
                break

        else:
            continue

        if code not in valid_codes:
            cache_file.unlink()


def get_cache_path(path, cache_dir, type):
    abs_path = Path(path).resolve()
    abs_cache_dir = Path(cache_dir).resolve()

    rel_path = abs_path.relative_to(ROOT_DIR)

    cache_name = str(rel_path.parent / rel_path.stem).replace("/", "_").replace("\\", "_")
    fingerprint = _get_file_fingerprint(abs_path)

    if type == "scene":
        return abs_cache_dir / f"{type}_{cache_name}_{fingerprint}"
    elif type == "bvh":
        return abs_cache_dir / f"{type}_{cache_name}_{fingerprint}"


class Texture:
    def __init__(self, pil_image):
        if pil_image is None:
            self.is_empty = True
            self.data = None
            return
            
        self.is_empty = False
        self.image = pil_image.convert("RGBA")
    
    def resize(self, width, height):
        if self.is_empty:
            return
        self.image = self.image.resize((width, height)).convert("RGBA")


class Material:
    def __init__(self, trimesh_material, extensions):
        alpha_mode = getattr(trimesh_material, "alphaMode", "OPAQUE")
        if alpha_mode == "MASK":
            self.alpha_mode = 1
        elif alpha_mode == "BLEND":
            self.alpha_mode = 2
        else: # OPAQUE
            self.alpha_mode = 0
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

        width, height = render_settings.texture_size
        for tex in self.textures:
            tex.resize(width, height)

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
            self.emissive_color = np.array([0, 0, 0], dtype=f4)
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
        
        # glTF extensions
        # ---------------
        extensions = extensions or {}

        KHR_materials_emissive_strength = extensions.get("KHR_materials_emissive_strength")
        if KHR_materials_emissive_strength:
            self.emissive_strength = KHR_materials_emissive_strength["emissiveStrength"]
        else:
            self.emissive_strength = set_f4(0)

        KHR_materials_transmission = extensions.get("KHR_materials_transmission")
        if KHR_materials_transmission:
            self.transmission = KHR_materials_transmission["transmissionFactor"]
        else:
            self.transmission = set_f4(0)

        KHR_materials_ior = extensions.get("KHR_materials_ior")
        if KHR_materials_ior:
            self.ior = KHR_materials_ior["ior"]
        else:
            self.ior = set_f4(1.5)

    def _to_float_rgb(self, color):
        color = np.asarray(color, dtype=f4)
        if np.max(color) > 1.0:
            # Convert to float RGB
            return color / 255
        return color

    def snapshot_original(self):
        """
        Create a snapshot of the original material before scrambling.
        Only used for AI training.
        """

        self._original_base_color = self.base_color.copy()
        self._original_roughness = float(self.roughness)
        self._original_metallic = float(self.metallic)
        self._original_emissive_color = self.emissive_color.copy()
        self._original_emissive_strength = float(self.emissive_strength)
        self._original_has_emission = bool(self.has_emission)
        self._original_transmission = float(self.transmission)
        self._original_ior = float(self.ior)
        self._original_alpha_mode = int(self.alpha_mode)

    def _reset(self):
        """
        Restore this material to its original (un-scrambled) values.
        Only used for AI training.
        """

        self.base_color = self._original_base_color.copy()
        self.roughness = set_f4(self._original_roughness)
        self.metallic = set_f4(self._original_metallic)
        self.emissive_color = self._original_emissive_color.copy()
        self.emissive_strength = self._original_emissive_strength
        self.has_emission = set_i4(1 if self._original_has_emission else 0)
        self.transmission = set_f4(self._original_transmission)
        self.ior = set_f4(self._original_ior)
        self.alpha_mode = set_f4(self._original_alpha_mode)

    def scramble(self):
        """
        Randomize material properties.
        Only used for AI training.
        """

        self._reset()

        self.base_color[:3] = np.random.uniform(0, 1, 3).astype(f4)
        if np.random.rand() < 0.1:
            self.base_color[-1] = set_f4(np.random.uniform(0.1, 0.9))
            self.alpha_mode = 2 # BLEND
        
        self.roughness = set_f4(np.random.uniform(0, 1))
        self.metallic = set_f4(np.random.uniform(0, 1))

        if self._original_has_emission:
            self.emissive_color = np.random.uniform(0, 1, 3).astype(f4)
            self.emissive_strength *= set_f4(np.random.uniform(0.1, 10))

        if np.random.rand() < 0.3:
            self.transmission = set_f4(np.random.uniform(0, 1))
            self.ior = set_f4(np.random.uniform(1, 2.4))


class HDRI:
    def __init__(self, hdri_path):
        img = cv2.imread(hdri_path, cv2.IMREAD_UNCHANGED)
        # Convert from OpenCV default format of BGR color to RGB color
        self.img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        self.height, self.width, self.channels = self.img.shape
        self.img_bytes = self.img.tobytes()

        self.hdri_tex = None

        self._build_hdri_distribution()

    # https://pbr-book.org/3ed-2018/Light_Transport_I_Surface_Reflection/Sampling_Light_Sources#InfiniteAreaLights
    def _build_hdri_distribution(self):
        img = self.img.astype(np.float64)
        luminance = img[:, :, 0] * 0.2126 + img[:, :, 1] * 0.7152 + img[:, :, 2] * 0.0722

        # Adjust for equirectangular map spherical distortion
        theta = (np.arange(self.height) + 0.5) / self.height * np.pi
        sin_theta = np.sin(theta)[:, None]
        weighted = luminance * sin_theta

        # Build the CDFs
        # --------------
        # Marginal distribution over rows
        row_sums = weighted.sum(axis=1)
        row_cdf = np.cumsum(row_sums)
        row_cdf /= row_cdf[-1]

        # Conditional distribution over column given a row
        col_cdf = np.cumsum(weighted, axis=1)
        col_cdf /= col_cdf[:, -1:]

        self.row_cdf = row_cdf.astype(f4)
        self.col_cdf = col_cdf.astype(f4)
    
    def bind_img(self, ctx, loc):
        self.hdri_tex = ctx.texture(
            (self.width, self.height),
            self.channels,
            self.img_bytes,
            dtype=f4
            )
        self.hdri_tex.use(location=loc)

    def bind_cdfs(self, ctx, row_loc, col_loc):
        row_height = self.row_cdf.shape[0]
        col_height, col_width = self.col_cdf.shape

        self.row_cdf_tex = ctx.texture(
            (1, row_height),
            1,
            self.row_cdf.tobytes(),
            dtype=f4
        )
        self.col_cdf_tex = ctx.texture(
            (col_width, col_height),
            1,
            self.col_cdf.tobytes(),
            dtype=f4
        )

        self.row_cdf_tex.use(location=row_loc)
        self.col_cdf_tex.use(location=col_loc)
    
    def release(self):
        if self.hdri_tex is not None:
            self.hdri_tex.release()

    def snapshot_original(self):
        """
        Create a snapshot of the original image before scrambling.
        Only used for AI training.
        """
        
        self._original_img = self.img.copy()

    def _reset(self):
        """
        Restore this HDRI to its original (un-scrambled) image.
        Only used for AI training.
        """

        self.img = self._original_img.copy()
        self.img_bytes = self.img.tobytes()

    def scramble(self):
        """
        Randomize HDRI rotation, emissive strength, and color.
        Only used for AI training.
        """

        self._reset()

        random_rot = np.random.uniform(0, 2 * np.pi, 3).astype(f4)
        random_exposure_factor = set_f4(np.random.uniform(0.1, 10))
        random_color_factor = np.random.uniform(0, 2, 3).astype(f4)

        u = (np.arange(self.width) + 0.5) / self.width
        v = (np.arange(self.height) + 0.5) / self.height

        theta, phi = self._uv_to_spherical(u, v)
        x, y, z = self._spherical_to_cartesian(theta, phi)

        rot_mat = self._rotation_matrix(*random_rot)
        # Transform the matrix since numpy is row-major, the matrix is column-major
        rotated = np.stack([x, y, z], axis=-1) @ rot_mat.T

        x = rotated[..., 0]
        y = rotated[..., 1]
        z = rotated[..., 2]

        theta, phi = self._cartesian_to_spherical(x, y, z)

        u, v = self._spherical_to_uv(theta, phi)
        x_map = (u * self.width).astype(f4)
        y_map = (v * self.height).astype(f4)

        rotated_img = cv2.remap(
            self._original_img,
            x_map, y_map,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_WRAP,
        )

        self.img = rotated_img * random_exposure_factor * random_color_factor
        self.img_bytes = self.img.tobytes()

        # Rebuild alias tables based on the new HDRI
        self._build_hdri_distribution()

    def _uv_to_spherical(self, u, v):
        # Azimuthal [-π, π]
        phi = (u - 0.5) * 2 * np.pi
        # Zenith [0, π]
        theta = v * np.pi

        return theta, phi

    def _spherical_to_cartesian(self, theta, phi):
        theta_grid, phi_grid = np.meshgrid(theta, phi, indexing="ij")

        x = np.sin(theta_grid) * np.cos(phi_grid)
        y = np.cos(theta_grid)
        z = np.sin(theta_grid) * np.sin(phi_grid)

        return x, y, z

    def _cartesian_to_spherical(self, x, y, z):
        # Prevent floating point error
        y = np.clip(y, -1, 1)

        theta = np.arccos(y)
        phi = np.arctan2(z, x)

        return theta, phi

    def _rotation_matrix(self, pitch_rad, yaw_rad, roll_rad):
        p = pitch_rad
        y = yaw_rad
        r = roll_rad

        R_pitch = np.array([
            [1, 0, 0],
            [0, np.cos(p), -np.sin(p)],
            [0, np.sin(p), np.cos(p)]
        ])

        R_roll = np.array([
            [np.cos(r), -np.sin(r), 0],
            [np.sin(r), np.cos(r), 0],
            [0, 0, 1]
        ])

        R_yaw = np.array([
            [np.cos(y), 0, np.sin(y)],
            [0, 1, 0],
            [-np.sin(y), 0, np.cos(y)]
        ])

        return R_yaw @ R_pitch @ R_roll

    def _spherical_to_uv(self, theta, phi):
        u = phi / (2 * np.pi) + 0.5
        v = theta / np.pi

        return u, v

    def update_img(self):
        """
        Update the HDRI image buffer after scrambling.
        Only used for AI training.
        """

        self.hdri_tex.write(self.img_bytes)

    def update_cdfs(self):
        """
        Update the CDF buffers after scrambling.
        Only used for AI training.
        """
        
        self.row_cdf_tex.write(self.row_cdf.tobytes())
        self.col_cdf_tex.write(self.col_cdf.tobytes())


class Scene:
    def __init__(self, scene_path):
        self.scene_path = scene_path
        self.scene_name = Path(scene_path).stem

        self.scene_cache_path = get_cache_path(scene_path, file_paths.scene_cache, "scene")
        self.bvh_cache_path = get_cache_path(scene_path, file_paths.bvh_cache, "bvh")

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
            width, height = render_settings.texture_size
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
        intensity = self.lights["intensity"][finite_indices] * LUMENS_TO_WATTS
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
    
    # https://pbr-book.org/4ed/Sampling_Algorithms/The_Alias_Method#AliasTable
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
    
    def build_bvh(self):
        try:
            # Note: numpy adds the file suffix automatically
            cache_path = get_cache_path(self.scene_path, file_paths.bvh_cache, "bvh").with_suffix(".npz")

            self.bvh = load_bvh_data(cache_path)
            self.num_bvh_nodes = self.bvh.nodes_used

            print("Loaded BVH from cache")
        except:
            start_time = time.perf_counter()
            print("Building BVH...")

            bvh = BVH(self)
            self.bvh = bvh
            self.num_bvh_nodes = self.bvh.nodes_used

            end_time = time.perf_counter()
            print(f"BVH built in {end_time - start_time:.4f}s")

            save_bvh_data(bvh, self.bvh_cache_path)
            
            print("BVH saved to cache")
    
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

            intensity = light_def.get("intensity", 1) * LUMENS_TO_WATTS

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
            
            width, height = render_settings.texture_size
                
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
    

def save_bvh_data(bvh, cache_path):
    np.savez_compressed(
        cache_path,
        aabb_mins=bvh.aabb_mins,
        aabb_maxs=bvh.aabb_maxs,
        left_child_indices=bvh.left_child_indices,
        right_child_indices=bvh.right_child_indices,
        first_tri_indices=bvh.first_tri_indices,
        tri_counts=bvh.tri_counts,
        is_leafs=bvh.is_leafs,
        depths=bvh.depths,
        tri_indices=bvh.tri_indices,
        nodes_used=bvh.nodes_used,
        max_depth=bvh.max_depth,
    )


def load_bvh_data(cache_path):
    data = np.load(cache_path)

    # Skip __init__ since it excepts a Scene object to build from
    bvh = BVH.__new__(BVH)

    bvh.aabb_mins = data["aabb_mins"]
    bvh.aabb_maxs = data["aabb_maxs"]
    bvh.left_child_indices = data["left_child_indices"]
    bvh.right_child_indices = data["right_child_indices"]
    bvh.first_tri_indices = data["first_tri_indices"]
    bvh.tri_counts = data["tri_counts"]
    bvh.is_leafs = data["is_leafs"]
    bvh.depths = data["depths"]
    bvh.tri_indices = data["tri_indices"]
    bvh.nodes_used = int(data["nodes_used"])
    bvh.max_depth = int(data["max_depth"])

    return bvh


def save_scene_data(scene, cache_path):
    # Unduplicate material textures by stripping texture images
    scene.strip_material_images()

    np.savez_compressed(
        cache_path,
        vertices=scene.vertices,
        triangles=scene.triangles,
        centroids=scene.centroids,
        normals=scene.normals,
        uvs=scene.uvs,
        tangents=scene.tangents,
        bitangents=scene.bitangents,
        material_ids=scene.material_ids,
        extent=scene.extent,
        lights=scene.lights,
        materials=scene.materials,
        base_color_textures=scene.base_color_textures,
        emissive_textures=scene.emissive_textures,
        roughness_textures=scene.roughness_textures,
        metallic_textures=scene.metallic_textures,
        normal_textures=scene.normal_textures,
        occlusion_textures=scene.occlusion_textures,
        emissive_triangle_indices=scene.emissive_triangle_indices,
        area_light_q=scene.area_light_q,
        area_light_p=scene.area_light_p,
        area_light_alias=scene.area_light_alias,
        triangle_areas=scene.triangle_areas,
        finite_light_indices=scene.finite_light_indices,
        finite_light_q=scene.finite_light_q,
        finite_light_p=scene.finite_light_p,
        finite_light_alias=scene.finite_light_alias
    )


def load_scene_data(scene, cache_path):
    # allow_pickle=True because of the Material objects in scene.materials
    data = np.load(cache_path, allow_pickle=True)

    scene.vertices = data["vertices"]
    scene.triangles = data["triangles"]
    scene.centroids = data["centroids"]
    scene.normals = data["normals"]
    scene.uvs = data["uvs"]
    scene.tangents = data["tangents"]
    scene.bitangents = data["bitangents"]
    scene.material_ids = data["material_ids"]
    scene.extent = data["extent"].item()
    scene.lights = data["lights"]
    scene.num_lights = len(scene.lights)
    scene.materials = data["materials"]
    scene.num_materials = len(scene.materials)
    scene.base_color_textures = data["base_color_textures"]
    scene.emissive_textures = data["emissive_textures"]
    scene.roughness_textures = data["roughness_textures"]
    scene.metallic_textures = data["metallic_textures"]
    scene.normal_textures = data["normal_textures"]
    scene.occlusion_textures = data["occlusion_textures"]
    scene.emissive_triangle_indices = data["emissive_triangle_indices"]
    scene.area_light_q = data["area_light_q"]
    scene.area_light_p = data["area_light_p"]
    scene.area_light_alias = data["area_light_alias"]
    scene.triangle_areas = data["triangle_areas"]
    scene.finite_light_indices = data["finite_light_indices"]
    scene.finite_light_q = data["finite_light_q"]
    scene.finite_light_p = data["finite_light_p"]
    scene.finite_light_alias = data["finite_light_alias"]
    scene.num_finite_lights = len(scene.finite_light_indices)
    scene.num_emissive_triangles = len(scene.emissive_triangle_indices)
    scene.num_triangles = len(scene.triangles)
    scene.bvh = None
    scene.num_bvh_nodes = None
    scene.hdri = None


def load_scene(scene_path):
    # Note: numpy adds the file suffix automatically
    scene_cache_path = get_cache_path(scene_path, file_paths.scene_cache, "scene").with_suffix(".npz")

    scene = Scene(scene_path)

    try:
        load_scene_data(scene, scene_cache_path)

        print("Loaded scene data from cache")
    except:
        print("Building scene...")
        start_time = time.perf_counter()

        scene.build()

        end_time = time.perf_counter()
        print(f"Scene built in {end_time - start_time:.4f}s")

        print("Scene saving to cache...")

        save_scene_data(scene, scene_cache_path)
        
        print("Scene data saved to cache")
    
    return scene
