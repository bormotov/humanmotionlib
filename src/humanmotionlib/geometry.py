# SPDX-License-Identifier: Apache-2.0
"""Fixed-resolution body-local meshes. No Blender or source-loader dependency."""

import math
from humanmotionlib import math3d as m

LONGITUDES, LATITUDES, RADIAL_SIDES, CURVE_INTERVALS = 24,12,16,16


def triangulate(faces):
    return [tuple((face[0],face[i],face[i+1])) for face in faces for i in range(1,len(face)-1)]


def ellipsoid(center,radii):
    vertices = [m.add(center,[0,0,-radii[2]])]
    for lat in range(1,LATITUDES):
        phi = -math.pi/2+math.pi*lat/LATITUDES
        for lon in range(LONGITUDES):
            theta = 2*math.pi*lon/LONGITUDES
            vertices.append(m.add(center,[radii[0]*math.cos(phi)*math.cos(theta),radii[1]*math.cos(phi)*math.sin(theta),radii[2]*math.sin(phi)]))
    top = len(vertices);vertices.append(m.add(center,[0,0,radii[2]]))
    faces = []
    for lon in range(LONGITUDES):
        nxt = (lon+1)%LONGITUDES
        faces.append((0,1+nxt,1+lon))
        for lat in range(LATITUDES-2):
            a,b = 1+lat*LONGITUDES+lon,1+lat*LONGITUDES+nxt
            faces.append((a,b,b+LONGITUDES,a+LONGITUDES))
        faces.append((top,1+(LATITUDES-2)*LONGITUDES+lon,1+(LATITUDES-2)*LONGITUDES+nxt))
    return vertices,triangulate(faces)


def centerline(points):
    if len(points)<2: raise ValueError("Tube/capsule needs two endpoints")
    if len(points)==2:
        return [m.add(m.scale(points[0],1-i/CURVE_INTERVALS),m.scale(points[1],i/CURVE_INTERVALS)) for i in range(CURVE_INTERVALS+1)]
    # Interpolating Catmull-Rom, endpoint tangents from duplicated end points.
    result = []
    for i in range(CURVE_INTERVALS+1):
        u = i/CURVE_INTERVALS*(len(points)-1)
        j = min(len(points)-2,int(u));t=u-j
        p0,p1,p2,p3 = points[max(0,j-1)],points[j],points[j+1],points[min(len(points)-1,j+2)]
        result.append([.5*(2*p1[a]+(-p0[a]+p2[a])*t+(2*p0[a]-5*p1[a]+4*p2[a]-p3[a])*t*t+(-p0[a]+3*p1[a]-3*p2[a]+p3[a])*t*t*t) for a in range(3)])
    return result


def tube(points,radius):
    points = centerline(points)
    vertices,faces = [],[]
    previous = None
    for i,point in enumerate(points):
        tangent = m.unit(m.sub(points[min(i+1,len(points)-1)],points[max(0,i-1)]))
        if previous is None:
            reference = min(([1,0,0],[0,1,0],[0,0,1]),key=lambda axis:abs(m.dot(axis,tangent)))
            x = m.unit(m.sub(reference,m.scale(tangent,m.dot(reference,tangent))))
        else:
            x = m.unit(m.sub(previous,m.scale(tangent,m.dot(previous,tangent))))
        y = m.cross(tangent,x);previous=x
        vertices.extend(m.add(point,m.add(m.scale(x,radius*math.cos(2*math.pi*j/RADIAL_SIDES)),m.scale(y,radius*math.sin(2*math.pi*j/RADIAL_SIDES)))) for j in range(RADIAL_SIDES))
        if i:
            for j in range(RADIAL_SIDES):
                a=(i-1)*RADIAL_SIDES+j;b=(i-1)*RADIAL_SIDES+(j+1)%RADIAL_SIDES
                faces.append((a,b,b+RADIAL_SIDES,a+RADIAL_SIDES))
    faces.extend([tuple(reversed(range(RADIAL_SIDES))),tuple((len(points)-1)*RADIAL_SIDES+j for j in range(RADIAL_SIDES))])
    return vertices,triangulate(faces)


def shell(points,faces,thickness):
    normals = [[0.,0.,0.] for _ in points]
    triangles = triangulate(faces)
    for a,b,c in triangles:
        normal = m.cross(m.sub(points[b],points[a]),m.sub(points[c],points[a]))
        for i in (a,b,c): normals[i] = m.add(normals[i],normal)
    normals = [m.unit(n) for n in normals]
    vertices = [m.add(p,m.scale(n,sign*thickness/2)) for sign in (-1,1) for p,n in zip(points,normals)]
    count = len(points)
    output = [tuple(reversed(f)) for f in triangles]+[tuple(i+count for i in f) for f in triangles]
    edges = {}
    for face in triangles:
        for a,b in zip(face,face[1:]+face[:1]):
            key=tuple(sorted((a,b)))
            if key in edges: edges[key]=None
            else:edges[key]=(a,b)
    output += triangulate([(a,b,b+count,a+count) for edge in edges.values() if edge is not None for a,b in [edge]])
    return vertices,output


def primitive_mesh(primitive,points_override=None):
    kind = primitive["type"]
    if kind in ("ellipsoid","sphere","recess"):
        radii = [primitive["radius_m"]]*3 if kind=="sphere" else primitive["radii_m"]
        return ellipsoid(primitive["center_m"],radii)
    if kind == "tube": return tube(points_override or primitive["points_m"],primitive["radius_m"])
    if kind == "shell": return shell(primitive["points_m"],primitive["faces"],primitive["thickness_m"])
    if kind == "block":
        center,dimensions = primitive["center_m"],primitive["dimensions_m"]
        vertices = [m.add(center,[a*dimensions[0]/2,b*dimensions[1]/2,c*dimensions[2]/2]) for a,b,c in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
        return vertices,triangulate([(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    if kind == "elliptic_capsule":
        # Y is longitudinal in this explicitly authored sternum body frame.
        start,end = primitive["points_m"]
        if abs(end[0]-start[0])+abs(end[2]-start[2])>1e-12: raise ValueError("Capsule endpoints must follow local Y")
        rx,rz = primitive["radii_m"]
        center = m.scale(m.add(start,end),.5)
        vertices,faces = ellipsoid([0,0,0],[rx,rz,rz])
        for i,v in enumerate(vertices):
            # Rotate the local sphere's polar axis Z onto longitudinal Y.
            vertices[i] = m.add(center,[v[0],v[2]+(-1 if v[2]<0 else 1)*(end[1]-start[1])/2,-v[1]])
        return vertices,faces
    raise ValueError("Unknown geometry primitive: "+kind)
