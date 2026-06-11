import glm
import moderngl


def _load_shader(path):
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find shader file at: {path}")
        

class Shader:
    def __init__(self, ctx, vert_path, frag_path):
        try:
            vert_src = _load_shader(vert_path)
            frag_src = _load_shader(frag_path)

            self.prog = ctx.program(
                vertex_shader=vert_src,
                fragment_shader=frag_src
            )
        except Exception as e:
            print(f"Shader files not successfully read: {e}")


class CompShader:
    def __init__(self, ctx, comp_path):
        try:
            src = _load_shader(comp_path)

            self.prog = ctx.compute_shader(src)
        except Exception as e:
            print(f"Compute shader file was not succesfully read: {e}")
