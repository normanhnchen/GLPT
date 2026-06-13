#version 460 core

in vec2 aPos;
in vec2 aTexCoords;

out vec2 texCoords;

void main() {
	gl_Position = vec4(aPos, 0.0, 1.0);
    texCoords = aTexCoords;
}
