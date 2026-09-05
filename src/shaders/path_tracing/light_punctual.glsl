#ifndef LIGHT_PUNCTUAL_GLSL
#define LIGHT_PUNCTUAL_GLSL


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/util.glsl"


// See 7.4 Power Sampling
Light PowerFinitePunctualLightSample(float Xi, out float lightPdf) {
    /* Sample from the precomputed alias table */
    
    int offset = min(int(Xi * numFiniteLights), numFiniteLights - 1);
    float up = min(Xi * numFiniteLights - offset, 1.0 - EPSILON);

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

// See 7.5 Punctual Lights
BsdfSplit SampleFinitePunctualLight(SurfaceInteraction si, Ray ray, inout uvec3 rng) {
    BsdfSplit bsdfSplit;
    bsdfSplit.diffuse = vec3(0.0);
    bsdfSplit.specular = vec3(0.0);

    if (numFiniteLights == 0) {
        return bsdfSplit;
    }

    // See 2.2 The PCG Hash
    vec3 Xi = Pcg3d(rng);

    // See 7.4 Power Sampling
    float lightPdf;
    Light light = PowerFinitePunctualLightSample(Xi.x, lightPdf);

    vec3 wi = normalize(light.pos - si.p);
    float dist = length(light.pos - si.p);
    vec3 Li;
    if (light.type == 0) {
        /* Point light */
        
        Li = light.col * light.intensity / max(dist * dist, EPSILON);
    } else if (light.type == 2) {
        /* Spotlight */

        float lightAngleScale = 1.0 / max(EPSILON, cos(light.innerConeAngle) - cos(light.outerConeAngle));
        float lightAngleOffset = -cos(light.outerConeAngle) * lightAngleScale;

        float cd = dot(normalize(-light.d), wi);
        float angularAttenuation = clamp(cd * lightAngleScale + lightAngleOffset, 0.0, 1.0);
        angularAttenuation *= angularAttenuation;
        float attenuation = angularAttenuation / max(dist * dist, EPSILON);

        Li = light.col * light.intensity * attenuation;
    }

    vec3 ns = si.ns;
    
    float nsDotWi = dot(ns, wi);
    
    if (si.mat.transmission == 0.0 && nsDotWi <= 0.0) {
        // Light is blocked from passing through
        return bsdfSplit;
    }

    // See 7.2 Shadow Rays
    VisibilityInteraction vi = ShadowRayTest(rng, si, dist, wi);
    if (vi.isOccluded) {
        return bsdfSplit;
    }

    // See 5.12 BSDF Evaluation
    BsdfSplit f = EvaluateBsdfSplit(wi, ray, si);

    vec3 Le = Li / lightPdf;

    bsdfSplit.diffuse = f.diffuse * Le;
    bsdfSplit.specular = f.specular * Le;

    return bsdfSplit;
}

// See 7.5 Punctual Lights
BsdfSplit SampleInfinitePunctualLight(SurfaceInteraction si, Ray ray, Light light, inout uvec3 rng) {
    BsdfSplit bsdfSplit;
    bsdfSplit.diffuse = vec3(0.0);
    bsdfSplit.specular = vec3(0.0);

    vec3 wi = normalize(-light.d);
    float dist = INF;
    vec3 Li = light.col * light.intensity;

    vec3 ns = si.ns;
    
    float nsDotWi = dot(ns, wi);
    
    if (si.mat.transmission == 0.0 && nsDotWi <= 0.0) {
        // Light is blocked from passing through
        return bsdfSplit;
    }

    // See 7.2 Shadow Rays
    VisibilityInteraction vi = ShadowRayTest(rng, si, dist, wi);
    if (vi.isOccluded) {
        return bsdfSplit;
    }

    // See 5.12 BSDF Evaluation
    BsdfSplit f = EvaluateBsdfSplit(wi, ray, si);

    bsdfSplit.diffuse = f.diffuse * Li;
    bsdfSplit.specular = f.specular * Li;

    return bsdfSplit;
}


#endif