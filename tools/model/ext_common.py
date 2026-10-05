"""Helpers shared by the exterior region modules (ext_front / ext_cab / ext_rear)."""
import math

from mathutils import Matrix, Vector

from at4x_dims import *  # noqa: F401,F403
from geom import rrect
from surf import densify, panel, pchip, point_in_poly, smoothstep


IN_X = Vector((-1, 0, 0))


REAR_LIFT = ZG_RAIL - 1.445        # tailgate / lamps / rear bumper were authored for a 1.445 m rail
FRONT_DROP = -0.04                 # lamps / grille authored for a slightly higher hood nose
MIRROR_DROP = -0.12


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


def arch_flare(m, cy, shape, x_fn):
    """Factory black arch moulding (misc_d) following a wheel opening."""
    pts = arch_outline(cy, shape)
    rings = []
    for i, (y, z) in enumerate(pts):
        a = Vector(pts[max(i - 1, 0)])
        b = Vector(pts[min(i + 1, len(pts) - 1)])
        t = (b - a).normalized()
        n = Vector((t.y, -t.x))
        if n.dot(Vector((y - cy, z - 0.5))) < 0:
            n = -n
        xb = x_fn(y + n.x * 0.035, z + n.y * 0.035)
        sec = [(0.0, -0.04), (0.0, 0.018), (0.02, 0.028), (0.048, 0.022), (FLARE_W, 0.004),
               (FLARE_W + 0.002, -0.008), (0.04, -0.035)]
        rings.append([(xb + dx, y + n.x * d, G(z + n.y * d)) for d, dx in sec])
    m.loft(rings, "plastic", "misc_d")


def _lifted(mb, dz):
    return mb.push_ctx(Matrix.Translation((0, 0, dz)))
