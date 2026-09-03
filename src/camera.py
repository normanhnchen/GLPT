import glm
import random
import math

from src.settings import settings


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
            pos=settings.camera.pos,
            front=settings.camera.front,
            up=settings.camera.up,
            right=None,
            world_up=settings.camera.world_up,
            yaw=settings.camera.yaw,
            pitch=settings.camera.pitch,
            movement_speed=settings.camera.movement_speed,
            mouse_sensitivity=settings.camera.mouse_sensitivity,
            fov=settings.camera.fov,
            blur=settings.camera.blur,
            dof_enabled=settings.camera.dof_enabled,
            aperture=settings.camera.aperture,
            focus_dist=settings.camera.focus_dist
        ):
        self.pos = glm.vec3(pos)
        self.front = glm.vec3(front)
        self.up = glm.vec3(up)
        self.right = right
        self.world_up = glm.vec3(world_up)
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
    
    def process_mouse_movement(self, xoffset, yoffset, constrainpitch=True):
        xoffset *= self.mouse_sensitivity
        yoffset *= self.mouse_sensitivity

        self.yaw += xoffset
        self.pitch += yoffset

        # Make sure that when pitch is out of bounds, screen doesn't get flipped
        if constrainpitch:
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

    def set_orientation(self, yaw=None, pitch=None, constrainpitch=True):
        if yaw is not None:
            self.yaw = yaw
        if pitch is not None:
            self.pitch = pitch
        
            # Make sure that when pitch is out of bounds, screen doesn't get flipped
            if constrainpitch:
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

    def load_state(self, state, randomize=False):
        self.pos = glm.vec3(state["pos"])
        self.yaw = state["yaw"]
        self.pitch = state["pitch"]
        self.fov = state["fov"]

        if randomize:
            # Randomize all camera DOF and blur properties
            # Only used for AI training

            self.blur = 1
            self.dof_enabled = False
            self.aperture = 0
            self.focus_dist = state["focus_dist"]

            if random.random() < 0.5:
                if random.random() < 0.9:
                    self.blur = random.uniform(0, 2)
                
                else:
                    self.blur = math.exp(random.uniform(math.log(2), math.log(10)))

            if random.random() < 0.1:
                self.dof_enabled = True
                self.aperture = math.exp(random.uniform(math.log(0.01), math.log(0.99)))
                self.focus_dist = random.uniform(1, 50)
        
        else:
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
        return glm.perspective(glm.radians(self.fov), settings.screen.width / settings.screen.height, near, far)

    def get_view(self):
        return glm.lookAt(self.pos, self.pos + self.front, self.up)

    def reload_from_settings(self):
        self.pos = glm.vec3(settings.camera.pos)
        self.front = glm.vec3(settings.camera.front)
        self.up = glm.vec3(settings.camera.up)
        self.right = None
        self.world_up = glm.vec3(settings.camera.world_up)
        self.yaw = settings.camera.yaw
        self.pitch = settings.camera.pitch
        self.movement_speed = settings.camera.movement_speed
        self.mouse_sensitivity = settings.camera.mouse_sensitivity
        self.fov = settings.camera.fov
        self.blur = settings.camera.blur
        self.dof_enabled = settings.camera.dof_enabled
        self.aperture = settings.camera.aperture
        self.focus_dist = settings.camera.focus_dist

        self._update_camera_vectors()
