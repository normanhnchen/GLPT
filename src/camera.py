import glm


# Defines several possible options for camera movement
# Used as abstraction to stay away from window-system specific input methods
class CameraMovement:
    FORWARD = 0
    BACKWARD = 1
    LEFT = 2
    RIGHT = 3


# Default camera values
YAW = 90
PITCH = 0
SPEED = 2.5
SENSITIVITY = 0.1
FOV = 45


# An abstract camera class that processes input
# calculates the corresponding Euler Angles, Vectors and Matrices for use in OpenGL
class Camera:
    def __init__(
            self,
            pos=glm.vec3(0, 0, 0),
            front=glm.vec3(0, 0, -1),
            up=glm.vec3(0, 1, 0),
            right=None,
            world_up=glm.vec3(0, 1, 0),
            yaw=YAW,
            pitch=PITCH,
            movement_speed=SPEED,
            mouse_sensitivity=SENSITIVITY,
            fov=FOV
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

        self._update_camera_vectors()
    
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
        
        # Update Front, Right and Up Vectors using the updated Euler angles
        self._update_camera_vectors()
    
    def process_mouse_scroll(self, yoffset):
        self.fov -= yoffset
        if self.fov < 1:
            self.fov = 1
        elif self.fov > 45:
            self.fov = 45

    def _update_camera_vectors(self):
        # Calculate the new Front vector
        self.front = glm.vec3()
        self.front.x = glm.cos(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        self.front.y = glm.sin(glm.radians(self.pitch))
        self.front.z = glm.sin(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        self.front = glm.normalize(self.front)
        # Also re-calculate the Right and Up vector
        self.right = glm.normalize(glm.cross(self.front, self.world_up))
        self.up = glm.normalize(glm.cross(self.right, self.front))
