from src.model import *


scene = Scene("src/assets/cornell_box.glb")


# https://jacco.ompf2.com/2022/04/13/how-to-build-a-bvh-part-1-basics/

class BVHNode:
    aabb_min = None
    aabb_max = None
    left_node = None
    right_node = None
    first_tri_idx = None
    tri_count = None
    is_leaf = False


class BVH:
    def __init__(self, scene):
        self.scene = scene

        self.root = BVHNode()
        self.root.aabb_max = np.max(scene.vertices, axis=0)
        self.root.aabb_min = np.min(scene.vertices, axis=0)
        self.root.first_tri_idx = 0
        self.root.tri_count = scene.num_triangles

        self.node_idx = 0
        self.nodes = [self.root]
        self.tri_indices = np.arange(scene.num_triangles)

        self.subdivide(self.root)
    
    def subdivide(self, node):
        if node.tri_count <= 2:
            print(f"LEAF: tri_count={node.tri_count}")
            return

        extent = node.aabb_max - node.aabb_min
        axis = np.argmax(extent)

        indices = self.tri_indices[node.first_tri_idx : node.first_tri_idx + node.tri_count]
        split_pos = np.mean(self.scene.centroids[indices, axis])
        
        i = node.first_tri_idx
        j = i + node.tri_count - 1
        while i <= j:
            tri_idx = self.tri_indices[i]
            if self.scene.centroids[tri_idx][axis] < split_pos:
                i += 1
            else:
                # Swap triangle indices
                self.tri_indices[[i, j]] = self.tri_indices[[j, i]]
                j -= 1
        left_count = i - node.first_tri_idx
        if left_count == 0 or left_count == node.tri_count:
            return

        left_child = BVHNode()
        right_child = BVHNode()

        left_child.first_tri_idx = node.first_tri_idx
        left_child.tri_count = left_count
        right_child.first_tri_idx = i
        right_child.tri_count = node.tri_count - left_count

        self.update_node_bounds(left_child)
        self.update_node_bounds(right_child)

        node.left_node = left_child
        node.right_node = right_child

        self.subdivide(left_child)
        self.subdivide(right_child)
        
    def update_node_bounds(self, node):
        indices = self.tri_indices[node.first_tri_idx : node.first_tri_idx + node.tri_count]
        tri_verts = self.scene.vertices[self.scene.triangles[indices]]
        node.aabb_min = np.min(tri_verts, axis=(0, 1))
        node.aabb_max = np.max(tri_verts, axis=(0, 1))


bvh = BVH(scene)
