#version 460 core


flat in int vDepth;
out vec4 fragColor;


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/util_functions.glsl"


void main() {
    if (bvhColorMode == 0) {
        fragColor = vec4(GetBvhDepthColor(vDepth, bvhMaxDepth), 1.0);
    } else if (bvhColorMode == 1) {
        fragColor = vec4(GetBvhRgbColor(vDepth, bvhMaxDepth), 1.0);
    }
}
