#version 460 core

in vec2 texCoords;

out vec4 fragColor;

uniform sampler2D tex;

uniform float exposure;

uniform bool Reinhard;
uniform bool Reinhard2;
uniform bool ACESFilm;
uniform bool Uchimura;
uniform bool Lottes;

// https://www-old.cs.utah.edu/docs/techreports/2002/pdf/UUCS-02-001.pdf
float TonemapReinhard(float x) {
    return x / (1.0 + x);
}

float TonemapReinhard2(float x, float Lwhite) {
    return (x * (1 + x / Lwhite * Lwhite)) / (1 + x);
}

// https://knarkowicz.wordpress.com/2016/01/06/aces-filmic-tone-mapping-curve/
float TonemapACESFilm(float x) {
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;
    float e = 0.14;

    return clamp((x*(a*x+b))/(x*(c*x+d)+e), 0.0, 1.0);
}

// https://www.desmos.com/calculator/gslcdxvipg
float TonemapUchimura(float x, float P, float a, float m, float l, float c, float b) {
    float l0 = ((P - m) * l) / a;
    float L0 = m - m / a;
    float L1 = m + (1.0 - m) / a;
    float S0 = m + l0;
    float S1 = m + a * l0;
    float C2 = (a * P) / (P - S1);

    float w0 = 1.0 - smoothstep(0.0, m, x);
    float w2 = step(m + l0, x);
    float w1 = 1.0 - w0 - w2;

    float L = m + a * (x - m);
    float T = m * pow(x / m, c) + b;
    float S = P - (P - S1) * exp(-C2 * (x - S0) / P);

    return T * w0 + L * w1 + S * w2;
}

float TonemapLottes(float x, float a, float d, float hdrMax, float midIn, float midOut) {
    float b =
        (-pow(midIn, a) + pow(hdrMax, a) * midOut) /
        ((pow(hdrMax, a * d) - pow(midIn, a * d)) * midOut);
    float c =
        (pow(hdrMax, a * d) * pow(midIn, a) - pow(hdrMax, a) * pow(midIn, a * d) * midOut) /
        ((pow(hdrMax, a * d) - pow(midIn, a * d)) * midOut);

    return pow(x, a) / (pow(x, a * d) * b + c);
}

void main() {             
    vec3 hdrColor = texture(tex, texCoords).rgb;

    hdrColor *= exposure;

    // Tone mapping
    vec3 color = hdrColor;
    if (Reinhard) {
        color.r = TonemapReinhard(hdrColor.r);
        color.g = TonemapReinhard(hdrColor.g);
        color.b = TonemapReinhard(hdrColor.b);
    } else if (Reinhard2) {
        float Lwhite = 10.0;

        color.r = TonemapReinhard2(hdrColor.r, Lwhite);
        color.g = TonemapReinhard2(hdrColor.g, Lwhite);
        color.b = TonemapReinhard2(hdrColor.b, Lwhite);
    } else if (ACESFilm) {
        color.r = TonemapACESFilm(hdrColor.r);
        color.g = TonemapACESFilm(hdrColor.g);
        color.b = TonemapACESFilm(hdrColor.b);
    } else if (Uchimura) {
        float P = 1.0;  // Max brightness
        float a = 1.0;  // Contrast
        float m = 0.22; // Linear section start
        float l = 0.4;  // Linear section length
        float c = 1.33; // Black tightness
        float b = 0.0; // Pedestal

        color.r = TonemapUchimura(hdrColor.r, P, a, m, l, c, b);
        color.g = TonemapUchimura(hdrColor.g, P, a, m, l, c, b);
        color.b = TonemapUchimura(hdrColor.b, P, a, m, l, c, b);
    } else if (Lottes) {
        float a = 1.6; // Contrast
        float d = 0.977; // Clipping point
        float hdrMax = 8.0; // Input white point
        float midIn = 0.18; // Input mid-point value
        float midOut = 0.267; // Desired mid-point output

        color.r = TonemapLottes(hdrColor.r, a, d, hdrMax, midIn, midOut);
        color.g = TonemapLottes(hdrColor.g, a, d, hdrMax, midIn, midOut);
        color.b = TonemapLottes(hdrColor.b, a, d, hdrMax, midIn, midOut);
    }

    // Gamma correction
    vec3 finalColor = pow(color, vec3(1.0 / 2.2));
    fragColor = vec4(finalColor, 1.0);
}
