import numpy as np

from src.dtypes import *


class DepthDebugPass:
    def __init__(self, pt_state):
        self.pt_state = pt_state

    def render(self):
        depth_arr = self.pt_state.framebuffers.get_ndarray_depth()

        depth = depth_arr[..., 0]
        hit_fraction = depth_arr[..., 1]
        # Misses are set to 0.0 in the path trace shader
        hit_mask = hit_fraction > 0.0

        normalized = np.zeros_like(depth, dtype=f4)

        if np.any(hit_mask):
            hit_depths = depth[hit_mask]
            min_depth = hit_depths.min()
            max_depth = hit_depths.max()

            if max_depth > min_depth:
                remapped = (hit_depths - min_depth) / (max_depth - min_depth)
                # Subtract from 1 to follow convention: close = 1, far = 0
                normalized[hit_mask] = 1 - remapped
            else:
                normalized[hit_mask] = 1

        normalized = normalized * hit_fraction

        output = depth_arr.copy()
        output[..., 0] = normalized
        output[..., 1] = normalized
        output[..., 2] = normalized

        self.pt_state.framebuffers.combined.write(output.tobytes())
