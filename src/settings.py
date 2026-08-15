import json
import numpy as np
import glm
from pathlib import Path
import torch


class ScreenSettings:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["screen"]
        self.user_config = user_settings["screen"]

        self._load_internal()
        self._load_user()

    def _load_internal(self):
        self.width = self.internal_config["width"]
        self.height = self.internal_config["height"]
        self.resolution = [self.width, self.height]
        self.aspect_ratio = self.width / max(self.height, 1)
        self.vsync = self.internal_config["vsync"]
        self.fps_cap = self.internal_config["fps_cap"]
        self.min_width = self.internal_config["min_width"]
        self.min_height = self.internal_config["min_height"]

    def _load_user(self):
        self.width = self.user_config["width"]
        self.height = self.user_config["height"]
        self.resolution = [self.width, self.height]
        self.aspect_ratio = self.width / max(self.height, 1)
        self.vsync = self.user_config["vsync"]
        self.fps_cap = self.user_config["fps_cap"]
    
    def reset(self):
        self._load_internal()

    def user_settings_to_dict(self):
        return {
            "screen": {
                "width": self.width,
                "height": self.height,
                "vsync": self.vsync,
                "fps_cap": self.fps_cap,
            }
        }
    


class CameraSettings:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["camera"]
        self.user_config = user_settings["camera"]

        self._load_internal()
        self._load_user()

    def _load_internal(self):
        self.yaw = self.internal_config["yaw"]
        self.pitch = self.internal_config["pitch"]
        self.movement_speed = self.internal_config["movement_speed"]
        self.mouse_sensitivity = self.internal_config["mouse_sensitivity"]
        self.fov = self.internal_config["fov"]
        self.pos = self.internal_config["pos"]
        self.front = self.internal_config["front"]
        self.up = self.internal_config["up"]
        self.world_up = self.internal_config["world_up"]
        
        self.blur = self.internal_config["blur"]
        self.dof_enabled = self.internal_config["dof_enabled"]
        self.aperture = self.internal_config["aperture"]
        self.focus_dist = self.internal_config["focus_dist"]

    def _load_user(self):
        self.yaw = self.user_config["yaw"]
        self.pitch = self.user_config["pitch"]
        self.movement_speed = self.user_config["movement_speed"]
        self.mouse_sensitivity = self.user_config["mouse_sensitivity"]
        self.fov = self.user_config["fov"]
        self.pos = self.user_config["pos"]
        
        self.blur = self.user_config["blur"]
        self.dof_enabled = self.user_config["dof_enabled"]
        self.aperture = self.user_config["aperture"]
        self.focus_dist = self.user_config["focus_dist"]

    def reset(self):
        self._load_internal()

    def user_settings_to_dict(self):
        return {
            "camera": {
                "yaw": self.yaw,
                "pitch": self.pitch,
                "movement_speed": self.movement_speed,
                "mouse_sensitivity": self.mouse_sensitivity,
                "fov": self.fov,
                "pos": list(self.pos),
                "blur": self.blur,
                "dof_enabled": self.dof_enabled,
                "aperture": self.aperture,
                "focus_dist": self.focus_dist
            }
        }


class PathTracingSettings:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["path_tracing"]
        self.user_config = user_settings["path_tracing"]

        self._load_internal()
        self._load_user()

    def _load_internal(self):
        self.spp = self.internal_config["samples_per_pixel"]
        self.max_samples = self.internal_config["max_samples"]

        self.total_bounces = self.internal_config["total_bounces"]
        self.diffuse_bounces = self.internal_config["diffuse_bounces"]
        self.specular_bounces = self.internal_config["specular_bounces"]
        self.transmission_bounces = self.internal_config["transmission_bounces"]

        self.specular_mode = self.internal_config["specular_mode"]
        self.geometry_mode = self.internal_config["geometry_mode"]
        self.transmission_mode = self.internal_config["transmission_mode"]
        self.mis_mode = self.internal_config["mis_mode"]

        self.backface_culling = self.internal_config["backface_culling"]

        self.max_direct_luminance = self.internal_config["max_direct_luminance"]
        self.max_indirect_luminance = self.internal_config["max_indirect_luminance"]

    def _load_user(self):
        self.spp = self.user_config["samples_per_pixel"]
        self.max_samples = self.user_config["max_samples"]

        self.total_bounces = self.user_config["total_bounces"]
        self.diffuse_bounces = self.user_config["diffuse_bounces"]
        self.specular_bounces = self.user_config["specular_bounces"]
        self.transmission_bounces = self.user_config["transmission_bounces"]

        self.specular_mode = self.user_config["specular_mode"]
        self.geometry_mode = self.user_config["geometry_mode"]
        self.transmission_mode = self.user_config["transmission_mode"]
        self.mis_mode = self.user_config["mis_mode"]

        self.backface_culling = self.user_config["backface_culling"]

        self.max_direct_luminance = self.user_config["max_direct_luminance"]
        self.max_indirect_luminance = self.user_config["max_indirect_luminance"]

    def reset(self):
        self._load_internal()

    def user_settings_to_dict(self):
        return {
            "path_tracing": {
                "samples_per_pixel": self.spp,
                "max_samples": self.max_samples,
                "total_bounces": self.total_bounces,
                "diffuse_bounces": self.diffuse_bounces,
                "specular_bounces": self.specular_bounces,
                "transmission_bounces": self.transmission_bounces,
                "mis_mode": self.mis_mode,
                "specular_mode": self.specular_mode,
                "geometry_mode": self.geometry_mode,
                "transmission_mode": self.transmission_mode,
                "backface_culling": self.backface_culling,
                "max_direct_luminance": self.max_direct_luminance,
                "max_indirect_luminance": self.max_indirect_luminance
            }
        }


class BVHSettings:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["bvh"]
        self.user_config = user_settings["bvh"]

        self._load_internal()
        self._load_user()

    def _load_internal(self):
        self.max_depth = self.internal_config["max_depth"]
        self.sah_bins = self.internal_config["sah_bins"]

    def _load_user(self):
        self.max_depth = self.user_config["max_depth"]
        self.sah_bins = self.user_config["sah_bins"]

    def reset(self):
        self._load_internal()

    def user_settings_to_dict(self):
        return {
            "bvh": {
                "max_depth": self.max_depth,
                "sah_bins": self.sah_bins
            }
        }


class DebugSettings:
    class BVH:
        def __init__(self, internal_config, user_config):
            self.internal_config = internal_config
            self.user_config = user_config

            self._load_internal()
            self._load_user()

        def _load_internal(self):
            self.view_layer = self.internal_config["view_layer"]
            self.view_depth = self.internal_config["view_depth"]
            self.color_mode = self.internal_config["color_mode"]

        def _load_user(self):
            self.view_layer = self.user_config["view_layer"]
            self.view_depth = self.user_config["view_depth"]
            self.color_mode = self.user_config["color_mode"]
    
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["debug"]
        self.user_config = user_settings["debug"]

        self._load_internal()
        self._load_user()

    def _load_internal(self):
        self.bvh = self.BVH(self.internal_config["bvh"], self.user_config["bvh"])

    def _load_user(self):
        self.bvh = self.BVH(self.internal_config["bvh"], self.user_config["bvh"])

    def reset(self):
        self._load_internal()

    def user_settings_to_dict(self):
        return {
            "debug": {
                "bvh": {
                    "view_layer": self.bvh.view_layer,
                    "view_depth": self.bvh.view_depth,
                    "color_mode": self.bvh.color_mode
                }
            }
        }


class PostProcessingSettings:
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["post_processing"]
        self.user_config = user_settings["post_processing"]

        self._load_internal()
        self._load_user()

    def _load_internal(self):
        self.exposure = self.internal_config["exposure"]
        self.tonemap = self.internal_config["tonemap"]
        self.hdri_exposure = self.internal_config["hdri_exposure"]

    def _load_user(self):
        self.exposure = self.user_config["exposure"]
        self.tonemap = self.user_config["tonemap"]
        self.hdri_exposure = self.user_config["hdri_exposure"]

    def reset(self):
        self._load_internal()

    def user_settings_to_dict(self):
        return {
            "post_processing": {
                "exposure": self.exposure,
                "tonemap": self.tonemap,
                "hdri_exposure": self.hdri_exposure
            }
        }


class ShaderGroup:
    def __init__(self, config):
        for attr, rel_dir in config.items():
            if isinstance(rel_dir, dict):
                # Parse nested shader groups
                setattr(self, attr, ShaderGroup(rel_dir))
            else:
                root_dir = ROOT_DIR / rel_dir
                setattr(self, attr, root_dir)

class FilePathSettings:
    class AITraining:
        def __init__(self, internal_config, user_config):
            self.internal_config = internal_config
            self.user_config = user_config

            self._load_internal()
            self._load_user()

        def _load_internal(self):
            self.scenes = ROOT_DIR / self.internal_config["scenes"]
            self.hdris = ROOT_DIR / self.internal_config["hdris"]
            self.renders = ROOT_DIR / self.internal_config["renders"]
            self.camera_capture_states = ROOT_DIR / self.internal_config["camera_capture_states"]

        def _load_user(self):
            self.scenes = ROOT_DIR / self.user_config["scenes"]
            self.hdris = ROOT_DIR / self.user_config["hdris"]
            self.renders = ROOT_DIR / self.user_config["renders"]

    class Denoiser:
        def __init__(self, internal_config):
            self.internal_config = internal_config

            self._load_internal()

        def _load_internal(self):
            self.checkpoint = ROOT_DIR / self.internal_config["checkpoint"]
            self.last_checkpoint = ROOT_DIR / self.internal_config["last_checkpoint"]

    class Cache:
        def __init__(self, internal_config):
            self.internal_config = internal_config

            self._load_internal()

        def _load_internal(self):
            self.scene = ROOT_DIR / self.internal_config["scene"]
            self.bvh = ROOT_DIR / self.internal_config["bvh"]
            
    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["file_paths"]
        self.user_config = user_settings["file_paths"]

        self._load_internal()
        self._load_user()

    def _load_internal(self):
        self.scenes = ROOT_DIR / self.internal_config["scenes"]
        self.scene = ROOT_DIR / self.internal_config["scene"]
        self.hdri = ROOT_DIR / self.internal_config["hdri"]
        self.renders = ROOT_DIR / self.internal_config["renders"]

        self.ai_training = self.AITraining(self.internal_config["ai_training"], self.user_config["ai_training"])
        self.denoiser = self.Denoiser(self.internal_config["denoiser"])

        self.path_tracing = ShaderGroup(self.internal_config["path_tracing"])
        self.background = ShaderGroup(self.internal_config["rasterization"]["background"])
        self.pbr = ShaderGroup(self.internal_config["rasterization"]["pbr"])
        self.final = ShaderGroup(self.internal_config["rasterization"]["final"])

        self.cache = self.Cache(self.internal_config["cache"])

    def _load_user(self):
        self.scenes = ROOT_DIR / self.user_config["scenes"]
        self.scene = ROOT_DIR / self.user_config["scene"]
        self.hdri = ROOT_DIR / self.user_config["hdri"]
        self.renders = ROOT_DIR / self.user_config["renders"]

        self.ai_training = self.AITraining(self.internal_config["ai_training"], self.user_config["ai_training"])

    def reset(self):
        self._load_internal()

    def user_settings_to_dict(self):
        def rel(path):
            path = Path(path)

            try:
                return str(path.relative_to(ROOT_DIR))
            except:
                # File lives outside of the project root
                return str(path)
        
        return {
            "file_paths": {
                "scenes": rel(self.scenes),
                "scene": rel(self.scene),
                "hdri": rel(self.hdri),
                "renders": rel(self.renders),
                "ai_training": {
                    "scenes": rel(self.ai_training.scenes),
                    "hdris": rel(self.ai_training.hdris),
                    "renders": rel(self.ai_training.renders),
                }
            }
        }


class RenderingSettings:
    class Tiles:
        def __init__(self, internal_config, user_config):
            self.internal_config = internal_config
            self.user_config = user_config

            self._load_internal()
            self._load_user()

        def _load_internal(self):
            self.x = self.internal_config["x"]
            self.y = self.internal_config["y"]

        def _load_user(self):
            self.x = self.user_config["x"]
            self.y = self.user_config["y"]

    def __init__(self, internal_settings, user_settings):
        self.internal_config = internal_settings["rendering"]
        self.user_config = user_settings["rendering"]

        self._load_internal()
        self._load_user()

    def _load_internal(self):
        self.mode = self.internal_config["mode"]
        self.texture_size = self.internal_config["texture_size"]
        self.tiles = self.Tiles(self.internal_config["tiles"], self.user_config["tiles"])

    def _load_user(self):
        self.mode = self.user_config["mode"]
        self.texture_size = self.user_config["texture_size"]
        self.tiles = self.Tiles(self.internal_config["tiles"], self.user_config["tiles"])

    def reset(self):
        self._load_internal()

    def user_settings_to_dict(self):
        return {
            "rendering": {
                "mode": self.mode,
                "texture_size": self.texture_size,
                "tiles": {
                    "x": self.tiles.x,
                    "y": self.tiles.y
                }
            }
        }


class AITrainingSettings:
    def __init__(self, internal_settings):
        self.internal_config = internal_settings["ai_training"]

        self._load_internal()

    def _load_internal(self):
        self.mode = self.internal_config["mode"]

    def reset(self):
        self._load_internal()


class Settings:
    def __init__(self, internal_settings, user_settings):
        self.screen = ScreenSettings(internal_settings, user_settings)
        self.camera = CameraSettings(internal_settings, user_settings)
        self.path_tracing = PathTracingSettings(internal_settings, user_settings)
        self.bvh = BVHSettings(internal_settings, user_settings)
        self.debug = DebugSettings(internal_settings, user_settings)
        self.post_processing = PostProcessingSettings(internal_settings, user_settings)
        self.file_paths = FilePathSettings(internal_settings, user_settings)
        self.rendering = RenderingSettings(internal_settings, user_settings)
        self.ai_training = AITrainingSettings(internal_settings)

        self._groups = [
            self.screen, self.camera, self.path_tracing, self.bvh, self.debug,
            self.post_processing, self.file_paths, self.rendering
        ]

    def export_user_settings(self):
        merged = {}
        for group in self._groups:
            merged.update(group.user_settings_to_dict())

        with open("src/settings/user.json", "w") as f:
            json.dump(merged, f, indent=4, sort_keys=True)

    def reset_all(self):
        for group in self._groups:
            group.reset()


with open("src/settings/internal.json") as f:
    internal_settings = json.load(f)

with open("src/settings/user.json") as f:
    user_settings = json.load(f)

ROOT_DIR = Path(__file__).resolve().parent.parent

# glTF KHR_lights_punctual defines intensity in photometric units
# Convert to radiometric units matching Blender's export constant
LUMENS_TO_WATTS = 1.0 / 683.0

AI_DEVICE = torch.device("cpu")
if torch.cuda.is_available():
    AI_DEVICE = torch.device("cuda")

settings = Settings(internal_settings, user_settings)
