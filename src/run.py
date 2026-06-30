import numpy as np
from glfw.GLFW import *
import moderngl
import sys
import time
import pickle
from imgui_bundle import imgui, imgui_ctx
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

from src.settings import *
from src.dtypes import *
from src.shader import *
from src.camera import *
from src.model import *


camera = Camera()

first_mouse = True
last_x = screen.width / 2
last_y = screen.height / 2

middle_mouse_down = False


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
    glfwSetCursorPosCallback(window, mouse_callback)
    glfwSetScrollCallback(window, scroll_callback)
    glfwSetMouseButtonCallback(window, mouse_button_callback)

    try:
        with open("src/assets/cache/dragon_scene.pkl", "rb") as f:
            scene = pickle.load(f)
    except:
        scene = Scene(file_paths.scene, hdri_path=file_paths.hdri)
        with open("src/assets/cache/dragon_scene.pkl", "wb") as f:
            pickle.dump(scene, f)

    # scene = Scene(file_paths.scene, hdri_path=file_paths.hdri)

    pt_shaders = PTShaders(ctx)
    raster_shaders = RasterShaders(ctx,)
    
    compute_texture = ctx.texture(screen.resolution, 4, dtype=f4)

    full_screen_quad = FullScreenQuad(ctx, pt_shaders.final)

    pbr_pass = PBRPass(ctx, scene, raster_shaders.pbr)
    bg_pass = BGPass(ctx, raster_shaders.bg)

    raster_color_tex = ctx.texture(screen.resolution, 4, dtype=f4)
    raster_depth_texture = ctx.depth_texture(screen.resolution)
    raster_fbo = ctx.framebuffer(
        color_attachments=[raster_color_tex],
        depth_attachment=raster_depth_texture
    )

    camera_buffer = CameraBuffer()

    material_buffer = MaterialBuffer(scene)

    triangle_buffer = TriangleBuffer(material_buffer, scene)

    bvh_node_buffer = BVHNodeBuffer(scene)

    light_buffer = LightBuffer(scene)

    camera_buffer.bind(ctx, 0)

    triangle_buffer.bind(ctx, 1)

    material_buffer.bind(ctx, 2)

    bvh_node_buffer.bind(ctx, 3)

    light_buffer.bind(ctx, 4)

    tri_indices_data = scene.bvh.tri_indices.astype(i4)
    tri_indices_buffer = ctx.buffer(tri_indices_data.tobytes())
    tri_indices_buffer.bind_to_storage_buffer(5)

    scene.create_texture_arrays(ctx, *render_settings.texture_size)
    scene.bind_texture_arrays()

    scene.hdri.bind(ctx, 6)
    
    last_frame_start = 0
    stats_start_time = time.perf_counter()

    avg_fps = 0

    total_samples = 0
    stats_frame_count = 0

    should_render = True

    if render_settings.render_mode == "path_tracing":
        ctx.disable(moderngl.DEPTH_TEST)
    elif render_settings.render_mode == "rasterization":
        ctx.enable(moderngl.DEPTH_TEST)

    curr_selection = "Rasterization"
    options = ["Rasterization", "Path Tracing"]
    
    settings_window = True
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
        
        update_stats(window, avg_fps, total_samples)

        glfwPollEvents()

        process_input(window, delta_time)

        impl.process_inputs()
        
        imgui.new_frame()

        if settings_window:
            imgui.set_next_window_size((400, 600))

            is_expand, settings_window = imgui.begin("Settings", True)
            if is_expand:
                if imgui.begin_combo("Render Mode", curr_selection):
                    for item in options:
                        is_selected = (curr_selection == item)

                        clicked, state = imgui.selectable(item, is_selected)

                        if clicked:
                            curr_selection = item

                            if curr_selection == "Path Tracing":
                                render_settings.render_mode = "path_tracing"
                                camera_buffer.update_data()
                                total_samples = 0
                                should_render = True
                            else:
                                render_settings.render_mode = "rasterization"

                        if is_selected:
                            imgui.set_item_default_focus()
                    
                    imgui.end_combo()
                
            imgui.end()

        ctx.clear(0, 0, 0, 1)

        if render_settings.render_mode == "path_tracing":
            if total_samples >= pt_settings.max_samples:
                should_render = False
            
            if should_render:
                pt_shaders.pt.prog["totalSamples"].value = total_samples
                pt_shaders.pt.prog["maxDepth"].value = pt_settings.max_depth

                pt_shaders.pt.prog["blur"].value = post_process_settings.blur

                pt_shaders.pt.prog["hdriExposure"].value = post_process_settings.hdri_exposure

                # Apply ceiling function
                # Allows the GPU to reach the entire screen despite different screen resolutions
                local_size_x = (screen.width + 15) // 16
                local_size_y = (screen.height + 15) // 16
                
                # Run compute shader
                compute_texture.bind_to_image(0, read=True, write=True)
                pt_shaders.pt.prog.run(local_size_x, local_size_y)
            
                # Draw to screen
                compute_texture.use(location=0)

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

                full_screen_quad.draw()
        
        elif render_settings.render_mode == "rasterization":
            raster_fbo.use()
            raster_fbo.clear(0.0, 0.0, 0.0, 1.0)

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
            raster_color_tex.use(location=0)

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

            full_screen_quad.draw()
    
        # Render UI
        # ---------
        imgui.render()
        impl.render(imgui.get_draw_data())

        glfwSwapBuffers(window)

        if should_render:
            total_samples += 1
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


def update_stats(window, fps, samples):
    if render_settings.render_mode == "path_tracing":
        glfwSetWindowTitle(
            window,
            f"FPS: {fps:.2f} | Samples: {samples}"
        )
    else:
        glfwSetWindowTitle(
            window,
            f"FPS: {fps:.2f}"
        )


def process_input(window, delta_time):
    if glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS:
        glfwSetWindowShouldClose(window, True)

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


def mouse_button_callback(window, button, action, mods):
    if hasattr(impl, "mouse_button_callback"):
        impl.mouse_button_callback(window, button, action, mods)
    
    if imgui.get_io().want_capture_mouse:
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


class CameraBuffer:
    def __init__(self):
        camera_dtype = np.dtype([
            ("pos", *vec3),
            ("aperture", f4),
            ("front", *vec3),
            ("focusDist", f4),
            ("up", *vec3),
            ("autoFocus", f4),
            ("right", *vec3),
            ("fov", f4)
        ])
        
        camera_data = np.zeros(1, dtype=camera_dtype)

        camera_data["aperture"] = post_process_settings.aperture
        camera_data["focusDist"] = post_process_settings.focus_dist
        camera_data["autoFocus"] = post_process_settings.auto_focus

        self.camera_dtype = camera_dtype
        self.camera_data = camera_data
    
    def update_data(self):
        self.camera_data["pos"] = camera.pos
        self.camera_data["front"] = camera.front
        self.camera_data["up"] = camera.up
        self.camera_data["right"] = camera.right
        self.camera_data["fov"] = camera.fov

        self.camera_buffer.write(self.camera_data.tobytes())
    
    def bind(self, ctx, loc):
        self.camera_buffer = ctx.buffer(self.camera_data.tobytes())
        self.camera_buffer.bind_to_storage_buffer(loc)


class MaterialBuffer:
    def __init__(self, scene):
        material_dtype = np.dtype([
            ("baseCol", *vec3),
            ("alpha", f4),
            ("emissive", *vec3),
            ("metallic", f4),
            ("roughness", f4),
            ("ao", f4),
            # Settings
            ("alphaMode", i4), # 0=OPAQUE, 1=MASK, or 2=BLEND
            ("alphaCutoff", f4),
            ("doubleSided", i4),
            # Flags
            ("hasEmission", i4),
            ("hasBaseColTex", i4),
            ("hasEmissiveTex", i4),
            ("hasRoughTex", i4),
            ("hasMetalTex", i4),
            ("hasNormalTex", i4),
            ("hasOcclTex", i4),
            # Texture IDs
            ("baseTexId", i4),
            ("emissiveTexId", i4),
            ("roughTexId", i4),
            ("metalTexId", i4),
            ("normalTexId", i4),
            ("occlTexId", i4),
            ("emissiveStrength", f4),
            ("transmission", f4),
            ("ior", f4),
            ("pad1", f4),
            ("pad2", f4),
            ("pad3", f4)
        ])

        material_data = np.zeros(scene.num_materials, dtype=material_dtype)

        for i, mat in enumerate(scene.materials):
            material_data[i]["baseCol"] = mat.base_color[:3]
            material_data[i]["alpha"] = mat.base_color[-1]
            material_data[i]["roughness"] = mat.roughness
            material_data[i]["emissive"] = mat.emissive_color
            material_data[i]["metallic"] = mat.metallic
            # Ambient occlusion is changed only from material textures
            # Set default to 1.0 for a fully lit material
            material_data[i]["ao"] = set_f4(1)

            material_data[i]["alphaMode"] = mat.alpha_mode
            material_data[i]["alphaCutoff"] = mat.alpha_cutoff
            material_data[i]["doubleSided"] = mat.double_sided

            # Flags
            material_data[i]["hasEmission"] = mat.has_emission
            material_data[i]["hasBaseColTex"] = mat.has_base_color_tex
            material_data[i]["hasEmissiveTex"] = mat.has_emissive_tex
            material_data[i]["hasRoughTex"] = mat.has_roughness_tex
            material_data[i]["hasMetalTex"] = mat.has_metallic_tex
            material_data[i]["hasNormalTex"] = mat.has_normal_tex
            material_data[i]["hasOcclTex"] = mat.has_occlusion_tex
            
            # Texture IDs
            material_data[i]["baseTexId"] = mat.base_color_tex_id
            material_data[i]["emissiveTexId"] = mat.emissive_tex_id
            material_data[i]["roughTexId"] = mat.roughness_tex_id
            material_data[i]["metalTexId"] = mat.metallic_tex_id
            material_data[i]["normalTexId"] = mat.normal_tex_id
            material_data[i]["occlTexId"] = mat.occlusion_tex_id
            
            # glTF extensions
            extensions = mat.extensions

            KHR_materials_emissive_strength = extensions.get("KHR_materials_emissive_strength")
            if KHR_materials_emissive_strength:
                material_data[i]["emissiveStrength"] = KHR_materials_emissive_strength["emissiveStrength"]
            else:
                material_data[i]["emissiveStrength"] = 0.0

            KHR_materials_transmission = extensions.get("KHR_materials_transmission")
            if KHR_materials_transmission:
                material_data[i]["transmission"] = KHR_materials_transmission["transmissionFactor"]
            else:
                material_data[i]["transmission"] = set_f4(0.0)

            KHR_materials_ior = extensions.get("KHR_materials_ior")
            if KHR_materials_ior:
                material_data[i]["ior"] = KHR_materials_ior["ior"]
            else:
                material_data[i]["ior"] = set_f4(1.5)
        
        self.material_dtype = material_dtype
        self.material_data = material_data
    
    def bind(self, ctx, loc):
        self.material_buffer = ctx.buffer(self.material_data.tobytes())
        self.material_buffer.bind_to_storage_buffer(loc)


class LightBuffer:
    def __init__(self, scene):
        light_dtype = np.dtype([
            ("col", *vec3),
            ("type", i4), # Point: 0, directional: 1, spot: 2
            ("pos", *vec3),
            ("intensity", f4),
            ("dir", *vec3),
            ("range", f4),
            ("isSpot", i4),
            ("innerConeAngle", f4), # Radians
            ("outerConeAngle", f4), # Radians
            ("pad1", f4)
        ])

        # Ensure there is atleast a buffer size
        buffer_size = max(1, scene.num_lights)

        light_data = np.zeros(buffer_size, dtype=light_dtype)

        for i, light in enumerate(scene.lights):
            light_type = light["type"]
            if light_type == "directional":
                light_data[i]["type"] = 1
            elif light_type == "spot":
                light_data[i]["type"] = 2
            else:
                light_data[i]["type"] = 0

            light_data[i]["col"]       = light["color"]
            light_data[i]["intensity"] = light["intensity"]
            light_data[i]["range"]     = light["range"]

            spot = light["spot"]
            if spot:
                light_data[i]["isSpot"] = 1
                light_data[i]["innerConeAngle"] = spot["innerConeAngle"]
                light_data[i]["outerConeAngle"] = spot["outerConeAngle"]
            else:
                light_data[i]["isSpot"] = 0
            
            # Convert to list then array as they are glm.vec3 objects
            light_data[i]["pos"] = np.array(list(light["position"]))
            light_data[i]["dir"] = np.array(list(light["direction"]))
        
        self.light_dtype = light_dtype
        self.light_data = light_data
    
    def bind(self, ctx, loc):
        self.light_buffer = ctx.buffer(self.light_data.tobytes())
        self.light_buffer.bind_to_storage_buffer(loc)


class TriangleBuffer:
    def __init__(self, material_buffer, scene):
        vertex_dtype = np.dtype([
            ("pos", *vec3),
            ("pad1", f4),
            ("uv", *vec2),
            ("pad2", *vec2),
            ("normal", *vec3),
            ("pad3", f4),
            ("tangent", *vec3),
            ("pad4", f4),
            ("bitangent", *vec3),
            ("pad5", f4),
        ])

        triangle_dtype = np.dtype([
            ("v0", vertex_dtype), ("v1", vertex_dtype), ("v2", vertex_dtype),
            ("mat", material_buffer.material_dtype),
        ])

        triangle_data = np.zeros(scene.num_triangles, dtype=triangle_dtype)
        
        idx0 = scene.triangles[:, 0]
        idx1 = scene.triangles[:, 1]
        idx2 = scene.triangles[:, 2]

        triangle_data["v0"]["pos"] = scene.vertices[idx0]
        triangle_data["v1"]["pos"] = scene.vertices[idx1]
        triangle_data["v2"]["pos"] = scene.vertices[idx2]

        triangle_data["v0"]["uv"] = scene.uvs[idx0]
        triangle_data["v1"]["uv"] = scene.uvs[idx1]
        triangle_data["v2"]["uv"] = scene.uvs[idx2]

        triangle_data["v0"]["normal"] = scene.normals[idx0]
        triangle_data["v1"]["normal"] = scene.normals[idx1]
        triangle_data["v2"]["normal"] = scene.normals[idx2]

        triangle_data["v0"]["tangent"] = scene.tangents[idx0]
        triangle_data["v1"]["tangent"] = scene.tangents[idx1]
        triangle_data["v2"]["tangent"] = scene.tangents[idx2]

        triangle_data["v0"]["bitangent"] = scene.bitangents[idx0]
        triangle_data["v1"]["bitangent"] = scene.bitangents[idx1]
        triangle_data["v2"]["bitangent"] = scene.bitangents[idx2]

        triangle_data["mat"] = material_buffer.material_data[scene.material_ids]

        self.vertex_dtype = vertex_dtype
        self.triangle_dtype = triangle_dtype
        self.triangle_data = triangle_data

    def bind(self, ctx, loc):
        self.triangle_buffer = ctx.buffer(self.triangle_data.tobytes())
        self.triangle_buffer.bind_to_storage_buffer(loc)


class BVHNodeBuffer:
    def __init__(self, scene):
        bvh_node_dtype = np.dtype([
            ("aabbMin", *vec3),
            ("leftChildIdx", i4),
            ("aabbMax", *vec3),
            ("rightChildIdx", i4),
            ("firstTriIdx", i4),
            ("triCount", i4),
            ("isLeaf", i4),
            ("pad1", f4)
        ])
        
        bvh_node_data = np.zeros(scene.num_bvh_nodes, bvh_node_dtype)

        for i, node in enumerate(scene.bvh.nodes):
            bvh_node_data[i]["aabbMin"] = node.aabb_min
            bvh_node_data[i]["aabbMax"] = node.aabb_max
            bvh_node_data[i]["leftChildIdx"] = node.left_child_idx
            bvh_node_data[i]["rightChildIdx"] = node.right_child_idx
            bvh_node_data[i]["firstTriIdx"] = node.first_tri_idx
            bvh_node_data[i]["triCount"] = node.tri_count
            bvh_node_data[i]["isLeaf"] = node.is_leaf
        
        self.bvh_node_dtype = bvh_node_dtype
        self.bvh_node_data = bvh_node_data
    
    def bind(self, ctx, loc):
        self.bvh_node_buffer = ctx.buffer(self.bvh_node_data.tobytes())
        self.bvh_node_buffer.bind_to_storage_buffer(loc)


class FullScreenQuad:
    def __init__(self, ctx, shader):
        # Full-screen quad
        self.quad_buffer = ctx.buffer(np.array([
            # Vertices    # TexCoords
            -1.0,  1.0,   0.0, 1.0,
            -1.0, -1.0,   0.0, 0.0,
            1.0,  1.0,   1.0, 1.0,
            1.0, -1.0,   1.0, 0.0,
        ], dtype=f4))

        self.vao = ctx.vertex_array(
            shader.prog,
            [
                (self.quad_buffer, "2f 2f", "aPos", "aTexCoords")
            ]
        )

    def draw(self):
        self.vao.render(moderngl.TRIANGLE_STRIP)


class PBRPass:
    def __init__(self, ctx, scene, pbr_shader):
        vertices = scene.vertices[scene.triangles]
        uvs = scene.uvs[scene.triangles]
        normals = scene.normals[scene.triangles]
        tangents = scene.tangents[scene.triangles]
        bitangents = scene.bitangents[scene.triangles]
        ids = np.repeat(scene.material_ids, 3)

        vertices = vertices.reshape(-1, 3)
        uvs = uvs.reshape(-1, 2)
        normals = normals.reshape(-1, 3)
        tangents = tangents.reshape(-1, 3)
        bitangents = bitangents.reshape(-1, 3)
        ids = ids.reshape(-1,)

        pbr_dtype = np.dtype([
            ("pos", *vec3),
            ("uv", *vec2),
            ("normal", *vec3),
            ("tangent", *vec3),
            ("bitangent", *vec3),
            ("matId", i4)
        ])

        pbr_data = np.zeros(len(vertices), dtype=pbr_dtype)

        pbr_data["pos"] = vertices
        pbr_data["uv"] = uvs
        pbr_data["normal"] = normals
        pbr_data["tangent"] = tangents
        pbr_data["bitangent"] = bitangents
        pbr_data["matId"] = ids

        pbr_vbo = ctx.buffer(pbr_data.tobytes())

        pbr_vao = ctx.vertex_array(
            pbr_shader.prog,
            [
                (
                    pbr_vbo,
                    "3f 2f 3f 3f 3f 1i",
                    "aPos", "aTexCoords", "aNormal", "aTangent", "aBitangent", "aMatId"
                )
            ]
        )

        self.pbr_data = pbr_data
        self.pbr_vao = pbr_vao

    def draw(self):
        self.pbr_vao.render(moderngl.TRIANGLES)


class BGPass:
    def __init__(self, ctx, bg_shader):
        cubemap_data = np.array([
            -1, -1, -1,   -1, -1,  1,   -1,  1,  1,
            -1, -1, -1,   -1,  1,  1,   -1,  1, -1,

            1, -1,  1,    1, -1, -1,    1,  1, -1,
            1, -1,  1,    1,  1, -1,    1,  1,  1,

            -1, -1, -1,    1, -1, -1,    1, -1,  1,
            -1, -1, -1,    1, -1,  1,   -1, -1,  1,

            -1,  1,  1,    1,  1,  1,    1,  1, -1,
            -1,  1,  1,    1,  1, -1,   -1,  1, -1,

            1, -1, -1,   -1, -1, -1,   -1,  1, -1,
            1, -1, -1,   -1,  1, -1,    1,  1, -1,

            -1, -1,  1,    1, -1,  1,    1,  1,  1,
            -1, -1,  1,    1,  1,  1,   -1,  1,  1,
        ], dtype=f4)

        bg_vbo = ctx.buffer(cubemap_data.tobytes())

        bg_vao = ctx.vertex_array(
            bg_shader.prog,
            [
                (
                    bg_vbo,
                    "3f",
                    "aPos"
                )
            ]
        )

        self.bg_data = cubemap_data
        self.bg_vbo = bg_vbo
        self.bg_vao = bg_vao
    
    def draw(self):
        self.bg_vao.render(moderngl.TRIANGLES)


if __name__ == "__main__":
    main()
