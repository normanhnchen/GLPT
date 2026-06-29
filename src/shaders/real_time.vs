#version 460 core

in vec3 aPos;
in vec2 aTexCoords;

out vec2 texCoords;

uniform mat4 projection;
uniform mat4 view;

void main() {
	gl_Position = projection * view * vec4(aPos, 1.0);
    texCoords = aTexCoords;
}
