#ifndef LIGHT_ENV_GLSL
#define LIGHT_ENV_GLSL


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/util.glsl"
#include "src/shaders/path_tracing/bsdf.glsl"
#include "src/shaders/path_tracing/intersect.glsl"


// "Sampling light sources," in Physically Based Rendering: From Theory to Implementation
// https://pbr-book.org/3ed-2018/Light_Transport_I_Surface_Reflection/Sampling_Light_Sources#InfiniteAreaLights
int SampleRowCdf(float Xi, int height, out float rowHigh, out float rowLow, out float rowPmf) {
    /* Binary search to find the correct row */

    int lo = 0, hi = height - 1;
    while (lo < hi) {
        int mid = (hi + lo) / 2;
        float val = texelFetch(hdriRowCdf, ivec2(0, mid), 0).r;
        if (val < Xi) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }

    // Use lo as the chosen row index
    rowHigh = texelFetch(hdriRowCdf, ivec2(0, lo), 0).r;
    rowLow = lo > 0 ? texelFetch(hdriRowCdf, ivec2(0, lo - 1), 0).r : 0.0;
    rowPmf = max(rowHigh - rowLow, 1e-8);
    return lo;
}

// "Sampling light sources," in Physically Based Rendering: From Theory to Implementation
// https://pbr-book.org/3ed-2018/Light_Transport_I_Surface_Reflection/Sampling_Light_Sources#InfiniteAreaLights
int SampleColCdf(float Xi, int row, int width, out float colHigh, out float colLow, out float colPmf) {
    /* Binary search to find the correct column */

    int lo = 0, hi = width - 1;
    while (lo < hi) {
        int mid = (hi + lo) / 2;
        float val = texelFetch(hdriColCdf, ivec2(mid, row), 0).r;
        if (val < Xi) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }

    // Use (low, row) as the chosen (row, col) indices
    colHigh = texelFetch(hdriColCdf, ivec2(lo, row), 0).r;
    colLow = lo > 0 ? texelFetch(hdriColCdf, ivec2(lo - 1, row), 0).r : 0.0;
    colPmf = max(colHigh - colLow, 1e-8);
    return lo;
}

vec3 SampleHdri(vec3 d) {
    // Convert to spherical coordinates
    float phi = atan(d.z, d.x);
    float theta = acos(d.y);
    // Convert to uv coordinates
    vec2 uv = vec2(phi / (2.0 * PI) + 0.5, theta / PI);
    return texture(hdri, uv).rgb;
}

// "Sampling light sources," in Physically Based Rendering: From Theory to Implementation
// https://pbr-book.org/3ed-2018/Light_Transport_I_Surface_Reflection/Sampling_Light_Sources#InfiniteAreaLights
vec3 DirectSampleHdri(inout uvec3 rng, out vec3 d, out float hdriPdf) {
    ivec2 size = textureSize(hdri, 0);
    int width = size.x, height = size.y;

    vec3 Xi = Pcg3d(rng);

    float rowHigh, rowLow, rowPmf;
    int row = SampleRowCdf(Xi.x, height, rowHigh, rowLow, rowPmf);
    float colHigh, colLow, colPmf;
    int col = SampleColCdf(Xi.y, row, width, colHigh, colLow, colPmf);

    // Offsets to the row and column column to map it back to a continuous point
    float dv = (Xi.x - rowLow) / rowPmf;
    float du = (Xi.y - colLow) / colPmf;

    // Sampled continuous point in ranges [0, 1)
    float u = (float(col) + du) / float(width);
    float v = (float(row) + dv) / float(height);

    float theta = v * PI;
    float phi = (u - 0.5) * 2.0 * PI;

    d = normalize(vec3(
        sin(theta) * cos(phi),
        cos(theta),
        sin(theta) * sin(phi)
    ));

    float mapPdf = rowPmf * colPmf * float(width) * float(height);
    float sinTheta = sin(theta);
    hdriPdf = sinTheta > 0.0 ? mapPdf / (2.0 * PI * PI * sinTheta) : 0.0;

    return texture(hdri, vec2(u, v)).rgb;
}

vec3 SampleHdriLight(SurfaceInteraction si, Ray ray, inout uvec3 rng) {
    vec3 wi;
    float lightPdf;
    vec3 Li = DirectSampleHdri(rng, wi, lightPdf);
    if (lightPdf <= 0.0) return vec3(0.0);

    vec3 ns = si.ns;

    float nsDotWi = dot(ns, wi);

    float dist = INF;
    
    if (si.mat.transmission == 0.0 && nsDotWi <= 0.0) {
        return vec3(0.0);
    }

    VisibilityInteraction vi = ShadowRayTest(rng, si, dist, wi);
    if (vi.isOccluded) {
        return vec3(0.0);
    }

    /* Multiple Importance Sample (MIS) */

    float bsdfPdf;
    vec3 f = EvaluateBsdfAndPdf(wi, ray, si, bsdfPdf);
    float misWeight = PowerHeuristic(1, lightPdf, 1, bsdfPdf);

    return (f * Li * hdriExposure) / lightPdf * misWeight;
}

// "Sampling light sources," in Physically Based Rendering: From Theory to Implementation
// https://pbr-book.org/3ed-2018/Light_Transport_I_Surface_Reflection/Sampling_Light_Sources#InfiniteAreaLights
float HdriPdf(vec3 d) {
    ivec2 size = textureSize(hdri, 0);
    int width = size.x, height = size.y;

    // Convert to spherical coordinates
    float phi = atan(d.z, d.x);
    float theta = acos(d.y);
    // Convert to uv coordinates
    vec2 uv = vec2(phi / (2.0 * PI) + 0.5, theta / PI);

    int col = min(int(uv.x * float(width)), width - 1);
    int row = min(int(uv.y * float(height)), height - 1);

    float rowHigh = texelFetch(hdriRowCdf, ivec2(0, row), 0).r;
    float rowLow = row > 0 ? texelFetch(hdriRowCdf, ivec2(0, row - 1), 0).r : 0.0;
    float rowPmf = max(rowHigh - rowLow, 1e-8);
    
    float colHigh = texelFetch(hdriColCdf, ivec2(col, row), 0).r;
    float colLow = col > 0 ? texelFetch(hdriColCdf, ivec2(col - 1, row), 0).r : 0.0;
    float colPmf = max(colHigh - colLow, 1e-8);

    float mapPdf = rowPmf * colPmf * float(width) * float(height);
    float sinTheta = sin(theta);
    return sinTheta > 0.0 ? mapPdf / (2.0 * PI * PI * sinTheta) : 0.0;
}


#endif