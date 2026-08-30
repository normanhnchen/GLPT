#ifndef BRDF_GLSL
#define BRDF_GLSL


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/microfacet.glsl"


// See 5.12 BSDF Evaluation
vec3 EvaluateBrdf(vec3 wi, Ray ray, SurfaceInteraction si) {
    Material mat = si.mat;

    vec3 ns = si.ns;
    vec3 wo = -ray.d;

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, mat.baseCol, mat.metallic);

    vec3 wh = normalize(wo + wi);

    float alpha = mat.roughness * mat.roughness;
    float alpha2 = alpha * alpha;

    float nsDotWh = dot(ns, wh);
    float nsDotWo = dot(ns, wo);
    float nsDotWi = dot(ns, wi);
    float whDotWo = dot(wh, wo);

    // See 5.7 Fresnel-Schlick Approximation
    vec3 F = FresnelSchlick(max(whDotWo, 0.0), F0);
    // See 5.4 Trowbridge-Reitz GGX
    float D = TrowbridgeReitzGgx(max(nsDotWh, 0.0), alpha);

    float G;
    if (geometryMode == 0) {
        /*
         * Height-correlated Smith method
         * See 5.6 Height-Correlated Smith
         */

        G = SmithGgxMaskingShadowing(abs(nsDotWi), abs(nsDotWo), alpha2);
    } else {
        /*
         * Schlick-GGX approximation method
         * See 5.5 Schlick-GGX Approximation
         */
        
        float k = (mat.roughness + 1.0) * (mat.roughness + 1.0) / 8.0;
        G = GeometrySmith(max(nsDotWo, 0.0), max(nsDotWi, 0.0), k);
    }

    /* Energy conservation */

    vec3 diffuse = vec3(1.0) - F;
    diffuse *= 1.0 - mat.metallic;
    diffuse *= 1.0 - mat.transmission;

    vec3 specular = (D * G * F) / max(4.0 * max(nsDotWo, 0.0) * max(nsDotWi, 0.0), EPSILON);
    // See 5.2 Lambert's Cosine Law
    diffuse *= mat.baseCol / PI;

    vec3 brdf = (diffuse + specular) * max(nsDotWi, 0.0);

    return brdf;
}

// See 5.12 BSDF Evaluation
vec3 EvaluateBrdfAndPdf(vec3 wi, Ray ray, SurfaceInteraction si, out float brdfPdf) {
    Material mat = si.mat;

    vec3 ns = si.ns;
    vec3 wo = -ray.d;

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, mat.baseCol, mat.metallic);

    vec3 wh = normalize(wo + wi);

    float alpha = mat.roughness * mat.roughness;
    float alpha2 = alpha * alpha;

    float nsDotWo = dot(ns, wo);
    float nsDotWi = dot(ns, wi);
    float nsDotWh = dot(ns, wh);
    float whDotWo = dot(wh, wo);

    // See 5.7 Fresnel-Schlick Approximation
    vec3 F = FresnelSchlick(max(whDotWo, 0.0), F0);
    // See 5.4 Trowbridge-Reitz GGX
    float D = TrowbridgeReitzGgx(max(nsDotWh, 0.0), alpha);

    float G1, G2;
    if (geometryMode == 0) {
        /*
         * Height-correlated Smith method
         * See 5.6 Height-Correlated Smith
         */

        G1 = SmithGgxMasking(abs(nsDotWo), alpha2);
        G2 = SmithGgxMaskingShadowing(abs(nsDotWi), abs(nsDotWo), alpha2);
    } else {
        /*
         * Schlick-GGX approximation method
         * See 5.5 Schlick-GGX Approximation
         */
        
        float k = (mat.roughness + 1.0) * (mat.roughness + 1.0) / 8.0;
        G1 = GeometrySchlickGgx(max(nsDotWo, EPSILON), k);
        G2 = GeometrySmith(max(nsDotWo, 0.0), max(nsDotWi, 0.0), k);
    }

    // See 5.10 Lobe Selection
    LobeProbs lobeProbs = ComputeLobeProbs(mat, max(nsDotWo, 0.0), F0);

    float specularPdf;
    if (specularMode == 0) {
        /* 
         * GGX VNDF importance sampling
         * See 5.8 GGX VNDF Importance Sampling
         */

        specularPdf = (D * G1) / max((4.0 * max(nsDotWo, 0.0)), EPSILON) * lobeProbs.specular;
    } else if (specularMode == 1) {
        /*
         * Cosine-weighted hemisphere sampling
         * See 5.3 Cosine-Weighted Hemisphere Sampling
         */
        
        specularPdf = CosineSampleHemispherePdf(max(nsDotWi, 0.0)) * lobeProbs.specular;
    }
    // See 5.3 Cosine-Weighted Hemisphere Sampling
    float diffusePdf = CosineSampleHemispherePdf(max(nsDotWi, 0.0)) * lobeProbs.diffuse;

    brdfPdf = specularPdf + diffusePdf;

    /* Energy Conservation */

    vec3 diffuse = vec3(1.0) - F;
    diffuse *= 1.0 - mat.metallic;
    diffuse *= 1.0 - mat.transmission;
    // See 5.2 Lambert's Cosine Law
    diffuse *= mat.baseCol / PI;

    vec3 specular = (D * G2 * F) / max(4.0 * max(nsDotWo, 0.0) * max(nsDotWi, 0.0), EPSILON);

    vec3 brdf = (diffuse + specular) * max(nsDotWi, 0.0);

    return brdf;
}


#endif
