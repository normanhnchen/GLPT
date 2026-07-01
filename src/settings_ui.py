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
            self.pt_state.restart_render()
    
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
    
    def tiles_x_slider(self):
        # Slider 
        # ------
        slider_speed = 0.5
        hardcoded_min_tiles_x = 1
        hardcoded_max_tiles_x = 1024
        tiles_x = render_settings.tiles_x
        changed, tiles_x = imgui.drag_int(
            "##tiles_x",
            tiles_x,
            slider_speed,
            hardcoded_min_tiles_x,
            hardcoded_max_tiles_x
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active() and changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            render_settings.tiles_x = tiles_x
            self.pt_state.restart_render()
            self.pt_state.total_samples = 0
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
        
        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##tiles_x_minus"):
            if render_settings.tiles_x > hardcoded_min_tiles_x:
                render_settings.tiles_x -= 1
                self.pt_state.restart_render()
                self.pt_state.total_samples = 0
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##tiles_x_plus"):
            if render_settings.tiles_x < hardcoded_max_tiles_x:
                render_settings.tiles_x += 1
                self.pt_state.restart_render()
                self.pt_state.total_samples = 0
            
        # Label
        # -----
        imgui.same_line()
        imgui.text("Tiles X")
    
    def tiles_y_slider(self):
        # Slider 
        # ------
        slider_speed = 0.5
        hardcoded_min_tiles_y = 1
        hardcoded_max_tiles_y = 1024
        tiles_y = render_settings.tiles_y
        changed, tiles_y = imgui.drag_int(
            "##tiles_y",
            tiles_y,
            slider_speed,
            hardcoded_min_tiles_y,
            hardcoded_max_tiles_y
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active() and changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            render_settings.tiles_y = tiles_y
            self.pt_state.restart_render()
            self.pt_state.total_samples = 0
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
        
        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##tiles_y_minus"):
            if render_settings.tiles_y > hardcoded_min_tiles_y:
                render_settings.tiles_y -= 1
                self.pt_state.restart_render()
                self.pt_state.total_samples = 0
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##tiles_y_plus"):
            if render_settings.tiles_y < hardcoded_max_tiles_y:
                render_settings.tiles_y += 1
                self.pt_state.restart_render()
                self.pt_state.total_samples = 0
        
        # Label
        # -----
        imgui.same_line()
        imgui.text("Tiles Y")


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
            "##max_bounces",
            bounces,
            slider_speed,
            hardcoded_min_bounces,
            hardcoded_max_bounces
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active() and changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            pt_settings.max_bounces = bounces
            self.pt_state.restart_render()
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
        
        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##bounces_minus"):
            if pt_settings.max_bounces > hardcoded_min_bounces:
                pt_settings.max_bounces -= 1
                self.pt_state.restart_render()
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##bounces_plus"):
            if pt_settings.max_bounces < hardcoded_max_bounces:
                pt_settings.max_bounces += 1
                self.pt_state.restart_render()
        
        # Label
        # -----
        imgui.same_line()
        imgui.text("Max Bounces")
        
    def max_samples_slider(self):
        # Slider 
        # ------
        slider_speed = 0.5
        hardcoded_min_samples = 1
        hardcoded_max_samples = 16384
        samples = pt_settings.max_samples
        changed, samples = imgui.drag_int(
            "##max_samples",
            samples,
            slider_speed,
            hardcoded_min_samples,
            hardcoded_max_samples
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active() and changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            pt_settings.max_samples = samples
            self.pt_state.restart_render()
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)

        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##samples_minus"):
            if pt_settings.max_samples > hardcoded_min_samples:
                pt_settings.max_samples -= 1
                self.pt_state.restart_render()
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##samples_plus"):
            if pt_settings.max_samples < hardcoded_max_samples:
                pt_settings.max_samples += 1
                self.pt_state.restart_render()
        
        # Label
        # -----
        imgui.same_line()
        imgui.text("Max Samples")
    
    def spp_slider(self):
        # Slider 
        # ------
        slider_speed = 0.5
        hardcoded_min_spp = 1
        hardcoded_max_spp = 1024
        spp = pt_settings.spp
        changed, spp = imgui.drag_int(
            "##spp",
            spp,
            slider_speed,
            hardcoded_min_spp,
            hardcoded_max_spp
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active() and changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            pt_settings.spp = spp
            self.pt_state.restart_render()
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
        
        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##spp_minus"):
            if pt_settings.spp > hardcoded_min_spp:
                pt_settings.spp -= 1
                self.pt_state.restart_render()
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##spp_plus"):
            if pt_settings.spp < hardcoded_max_spp:
                pt_settings.spp += 1
                self.pt_state.restart_render()
        
        # Label
        # -----
        imgui.same_line()
        imgui.text("Samples Per Pixel")
    
    def reset_pt_button(self):
        if imgui.button("Reset Path Tracing Settings"):
            pt_settings.max_bounces = _pt_settings_default.max_bounces
            pt_settings.max_samples = _pt_settings_default.max_samples
            pt_settings.spp = _pt_settings_default.spp
            self.pt_state.restart_render()


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
        val_format = "%.1f"
        speed = self.camera.movement_speed
        changed, speed = imgui.drag_float(
            "##movement_speed",
            speed,
            slider_speed,
            hardcoded_min_speed,
            hardcoded_max_speed
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active() and changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            self.camera.movement_speed = speed
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)

        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##speed_minus"):
            if self.camera.movement_speed >= hardcoded_min_speed + 1:
                self.camera.movement_speed -= 1
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##speed_plus"):
            if self.camera.movement_speed <= hardcoded_max_speed - 1:
                self.camera.movement_speed += 1
        
        # Label
        # -----
        imgui.same_line()
        imgui.text("Movement Speed")
    
    def fov_slider(self):
        # Slider 
        # ------
        slider_speed = 1
        hardcoded_min_fov = 1
        hardcoded_max_fov = 135
        val_format = "%.1f"
        fov = self.camera.fov
        changed, fov = imgui.drag_float(
            "##fov",
            fov,
            slider_speed,
            hardcoded_min_fov,
            hardcoded_max_fov,
            val_format
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active() and changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            self.camera.fov = fov
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)

        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##fov_minus"):
            if self.camera.fov >= hardcoded_min_fov + 1:
                self.camera.fov -= 1
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##fov_plus"):
            if self.camera.fov <= hardcoded_max_fov - 1:
                self.camera.fov += 1
        
        # Label
        # -----
        imgui.same_line()
        imgui.text("FOV")
    
    def mouse_sensitivity_slider(self):
        # Slider 
        # ------
        slider_speed = 0.1
        hardcoded_min_sensitivity = 0.1
        hardcoded_max_sensitivity = 10
        val_format = "%.1f"
        # Alter the slider values to look larger but is the same internally
        visual_factor = 10
        mouse_sensitivity = self.camera.mouse_sensitivity * visual_factor
        changed, mouse_sensitivity = imgui.drag_float(
            "##mouse_sensitivity",
            mouse_sensitivity,
            slider_speed,
            hardcoded_min_sensitivity,
            hardcoded_max_sensitivity,
            val_format
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active() and changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            self.camera.mouse_sensitivity = mouse_sensitivity / visual_factor
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)

        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##sens_minus"):
            if self.camera.mouse_sensitivity >= hardcoded_min_sensitivity + 1:
                self.camera.mouse_sensitivity -= 1
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##sens_plus"):
            if self.camera.mouse_sensitivity <= hardcoded_max_sensitivity - 1:
                self.camera.mouse_sensitivity += 1
        
        # Label
        # -----
        imgui.same_line()
        imgui.text("Mouse Sensitivity")


class PostProcessingUI:
    def __init__(self, **kwargs):
        self.pt_state = kwargs.get("pt_state")

        super().__init__(**kwargs)

    def tonemap_dropdown(self):
        options = ["None", "ACESFilm", "AgX", "AgXGolden", "AgXPunchy", "Filmic", "Lottes",
                   "Neutral", "Reinhard", "Reinhard2", "Uchimura", "Uncharted2", "Unreal"]

        curr_tonemap = "AgX"

        if imgui.begin_combo("Render Mode", curr_tonemap):
            for tonemap in options:
                is_selected = (curr_tonemap == tonemap)

                clicked, state = imgui.selectable(tonemap, is_selected)

                if clicked:
                    curr_tonemap = tonemap

                    post_process_settings.tonemap = curr_tonemap
                    self.pt_state.restart_render()

                if is_selected:
                    imgui.set_item_default_focus()
            
            imgui.end_combo()


class SettingsUI(PostProcessingUI, CameraUI, PathTracingUI, RenderingUI):
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
            
        self.tiles_x_slider()
        self.tiles_y_slider()

    def path_tracing_ui(self):
        self.max_bounce_slider()
        self.max_samples_slider()
        self.spp_slider()
        self.reset_pt_button()
    
    def camera_ui(self):
        self.movement_speed_slider()
        self.fov_slider()
        self.mouse_sensitivity_slider()
    
    def post_processing_ui(self):
        self.tonemap_dropdown()
