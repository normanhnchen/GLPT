#version 460 core

in vec3 localPos;

out vec4 fragColor;

layout(binding = 6) uniform sampler2D hdri;

#define PI 3.14159265359

vec3 SampleHDRI(vec3 dir) {
    // Convert to spherical coordinates
    float phi = atan(dir.z, dir.x);
    float theta = acos(dir.y);
    // Convert to uv coordinates
    vec2 uv = vec2(phi / (2.0 * PI) + 0.5, theta / PI);
    return texture(hdri, uv).rgb;
}

void main() {
    vec3 color = SampleHDRI(normalize(localPos));

    fragColor = vec4(color, 1.0);
}
