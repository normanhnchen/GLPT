#version 460 core

in vec3 aPos;

flat out int nodeDepth;
flat out vec3 nodeMin;
flat out vec3 nodeMax;

uniform mat4 projection;
uniform mat4 view;


#include "src/shaders/common.glsl"


void main() {
    BvhNode node = BvhNodes[gl_InstanceID];
    nodeDepth = bvhNodeDepths[gl_InstanceID];

    nodeMin = node.aabbMin;
    nodeMax = node.aabbMax;

    bool visible = true;
    if (bvhViewLayer != -1) {
        // Show a specific layer
        visible = (nodeDepth == bvhViewLayer);
    } else if (bvhViewDepth != -1) {
        // Show every layer up to the depth
        visible = (nodeDepth <= bvhViewDepth);
    }

    if (!visible) {
        // Push outside the clip volume so the box is discarded
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
        return;
    }

    vec3 worldPos = node.aabbMin + aPos * (node.aabbMax - node.aabbMin);

	gl_Position = projection * view * vec4(worldPos, 1.0);
}
