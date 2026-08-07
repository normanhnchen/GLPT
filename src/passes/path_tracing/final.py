from src.settings import *


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
    def __init__(self, shader, pt_state, quad):
        self.shader = shader
        self.pt_state = pt_state
        self.quad = quad

    def render(self):
        # Draw to screen
        self.pt_state.framebuffers.combined.use(location=0)

        uniform_dict = _compute_uniforms()
        _set_uniforms(self.shader.prog, uniform_dict)

        self.shader.set_tonemap(post_process_settings.tonemap)

        self.quad.draw()
