from imgui_bundle import imgui
from glfw.GLFW import *
from src.settings import *


class IntSlider:
    def __init__(self, min_val, max_val, label, slider_speed=0.5, increment=1):
        self.window = glfwGetCurrentContext()
        self.slider_speed = slider_speed
        self.increment = increment
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
    def __init__(self, min_val, max_val, label, slider_speed=0.5, increment=0.5):
        self.window = glfwGetCurrentContext()
        self.slider_speed = slider_speed
        self.increment = increment
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

    def button(self, on_change, enabled=True):
        if enabled:
            if imgui.button(self.label):
                on_change()
        else:
            imgui.begin_disabled()

            imgui.button(self.label)

            imgui.end_disabled()


class CycleButton:
    def __init__(self, label):
        self.label = label

    def button(self, options, curr_idx, on_change):
        if imgui.button(f"{self.label}: {options[curr_idx]}"):
            curr_idx = (curr_idx + 1) % len(options)

            on_change(curr_idx)


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


class Checkbox:
    def __init__(self, label):
        self.label = label

    def checkbox(self, already_enabled, on_change, on_enable, on_disable):
        changed, enabled = imgui.checkbox(self.label, already_enabled)
        if changed:
            on_change(enabled)
            if enabled:
                on_enable()
            else:
                on_disable()


class RenderingUI:
    def __init__(self, pt_state, camera_buffer):
        self.pt_state = pt_state
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

        self.tiles_x_slider = IntSlider(1, 1024, "Tiles X", render_settings.tiles_x)
        self.tiles_y_slider = IntSlider(1, 1024, "Tiles Y", render_settings.tiles_y)
    
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
            render_settings.render_mode = "rasterization"
            self.pt_state.cancel_render()

        self.cancel_button.button(on_change)
    
    def draw_viewport_button(self):
        def on_change():
            render_settings.render_mode = "rasterization"
            self.pt_state.cancel_render()

        self.viewport_button.button(on_change)
    
    def draw_start_button(self):
        def on_change():
            render_settings.render_mode = "path_tracing"
            self.camera_buffer.update_data()
            self.pt_state.start_render()

        self.start_button.button(on_change)
    
    def draw_start_new_button(self):
        def on_change():
            render_settings.render_mode = "path_tracing"
            self.camera_buffer.update_data()
            self.pt_state.start_render()

        self.start_new_button.button(on_change)
        
    def draw_denoise_button(self):
        def on_change():
            self.pt_state.denoising.should_denoise = True

        self.denoise_button.button(on_change)
    
    def draw_view_saved_button(self):
        def on_change():
            render_settings.render_mode = "path_tracing"
            self.pt_state.rendering.should_view_saved = True

        self.view_saved_button.button(on_change)
    
    def draw_tiles_x_slider(self):
        def on_change(new_val):
            render_settings.tiles_x = new_val
            self.pt_state.restart_render()
            
        self.tiles_x_slider.slider(render_settings.tiles_x)
        self.tiles_x_slider.dragging_logic(on_change)
        self.tiles_x_slider.minus_button(on_change)
        self.tiles_x_slider.plus_button(on_change)
        self.tiles_x_slider.draw_label()
    
    def draw_tiles_y_slider(self):
        def on_change(new_val):
            render_settings.tiles_y = new_val
            self.pt_state.restart_render()
            
        self.tiles_y_slider.slider(render_settings.tiles_y)
        self.tiles_y_slider.dragging_logic(on_change)
        self.tiles_y_slider.minus_button(on_change)
        self.tiles_y_slider.plus_button(on_change)
        self.tiles_y_slider.draw_label()
    
    def draw_export_render_button(self):
        if imgui.button("Export Render"):
            self.pt_state.export_render()


class PathTracingUI:
    def __init__(self, pt_state):
        self.pt_state = pt_state

        self.total_bounces_slider = IntSlider(0, 1024, "Total Bounces")
        self.diffuse_bounces_slider = IntSlider(0, 1024, "Diffuse Bounces")
        self.specular_bounces_slider = IntSlider(0, 1024, "Specular Bounces")
        self.transmission_bounces_slider = IntSlider(0, 1024, "Transmission Bounces")
        self.max_samples_slider = IntSlider(1, 16384, "Max Samples")
        self.spp_slider = IntSlider(1, 128, "Samples Per Pixel")

        self.specular_cycle_button = CycleButton("Specular Mode")
        self.geometry_cycle_button = CycleButton("Geometry Mode")
        self.transmission_cycle_button = CycleButton("Transmission Mode")
        self.mis_cycle_button = CycleButton("Multiple Importance Sample")
    
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

    def draw_specular_cycle_button(self):
        specular_modes = ["GGX VNDF", "Cosine Hemisphere"]

        def on_change(next_val):
            pt_settings.specular_mode = next_val
            self.pt_state.restart_render()

        self.specular_cycle_button.button(specular_modes, pt_settings.specular_mode, on_change)

    def draw_geometry_cycle_button(self):
        geometry_modes = ["Height-Correlated Smith Method", "Schlick-GGX Approximation Method"]
        
        def on_change(next_val):
            pt_settings.geometry_mode = next_val
            self.pt_state.restart_render()

        self.geometry_cycle_button.button(geometry_modes, pt_settings.geometry_mode, on_change)
    
    def draw_transmission_cycle_button(self):
        transmissions_modes = ["Beer-Lambert", "None"]
        
        def on_change(next_val):
            pt_settings.transmission_mode = next_val
            self.pt_state.restart_render()

        self.transmission_cycle_button.button(transmissions_modes, pt_settings.transmission_mode, on_change)

    def draw_mis_cycle_button(self):
        mis_modes = ["On", "Off"]
        
        def on_change(next_val):
            pt_settings.mis_mode = next_val
            self.pt_state.restart_render()

        self.mis_cycle_button.button(mis_modes, pt_settings.mis_mode, on_change)
    
    def draw_reset_pt_button(self):
        if imgui.button("Reset Path Tracing Settings"):
            pt_settings.reset()
            self.pt_state.restart_render()


class CameraUI:
    def __init__(self, pt_state, camera, camera_buffer):
        self.pt_state = pt_state
        self.camera = camera
        self.camera_buffer = camera_buffer

        self.movement_speed_slider = FloatSlider(0, 10000, "Movement Speed", increment=1)
        self.fov_slider = FloatSlider(1, 135, "Field Of View", slider_speed=1)
        self.mouse_sensitivity_slider = FloatSlider(0.1, 10, "Mouse Sensitivity", slider_speed=0.1, increment=0.1)
        self.blur_slider = FloatSlider(0, 100, "Blur", increment=1)
        self.aperture_slider = FloatSlider(0, 1, "Aperture", slider_speed=0.01, increment=0.01)
        self.focus_dist_slider = FloatSlider(0.1, 1000, "Focus Distance", slider_speed=0.1, increment=0.1)

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


class PostProcessingUI:
    def __init__(self, pt_state):
        self.pt_state = pt_state
        self.window = glfwGetCurrentContext()

        self.exposure_slider = FloatSlider(0, 10, "Exposure", slider_speed=0.1, increment=0.1)
        self.hdri_exposure_slider = FloatSlider(0, 10, "HDRI Exposure", slider_speed=0.1, increment=0.1)
        
        self.tonemap_dropdown = Dropdown("Render Mode")

    def draw_tonemap_dropdown(self):
        options = ["None", "ACESFilm", "AgX", "AgXGolden", "AgXPunchy", "Filmic", "Lottes",
                   "Neutral", "Reinhard", "Reinhard2", "Uchimura", "Uncharted2", "Unreal"]

        def on_change(new_val):
            post_process_settings.tonemap = new_val
            self.pt_state.restart_render()

        self.tonemap_dropdown.dropdown(options, post_process_settings.tonemap, on_change)
        
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


class ScreenUI:
    def __init__(self, pt_state):
        self.pt_state = pt_state

        self.fps_slider = IntSlider(30, 361, "FPS", slider_speed=1)

        self.vsync_checkbox = Checkbox("VSync")
    
    def draw_vsync_checkbox(self):
        def on_change(enabled):
            screen.vsync = enabled

        def on_enable():
            glfwSwapInterval(1)

        def on_disable():
            glfwSwapInterval(0)
        
        enabled = screen.vsync

        self.vsync_checkbox.checkbox(enabled, on_change, on_enable, on_disable)
    
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
    

# Currently broken
class DebugUI:
    def __init__(self, pt_state):
        self.pt_state = pt_state

        self.debug_off_button = CycleButton("Debug Mode")
    
    def draw_debug_mode_button(self):
        options = [
            "Off",      # 0
            "Albedo",   # 1
            "Normal",   # 2
            "Depth",    # 3
            "Direct",   # 4
            "Indirect", # 5
        ]

        def on_change(new_val):
            self.pt_state.debug.mode = new_val
            self.pt_state.restart_render()

        self.debug_off_button.button(options, self.pt_state.debug.mode, on_change)


class SceneUI:
    def __init__(self, scene_state):
        self.scene_state = scene_state

        self.next_scene_button = Button("Next Scene")
        self.previous_scene_button = Button("Previous Scene")
    
    def draw_next_scene_button(self):
        enabled = self.scene_state.curr_scene_idx < self.scene_state.num_scenes - 1

        def on_change():
            self.scene_state.next_scene()

        self.next_scene_button.button(on_change, enabled)
    
    def draw_previous_scene_button(self):
        enabled = self.scene_state.curr_scene_idx > 0

        def on_change():
            self.scene_state.previous_scene()
        
        self.previous_scene_button.button(on_change, enabled)


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

        self.rendering_ui = RenderingUI(pt_state, camera_buffer)
        self.path_tracing_ui = PathTracingUI(pt_state)
        self.camera_ui = CameraUI(pt_state, camera, camera_buffer)
        self.post_processing_ui = PostProcessingUI(pt_state)
        self.screen_ui = ScreenUI(pt_state)
        self.debug_ui = DebugUI(pt_state)
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

        if not self.bvh_state.ready:
            imgui.text_disabled("Path tracing is disabled while the BVH is building...")
            return

        if render_settings.render_mode == "path_tracing":
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

    def draw_path_tracing_ui(self, allow_modes=True):
        self.path_tracing_ui.draw_total_bounces_slider()
        self.path_tracing_ui.draw_diffuse_bounces_slider()
        self.path_tracing_ui.draw_specular_bounces_slider()
        self.path_tracing_ui.draw_transmission_bounces_slider()
        self.path_tracing_ui.draw_max_samples_slider()
        self.path_tracing_ui.draw_spp_slider()

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
    
    def draw_post_processing_ui(self):
        self.post_processing_ui.draw_exposure_slider()
        self.post_processing_ui.draw_hdri_exposure_slider()
        self.post_processing_ui.draw_tonemap_dropdown()
    
    def draw_screen_ui(self):
        self.screen_ui.draw_vsync_checkbox()
        self.screen_ui.draw_fps_slider()
    
    def draw_debug_ui(self):
        self.debug_ui.draw_debug_mode_button()
    
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

        if ai_training_settings.camera_setup_mode:
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

        elif ai_training_settings.ai_training_mode:
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
