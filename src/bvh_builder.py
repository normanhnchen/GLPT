import threading


class BVHBuilder:
    def __init__(self, scene):
        self.scene = scene
        self._thread = threading.Thread(target=self._build, daemon=True)
        self._thread.start()
        self.is_done = False
    
    def _build(self):
        self.scene.build_bvh()
        self.is_done = True
    