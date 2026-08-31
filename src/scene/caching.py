import hashlib
import os
from pathlib import Path
import shutil
import numpy as np

from src.settings import settings
from src.scene.scene import Scene
from src.scene.bvh import BVH


def _get_file_fingerprint(path):
    size = os.path.getsize(path)
    h = hashlib.blake2b(digest_size=settings.cache_fingerprints.digest_size)
    h.update(str(size).encode())

    # Apply ceiling division
    num_chunks = min(settings.cache_fingerprints.max_chunks, -(-size // settings.cache_fingerprints.chunk_size))

    with open(path, "rb") as f:
        if num_chunks * settings.cache_fingerprints.chunk_size >= size:
            # File is small enough; read
            h.update(f.read())
        else:
            stride = (size - settings.cache_fingerprints.chunk_size) / (num_chunks - 1) if num_chunks > 1 else 0
            for i in range(num_chunks):
                offset = int(i * stride)
                f.seek(offset)
                h.update(f.read(settings.cache_fingerprints.chunk_size))

    return f"{Path(path).stem}_{h.hexdigest()}"


def _get_bvh_fingerprint():
    bvh_values = (settings.bvh.max_depth, settings.bvh.sah_bins, settings.bvh.max_leaf_size)
    h = hashlib.blake2b(repr(bvh_values).encode(), digest_size=4)
    return h.hexdigest()

def _get_scene_fingerprint():
    h = hashlib.blake2b(str(settings.rendering.texture_size).encode(), digest_size=4)
    return h.hexdigest()


def remove_stale_cache():
    valid_fingerprints = []
    for scene_file in Path(settings.file_paths.scenes).rglob("*"):
        if scene_file.is_file():
            valid_fingerprints.append(_get_file_fingerprint(scene_file))

    current_bvh_fingerprint = _get_bvh_fingerprint()
    current_scene_fingerprint = _get_scene_fingerprint()

    # Note: Cache files are saved as .npz files

    # Scene Caches
    # ------------
    for cache_file in Path(settings.file_paths.cache.scenes).rglob("*.npz"):
        if cache_file.is_file():
            stem = cache_file.stem
            if stem.startswith("scene_"):
                file_fingerprint, scene_fingerprint = stem[len("scene_"):].rsplit("_", 1)

                if file_fingerprint not in valid_fingerprints or scene_fingerprint != current_scene_fingerprint:
                    cache_file.unlink()

    # BVH Caches
    # ----------
    for cache_file in Path(settings.file_paths.cache.bvhs).rglob("*.npz"):
        if cache_file.is_file():
            stem = cache_file.stem
            if stem.startswith("bvh_"):
                file_fingerprint, bvh_fingerprint = stem[len("bvh_"):].rsplit("_", 1)

                if file_fingerprint not in valid_fingerprints or bvh_fingerprint != current_bvh_fingerprint:
                    cache_file.unlink()


def get_cache_path(path, type):
    path = Path(path).resolve()
    if type == "scene":
        cache_path = Path(settings.file_paths.cache.scenes).resolve()
    elif type == "bvh":
        cache_path = Path(settings.file_paths.cache.bvhs).resolve()

    file_fingerprint = _get_file_fingerprint(path)

    if type == "scene":
        scene_fingerprint = _get_scene_fingerprint()

        return cache_path / f"{type}_{file_fingerprint}_{scene_fingerprint}.npz"
    elif type == "bvh":
        bvh_fingerprint = _get_bvh_fingerprint()
        
        return cache_path / f"{type}_{file_fingerprint}_{bvh_fingerprint}.npz"


def save_bvh_data(bvh, cache_path):
    # Note: numpy adds the file suffix automatically
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

    # Note: numpy adds the file suffix automatically
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
    scene_cache_path = get_cache_path(scene_path, "scene")

    scene = Scene(scene_path)

    try:
        load_scene_data(scene, scene_cache_path)
    except:
        scene.build()

        save_scene_data(scene, scene_cache_path)
    
    return scene


def load_bvh(scene):
    cache_path = get_cache_path(scene.scene_path, "bvh")

    try:
        bvh = load_bvh_data(cache_path)
    
    except:
        bvh = BVH(scene)

        save_bvh_data(bvh, cache_path)

    return bvh


def import_model(src_path):
    src_path = Path(src_path)
    dst_path = settings.file_paths.scenes / src_path.name

    shutil.copy2(src_path, dst_path)

    return dst_path
