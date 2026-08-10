from src.passes.path_tracing.path_trace import *
from src.passes.path_tracing.final import *
from src.passes.path_tracing.bvh_depth_debug import *
from src.passes.path_tracing.bvh_bounds_debug import *


class PathTracingPipeline:
    def __init__(self, ctx, scene, camera, pt_state, final_output_state, pt_shaders, ai_denoiser=None):
        self.ctx = ctx
        self.pt_state = pt_state
        self.ai_denoiser = ai_denoiser
        self.pt_pass = PathTracePass(scene, camera, pt_state, pt_shaders.pt)
        self.bvh_depth_debug_pass = BVHDepthDebugPass(pt_state)
        self.bvh_bounds_debug_pass = BVHBoundsDebugPass(ctx, scene, camera, pt_shaders.bvh_bounds_debug)
        self.final_pass = FinalPass(ctx, pt_shaders.final, pt_state, final_output_state)

    def render(self):
        is_denoising = (
            self.pt_state.denoising.should_denoise and
            self.ai_denoiser is not None and
            self.pt_state.debug.mode == 0 # Off
        )

        if is_denoising:
            self.pt_state.denoise(self.ai_denoiser)

            # Draw to screen
            self.pt_state.denoising.saved_denoised.use(location=0)

            # Prevent resizing saved texture
            # Clips the image
            self.ctx.viewport = (0, 0, *self.pt_state.framebuffers.saved_combined.size)

        elif self.pt_state.rendering.should_view_saved:
            # Prevent resizing saved texture to new screen dimensions
            # Doesn't matter which saved texture to use since all are saved at the same dimensions
            self.ctx.viewport = (0, 0, *self.pt_state.framebuffers.saved_combined.size)
        
        elif self.pt_state.rendering.should_render:
            self.pt_pass.render()

            # Depth
            if self.pt_state.debug.mode == 3:
                self.bvh_depth_debug_pass.render()

            # BVH Bounds
            if self.pt_state.debug.mode == 7:
                self.bvh_bounds_debug_pass.render()
                self.ctx.screen.use()
                return

        self.final_pass.render()
