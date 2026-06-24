# Fundamental Theory

## The Microfacet Model

The microfacet theory describes that any surface at the microscopic scale can be described by tiny aligned mirrors called microfacets. The alignment of these microfacets depends on the roughness of the surface. On a rougher surface, the alignment will be chaotic, scattering light in more different directions. On a smoother surface, the microfacets will be aligned more, allowing light to bounce more in the same direction.

## Energy Conservation

Energy conservation: outgoing light energy cannot exceed the incoming light energy. When light hits a surface, the rays become split between a refraction part and a reflection part. The reflected light doesn't enter the surface; this is known as specular lighting. The refracted light enters the surface and gets absorbed; this is known as diffuse lighting.

**Note**: metallic surfaces behave differently than non-metallic surfaces (dialectrics). All refracted light is absorbed immediately without scattering. The specular reflection of a metallic object takes on the material's color rather than being white/colorless in a dielectric.

In code, we calculate the specular fraction and the diffuse fraction is calculated from that. The fractions must add up to 1 for energy conservation.

```
// GLSL Pseudocode

// Specular
float kS = specularComponent;
// Diffuse
float kD = 1.0 - kS;
```

# References

- https://learnopengl.com/PBR/Theory
