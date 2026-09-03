#ifndef UNIFORMS_GLSL
#define UNIFORMS_GLSL


/*
 * ============
 * Path Tracing
 * ============
 */


/* path_trace.comp */

uniform float aspectRatio;
// Top left corner of the current tile
uniform ivec2 uOffset;

uniform int samplesPerPixel;
uniform int totalSamples;
uniform float blur;
uniform float hdriExposure;

uniform int maxTotalBounces;
uniform int maxDiffuseBounces;
uniform int maxSpecularBounces;
uniform int maxTransmissionBounces;

uniform int numFiniteLights;
uniform int numEmissiveTriangles;

uniform int specularMode;
uniform int geometryMode;
uniform int transmissionMode;
uniform int misMode;

uniform int debugMode;

uniform int maxBvhDepth;

uniform int backfaceCulling;

uniform float maxDirectLuminance;
uniform float maxIndirectLuminance;
uniform float maxBsdfLuminance;


/* final.fs */

uniform sampler2D tex;

uniform float exposure;

uniform bool None;
uniform bool ACESFilm;
uniform bool AgX;
uniform bool AgXGolden;
uniform bool AgXPunchy;
uniform bool Filmic;
uniform bool Lottes;
uniform bool Neutral;
uniform bool Reinhard;
uniform bool Reinhard2;
uniform bool Uchimura;
uniform bool Uncharted2;
uniform bool Unreal;


/* bvh_bounds_debug.vs */
/* bvh_bounds_debug.fs */

uniform int bvhViewLayer;
uniform int bvhViewDepth;
uniform int bvhMaxNodeDepth;
uniform int bvhColorMode;


/*
 * =============
 * Rasterization
 * =============
 */


/* pbr.fs */

uniform int numLights;
uniform vec3 cameraPos;

/* final.fs */

/* Uniforms previously defined */

// uniform sampler2D tex;
// uniform float exposure;
// uniform bool None;
// uniform bool ACESFilm;
// uniform bool AgX;
// uniform bool AgXGolden;
// uniform bool AgXPunchy;
// uniform bool Filmic;
// uniform bool Lottes;
// uniform bool Neutral;
// uniform bool Reinhard;
// uniform bool Reinhard2;
// uniform bool Uchimura;
// uniform bool Uncharted2;
// uniform bool Unreal;


#endif
