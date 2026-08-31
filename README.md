# GLPT

GLPT is a GPU path tracer built with a ModernGL and GLFW backend. 

## Path Tracer Features

- **Primitive Intersection:** Möller-Trumbore ray-triangle intersection
- **Bounding Volume Hierarchy (BVH):** Background CPU construction with SAH binning
- **BSDF & Microfacet Models:** Microfacet transmission, height-correlated Smith, and Fresnel-Schlick approximation
- **Advanced Sampling:** GGX VNDF importance sampling and cosine-weighted hemisphere sampling
- **Next Event Estimation (NEE):** Direct sampling for punctual lights, area lights, and HDRI
- **Multiple Importance Sampling (MIS):** Power heuristic for combining BSDF and NEE contributions
- **Volumetrics:** Beer-Lambert law integration for homogenous mediums
- **AI Denoising:** Kernel-Predicting Convolutional Network (KPCN) with a U-Net architecture

## Requirements

### Hardware & OS
- A GPU with **OpenGL 4.6** support (compute shaders, SSBOs) is required, effectively meaning a Windows or Linux OS (**macOS is not supported**)
- A dedicated GPU is strongly recommended because path-tracing is significantly demanding on the GPU side
- A capable CPU speeds up BVH construction especially for more complex scenes

### Scene Format
Scenes must be `glTF` or `.glb`. GLPT reads the following extra lighting and material data through glTF extensions:

- `KHR_materials_emissive_strength`
- `KHR_materials_transmission`
- `KHR_materials_ior`
- `KHR_lights_punctual`

## Gallery

## Benchmarks

## Developer Installation

Requires **Python 3.10+**.

```bash
git clone https://github.com/normanhnchen/GLPT
cd glpt
pip install -r requirements.txt
```

If you have an NVIDIA GPU, install a CUDA-accelerated `torch` build from
[pytorch.org](https://pytorch.org/get-started/locally/) instead for faster AI denoising / training.

Run the main launcher with:

```bash
python -m src.run
```

## Documentation

GLPT includes comprehensive documentation covering the underlying mathematics, derivations, and concepts used in the engine. 

**[Read the Documentation](docs/1_Introduction/1.0_Table_of_Contents.md)**

## License

Unless otherwise noted, all original source code in this repository is Copyright © 2026 Norman Chen.

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Third-party code and assets remain under their respective licenses and copyrights.

## Assets

All 3d scenes were created by me using Blender 4.4.

### External Assets

- Textures and HDRI environments are from [ambientCG.com](ambientCG.com),
licensed under the Creative Commons CC0 1.0 Universal License.

- Models from the Stanford 3D Scanning Repository: 
    - Stanford Dragon

Stanford Dragon
Source: Stanford Computer Graphics Laboratory
https://graphics.stanford.edu/data/3Dscanrep/

Please see the Stanford 3D Scanning Repository for licensing and usage terms.

## Third-Party Code

### LearnOpenGL
Portions of this project are adapted from the LearnOpenGL tutorials by Joey de Vries. The original tutorial code has been substantially modified. This project also incorporates techniques discussed in the *Advanced Lighting* chapter on Normal Mapping.
- **Source:** [LearnOpenGL](https://learnopengl.com)
- **License:** Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)

### Tone Mapping Functions
Tone mapping functions are adapted from the `glsl-tone-map` repository by Damien Seguin.
- **Source:** [glsl-tone-map](https://github.com/dmnsgn/glsl-tone-map)

- **License: MIT License**

    MIT License

    Copyright (C) 2019 Damien Seguin

    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## References

The following resources were consulted during the implementation of this project. Unless otherwise stated, their code, text, figures, and other copyrighted material are **not** included in this repository.

### Introduction & Path Tracing
- **The Rendering Equation:** P. Pharr, W. Jakob, and G. Humphreys, *Physically Based Rendering: From Theory to Implementation*, 3rd ed. [Read here](https://pbr-book.org/3ed-2018/Introduction/Photorealistic_Rendering_and_the_Ray-Tracing_Algorithm).
- **Ray Tracing in One Weekend:** Algorithms and rendering techniques inspired by Peter Shirley, Trevor David Black, and Steve Hollasch. [Read here](https://raytracing.github.io/books/RayTracingInOneWeekend.html).
- **Russian Roulette:** System reference via *Physically Based Rendering*. [Read here](https://pbr-book.org/3ed-2018/Monte_Carlo_Integration/Russian_Roulette_and_Splitting).

### Basic Utilities
- **Robust Ray Origin Offset:** C. Wächter and N. Binder, "A fast and robust method for avoiding self-intersection," *Ray Tracing Gems*, 2019. [DOI: 10.1007/978-1-4842-4427-2](https://doi.org/10.1007/978-1-4842-4427-2).
- **Uniform Disk Sampling:** M. Pharr, W. Jakob, and G. Humphreys, *Physically Based Rendering*, 4th ed., 2023. [Read here](https://www.pbr-book.org/4ed/Sampling_Algorithms/Sampling_Multidimensional_Functions#SamplingaUnitDisk).
- **Orthonormal Basis:** T. Duff et al., "Building an Orthonormal Basis, Revisited," *JCGT*, 2017. [Read here](http://jcgt.org/published/0006/01/01/).

### Primitive Intersection
- **AABB Testing (Slab Method):** M. Pharr, W. Jakob, and G. Humphreys, "Ray–Bounds Intersections," in *Physically Based Rendering: From Theory to Implementation*, 3rd ed. [Read here](https://pbr-book.org/3ed-2018/Shapes/Basic_Shape_Interface#RayndashBoundsIntersections).
- **Ray-Triangle Intersection (Möller-Trumbore):** T. Möller and B. Trumbore, "Fast, minimum storage ray/triangle intersection," in *ACM SIGGRAPH 2005 Courses*, Los Angeles, CA, USA: Association for Computing Machinery, 2005, Art. no. 7. doi: 10.1145/1198555.1198746.
  - Wikipedia contributors, "Cramer's rule," *Wikipedia, The Free Encyclopedia*. [Read here](https://en.wikipedia.org/wiki/Cramer%27s_rule).
  - Wikipedia contributors, "Triple product," *Wikipedia, The Free Encyclopedia*. [Read here](https://en.wikipedia.org/wiki/Triple_product).

### Bounding Volume Hierarchy (BVH)
- **Construction & Traversal:** J. Bikker, "How to Build a BVH" tutorial series (Basics, Faster Rays, Quick Builds), *jacco.ompf2.com*, 2022. [Part 1](https://jacco.ompf2.com/2022/04/13/how-to-build-a-bvh-part-1-basics/) | [Part 2](https://jacco.ompf2.com/2022/04/18/how-to-build-a-bvh-part-2-faster-rays/) | [Part 3](https://jacco.ompf2.com/2022/04/21/how-to-build-a-bvh-part-3-quick-builds/).
- **Debug Visualization:** I. Quilez, "Smooth HSV," *Shadertoy*. [Read here](https://www.shadertoy.com/view/MsS3Wc).

### BSDF & Microfacet Models
- **Cosine-Weighted Hemisphere Sampling:** *Physically Based Rendering*, 3rd ed. [Read here](https://www.pbr-book.org/3ed-2018/Monte_Carlo_Integration/2D_Sampling_with_Multidimensional_Transformations#Cosine-WeightedHemisphereSampling).
- **Trowbridge-Reitz GGX:** T. S. Trowbridge and K. P. Reitz, *J. Opt. Soc. Am.*, 1975. [DOI: 10.1364/JOSA.65.000531](https://doi.org/10.1364/JOSA.65.000531).
- **Schlick-GGX Approximation:** B. Karis, "Real Shading in Unreal Engine 4," *SIGGRAPH 2013 Courses*. [Read here](https://blog.selfshadow.com/publications/s2013-shading-course/karis/s2013_pbs_epic_notes_v2.pdf).
- **Height-Correlated Smith:** 
  - E. Heitz, "Understanding the Masking-Shadowing Function in Microfacet-Based BRDFs," *JCGT*, 2014. [Read here](https://jcgt.org/published/0003/02/03/).
  - J. Schutte, "Importance Sampling techniques for GGX with Smith Masking-Shadowing: Part 2," 2018. [Read here](https://schuttejoe.github.io/post/ggximportancesamplingpart2/).
- **Fresnel-Schlick Approximation:** *Physically Based Rendering*, 3rd ed. [Read here](https://pbr-book.org/3ed-2018/Reflection_Models/Fresnel_Incidence_Effects).
- **GGX VNDF Importance Sampling:** 
  - E. Heitz, "Sampling the GGX Distribution of Visible Normals," *JCGT*, 2018. [Read here](http://jcgt.org/published/0007/04/01/).
  - E. Heitz and E. d'Eon, "Importance Sampling Microfacet-Based BSDFs using the Distribution of Visible Normals," *Computer Graphics Forum*, 2014.
  - *Physically Based Rendering*, 3rd ed. [Read here](https://pbr-book.org/3ed-2018/Light_Transport_I_Surface_Reflection/Sampling_Reflection_Functions#MicrofacetBxDFs).
- **Microfacet Transmission:** B. Walter et al., "Microfacet models for refraction through rough surfaces," *EGSR'07*, 2007. [Read here](https://dl.acm.org/doi/10.5555/2383847.2383874).

### Volumetrics
- **Beer-Lambert Law:** M. Pharr, W. Jakob, and G. Humphreys, "Volume Scattering Processes," *Physically Based Rendering: From Theory to Implementation*, 3rd ed. [Read here](https://www.pbr-book.org/3ed-2018/Volume_Scattering/Volume_Scattering_Processes).

### Light Sampling
- **HDRI & Area Light Sampling:** *Physically Based Rendering*, 3rd & 4th eds. [HDRI Sampling](https://pbr-book.org/3ed-2018/Light_Transport_I_Surface_Reflection/Sampling_Light_Sources#InfiniteAreaLights) | [Area Lights](https://pbr-book.org/4ed/Light_Sources/Light_Sampling#PowerLightSampler) | [Triangle Meshes](https://pbr-book.org/4ed/Shapes/Triangle_Meshes#Sampling).
- **Power Sampling & The Alias Method:** *Physically Based Rendering*, 4th ed. [Read here](https://pbr-book.org/4ed/Sampling_Algorithms/The_Alias_Method#AliasTable::Sample).
- **Punctual Lights:** *Physically Based Rendering*, 4th ed. [Read here](https://www.pbr-book.org/4ed/Light_Sources/Point_Lights#) and The Khronos Group, "KHR_lights_punctual," 2017. [Read here](https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_lights_punctual/README.md).
- **Multiple Importance Sampling (MIS):** *Physically Based Rendering*, 3rd ed. [Read here](https://pbr-book.org/3ed-2018/Monte_Carlo_Integration/Importance_Sampling#MultipleImportanceSampling).

### AI Denoiser
- **The U-Net:** GeeksforGeeks, "U-Net Architecture Explained." [Read here](https://www.geeksforgeeks.org/machine-learning/u-net-architecture-explained/).
- **KPCN:** S. Bako et al., "Kernel-predicting convolutional networks for denoising Monte Carlo renderings," *ACM Transactions on Graphics*, 2017. [DOI: 10.1145/3072959.3073708](https://doi.org/10.1145/3072959.3073708).
