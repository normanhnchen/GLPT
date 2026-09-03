from pathlib import Path
import random
import time
import json

from src.settings import settings
from src.bvh_builder import BVHBackgroundBuilder
from src.buffer_loading import BVHNodeBuffer, TriangleIndicesBuffer, BVHDepthsBuffer
from src.scene.caching import load_bvh


class SceneState:
    def __init__(self):
        self.scenes_path = Path(settings.file_paths.ai_training.scenes)
        self.scene_files = [scene for scene in self.scenes_path.iterdir()]
        self.num_scenes = len(self.scene_files)
        self.curr_scene_idx = 0
        self.curr_scene_file = self.scene_files[self.curr_scene_idx]

        self.hdris_path = Path(settings.file_paths.ai_training.hdris)
        self.hdri_files = [hdri for hdri in self.hdris_path.iterdir()]
        random.shuffle(self.hdri_files)
        self.num_hdris = len(self.hdri_files)
        self.curr_hdri_idx = 0
        self.curr_hdri_file = self.hdri_files[self.curr_hdri_idx]

        self.changed_scene = False
        self.ai_training_finished = False
    
    def next_scene(self):
        if self.curr_scene_idx < self.num_scenes - 1:
            self.curr_scene_idx += 1
            self.curr_scene_file = self.scene_files[self.curr_scene_idx]
            
            # Wrap back to the first HDRI once we've cycled through all of them
            self.curr_hdri_idx = (self.curr_hdri_idx + 1) % self.num_hdris
            self.curr_hdri_file = self.hdri_files[self.curr_hdri_idx]

            self.changed_scene = True
        
        else:
            self.ai_training_finished = True
    
    def previous_scene(self):
        if self.curr_scene_idx > 0:
            self.curr_scene_idx -= 1
            self.curr_scene_file = self.scene_files[self.curr_scene_idx]

            # Wrap back to the last HDRI if we go below the first one
            self.curr_hdri_idx = (self.curr_hdri_idx - 1) % self.num_hdris
            self.curr_hdri_file = self.hdri_files[self.curr_hdri_idx]

            self.changed_scene = True


class BVHState:
    def __init__(self, ctx, scene):
        self.ctx = ctx
        self.scene = scene

        self.ready = False
        self.built = False
        self.builder = None

        self.build_time = None
        self.buffers_created = False

    def background_build(self):
        self.builder = BVHBackgroundBuilder(self.scene)
        self.bvh_built = False

    def build(self):
        build_start_time = time.perf_counter()

        bvh = load_bvh(self.scene)
        self.scene.bvh = bvh
        self.scene.num_bvh_nodes = bvh.nodes_used

        self.bvh_built = True

        build_end_time = time.perf_counter()
        self.build_time = build_end_time - build_start_time

    def update(self, bvh_node_loc, tri_indices_loc, bvh_depths_loc):
        if self.ready:
            return

        if self.builder is not None and self.builder.is_done:
            self.bvh_built = True
            self.builder = None
        
        if self.bvh_built:
            bvh_node_buffer = BVHNodeBuffer(self.scene)
            tri_indices_buffer = TriangleIndicesBuffer(self.scene)
            bvh_depths_buffer = BVHDepthsBuffer(self.scene)

            bvh_node_buffer.bind(self.ctx, bvh_node_loc)
            tri_indices_buffer.bind(self.ctx, tri_indices_loc)
            bvh_depths_buffer.bind(self.ctx, bvh_depths_loc)

            self.ready = True

            self.buffers_created = True



# See 9.4 Rendering
class CameraCaptureState:
    def __init__(self, scene_state, camera):
        self.scene_state = scene_state
        self.camera = camera
        self.camera_buffer = None
        self.states = {self._key(f):[] for f in self.scene_state.scene_files}
        self.curr_state_idx = 0
        self.browse_idx = 0

        self._load_states()

    def set_camera_buffer(self, camera_buffer):
        self.camera_buffer = camera_buffer

    def _key(self, scene_file):
        return Path(scene_file).name

    def _get_key(self):
        scene_file = self.scene_state.scene_files[self.scene_state.curr_scene_idx]
        return self._key(scene_file)
    
    def _load_states(self):
        try:
            with open(settings.file_paths.ai_training.camera_capture_states) as f:
                loaded = json.load(f)
        except:
            loaded = {}

        # Rebuild to add new scenes and remove stale keys
        self.states = {
            self._key(f): loaded.get(self._key(f), [])
            for f in self.scene_state.scene_files
        }

    def _get_scene_captures(self):
        return self.states[self._get_key()]

    def _load_state(self, state):
        self.camera.load_state(state, randomize=True)
        self.camera_buffer.update_data()

    def _write(self):
        with open(settings.file_paths.ai_training.camera_capture_states, "w") as f:
            json.dump(self.states, f, indent=4, sort_keys=True)

    def save_state(self):
        key = self._get_key()
        self.states[key].append(self.camera.get_state())
        self.browse_idx = len(self.states[key]) - 1
        self._write()
    
    def load_next_state(self):
        while True:
            captures = self._get_scene_captures()

            if self.curr_state_idx < len(captures):
                self._load_state(captures[self.curr_state_idx])
                self.curr_state_idx += 1
                return
            
            self.scene_state.next_scene()

            if self.scene_state.ai_training_finished:
                return
            
            self.curr_state_idx = 0

    def view_current(self):
        captures = self._get_scene_captures()
        if captures:
            self._load_state(captures[self.browse_idx])

    def next_capture(self):
        captures = self._get_scene_captures()
        if not captures:
            return
        self.browse_idx = (self.browse_idx + 1) % len(captures)
        self._load_state(captures[self.browse_idx])

    def previous_capture(self):
        captures = self._get_scene_captures()
        if not captures:
            return
        self.browse_idx = (self.browse_idx - 1) % len(captures)
        self._load_state(captures[self.browse_idx])

    def delete_current(self):
        captures = self._get_scene_captures()
        if not captures:
            return

        captures.pop(self.browse_idx)
        self._write()

        if not captures:
            self.browse_idx = 0
            return

        self.browse_idx = min(self.browse_idx, len(captures) - 1)
