#ifndef INTERSECT_GLSL
#define INTERSECT_GLSL


#include "src/shaders/common.glsl"


// See 3.3 Ray-Triangle Intersection
bool RayTriangleIntersect(Ray ray, Triangle tri, int triId, float closestT, inout SurfaceInteraction si) {
    vec3 e1 = tri.v1.pos - tri.v0.pos;
    vec3 e2 = tri.v2.pos - tri.v0.pos;
    vec3 pvec = cross(ray.d, e2);
    float det = dot(e1, pvec);

    // If det is close to 0, ray is parallel to the triangle
    if (abs(det) < 1e-7) return false;

    float invDet = 1.0 / det;

    vec3 tvec = ray.o - tri.v0.pos;
    float u = dot(tvec, pvec) * invDet;
    if (u < 0.0 || u > 1.0) return false;

    vec3 qvec = cross(tvec, e1);
    float v = dot(ray.d, qvec) * invDet;
    if (v < 0.0 || u + v > 1.0) return false;
    
    float t = dot(e2, qvec) * invDet;
    // Check if the hit distance is positive and closer than current closest triangle
    if (t < EPSILON || t >= closestT) return false;

    if (backfaceCulling == 1) {
        Material mat = materials[tri.matId];
        if (mat.doubleSided == 0 && det < 0.0 && mat.transmission == 0.0) return false;
    }

    si.bary = vec2(u, v);
    si.t = t;
    si.triId = triId;
    si.ng = normalize(cross(e1, e2));
    return true;
}

// See 3.3 Ray-Triangle Intersection
bool ShadowRayTriangleIntersect(inout uvec3 rng, inout Ray ray, Triangle tri, int triId, float closestT, inout VisibilityInteraction vi) {
    vec3 e1 = tri.v1.pos - tri.v0.pos;
    vec3 e2 = tri.v2.pos - tri.v0.pos;
    vec3 pvec = cross(ray.d, e2);
    float det = dot(e1, pvec);

    // If det is close to 0, ray is parallel to the triangle
    if (abs(det) < 1e-7) return false;

    float invDet = 1.0 / det;

    vec3 tvec = ray.o - tri.v0.pos;
    float u = dot(tvec, pvec) * invDet;
    if (u < 0.0 || u > 1.0) return false;

    vec3 qvec = cross(tvec, e1);
    float v = dot(ray.d, qvec) * invDet;
    if (v < 0.0 || u + v > 1.0) return false;
    
    float t = dot(e2, qvec) * invDet;
    // Check if the hit distance is positive and closer than current closest triangle
    if (t < EPSILON || t >= closestT) return false;

    Material mat = materials[tri.matId];
    if (backfaceCulling == 1) {
        if (mat.doubleSided == 0 && det < 0.0 && mat.transmission == 0.0) return false;
    }

    float w = 1.0 - u - v;
    vec2 texCoords = w * tri.v0.uv + u * tri.v1.uv + v * tri.v2.uv;

    if (mat.alphaMode != 0) {
        if (mat.hasBaseColTex == 1) {
            vec4 baseCol = texture(baseColorTextures, vec3(vec2(u, v), mat.baseTexId));
            mat.alpha = baseCol.w;
        }

        // See 2.4 Ray Utilities
        vec3 p = GetRayPoint(ray, t);

        if (mat.alphaMode == 1) {
            /* MASK */

            if (mat.alpha < mat.alphaCutoff) return false;
        } else if (mat.alphaMode == 2) {
            /* BLEND */

            // See 2.2 The PCG Hash
            float Xi = Pcg3d(rng).x;

            if (Xi > mat.alpha) return false;
        }
    }

    vi.t = t;
    return true;
}

// See 3.2 AABB Testing
AabbHit AabbTest(Ray ray, vec3 invRayD, BvhNode node, float closestT) {
    vec3 t0 = (node.aabbMin - ray.o) * invRayD;
    vec3 t1 = (node.aabbMax - ray.o) * invRayD;
    
    vec3 tMin = min(t0, t1);
    vec3 tMax = max(t0, t1);

    float tNear = max(max(tMin.x, tMin.y), tMin.z);
    float tFar  = min(min(tMax.x, tMax.y), tMax.z);
    
    AabbHit h;
    h.hit = tNear <= tFar && tFar > 0.0 && tNear < closestT;
    h.tNear = tNear;

    return h;
}

// See 4.3 Traversal
bool Intersect(Ray ray, inout SurfaceInteraction si) {
    /*
     * BVH traversal to find the closest ray-triangle intersection.
     * Used for primary or bounce rays.
     */

    SurfaceInteraction tempSi;
    bool didIntersect = false;
    float closestT = INF;

    int totalNodesVisited = si.nodesVisited;

    int nodeStack[MAX_BVH_DEPTH];
    int stackIdx = 0;
    // Push root node index onto the stack
    nodeStack[stackIdx++] = 0;

    vec3 invRayD = 1.0 / ray.d;

    while (stackIdx > 0) {
        totalNodesVisited++;
        
        // Pop the latest node index off
        int currIdx = nodeStack[--stackIdx];
        BvhNode currNode = BvhNodes[currIdx];

        if (AabbTest(ray, invRayD, currNode, closestT).hit) {
            if (currNode.isLeaf == 1) {
                for (int i = 0; i < currNode.triCount; i++) {
                    int triIndex = triIndices[currNode.firstTriId + i];
                    Triangle tri = triangles[triIndex];
                    if (RayTriangleIntersect(ray, tri, triIndex, closestT, tempSi)) {
                        didIntersect = true;
                        closestT = tempSi.t;
                        si = tempSi;
                    }
                }
            } else {
                int left = currNode.leftChildId;
                int right = currNode.rightChildId;

                if (stackIdx < maxBvhDepth && stackIdx < MAX_BVH_DEPTH) {
                    // Push children onto the stack if there are children
                    if (left != -1 && right != -1) {
                        BvhNode leftNode = BvhNodes[left];
                        BvhNode rightNode = BvhNodes[right];

                        AabbHit lh = AabbTest(ray, invRayD, leftNode, closestT);
                        AabbHit rh = AabbTest(ray, invRayD, rightNode, closestT);

                        // Push farther child first so the nearer one pops first (LIFO)
                        if (lh.tNear < rh.tNear) {
                            if (rh.hit) nodeStack[stackIdx++] = right;
                            if (lh.hit) nodeStack[stackIdx++] = left;
                        } else {
                            if (lh.hit) nodeStack[stackIdx++] = left;
                            if (rh.hit) nodeStack[stackIdx++] = right;
                        }
                    } else if (left != -1) {
                        nodeStack[stackIdx++] = left;
                    } else if (right != -1) {
                        nodeStack[stackIdx++] = right;
                    }
                }
            }
        }
    }

    si.nodesVisited = totalNodesVisited;

    return didIntersect;
}

// See 4.3 Traversal
VisibilityInteraction TestVisibility(inout uvec3 rng, Ray ray, float maxDist) {
    /*
     * BVH traversal to find if there is a ray-triangle intersection.
     * Used for shadow rays in NEE to determine occlusion.
     */
    
    VisibilityInteraction vi;
    VisibilityInteraction tempVi;
    float closestT = maxDist;

    int nodeStack[MAX_BVH_DEPTH];
    int stackIdx = 0;
    // Push root node index onto the stack
    nodeStack[stackIdx++] = 0;

    vec3 invRayD = 1.0 / ray.d;

    while (stackIdx > 0) {
        // Pop the latest node index off
        int currIdx = nodeStack[--stackIdx];
        BvhNode currNode = BvhNodes[currIdx];

        if (AabbTest(ray, invRayD, currNode, closestT).hit) {
            if (currNode.isLeaf == 1) {
                for (int i = 0; i < currNode.triCount; i++) {
                    int triIndex = triIndices[currNode.firstTriId + i];
                    Triangle tri = triangles[triIndex];
                    if (ShadowRayTriangleIntersect(rng, ray, tri, triIndex, closestT, tempVi)) {
                        vi = tempVi;
                        vi.isOccluded = true;
                        return vi;
                    }
                }
            } else {
                int left = currNode.leftChildId;
                int right = currNode.rightChildId;

                if (stackIdx < MAX_BVH_DEPTH) {
                    // Push children onto the stack if there are children
                    if (left != -1 && right != -1) {
                        BvhNode leftNode = BvhNodes[left];
                        BvhNode rightNode = BvhNodes[right];

                        AabbHit lh = AabbTest(ray, invRayD, leftNode, closestT);
                        AabbHit rh = AabbTest(ray, invRayD, rightNode, closestT);

                        // Push farther child first so the nearer one pops first (LIFO)
                        if (lh.tNear < rh.tNear) {
                            if (rh.hit) nodeStack[stackIdx++] = right;
                            if (lh.hit) nodeStack[stackIdx++] = left;
                        } else {
                            if (lh.hit) nodeStack[stackIdx++] = left;
                            if (rh.hit) nodeStack[stackIdx++] = right;
                        }
                    } else if (left != -1) {
                        nodeStack[stackIdx++] = left;
                    } else if (right != -1) {
                        nodeStack[stackIdx++] = right;
                    }
                }
            }
        }
    }

    vi.isOccluded = false;
    return vi;
}

// See 7.2 Shadow Rays
VisibilityInteraction ShadowRayTest(inout uvec3 rng, SurfaceInteraction si, float dist, vec3 wi) {
    Ray shadowRay;
    vec3 offsetDir = dot(si.ng, wi) < 0.0 ? -si.ng : si.ng;
    // See 2.4 Ray Utilities
    shadowRay.o = OffsetRayOrigin(si.p, offsetDir);
    shadowRay.d = wi;

    // See 4.3 Traversal
    VisibilityInteraction vi = TestVisibility(rng, shadowRay, dist);

    return vi;
}


#endif
