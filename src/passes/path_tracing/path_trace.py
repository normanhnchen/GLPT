from src.dtypes import *
from src.settings import *


def _compute_uniforms(scene, pt_state):
    # Prevent the samples from going over the max samples limit
    samples_left = pt_settings.max_samples - pt_state.rendering.total_samples
    if samples_left < pt_settings.spp:
        spp = samples_left
    else:
        spp = pt_settings.spp

    return {
        "aspectRatio": set_f4(screen.aspect_ratio),
        "samplesPerPixel": spp,
        "totalSamples": pt_state.rendering.total_samples,

        "maxTotalBounces": pt_settings.total_bounces,
        "maxDiffuseBounces": pt_settings.diffuse_bounces,
        "maxSpecularBounces": pt_settings.specular_bounces,
        "maxTransmissionBounces": pt_settings.transmission_bounces,

        "depthFactor": 1 / scene.extent,

        "numFiniteLights": scene.num_finite_lights,
        "numEmissiveTriangles": scene.num_emissive_triangles,

        "specularMode": pt_settings.specular_mode,
        "geometryMode": pt_settings.geometry_mode,
        "transmissionMode": pt_settings.transmission_mode,
        "misMode": pt_settings.mis_mode,
        "uOffset": np.array([pt_state.tiles.curr_tile_x, pt_state.tiles.curr_tile_y], dtype=i4),

        "blur": post_process_settings.blur,
        "hdriExposure": post_process_settings.hdri_exposure
    }


def _set_uniforms(prog, uniform_dict):
    for uniform, value in uniform_dict.items():
        prog[uniform].value = value


class PathTracePass:
    def __init__(self, compute_shader):
        self.shader = compute_shader

    def render(self, scene, pt_state):
        uniform_dict = _compute_uniforms(scene, pt_state)
        _set_uniforms(self.shader.prog, uniform_dict)

        # Apply ceiling function
        # Allows the compute shader to reach the entire screen
        groups_x = (pt_state.tiles.tile_width + 15) // 16
        groups_y = (pt_state.tiles.tile_height + 15) // 16

        pt_state.advance_render()
        
        # Dispatch compute shader
        pt_state.framebuffers.bind_to_images()
        self.shader.prog.run(groups_x, groups_y)
