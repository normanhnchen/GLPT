from src.passes.path_tracing.path_trace import *
from src.passes.path_tracing.final import *


class PathTracingPipeline:
    def __init__(self, scene, pt_state, pt_shaders, pt_quad):
        self.pt_state = pt_state
        self.pt_pass = PathTracePass(scene, pt_state, pt_shaders.pt)
        self.final_pass = FinalPass(pt_shaders.final, pt_state, pt_quad)

    def render(self):
        if self.pt_state.rendering.should_render:
            self.pt_pass.render()
        self.final_pass.render()
