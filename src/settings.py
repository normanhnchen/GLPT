import json
import numpy as np


class Screen:
    def __init__(self, settings):
        self.width = settings["screen"]["width"]
        self.height = settings["screen"]["height"]
        self.resolution = np.array([self.width, self.height])
        self.vsync = settings["screen"]["vsync"]
        self.fps_cap = settings["screen"]["fps_cap"]


class PathTracing:
    def __init__(self, settings):
        self.max_depth = settings["path_tracing"]["max_depth"]


with open("src/settings.json") as f:
    json_settings = json.load(f)

screen = Screen(json_settings)
path_tracing = PathTracing(json_settings)