import numpy as np
import cv2

from src.settings import settings
from src.dtypes import *


class HDRI:
    def __init__(self, hdri_path):
        if hdri_path:
            img = cv2.imread(hdri_path, cv2.IMREAD_UNCHANGED)
            # Convert from OpenCV default format of BGR color to RGB color
            self.img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            self.height, self.width, self.channels = self.img.shape
            self.img_bytes = self.img.tobytes()

        else:
            self.height, self.width, self.channels = 1, 1, 3
            self.img = np.full((self.height, self.width, self.channels), settings.path_tracing.default_hdri_color, dtype=f4)
            self.img_bytes = self.img.tobytes()

        self.hdri_tex = None

        self._build_hdri_distribution()

    # See 7.3 HDRI Sampling
    def _build_hdri_distribution(self):
        img = self.img.astype(np.float64)
        luminance = img[:, :, 0] * 0.2126 + img[:, :, 1] * 0.7152 + img[:, :, 2] * 0.0722

        # Adjust for equirectangular map spherical distortion
        theta = (np.arange(self.height) + 0.5) / self.height * np.pi
        sin_theta = np.sin(theta)[:, None]
        weighted = luminance * sin_theta

        # Build the CDFs
        # --------------
        # Marginal distribution over rows
        row_sums = weighted.sum(axis=1)
        row_cdf = np.cumsum(row_sums)
        row_cdf /= row_cdf[-1]

        # Conditional distribution over column given a row
        col_cdf = np.cumsum(weighted, axis=1)
        col_cdf /= col_cdf[:, -1:]

        self.row_cdf = row_cdf.astype(f4)
        self.col_cdf = col_cdf.astype(f4)
    
    def bind_img(self, ctx, loc):
        self.hdri_tex = ctx.texture(
            (self.width, self.height),
            self.channels,
            self.img_bytes,
            dtype=f4
            )
        self.hdri_tex.use(location=loc)

    def bind_cdfs(self, ctx, row_loc, col_loc):
        row_height = self.row_cdf.shape[0]
        col_height, col_width = self.col_cdf.shape

        self.row_cdf_tex = ctx.texture(
            (1, row_height),
            1,
            self.row_cdf.tobytes(),
            dtype=f4
        )
        self.col_cdf_tex = ctx.texture(
            (col_width, col_height),
            1,
            self.col_cdf.tobytes(),
            dtype=f4
        )

        self.row_cdf_tex.use(location=row_loc)
        self.col_cdf_tex.use(location=col_loc)
    
    def release(self):
        if self.hdri_tex is not None:
            self.hdri_tex.release()

    def snapshot_original(self):
        """
        Create a snapshot of the original image before scrambling.
        Only used for AI training.
        """
        
        self._original_img = self.img.copy()

    def _reset(self):
        """
        Restore this HDRI to its original (un-scrambled) image.
        Only used for AI training.
        """

        self.img = self._original_img.copy()
        self.img_bytes = self.img.tobytes()

    # See 9.4 Rendering
    def scramble(self):
        """
        Randomize HDRI rotation, emissive strength, and color.
        Only used for AI training.
        """

        self._reset()

        random_rot = np.random.uniform(0, 2 * np.pi, 3).astype(f4)
        random_exposure_factor = set_f4(np.random.uniform(0.1, 10))
        random_color_factor = np.random.uniform(0, 2, 3).astype(f4)

        u = (np.arange(self.width) + 0.5) / self.width
        v = (np.arange(self.height) + 0.5) / self.height

        theta, phi = self._uv_to_spherical(u, v)
        x, y, z = self._spherical_to_cartesian(theta, phi)

        rot_mat = self._rotation_matrix(*random_rot)
        # Transform the matrix since numpy is row-major, the matrix is column-major
        rotated = np.stack([x, y, z], axis=-1) @ rot_mat.T

        x = rotated[..., 0]
        y = rotated[..., 1]
        z = rotated[..., 2]

        theta, phi = self._cartesian_to_spherical(x, y, z)

        u, v = self._spherical_to_uv(theta, phi)
        x_map = (u * self.width).astype(f4)
        y_map = (v * self.height).astype(f4)

        rotated_img = cv2.remap(
            self._original_img,
            x_map, y_map,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_WRAP,
        )

        self.img = rotated_img * random_exposure_factor * random_color_factor
        self.img_bytes = self.img.tobytes()

        # Rebuild alias tables based on the new HDRI
        self._build_hdri_distribution()

    def _uv_to_spherical(self, u, v):
        # Azimuthal [-π, π]
        phi = (u - 0.5) * 2 * np.pi
        # Zenith [0, π]
        theta = v * np.pi

        return theta, phi

    def _spherical_to_cartesian(self, theta, phi):
        theta_grid, phi_grid = np.meshgrid(theta, phi, indexing="ij")

        x = np.sin(theta_grid) * np.cos(phi_grid)
        y = np.cos(theta_grid)
        z = np.sin(theta_grid) * np.sin(phi_grid)

        return x, y, z

    def _cartesian_to_spherical(self, x, y, z):
        # Prevent floating point error
        y = np.clip(y, -1, 1)

        theta = np.arccos(y)
        phi = np.arctan2(z, x)

        return theta, phi

    def _rotation_matrix(self, pitch_rad, yaw_rad, roll_rad):
        p = pitch_rad
        y = yaw_rad
        r = roll_rad

        R_pitch = np.array([
            [1, 0, 0],
            [0, np.cos(p), -np.sin(p)],
            [0, np.sin(p), np.cos(p)]
        ])

        R_roll = np.array([
            [np.cos(r), -np.sin(r), 0],
            [np.sin(r), np.cos(r), 0],
            [0, 0, 1]
        ])

        R_yaw = np.array([
            [np.cos(y), 0, np.sin(y)],
            [0, 1, 0],
            [-np.sin(y), 0, np.cos(y)]
        ])

        return R_yaw @ R_pitch @ R_roll

    def _spherical_to_uv(self, theta, phi):
        u = phi / (2 * np.pi) + 0.5
        v = theta / np.pi

        return u, v

    def update_img(self):
        """
        Update the HDRI image buffer after scrambling.
        Only used for AI training.
        """

        self.hdri_tex.write(self.img_bytes)

    def update_cdfs(self):
        """
        Update the CDF buffers after scrambling.
        Only used for AI training.
        """
        
        self.row_cdf_tex.write(self.row_cdf.tobytes())
        self.col_cdf_tex.write(self.col_cdf.tobytes())
