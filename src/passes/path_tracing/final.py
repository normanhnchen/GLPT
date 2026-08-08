from src.settings import *
from src.fullscreen_quad import *


def _compute_uniforms():
    return {
        "exposure": post_process_settings.exposure
    }


def _set_uniforms(prog, uniform_dict):
    for uniform, value in uniform_dict.items():
        if isinstance(value, bytes):
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

    def render(self):
        self.final_output_state.output_fbo.use()

        # Draw to screen
        self.pt_state.framebuffers.combined.use(location=0)

        uniform_dict = _compute_uniforms()
        _set_uniforms(self.shader.prog, uniform_dict)

        self.shader.set_tonemap(post_process_settings.tonemap)

        self.quad.draw()

        self.ctx.copy_framebuffer(self.ctx.screen, self.final_output_state.output_fbo)
        self.ctx.screen.use()
