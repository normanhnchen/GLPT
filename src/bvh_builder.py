import threading

from src.scene.caching import load_bvh


class BVHBackgroundBuilder:
    def __init__(self, scene):
        self.scene = scene
        self.is_done = False
        self._thread = threading.Thread(target=self._build, daemon=True)
        self._thread.start()
    
    def _build(self):
        bvh = load_bvh(self.scene)
        self.scene.bvh = bvh
        self.scene.num_bvh_nodes = bvh.nodes_used
        self.is_done = True
    