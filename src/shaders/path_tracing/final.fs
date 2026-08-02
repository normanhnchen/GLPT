#version 460 core

in vec2 texCoords;

out vec4 fragColor;


#include "src/shaders/common.glsl"
#include "src/shaders/tonemaps.glsl"


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
