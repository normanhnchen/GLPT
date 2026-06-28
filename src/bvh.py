import numpy as np
import time


# https://jacco.ompf2.com/2022/04/13/how-to-build-a-bvh-part-1-basics/
# https://jacco.ompf2.com/2022/04/18/how-to-build-a-bvh-part-2-faster-rays/
# https://jacco.ompf2.com/2022/04/21/how-to-build-a-bvh-part-3-quick-builds/


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
        
        start_time = time.perf_counter()

        self.subdivide(self.root)

        end_time = time.perf_counter()
        print(f"BVH built in {end_time - start_time:.4f}s")
    
    def subdivide(self, node):
        if node.tri_count <= 4:
            node.is_leaf = True
            return
        
        best_axis, best_pos, best_cost = self.find_best_split(node)

        parent_cost = self.calculate_node_cost(node)

        # Less cost to not split; terminate
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
    
    def find_best_split(self, node):
        best_axis = -1
        best_pos = 0
        best_cost = np.inf

        indices = self.tri_indices[node.first_tri_idx : node.first_tri_idx + node.tri_count]
        triangles = self.scene.triangles[indices]
        centroids = self.scene.centroids[indices]
        vertices = self.scene.vertices[triangles]

        BINS = 8
        # Determine best split position using SAH
        for axis in range(3):
            c = centroids[:, axis]

            bounds_min = np.min(c)
            bounds_max = np.max(c)
            
            if bounds_min == bounds_max:
                continue

            scale = BINS / (bounds_max - bounds_min)
            
            bin_ids = np.minimum(BINS - 1, (c - bounds_min) * scale).astype(np.int32)
            # AABBs
            bin_mins = np.full((BINS, 3), np.inf)
            bin_maxs = np.full((BINS, 3), -np.inf)

            bin_tri_counts = np.bincount(bin_ids, minlength=BINS)

            # Get the minimum within each vertex
            vertices_min = np.min(vertices, axis=1)
            vertices_max = np.max(vertices, axis=1)

            np.minimum.at(bin_mins, bin_ids, vertices_min)
            np.maximum.at(bin_maxs, bin_ids, vertices_max)
            
            left_area = np.zeros(BINS - 1)
            right_area = np.zeros(BINS - 1)

            left_count = np.zeros(BINS - 1)
            right_count = np.zeros(BINS - 1)

            # AABB boxes
            lb_mins = np.full(3,  np.inf)
            lb_maxs = np.full(3, -np.inf)
            rb_mins = np.full(3,  np.inf)
            rb_maxs = np.full(3, -np.inf)

            left_sum = 0
            right_sum = 0
            
            # Gather data for the BINS - 1 planes
            for i in range(BINS - 1):
                left_sum += bin_tri_counts[i]
                left_count[i] = left_sum
                lb_mins = np.minimum(lb_mins, bin_mins[i])
                lb_maxs = np.maximum(lb_maxs, bin_maxs[i])
                left_area[i] = self.get_aabb_area(lb_mins, lb_maxs)

                right_sum += bin_tri_counts[BINS - 1 - i]
                right_count[BINS - 2 - i] = right_sum
                rb_mins = np.minimum(rb_mins, bin_mins[BINS - 2 - i])
                rb_maxs = np.maximum(rb_maxs, bin_maxs[BINS - 2 - i])
                right_area[BINS - 2 - i] = self.get_aabb_area(rb_mins, rb_maxs)
            
            # Calculate the SAH cost for the BINS - 1 planes
            scale = (bounds_max - bounds_min) / BINS
            for i in range(BINS - 1):
                if left_count[i] == 0 or right_count[i] == 0:
                    plane_cost = np.inf
                else:
                    plane_cost = left_count[i] * left_area[i] + right_count[i] * right_area[i]
                if plane_cost < best_cost:
                    best_axis = axis
                    best_pos = bounds_min + scale * (i + 1)
                    best_cost = plane_cost
        
        return best_axis, best_pos, best_cost
    
    def calculate_node_cost(self, node):
        e = node.aabb_max - node.aabb_min
        area = e[0] * e[1] + e[1] * e[2] + e[2] * e[0]
        return node.tri_count * area

    def get_aabb_area(self, aabb_min, aabb_max):
        e = aabb_max - aabb_min
        return e[0] * e[1] + e[1] * e[2] + e[2] * e[0]


class AABB:
    def __init__(self):
        self.min = np.full(3, np.inf)
        self.max = np.full(3, -np.inf)
    
    def grow(self, triangle):
        self.min = np.minimum(self.min, np.min(triangle, axis=0))
        self.max = np.maximum(self.max, np.max(triangle, axis=0))
    
    def grow_aabb(self, other_aabb):
        self.min = np.minimum(self.min, other_aabb.min)
        self.max = np.maximum(self.max, other_aabb.max)
    
    def get_area(self):
        e = self.max - self.min
        return e[0] * e[1] + e[1] * e[2] + e[2] * e[0]


class Bin:
    def __init__(self):
        self.aabb = AABB()
        self.tri_count = 0
