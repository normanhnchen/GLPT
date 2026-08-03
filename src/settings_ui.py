from imgui_bundle import imgui
from glfw.GLFW import *
from src.settings import *
from src.settings import _pt_settings_default


class IntSlider:
    def __init__(self, min_val, max_val, label, slider_speed=0.5):
        self.window = glfwGetCurrentContext()
        self.slider_speed = slider_speed
        self.min_val = min_val
        self.max_val = max_val
        self.label = label
        self.unique_code = label.lower().replace(" ", "_")

    def slider(self, curr_val, val_format=None):
        fmt = val_format if val_format is not None else "%d"
        self.changed, self.val = imgui.drag_int(
            f"##{self.unique_code}",
            curr_val,
            self.slider_speed,
            self.min_val,
            self.max_val,
            format=fmt
        )

    def dragging_logic(self, on_change):
        if imgui.is_item_active() and self.changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            on_change(self.val)
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)

    def minus_button(self, on_change):
        imgui.same_line()
        if imgui.button(f"-##{self.unique_code}_minus"):
            if self.min_val + self.slider_speed <= self.val <= self.max_val:
                self.val -= self.slider_speed

                on_change(self.val)

    def plus_button(self, on_change):
        imgui.same_line()
        if imgui.button(f"+##{self.unique_code}_plus"):
            if self.min_val <= self.val <= self.max_val - self.slider_speed:
                self.val += self.slider_speed

                on_change(self.val)

    def draw_label(self):
        imgui.same_line()
        imgui.text(self.label)


class FloatSlider:
    def __init__(self, min_val, max_val, label, slider_speed=0.5):
        self.window = glfwGetCurrentContext()
        self.slider_speed = slider_speed
        self.min_val = min_val
        self.max_val = max_val
        self.label = label
        self.unique_code = label.lower().replace(" ", "_")

    def slider(self, curr_val, val_format=None):
        fmt = val_format if val_format is not None else "%.1f"
        self.changed, self.val = imgui.drag_float(
            f"##{self.unique_code}",
            curr_val,
            self.slider_speed,
            self.min_val,
            self.max_val,
            format=fmt
        )

    def dragging_logic(self, on_change):
        if imgui.is_item_active() and self.changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            on_change(self.val)
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)

    def minus_button(self, on_change):
        imgui.same_line()
        if imgui.button(f"-##{self.unique_code}_minus"):
            if self.min_val + self.slider_speed <= self.val <= self.max_val:
                self.val -= self.slider_speed

                on_change(self.val)

    def plus_button(self, on_change):
        imgui.same_line()
        if imgui.button(f"+##{self.unique_code}_plus"):
            if self.min_val <= self.val <= self.max_val - self.slider_speed:
                self.val += self.slider_speed

                on_change(self.val)

    def draw_label(self):
        imgui.same_line()
        imgui.text(self.label)


class Dropdown:
    def __init__(self, label):
        self.label = label

    def dropdown(self, options, curr_selection, on_change):
        if imgui.begin_combo(self.label, curr_selection):
            for option in options:
                is_selected = curr_selection == option

                clicked, _ = imgui.selectable(option, is_selected)

                if clicked:
                    curr_selection = option

                    on_change(curr_selection)

                if is_selected:
                    imgui.set_item_default_focus()
            
            imgui.end_combo()


class RenderingUI:
    def __init__(self, **kwargs):
        self.pt_state = kwargs.get("pt_state")
        self.camera_buffer = kwargs.get("camera_buffer")
        self.window = glfwGetCurrentContext()

        super().__init__()

        self.tiles_x_slider = IntSlider(1, 1024, "Tiles X", render_settings.tiles_x)
        self.tiles_y_slider = IntSlider(1, 1024, "Tiles Y", render_settings.tiles_y)
    
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
            self.pt_state.should_denoise = False
    
    def viewport_button(self):
        if imgui.button("Back to Viewport"):
            render_settings.render_mode = "rasterization"
            self.pt_state.view_saved = False
            self.pt_state.should_denoise = False
    
    def start_button(self):
        if imgui.button("Start Render"):
            self.pt_state.start_render(self.camera_buffer)
            self.pt_state.view_saved = False
            self.pt_state.should_render = True
            self.pt_state.should_denoise = False
    
    def start_new_button(self):
        if imgui.button("Start New Render"):
            self.pt_state.start_render(self.camera_buffer)
            self.pt_state.view_saved = False
            self.pt_state.should_render = True
            self.pt_state.should_denoise = False
        
    def denoise_button(self):
        if imgui.button("Start Denoising"):
            self.pt_state.should_denoise = True
    
    def view_saved_button(self):
        if imgui.button("View Saved Render"):
            render_settings.render_mode = "path_tracing"
            self.pt_state.view_saved = True
    
    def draw_tiles_x_slider(self):
        def on_change(new_val):
            render_settings.tiles_x = new_val
            self.pt_state.restart_render()
            self.pt_state.total_samples = 0
            
        self.tiles_x_slider.slider(render_settings.tiles_x)
        self.tiles_x_slider.dragging_logic(on_change)
        self.tiles_x_slider.minus_button(on_change)
        self.tiles_x_slider.plus_button(on_change)
        self.tiles_x_slider.draw_label()
    
    def draw_tiles_y_slider(self):
        def on_change(new_val):
            render_settings.tiles_y = new_val
            self.pt_state.restart_render()
            self.pt_state.total_samples = 0
            
        self.tiles_y_slider.slider(render_settings.tiles_y)
        self.tiles_y_slider.dragging_logic(on_change)
        self.tiles_y_slider.minus_button(on_change)
        self.tiles_y_slider.plus_button(on_change)
        self.tiles_y_slider.draw_label()
    
    def export_render_button(self):
        if imgui.button("Export Render"):
            self.pt_state.export_render()


class PathTracingUI:
    def __init__(self, **kwargs):
        self.pt_state = kwargs.get("pt_state")
        self.window = glfwGetCurrentContext()

        super().__init__(**kwargs)

        self.total_bounces_slider = IntSlider(0, 1024, "Total Bounces")
        self.diffuse_bounces_slider = IntSlider(0, 1024, "Diffuse Bounces")
        self.specular_bounces_slider = IntSlider(0, 1024, "Specular Bounces")
        self.transmission_bounces_slider = IntSlider(0, 1024, "Transmission Bounces")
        self.max_samples_slider = IntSlider(1, 16384, "Max Samples")
        self.spp_slider = IntSlider(1, 128, "Samples Per Pixel")
    
    def draw_total_bounces_slider(self):
        def on_change(new_val):
            pt_settings.total_bounces = new_val
            self.pt_state.restart_render()
        
        self.total_bounces_slider.slider(pt_settings.total_bounces)
        self.total_bounces_slider.dragging_logic(on_change)
        self.total_bounces_slider.minus_button(on_change)
        self.total_bounces_slider.plus_button(on_change)
        self.total_bounces_slider.draw_label()

    def draw_diffuse_bounces_slider(self):
        def on_change(new_val):
            pt_settings.diffuse_bounces = new_val
            self.pt_state.restart_render()
        
        self.diffuse_bounces_slider.slider(pt_settings.diffuse_bounces)
        self.diffuse_bounces_slider.dragging_logic(on_change)
        self.diffuse_bounces_slider.minus_button(on_change)
        self.diffuse_bounces_slider.plus_button(on_change)
        self.diffuse_bounces_slider.draw_label()

    def draw_specular_bounces_slider(self):
        def on_change(new_val):
            pt_settings.specular_bounces = new_val
            self.pt_state.restart_render()
        
        self.specular_bounces_slider.slider(pt_settings.specular_bounces)
        self.specular_bounces_slider.dragging_logic(on_change)
        self.specular_bounces_slider.minus_button(on_change)
        self.specular_bounces_slider.plus_button(on_change)
        self.specular_bounces_slider.draw_label()

    def draw_transmission_bounces_slider(self):
        def on_change(new_val):
            pt_settings.transmission_bounces = new_val
            self.pt_state.restart_render()
        
        self.transmission_bounces_slider.slider(pt_settings.transmission_bounces)
        self.transmission_bounces_slider.dragging_logic(on_change)
        self.transmission_bounces_slider.minus_button(on_change)
        self.transmission_bounces_slider.plus_button(on_change)
        self.transmission_bounces_slider.draw_label()
        
    def draw_max_samples_slider(self):
        def on_change(new_val):
            pt_settings.max_samples = new_val
            self.pt_state.restart_render()
        
        self.max_samples_slider.slider(pt_settings.max_samples)
        self.max_samples_slider.dragging_logic(on_change)
        self.max_samples_slider.minus_button(on_change)
        self.max_samples_slider.plus_button(on_change)
        self.max_samples_slider.draw_label()
    
    def draw_spp_slider(self):
        def on_change(new_val):
            pt_settings.spp = new_val
            self.pt_state.restart_render()
        
        self.spp_slider.slider(pt_settings.spp)
        self.spp_slider.dragging_logic(on_change)
        self.spp_slider.minus_button(on_change)
        self.spp_slider.plus_button(on_change)
        self.spp_slider.draw_label()

    def specular_mode_combo(self):
        specular_modes = ["GGX VNDF", "Cosine Hemisphere"]

        current_mode_name = specular_modes[self.pt_state.specular_mode]

        if imgui.button(f"Specular Mode: {current_mode_name}"):
            self.pt_state.specular_mode = (self.pt_state.specular_mode + 1) % len(specular_modes)
            self.pt_state.restart_render()

    def geometry_mode_combo(self):
        geometry_modes = ["Height-Correlated Smith Method", "Schlick-GGX Approximation Method"]

        current_mode_name = geometry_modes[self.pt_state.geometry_mode]
        
        if imgui.button(f"Geometry Mode: {current_mode_name}"):
            self.pt_state.geometry_mode = (self.pt_state.geometry_mode + 1) % len(geometry_modes)
            self.pt_state.restart_render()
    
    def transmission_mode_combo(self):
        transmissions_modes = ["Beer-Lambert", "None"]

        current_mode_name = transmissions_modes[self.pt_state.transmission_mode]
        
        if imgui.button(f"Transmission Mode: {current_mode_name}"):
            self.pt_state.transmission_mode = (self.pt_state.transmission_mode + 1) % len(transmissions_modes)
            self.pt_state.restart_render()

    def mis_mode_combo(self):
        mis_modes = ["On", "Off"]

        current_mode_name = mis_modes[self.pt_state.mis_mode]
        
        if imgui.button(f"MIS Mode: {current_mode_name}"):
            self.pt_state.mis_mode = (self.pt_state.mis_mode + 1) % len(mis_modes)
            self.pt_state.restart_render()
    
    def reset_pt_button(self):
        if imgui.button("Reset Path Tracing Settings"):
            pt_settings.total_bounces = _pt_settings_default.total_bounces
            pt_settings.diffuse_bounces = _pt_settings_default.diffuse_bounces
            pt_settings.specular_bounces = _pt_settings_default.specular_bounces
            pt_settings.transmission_bounces = _pt_settings_default.transmission_bounces
            pt_settings.max_samples = _pt_settings_default.max_samples
            pt_settings.spp = _pt_settings_default.spp
            self.pt_state.specular_mode = _pt_settings_default.specular_mode
            self.pt_state.geometry_mode = _pt_settings_default.geometry_mode
            self.pt_state.transmission_mode = _pt_settings_default.transmission_mode
            self.pt_state.mis_mode = _pt_settings_default.mis_mode
            self.pt_state.restart_render()


class CameraUI:
    def __init__(self, **kwargs):
        self.pt_state = kwargs.get("pt_state")
        self.camera = kwargs.get("camera")
        self.window = glfwGetCurrentContext()

        super().__init__(**kwargs)

        self.movement_speed_slider = FloatSlider(0, 10000, "Movement Speed")
        self.fov_slider = FloatSlider(1, 135, "Field Of View", slider_speed=1)
        self.mouse_sensitivity_slider = FloatSlider(0.1, 10, "Mouse Sensitivity", slider_speed=0.1)

    def draw_movement_speed_slider(self):
        def on_change(new_val):
            self.camera.movement_speed = new_val
        
        self.movement_speed_slider.slider(self.camera.movement_speed)
        self.movement_speed_slider.dragging_logic(on_change)
        self.movement_speed_slider.minus_button(on_change)
        self.movement_speed_slider.plus_button(on_change)
        self.movement_speed_slider.draw_label()
    
    def draw_fov_slider(self):
        def on_change(new_val):
            self.camera.fov = new_val
        
        self.fov_slider.slider(self.camera.fov)
        self.fov_slider.dragging_logic(on_change)
        self.fov_slider.minus_button(on_change)
        self.fov_slider.plus_button(on_change)
        self.fov_slider.draw_label()
    
    def draw_mouse_sensitivity_slider(self):
        # Alter the slider values to look larger but is the same internally
        visual_factor = 10
        
        def on_change(new_val):
            self.camera.mouse_sensitivity = new_val / visual_factor
        
        self.mouse_sensitivity_slider.slider(self.camera.mouse_sensitivity * visual_factor)
        self.mouse_sensitivity_slider.dragging_logic(on_change)
        self.mouse_sensitivity_slider.minus_button(on_change)
        self.mouse_sensitivity_slider.plus_button(on_change)
        self.mouse_sensitivity_slider.draw_label()


class PostProcessingUI:
    def __init__(self, **kwargs):
        self.pt_state = kwargs.get("pt_state")
        self.post_process_state = kwargs.get("post_process_state")
        self.camera_buffer = kwargs.get("camera_buffer")
        self.window = glfwGetCurrentContext()

        super().__init__(**kwargs)

        self.exposure_slider = FloatSlider(0, 10, "Exposure", slider_speed=0.1)
        self.hdri_exposure_slider = FloatSlider(0, 10, "HDRI Exposure", slider_speed=0.1)
        self.blur_slider = FloatSlider(0, 100, "Blur")
        self.aperture_slider = FloatSlider(0.1, 10, "Aperture", slider_speed=0.1)
        self.focus_dist_slider = FloatSlider(0.1, 1000, "Focus Distance", slider_speed=0.1)
        
        self.tonemap_dropdown = Dropdown("Render Mode")

    def draw_tonemap_dropdown(self):
        options = ["None", "ACESFilm", "AgX", "AgXGolden", "AgXPunchy", "Filmic", "Lottes",
                   "Neutral", "Reinhard", "Reinhard2", "Uchimura", "Uncharted2", "Unreal"]

        def on_change(new_val):
            self.post_process_state.tonemap = new_val
            post_process_settings.tonemap = self.post_process_state.tonemap
            self.pt_state.restart_render()

        self.tonemap_dropdown.dropdown(options, self.post_process_state.tonemap, on_change)
        
    def draw_exposure_slider(self):
        def on_change(new_val):
            post_process_settings.exposure = new_val
            self.pt_state.restart_render()
        
        self.exposure_slider.slider(post_process_settings.exposure)
        self.exposure_slider.dragging_logic(on_change)
        self.exposure_slider.minus_button(on_change)
        self.exposure_slider.plus_button(on_change)
        self.exposure_slider.draw_label()
    
    def draw_hdri_exposure_slider(self):
        def on_change(new_val):
            post_process_settings.hdri_exposure = new_val
            self.pt_state.restart_render()
        
        self.hdri_exposure_slider.slider(post_process_settings.hdri_exposure)
        self.hdri_exposure_slider.dragging_logic(on_change)
        self.hdri_exposure_slider.minus_button(on_change)
        self.hdri_exposure_slider.plus_button(on_change)
        self.hdri_exposure_slider.draw_label()

    def draw_blur_slider(self):
        def on_change(new_val):
            post_process_settings.blur = new_val
            self.pt_state.restart_render()
        
        self.blur_slider.slider(post_process_settings.blur)
        self.blur_slider.dragging_logic(on_change)
        self.blur_slider.minus_button(on_change)
        self.blur_slider.plus_button(on_change)
        self.blur_slider.draw_label()
    
    def dof_checkbox(self):
        enabled = self.post_process_state.dof_enabled
        changed, enabled = imgui.checkbox("Enable Depth of Field", enabled)
        if changed:
            self.post_process_state.dof_enabled = enabled
            if not enabled:
                post_process_settings.aperture = 0
                self.camera_buffer.update_data()
                self.pt_state.restart_render()
            else:
                post_process_settings.aperture = self.post_process_state.aperture
                self.camera_buffer.update_data()
                self.pt_state.restart_render()
        
    def draw_aperture_slider(self):
        if not self.post_process_state.dof_enabled:
            return

        def on_change(new_val):
            post_process_settings.aperture = new_val
            self.post_process_state.aperture = post_process_settings.aperture
            self.camera_buffer.update_data()
            self.pt_state.restart_render()
        
        self.blur_slider.slider(post_process_settings.aperture)
        self.blur_slider.dragging_logic(on_change)
        self.blur_slider.minus_button(on_change)
        self.blur_slider.plus_button(on_change)
        self.blur_slider.draw_label()
    
    def draw_focus_dist_slider(self):
        if not self.post_process_state.dof_enabled:
            return

        def on_change(new_val):
            post_process_settings.focus_dist = new_val
            self.post_process_state.focus_dist = post_process_settings.focus_dist
            self.camera_buffer.update_data()
            self.pt_state.restart_render()
        
        self.blur_slider.slider(post_process_settings.focus_dist)
        self.blur_slider.dragging_logic(on_change)
        self.blur_slider.minus_button(on_change)
        self.blur_slider.plus_button(on_change)
        self.blur_slider.draw_label()


class ScreenUI:
    def __init__(self, **kwargs):
        self.pt_state = kwargs.get("pt_state")
        self.window = glfwGetCurrentContext()

        super().__init__(**kwargs)

        self.fps_slider = IntSlider(30, 361, "FPS", slider_speed=1)
    
    def vsync_checkbox(self):
        enabled = screen.vsync
        changed, enabled = imgui.checkbox("VSync", enabled)

        if changed:
            screen.vsync = enabled

            if screen.vsync == True:
                glfwSwapInterval(1)
            else:
                glfwSwapInterval(0)
    
    def draw_fps_slider(self):
        is_unlimited = screen.fps_cap == -1
        display_fps = 361 if is_unlimited else screen.fps_cap
        fps_format = "None" if is_unlimited else "%d"
        
        def on_change(new_val):
            screen.fps_cap = -1 if new_val > 360 else new_val

        self.fps_slider.slider(display_fps, val_format=fps_format)
        self.fps_slider.dragging_logic(on_change)
        self.fps_slider.minus_button(on_change)
        self.fps_slider.plus_button(on_change)
        self.fps_slider.draw_label()
    

class DebugUI:
    def __init__(self, **kwargs):
        self.pt_state = kwargs.get("pt_state")

        super().__init__(**kwargs)
    
    def debug_mode_button(self):
        if self.pt_state.saved_combined is not None:
            if imgui.button("Off"):
                self.pt_state.debug_mode = "off"
            else:
                if imgui.button("View Albedo"):
                    self.pt_state.debug_mode = "albedo"
                if imgui.button("View Normal"):
                    self.pt_state.debug_mode = "normal"
                if imgui.button("View Depth"):
                    self.pt_state.debug_mode = "depth"
        else:
            imgui.text_disabled("No saved renders")


class SceneUI:
    def __init__(self, **kwargs):
        self.scene_state = kwargs.get("scene_state")

        super().__init__(**kwargs)
    
    def next_scene_button(self):
        enabled = self.scene_state.curr_scene_idx < self.scene_state.num_scenes - 1
        imgui.begin_disabled(not enabled)

        if imgui.button("Next Scene"):
            self.scene_state.next_scene()
        
        imgui.end_disabled()
    
    def previous_scene_button(self):
        enabled = self.scene_state.curr_scene_idx > 0
        imgui.begin_disabled(not enabled)

        if imgui.button("Previous Scene"):
            self.scene_state.previous_scene()
        
        imgui.end_disabled()


class CameraCapturingUI:
    def __init__(self, **kwargs):
        self.scene_state = kwargs.get("scene_state")
        self.camera_capture_state = kwargs.get("camera_capture_state")

        super().__init__(**kwargs)
    
    def save_state_button(self):
        if imgui.button("Save Current Camera State"):
            self.camera_capture_state.save_state()
    
    def remove_state_button(self):
        scene_file = self.scene_state.scene_files[self.scene_state.curr_scene_idx]
        scene_captures = self.camera_capture_state.states[str(scene_file)]
        scene_capture_count = len(scene_captures)

        enabled = scene_capture_count > 0
        imgui.begin_disabled(not enabled)

        if imgui.button("Remove Last Camera State From This Scene"):
            self.camera_capture_state.remove_state()
        
        imgui.end_disabled()


class SettingsUI(CameraCapturingUI, SceneUI, DebugUI, ScreenUI, PostProcessingUI, CameraUI, PathTracingUI, RenderingUI):
    def __init__(self,
            pt_state,
            post_process_state,
            scene_state,
            camera_capture_state,
            camera_buffer,
            camera
        ):
        super().__init__(
            pt_state=pt_state,
            post_process_state=post_process_state,
            scene_state=scene_state,
            camera_capture_state=camera_capture_state,
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
                self.denoise_button()
                # Disable for now!
                # Fix render exporting by adding an FBO to include tonemapping / gamma correction
                # self.export_render_button()
            
            self.restart_button()
        
        else:
            if self.pt_state.saved_combined is None:
                self.start_button()
            
            else:
                self.start_new_button()
                self.view_saved_button()
            
        self.draw_tiles_x_slider()
        self.draw_tiles_y_slider()

    def path_tracing_ui(self):
        self.draw_total_bounces_slider()
        self.draw_diffuse_bounces_slider()
        self.draw_specular_bounces_slider()
        self.draw_transmission_bounces_slider()
        self.draw_max_samples_slider()
        self.draw_spp_slider()
        if imgui.tree_node("BSDF Sampling"):
            self.specular_mode_combo()
            self.geometry_mode_combo()
            self.transmission_mode_combo()
            self.mis_mode_combo()

            imgui.tree_pop()
        self.reset_pt_button()
    
    def camera_ui(self):
        self.draw_movement_speed_slider()
        self.draw_fov_slider()
        self.draw_mouse_sensitivity_slider()
    
    def post_processing_ui(self):
        self.draw_exposure_slider()
        self.draw_hdri_exposure_slider()
        self.draw_tonemap_dropdown()
        self.draw_blur_slider()
        self.dof_checkbox()
        self.draw_aperture_slider()
        self.draw_focus_dist_slider()
    
    def screen_ui(self):
        self.vsync_checkbox()
        self.draw_fps_slider()
    
    def debug_ui(self):
        self.debug_mode_button()
    
    def scene_ui(self):
        self.next_scene_button()
        self.previous_scene_button()
    
    def camera_capturing_ui(self):
        self.save_state_button()
        self.remove_state_button()
