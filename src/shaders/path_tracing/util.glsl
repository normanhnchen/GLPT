#ifndef UTIL_GLSL
#define UTIL_GLSL


#include "src/shaders/common.glsl"


// Jarzynski & Olano, "Hash Functions for GPU Rendering," JCGT, vol. 9, no. 3, 2020.
// http://jcgt.org/published/0009/03/02/
vec3 Pcg3d(inout uvec3 rng) {
    rng = rng * 1664525u + 1013904223u;
    rng.x += rng.y*rng.z; rng.y += rng.z*rng.x; rng.z += rng.x*rng.y;
    rng ^= rng >> 16u;
    rng.x += rng.y*rng.z; rng.y += rng.z*rng.x; rng.z += rng.x*rng.y;
    // Convert to range [0, 1)
    return vec3(rng) / float(UINT32_MAX);
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

float GetLuminance(vec3 col) {
    return dot(col, vec3(0.2126, 0.7152, 0.0722));
}

vec3 ClampLuminance(vec3 col, float maxLum) {
    float lum = GetLuminance(col);
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

vec2 UniformSampleUnitDisk(inout uvec3 rng) {
    vec3 Xi = Pcg3d(rng);
    float Xi1 = Xi.x;
    float Xi2 = Xi.y;
    
    float r = sqrt(Xi1);
    float theta = 2.0 * PI * Xi2;
    return vec2(r * cos(theta), r * sin(theta));
}

// "Building an Orthonormal Basis, Revisited," Journal of Computer Graphics Techniques (JCGT)
// http://jcgt.org/published/0006/01/01/
void ONB(vec3 n, out vec3 dpdu, out vec3 dpdv) {
    float s = sign(n.z) == 0.0 ? 1.0 : sign(n.z);
    float a = -1.0 / (s + n.z);
    float b = n.x * n.y * a;
    dpdu = vec3(1.0 + s * n.x * n.x * a, s * b, -s * n.x);
    dpdv = vec3(b, s + n.y * n.y * a, -n.y);
}

// "Importance Sampling," in Physically Based Rendering: From Theory to Implementation
// https://pbr-book.org/3ed-2018/Monte_Carlo_Integration/Importance_Sampling#MultipleImportanceSampling
float PowerHeuristic(int nf, float fPdf, int ng, float gPdf) {
    float f = float(nf) * fPdf;
    float g = float(ng) * gPdf;
    return (f * f) / (f * f + g * g);
}

vec3 GetBvhDepthColor(int currDepth, int maxDepth) {
    float t = clamp(float(currDepth) / float(maxDepth), 0.0, 1.0);

    vec3 col;
    col.r = smoothstep(0.5, 0.75, t);
    col.g = smoothstep(0.0, 0.25, t) - smoothstep(0.75, 1.0, t);
    col.b = 1.0 - smoothstep(0.25, 0.5, t);

    return col;
}

// Adapted from Iñigo Quilez's HSB to RGB function
// https://www.shadertoy.com/view/MsS3Wc
vec3 HsbToRgb(in vec3 hsb){
    vec3 rgb = clamp(abs(mod(hsb.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
    rgb = rgb * rgb * (3.0 - 2.0 * rgb);
    return hsb.z * mix(vec3(1.0), rgb, hsb.y);
}

vec3 GetBvhAngleColor(vec3 aabbMin, vec3 aabbMax) {
    vec3 center = (aabbMin + aabbMax) * 0.5;
    
    float theta = atan(center.z, center.x);
    
    // Map from [-π, π] to [0, 1]
    float c = theta / (2.0 * PI) + 0.5;
    
    vec3 hsb = vec3(c, 1.0, 1.0);
    return HsbToRgb(hsb);
}


#endif
