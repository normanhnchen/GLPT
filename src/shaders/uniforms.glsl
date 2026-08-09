#ifndef UNIFORMS_GLSL
#define UNIFORMS_GLSL


/*
 * ============
 * Path Tracing
 * ============
 */


// --- path_trace.comp ---

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


// --- final.fs ---

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


/*
 * =============
 * Rasterization
 * =============
 */


// --- pbr.fs ---

uniform int numLights;
uniform vec3 cameraPos;

// --- final.fs ---

// Uniforms previously defined
// -----------------------------------
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
