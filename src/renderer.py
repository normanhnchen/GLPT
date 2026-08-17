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
from src.bvh_builder import *
from src.settings_ui import *
from src.ai.denoiser.network import *
from src.pipelines.path_tracing import *
from src.pipelines.rasterization import *


def preload_scene_data(progress_callback=None):
    """
    Load everything which doesn't require a moderngl/GLFW/ImGui context.
    Called by the PySide6 launcher app to build the scene on a separate thread
    while displaying a loading bar about the build status.
    """

    def report(percentage, status):
        if progress_callback:
            progress_callback(percentage, status)

    report(0, "Cleaning Stale Cache...")
    remove_stale_cache()

    report(15, "Loading Scene...")
    scene = load_scene(settings.file_paths.scene)

    report(50, "Loading HDRI")
    scene.hdri = HDRI(settings.file_paths.hdri)

    report(70, "Loading AI Denoiser")
    ai_denoiser = KPCN()
    # Load saved weights and biases
    ai_denoiser.load_state_dict(torch.load(settings.file_paths.denoiser.checkpoint)["model_state_dict"])

    camera = Camera()
    
    report(85, "Building Scene Buffers")
    buffers = {
        "camera": CameraBuffer(camera),
        "material": MaterialBuffer(scene),
        "triangle": TriangleBuffer(scene),
        "light": LightBuffer(scene),
        "emissive_triangles": EmissiveTrianglesBuffer(scene),
        "finite_lights": FiniteLightsBuffer(scene),
    }

    report(100, "Starting Renderer")

    return scene, ai_denoiser, camera, buffers


def run_app(scene, ai_denoiser, camera, buffers):
    glfw_window = GlfwWindow()
    imgui_state = ImguiState()
    input_state = InputState(glfw_window, imgui_state)
    ui_state = UIState()

    glfw_window.create("FPS: 0 | Samples: 0")

    ctx = moderngl.create_context()

    imgui_state.create(glfw_window.window)
    
    glfw_callback_state = GlfwCallbackState(glfw_window, input_state, ui_state, imgui_state, camera)
    # Set callbacks after so imgui doesn't override them
    glfw_callback_state.set_callbacks()
    
    pt_shaders = PTShaders(ctx)
    raster_shaders = RasterShaders(ctx)
    
    pt_state = PTState(ctx)
    raster_state = RasterState(ctx)
    final_output_state = FinalOutputState(ctx)
    export_state = ExportState(pt_state, final_output_state)
    scene_state = SceneState()
    camera_capture_state = CameraCaptureState(scene_state, camera)
    frame_stats = FrameStatsState()
    bvh_state = BVHState(ctx, scene)
    bvh_state.background_build()

    buffers["camera"].bind(ctx, 0)
    buffers["triangle"].bind(ctx, 1)
    buffers["material"].bind(ctx, 2)
    buffers["light"].bind(ctx, 3)
    buffers["emissive_triangles"].bind(ctx, 6)
    buffers["finite_lights"].bind(ctx, 7)

    scene.create_texture_arrays(ctx)
    scene.bind_texture_arrays()

    scene.hdri.bind_img(ctx, 6)
    scene.hdri.bind_cdfs(ctx, 7, 8)

    if settings.rendering.mode == "path_tracing":
        ctx.disable(moderngl.DEPTH_TEST)
    elif settings.rendering.mode == "rasterization":
        ctx.enable(moderngl.DEPTH_TEST)
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

    settings_ui = SettingsUI(
        scene,
        pt_state,
        scene_state,
        camera_capture_state,
        export_state,
        bvh_state,
        buffers["camera"],
        camera
    )

    pt_pipeline = PathTracingPipeline(ctx, scene, camera, pt_state, final_output_state, pt_shaders, ai_denoiser)
    raster_pipeline = RasterizationPipeline(ctx, scene, camera, raster_state, raster_shaders)

    frame_stats.start_tracking()

    # Render loop
    while not glfw_window.should_close():
        frame_stats.track()

        if settings.screen.width <= 0 or settings.screen.height <= 0:
            glfwPollEvents()
            continue

        bvh_state.update(4, 5, 8)
        
        if glfw_window.need_resize:
            pt_state.reset()
            raster_state.resize()
            final_output_state.resize()

            ctx.screen.use()
            ctx.viewport = (0, 0, settings.screen.width, settings.screen.height)

            glfw_window.need_resize = False

            pt_state.start_render()
        
        update_stats(glfw_window, pt_state, bvh_state, frame_stats.avg_fps, pt_state.rendering.total_samples, pt_state.rendering.render_complete)
        
        ctx.clear(0, 0, 0, 1)

        glfw_window.poll()
        input_state.process_input(frame_stats.delta_time, camera)
        imgui_state.begin_frame()
        ui_state.settings_window = settings_ui.draw(ui_state.settings_window)

        if settings.rendering.mode == "path_tracing":
            pt_pipeline.render()
        
        elif settings.rendering.mode == "rasterization":
            raster_pipeline.render()
    
        imgui_state.end_frame()
        glfw_window.swap()
        frame_stats.increment_frame_count()

        frame_stats.cap_fps(settings.screen.fps_cap)
    
    imgui_state.shutdown()
    glfw_window.shutdown()


def main():
    scene, ai_denoiser, camera, buffers = preload_scene_data()
    run_app(scene, ai_denoiser, camera, buffers)


def update_stats(glfw_window, pt_state, bvh_state, fps, samples, render_complete):
    # BVH Bounds
    if pt_state.debug.mode == 7:
        # This mode runs through a rasterizer so don't display samples
        glfw_window.set_title(f"FPS: {fps:.2f}")

    elif settings.rendering.mode == "path_tracing":
        if render_complete or pt_state.rendering.should_view_saved:
            glfw_window.set_title(f"FPS: {fps:.2f} | Render Complete in {pt_state.rendering.render_time:.2f}s")
        
        else:
            glfw_window.set_title(f"FPS: {fps:.2f} | Samples: {samples}")
    
    else:
        if not bvh_state.ready:
            glfw_window.set_title(f"FPS: {fps:.2f} | Building BVH")

        else:
            if not bvh_state.buffers_created:
                glfw_window.set_title(f"FPS: {fps:.2f} | Creating BVH Buffers | BVH Built In {bvh_state.build_time:.2f}s")

            elif bvh_state.build_time:
                glfw_window.set_title(f"FPS: {fps:.2f} | Path Tracing Is Ready | BVH Built In {bvh_state.build_time:.2f}s")

            else:
                glfw_window.set_title(f"FPS: {fps:.2f} | Path Tracing Is Ready")


class PTShaders:
    def __init__(self, ctx):
        self.final = Shader(
            ctx,
            settings.file_paths.path_tracing.vert,
            settings.file_paths.path_tracing.frag
        )
        self.pt = ComputeShader(
            ctx,
            settings.file_paths.path_tracing.comp
        )
        self.bvh_bounds_debug = Shader(
            ctx,
            settings.file_paths.path_tracing.bvh_bounds_debug.vert,
            settings.file_paths.path_tracing.bvh_bounds_debug.frag
        )


class RasterShaders:
    def __init__(self, ctx):
        self.pbr = Shader(
            ctx,
            settings.file_paths.pbr.vert,
            settings.file_paths.pbr.frag
        )
        self.bg = Shader(
            ctx,
            settings.file_paths.background.vert,
            settings.file_paths.background.frag
        )
        self.final = Shader(
            ctx,
            settings.file_paths.final.vert,
            settings.file_paths.final.frag
        )


if __name__ == "__main__":
    main()
