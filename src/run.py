import numpy as np
from glfw.GLFW import *
import moderngl
import sys
import time
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

from src.settings import *
from src.dtypes import *
from src.shader import *
from src.camera import *
from src.model import *
from src.render_state import *
from src.buffer_loading import *
from src.draw_passes import *
from src.bvh_builder import *
from src.settings_ui import *
from src.network import *
from src.pipelines.path_tracing import *
from src.pipelines.rasterization import *


def main():
    glfw_window = GlfwWindow()
    imgui_state = ImguiState()
    input_state = InputState(glfw_window, imgui_state)
    ui_state = UIState()
    camera = Camera()

    glfw_window.create("FPS: 0 | Samples: 0")

    ctx = moderngl.create_context()

    imgui_state.create(glfw_window.window)
    
    glfw_callback_state = GlfwCallbackState(glfw_window, input_state, ui_state, imgui_state, camera)
    # Set callbacks after so imgui doesn't override them
    glfw_callback_state.set_callbacks()

    scene = load_scene(file_paths.scene)
    scene.hdri = HDRI(file_paths.hdri)
    
    pt_shaders = PTShaders(ctx)
    raster_shaders = RasterShaders(ctx)
    
    global pt_state
    global raster_state
    pt_state = PTState(ctx)
    raster_state = RasterState(ctx)
    export_state = ExportState(pt_state)
    scene_state = SceneState()
    camera_capture_state = CameraCaptureState(scene_state, camera)
    frame_stats = FrameStatsState()

    pt_quad = FullScreenQuad(ctx, pt_shaders.final)
    raster_quad = FullScreenQuad(ctx, raster_shaders.final)

    camera_buffer = CameraBuffer(camera)
    material_buffer = MaterialBuffer(scene)
    triangle_buffer = TriangleBuffer(scene)
    light_buffer = LightBuffer(scene)
    emissive_triangles_buffer = EmissiveTrianglesBuffer(scene)
    finite_lights_buffer = FiniteLightsbuffer(scene)

    bvh_builder = BVHBackgroundBuilder(scene)
    bvh_ready = False

    camera_buffer.bind(ctx, 0)
    triangle_buffer.bind(ctx, 1)
    material_buffer.bind(ctx, 2)
    light_buffer.bind(ctx, 3)
    emissive_triangles_buffer.bind(ctx, 6)
    finite_lights_buffer.bind(ctx, 7)

    scene.create_texture_arrays(ctx)
    scene.bind_texture_arrays()

    scene.hdri.bind_img(ctx, 6)
    scene.hdri.bind_cdfs(ctx, 7, 8)

    if render_settings.render_mode == "path_tracing":
        ctx.disable(moderngl.DEPTH_TEST)
    elif render_settings.render_mode == "rasterization":
        ctx.enable(moderngl.DEPTH_TEST)
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

    settings_ui = SettingsUI(
            pt_state,
            scene_state,
            camera_capture_state,
            camera_buffer,
            camera
        )

    ai_denoiser = KPCN()
    # Load saved weights and biases
    ai_denoiser.load_state_dict(torch.load("src/denoiser/checkpoint.pt")["model_state_dict"])

    pt_pipeline = PathTracingPipeline(scene, pt_state, pt_shaders, pt_quad)
    raster_pipeline = RasterizationPipeline(ctx, scene, camera, raster_state, raster_shaders, raster_quad)

    frame_stats.start_tracking()

    # Render loop
    while not glfw_window.should_close():
        frame_stats.track()

        if screen.width <= 0 or screen.height <= 0:
            glfwPollEvents()
            continue

        if not bvh_ready and bvh_builder.is_done:
            print("Creating BVH buffers...")

            bvh_node_buffer = BVHNodeBuffer(scene)
            tri_indices_buffer = TriangleIndicesBuffer(scene)

            bvh_node_buffer.bind(ctx, 4)
            tri_indices_buffer.bind(ctx, 5)

            bvh_ready = True

            print("Path tracing is ready")
        
        if glfw_window.need_resize:
            pt_state.reset()
            raster_state.resize()

            ctx.screen.use()
            ctx.viewport = (0, 0, screen.width, screen.height)

            glfw_window.need_resize = False
        
        update_stats(glfw_window, frame_stats.avg_fps, pt_state.rendering.total_samples, pt_state.rendering.render_complete)
        
        ctx.clear(0, 0, 0, 1)

        glfw_window.poll()
        input_state.process_input(frame_stats.delta_time, camera)
        imgui_state.begin_frame()
        ui_state.settings_window = settings_ui.draw(ui_state.settings_window)
        
        if pt_state.denoising.should_denoise:
            pt_state.denoise(ai_denoiser)

            # Draw to screen
            pt_state.denoising.saved_denoised.use(location=0)

            # Prevent resizing saved texture
            # Clips the image
            ctx.viewport = (0, 0, *pt_state.framebuffers.saved_combined.size)

            # Post Processing
            # ---------------
            pt_shaders.final.prog["exposure"].value = post_process_settings.exposure
            
            pt_shaders.final.set_tonemap(post_process_settings.tonemap)

            pt_quad.draw()

        elif pt_state.rendering.should_view_saved:
            # Draw texture to screen depending on the debug mode
            # Currently broken!
            if pt_state.rendering.debug_mode == "off":
                pt_state.framebuffers.saved_combined.use(location=0)
            elif pt_state.rendering.debug_mode == "albedo":
                pt_state.framebuffers.saved_albedo.use(location=0)
            elif pt_state.rendering.debug_mode == "normal":
                pt_state.framebuffers.saved_normal.use(location=0)
            elif pt_state.rendering.debug_mode == "depth":
                pt_state.framebuffers.saved_depth.use(location=0)

            # Prevent resizing saved texture to new screen dimensions
            # Doesn't matter which saved texture to use since all are saved at the same dimensions
            ctx.viewport = (0, 0, *pt_state.framebuffers.saved_combined.size)

            # Post Processing
            # ---------------
            pt_shaders.final.prog["exposure"].value = post_process_settings.exposure
            
            pt_shaders.final.set_tonemap(post_process_settings.tonemap)

            pt_quad.draw()

        elif render_settings.render_mode == "path_tracing":
            pt_pipeline.render()
        
        elif render_settings.render_mode == "rasterization":
            raster_state.raster_fbo.use()
            raster_state.raster_fbo.clear(0.0, 0.0, 0.0, 1.0)

            raster_pipeline.render()
    
        imgui_state.end_frame()
        glfw_window.swap()
        frame_stats.increment_frame_count()

        frame_stats.cap_fps(screen.fps_cap)
    
    imgui_state.shutdown()
    glfw_window.shutdown()


def update_stats(glfw_window, fps, samples, render_complete):
    if render_settings.render_mode == "path_tracing":
        if render_complete or pt_state.rendering.should_view_saved:
            glfw_window.set_title(f"FPS: {fps:.2f} | Render Complete")
        else:
            glfw_window.set_title(f"FPS: {fps:.2f} | Samples: {samples}")
    else:
        glfw_window.set_title(f"FPS: {fps:.2f}")


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
