#ifndef UTIL_FUNCTIONS_GLSL
#define UTIL_FUNCTIONS_GLSL


#include "src/shaders/common.glsl"


// PCG 3d hash randomization
// http://www.jcgt.org/published/0009/03/02/
vec3 Pcg3d(inout uvec3 rng) {
    rng = rng * 1664525u + 1013904223u;
    rng.x += rng.y*rng.z; rng.y += rng.z*rng.x; rng.z += rng.x*rng.y;
    rng ^= rng >> 16u;
    rng.x += rng.y*rng.z; rng.y += rng.z*rng.x; rng.z += rng.x*rng.y;
    // Divide by 2^32 (uint32 limit) to convert to range [0, 1]
    return vec3(rng) / 4294967295.0;
}

vec3 GetRayPoint(Ray ray, float t) {
    return ray.o + t * ray.d;
}

// Adapted from Ray Tracing Gems, Chapter 6:
// "A Fast and Robust Method for Avoiding Self-Intersection" (Wächter and Binder)
vec3 OffsetRayOrigin(vec3 p, vec3 n) {
    const float intScale = 256.0;
    const float floatScale = 1.0 / 65536.0;
    const float origin = 1.0 / 32.0;

    ivec3 of_i = ivec3(n * intScale);

    vec3 p_i = vec3(
        intBitsToFloat(floatBitsToInt(p.x) + ((p.x < 0.0) ? -of_i.x : of_i.x)),
        intBitsToFloat(floatBitsToInt(p.y) + ((p.y < 0.0) ? -of_i.y : of_i.y)),
        intBitsToFloat(floatBitsToInt(p.z) + ((p.z < 0.0) ? -of_i.z : of_i.z))
    );

    return vec3(
        abs(p.x) < origin ? p.x + floatScale * n.x : p_i.x,
        abs(p.y) < origin ? p.y + floatScale * n.y : p_i.y,
        abs(p.z) < origin ? p.z + floatScale * n.z : p_i.z
    );
}

vec3 ClampLuminance(vec3 col, float maxLum) {
    float lum = dot(col, vec3(0.2126, 0.7152, 0.0722));
    if (lum > maxLum) {
        col *= maxLum / max(lum, 1e-4);
    }
    return col;
}

vec3 EnsureValidReflection(vec3 ng, vec3 wo, vec3 ns) {
    vec3 R = reflect(-wo, ns);

    // Check if the reflection is above the surface
    float horizon = dot(ng, R);
    
    if (horizon < 0.0) {
        float blendFactor = clamp(abs(horizon) / dot(ng, wo) + 1e-4, 0.0, 1.0);

        // Blend the shading normal toward the geometric normal
        return normalize(mix(ns, ng, blendFactor));
    } else {
        return ns;
    }
}

uvec3 InitRngState(ivec2 pixelCoords) {
    uvec3 state = uvec3(
        (pixelCoords.x) * 1512558u,
        uint(pixelCoords.y) * 1029858u,
        uint(totalSamples) * 739391335u
    );

    state ^= uvec3(1597334677u, 3812015801u, 2798796415u);

    return state;
}

vec2 SampleUnitDisk(inout uvec3 rng) {
    vec3 r = Pcg3d(rng);
    float theta = 2.0 * PI * r.x;
    float radius = sqrt(r.y);
    return vec2(radius * cos(theta), radius * sin(theta));
}

vec3 GetBvhDepthColor(int currDepth, int maxDepth) {
    float t = clamp(float(currDepth) / float(maxDepth), 0.0, 1.0);

    vec3 col;
    col.r = smoothstep(0.5, 0.75, t);
    col.g = smoothstep(0.0, 0.25, t) - smoothstep(0.75, 1.0, t);
    col.b = 1.0 - smoothstep(0.25, 0.5, t);

    return col;
}

vec3 GetBvhBoundsColor(int currDepth, int maxDepth) {
    float t = clamp(float(currDepth) / float(maxDepth), 0.0, 1.0);

    const vec3 stops[5] = vec3[](
        vec3(0.0, 0.0, 1.0), // blue  (shallow)
        vec3(0.0, 1.0, 1.0), // cyan
        vec3(0.0, 1.0, 0.0), // green
        vec3(1.0, 1.0, 0.0), // yellow
        vec3(1.0, 0.0, 0.0)  // red   (deep)
    );

    float scaled = t * 4.0;              // 4 segments across 5 stops
    int   i      = clamp(int(scaled), 0, 3);
    float frac   = smoothstep(0.0, 1.0, scaled - float(i)); // ease in/out of each segment

    return mix(stops[i], stops[i + 1], frac);
}


#endif
