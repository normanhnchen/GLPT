#ifndef MIS_FUNCTIONS_GLSL
#define MIS_FUNCTIONS_GLSL


#include "src/shaders/common.glsl"


// https://pbr-book.org/3ed-2018/Monte_Carlo_Integration/Importance_Sampling#MultipleImportanceSampling
float PowerHeuristic(int nf, float fPdf, int ng, float gPdf) {
    float f = float(nf) * fPdf;
    float g = float(ng) * gPdf;
    return (f * f) / (f * f + g * g);
}

// https://learnopengl.com/PBR/Theory
vec3 EvaluateBrdf(vec3 wi, Ray ray, SurfaceInteraction si) {
    Material mat = si.mat;

    vec3 ns = si.ns;
    vec3 wo = -ray.d;

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, mat.baseCol, mat.metallic);

    vec3 wh = normalize(wo + wi);

    float alpha = mat.roughness * mat.roughness;
    float alpha2 = alpha * alpha;

    vec3 F = FresnelSchlick(max(dot(wh, wo), 0.0), F0);
    float D = DistributionGgx(ns, wh, alpha);
    float G = SmithGgxMaskingShadowing(wi, wo, ns, alpha2);

    vec3 kS = F;
    vec3 kD = vec3(1.0) - kS;
    kD *= 1.0 - mat.metallic;
    kD *= 1.0 - mat.transmission;

    float nsDotWo = max(dot(ns, wo), 0.0);
    float nsDotWi = max(dot(ns, wi), 0.0);

    vec3 specular = (D * G * F) / max(4.0 * nsDotWo * nsDotWi, 0.0001);
    vec3 diffuse = kD * mat.baseCol / PI;

    vec3 brdf = (diffuse + specular) * nsDotWi;

    return brdf;
}

// https://www.graphics.cornell.edu/~bjw/microfacetbsdf.pdf
vec3 EvaluateBtdf(vec3 wi, Ray ray, SurfaceInteraction si) {
    Material mat = si.mat;
    vec3 ns = si.ns;
    vec3 wo = -ray.d;
    float eta = si.eta;

    float a = mat.roughness * mat.roughness;
    float a2 = a * a;

    vec3 wh = normalize(wo + eta * wi);
    if (dot(ns, wh) < 0.0) wh = -wh;

    float nsDotWo = abs(dot(ns, wo));
    float nsDotWi = abs(dot(ns, wi));
    float woDotWh = dot(wo, wh);
    float wiDotWh = dot(wi, wh);

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, mat.baseCol, mat.metallic);
    vec3 F = FresnelSchlick(abs(woDotWh), F0);

    float D = DistributionGgx(ns, wh, a);
    float G = SmithGgxMaskingShadowing(wi, wo, ns, a2);

    float denom = woDotWh + eta * wiDotWh;
    denom = max(denom * denom, 0.0001);

    float jacobian = abs(woDotWh * wiDotWh) / max(nsDotWo * nsDotWi, 0.0001);

    vec3 btdf = (vec3(1.0) - F) * D * G * jacobian / denom;

    return btdf;
}

vec3 EvaluateBsdf(vec3 wi, Ray ray, SurfaceInteraction si) {
    vec3 ns = si.ns;
    float nsDotWi = dot(ns, wi);
    if (nsDotWi > 0.0) {
        return EvaluateBrdf(wi, ray, si);
    } else {
        return EvaluateBtdf(wi, ray, si);
    }
}

float HdriPdf(vec3 d) {
    ivec2 size = textureSize(hdri, 0);
    int width = size.x, height = size.y;

    // Convert to spherical coordinates
    float phi = atan(d.z, d.x);
    float theta = acos(d.y);
    // Convert to uv coordinates
    vec2 uv = vec2(phi / (2.0 * PI) + 0.5, theta / PI);

    int col = int(uv.x * float(width));
    int row = int(uv.y * float(height));

    float rowHigh = texelFetch(hdriRowCdf, ivec2(0, row), 0).r;
    float rowLow = row > 0 ? texelFetch(hdriRowCdf, ivec2(0, row - 1), 0).r : 0.0;
    float rowPdf = max(rowHigh - rowLow, 1e-8);
    
    float colHigh = texelFetch(hdriColCdf, ivec2(col, row), 0).r;
    float colLow = col > 0 ? texelFetch(hdriColCdf, ivec2(col - 1, row), 0).r : 0.0;
    float colPdf = max(colHigh - colLow, 1e-8);

    float mapPdf = rowPdf * colPdf * float(width) * float(height);
    float sinTheta = sin(theta);
    return sinTheta > 0.0 ?  mapPdf / (2.0 * PI * PI * sinTheta) : 0.0;
}

float AreaLightPdf(SurfaceInteraction si, Ray ray, vec3 prevPoint) {
    Triangle tri = triangles[si.triId];
    vec3 wi = normalize(si.p - prevPoint);
    float dist = length(si.p - prevPoint);

    // Check if ray hit light's backface
    float cosLight = dot(si.ns, -wi);
    if (cosLight <= 0.0) {
        return 0.0;
    }

    float pdfTri = tri.lightPmf;
    float pdfPoint = (dist * dist) / (cosLight * si.area);
    float pdf = pdfTri * pdfPoint;
    return pdf;
}


#endif
