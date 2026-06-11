import numpy as np
from glfw.GLFW import *
import moderngl
import sys

from src.settings import *


def main():
    if not glfwInit():
        return "Failed to initialize GLFW"

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3)
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)
    # Apple system required config
    if sys.platform == "darwin":
        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE)
    
    window = glfwCreateWindow(screen.width, screen.height, "Engine", None, None)

    if not window:
        return "Failed to create GLFW window"
    
    glfwMakeContextCurrent(window)

    ctx = moderngl.create_context()

    while not glfwWindowShouldClose(window):
        process_input(window)

        ctx.clear(0, 0, 0, 1)

        glfwSwapBuffers(window)
        glfwPollEvents()
    
    glfwTerminate()


def process_input(window):
    if glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS:
        glfwSetWindowShouldClose(window, True)


if __name__ == "__main__":
    main()