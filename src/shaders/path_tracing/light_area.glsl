#ifndef LIGHT_AREA_GLSL
#define LIGHT_AREA_GLSL


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/util.glsl"
#include "src/shaders/path_tracing/intersect.glsl"


// See 7.3 Power Based Sampling
Triangle PowerEmissiveTriangleSample(float Xi, out float triPdf) {
    /* Sample from the precomputed alias table */

    int offset = min(int(Xi.x * numEmissiveTriangles), numEmissiveTriangles - 1);
    float up = min(Xi.x * numEmissiveTriangles - offset, 1.0 - EPSILON);

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

// See 7.6 Area Light Sampling
BsdfSplit SampleAreaLight(SurfaceInteraction si, Ray ray, inout uvec3 rng) {
    BsdfSplit bsdfSplit;
    bsdfSplit.diffuse = vec3(0.0);
    bsdfSplit.specular = vec3(0.0);

    if (numEmissiveTriangles == 0) {
        return bsdfSplit;
    }

    // See 2.2 The PCG Hash
    vec3 Xi = Pcg3d(rng);

    float triPdf;
    Triangle tri = PowerEmissiveTriangleSample(Xi.x, triPdf);

    // See 7.6 Area Light Sampling
    float b0, b1, b2;
    UniformSampleTrianglePoint(Xi.yz, b0, b1, b2);

    vec3 p = b0 * tri.v0.pos + b1 * tri.v1.pos + b2 * tri.v2.pos;
    vec3 lightNs = normalize(b0 * tri.v0.n + b1 * tri.v1.n + b2 * tri.v2.n);

    vec3 wi = normalize(p - si.p);
    float dist = length(p - si.p);

    vec3 ns = si.ns;

    float cosLight = dot(lightNs, -wi);
    if (cosLight <= 0.0) {
        // Ray hit the light's backface
        return bsdfSplit;
    }
    
    float nsDotWi = dot(ns, wi);
    
    if (si.mat.transmission == 0.0 && nsDotWi <= 0.0) {
        return bsdfSplit;
    }

    // See 7.2 Shadow Rays
    VisibilityInteraction vi = ShadowRayTest(rng, si, dist, wi);
    if (vi.isOccluded) {
        return bsdfSplit;
    }

    float pdfPoint = (dist * dist) / (cosLight * tri.area);
    float lightPdf = triPdf * pdfPoint;

    Material lightMat = materials[tri.matId];

    /*
     * Multiple importance sample (MIS)
     * See 7.7 Multiple Importance Sampling
     */

    float bsdfPdf;
    BsdfSplit f = EvaluateBsdfAndPdfSplit(wi, ray, si, bsdfPdf);
    float misWeight = PowerHeuristic(1, lightPdf, 1, bsdfPdf);
    
    vec3 Le = lightMat.emissive * lightMat.emissiveStrength / lightPdf * misWeight;

    bsdfSplit.diffuse = f.diffuse * Le;
    bsdfSplit.specular = f.specular * Le;

    return bsdfSplit;
}

// See 7.6 Area Light Sampling
float AreaLightPdf(SurfaceInteraction si, Ray ray, vec3 prevPoint) {
    Triangle tri = triangles[si.triId];
    vec3 wi = normalize(si.p - prevPoint);
    float dist = length(si.p - prevPoint);

    float cosLight = dot(si.ns, -wi);
    if (cosLight <= 0.0) {
        // Ray hit the light's backface
        return 0.0;
    }

    float pdfTri = tri.lightPmf;
    float pdfPoint = (dist * dist) / (cosLight * si.area);
    float pdf = pdfTri * pdfPoint;
    return pdf;
}


#endif
