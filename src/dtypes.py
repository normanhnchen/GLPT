import numpy as np


"""
f4/i4/u4 = np.float32/int32/uint32 shorthand.
vec2/vec3/vec4 (and ivec2, uvec2, etc. variants) are (dtype, size) shorthands, so
we unpack them with * when used in a dtype definition
"""


f4 = "f4"
i4 = "i4"
u4 = "u4"

def vec(dtype, size):
    return (dtype, size)

vec2 = vec(f4, 2)
vec3 = vec(f4, 3)
vec4 = vec(f4, 4)

ivec2 = vec(i4, 2)
ivec3 = vec(i4, 3)
ivec4 = vec(i4, 4)

uvec2 = vec(u4, 2)
uvec3 = vec(u4, 3)
uvec4 = vec(u4, 4)

def set_f4(v):
    return np.float32(v)

def set_i4(v):
    return np.int32(v)

def set_u4(v):
    return np.uint32(v)
