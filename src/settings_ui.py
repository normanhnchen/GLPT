from imgui_bundle import imgui


class RenderingUI:
    def __init__(self, pt_state, render_settings, camera_buffer):
        self.pt_state = pt_state
        self.render_settings = render_settings
        self.camera_buffer = camera_buffer
    
    def stop_button(self):
            if imgui.button("Stop"):
                self.pt_state.view_saved = False
                self.pt_state.should_render = False
    
    def continue_button(self):
        if imgui.button("Continue"):
            self.pt_state.view_saved = False
            self.pt_state.should_render = True
    
    def cancel_button(self):
        if imgui.button("Cancel"):
            self.render_settings.render_mode = "rasterization"
            self.pt_state.view_saved = False
    
    def viewport_button(self):
        if imgui.button("Back to Viewport"):
            self.render_settings.render_mode = "rasterization"
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
            self.render_settings.render_mode = "path_tracing"
            self.pt_state.view_saved = True


class SettingsUI(RenderingUI):
    def __init__(self, pt_state, render_settings, camera_buffer):
        super().__init__(pt_state, render_settings, camera_buffer)

        self.is_expand = None
        self.settings_window = None
    
    def set_window(self, width, height):
        imgui.set_next_window_size((width, height))

    def begin(self, name):
        self.is_expand, self.settings_window = imgui.begin(name, True)

    def rendering_ui(self):
        if self.render_settings.render_mode == "path_tracing":
            if not self.pt_state.view_saved:
                if self.pt_state.should_render:
                    self.stop_button()
                
                else:
                    self.continue_button()
                
                self.cancel_button()
            
            else:
                self.viewport_button()
        
        else:
            if self.pt_state.saved_render is None:
                self.start_button()
            
            else:
                self.start_new_button()
                self.view_saved_button()
