from glfw.GLFW import *
import sys
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

from src.settings import *
from src.camera import CameraMovement


class GlfwWindow:
    def __init__(self):
        self.window = None
        self.need_resize = False

    def create(self, title):
        if not glfwInit():
            return "Failed to initialize GLFW"
    
        glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4)
        glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 6)
        glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)
        # Apple system required config
        if sys.platform == "darwin":
            glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE)
        
        window = glfwCreateWindow(settings.screen.width, settings.screen.height, title, None, None)
    
        if not window:
            return "Failed to create GLFW window"

        self.window = window
        
        glfwMakeContextCurrent(window)
        if settings.screen.vsync == True:
            glfwSwapInterval(1)
        else:
            glfwSwapInterval(0)

    def set_title(self, title):
        glfwSetWindowTitle(self.window, title)

    def resize(self, width, height):
        width = max(1, int(width))
        height = max(1, int(height))

        settings.screen.width = width
        settings.screen.height = height
        settings.screen.resolution = [width, height]
        settings.screen.aspect_ratio = settings.screen.width / max(settings.screen.height, 1)

        self.need_resize = True

    def should_close(self):
        return glfwWindowShouldClose(self.window)

    def shutdown(self):
        glfwTerminate()

    def swap(self):
        glfwSwapBuffers(self.window)

    def disable_cursor(self):
        glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)

    def enable_cursor(self):
        glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)

    def poll(self):
        glfwPollEvents()


class InputState:
    def __init__(self, glfw_window, imgui_state):
        self.glfw_window = glfw_window
        self.imgui_state = imgui_state

        self.first_mouse = True
        self.last_x = settings.screen.width / 2
        self.last_y = settings.screen.height / 2
        self.middle_mouse_down = False

    def begin_drag(self):
        self.middle_mouse_down = True
        self.first_mouse = True

    def end_drag(self):
        self.middle_mouse_down = False

    def drag_delta(self, xpos, ypos):
        if self.first_mouse:
            self.last_x, self.last_y = xpos, ypos
            self.first_mouse = False
        
        xoffset = xpos - self.last_x
        # Reversed since y-coordinates go from bottom to top
        yoffset = self.last_y - ypos
        self.last_x, self.last_y = xpos, ypos

        return xoffset, yoffset

    def _pressed(self, key):
        return glfwGetKey(self.glfw_window.window, key) == GLFW_PRESS

    def process_input(self, delta_time, camera):
        if self.imgui_state.want_text_input():
            return
        
        if settings.rendering.mode == "path_tracing":
            return
        
        if self._pressed(GLFW_KEY_W):
            camera.process_keyboard(CameraMovement.FORWARD, delta_time)
        if self._pressed(GLFW_KEY_S):
            camera.process_keyboard(CameraMovement.BACKWARD, delta_time)
        if self._pressed(GLFW_KEY_A):
            camera.process_keyboard(CameraMovement.LEFT, delta_time)
        if self._pressed(GLFW_KEY_D):
            camera.process_keyboard(CameraMovement.RIGHT, delta_time)
        if self._pressed(GLFW_KEY_SPACE):
            camera.process_keyboard(CameraMovement.UP, delta_time)
        if self._pressed(GLFW_KEY_LEFT_SHIFT):
            camera.process_keyboard(CameraMovement.DOWN, delta_time)


class UIState:
    def __init__(self):
        self.settings_window = False

    def toggle_settings(self):
        self.settings_window = not self.settings_window


class ImguiState:
    def __init__(self):
        self.impl = None

    def create(self, window):
        imgui.create_context()
        self.impl = GlfwRenderer(window)

    def want_capture_mouse(self):
        return imgui.get_io().want_capture_mouse

    def want_text_input(self):
        return imgui.get_io().want_text_input

    def begin_frame(self):
        self.impl.process_inputs()
        imgui.new_frame()

    def end_frame(self):
        imgui.render()
        self.impl.render(imgui.get_draw_data())

    def shutdown(self):
        self.impl.shutdown()

    def forward_mouse(self, window, xpos, ypos):
        if hasattr(self.impl, "mouse_callback"):
            self.impl.mouse_callback(window, xpos, ypos)

    def forward_key(self, window, key, scancode, action, mods):
        if hasattr(self.impl, "keyboard_callback"):
            self.impl.keyboard_callback(window, key, scancode, action, mods)

    def forward_mouse_button(self, window, button, action, mods):
        if hasattr(self.impl, "mouse_button_callback"):
            self.impl.mouse_button_callback(window, button, action, mods)

    def forward_scroll(self, window, xoffset, yoffset):
        if hasattr(self.impl, "scroll_callback"):
            self.impl.scroll_callback(window, xoffset, yoffset)


class GlfwCallbackState:
    def __init__(self, glfw_window, input_state, ui_state, imgui_state, camera):
        self.glfw_window = glfw_window
        self.input_state = input_state
        self.ui_state = ui_state
        self.imgui_state = imgui_state
        self.camera = camera

    def set_callbacks(self):
        window = self.glfw_window.window
        glfwSetCursorPosCallback(window, self._mouse_callback)
        glfwSetScrollCallback(window, self._scroll_callback)
        glfwSetMouseButtonCallback(window, self._mouse_button_callback)
        glfwSetKeyCallback(window, self._key_callback)
        glfwSetFramebufferSizeCallback(window, self._framebuffer_size_callback)
        glfwSetWindowSizeLimits(window, settings.screen.min_width, settings.screen.min_height, GLFW_DONT_CARE, GLFW_DONT_CARE)

    def _framebuffer_size_callback(self, window, width, height):
        self.glfw_window.resize(width, height)

    def _key_callback(self, window, key, scancode, action, mods):
        self.imgui_state.forward_key(window, key, scancode, action, mods)

        if key == GLFW_KEY_ESCAPE and action == GLFW_PRESS:
            self.ui_state.toggle_settings()

    def _mouse_button_callback(self, window, button, action, mods):
        self.imgui_state.forward_mouse_button(window, button, action, mods)
        
        if self.imgui_state.want_capture_mouse():
            return

        if settings.rendering.mode == "path_tracing":
            return

        if button == GLFW_MOUSE_BUTTON_MIDDLE:
            if action == GLFW_PRESS:
                self.input_state.begin_drag()
                self.glfw_window.disable_cursor()
                
            elif action == GLFW_RELEASE:
                self.input_state.end_drag()
                self.glfw_window.enable_cursor()

    def _mouse_callback(self, window, xpos, ypos):
        self.imgui_state.forward_mouse(window, xpos, ypos)
        
        if self.imgui_state.want_capture_mouse():
            return

        if settings.rendering.mode == "path_tracing":
            return

        if self.input_state.middle_mouse_down:
            xoffset, yoffset = self.input_state.drag_delta(xpos, ypos)

            self.camera.process_mouse_movement(xoffset, yoffset)

    def _scroll_callback(self, window, xoffset, yoffset):
        self.imgui_state.forward_scroll(window, xoffset, yoffset)
        
        if self.imgui_state.want_capture_mouse():
            return
        
        if settings.rendering.mode == "path_tracing":
            return

        self.camera.process_mouse_scroll(yoffset)
