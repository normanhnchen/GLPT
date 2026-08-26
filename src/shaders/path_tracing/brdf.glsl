#ifndef BRDF_GLSL
#define BRDF_GLSL


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/microfacet.glsl"


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

    vec3 F = FresnelSchlick(max(dot(wh, wo), 0.0), F0);
    float D = TrowbridgeReitzGgx(max(nsDotWh, 0.0), alpha);

    float G;
    if (geometryMode == 0) {
        /* Height-correlated Smith method */

        G = SmithGgxMaskingShadowing(abs(nsDotWi), abs(nsDotWo), alpha2);
    } else {
        /* Schlick-GGX approximation method */
        
        float k = (mat.roughness + 1.0) * (mat.roughness + 1.0) / 8.0;
        G = GeometrySmith(max(nsDotWo, 0.0), max(nsDotWi, 0.0), k);
    }

    vec3 kS = F;
    vec3 kD = vec3(1.0) - kS;
    kD *= 1.0 - mat.metallic;
    kD *= 1.0 - mat.transmission;

    vec3 specular = (D * G * F) / max(4.0 * max(nsDotWo, 0.0) * max(nsDotWi, 0.0), EPSILON);
    vec3 diffuse = kD * mat.baseCol / PI;

    vec3 brdf = (diffuse + specular) * max(nsDotWi, 0.0);

    return brdf;
}

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

    vec3 F = FresnelSchlick(max(dot(wh, wo), 0.0), F0);
    float D = TrowbridgeReitzGgx(max(nsDotWh, 0.0), alpha);

    float G1, G2;
    if (geometryMode == 0) {
        /* Height-correlated Smith method */

        G1 = SmithGgxMasking(abs(nsDotWo), alpha2);
        G2 = SmithGgxMaskingShadowing(abs(nsDotWi), abs(nsDotWo), alpha2);
    } else {
        /* Schlick-GGX approximation method */
        
        float k = (mat.roughness + 1.0) * (mat.roughness + 1.0) / 8.0;
        G1 = GeometrySchlickGgx(max(dot(ns, wo), EPSILON), k);
        G2 = GeometrySmith(max(nsDotWo, 0.0), max(nsDotWi, 0.0), k);
    }

    LobeProbs lobeProbs = ComputeLobeProbs(mat, max(nsDotWo, 0.0), F0);

    float specularPdf;
    if (specularMode == 0) {
        specularPdf = (D * G1) / max((4.0 * max(nsDotWo, 0.0)), EPSILON) * lobeProbs.specular;
    } else if (specularMode == 1) {
        specularPdf = CosineSampleHemispherePdf(max(nsDotWi, 0.0)) * lobeProbs.specular;
    }
    float diffusePdf = CosineSampleHemispherePdf(max(nsDotWi, 0.0)) * lobeProbs.diffuse;
    brdfPdf = specularPdf + diffusePdf;

    vec3 kS = F;
    vec3 kD = vec3(1.0) - kS;
    kD *= 1.0 - mat.metallic;
    kD *= 1.0 - mat.transmission;

    vec3 specular = (D * G2 * F) / max(4.0 * max(nsDotWo, 0.0) * max(nsDotWi, 0.0), EPSILON);
    vec3 diffuse = kD * mat.baseCol / PI;

    vec3 brdf = (diffuse + specular) * max(nsDotWi, 0.0);

    return brdf;
}


#endif
