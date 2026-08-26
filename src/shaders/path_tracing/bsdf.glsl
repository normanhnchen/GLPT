#ifndef BSDF_GLSL
#define BSDF_GLSL


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/util.glsl"
#include "src/shaders/path_tracing/microfacet.glsl"
#include "src/shaders/path_tracing/brdf.glsl"
#include "src/shaders/path_tracing/btdf.glsl"


// https://learnopengl.com/PBR/Theory
// https://schuttejoe.github.io/post/ggximportancesamplingpart1/
BsdfSample SampleBsdf(inout uvec3 rng, Ray ray, SurfaceInteraction si, inout BounceDepth bounceDepth) {
    Material mat = si.mat;

    bool enteringMedium = !si.isBackFace;

    vec3 ns = si.ns;
    vec3 wo = -ray.d;

    vec3 Xi = Pcg3d(rng);

    float nsDotWo = abs(dot(ns, wo));

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, mat.baseCol, mat.metallic);
    
    LobeProbs lobeProbs = ComputeLobeProbs(mat, nsDotWo, F0);

    BsdfSample bsdfSample;

    if (Xi.z < lobeProbs.specular) {
        // Specular lobe
        // -------------

        bounceDepth.specular++;

        float alpha = mat.roughness * mat.roughness;
        float alpha2 = alpha * alpha;

        vec3 wi, wh;
        if (specularMode == 0) {
            // GGX VNDF Importance Sampling
            // ----------------------------

            // Convert wo to tangent space for the GGX VNDF importance sample
            vec3 woTangent = si.worldToLocal * wo;

            vec3 whTangent = ImportanceSampleGgxVndf(Xi.xy, woTangent, alpha);

            // Transform wh back to world space
            wh = normalize(si.localToWorld * whTangent);
            wi = reflect(-wo, wh);
        } else if (specularMode == 1) {
            // Cosine Hemisphere Sampling
            // --------------------------
            wi = CosineSampleHemisphere(rng, si);
            wh = normalize(wo + wi);
        }

        // Below the surface
        if (dot(ns, wi) <= 0.0) {
            bsdfSample.f = vec3(0.0);
            bsdfSample.wi = wi;
            bsdfSample.pdf = 0.0;

            return bsdfSample;
        }

        float wiDotWh = dot(wi, wh);
        vec3 F = FresnelSchlick(wiDotWh, F0);
        
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

        vec3 specular;
        if (specularMode == 0) {
            specular = F * (G2 / max(G1, 1e-4));
        } else if (specularMode == 1) {
            float D = TrowbridgeReitzGgx(ns, wh, alpha);
            float nDotWo = max(dot(ns, wo), 1e-4);
            float nDotWi = max(dot(ns, wi), 1e-4);
            specular = D * F * G2 / (4.0 * nDotWo * nDotWi);
        }
        
        // Calculate the PDF for this lobe
        // -------------------------------
        float specularPdf;
        if (specularMode == 0) {
            specularPdf = GgxVndfPdf(ns, wo, wi, alpha) * lobeProbs.specular;
        } else if (specularMode == 1) {
            specularPdf = CosineSampleHemispherePdf(ns, wi) * lobeProbs.specular;
        }
        float diffusePdf = CosineSampleHemispherePdf(ns, wi) * lobeProbs.diffuse;
        float bsdfPdf = specularPdf + diffusePdf;

        bsdfSample.pdf = bsdfPdf;
        bsdfSample.wi = wi;
        bsdfSample.f = specular / lobeProbs.specular;

        return bsdfSample;
    } else {
        // Transmission/Diffuse lobe
        // -------------------------

        if (Xi.z < lobeProbs.specular + lobeProbs.transmission) {
            // Transmission lobe
            // -----------------

            bounceDepth.transmission++;

            float alpha = mat.roughness * mat.roughness;
            float alpha2 = alpha * alpha;

            // Convert wo to tangent space for the GGX VNDF importance sample
            vec3 woTangent = si.worldToLocal * wo;

            vec3 whTangent = ImportanceSampleGgxVndf(Xi.xy, woTangent, alpha);

            // Transform wh back to world space
            vec3 wh = normalize(si.localToWorld * whTangent);

            vec3 wi = refract(ray.d, wh, si.eta_i / si.eta_t);

            // Total internal reflection (TIR)
            // -------------------------------

            // GLSL refract function returns vec3(0.0) on TIR
            if (wi == vec3(0.0)) {
                wi = reflect(ray.d, wh);

                vec3 F = vec3(1.0);

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

                vec3 specular;
                if (specularMode == 0) {
                    specular = F * (G2 / max(G1, 1e-4));
                } else if (specularMode == 1) {
                    float D = TrowbridgeReitzGgx(ns, wh, alpha);
                    float nDotWo = max(dot(ns, wo), 1e-4);
                    float nDotWi = max(dot(ns, wi), 1e-4);
                    specular = vec3(D) * F * G2 / max((4.0 * nDotWo * nDotWi), 1e-4);
                }

                // Calculate the PDF for this lobe
                // -------------------------------
                float specularPdf;
                if (specularMode == 0) {
                    specularPdf = GgxVndfPdf(ns, wo, wi, alpha) * lobeProbs.specular;
                } else if (specularMode == 1) {
                    specularPdf = CosineSampleHemispherePdf(ns, wi) * lobeProbs.specular;
                }
                float diffusePdf = CosineSampleHemispherePdf(ns, wi) * lobeProbs.diffuse;
                float bsdfPdf = specularPdf + diffusePdf;

                bsdfSample.pdf = bsdfPdf;
                bsdfSample.f = specular / lobeProbs.transmission;
                bsdfSample.wi = wi;

                return bsdfSample;
            }

            float wiDotWh = abs(dot(wi, wh));
            vec3 F = FresnelSchlick(wiDotWh, F0);

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

            vec3 transmission;
            if (specularMode == 0) {
                transmission = (1.0 - F) * (G2 / max(G1, 1e-4));
            } else if (specularMode == 1) {
                float D = TrowbridgeReitzGgx(ns, wh, alpha);
                float nDotWo = max(dot(ns, wo), 1e-4);
                float nDotWi = max(dot(ns, wi), 1e-4);
                transmission = vec3(D) * (1.0 - F) * G2 / max((4.0 * nDotWo * nDotWi), 1e-4);
            }

            // Calculate the PDF for this lobe
            // -------------------------------
            float bsdfPdf = BtdfPdf(ns, wo, wi, alpha, si.eta_i, si.eta_t) * lobeProbs.transmission;

            bsdfSample.pdf = bsdfPdf;
            bsdfSample.f = transmission / lobeProbs.transmission;
            bsdfSample.wi = wi;

            return bsdfSample;
        } else {
            // Diffuse lobe
            // ------------

            bounceDepth.diffuse++;

            vec3 wi = CosineSampleHemisphere(rng, si);

            // Below surface
            if (dot(ns, wi) <= 0.0) {
                bsdfSample.f = vec3(0.0);
                bsdfSample.wi = wi;
                bsdfSample.pdf = 0.0;

                return bsdfSample;
            }

            vec3 wh = normalize(wo + wi);

            float woDotWh = abs(dot(wo, wh));

            vec3 F = FresnelSchlick(woDotWh, F0);

            vec3 kS = F;
            vec3 kD = vec3(1.0) - kS;
            kD *= 1.0 - mat.metallic;
            kD *= 1.0 - mat.transmission;

            vec3 diffuse = kD * mat.baseCol;

            float alpha = mat.roughness * mat.roughness;

            // Calculate the PDF for this lobe
            // -------------------------------
            float specularPdf;
            if (specularMode == 0) {
                specularPdf = GgxVndfPdf(ns, wo, wi, alpha) * lobeProbs.specular;
            } else if (specularMode == 1) {
                specularPdf = CosineSampleHemispherePdf(ns, wi) * lobeProbs.specular;
            }
            float diffusePdf = CosineSampleHemispherePdf(ns, wi) * lobeProbs.diffuse;
            float bsdfPdf = specularPdf + diffusePdf;

            bsdfSample.pdf = bsdfPdf;
            bsdfSample.f = diffuse / lobeProbs.diffuse;
            bsdfSample.wi = wi;

            return bsdfSample;
        }
    }
}

vec3 EvaluateBsdf(vec3 wi, Ray ray, SurfaceInteraction si) {
    vec3 ns = si.ns;
    float nsDotWi = dot(ns, wi);
    if (nsDotWi > 0.0) {
        return EvaluateBrdf(wi, ray, si);
    } else {
        return EvaluateBtdf(wi, ray, si);
    }
}

vec3 EvaluateBsdfAndPdf(vec3 wi, Ray ray, SurfaceInteraction si, out float bsdfPdf) {
    float nsDotWi = dot(si.ns, wi);
    if (nsDotWi > 0.0) {
        return EvaluateBrdfAndPdf(wi, ray, si, bsdfPdf);
    } else {
        return EvaluateBtdfAndPdf(wi, ray, si, bsdfPdf);
    }
}


#endif
