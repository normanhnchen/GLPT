# Reflectance Equation

**Radiometry**: measurement of electromagnetic radiation

**Radiant flux $\Phi$**: transmitted energy of a light source measured in Watts

**Solid angle $\omega$**: area of a shape projected onto a unit sphere

**Radiant intensity $I$**: amount of radiant flux per solid angle

**Radiance $L$**: radiometric measure of light in an area (total energy in an area $A$ over $\omega$ of a light with intensity $I$)

**Irradiance**: sum of all incoming light onto a point $p$

## The Equation

In summary, the reflectance equation calculates irradiance at a point $p$ over the hemisphere $\Omega$.

$$L_0 (p, \omega_0) = \int_{\Omega} f_r (p, \omega_i, \omega_0) L_i (p, \omega_i) n \cdot \omega_i d \omega_i$$

$L_0 (p, \omega_0)$: outgoing radiance

$\int_{\Omega}$: integrating over the hemisphere (gather light from every direction)

$f_r (p, \omega_i, \omega_0)$: the BRDF (Bidirectional Reflectance Distribution Funcion)

$L_i (p, \omega_i)$: incoming radiance

$n \cdot \omega_i$: cosine falloff (Lambert's Cosine Law)

## Halfway Vector

The halfway vector is a unit vector that is halfway between the view direction and light direction. In microfacet theory, the alignment of microfacets to this vector determines the strength of the specular reflection. THe halfway vector can be calculated using the light vector $l$ and the view vector $v$ using the equation

$$ h = \dfrac{l + v}{\lVert l + v \rVert}$$

# References

- https://learnopengl.com/PBR/Theory
