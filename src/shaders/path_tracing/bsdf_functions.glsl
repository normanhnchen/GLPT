#ifndef BSDF_FUNCTIONS_GLSL
#define BSDF_FUNCTIONS_GLSL


#include "src/shaders/common.glsl"


// Method toggling (switch out for uniforms and UI later)

// 0: GGX VNDF Importance Sample
// 1: Cosine Hemisphere Sampling
int specularMode = 0;
// 0: Height-Correlated Smith Method
// 1: Schlick-GGX Approximation Method
int geometryMode = 0;
// 0: Beer-Lambert
// 1: No Beer-Lambert
int transmissionMode = 1;


// https://pema.dev/obsidian/math/light-transport/cosine-weighted-sampling.html
vec3 CosineSampleHemisphere(inout uvec3 rng, SurfaceInteraction si) {
    vec3 Xi = Pcg3d(rng);
    float Xi1 = Xi.x;
    float Xi2 = Xi.y;

    float theta = acos(sqrt(Xi1));
    float phi = 2.0 * PI * Xi2;
    
    // Sample in local space
    vec3 wo = vec3(
        sin(theta) * cos(phi),
        sin(theta) * sin(phi),
        cos(theta)
    );

    // Transform to world space
    return normalize(si.localToWorld * wo);
}

// https://learnopengl.com/PBR/Theory
float DistributionGgx(vec3 n, vec3 wh, float alpha) {
    float alpha2  = alpha * alpha;
    float nDotWh  = max(dot(n, wh), 0.0);
    float nDotWh2 = nDotWh * nDotWh;
	
    float nom   = alpha2;
    float denom = nDotWh2 * (alpha2 - 1.0) + 1.0;
    denom       = PI * denom * denom;
	
    // Clamp to prevent denom from clamping to 0.0 when underflowing (when roughness ~ 0.0)
    return nom / max(denom, 1e-4);
}

// https://learnopengl.com/PBR/Theory
float GeometrySchlickGGX(float nDotWo, float k) {
    float nom   = nDotWo;
    float denom = nDotWo * (1.0 - k) + k;
	
    return nom / denom;
}

// https://learnopengl.com/PBR/Theory
float GeometrySmith(vec3 n, vec3 wo, vec3 wi, float k) {
    float nDotWo = max(dot(n, wo), 0.0);
    float nDotWi = max(dot(n, wi), 0.0);
    float ggx1 = GeometrySchlickGGX(nDotWo, k);
    float ggx2 = GeometrySchlickGGX(nDotWi, k);
	
    return ggx1 * ggx2;
}

// https://schuttejoe.github.io/post/ggximportancesamplingpart2/
float SmithGgxMasking(vec3 wi, vec3 wo, vec3 n, float alpha2) {
    float nDotWi = abs(dot(n, wi));
    float nDotWo = abs(dot(n, wo));
    float denomC = sqrt(alpha2 + (1.0 - alpha2) * nDotWo * nDotWo) + nDotWo;

    return 2.0 * nDotWo / denomC;
}

// https://schuttejoe.github.io/post/ggximportancesamplingpart2/
float SmithGgxMaskingShadowing(vec3 wi, vec3 wo, vec3 n, float alpha2) {
    float nDotWi = abs(dot(n, wi));
    float nDotWo = abs(dot(n, wo));

    float denomA = nDotWo * sqrt(alpha2 + (1.0 - alpha2) * nDotWi * nDotWi);
    float denomB = nDotWi * sqrt(alpha2 + (1.0 - alpha2) * nDotWo * nDotWo);

    return 2.0 * nDotWi * nDotWo / (denomA + denomB);
}

// https://learnopengl.com/PBR/Theory
vec3 FresnelSchlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

// https://schuttejoe.github.io/post/ggximportancesamplingpart2/
vec3 ImportanceSampleGgxVndf(vec2 Xi, vec3 wo, float roughness) {
    // Stretch the view vector as if roughness = 1
    wo = normalize(vec3(
        wo.x * roughness,
        wo.y * roughness,
        wo.z
    ));

    // Build an orthonormal basis (ONB)
    vec3 helper = abs(wo.z) > 0.999 ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 0.0, 1.0);
    vec3 t1 = normalize(cross(helper, wo));
    vec3 t2 = cross(wo, t1);

    // Choose a point on a disk with each half of the disk weighted
    // proportionally to its projection onto direction wo
    float a = 1.0 / (1.0 + wo.z);
    float r = sqrt(Xi.x);
    float phi = (Xi.y < a) ? (Xi.y / a) * PI : PI + (Xi.y - a) / (1.0 - a) * PI;
    float p1 = r * cos(phi);
    float p2 = r * sin(phi) * ((Xi.y < a) ? 1.0 : wo.z);

    // Calculate the normal in stretched tangent space
    vec3 n = p1 * t1 + p2 * t2 + sqrt(max(0.0, 1.0 - p1 * p1 - p2 * p2)) * wo;

    // Unstretch and normalize the normal
    return normalize(vec3(
        roughness * n.x,
        roughness * n.y,
        max(0.0, n.z)
    ));
}

// Beer-Lambert law: light attenuates exponentially with distance traveled through a medium
// https://www.pbr-book.org/3ed-2018/Volume_Scattering/Volume_Scattering_Processes
void BeerLambert(inout bool insideMedium, inout vec3 entryPoint, SurfaceInteraction si, out vec3 transmittance, bool didRefract) {
    transmittance = vec3(1.0);

    bool isTransmission = si.mat.transmission > 0.0;
    bool isEntering = !si.isBackFace;
    bool isExiting = si.isBackFace;

    // Only apply when the material is transmissive and the ray is exiting the medium
    if (isTransmission) {
        if (isEntering && !insideMedium) {
            entryPoint = si.p;
            insideMedium = true;
        } else if (isExiting && didRefract && insideMedium) {
            if (transmissionMode == 0) {
                // Beer-Lambert
                // ------------
                float distTravelled = max(length(si.p - entryPoint), 1e-4);
                vec3 absorption = -log(max(si.mat.baseCol, 1e-4));
                transmittance = exp(-absorption * distTravelled);
            } else if (transmissionMode == 1) {
                transmittance = si.mat.baseCol;
            }

            insideMedium = false;
        }
    }
}

LobeProbs ComputeLobeProbs(Material mat, float nsDotWo, vec3 F0) {
    vec3 F_approx = FresnelSchlick(nsDotWo, F0);

    // AI method: average the Fresnel approximation for a single float probability
    float weight = (F_approx.r + F_approx.g + F_approx.b) / 3.0;
    
    LobeProbs lobeProbs;
    lobeProbs.specular = clamp(weight, 0.05, 0.95);
    lobeProbs.transmission = mat.transmission * (1.0 - lobeProbs.specular);
    // Fully metal objects cannot refract
    lobeProbs.transmission *= (1.0 - mat.metallic);
    lobeProbs.diffuse = 1.0 - lobeProbs.specular - lobeProbs.transmission;

    return lobeProbs;
}

float GgxVndfPdf(vec3 n, vec3 wo, vec3 wi, float alpha) {
    float nDotWo = abs(dot(n, wo));
    vec3 wh = normalize(wo + wi);
    float alpha2 = alpha * alpha;

    float D = DistributionGgx(n, wh, alpha);

    float G1;
    if (geometryMode == 0) {
        // Height-Correlated Smith Method
        // ------------------------------
        G1 = SmithGgxMasking(wi, wo, n, alpha2);
    } else {
        // Schlick-GGX Approximation Method
        // --------------------------------
        float roughness = sqrt(alpha);
        float k = (roughness + 1.0) * (roughness + 1.0) / 8.0;
        G1 = GeometrySchlickGGX(max(dot(n, wo), 1e-4), k);
    }

    return (D * G1) / max((4.0 * nDotWo), 1e-4);
}

float CosineSamplePdf(vec3 n, vec3 wi) {
    float nDotWi = max(dot(n, wi), 0.0);
    return nDotWi / PI;
}

// https://www.graphics.cornell.edu/~bjw/microfacetbsdf.pdf
float BtdfPdf(vec3 n, vec3 wo, vec3 wi, float alpha, float eta) {
    float nDotWo = abs(dot(n, wo));
    float alpha2 = alpha * alpha;

    vec3 wh = normalize(wo + eta * wi);
    if (dot(n, wh) < 0.0) wh = -wh;

    float D = DistributionGgx(n, wh, alpha);
    
    float G1;
    if (geometryMode == 0) {
        // Height-Correlated Smith Method
        // ------------------------------
        G1 = SmithGgxMasking(wi, wo, n, alpha2);
    } else {
        // Schlick-GGX Approximation Method
        // --------------------------------
        float roughness = sqrt(alpha);
        float k = (roughness + 1.0) * (roughness + 1.0) / 8.0;
        G1 = GeometrySchlickGGX(max(dot(n, wo), 1e-4), k);
    }

    float woDotWh = dot(wo, wh);
    float wiDotWh = dot(wi, wh);

    float denom = woDotWh + eta * wiDotWh;
    float dwh_dwi = abs((eta * eta * wiDotWh) / max(denom * denom, 0.0001));
    return D * G1 * abs(woDotWh) / max(nDotWo, 0.0001) * dwh_dwi;
}

float BsdfPdf(vec3 wi, Ray ray, SurfaceInteraction si) {
    Material mat = si.mat;
    vec3 ns = si.ns;
    vec3 wo = -ray.d;

    float nsDotWo = abs(dot(ns, wo));

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, mat.baseCol, mat.metallic);
    
    LobeProbs lobeProbs = ComputeLobeProbs(mat, nsDotWo, F0);

    float nsDotWi = dot(ns, wi);

    float alpha = mat.roughness * mat.roughness;

    if (nsDotWi > 0.0) {
        float specularPdf;
        if (specularMode == 0) {
            specularPdf = GgxVndfPdf(ns, wo, wi, alpha) * lobeProbs.specular;
        } else if (specularMode == 1) {
            specularPdf = CosineSamplePdf(ns, wi) * lobeProbs.specular;
        }

        float diffusePdf = CosineSamplePdf(ns, wi) * lobeProbs.diffuse;

        return specularPdf + diffusePdf;
    } else {
        return BtdfPdf(ns, wo, wi, alpha, si.eta) * lobeProbs.transmission;
    }
}

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
            G1 = SmithGgxMasking(wi, wo, ns, alpha2);
            G2 = SmithGgxMaskingShadowing(wi, wo, ns, alpha2);
        } else {
            // Schlick-GGX Approximation Method
            // --------------------------------
            float k = (mat.roughness + 1.0) * (mat.roughness + 1.0) / 8.0;
            G1 = GeometrySchlickGGX(max(dot(ns, wo), 1e-4), k);
            G2 = GeometrySmith(ns, wo, wi, k);
        }

        vec3 specular;
        if (specularMode == 0) {
            specular = F * (G2 / max(G1, 1e-4));
        } else if (specularMode == 1) {
            float D = DistributionGgx(ns, wh, alpha);
            float nDotWo = max(dot(ns, wo), 1e-4);
            float nDotWi = max(dot(ns, wi), 1e-4);
            specular = vec3(D) * F * G2 * PI / (4.0 * nDotWo * nDotWi);
        }
        

        bsdfSample.pdf = BsdfPdf(wi, ray, si);
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

            vec3 wi = refract(ray.d, wh, si.eta);

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
                    G1 = SmithGgxMasking(wi, wo, ns, alpha2);
                    G2 = SmithGgxMaskingShadowing(wi, wo, ns, alpha2);
                } else {
                    // Schlick-GGX Approximation Method
                    // --------------------------------
                    float k = (mat.roughness + 1.0) * (mat.roughness + 1.0) / 8.0;
                    G1 = GeometrySchlickGGX(max(dot(ns, wo), 1e-4), k);
                    G2 = GeometrySmith(ns, wo, wi, k);
                }

                vec3 specular;
                if (specularMode == 0) {
                    specular = F * (G2 / max(G1, 1e-4));
                } else if (specularMode == 1) {
                    float D = DistributionGgx(ns, wh, alpha);
                    float nDotWo = max(dot(ns, wo), 1e-4);
                    float nDotWi = max(dot(ns, wi), 1e-4);
                    specular = vec3(D) * F * G2 * PI / max((4.0 * nDotWo * nDotWi), 1e-4);
                }

                bsdfSample.f = specular / lobeProbs.transmission;
                bsdfSample.wi = wi;
                bsdfSample.pdf = BsdfPdf(wi, ray, si);

                return bsdfSample;
            }

            bsdfSample.f = vec3(1.0) / lobeProbs.transmission;
            bsdfSample.wi = wi;
            bsdfSample.pdf = BsdfPdf(wi, ray, si);

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

            bsdfSample.f = diffuse / lobeProbs.diffuse;
            bsdfSample.wi = wi;
            bsdfSample.pdf = BsdfPdf(wi, ray, si);

            return bsdfSample;
        }
    }
}


#endif
