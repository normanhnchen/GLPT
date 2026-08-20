#ifndef STRUCTS_GLSL
#define STRUCTS_GLSL


struct Vertex {
    vec3 pos;
    float pad1;
    vec2 uv;
    vec2 pad2;
    vec3 n;
    float pad3;
    vec3 dpdu;
    float pad4;
    vec3 dpdv;
    float pad5;
};

struct Material {
    // Basic material
    // --------------
    vec3 baseCol;
    float alpha;
    vec3 emissive;
    float metallic;
    float roughness;
    float ao;
    // Settings
    // --------
    int alphaMode; // 0=OPAQUE, 1=MASK, or 2=BLEND
    float alphaCutoff;
    int doubleSided;
    // Flags
    // -----
    int hasEmission;
    int hasBaseColTex;
    int hasEmissiveTex;
    int hasRoughTex;
    int hasMetalTex;
    int hasNormalTex;
    int hasOcclTex;
    // Texture IDs
    // -----------
    int baseTexId;
    int emissiveTexId;
    int roughTexId;
    int metalTexId;
    int normalTexId;
    int occlTexId;
    // glTF extensions
    // ---------------
    float emissiveStrength;
    float transmission;
    float ior;
    float pad1;
    float pad2;
    float pad3;
};

struct Triangle {
    Vertex v0, v1, v2;
    int matId;
    float area; // -1 if not emissive
    float lightPmf;
    float pad1;
};

struct BvhNode {
    vec3 aabbMin;
    int leftChildId;
    vec3 aabbMax;
    int rightChildId;
    int firstTriId;
    int triCount;
    int isLeaf;
    float pad1;
};

struct Light {
    vec3 col;
    int type; // Point: 0, directional: 1, spot: 2
    vec3 pos;
    float intensity;
    vec3 d;
    float range;
    int isSpot;
    float innerConeAngle;
    float outerConeAngle;
    float lightPmf;
};

struct FiniteLight {
    int lightId;
    float q;
    float p;
    int alias;
};

struct EmissiveTriangle {
    int triId;
    float q;
    float p;
    int alias;
};

struct Ray {
    vec3 o;
    vec3 d;
    vec3 col;
};

struct SurfaceInteraction {
    vec3 p;
    vec3 ng;
    vec3 ns;
    vec3 dpdu;
    vec3 dpdv;
    mat3 localToWorld;
    mat3 worldToLocal;
    vec2 bary;
    vec2 uv;
    Material mat;
    float eta;
    float t;
    int triId;
    bool isBackFace;
    // Only used for emissive triangles
    float area;
    // Track BVH node checks
    int nodesVisited;
};

struct VisibilityInteraction {
    float t;
    bool isBackFace;
};

struct LobeProbs {
    float specular;
    float diffuse;
    float transmission;
};

struct BounceDepth {
    int diffuse;
    int specular;
    int transmission;
};

struct BsdfSample {
    vec3 f;
    vec3 wi;
    float pdf;
};

struct PathSample {
    vec3 combined;
    vec3 baseCol;
    vec3 normal;
    float depth;
};

struct AabbHit {
    bool hit;
    float tNear;
};


#endif
