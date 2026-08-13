import json
import numpy as np
import glm
from pathlib import Path
import torch


class Screen:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["screen"]
        self.user_config = user_settings["screen"]

        self._load_internal(self.internal_config)
        self._load_user(self.user_config)

    def _load_internal(self, config):
        self.width = config["width"]
        self.height = config["height"]
        self.resolution = [self.width, self.height]
        self.aspect_ratio = self.width / max(self.height, 1)
        self.vsync = config["vsync"]
        self.fps_cap = config["fps_cap"]

    def _load_user(self, config):
        self.width = config["width"]
        self.height = config["height"]
        self.resolution = [self.width, self.height]
        self.aspect_ratio = self.width / max(self.height, 1)
        self.vsync = config["vsync"]
        self.fps_cap = config["fps_cap"]
    
    def reset(self):
        self._load_internal(self.internal_config)


class CameraSettings:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["camera"]
        self.user_config = user_settings["camera"]

        self._load_internal(self.internal_config)
        self._load_user(self.user_config)

    def _load_internal(self, config):
        self.yaw = config["yaw"]
        self.pitch = config["pitch"]
        self.movement_speed = config["movement_speed"]
        self.mouse_sensitivity = config["mouse_sensitivity"]
        self.fov = config["fov"]
        self.pos = config["pos"]
        self.front = config["front"]
        self.up = config["up"]
        self.world_up = config["world_up"]
        
        self.blur = config["blur"]
        self.dof_enabled = config["dof_enabled"]
        self.aperture = config["aperture"]
        self.focus_dist = config["focus_dist"]

    def _load_user(self, config):
        self.yaw = config["yaw"]
        self.pitch = config["pitch"]
        self.movement_speed = config["movement_speed"]
        self.mouse_sensitivity = config["mouse_sensitivity"]
        self.fov = config["fov"]
        self.pos = config["pos"]
        
        self.blur = config["blur"]
        self.dof_enabled = config["dof_enabled"]
        self.aperture = config["aperture"]
        self.focus_dist = config["focus_dist"]

    def reset(self):
        self._load_internal(self.internal_config)


class PTSettings:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["path_tracing"]
        self.user_config = user_settings["path_tracing"]

        self._load_internal(self.internal_config)
        self._load_user(self.user_config)

    def _load_internal(self, config):
        self.spp = config["samples_per_pixel"]
        self.max_samples = config["max_samples"]

        self.total_bounces = config["total_bounces"]
        self.diffuse_bounces = config["diffuse_bounces"]
        self.specular_bounces = config["specular_bounces"]
        self.transmission_bounces = config["transmission_bounces"]

        self.specular_mode = config["specular_mode"]
        self.geometry_mode = config["geometry_mode"]
        self.transmission_mode = config["transmission_mode"]
        self.mis_mode = config["mis_mode"]

        self.backface_culling = config["backface_culling"]

        self.max_direct_luminance = config["max_direct_luminance"]
        self.max_indirect_luminance = config["max_indirect_luminance"]

    def _load_user(self, config):
        self.spp = config["samples_per_pixel"]
        self.max_samples = config["max_samples"]

        self.total_bounces = config["total_bounces"]
        self.diffuse_bounces = config["diffuse_bounces"]
        self.specular_bounces = config["specular_bounces"]
        self.transmission_bounces = config["transmission_bounces"]

        self.specular_mode = config["specular_mode"]
        self.geometry_mode = config["geometry_mode"]
        self.transmission_mode = config["transmission_mode"]
        self.mis_mode = config["mis_mode"]

        self.backface_culling = config["backface_culling"]

        self.max_direct_luminance = config["max_direct_luminance"]
        self.max_indirect_luminance = config["max_indirect_luminance"]

    def reset(self):
        self._load_internal(self.internal_config)


class BVHSettings:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["bvh"]
        self.user_config = user_settings["bvh"]

        self._load_internal(self.internal_config)
        self._load_user(self.user_config)

    def _load_internal(self, config):
        self.max_depth = config["max_depth"]
        self.sah_bins = config["sah_bins"]

    def _load_user(self, config):
        self.max_depth = config["max_depth"]
        self.sah_bins = config["sah_bins"]

    def reset(self):
        self._load_internal(self.internal_config)


class DebugSettings:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["debug"]
        self.user_config = user_settings["debug"]

        self._load_internal(self.internal_config)
        self._load_user(self.user_config)

    def _load_internal(self, config):
        class BVH:
            def __init__(self, debug_config):
                self.internal_config = debug_config["bvh"]

                self._load_internal(self.internal_config)

            def _load_internal(self, config):
                self.view_layer = config["view_layer"]
                self.view_depth = config["view_depth"]
                self.color_mode = config["color_mode"]

        self.bvh = BVH(config)

    def _load_user(self, config):
        class BVH:
            def __init__(self, debug_config):
                self.internal_config = debug_config["bvh"]

                self._load_user(self.internal_config)

            def _load_user(self, config):
                self.view_layer = config["view_layer"]
                self.view_depth = config["view_depth"]
                self.color_mode = config["color_mode"]

        self.bvh = BVH(config)

    def reset(self):
        self._load_internal(self.internal_config)


class PostProcessSettings:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["post_processing"]
        self.user_config = user_settings["post_processing"]

        self._load_internal(self.internal_config)
        self._load_user(self.user_config)

    def _load_internal(self, config):
        self.exposure = config["exposure"]
        self.tonemap = config["tonemap"]
        self.hdri_exposure = config["hdri_exposure"]

    def _load_user(self, config):
        self.exposure = config["exposure"]
        self.tonemap = config["tonemap"]
        self.hdri_exposure = config["hdri_exposure"]

    def reset(self):
        self._load_internal(self.internal_config)


class ShaderGroup:
    def __init__(self, config):
        for attr, rel_dir in config.items():
            if isinstance(rel_dir, dict):
                # Parse nested shader groups
                setattr(self, attr, ShaderGroup(rel_dir))
            else:
                root_dir = ROOT_DIR / rel_dir
                setattr(self, attr, root_dir)

class FilePaths:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["file_paths"]
        self.user_config = user_settings["file_paths"]

        self._load_internal(self.internal_config)
        self._load_user(self.user_config)

    def _load_internal(self, config):
        self.ai_training_scenes = ROOT_DIR / config["ai_training_scenes"]
        self.scenes = ROOT_DIR / config["scenes"]
        self.scene = ROOT_DIR / config["scene"]
        self.ai_training_hdris = ROOT_DIR / config["ai_training_hdris"]
        self.hdri = ROOT_DIR / config["hdri"]
        self.ai_training_renders = ROOT_DIR / config["ai_training_renders"]
        self.renders = ROOT_DIR / config["renders"]
        self.camera_capture_states = ROOT_DIR / config["camera_capture_states"]
        self.denoise_checkpoint = ROOT_DIR / config["denoiser_checkpoint"]
        self.denoiser_last_checkpoint = ROOT_DIR / config["denoiser_last_checkpoint"]
        
        self.path_tracing = ShaderGroup(config["path_tracing"])
        self.background = ShaderGroup(config["rasterization"]["background"])
        self.pbr = ShaderGroup(config["rasterization"]["pbr"])
        self.final = ShaderGroup(config["rasterization"]["final"])

        self.scene_cache = ROOT_DIR / config["cache"]["scene"]
        self.bvh_cache = ROOT_DIR / config["cache"]["bvh"]

    def _load_user(self, config):
        self.scenes = ROOT_DIR / config["scenes"]
        self.scene = ROOT_DIR / config["scene"]
        self.hdri = ROOT_DIR / config["hdri"]
        self.renders = ROOT_DIR / config["renders"]
        self.ai_training_scenes = ROOT_DIR / config["ai_training_scenes"]
        self.ai_training_hdris = ROOT_DIR / config["ai_training_hdris"]
        self.ai_training_renders = ROOT_DIR / config["ai_training_renders"]

    def reset(self):
        self._load_internal(self.internal_config)


class RenderSettings:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["render"]
        self.user_config = user_settings["render"]

        self._load_internal(self.internal_config)
        self._load_user(self.user_config)

    def _load_internal(self, config):
        self.render_mode = config["render_mode"]
        self.texture_size = config["texture_size"]
        self.tiles_x = config["tiles_x"]
        self.tiles_y = config["tiles_y"]

    def _load_user(self, config):
        self.render_mode = config["render_mode"]
        self.texture_size = config["texture_size"]
        self.tiles_x = config["tiles_x"]
        self.tiles_y = config["tiles_y"]

    def reset(self):
        self._load_internal(self.internal_config)


class AITrainingSettings:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["ai_training"]

        self._load_internal(self.internal_config)

    def _load_internal(self, config):
        self.ai_training_mode = config["ai_training_mode"]
        self.camera_setup_mode = config["camera_setup_mode"]

    def reset(self):
        self._load_internal(self.internal_config)


with open("src/settings/internal.json") as f:
    internal_settings = json.load(f)

with open("src/settings/user.json") as f:
    user_settings = json.load(f)

ROOT_DIR = Path(__file__).resolve().parent.parent

# glTF KHR_lights_punctual defines intensity in photometric units
# Convert to radiometric units matching Blender's export constant
LUMENS_TO_WATTS = 1.0 / 683.0

screen = Screen(internal_settings, user_settings)
camera_settings = CameraSettings(internal_settings, user_settings)
pt_settings = PTSettings(internal_settings, user_settings)
bvh_settings = BVHSettings(internal_settings, user_settings)
debug_settings = DebugSettings(internal_settings, user_settings)
post_process_settings = PostProcessSettings(internal_settings, user_settings)
file_paths = FilePaths(internal_settings, user_settings)
render_settings = RenderSettings(internal_settings, user_settings)
ai_training_settings = AITrainingSettings(internal_settings, user_settings)

AI_DEVICE = torch.device("cpu")
if torch.cuda.is_available():
    AI_DEVICE = torch.device("cuda")
