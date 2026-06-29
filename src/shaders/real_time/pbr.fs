#version 460 core

in vec2 texCoords;
in vec3 worldPos;
in vec3 normal;
in vec3 tangent;
in vec3 bitangent;
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

struct Light {
    vec3 col;
    int type; // Point: 0, directional: 1, spot: 2
    vec3 pos;
    float intensity;
    vec3 dir;
    float range;
    int isSpot;
    float innerConeAngle;
    float outerConeAngle;
    float pad1;
};

layout (std430, binding = 0) buffer MaterialBuffer {
    Material materials[];
};

layout (std430, binding = 0) buffer LightBuffer {
    Light lights[];
};

layout(binding = 0) uniform sampler2DArray baseColorTextures;
layout(binding = 1) uniform sampler2DArray emissiveTextures;
layout(binding = 2) uniform sampler2DArray roughnessTextures;
layout(binding = 3) uniform sampler2DArray metallicTextures;
layout(binding = 4) uniform sampler2DArray normalTextures;
layout(binding = 5) uniform sampler2DArray occlusionTextures;

#define PI 3.14159265359

uniform vec3 cameraPos;

void main() {
    Material mat = materials[matId];
    if (mat.hasBaseColTex == 1) {
        vec4 baseCol = texture(baseColorTextures, vec3(texCoords, mat.baseTexId));
        mat.baseCol = baseCol.rgb;
        mat.alpha = baseCol.w;
    }
    if (mat.hasEmissiveTex == 1) {
        mat.emissive = texture(emissiveTextures, vec3(texCoords, mat.emissiveTexId)).rgb;
    }
    if (mat.hasRoughTex == 1) {
        mat.roughness = texture(roughnessTextures, vec3(texCoords, mat.roughTexId)).r;
    }
    if (mat.hasMetalTex == 1) {
        mat.metallic = texture(metallicTextures, vec3(texCoords, mat.metalTexId)).r;
    }
    mat3 TBN;
    mat3 invTBN;
    // https://learnopengl.com/Advanced-Lighting/Normal-Mapping
    if (mat.hasNormalTex == 1) {
        TBN = mat3(tangent, bitangent, normal);
        // Get normal in world space
        vec3 normal = texture(normalTextures, vec3(texCoords, mat.normalTexId)).rgb;
        normal = normal * 2.0 - 1.0;
        normal = normalize(TBN * normal);

        vec3 N = normal;

        // Build an Orthonormal basis (ONB)
        vec3 helper = abs(N.z) > 0.999 ? vec3(0, 1, 0) : vec3(0, 0, 1);
        vec3 T = normalize(cross(helper, N));
        vec3 B = cross(N, T);

        TBN = mat3(T, B, N);
        invTBN = transpose(TBN);
    } else {
        vec3 N = normal;

        // Build an Orthonormal basis (ONB)
        vec3 helper = abs(N.z) > 0.999 ? vec3(0, 1, 0) : vec3(0, 0, 1);
        vec3 T = normalize(cross(helper, N));
        vec3 B = cross(N, T);

        TBN = mat3(T, B, N);
        invTBN = transpose(TBN);
    }
    if (mat.hasOcclTex == 1) {
        // No implementation currently
    }

    fragColor.rgb = mat.baseCol * normal * TBN;
}
