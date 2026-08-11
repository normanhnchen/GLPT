import glm

from src.settings import camera_settings, screen


# Defines several possible options for camera movement
# Used as abstraction to stay away from window-system specific input methods
class CameraMovement:
    FORWARD = 0
    BACKWARD = 1
    LEFT = 2
    RIGHT = 3
    UP = 4
    DOWN = 5


# An abstract camera class that processes input
# Calculates the corresponding Euler Angles, Vectors and Matrices for use in OpenGL
class Camera:
    def __init__(
            self,
            pos=camera_settings.pos,
            front=camera_settings._front,
            up=camera_settings._up,
            right=None,
            world_up=camera_settings._world_up,
            yaw=camera_settings._yaw,
            pitch=camera_settings._pitch,
            movement_speed=camera_settings.movement_speed,
            mouse_sensitivity=camera_settings.mouse_sensitivity,
            fov=camera_settings.fov,
            blur=camera_settings.blur,
            dof_enabled=camera_settings.dof_enabled,
            aperture=camera_settings.aperture,
            focus_dist=camera_settings.focus_dist
        ):
        self.pos = pos
        self.front = front
        self.up = up
        self.right = right
        self.world_up = world_up
        # Euler angles
        self.yaw = yaw
        self.pitch = pitch
        # Camera options
        self.movement_speed = movement_speed
        self.mouse_sensitivity = mouse_sensitivity
        self.fov = fov

        self.blur = blur
        self.dof_enabled = dof_enabled
        self.aperture = aperture
        self.focus_dist = focus_dist

        self._update_camera_vectors()

        self.last_state = self.get_state()
    
    def get_view_matrix(self):
        return glm.lookAt(self.pos, self.pos + self.front, self.up)

    def process_keyboard(self, direction, delta_time):
        velocity = self.movement_speed * delta_time
        if direction == CameraMovement.FORWARD:
            self.pos += self.front * velocity
        elif direction == CameraMovement.BACKWARD:
            self.pos -= self.front * velocity
        elif direction == CameraMovement.LEFT:
            self.pos -= self.right * velocity
        elif direction == CameraMovement.RIGHT:
            self.pos += self.right * velocity
        elif direction == CameraMovement.UP:
            self.pos += self.world_up * velocity
        elif direction == CameraMovement.DOWN:
            self.pos -= self.world_up * velocity
    
    def process_mouse_movement(self, xoffset, yoffset, constrain_pitch=True):
        xoffset *= self.mouse_sensitivity
        yoffset *= self.mouse_sensitivity

        self.yaw += xoffset
        self.pitch += yoffset

        # Make sure that when pitch is out of bounds, screen doesn't get flipped
        if constrain_pitch:
            if self.pitch > 89.99:
                self.pitch = 89.99
            elif self.pitch < -89.99:
                self.pitch = -89.99
        
        # Update front, right and up Vectors using the updated Euler angles
        self._update_camera_vectors()
    
    def process_mouse_scroll(self, yoffset):
        self.fov -= yoffset
        if self.fov < 1:
            self.fov = 1
        elif self.fov > 135:
            self.fov = 135

    def set_orientation(self, yaw=None, pitch=None, constrain_pitch=True):
        if yaw is not None:
            self.yaw = yaw
        if pitch is not None:
            self.pitch = pitch
        
            # Make sure that when pitch is out of bounds, screen doesn't get flipped
            if constrain_pitch:
                if self.pitch > 89.99:
                    self.pitch = 89.99
                elif self.pitch < -89.99:
                    self.pitch = -89.99
        
        # Update front, right and up Vectors using the updated Euler angles
        self._update_camera_vectors()

    def _update_camera_vectors(self):
        # Calculate the new front vector
        self.front = glm.vec3()
        self.front.x = glm.cos(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        self.front.y = glm.sin(glm.radians(self.pitch))
        self.front.z = glm.sin(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        self.front = glm.normalize(self.front)
        # Also re-calculate the Right and Up vector
        self.right = glm.normalize(glm.cross(self.front, self.world_up))
        self.up = glm.normalize(glm.cross(self.right, self.front))

    def get_state(self):
        return {
            "pos": list(self.pos),
            "yaw": self.yaw,
            "pitch": self.pitch,
            "fov": self.fov,
            "dof_enabled": self.dof_enabled,
            "aperture": self.aperture,
            "focus_dist": self.focus_dist,
            "blur": self.blur,
        }

    def load_state(self, state):
        self.pos = glm.vec3(state["pos"])
        self.yaw = state["yaw"]
        self.pitch = state["pitch"]
        self.fov = state["fov"]
        self.dof_enabled = state["dof_enabled"]
        self.aperture = state["aperture"]
        self.focus_dist = state["focus_dist"]
        self.blur = state["blur"]

        self._update_camera_vectors()
    
    def has_moved(self):
        current_state = self.get_state()
        if self.last_state != current_state:
            self.last_state = current_state
            return True
        return False

    def get_perspective(self):
        near = 0.01
        far = 1000
        return glm.perspective(glm.radians(self.fov), screen.width / screen.height, near, far)

    def get_view(self):
        return glm.lookAt(self.pos, self.pos + self.front, self.up)
