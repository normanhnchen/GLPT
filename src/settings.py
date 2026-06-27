import json
import numpy as np
import glm


class Screen:
    def __init__(self, json_settings):
        screen_config = json_settings["screen"]

        self.width = screen_config["width"]
        self.height = screen_config["height"]
        self.resolution = np.array([self.width, self.height])
        self.vsync = screen_config["vsync"]
        self.fps_cap = screen_config["fps_cap"]


class CameraSettings:
    def __init__(self, json_settings):
        camera_config = json_settings["camera"]

        self._yaw = camera_config["_yaw"]
        self._pitch = camera_config["_pitch"]
        self.movement_speed = camera_config["movement_speed"]
        self.mouse_sensitivity = camera_config["mouse_sensitivity"]
        self.fov = camera_config["fov"]
        self.pos = glm.vec3(camera_config["pos"])
        self._front = glm.vec3(camera_config["_front"])
        self._up = glm.vec3(camera_config["_up"])
        self._world_up = glm.vec3(camera_config["_world_up"])


class PTSettings:
    def __init__(self, json_settings):
        pt_config = json_settings["path_tracing"]

        self.max_depth = pt_config["max_depth"]
        self.max_samples = pt_config["max_samples"]


class PostProcessSettings:
    def __init__(self, json_settings):
        post_process_config = json_settings["post_processing"]

        self.blur = post_process_config["blur"]
        self.aperture = post_process_config["aperture"]
        self.focus_dist = post_process_config["focus_dist"]
        self.auto_focus = post_process_config["auto_focus"]
        self.exposure = post_process_config["exposure"]
        self.tonemap = post_process_config["tonemap"]
        self.hdri_exposure = post_process_config["hdri_exposure"]


class FilePaths:
    def __init__(self, json_settings):
        file_paths_config = json_settings["file_paths"]

        self.scene = file_paths_config["scene"]
        self.hdri = file_paths_config["hdri"]
        
        self.vert = file_paths_config["vert"]
        self.frag = file_paths_config["frag"]
        self.comp = file_paths_config["comp"]        


with open("src/settings.json") as f:
    json_settings = json.load(f)

screen = Screen(json_settings)
camera_settings = CameraSettings(json_settings)
pt_settings = PTSettings(json_settings)
post_process_settings = PostProcessSettings(json_settings)
file_paths = FilePaths(json_settings)
