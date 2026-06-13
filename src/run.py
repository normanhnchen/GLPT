import numpy as np
from glfw.GLFW import *
import moderngl
import sys
import time

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
    
    window = glfwCreateWindow(screen.width, screen.height, "FPS: ", None, None)

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

    compute_texture = ctx.texture(screen.resolution, 4, dtype="f4")

    # Full-screen quad
    quad_buffer = ctx.buffer(np.array([
        # Vertices    # TexCoords
        -1.0,  1.0,   0.0, 1.0,
        -1.0, -1.0,   0.0, 0.0,
         1.0,  1.0,   1.0, 1.0,
         1.0, -1.0,   1.0, 0.0,
    ], dtype="f4"))

    vao = ctx.vertex_array(
        shader.prog,
        [
            [quad_buffer, "2f 2f", "aPos", "aTexCoords"]
        ]
    )

    start_time = time.perf_counter()
    last_time = 0
    stats_start_time = time.perf_counter()

    curr_frame_count = 0
    stats_frame_count = 0

    while not glfwWindowShouldClose(window):
        current_time = time.perf_counter() - start_time
        delta_time = current_time - last_time
        last_time = current_time

        stats_elapsed_time = time.perf_counter() - stats_start_time
        
        # Log stats every 1.5 seconds
        if stats_elapsed_time >= 1.5:
            # Calculate average FPS over the 1.5 second window
            avg_fps = stats_frame_count / stats_elapsed_time
            update_stats(window, avg_fps)

            # Reset stats counters
            stats_start_time = time.perf_counter()
            stats_frame_count = 0

        process_input(window, delta_time)

        ctx.clear(0, 0, 0, 1)

        # Apply ceiling function
        # Allows the GPU to reach the entire screen despite different screen resolutions
        groups_x = (screen.width + 15) // 16
        groups_y = (screen.height + 15) // 16

        # Run compute shader
        compute_texture.bind_to_image(0, read=True, write=True)
        compute_shader.prog.run(groups_x, groups_y)

        compute_texture.use(location=0)

        vao.render(moderngl.TRIANGLE_STRIP)

        glfwSwapBuffers(window)
        glfwPollEvents()

        curr_frame_count += 1
        stats_frame_count += 1
    
    glfwTerminate()


def update_stats(window, fps):
    glfwSetWindowTitle(
        window,
        f"FPS: {fps:.2f}"
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