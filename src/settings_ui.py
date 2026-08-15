from imgui_bundle import imgui
from glfw.GLFW import *
from src.settings import *


class IntSlider:
    def __init__(self, min_val, max_val, label, slider_speed=0.5, increment=1, wrap=False):
        self.window = glfwGetCurrentContext()
        self.slider_speed = slider_speed
        self.increment = increment
        self.min_val = min_val
        self.max_val = max_val
        self.label = label
        self.wrap = wrap
        self.unique_code = label.lower().replace(" ", "_")

    def slider(self, curr_val, val_format="%d", enabled=True, reason="", width=None):
        if self.wrap:
            val_format = val_format
        
        if width is not None:
            imgui.push_item_width(width)

        if not enabled:
            imgui.begin_disabled()

        if self.wrap:
            # Tell ImGui to disable min max slider bounds
            drag_min = 0
            drag_max = 0
        else:
            drag_min = self.min_val
            drag_max = self.max_val
        
        self.changed, self.val = imgui.drag_int(
            f"##{self.unique_code}",
            curr_val,
            self.slider_speed,
            drag_min,
            drag_max,
            format=val_format
        )

        if not enabled:
            imgui.end_disabled()
            if reason and imgui.is_item_hovered(imgui.HoveredFlags_.allow_when_disabled):
                imgui.set_tooltip(reason)

        if width is not None:
            imgui.pop_item_width()

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
            if self.min_val + self.increment <= self.val <= self.max_val:
                self.val -= self.increment

                on_change(self.val)

    def plus_button(self, on_change):
        imgui.same_line()
        if imgui.button(f"+##{self.unique_code}_plus"):
            if self.min_val <= self.val <= self.max_val - self.increment:
                self.val += self.increment

                on_change(self.val)

    def draw_label(self):
        imgui.same_line()
        imgui.text(self.label)


class FloatSlider:
    def __init__(self, min_val, max_val, label, slider_speed=0.5, increment=0.5, wrap=False):
        self.window = glfwGetCurrentContext()
        self.slider_speed = slider_speed
        self.increment = increment
        self.min_val = min_val
        self.max_val = max_val
        self.label = label
        self.wrap = wrap
        self.unique_code = label.lower().replace(" ", "_")

    def _wrapped(self, val):
        range_size = self.max_val - self.min_val
        return self.min_val + (val - self.min_val) % range_size

    def slider(self, curr_val, val_format="%.1f", enabled=True, reason="", width=None):
        if self.wrap:
            val_format = val_format

        if width is not None:
            imgui.push_item_width(width)

        if not enabled:
            imgui.begin_disabled()

        if self.wrap:
            # Tell ImGui to disable min max slider bounds
            drag_min = 0
            drag_max = 0
        else:
            drag_min = self.min_val
            drag_max = self.max_val

        self.changed, self.val = imgui.drag_float(
            f"##{self.unique_code}",
            curr_val,
            self.slider_speed,
            drag_min,
            drag_max,
            format=val_format
        )

        if self.wrap and self.changed:
            self.val = self._wrapped(self.val)

        if not enabled:
            imgui.end_disabled()
            if reason and imgui.is_item_hovered(imgui.HoveredFlags_.allow_when_disabled):
                imgui.set_tooltip(reason)

        if width is not None:
            imgui.pop_item_width()

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
            if self.min_val + self.increment <= self.val <= self.max_val:
                self.val -= self.increment

                on_change(self.val)

    def plus_button(self, on_change):
        imgui.same_line()
        if imgui.button(f"+##{self.unique_code}_plus"):
            if self.min_val <= self.val <= self.max_val - self.increment:
                self.val += self.increment

                on_change(self.val)

    def draw_label(self):
        imgui.same_line()
        imgui.text(self.label)


class Button:
    def __init__(self, label):
        self.label = label

    def button(self, on_change, enabled=True, reason=""):
        if not enabled:
            imgui.begin_disabled()
        
        if imgui.button(self.label):
            on_change()
        
        if not enabled:
            imgui.end_disabled()
            if reason and imgui.is_item_hovered(imgui.HoveredFlags_.allow_when_disabled):
                imgui.set_tooltip(reason)


class CycleButton:
    def __init__(self, label):
        self.label = label

    def button(self, options, curr_idx, on_change, enabled=True, reason=""):
        if not enabled:
            imgui.begin_disabled()
        
        if imgui.button(f"{self.label}: {options[curr_idx]}"):
            curr_idx = (curr_idx + 1) % len(options)

            on_change(curr_idx)

        if not enabled:
            imgui.end_disabled()
            if reason and imgui.is_item_hovered(imgui.HoveredFlags_.allow_when_disabled):
                imgui.set_tooltip(reason)


class Dropdown:
    def __init__(self, label):
        self.label = label

    def dropdown(self, options, curr_selection, on_change, enabled=True, reason=""):
        if not enabled:
            imgui.begin_disabled()
        
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

        if not enabled:
            imgui.end_disabled()
            if reason and imgui.is_item_hovered(imgui.HoveredFlags_.allow_when_disabled):
                imgui.set_tooltip(reason)


class Checkbox:
    def __init__(self, label):
        self.label = label

    def checkbox(self, already_enabled, on_change, on_enable, on_disable, enabled=True, reason=""):
        if not enabled:
            imgui.begin_disabled()
        
        changed, value = imgui.checkbox(self.label, already_enabled)

        if not enabled:
            imgui.end_disabled()
            if reason and imgui.is_item_hovered(imgui.HoveredFlags_.allow_when_disabled):
                imgui.set_tooltip(reason)

        if changed:
            on_change(value)
            if value:
                on_enable()
            else:
                on_disable()


class RenderingUI:
    def __init__(self, pt_state, bvh_state, camera_buffer):
        self.pt_state = pt_state
        self.bvh_state = bvh_state
        self.camera_buffer = camera_buffer

        self.stop_button = Button("Stop")
        self.continue_button = Button("Continue")
        self.restart_button = Button("Restart")
        self.cancel_button = Button("Cancel")
        self.viewport_button = Button("Back to Viewport")
        self.start_button = Button("Start Render")
        self.start_new_button = Button("Start New Render")
        self.denoise_button = Button("Denoise")
        self.view_saved_button = Button("View Saved Render")

        self.reset_rendering_button = Button("Reset Rendering Settings")

        self.tiles_x_slider = IntSlider(1, 1024, "Tiles X", settings.rendering.tiles.x)
        self.tiles_y_slider = IntSlider(1, 1024, "Tiles Y", settings.rendering.tiles.y)
    
    def draw_stop_button(self):
        def on_change():
            self.pt_state.stop_render()
        
        self.stop_button.button(on_change)
    
    def draw_continue_button(self):
        def on_change():
            self.pt_state.continue_render()

        self.continue_button.button(on_change)
        
    def draw_restart_button(self):
        def on_change():
            self.pt_state.restart_render()

        self.restart_button.button(on_change)
    
    def draw_cancel_button(self):
        def on_change():
            settings.rendering.mode = "rasterization"
            self.pt_state.cancel_render()

        self.cancel_button.button(on_change)
    
    def draw_viewport_button(self):
        def on_change():
            settings.rendering.mode = "rasterization"
            self.pt_state.cancel_render()

        self.viewport_button.button(on_change)
    
    def draw_start_button(self):
        def on_change():
            settings.rendering.mode = "path_tracing"
            self.camera_buffer.update_data()
            self.pt_state.start_render()

        bvh_ready = self.bvh_state.ready

        self.start_button.button(on_change, enabled=bvh_ready, reason="BVH is still building...")
    
    def draw_start_new_button(self):
        def on_change():
            settings.rendering.mode = "path_tracing"
            self.camera_buffer.update_data()
            self.pt_state.start_render()

        self.start_new_button.button(on_change)
        
    def draw_denoise_button(self):
        def on_change():
            self.pt_state.denoising.should_denoise = True

        self.denoise_button.button(on_change)
    
    def draw_view_saved_button(self):
        def on_change():
            settings.rendering.mode = "path_tracing"
            self.pt_state.rendering.should_view_saved = True

        self.view_saved_button.button(on_change)
    
    def draw_tiles_x_slider(self):
        def on_change(new_val):
            settings.rendering.tiles.x = new_val
            self.pt_state.restart_render()
            
        self.tiles_x_slider.slider(settings.rendering.tiles.x)
        self.tiles_x_slider.dragging_logic(on_change)
        self.tiles_x_slider.minus_button(on_change)
        self.tiles_x_slider.plus_button(on_change)
        self.tiles_x_slider.draw_label()
    
    def draw_tiles_y_slider(self):
        def on_change(new_val):
            settings.rendering.tiles.y = new_val
            self.pt_state.restart_render()
            
        self.tiles_y_slider.slider(settings.rendering.tiles.y)
        self.tiles_y_slider.dragging_logic(on_change)
        self.tiles_y_slider.minus_button(on_change)
        self.tiles_y_slider.plus_button(on_change)
        self.tiles_y_slider.draw_label()
    
    def draw_export_render_button(self):
        if imgui.button("Export Render"):
            self.pt_state.export_render()

    def draw_reset_rendering_button(self):
        def on_change():
            settings.rendering.reset()
            self.pt_state.restart_render()

        self.reset_rendering_button.button(on_change)

class PathTracingUI:
    def __init__(self, pt_state):
        self.pt_state = pt_state

        self.total_bounces_slider = IntSlider(0, 1024, "Total Bounces")
        self.diffuse_bounces_slider = IntSlider(0, 1024, "Diffuse Bounces")
        self.specular_bounces_slider = IntSlider(0, 1024, "Specular Bounces")
        self.transmission_bounces_slider = IntSlider(0, 1024, "Transmission Bounces")
        self.max_samples_slider = IntSlider(1, 16384, "Max Samples")
        self.spp_slider = IntSlider(1, 128, "Samples Per Pixel")
        self.bvh_depth_slider = IntSlider(1, settings.bvh.max_depth, "BVH Depth")

        self.specular_cycle_button = CycleButton("Specular Mode")
        self.geometry_cycle_button = CycleButton("Geometry Mode")
        self.transmission_cycle_button = CycleButton("Transmission Mode")
        self.mis_cycle_button = CycleButton("Multiple Importance Sample")

        self.reset_pt_button = Button("Reset Path Tracing Settings")

        self.backface_culling_checkbox = Checkbox("Backface Culling")
    
    def draw_total_bounces_slider(self):
        def on_change(new_val):
            settings.path_tracing.total_bounces = new_val
            self.pt_state.restart_render()
        
        self.total_bounces_slider.slider(settings.path_tracing.total_bounces)
        self.total_bounces_slider.dragging_logic(on_change)
        self.total_bounces_slider.minus_button(on_change)
        self.total_bounces_slider.plus_button(on_change)
        self.total_bounces_slider.draw_label()

    def draw_diffuse_bounces_slider(self):
        def on_change(new_val):
            settings.path_tracing.diffuse_bounces = new_val
            self.pt_state.restart_render()
        
        self.diffuse_bounces_slider.slider(settings.path_tracing.diffuse_bounces)
        self.diffuse_bounces_slider.dragging_logic(on_change)
        self.diffuse_bounces_slider.minus_button(on_change)
        self.diffuse_bounces_slider.plus_button(on_change)
        self.diffuse_bounces_slider.draw_label()

    def draw_specular_bounces_slider(self):
        def on_change(new_val):
            settings.path_tracing.specular_bounces = new_val
            self.pt_state.restart_render()
        
        self.specular_bounces_slider.slider(settings.path_tracing.specular_bounces)
        self.specular_bounces_slider.dragging_logic(on_change)
        self.specular_bounces_slider.minus_button(on_change)
        self.specular_bounces_slider.plus_button(on_change)
        self.specular_bounces_slider.draw_label()

    def draw_transmission_bounces_slider(self):
        def on_change(new_val):
            settings.path_tracing.transmission_bounces = new_val
            self.pt_state.restart_render()
        
        self.transmission_bounces_slider.slider(settings.path_tracing.transmission_bounces)
        self.transmission_bounces_slider.dragging_logic(on_change)
        self.transmission_bounces_slider.minus_button(on_change)
        self.transmission_bounces_slider.plus_button(on_change)
        self.transmission_bounces_slider.draw_label()
        
    def draw_max_samples_slider(self):
        def on_change(new_val):
            settings.path_tracing.max_samples = new_val
            self.pt_state.restart_render()
        
        self.max_samples_slider.slider(settings.path_tracing.max_samples)
        self.max_samples_slider.dragging_logic(on_change)
        self.max_samples_slider.minus_button(on_change)
        self.max_samples_slider.plus_button(on_change)
        self.max_samples_slider.draw_label()
    
    def draw_spp_slider(self):
        def on_change(new_val):
            settings.path_tracing.spp = new_val
            self.pt_state.restart_render()
        
        self.spp_slider.slider(settings.path_tracing.spp)
        self.spp_slider.dragging_logic(on_change)
        self.spp_slider.minus_button(on_change)
        self.spp_slider.plus_button(on_change)
        self.spp_slider.draw_label()

    def draw_specular_cycle_button(self):
        specular_modes = ["GGX VNDF", "Cosine Hemisphere"]

        def on_change(next_val):
            settings.path_tracing.specular_mode = next_val
            self.pt_state.restart_render()

        self.specular_cycle_button.button(specular_modes, settings.path_tracing.specular_mode, on_change)

    def draw_geometry_cycle_button(self):
        geometry_modes = ["Height-Correlated Smith Method", "Schlick-GGX Approximation Method"]
        
        def on_change(next_val):
            settings.path_tracing.geometry_mode = next_val
            self.pt_state.restart_render()

        self.geometry_cycle_button.button(geometry_modes, settings.path_tracing.geometry_mode, on_change)
    
    def draw_transmission_cycle_button(self):
        transmissions_modes = ["Beer-Lambert", "None"]
        
        def on_change(next_val):
            settings.path_tracing.transmission_mode = next_val
            self.pt_state.restart_render()

        self.transmission_cycle_button.button(transmissions_modes, settings.path_tracing.transmission_mode, on_change)

    def draw_mis_cycle_button(self):
        mis_modes = ["On", "Off"]
        
        def on_change(next_val):
            settings.path_tracing.mis_mode = next_val
            self.pt_state.restart_render()

        self.mis_cycle_button.button(mis_modes, settings.path_tracing.mis_mode, on_change)

    def draw_bvh_depth_slider(self):
        def on_change(new_val):
            settings.bvh.max_depth = new_val
            self.pt_state.restart_render()
        
        self.bvh_depth_slider.slider(settings.bvh.max_depth)
        self.bvh_depth_slider.dragging_logic(on_change)
        self.bvh_depth_slider.minus_button(on_change)
        self.bvh_depth_slider.plus_button(on_change)
        self.bvh_depth_slider.draw_label()

    def draw_backface_culling_checkbox(self):
        def on_change(enabled):
            settings.path_tracing.backface_culling = enabled

        def on_enable():
            self.pt_state.restart_render()

        def on_disable():
            self.pt_state.restart_render()

        self.backface_culling_checkbox.checkbox(settings.path_tracing.backface_culling, on_change, on_enable, on_disable)

    def draw_reset_pt_button(self):
        def on_change():
            settings.path_tracing.reset()
            self.pt_state.restart_render()

        self.reset_pt_button.button(on_change)


class CameraUI:
    def __init__(self, pt_state, camera, camera_buffer):
        self.pt_state = pt_state
        self.camera = camera
        self.camera_buffer = camera_buffer

        self.reset_camera_button = Button("Reset Camera Settings")

        self.movement_speed_slider = FloatSlider(0, 10000, "Movement Speed", increment=1)
        self.fov_slider = FloatSlider(1, 135, "Field Of View", slider_speed=1)
        self.mouse_sensitivity_slider = FloatSlider(0.1, 10, "Mouse Sensitivity", slider_speed=0.1, increment=0.1)
        self.blur_slider = FloatSlider(0, 100, "Blur", increment=1)
        self.aperture_slider = FloatSlider(0, 1, "Aperture", slider_speed=0.01, increment=0.01)
        self.focus_dist_slider = FloatSlider(0.1, 1000, "Focus Distance", slider_speed=0.1, increment=0.1)

        self.pos_x_slider = FloatSlider(-10000, 10000, "X", slider_speed=0.1, increment=0.1)
        self.pos_y_slider = FloatSlider(-10000, 10000, "Y", slider_speed=0.1, increment=0.1)
        self.pos_z_slider = FloatSlider(-10000, 10000, "Z", slider_speed=0.1, increment=0.1)

        self.yaw_slider = FloatSlider(0, 360, "Yaw", slider_speed=0.1, increment=0.1, wrap=True)
        self.pitch_slider = FloatSlider(-89.99, 89.99, "Pitch", slider_speed=0.1, increment=0.1)

        self.dof_checkbox = Checkbox("Depth of Field")

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

    def draw_blur_slider(self):
        def on_change(new_val):
            self.camera.blur = new_val
            self.pt_state.restart_render()
        
        self.blur_slider.slider(self.camera.blur)
        self.blur_slider.dragging_logic(on_change)
        self.blur_slider.minus_button(on_change)
        self.blur_slider.plus_button(on_change)
        self.blur_slider.draw_label()
    
    def draw_dof_checkbox(self):
        def on_change(enabled):
            self.camera.dof_enabled = enabled
            self.pt_state.restart_render()

        def on_enable():
            self.camera.aperture = self.camera.aperture
            self.camera_buffer.update_data()
            self.pt_state.restart_render()

        def on_disable():
            self.camera.aperture = 0
            self.camera_buffer.update_data()
            self.pt_state.restart_render()

        self.dof_checkbox.checkbox(self.camera.dof_enabled, on_change, on_enable, on_disable)
        
    def draw_aperture_slider(self):
        if not self.camera.dof_enabled:
            return

        def on_change(new_val):
            self.camera.aperture = new_val
            self.camera.aperture = self.camera.aperture
            self.camera_buffer.update_data()
            self.pt_state.restart_render()
        
        self.aperture_slider.slider(self.camera.aperture, val_format="%.2f")
        self.aperture_slider.dragging_logic(on_change)
        self.aperture_slider.minus_button(on_change)
        self.aperture_slider.plus_button(on_change)
        self.aperture_slider.draw_label()
    
    def draw_focus_dist_slider(self):
        if not self.camera.dof_enabled:
            return

        def on_change(new_val):
            self.camera.focus_dist = new_val
            self.camera.focus_dist = self.camera.focus_dist
            self.camera_buffer.update_data()
            self.pt_state.restart_render()
        
        self.focus_dist_slider.slider(self.camera.focus_dist)
        self.focus_dist_slider.dragging_logic(on_change)
        self.focus_dist_slider.minus_button(on_change)
        self.focus_dist_slider.plus_button(on_change)
        self.focus_dist_slider.draw_label()

    def draw_pos_sliders(self):
        def on_change_x(new_val):
            self.camera.pos.x = new_val
            self.camera_buffer.update_data()
            self.pt_state.restart_render()

        def on_change_y(new_val):
            self.camera.pos.y = new_val
            self.camera_buffer.update_data()
            self.pt_state.restart_render()

        def on_change_z(new_val):
            self.camera.pos.z = new_val
            self.camera_buffer.update_data()
            self.pt_state.restart_render()

        avail_width = imgui.get_content_region_avail().x
        slot_width = avail_width / 5

        imgui.text("Pos:")

        # X
        imgui.same_line()
        self.pos_x_slider.draw_label()
        imgui.same_line()
        self.pos_x_slider.slider(self.camera.pos.x, val_format="%.3f", width=slot_width)
        self.pos_x_slider.dragging_logic(on_change_x)

        # Y
        imgui.same_line()
        self.pos_y_slider.draw_label()
        imgui.same_line()
        self.pos_y_slider.slider(self.camera.pos.y, val_format="%.3f", width=slot_width)
        self.pos_y_slider.dragging_logic(on_change_y)

        # Z
        imgui.same_line()
        self.pos_z_slider.draw_label()
        imgui.same_line()
        self.pos_z_slider.slider(self.camera.pos.z, val_format="%.3f", width=slot_width)
        self.pos_z_slider.dragging_logic(on_change_z)

    def draw_yaw_pitch_sliders(self):
        def on_change_yaw(new_val):
            self.camera.set_orientation(yaw=new_val)
            self.camera_buffer.update_data()
            self.pt_state.restart_render()

        def on_change_pitch(new_val):
            self.camera.set_orientation(pitch=new_val)
            self.camera_buffer.update_data()
            self.pt_state.restart_render()

        avail_width = imgui.get_content_region_avail().x
        slot_width = avail_width / 3

        # Create new line since draw_label() doesn't create one
        imgui.new_line()

        # Yaw
        self.yaw_slider.draw_label()
        imgui.same_line()
        self.yaw_slider.slider(self.camera.yaw, val_format="%.1f", width=slot_width)
        self.yaw_slider.dragging_logic(on_change_yaw)

        # Pitch
        imgui.same_line()
        self.pitch_slider.draw_label()
        imgui.same_line()
        self.pitch_slider.slider(self.camera.pitch, val_format="%.1f", width=slot_width)
        self.pitch_slider.dragging_logic(on_change_pitch)

    def draw_reset_camera_button(self):
        def on_change():
            settings.camera.reset()
            self.camera.reload_from_settings()
            self.camera_buffer.update_data()
            self.pt_state.restart_render()

        self.reset_camera_button.button(on_change)


class PostProcessingUI:
    def __init__(self, pt_state):
        self.pt_state = pt_state
        self.window = glfwGetCurrentContext()

        self.reset_post_process_button = Button("Reset Post Processing Settings")

        self.exposure_slider = FloatSlider(0, 10, "Exposure", slider_speed=0.1, increment=0.1)
        self.hdri_exposure_slider = FloatSlider(0, 10, "HDRI Exposure", slider_speed=0.1, increment=0.1)
        
        self.tonemap_dropdown = Dropdown("Render Mode")

    def draw_tonemap_dropdown(self):
        options = ["None", "ACESFilm", "AgX", "AgXGolden", "AgXPunchy", "Filmic", "Lottes",
                   "Neutral", "Reinhard", "Reinhard2", "Uchimura", "Uncharted2", "Unreal"]

        def on_change(new_val):
            settings.post_processing.tonemap = new_val
            self.pt_state.restart_render()

        self.tonemap_dropdown.dropdown(options, settings.post_processing.tonemap, on_change)
        
    def draw_exposure_slider(self):
        def on_change(new_val):
            settings.post_processing.exposure = new_val
            self.pt_state.restart_render()
        
        self.exposure_slider.slider(settings.post_processing.exposure)
        self.exposure_slider.dragging_logic(on_change)
        self.exposure_slider.minus_button(on_change)
        self.exposure_slider.plus_button(on_change)
        self.exposure_slider.draw_label()
    
    def draw_hdri_exposure_slider(self):
        def on_change(new_val):
            settings.post_processing.hdri_exposure = new_val
            self.pt_state.restart_render()
        
        self.hdri_exposure_slider.slider(settings.post_processing.hdri_exposure)
        self.hdri_exposure_slider.dragging_logic(on_change)
        self.hdri_exposure_slider.minus_button(on_change)
        self.hdri_exposure_slider.plus_button(on_change)
        self.hdri_exposure_slider.draw_label()

    def draw_reset_post_process_button(self):
        def on_change():
            settings.post_processing.reset()
            self.pt_state.restart_render()

        self.reset_post_process_button.button(on_change)


class ScreenUI:
    def __init__(self, pt_state):
        self.pt_state = pt_state

        self.reset_screen_button = Button("Reset Screen Settings")

        self.vsync_checkbox = Checkbox("VSync")

        self.fps_slider = IntSlider(30, 361, "FPS", slider_speed=1)

        self.window_resize_width_slider = IntSlider(settings.screen.min_width, 999999, "Width")
        self.window_resize_height_slider = IntSlider(settings.screen.min_height, 999999, "Height")
    
    def draw_vsync_checkbox(self):
        def on_change(enabled):
            settings.screen.vsync = enabled

        def on_enable():
            glfwSwapInterval(1)

        def on_disable():
            glfwSwapInterval(0)
        
        enabled = settings.screen.vsync

        self.vsync_checkbox.checkbox(enabled, on_change, on_enable, on_disable)
    
    def draw_fps_slider(self):
        is_unlimited = settings.screen.fps_cap == -1
        display_fps = 361 if is_unlimited else settings.screen.fps_cap
        fps_format = "None" if is_unlimited else "%d"
        
        def on_change(new_val):
            settings.screen.fps_cap = -1 if new_val > 360 else new_val

        self.fps_slider.slider(display_fps, val_format=fps_format)
        self.fps_slider.dragging_logic(on_change)
        self.fps_slider.minus_button(on_change)
        self.fps_slider.plus_button(on_change)
        self.fps_slider.draw_label()

    def draw_window_resize_sliders(self):
        current_window = glfwGetCurrentContext()

        def on_change_width(new_val):
            glfwSetWindowSize(current_window, new_val, settings.screen.height)
            self.pt_state.restart_render()

        def on_change_height(new_val):
            glfwSetWindowSize(current_window, settings.screen.width, new_val)
            self.pt_state.restart_render()

        avail_width = imgui.get_content_region_avail().x
        slot_width = avail_width / 3

        # Create new line since draw_label() doesn't create one
        imgui.new_line()

        # Width
        self.window_resize_width_slider.draw_label()
        imgui.same_line()
        self.window_resize_width_slider.slider(settings.screen.width, width=slot_width)
        self.window_resize_width_slider.dragging_logic(on_change_width)

        # Height
        imgui.same_line()
        self.window_resize_height_slider.draw_label()
        imgui.same_line()
        self.window_resize_height_slider.slider(settings.screen.height, width=slot_width)
        self.window_resize_height_slider.dragging_logic(on_change_height)

    def draw_reset_screen_button(self):
        def on_change():
            settings.screen.reset()
            self.pt_state.restart_render()

        self.reset_screen_button.button(on_change)
    

class DebugUI:
    def __init__(self, scene, pt_state):
        self.scene = scene
        self.pt_state = pt_state

        self.reset_debug_button = Button("Reset Debug Settings ")

        self.debug_off_button = Dropdown("Debug Mode")

        self.bvh_color_mode_cycle_button = CycleButton("BVH Color Mode")

        self.bvh_view_layer_slider = IntSlider(-1, self._get_max_idx(), "View Layer")
        self.bvh_view_depth_slider = IntSlider(-1, self._get_max_idx(), "View Depth")

        self.max_direct_luminance_slider = FloatSlider(0, 1000, "Max Direct Luminance", slider_speed=0.1, increment=0.1)
        self.max_indirect_luminance_slider = FloatSlider(0, 1000, "Max Indirect Luminance", slider_speed=0.1, increment=0.1)

    def _get_max_idx(self):
        """
        BVH is initiated as a NoneType object,
        so calling bvh.max_depth returns an error.
        Use -1 as a placeholder.
        """

        bvh = self.scene.bvh
        if bvh is None:
            return -1
        return max(bvh.max_depth - 1, -1)
    
    def draw_debug_mode_dropdown(self):
        options = [
            "Off", # 0
            "Albedo", # 1
            "Normal", # 2
            "Depth", # 3
            "Direct", # 4
            "Indirect", # 5
            "BVH Depth", # 6
            "BVH Bounds", # 7
        ]

        def on_change(new_val):
            self.pt_state.debug.mode = options.index(new_val)
            self.pt_state.restart_render()

        self.debug_off_button.dropdown(options, options[self.pt_state.debug.mode], on_change)

    def draw_bvh_color_mode_cycle_button(self):
        options = [
            "Depth-Based",
            "Node-Based"
        ]

        def on_change(new_val):
            settings.debug.bvh.color_mode = new_val
            self.pt_state.restart_render()

        bvh_ready = self.scene.bvh is not None

        self.bvh_color_mode_cycle_button.button(options, settings.debug.bvh.color_mode, on_change, enabled=bvh_ready, reason="BVH is still building...")

    def _clamp_to_scene_max_depth(self):
        # Clamps view layer/view depth back into range
        # whenever the actual scene BVH depth shrinks

        max_idx = self._get_max_idx()

        # Clamp view depth to the scene's max depth
        if settings.debug.bvh.view_depth != -1 and settings.debug.bvh.view_depth > max_idx:
            settings.debug.bvh.view_depth = max_idx

        # Clamp view layer to the current view depth
        if settings.debug.bvh.view_depth != -1 and settings.debug.bvh.view_layer > settings.debug.bvh.view_depth:
            settings.debug.bvh.view_layer = settings.debug.bvh.view_depth

        # Clamp view layer to the scene's max depth
        if settings.debug.bvh.view_layer > max_idx:
            settings.debug.bvh.view_layer = max_idx

    def draw_bvh_view_layer_slider(self):
        self.bvh_view_layer_slider.max_val = self._get_max_idx()
        self._clamp_to_scene_max_depth()

        is_all = settings.debug.bvh.view_layer == -1
        display_layer = -1 if is_all else settings.debug.bvh.view_layer
        layer_format = "All" if is_all else "%d"

        def on_change(new_val):
            settings.debug.bvh.view_layer = -1 if new_val < 0 else new_val

        bvh_ready = self.scene.bvh is not None

        self.bvh_view_layer_slider.slider(display_layer, val_format=layer_format, enabled=bvh_ready, reason="BVH is still building...")
        self.bvh_view_layer_slider.dragging_logic(on_change)
        self.bvh_view_layer_slider.minus_button(on_change)
        self.bvh_view_layer_slider.plus_button(on_change)
        self.bvh_view_layer_slider.draw_label()

    def draw_bvh_view_depth_slider(self):
        self.bvh_view_depth_slider.max_val = self._get_max_idx()
        self._clamp_to_scene_max_depth()

        is_max = settings.debug.bvh.view_depth == -1
        display_depth = -1 if is_max else settings.debug.bvh.view_depth
        depth_format = "Max" if is_max else "%d"

        def on_change(new_val):
            settings.debug.bvh.view_depth = -1 if new_val < 0 else new_val
            self._clamp_to_scene_max_depth()

        bvh_ready = self.scene.bvh is not None
        
        self.bvh_view_depth_slider.slider(display_depth, val_format=depth_format, enabled=bvh_ready, reason="BVH is still building...")
        self.bvh_view_depth_slider.dragging_logic(on_change)
        self.bvh_view_depth_slider.minus_button(on_change)
        self.bvh_view_depth_slider.plus_button(on_change)
        self.bvh_view_depth_slider.draw_label()

    def draw_max_direct_luminance_slider(self):
        def on_change(new_val):
            settings.path_tracing.max_direct_luminance = new_val
            self.pt_state.restart_render()

        self.max_direct_luminance_slider.slider(settings.path_tracing.max_direct_luminance)
        self.max_direct_luminance_slider.dragging_logic(on_change)
        self.max_direct_luminance_slider.minus_button(on_change)
        self.max_direct_luminance_slider.plus_button(on_change)
        self.max_direct_luminance_slider.draw_label()

    def draw_max_indirect_luminance_slider(self):
        def on_change(new_val):
            settings.path_tracing.max_indirect_luminance = new_val
            self.pt_state.restart_render()

        self.max_indirect_luminance_slider.slider(settings.path_tracing.max_indirect_luminance)
        self.max_indirect_luminance_slider.dragging_logic(on_change)
        self.max_indirect_luminance_slider.minus_button(on_change)
        self.max_indirect_luminance_slider.plus_button(on_change)
        self.max_indirect_luminance_slider.draw_label()

    def draw_reset_debug_button(self):
        def on_change():
            settings.debug.reset()
            self.bvh_view_depth_slider.max_val = self._get_max_idx()
            self._clamp_to_scene_max_depth()

        self.reset_debug_button.button(on_change)


class SceneUI:
    def __init__(self, scene_state):
        self.scene_state = scene_state

        self.next_scene_button = Button("Next Scene")
        self.previous_scene_button = Button("Previous Scene")
    
    def draw_next_scene_button(self):
        enabled = self.scene_state.curr_scene_idx < self.scene_state.num_scenes - 1

        def on_change():
            self.scene_state.next_scene()

        self.next_scene_button.button(on_change, enabled, reason="Already at the last scene")
    
    def draw_previous_scene_button(self):
        enabled = self.scene_state.curr_scene_idx > 0

        def on_change():
            self.scene_state.previous_scene()
        
        self.previous_scene_button.button(on_change, enabled, reason="Already at the first scene")


class CameraCapturingUI:
    def __init__(self, pt_state, scene_state, camera_capture_state):
        self.pt_state = pt_state
        self.scene_state = scene_state
        self.camera_capture_state = camera_capture_state

        self.save_state_button = Button("Save Current Camera State")
        self.delete_current_button = Button("Delete Current Capture")
        self.view_current_button = Button("View Current Capture")
        self.previous_button = Button("< Previous")
        self.next_button = Button("Next >")
    
    def draw_save_state_button(self):
        def on_change():
            self.camera_capture_state.save_state()
            self.pt_state.restart_render()

        self.save_state_button.button(on_change)

    def draw_delete_current_button(self):
        def on_change():
            self.camera_capture_state.delete_current()
            self.pt_state.restart_render()

        self.delete_current_button.button(on_change)

    def draw_view_current_button(self):
        def on_change():
            self.camera_capture_state.view_current()
            self.pt_state.restart_render()

        self.view_current_button.button(on_change)

    def draw_browse_controls(self):
        captures = self.camera_capture_state._get_scene_captures()

        if len(captures) == 0:
            imgui.text_disabled("No captures for this scene yet")
            return

        imgui.text(f"Capture {self.camera_capture_state.browse_idx + 1} / {len(captures)}")

        def on_prev():
            self.camera_capture_state.previous_capture()
            self.pt_state.restart_render()

        def on_next():
            self.camera_capture_state.next_capture()
            self.pt_state.restart_render()

        self.previous_button.button(on_prev)
        self.next_button.button(on_next)


class ExportUI:
    def __init__(self, export_state):
        self.export_state = export_state

        self.export_button = Button("Export")

    def draw_export_button(self):
        def on_change():
            self.export_state.export_render()

        self.export_button.button(on_change)


class SettingsUI:
    def __init__(self,
            scene,
            pt_state,
            scene_state,
            camera_capture_state,
            export_state,
            bvh_state,
            camera_buffer,
            camera
        ):

        self.pt_state = pt_state
        self.scene_state = scene_state
        self.camera_capture_state = camera_capture_state
        self.export_state = export_state
        self.bvh_state = bvh_state
        self.camera_buffer = camera_buffer
        self.camera = camera

        self.rendering_ui = RenderingUI(pt_state, bvh_state, camera_buffer)
        self.path_tracing_ui = PathTracingUI(pt_state)
        self.camera_ui = CameraUI(pt_state, camera, camera_buffer)
        self.post_processing_ui = PostProcessingUI(pt_state)
        self.screen_ui = ScreenUI(pt_state)
        self.debug_ui = DebugUI(scene, pt_state)
        self.scene_ui = SceneUI(scene_state)
        self.camera_capturing_ui = CameraCapturingUI(pt_state, scene_state, camera_capture_state)
        self.export_ui = ExportUI(export_state)

    def draw_rendering_ui(self,
            allow_start=True,
            allow_cancel=True,
            allow_viewport=True,
            allow_denoise=True,
            allow_view_saved=True
        ):

        if settings.rendering.mode == "path_tracing":
            if not self.pt_state.rendering.should_view_saved:
                if self.pt_state.rendering.should_render:
                    self.rendering_ui.draw_stop_button()
                
                else:
                    self.rendering_ui.draw_continue_button()

                if allow_cancel: self.rendering_ui.draw_cancel_button()
            
            else:
                if allow_viewport: self.rendering_ui.draw_viewport_button()
                if allow_denoise: self.rendering_ui.draw_denoise_button()

            self.rendering_ui.draw_restart_button()
        
        else:
            if self.pt_state.framebuffers.saved_combined is None:
                if allow_start: self.rendering_ui.draw_start_button()
            
            else:
                if allow_start: self.rendering_ui.draw_start_new_button()
                if allow_view_saved: self.rendering_ui.draw_view_saved_button()

        self.rendering_ui.draw_tiles_x_slider()
        self.rendering_ui.draw_tiles_y_slider()

        self.rendering_ui.draw_reset_rendering_button()

    def draw_path_tracing_ui(self, allow_modes=True):
        self.path_tracing_ui.draw_total_bounces_slider()
        self.path_tracing_ui.draw_diffuse_bounces_slider()
        self.path_tracing_ui.draw_specular_bounces_slider()
        self.path_tracing_ui.draw_transmission_bounces_slider()
        self.path_tracing_ui.draw_max_samples_slider()
        self.path_tracing_ui.draw_spp_slider()
        self.path_tracing_ui.draw_bvh_depth_slider()
        self.path_tracing_ui.draw_backface_culling_checkbox()

        if allow_modes:
            if imgui.tree_node("BSDF Sampling"):
                self.path_tracing_ui.draw_specular_cycle_button()
                self.path_tracing_ui.draw_geometry_cycle_button()
                self.path_tracing_ui.draw_transmission_cycle_button()
                self.path_tracing_ui.draw_mis_cycle_button()

                imgui.tree_pop()

        self.path_tracing_ui.draw_reset_pt_button()
    
    def draw_camera_ui(self):
        self.camera_ui.draw_movement_speed_slider()
        self.camera_ui.draw_fov_slider()
        self.camera_ui.draw_mouse_sensitivity_slider()
        self.camera_ui.draw_blur_slider()
        self.camera_ui.draw_dof_checkbox()
        self.camera_ui.draw_aperture_slider()
        self.camera_ui.draw_focus_dist_slider()

        if imgui.tree_node("More"):
            self.camera_ui.draw_pos_sliders()
            self.camera_ui.draw_yaw_pitch_sliders()

            imgui.tree_pop()

        self.camera_ui.draw_reset_camera_button()
    
    def draw_post_processing_ui(self):
        self.post_processing_ui.draw_exposure_slider()
        self.post_processing_ui.draw_hdri_exposure_slider()
        self.post_processing_ui.draw_tonemap_dropdown()

        self.post_processing_ui.draw_reset_post_process_button()
    
    def draw_screen_ui(self):
        self.screen_ui.draw_vsync_checkbox()
        self.screen_ui.draw_fps_slider()

        if imgui.tree_node("More"):
            self.screen_ui.draw_window_resize_sliders()

            imgui.tree_pop()

        self.screen_ui.draw_reset_screen_button()
    
    def draw_debug_ui(self):
        self.debug_ui.draw_debug_mode_dropdown()

        # BVH Bounds
        if self.pt_state.debug.mode == 7:
            if self.debug_ui.scene.bvh is None:
                imgui.text_disabled("BVH is still building...")
            else:
                self.debug_ui.draw_bvh_color_mode_cycle_button()
                self.debug_ui.draw_bvh_view_layer_slider()
                self.debug_ui.draw_bvh_view_depth_slider()

        self.debug_ui.draw_max_direct_luminance_slider()
        self.debug_ui.draw_max_indirect_luminance_slider()

        self.debug_ui.draw_reset_debug_button()
    
    def draw_scene_ui(self):
        self.scene_ui.draw_next_scene_button()
        self.scene_ui.draw_previous_scene_button()
    
    def draw_camera_capturing_ui(self):
        self.camera_capturing_ui.draw_save_state_button()
        self.camera_capturing_ui.draw_delete_current_button()
        self.camera_capturing_ui.draw_view_current_button()
        self.camera_capturing_ui.draw_browse_controls()

    def draw_export_ui(self):
        self.export_ui.draw_export_button()

    def draw_ai_training_ui(self):
        self.draw_scene_ui()
        self.draw_camera_capturing_ui()

    def draw(self, settings_window):
        if not settings_window:
            return settings_window

        imgui.set_next_window_size((600, 600))
        is_expand, settings_window = imgui.begin("Settings", settings_window)

        # Render Mode
        # -----------
        if settings.ai_training.mode == 0:
            if is_expand:
                if imgui.tree_node("Rendering"):
                    self.draw_rendering_ui(
                        allow_cancel=False,
                        allow_view_saved=False,
                        allow_viewport=False,
                        allow_denoise=False,
                        allow_start=False
                    )

                    imgui.tree_pop()
                
                if imgui.tree_node("Path Tracing"):
                    self.draw_path_tracing_ui(allow_modes=False)
                        
                    imgui.tree_pop()
                
                if imgui.tree_node("Post Processing"):
                    self.draw_post_processing_ui()

                    imgui.tree_pop()
                
                if imgui.tree_node("Screen"):
                    self.draw_screen_ui()

                    imgui.tree_pop()

                if imgui.tree_node("AI Training"):
                    self.draw_ai_training_ui()

                    imgui.tree_pop()

        # Camera Setup Mode
        # -----------------
        elif settings.ai_training.mode == 1:
            if is_expand:
                if imgui.tree_node("Rendering"):
                    self.draw_rendering_ui()

                    imgui.tree_pop()
                
                if imgui.tree_node("Camera UI"):
                    self.draw_camera_ui()

                    imgui.tree_pop()
                
                if imgui.tree_node("Post Processing"):
                    self.draw_post_processing_ui()

                    imgui.tree_pop()
                
                if imgui.tree_node("Screen"):
                    self.draw_screen_ui()

                    imgui.tree_pop()
                    
                if imgui.tree_node("AI Training"):
                    self.draw_ai_training_ui()

                    imgui.tree_pop()

        else:
            if is_expand:
                if imgui.tree_node("Rendering"):
                    self.draw_rendering_ui()

                    imgui.tree_pop()
                
                if imgui.tree_node("Path Tracing"):
                    self.draw_path_tracing_ui()
                        
                    imgui.tree_pop()
                
                if imgui.tree_node("Camera UI"):
                    self.draw_camera_ui()

                    imgui.tree_pop()
                
                if imgui.tree_node("Post Processing"):
                    self.draw_post_processing_ui()

                    imgui.tree_pop()
                
                if imgui.tree_node("Screen"):
                    self.draw_screen_ui()

                    imgui.tree_pop()
                
                if imgui.tree_node("Debug"):
                    self.draw_debug_ui()

                    imgui.tree_pop()

                if imgui.tree_node("Export"):
                    self.draw_export_ui()

                    imgui.tree_pop()
        
        imgui.end()

        return settings_window
    