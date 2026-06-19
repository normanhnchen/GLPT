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
