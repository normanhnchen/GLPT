from src.settings import settings
from src.dtypes import *


class Texture:
    def __init__(self, pil_image):
        if pil_image is None:
            self.is_empty = True
            self.data = None
            return
            
        self.is_empty = False
        self.image = pil_image.convert("RGBA")
    
    def resize(self, width, height):
        if self.is_empty:
            return
        self.image = self.image.resize((width, height)).convert("RGBA")


class Material:
    def __init__(self, trimesh_material, extensions, pbr_factors=None):
        alpha_mode = getattr(trimesh_material, "alphaMode", "OPAQUE")
        if alpha_mode == "MASK":
            self.alpha_mode = 1
        elif alpha_mode == "BLEND":
            self.alpha_mode = 2
        else: # OPAQUE
            self.alpha_mode = 0
        self.alpha_cutoff = getattr(trimesh_material, "alphaCutoff", 0.5)
        self.double_sided = bool(getattr(trimesh_material, "doubleSided", False))

        base_color = getattr(trimesh_material, "baseColorFactor", None)
        emissive_color = getattr(trimesh_material, "emissiveFactor", None)
        roughness = getattr(trimesh_material, "roughnessFactor", None)
        metallic = getattr(trimesh_material, "metallicFactor", None)

        base_color_tex = getattr(trimesh_material, "baseColorTexture", None)
        emissive_tex = getattr(trimesh_material, "emissiveTexture", None)
        normal_tex = getattr(trimesh_material, "normalTexture", None)
        occlusion_tex = getattr(trimesh_material, "occlusionTexture", None)

        metallic_roughness_texture = getattr(trimesh_material, "metallicRoughnessTexture", None)
        
        roughness_tex = None
        metallic_tex = None

        # Unpack metallic roughness texture
        if metallic_roughness_texture is not None:
            channels = metallic_roughness_texture.split()
            roughness_tex = channels[1] # Green channel
            metallic_tex = channels[2] # Blue channel
        
        self.base_color_tex = Texture(base_color_tex)
        self.emissive_tex = Texture(emissive_tex)
        self.roughness_tex = Texture(roughness_tex)
        self.metallic_tex = Texture(metallic_tex)
        self.normal_tex = Texture(normal_tex)
        self.occlusion_tex = Texture(occlusion_tex)

        self.textures = [
            self.base_color_tex,
            self.emissive_tex,
            self.roughness_tex,
            self.metallic_tex,
            self.normal_tex,
            self.occlusion_tex
        ]

        width, height = settings.rendering.texture_size
        for tex in self.textures:
            tex.resize(width, height)

        if base_color is not None:
            self.base_color = self._to_float_rgb(trimesh_material.baseColorFactor)
        else:
            # Set default color
            self.base_color = np.array([0.8, 0.8, 0.8, 1.0], dtype=f4)
        
        if emissive_color is not None:
            self.emissive_color = self._to_float_rgb(trimesh_material.emissiveFactor)
            self.has_emission = set_i4(1)
        else:
            # Set to no emission 
            self.emissive_color = np.array([0, 0, 0], dtype=f4)
            self.has_emission = set_i4(0)

        if roughness is not None:
            self.roughness = set_f4(trimesh_material.roughnessFactor)
        else:
            # Set default roughness
            self.roughness = set_f4(0.8)
        
        if metallic is not None:
            self.metallic = set_f4(trimesh_material.metallicFactor)
        else:
            # Set to no metallic
            self.metallic = set_f4(0)
        
        self.has_emission = set_i4(1) if emissive_color is not None else set_i4(0)
        self.has_base_color_tex = set_i4(0) if self.base_color_tex.is_empty else set_i4(1)
        self.has_emissive_tex = set_i4(0) if self.emissive_tex.is_empty else set_i4(1)
        self.has_roughness_tex = set_i4(0) if self.roughness_tex.is_empty else set_i4(1)
        self.has_metallic_tex = set_i4(0) if self.metallic_tex.is_empty else set_i4(1)
        self.has_normal_tex = set_i4(0) if self.normal_tex.is_empty else set_i4(1)
        self.has_occlusion_tex = set_i4(0) if self.occlusion_tex.is_empty else set_i4(1)

        self.base_color_tex_id = set_i4(-1)
        self.emissive_tex_id = set_i4(-1)
        self.roughness_tex_id = set_i4(-1)
        self.metallic_tex_id = set_i4(-1)
        self.normal_tex_id = set_i4(-1)
        self.occlusion_tex_id = set_i4(-1)
        
        # glTF extensions
        # ---------------
        extensions = extensions or {}

        KHR_materials_emissive_strength = extensions.get("KHR_materials_emissive_strength")
        if KHR_materials_emissive_strength:
            self.emissive_strength = KHR_materials_emissive_strength["emissiveStrength"]
        else:
            self.emissive_strength = set_f4(0)

        KHR_materials_transmission = extensions.get("KHR_materials_transmission")
        if KHR_materials_transmission:
            self.transmission = KHR_materials_transmission["transmissionFactor"]
        else:
            self.transmission = set_f4(0)

        KHR_materials_ior = extensions.get("KHR_materials_ior")
        if KHR_materials_ior:
            self.ior = KHR_materials_ior["ior"]
        else:
            self.ior = set_f4(1.5)

        # Replace roughness and metallic with extracted factors from glTF extensions
        # NOTE: Trimesh has an issue where it converts roughness = 1 and metallic = 1 to None
        pbr_factors = pbr_factors or {}
        self.roughness = set_f4(pbr_factors.get("roughnessFactor", 1))
        self.metallic = set_f4(pbr_factors.get("metallicFactor", 0))

    def _to_float_rgb(self, color):
        color = np.asarray(color, dtype=f4)
        if np.max(color) > 1.0:
            # Convert to float RGB
            return color / 255
        return color

    def snapshot_original(self):
        """
        Create a snapshot of the original material before scrambling.
        Only used for AI training.
        """

        self._original_base_color = self.base_color.copy()
        self._original_roughness = float(self.roughness)
        self._original_metallic = float(self.metallic)
        self._original_emissive_color = self.emissive_color.copy()
        self._original_emissive_strength = float(self.emissive_strength)
        self._original_has_emission = bool(self.has_emission)
        self._original_transmission = float(self.transmission)
        self._original_ior = float(self.ior)
        self._original_alpha_mode = int(self.alpha_mode)

    def _reset(self):
        """
        Restore this material to its original (un-scrambled) values.
        Only used for AI training.
        """

        self.base_color = self._original_base_color.copy()
        self.roughness = set_f4(self._original_roughness)
        self.metallic = set_f4(self._original_metallic)
        self.emissive_color = self._original_emissive_color.copy()
        self.emissive_strength = self._original_emissive_strength
        self.has_emission = set_i4(1 if self._original_has_emission else 0)
        self.transmission = set_f4(self._original_transmission)
        self.ior = set_f4(self._original_ior)
        self.alpha_mode = set_f4(self._original_alpha_mode)

    # See 9.4 Rendering
    def scramble(self):
        """
        Randomize material properties.
        Only used for AI training.
        """

        self._reset()

        self.base_color[:3] = np.random.uniform(0, 1, 3).astype(f4)
        if np.random.rand() < 0.1:
            self.base_color[-1] = set_f4(np.random.uniform(0.1, 0.9))
            self.alpha_mode = 2 # BLEND
        
        self.roughness = set_f4(np.random.uniform(0, 1))
        self.metallic = set_f4(np.random.uniform(0, 1))

        if self._original_has_emission:
            self.emissive_color = np.random.uniform(0, 1, 3).astype(f4)
            self.emissive_strength *= set_f4(np.random.uniform(0.1, 10))

        if np.random.rand() < 0.3:
            self.transmission = set_f4(np.random.uniform(0, 1))
            self.ior = set_f4(np.random.uniform(1, 2.4))
