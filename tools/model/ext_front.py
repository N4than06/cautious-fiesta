"""Front of the AT4X: front fenders + arch moulding, hood, cowl, fascia, headlamps, grille, front bumper.

Measured on the straight-on photos (front_straight.jpg with its 90 mm-equivalent lens, kelley_002) and on the red
profile photo (consumer_006, camera solved from both wheels and the bumper extremes).

The front corner is one plan-view section per height (`Wrap`): a nearly flat face behind the grille, a bend at the
grille edge, the swept-back headlamp chamfer, a rounded corner at the DRL, and a fillet into the body side. It is
parametrised by w = arc length from the centreline (w ~ x across the face, then round the corner and back along the
side), so the fender, lamp lenses, upper fascia and bumper are panels drawn in (w, zg) that share one surface and
meet at real seams.
"""
import math

from mathutils import Vector

from at4x_dims import *  # noqa: F401,F403
from surf import panel, pchip, smoothstep
from ext_common import *  # noqa: F401,F403
from ext_common import _wheelhouse

# Front wheel opening (dy from the axle, zg), shadowing the shared constant: measured on the profile photo the opening
# is taller (flat top ~1.01 m) and sweeps much further forward before dropping into the bumper.
FRONT_ARCH = [(0.50, 0.74), (0.405, 0.925), (0.22, 1.008), (-0.31, 1.008), (-0.44, 0.88), (-0.44, ZG_BODY)]
FRONT_ARCH_EXT = [(0.53, 0.58)] + FRONT_ARCH

# Headlamp outer lens: needs a clear-glass material; the shared "glass" is the dark window tint and would black the
# lamps out, so the lens is only built once a "lens" material exists (requested), otherwise the internals show.
try:
    import materials as _materials
    LENS = "lens" if "lens" in _materials.SPEC else None
except ImportError:
    LENS = None

# ---- master front-view dimensions (heights above ground / half-widths)
Z_LAMP_T = 1.268    # top of the headlamps at the face
Z_BROW_T = 1.336    # brow top (centre)
Z_BROW_B = 1.236    # brow bottom = grille opening top
Z_GR_B = 0.806      # grille opening bottom (centre)
Z_STEP = 0.728      # upper-fascia overhang above the bumper (centre)
Z_VAL_T = 0.585     # black valance top (centre)
Z_VAL_B = 0.385     # valance bottom
X_GR = 0.668        # grille opening half-width (top)
X_LAMP_IN = 0.674   # headlamp inner edge (front view)

def ftop(y):
    """Fender top / hood side shut line (side view): flat over the lamps, steepest ahead of the arch, easing
    into the cowl (one smooth ramp so the hood surface built on it has no ripples)."""
    t = max(0.0, min(1.0, (2.85 - y) / 1.23))
    return 1.276 + 0.161 * smoothstep(0.0, 1.0, t) ** 1.55


def _nose(y):
    return -0.075 * smoothstep(2.48, Y_FENDER_F + 0.01, y) ** 2


def xs_base(y, zg):
    """Body side near the front: shared side surface without its nose taper (the corner is built by Wrap) and without
    the arch swell (added along the normal by Wrap.lift). The upper fender pulls in towards the lamps and its top
    rolls in under the hood edge."""
    x = side_x(y, zg) - _nose(y)
    x -= 0.045 * smoothstep(1.95, 2.40, y) * smoothstep(0.95, 1.20, zg)
    t = ftop(y)
    x -= 0.050 * smoothstep(t - 0.09, t + 0.002, zg) ** 1.6
    return x


def swell(y, zg):
    return arch_swell(y, zg, FAX, FRONT_ARCH)


def _qfillet(pts, radii, seg=10, clamp=True):
    """Polyline with a quadratic-Bezier fillet at every vertex whose radius > 0. Tangent points are found by arc
    length along the neighbouring polyline, so a vertex between a straight and a sampled curve can be filleted
    (clamp=False lets a fillet run over several short segments)."""
    P = [Vector(p) for p in pts]
    cum = [0.0]
    for a, b in zip(P, P[1:]):
        cum.append(cum[-1] + (b - a).length)

    def at(s):
        s = max(0.0, min(cum[-1], s))
        lo, hi = 0, len(cum) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if cum[mid] <= s:
                lo = mid
            else:
                hi = mid
        t = (s - cum[lo]) / max(cum[hi] - cum[lo], 1e-12)
        return P[lo].lerp(P[hi], t)
    cuts = []
    for i, r in enumerate(radii):
        if r <= 0 or i == 0 or i == len(P) - 1:
            continue
        d1 = (at(cum[i] - 0.005) - P[i]).normalized()
        d2 = (at(cum[i] + 0.005) - P[i]).normalized()
        ang = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        if abs(ang - math.pi) < 1e-3:
            continue
        t = r / math.tan(ang / 2)
        if clamp:
            t = min(t, (0.45 if radii[i - 1] > 0 else 1.0) * (cum[i] - cum[i - 1]),
                    (0.45 if radii[i + 1] > 0 else 1.0) * (cum[i + 1] - cum[i]))
        cuts.append((cum[i] - t, cum[i] + t, i))
    out = []
    s_prev = -1.0
    for s0, s1, i in cuts:
        out += [P[k] for k in range(len(P)) if s_prev < cum[k] < s0]
        p1, p2, b = at(s0), at(s1), P[i]
        out += [(1 - u) ** 2 * p1 + 2 * (1 - u) * u * b + u ** 2 * p2 for u in (k / seg for k in range(seg + 1))]
        s_prev = s1
    out += [P[k] for k in range(len(P)) if cum[k] > s_prev]
    return out


class Wrap:
    """Plan-view section of the front corner as a function of height (see module docstring)."""
    Y3, Y_END = 2.30, 1.95

    def __init__(self, tables, z0, z1, dz=0.005):
        self.t = {k: pchip(v) for k, v in tables.items()}
        self.z0, self.dz = z0, dz
        self.n = int(math.ceil((z1 - z0) / dz)) + 1
        self.rows = {}
        self.ncache = {}

    def _ctrl(self, zg):
        g = lambda k: self.t[k](zg)
        yf = g("yf")
        pts = [(0.0, yf), (0.30, yf - 0.004), (g("x1"), yf - g("dy1")), (g("x2"), g("y2")),
               (xs_base(self.Y3, zg), self.Y3)]
        radii = [0, 0, g("r1"), g("r2"), 0.35]
        y = self.Y3 - 0.02
        while y > self.Y_END - 1e-6:
            pts.append((xs_base(y, zg), y))
            radii.append(0)
            y -= 0.02
        return pts, radii

    def row(self, i):
        i = max(0, min(self.n - 1, i))
        r = self.rows.get(i)
        if r is None:
            zg = self.z0 + i * self.dz
            pts, radii = self._ctrl(zg)
            P = _qfillet(pts, radii, clamp=False)
            dense = [P[0]]
            for a, b in zip(P, P[1:]):
                k = max(1, int((b - a).length / 0.005))
                dense += [a.lerp(b, j / k) for j in range(1, k + 1)]
            W = [0.0]
            for a, b in zip(dense, dense[1:]):
                W.append(W[-1] + (b - a).length)
            xs = [p.x for p in dense]
            top = max(range(len(xs)), key=lambda k: xs[k])
            r = (zg, W, dense, xs[:top + 1], [p.y for p in dense])
            self.rows[i] = r
        return r

    @staticmethod
    def _bs(arr, v, decreasing=False):
        lo, hi = 0, len(arr) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if (arr[mid] <= v) != decreasing:
                lo = mid
            else:
                hi = mid
        return lo

    def _eval_row(self, i, w):
        zg, W, D, _, _ = self.row(i)
        if w >= W[-1]:
            y = D[-1].y - (w - W[-1])
            x = xs_base(y, zg)
            d = (xs_base(y + 0.004, zg) - xs_base(y - 0.004, zg)) / 0.008
            return x, y, Vector((1.0, -d)).normalized()
        k = self._bs(W, w)
        t = (w - W[k]) / max(W[k + 1] - W[k], 1e-12)
        p = D[k].lerp(D[k + 1], t)
        a, b = D[max(k - 1, 0)], D[min(k + 2, len(D) - 1)]
        tg = (b - a).normalized()
        return p.x, p.y, Vector((-tg.y, tg.x))

    def _rows_for(self, zg):
        f = (zg - self.z0) / self.dz
        i = int(math.floor(f))
        return i, f - i

    def point(self, w, zg):
        i, f = self._rows_for(zg)
        x0, y0, n0 = self._eval_row(i, w)
        x1, y1, n1 = self._eval_row(i + 1, w)
        return x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, n0.lerp(n1, f).normalized()

    def lift(self, w, zg, off=0.0, sw=True):
        sgn = -1.0 if w < 0 else 1.0
        x, y, n = self.point(abs(w), zg)
        o = off + (swell(y, zg) if sw else 0.0)
        p = Vector((sgn * (x + o * n.x), y + o * n.y, G(zg)))
        self.ncache[(round(p.x, 4), round(p.y, 4), round(p.z, 4))] = Vector((sgn * n.x, n.y, 0.0))
        return p

    def normal_at(self, p):
        n = self.ncache.get((round(p.x, 4), round(p.y, 4), round(p.z, 4)))
        if n is None:
            n = Vector((math.copysign(max(abs(p.x) - 0.55, 0.0) * 3, p.x), max(p.y - 2.2, 0.05) * 1.5, 0.0))
        return n.normalized()

    def _w_row_y(self, i, y):
        zg, W, D, _, ys = self.row(i)
        if y <= ys[-1]:
            return W[-1] + (ys[-1] - y)
        k = self._bs(ys, y, decreasing=True)
        t = (ys[k] - y) / max(ys[k] - ys[k + 1], 1e-12)
        return W[k] + (W[k + 1] - W[k]) * t

    def w_at_y(self, y, zg):
        i, f = self._rows_for(zg)
        return self._w_row_y(i, y) * (1 - f) + self._w_row_y(i + 1, y) * f

    def _w_row_x(self, i, x):
        zg, W, D, xs, _ = self.row(i)
        k = min(self._bs(xs, x), len(xs) - 2)
        t = (x - xs[k]) / max(xs[k + 1] - xs[k], 1e-12)
        return W[k] + (W[k + 1] - W[k]) * t

    def w_at_x(self, x, zg):
        i, f = self._rows_for(zg)
        return self._w_row_x(i, x) * (1 - f) + self._w_row_x(i + 1, x) * f


# Upper wrap: headlamps, upper fascia (with the corner vents) and the front fender.
UP = Wrap({
    "yf": [(0.50, 2.962), (0.70, 2.962), (0.735, 2.957), (0.80, 2.946), (0.865, 2.939), (0.905, 2.925),
           (1.00, 2.899), (1.10, 2.883), (1.20, 2.870), (1.30, 2.857), (1.50, 2.838)],
    "x1": [(0.50, 0.62), (0.70, 0.62), (0.735, 0.63), (0.80, 0.655), (0.90, 0.665), (1.50, 0.665)],
    "dy1": [(0.50, 0.022), (0.735, 0.022), (0.80, 0.025), (0.88, 0.030), (1.00, 0.048), (1.50, 0.050)],
    "r1": [(0.50, 0.30), (0.70, 0.30), (0.735, 0.28), (0.80, 0.14), (0.90, 0.06), (1.00, 0.05), (1.50, 0.05)],
    "x2": [(0.50, 0.985), (0.70, 0.980), (0.735, 0.970), (0.80, 0.940), (0.90, 0.905), (1.00, 0.884),
           (1.10, 0.876), (1.50, 0.874)],
    "y2": [(0.50, 2.790), (0.70, 2.790), (0.735, 2.786), (0.80, 2.766), (0.90, 2.736), (1.00, 2.714),
           (1.10, 2.706), (1.25, 2.703), (1.50, 2.70)],
    "r2": [(0.50, 0.16), (0.70, 0.16), (0.735, 0.16), (0.80, 0.12), (0.90, 0.08), (1.00, 0.06), (1.50, 0.06)],
}, 0.50, 1.50)

# Bumper wrap (painted bumper and black valance); the face bulges forward at 0.66 m.
_YB = [(0.30, 2.800), (0.36, 2.850), (0.40, 2.878), (0.45, 2.902), (0.50, 2.920), (0.585, 2.940), (0.62, 2.951),
       (0.66, 2.958), (0.695, 2.952), (0.715, 2.940), (0.735, 2.925), (0.80, 2.905)]
BUMP = Wrap({
    "yf": _YB,
    "x1": [(0.3, 0.62), (0.8, 0.62)],
    "dy1": [(0.3, 0.022), (0.8, 0.022)],
    "r1": [(0.3, 0.30), (0.8, 0.30)],
    "x2": [(0.3, 0.955), (0.45, 0.965), (0.6, 0.975), (0.8, 0.975)],
    "y2": [(z, y - 0.19) for z, y in _YB],
    "r2": [(0.3, 0.16), (0.8, 0.16)],
}, 0.28, 0.82)


def wpanel(mb, wrap, outline, mat, bone, off=0.0, spacing=0.02, holes=(), creases=(), flange=None,
           flange_mat=None, light=None, sw=True):
    """Panel drawn in (w, zg) and lifted through a Wrap; flange=depth folds the edges back along -normal."""
    fl = (flange, lambda p: -wrap.normal_at(p)) if flange else None
    return panel(mb, outline, lambda w, zg: wrap.lift(w, zg, off, sw), mat, bone, out=wrap.normal_at,
                 spacing=spacing, holes=holes, creases=creases, flange=fl, flange_mat=flange_mat, light=light)


def wwall(mb, wrap, outline, off0, off1, mat, bone, spacing=0.02):
    """Side wall following a (w, zg) outline between two offsets along the wrap normal (lamp housings)."""
    loop = []
    for a, b in zip(outline, outline[1:] + outline[:1]):
        k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / spacing))
        loop += [(a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k) for j in range(k)]
    rings = [[wrap.lift(w, z, off) for w, z in loop] for off in (off0, off1)]
    mb.loft(rings, mat, bone, cap0=False, cap1=False)


def _smooth(pts, r=0.02, seg=4):
    return [tuple(p) for p in _qfillet([Vector(p) for p in pts] + [Vector(pts[0])], [r] * (len(pts) + 1), seg)][:-1]


def zs_xy(x, y):
    """Height of the upper-fascia overhang ("step") by plan position: level across the face, dipping under the
    corner vent and running down-back to the wheel opening."""
    return Z_STEP + 0.008 * smoothstep(0.45, 0.86, x) - 0.030 * smoothstep(2.82, 2.70, y) - \
        0.043 * smoothstep(2.70, 2.52, y)


def z_step_up(w):
    x, y, _ = UP.point(w, Z_STEP)
    return zs_xy(x, y)


# ---------------------------------------------------------------------------------------------- fender

SEAM_TOP = (2.585, 1.066)      # fender / fascia seam meets the lamp's lower edge
SEAM_BOT = (2.468, 0.925)      # ... and runs down-back under the arch moulding
STEP_END = (2.500, 0.665)      # the step line reaches the wheel opening


def _arch_ext():
    return arch_outline(FAX, FRONT_ARCH_EXT)


def _arch_cut():
    """Index of the opening outline point where the fender/fascia seam leaves it (front diagonal)."""
    arch = _arch_ext()
    cand = [i for i, (y, z) in enumerate(arch) if y > FAX + 0.2]
    return min(cand, key=lambda i: abs(arch[i][1] - 0.875))


def _lamp_side_edge():
    """Lower-rear edge of the headlamp on the side (y, zg): from the top-rear corner sweeping down-forward."""
    return [(2.410, ftop(2.410) - 0.015), (2.428, 1.232), (2.462, 1.182), (2.510, 1.125), (2.560, 1.084),
            SEAM_TOP, (2.612, 1.040)]


def fender_lift(y, zg):
    return UP.lift(UP.w_at_y(y, zg), zg)


def front_fender(mb):
    arch = _arch_ext()
    k = _arch_cut()
    rear_part = list(reversed(arch[k:]))           # rear foot -> over the top -> front diagonal (seam start)
    side = _lamp_side_edge()
    y_tr = side[0][0]
    ys = [Y_FDOOR_F + 0.006 + (y_tr - 0.012 - Y_FDOOR_F - 0.006) * j / 30 for j in range(31)]
    top = [(y, ftop(y)) for y in reversed(ys)]
    outline = [(Y_FDOOR_F + 0.006, ZG_BODY)] + rear_part + [SEAM_BOT, SEAM_TOP] + list(reversed(side[:-2])) + top
    creases = [[(Y_FDOOR_F + 0.01, ZG_CREASE), (2.25, ZG_CREASE)]]
    mirror_side(mb, lambda m: panel(m, outline, fender_lift, "paint", "chassis", out=(1, 0, 0), spacing=0.026,
                                     creases=creases, flange=(0.028, lambda p: Vector((-1, 0, 0)))))
    mirror_side(mb, lambda m: _wheelhouse(m, FAX, FRONT_ARCH_EXT))
    mirror_side(mb, fender_badge)


def fender_badge(m):
    """'6.2L V8' gill on the fender ahead of the door: black housing, badge, ribbed tail."""
    y0, y1, zc = 1.49, 1.79, 1.300
    rings = []
    for j in range(13):
        y = y0 + (y1 - y0) * j / 12
        x = fender_lift(y, zc).x
        h = 0.034 - 0.010 * smoothstep(y0 + 0.20, y1, y)
        rings.append([(x - 0.004, y, G(zc - h)), (x + 0.004, y, G(zc - h)), (x + 0.007, y, G(zc - h + 0.008)),
                      (x + 0.007, y, G(zc + h - 0.008)), (x + 0.004, y, G(zc + h)), (x - 0.004, y, G(zc + h))])
    m.loft(rings, "gloss_black", "chassis")
    yb = y0 + 0.105
    m.decal((fender_lift(yb, zc).x + 0.0085, yb, G(zc + 0.002)), (1, 0, 0), (0, 0, 1), 0.165, 0.042, "badge_v8",
            "chassis")
    for j in range(5):
        z = zc - 0.016 + j * 0.008
        y = y0 + 0.215
        x = fender_lift(y, z).x + 0.0075
        m.box((x, y, G(z)), (x + 0.003, y1 - 0.02, G(z + 0.0035)), "trim", "chassis")


def front_flares(mb):
    mirror_side(mb, lambda m: arch_flare(m, FAX, FRONT_ARCH_EXT, lambda y, z: fender_lift(y, z).x))


# ---------------------------------------------------------------------------------------------- hood

_ZC = pchip([(1.62, 1.468), (1.99, 1.453), (2.30, 1.428), (2.60, 1.397), (2.80, 1.373), (2.90, 1.362)])
_HO = []


def _hood_edge_z(y):
    """Height of the hood's outer edge: on the lamp tops at the front corners, on the fender shut line further back."""
    return Z_LAMP_T + 0.006 + (ftop(y) - Z_LAMP_T - 0.006) * smoothstep(2.66, 2.50, y)


def _hood_half():
    """Hood plan outline (x >= 0): front centre -> leading edge over the brow and lamps -> corner -> side -> rear."""
    if not _HO:
        wa = UP.w_at_y(2.30, ftop(2.30))
        for j in range(61):
            w = wa * j / 60
            inset = 0.004 + 0.024 * (1 - smoothstep(0.36, 0.66, w))
            zt = Z_LAMP_T + 0.004
            for _ in range(3):
                y = UP.point(w, zt)[1]
                zt = _hood_edge_z(y)
            p = UP.lift(w, zt, -inset, sw=False)
            _HO.append((p.x, p.y))
        y = _HO[-1][1]
        while y > Y_HOOD_R + 1e-6:
            y = max(Y_HOOD_R, y - 0.03)
            p = UP.lift(UP.w_at_y(y, ftop(y)), ftop(y), -0.004, sw=False)
            _HO.append((p.x, y))
    return _HO


def _front_edge_y(ax):
    pts = _hood_half()
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= ax <= x1 and x1 > x0:
            return y0 + (y1 - y0) * (ax - x0) / (x1 - x0)
    return pts[-1][1]


def _dome_w(y):
    """Half-width of the raised centre section: wide at the cowl, converging on the ends of the brow notch."""
    return 0.52 - 0.155 * smoothstep(1.62, 2.80, y)


def hood_z(x, y):
    """Hood height: the outer edge on the fender shut line (front corners on the lamp tops), a smooth crown with a
    soft power dome that narrows forward; towards the leading edge the profile flattens across the brow and rolls
    down to the lamp tops at the corners."""
    ax = abs(x)
    e = _hood_edge_z(y) + 0.004
    A = _ZC(y) - e
    u = min(1.0, ax / 0.945)
    wd = _dome_w(y)
    dh = 0.015 + 0.009 * smoothstep(1.8, 2.7, y)
    dome = 1 - smoothstep(wd - 0.032, wd + 0.032, ax)
    p_rear = 1 - u ** 2.3
    p_front = 1 - smoothstep(0.46, 0.80, ax) ** 1.2
    f = smoothstep(2.05, 2.80, y)
    P = p_rear * (1 - f) + p_front * f
    z = e + (A - dh) * max(0.0, P) + dh * dome * max(0.0, P) ** 0.3
    wr = 1 - smoothstep(0.56, 0.72, ax)
    if wr > 0:
        ye = _front_edge_y(ax)
        z -= 0.011 * wr * smoothstep(ye - 0.07, ye, y) ** 2
    return z


def hood(mb):
    half = _hood_half()
    outline = half[::-1] + [(-x, y) for x, y in half[1:]]
    lift = lambda x, y: Vector((x, y, G(hood_z(x, y))))
    ys = [Y_HOOD_R + 0.02 + j * (2.80 - Y_HOOD_R) / 40 for j in range(41)]
    creases = [[(s * (_dome_w(y) + d), y) for y in ys if y < _front_edge_y(_dome_w(y) + d) - 0.02]
               for s in (-1, 1) for d in (-0.032, 0.0, 0.032)]
    panel(mb, outline, lift, "paint", "bonnet", out=(0, 0, 1), spacing=0.021, creases=creases,
          flange=(0.034, lambda p: Vector((0, 0, -1))))
    panel(mb, outline, lambda x, y: Vector((x, y, G(hood_z(x, y) - 0.045))), "black", "bonnet", out=(0, 0, -1),
          spacing=0.12)
    # gloss-black lip in the centre of the leading edge (the "slot" above the brow)
    slot = [(-0.380, 1.326), (0.380, 1.326), (0.350, 1.352), (-0.350, 1.352)]
    panel(mb, slot, lambda x, z: Vector((x, _front_edge_y(abs(x)) + 0.0045, G(z))), "gloss_black", "bonnet",
          out=(0, 1, 0), spacing=0.03, flange=(0.03, lambda p: Vector((0, -1, 0))))


def cowl(mb):
    zr = hood_z(0.85, Y_HOOD_R) - 0.012
    mb.loft([[(x, Y_WS - 0.01, G(ZG_BELT - 0.006)), (x, Y_HOOD_R - 0.006, G(zr)),
              (x, Y_HOOD_R - 0.006, G(zr - 0.05)), (x, Y_WS - 0.01, G(ZG_BELT - 0.06))] for x in (-0.905, 0.905)],
            "plastic", "chassis")
    # wipers parked at the base of the windshield
    for x0 in (-0.74, 0.04):
        mb.box((x0, Y_WS - 0.04, G(ZG_BELT - 0.004)), (x0 + 0.64, Y_WS - 0.022, G(ZG_BELT + 0.006)), "black",
               "chassis")
    # whip antenna (passenger side, at the rear corner of the hood) and roof shark fin
    mb.cylinder((0.86, Y_HOOD_R + 0.03, G(1.425)), (0.86, Y_HOOD_R + 0.09, G(2.25)), 0.004, "black", "chassis",
                seg=6)
    mb.cylinder((0.86, Y_HOOD_R + 0.03, G(1.412)), (0.86, Y_HOOD_R + 0.03, G(1.44)), 0.012, "black", "chassis",
                seg=8)
    shark_fin(mb)


def shark_fin(mb):
    """Roof shark-fin antenna right behind the windshield header, seated on the roof crown (photos consumer_006, 06):
    low rounded nose, rising to ~6 cm, rounded rear face."""
    from ext_cab import _roof_zg     # lazy: the cab module owns the roof surface
    y0, y1 = 0.735, 0.585            # nose / tail
    rings = []
    nr = 14
    for k in range(nr + 1):
        t = k / nr
        y = y0 + (y1 - y0) * t
        # side view: nose rises along a convex curve, tail rolls down steeply; plan: teardrop
        h = 0.064 * math.sin(min(t, 0.999) * math.pi * 0.5) ** 1.15 * (1.0 - smoothstep(0.86, 1.0, t) * 0.72)
        w = 0.034 * math.sin(min(t, 0.999) * math.pi * 0.5) ** 0.7 * (1.0 - smoothstep(0.80, 1.0, t) * 0.45)
        h, w = max(h, 0.004), max(w, 0.004)
        ring = []
        for a in range(13):
            ang = math.pi * a / 12
            x = w * math.cos(ang)
            zb = _roof_zg(x, y) - 0.003
            ring.append((x, y, G(zb + h * math.sin(ang) ** 0.85)))
        for x in (-w * 0.6, 0.0, w * 0.6):
            ring.append((x, y, G(_roof_zg(x, y) - 0.004)))
        rings.append(ring)
    mb.loft(rings, "gloss_black", "chassis")


# ---------------------------------------------------------------------------------------------- headlamps

def _wx(x, zg):
    return UP.w_at_x(x, zg)


def _wy(y, zg):
    return UP.w_at_y(y, zg)


# DRL light pipe centre line in the front view: down the corner, then the long hook in under the projectors
_DRL_V = 0.846
_HOOK = [(_DRL_V, 1.050), (0.838, 1.018), (0.812, 0.985), (0.760, 0.940), (0.712, 0.902)]


def _hook_edges(d):
    """Hook centre line offset by d (positive = outer/lower side), front view."""
    out = []
    for i, (x, z) in enumerate(_HOOK):
        a = Vector(_HOOK[max(i - 1, 0)])
        b = Vector(_HOOK[min(i + 1, len(_HOOK) - 1)])
        t = (b - a).normalized()
        n = Vector((t.y, -t.x))
        if n.x < 0 and n.y > 0:
            n = -n
        out.append((x + n.x * d, z + n.y * d))
    return out


def _lamp_top(y):
    return min(Z_LAMP_T + 0.012 * smoothstep(2.62, 2.45, y), ftop(y) - 0.015)


def _lens_outline():
    """Headlamp lens (w, zg): top edge across and round the corner, the sloping side edge, the DRL hook, then back
    up round the projector box to the grille edge."""
    pts = [(_wx(x, Z_LAMP_T), Z_LAMP_T) for x in (X_LAMP_IN, 0.72, 0.78, 0.83, 0.86)]
    for y in (2.64, 2.60, 2.55, 2.50, 2.45):
        pts.append((_wy(y, _lamp_top(y)), _lamp_top(y)))
    pts += [(_wy(y, z), z) for y, z in _lamp_side_edge()]
    pts += [(_wx(x, z), z) for x, z in _hook_edges(0.014)]
    pts.append((_wx(0.700, 0.893), 0.893))
    pts += [(_wx(x, z), z) for x, z in reversed(_hook_edges(-0.014))]
    pts += [(_wx(x, z), z) for x, z in ((0.829, 1.06), (0.712, 1.06), (0.712, 1.213), (X_LAMP_IN, 1.213))]
    return pts


def headlamps(mb):
    lens = _lens_outline()
    side = _lamp_side_edge()
    edge = pchip([(z, y) for y, z in side[1:]])

    def lamp(m, lid, ind):
        # clear outer lens (only with a clear lens material, see LENS) over a black housing
        if LENS:
            wpanel(m, UP, lens, LENS, "chassis", off=0.0015, spacing=0.02)
        wwall(m, UP, lens, 0.0015, -0.058, "black", "chassis")
        wpanel(m, UP, lens, "black", "chassis", off=-0.058, spacing=0.05)
        # projector box: dark-chrome bezel with two stacked LED modules and a chrome divider
        box = [(_wx(x, z), z) for x, z in ((0.716, 1.064), (0.824, 1.064), (0.824, 1.207), (0.716, 1.207))]
        wpanel(m, UP, _smooth(box, 0.012), "reflector", "chassis", off=-0.016, spacing=0.02, flange=0.03)
        for z0, z1 in ((1.143, 1.198), (1.073, 1.128)):
            mod = [(_wx(x, z), z) for x, z in ((0.726, z0), (0.814, z0), (0.814, z1), (0.726, z1))]
            wpanel(m, UP, _smooth(mod, 0.01), "chrome", "chassis", off=-0.013, spacing=0.02, flange=0.004)
            # LED lens elements inside each module (lit by the headlight)
            for xa, xb in ((0.734, 0.766), (0.774, 0.806)):
                el = [(_wx(x, z), z) for x, z in ((xa, z0 + 0.010), (xb, z0 + 0.010), (xb, z1 - 0.010), (xa, z1 - 0.010))]
                wpanel(m, UP, _smooth(el, 0.008), "light_clear", "chassis", off=-0.010, spacing=0.02, light=lid)
        bar = [(_wx(x, z), z) for x, z in ((0.722, 1.131), (0.806, 1.131), (0.818, 1.137), (0.806, 1.142),
                                           (0.722, 1.142))]
        wpanel(m, UP, bar, "chrome", "chassis", off=-0.007, spacing=0.02)
        # DRL light pipe: top bar along the lamp top, down the corner and the long hook
        drl = [(_wx(x, 1.258), 1.258) for x in (0.680, 0.76, 0.86)] + [(_wx(0.872, 1.25), 1.25)]
        drl += [(_wx(_DRL_V + 0.014, z), z) for z in (1.20, 1.12)]
        drl += [(_wx(x, z), z) for x, z in _hook_edges(0.009)]
        drl += [(_wx(0.706, 0.896), 0.896)]
        drl += [(_wx(x, z), z) for x, z in reversed(_hook_edges(-0.009))]
        drl += [(_wx(_DRL_V - 0.012, z), z) for z in (1.12, 1.215)]
        drl += [(_wx(x, 1.222), 1.222) for x in (0.76, 0.680)]
        wpanel(m, UP, drl, "light_led", "chassis", off=-0.004, spacing=0.012, light=lid)
        # outboard section on the side: amber marker along the top, stacked chrome blades below, small reflector
        y_f = 2.672
        amber = [(_wy(y, _lamp_top(y) - 0.007), _lamp_top(y) - 0.007) for y in (y_f, 2.62, 2.56, 2.50, 2.445)]
        amber += [(_wy(y, _lamp_top(y) - 0.032), _lamp_top(y) - 0.032) for y in (2.458, 2.50, 2.56, 2.62, y_f)]
        wpanel(m, UP, amber, "light_amber", "chassis", off=-0.007, spacing=0.015, light=ind)
        for j, z in enumerate((1.216, 1.186, 1.156, 1.126, 1.096)):
            y_rear = edge(z + 0.007) + 0.012
            y_front = y_f - 0.006 * j
            if y_rear >= y_front - 0.03:
                continue
            blade = [(_wy(y_front, z), z), (_wy(y_rear + 0.008, z), z), (_wy(y_rear, z + 0.014), z + 0.014),
                     (_wy(y_front, z + 0.014), z + 0.014)]
            wpanel(m, UP, blade, "chrome", "chassis", off=-0.012, spacing=0.03, flange=0.028, flange_mat="reflector")
        refl = [(_wy(2.640, 1.050), 1.050), (_wy(2.640, 1.074), 1.074), (_wy(2.606, 1.080), 1.080),
                (_wy(2.616, 1.050), 1.050)]
        wpanel(m, UP, refl, "light_amber", "chassis", off=-0.008, spacing=0.03, light=ind)
    lamp(mb, 2, 6)
    with mb.mirrored():
        lamp(mb, 1, 5)


# ---------------------------------------------------------------------------------------------- upper fascia

def _grille_opening():
    """Grille opening (front view, x >= 0): top centre -> outer side -> chamfered lower corner -> bottom centre."""
    pts = [(0.0, Z_BROW_B), (X_GR, Z_BROW_B), (0.664, 1.10), (0.656, 0.99), (0.640, 0.935), (0.600, 0.885),
           (0.540, 0.835), (0.480, 0.814), (0.25, 0.808), (0.0, Z_GR_B)]
    return [tuple(p) for p in _qfillet(pts, [0, 0.0, 0, 0.03, 0.04, 0.04, 0.03, 0.03, 0, 0], 4)]


def _vent_outline():
    """Air-curtain vent on the fascia corner: tall hexagon, chamfered on the leading corners."""
    wc = UP.w_at_x(0.926, 0.80)
    hw = 0.024
    return [(wc - hw + 0.012, 0.718), (wc + hw, 0.718), (wc + hw, 0.884), (wc - hw + 0.012, 0.884),
            (wc - hw, 0.868), (wc - hw, 0.734)]


def upper_fascia(mb):
    lens = _lens_outline()
    i0 = next(i for i, (w, z) in enumerate(lens) if abs(z - SEAM_TOP[1]) < 1e-9)
    lens_low = lens[i0:]                           # seam -> hook -> round the box -> top-bar bottom at the grille
    grille_side = [(UP.w_at_x(x, z), z) for x, z in _grille_opening() if z < 1.213 and x > 1e-6]
    w_end = UP.w_at_y(*STEP_END)
    step = [(w_end * j / 48, z_step_up(w_end * j / 48)) for j in range(49)]
    arch = _arch_ext()
    k = _arch_cut()
    rear = [(y, z) for y, z in arch[:k + 1] if z > STEP_END[1] + 0.01]
    rear_w = [(UP.w_at_y(y, z), z) for y, z in rear]
    seam = [(UP.w_at_y(*SEAM_BOT), SEAM_BOT[1])]
    half = step + rear_w + seam + lens_low + grille_side + [(0.0, Z_GR_B)]
    full = half + [(-w, z) for w, z in reversed(half[1:-1])]
    vent = _vent_outline()
    vent_m = [(-w, z) for w, z in reversed(vent)]
    # shoulder crease under the lamps: from the grille's lower corner out to the vent
    zc = 0.874
    w0, w1 = UP.w_at_x(0.592, zc), min(w for w, _ in vent) - 0.008
    crease = [(w0 + (w1 - w0) * j / 20, zc - 0.008 * smoothstep(0.5, 1.0, j / 20)) for j in range(21)]
    creases = [crease, [(-w, z) for w, z in crease]]
    wpanel(mb, UP, full, "paint", "chassis", spacing=0.022, holes=[vent, vent_m], flange=0.03, creases=creases)

    def vent_box(m):
        wpanel(m, UP, vent, "black", "chassis", off=-0.045, spacing=0.03)
        wc = sum(w for w, _ in vent) / len(vent)
        for j in range(5):
            z = 0.738 + j * 0.031
            sl = [(wc - 0.020, z), (wc + 0.022, z + 0.012), (wc + 0.022, z + 0.020), (wc - 0.020, z + 0.008)]
            wpanel(m, UP, sl, "gloss_black", "chassis", off=-0.012, spacing=0.03, flange=0.02)
    mirror_side(mb, vent_box)


# ---------------------------------------------------------------------------------------------- grille

def gy(x, zg):
    """Grille face (front of the bars): leans back towards the top, curved slightly in plan."""
    return 2.893 - 0.060 * (zg - 0.95) - 0.012 * (x / X_GR) ** 2


def grille(mb):
    """AT4X grille (misc_c): Titanium brow, six chunky Titanium bars (the third dips under the emblem, the lowest
    rises in the centre), gloss-black blade inserts in the outer bays, vertical posts, GMC emblem, AT4X badge."""
    b = "misc_c"
    op = _grille_opening()
    full = op + [(-x, z) for x, z in reversed(op[1:-1])]
    hole = [(x * 0.975, min(max(z, Z_GR_B + 0.012), Z_BROW_B - 0.010)) for x, z in full]
    panel(mb, full, lambda x, z: Vector((x, gy(x, z) - 0.014, G(z))), "gloss_black", b, out=(0, 1, 0),
          spacing=0.05, holes=[hole], flange=(0.12, lambda p: Vector((0, -1, 0))))
    panel(mb, full, lambda x, z: Vector((x, gy(x, z) - 0.09, G(z))), "black", b, out=(0, 1, 0), spacing=0.1)
    # inner grid: vertical posts and horizontal ties behind the bars
    for j in range(-7, 8):
        x = j * 0.088
        zl = 0.82 if abs(x) < 0.47 else 0.86
        mb.box((x - 0.006, gy(x, 1.0) - 0.085, G(zl)), (x + 0.006, gy(x, 1.0) - 0.035, G(Z_BROW_B - 0.01)),
               "gloss_black", b)
    for zc in (1.168, 1.03, 0.89):
        mb.box((-0.62, gy(0, zc) - 0.085, G(zc - 0.004)), (0.62, gy(0, zc) - 0.045, G(zc + 0.004)), "gloss_black", b)

    def half_w(zg):
        for (x0, z0), (x1, z1) in zip(op, op[1:]):
            if (z0 - zg) * (z1 - zg) <= 0 and z0 != z1:
                return x0 + (x1 - x0) * (zg - z0) / (z1 - z0) - 0.008
        return 0.6

    def bar(zc_fn, x0, x1, h=0.024):
        if x1 > 0.69:
            x1 = half_w(zc_fn(0.7))
        if x0 < -0.69:
            x0 = -half_w(zc_fn(0.7))
        rings = []
        for i in range(37):
            x = x0 + (x1 - x0) * i / 36
            zc = zc_fn(abs(x))
            y = gy(x, zc)
            rings.append([(x, y - 0.058, G(zc - h / 2)), (x, y - 0.002, G(zc - h / 2)), (x, y, G(zc - h / 2 + 0.004)),
                          (x, y, G(zc + h / 2 - 0.008)), (x, y - 0.012, G(zc + h / 2)), (x, y - 0.058, G(zc + h / 2))])
        mb.loft(rings, "titanium", b)

    lim = 0.70
    bar(lambda ax: 1.224, -lim, lim, 0.025)                                         # A under the brow
    bar(lambda ax: 1.120, 0.272, lim, 0.027)                                        # B (outer bays only)
    bar(lambda ax: 1.120, -lim, -0.272, 0.027)
    bar(lambda ax: 1.074 - 0.042 * (1 - smoothstep(0.20, 0.29, ax)), -lim, lim, 0.027)  # C dips under the emblem
    bar(lambda ax: 0.982, -lim, lim, 0.027)                                         # D
    bar(lambda ax: 0.940, -lim, lim, 0.029)                                         # E
    bar(lambda ax: 0.855 + 0.019 * (1 - smoothstep(0.19, 0.265, ax)), -lim, lim, 0.025)  # F rises in the centre
    # rounded outer ends joining the bar pairs round each blade bay (A-B, C-D, E-F)
    for s in (-1, 1):
        for z0, z1 in ((1.108, 1.236), (0.962, 1.086), (0.843, 0.954)):
            rings = []
            for k in range(9):
                a = math.pi * k / 8
                z = (z0 + z1) / 2 + (z1 - z0) / 2 * math.cos(a)
                x = half_w(z) - 0.004 - 0.022 * (1 - math.sin(a)) ** 0.5 * 0 - 0.010 * (1 - math.sin(a))
                y = gy(x, z) - 0.002
                rings.append([(s * (x - 0.024), y - 0.004, G(z)), (s * (x - 0.004), y, G(z)), (s * x, y - 0.012, G(z)),
                              (s * x, y - 0.058, G(z)), (s * (x - 0.024), y - 0.058, G(z))])
            mb.loft(rings, "titanium", b)

    def insert(z0, z1, s):
        x_in = 0.285
        rings = []
        for x in (x_in, x_in + 0.02, 0.45, half_w(z1) - 0.01):
            zt = z1 if x > x_in + 0.01 else z1 - 0.012
            rings.append([(s * x, gy(x, z0) - 0.045, G(z0)), (s * x, gy(x, z0) - 0.010, G(z0)),
                          (s * x, gy(x, zt) - 0.010, G(zt)), (s * x, gy(x, zt) - 0.045, G(zt))])
        mb.loft(rings, "gloss_black", b)
        # fine horizontal ribs across the blade face
        for k in range(1, 4):
            zr = z0 + (z1 - z0) * k / 4 - 0.002
            xs_ = [x_in + 0.03, half_w(zr) - 0.02]
            mb.loft([[(s * x, gy(x, zr) - 0.0105, G(zr)), (s * x, gy(x, zr) - 0.0105, G(zr + 0.004)),
                      (s * x, gy(x, zr) - 0.006, G(zr + 0.004)), (s * x, gy(x, zr) - 0.006, G(zr))] for x in xs_],
                    "black", b)
    for s in (-1, 1):
        for z0, z1 in ((1.142, 1.206), (1.003, 1.058), (0.873, 0.922)):
            insert(z0, z1, s)
    # GMC emblem (red letters, chrome outline), front camera under it, AT4X badge in the lower driver-side bay
    yg = gy(0, 1.125) + 0.016
    mb.rbox((-0.248, yg - 0.03, G(1.068)), (0.248, yg - 0.007, G(1.182)), 0.03, "gloss_black", b, seg=4)
    mb.decal((0, yg, G(1.125)), (0, 1, 0.06), (0, -0.06, 1), 0.48, 0.12, "badge_gmc", b)
    mb.rbox((-0.03, gy(0, 1.045) - 0.03, G(1.034)), (0.03, gy(0, 1.045) + 0.004, G(1.056)), 0.006, "gloss_black", b)
    mb.decal((-0.49, gy(0.49, 0.897) - 0.008, G(0.897)), (0, 1, 0), (0, 0, 1), 0.15, 0.036, "badge_at4x", b)
    brow(mb)


def brow(mb):
    """Titanium brow across the top of the grille, tucked under the hood's leading edge."""
    b = "misc_c"
    top_r = [(0.670, 1.262), (0.60, 1.300), (0.545, 1.318), (0.378, 1.320), (0.345, Z_BROW_T)]
    pts = [(-0.670, Z_BROW_B - 0.004), (0.670, Z_BROW_B - 0.004)] + top_r + [(-x, z) for x, z in reversed(top_r)] + \
        [(-0.670, 1.262)]
    pts = pts[:-1]
    out = [tuple(p) for p in _qfillet(pts, [0, 0, 0, 0.05, 0.05, 0.02, 0.02, 0.02, 0.02, 0.05, 0.05, 0], 5)]
    top_fn = pchip([(0.0, Z_BROW_T)] + [(x, z) for x, z in reversed(top_r)])

    prof = pchip([(0.0, -0.014), (0.12, -0.003), (0.38, 0.0), (0.60, -0.006), (0.78, -0.020), (0.92, -0.044),
                  (1.0, -0.064)])

    def lift(x, z):
        ax = abs(x)
        yf = 2.905 - 0.012 * (ax / X_GR) ** 2 - 0.030 * smoothstep(0.50, 0.67, ax)
        top = top_fn(min(ax, 0.67))
        t = (z - (Z_BROW_B - 0.004)) / (top - Z_BROW_B + 0.004)
        return Vector((x, yf + prof(max(0.0, min(1.0, t))), G(z)))
    panel(mb, out, lift, "titanium", b, out=(0, 1, 0.2), spacing=0.025, flange=(0.06, lambda p: Vector((0, -1, 0))))


# ---------------------------------------------------------------------------------------------- bumper

def _paint_bottom(w):
    """Lower edge of the painted bumper (= top of the black valance): level across the front above the fog lamps,
    a little lower outboard of them, round the corner and back to the wheel opening."""
    x, y, _ = BUMP.point(w, 0.5)
    return Z_VAL_T - 0.040 * smoothstep(0.800, 0.816, x)


def front_bumper(mb):
    """AT4X front bumper (bumper_f): painted upper bumper wrapping to the wheel openings, black textured valance
    with the centre intake, red recovery hooks in vertical pockets, fog lamps outboard, plate, sensors."""
    b = "bumper_f"
    w_end = BUMP.w_at_y(STEP_END[0] + 0.012, 0.62)
    ws = [w_end * j / 56 for j in range(57)]
    top = [(w, zs_xy(*BUMP.point(w, Z_STEP)[:2]) - 0.006) for w in ws]
    bot = [(w, _paint_bottom(w)) for w in ws]
    half = top + bot[::-1]
    full = half + [(-w, z) for w, z in reversed(half[1:-1])]
    fog = [(0.672, 0.488), (0.79, 0.488), (0.79, 0.556), (0.672, 0.556)]
    fog_w = [(BUMP.w_at_x(x, z), z) for x, z in fog]
    fog_m = [(-w, z) for w, z in reversed(fog_w)]
    wpanel(mb, BUMP, full, "paint", b, spacing=0.022, flange=0.03)
    # black textured valance
    low = [(w, Z_VAL_B - 0.025 * smoothstep(0.55, 0.85, w) + 0.10 * smoothstep(w_end - 0.25, w_end, w) ** 1.5)
           for w in ws]
    vhalf = [(w, _paint_bottom(w)) for w in ws] + low[::-1]
    vfull = vhalf + [(-w, z) for w, z in reversed(vhalf[1:-1])]
    intake = [(-0.255, 0.552), (0.255, 0.552), (0.235, 0.462), (-0.235, 0.462)]
    pockets = [_smooth([(s * 0.38 - 0.036, 0.444), (s * 0.38 + 0.036, 0.444), (s * 0.38 + 0.036, 0.558),
                        (s * 0.38 - 0.036, 0.558)], 0.008) for s in (-1, 1)]
    holes = [[(math.copysign(BUMP.w_at_x(abs(x), z), x), z) for x, z in h] for h in [intake] + pockets] + \
        [fog_w, fog_m]
    wpanel(mb, BUMP, vfull, "plastic", b, off=-0.004, spacing=0.03, flange=0.04, holes=holes)
    # raised gloss-black rim outlining the centre section
    rim_o = [(0.0, 0.576), (0.60, 0.576), (0.635, 0.548), (0.635, 0.470), (0.60, 0.432), (0.0, 0.432)]
    rim_i = [(0.0, 0.566), (0.594, 0.566), (0.624, 0.543), (0.624, 0.474), (0.594, 0.442), (0.0, 0.442)]
    conv = lambda pts: [(BUMP.w_at_x(x, z) if x > 0 else 0.0, z) for x, z in pts]
    ro, ri = conv(rim_o), conv(rim_i)
    ring = ro + [(-w, z) for w, z in reversed(ro[1:-1])]
    ring_in = ri + [(-w, z) for w, z in reversed(ri[1:-1])]
    wpanel(mb, BUMP, ring, "gloss_black", b, off=0.002, spacing=0.03, holes=[ring_in], flange=0.008)
    for h in (fog_w, fog_m):     # gloss-black bezel round each fog lamp
        w0, w1 = min(w for w, _ in h) - 0.012, max(w for w, _ in h) + 0.012
        z0, z1 = min(z for _, z in h) - 0.010, max(z for _, z in h) + 0.010
        wpanel(mb, BUMP, [(w0, z0), (w1, z0), (w1, z1), (w0, z1)], "gloss_black", b, off=0.001, spacing=0.03,
               holes=[h], flange=0.006)
    # centre intake: recessed slats
    for j in range(4):
        z = 0.472 + j * 0.022
        hw = 0.235 + 0.02 * (z - 0.462) / 0.09
        y0 = BUMP.point(0, z)[1]
        mb.box((-hw, y0 - 0.05, G(z)), (hw, y0 - 0.012, G(z + 0.008)), "gloss_black", b)
    y5 = BUMP.point(0, 0.5)[1]
    mb.box((-0.26, y5 - 0.075, G(0.455)), (0.26, y5 - 0.065, G(0.56)), "black", b)
    # recovery hooks (red, vertical loops) in their pockets
    for s in (-1, 1):
        x = s * 0.380
        yv = BUMP.point(0.380, 0.5)[1]
        mb.box((x - 0.036, yv - 0.08, G(0.444)), (x + 0.036, yv - 0.07, G(0.558)), "black", b)
        path = [(x, yv - 0.075, G(0.462)), (x, yv - 0.020, G(0.462)), (x, yv + 0.006, G(0.478)),
                (x, yv + 0.012, G(0.500)), (x, yv + 0.006, G(0.522)), (x, yv - 0.020, G(0.538)),
                (x, yv - 0.075, G(0.538))]
        mb.tube(path, 0.014, "red", b, seg=10)

    # fog lamps in gloss-black bezels at the outer corners
    def fogl(m, light):
        wpanel(m, BUMP, fog_w, "gloss_black", b, off=-0.025, spacing=0.03)
        lens = [(BUMP.w_at_x(x, z), z) for x, z in ((0.685, 0.498), (0.777, 0.498), (0.777, 0.546), (0.685, 0.546))]
        wpanel(m, BUMP, _smooth(lens, 0.006), "light_clear", b, off=-0.018, spacing=0.03, light=light)
    fogl(mb, 15)
    with mb.mirrored():
        fogl(mb, 14)
    # licence plate on a black bracket, parking sensors
    yp = BUMP.point(0, 0.648)[1]
    mb.rbox((-0.168, yp - 0.006, G(0.563)), (0.168, yp + 0.004, G(0.733)), 0.01, "black", b)
    mb.decal((0, yp + 0.0055, G(0.648)), (0, 1, 0), (0, 0, 1), 0.305, 0.152, "plate", b)
    for x in (0.335, 0.72):
        for s in (-1, 1):
            p = BUMP.lift(s * BUMP.w_at_x(x, 0.622), 0.622)
            n = BUMP.normal_at(p)
            mb.cylinder(p - n * 0.004, p + n * 0.0025, 0.011, "paint", b, seg=10)
    # skid plate (misc_g) under the valance
    yb0 = BUMP.point(0, Z_VAL_B)[1]
    mb.loft([[(x, yb0 - 0.02, G(Z_VAL_B + 0.012)), (x, yb0 - 0.05, G(Z_VAL_B - 0.012)), (x, 2.30, G(0.355)),
              (x, 2.30, G(0.343)), (x, yb0 - 0.06, G(Z_VAL_B - 0.024)), (x, yb0 - 0.03, G(Z_VAL_B - 0.001))]
             for x in (-0.50, -0.46, 0.46, 0.50)], "black", "misc_g")


def front_backing(mb):
    """Black closing panel behind the grille / lamps / bumper so nothing reads through the gaps."""
    mb.box((-0.83, 2.60, G(0.42)), (0.83, 2.64, G(1.27)), "black", "chassis")


def build_front(mb):
    front_fender(mb)
    front_flares(mb)
    hood(mb)
    cowl(mb)
    headlamps(mb)
    upper_fascia(mb)
    grille(mb)
    front_bumper(mb)
    front_backing(mb)
