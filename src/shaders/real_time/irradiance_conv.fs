#version 460 core

in vec3 localPos;
in vec3 normal;

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

// https://learnopengl.com/PBR/IBL/Diffuse-irradiance
void main() {
    vec3 irradiance = vec3(0.0);  

    vec3 up = vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(up, normal));
    up = normalize(cross(normal, right));

    float sampleDelta = 0.025;
    float nrSamples = 0.0; 
    for(float phi = 0.0; phi < 2.0 * PI; phi += sampleDelta)
    {
        for(float theta = 0.0; theta < 0.5 * PI; theta += sampleDelta)
        {
            // Spherical to cartesian (in tangent space)
            vec3 tangentSample = vec3(sin(theta) * cos(phi),  sin(theta) * sin(phi), cos(theta));
            // Tangent space to world
            vec3 sampleVec = tangentSample.x * right + tangentSample.y * up + tangentSample.z * normal; 

            irradiance += SampleHDRI(sampleVec) * cos(theta) * sin(theta);
            nrSamples++;
        }
    }
    irradiance = PI * irradiance * (1.0 / float(nrSamples));

    fragColor = vec4(irradiance, 1.0);
}
