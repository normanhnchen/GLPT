#version 460 core

in vec2 texCoords;

out vec4 fragColor;

void main() {
    fragColor = vec4(texCoords, 1.0, 1.0);
}
