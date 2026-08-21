# Derivations

## Triangle Area Calculation

From the definition of a cross product:

$|\vec{a} \times \vec{b}| = \|\vec{a}\| \|\vec{b}\| \sin\theta$

$\therefore \quad A_{triangle} = \dfrac{|\vec{a} \times \vec{b}|} {2}.$

## Ray-Bounding Box Intersection (The Slab Method)

### Rays

A point on a ray can be defined as

$$P(t) = O + t\vec{D}$$

where:

- $\vec{P}(t)$ = point
- $O$ = ray origin
- $\vec{D}$ = normalized ray direction $\implies ||\vec{D}|| = 1$
- $t \ge 0$ = distance from $\vec{O}$ to $P(t)$ because $||t\vec{D}|| = t \cdot ||\vec{D}|| = t$

### Bounding Boxes

A bounding box can be specified using $2$ of its corners:

$$
b_{\min} = \begin{pmatrix} x_{\min} \\ y_{\min} \\ z_{\min} \end{pmatrix}, \quad
b_{\max} = \begin{pmatrix} x_{\max} \\ y_{\max} \\ z_{\max} \end{pmatrix}.
$$

A point
$\vec{P}(t) = \begin{pmatrix} x & y & z \end{pmatrix}$
is in the bounding box if and only if

- $x_{\min} < x < x_{\max}$
- $y_{\min} < y < y_{\max}$
- $z_{\min} < z < z_{\max}$

### The Slab Method

The slab method is calculating if a ray's separate $x, y, z$ directions intersects the bounds'  
separate $x, y, z$ planes (slabs).

For each slab $x, y, z$:

$$
t = \dfrac{b - O} {D} \\[10pt]

\implies t_1 = \dfrac{b_{\min} - O} {D}, \quad
t_2 = \dfrac{b_{\max} - O} {D} \\[10pt]

t_{\min} = \min(t_1,\ t_2), \quad
t_{\max} = \max(t_1,\ t_2).
$$

Intersection with all the slabs are:  

$$
t_{\min} = \max(t_{\min},\ \min(t_1,\ t_2)), \quad
t_{\max} = \min(t_{\max},\ \max(t_1,\ t_2)).
$$

Finally, intersection only exists if and only if

$$
t_{\min} < t_{\max}.
$$

## Ray-Triangle Intersection (Möller-Trumbore)

### Rays

A point on a ray can be defined as

$$P(t) = O + t\vec{D}$$

where:

- $\vec{P}(t)$ = point
- $O$ = ray origin
- $\vec{D}$ = normalized ray direction $\implies ||\vec{D}|| = 1$
- $t \ge 0$ = distance from $\vec{O}$ to $P(t)$ because $||t\vec{D}|| = t \cdot ||\vec{D}|| = t$

### Barycentric Coordinates

With Barycentric coordinates, any point located on a triangle can be represented as:

$$P = uA + vB + wC.$$

where:

- $P$ is the point
- $A, B, C$ are the vertices of the triangle
- $u, v, w$ are arbitrary scalars

A point P is only inside the triangle if $0 \le u, v, w \le 1$ and $0 ≤ u + v + w ≤ 1.$

### Möller-Trumbore's Algorithm

Möller-Trumbore uses the convention they define,

$P = A + u\overline{AB} + v\overline{AC}$:

1) Start from $A$
2) move along $\overline{AB}$ by $u$
3) move along $\overline{AC}$ by $v$


$$
\begin{aligned}
\therefore \quad P &= A + u(B - A) + v(C - A) \\
&= (1 - u - v)A + uB + vC.
\end{aligned}
$$

---

Setting a ray's equation equal to the Barycentric coordinates

$$
\begin{aligned}
P = O + tD &= (1 - u - v)A + uB + vC
\end{aligned}
$$

Simplifying, the result is

$$
P = O + tD = (1 - u - v)A + uB + vC \\[10pt]

O - A = -tD + u(B - A) + v(C - A) \\[10pt]

\begin{bmatrix} -D & (B - A) & (C - A) \end{bmatrix}
\begin{pmatrix} t \\ u \\ v \end{pmatrix}
= O - A.
$$

### Cramer's Rule

For a system $A\vec{x} = \vec{b}$,

where:

- $A = \begin{bmatrix}
a_{11} & a_{12} & \cdots & a_{1n} \\
a_{21} & a_{22} & \cdots & a_{2n} \\
\vdots & \vdots & \ddots & \vdots \\
a_{n1} & a_{n2} & \cdots & a_{nn}
\end{bmatrix},\ det(A) \ne 0$ is the coefficient matrix,

- $\vec{x} = \begin{bmatrix}
x_{1} \\ x_{2} \\ \vdots \\ x_{n}
\end{bmatrix}$ is the variable vector, and

- $\vec{b} = \begin{bmatrix}
b_{1} \\ b_{2} \\ \vdots \\ b_{n}
\end{bmatrix}$ is the variable vector

Cramer's rule states

$$x_{i} = \frac{\det(A_{i})} {\det(A)}$$

where $A_{i}$ is formed by replacing the $i$-th column of $A$ with $\vec{b}$.

### Applying It To The Möller-Trumbore Algorithm

Again,

$$A\vec{x} = \vec{b}.$$

From the previous calculations,

$$
\begin{bmatrix} -D & (B - A) & (C - A) \end{bmatrix}
\begin{pmatrix} t \\ u \\ v \end{pmatrix}
= O - A. \\[10pt]

\implies 
A = \begin{bmatrix} -D & (B - A) & (C - A) \end{bmatrix}, \quad
\vec{x} = \begin{pmatrix} t \\ u \\ v \end{pmatrix}, \quad
\vec{b} = O - A.
$$

Then the matrices for Cramer's rule are:

$$
A_t = \begin{bmatrix} O - A & (B-A) & (C-A) \end{bmatrix}, \quad
A_u = \begin{bmatrix} -D & O - A & (C-A) \end{bmatrix}, \quad
A_v = \begin{bmatrix} -D & (B-A) & O - A \end{bmatrix}.
$$

Letting

$$
T = O - A, \quad
E_1 = B - A, \quad
E_2 = C - A
$$

the result after applying Cramer's rule is:

$$
\\[10pt]
t = \frac{\det\begin{bmatrix} T & E_1 & E_2 \end{bmatrix}}
         {\det\begin{bmatrix} -D & E_1 & E_2 \end{bmatrix}}, \quad
u = \frac{\det\begin{bmatrix} -D & T & E_2 \end{bmatrix}}
         {\det\begin{bmatrix} -D & E_1 & E_2 \end{bmatrix}}, \quad
         v = \frac{\det\begin{bmatrix} -D & E_1 & T \end{bmatrix}}
         {\det\begin{bmatrix} -D & E_1 & E_2 \end{bmatrix}}.
$$

### Final Calculations

From the scalar triple product,

$$\det(A,\ B,\ C) = A \cdot (B \times C).$$

Therefore,

$$
t = \frac{(T \times E_1) \cdot E_2} {(-D \times E_1) \cdot E_2}, \quad
u = \frac{(-D \times T) \cdot E_2} {(-D \times E_1) \cdot E_2}, \quad
v = \frac{(-D \times E_1) \cdot T} {(-D \times E_1) \cdot E_2}.
$$

---

Letting

$$
P = D \times E_2, \quad
Q = T \times E_1.
$$

The final desired result is

$$
t = \frac{Q \cdot E_2} {P \cdot E_1}, \quad
u = \frac{P \cdot T} {P \cdot E_1}, \quad
v = \frac{Q \cdot D} {P \cdot E_1}.
$$

## Fresnel-Schlick

### Fresnel Equations

The Fresnel equation calculates exactly how much light is reflected or transmitted.

It is defined through s-polarization (electric field is **perpendicular** to the plane of dincidence), and p-polarization (electric field is **parallel** to the plane incidence).

Based on Snell's law,

$$n_1 \sin\theta_i = n_2 \sin\theta_t$$

where $\theta_i$ is the angle of incidence and $\theta_t$ is the angle of transmission.

This gives

$$\cos\theta_t = \sqrt{1 - (\frac{n_1} {n_2} \sin\theta_i) ^ 2}$$

using $\sin ^ 2 + \cos ^ 2 = 1$.

---

Applying this to Fresnel equations (derived from electromagnetic theory), the equation given by
s-polarization is

$$
R_s = \left| \frac{
    n_1 \cos\theta_i - n_2 \sqrt{1 - (\frac{n_1} {n_2} \sin\theta_i) ^ 2}
} {
    n_1 \cos\theta_i + n_2 \sqrt{1 - (\frac{n_1} {n_2} \sin\theta_i) ^ 2}
} \right| ^ 2 \\[10pt]
$$

and the equation given by p-polarization is

$$
R_p = \left| \frac{
    n_1 \sqrt{1 - (\frac{n_1} {n_2} \sin\theta_i) ^ 2} - n_2 \cos\theta_i
} {    
    n_1 \sqrt{1 - (\frac{n_1} {n_2} \sin\theta_i) ^ 2} + n_2 \cos\theta_i

} \right| ^ 2 \\[10pt]
$$

where $R$ represents the reflectance (the fraction of light reflected).

The effective reflectance and the final formula is the average of the two:
$$
R_{eff} = \frac{R_s + R_p} {2}.
$$

# References

- https://tavianator.com/2022/ray_box_boundary.html
- https://www.scratchapixel.com/lessons/3d-basic-rendering/ray-tracing-rendering-a-triangle/barycentric-coordinates.html  
- https://www.scratchapixel.com/lessons/3d-basic-rendering/ray-tracing-rendering-a-triangle/moller-trumbore-ray-triangle-intersection.html
- https://en.wikipedia.org/wiki/Cramer%27s_rule
- https://en.wikipedia.org/wiki/Fresnel_equations