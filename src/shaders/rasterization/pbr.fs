#version 460 core

in vec2 texCoords;
in vec3 worldPos;
in vec3 normal;
flat in int matId;

out vec4 fragColor;

struct Material {
    // Basic material
    vec3 baseCol;
    float alpha;
    vec3 emissive;
    float metallic;
    float roughness;
    // Settings
    int alphaMode; // 0=OPAQUE, 1=MASK, or 2=BLEND
    float alphaCutoff;
    int doubleSided;
    // Flags
    int hasEmission;
    int hasBaseColTex;
    int hasEmissiveTex;
    int hasRoughTex;
    int hasMetalTex;
    int hasNormalTex;
    int hasOcclTex;
    // Texture IDs
    int baseTexId;
    int emissiveTexId;
    int roughTexId;
    int metalTexId;
    int normalTexId;
    int occlTexId;
    // glTF extensions
    float emissiveStrength;
    float transmission;
    float ior;
};

layout (std430, binding = 0) buffer MaterialBuffer {
    Material materials[];
};

layout(binding = 0) uniform sampler2DArray baseColorTextures;
layout(binding = 1) uniform sampler2DArray emissiveTextures;
layout(binding = 2) uniform sampler2DArray roughnessTextures;
layout(binding = 3) uniform sampler2DArray metallicTextures;
layout(binding = 4) uniform sampler2DArray normalTextures;
layout(binding = 5) uniform sampler2DArray occlusionTextures;

#define PI 3.14159265359

// uniform vec3 cameraPos;

void main() {
    Material mat = materials[matId];
    if (mat.hasBaseColTex == 1) {
        vec4 baseCol = texture(baseColorTextures, vec3(texCoords, mat.baseTexId));
        mat.baseCol = baseCol.rgb;
        mat.alpha = baseCol.w;
    }

    fragColor.rgb = mat.baseCol * normal;
}
