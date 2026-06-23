# Notes

## Orthogonalization

### Gram-Schmidt process

Process of re-orthogonalizing the TBN (tangent, bitangent, normal) vectors to be mutually perpendicular.

Source: https://learnopengl.com/Advanced-Lighting/Normal-Mapping
```
// GLSL

vec3 T = normalize(vec3(model * vec4(aTangent, 0.0)));
vec3 N = normalize(vec3(model * vec4(aNormal, 0.0)));
T = normalize(T - dot(T, N) * N);
vec3 B = cross(N, T);

mat3 TBN = mat3(T, B, N)
```

## Building an Orthonormal Basis

Used to transform from tangent to world space using the normal vector as a basis.

The code creates a helper which helps avoid division by zero during the cross product. The helper's code is to make sure it is never parallel to the normal vector by checking which direction the normal is mostly pointing towards.

Source: AI (Classic hack) \
Learned when I needed to convert from tangent to world space.

```
// GLSL Pseudocode

vec3 helper = abs(normal.x) > 0.9 ? vec3(0, 1, 0) : vec3(1, 0, 0);
vec3 tangent = normalize(cross(normal, helper));
vec3 bitangent = cross(normal, tangent);
```

## Probability Density Functions (PDF)

A PDF is a function that describes the likelyhood a random sampled value is going to take on a certain value. This is important in computer graphics, especially in sampling techniques, as using a PDF can mimick the behaviour of light in real life, reduce noise, and increase rendering speed. However, since it creates bias for certain values (which increases density of samples in important areas), we must divide by its PDF value (rate of probability) to guarantee an unbiased result.

Source: https://www.scratchapixel.com/lessons/mathematics-physics-for-computer-graphics/monte-carlo-methods-mathematical-foundations/quick-introduction-to-monte-carlo-methods.html

## Sampling Techniques

### Uniform Sampling

Technique of sampling a uniform random direction over a sphere.

Source: https://pema.dev/obsidian/math/light-transport/cosine-weighted-sampling.html

### Cosine weighted sampling

Technique of sampling a direction over a hemisphere which are more oriented towards the surface normal. This is more accurate and more efficient as light with an angle shallower (angle of incidence) to the normal reflect less energy. This phenomenon is also known as Lambert's Cosine Law.

The function in the code first takes in two uniform random floats (convention: in the range [0, 1]) which acts as the base for generating the random direction. Theta and phi are then created, representing the angular coordinates for creating a direction on a 3d hemisphere. Theta represents the elevation angle (tilt) spanning from 0 to π/2. Phi represents the azimuthal angle (rotation) spanning from 0 to 2π.

Sources:
- https://pema.dev/obsidian/math/light-transport/cosine-weighted-sampling.html
- AI for further explanation of the code and Lambert's Cosine Law

```
// GLSL Pseudocode

vec3 CosineSampleHemisphere(float random1, float random2) {
    float theta = acos(sqrt(random1));
    float phi = 2.0 * PI * random2;
    vec3 sampleDir = vec3(
        sin(theta) * cos(phi),
        cos(theta),
        sin(theta) * sin(phi)
    );
    return sampleDir;
}
```


## PBR

### The Microfacet Model

The microfacet theory describes that any surface at the microscopic scale can be described by tiny aligned mirrors called microfacets. The alignment of these microfacets depends on the roughness of the surface. On a rougher surface, the alignment will be chaotic, scattering light in more different directions. On a smoother surface, the microfacets will be aligned more, allowing light to bounce more in the same direction.

Source: https://learnopengl.com/PBR/Theory

## Energy Conservation

Energy conservation: outgoing light energy cannot exceed the incoming light energy. When light hits a surface, the rays become split between a refraction part and a reflection part. The reflected light doesn't enter the surface; this is known as specular lighting. The refracted light enters the surface and gets absorbed; this is known as diffuse lighting.

Note: metallic surfaces behave differently than non-metallic surfaces (dialectrics). All refracted light is absorbed immediately without scattering. The specular reflection of a metallic object takes on the material's color rather than being white/colorless in a dielectric.

In code, we calculate the specular fraction and the diffuse fraction is calculated from that. The fractions must add up to 1 for energy conservation.

Source: https://learnopengl.com/PBR/Theory

```
// GLSL Pseudocode

// Specular
float kS = specularComponent;
// Diffuse
float kD = 1.0 - kS;
```
