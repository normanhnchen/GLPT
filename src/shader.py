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
    
    def _reset_tonemaps(self):
        self.prog["None"].value = set_i4(0)
        self.prog["ACESFilm"].value = set_i4(0)
        self.prog["AgX"].value = set_i4(0)
        self.prog["AgXGolden"].value = set_i4(0)
        self.prog["AgXPunchy"].value = set_i4(0)
        self.prog["Filmic"].value = set_i4(0)
        self.prog["Lottes"].value = set_i4(0)
        self.prog["Neutral"].value = set_i4(0)
        self.prog["Reinhard"].value = set_i4(0)
        self.prog["Reinhard2"].value = set_i4(0)
        self.prog["Uchimura"].value = set_i4(0)
        self.prog["Uncharted2"].value = set_i4(0)
        self.prog["Unreal"].value = set_i4(0)

    def set_tonemap(self, name):
        self._reset_tonemaps()

        if name == "None":
            self.prog["None"].value = set_i4(1)
        elif name == "ACESFilm":
            self.prog["ACESFilm"].value = set_i4(1)
        elif name == "AgX":
            self.prog["AgX"].value = set_i4(1)
        elif name == "AgXGolden":
            self.prog["AgXGolden"].value = set_i4(1)
        elif name == "AgXPunchy":
            self.prog["AgXPunchy"].value = set_i4(1)
        elif name == "Filmic":
            self.prog["Filmic"].value = set_i4(1)
        elif name == "Lottes":
            self.prog["Lottes"].value = set_i4(1)
        elif name == "Neutral":
            self.prog["Neutral"].value = set_i4(1)
        elif name == "Reinhard":
            self.prog["Reinhard"].value = set_i4(1)
        elif name == "Reinhard2":
            self.prog["Reinhard2"].value = set_i4(1)
        elif name == "Uchimura":
            self.prog["Uchimura"].value = set_i4(1)
        elif name == "Uncharted2":
            self.prog["Uncharted2"].value = set_i4(1)
        elif name == "Unreal":
            self.prog["Unreal"].value = set_i4(1)


class ComputeShader:
    def __init__(self, ctx, comp_path):
        try:
            src = _load_shader(comp_path)

            self.prog = ctx.compute_shader(src)
        except Exception as e:
            print(f"Compute shader file was not succesfully read: {e}")
