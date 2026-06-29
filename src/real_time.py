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

    pbr_shader = Shader(
        ctx,
        file_paths.pbr.vert,
        file_paths.pbr.frag
    )
    bg_shader = Shader(
        ctx,
        file_paths.background.vert,
        file_paths.background.frag
    )

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

    # NOTE: std140 or std430 blocks are padded to multiples of 16 bytes

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

    light_data = np.zeros(scene.num_lights, dtype=light_dtype)

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

    material_buffer = ctx.buffer(material_data.tobytes())
    material_buffer.bind_to_storage_buffer(0)

    light_buffer = ctx.buffer(light_data.tobytes())
    light_buffer.bind_to_storage_buffer(1)

    scene.create_texture_arrays(ctx, 1024, 1024)
    scene.bind_texture_arrays()

    scene.hdri.bind(ctx, 6)
    
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

        # --- Background shader ---
        
        ctx.depth_func = "<="

        # Vertex shader uniforms
        bg_shader.prog["view"].write(camera.get_view().to_bytes())
        bg_shader.prog["projection"].write(camera.get_perspective().to_bytes())

        bg_vao.render(moderngl.TRIANGLES)

        ctx.depth_func = "<"

        # --- PBR shader ---

        # Vertex shader uniforms
        pbr_shader.prog["view"].write(camera.get_view().to_bytes())
        pbr_shader.prog["projection"].write(camera.get_perspective().to_bytes())

        # Fragment shader uniforms
        pbr_shader.prog["numLights"].value = set_i4(scene.num_lights)
        pbr_shader.prog["cameraPos"].value = camera.pos

        pbr_vao.render(moderngl.TRIANGLES)

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
