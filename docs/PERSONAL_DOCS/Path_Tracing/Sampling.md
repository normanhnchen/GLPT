# Sampling

## Uniform Sampling

Technique of sampling a uniform random direction over a sphere.

## Importance Sampling

Importance sampling is a Monte Carlo method used to evaluate properties of a particular distribution by sampling from another distribution. In this way, we estimate rarer events by sampling more important values (and applying a weight to correct for the bias). In path tracing, this is particularly useful for reducing noise and improving render times.

## Cosine-Weighted Sampling

Cosine-weighted sampling is an importance sampling technique of sampling a direction over a hemisphere which are more oriented towards the surface normal. This is more accurate and more efficient as light with an angle shallower (angle of incidence) to the normal reflect less energy. This phenomenon is also known as Lambert's Cosine Law.

The function in the code first takes in two uniform random floats (convention: in the range $[0, 1]$) which acts as the base for generating the random direction. Theta and phi are then created, representing the angular coordinates for creating a direction on a 3d hemisphere. Theta represents the elevation angle (tilt) spanning from $0$ to $\frac{\pi}{2}$. Phi represents the azimuthal angle (rotation) spanning from $0$ to $2\pi$.

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

# References

- https://pema.dev/obsidian/math/light-transport/cosine-weighted-sampling.html
- https://en.wikipedia.org/wiki/Importance_sampling

- Artificial Intelligence (Gemini)
    - Further explanation of the Cosine weighted sampling code and Lambert's Cosine Law
