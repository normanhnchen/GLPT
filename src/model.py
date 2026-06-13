import trimesh


class Scene:
    def __init__(self, file_path):
        scene = trimesh.load(file_path)
        self.scene = scene.to_mesh()
        self.vertices = self.scene.vertices.astype("f4")
        self.face_indices = self.scene.faces.astype("i4")
