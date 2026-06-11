#version 460 core

in vec2 texCoords;

out vec4 fragColor;

uniform sampler2D tex;

void main() {
    vec4 col = texture(tex, texCoords);
    fragColor = col;
}
