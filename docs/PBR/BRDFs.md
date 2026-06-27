# Bidirectional Reflectance Distribution Funcion (BRDF)

A BRDF (Bidirectional Reflectance Distribution Funcion) is a mathematical equation that determines how light reflects off of a material's surface given a viewing direction. It adhere's to the principle of energy conservation to be physically accurate.

# Cook-Torrance BRDF

The equation:

$$f_r = k_d f_{lambert} + k_s f_{cookTorrance}$$

$k_d$: ratio of incoming light refracted
$k_s$: ratio of incoming light reflected

$f_{lambert}$: Lambertian diffuse where

$$f_{lambert} = \dfrac{c}{\pi}$$

$c$ represents the surface color. We divide by $\pi$ to normalize the diffuse light as the Cook-Torrance BRDF equation has a PDF of $\pi$.

$f_{cookTorrance}$: specular part where

$$f_{cookTorrance} = \dfrac{DFG}{4(\omega_0 \cdot n)(\omega_i \cdot n)}$$

$D$, $F$ and $G$ each represent functions approximating different part's of specular part.

## $D$: Normal Distribution Function

The normal distribution function $D$ approximates the concentration of microfacets aligned to reflect light to the viewer.

### Trowbridge-Reitz GGX

$$D(n, h, \alpha) = \dfrac{\alpha^2}{\pi((n \cdot h)^2(\alpha^2 - 1) + 1)^2}$$

$n$: surface normal

$h$: halfway vector

$\alpha$: surface roughness

```
// GLSL Pseudocode

float DistributionGGX(vec3 N, vec3 H, float a) {
    float a2     = a*a;
    float NdotH  = max(dot(N, H), 0.0);
    float NdotH2 = NdotH*NdotH;
	
    float nom    = a2;
    float denom  = (NdotH2 * (a2 - 1.0) + 1.0);
    denom        = PI * denom * denom;
	
    return nom / denom;
}
```

## $G$: Geometry Function

The geometry function approximates the concentration of microfacets geometrically occluding eachother because of their alignments.

### Schlick-GGX

$$G(n, v, k) = \dfrac{n \cdot v}{(n \cdot v)(1 - k) + k}$$

$n$: surface normal

$v$: view vector

$k$: remapping of $\alpha$ depending on the use of the function.
- Direct lighting: $k_{direct} = \dfrac{(\alpha + 1)^2}{8}$
- IBL lighting: $k_{IBL} = \dfrac{\alpha^2}{2}$

### Smith GGX

The approximation of geometry requires considering both the view direction (geometry obstruction) and the light direction (geometry shadowing). Smith's method takes this into considering:

$$ G(n, v, l, k) = G_{sub}(n, v, k)G_{sub}(n, l, k)$$

We can use Schlick-GGX as $G_{sub}$.

```
float GeometrySchlickGGX(float NdotV, float k) {
    float nom   = NdotV;
    float denom = NdotV * (1.0 - k) + k;
	
    return nom / denom;
}
  
float GeometrySmith(vec3 N, vec3 V, vec3 L, float k) {
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    float ggx1 = GeometrySchlickGGX(NdotV, k);
    float ggx2 = GeometrySchlickGGX(NdotL, k);
	
    return ggx1 * ggx2;
}
```

## $F$: Fresnel Equations

The Fresnel equations describe the ratio of reflected/refracted light depending on the view angle. The phenomenon of the reflection of a surface changing depending on the view angle is called Fresnel.

### Fresnel-Schlick approximation

$$F(h, v, F_0) = F_0 + (1 - F_0)(1 - (h \cdot v))^5$$

$h$: halfway vector

$v$: view vector

$F_0$: base reflectivity of the surface calculated using its IOR (index of refraction)

```
vec3 F0 = vec3(0.04);
F0 = mix(F0, surfaceColor.rgb, metallic);
```

A base reflectivity $F_0$ value of 0.04 holds for most dielectrics. For metallic surfaces, we tint the $F_0$ value based on its metallic value (metalness) and the surface color.

The Fresnel-Schlick approximation in code is

```
vec3 FresnelSchlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}
```

## Cook-Torrance Reflectance Equation

Combining all equations together, we get the final Cook-Torrance reflectance equation

$$
L_0 (p, \omega_0) =
\int_{\Omega}
(k_d \dfrac{c}{\pi} + \dfrac{DFG}{4(\omega_0 \cdot n)(\omega_i \cdot n)})
L_i (p, \omega_i) n \cdot \omega_i d \omega_i
$$

# References

- https://learnopengl.com/PBR/Theory
