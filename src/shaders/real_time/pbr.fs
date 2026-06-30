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
    float ao;
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
    float pad1;
    float pad2;
    float pad3;
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

layout (std430, binding = 1) buffer LightBuffer {
    Light lights[];
};

layout(binding = 0) uniform sampler2DArray baseColorTextures;
layout(binding = 1) uniform sampler2DArray emissiveTextures;
layout(binding = 2) uniform sampler2DArray roughnessTextures;
layout(binding = 3) uniform sampler2DArray metallicTextures;
layout(binding = 4) uniform sampler2DArray normalTextures;
layout(binding = 5) uniform sampler2DArray occlusionTextures;

// layout(binding = 6) uniform sampler2D hdri;

layout(binding = 7) uniform samplerCube irradianceMap;

#define PI 3.14159265359

uniform int numLights;

uniform vec3 cameraPos;

// https://learnopengl.com/PBR/Theory
float DistributionGGX(vec3 N, vec3 H, float a) {
    float a2     = a*a;
    float NdotH  = max(dot(N, H), 0.0);
    float NdotH2 = NdotH*NdotH;
	
    float nom    = a2;
    float denom  = (NdotH2 * (a2 - 1.0) + 1.0);
    denom        = PI * denom * denom;
	
    return nom / denom;
}

// https://learnopengl.com/PBR/Theory
float GeometrySchlickGGX(float NdotV, float k) {
    float nom   = NdotV;
    float denom = NdotV * (1.0 - k) + k;
	
    return nom / denom;
}

// https://learnopengl.com/PBR/Theory
float GeometrySmith(vec3 N, vec3 V, vec3 L, float k) {
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    float ggx1 = GeometrySchlickGGX(NdotV, k);
    float ggx2 = GeometrySchlickGGX(NdotL, k);
	
    return ggx1 * ggx2;
}

// https://learnopengl.com/PBR/Theory
vec3 fresnelSchlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

// https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_lights_punctual/README.md
// https://www.pbr-book.org/4ed/Light_Sources/Point_Lights
void SampleLight(Light light, out vec3 L, out vec3 radiance) {
    // Directional
    if (light.type == 1) {
        L = normalize(-light.dir);
        radiance = light.col * light.intensity;
        return;
    }

    L = normalize(light.pos - worldPos);
    float dist = length(light.pos - worldPos);

    // Prevent division by zero
    float attenuation = 1.0 / max(dist * dist, 0.0001);

    // Point
    if (light.type == 0) {
        radiance = light.col * light.intensity * attenuation;
        radiance /= 4.0 * PI * 100.0;
        return;
    } 
    
    // Spot

    float lightAngleScale = 1.0 / max(0.001, cos(light.innerConeAngle) - cos(light.outerConeAngle));
    float lightAngleOffset = -cos(light.outerConeAngle) * lightAngleScale;

    float cd = dot(normalize(-light.dir), L);
    float angularAttenuation = clamp(cd * lightAngleScale + lightAngleOffset, 0.0, 1.0);
    angularAttenuation *= angularAttenuation;
    attenuation *= angularAttenuation;

    radiance = light.col * light.intensity * attenuation;
    radiance /= 4.0 * PI * 100.0;
}

// https://learnopengl.com/PBR/Theory
// https://learnopengl.com/PBR/IBL/Diffuse-irradiance
vec3 SamplePBR(vec3 N, Material mat) {
    vec3 V = normalize(vec3(cameraPos - worldPos));

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, mat.baseCol, mat.metallic);

    // Total radiance
    vec3 Lo = vec3(0.0);
    // Reflectance equation for direct lighting
    for (int i = 0; i < numLights; i++) {
        Light light = lights[i];
        // Calculate radiance
        vec3 L;
        vec3 radiance;
        SampleLight(light, L, radiance);
        vec3 H = normalize(V + L);

        float a = mat.roughness * mat.roughness;
        float k = (mat.roughness + 1.0) * (mat.roughness + 1.0) / 8.0;

        // Cook-Torrance BRDF terms
        float NDF = DistributionGGX(N, H, a);
        float G = GeometrySmith(N, V, L, k);
        vec3 F = fresnelSchlick(max(dot(H, V), 0.0), F0);

        vec3 kS = F;
        vec3 kD = vec3(1.0) - kS;
        kD *= 1.0 - mat.metallic;

        vec3 numerator = NDF * G * F;
        float denominator = 4.0 * max(dot(N, V), 0.0) * max(dot(N, L), 0.0) + 0.0001;
        vec3 specular = numerator / denominator;

        vec3 diffuse = kD * mat.baseCol / PI;

        float NdotL = max(dot(N, L), 0.0);

        vec3 brdf = diffuse + specular;

        Lo += brdf * radiance * NdotL;
    }

    vec3 kS = fresnelSchlick(max(dot(N, V), 0.0), F0);
    vec3 kD = 1.0 - kS;
    kD *= 1.0 - mat.metallic;	  
    vec3 irradiance = texture(irradianceMap, N).rgb;
    vec3 diffuse = irradiance * mat.baseCol;
    vec3 ambient = (kD * diffuse) * mat.ao;

    return Lo + ambient;
}

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
    vec3 N;
    vec3 T;
    vec3 B;
    // https://learnopengl.com/Advanced-Lighting/Normal-Mapping
    if (mat.hasNormalTex == 1) {
        N = normalize(normal);
        T = normalize(tangent);
        B = normalize(bitangent);
        mat3 TBN = mat3(T, B, N);
        // Get normal in world space
        N = texture(normalTextures, vec3(texCoords, mat.normalTexId)).rgb;
        N = N * 2.0 - 1.0;
        N = normalize(TBN * N);

        // Build an Orthonormal basis (ONB)
        vec3 helper = abs(N.z) > 0.999 ? vec3(0, 1, 0) : vec3(0, 0, 1);
        T = normalize(cross(helper, N));
        B = cross(N, T);

        TBN = mat3(T, B, N);
        mat3 invTBN = transpose(TBN);
    } else {
        N = normalize(normal);

        // Build an Orthonormal basis (ONB)
        vec3 helper = abs(N.z) > 0.999 ? vec3(0, 1, 0) : vec3(0, 0, 1);
        T = normalize(cross(helper, N));
        B = cross(N, T);

        mat3 TBN = mat3(T, B, N);
        mat3 invTBN = transpose(TBN);
    }
    if (mat.hasOcclTex == 1) {
        float ao = texture(occlusionTextures, vec3(texCoords, mat.occlTexId)).r;

        mat.ao = ao;
    }

    vec3 color = SamplePBR(N, mat);

    // Gamma correction
    vec3 finalColor = pow(color, vec3(1.0 / 2.2));
    fragColor = vec4(finalColor, 1.0);
}
