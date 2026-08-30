from src.settings import settings
from src.dtypes import *


def _load_shader_source(path, is_root=True):
        try:
            version = ""
            shader_source = ""
            with open(path, "r") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("#include"):
                        include_path = stripped.split('"')[1]
                        file_path = settings.root_dir / include_path
                        shader_source += _load_shader_source(file_path, is_root=False)
                        shader_source += "\n"

                    elif stripped.startswith("#version"):
                        if is_root and not version:
                            version = line

                    else:
                        shader_source += line

            return version + shader_source

        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find shader file at: {path}")

        
class Shader:
    def __init__(self, ctx, vert_path, frag_path):
        try:
            vert_src = _load_shader_source(vert_path)
            frag_src = _load_shader_source(frag_path)

            self.prog = ctx.program(
                vertex_shader=vert_src,
                fragment_shader=frag_src
            )
        except Exception as e:
            print(f"Shader files not successfully read: {e}")
            raise
    
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
            src = _load_shader_source(comp_path)

            self.prog = ctx.compute_shader(src)
        except Exception as e:
            print(f"Compute shader file was not succesfully read: {e}")
            raise
