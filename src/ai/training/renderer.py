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


camera = Camera()

first_mouse = True
last_x = settings.screen.width / 2
last_y = settings.screen.height / 2

middle_mouse_down = False

need_resize = False


# See 9.4 Rendering
def run_app():
    glfw_window = None

    try:
        for _ in range(settings.ai_training.num_pass_throughs):
            remove_stale_cache()

            # Break if the user exited the previous window
            if glfw_window:
                if glfw_window.should_close():
                    break
            
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
            
            pt_shaders = PTShaders(ctx)
            raster_shaders = RasterShaders(ctx)
            
            pt_state = PTState(ctx)
            raster_state = RasterState(ctx)
            final_output_state = FinalOutputState(ctx)
            export_state = ExportState(pt_state, final_output_state)
            scene_state = SceneState()
            camera_capture_state = CameraCaptureState(scene_state, camera)
            frame_stats = FrameStatsState()

            camera_buffer = CameraBuffer(camera)
            camera_buffer.bind(ctx, 0)
            camera_capture_state.set_camera_buffer(camera_buffer)
        
            frame_stats.start_tracking()

            while not glfw_window.should_close():
                if scene_state.ai_training_finished:
                    break

                settings.file_paths.scene = scene_state.curr_scene_file
                settings.file_paths.hdri = scene_state.curr_hdri_file
                scene = load_scene(settings.file_paths.scene)
                scene.hdri = HDRI(settings.file_paths.hdri)

                scene.snapshot_original_materials()
                scene.hdri.snapshot_original()

                scene.scramble_materials()
                scene.hdri.scramble()

                settings.ai_training.get_new_noisy_samples()
                
                if settings.ai_training.mode != "camera_setup":
                    camera_capture_state.load_next_state()
                
                material_buffer = MaterialBuffer(scene)
                triangle_buffer = TriangleBuffer(scene)
                light_buffer = LightBuffer(scene)
                emissive_triangles_buffer = EmissiveTrianglesBuffer(scene)
                finite_lights_buffer = FiniteLightsBuffer(scene)

                if settings.ai_training.mode != "camera_setup":
                    scene.build_bvh()
                    bvh_node_buffer = BVHNodeBuffer(scene)
                    tri_indices_buffer = TriangleIndicesBuffer(scene)
                    bvh_node_buffer.bind(ctx, 4)
                    tri_indices_buffer.bind(ctx, 5)

                triangle_buffer.bind(ctx, 1)
                material_buffer.bind(ctx, 2)
                light_buffer.bind(ctx, 3)
                emissive_triangles_buffer.bind(ctx, 6)
                finite_lights_buffer.bind(ctx, 7)

                scene.create_texture_arrays(ctx)
                scene.bind_texture_arrays()

                scene.hdri.bind_img(ctx, 6)
                scene.hdri.bind_cdfs(ctx, 7, 8)

                bvh_state = BVHState(ctx, scene)
                bvh_state.build()

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
                    camera_buffer,
                    camera
                )

                pt_pipeline = PathTracingPipeline(ctx, scene, camera, pt_state, final_output_state, pt_shaders)
                raster_pipeline = RasterizationPipeline(ctx, scene, camera, raster_state, raster_shaders)

                frame_stats.start_tracking()

                is_first_render = True

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

                        ctx.screen.use()
                        ctx.viewport = (0, 0, settings.screen.width, settings.screen.height)

                        glfw_window.need_resize = False
                    
                    if scene_state.ai_training_finished:
                        break

                    update_stats(glfw_window, pt_state, bvh_state, frame_stats.avg_fps, pt_state.rendering.total_samples, pt_state.rendering.render_complete)

                    ctx.screen.use()
                    ctx.viewport = (0, 0, settings.screen.width, settings.screen.height)

                    ctx.clear(0, 0, 0, 1)

                    glfw_window.poll()
                    input_state.process_input(frame_stats.delta_time, camera)
                    imgui_state.begin_frame()
                    ui_state.settings_window = settings_ui.draw(ui_state.settings_window)

                    # NOTE: Disable blur and DOF since the AI denoiser will process the buffers
                    # as if the blur and DOF create "new" geometry, causing incorrect results.
                    camera.blur = 0
                    camera.dof_enabled = False
                    camera.aperture = 0
                    camera_buffer.update_data()

                    if settings.ai_training.mode != "camera_setup":
                        if is_first_render and bvh_state.ready:
                            pt_state.start_render()
                            is_first_render = False
                        
                        settings.rendering.mode = "path_tracing"
                        pt_state.rendering.should_render = True

                    if settings.rendering.mode == "path_tracing":
                        if bvh_state.ready:
                            pt_pipeline.render()

                            if settings.ai_training.mode and pt_state.rendering.should_render:
                                export_state.auto_save_training_renders()

                            if pt_state.rendering.render_complete:
                                camera_capture_state.load_next_state()

                                # NOTE: Disable blur and DOF since the AI denoiser will process the buffers
                                # as if the blur and DOF create "new" geometry, causing incorrect results.
                                camera.blur = 0
                                camera.dof_enabled = False
                                camera.aperture = 0

                                scene.scramble_materials()
                                scene.hdri.scramble()

                                scene.hdri.update_img()
                                scene.hdri.update_cdfs()
                                material_buffer.update_data()
                                emissive_triangles_buffer.update_data()
                                triangle_buffer.update_data()
                                
                                if scene_state.changed_scene:
                                    imgui_state.end_frame()
                                    glfw_window.swap()
                                    scene_state.changed_scene = False

                                    break
                
                                camera_buffer.update_data()
                                pt_state.start_render()
                    
                    elif settings.rendering.mode == "rasterization":
                        raster_pipeline.render()
                
                    imgui_state.end_frame()
                    glfw_window.swap()
                    frame_stats.increment_frame_count()
            
                    frame_stats.cap_fps(settings.screen.fps_cap)

                    if scene_state.changed_scene:
                        scene_state.changed_scene = False
                        break
                
                scene.release_all()

    finally:
        imgui_state.shutdown()
        glfw_window.shutdown()


def main():
    run_app()


def update_stats(glfw_window, pt_state, bvh_state, fps, samples, render_complete):
    if settings.rendering.mode == "path_tracing":
        if render_complete or pt_state.rendering.should_view_saved:
            glfw_window.set_title(f"FPS: {fps:.2f} | Render Complete In {pt_state.rendering.render_time:.2f}s")
        
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
