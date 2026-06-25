import glm
import moderngl

from src.dtypes import *


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
        
    def set_tonemap(self, name):
        # Reset selected tonemap
        self.prog["Reinhard"].value = set_i4(0)
        self.prog["Reinhard2"].value = set_i4(0)
        self.prog["ACESFilm"].value = set_i4(0)
        self.prog["Uchimura"].value = set_i4(0)
        self.prog["Lottes"].value = set_i4(0)

        if name == "Reinhard":
            self.prog["Reinhard"].value = set_i4(1)
        elif name == "Reinhard2":
            self.prog["Reinhard2"].value = set_i4(1)
        elif name == "ACES":
            self.prog["ACES"].value = set_i4(1)
        elif name == "Uchimura":
            self.prog["Uchimura"].value = set_i4(1)
        elif name == "Lottes":
            self.prog["Lottes"].value = set_i4(1)
        

class ComputeShader:
    def __init__(self, ctx, comp_path):
        try:
            src = _load_shader(comp_path)

            self.prog = ctx.compute_shader(src)
        except Exception as e:
            print(f"Compute shader file was not succesfully read: {e}")
