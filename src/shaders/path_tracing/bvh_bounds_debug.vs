#version 460 core

in vec3 aPos;

flat out int vDepth;

uniform mat4 projection;
uniform mat4 view;


#include "src/shaders/common.glsl"


void main() {
    BvhNode node = BvhNodes[gl_InstanceID];
    vDepth = bvhNodeDepths[gl_InstanceID];

    vec3 worldPos = node.aabbMin + aPos * (node.aabbMax - node.aabbMin);

	gl_Position = projection * view * vec4(worldPos, 1.0);
}
