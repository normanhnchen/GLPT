#ifndef MICROFACET_GLSL
#define MICROFACET_GLSL


#include "src/shaders/common.glsl"


// See 5.3 Cosine-Weighted Hemisphere Sampling
vec3 CosineSampleHemisphere(inout uvec3 rng, SurfaceInteraction si) {
    vec2 xy = UniformSampleUnitDisk(rng);
    float x = xy.x;
    float y = xy.y;

    // Malley's Method
    float z = sqrt(max(1.0 - x * x - y * y, 0.0));

    vec3 wo = vec3(x, y, z);

    // Transform to world space
    return normalize(si.localToWorld * wo);
}

// See 5.3 Cosine-Weighted Hemisphere Sampling
float CosineSampleHemispherePdf(float nDotWi) {
    return nDotWi / PI;
}

// See 5.4 Trowbridge-Reitz GGX
float TrowbridgeReitzGgx(float nDotWh, float alpha) {
    float alpha2  = alpha * alpha;
    float nDotWh2 = nDotWh * nDotWh;
	
    float numer = alpha2;
    float denom = nDotWh2 * (alpha2 - 1.0) + 1.0;
    denom       = PI * denom * denom;
	
    // Note that the denominator clamp is essential
    // for surfaces with roughness ~ 0 because the
    // denominator can underflow to 0.0
    return numer / max(denom, EPSILON);
}

// See 5.5 Schlick-GGX Approximation
float GeometrySchlickGgx(float nDotWo, float k) {
    float numer = nDotWo;
    float denom = nDotWo * (1.0 - k) + k;

    return numer / max(denom, EPSILON);
}

// See 5.5 Schlick-GGX Approximation
float GeometrySmith(float nDotWo, float nDotWi, float k) {
    float ggx1 = GeometrySchlickGgx(nDotWo, k);
    float ggx2 = GeometrySchlickGgx(nDotWi, k);
	
    return ggx1 * ggx2;
}

// See 5.6 Height-Correlated Smith
float SmithGgxMasking(float nDotWo, float alpha2) {
    float denom = sqrt(alpha2 + (1.0 - alpha2) * nDotWo * nDotWo) + nDotWo;

    return 2.0 * nDotWo / max(denom, EPSILON);
}

// See 5.6 Height-Correlated Smith
float SmithGgxMaskingShadowing(float nDotWi, float nDotWo, float alpha2) {
    float denomA = nDotWo * sqrt(alpha2 + (1.0 - alpha2) * nDotWi * nDotWi);
    float denomB = nDotWi * sqrt(alpha2 + (1.0 - alpha2) * nDotWo * nDotWo);

    return 2.0 * nDotWi * nDotWo / max(denomA + denomB, EPSILON);
}

// See 5.7 Fresnel-Schlick Approximation
vec3 FresnelSchlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(1.0 - clamp(cosTheta, 0.0, 1.0), 5.0);
}

// See 5.8 GGX VNDF Importance Sampling
vec3 ImportanceSampleGgxVndf(SurfaceInteraction si, vec2 Xi, vec3 wo, float roughness) {
    // Convert wo to tangent space for GGX VNDF importance sampling
    vec3 woTangent = si.worldToLocal * wo;
    
    // Stretch the view into the hemisphere configuration
    vec3 Vh = normalize(vec3(
        woTangent.x * roughness,
        woTangent.y * roughness,
        woTangent.z
    ));

    // Orthonormal basis
    // T1 must be the tangent plane orthogonal to Z = (0, 0, 1)
    // so a typical ONB function doesn't necessarily work
    float lensq = Vh.x * Vh.x + Vh.y * Vh.y;
    vec3 t1 = (lensq > 0.0) ? vec3(-Vh.y, Vh.x, 0.0) * inversesqrt(lensq) : vec3(1.0, 0.0, 0.0);
    vec3 t2 = cross(Vh, t1);

    // Sample the projected area of the hemisphere
    float r = sqrt(Xi.x);
    float phi = 2.0 * PI * Xi.y;
    float p1 = r * cos(phi);
    float p2 = r * sin(phi);
    float s = 0.5 * (1.0 + Vh.z);
    p2 = (1.0 - s) * sqrt(1.0 - p1 * p1) + s * p2;

    // Reproject onto the hemisphere
    vec3 wm = p1 * t1 + p2 * t2 + sqrt(max(0.0, 1.0 - p1 * p1 - p2 * p2)) * Vh;

    // Unstretch the normal back into the ellipsoid configuration
    wm = normalize(vec3(
        roughness * wm.x,
        roughness * wm.y,
        max(0.0, wm.z)
    ));

    // Transform wm from tangent sapce back to world space
    return normalize(si.localToWorld * wm);
}

// See 5.8 GGX VNDF Importance Sampling
float GgxVndfPdf(vec3 n, vec3 wo, vec3 wi, float alpha) {
    float nDotWo = dot(n, wo);
    vec3 wh = normalize(wo + wi);
    float alpha2 = alpha * alpha;

    float nDotWh = dot(n, wh);

    // See 5.4 Trowbridge-Reitz GGX
    float D = TrowbridgeReitzGgx(nDotWh, alpha);

    float G1;
    if (geometryMode == 0) {
        /*
         * Height-correlated Smith method
         * See 5.6 Height-Correlated Smith
         */

        G1 = SmithGgxMasking(abs(nDotWo), alpha2);
    } else {
        /*
         * Schlick-GGX approximation method
         * See 5.5 Schlick-GGX Approximation
         */
        
        float roughness = sqrt(alpha);
        float k = (roughness + 1.0) * (roughness + 1.0) / 8.0;
        G1 = GeometrySchlickGgx(max(dot(n, wo), EPSILON), k);
    }

    return (D * G1) / max((4.0 * abs(nDotWo)), EPSILON);
}

// See 5.10 Lobe Selection
LobeProbs ComputeLobeProbs(Material mat, float nsDotWo, vec3 F0) {
    // See 5.7 Fresnel-Schlick Approximation
    vec3 F = FresnelSchlick(nsDotWo, F0);
    // See 2.3 Firefly Clamping
    float weight = GetLuminance(F);

    float pSpec = clamp(weight, 0.05, 0.95);
    pSpec = mix(pSpec, 1.0, mat.metallic);
    float pTrans = (1.0 - pSpec) * mat.transmission;
    float pDiff = 1.0 - pSpec - pTrans;
    
    LobeProbs lobeProbs;
    lobeProbs.specular = pSpec;
    lobeProbs.transmission = pTrans;
    lobeProbs.diffuse = pDiff;

    return lobeProbs;
}


#endif
