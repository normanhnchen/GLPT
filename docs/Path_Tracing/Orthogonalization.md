# Orthogonalization

## Gram-Schmidt process

Process of re-orthogonalizing the TBN (tangent, bitangent, normal) vectors to be mutually perpendicular.

```
// GLSL

vec3 T = normalize(vec3(model * vec4(aTangent, 0.0)));
vec3 N = normalize(vec3(model * vec4(aNormal, 0.0)));
T = normalize(T - dot(T, N) * N);
vec3 B = cross(N, T);

mat3 TBN = mat3(T, B, N)
```

## Building an Orthonormal Basis

Used to transform from tangent to world space using the normal vector as a basis.

The code creates a helper which helps avoid division by zero during the cross product. The helper's code is to make sure it is never parallel to the normal vector by checking which direction the normal is mostly pointing towards.

```
// GLSL Pseudocode

vec3 helper = abs(normal.x) > 0.9 ? vec3(0, 1, 0) : vec3(1, 0, 0);
vec3 tangent = normalize(cross(normal, helper));
vec3 bitangent = cross(normal, tangent);
```

# References

- https://learnopengl.com/Advanced-Lighting/Normal-Mapping

- Artificial Intelligence (Gemini)
    - Used when I needed to convert from tangent to world space