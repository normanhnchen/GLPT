import numpy as np
from glfw.GLFW import *
import moderngl
import sys
import time
import pickle
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

from src.settings import *
from src.dtypes import *
from src.shader import *
from src.camera import *
from src.model import *
from src.render_state import *
from src.buffers import *
from src.draw_passes import *
from src.bvh_builder import *
from src.settings_ui import *


camera = Camera()

first_mouse = True
last_x = screen.width / 2
last_y = screen.height / 2

middle_mouse_down = False

need_resize = False


def main():
    if not glfwInit():
        return "Failed to initialize GLFW"

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4)
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 6)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)
    # Apple system required config
    if sys.platform == "darwin":
        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE)
    
    window = glfwCreateWindow(screen.width, screen.height, "FPS: 0 | Samples: 0", None, None)

    if not window:
        return "Failed to create GLFW window"
    
    glfwMakeContextCurrent(window)
    if screen.vsync == True:
        glfwSwapInterval(1)
    else:
        glfwSwapInterval(0)

    ctx = moderngl.create_context()

    imgui.create_context()

    global impl
    impl = GlfwRenderer(window)
    
    # Set callbacks after so imgui doesn't override them
    glfw_set_callbacks(window)

    # try:
    #     with open("src/assets/cache/dragon_scene.pkl", "rb") as f:
    #         scene = pickle.load(f)
    # except:
    #     scene = Scene(file_paths.scene, hdri_path=file_paths.hdri)
    #     with open("src/assets/cache/dragon_scene.pkl", "wb") as f:
    #         pickle.dump(scene, f)

    scene = Scene(file_paths.scene, hdri_path=file_paths.hdri)
    
    pt_shaders = PTShaders(ctx)
    raster_shaders = RasterShaders(ctx)
    
    global pt_state
    global raster_state
    pt_state = PTState(ctx)
    raster_state = RasterState(ctx)

    pt_quad = FullScreenQuad(ctx, pt_shaders.final)
    raster_quad = FullScreenQuad(ctx, raster_shaders.final)

    pbr_pass = PBRPass(ctx, scene, raster_shaders.pbr)
    bg_pass = BGPass(ctx, raster_shaders.bg)

    camera_buffer = CameraBuffer(camera)
    material_buffer = MaterialBuffer(scene)
    triangle_buffer = TriangleBuffer(material_buffer, scene)
    light_buffer = LightBuffer(scene)

    bvh_builder = BVHBuilder(scene)
    bvh_ready = False

    camera_buffer.bind(ctx, 0)
    triangle_buffer.bind(ctx, 1)
    material_buffer.bind(ctx, 2)
    light_buffer.bind(ctx, 3)

    scene.create_texture_arrays(ctx, *render_settings.texture_size)
    scene.bind_texture_arrays()

    scene.hdri.bind(ctx, 6)
    
    last_frame_start = 0
    stats_start_time = time.perf_counter()

    avg_fps = 0

    stats_frame_count = 0

    if render_settings.render_mode == "path_tracing":
        ctx.disable(moderngl.DEPTH_TEST)
    elif render_settings.render_mode == "rasterization":
        ctx.enable(moderngl.DEPTH_TEST)
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
    
    global settings_window
    settings_window = False

    global need_resize

    settings_ui = SettingsUI(
        pt_state,
        render_settings,
        camera_buffer,
        pt_settings
    )

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

        if not bvh_ready and bvh_builder.is_done:
            bvh_node_buffer = BVHNodeBuffer(scene)
            tri_indices_buffer = TriangleIndicesBuffer(scene)

            bvh_node_buffer.bind(ctx, 4)
            tri_indices_buffer.bind(ctx, 5)

            bvh_ready = True
        
        if need_resize:
            pt_state.resize()
            raster_state.resize()

            ctx.screen.use()
            ctx.viewport = (0, 0, screen.width, screen.height)

            need_resize = False
        
        update_stats(window, avg_fps, pt_state.total_samples, pt_state.render_complete)
        
        ctx.clear(0, 0, 0, 1)

        glfwPollEvents()

        process_input(window, delta_time)

        impl.process_inputs()
        
        imgui.new_frame()
        
        if pt_state.total_samples == pt_settings.max_samples and not pt_state.render_complete:
            pt_state.save_render()

        if settings_window:
            imgui.set_next_window_size((400, 600))
            is_expand, settings_window = imgui.begin("Settings", settings_window)

            if is_expand:
                if not bvh_ready:
                    imgui.text_disabled("Preparing path tracer (building BVH)...")
                else:
                    settings_ui.rendering_ui()
                    settings_ui.path_tracing_ui()
                
            imgui.end()

        if pt_state.view_saved:
            # Draw to screen
            pt_state.saved_render.use(location=0)

            # Prevent resizing saved texture
            # Clips the image
            ctx.viewport = (0, 0, *pt_state.saved_render.size)

            # Post Processing
            # ---------------
            pt_shaders.final.prog["exposure"].value = post_process_settings.exposure
            
            # Options:
            #   - None
            #   - ACESFilm
            #   - AgX, AgXGolden, AgXPunchy
            #   - Filmic
            #   - Lottes
            #   - Neutral
            #   - Reinhard, Reinhard2
            #   - Uchimura
            #   - Uncharted2
            #   - Unreal
            pt_shaders.final.set_tonemap(post_process_settings.tonemap)

            pt_quad.draw()

        elif render_settings.render_mode == "path_tracing":
            if pt_state.total_samples >= pt_settings.max_samples:
                pt_state.should_render = False
            
            if pt_state.should_render:
                pt_shaders.pt.prog["aspectRatio"].value = set_f4(screen.width / screen.height)

                pt_shaders.pt.prog["totalSamples"].value = pt_state.total_samples
                pt_shaders.pt.prog["maxBounces"].value = pt_settings.max_bounces

                pt_shaders.pt.prog["blur"].value = post_process_settings.blur

                pt_shaders.pt.prog["hdriExposure"].value = post_process_settings.hdri_exposure

                # Apply ceiling function
                # Allows the compute shader to reach the entire screen
                groups_x = (pt_state.tile_width + 15) // 16
                groups_y = (pt_state.tile_height + 15) // 16

                offset_x = pt_state.curr_tile_x
                offset_y = screen.height - pt_state.curr_tile_y

                pt_shaders.pt.prog["uOffset"].value = np.array([offset_x, offset_y], dtype=i4)

                pt_state.curr_tile_x += pt_state.tile_width
                if pt_state.curr_tile_x > screen.width:
                    pt_state.curr_tile_x = 0
                    pt_state.curr_tile_y += pt_state.tile_height
                
                if pt_state.curr_tile_y > screen.height:
                    pt_state.curr_tile_y = 0
                    # Finished rendering entire screen; add a sample
                    pt_state.total_samples += 1
                
                # Run compute shader
                pt_state.compute_tex.bind_to_image(0, read=True, write=True)
                pt_shaders.pt.prog.run(groups_x, groups_y)
            
            # Draw to screen
            pt_state.compute_tex.use(location=0)

            # Post Processing
            # ---------------
            pt_shaders.final.prog["exposure"].value = post_process_settings.exposure
            
            # Options:
            #   - None
            #   - ACESFilm
            #   - AgX, AgXGolden, AgXPunchy
            #   - Filmic
            #   - Lottes
            #   - Neutral
            #   - Reinhard, Reinhard2
            #   - Uchimura
            #   - Uncharted2
            #   - Unreal
            pt_shaders.final.set_tonemap(post_process_settings.tonemap)

            pt_quad.draw()
        
        elif render_settings.render_mode == "rasterization":
            raster_state.raster_fbo.use()
            raster_state.raster_fbo.clear(0.0, 0.0, 0.0, 1.0)

            # Background Shader
            # -----------------
            ctx.depth_func = "<="

            # Vertex shader uniforms
            raster_shaders.bg.prog["view"].write(camera.get_view().to_bytes())
            raster_shaders.bg.prog["projection"].write(camera.get_perspective().to_bytes())

            bg_pass.draw()

            ctx.depth_func = "<"

            # PBR Shader
            # ----------
            # Vertex shader uniforms
            raster_shaders.pbr.prog["view"].write(camera.get_view().to_bytes())
            raster_shaders.pbr.prog["projection"].write(camera.get_perspective().to_bytes())

            # Fragment shader uniforms
            raster_shaders.pbr.prog["numLights"].value = set_i4(scene.num_lights)
            raster_shaders.pbr.prog["cameraPos"].value = camera.pos

            pbr_pass.draw()

            ctx.screen.use()
            raster_state.raster_color_tex.use(location=0)

            # Post Processing
            # ---------------
            raster_shaders.final.prog["exposure"].value = post_process_settings.exposure
            
            # Options:
            #   - None
            #   - ACESFilm
            #   - AgX, AgXGolden, AgXPunchy
            #   - Filmic
            #   - Lottes
            #   - Neutral
            #   - Reinhard, Reinhard2
            #   - Uchimura
            #   - Uncharted2
            #   - Unreal
            raster_shaders.final.set_tonemap(post_process_settings.tonemap)

            raster_quad.draw()
    
        # Render UI
        # ---------
        imgui.render()
        impl.render(imgui.get_draw_data())

        glfwSwapBuffers(window)

        stats_frame_count += 1

        cap_fps(frame_start, screen.fps_cap)
    
    impl.shutdown()
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


def update_stats(window, fps, samples, render_complete):
    if render_settings.render_mode == "path_tracing":
        if render_complete or pt_state.view_saved:
            glfwSetWindowTitle(
                window,
                f"FPS: {fps:.2f} | Render Complete"
            )
        else:
            glfwSetWindowTitle(
                window,
                f"FPS: {fps:.2f} | Samples: {samples}"
            )
    else:
        glfwSetWindowTitle(
            window,
            f"FPS: {fps:.2f}"
        )


def glfw_set_callbacks(window):
    glfwSetCursorPosCallback(window, mouse_callback)
    glfwSetScrollCallback(window, scroll_callback)
    glfwSetMouseButtonCallback(window, mouse_button_callback)
    glfwSetKeyCallback(window, key_callback)
    glfwSetFramebufferSizeCallback(window, framebuffer_size_callback)
    glfwSetWindowSizeLimits(window, 400, 300, GLFW_DONT_CARE, GLFW_DONT_CARE)


def framebuffer_size_callback(window, width, height):
    global need_resize, screen

    need_resize = True

    screen.width = width
    screen.height = height
    screen.resolution = (width, height)


def process_input(window, delta_time):
    if imgui.get_io().want_capture_keyboard:
        return
    
    if render_settings.render_mode == "path_tracing":
        return
    
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


def key_callback(window, key, scancode, action, mods):
    global settings_window

    if key == GLFW_KEY_ESCAPE and action == GLFW_PRESS:
        settings_window = not settings_window


def mouse_button_callback(window, button, action, mods):
    if hasattr(impl, "mouse_button_callback"):
        impl.mouse_button_callback(window, button, action, mods)
    
    if imgui.get_io().want_capture_mouse:
        return

    if render_settings.render_mode == "path_tracing":
        return
    
    global middle_mouse_down, first_mouse

    if button == GLFW_MOUSE_BUTTON_MIDDLE:
        if action == GLFW_PRESS:
            middle_mouse_down = True
            first_mouse = True
            glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
        elif action == GLFW_RELEASE:
            middle_mouse_down = False
            glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_NORMAL)


def mouse_callback(window, xpos, ypos):
    if hasattr(impl, "mouse_callback"):
        impl.mouse_callback(window, xpos, ypos)
    
    if imgui.get_io().want_capture_mouse:
        return

    if render_settings.render_mode == "path_tracing":
        return

    if middle_mouse_down:
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
    if hasattr(impl, "scroll_callback"):
        impl.scroll_callback(window, xoffset, yoffset)
    
    if imgui.get_io().want_capture_mouse:
        return
    
    if render_settings.render_mode == "path_tracing":
        return

    camera.process_mouse_scroll(yoffset)


class PTShaders:
    def __init__(self, ctx):
        self.final = Shader(
            ctx,
            file_paths.path_tracing.vert,
            file_paths.path_tracing.frag
        )
        self.pt = ComputeShader(
            ctx,
            file_paths.path_tracing.comp
        )


class RasterShaders:
    def __init__(self, ctx):
        self.pbr = Shader(
            ctx,
            file_paths.pbr.vert,
            file_paths.pbr.frag
        )
        self.bg = Shader(
            ctx,
            file_paths.background.vert,
            file_paths.background.frag
        )
        self.final = Shader(
            ctx,
            file_paths.final.vert,
            file_paths.final.frag
        )


if __name__ == "__main__":
    main()
