from src.settings import settings
from src.fullscreen_quad import FullScreenQuad


def _compute_uniforms(pt_state):
    return {
        # Fragment Shader Uniforms
        # ------------------------
        "exposure": settings.post_processing.exposure,
        "debugMode": pt_state.debug.mode
    }


def _set_uniforms(prog, uniform_dict):
    for uniform, value in uniform_dict.items():
        if isinstance(value, bytes):
            # Matrices can't be assigned via .value = ... like scalar/vector
            # uniforms; matrices need .write(bytes)
            prog[uniform].write(value)
        
        else:
            prog[uniform].value = value


class FinalPass:
    def __init__(self, ctx, shader, pt_state, final_output_state):
        self.ctx = ctx
        self.shader = shader
        self.pt_state = pt_state
        self.final_output_state = final_output_state
        self.quad = FullScreenQuad(ctx, shader)

    def render(self, override_texture=None):
        self.final_output_state.output_fbo.use()

        # Draw to screen
        texture = override_texture if override_texture is not None else self.pt_state.framebuffers.combined
        texture.use(location=0)

        uniform_dict = _compute_uniforms(self.pt_state)
        _set_uniforms(self.shader.prog, uniform_dict)

        self.shader.set_tonemap(settings.post_processing.tonemap)

        self.quad.draw()

        # The pass is always rendered into the output FBO and never directly to the screen
        # so blit it directly to the screen
        self.ctx.copy_framebuffer(self.ctx.screen, self.final_output_state.output_fbo)
        self.ctx.screen.use()
