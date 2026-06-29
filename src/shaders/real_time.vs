#version 460 core

in vec3 aPos;
in vec2 aTexCoords;
in vec3 aNormal;
in int aMatId;

out vec2 texCoords;
flat out int matId;
out vec3 normal;

uniform mat4 projection;
uniform mat4 view;

void main() {
	gl_Position = projection * view * vec4(aPos, 1.0);
    texCoords = aTexCoords;
    matId = aMatId;
    normal = aNormal;
}
