# Physically-Based Rendering

**Physically-based rendering (PBR)** models accurate lighting, reflections, and materials based  
on principles that approximate physics.

## Material Workflow

This path tracer uses a metalness-roughness workflow:

- **base color**: the material's color before lighting
- **roughness**: controls the blurriness or sharpness of a reflection
- **metalness**: determines whether the material behaves like a metal or non-metal
- **emission**: the amount of light the material emits

## Dialectrics / Conductors

**Dielectrics** are electric insulators (e.g. plastics, glass, paper, etc.)

- Reflects white color because of its low reflectivity
- Do not tint reflections with their base color

**Conductors** are metals (e.g. copper, gold, steel, etc.)

- Produces reflections tinted by its base color
- Have little to no diffuse reflection

## Reflections

**Diffuse reflection**: scatter of light on a rough surface  
**Specular reflection**: mirror-like reflection of light on a smooth surface

## Lighting

The path tracer only computes indirect lighting with path bounces, and does not implement  
irradiance caching and light sampling for multiple lights.

A full implementation would require:

- light sampling for direct lighting
- irradiance caching for accurate lighting

## Reflections

Microfacets mean surface imperfections.

## References

- https://en.wikipedia.org/wiki/Lambert%27s_cosine_law
- https://pema.dev/obsidian/math/light-transport/cosine-weighted-sampling.html
- https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html