import numpy as np
from glfw.GLFW import *
import moderngl
import sys
import time

from src.settings import *
from src.dtypes import *
from src.shader import *
from src.camera import *
from src.model import *


camera = Camera()


first_mouse = True
last_x = screen.width / 2
last_y = screen.height / 2


def main():
    if not glfwInit():
        return "Failed to initialize GLFW"

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4)
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 4)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)
    # Apple system required config
    if sys.platform == "darwin":
        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE)
    
    window = glfwCreateWindow(screen.width, screen.height, "FPS: 0 | Samples: 0", None, None)

    if not window:
        return "Failed to create GLFW window"
    
    glfwMakeContextCurrent(window)
    glfwSetCursorPosCallback(window, mouse_callback)
    glfwSetScrollCallback(window, scroll_callback)
    glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
    if screen.vsync == True:
        glfwSwapInterval(1)
    else:
        glfwSwapInterval(0)

    ctx = moderngl.create_context()

    scene = Scene("src/assets/glass_test.glb")

    shader = Shader(
        ctx,
        "src/shaders/render.vs",
        "src/shaders/render.fs"
    )
    compute_shader = ComputeShader(
        ctx,
        "src/shaders/render.comp"
    )

    compute_texture = ctx.texture(screen.resolution, 4, dtype=f4)

    # Full-screen quad
    quad_buffer = ctx.buffer(np.array([
        # Vertices    # TexCoords
        -1.0,  1.0,   0.0, 1.0,
        -1.0, -1.0,   0.0, 0.0,
         1.0,  1.0,   1.0, 1.0,
         1.0, -1.0,   1.0, 0.0,
    ], dtype=f4))

    vao = ctx.vertex_array(
        shader.prog,
        [
            [quad_buffer, "2f 2f", "aPos", "aTexCoords"]
        ]
    )

    # NOTE: std140 or std430 blocks are padded to multiples of 16 bytes

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

    material_dtype = np.dtype([
        ("baseCol", *vec3),
        ("alpha", f4),
        ("emissive", *vec3),
        ("metallic", f4),
        ("roughness", f4),
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
    ])

    triangle_dtype = np.dtype([
        ("v0", vertex_dtype), ("v1", vertex_dtype), ("v2", vertex_dtype),
        ("mat", material_dtype),
    ])

    material_data = np.zeros(scene.num_materials, dtype=material_dtype)

    for i, mat in enumerate(scene.materials):
        material_data[i]["baseCol"] = mat.base_color[:3]
        material_data[i]["alpha"] = mat.base_color[-1]
        material_data[i]["roughness"] = mat.roughness
        material_data[i]["emissive"] = mat.emissive_color
        material_data[i]["metallic"] = mat.metallic

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

    triangle_data["mat"] = material_data[scene.material_ids]

    camera_buffer = ctx.buffer(camera_data.tobytes())
    camera_buffer.bind_to_storage_buffer(0)

    triangle_buffer = ctx.buffer(triangle_data.tobytes())
    triangle_buffer.bind_to_storage_buffer(1)

    material_buffer = ctx.buffer(material_data.tobytes())
    material_buffer.bind_to_storage_buffer(2)

    scene.create_texture_arrays(ctx, 1024, 1024)
    scene.bind_texture_arrays()
    
    last_frame_start = 0
    stats_start_time = time.perf_counter()

    avg_fps = 0

    total_samples = 0
    stats_frame_count = 0

    should_render = True

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

        process_input(window, delta_time)

        ctx.clear(0, 0, 0, 1)

        if camera.has_moved():
            total_samples = 0
            should_render = True
        
        if total_samples >= pt_settings.max_samples:
            should_render = False
        
        if should_render:
            # Update camera data
            camera_data["pos"] = camera.pos
            camera_data["front"] = camera.front
            camera_data["up"] = camera.up
            camera_data["right"] = camera.right
            camera_data["fov"] = camera.fov

            camera_buffer.write(camera_data.tobytes())

            compute_shader.prog["totalSamples"].value = total_samples
            compute_shader.prog["numTriangles"].value = scene.num_triangles
            compute_shader.prog["maxDepth"].value = pt_settings.max_depth

            compute_shader.prog["blur"].value = post_process_settings.blur

            # Apply ceiling function
            # Allows the GPU to reach the entire screen despite different screen resolutions
            local_size_x = (screen.width + 15) // 16
            local_size_y = (screen.height + 15) // 16
            
            # Run compute shader
            compute_texture.bind_to_image(0, read=True, write=True)
            compute_shader.prog.run(local_size_x, local_size_y)
        
        # Draw to screen
        compute_texture.use(location=0)

        shader.prog["exposure"].value = 1.0
        
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
        shader.set_tonemap("None")
        
        vao.render(moderngl.TRIANGLE_STRIP)

        glfwSwapBuffers(window)
        glfwPollEvents()

        if should_render:
            total_samples += 1
        stats_frame_count += 1

        cap_fps(frame_start, screen.fps_cap)
    
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
    glfwSetWindowTitle(
        window,
        f"FPS: {fps:.2f} | Samples: {samples}"
    )


def process_input(window, delta_time):
    if glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS:
        glfwSetWindowShouldClose(window, True)
    
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


def mouse_callback(window, xpos, ypos):
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
    camera.process_mouse_scroll(yoffset)


if __name__ == "__main__":
    main()
