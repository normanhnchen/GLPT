from src.dtypes import *
from src.settings import settings


def _compute_uniforms(scene, camera, pt_state):
    # Prevent the samples from going over the max samples limit
    samples_left = settings.path_tracing.max_samples - pt_state.rendering.total_samples
    if samples_left < settings.path_tracing.spp:
        spp = samples_left
    else:
        spp = settings.path_tracing.spp

    return {
        "aspectRatio": set_f4(settings.screen.aspect_ratio),
        "samplesPerPixel": spp,
        "totalSamples": pt_state.rendering.total_samples,

        "maxTotalBounces": settings.path_tracing.total_bounces,
        "maxDiffuseBounces": settings.path_tracing.diffuse_bounces,
        "maxSpecularBounces": settings.path_tracing.specular_bounces,
        "maxTransmissionBounces": settings.path_tracing.transmission_bounces,

        "numFiniteLights": scene.num_finite_lights,
        "numEmissiveTriangles": scene.num_emissive_triangles,

        "specularMode": settings.path_tracing.specular_mode,
        "geometryMode": settings.path_tracing.geometry_mode,
        "transmissionMode": settings.path_tracing.transmission_mode,
        "misMode": settings.path_tracing.mis_mode,
        "uOffset": np.array([pt_state.tiles.curr_tile_x, pt_state.tiles.curr_tile_y], dtype=i4),

        "blur": camera.blur,
        "hdriExposure": settings.post_processing.hdri_exposure,

        "debugMode": pt_state.debug.mode,

        "maxBvhDepth": settings.bvh.max_depth,

        "backfaceCulling": set_i4(1) if settings.path_tracing.backface_culling else set_i4(0),

        "maxDirectLuminance": set_f4(settings.path_tracing.max_direct_luminance),
        "maxIndirectLuminance": set_f4(settings.path_tracing.max_indirect_luminance),
        "maxBsdfLuminance": set_f4(settings.path_tracing.max_bsdf_luminance)
    }


def _set_uniforms(prog, uniform_dict):
    for uniform, value in uniform_dict.items():
        if isinstance(value, bytes):
            # Matrices can't be assigned via .value = ... like scalar/vector
            # uniforms; matrices need .write(bytes)
            prog[uniform].write(value)
        
        else:
            prog[uniform].value = value


class PathTracePass:
    def __init__(self, scene, camera, pt_state, compute_shader):
        self.scene = scene
        self.camera = camera
        self.pt_state = pt_state
        self.shader = compute_shader

    def render(self):
        uniform_dict = _compute_uniforms(self.scene, self.camera, self.pt_state)
        _set_uniforms(self.shader.prog, uniform_dict)

        # Apply ceiling function
        # Allows the compute shader to reach the entire screen
        groups_x = (self.pt_state.tiles.tile_width + 15) // 16
        groups_y = (self.pt_state.tiles.tile_height + 15) // 16

        self.pt_state.advance_render()
        
        # Dispatch compute shader
        self.pt_state.framebuffers.bind_to_images()
        self.shader.prog.run(groups_x, groups_y)
