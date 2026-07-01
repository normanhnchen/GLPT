from imgui_bundle import imgui
from glfw.GLFW import *
from src.settings import *
from src.settings import _pt_settings_default


class RenderingUI:
    def __init__(self, **kwargs):
        self.pt_state = kwargs.get("pt_state")
        self.camera_buffer = kwargs.get("camera_buffer")

        super().__init__()
    
    def stop_button(self):
            if imgui.button("Stop"):
                self.pt_state.view_saved = False
                self.pt_state.should_render = False
    
    def continue_button(self):
        if imgui.button("Continue"):
            self.pt_state.view_saved = False
            self.pt_state.should_render = True
        
    def restart_button(self):
        if imgui.button("Restart"):
            self.pt_state.total_samples = 0
            self.pt_state.render_complete = False
            self.pt_state.view_saved = False
            self.pt_state.should_render = True
    
    def cancel_button(self):
        if imgui.button("Cancel"):
            render_settings.render_mode = "rasterization"
            self.pt_state.view_saved = False
    
    def viewport_button(self):
        if imgui.button("Back to Viewport"):
            render_settings.render_mode = "rasterization"
            self.pt_state.view_saved = False
    
    def start_button(self):
        if imgui.button("Start Render"):
            self.pt_state.start_render(self.camera_buffer)
            self.pt_state.view_saved = False
            self.pt_state.should_render = True
    
    def start_new_button(self):
        if imgui.button("Start New Render"):
            self.pt_state.start_render(self.camera_buffer)
            self.pt_state.view_saved = False
            self.pt_state.should_render = True
    
    def view_saved_button(self):
        if imgui.button("View Saved Render"):
            render_settings.render_mode = "path_tracing"
            self.pt_state.view_saved = True


class PathTracingUI:
    def __init__(self, **kwargs):
        self.pt_state = kwargs.get("pt_state")
        self.window = glfwGetCurrentContext()

        super().__init__(**kwargs)
    
    def max_bounce_slider(self):
        # Slider 
        # ------
        slider_speed = 0.5
        hardcoded_min_bounces = 1
        hardcoded_max_bounces = 1024
        bounces = pt_settings.max_bounces
        changed, bounces = imgui.drag_int(
            "Max Bounces",
            bounces,
            slider_speed,
            hardcoded_min_bounces,
            hardcoded_max_bounces
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            pt_settings.max_bounces = bounces
            self.pt_state.total_samples = 0
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
        
        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##bounces_minus"):
            if pt_settings.max_bounces > hardcoded_min_bounces:
                pt_settings.max_bounces -= 1
                self.pt_state.total_samples = 0
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##bounces_plus"):
            if pt_settings.max_bounces < hardcoded_max_bounces:
                pt_settings.max_bounces += 1
                self.pt_state.total_samples = 0
        
    def max_samples_slider(self):
        # Slider 
        # ------
        slider_speed = 0.5
        hardcoded_min_samples = 1
        hardcoded_max_samples = 16384
        samples = pt_settings.max_samples
        changed, samples = imgui.drag_int(
            "Max Samples",
            samples,
            slider_speed,
            hardcoded_min_samples,
            hardcoded_max_samples
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            pt_settings.max_samples = samples
            self.pt_state.total_samples = 0
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)

        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##samples_minus"):
            if pt_settings.max_samples > hardcoded_min_samples:
                pt_settings.max_samples -= 1
                self.pt_state.total_samples = 0
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##samples_plus"):
            if pt_settings.max_samples < hardcoded_max_samples:
                pt_settings.max_samples += 1
                self.pt_state.total_samples = 0
        
    def reset_pt_button(self):
        if imgui.button("Reset Path Tracing Settings"):
            pt_settings.max_bounces = _pt_settings_default.max_bounces
            pt_settings.max_samples = _pt_settings_default.max_samples
            self.pt_state.total_samples = 0
            self.pt_state.render_complete = False
            self.pt_state.view_saved = False
            self.pt_state.should_render = True


class CameraUI:
    def __init__(self, **kwargs):
        self.pt_state = kwargs.get("pt_state")
        self.camera = kwargs.get("camera")

        super().__init__(**kwargs)

    def movement_speed_slider(self):
        # Slider 
        # ------
        slider_speed = 0.5
        hardcoded_min_speed = 0
        hardcoded_max_speed = 10000
        speed = self.camera.movement_speed
        changed, speed = imgui.drag_float(
            "Movement Speed",
            speed,
            slider_speed,
            hardcoded_min_speed,
            hardcoded_max_speed
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            self.camera.movement_speed = speed
            self.pt_state.total_samples = 0
        
        else:
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)

        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##speed_minus"):
            if self.camera.movement_speed > hardcoded_min_speed:
                self.camera.movement_speed -= 1
                self.pt_state.total_samples = 0
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##speed_plus"):
            if self.camera.movement_speed < hardcoded_max_speed:
                self.camera.movement_speed += 1
                self.pt_state.total_samples = 0


class SettingsUI(CameraUI, PathTracingUI, RenderingUI):
    def __init__(self,
            pt_state,
            camera_buffer,
            camera
        ):
        super().__init__(
            pt_state=pt_state,
            camera_buffer=camera_buffer,
            camera=camera
        )

    def rendering_ui(self):
        if render_settings.render_mode == "path_tracing":
            if not self.pt_state.view_saved:
                if self.pt_state.should_render:
                    self.stop_button()
                
                else:
                    self.continue_button()
                
                self.cancel_button()
            
            else:
                self.viewport_button()
            
            self.restart_button()
        
        else:
            if self.pt_state.saved_render is None:
                self.start_button()
            
            else:
                self.start_new_button()
                self.view_saved_button()

    def path_tracing_ui(self):
        self.max_bounce_slider()
        self.max_samples_slider()
        self.reset_pt_button()
    
    def camera_ui(self):
        self.movement_speed_slider()
