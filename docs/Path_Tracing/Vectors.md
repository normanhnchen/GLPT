# Vectors

A 3D vector is defined as a direction in 3D space:

$$
\vec{v} =
\begin{pmatrix}
x \\
y \\
z
\end{pmatrix}.
$$

### Scalar Operations

For a scalar $\lambda \in \mathbb{R}$,

$$
\lambda
\begin{pmatrix}
a \\
b \\
c
\end{pmatrix}
=
\begin{pmatrix}
\lambda a \\
\lambda b \\
\lambda c
\end{pmatrix}.
$$

### Negation

$$
-\vec{v}
=
-\begin{pmatrix}
v_x \\
v_y \\
v_z
\end{pmatrix}
=
\begin{pmatrix}
-v_x \\
-v_y \\
-v_z
\end{pmatrix}.
$$

### Vector Addition and Subtraction

For vectors $\vec{v}, \vec{w} \in \mathbb{R}^3$,

$$
\vec{v} \diamond \vec{w}
=
\begin{pmatrix}
v_x \\
v_y \\
v_z
\end{pmatrix}
\diamond
\begin{pmatrix}
w_x \\
w_y \\
w_z
\end{pmatrix}
=
\begin{pmatrix}
v_x \diamond w_x \\
v_y \diamond w_y \\
v_z \diamond w_z
\end{pmatrix},
$$

where $\diamond \in \{+,-\}$.

### Magnitude

The magnitude (length) of a vector is derived from the Pythagorean theorem:

$$
\|\vec{v}\|
=
\sqrt{v_x^2 + v_y^2 + v_z^2}.
$$

### Normalization

A normalized (unit) vector has magnitude 1:

$$
\hat{v}
=
\frac{\vec{v}}{\|\vec{v}\|},
\qquad
\text{for } \vec{v} \neq \vec{0}.
$$

### Vector Multiplication

Vector multiplication is not uniquely defined; two standard products are commonly used.

#### Dot Product

$$
\vec{v} \cdot \vec{w}
=
\|\vec{v}\| \, \|\vec{w}\| \cos\theta,
$$

and if $\vec{v}$ and $\vec{w}$ are unit vectors,

$$
\vec{v} \cdot \vec{w} = \cos\theta.
$$

#### Cross Product

$$
\vec{v} \times \vec{w}
=
\begin{pmatrix}
v_y w_z - v_z w_y \\
v_z w_x - v_x w_z \\
v_x w_y - v_y w_x
\end{pmatrix}.
$$

---

## Matrices

A matrix is an array of numbers:

$$
A =
\begin{bmatrix}
a_{11} & a_{12} & \cdots & a_{1n} \\
a_{21} & a_{22} & \cdots & a_{2n} \\
\vdots & \vdots & \ddots & \vdots \\
a_{m1} & a_{m2} & \cdots & a_{mn}
\end{bmatrix}.
$$

### Matrix Addition and Subtraction

Addition and subtraction of matrices is defined only if $A$ and $B$ have the **same dimensions**.

If $A, B \in \mathbb{R}^{m\times n}$, then

$$
A \diamond B
=
\begin{bmatrix}
a_{11} \diamond b_{11} & \cdots & a_{1n} \diamond b_{1n} \\
a_{21} \diamond b_{21} & \cdots & a_{2n} \diamond b_{2n} \\
\vdots & \ddots & \vdots \\
a_{m1} \diamond b_{m1} & \cdots & a_{mn} \diamond b_{mn}
\end{bmatrix},
$$

where $\diamond \in \{+,-\}$.

### Scalar Multiplication

For scalar $\lambda \in \mathbb{R}$ and matrix $A \in \mathbb{R}^{m\times n}$,

$$
\lambda A
=
\begin{bmatrix}
\lambda a_{11} & \cdots & \lambda a_{1n} \\
\vdots & \ddots & \vdots \\
\lambda a_{m1} & \cdots & \lambda a_{mn}
\end{bmatrix}.
$$

### Matrix Multiplication

For matrices $A$ and $B$, matrix multiplication $AB$ is defined only if the number of columns of $A$ equals the number of rows of $B$.

If $A \in \mathbb{R}^{m\times n}$ and $B \in \mathbb{R}^{n\times p}$, then $AB \in \mathbb{R}^{m\times p}$ and

$$
AB
=
\begin{bmatrix}
\sum_{k=1}^{n} a_{1k}b_{k1} & \cdots & \sum_{k=1}^{n} a_{1k}b_{kp} \\
\vdots & \ddots & \vdots \\
\sum_{k=1}^{n} a_{mk}b_{k1} & \cdots & \sum_{k=1}^{n} a_{mk}b_{kp}
\end{bmatrix}.
$$

---

## Transformations in 3D (Linear Algebra + Homogeneous Coordinates)

### Translation (using homogeneous coordinates)

To represent translation as a matrix, convert vectors to homogeneous coordinates:

$$
\vec{v}_h =
\begin{pmatrix}
x \\ y \\ z \\ 1
\end{pmatrix}.
$$

A translation by $\vec{t} = (t_x, t_y, t_z)$ requires the matrix:

$$
T(\vec{t}) =
\begin{bmatrix}
1 & 0 & 0 & t_x \\
0 & 1 & 0 & t_y \\
0 & 0 & 1 & t_z \\
0 & 0 & 0 & 1
\end{bmatrix}.
$$

Then the translation is

$$
\vec{v}'_h = T(\vec{t}) \vec{v}_h.
$$

### Scaling

Scaling by factors $s_x, s_y, s_z$:

$$
S(s_x, s_y, s_z) =
\begin{bmatrix}
s_x & 0 & 0 & 0 \\
0 & s_y & 0 & 0 \\
0 & 0 & s_z & 0 \\
0 & 0 & 0 & 1
\end{bmatrix}.
$$

### Rotation (about the coordinate axes)

Rotation about the $x$-axis by angle $\theta$:

$$
R_x(\theta) =
\begin{bmatrix}
1 & 0 & 0 & 0 \\
0 & \cos\theta & -\sin\theta & 0 \\
0 & \sin\theta & \cos\theta & 0 \\
0 & 0 & 0 & 1
\end{bmatrix}.
$$

Rotation about the $y$-axis by angle $\theta$:

$$
R_y(\theta) =
\begin{bmatrix}
\cos\theta & 0 & \sin\theta & 0 \\
0 & 1 & 0 & 0 \\
-\sin\theta & 0 & \cos\theta & 0 \\
0 & 0 & 0 & 1
\end{bmatrix}.
$$

Rotation about the $z$-axis by angle $\theta$:

$$
R_z(\theta) =
\begin{bmatrix}
\cos\theta & -\sin\theta & 0 & 0 \\
\sin\theta & \cos\theta & 0 & 0 \\
0 & 0 & 1 & 0 \\
0 & 0 & 0 & 1
\end{bmatrix}.
$$

# References

- https://learnopengl.com/Getting-started/Transformations