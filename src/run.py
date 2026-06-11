import numpy as np
from glfw.GLFW import *
import moderngl
import sys
import time

from src.settings import *
from src.shader import *


def main():
    if not glfwInit():
        return "Failed to initialize GLFW"

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3)
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)
    # Apple system required config
    if sys.platform == "darwin":
        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE)
    
    window = glfwCreateWindow(screen.width, screen.height, "FPS: ", None, None)

    if not window:
        return "Failed to create GLFW window"
    
    glfwMakeContextCurrent(window)
    if screen.vsync == True:
        glfwSwapInterval(1)
    else:
        glfwSwapInterval(0)

    ctx = moderngl.create_context()

    shader = Shader(
        ctx,
        "src/shaders/render.vs",
        "src/shaders/render.fs"
    )

    start_time = time.perf_counter()
    last_time = 0
    stats_start_time = time.perf_counter()

    curr_frame_count = 0
    stats_frame_count = 0

    target_frame_time = 1 / screen.fps_cap

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

        process_input(window)

        ctx.clear(0, 0, 0, 1)

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

def process_input(window):
    if glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS:
        glfwSetWindowShouldClose(window, True)


if __name__ == "__main__":
    main()