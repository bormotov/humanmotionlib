# SPDX-License-Identifier: Apache-2.0
"""Canonical active right-handed transforms; meters and degree action inputs."""

import math

I = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))


def add(a, b): return [x+y for x, y in zip(a, b)]
def sub(a, b): return [x-y for x, y in zip(a, b)]
def scale(a, s): return [x*s for x in a]
def dot(a, b): return sum(x*y for x, y in zip(a, b))
def norm(a): return math.sqrt(dot(a, a))
def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
def transpose(a): return [list(row) for row in zip(*a)]
def mv(a, b): return [dot(row, b) for row in a]
def mm(a, b): return [[dot(row, col) for col in zip(*b)] for row in a]


def unit(v):
    length = norm(v)
    if not math.isfinite(length) or length < 1e-12:
        raise ValueError("Cannot normalize a degenerate/non-finite vector")
    return scale(v, 1 / length)


def determinant(a): return dot(a[0], cross(a[1], a[2]))


def validate_basis(b):
    if len(b) != 3 or any(len(row) != 3 for row in b):
        raise ValueError("Basis must be 3x3")
    if not all(math.isfinite(x) for row in b for x in row):
        raise ValueError("Non-finite basis")
    gram = mm(transpose(b), b)
    if abs(determinant(b)-1) > 1e-6 or any(abs(gram[i][j]-I[i][j]) > 1e-6 for i in range(3) for j in range(3)):
        raise ValueError("Basis must be orthonormal with determinant +1")
    return b


def shaft_basis(start, end):
    y = unit(sub(end, start))
    anterior = [0, 1, 0]
    z = sub(anterior, scale(y, dot(anterior, y)))
    if norm(z) < 1e-8:
        superior = [0, 0, 1]
        z = sub(superior, scale(y, dot(superior, y)))
    x = unit(cross(y, unit(z)))
    return validate_basis(transpose([x, y, cross(x, y)]))


def rot(axis, degrees):
    x, y, z = unit(axis)
    angle = math.radians(degrees)
    c, s = math.cos(angle), math.sin(angle)
    d = 1-c
    return [[c+x*x*d, x*y*d-z*s, x*z*d+y*s],
            [y*x*d+z*s, c+y*y*d, y*z*d-x*s],
            [z*x*d-y*s, z*y*d+x*s, c+z*z*d]]


def rx(d): return rot([1, 0, 0], d)
def ry(d): return rot([0, 1, 0], d)
def rz(d): return rot([0, 0, 1], d)


def validate_quaternion(q):
    if len(q) != 4 or not all(math.isfinite(x) for x in q) or abs(norm(q)-1) > 1e-6:
        raise ValueError("Expected finite unit quaternion [w,x,y,z] within 1e-6")
    return q


def qmul(a, b):
    validate_quaternion(a); validate_quaternion(b)
    w, x, y, z = a; v, i, j, k = b
    return [w*v-x*i-y*j-z*k, w*i+x*v+y*k-z*j,
            w*j-x*k+y*v+z*i, w*k+x*j-y*i+z*v]


def qinverse(q):
    validate_quaternion(q)
    return [q[0], -q[1], -q[2], -q[3]]


def qmatrix(q):
    validate_quaternion(q)
    w, x, y, z = q
    return [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
            [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
            [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]


def quaternion(a):
    validate_basis(a)
    # Select the largest diagonal component to avoid cancellation near pi.
    candidates = [1+a[0][0]+a[1][1]+a[2][2], 1+a[0][0]-a[1][1]-a[2][2],
                  1-a[0][0]+a[1][1]-a[2][2], 1-a[0][0]-a[1][1]+a[2][2]]
    index = max(range(4), key=lambda k: candidates[k])
    component = math.sqrt(max(0, candidates[index])) / 2
    divisor = 4*component
    if index == 0:
        q = [component, (a[2][1]-a[1][2])/divisor, (a[0][2]-a[2][0])/divisor, (a[1][0]-a[0][1])/divisor]
    elif index == 1:
        q = [(a[2][1]-a[1][2])/divisor, component, (a[0][1]+a[1][0])/divisor, (a[0][2]+a[2][0])/divisor]
    elif index == 2:
        q = [(a[0][2]-a[2][0])/divisor, (a[0][1]+a[1][0])/divisor, component, (a[1][2]+a[2][1])/divisor]
    else:
        q = [(a[1][0]-a[0][1])/divisor, (a[0][2]+a[2][0])/divisor, (a[1][2]+a[2][1])/divisor, component]
    q = scale(q, 1/norm(q))
    # Serialization canonicalization; validation still accepts the equivalent -q.
    if next((x for x in q if abs(x) > 1e-15), 1) < 0:
        q = scale(q, -1)
    return q


def local_delta(rest, solved): return qmul(qinverse(rest), solved)


def compose(parent, translation, rest, delta=(1, 0, 0, 0)):
    p, r = parent
    return add(p, mv(r, translation)), mm(r, qmatrix(qmul(rest, delta)))


def mirror_position(p): return [-p[0], p[1], p[2]]


def mirror_rotation(r):
    signs = [-1, 1, 1]
    return [[signs[i]*r[i][j]*signs[j] for j in range(3)] for i in range(3)]


def mirror_basis(b):
    signs = [-1, 1, 1]
    return validate_basis([[signs[i]*b[i][j]*signs[j] for j in range(3)] for i in range(3)])


def angle_error(a, b):
    relative = mm(transpose(a), b)
    cosine = max(-1., min(1., (sum(relative[i][i] for i in range(3))-1)/2))
    return math.degrees(math.acos(cosine))
