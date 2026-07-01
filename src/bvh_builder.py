import time
import threading


class BVHBuilder:
    def __init__(self, scene):
        self.scene = scene
        self._thread = threading.Thread(target=self._build, daemon=True)
        self._thread.start()
        self.is_done = False
    
    def _build(self):
        start_time = time.perf_counter()
        print("Building BVH in the background...")

        self.scene.build_bvh()
        self.is_done = True

        end_time = time.perf_counter()
        print(f"BVH built in {end_time - start_time:.4f}s")
    