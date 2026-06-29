import numpy as np
from glfw.GLFW import *
import moderngl
import sys
import time
import pickle

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
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 6)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)
    # Apple system required config
    if sys.platform == "darwin":
        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE)
    
    window = glfwCreateWindow(screen.width, screen.height, "FPS: 0", None, None)

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

    # try:
    #     with open("src/assets/cache/dragon_scene.pkl", "rb") as f:
    #         scene = pickle.load(f)
    # except:
    #     scene = Scene(file_paths.scene, hdri_path=file_paths.hdri)
    #     with open("src/assets/cache/dragon_scene.pkl", "wb") as f:
    #         pickle.dump(scene, f)

    scene = Scene(file_paths.scene, hdri_path=file_paths.hdri)

    shader = Shader(
        ctx,
        file_paths.real_time.vert,
        file_paths.real_time.frag
    )

    vertices = scene.vertices[scene.triangles].astype(f4)
    uvs = scene.uvs[scene.triangles].astype(f4)
    ids = np.repeat(scene.material_ids, 3).astype(i4)

    vertices = vertices.reshape(-1, 3)
    uvs = uvs.reshape(-1, 2)
    ids = ids.reshape(-1,)

    combined_dtype = np.dtype([
        ("pos", *vec3),
        ("uv", *vec2),
        ("matId", i4)
    ])

    combined_data = np.zeros(len(vertices), dtype=combined_dtype)

    combined_data["pos"] = vertices
    combined_data["uv"] = uvs
    combined_data["matId"] = ids

    vbo = ctx.buffer(combined_data.tobytes())

    vao = ctx.vertex_array(
        shader.prog,
        [
            (vbo, "3f 2f 1i", "aPos", "aTexCoords", "aMatId")
        ]
    )

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

    material_data = np.zeros(scene.num_materials, dtype=material_dtype)

    for i, mat in enumerate(scene.materials):
        material_data[i]["baseCol"] = mat.base_color[:3]
        material_data[i]["alpha"] = mat.base_color[-1]
        material_data[i]["roughness"] = mat.roughness
        material_data[i]["emissive"] = mat.emissive_color
        material_data[i]["metallic"] = mat.metallic

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
        
    material_buffer = ctx.buffer(material_data.tobytes())
    material_buffer.bind_to_storage_buffer(0)

    scene.create_texture_arrays(ctx, 1024, 1024)
    scene.bind_texture_arrays()
    
    last_frame_start = 0
    stats_start_time = time.perf_counter()

    avg_fps = 0

    stats_frame_count = 0

    ctx.enable(moderngl.DEPTH_TEST)

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
        
        update_stats(window, avg_fps)

        process_input(window, delta_time)

        ctx.clear(0, 0, 0, 1)

        shader.prog["view"].write(camera.get_view().to_bytes())
        shader.prog["projection"].write(camera.get_perspective().to_bytes())
        
        vao.render(moderngl.TRIANGLES)

        glfwSwapBuffers(window)
        glfwPollEvents()

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


def update_stats(window, fps):
    glfwSetWindowTitle(
        window,
        f"FPS: {fps:.2f}"
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
