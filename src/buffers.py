import numpy as np

from src.dtypes import *
from src.settings import *


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
    ("pad5", f4)
])

triangle_dtype = np.dtype([
    ("v0", vertex_dtype), ("v1", vertex_dtype), ("v2", vertex_dtype),
    ("matId", i4),
    ("area", f4), # -1 if not emissive
    ("pad1", f4), ("pad2", f4)
])

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

emissive_triangles_dtype = np.dtype([
    ("triIdx", i4)
])
