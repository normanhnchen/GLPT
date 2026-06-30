#version 460 core

in vec3 aPos;
in vec3 aNormal;

out vec3 normal;
out vec3 localPos;

uniform mat4 projection;
uniform mat4 view;

void main() {
    localPos = aPos;
    normal = aNormal;
    gl_Position = projection * view * vec4(aPos, 1.0);
}
