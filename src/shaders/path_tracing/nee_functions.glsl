#ifndef NEE_FUNCTIONS_GLSL
#define NEE_FUNCTIONS_GLSL


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/util_functions.glsl"
#include "src/shaders/path_tracing/bsdf_functions.glsl"
#include "src/shaders/path_tracing/intersect_functions.glsl"
#include "src/shaders/path_tracing/mis_functions.glsl"


// https://pbr-book.org/3ed-2018/Light_Transport_I_Surface_Reflection/Sampling_Light_Sources#InfiniteAreaLights
int SampleRowCdf(float Xi, int height, out float rowHigh, out float rowLow, out float rowPmf) {
    // Binary search to find the correct row
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

// https://pbr-book.org/3ed-2018/Light_Transport_I_Surface_Reflection/Sampling_Light_Sources#InfiniteAreaLights
int SampleColCdf(float Xi, int row, int width, out float colHigh, out float colLow, out float colPmf) {
    // Binary search to find the correct column
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
    
    if (si.mat.transmission == 0.0 && nsDotWi <= 0.0) {
        return vec3(0.0);
    }

    // Shadow ray
    Ray shadowRay;
    vec3 offsetDir = dot(si.ng, wi) < 0.0 ? -si.ng : si.ng;
    shadowRay.o = OffsetRayOrigin(si.p, offsetDir);
    shadowRay.d = wi;

    VisibilityInteraction vi;
    bool isOccluded = TestVisibility(rng, shadowRay, INF, vi);
    if (isOccluded) {
        return vec3(0.0); // Occluded
    }

    // Multiple Importance Sample (MIS)
    // --------------------------------
    float bsdfPdf;
    vec3 f = EvaluateBsdfAndPdf(wi, ray, si, bsdfPdf);
    float misWeight = PowerHeuristic(1, lightPdf, 1, bsdfPdf);

    return (f * Li * hdriExposure) / lightPdf * misWeight;
}

// https://pbr-book.org/4ed/Sampling_Algorithms/The_Alias_Method#AliasTable::Sample
Light PowerFinitePunctualLightSample(float Xi, out float lightPdf) {
    // Sample from the precomputed alias table weighted by power
    // ---------------------------------------------------------
    int offset = min(int(Xi.x * numFiniteLights), numFiniteLights - 1);
    float up = min(Xi.x * numFiniteLights - offset, ONE_MINUS_EPSILON);

    FiniteLight flOffset = finiteLights[offset];

    int finiteLightId;
    if (up < flOffset.q) {
        finiteLightId = offset;
        lightPdf = flOffset.p;
    } else {
        finiteLightId = flOffset.alias;
        lightPdf = finiteLights[finiteLightId].p;
    }

    int lightId = finiteLights[finiteLightId].lightId;
    return lights[lightId];
}

// https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_lights_punctual/README.md
// https://www.pbr-book.org/4ed/Light_Sources/Point_Lights
vec3 SampleFinitePunctualLight(SurfaceInteraction si, Ray ray, inout uvec3 rng) {
    if (numFiniteLights == 0) {
        return vec3(0.0);
    }

    vec3 Xi = Pcg3d(rng);

    float lightPdf;
    Light light = PowerFinitePunctualLightSample(Xi.x, lightPdf);

    vec3 wi = normalize(light.pos - si.p);
    float dist = length(light.pos - si.p);
    vec3 Li;
    // Point
    if (light.type == 0) {
        Li = light.col * light.intensity / max(dist * dist, 0.0001);
    }
    // Spot
    else if (light.type == 2) {
        float lightAngleScale = 1.0 / max(0.001, cos(light.innerConeAngle) - cos(light.outerConeAngle));
        float lightAngleOffset = -cos(light.outerConeAngle) * lightAngleScale;

        float cd = dot(normalize(-light.d), wi);
        float angularAttenuation = clamp(cd * lightAngleScale + lightAngleOffset, 0.0, 1.0);
        angularAttenuation *= angularAttenuation;
        float attenuation = angularAttenuation / max(dist * dist, 0.0001);

        Li = light.col * light.intensity * attenuation;
    }

    vec3 ns = si.ns;
    
    float nsDotWi = dot(ns, wi);
    
    if (si.mat.transmission == 0.0 && nsDotWi <= 0.0) {
        return vec3(0.0);
    }

    // Shadow ray
    Ray shadowRay;
    vec3 offsetDir = dot(si.ng, wi) < 0.0 ? -si.ng : si.ng;
    shadowRay.o = OffsetRayOrigin(si.p, offsetDir);
    shadowRay.d = wi;

    VisibilityInteraction vi;
    bool isOccluded = TestVisibility(rng, shadowRay, dist, vi);
    if (isOccluded && vi.t < dist) {
        return vec3(0.0); // Occluded
    }

    vec3 f = EvaluateBsdf(wi, ray, si);
    return f * Li / lightPdf;
}

vec3 SampleInfinitePunctualLight(SurfaceInteraction si, Ray ray, Light light, inout uvec3 rng) {
    vec3 wi = normalize(-light.d);
    float dist = INF;
    vec3 Li = light.col * light.intensity;

    vec3 ns = si.ns;
    
    float nsDotWi = dot(ns, wi);
    
    if (si.mat.transmission == 0.0 && nsDotWi <= 0.0) {
        return vec3(0.0);
    }

    // Shadow ray
    Ray shadowRay;
    vec3 offsetDir = dot(si.ng, wi) < 0.0 ? -si.ng : si.ng;
    shadowRay.o = OffsetRayOrigin(si.p, offsetDir);
    shadowRay.d = wi;

    VisibilityInteraction vi;
    bool isOccluded = TestVisibility(rng, shadowRay, dist, vi);
    if (isOccluded && vi.t < dist) {
        return vec3(0.0); // Occluded
    }

    vec3 f = EvaluateBsdf(wi, ray, si);
    return f * Li;
}

// https://pbr-book.org/4ed/Sampling_Algorithms/The_Alias_Method#AliasTable::Sample
Triangle PowerEmissiveTriangleSample(float Xi, out float triPdf) {
    // Sample from the precomputed alias table weighted by power
    // ---------------------------------------------------------
    int offset = min(int(Xi.x * numEmissiveTriangles), numEmissiveTriangles - 1);
    float up = min(Xi.x * numEmissiveTriangles - offset, ONE_MINUS_EPSILON);

    EmissiveTriangle etOffset = emissiveTriangles[offset];

    int emissiveTriId;
    if (up < etOffset.q) {
        emissiveTriId = offset;
        triPdf = etOffset.p;
    } else {
        emissiveTriId = etOffset.alias;
        triPdf = emissiveTriangles[emissiveTriId].p;
    }

    int triId = emissiveTriangles[emissiveTriId].triId;
    return triangles[triId];
}

// https://pbr-book.org/4ed/Light_Sources/Light_Sampling#PowerLightSampler
vec3 SampleAreaLight(SurfaceInteraction si, Ray ray, inout uvec3 rng) {
    if (numEmissiveTriangles == 0) {
        return vec3(0.0);
    }

    vec3 Xi = Pcg3d(rng);

    float triPdf;
    Triangle tri = PowerEmissiveTriangleSample(Xi.x, triPdf);

    // Uniformly sample random point on triangle
    // https://pbr-book.org/4ed/Shapes/Triangle_Meshes#Sampling
    float b0, b1, b2;
    if (Xi.y < Xi.z) {
        b0 = Xi.y / 2.0;
        b1 = Xi.z - b0;
        b2 = 1.0 - b0 - b1;
    } else {
        b1 = Xi.z / 2.0;
        b0 = Xi.y - b1;
        b2 = 1.0 - b0 - b1;
    }
    vec3 p = b0 * tri.v0.pos + b1 * tri.v1.pos + b2 * tri.v2.pos;
    vec3 lightNs = normalize(b0 * tri.v0.n + b1 * tri.v1.n + b2 * tri.v2.n);

    vec3 wi = normalize(p - si.p);
    float dist = length(p - si.p);

    vec3 ns = si.ns;

    // Check if ray hit light's backface
    float cosLight = dot(lightNs, -wi);
    if (cosLight <= 0.0) {
        return vec3(0.0);
    }
    
    float nsDotWi = dot(ns, wi);
    
    if (si.mat.transmission == 0.0 && nsDotWi <= 0.0) {
        return vec3(0.0);
    }

    // Shadow ray
    Ray shadowRay;
    vec3 offsetDir = dot(si.ng, wi) < 0.0 ? -si.ng : si.ng;
    shadowRay.o = OffsetRayOrigin(si.p, offsetDir);
    shadowRay.d = wi;

    // Distance-scaled offset dynamic with how far away the light source is
    float distOffset = max(dist * 1e-4, 1e-4);

    VisibilityInteraction vi;
    bool isOccluded = TestVisibility(rng, shadowRay, dist - distOffset, vi);
    if (isOccluded && vi.t < dist - distOffset) {
        return vec3(0.0); // Occluded
    }

    float pdfPoint = (dist * dist) / (cosLight * tri.area);
    float lightPdf = triPdf * pdfPoint;

    Material lightMat = materials[tri.matId];

    // Multiple Importance Sample (MIS)
    // --------------------------------
    float bsdfPdf;
    vec3 f = EvaluateBsdfAndPdf(wi, ray, si, bsdfPdf);
    float misWeight = PowerHeuristic(1, lightPdf, 1, bsdfPdf);

    return (f * lightMat.emissive * lightMat.emissiveStrength) / lightPdf * misWeight;
}


#endif
