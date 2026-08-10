import json
import numpy as np
import glm
from pathlib import Path
import torch


class Screen:
    def __init__(self, json_settings):
        self._default_config = json_settings["screen"]

        self._load(self._default_config)

    def _load(self, config):
        self.width = config["width"]
        self.height = config["height"]
        self.resolution = [self.width, self.height]
        self.aspect_ratio = self.width / max(self.height, 1)
        self.vsync = config["vsync"]
        self.fps_cap = config["fps_cap"]

    def reset(self):
        self._load(self._default_config)


class CameraSettings:
    def __init__(self, json_settings):
        self._default_config = json_settings["camera"]

        self._load(self._default_config)

    def _load(self, config):
        self._yaw = config["_yaw"]
        self._pitch = config["_pitch"]
        self.movement_speed = config["movement_speed"]
        self.mouse_sensitivity = config["mouse_sensitivity"]
        self.fov = config["fov"]
        self.pos = glm.vec3(config["pos"])
        self._front = glm.vec3(config["_front"])
        self._up = glm.vec3(config["_up"])
        self._world_up = glm.vec3(config["_world_up"])
        
        self.blur = config["blur"]
        self.dof_enabled = config["dof_enabled"]
        self.aperture = config["aperture"]
        self.focus_dist = config["focus_dist"]

    def reset(self):
        self._load(self._default_config)


class PTSettings:
    def __init__(self, json_settings):
        self._default_config = json_settings["path_tracing"]

        self._load(self._default_config)

    def _load(self, config):
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

        self.bvh_color_mode = config["bvh_color_mode"]

    def reset(self):
        self._load(self._default_config)


class BVHSettings:
    def __init__(self, json_settings):
        self._default_config = json_settings["bvh"]

        self._load(self._default_config)

    def _load(self, config):
        self.max_depth = config["max_depth"]
        self.sah_bins = config["sah_bins"]

class PostProcessSettings:
    def __init__(self, json_settings):
        self._default_config = json_settings["post_processing"]

        self._load(self._default_config)

    def _load(self, config):
        self.exposure = config["exposure"]
        self.tonemap = config["tonemap"]
        self.hdri_exposure = config["hdri_exposure"]

    def reset(self):
        self._load(self._default_config)


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
    def __init__(self, json_settings):
        self._default_config = json_settings["file_paths"]

        self._load(self._default_config)

    def _load(self, config):
        self.ai_training_scenes = ROOT_DIR / config["ai_training_scenes"]
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

    def reset(self):
        self._load(self._default_config)


class RenderSettings:
    def __init__(self, json_settings):
        self._default_config = json_settings["render"]

        self._load(self._default_config)

    def _load(self, config):
        self.render_mode = config["render_mode"]
        self.texture_size = config["texture_size"]
        self.tiles_x = config["tiles_x"]
        self.tiles_y = config["tiles_y"]

    def reset(self):
        self._load(self._default_config)


class AITrainingSettings:
    def __init__(self, json_settings):
        self._default_config = json_settings["ai_training"]

        self._load(self._default_config)

    def _load(self, config):
        self.ai_training_mode = config["ai_training_mode"]
        self.camera_setup_mode = config["camera_setup_mode"]

    def reset(self):
        self._load(self._default_config)


with open("src/settings.json") as f:
    json_settings = json.load(f)

ROOT_DIR = Path(__file__).resolve().parent.parent

# glTF KHR_lights_punctual defines intensity in photometric units
# Convert to radiometric units matching Blender's export constant
LUMENS_TO_WATTS = 1.0 / 683.0

screen = Screen(json_settings)
camera_settings = CameraSettings(json_settings)
pt_settings = PTSettings(json_settings)
bvh_settings = BVHSettings(json_settings)
post_process_settings = PostProcessSettings(json_settings)
file_paths = FilePaths(json_settings)
render_settings = RenderSettings(json_settings)
ai_training_settings = AITrainingSettings(json_settings)

AI_DEVICE = torch.device("cpu")
if torch.cuda.is_available():
    AI_DEVICE = torch.device("cuda")
