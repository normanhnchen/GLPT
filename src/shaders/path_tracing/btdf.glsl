#ifndef BTDF_GLSL
#define BTDF_GLSL


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/microfacet.glsl"


// "Microfacet models for refraction through rough surfaces"
// https://dl.acm.org/doi/10.5555/2383847.2383874
float BtdfPdf(vec3 n, vec3 wo, vec3 wi, float alpha, float eta_i, float eta_t) {
    float alpha2 = alpha * alpha;

    vec3 wh = normalize(eta_i * wo + eta_t * wi);
    if (dot(n, wh) < 0.0) wh = -wh;

    float nDotWo = dot(n, wo);
    float nDotWh = dot(n, wh);
    float woDotWh = dot(wo, wh);
    float wiDotWh = dot(wi, wh);

    float D = TrowbridgeReitzGgx(max(nDotWh, 0.0), alpha);
    
    float G1;
    if (geometryMode == 0) {
        /* Height-correlated Smith method */

        G1 = SmithGgxMasking(abs(nDotWo), alpha2);
    } else {
        /* Schlick-GGX approximation method */

        float roughness = sqrt(alpha);
        float k = (roughness + 1.0) * (roughness + 1.0) / 8.0;
        G1 = GeometrySchlickGgx(max(nDotWo, EPSILON), k);
    }

    float denom = eta_i * woDotWh + eta_t * wiDotWh;
    float dwh_dwi = abs((eta_t * eta_t * wiDotWh) / max(denom * denom, EPSILON));
    return D * G1 * abs(woDotWh) / max(nDotWo, EPSILON) * dwh_dwi;
}

vec3 EvaluateBtdf(vec3 wi, Ray ray, SurfaceInteraction si) {
    Material mat = si.mat;
    vec3 ns = si.ns;
    vec3 wo = -ray.d;
    float eta_i = si.eta_i;
    float eta_t = si.eta_t;

    float alpha = mat.roughness * mat.roughness;
    float alpha2 = alpha * alpha;

    vec3 wh = normalize(eta_i * wo + eta_t * wi);
    if (dot(ns, wh) < 0.0) wh = -wh;

    float nsDotWo = dot(ns, wo);
    float nsDotWi = dot(ns, wi);
    float nsDotWh = dot(ns, wh);
    float woDotWh = dot(wo, wh);
    float wiDotWh = dot(wi, wh);

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, mat.baseCol, mat.metallic);
    vec3 F = FresnelSchlick(abs(woDotWh), F0);

    float D = TrowbridgeReitzGgx(max(nsDotWh, 0.0), alpha);

    float G;
    if (geometryMode == 0) {
        /* Height-Correlated Smith Method */

        G = SmithGgxMaskingShadowing(abs(nsDotWi), abs(nsDotWo), alpha2);
    } else {
        /* Schlick-GGX Approximation Method */
        
        float k = (mat.roughness + 1.0) * (mat.roughness + 1.0) / 8.0;
        G = GeometrySmith(max(nsDotWo, 0.0), max(nsDotWi, 0.0), k);
    }

    float denom = eta_i * woDotWh + eta_t * wiDotWh;
    denom = max(denom * denom, EPSILON);

    float jacobian = abs(woDotWh * wiDotWh) / max(abs(nsDotWo) * abs(nsDotWi), EPSILON);

    vec3 btdf = (vec3(1.0) - F) * D * G * jacobian / denom;

    return btdf;
}

vec3 EvaluateBtdfAndPdf(vec3 wi, Ray ray, SurfaceInteraction si, out float btdfPdf) {
    Material mat = si.mat;
    vec3 ns = si.ns;
    vec3 wo = -ray.d;
    float eta_i = si.eta_i;
    float eta_t = si.eta_t;

    float alpha = mat.roughness * mat.roughness;
    float alpha2 = alpha * alpha;

    vec3 wh = normalize(eta_i * wo + eta_t * wi);
    if (dot(ns, wh) < 0.0) wh = -wh;

    float nsDotWo = dot(ns, wo);
    float nsDotWi = dot(ns, wi);
    float nsDotWh = dot(ns, wh);
    float woDotWh = dot(wo, wh);
    float wiDotWh = dot(wi, wh);

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, mat.baseCol, mat.metallic);
    vec3 F = FresnelSchlick(abs(woDotWh), F0);

    float D = TrowbridgeReitzGgx(max(nsDotWh, 0.0), alpha);

    float G1, G2;
    if (geometryMode == 0) {
        /* Height-correlated smith method */

        G1 = SmithGgxMasking(abs(nsDotWo), alpha2);
        G2 = SmithGgxMaskingShadowing(abs(nsDotWi), abs(nsDotWo), alpha2);
    } else {
        /* Schlick-GGX approximation method */

        float k = (mat.roughness + 1.0) * (mat.roughness + 1.0) / 8.0;
        G1 = GeometrySchlickGgx(max(nsDotWo, EPSILON), k);
        G2 = GeometrySmith(max(nsDotWo, 0.0), max(nsDotWi, 0.0), k);
    }

    float denom = eta_i * woDotWh + eta_t * wiDotWh;
    denom = max(denom * denom, EPSILON);

    LobeProbs lobeProbs = ComputeLobeProbs(mat, abs(nsDotWo), F0);

    float dwh_dwi = abs((eta_t * eta_t * wiDotWh) / max(denom, EPSILON));
    btdfPdf = D * G1 * abs(woDotWh) / max(abs(nsDotWo), EPSILON) * dwh_dwi;
    btdfPdf *= lobeProbs.transmission;

    float jacobian = abs(woDotWh * wiDotWh) / max(abs(nsDotWo) * abs(nsDotWi), EPSILON);

    vec3 btdf = (vec3(1.0) - F) * D * G2 * jacobian / denom;

    return btdf;
}


#endif
