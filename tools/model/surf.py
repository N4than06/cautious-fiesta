"""Sheet-metal style panels: dense curved surfaces cut to an exact 2D outline.

A panel is described by
  * an outline (and optional holes) in a 2D drawing plane (side view YZ, top view XY or front view XZ),
  * a height function that lifts each 2D point into 3D (e.g. side view: x = f(y, z)),
  * optional crease polylines that the triangulation must follow (crisp character lines),
  * a flange: the edge of the panel is folded inwards, which is what makes real panel gaps read.
"""
import math

from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt


# ---------------------------------------------------------------------------------------------- curves

def pchip(points):
    """Monotone piecewise-cubic interpolation through (t, value) points (no overshoot)."""
    pts = sorted(points)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    n = len(pts)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    def f(x):
        if x <= xs[0]:
            return ys[0] + m[0] * (x - xs[0])
        if x >= xs[-1]:
            return ys[-1] + m[-1] * (x - xs[-1])
        lo, hi = 0, n - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if xs[mid] <= x:
                lo = mid
            else:
                hi = mid
        i = lo
        t = (x - xs[i]) / h[i]
        t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * m[i] +
                (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h[i] * m[i + 1])
    return f


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def densify(poly, spacing, closed=True):
    out = []
    n = len(poly)
    segs = n if closed else n - 1
    for i in range(segs):
        a, b = Vector(poly[i]), Vector(poly[(i + 1) % n])
        k = max(1, int(math.ceil((b - a).length / spacing)))
        for j in range(k):
            out.append(tuple(a + (b - a) * (j / k)))
    if not closed:
        out.append(tuple(poly[-1]))
    return out


def superellipse_arch(cy, cz, a, b, n, z_bottom, seg=40):
    """Wheel opening outline in YZ: vertical sides below the centre, squared-off top (front->rear order)."""
    pts = [(cy + a, z_bottom)]
    for k in range(seg + 1):
        t = math.pi * k / seg                       # 0 = front, pi = rear
        c, s = math.cos(t), math.sin(t)
        y = cy + a * math.copysign(abs(c) ** (2 / n), c)
        z = cz + b * abs(s) ** (2 / n)
        pts.append((y, z))
    pts.append((cy - a, z_bottom))
    return pts


def point_in_poly(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def _dist_to_poly(p, poly):
    best = 1e9
    px, py = p
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
        qx, qy = ax + t * dx - px, ay + t * dy - py
        best = min(best, qx * qx + qy * qy)
    return math.sqrt(best)


# ---------------------------------------------------------------------------------------------- panel

def panel(mb, outline, lift, mat, bone, out, spacing=0.03, holes=(), creases=(), flange=None, light=None,
          flange_mat=None, uvs=1.0, double=False):
    """Triangulate `outline` (minus `holes`) with interior points every `spacing`, lift into 3D.

    lift(u, v) -> Vector: maps a 2D drawing-plane point to 3D.
    out: Vector (or fn(point3d) -> Vector) giving the outward side; faces are oriented to it explicitly.
    creases: open polylines (2D) the mesh must contain as edges.
    flange: (depth, direction_fn) — direction_fn(point3d) -> unit Vector pointing into the body; the outline and
            hole edges get a folded-back strip of that depth.
    """
    outline = [tuple(p) for p in outline]
    holes = [[tuple(p) for p in h] for h in holes]
    loops = [densify(outline, spacing)] + [densify(h, spacing) for h in holes]
    crease_pts = [densify(c, spacing, closed=False) for c in creases]

    verts2d, edges = [], []
    for loop in loops:
        base = len(verts2d)
        verts2d += loop
        edges += [(base + i, base + (i + 1) % len(loop)) for i in range(len(loop))]
    for c in crease_pts:
        base = len(verts2d)
        verts2d += c
        edges += [(base + i, base + i + 1) for i in range(len(c) - 1)]

    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    u = min(xs) + spacing * 0.5
    while u < max(xs):
        v = min(ys) + spacing * 0.5
        while v < max(ys):
            p = (u, v)
            if point_in_poly(p, outline) and not any(point_in_poly(p, h) for h in holes):
                near = _dist_to_poly(p, outline) < spacing * 0.6 or any(_dist_to_poly(p, h) < spacing * 0.6 for h in holes)
                near = near or any(_dist_to_poly(p, c) < spacing * 0.6 for c in crease_pts if len(c) > 1)
                if not near:
                    verts2d.append(p)
            v += spacing
        u += spacing

    out_v, _, out_f, _, _, _ = delaunay_2d_cdt([Vector(p) for p in verts2d], edges, [], 0, 1e-7)
    keep = []
    for f in out_f:
        c = sum((out_v[i] for i in f), Vector((0, 0))) / len(f)
        cp = (c.x, c.y)
        if point_in_poly(cp, outline) and not any(point_in_poly(cp, h) for h in holes):
            keep.append(f)

    out_fn = out if callable(out) else (lambda p, o=Vector(out): o)
    pts3 = [lift(p.x, p.y) for p in out_v]
    ids = [mb._vert(p, bone) for p in pts3]
    for f in keep:
        a, b, c = (pts3[i] for i in f[:3])
        tri = [ids[i] for i in f]
        if (b - a).cross(c - a).dot(out_fn(a)) < 0:
            tri.reverse()
        _oriented_face(mb, tri, mat, light, uvs)
        if double:
            _oriented_face(mb, list(reversed(tri)), mat, light, uvs)

    if flange:
        depth, dir_fn = flange
        regions = [outline] + []

        def inside(p):
            return point_in_poly(p, outline) and not any(point_in_poly(p, h) for h in holes)
        for loop in loops:
            strip_a = [lift(*p) for p in loop]
            strip_b = [p + dir_fn(p) * depth for p in strip_a]
            n = len(loop)
            ia = [mb._vert(p, bone) for p in strip_a]
            ib = [mb._vert(p, bone) for p in strip_b]
            for i in range(n):
                j = (i + 1) % n
                (ax, ay), (bx, by) = loop[i], loop[j]
                mx, my = (ax + bx) / 2, (ay + by) / 2
                nl = Vector((-(by - ay), bx - ax))
                if nl.length < 1e-9:
                    continue
                nl.normalize()
                eps = 1e-3
                out2 = -nl if inside((mx + nl.x * eps, my + nl.y * eps)) else nl
                pm = lift(mx, my)
                out3 = lift(mx + out2.x * eps, my + out2.y * eps) - pm
                quad = [ia[i], ia[j], ib[j], ib[i]]
                pa, pb, pc = strip_a[i], strip_a[j], strip_b[j]
                if (pb - pa).cross(pc - pa).dot(out3) < 0:
                    quad.reverse()
                _oriented_face(mb, quad, flange_mat or mat, light, uvs)
    return pts3


def _oriented_face(mb, idx, mat, light, uvs):
    """Add a face whose winding is already correct in local space (mirroring is handled by mb.face)."""
    mb.face(idx, mat, light, uvs, fixed=True)
