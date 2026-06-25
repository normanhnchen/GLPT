# GLPT

Python path tracer built on ModernGL and GLFW with GPU acceleration.

## License

Unless otherwise noted, all original source code in this repository is Copyright © 2026 Norman Chen.

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Third-party code and assets remain under their respective licenses and copyrights.

---

## Third-Party Code

### LearnOpenGL

Portions of this project are adapted from the LearnOpenGL tutorials by Joey de Vries. The original tutorial code has been substantially modified.

**Source:**
https://learnopengl.com

**License:**
Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)

**Additional Reference:**
This project also incorporates techniques discussed in the LearnOpenGL *Advanced Lighting* chapter on Normal Mapping.

---

### Tone Mapping Functions

Tone mapping functions are adapted from the `glsl-tone-map` repository by Damien Seguin.

**Source:**
https://github.com/dmnsgn/glsl-tone-map

**License:**
MIT License

Copyright (C) 2019 Damien Seguin

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## References

The following resources were consulted during the implementation of this project. Unless otherwise stated, their code, text, figures, and other copyrighted material are **not** included in this repository.

### Ray Tracing in One Weekend

Algorithms and rendering techniques are inspired by:

Peter Shirley, Trevor David Black, and Steve Hollasch

*Ray Tracing in One Weekend*

https://raytracing.github.io/books/RayTracingInOneWeekend.html

---

### Möller–Trumbore Ray-Triangle Intersection

Reference for the ray-triangle intersection algorithm.

**Scratchapixel:**
https://www.scratchapixel.com/lessons/3d-basic-rendering/ray-tracing-rendering-a-triangle/moller-trumbore-ray-triangle-intersection.html

---

### Russian Roulette

Reference for the Russian roulette system.

**Physically Based Rendering (PBRT):**
https://pbr-book.org/3ed-2018/Monte_Carlo_Integration/Russian_Roulette_and_Splitting

---

### Hash Functions for GPU Rendering

Reference for GPU-friendly random hash functions.

Jarzynski, M., & Olano, M. (2020).
*Hash Functions for GPU Rendering.*

*Journal of Computer Graphics Techniques.*

http://www.jcgt.org/published/0009/03/02/

---

### Cosine-Weighted Hemisphere Sampling

Reference for cosine-weighted hemisphere sampling for diffuse reflection.

https://pema.dev/obsidian/math/light-transport/cosine-weighted-sampling.html

---

### GGX Importance Sampling

Reference for GGX importance sampling and visible normal sampling.

Part 1:
https://schuttejoe.github.io/post/ggximportancesamplingpart1/

Part 2:
https://schuttejoe.github.io/post/ggximportancesamplingpart2/
