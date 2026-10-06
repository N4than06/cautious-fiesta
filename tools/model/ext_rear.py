"""Rear of the AT4X: bedsides + bed tub, rear arch moulding, MultiPro tailgate, taillamps, rear bumper.

Everything is authored directly in final coordinates relative to the bed rail (ZG_RAIL). Proportions come from the
straight-on rear photos (ref/lib/02_*/*rear_straight), the rear three-quarter photos (03, 04, rear34_sand) and the
side profiles (consumer_006, plaza_004).

The bedside is one continuous sheet that wraps around the plan-view rear corner into the narrow rear face beside the
tailgate: its drawing parameter u runs from the tailgate gap outwards across the rear face, around the corner radius
(stretched KA times in parameter space so the corner gets enough rows) and forwards along the side. The taillamp
pocket, the corner and the rear face are therefore cut from the same surface, and the lamp lens follows it.
"""
import math

from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt, tessellate_polygon

from at4x_dims import *  # noqa: F401,F403
from geom import rrect
from surf import densify, panel, pchip, point_in_poly, smoothstep
from ext_common import mirror_side

# Lamp outer lens: needs a clear-glass material; the shared "glass" is the dark window tint and would black the lamps
# out, so the lens is only built once a "lens" material exists (requested), otherwise the internals show.
try:
    import materials as _materials
    LENS = "lens" if "lens" in _materials.SPEC else None
except ImportError:
    LENS = None

R = ZG_RAIL
Y_T = Y_BED_R                 # rear face of the bedsides / tailgate plane
X_GAP = 0.836                 # inboard edge of the bedside rear face (tailgate gap)
RC, RC_LOW = 0.058, 0.140     # plan size of the bedside rear corner (superellipse) at the lamp / below it
KA = 3.0                      # parameter-space stretch of that corner

TL_TOP, TL_BOT = R - 0.085, R - 0.525        # taillamp
TL_LT, TL_LB = 0.170, 0.085                   # lamp length along the side at its top / bottom

TG_W = 0.8315                 # tailgate half width (4.5 mm shut line to the bedside / lamps)
TG_BOT = R - 0.675            # tailgate lower edge
TG_TOP = R - 0.020            # top of the painted face (black cap above)
IG_W, IG_BOT, IG_R = 0.760, R - 0.338, 0.085  # MultiPro inner gate
Z_LEDGE = R - 0.508           # step below SIERRA: the lower tailgate section stands proud

BP_TOP = TG_BOT - 0.008       # rear bumper step pad top
BP_BOT = BP_TOP - 0.282
RB = 0.125                    # bumper plan corner radius
# The bumper's rear face sits ~9 cm behind the tailgate (side profiles consumer_006 / photo 02), not at the shared
# overall-length station REAR.
YBR = Y_T - 0.088
Y_CAP_F = YBR + 0.420         # front end of the bumper end caps (mid height)
Y_STEP_F = YBR + 0.320        # front edge of the corner-step opening on the end cap
X_STEP_IN = 0.762             # inboard edge of the corner-step cut in the painted face
Z_STEP = BP_TOP - 0.118       # top of the corner-step opening
# front edge of the painted end cap on the side: swept back under the pad, bulging forward at mid height
_CAP_EDGE = pchip([(BP_BOT - 0.01, YBR + 0.380), (BP_BOT + 0.03, YBR + 0.392), (BP_BOT + 0.10, YBR + 0.412),
                   (0.72, Y_CAP_F), (BP_TOP - 0.08, YBR + 0.405), (BP_TOP - 0.03, YBR + 0.370),
                   (BP_TOP + 0.01, YBR + 0.340)])

ZR_BOT = BP_TOP - 0.012       # bedside rear-face lower edge (hidden behind the step pad)
BS_BOT_F = 0.575              # bedside lower edge at the front foot of the wheel opening (ZG_BODY at the cab)
BS_BOT_R = 0.528              # bedside lower edge behind the wheel (down to the bumper's lower edge)

# Rear wheel opening (inner edge of the moulding, relative to the axle), measured on consumer_006 (wheelbase-scaled):
# vertical legs +0.475 / -0.475 from the axle, flat top at 1.08 m, big round upper corners.
R_ARCH = [(0.475, 0.43), (0.475, 0.86), (0.250, 1.080), (-0.270, 1.080), (-0.475, 0.86), (-0.475, 0.43)]
R_ARCH_FILLET = [0.20, 0.22, 0.22, 0.20]
FW = 0.070                    # black moulding width
MOULD_REAR_BOT = 0.420        # the rear leg runs down past the bumper as a short spat

ZC_BED = 1.155                # bedside shoulder crease height (consumer_006: just above the fuel door)
FLARE_A, FLARE_D = 0.014, 0.085  # haunch flare below the crease: amplitude and depth over which it builds

FUEL = (-1.118, 1.036, 0.114, 0.094)     # fuel door centre y, zg, half width, half height (driver side)


def _fillet(pts, radii, seg=5, closed=True):
    """Polygon with filleted corners; radii: number or per-vertex list (0 = sharp)."""
    n = len(pts)
    out = []
    for i in range(n):
        r = radii[i] if isinstance(radii, (list, tuple)) else radii
        b = Vector(pts[i])
        if r <= 0 or (not closed and i in (0, n - 1)):
            out.append(tuple(b))
            continue
        a, c = Vector(pts[i - 1]), Vector(pts[(i + 1) % n])
        d1, d2 = (a - b), (c - b)
        if d1.length < 1e-9 or d2.length < 1e-9:
            out.append(tuple(b))
            continue
        d1.normalize()
        d2.normalize()
        ang = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        if ang < 1e-3 or abs(ang - math.pi) < 1e-3:
            out.append(tuple(b))
            continue
        t = min(r / math.tan(ang / 2), (a - b).length * 0.49, (c - b).length * 0.49)
        p1, p2 = b + d1 * t, b + d2 * t
        for k in range(seg + 1):
            u = k / seg
            out.append(tuple((1 - u) ** 2 * p1 + 2 * (1 - u) * u * b + u ** 2 * p2))
    return out


class Path2:
    """2D polyline parameterised by arc length (linear positions, interpolated vertex tangents)."""

    def __init__(self, pts):
        self.p = [Vector(p) for p in pts]
        self.s = [0.0]
        for i in range(1, len(self.p)):
            self.s.append(self.s[-1] + (self.p[i] - self.p[i - 1]).length)
        self.L = self.s[-1]
        n = len(self.p)
        self.t = [(self.p[min(i + 1, n - 1)] - self.p[max(i - 1, 0)]).normalized() for i in range(n)]

    def at(self, s):
        n = len(self.p)
        if s <= 0:
            return self.p[0] + self.t[0] * s, self.t[0]
        if s >= self.L:
            return self.p[-1] + self.t[-1] * (s - self.L), self.t[-1]
        lo, hi = 0, n - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.s[mid] <= s:
                lo = mid
            else:
                hi = mid
        f = (s - self.s[lo]) / max(1e-12, self.s[hi] - self.s[lo])
        return self.p[lo].lerp(self.p[hi], f), self.t[lo].lerp(self.t[hi], f).normalized()

    def find(self, fn, lo=0.0, hi=None, it=60):
        """s in [lo, hi] where fn(point) changes sign (bisection)."""
        hi = self.L if hi is None else hi
        flo = fn(self.at(lo)[0])
        for _ in range(it):
            mid = (lo + hi) / 2
            if (fn(self.at(mid)[0]) > 0) == (flo > 0):
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2


def _tube(mb, path, r, mat, bone, seg=8, light=None):
    """Round tube along a polyline, with an optional vehicle light id."""
    path = [Vector(p) for p in path]
    rings = []
    for i, p in enumerate(path):
        if i == 0:
            t = path[1] - path[0]
        elif i == len(path) - 1:
            t = path[-1] - path[-2]
        else:
            t = (path[i + 1] - path[i]).normalized() + (path[i] - path[i - 1]).normalized()
        t.normalize()
        ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
        u = t.cross(ref).normalized()
        w = t.cross(u).normalized()
        rings.append([p + (u * math.cos(a) + w * math.sin(a)) * r for a in (2 * math.pi * k / seg for k in range(seg))])
    mb.loft(rings, mat, bone, light=light)


def _flat(mb, pts3, normal, mat, bone, light=None):
    """Flat (possibly concave) polygon, triangulated and facing `normal`."""
    pts3 = [Vector(p) for p in pts3]
    n = Vector(normal)
    for tri in tessellate_polygon([pts3]):
        a, b, c = (pts3[k] for k in tri)
        ids = [mb._vert(p, bone) for p in (a, b, c)]
        if (b - a).cross(c - a).dot(n) < 0:
            ids.reverse()
        mb.face(ids, mat, light, fixed=True)


def edge_strip(mb, loop, lift, inward, depth, mat, bone, inside, spacing, light=None, flip=False):
    """Folded-back strip along a 2D loop of a panel (like surf.panel's flange, but with per-segment depth and
    material: depth(u, v) / mat(u, v) may be callables; mat None skips the segment)."""
    pts = densify(loop, spacing)
    n = len(pts)
    A = [lift(*p) for p in pts]
    B = []
    for p, a in zip(pts, A):
        d = depth(*p) if callable(depth) else depth
        B.append(a + inward(*p) * d)
    ia = [mb._vert(p, bone) for p in A]
    ib = [mb._vert(p, bone) for p in B]
    for i in range(n):
        j = (i + 1) % n
        (ax, ay), (bx, by) = pts[i], pts[j]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        m = mat(mx, my) if callable(mat) else mat
        if m is None:
            continue
        nl = Vector((-(by - ay), bx - ax))
        if nl.length < 1e-9:
            continue
        nl.normalize()
        eps = 1e-3
        out2 = -nl if inside((mx + nl.x * eps, my + nl.y * eps)) else nl
        out3 = lift(mx + out2.x * eps, my + out2.y * eps) - lift(mx, my)
        quad = [ia[i], ia[j], ib[j], ib[i]]
        if ((A[j] - A[i]).cross(B[j] - A[i]).dot(out3) < 0) != flip:
            quad.reverse()
        mb.face(quad, m, light, 1.0, fixed=True)


def loft_fixed(mb, rings, mat, bone, ref, caps=True, closed=True, light=None):
    """Loft whose faces keep the winding implied by the ring/section order (no normal recalculation, so folded
    or self-touching lofts cannot come out partly inside-out). ref = (ring index, section index, expected normal)
    picks the global winding."""
    n = len(rings[0])
    ids = [[mb._vert(p, bone) for p in ring] for ring in rings]
    P = [[Vector(p) for p in ring] for ring in rings]
    ri, si, ne = ref
    a, b_, c = P[ri][si], P[ri][(si + 1) % n], P[ri + 1][(si + 1) % n]
    flip = (b_ - a).cross(c - a).dot(Vector(ne)) < 0
    segs = n if closed else n - 1
    for r in range(len(rings) - 1):
        for i in range(segs):
            j = (i + 1) % n
            q = [ids[r][i], ids[r][j], ids[r + 1][j], ids[r + 1][i]]
            if flip:
                q.reverse()
            mb.face(q, mat, light, 1.0, fixed=True)
    if caps and closed:
        for k, sgn in ((0, -1), (len(rings) - 1, 1)):
            t = (P[min(k + 1, len(P) - 1)][0] - P[max(k - 1, 0)][0]).normalized() * sgn
            _flat(mb, rings[k], t, mat, bone, light)


def _grid_faces(mb, grid, mat, bone, light=None, double=False):
    """Quads over a grid of (point, expected outward normal) with explicit orientation (double: both sides)."""
    ids = [[mb._vert(p, bone) for p, _ in row] for row in grid]
    ids2 = [[mb._vert(p - n.normalized() * 0.0015, bone) for p, n in row] for row in grid] if double else None
    for i in range(len(grid) - 1):
        for j in range(len(grid[0]) - 1):
            P = [grid[i][j][0], grid[i + 1][j][0], grid[i + 1][j + 1][0], grid[i][j + 1][0]]
            ne = grid[i][j][1] + grid[i + 1][j + 1][1]
            q = [ids[i][j], ids[i + 1][j], ids[i + 1][j + 1], ids[i][j + 1]]
            nn = (P[1] - P[0]).cross(P[2] - P[0]) + (P[2] - P[0]).cross(P[3] - P[0])
            rev = nn.dot(ne) < 0
            if rev:
                q.reverse()
            mb.face(q, mat, light, 1.0, fixed=True)
            if double:
                q2 = [ids2[i][j], ids2[i + 1][j], ids2[i + 1][j + 1], ids2[i][j + 1]]
                if not rev:
                    q2.reverse()
                mb.face(q2, mat, light, 1.0, fixed=True)


def _call(f, u, v):
    return f(u, v) if callable(f) else f


def spanel(mb, outline, lift, mat, bone, out, spacing, holes=(), creases=(), roll=None, light=None,
           regions=None, uvs=1.0):
    """surf.panel with a rolled (radiused) edge that shares the panel's boundary vertices, so highlights run
    smoothly over the edge into the shut line.

    roll: dict(r=radius, depth=total fold depth, inward=fn(u, v) -> unit Vector into the body,
               mat=roll material (str | fn(u, v) | None to skip a segment), fmat=material of the straight fold
               below the radius (default: mat), seg=rows on the radius, loops=None (all) or indices of the loops
               (0 = outline, 1.. = holes) that get the edge). r and depth may be fn(u, v).
    """
    outline = [tuple(p) for p in outline]
    holes = [[tuple(p) for p in h] for h in holes]
    loops = [densify(outline, spacing)] + [densify(h, spacing) for h in holes]
    crease_pts = [densify(c, spacing, closed=False) for c in creases]

    def inside(p):
        return point_in_poly(p, outline) and not any(point_in_poly(p, h) for h in holes)
    verts2d, edges, loop_ids = [], [], []
    for loop in loops:
        base = len(verts2d)
        loop_ids.append(list(range(base, base + len(loop))))
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
            if inside(p):
                near = any(_dist_poly(p, lp) < spacing * 0.6 for lp in loops)
                near = near or any(_dist_poly(p, c, False) < spacing * 0.6 for c in crease_pts if len(c) > 1)
                if not near:
                    verts2d.append(p)
            v += spacing
        u += spacing
    out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt([Vector(p) for p in verts2d], edges, [], 0, 1e-7)
    in2out = {}
    for oi, origs in enumerate(orig_v):
        for k in origs:
            in2out[k] = oi
    out_fn = out if callable(out) else (lambda p, o=Vector(out): o)
    pts3 = [lift(p.x, p.y) for p in out_v]
    cache = {}

    def vid(i, b=bone):
        if (i, b) not in cache:
            cache[(i, b)] = mb._vert(pts3[i], b)
        return cache[(i, b)]
    for f in out_f:
        c = sum((out_v[i] for i in f), Vector((0, 0))) / len(f)
        if not inside((c.x, c.y)):
            continue
        fmat, fbone = mat, bone
        if regions is not None:
            r = regions(c.x, c.y)
            if r is None:
                continue
            fmat, fbone = r
        a, b, cc = (pts3[i] for i in f[:3])
        tri = [vid(i, fbone) for i in f]
        if (b - a).cross(cc - a).dot(out_fn(a)) < 0:
            tri.reverse()
        mb.face(tri, fmat, light, uvs, fixed=True)
    if not roll:
        return pts3
    seg = roll.get("seg", 3)
    rmat = roll.get("mat", mat)
    fmat_ = roll.get("fmat", rmat)
    sel = roll.get("loops")
    for li, (loop, ids) in enumerate(zip(loops, loop_ids)):
        if sel is not None and li not in sel:
            continue
        n = len(loop)
        rows, nrm = [], []
        for i in range(n):
            p = Vector(loop[i])
            t = (Vector(loop[(i + 1) % n]) - Vector(loop[i - 1]))
            if t.length < 1e-9:
                t = Vector(loop[(i + 1) % n]) - p
            t.normalize()
            m = Vector((t.y, -t.x))
            if inside(tuple(p + m * 1e-4)):
                m = -m
            r = _call(roll["r"], p.x, p.y)
            dep = _call(roll["depth"], p.x, p.y)
            w = roll["inward"](p.x, p.y)
            oi = in2out[ids[i]]
            ring, rp = [vid(oi)], [pts3[oi]]
            for j in range(1, seg + 1):
                th = 0.5 * math.pi * j / seg
                rp.append(lift(*(p + m * (r * math.sin(th)))) + w * (r * (1 - math.cos(th))))
                ring.append(mb._vert(rp[-1], bone))
            rp.append(lift(*(p + m * r)) + w * max(dep, r + 1e-4))
            ring.append(mb._vert(rp[-1], bone))
            m3 = lift(*(p + m * 1e-3)) - lift(*p)
            m3.normalize()
            rows.append((ring, rp))
            nrm.append((-w, m3))
        for i in range(n):
            j = (i + 1) % n
            (ax, ay), (bx, by) = loop[i], loop[j]
            mx, my = (ax + bx) / 2, (ay + by) / 2
            for k in range(seg + 1):
                mm = _call(rmat if k < seg else fmat_, mx, my)
                if mm is None:
                    continue
                if k < seg:
                    th = 0.5 * math.pi * (k + 0.5) / seg
                    ne = nrm[i][0] * math.cos(th) + nrm[i][1] * math.sin(th)
                else:
                    ne = nrm[i][1]
                q = [rows[i][0][k], rows[j][0][k], rows[j][0][k + 1], rows[i][0][k + 1]]
                P = [rows[i][1][k], rows[j][1][k], rows[j][1][k + 1], rows[i][1][k + 1]]
                nn = (P[1] - P[0]).cross(P[2] - P[0]) + (P[2] - P[0]).cross(P[3] - P[0])
                if nn.dot(ne) < 0:
                    q.reverse()
                mb.face(q, mm, light, uvs, fixed=True)
    return pts3


def _dist_poly(p, poly, closed=True):
    best = 1e18
    px, py = p
    n = len(poly)
    for i in range(n if closed else n - 1):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
        qx, qy = ax + t * dx - px, ay + t * dy - py
        best = min(best, qx * qx + qy * qy)
    return math.sqrt(best)


# ---------------------------------------------------------------------------------------------- body side

def arch_pts(offset=0.0, seg=10, z_front=None, z_rear=None):
    """Rear wheel opening outline (y, zg), front foot -> over the top -> rear foot, optionally offset outwards."""
    zf = R_ARCH[0][1] if z_front is None else z_front
    zr = R_ARCH[-1][1] if z_rear is None else z_rear
    base = [(RAX + R_ARCH[0][0], zf)] + [(RAX + dy, z) for dy, z in R_ARCH[1:-1]] + [(RAX + R_ARCH[-1][0], zr)]
    pts = _fillet(base, [0] + list(R_ARCH_FILLET) + [0], seg=seg, closed=False)
    pts = densify(pts, 0.025, closed=False)
    if offset == 0.0:
        return pts
    out = []
    for i, p in enumerate(pts):
        a = Vector(pts[max(i - 1, 0)])
        b = Vector(pts[min(i + 1, len(pts) - 1)])
        t = (b - a).normalized()
        n = Vector((t.y, -t.x))
        if n.dot(Vector(p) - Vector((RAX, 0.55))) < 0:
            n = -n
        out.append((p[0] + n.x * offset, p[1] + n.y * offset))
    return out


def crease_z(y):
    """Height of the bedside shoulder crease: continues the cab line at the bed front, then runs just above the
    fuel door and the rear arch moulding back into the taillamp (consumer_006 / rear34 photos)."""
    return ZC_BED + 0.052 * gauss(y, RAX - 0.02, 0.55)


def _remap(zg, zc):
    """Height on the shared side profile (crease at ZG_CREASE) for a bedside height whose crease sits at zc."""
    if zg <= zc:
        return 0.40 + (zg - 0.40) * (ZG_CREASE - 0.40) / (zc - 0.40)
    return ZG_CREASE + (zg - zc) * (ZG_RAIL - ZG_CREASE) / (ZG_RAIL - zc)


def _bow(y):
    """Plan bow of the bedside: the shared one with a softer bulge over the rear wheel (keeps the width in check)."""
    return bow(y) - 0.012 * haunch(y)


_X_CACHE = {}


def bs_x(y, zg):
    """Bedside outer surface (side portion): shared side profile with the crease moved to crease_z(y), plan bow,
    tumblehome above the crease on the haunch, and the flare below the crease (the haunch around the wheel)."""
    key = (round(y, 6), round(zg, 6))
    v = _X_CACHE.get(key)
    if v is not None:
        return v
    zc = crease_z(y)
    x = side_base(_remap(zg, zc)) + _bow(y)
    if zg > zc:
        k = (zg - zc) / (ZG_RAIL - zc)
        x -= 0.016 * haunch(y) * k * k
    else:
        d = min(1.0, (zc - zg) / FLARE_D)
        amp = FLARE_A * smoothstep(Y_BED_F - 0.01, Y_BED_F - 0.30, y) * (0.55 + 0.45 * smoothstep(Y_T + 0.05, Y_T + 0.45, y))
        x += amp * (1 - (1 - d) ** 2)
    _X_CACHE[key] = x
    return x


def RCz(zg):
    """Size of the bedside rear corner in plan: tight where the lamp wraps it, generous below the lamp."""
    return RC + (RC_LOW - RC) * smoothstep(TL_BOT + 0.02, TL_BOT - 0.26, zg)


SE_N = 2.6          # superellipse exponent of the plan corner: curvature fades to zero into the flats (G2 blend)


def _se_tables(n=SE_N, k=256):
    """Arc length of the unit superellipse quarter as a function of its parameter (for real-length placement)."""
    ph = [0.5 * math.pi * i / k for i in range(k + 1)]
    pts = [(math.sin(p) ** (2 / n), -math.cos(p) ** (2 / n)) for p in ph]
    s = [0.0]
    for i in range(1, k + 1):
        s.append(s[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    return ph, s


_SE_PH, _SE_S = _se_tables()
SE_LEN = _SE_S[-1]                      # quarter length of the unit superellipse


def _se_phi(frac):
    """Superellipse parameter at a fraction of the quarter's arc length."""
    t = frac * SE_LEN
    lo, hi = 0, len(_SE_S) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if _SE_S[mid] <= t:
            lo = mid
        else:
            hi = mid
    f = (t - _SE_S[lo]) / max(1e-12, _SE_S[hi] - _SE_S[lo])
    return _SE_PH[lo] + (_SE_PH[hi] - _SE_PH[lo]) * f


def se_corner(cx, cy, A, frac):
    """Point and outward normal on the plan corner (rear face -> side) at a fraction of its arc length.
    (cx, cy) is the corner centre: rear face at y = cy - A, side at x = cx + A."""
    ph = _se_phi(max(0.0, min(1.0, frac)))
    sx, cyy = math.sin(ph) ** (2 / SE_N), math.cos(ph) ** (2 / SE_N)
    nx, ny = sx ** (SE_N - 1), -(cyy ** (SE_N - 1))
    ln = math.hypot(nx, ny)
    return (cx + A * sx, cy - A * cyy), (nx / ln, ny / ln)


def bs_corner(zg):
    rc = RCz(zg)
    xc = bs_x(Y_T + rc, zg)
    return xc, xc - rc - X_GAP


def bs_frame(u, zg):
    """Point (x, y) and outward normal (nx, ny) on the bedside plan contour at height zg."""
    rc = RCz(zg)
    xc, a = bs_corner(zg)
    la = KA * rc * SE_LEN
    if u <= a:
        return (X_GAP + u, Y_T), (0.0, -1.0)
    if u <= a + la:
        return se_corner(xc - rc, Y_T + rc, rc, (u - a) / la)
    y = Y_T + rc + (u - a - la)
    # side portion: follow the surface normal in plan (the bow is tiny, keep the normal on +x)
    return (bs_x(y, zg), y), (1.0, 0.0)


def bs_lift(u, zg, inset=0.0):
    (x, y), (nx, ny) = bs_frame(u, zg)
    return Vector((x - nx * inset, y - ny * inset, G(zg)))


def bs_in(u, zg):
    _, (nx, ny) = bs_frame(u, zg)
    return Vector((-nx, -ny, 0.0))


def bs_u(y, zg):
    """u of a point on the side portion."""
    rc = RCz(zg)
    xc, a = bs_corner(zg)
    return a + KA * rc * SE_LEN + (y - Y_T - rc)


def bs_cu(c, zg):
    """u of a real contour length c (measured from the tailgate gap)."""
    rc = RCz(zg)
    xc, a = bs_corner(zg)
    arc = rc * SE_LEN
    if c <= a:
        return c
    if c <= a + arc:
        return a + (c - a) * KA
    return c + (KA - 1) * arc


def bs_out(p):
    zg = p.z - GROUND
    rc = RCz(zg)
    xc, a = bs_corner(zg)
    if p.y >= Y_T + rc - 1e-5:
        return Vector((1, 0, 0))
    if p.x <= xc - rc + 1e-6:
        return Vector((0, -1, 0))
    return Vector((p.x - (xc - rc), p.y - (Y_T + rc), 0)).normalized()


def lamp_outline(gap=0.0, u0=0.0):
    """Taillamp outline in bedside (u, zg) space: top edge level, front edge raked on the side, rounded front."""
    zt, zb = TL_TOP - gap, TL_BOT + gap
    u_tf = bs_u(Y_T + TL_LT - gap, zt)
    u_bf = bs_u(Y_T + TL_LB - gap, zb)
    return _fillet([(u0, zb), (u_bf, zb), (u_tf, zt), (u0, zt)], [0, 0.04, 0.075, 0], seg=9)


def fuel_door_outline(gap=0.0):
    yc, zc, hw, hh = FUEL
    hw, hh = hw - gap, hh - gap
    pts = _fillet([(yc - hw, zc - hh), (yc + hw, zc - hh), (yc + hw, zc + hh), (yc - hw, zc + hh)],
                  [0.050, 0.050, 0.040, 0.040], seg=7)
    return [(bs_u(y, z), z) for y, z in pts]


def cap_front_y(zg):
    """Front edge of the painted bumper end cap on the side (y), from the step pad down to the bottom."""
    return _CAP_EDGE(zg)


def bedside(m, fuel):
    r_top = R - 0.012
    g = 0.0045                                                   # shut line to the bumper end cap
    # outline in (u, zg): rear face bottom (behind the step pad) -> along the cap -> down the cap's front edge ->
    # lower edge behind the wheel -> wheel opening -> lower edge ahead of the wheel -> front edge -> rail -> lamp
    ol = [(0.0, ZR_BOT)]
    zs = [ZR_BOT - (ZR_BOT - (BP_BOT + 0.03)) * k / 24 for k in range(25)]
    ol += [(bs_u(cap_front_y(z) + g, z), z) for z in zs]
    yb = cap_front_y(BP_BOT + 0.03) + g
    ol += [(bs_u(yb + 0.03, BS_BOT_R + 0.012), BS_BOT_R + 0.012), (bs_u(yb + 0.07, BS_BOT_R), BS_BOT_R)]
    arch = arch_pts(z_front=BS_BOT_F, z_rear=BS_BOT_R)
    ol += [(bs_u(y, z), z) for y, z in reversed(arch)]
    yf = Y_BED_F
    ol += [(bs_u(y, z), z) for y, z in ((RAX + 0.62, BS_BOT_F + 0.004), (RAX + 0.90, BS_BOT_F + 0.014),
                                       (yf, ZG_BODY))]
    ol += [(bs_u(yf, ZG_BODY + (r_top - ZG_BODY) * k / 90), ZG_BODY + (r_top - ZG_BODY) * k / 90)
           for k in range(1, 91)]
    ol += [(0.0, r_top), (0.0, TL_TOP)]
    ol += list(reversed(lamp_outline()))[1:-1]
    ol += [(0.0, TL_BOT)]
    holes = [fuel_door_outline(-0.0005)] if fuel else []
    sp = 0.024
    # crease + guide lines either side so the mesh resolves the shoulder crisply
    yl = Y_T + TL_LB + (TL_LT - TL_LB) * (ZC_BED - TL_BOT) / (TL_TOP - TL_BOT) + 0.012
    ys = [Y_BED_F - 0.004 - (Y_BED_F - 0.004 - yl) * k / 70 for k in range(71)]
    creases = []
    for dz in (-0.022, -0.009, 0.0, 0.008):
        creases.append([(bs_u(y, crease_z(y) + dz), crease_z(y) + dz) for y in ys])

    def in_pocket(u, z):
        return TL_BOT - 1e-4 <= z <= TL_TOP + 1e-4 and 1e-4 < u < bs_u(Y_T + 0.30, TL_TOP)

    def is_gap(u, z):                                   # tailgate gap edge of the rear face
        return u < 1e-4 and z < TL_BOT - 1e-4

    def rmat(u, z):
        return "paint"

    def fmat(u, z):
        if in_pocket(u, z):
            return "black"
        return "paint"

    def depth(u, z):
        if in_pocket(u, z):
            return 0.034
        if z < BS_BOT_F + 0.02 and u > 0.3:             # lower edges: a deeper return flange
            return 0.030
        return 0.024
    spanel(m, ol, bs_lift, "paint", "chassis", bs_out, sp, holes=holes, creases=creases,
           roll=dict(r=0.0035, depth=depth, inward=bs_in, mat=rmat, fmat=fmat, seg=3, loops=[0]))
    if fuel:
        # fuel door: hinged on the front edge, sits 1 mm proud in a 4 mm shut line with a dark pocket behind
        door = fuel_door_outline(0.0040)
        h = fuel_door_outline(-0.0005)
        edge_strip(m, h, lambda u, z: bs_lift(u, z), bs_in, 0.020, "black", "chassis",
                   lambda p: not point_in_poly(p, h), 0.02)
        _flat(m, [bs_lift(u, z, 0.020) for u, z in h], (1, 0, 0), "black", "chassis")

        def dl(u, z):
            return bs_lift(u, z, -0.0006)
        spanel(m, door, dl, "paint", "petrolcap", bs_out, 0.02,
               roll=dict(r=0.0028, depth=0.010, inward=bs_in, seg=3))


def rail_cap(m):
    """Black bed-rail protector on top of the bedside (wraps over the outer edge, rounds the rear corner)."""
    rings = []
    zr = R - 0.012
    rc = RCz(zr)
    xc, a = bs_corner(zr)
    pts = [(bs_x(y, zr), y) for y in (Y_BED_F + 0.004 - (Y_BED_F + 0.004 - (Y_T + rc)) * k / 48 for k in range(48))]
    pts += [se_corner(xc - rc, Y_T + rc, rc, 1 - k / 12)[0] for k in range(12)]
    pts += [(xc - rc - 0.002, Y_T - 0.001)]
    for xo, y in pts:
        xi = 0.795 + (X_GAP + 0.002 - 0.795) * smoothstep(Y_T + 0.095, Y_T + 0.072, y)   # clear of the tailgate
        rings.append([(xi, y, G(R - 0.024)), (xi, y, G(R + 0.003)), (xi + 0.005, y, G(R + 0.0085)),
                      (xi + 0.015, y, G(R + 0.0105)), (xo - 0.020, y, G(R + 0.0105)), (xo - 0.008, y, G(R + 0.008)),
                      (xo - 0.0015, y, G(R + 0.002)), (xo + 0.0035, y, G(R - 0.006)), (xo + 0.0045, y, G(R - 0.014)),
                      (xo + 0.002, y, G(R - 0.019)), (xo - 0.008, y, G(R - 0.020))])
    # rounded rear end: the section rolls down over the rear face
    last = rings[-1]
    for k, (dy, dz, sc) in enumerate(((-0.002, -0.001, 0.98), (-0.0035, -0.004, 0.92), (-0.0045, -0.008, 0.80))):
        c = sum((Vector(p) for p in last), Vector()) / len(last)
        rings.append([(p[0], p[1] + dy, c.z + (p[2] - c.z) * sc + dz) for p in last])
    m.loft(rings, "plastic", "chassis")


def wheelhouse(m):
    """Black wheel-well liner: follows the opening, curves in over the tyre."""
    pts = arch_pts(offset=-0.012, z_front=BS_BOT_F - 0.03, z_rear=0.43)
    up = arch_pts(offset=0.008, z_front=BS_BOT_F - 0.03, z_rear=0.43)
    rings = []
    # first ring tucks up behind the bedside's folded edge, so nothing of the hollow bedside shows
    rings.append([(Vector((bs_x(y, max(z, BS_BOT_R)) - 0.030, y, G(z))), Vector((0.0, RAX - y, WZ - G(z))).normalized())
                  for y, z in up])
    for x0, dz in ((None, 0.0), (0.90, 0.02), (0.78, 0.035), (0.62, 0.045)):
        ring = []
        for y, z in pts:
            x = bs_x(y, max(z, BS_BOT_R)) - 0.032 if x0 is None else x0
            ring.append((Vector((x, y, G(z + dz * smoothstep(0.6, 1.0, z)))),
                         Vector((0.0, RAX - y, WZ - G(z))).normalized()))
        rings.append(ring)
    n = min(len(r) for r in rings)
    _grid_faces(m, [list(r) for r in zip(*[r[:n] for r in rings])], "black", "chassis", double=True)
    # inner wall closes the tub (no see-through under the bed)
    wall = [(0.62, y, G(z + 0.045 * smoothstep(0.6, 1.0, z))) for y, z in pts]
    _flat(m, wall, (1, 0, 0), "black", "chassis")
    _flat(m, [(x - 0.0015, y, z) for x, y, z in wall], (-1, 0, 0), "black", "chassis")


def bedside_closures(m):
    """Black closing panels under the hollow bedside (ahead of and behind the wheel), facing down."""
    def strip(y0, y1, zf):
        n = 16
        grid = []
        for i in range(n + 1):
            y = y0 + (y1 - y0) * i / n
            z = zf(y)
            xo = bs_x(y, z) - 0.026
            grid.append([(Vector((x, y, G(z))), Vector((0, 0, -1))) for x in (xo, 0.86, 0.80)])
        _grid_faces(m, grid, "black", "chassis")
    yf = RAX + R_ARCH[0][0] + 0.02
    strip(yf, Y_BED_F - 0.004, lambda y: BS_BOT_F + 0.006 + (ZG_BODY - BS_BOT_F) * smoothstep(RAX + 0.6, Y_BED_F, y))
    yr = RAX + R_ARCH[-1][0] - 0.02
    strip(cap_front_y(0.70) + 0.03, yr, lambda y: BS_BOT_R + 0.006)


def arch_moulding(m):
    """Factory black rear arch moulding (misc_d): ~70 mm wide, two-tier crowned face standing ~28 mm proud,
    rounded inner lip rolling into the wheel opening, rounded outer edge. The rear leg runs down past the bumper
    as a short spat; the front leg stops at the bedside's lower edge."""
    pts = arch_pts(seg=14, z_front=BS_BOT_F - 0.018, z_rear=MOULD_REAR_BOT)
    sec = [(-0.003, -0.050), (-0.006, -0.016), (-0.005, 0.004), (-0.002, 0.015), (0.004, 0.023), (0.012, 0.0275),
           (0.022, 0.0290), (0.036, 0.0285), (0.041, 0.0270), (0.044, 0.0235), (0.050, 0.0215), (0.058, 0.0185),
           (FW - 0.006, 0.0140), (FW - 0.002, 0.0090), (FW, 0.0040), (FW - 0.001, -0.0005), (FW - 0.010, -0.004),
           (0.010, -0.006)]
    rings = []
    n = len(pts)
    for i, (y, z) in enumerate(pts):
        a = Vector(pts[max(i - 1, 0)])
        b = Vector(pts[min(i + 1, n - 1)])
        t = (b - a).normalized()
        nn = Vector((t.y, -t.x))
        if nn.dot(Vector((y, z)) - Vector((RAX, 0.55))) < 0:
            nn = -nn
        ring = []
        for d, dx in sec:
            yy, zz = y + nn.x * d, z + nn.y * d
            ring.append((bs_x(yy, max(zz, BS_BOT_R)) + dx, yy, G(zz)))
        rings.append(ring)
    # rounded ends: shrink the section over the last few millimetres
    def shrink(ring, k, dz):
        c = sum((Vector(p) for p in ring), Vector()) / len(ring)
        return [tuple(c + (Vector(p) - c) * k + Vector((0, 0, dz))) for p in ring]
    rings = [shrink(rings[0], 0.55, -0.006), shrink(rings[0], 0.85, -0.003)] + rings + \
        [shrink(rings[-1], 0.85, -0.003), shrink(rings[-1], 0.55, -0.006)]
    m.loft(rings, "plastic", "misc_d")


# ---------------------------------------------------------------------------------------------- bed tub

def bed_tub(mb):
    fl = BED_FLOOR
    y0, y1 = Y_T + 0.068, Y_BED_F - 0.045            # tailgate inner face .. front wall
    zt = R - 0.020

    def wall(m):
        m.box((0.800, y0, G(fl)), (0.836, y1, G(zt)), "bedliner", "chassis")
        # stamped vertical ribs
        for y in (y1 - 0.25, y1 - 0.62, RAX + 0.62, RAX - 0.62, y0 + 0.22):
            m.box((0.790, y - 0.035, G(fl + 0.26)), (0.801, y + 0.035, G(zt - 0.05)), "bedliner", "chassis")
        # wheel tub
        m.loft([[(x, y, G(z)) for x, z in ((0.801, fl), (0.801, fl + 0.20), (0.775, fl + 0.255), (0.70, fl + 0.275),
                                           (0.60, fl + 0.265), (0.565, fl + 0.22), (0.56, fl))]
                for y in (RAX - 0.50, RAX - 0.47, RAX + 0.47, RAX + 0.50)], "bedliner", "chassis")
        # tie-down cleats (low and high)
        for y in (y0 + 0.10, y1 - 0.10):
            m.box((0.775, y - 0.04, G(fl + 0.05)), (0.800, y + 0.04, G(fl + 0.09)), "steel", "chassis")
        for y in (y0 + 0.12, y1 - 0.12):
            m.box((0.770, y - 0.03, G(zt - 0.09)), (0.800, y + 0.03, G(zt - 0.05)), "steel", "chassis")
        # cargo lamp under the rail at the front
        m.box((0.796, y1 - 0.22, G(zt - 0.045)), (0.801, y1 - 0.14, G(zt - 0.025)), "light_clear", "chassis")
    mirror_side(mb, wall)
    mb.box((-0.836, y1, G(fl)), (0.836, Y_BED_F, G(zt)), "bedliner", "chassis")              # front wall
    for k in range(-5, 6):
        x = k * 0.14
        mb.box((x - 0.025, y1 - 0.010, G(fl + 0.05)), (x + 0.025, y1, G(zt - 0.06)), "bedliner", "chassis")
    mb.box((-0.836, y0, G(fl - 0.045)), (0.836, y1, G(fl)), "bedliner", "chassis")           # floor
    for k in range(-6, 7):                                                                    # floor corrugations
        x = k * 0.118
        mb.box((x - 0.028, y0 + 0.02, G(fl)), (x + 0.028, y1 - 0.02, G(fl + 0.014)), "bedliner", "chassis")
    mb.box((-0.99, Y_BED_F, G(0.62)), (0.99, Y_BED_F + 0.008, G(R - 0.01)), "black", "chassis")  # cab gap filler
    mb.box((-0.836, Y_T + 0.04, G(TG_BOT + 0.01)), (0.836, y0, G(fl)), "black", "chassis")   # sill under the gate


def build_bedsides(mb):
    bedside(mb, False)
    with mb.mirrored():
        bedside(mb, True)
    mirror_side(mb, rail_cap)
    mirror_side(mb, wheelhouse)
    mirror_side(mb, bedside_closures)
    mirror_side(mb, arch_moulding)
    bed_tub(mb)


# ---------------------------------------------------------------------------------------------- taillamps

def _c2u(c, z):
    return bs_cu(c, z)


def _front_c(z, gap=0.0):
    """Contour length (from the tailgate gap) of the lamp's front edge on the side at height z."""
    t = (z - TL_BOT) / (TL_TOP - TL_BOT)
    y = Y_T + TL_LB + (TL_LT - TL_LB) * t - gap
    rc = RCz(z)
    xc, a = bs_corner(z)
    return a + rc * SE_LEN + (y - Y_T - rc)


def taillamp(m, tail, brake, ind, rev):
    """Taillamp in its bedside pocket: lens rim, deep black housing, inboard chamber (bright red field, C-shaped
    light pipe, clear reverse block), raised silver divider, smoked-red outboard section wrapping the corner with the
    upper stop/turn chamber and an outer light pipe."""
    b = "chassis"
    gap = 0.0025
    zb, zt = TL_BOT, TL_TOP

    def L(d):
        return lambda u, z: bs_lift(u, z, d)

    def ins(poly):
        return lambda p: point_in_poly(p, poly)

    def CZ(pts):
        return [(_c2u(c, z), z) for c, z in pts]
    lo = lamp_outline(gap)
    # lens rim (the clear lens edge catching the light) and the housing walls behind it
    rim_in = lamp_outline(gap + 0.0045, 0.0025)
    panel(m, lo, L(0.0030), "alu", b, out=bs_out, spacing=0.03, holes=[rim_in])
    edge_strip(m, rim_in, L(0.0030), bs_in, 0.046, "black", b, ins(rim_in), 0.014, flip=True)
    if LENS:
        panel(m, lamp_outline(gap + 0.001), L(0.0022), LENS, b, out=bs_out, spacing=0.02)
    # inboard housing strip next to the tailgate gap
    panel(m, CZ([(0.003, zb + 0.006), (0.013, zb + 0.006), (0.013, zt - 0.006), (0.003, zt - 0.006)]), L(0.008),
          "gloss_black", b, out=bs_out, spacing=0.02)
    # inboard chamber: bright red field around the clear reverse block
    c_div0, c_div1 = 0.086, 0.108
    fz0, fz1 = zb + 0.010, zt - 0.010
    field = CZ(_fillet([(0.013, fz0), (c_div0 + 0.002, fz0), (c_div0 + 0.002, fz1), (0.013, fz1)],
                       [0.01, 0.0, 0.0, 0.01], seg=3))
    rv = _fillet([(0.017, 1.086), (0.052, 1.086), (0.052, 1.182), (0.017, 1.182)], 0.006, seg=3)
    panel(m, field, L(0.042), "red", b, out=bs_out, spacing=0.016, holes=[CZ(rv)])
    # faint vertical optic flutes in the field
    for c in (0.030, 0.046, 0.062):
        zz = [fz0 + 0.04 + (fz1 - fz0 - 0.08) * k / 10 for k in range(11)]
        _tube(m, [bs_lift(_c2u(c, z), z, 0.041) for z in zz if not (c < 0.055 and 1.08 < z < 1.19)], 0.0025, "red", b,
              seg=5)
    # reverse lamp: clear block with horizontal optic ribs
    panel(m, CZ(rv), L(0.028), "light_clear", b, out=bs_out, spacing=0.012, light=rev)
    edge_strip(m, CZ(rv), L(0.028), bs_in, 0.015, "light_clear", b, ins(CZ(rv)), 0.012, light=rev)
    for k in range(8):
        z = 1.093 + k * 0.0115
        _tube(m, [bs_lift(_c2u(c, z), z, 0.0272) for c in (0.020, 0.0345, 0.049)], 0.0022, "light_clear", b, seg=5,
              light=rev)
    # C-shaped light pipe (tail): inboard bar from above the reverse block, over the top, down the outboard side
    # of the chamber and back along the bottom under the reverse block
    rr = 0.020
    loop = _fillet([(0.021, 1.200), (0.021, zt - 0.034), (0.077, zt - 0.034), (0.077, zb + 0.046),
                    (0.026, zb + 0.046)], [0, rr, rr, rr, 0], seg=7, closed=False)
    loop = densify(loop, 0.010, closed=False)
    _tube(m, [bs_lift(_c2u(c, z), z, 0.024) for c, z in loop], 0.0068, "light_red", b, seg=10, light=tail)
    # thin outer pipe tracing the chamber's outboard edge
    loop2 = _fillet([(0.030, zt - 0.018), (0.084, zt - 0.018), (0.084, zb + 0.022), (0.030, zb + 0.022)],
                    [0, 0.018, 0.018, 0], seg=6, closed=False)
    loop2 = densify(loop2, 0.012, closed=False)
    _tube(m, [bs_lift(_c2u(c, z), z, 0.030) for c, z in loop2], 0.0028, "light_red", b, seg=6, light=brake)
    # raised silver divider between the inboard chamber and the outboard section
    rings = []
    for k in range(25):
        z = zb + 0.008 + (zt - zb - 0.016) * k / 24
        sec = [(c_div0, 0.044), (c_div0 + 0.002, 0.020), (c_div0 + 0.005, 0.0125), (0.097, 0.0100),
               (c_div1 - 0.005, 0.0125), (c_div1 - 0.002, 0.020), (c_div1, 0.044)]
        rings.append([bs_lift(_c2u(c, z), z, d) for c, d in sec])
    m.loft(rings, "alu", b)
    # outboard section: smoked red lens back, wrapping the corner onto the side
    ob = []
    zs = [zb + 0.006 + (zt - zb - 0.012) * k / 20 for k in range(21)]
    ob += [(c_div1 - 0.002, z) for z in zs]
    ob += [(_front_c(z, gap + 0.004), z) for z in reversed(zs)]
    ob = CZ(ob)
    panel(m, ob, L(0.040), "red", b, out=bs_out, spacing=0.016)
    for k in range(5):                                   # faint optic steps behind the smoked lens
        z = zb + 0.060 + (zt - 0.160 - zb - 0.060) * k / 4
        cs = [c_div1 + 0.004 + (_front_c(z, gap + 0.008) - c_div1 - 0.004) * j / 6 for j in range(7)]
        _tube(m, [bs_lift(_c2u(c, z), z, 0.0392) for c in cs], 0.0016, "gloss_black", b, seg=5)
    # upper stop/turn chamber: black-walled box with a horizontal LED bar and two LED dots
    cz0, cz1 = zt - 0.108, zt - 0.016
    cf0, cf1 = _front_c(cz0, 0.016), _front_c(cz1, 0.016)
    ch = CZ(_fillet([(0.113, cz0), (cf0, cz0), (cf1, cz1), (0.113, cz1)], [0.008, 0.014, 0.014, 0.008], seg=4))
    panel(m, ch, L(0.016), "black", b, out=bs_out, spacing=0.03, holes=[CZ(_fillet(
        [(0.118, cz0 + 0.006), (cf0 - 0.005, cz0 + 0.006), (cf1 - 0.005, cz1 - 0.006), (0.118, cz1 - 0.006)],
        [0.005, 0.010, 0.010, 0.005], seg=4))])
    chi = CZ(_fillet([(0.118, cz0 + 0.006), (cf0 - 0.005, cz0 + 0.006), (cf1 - 0.005, cz1 - 0.006),
                      (0.118, cz1 - 0.006)], [0.005, 0.010, 0.010, 0.005], seg=4))
    edge_strip(m, chi, L(0.016), bs_in, 0.014, "black", b, ins(chi), 0.012, flip=True)
    panel(m, chi, L(0.030), "light_red", b, out=bs_out, spacing=0.014, light=ind)
    zbar = cz0 + 0.030
    bar = _fillet([(0.124, zbar - 0.008), (cf0 - 0.012, zbar - 0.008), (cf0 - 0.012, zbar + 0.008),
                   (0.124, zbar + 0.008)], 0.006, seg=3)
    panel(m, CZ(bar), L(0.022), "light_red", b, out=bs_out, spacing=0.01, light=brake)
    edge_strip(m, CZ(bar), L(0.022), bs_in, 0.008, "light_red", b, ins(CZ(bar)), 0.01, light=brake)
    for c in (0.135, 0.162):
        z = cz1 - 0.026
        p = bs_lift(_c2u(c, z), z, 0.027)
        nrm = -bs_in(_c2u(c, z), z)
        m.cylinder(p, p + nrm * 0.006, 0.0075, "light_red", b, seg=14, light=brake)
    # outer light pipe: down the lamp's front (side) edge from the chamber and round into the bottom
    pz = [cz0 - 0.010 - (cz0 - 0.010 - (zb + 0.050)) * k / 14 for k in range(15)]
    path = [(_front_c(z, 0.012), z) for z in pz]
    cb = _front_c(zb + 0.03, 0.012)
    path += [(cb - 0.012, zb + 0.032), (cb - 0.030, zb + 0.026), (c_div1 + 0.012, zb + 0.026)]
    _tube(m, [bs_lift(_c2u(c, z), z, 0.022) for c, z in path], 0.0042, "light_red", b, seg=8, light=tail)


def taillamps(mb):
    taillamp(mb, 4, 10, 8, 13)
    with mb.mirrored():
        taillamp(mb, 3, 9, 7, 12)


# ---------------------------------------------------------------------------------------------- tailgate

def z_ledge(x):
    """Step line under SIERRA: straight across, dipping slightly towards the gate ends."""
    return Z_LEDGE - 0.016 * smoothstep(0.60, 0.80, abs(x))


def z_band(x):
    """Lower edge of the top facet of the gate (the 'spoiler' band), dipping around the handle module."""
    return TG_TOP - 0.058 - 0.046 * smoothstep(0.240, 0.168, abs(x))


def tg_y(x, zg):
    """Tailgate outer surface (y; smaller = further rearward)."""
    ax = abs(x)
    y = Y_T - 0.004 - 0.011 * (1 - (x / TG_W) ** 2)
    y -= 0.0035 * math.sin(math.pi * max(0.0, min(1.0, (zg - TG_BOT) / (TG_TOP - TG_BOT))))   # soft vertical crown
    zl = z_ledge(x)
    bulge = 0.0050 + 0.0030 * smoothstep(0.62, 0.30, ax)
    y -= bulge * smoothstep(zl + 0.0020, zl - 0.0050, zg)
    zb = z_band(x)
    if zg > zb:
        y += (zg - zb) * 0.30
    y += 0.028 * smoothstep(TG_BOT + 0.04, TG_BOT, zg) ** 2
    y += 0.006 * smoothstep(TG_W - 0.035, TG_W, ax) ** 2
    return y


def ig_y(x, zg):
    """Inner gate surface: shares the outer-gate surface."""
    return tg_y(x, zg)


def ig_path(w, zb, r):
    """Inner-gate cut line from the top right, down, across the bottom, up to the top left."""
    return _fillet([(w, TG_TOP + 0.03), (w, zb), (-w, zb), (-w, TG_TOP + 0.03)], [0, r, r, 0], seg=8,
                   closed=False)


def _letters(h=0.093, t=0.0215):
    """GMC emblem letters (strokes ~22 mm like the real emblem), centred on x = 0, z from 0 to h."""
    wg, wm, wc, gap = 0.156, 0.170, 0.146, 0.024
    G_ = [(0, 0), (wg, 0), (wg, h * 0.56), (wg * 0.46, h * 0.56), (wg * 0.46, h * 0.56 - t * 0.9),
          (wg - t, h * 0.56 - t * 0.9), (wg - t, t), (t, t), (t, h - t), (wg, h - t), (wg, h), (0, h)]
    Gr = [0.02, 0.012, 0, 0, 0, 0, 0.004, 0.006, 0.006, 0, 0, 0.02]
    M_ = [(0, 0), (t, 0), (t, h - t * 1.7), (wm / 2, h * 0.30), (wm - t, h - t * 1.7), (wm - t, 0), (wm, 0), (wm, h),
          (wm - t * 1.15, h), (wm / 2, h * 0.30 + t * 1.35), (t * 1.15, h), (0, h)]
    Mr = [0.004, 0.004, 0.003, 0.004, 0.003, 0.004, 0.004, 0.006, 0.003, 0.003, 0.003, 0.006]
    C_ = [(0, 0), (wc, 0), (wc, t), (t, t), (t, h - t), (wc, h - t), (wc, h), (0, h)]
    Cr = [0.02, 0, 0, 0.006, 0.006, 0, 0, 0.02]
    total = wg + wm + wc + 2 * gap
    x0 = -total / 2
    out = []
    for poly, rad, w in ((G_, Gr, wg), (M_, Mr, wm), (C_, Cr, wc)):
        out.append([(x0 + x, z) for x, z in _fillet(poly, rad, seg=4)])
        x0 += w + gap
    return out


def _offset_in(P, d):
    """Inward offset of a CCW polygon (mitred, clamped)."""
    n = len(P)
    out = []
    for i in range(n):
        a, b, c = Vector(P[i - 1]), Vector(P[i]), Vector(P[(i + 1) % n])
        e1, e2 = (b - a), (c - b)
        if e1.length < 1e-9 or e2.length < 1e-9:
            out.append(tuple(b))
            continue
        e1.normalize()
        e2.normalize()
        n1, n2 = Vector((-e1.y, e1.x)), Vector((-e2.y, e2.x))
        mm = n1 + n2
        mm = n1 if mm.length < 1e-6 else mm.normalized()
        k = d / max(0.35, mm.dot(n1))
        out.append(tuple(b + mm * k))
    return out


def gmc_emblem(mb, zc, bone):
    """Raised GMC letters: chrome bodies with inset red faces."""
    h = 0.093
    for poly in _letters(h):
        P = [(x, zc - h / 2 + z) for x, z in poly]
        Q1 = _offset_in(P, 0.0016)
        Q = _offset_in(P, 0.0040)
        rings = [[(x, ig_y(x, z) + 0.002, G(z)) for x, z in P], [(x, ig_y(x, z) - 0.0070, G(z)) for x, z in P],
                 [(x, ig_y(x, z) - 0.0090, G(z)) for x, z in Q1], [(x, ig_y(x, z) - 0.0092, G(z)) for x, z in Q],
                 [(x, ig_y(x, z) - 0.0080, G(z)) for x, z in Q]]
        mb.loft(rings, "chrome", bone, cap0=False, cap1=False)
        _flat(mb, [(x, ig_y(x, z) - 0.0081, G(z)) for x, z in Q], (0, -1, 0), "red", bone)


def _badge_solid(mb, loops, zc_off, surf_y, th, mat_side, mat_face, bone, face_inset=0.0):
    """Raised badge part: 2D loops (outer CCW first, then holes) in (x, z), extruded rearwards from the surface."""
    for lp in loops:
        rings = [[(x, surf_y(x, z) + 0.0015, G(z)) for x, z in lp], [(x, surf_y(x, z) - th, G(z)) for x, z in lp]]
        mb.loft(rings, mat_side, bone, cap0=False, cap1=False)
    pts = [[Vector((x, surf_y(x, z) - th - 0.0002, G(z))) for x, z in lp] for lp in loops]
    tris = tessellate_polygon([[Vector((x, z, 0)) for x, z in lp] for lp in loops])
    allp = [p for lp in pts for p in lp]
    for t in tris:
        a, b, c = (allp[i] for i in t)
        ids = [mb._vert(p, bone) for p in (a, b, c)]
        if (b - a).cross(c - a).dot(Vector((0, -1, 0))) < 0:
            ids.reverse()
        mb.face(ids, mat_face, None, fixed=True)


def _at4x_loops(h=0.040, t=0.0085, slant=0.20):
    """AT4X emblem letterforms (blocky italic, red 4), as lists of loops per glyph: (loops, red?)."""
    out = []
    x0 = 0.0
    wA, wT, w4, wX, gp = 0.050, 0.046, 0.046, 0.054, 0.010
    A = [[(0, 0), (t, 0), (t, h * 0.36), (wA - t, h * 0.36), (wA - t, 0), (wA, 0), (wA, h * 0.80), (wA - h * 0.20, h),
          (0, h)],
         [(t, h * 0.36 + t), (t, h - t), (wA - h * 0.20 - t * 0.4, h - t), (wA - t, h * 0.80 - t * 0.2),
          (wA - t, h * 0.36 + t)]]
    T = [[(wT / 2 - t / 2, 0), (wT / 2 + t / 2, 0), (wT / 2 + t / 2, h - t), (wT, h - t), (wT, h), (0, h),
          (0, h - t), (wT / 2 - t / 2, h - t)]]
    a4 = w4 * 0.62
    F = [[(a4, 0), (a4 + t, 0), (a4 + t, h * 0.30), (w4, h * 0.30), (w4, h * 0.30 + t), (a4 + t, h * 0.30 + t),
          (a4 + t, h), (a4, h), (a4, h * 0.30 + t), (t, h * 0.30 + t), (t, h), (0, h), (0, h * 0.30), (a4, h * 0.30)]]
    c = t * 0.75
    X = [[(0, 0), (c * 1.4, 0), (wX / 2, h / 2 - c * 0.9), (wX - c * 1.4, 0), (wX, 0), (wX / 2 + c * 1.1, h / 2),
          (wX, h), (wX - c * 1.4, h), (wX / 2, h / 2 + c * 0.9), (c * 1.4, h), (0, h), (wX / 2 - c * 1.1, h / 2)]]
    for g, w, red in ((A, wA, False), (T, wT, False), (F, w4, True), (X, wX, False)):
        out.append(([[(x0 + x + z * slant, z) for x, z in lp] for lp in g], red))
        x0 += w + gp
    return out, x0 - gp


def _sierra_loops(h=0.031, t=0.0058):
    """SIERRA wordmark: wide squared letters (rounded outer corners), as lists of loops per glyph."""
    glyphs = []
    wS, wE, wR, wA, gp = 0.064, 0.058, 0.062, 0.070, 0.0215
    m0, m1 = h / 2 - t / 2, h / 2 + t / 2
    S = [_fillet([(0, 0), (wS, 0), (wS, m1), (t, m1), (t, h - t), (wS, h - t), (wS, h), (0, h), (0, m0),
                  (wS - t, m0), (wS - t, t), (0, t)], [0.004, 0.006, 0.006, 0.002, 0.002, 0, 0, 0.006, 0.006, 0.002,
                                                       0.002, 0], seg=3)]
    I = [[(0, 0), (t, 0), (t, h), (0, h)]]
    E = [[(0, 0), (wE, 0), (wE, t), (t, t), (t, m0), (wE * 0.86, m0), (wE * 0.86, m1), (t, m1), (t, h - t), (wE, h - t),
          (wE, h), (0, h)]]
    R_ = [_fillet([(0, 0), (t, 0), (t, m0), (wR * 0.44, m0), (wR - t * 1.35, 0), (wR, 0), (wR * 0.44 + t * 1.35, m0),
                   (wR, m0), (wR, h), (0, h)], [0, 0, 0, 0, 0, 0, 0, 0.002, 0.006, 0], seg=3),
          list(reversed(_fillet([(t, m1), (wR - t, m1), (wR - t, h - t), (t, h - t)], [0, 0, 0.002, 0], seg=2)))]
    k = h - t * 1.7

    def xl(z):
        return t * 1.35 + (wA / 2 - t * 1.35) * z / k

    def xr(z):
        return wA - t * 1.35 - (wA / 2 - t * 1.35) * z / k
    zc0 = h * 0.26
    A = [[(0, 0), (t * 1.35, 0), (xl(zc0), zc0), (xr(zc0), zc0), (wA - t * 1.35, 0), (wA, 0), (wA / 2 + t * 0.75, h),
          (wA / 2 - t * 0.75, h)],
         list(reversed([(xl(zc0 + t), zc0 + t), (xr(zc0 + t), zc0 + t), (wA / 2, k)]))]
    x0 = 0.0
    for g, w in ((S, wS), (I, t), (E, wE), (R_, wR), (R_, wR), (A, wA)):
        glyphs.append([[(x0 + x, z) for x, z in lp] for lp in g])
        x0 += w + gp
    return glyphs, x0 - gp


def sierra_emblem(mb, zc, surf_y, bone):
    glyphs, W = _sierra_loops()
    for loops in glyphs:
        L = [[(-W / 2 + x, zc - 0.0155 + z) for x, z in lp] for lp in loops]
        _badge_solid(mb, L, 0, surf_y, 0.0035, "chrome", "chrome", bone)


def at4x_emblem(mb, xc, zc, surf_y, bone):
    glyphs, W = _at4x_loops()
    for loops, red in glyphs:
        L = [[(xc - W / 2 + x, zc - 0.020 + z) for x, z in lp] for lp in loops]
        # outer loops CCW, holes CW (tessellate_polygon only needs them as separate loops)
        _badge_solid(mb, L, 0, surf_y, 0.0045, "chrome", "red" if red else "chrome", bone)


def tailgate(mb):
    """MultiPro tailgate: outer gate (boot) with the wide inner gate (misc_j) cut into it."""
    sp = 0.020
    g = 0.0022
    ig_out = ig_path(IG_W + g, IG_BOT - g, IG_R + g)
    outer = [(-TG_W, TG_BOT), (TG_W, TG_BOT), (TG_W, TG_TOP), (IG_W + g, TG_TOP)] + ig_out[1:-1] + \
        [(-IG_W - g, TG_TOP), (-TG_W, TG_TOP)]
    outer = _fillet(outer, [0.02, 0.02] + [0] * (len(outer) - 2), seg=4)

    def lift_o(x, z):
        return Vector((x, tg_y(x, z), G(z)))
    xs = [-TG_W + 0.003 + (2 * TG_W - 0.006) * k / 80 for k in range(81)]
    creases = [[(x, z_ledge(x) + dz) for x in xs] for dz in (0.0020, -0.0015, -0.0050)]
    xb = [x for x in xs if abs(x) > IG_W + g + 0.004]
    creases += [[(x, z_band(x)) for x in xb if x > 0], [(x, z_band(x)) for x in xb if x < 0]]
    spanel(mb, outer, lift_o, "paint", "boot", (0, -1, 0), sp, creases=creases,
           roll=dict(r=0.0022, depth=lambda x, z: 0.030 if (abs(x) < IG_W + 0.01 and z > IG_BOT - 0.01) else 0.050,
                     inward=lambda x, z: Vector((0, 1, 0)), seg=3))
    # inner gate
    ig_ol = [(IG_W - g, TG_TOP)] + ig_path(IG_W - g, IG_BOT + g, IG_R - g)[1:-1] + [(-IG_W + g, TG_TOP)]

    def lift_i(x, z):
        return Vector((x, ig_y(x, z), G(z)))
    xi = [-IG_W + g + 0.002 + (2 * IG_W - 2 * g - 0.004) * k / 90 for k in range(91)]
    spanel(mb, ig_ol, lift_i, "paint", "misc_j", (0, -1, 0), sp,
           creases=[[(x, z_band(x)) for x in xi], [(x, z_band(x) - 0.006) for x in xi]],
           roll=dict(r=0.0022, depth=0.030, inward=lambda x, z: Vector((0, 1, 0)), seg=3))
    # top cap (black), spanning the gate: rounded rear lip over the facet
    rings = []
    for k in range(41):
        x = -TG_W - 0.002 + (2 * TG_W + 0.004) * k / 40
        fy = tg_y(max(-TG_W, min(TG_W, x)), TG_TOP)
        rings.append([(x, fy + 0.008, G(TG_TOP - 0.007)), (x, fy - 0.0015, G(TG_TOP + 0.0005)),
                      (x, fy - 0.0035, G(TG_TOP + 0.006)), (x, fy - 0.0030, G(R - 0.004)),
                      (x, fy - 0.0005, G(R + 0.003)), (x, fy + 0.006, G(R + 0.0075)), (x, fy + 0.014, G(R + 0.009)),
                      (x, Y_T + 0.052, G(R + 0.009)), (x, Y_T + 0.064, G(R + 0.004)), (x, Y_T + 0.068, G(R - 0.004)),
                      (x, Y_T + 0.068, G(TG_TOP - 0.010)), (x, fy + 0.02, G(TG_TOP - 0.010))])
    mb.loft(rings, "plastic", "boot")
    # inner skin of the gate (faces the bed) and the lower edge
    mb.box((-TG_W + 0.004, Y_T + 0.060, G(TG_BOT + 0.012)), (TG_W - 0.004, Y_T + 0.068, G(TG_TOP)), "plastic", "boot")
    mb.box((-TG_W + 0.004, Y_T + 0.020, G(TG_BOT + 0.004)), (TG_W - 0.004, Y_T + 0.064, G(TG_BOT + 0.014)),
           "black", "boot")
    # handle / camera module: gloss-black rounded housing in the dipped facet, release button, camera
    hz0, hz1, hw = TG_TOP - 0.092, TG_TOP - 0.010, 0.132
    hzc = (hz0 + hz1) / 2
    yb = ig_y(0, hz0 + 0.004)
    sec = rrect(0, hzc, hw, (hz1 - hz0) / 2, 0.020, 5)
    rings = [[(x, ig_y(x, z) + 0.010, G(z)) for x, z in sec]]
    for k, (sc, dy) in enumerate(((1.0, -0.0005), (0.995, -0.0045), (0.982, -0.0070), (0.962, -0.0080))):
        rings.append([(x * sc, yb + dy - 0.004, G((z - hzc) * (1 - (1 - sc) * 1.6) + hzc)) for x, z in sec])
    mb.loft(rings, "gloss_black", "misc_j")
    yf = yb - 0.012
    mb.rbox((-0.016, yf - 0.002, G(hzc + 0.004)), (0.016, yf + 0.001, G(hzc + 0.022)), 0.004, "black", "misc_j")
    cz = hz0 + 0.020
    mb.cylinder((0, yf + 0.001, G(cz)), (0, yf - 0.003, G(cz)), 0.010, "black", "misc_j", seg=16)
    mb.cylinder((0, yf - 0.003, G(cz)), (0, yf - 0.0035, G(cz)), 0.0065, "glass", "misc_j", seg=16)
    for x in (-0.052, 0.052):
        mb.cylinder((x, yf + 0.001, G(cz + 0.004)), (x, yf - 0.0025, G(cz + 0.004)), 0.0075, "black", "misc_j", seg=14)
        mb.cylinder((x, yf - 0.0025, G(cz + 0.004)), (x, yf - 0.0032, G(cz + 0.004)), 0.0058, "alu", "misc_j",
                    seg=14)
        mb.cylinder((x, yf - 0.0032, G(cz + 0.004)), (x, yf - 0.0036, G(cz + 0.004)), 0.0042, "gloss_black", "misc_j",
                    seg=14)
    # emblems: 3D GMC letters on the inner gate, SIERRA on the band below it, AT4X on the lower right
    gmc_emblem(mb, R - 0.258, "misc_j")
    zs = R - 0.470
    sierra_emblem(mb, zs, tg_y, "boot")
    at4x_emblem(mb, 0.600, R - 0.612, tg_y, "boot")


# ---------------------------------------------------------------------------------------------- rear bumper

XB = bs_x(Y_CAP_F, 0.70) - 0.001      # end caps flush with the bedside ahead of them
Y_PLAN_F = YBR + 0.45                 # the plan path starts ahead of the end caps (the outline trims it)
_FACE = pchip([(BP_BOT + 0.030, 0.013), (BP_BOT + 0.060, 0.005), (BP_BOT + 0.100, 0.0005), (0.690, -0.004),
               (0.745, -0.0025), (BP_TOP - 0.060, 0.004), (BP_TOP - 0.026, 0.011)])


def _bumper_plan():
    yc = YBR + 0.008 + RB
    cx = XB - 0.010 - RB                 # the ends tuck in 10 mm towards the corners
    pts = []
    for k in range(9):
        f = k / 8
        pts.append((-(XB - 0.010 * smoothstep(0, 1, f)), Y_PLAN_F + (yc - Y_PLAN_F) * f))
    for k in range(1, 17):
        a = math.radians(180 + 90 * k / 16)
        pts.append((-cx + RB * math.cos(a), yc + RB * math.sin(a)))
    for k in range(1, 40):
        x = -cx + 2 * cx * k / 40
        pts.append((x, YBR + 0.008 * (x / cx) ** 2))
    for k in range(0, 17):
        a = math.radians(270 + 90 * k / 16)
        pts.append((cx + RB * math.cos(a), yc + RB * math.sin(a)))
    for k in range(1, 9):
        f = k / 8
        pts.append(((XB - 0.010 * smoothstep(0, 1, 1 - f)), yc + (Y_PLAN_F - yc) * f))
    return Path2(pts)


def _bumper_profile():
    """(inward offset d, zg) from under the bumper, round the lower edge, up the face (crown at the sensor line)."""
    pts = [(0.145, BP_BOT + 0.012), (0.105, BP_BOT + 0.005), (0.070, BP_BOT + 0.001), (0.048, BP_BOT),
           (0.034, BP_BOT + 0.002), (0.024, BP_BOT + 0.007), (0.017, BP_BOT + 0.014), (0.014, BP_BOT + 0.022)]
    z0, z1 = BP_BOT + 0.030, BP_TOP - 0.026
    for k in range(21):
        z = z0 + (z1 - z0) * k / 20
        pts.append((_FACE(z), z))
    return Path2(pts)


PLAN = _bumper_plan()
PROF = _bumper_profile()


def _cap_corr():
    """Face offset correction that makes the end caps flush with the bedside along their shut line."""
    zs = [BP_BOT + 0.03 + (BP_TOP - 0.026 - BP_BOT - 0.03) * k / 12 for k in range(13)]
    return pchip([(z, (XB - (bs_x(Y_CAP_F - 0.02, z) - 0.0015)) - _FACE(z)) for z in zs])


_CAP_CORR = _cap_corr()


def cap_corr(py, z):
    """Inward-offset correction on the end caps at plan y / height z (see _cap_corr)."""
    w = smoothstep(YBR + RB + 0.02, YBR + RB + 0.16, py)
    if w <= 0.0:
        return 0.0
    return w * _CAP_CORR(min(max(z, BP_BOT + 0.03), BP_TOP - 0.026)) * smoothstep(BP_BOT + 0.005, BP_BOT + 0.03, z)


def bp_lift(s, v, dd=0.0):
    p, t = PLAN.at(s)
    q, _ = PROF.at(v)
    d = q.x + dd + cap_corr(p.y, q.y)
    return Vector((p.x - t.y * d, p.y + t.x * d, G(q.y)))


def bp_in(s, v):
    h = 1e-3
    es = bp_lift(s + h, v) - bp_lift(s - h, v)
    ev = bp_lift(s, v + h) - bp_lift(s, v - h)
    n = es.cross(ev).normalized()
    p, t = PLAN.at(s)
    c = Vector((p.x - t.y * 0.20, p.y + t.x * 0.20, G(0.71)))
    if n.dot(c - bp_lift(s, v)) < 0:
        n = -n
    return n


def _bp_out(p):
    """Outward direction of the bumper shell at a 3D point (from an interior reference point)."""
    if p.y < YBR + RB + 0.008:
        cx = max(-(XB - RB), min(XB - RB, p.x))
        c = Vector((cx, YBR + 0.20, G(0.71)))
    else:
        c = Vector((math.copysign(XB - 0.20, p.x), p.y, G(0.71)))
    return (p - c).normalized()


def s_x(x):
    """Bumper plan parameter at rear-face x."""
    return PLAN.find(lambda p: p.x - x, PLAN.L * 0.2, PLAN.L * 0.8)


def s_y(y, right):
    """Bumper plan parameter on a side end at y."""
    if right:
        return PLAN.find(lambda p: p.y - y, PLAN.L * 0.8, PLAN.L)
    return PLAN.find(lambda p: p.y - y, 0.0, PLAN.L * 0.2)


def v_z(z):
    """Profile parameter at face height z."""
    return PROF.find(lambda q: q.y - z, PROF.L * 0.25, PROF.L)


def bp_at(s, v, h):
    """Point h above the bumper surface (along its outward normal)."""
    return bp_lift(s, v) - bp_in(s, v) * h


def _ring_path(path, centre, sec, lift3):
    """Rings for a loft along a 2D (s, v) path: sec = [(n, h)] with n measured into the opening (towards centre)."""
    rings = []
    m = len(path)
    for i, (s, v) in enumerate(path):
        a = Vector(path[max(i - 1, 0)])
        b = Vector(path[min(i + 1, m - 1)])
        t = (b - a).normalized()
        nn = Vector((t.y, -t.x))
        if nn.dot(Vector(centre) - Vector((s, v))) < 0:
            nn = -nn
        rings.append([lift3(s + nn.x * n, v + nn.y * n, h) for n, h in sec])
    return rings


def corner_step(mb, sa, sb, vS, b):
    """Corner step: black moulded loop framing the opening in the painted end of the bumper, dark pocket, tread."""
    rr = 0.045
    v0 = v_z(BP_BOT + 0.024)
    path = _fillet([(sa, v0), (sa, vS), (sb, vS), (sb, v0)], [0, rr, rr, 0], seg=10, closed=False)
    path = densify(path, 0.012, closed=False)
    centre = ((sa + sb) / 2, vS * 0.45)
    # frame section: tucks under the painted edge, rounded crown ~9 mm proud, rolls into the pocket wall
    sec = [(-0.004, -0.006), (-0.001, 0.0020), (0.002, 0.0075), (0.007, 0.0115), (0.014, 0.0130), (0.021, 0.0120),
           (0.027, 0.0085), (0.031, 0.0030), (0.033, -0.0040), (0.034, -0.015), (0.035, -0.050), (0.036, -0.105),
           (0.024, -0.105)]
    rings = _ring_path(path, centre, sec, bp_at)
    mid = len(rings) // 2
    sm, vm = path[mid]
    loft_fixed(mb, rings, "gloss_black", b, (mid, 4, -bp_in(sm, vm)))
    # pocket back
    ns, nv = 18, 6
    zb0, zb1 = BP_BOT + 0.010, PROF.at(vS)[0].y + 0.012
    grid = []
    for i in range(ns + 1):
        s = sa - 0.01 + (sb - sa + 0.02) * i / ns
        p, t = PLAN.at(s)
        nx, ny = t.y, -t.x
        row = []
        for j in range(nv + 1):
            z = zb0 + (zb1 - zb0) * j / nv
            d = 0.104 + cap_corr(p.y, z)
            row.append((Vector((p.x - nx * d, p.y - ny * d, G(z))), Vector((nx, ny, 0.0))))
        grid.append(row)
    _grid_faces(mb, grid, "black", b)
    # tread with a rounded nose (the bottom bar of the loop), diamond pads on top
    n = 24
    rings = []
    s0, s1 = sa + 0.012, sb - 0.012
    zt = BP_BOT + 0.040
    for i in range(n + 1):
        s = s0 + (s1 - s0) * i / n
        p, t = PLAN.at(s)
        nx, ny = t.y, -t.x
        sec2 = [(0.105, BP_BOT + 0.004), (0.030, BP_BOT - 0.002), (0.004, BP_BOT + 0.001), (-0.010, BP_BOT + 0.009),
                (-0.015, BP_BOT + 0.021), (-0.012, BP_BOT + 0.033), (-0.003, zt - 0.001), (0.012, zt + 0.001),
                (0.105, zt + 0.002), (0.106, BP_BOT + 0.020)]
        cc = cap_corr(p.y, BP_BOT + 0.03)
        rings.append([(p.x - nx * (d + cc), p.y - ny * (d + cc), G(z)) for d, z in sec2])
    mb.loft(rings, "plastic", b)
    for k in range(9):
        s = s0 + 0.02 + (s1 - s0 - 0.04) * (k + 0.5) / 9
        p, t = PLAN.at(s)
        nx, ny = t.y, -t.x
        for d in (0.032, 0.058, 0.084):
            c = Vector((p.x - nx * d, p.y - ny * d))
            ring = []
            for zz, k2 in ((zt + 0.0005, 1.0), (zt + 0.0040, 0.75)):
                ring.append([(c.x + (t.x * dx - nx * dy) * k2, c.y + (t.y * dx - ny * dy) * k2, G(zz))
                             for dx, dy in ((-0.011, 0.0), (0.0, -0.010), (0.011, 0.0), (0.0, 0.010))])
            mb.loft(ring, "plastic", b)


def rear_bumper(mb):
    """Rear bumper (bumper_r): painted wrap-around shell (crowned face, rolled lower edge, end caps flush with the
    bedside), black ribbed step pad on top dipping into the trapezoid centre recess (plate, connectors), corner-step
    loops in the lower outer corners, sensors, hitch receiver."""
    b = "bumper_r"
    S, V = PLAN.L, PROF.L
    sSL, sFL = s_y(Y_STEP_F, False), s_x(-X_STEP_IN)
    sFR, sSR = s_x(X_STEP_IN), s_y(Y_STEP_F, True)
    vS = v_z(Z_STEP)
    tz0 = v_z(BP_TOP - 0.215)
    s0 = s_x(0.0)
    vs = [V * k / 16 for k in range(17)]
    left_end = [(s_y(cap_front_y(PROF.at(v)[0].y), False), v) for v in reversed(vs)]     # top -> bottom
    right_end = [(s_y(cap_front_y(PROF.at(v)[0].y), True), v) for v in vs]               # bottom -> top
    body = [(sSL, 0.0), (sSL, vS), (sFL, vS), (sFL, 0.0), (sFR, 0.0), (sFR, vS), (sSR, vS), (sSR, 0.0)]
    rad = [0, 0.048, 0.048, 0, 0, 0.048, 0.048, 0]
    top = [(s_x(0.418), V), (s_x(0.292), tz0), (s_x(-0.292), tz0), (s_x(-0.418), V)]
    rad_t = [0.022, 0.05, 0.05, 0.022]
    pts = left_end[-1:] + body + right_end + top + left_end[:-1]
    radii = [0.010] + rad + [0] * (len(right_end) - 1) + [0.018] + rad_t + [0.018] + [0] * (len(left_end) - 2)
    ol = _fillet(pts, radii, seg=8)
    sp = 0.022

    def in_step(s, v):
        return v < vS + 0.03 and (sSL - 0.03 <= s <= sFL + 0.03 or sFR - 0.03 <= s <= sSR + 0.03)

    def in_trap(s, v):
        return tz0 - 0.03 < v and abs(s - s0) < 0.47

    def rmat(s, v):
        if v < 1e-4:
            return None
        return "paint"

    def is_end(s, v):
        return s < sSL - 0.02 or s > sSR + 0.02

    def fmat(s, v):
        if v < 1e-4:
            return None
        if is_end(s, v):
            return "black"
        return "plastic" if (in_trap(s, v) or in_step(s, v)) else "paint"

    def depth(s, v):
        if in_trap(s, v):
            return 0.055
        if is_end(s, v):
            return 0.120
        return 0.022
    spanel(mb, ol, bp_lift, "paint", b, _bp_out, sp,
           roll=dict(r=0.004, depth=depth, inward=bp_in, mat=rmat, fmat=fmat, seg=3))
    # recess back (black) with the licence plate, plate lamps and trailer connectors
    trap = _fillet([(s_x(0.46), V + 0.01), (s_x(0.31), tz0 - 0.015), (s_x(-0.31), tz0 - 0.015),
                    (s_x(-0.46), V + 0.01)], [0, 0.05, 0.05, 0], seg=6)
    panel(mb, trap, lambda s, v: bp_lift(s, v, 0.053), "plastic", b, out=(0, -1, 0), spacing=0.03)
    pz = 0.722
    py = bp_lift(s0, v_z(pz), 0.053).y
    mb.rbox((-0.170, py - 0.006, G(pz - 0.085)), (0.170, py + 0.002, G(pz + 0.085)), 0.012, "black", b, seg=4)
    mb.decal((0, py - 0.0075, G(pz)), (0, -1, 0), (0, 0, 1), 0.305, 0.152, "plate", b)
    for x in (-0.075, 0.075):
        mb.rbox((x - 0.024, py - 0.012, G(BP_TOP - 0.056)), (x + 0.024, py, G(BP_TOP - 0.038)), 0.005, "black", b)
        mb.rbox((x - 0.019, py - 0.0135, G(BP_TOP - 0.053)), (x + 0.019, py - 0.011, G(BP_TOP - 0.041)), 0.004,
                "light_clear", b)
    yl = bp_lift(s_x(-0.245), v_z(0.73), 0.053).y
    mb.rbox((-0.285, yl - 0.035, G(0.698)), (-0.205, yl, G(0.778)), 0.012, "black", b, seg=4)
    mb.rbox((-0.276, yl - 0.041, G(0.744)), (-0.214, yl - 0.033, G(0.772)), 0.006, "gloss_black", b)
    yr = bp_lift(s_x(0.245), v_z(0.73), 0.053).y
    mb.cylinder((0.245, yr, G(0.735)), (0.245, yr - 0.028, G(0.735)), 0.031, "black", b, seg=20)
    mb.cylinder((0.245, yr - 0.028, G(0.735)), (0.245, yr - 0.033, G(0.735)), 0.025, "gloss_black", b, seg=20)
    # black ribbed step pad: wraps the whole top and the corners
    def pad_depth(p):
        side = smoothstep(XB - RB - 0.02, XB - 0.02, abs(p.x)) * smoothstep(YBR + 0.02, YBR + RB, p.y)
        return (Y_T + 0.010 - YBR) - 0.020 * side
    sa_p, sb_p = s_y(cap_front_y(BP_TOP + 0.01) + 0.004, False), s_y(cap_front_y(BP_TOP + 0.01) + 0.004, True)
    n_r = int((sb_p - sa_p) / 0.02)
    rings = []
    nose = [(0.014, BP_TOP - 0.036), (0.004, BP_TOP - 0.035), (-0.004, BP_TOP - 0.031), (-0.008, BP_TOP - 0.024),
            (-0.009, BP_TOP - 0.015), (-0.007, BP_TOP - 0.007), (-0.002, BP_TOP - 0.001), (0.006, BP_TOP + 0.002),
            (0.014, BP_TOP + 0.003)]
    for k in range(n_r + 1):
        s = sa_p + (sb_p - sa_p) * k / n_r
        p, t = PLAN.at(s)
        nx, ny = t.y, -t.x
        D = pad_depth(p)
        sec = nose + [(D, BP_TOP + 0.003), (D + 0.004, BP_TOP - 0.010), (D, BP_TOP - 0.038)]
        cc = cap_corr(p.y, BP_TOP - 0.026)
        rings.append([(p.x - nx * (d + cc), p.y - ny * (d + cc), G(z)) for d, z in sec])
    # rounded ends: quarter-round in plan and section over the last 14 mm
    def end_rings(s, sgn):
        p, t = PLAN.at(s)
        nx, ny = t.y, -t.x
        D = pad_depth(p)
        cc = cap_corr(p.y, BP_TOP - 0.026)
        sec = [(d + cc, z) for d, z in nose + [(D, BP_TOP + 0.003), (D + 0.004, BP_TOP - 0.010), (D, BP_TOP - 0.038)]]
        dmin, dmax = min(d for d, z in sec), max(d for d, z in sec)
        cd, r = (dmin + dmax) / 2, (dmax - dmin) / 2
        out = []
        for th in (18, 36, 54, 70, 82, 89):
            a = math.radians(th)
            k = math.cos(a)
            off = r * math.sin(a) * sgn
            out.append([(p.x - nx * (cd + (d - cd) * k) + t.x * off, p.y - ny * (cd + (d - cd) * k) + t.y * off,
                         G(z - 0.004 * (1 - k))) for d, z in sec])
        return out
    rings = list(reversed(end_rings(sa_p, -1))) + rings + end_rings(sb_p, 1)
    mb.loft(rings, "plastic", b)
    # transverse tread ribs on the pad (rounded tops, chevron ends)
    s = sa_p + 0.03
    while s < sb_p - 0.03:
        p, t = PLAN.at(s)
        nx, ny = t.y, -t.x
        D = pad_depth(p)
        d0, d1 = 0.024, D - 0.020
        sk = 0.20
        ring = []
        cc = cap_corr(p.y, BP_TOP - 0.026)
        for d in (d0, d0 + 0.012, d1 - 0.012, d1):
            c = Vector((p.x - nx * (d + cc) + t.x * sk * (d - d0), p.y - ny * (d + cc) + t.y * sk * (d - d0)))
            hgt = 0.0035 if d in (d0, d1) else 0.0058
            ring.append([(c.x - t.x * 0.0075, c.y - t.y * 0.0075, G(BP_TOP + 0.002)),
                         (c.x + t.x * 0.0075, c.y + t.y * 0.0075, G(BP_TOP + 0.002)),
                         (c.x + t.x * 0.0055, c.y + t.y * 0.0055, G(BP_TOP + 0.002 + hgt)),
                         (c.x - t.x * 0.0055, c.y - t.y * 0.0055, G(BP_TOP + 0.002 + hgt))])
        mb.loft(ring, "plastic", b)
        s += 0.056
    # corner steps
    corner_step(mb, sSL, sFL, vS, b)
    corner_step(mb, sFR, sSR, vS, b)
    # parking sensors (4 across the rear face on the crown line, 1 on each end cap)
    for s, z in ((s_x(-0.705), 0.672), (s_x(-0.360), 0.672), (s_x(0.360), 0.672), (s_x(0.705), 0.672),
                 (s_y(YBR + 0.330, False), 0.790), (s_y(YBR + 0.330, True), 0.790)):
        v = v_z(z)
        p = bp_lift(s, v)
        n = -bp_in(s, v)
        mb.cylinder(p - n * 0.004, p + n * 0.0008, 0.0135, "black", b, seg=18)
        mb.cylinder(p - n * 0.002, p + n * 0.0016, 0.0108, "paint", b, seg=18)
    # backing (no see-through), brackets, hitch receiver
    # inner liner: closes the shell from behind/below along its whole length (no see-through in game)
    grid = []
    for k in range(int(S / 0.03) + 1):
        s = S * k / int(S / 0.03)
        p, t = PLAN.at(s)
        nx, ny = t.y, -t.x
        row = []
        for z in (BP_BOT + 0.008, BP_BOT + 0.06, 0.72, BP_TOP - 0.036):
            d = 0.146 + cap_corr(p.y, z)
            row.append((Vector((p.x - nx * d, p.y - ny * d, G(z))), Vector((-nx, -ny, 0.0))))
        grid.append(row)
    _grid_faces(mb, grid, "black", b, double=True)
    mirror_side(mb, lambda m: m.box((0.43, YBR + 0.17, G(0.50)), (0.54, YBR + 0.36, G(0.70)), "black", b))
    mb.box((-0.50, YBR + 0.30, G(0.48)), (0.50, YBR + 0.38, G(0.56)), "black", b)
    hz = 0.500
    mb.rbox((-0.037, YBR + 0.012, G(hz - 0.037)), (0.037, YBR + 0.34, G(hz + 0.037)), 0.004, "black", b)
    sq = rrect(0, 0, 0.046, 0.046, 0.006, 2)
    mb.loft([[(x, YBR + 0.008, G(hz + z)) for x, z in sq], [(x, YBR + 0.030, G(hz + z)) for x, z in sq]], "black", b)
    sq2 = rrect(0, 0, 0.0255, 0.0255, 0.003, 2)
    mb.loft([[(x, YBR + 0.0075, G(hz + z)) for x, z in sq2], [(x, YBR + 0.060, G(hz + z)) for x, z in sq2]],
            "gloss_black", b)
    mb.cylinder((-0.058, YBR + 0.065, G(hz)), (0.052, YBR + 0.065, G(hz)), 0.0075, "steel", b, seg=12)
    mb.cylinder((-0.058, YBR + 0.065, G(hz)), (-0.064, YBR + 0.065, G(hz)), 0.013, "steel", b, seg=12)
    for x in (-0.075, 0.075):
        _tube(mb, [(x, YBR + 0.09, G(hz - 0.02)), (x * 1.25, YBR + 0.06, G(hz - 0.035)),
                   (x * 1.25, YBR + 0.04, G(hz - 0.02)), (x, YBR + 0.06, G(hz - 0.005))], 0.0065, "black", b, seg=8)


def build_rear(mb):
    build_bedsides(mb)
    taillamps(mb)
    tailgate(mb)
    rear_bumper(mb)
