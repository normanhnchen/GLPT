from src.passes.path_tracing.path_trace import *
from src.passes.path_tracing.final import *


class PathTracingPipeline:
    def __init__(self, ctx, scene, pt_state, final_output_state, pt_shaders, ai_denoiser=None):
        self.ctx = ctx
        self.pt_state = pt_state
        self.ai_denoiser = ai_denoiser
        self.pt_pass = PathTracePass(scene, pt_state, pt_shaders.pt)
        self.final_pass = FinalPass(ctx, pt_shaders.final, pt_state, final_output_state)

    def render(self):
        if self.pt_state.denoising.should_denoise and self.ai_denoiser is not None:
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
        
        self.final_pass.render()
