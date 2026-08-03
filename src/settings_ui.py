from imgui_bundle import imgui
from glfw.GLFW import *
from src.settings import *
from src.settings import _pt_settings_default


class IntSlider:
    def __init__(
            self,
            window,
            min_val,
            max_val,
            label,
            slider_speed=0.5
        ):
        self.window = window
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
            if self.min_val < self.val < self.max_val:
                self.val -= 1

                on_change(self.val)

    def plus_button(self, on_change):
        imgui.same_line()
        if imgui.button(f"+##{self.unique_code}_plus"):
            if self.min_val < self.val < self.max_val:
                self.val += 1

                on_change(self.val)

    def draw_label(self):
        imgui.same_line()
        imgui.text(self.label)


class RenderingUI:
    def __init__(self, **kwargs):
        self.pt_state = kwargs.get("pt_state")
        self.camera_buffer = kwargs.get("camera_buffer")
        self.window = glfwGetCurrentContext()

        super().__init__()

        self.tiles_x_slider = IntSlider(self.window, 1, 1024, "Tiles X", render_settings.tiles_x)
        self.tiles_y_slider = IntSlider(self.window, 1, 1024, "Tiles Y", render_settings.tiles_y)
    
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

        self.total_bounces_slider = IntSlider(self.window, 0, 1024, "Total Bounces", pt_settings.total_bounces)
        self.diffuse_bounces_slider = IntSlider(self.window, 0, 1024, "Diffuse Bounces", pt_settings.diffuse_bounces)
        self.specular_bounces_slider = IntSlider(self.window, 0, 1024, "Specular Bounces", pt_settings.specular_bounces)
        self.transmission_bounces_slider = IntSlider(self.window, 0, 1024, "Transmission Bounces", pt_settings.transmission_bounces)
        self.max_samples_slider = IntSlider(self.window, 1, 16384, "Max Samples", pt_settings.max_samples)
        self.spp_slider = IntSlider(self.window, 1, 128, "Samples Per Pixel", pt_settings.spp)
    
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

        super().__init__(**kwargs)

    def draw_movement_speed_slider(self):
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
            hardcoded_max_speed,
            val_format
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
    
    def draw_fov_slider(self):
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
    
    def draw_mouse_sensitivity_slider(self):
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
        self.post_process_state = kwargs.get("post_process_state")
        self.camera_buffer = kwargs.get("camera_buffer")

        super().__init__(**kwargs)

    def tonemap_dropdown(self):
        options = ["None", "ACESFilm", "AgX", "AgXGolden", "AgXPunchy", "Filmic", "Lottes",
                   "Neutral", "Reinhard", "Reinhard2", "Uchimura", "Uncharted2", "Unreal"]

        if imgui.begin_combo("Render Mode", self.post_process_state.tonemap):
            for tonemap in options:
                is_selected = (self.post_process_state.tonemap == tonemap)

                clicked, state = imgui.selectable(tonemap, is_selected)

                if clicked:
                    self.post_process_state.tonemap = tonemap

                    post_process_settings.tonemap = self.post_process_state.tonemap
                    self.pt_state.restart_render()

                if is_selected:
                    imgui.set_item_default_focus()
            
            imgui.end_combo()
        
    def draw_exposure_slider(self):
        # Slider 
        # ------
        slider_speed = 0.1
        hardcoded_min_exposure = 0.1
        hardcoded_max_exposure = 10
        exposure = post_process_settings.exposure
        val_format = "%.1f"
        changed, exposure = imgui.drag_float(
            "##exposure",
            exposure,
            slider_speed,
            hardcoded_min_exposure,
            hardcoded_max_exposure,
            val_format
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active() and changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            post_process_settings.exposure = exposure
            self.pt_state.restart_render()
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
        
        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##exposure_minus"):
            if post_process_settings.exposure > hardcoded_min_exposure:
                post_process_settings.exposure -= 1
                self.pt_state.restart_render()
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##exposure_plus"):
            if post_process_settings.exposure < hardcoded_max_exposure:
                post_process_settings.exposure += 1
                self.pt_state.restart_render()
        
        # Label
        # -----
        imgui.same_line()
        imgui.text("Exposure")
    
    def draw_hdri_exposure_slider(self):
        # Slider 
        # ------
        slider_speed = 0.1
        hardcoded_min_hdri_exposure = 0.1
        hardcoded_max_hdri_exposure = 10
        hdri_exposure = post_process_settings.hdri_exposure
        val_format = "%.1f"
        changed, hdri_exposure = imgui.drag_float(
            "##hdri_exposure",
            hdri_exposure,
            slider_speed,
            hardcoded_min_hdri_exposure,
            hardcoded_max_hdri_exposure,
            val_format
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active() and changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            post_process_settings.hdri_exposure = hdri_exposure
            self.pt_state.restart_render()
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
        
        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##hdri_exposure_minus"):
            if post_process_settings.hdri_exposure > hardcoded_min_hdri_exposure:
                post_process_settings.hdri_exposure -= 1
                self.pt_state.restart_render()
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##hdri_exposure_plus"):
            if post_process_settings.hdri_exposure < hardcoded_max_hdri_exposure:
                post_process_settings.hdri_exposure += 1
                self.pt_state.restart_render()
        
        # Label
        # -----
        imgui.same_line()
        imgui.text("HDRI Exposure")
    
    def draw_blur_slider(self):
        # Slider 
        # ------
        slider_speed = 0.5
        hardcoded_min_blur = 0
        hardcoded_max_blur = 100
        blur = post_process_settings.blur
        val_format = "%.1f"
        changed, blur = imgui.drag_float(
            "##blur",
            blur,
            slider_speed,
            hardcoded_min_blur,
            hardcoded_max_blur,
            val_format
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active() and changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            post_process_settings.blur = blur
            self.pt_state.restart_render()
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
        
        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##blur_minus"):
            if post_process_settings.blur > hardcoded_min_blur:
                post_process_settings.blur -= 1
                self.pt_state.restart_render()
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##blur_plus"):
            if post_process_settings.blur < hardcoded_max_blur:
                post_process_settings.blur += 1
                self.pt_state.restart_render()
        
        # Label
        # -----
        imgui.same_line()
        imgui.text("Blur")
    
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
        
        # Slider 
        # ------
        slider_speed = 0.1
        hardcoded_min_aperture = 0.1
        hardcoded_max_aperture = 10
        aperture = post_process_settings.aperture
        val_format = "%.1f"
        changed, aperture = imgui.drag_float(
            "##aperture",
            aperture,
            slider_speed,
            hardcoded_min_aperture,
            hardcoded_max_aperture,
            val_format
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active() and changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            post_process_settings.aperture = aperture
            self.post_process_state.aperture = post_process_settings.aperture
            self.camera_buffer.update_data()
            self.pt_state.restart_render()
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
        
        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##aperture_minus"):
            if post_process_settings.aperture > hardcoded_min_aperture:
                post_process_settings.aperture -= 1
                self.post_process_state.aperture = post_process_settings.aperture
                self.camera_buffer.update_data()
                self.pt_state.restart_render()
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##aperture_plus"):
            if post_process_settings.aperture < hardcoded_max_aperture:
                post_process_settings.aperture += 1
                self.post_process_state.aperture = post_process_settings.aperture
                self.camera_buffer.update_data()
                self.pt_state.restart_render()
        
        # Label
        # -----
        imgui.same_line()
        imgui.text("Aperture")
    
    def draw_focus_dist_slider(self):
        if not self.post_process_state.dof_enabled:
            return
        
        # Slider 
        # ------
        slider_speed = 0.1
        hardcoded_min_focus_dist = 0.1
        hardcoded_max_focus_dist = 1000
        focus_dist = post_process_settings.focus_dist
        val_format = "%.1f"
        changed, focus_dist = imgui.drag_float(
            "##focus_dist",
            focus_dist,
            slider_speed,
            hardcoded_min_focus_dist,
            hardcoded_max_focus_dist,
            val_format
        )

        # Dragging logic
        # --------------
        if imgui.is_item_active() and changed:
            if imgui.is_mouse_dragging(0):
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            else:
                glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
            
            post_process_settings.focus_dist = focus_dist
            self.post_process_state.focus_dist = post_process_settings.focus_dist
            self.camera_buffer.update_data()
            self.pt_state.restart_render()
        
        if imgui.is_item_deactivated():
            glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)
        
        # Minus button
        # ------------
        imgui.same_line()
        if imgui.button("-##focus_dist_minus"):
            if post_process_settings.focus_dist > hardcoded_min_focus_dist:
                post_process_settings.focus_dist -= 1
                self.post_process_state.focus_dist = post_process_settings.focus_dist
                self.camera_buffer.update_data()
                self.pt_state.restart_render()
        
        # Plus button
        # ------------
        imgui.same_line()
        if imgui.button("+##focus_dist_plus"):
            if post_process_settings.focus_dist < hardcoded_max_focus_dist:
                post_process_settings.focus_dist += 1
                self.post_process_state.focus_dist = post_process_settings.focus_dist
                self.camera_buffer.update_data()
                self.pt_state.restart_render()
        
        # Label
        # -----
        imgui.same_line()
        imgui.text("Focus Distance")


class ScreenUI:
    def __init__(self, **kwargs):
        self.pt_state = kwargs.get("pt_state")
        self.window = glfwGetCurrentContext()

        super().__init__(**kwargs)

        self.fps_slider = IntSlider(self.window, 30, 360, "Samples Per Pixel", slider_speed=1)
    
    def vsync_checkbox(self):
        enabled = screen.vsync
        changed, enabled = imgui.checkbox("Vsync", enabled)

        if changed:
            screen.vsync = enabled

            if screen.vsync == True:
                glfwSwapInterval(1)
            else:
                glfwSwapInterval(0)
    
    def draw_fps_slider(self):
        is_unlimited = screen.fps_cap == -1
        display_fps = 360 if is_unlimited else screen.fps_cap
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
        self.total_bounces_slider()
        self.diffuse_bounces_slider()
        self.specular_bounces_slider()
        self.transmission_bounces_slider()
        self.max_samples_slider()
        self.spp_slider()
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
        self.tonemap_dropdown()
        self.draw_blur_slider()
        self.dof_checkbox()
        self.draw_aperture_slider()
        self.draw_focus_dist_slider()
    
    def screen_ui(self):
        self.vsync_checkbox()
        self.fps_slider()
    
    def debug_ui(self):
        self.debug_mode_button()
    
    def scene_ui(self):
        self.next_scene_button()
        self.previous_scene_button()
    
    def camera_capturing_ui(self):
        self.save_state_button()
        self.remove_state_button()
