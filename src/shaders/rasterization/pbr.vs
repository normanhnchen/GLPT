#version 460 core

in vec3 aPos;
in vec2 aTexCoords;
in vec3 aNormal;
in int aMatId;

out vec2 texCoords;
out vec3 normal;
out vec3 worldPos;
flat out int matId;

uniform mat4 projection;
uniform mat4 view;

void main() {
	gl_Position = projection * view * vec4(aPos, 1.0);
    texCoords = aTexCoords;
    normal = aNormal;
    worldPos = aPos;
    matId = aMatId;
}
