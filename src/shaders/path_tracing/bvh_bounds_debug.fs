#version 460 core


flat in int nodeDepth;
flat in vec3 nodeMin;
flat in vec3 nodeMax;

out vec4 fragColor;


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/util.glsl"


void main() {
    if (bvhColorMode == 0) {
        /* BVH depth color */

        fragColor = vec4(GetBvhDepthColor(nodeDepth, bvhMaxNodeDepth), 1.0);
    } else if (bvhColorMode == 1) {
        /* BVH angle color */

        fragColor = vec4(GetBvhAngleColor(nodeMin, nodeMax), 1.0);
    }
}
