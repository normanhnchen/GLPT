#version 460 core

in vec2 texCoords;

out vec4 fragColor;

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
 * Tone Mapping Operators
 * Source: https://github.com/dmnsgn/glsl-tone-map
 */

// --- ACESFilm ---

vec3 TonemapACESFilm(vec3 x, float a, float b, float c, float d, float e) {
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

// --- AgX ---

const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
     1.6605, -0.1246, -0.0182,
    -0.5876,  1.1329, -0.1006,
    -0.0728, -0.0083,  1.1187
);

const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
    0.6274, 0.0691, 0.0164,
    0.3293, 0.9195, 0.0880,
    0.0433, 0.0113, 0.8956
);

const mat3 AgXInsetMatrix = mat3(
    0.856627153315983,  0.137318972929847,  0.11189821299995,
    0.0951212405381588, 0.761241990602591,  0.0767994186031903,
    0.0482516061458583, 0.101439036467562,  0.811302368396859
);

const mat3 AgXOutsetMatrix = mat3(
     1.1271005818144368,  -0.1413297634984383,  -0.14132976349843826,
    -0.11060664309660323,  1.157823702216272,   -0.11060664309660294,
    -0.016493938717834573, -0.016493938717834257, 1.2519364065950405
);

const float AgxMinEv = -12.47393;
const float AgxMaxEv =   4.026069;

vec3 TonemapAgXCdl(vec3 color, vec3 slope, vec3 offset, vec3 power, float saturation) {
    color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;

    color = AgXInsetMatrix * color;
    color = max(color, 1e-10);

    color = clamp(log2(color), AgxMinEv, AgxMaxEv);
    color = (color - AgxMinEv) / (AgxMaxEv - AgxMinEv);
    color = clamp(color, 0.0, 1.0);

    vec3 x2 = color * color;
    vec3 x4 = x2 * x2;
    color = + 15.5     * x4 * x2
            - 40.14    * x4 * color
            + 31.96    * x4
            -  6.868   * x2 * color
            +  0.4298  * x2
            +  0.1191  * color
            -  0.00232;

    color = pow(color * slope + offset, power);

    const vec3 lw = vec3(0.2126, 0.7152, 0.0722);
    float luma = dot(color, lw);
    color = luma + saturation * (color - luma);

    color = AgXOutsetMatrix * color;
    color = pow(max(vec3(0.0), color), vec3(2.2));
    color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
    color = clamp(color, 0.0, 1.0);

    return color;
}

vec3 TonemapAgX(vec3 color) {
    return TonemapAgXCdl(color, vec3(1.0), vec3(0.0), vec3(1.0), 1.0);
}

vec3 TonemapAgXGolden(vec3 color) {
    return TonemapAgXCdl(color, vec3(1.0, 0.9, 0.5), vec3(0.0), vec3(0.8), 1.3);
}

vec3 TonemapAgXPunchy(vec3 color) {
    return TonemapAgXCdl(color, vec3(1.0), vec3(0.0), vec3(1.35), 1.4);
}

// --- Filmic ---

vec3 TonemapFilmic(vec3 x) {
    vec3 X = max(vec3(0.0), x - 0.004);
    vec3 result = (X * (6.2 * X + 0.5)) / (X * (6.2 * X + 1.7) + 0.06);
    return pow(result, vec3(2.2));
}

// --- Lottes ---

vec3 TonemapLottes(vec3 x, vec3 a, vec3 d, vec3 hdrMax, vec3 midIn, vec3 midOut) {
    const vec3 b =
        (-pow(midIn, a) + pow(hdrMax, a) * midOut) /
        ((pow(hdrMax, a * d) - pow(midIn, a * d)) * midOut);
    const vec3 c =
        (pow(hdrMax, a * d) * pow(midIn, a) - pow(hdrMax, a) * pow(midIn, a * d) * midOut) /
        ((pow(hdrMax, a * d) - pow(midIn, a * d)) * midOut);

    return pow(x, a) / (pow(x, a * d) * b + c);
}

// --- Neutral ---

vec3 TonemapNeutral(vec3 color) {
    const float startCompression = 0.8 - 0.04;
    const float desaturation = 0.15;

    float x = min(color.r, min(color.g, color.b));
    float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
    color -= offset;

    float peak = max(color.r, max(color.g, color.b));
    if (peak < startCompression) return color;

    const float d = 1.0 - startCompression;
    float newPeak = 1.0 - d * d / (peak + d - startCompression);
    color *= newPeak / peak;

    float g = 1.0 - 1.0 / (desaturation * (peak - newPeak) + 1.0);
    return mix(color, vec3(newPeak), g);
}

// --- Reinhard ---

vec3 TonemapReinhard(vec3 x) {
    return x / (1.0 + x);
}

// --- Reinhard2 ---

vec3 TonemapReinhard2(vec3 x, float Lwhite) {
    return (x * (1.0 + x / (Lwhite * Lwhite))) / (1.0 + x);
}

// --- Uchimura ---

vec3 TonemapUchimura(vec3 x, float P, float a, float m, float l, float c, float b) {
    float l0 = ((P - m) * l) / a;
    float L0 = m - m / a;
    float L1 = m + (1.0 - m) / a;
    float S0 = m + l0;
    float S1 = m + a * l0;
    float C2 = (a * P) / (P - S1);
    float CP = -C2 / P;

    vec3 w0 = vec3(1.0 - smoothstep(0.0, m, x));
    vec3 w2 = vec3(step(m + l0, x));
    vec3 w1 = vec3(1.0 - w0 - w2);

    vec3 T = vec3(m * pow(x / m, vec3(c)) + b);
    vec3 S = vec3(P - (P - S1) * exp(CP * (x - S0)));
    vec3 L = vec3(m + a * (x - m));

    return T * w0 + L * w1 + S * w2;
}

// --- Uncharted2 ---

vec3 TonemapUncharted2(vec3 x, float A, float B, float C, float D, float E, float F) {
    return ((x * (A * x + C * B) + D * E) / (x * (A * x + B) + D * F)) - E / F;
}

// --- Unreal ---

vec3 TonemapUnreal(vec3 x) {
    return x / (x + 0.155) * 1.019;
}

void main() {
    vec3 hdrColor = texture(tex, texCoords).rgb;

    hdrColor *= exposure;

    // Tone mapping
    vec3 color;
    if (None) {
        color = hdrColor;
    } else if (ACESFilm) {
        const float a = 2.51;
        const float b = 0.03;
        const float c = 2.43;
        const float d = 0.59;
        const float e = 0.14;

        color = TonemapACESFilm(hdrColor, a, b, c, d, e);
    } else if (AgX) {
        color = TonemapAgX(hdrColor);

        // Correct because gamma correction is baked in
        color = pow(color, vec3(2.2));
    } else if (AgXGolden) {
        color = TonemapAgXGolden(hdrColor);

        // Correct because gamma correction is baked in
        color = pow(color, vec3(2.2));
    } else if (AgXPunchy) {
        color = TonemapAgXPunchy(hdrColor);

        // Correct because gamma correction is baked in
        color = pow(color, vec3(2.2));
    } else if (Filmic) {
        color = TonemapFilmic(hdrColor);

        // Correct because gamma correction is baked in
        color = pow(color, vec3(2.2));
    } else if (Lottes) {
        vec3 a = vec3(1.6);
        vec3 d = vec3(0.977);
        vec3 hdrMax = vec3(8.0);
        vec3 midIn = vec3(0.18);
        vec3 midOut = vec3(0.267);

        color = TonemapLottes(hdrColor, a, d, hdrMax, midIn, midOut);
    } else if (Neutral) {
        color = TonemapNeutral(hdrColor);
    } else if (Reinhard) {
        color = TonemapReinhard(hdrColor);
    } else if (Reinhard2) {
        float Lwhite = 10.0;

        color = TonemapReinhard2(hdrColor, Lwhite);
    } else if (Uchimura) {
        float P = 1.0;  // Max brightness
        float a = 1.0;  // Contrast
        float m = 0.22; // Linear section start
        float l = 0.4;  // Linear section length
        float c = 1.33; // Black tightness
        float b = 0.0;  // Pedestal

        color = TonemapUchimura(hdrColor, P, a, m, l, c, b);
    } else if (Uncharted2) {
        float A = 0.15;
        float B = 0.50;
        float C = 0.10;
        float D = 0.20;
        float E = 0.02;
        float F = 0.30;
        float W = 11.2;
        float exposureBias = 2.0;

        vec3 curr = TonemapUncharted2(exposureBias * hdrColor, A, B, C, D, E, F);
        vec3 whiteScale = 1.0 / TonemapUncharted2(vec3(W), A, B, C, D, E, F);
        color = curr * whiteScale;
    } else if (Unreal) {
        color = TonemapUnreal(hdrColor);

        // Correct because gamma correction is baked in
        color = pow(color, vec3(2.2));
    }

    // Gamma correction
    vec3 finalColor = pow(color, vec3(1.0 / 2.2));
    fragColor = vec4(finalColor, 1.0);
}