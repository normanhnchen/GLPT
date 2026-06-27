import numpy as np


# https://jacco.ompf2.com/2022/04/13/how-to-build-a-bvh-part-1-basics/
# https://jacco.ompf2.com/2022/04/18/how-to-build-a-bvh-part-2-faster-rays/


class BVHNode:
    aabb_min = None
    aabb_max = None
    left_child_idx = -1
    right_child_idx = -1
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

        self.nodes = [self.root]
        self.tri_indices = np.arange(scene.num_triangles)

        self.subdivide(self.root)
    
    def subdivide(self, node):
        if node.tri_count <= 4:
            node.is_leaf = True
            return

        best_axis = -1
        best_pos = 0
        best_cost = np.inf

        # Determine best split position using SAH
        for axis in range(3):
            for i in range(node.tri_count):
                tri_idx = self.tri_indices[i]
                centroid_pos = self.scene.centroids[tri_idx][axis]
                cost = self.evaluate_SAH(node, axis, centroid_pos)
                if cost < best_cost:
                    best_pos = centroid_pos
                    best_axis = axis
                    best_cost = cost

        # Extent of the parent
        e = node.aabb_max - node.aabb_min
        parent_area = e[0] * e[1] + e[1] * e[2] + e[2] * e[0]
        parent_cost = node.tri_count * parent_area

        if (best_cost >= parent_cost):
            node.is_leaf = True
            return
                
        axis = best_axis
        split_pos = best_pos
        
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
        
        # Stop if one of the sides are empty
        left_count = i - node.first_tri_idx
        if left_count == 0 or left_count == node.tri_count:
            node.is_leaf = True
            return

        left_child = BVHNode()

        left_child.first_tri_idx = node.first_tri_idx
        left_child.tri_count = left_count
        self.update_node_bounds(left_child)

        left_idx = len(self.nodes)
        self.nodes.append(left_child)

        node.left_child_idx = left_idx

        self.subdivide(left_child)

        right_child = BVHNode()

        right_child.first_tri_idx = i
        right_child.tri_count = node.tri_count - left_count
        self.update_node_bounds(right_child)

        right_idx = len(self.nodes)
        self.nodes.append(right_child)

        node.right_child_idx = right_idx

        self.subdivide(right_child)
        
    def update_node_bounds(self, node):
        indices = self.tri_indices[node.first_tri_idx : node.first_tri_idx + node.tri_count]
        tri_verts = self.scene.vertices[self.scene.triangles[indices]]
        node.aabb_min = np.min(tri_verts, axis=(0, 1))
        node.aabb_max = np.max(tri_verts, axis=(0, 1))
    
    def evaluate_SAH(self, node, axis, pos):
        left_box = AABB()
        right_box = AABB()

        left_count = 0
        right_count = 0

        for i in range(node.tri_count):
            tri_idx = self.tri_indices[node.first_tri_idx + i]
            tri = self.scene.triangles[tri_idx]
            vertices = self.scene.vertices[tri]
            centroid = self.scene.centroids[tri_idx]
            if centroid[axis] < pos:
                left_box.grow(vertices)
                left_count += 1
            else:
                right_box.grow(vertices)
                right_count += 1
        
        cost = left_count * left_box.get_area() + right_count * right_box.get_area()

        if cost > 0:
            return cost
        return np.inf


class AABB:
    def __init__(self):
        self.min = np.full(3, np.inf)
        self.max = np.full(3, -np.inf)
    
    def grow(self, triangle):
        self.min = np.minimum(self.min, np.min(triangle, axis=0))
        self.max = np.maximum(self.max, np.max(triangle, axis=0))
    
    def get_area(self):
        e = self.max - self.min
        return e[0] * e[1] + e[1] * e[2] + e[2] * e[0]
