"""Helpers shared by the exterior region modules (ext_front / ext_cab / ext_rear)."""
import math

from mathutils import Matrix, Vector

from at4x_dims import *  # noqa: F401,F403
from geom import rrect
from surf import densify, panel, pchip, point_in_poly, smoothstep


IN_X = Vector((-1, 0, 0))


def mirror_side(mb, fn):
    fn(mb)
    with mb.mirrored():
        fn(mb)


def side_panel(mb, outline, bone, x_fn, holes=(), creases=(), flange=0.028, mat="paint", spacing=0.026):
    def lift(y, zg):
        return Vector((x_fn(y, zg), y, G(zg)))
    panel(mb, outline, lift, mat, bone, out=(1, 0, 0), spacing=spacing, holes=holes, creases=creases,
          flange=(flange, lambda p: IN_X))


def crease_line(y0, y1):
    return [(y0, ZG_CREASE), (y1, ZG_CREASE)]


def _wheelhouse(mb, cy, shape):
    pts = arch_outline(cy, shape, offset=-0.012)
    rings = [[(x, y, G(z)) for y, z in pts] for x in (0.975, 0.60)]
    mb.loft(rings, "black", "chassis", closed=False)


def _glass_grid(mb, fn, bone, out, nu=8, nv=6, centered=True):
    us = [(-1 + 2 * i / nu) if centered else i / nu for i in range(nu + 1)]
    vs = [j / nv for j in range(nv + 1)]
    grid = [[fn(u, v) for u in us] for v in vs]
    for mat, off, flip in (("glass", 0.0, False), ("glass_in", -0.004, True)):
        ids = [[mb._vert(p + out.normalized() * off, bone) for p in row] for row in grid]
        for j in range(nv):
            for i in range(nu):
                q = [ids[j][i], ids[j][i + 1], ids[j + 1][i + 1], ids[j + 1][i]]
                a, b, c = grid[j][i], grid[j][i + 1], grid[j + 1][i + 1]
                if ((b - a).cross(c - a).dot(out) < 0) != flip:
                    q.reverse()
                mb.face(q, mat, None, fixed=True)


def _rounded_loop(pts, r):
    return rounded_poly(pts[-1:] + pts + pts[:1], r, seg=5)[1:-1]


# Factory arch moulding section (d = distance outwards from the opening edge, dx = stand-off from the body side):
# ~70 mm wide, two-tier crowned face standing ~29 mm proud, rounded inner lip rolling into the wheel opening and a
# rounded outer edge sitting on the paint (same section as the rear moulding in ext_rear).
FLARE_SEC = [(-0.003, -0.050), (-0.006, -0.016), (-0.005, 0.004), (-0.002, 0.015), (0.004, 0.023), (0.012, 0.0275),
             (0.022, 0.0290), (0.036, 0.0285), (0.041, 0.0270), (0.044, 0.0235), (0.050, 0.0215), (0.058, 0.0185),
             (FLARE_W - 0.006, 0.0140), (FLARE_W - 0.002, 0.0090), (FLARE_W, 0.0040), (FLARE_W - 0.001, -0.0005),
             (FLARE_W - 0.010, -0.004), (0.010, -0.006)]


def arch_flare(m, cy, shape, x_fn):
    """Factory black arch moulding (misc_d) following a wheel opening, with rounded ends."""
    pts = densify(arch_outline(cy, shape), 0.035, closed=False)
    rings = []
    for i, (y, z) in enumerate(pts):
        a = Vector(pts[max(i - 1, 0)])
        b = Vector(pts[min(i + 1, len(pts) - 1)])
        t = (b - a).normalized()
        n = Vector((t.y, -t.x))
        if n.dot(Vector((y - cy, z - 0.5))) < 0:
            n = -n
        ring = []
        for d, dx in FLARE_SEC:
            yy, zz = y + n.x * d, z + n.y * d
            ring.append((x_fn(yy, zz) + dx, yy, G(zz)))
        rings.append(ring)

    def shrink(ring, k, dz):
        c = sum((Vector(p) for p in ring), Vector()) / len(ring)
        return [tuple(c + (Vector(p) - c) * k + Vector((0, 0, dz))) for p in ring]
    rings = [shrink(rings[0], 0.55, -0.006), shrink(rings[0], 0.85, -0.003)] + rings + \
        [shrink(rings[-1], 0.85, -0.003), shrink(rings[-1], 0.55, -0.006)]
    m.loft(rings, "plastic", "misc_d")


def _lifted(mb, dz):
    return mb.push_ctx(Matrix.Translation((0, 0, dz)))
