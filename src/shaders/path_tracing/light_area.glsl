#ifndef LIGHT_AREA_GLSL
#define LIGHT_AREA_GLSL


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/util.glsl"
#include "src/shaders/path_tracing/intersect.glsl"


// "The Alias Method," in Physically Based Rendering: From Theory to Implementation
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

// "Sampling Light Sources," in Physically Based Rendering: From Theory to Implementation
// https://pbr-book.org/4ed/Light_Sources/Light_Sampling#PowerLightSampler
vec3 SampleAreaLight(SurfaceInteraction si, Ray ray, inout uvec3 rng) {
    if (numEmissiveTriangles == 0) {
        return vec3(0.0);
    }

    vec3 Xi = Pcg3d(rng);

    float triPdf;
    Triangle tri = PowerEmissiveTriangleSample(Xi.x, triPdf);

    float b0, b1, b2;
    UniformSampleTrianglePoint(Xi.yz, b0, b1, b2);
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

    VisibilityInteraction vi = ShadowRayTest(rng, si, dist, wi);
    if (vi.isOccluded) {
        return vec3(0.0);
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

float AreaLightPdf(SurfaceInteraction si, Ray ray, vec3 prevPoint) {
    Triangle tri = triangles[si.triId];
    vec3 wi = normalize(si.p - prevPoint);
    float dist = length(si.p - prevPoint);

    // Check if ray hit light's backface
    float cosLight = dot(si.ns, -wi);
    if (cosLight <= 0.0) {
        return 0.0;
    }

    float pdfTri = tri.lightPmf;
    float pdfPoint = (dist * dist) / (cosLight * si.area);
    float pdf = pdfTri * pdfPoint;
    return pdf;
}


#endif
