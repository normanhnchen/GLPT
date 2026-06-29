import numpy as np
from glfw.GLFW import *
import moderngl
import sys
import time
import pickle

from src.settings import *
from src.dtypes import *
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
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 6)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)
    # Apple system required config
    if sys.platform == "darwin":
        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE)
    
    window = glfwCreateWindow(screen.width, screen.height, "FPS: 0", None, None)

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

    # try:
    #     with open("src/assets/cache/dragon_scene.pkl", "rb") as f:
    #         scene = pickle.load(f)
    # except:
    #     scene = Scene(file_paths.scene, hdri_path=file_paths.hdri)
    #     with open("src/assets/cache/dragon_scene.pkl", "wb") as f:
    #         pickle.dump(scene, f)

    scene = Scene(file_paths.scene, hdri_path=file_paths.hdri)

    shader = Shader(
        ctx,
        file_paths.real_time.vert,
        file_paths.real_time.frag
    )

    vertices = scene.vertices[scene.triangles]
    uvs = scene.uvs[scene.triangles]

    vertices = vertices.reshape(-1, 3)
    uvs = uvs.reshape(-1, 2)

    data = np.hstack((vertices, uvs), dtype=f4)

    vbo = ctx.buffer(data.tobytes())

    vao = ctx.vertex_array(
        shader.prog,
        [
            (vbo, "3f 2f", "aPos", "aTexCoords")
        ]
    )

    ctx.enable(moderngl.DEPTH_TEST)
    
    last_frame_start = 0
    stats_start_time = time.perf_counter()

    avg_fps = 0

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
        
        update_stats(window, avg_fps)

        process_input(window, delta_time)

        ctx.clear(0, 0, 0, 1)

        shader.prog["view"].write(camera.get_view().to_bytes())
        shader.prog["projection"].write(camera.get_perspective().to_bytes())
        
        vao.render(moderngl.TRIANGLES)

        glfwSwapBuffers(window)
        glfwPollEvents()

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
