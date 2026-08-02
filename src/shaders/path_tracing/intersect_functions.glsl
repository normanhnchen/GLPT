#ifndef INTERSECT_FUNCTIONS_GLSL
#define INTERSECT_FUNCTIONS_GLSL


#include "src/shaders/common.glsl"


// Möller-Trumbore ray-triangle intersection algorithm
// https://www.scratchapixel.com/lessons/3d-basic-rendering/ray-tracing-rendering-a-triangle/moller-trumbore-ray-triangle-intersection.html
bool RayTriangleIntersect(Ray ray, Triangle tri, int triId, float closestT, inout SurfaceInteraction si) {
    vec3 e1 = tri.v1.pos - tri.v0.pos;
    vec3 e2 = tri.v2.pos - tri.v0.pos;
    vec3 pvec = cross(ray.d, e2);
    float det = dot(e1, pvec);

    Material mat = materials[tri.matId];
    if (mat.doubleSided == 0 && det < 0.0 && mat.transmission == 0.0) return false;

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

    si.bary = vec2(u, v);
    si.t = t;
    si.triId = triId;
    return true;
}

// Möller-Trumbore ray-triangle intersection algorithm
// https://www.scratchapixel.com/lessons/3d-basic-rendering/ray-tracing-rendering-a-triangle/moller-trumbore-ray-triangle-intersection.html
bool ShadowRayTriangleIntersect(inout uvec3 rng, inout Ray ray, Triangle tri, int triId, float closestT, inout VisibilityInteraction vi) {
    vec3 e1 = tri.v1.pos - tri.v0.pos;
    vec3 e2 = tri.v2.pos - tri.v0.pos;
    vec3 pvec = cross(ray.d, e2);
    float det = dot(e1, pvec);

    Material mat = materials[tri.matId];
    if (mat.doubleSided == 0 && det < 0.0 && mat.transmission == 0.0) return false;

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

    float w = 1.0 - u - v;
    vec2 texCoords = w * tri.v0.uv + u * tri.v1.uv + v * tri.v2.uv;

    if (mat.alphaMode != 0) {
        if (mat.hasBaseColTex == 1) {
            vec4 baseCol = texture(baseColorTextures, vec3(vec2(u, v), mat.baseTexId));
            mat.alpha = baseCol.w;
        }

        vec3 p = GetRayPoint(ray, t);

        if (mat.alphaMode == 1) {
            // MASK
            if (mat.alpha < mat.alphaCutoff) return false;
        } else if (mat.alphaMode == 2) {
            // BLEND
            if (Pcg3d(rng).x > mat.alpha) return false;
        }
    }

    vi.t = t;
    return true;
}

bool AabbIntersect(Ray ray, vec3 invRayD, BvhNode node, float closestT) {
    vec3 t0 = (node.aabbMin - ray.o) * invRayD;
    vec3 t1 = (node.aabbMax - ray.o) * invRayD;
    
    vec3 tMin = min(t0, t1);
    vec3 tMax = max(t0, t1);

    float tNear = max(max(tMin.x, tMin.y), tMin.z);
    float tFar  = min(min(tMax.x, tMax.y), tMax.z);
    
    return tNear <= tFar && tFar > 0.0 && tNear < closestT;
}

float AabbTNear(Ray ray, vec3 invRayD, BvhNode node) {
    vec3 t0 = (node.aabbMin - ray.o) * invRayD;
    vec3 t1 = (node.aabbMax - ray.o) * invRayD;
    
    vec3 tMin = min(t0, t1);

    float tNear = max(max(tMin.x, tMin.y), tMin.z);
    return tNear;
}

// https://jacco.ompf2.com/2022/04/18/how-to-build-a-bvh-part-2-faster-rays/
bool Intersect(Ray ray, inout SurfaceInteraction si) {
    SurfaceInteraction tempSi;
    bool didIntersect = false;
    float closestT = INF;

    int nodeStack[MAX_BVH_DEPTH];
    int stackIdx = 0;
    // Push root node index onto the stack
    nodeStack[stackIdx++] = 0;

    vec3 invRayD = 1.0 / ray.d;

    while (stackIdx > 0) {
        // Pop the latest node index off
        int currIdx = nodeStack[--stackIdx];
        BvhNode currNode = BvhNodes[currIdx];

        if (AabbIntersect(ray, invRayD, currNode, closestT)) {
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

                if (stackIdx < MAX_BVH_DEPTH) {
                    // Push children onto the stack if there are children
                    if (left != -1 && right != -1) {
                        BvhNode leftNode = BvhNodes[left];
                        BvhNode rightNode = BvhNodes[right];

                        float leftT = AabbTNear(ray, invRayD, leftNode);
                        float rightT = AabbTNear(ray, invRayD, rightNode);

                        // Push farther child first so the nearer one pops first (LIFO)
                        if (leftT < rightT) {
                            nodeStack[stackIdx++] = right;
                            nodeStack[stackIdx++] = left;
                        } else {
                            nodeStack[stackIdx++] = left;
                            nodeStack[stackIdx++] = right;
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

    return didIntersect;
}

bool TestVisibility(inout uvec3 rng, Ray ray, float maxDist, inout VisibilityInteraction vi) {
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

        if (AabbIntersect(ray, invRayD, currNode, closestT)) {
            if (currNode.isLeaf == 1) {
                for (int i = 0; i < currNode.triCount; i++) {
                    int triIndex = triIndices[currNode.firstTriId + i];
                    Triangle tri = triangles[triIndex];
                    if (ShadowRayTriangleIntersect(rng, ray, tri, triIndex, closestT, tempVi)) {
                        vi = tempVi;
                        return true;
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

                        float leftT = AabbTNear(ray, invRayD, leftNode);
                        float rightT = AabbTNear(ray, invRayD, rightNode);

                        // Push farther child first so the nearer one pops first (LIFO)
                        if (leftT < rightT) {
                            nodeStack[stackIdx++] = right;
                            nodeStack[stackIdx++] = left;
                        } else {
                            nodeStack[stackIdx++] = left;
                            nodeStack[stackIdx++] = right;
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

    return false;
}


#endif
