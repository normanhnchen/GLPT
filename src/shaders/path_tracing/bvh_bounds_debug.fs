#version 460 core


flat in int vDepth;
out vec4 fragColor;


#include "src/shaders/common.glsl"
#include "src/shaders/path_tracing/util_functions.glsl"


void main() {
    fragColor = vec4(GetBvhBoundsColor(vDepth, bvhMaxDepth), 1.0);
}
