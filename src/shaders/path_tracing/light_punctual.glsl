#ifndef LIGHT_PUNCTUAL_GLSL
#define LIGHT_PUNCTUAL_GLSL


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/util.glsl"


// "The Alias Method," in Physically Based Rendering: From Theory to Implementation
// https://pbr-book.org/4ed/Sampling_Algorithms/The_Alias_Method#AliasTable::Sample
Light PowerFinitePunctualLightSample(float Xi, out float lightPdf) {
    // Sample from the precomputed alias table weighted by power
    // ---------------------------------------------------------
    int offset = min(int(Xi * numFiniteLights), numFiniteLights - 1);
    float up = min(Xi * numFiniteLights - offset, ONE_MINUS_EPSILON);

    FiniteLight flOffset = finiteLights[offset];

    int finiteLightId;
    if (up < flOffset.q) {
        finiteLightId = offset;
        lightPdf = flOffset.p;
    } else {
        finiteLightId = flOffset.alias;
        lightPdf = finiteLights[finiteLightId].p;
    }

    int lightId = finiteLights[finiteLightId].lightId;
    return lights[lightId];
}

// The Khronos Group, "KHR_lights_punctual," in glTF 2.0 Extensions
// https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_lights_punctual/README.md
// "Light Sources," in Physically Based Rendering: From Theory to Implementation
// https://www.pbr-book.org/4ed/Light_Sources/Point_Lights#
vec3 SampleFinitePunctualLight(SurfaceInteraction si, Ray ray, inout uvec3 rng) {
    if (numFiniteLights == 0) {
        return vec3(0.0);
    }

    vec3 Xi = Pcg3d(rng);

    float lightPdf;
    Light light = PowerFinitePunctualLightSample(Xi.x, lightPdf);

    vec3 wi = normalize(light.pos - si.p);
    float dist = length(light.pos - si.p);
    vec3 Li;
    // Point
    if (light.type == 0) {
        Li = light.col * light.intensity / max(dist * dist, 0.0001);
    }
    // Spot
    else if (light.type == 2) {
        float lightAngleScale = 1.0 / max(0.001, cos(light.innerConeAngle) - cos(light.outerConeAngle));
        float lightAngleOffset = -cos(light.outerConeAngle) * lightAngleScale;

        float cd = dot(normalize(-light.d), wi);
        float angularAttenuation = clamp(cd * lightAngleScale + lightAngleOffset, 0.0, 1.0);
        angularAttenuation *= angularAttenuation;
        float attenuation = angularAttenuation / max(dist * dist, 0.0001);

        Li = light.col * light.intensity * attenuation;
    }

    vec3 ns = si.ns;
    
    float nsDotWi = dot(ns, wi);
    
    if (si.mat.transmission == 0.0 && nsDotWi <= 0.0) {
        return vec3(0.0);
    }

    VisibilityInteraction vi = ShadowRayTest(rng, si, dist, wi);
    if (vi.isOccluded) {
        return vec3(0.0);
    }

    vec3 f = EvaluateBsdf(wi, ray, si);
    return f * Li / lightPdf;
}

// The Khronos Group, "KHR_lights_punctual," in glTF 2.0 Extensions
// https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_lights_punctual/README.md
// "Light Sources," in Physically Based Rendering: From Theory to Implementation
// https://www.pbr-book.org/4ed/Light_Sources/Point_Lights#
vec3 SampleInfinitePunctualLight(SurfaceInteraction si, Ray ray, Light light, inout uvec3 rng) {
    vec3 wi = normalize(-light.d);
    float dist = INF;
    vec3 Li = light.col * light.intensity;

    vec3 ns = si.ns;
    
    float nsDotWi = dot(ns, wi);
    
    if (si.mat.transmission == 0.0 && nsDotWi <= 0.0) {
        return vec3(0.0);
    }

    VisibilityInteraction vi = ShadowRayTest(rng, si, dist, wi);
    if (vi.isOccluded) {
        return vec3(0.0);
    }

    vec3 f = EvaluateBsdf(wi, ray, si);
    return f * Li;
}


#endif