#version 460 core

in vec2 texCoords;

out vec4 fragColor;

uniform sampler2D tex;

void main() {             
    vec3 color = texture(tex, texCoords).rgb;
    // Gamma correction
    vec3 finalColor = pow(color, vec3(1.0 / 2.2));
    fragColor = vec4(finalColor, 1.0);
}
