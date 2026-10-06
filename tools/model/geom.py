"""Procedural mesh building blocks for the AT4X model.

Coordinates are GTA vehicle space in metres: +X = passenger side, +Y = forward, +Z = up.
A MeshBuilder collects primitives (each tagged with a material key, a bone and an optional vehicle
light id) and turns them into one Blender mesh with two UV maps, a "Color 1" attribute and one vertex
group per bone.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.geometry import tessellate_polygon

# Vertex colour defaults: R = ambient occlusion (1 = none), G = deformation, B = burn, A = light id / 255.
DEFAULT_COLOR = (1.0, 1.0, 0.0, 1.0)


def V(*a):
    return Vector(a[0]) if len(a) == 1 else Vector(a)


class MeshBuilder:
    def __init__(self):
        self.verts = []        # Vector
        self.vgroup = []       # bone name per vertex
        self.faces = []        # (vertex indices, material key, alpha, uv scale, explicit uvs | None)
        self.fixed = []        # True for faces whose orientation is explicit (decals, glass panes)
        self.xform = Matrix.Identity(4)
        self.mirror = False

    # ------------------------------------------------------------------ transforms

    def push(self, m):
        prev = (self.xform.copy(), self.mirror)
        self.xform = self.xform @ m
        self.mirror = self.xform.to_3x3().determinant() < 0
        return prev

    def pop(self, prev):
        self.xform, self.mirror = prev

    def mirrored(self):
        """Context helper: everything added inside is mirrored to the other side (X -> -X)."""
        return _Push(self, Matrix.Scale(-1, 4, (1, 0, 0)))

    def push_ctx(self, m):
        return _Push(self, m)

    def at(self, loc, rot=None):
        m = Matrix.Translation(Vector(loc))
        if rot is not None:
            m = m @ rot.to_4x4()
        return _Push(self, m)

    # ------------------------------------------------------------------ raw

    def _vert(self, p, bone):
        self.verts.append(self.xform @ Vector(p))
        self.vgroup.append(bone)
        return len(self.verts) - 1

    def face(self, idx, mat, light=None, uvs=1.0, uv=None, fixed=False):
        self.fixed.append(fixed)
        idx = list(idx)
        if uv is not None:
            uv = list(uv)
        if self.mirror:
            idx.reverse()
            if uv is not None:
                uv.reverse()
        alpha = 1.0 if light is None else light / 255.0
        self.faces.append((idx, mat, alpha, uvs, uv))

    def quad(self, pts, mat, bone, uv=((0, 0), (1, 0), (1, 1), (0, 1)), light=None, double=False):
        """Face with explicit UVs (badges, gauges). double=True also adds the back face."""
        ids = [self._vert(p, bone) for p in pts]
        self.face(ids, mat, light, uv=uv, fixed=True)
        if double:
            ids2 = [self._vert(p, bone) for p in pts]
            self.face(list(reversed(ids2)), mat, light, uv=list(reversed(list(uv))), fixed=True)

    def decal(self, center, normal, up, w, hgt, mat, bone, light=None, uv=((0, 0), (1, 0), (1, 1), (0, 1))):
        """Flat textured quad facing `normal`, readable from the front (also on mirrored sides)."""
        c, n, u = Vector(center), Vector(normal).normalized(), Vector(up).normalized()
        r = u.cross(n)
        pts = [c - r * w / 2 - u * hgt / 2, c + r * w / 2 - u * hgt / 2, c + r * w / 2 + u * hgt / 2,
               c - r * w / 2 + u * hgt / 2]
        uv = list(uv)
        if self.mirror:
            uv = [(1 - a, b) for a, b in uv]
        ids = [self._vert(p, bone) for p in pts]
        self.face(ids, mat, light, uv=uv, fixed=True)

    def poly(self, pts, mat, bone, light=None, uvs=1.0, fixed=False):
        ids = [self._vert(p, bone) for p in pts]
        self.face(ids, mat, light, uvs, fixed=fixed)

    # ------------------------------------------------------------------ primitives

    def loft(self, rings, mat, bone, closed=True, cap0=True, cap1=True, light=None, uvs=1.0, cap_mat=None):
        """Connect rings of equal length point lists. Rings are traversed in order; caps are filled."""
        n = len(rings[0])
        ids = [[self._vert(p, bone) for p in ring] for ring in rings]
        segs = n if closed else n - 1
        for r in range(len(rings) - 1):
            a, b = ids[r], ids[r + 1]
            for i in range(segs):
                j = (i + 1) % n
                self.face([a[i], a[j], b[j], b[i]], mat, light, uvs)
        if closed:
            cm = cap_mat or mat
            if cap0:
                self._cap(ids[0], [Vector(p) for p in rings[0]], cm, light, uvs, reverse=False)
            if cap1:
                self._cap(ids[-1], [Vector(p) for p in rings[-1]], cm, light, uvs, reverse=True)

    def _cap(self, ids, pts, mat, light, uvs, reverse):
        tris = tessellate_polygon([pts])
        # orient each triangle consistently with the ring winding
        normal = _poly_normal(pts)
        for t in tris:
            a, b, c = (pts[k] for k in t)
            n = (b - a).cross(c - a)
            tri = [ids[k] for k in t]
            flip = n.dot(normal) < 0
            if flip != reverse:
                tri.reverse()
            self.face(tri, mat, light, uvs)

    def box(self, lo, hi, mat, bone, light=None, uvs=1.0):
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        rings = [[(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
                 [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]]
        self.loft(rings, mat, bone, light=light, uvs=uvs)

    def cbox(self, c, size, mat, bone, light=None):
        h = Vector(size) / 2
        c = Vector(c)
        self.box(c - h, c + h, mat, bone, light)

    def rbox(self, lo, hi, r, mat, bone, seg=3, light=None, uvs=1.0):
        """Box with rounded edges along Y (rounded rectangle cross-section in XZ, lofted along Y)."""
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        sec = rrect((x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2, (z1 - z0) / 2, r, seg)
        self.loft([[(x, y0, z) for x, z in sec], [(x, y1, z) for x, z in sec]], mat, bone, light=light, uvs=uvs)

    def extrude_yz(self, outline, x0, x1, mat, bone, light=None, uvs=1.0, side_mat=None):
        """Extrude a 2D outline drawn in the YZ plane (list of (y, z), any shape) from x0 to x1."""
        rings = [[(x0, y, z) for y, z in outline], [(x1, y, z) for y, z in outline]]
        self.loft(rings, side_mat or mat, bone, light=light, uvs=uvs, cap_mat=mat)

    def extrude_xz(self, outline, y0, y1, mat, bone, light=None, uvs=1.0, side_mat=None):
        rings = [[(x, y0, z) for x, z in outline], [(x, y1, z) for x, z in outline]]
        self.loft(rings, side_mat or mat, bone, light=light, uvs=uvs, cap_mat=mat)

    def extrude_xy(self, outline, z0, z1, mat, bone, light=None, uvs=1.0, side_mat=None):
        rings = [[(x, y, z0) for x, y in outline], [(x, y, z1) for x, y in outline]]
        self.loft(rings, side_mat or mat, bone, light=light, uvs=uvs, cap_mat=mat)

    def cylinder(self, p0, p1, r, mat, bone, seg=16, caps=True, light=None, r1=None, uvs=1.0):
        p0, p1 = Vector(p0), Vector(p1)
        axis = (p1 - p0).normalized()
        u, w = _basis(axis)
        r1 = r if r1 is None else r1
        rings = []
        for p, rr in ((p0, r), (p1, r1)):
            rings.append([p + (u * math.cos(a) + w * math.sin(a)) * rr
                          for a in (2 * math.pi * i / seg for i in range(seg))])
        self.loft(rings, mat, bone, cap0=caps, cap1=caps, light=light, uvs=uvs)

    def tube(self, path, r, mat, bone, seg=10, caps=True, uvs=1.0):
        """Round tube along a polyline (for rails, roll bars, pipes)."""
        path = [Vector(p) for p in path]
        rings = []
        for i, p in enumerate(path):
            if i == 0:
                t = path[1] - path[0]
            elif i == len(path) - 1:
                t = path[-1] - path[-2]
            else:
                t = (path[i + 1] - path[i]).normalized() + (path[i] - path[i - 1]).normalized()
            u, w = _basis(t.normalized())
            rings.append([p + (u * math.cos(a) + w * math.sin(a)) * r
                          for a in (2 * math.pi * k / seg for k in range(seg))])
        self.loft(rings, mat, bone, cap0=caps, cap1=caps, uvs=uvs)

    def lathe(self, profile, mat, bone, seg=32, axis_x=True, light=None, uvs=1.0, close=False, polar_uv=None):
        """Revolve a (radius, x) profile around the X axis through the current origin.

        polar_uv=(r_in, r_out, repeats): map u around the circle and v across the radius (tire lettering)."""
        rings = []
        for rad, x in profile:
            rings.append([(x, rad * math.cos(a), rad * math.sin(a))
                          for a in (2 * math.pi * i / seg for i in range(seg))])
        # rings are circles; connect consecutive profile points
        n = seg
        ids = [[self._vert(p, bone) for p in ring] for ring in rings]
        for r in range(len(rings) - 1):
            a, b = ids[r], ids[r + 1]
            for i in range(n):
                j = (i + 1) % n
                uv = None
                if polar_uv is not None:
                    r_in, r_out, rep_ = polar_uv
                    va = (profile[r][0] - r_in) / (r_out - r_in)
                    vb = (profile[r + 1][0] - r_in) / (r_out - r_in)
                    ui, uj = rep_ * i / n, rep_ * (i + 1) / n
                    uv = [(ui, va), (uj, va), (uj, vb), (ui, vb)]
                self.face([a[i], a[j], b[j], b[i]], mat, light, uvs, uv=uv)
        if close:
            a, b = ids[-1], ids[0]
            for i in range(n):
                j = (i + 1) % n
                self.face([a[i], a[j], b[j], b[i]], mat, light, uvs)

    def disc(self, center, normal, r, mat, bone, seg=24, light=None):
        c = Vector(center)
        u, w = _basis(Vector(normal).normalized())
        pts = [c + (u * math.cos(a) + w * math.sin(a)) * r for a in (2 * math.pi * i / seg for i in range(seg))]
        self.poly(pts, mat, bone, light)

    def arch_band(self, cy, cz, r_in, r_out, x0, x1, a0, a1, mat, bone, seg=16):
        """Curved band around a wheel arch (angles in degrees, 0 = +Y/front, 90 = up)."""
        rings = []
        for k in range(seg + 1):
            a = math.radians(a0 + (a1 - a0) * k / seg)
            ca, sa = math.cos(a), math.sin(a)
            rings.append([(x0, cy + ca * r_in, cz + sa * r_in), (x1, cy + ca * r_in, cz + sa * r_in),
                          (x1, cy + ca * r_out, cz + sa * r_out), (x0, cy + ca * r_out, cz + sa * r_out)])
        self.loft(rings, mat, bone)

    # ------------------------------------------------------------------ output

    def to_mesh(self, name, materials, group_index=None):
        """materials: key -> bpy Material. group_index: bone name -> vertex group index (skinned meshes).
        Returns a bpy Mesh."""
        keys = []
        for _, m, _, _, _ in self.faces:
            if m not in keys:
                keys.append(m)
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([tuple(v) for v in self.verts], [], [f[0] for f in self.faces])
        for k in keys:
            mesh.materials.append(materials[k])
        mat_index = [keys.index(f[1]) for f in self.faces]
        mesh.polygons.foreach_set("material_index", mat_index)

        mesh.uv_layers.new(name="UVMap 0")
        mesh.uv_layers.new(name="UVMap 1")
        mesh.color_attributes.new("Color 1", "BYTE_COLOR", "CORNER")
        verts = self.verts
        uv0, uv1, cols = [], [], []
        loop_vert = [0] * len(mesh.loops)
        mesh.loops.foreach_get("vertex_index", loop_vert)
        for poly, (idx, _, alpha, uvs, explicit) in zip(mesh.polygons, self.faces):
            n = poly.normal
            ax = max(range(3), key=lambda i: abs(n[i]))
            if explicit is not None:
                for (u, v) in explicit:
                    uv0 += (u, v)
                    uv1 += (u, v)
                    cols += (DEFAULT_COLOR[0], DEFAULT_COLOR[1], DEFAULT_COLOR[2], alpha)
                continue
            for li in range(poly.loop_start, poly.loop_start + poly.loop_total):
                p = verts[loop_vert[li]]
                if ax == 0:
                    u, v = p.y, p.z
                elif ax == 1:
                    u, v = p.x, p.z
                else:
                    u, v = p.x, p.y
                uv0 += (u * uvs, v * uvs)
                uv1 += (u * 0.25, v * 0.25)
                cols += (DEFAULT_COLOR[0], DEFAULT_COLOR[1], DEFAULT_COLOR[2], alpha)
        mesh.uv_layers["UVMap 0"].data.foreach_set("uv", uv0)
        mesh.uv_layers["UVMap 1"].data.foreach_set("uv", uv1)
        mesh.color_attributes["Color 1"].data.foreach_set("color", cols)
        mesh.validate()
        # Make every closed part face outwards regardless of how its rings were wound.
        bm = bmesh.new()
        bm.from_mesh(mesh)
        if group_index is not None:
            dl = bm.verts.layers.deform.verify()
            bm.verts.ensure_lookup_table()
            for i, bone in enumerate(self.vgroup):
                bm.verts[i][dl][group_index[bone]] = 1.0
        bm.faces.ensure_lookup_table()
        bmesh.ops.recalc_face_normals(bm, faces=[f for f, fx in zip(bm.faces, self.fixed) if not fx])
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        return mesh

    def bones_used(self):
        return sorted(set(self.vgroup))


class _Push:
    def __init__(self, mb, m):
        self.mb, self.m = mb, m

    def __enter__(self):
        self.prev = self.mb.push(self.m)
        return self.mb

    def __exit__(self, *a):
        self.mb.pop(self.prev)


def _basis(axis):
    ref = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))
    u = axis.cross(ref).normalized()
    w = axis.cross(u).normalized()
    return u, w


def _poly_normal(pts):
    n = Vector()
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        n += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
    return n


def rrect(cx, cz, hw, hh, r, seg=3):
    """Rounded rectangle (counter-clockwise) as a list of (x, z)."""
    r = min(r, hw * 0.999, hh * 0.999)
    pts = []
    corners = [(cx + hw - r, cz - hh + r, -90), (cx + hw - r, cz + hh - r, 0),
               (cx - hw + r, cz + hh - r, 90), (cx - hw + r, cz - hh + r, 180)]
    for ox, oz, start in corners:
        if r <= 0:
            pts.append((ox, oz))
            continue
        for k in range(seg + 1):
            a = math.radians(start + 90 * k / seg)
            pts.append((ox + r * math.cos(a), oz + r * math.sin(a)))
    return pts


def arc(cy, cz, r, a0, a1, seg):
    """Points on an arc in the YZ plane (degrees, 0 = +Y)."""
    return [(cy + r * math.cos(math.radians(a0 + (a1 - a0) * k / seg)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * k / seg))) for k in range(seg + 1)]


def finalize_mesh(mesh, smooth_angle=35.0):
    """Smooth shading with sharp edges above the given angle."""
    mesh.shade_smooth()
    if hasattr(mesh, "set_sharp_from_angle"):
        mesh.set_sharp_from_angle(angle=math.radians(smooth_angle))
