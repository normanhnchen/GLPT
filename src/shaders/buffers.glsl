#ifndef BUFFERS_GLSL
#define BUFFERS_GLSL


#include "src/shaders/structs.glsl"


layout(rgba32f, binding = 0) uniform image2D combinedPass;
layout(rgba32f, binding = 1) uniform image2D baseColorPass;
layout(rgba32f, binding = 2) uniform image2D normalPass;
layout(rgba32f, binding = 3) uniform image2D depthPass;

layout(std430, binding = 0) buffer CameraBuffer {
    vec3 pos;
    float aperture;
    vec3 front;
    float focusDist;
    vec3 up;
    int autoFocus;
    vec3 right;
    float fov;
} Camera;

layout(std430, binding = 1) buffer TriangleBuffer {
    Triangle triangles[];
};

layout(std430, binding = 2) buffer MaterialBuffer {
    Material materials[];
};

layout (std430, binding = 3) buffer LightBuffer {
    Light lights[];
};

layout(std430, binding = 4) buffer BvhNodesBuffer {
    BvhNode BvhNodes[];
};

layout(std430, binding = 5) buffer TriIndicesBuffer {
    int triIndices[];
};

layout(std430, binding = 6) buffer EmissiveTrianglesBuffer {
    EmissiveTriangle emissiveTriangles[];
};

layout(std430, binding = 7) buffer FiniteLightsBuffer {
    FiniteLight finiteLights[];
};

layout(binding = 0) uniform sampler2DArray baseColorTextures;
layout(binding = 1) uniform sampler2DArray emissiveTextures;
layout(binding = 2) uniform sampler2DArray roughnessTextures;
layout(binding = 3) uniform sampler2DArray metallicTextures;
layout(binding = 4) uniform sampler2DArray normalTextures;
layout(binding = 5) uniform sampler2DArray occlusionTextures;

layout(binding = 6) uniform sampler2D hdri;
layout(binding = 7) uniform sampler2D hdriRowCdf;
layout(binding = 8) uniform sampler2D hdriColCdf;


#endif
