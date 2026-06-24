# Coordinate Spaces

## Screen Space

**Screen space**: 2d coordinate system of the display screen.

`(0, 0)` is the **top-left corner**  
X increases **to the right**  
Y increases **downward**

## World Space

**World space**: 3d coordinate system where the scene exists.

Objects, camera, etc. all lie in world space.

Units are arbitrary and depend on mesh scale.

## Projection Plane

**Projection plane**: an imaginary 2d plane in front of the camera where the 3d world is projected  
onto the 2d screen. It bridges the gap between 2d and 3d space.

- Screen pixels are mapped to points on this plane
- Each pixel transforms into a 3d ray based on its point
- The rays travel into the scene to path trace

# References

- https://learnopengl.com/Getting-started/Coordinate-Systems