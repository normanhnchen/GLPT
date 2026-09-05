#ifndef BSDF_GLSL
#define BSDF_GLSL


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/util.glsl"
#include "src/shaders/path_tracing/microfacet.glsl"
#include "src/shaders/path_tracing/brdf.glsl"
#include "src/shaders/path_tracing/btdf.glsl"


// See 5.11 BSDF Sampling
BsdfSample SampleBsdf(inout uvec3 rng, Ray ray, SurfaceInteraction si, inout BounceDepth bounceDepth) {
    Material mat = si.mat;

    vec3 ns = si.ns;
    vec3 wo = -ray.d;

    // See 2.2 The PCG Hash
    vec3 Xi = Pcg3d(rng);

    float nsDotWo = dot(ns, wo);

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, mat.baseCol, mat.metallic);
    
    // See 5.10 Lobe Selection
    LobeProbs lobeProbs = ComputeLobeProbs(mat, abs(nsDotWo), F0);

    BsdfSample bsdfSample;

    if (Xi.z < lobeProbs.specular) {
        /* Specular lobe */

        bounceDepth.specular++;

        float alpha = mat.roughness * mat.roughness;
        float alpha2 = alpha * alpha;

        vec3 wi, wm;
        if (specularMode == 0) {
            /* 
             * GGX VNDF importance sampling
             * See 5.8 GGX VNDF Importance Sampling
             */

            wm = ImportanceSampleGgxVndf(si, Xi.xy, wo, alpha);

            wi = reflect(-wo, wm);
        } else if (specularMode == 1) {
            /*
             * Cosine-weighted hemisphere sampling
             * See 5.3 Cosine-Weighted Hemisphere Sampling
             */

            wi = CosineSampleHemisphere(rng, si);
            wm = normalize(wo + wi);
        }

        float nsDotWi = dot(ns, wi);

        if (nsDotWi <= 0.0) {
            // wi is below the hemisphere
            
            bsdfSample.f = vec3(0.0);
            bsdfSample.wi = wi;
            bsdfSample.pdf = 0.0;
            bsdfSample.lobeType = 1; // Specular

            return bsdfSample;
        }

        float wiDotWh = dot(wi, wm);

        // See 5.7 Fresnel-Schlick Approximation
        vec3 F = FresnelSchlick(abs(wiDotWh), F0);
        
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

        float nsDotWm = dot(ns, wm);

        vec3 specular;
        if (specularMode == 0) {
            /* 
             * GGX VNDF importance sampling
             * See 5.8 GGX VNDF Importance Sampling
             */

            specular = F * (G2 / max(G1, EPSILON));
        } else if (specularMode == 1) {
            /*
             * Cosine-weighted hemisphere sampling
             * See 5.3 Cosine-Weighted Hemisphere Sampling
             */

            float D = TrowbridgeReitzGgx(max(nsDotWm, 0.0), alpha);
            specular = D * F * G2 / max((4.0 * max(nsDotWo, 0.0) * max(nsDotWi, 0.0)), EPSILON);
        }
        
        float specularPdf;
        if (specularMode == 0) {
            /* 
             * GGX VNDF importance sampling
             * See 5.8 GGX VNDF Importance Sampling
             */

            specularPdf = GgxVndfPdf(ns, wo, wi, alpha) * lobeProbs.specular;
        } else if (specularMode == 1) {
            /*
             * Cosine-weighted hemisphere sampling
             * See 5.3 Cosine-Weighted Hemisphere Sampling
             */

            specularPdf = CosineSampleHemispherePdf(max(nsDotWi, 0.0)) * lobeProbs.specular;
        }
        // See 5.3 Cosine-Weighted Hemisphere Sampling
        float diffusePdf = CosineSampleHemispherePdf(max(nsDotWi, 0.0)) * lobeProbs.diffuse;

        float bsdfPdf = specularPdf + diffusePdf;

        bsdfSample.pdf = bsdfPdf;
        bsdfSample.wi = wi;
        bsdfSample.f = specular / lobeProbs.specular;
        bsdfSample.lobeType = 1; // Specular

        return bsdfSample;
    } else {
        /* Transmission & diffuse lobe */

        if (Xi.z < lobeProbs.specular + lobeProbs.transmission) {
            /*
             * Transmission lobe
             * See 5.8 Microfacet Transmission
             */

            bounceDepth.transmission++;

            float alpha = mat.roughness * mat.roughness;
            float alpha2 = alpha * alpha;

            // See 5.8 GGX VNDF Importance Sampling
            vec3 wh = ImportanceSampleGgxVndf(si, Xi.xy, wo, alpha);

            vec3 wi = refract(ray.d, wh, si.eta_i / si.eta_t);

            /* Total internal reflection (TIR) */

            // GLSL refract function returns vec3(0.0) on TIR
            if (wi == vec3(0.0)) {
                wi = reflect(ray.d, wh);

                float nsDotWi = dot(ns, wi);

                vec3 F = vec3(1.0);

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

                float nsDotWh = dot(ns, wh);

                vec3 specular;
                if (specularMode == 0) {
                    /* 
                     * GGX VNDF importance sampling
                     * See 5.8 GGX VNDF Importance Sampling
                     */

                    specular = F * (G2 / max(G1, EPSILON));
                } else if (specularMode == 1) {
                    /*
                     * Cosine-weighted hemisphere sampling
                     * See 5.3 Cosine-Weighted Hemisphere Sampling
                     */

                    float D = TrowbridgeReitzGgx(max(nsDotWh, 0.0), alpha);
                    specular = vec3(D) * F * G2 / max((4.0 * max(nsDotWo, 0.0) * max(nsDotWi, 0.0)), EPSILON);
                }

                float specularPdf;
                if (specularMode == 0) {
                    /* 
                     * GGX VNDF importance sampling
                     * See 5.8 GGX VNDF Importance Sampling
                     */

                    specularPdf = GgxVndfPdf(ns, wo, wi, alpha) * lobeProbs.specular;
                } else if (specularMode == 1) {
                    /*
                     * Cosine-weighted hemisphere sampling
                     * See 5.3 Cosine-Weighted Hemisphere Sampling
                     */

                    specularPdf = CosineSampleHemispherePdf(max(nsDotWi, 0.0)) * lobeProbs.specular;
                }
                // See 5.3 Cosine-Weighted Hemisphere Sampling
                float diffusePdf = CosineSampleHemispherePdf(max(nsDotWi, 0.0)) * lobeProbs.diffuse;

                float bsdfPdf = specularPdf + diffusePdf;

                bsdfSample.pdf = bsdfPdf;
                bsdfSample.f = specular / lobeProbs.transmission;
                bsdfSample.wi = wi;
                bsdfSample.lobeType = 2; // Transmission

                return bsdfSample;
            }

            float wiDotWh = dot(wi, wh);
            float nsDotWh = dot(ns, wh);
            float nsDotWi = dot(ns, wi);

            // See 5.7 Fresnel-Schlick Approximation
            vec3 F = FresnelSchlick(abs(wiDotWh), F0);

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

            vec3 transmission;
            if (specularMode == 0) {
                /* 
                 * GGX VNDF importance sampling
                 * See 5.8 GGX VNDF Importance Sampling
                 */

                transmission = (1.0 - F) * (G2 / max(G1, EPSILON));
            } else if (specularMode == 1) {
                /*
                 * Cosine-weighted hemisphere sampling
                 * See 5.3 Cosine-Weighted Hemisphere Sampling
                 */

                float D = TrowbridgeReitzGgx(max(nsDotWh, 0.0), alpha);
                transmission = vec3(D) * (1.0 - F) * G2 / max((4.0 * max(nsDotWo, 0.0) * max(nsDotWi, 0.0)), EPSILON);
            }

            // See 5.8 Microfacet Transmission
            float bsdfPdf = BtdfPdf(ns, wo, wi, alpha, si.eta_i, si.eta_t) * lobeProbs.transmission;

            bsdfSample.pdf = bsdfPdf;
            bsdfSample.f = transmission / lobeProbs.transmission;
            bsdfSample.wi = wi;
            bsdfSample.lobeType = 2; // Transmission

            return bsdfSample;
        } else {
            /* Diffuse lobe */

            bounceDepth.diffuse++;

            vec3 wi = CosineSampleHemisphere(rng, si);

            float nsDotWi = dot(ns, wi);

            if (nsDotWi <= 0.0) {
                // wi is below the hemisphere

                bsdfSample.f = vec3(0.0);
                bsdfSample.wi = wi;
                bsdfSample.pdf = 0.0;
                bsdfSample.lobeType = 0; // Diffuse

                return bsdfSample;
            }

            vec3 wh = normalize(wo + wi);

            float woDotWh = abs(dot(wo, wh));

            // See 5.7 Fresnel-Schlick Approximation
            vec3 F = FresnelSchlick(woDotWh, F0);

            /* Energy Conservation */

            vec3 diffuse = vec3(1.0) - F;
            diffuse *= 1.0 - mat.metallic;
            diffuse *= 1.0 - mat.transmission;
            // See 5.3 Cosine-Weighted Hemisphere Sampling
            diffuse *= mat.baseCol;

            float alpha = mat.roughness * mat.roughness;

            float specularPdf;
            if (specularMode == 0) {
                /* 
                 * GGX VNDF importance sampling
                 * See 5.8 GGX VNDF Importance Sampling
                 */

                specularPdf = GgxVndfPdf(ns, wo, wi, alpha) * lobeProbs.specular;
            } else if (specularMode == 1) {
                /*
                 * Cosine-weighted hemisphere sampling
                 * See 5.3 Cosine-Weighted Hemisphere Sampling
                 */

                specularPdf = CosineSampleHemispherePdf(max(nsDotWi, 0.0)) * lobeProbs.specular;
            }
            // See 5.3 Cosine-Weighted Hemisphere Sampling
            float diffusePdf = CosineSampleHemispherePdf(max(nsDotWi, 0.0)) * lobeProbs.diffuse;

            float bsdfPdf = specularPdf + diffusePdf;

            bsdfSample.pdf = bsdfPdf;
            bsdfSample.f = diffuse / lobeProbs.diffuse;
            bsdfSample.wi = wi;
            bsdfSample.lobeType = 0; // Diffuse

            return bsdfSample;
        }
    }
}

// See 5.12 BSDF Evaluation
vec3 EvaluateBsdf(vec3 wi, Ray ray, SurfaceInteraction si) {
    vec3 ns = si.ns;
    float nsDotWi = dot(ns, wi);
    if (nsDotWi > 0.0) {
        /*
         * Sample the BRDF
         * See 5.12 BSDF Evaluation
         */

        return EvaluateBrdf(wi, ray, si);
    } else {
        /*
         * Sample the BTDF
         * See 5.12 BSDF Evaluation
         */

        return EvaluateBtdf(wi, ray, si);
    }
}

// See 5.12 BSDF Evaluation
vec3 EvaluateBsdfAndPdf(vec3 wi, Ray ray, SurfaceInteraction si, out float bsdfPdf) {
    float nsDotWi = dot(si.ns, wi);
    if (nsDotWi > 0.0) {
        /*
         * Sample the BRDF
         * See 5.12 BSDF Evaluation
         */

        return EvaluateBrdfAndPdf(wi, ray, si, bsdfPdf);
    } else {
        /*
         * Sample the BTDF
         * See 5.12 BSDF Evaluation
         */

        return EvaluateBtdfAndPdf(wi, ray, si, bsdfPdf);
    }
}

/* The following functions return a diffuse / specular BSDF split for AI denoising */

// See 5.12 BSDF Evaluation
BsdfSplit EvaluateBsdfSplit(vec3 wi, Ray ray, SurfaceInteraction si) {
    vec3 ns = si.ns;
    float nsDotWi = dot(ns, wi);
    if (nsDotWi > 0.0) {
        /*
         * Sample the BRDF
         * See 5.12 BSDF Evaluation
         */

        return EvaluateBrdfSplit(wi, ray, si);
    } else {
        /*
         * Sample the BTDF
         * See 5.12 BSDF Evaluation
         */

        return EvaluateBtdfSplit(wi, ray, si);
    }
}

// See 5.12 BSDF Evaluation
BsdfSplit EvaluateBsdfAndPdfSplit(vec3 wi, Ray ray, SurfaceInteraction si, out float bsdfPdf) {
    float nsDotWi = dot(si.ns, wi);
    if (nsDotWi > 0.0) {
        /*
         * Sample the BRDF
         * See 5.12 BSDF Evaluation
         */

        return EvaluateBrdfAndPdfSplit(wi, ray, si, bsdfPdf);
    } else {
        /*
         * Sample the BTDF
         * See 5.12 BSDF Evaluation
         */

        return EvaluateBtdfAndPdfSplit(wi, ray, si, bsdfPdf);
    }
}


#endif
