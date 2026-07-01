import numpy as np
from numba import njit, prange


# https://jacco.ompf2.com/2022/04/13/how-to-build-a-bvh-part-1-basics/
# https://jacco.ompf2.com/2022/04/18/how-to-build-a-bvh-part-2-faster-rays/
# https://jacco.ompf2.com/2022/04/21/how-to-build-a-bvh-part-3-quick-builds/


class BVH:
    def __init__(self, scene):
        self.scene = scene

        max_nodes = 2 * scene.num_triangles

        # Preallocate all lists
        self.aabb_mins = np.zeros((max_nodes, 3), dtype=np.float32)
        self.aabb_maxs = np.zeros((max_nodes, 3), dtype=np.float32)
        self.left_child_indices = np.full(max_nodes, -1, dtype=np.int32)
        self.right_child_indices = np.full(max_nodes, -1, dtype=np.int32)
        self.first_tri_indices = np.zeros(max_nodes, dtype=np.int32)
        self.tri_counts = np.zeros(max_nodes, dtype=np.int32)
        self.is_leafs = np.zeros(max_nodes, dtype=np.int32)

        self.nodes_used = 0

        # Build the root node
        self.aabb_mins[0] = np.min(scene.vertices, axis=0)
        self.aabb_maxs[0] = np.max(scene.vertices, axis=0)
        self.first_tri_indices[0] = 0
        self.tri_counts[0] = scene.num_triangles

        self.nodes_used += 1

        self.tri_indices = np.arange(scene.num_triangles)
        
        self.subdivide(0)

        # Truncate to only the used parts of the list
        self.aabb_mins = self.aabb_mins[:self.nodes_used]
        self.aabb_maxs = self.aabb_maxs[:self.nodes_used]
        self.left_child_indices = self.left_child_indices[:self.nodes_used]
        self.first_tri_indices = self.first_tri_indices[:self.nodes_used]
        self.tri_counts = self.tri_counts[:self.nodes_used]
        self.is_leafs = self.is_leafs[:self.nodes_used]
    
    def subdivide(self, node_idx):
        if self.tri_counts[node_idx] <= 4:
            self.is_leafs[node_idx] = 1
            return
        
        indices = self.tri_indices[self.first_tri_indices[node_idx] : self.first_tri_indices[node_idx] + self.tri_counts[node_idx]]
        triangles = self.scene.triangles[indices]
        centroids = self.scene.centroids[indices]
        vertices = self.scene.vertices[triangles]
        
        best_axis, best_pos, best_cost = find_best_split(centroids, vertices)

        parent_cost = self.calculate_node_cost(node_idx)

        # Less cost to not split; terminate
        if (best_cost >= parent_cost):
            self.is_leafs[node_idx] = 1
            return
                
        axis = best_axis
        split_pos = best_pos
        
        i = self.first_tri_indices[node_idx]
        j = i + self.tri_counts[node_idx] - 1
        while i <= j:
            tri_idx = self.tri_indices[i]
            if self.scene.centroids[tri_idx][axis] < split_pos:
                i += 1
            else:
                # Swap triangle indices
                self.tri_indices[[i, j]] = self.tri_indices[[j, i]]
                j -= 1
        
        # Stop if one of the sides are empty
        left_count = i - self.first_tri_indices[node_idx]
        if left_count == 0 or left_count == self.tri_counts[node_idx]:
            self.is_leafs[node_idx] = 1
            return

        left_child_idx = self.nodes_used

        self.first_tri_indices[left_child_idx] = self.first_tri_indices[node_idx]
        self.tri_counts[left_child_idx] = left_count
        self.update_node_bounds(left_child_idx)

        self.nodes_used += 1

        self.left_child_indices[node_idx] = left_child_idx

        self.subdivide(left_child_idx)

        right_child_idx = self.nodes_used

        self.first_tri_indices[right_child_idx] = i
        self.tri_counts[right_child_idx] = self.tri_counts[node_idx] - left_count
        self.update_node_bounds(right_child_idx)

        self.nodes_used += 1

        self.right_child_indices[node_idx] = right_child_idx

        self.subdivide(right_child_idx)
        
    def update_node_bounds(self, node_idx):
        indices = self.tri_indices[self.first_tri_indices[node_idx] : self.first_tri_indices[node_idx] + self.tri_counts[node_idx]]
        tri_verts = self.scene.vertices[self.scene.triangles[indices]]
        self.aabb_mins[node_idx] = np.min(tri_verts, axis=(0, 1))
        self.aabb_maxs[node_idx] = np.max(tri_verts, axis=(0, 1))
    
    def calculate_node_cost(self, node_idx):
        e = self.aabb_maxs[node_idx] - self.aabb_mins[node_idx]
        area = e[0] * e[1] + e[1] * e[2] + e[2] * e[0]
        return self.tri_counts[node_idx] * area


@njit(nogil=True, fastmath=True, parallel=True)
def find_best_split(centroids, vertices):
    BINS = 8

    costs_per_axis = np.zeros(3, dtype=np.float32)
    pos_per_axis = np.zeros(3, dtype=np.float32)

    # Determine best split position using SAH
    for axis in prange(3):
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

        # Populate the bins
        for i in range(len(c)):
            bin_idx = int(min(BINS - 1, (c[i] - bounds_min) * scale))

            v0 = vertices[i][0]
            v1 = vertices[i][1]
            v2 = vertices[i][2]

            # Update the AABB for this bin
            for j in range(3):
                tri_min = min(v0[j], v1[j], v2[j])
                tri_max = max(v0[j], v1[j], v2[j])

                if tri_min < bin_mins[bin_idx, j]:
                    bin_mins[bin_idx, j] = tri_min
                if tri_max > bin_maxs[bin_idx, j]:
                    bin_maxs[bin_idx, j] = tri_max
        
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
            for j in range(3):
                if bin_mins[i, j] < lb_mins[j]:
                    lb_mins[j] = bin_mins[i, j]
                if bin_maxs[i, j] > lb_maxs[j]:
                    lb_maxs[j] = bin_maxs[i, j]
            left_area[i] = get_aabb_area(lb_mins, lb_maxs)

            right_sum += bin_tri_counts[BINS - 1 - i]
            right_count[BINS - 2 - i] = right_sum
            rb_mins = np.minimum(rb_mins, bin_mins[BINS - 2 - i])
            rb_maxs = np.maximum(rb_maxs, bin_maxs[BINS - 2 - i])
            right_area[BINS - 2 - i] = get_aabb_area(rb_mins, rb_maxs)
        
        best_pos = 0
        best_cost = np.inf

        # Calculate the SAH cost for the BINS - 1 planes
        scale = (bounds_max - bounds_min) / BINS
        for i in range(BINS - 1):
            if left_count[i] == 0 or right_count[i] == 0:
                plane_cost = np.inf
            else:
                plane_cost = left_count[i] * left_area[i] + right_count[i] * right_area[i]
            if plane_cost < best_cost:
                best_pos = bounds_min + scale * (i + 1)
                best_cost = plane_cost
        
        costs_per_axis[axis] = best_cost
        pos_per_axis[axis] = best_pos
    
    best_axis = -1
    best_pos = 0
    best_cost = np.inf

    for axis in range(3):
        if costs_per_axis[axis] < best_cost:
            best_axis = axis
            best_pos = pos_per_axis[axis]
            best_cost = costs_per_axis[axis]
    
    return best_axis, best_pos, best_cost


@njit(fastmath=True)
def get_aabb_area(aabb_min, aabb_max):
    e = aabb_max - aabb_min
    return e[0] * e[1] + e[1] * e[2] + e[2] * e[0]
