# Coordinate Spaces

## Local Space

Coordinate space that is local to an object, where the object's origin is at (0, 0, 0).

## World Space

3d coordinate space where all geometry is relative to a certain world.

Transformation from local to world space can be achieved the *model* matrix, which transforms geometry to be placed where it belongs in the  world.

## View Space

Also referred to as camera space or eye space, the view space is the space seen from the camera's point of view. This is achieved by applying the *view* matrix, which transforms the entire world so that the camera is positioned at (0, 0, 0) looking down the negative z-axis (OpenGL convention).

## Clip Space

Clip space is a space where coordinates not inside the range [-1, 1] (expected by OpenGL) are clipped and discarded. To transform from view space to clip space, the *projection* matrix is used. It defines a frustum (viewing box created by the projection matrix) which can be a perspective or orthographic projection. The frustum maps coordinates into the clip space range.

## Screen Space

To convert from clip space to screen space, OpenGL performs a *perspective division* if using a perspective projection and then the *viewport transform* to map clip space coordinates to the pixel coordinates of the window.

In screen space,
- the coordinate `(0, 0)` is the **top-left corner** 
- x-coordinates increases **to the right**  
- y-coordinates increases **downward**

## Tangent Space

This space treats a surface normal as the up vector, while the tangent and bitangent vectors are the right and forward directions respectively along the surface.

To convert between tangent space and world space, the TBN (Tangent, Bitangent, Normal) matrix is used.

# References

- https://learnopengl.com/Getting-started/Coordinate-Systems
- Artificial Intelligence (Gemini)
    - Used for explanations on tangent space and converting between tangent sapce and world space
