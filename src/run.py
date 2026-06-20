import numpy as np
from glfw.GLFW import *
import moderngl
import sys
import time

from src.dtypes import *
from src.settings import *
from src.shader import *
from src.camera import *
from src.model import *


camera = Camera()


first_mouse = True
last_x = screen.width / 2
last_y = screen.height / 2


def main():
    if not glfwInit():
        return "Failed to initialize GLFW"

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4)
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 4)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)
    # Apple system required config
    if sys.platform == "darwin":
        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE)
    
    window = glfwCreateWindow(screen.width, screen.height, "FPS: 0 | Samples: 0", None, None)

    if not window:
        return "Failed to create GLFW window"
    
    glfwMakeContextCurrent(window)
    glfwSetCursorPosCallback(window, mouse_callback)
    glfwSetScrollCallback(window, scroll_callback)
    glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
    if screen.vsync == True:
        glfwSwapInterval(1)
    else:
        glfwSwapInterval(0)

    ctx = moderngl.create_context()

    scene = Scene("src/assets/cornell_box.glb")

    shader = Shader(
        ctx,
        "src/shaders/render.vs",
        "src/shaders/render.fs"
    )
    compute_shader = ComputeShader(
        ctx,
        "src/shaders/render.comp"
    )

    compute_texture = ctx.texture(screen.resolution, 4, dtype=f4)

    # Full-screen quad
    quad_buffer = ctx.buffer(np.array([
        # Vertices    # TexCoords
        -1.0,  1.0,   0.0, 1.0,
        -1.0, -1.0,   0.0, 0.0,
         1.0,  1.0,   1.0, 1.0,
         1.0, -1.0,   1.0, 0.0,
    ], dtype=f4))

    vao = ctx.vertex_array(
        shader.prog,
        [
            [quad_buffer, "2f 2f", "aPos", "aTexCoords"]
        ]
    )

    # NOTE: std140 or std430 blocks are padded to multiples of 16 bytes

    camera_dtype = np.dtype([
        ("pos", *vec3),
        ("pad1", f4),
        ("front", *vec3),
        ("pad2", f4),
        ("up", *vec3),
        ("pad3", f4),
        ("right", *vec3),
        ("fov", f4)
    ])

    camera_data = np.zeros(1, dtype=camera_dtype)

    camera_buffer = ctx.buffer(camera_data.tobytes())
    camera_buffer.bind_to_storage_buffer(0)

    vertex_dtype = np.dtype([
        ("pos", *vec3),
        ("pad1", f4),
    ])

    material_dtype = np.dtype([
        ("baseCol", *vec3),
        ("roughness", f4),
        ("emissive", *vec3),
        ("hasEmission", i4)
    ])

    triangle_dtype = np.dtype([
        ("v0", vertex_dtype),
        ("v1", vertex_dtype),
        ("v2", vertex_dtype),
        ("mat", material_dtype),
    ])

    material_data = np.zeros(scene.num_materials, dtype=material_dtype)

    base_colors = np.vstack([mat.base_color for mat in scene.materials], dtype=f4)
    roughnesses = np.array([mat.roughness for mat in scene.materials], dtype=f4)
    emissive_colors = np.vstack([mat.emissive_color for mat in scene.materials], dtype=f4)
    has_emissions = np.array([mat.has_emission for mat in scene.materials], dtype=i4)

    material_data["baseCol"] = base_colors
    material_data["roughness"] = roughnesses
    material_data["emissive"] = emissive_colors
    material_data["hasEmission"] = has_emissions

    triangle_data = np.zeros(scene.num_triangles, dtype=triangle_dtype)
    
    idx0 = scene.triangles[:, 0]
    idx1 = scene.triangles[:, 1]
    idx2 = scene.triangles[:, 2]

    triangle_data["v0"]["pos"] = scene.vertices[idx0]
    triangle_data["v1"]["pos"] = scene.vertices[idx1]
    triangle_data["v2"]["pos"] = scene.vertices[idx2]
    triangle_data["mat"] = material_data[scene.material_ids]
    
    triangle_buffer = ctx.buffer(triangle_data.tobytes())
    triangle_buffer.bind_to_storage_buffer(1)
    
    last_frame_start = 0
    stats_start_time = time.perf_counter()

    avg_fps = 0

    total_frame_count = 0
    stats_frame_count = 0

    # Render loop
    while not glfwWindowShouldClose(window):
        frame_start = time.perf_counter()
        delta_time = frame_start - last_frame_start
        last_frame_start = frame_start

        stats_elapsed_time = time.perf_counter() - stats_start_time
        
        # Log stats every 1.5 seconds
        if stats_elapsed_time >= 1.5:
            # Calculate average FPS over the 1.5 second window
            avg_fps = stats_frame_count / stats_elapsed_time

            # Reset stats counters
            stats_start_time = time.perf_counter()
            stats_frame_count = 0
        
        update_stats(window, avg_fps, total_frame_count)

        process_input(window, delta_time)

        ctx.clear(0, 0, 0, 1)

        if camera.has_moved():
            total_frame_count = 0

        # Update camera data
        camera_data["pos"] = camera.pos
        camera_data["front"] = camera.front
        camera_data["up"] = camera.up
        camera_data["right"] = camera.right
        camera_data["fov"] = camera.fov

        camera_buffer.write(camera_data.tobytes())

        compute_shader.prog["totalSamples"].value = total_frame_count
        compute_shader.prog["numTriangles"].value = scene.num_triangles
        compute_shader.prog["maxDepth"].value = path_tracing.max_depth

        # Apply ceiling function
        # Allows the GPU to reach the entire screen despite different screen resolutions
        groups_x = (screen.width + 15) // 16
        groups_y = (screen.height + 15) // 16

        # Run compute shader
        compute_texture.bind_to_image(0, read=True, write=True)
        compute_shader.prog.run(groups_x, groups_y)

        # Draw to screen
        compute_texture.use(location=0)

        vao.render(moderngl.TRIANGLE_STRIP)

        glfwSwapBuffers(window)
        glfwPollEvents()

        total_frame_count += 1
        stats_frame_count += 1

        cap_fps(frame_start, screen.fps_cap)
    
    glfwTerminate()


def cap_fps(frame_start, target_fps):
    target_duration = 1 / target_fps
    # Target time when the target_fps is reached
    target_time = frame_start + target_duration

    # Sleep/wait until the target_time is reached
    while True:
        remaining_time = target_time - time.perf_counter()

        if remaining_time <= 0:
            break
        
        # Sleep for the majority of the time to save CPU resources
        if remaining_time > 0.001:
            # Sleep for half of the remaining time
            # This methods allow sleeping precision as remaining time approaches zero
            sleep_time = remaining_time * 0.5
            time.sleep(sleep_time)
        
        # Wait until the target time is reached
        else:
            pass


def update_stats(window, fps, samples):
    glfwSetWindowTitle(
        window,
        f"FPS: {fps:.2f} | Samples: {samples}"
    )


def process_input(window, delta_time):
    if glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS:
        glfwSetWindowShouldClose(window, True)
    
    if glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS:
        camera.process_keyboard(CameraMovement.FORWARD, delta_time)
    if glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS:
        camera.process_keyboard(CameraMovement.BACKWARD, delta_time)
    if glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS:
        camera.process_keyboard(CameraMovement.LEFT, delta_time)
    if glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS:
        camera.process_keyboard(CameraMovement.RIGHT, delta_time)
    if glfwGetKey(window, GLFW_KEY_SPACE) == GLFW_PRESS:
        camera.process_keyboard(CameraMovement.UP, delta_time)
    if glfwGetKey(window, GLFW_KEY_LEFT_SHIFT) == GLFW_PRESS:
        camera.process_keyboard(CameraMovement.DOWN, delta_time)


def mouse_callback(window, xpos, ypos):
    global first_mouse, last_x, last_y

    if first_mouse:
        last_x = xpos
        last_y = ypos
        first_mouse = False
    
    xoffset = xpos - last_x
    # Reversed since y-coordinates go from bottom to top
    yoffset = last_y - ypos
    last_x = xpos
    last_y = ypos

    camera.process_mouse_movement(xoffset, yoffset)


def scroll_callback(window, xoffset, yoffset):
    camera.process_mouse_scroll(yoffset)

if __name__ == "__main__":
    main()