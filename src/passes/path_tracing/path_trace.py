from src.dtypes import *
from src.settings import *


def _compute_uniforms(scene, camera, pt_state):
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

        "numFiniteLights": scene.num_finite_lights,
        "numEmissiveTriangles": scene.num_emissive_triangles,

        "specularMode": pt_settings.specular_mode,
        "geometryMode": pt_settings.geometry_mode,
        "transmissionMode": pt_settings.transmission_mode,
        "misMode": pt_settings.mis_mode,
        "uOffset": np.array([pt_state.tiles.curr_tile_x, pt_state.tiles.curr_tile_y], dtype=i4),

        "blur": camera.blur,
        "hdriExposure": post_process_settings.hdri_exposure,

        "debugMode": pt_state.debug.mode,

        "maxBvhDepth": bvh_settings.max_depth
    }


def _set_uniforms(prog, uniform_dict):
    for uniform, value in uniform_dict.items():
        if isinstance(value, bytes):
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
