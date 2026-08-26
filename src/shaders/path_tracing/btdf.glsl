#ifndef BTDF_GLSL
#define BTDF_GLSL


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/microfacet.glsl"


// "Microfacet models for refraction through rough surfaces"
// https://dl.acm.org/doi/10.5555/2383847.2383874
float BtdfPdf(vec3 n, vec3 wo, vec3 wi, float alpha, float eta_i, float eta_t) {
    float nDotWo = abs(dot(n, wo));
    float alpha2 = alpha * alpha;

    vec3 wh = normalize(eta_i * wo + eta_t * wi);
    if (dot(n, wh) < 0.0) wh = -wh;

    float D = TrowbridgeReitzGgx(n, wh, alpha);
    
    float G1;
    if (geometryMode == 0) {
        // Height-Correlated Smith Method
        // ------------------------------
        G1 = SmithGgxMasking(wo, n, alpha2);
    } else {
        // Schlick-GGX Approximation Method
        // --------------------------------
        float roughness = sqrt(alpha);
        float k = (roughness + 1.0) * (roughness + 1.0) / 8.0;
        G1 = GeometrySchlickGgx(max(dot(n, wo), 1e-4), k);
    }

    float woDotWh = dot(wo, wh);
    float wiDotWh = dot(wi, wh);

    float denom = eta_i * woDotWh + eta_t * wiDotWh;
    float dwh_dwi = abs((eta_t * eta_t * wiDotWh) / max(denom * denom, 0.0001));
    return D * G1 * abs(woDotWh) / max(nDotWo, 0.0001) * dwh_dwi;
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

    float nsDotWo = abs(dot(ns, wo));
    float nsDotWi = abs(dot(ns, wi));
    float woDotWh = dot(wo, wh);
    float wiDotWh = dot(wi, wh);

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, mat.baseCol, mat.metallic);
    vec3 F = FresnelSchlick(abs(woDotWh), F0);

    float D = TrowbridgeReitzGgx(ns, wh, alpha);

    float G;
    if (geometryMode == 0) {
        // Height-Correlated Smith Method
        // ------------------------------
        G = SmithGgxMaskingShadowing(wi, wo, ns, alpha2);
    } else {
        // Schlick-GGX Approximation Method
        // --------------------------------
        float k = (mat.roughness + 1.0) * (mat.roughness + 1.0) / 8.0;
        G = GeometrySmith(ns, wo, wi, k);
    }

    float denom = eta_i * woDotWh + eta_t * wiDotWh;
    denom = max(denom * denom, 0.0001);

    float jacobian = abs(woDotWh * wiDotWh) / max(nsDotWo * nsDotWi, 0.0001);

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

    float nsDotWo = abs(dot(ns, wo));
    float nsDotWi = abs(dot(ns, wi));
    float woDotWh = dot(wo, wh);
    float wiDotWh = dot(wi, wh);

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, mat.baseCol, mat.metallic);
    vec3 F = FresnelSchlick(abs(woDotWh), F0);

    float D = TrowbridgeReitzGgx(ns, wh, alpha);

    float G1, G2;
    if (geometryMode == 0) {
        // Height-Correlated Smith Method
        // ------------------------------
        G1 = SmithGgxMasking(wo, ns, alpha2);
        G2 = SmithGgxMaskingShadowing(wi, wo, ns, alpha2);
    } else {
        // Schlick-GGX Approximation Method
        // --------------------------------
        float k = (mat.roughness + 1.0) * (mat.roughness + 1.0) / 8.0;
        G1 = GeometrySchlickGgx(max(dot(ns, wo), 1e-4), k);
        G2 = GeometrySmith(ns, wo, wi, k);
    }

    float denom = eta_i * woDotWh + eta_t * wiDotWh;
    denom = max(denom * denom, 0.0001);

    LobeProbs lobeProbs = ComputeLobeProbs(mat, nsDotWo, F0);

    float dwh_dwi = abs((eta_t * eta_t * wiDotWh) / max(denom, 0.0001));
    btdfPdf = D * G1 * abs(woDotWh) / max(nsDotWo, 0.0001) * dwh_dwi;
    btdfPdf *= lobeProbs.transmission;

    float jacobian = abs(woDotWh * wiDotWh) / max(nsDotWo * nsDotWi, 0.0001);

    vec3 btdf = (vec3(1.0) - F) * D * G2 * jacobian / denom;

    return btdf;
}


#endif
