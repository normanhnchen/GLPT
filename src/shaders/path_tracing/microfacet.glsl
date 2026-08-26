#ifndef MICROFACET_GLSL
#define MICROFACET_GLSL


#include "src/shaders/common.glsl"


// Adaptation from "Cosine-Weighted Hemisphere Sampling," Physically Based Rendering: From Theory to Implementation
// https://www.pbr-book.org/3ed-2018/Monte_Carlo_Integration/2D_Sampling_with_Multidimensional_Transformations#Cosine-WeightedHemisphereSampling
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

// Adaptation from "Cosine-Weighted Hemisphere Sampling," Physically Based Rendering: From Theory to Implementation
// https://www.pbr-book.org/3ed-2018/Monte_Carlo_Integration/2D_Sampling_with_Multidimensional_Transformations#Cosine-WeightedHemisphereSampling
float CosineSampleHemispherePdf(vec3 n, vec3 wi) {
    float cosTheta = max(dot(n, wi), 0.0);
    return cosTheta / PI;
}

// Adaptation from "Average irregularity representation of a rough surface for ray reflection,"
// https://doi.org/10.1364/JOSA.65.000531
float TrowbridgeReitzGgx(vec3 n, vec3 wh, float alpha) {
    float alpha2  = alpha * alpha;
    float nDotWh  = max(dot(n, wh), 0.0);
    float nDotWh2 = nDotWh * nDotWh;
	
    float numer = alpha2;
    float denom = nDotWh2 * (alpha2 - 1.0) + 1.0;
    denom       = PI * denom * denom;
	
    // Clamp to prevent division by zero
    return numer / max(denom, EPSILON);
}

// "Real Shading in Unreal Engine 4,"
// https://blog.selfshadow.com/publications/s2013-shading-course/karis/s2013_pbs_epic_notes_v2.pdf
float GeometrySchlickGgx(float nDotWo, float k) {
    float numer = nDotWo;
    float denom = nDotWo * (1.0 - k) + k;

    return numer / denom;
}

// "Real Shading in Unreal Engine 4,"
// https://blog.selfshadow.com/publications/s2013-shading-course/karis/s2013_pbs_epic_notes_v2.pdf
float GeometrySmith(vec3 n, vec3 wo, vec3 wi, float k) {
    float nDotWo = max(dot(n, wo), 0.0);
    float nDotWi = max(dot(n, wi), 0.0);
    float ggx1 = GeometrySchlickGgx(nDotWo, k);
    float ggx2 = GeometrySchlickGgx(nDotWi, k);
	
    return ggx1 * ggx2;
}

// "Understanding the Masking-Shadowing Function in Microfacet-Based BRDFs,"
// Journal of Computer Graphics Techniques
// https://jcgt.org/published/0003/02/03/
// "Importance Sampling techniques for GGX with Smith Masking-Shadowing: Part 2," Joe Schutte's Blog,
// https://schuttejoe.github.io/post/ggximportancesamplingpart2/.
float SmithGgxMasking(vec3 wo, vec3 n, float alpha2) {
    float nDotWo = abs(dot(n, wo));
    float denomC = sqrt(alpha2 + (1.0 - alpha2) * nDotWo * nDotWo) + nDotWo;

    return 2.0 * nDotWo / denomC;
}

// "Understanding the Masking-Shadowing Function in Microfacet-Based BRDFs,"
// Journal of Computer Graphics Techniques
// https://jcgt.org/published/0003/02/03/
// "Importance Sampling techniques for GGX with Smith Masking-Shadowing: Part 2," Joe Schutte's Blog,
// https://schuttejoe.github.io/post/ggximportancesamplingpart2/.
float SmithGgxMaskingShadowing(vec3 wi, vec3 wo, vec3 n, float alpha2) {
    float nDotWi = abs(dot(n, wi));
    float nDotWo = abs(dot(n, wo));

    float denomA = nDotWo * sqrt(alpha2 + (1.0 - alpha2) * nDotWi * nDotWi);
    float denomB = nDotWi * sqrt(alpha2 + (1.0 - alpha2) * nDotWo * nDotWo);

    return 2.0 * nDotWi * nDotWo / (denomA + denomB);
}

// "Fresnel Incidence Effects," in Physically Based Rendering: From Theory to Implementation
// https://pbr-book.org/3ed-2018/Reflection_Models/Fresnel_Incidence_Effects
vec3 FresnelSchlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

// "Sampling the GGX Distribution of Visible Normals," Journal of Computer Graphics Techniques (JCGT)
// http://jcgt.org/published/0007/04/01/
vec3 ImportanceSampleGgxVndf(vec2 Xi, vec3 wo, float roughness) {
    // Stretch the view into the hemisphere configuration
    vec3 Vh = normalize(vec3(
        wo.x * roughness,
        wo.y * roughness,
        wo.z
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
    return normalize(vec3(
        roughness * wm.x,
        roughness * wm.y,
        max(0.0, wm.z)
    ));
}

float GgxVndfPdf(vec3 n, vec3 wo, vec3 wi, float alpha) {
    float nDotWo = abs(dot(n, wo));
    vec3 wh = normalize(wo + wi);
    float alpha2 = alpha * alpha;

    float D = TrowbridgeReitzGgx(n, wh, alpha);

    float G1;
    if (geometryMode == 0) {
        /* Height-correlated Smith method */

        G1 = SmithGgxMasking(wo, n, alpha2);
    } else {
        /* Schlick-GGX approximation method */
        
        float roughness = sqrt(alpha);
        float k = (roughness + 1.0) * (roughness + 1.0) / 8.0;
        G1 = GeometrySchlickGgx(max(dot(n, wo), EPSILON), k);
    }

    return (D * G1) / max((4.0 * nDotWo), EPSILON);
}

LobeProbs ComputeLobeProbs(Material mat, float nsDotWo, vec3 F0) {
    vec3 F = FresnelSchlick(nsDotWo, F0);
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
