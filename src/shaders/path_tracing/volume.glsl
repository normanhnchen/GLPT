#ifndef VOLUME_GLSL
#define VOLUME_GLSL


#include "src/shaders/common.glsl"


// Beer-Lambert law: light attenuates exponentially with distance traveled through a medium
// https://www.pbr-book.org/3ed-2018/Volume_Scattering/Volume_Scattering_Processes
void BeerLambert(inout bool insideMedium, inout vec3 entryPoint, SurfaceInteraction si, out vec3 transmittance, bool didRefract) {
    transmittance = vec3(1.0);

    bool isTransmission = si.mat.transmission > 0.0;
    bool isEntering = !si.isBackFace;
    bool isExiting = si.isBackFace;

    // Only apply when the material is transmissive and the ray is exiting the medium
    if (isTransmission) {
        if (isEntering && !insideMedium) {
            /* Entering medium */

            entryPoint = si.p;
            insideMedium = true;
        } else if (isExiting && didRefract && insideMedium) {
            /* Exiting medium */

            if (transmissionMode == 0) {
                /* Beer-Lambert */

                float distTravelled = max(length(si.p - entryPoint), EPSILON);
                vec3 absorption = -log(max(si.mat.baseCol, EPSILON));
                transmittance = exp(-absorption * distTravelled);
            } else if (transmissionMode == 1) {
                /*
                 * No Beer-Lambert
                 * Default to base color
                 */

                transmittance = si.mat.baseCol;
            }

            insideMedium = false;
        }
    }
}


#endif
