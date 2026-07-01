import json
import numpy as np
import glm


class Screen:
    def __init__(self, json_settings):
        config = json_settings["screen"]

        self.width = config["width"]
        self.height = config["height"]
        self.resolution = np.array([self.width, self.height])
        self.vsync = config["vsync"]
        self.fps_cap = config["fps_cap"]


class CameraSettings:
    def __init__(self, json_settings):
        config = json_settings["camera"]

        self._yaw = config["_yaw"]
        self._pitch = config["_pitch"]
        self.movement_speed = config["movement_speed"]
        self.mouse_sensitivity = config["mouse_sensitivity"]
        self.fov = config["fov"]
        self.pos = glm.vec3(config["pos"])
        self._front = glm.vec3(config["_front"])
        self._up = glm.vec3(config["_up"])
        self._world_up = glm.vec3(config["_world_up"])


class PTSettings:
    def __init__(self, json_settings):
        config = json_settings["path_tracing"]

        self.spp = config["samples_per_pixel"]
        self.max_bounces = config["max_bounces"]
        self.max_samples = config["max_samples"]


class PostProcessSettings:
    def __init__(self, json_settings):
        config = json_settings["post_processing"]

        self.blur = config["blur"]
        self.aperture = config["aperture"]
        self.focus_dist = config["focus_dist"]
        self.auto_focus = config["auto_focus"]
        self.exposure = config["exposure"]
        self.tonemap = config["tonemap"]
        self.hdri_exposure = config["hdri_exposure"]


class ShaderGroup:
    def __init__(self, config):
        for key, value in config.items():
            setattr(self, key, value)

class FilePaths:
    def __init__(self, json_settings):
        config = json_settings["file_paths"]

        self.scene = config["scene"]
        self.hdri = config["hdri"]
        
        self.path_tracing = ShaderGroup(config["path_tracing"])
        self.background = ShaderGroup(config["rasterization"]["background"])
        self.pbr = ShaderGroup(config["rasterization"]["pbr"])
        self.final = ShaderGroup(config["rasterization"]["final"])

        self.scene_cache = config["cache"]["scene"]
        self.bvh_cache = config["cache"]["bvh"]


class RenderSettings:
    def __init__(self, json_settings):
        config = json_settings["render"]

        self.render_mode = config["render_mode"]
        self.texture_size = config["texture_size"]
        self.tiles_x = config["tiles_x"]
        self.tiles_y = config["tiles_y"]


with open("src/settings.json") as f:
    json_settings = json.load(f)

screen = Screen(json_settings)
camera_settings = CameraSettings(json_settings)
pt_settings = PTSettings(json_settings)
post_process_settings = PostProcessSettings(json_settings)
file_paths = FilePaths(json_settings)
render_settings = RenderSettings(json_settings)
screen_default = Screen(json_settings)
_camera_settings_default = CameraSettings(json_settings)
_pt_settings_default = PTSettings(json_settings)
_post_process_settings_default = PostProcessSettings(json_settings)
_file_paths_default = FilePaths(json_settings)
_render_settings_default = RenderSettings(json_settings)
