"""Cab of the AT4X: greenhouse (roof / windshield / pillars / side glass), cab back, doors, mirrors, running boards.

Shapes are measured from the side-profile reference photos (consumer_006 red, plaza_004 blue, dealer photo 02) and
checked against the calibrated front/rear three-quarter photos.

Greenhouse construction
-----------------------
The whole greenhouse is ONE continuous surface triangulated in an "unrolled" 2D domain (u, y):
  * |u| <= xs(y): top skin, a height field z = T(x=u, y) (windshield, A-pillar crowns, header, roof)
  * |u| >  xs(y): side skin, x = S(y, z) with z = zs(y) - (|u| - xs(y)) (side glass, door frames, pillars)
The two meet along the seam (xs(y), zs(y)) where both are inclined at 45 degrees with matching tangent, so the roof
side roll and the A-pillars are smooth (no crease, no dark band). Near the cab back the skin is rolled inwards along
its section normal and the back panel (height field y = f(x, z)) picks up the same 45-degree seam, which gives the
rounded C-pillar / roof-rear corner.
"""
import math

from mathutils import Vector

from at4x_dims import *  # noqa: F401,F403
from geom import rrect
from surf import densify, panel, pchip, point_in_poly, smoothstep
from ext_common import *  # noqa: F401,F403


# ---------------------------------------------------------------------------------------------- stations
# Door / pillar stations measured from the side profiles (wheel-anchored). They differ from the shared at4x_dims
# values (B-pillar 0.31 -> 0.22, C-pillar 0.15 -> 0.10 wide); see the requests in the hand-over notes.
Y_B = 0.220                       # B-pillar shut line
Y_FD_R = Y_B + 0.004              # rear edge of the front door
Y_RD_F = Y_B - 0.004              # front edge of the rear door
Z_DOOR_BOT = 0.585                # door bottom edge (painted rocker below)
Z_BELT = ZG_BELT
Z_CREASE = ZG_CREASE              # body-side character line (shared)

R_CORNER = 0.055                  # C-pillar / roof-rear corner roll ("radius")


def z_gap(y):
    """Door-frame / roof-rail gap line (follows the roof down towards the back)."""
    return 1.905 - 0.006 * smoothstep(-0.2, -0.75, y)


def y_plane(zg):
    """Cab back plane in side view: vertical behind the bed, leaning forward 4 cm towards the roof."""
    return Y_CAB_R + 0.040 * smoothstep(1.46, 1.90, zg)


def y_bseam(zg):
    return y_plane(zg) + R_CORNER / 2


def y_rdr(zg):
    """Rear edge of the rear door (C-pillar shut line); leans forward towards the roof like the cab back."""
    if zg >= Z_BELT:
        return y_plane(zg) + 0.100 + 0.022 * smoothstep(Z_BELT, 1.90, zg)
    return Y_CAB_R + 0.100 - 0.030 * (Z_BELT - zg) / (Z_BELT - Z_DOOR_BOT)


# ---------------------------------------------------------------------------------------------- body side section

def door_x(y, zg):
    """Door / cab-side skin: the shared body-side surface (so the shut lines to the fender and bedside are flush)."""
    return side_x(y, zg)


# ---------------------------------------------------------------------------------------------- greenhouse section
# windshield centreline / roof profile (side silhouette of photo consumer_006, A-pillar 59.7 deg from vertical)
_ZC = pchip([(1.64, 1.384), (1.544, 1.448), (1.40, 1.532), (1.20, 1.648), (1.00, 1.764), (0.86, 1.846),
             (0.76, 1.902), (0.68, 1.937), (0.58, 1.962), (0.45, 1.978), (0.25, 1.988), (0.00, 1.990),
             (-0.30, 1.987), (-0.60, 1.979), (-0.95, 1.966)])
Z_COWL = ZG_BELT - 0.008


def zc(y):
    return _ZC(y)


def _wroof(y):
    """0 on the windshield / A-pillars, 1 on the roof."""
    return smoothstep(0.80, 0.52, y)


def crown(y):
    return 0.012 + 0.018 * _wroof(y)


def seam_z(y):
    return zc(y) - (0.034 + 0.030 * _wroof(y))


def seam_d(y):
    """How far the seam sits inboard of the straight tumblehome."""
    return 0.010 + 0.006 * _wroof(y)


def glass_side(zg):
    """Side glass / door frame surface (tumblehome)."""
    t = (zg - ZG_BELT) / (1.92 - ZG_BELT)
    return 0.962 - 0.105 * t


GS_DZ = -0.105 / (1.92 - ZG_BELT)


def _find_y_foot():
    lo, hi = 1.2, 1.6
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if seam_z(mid) > Z_BELT:
            lo = mid
        else:
            hi = mid
    return lo


Y_FOOT = _find_y_foot()          # where the A-pillar seam reaches the belt
Y_COWL = Y_WS - 0.010            # front edge of the greenhouse skin (meets the cowl panel)
X_COWL = 0.905


class _Station:
    """Cross-section data at one y station."""
    __slots__ = ("zs", "xs", "xr", "k", "cr", "mu", "zr")

    def __init__(self, y):
        yy = min(y, Y_FOOT)
        zs = seam_z(yy)
        xs = glass_side(zs) - seam_d(yy)
        cr = crown(yy)
        z0 = zc(yy) - cr * (xs / 0.85) ** 2
        z0x = -2 * cr * xs / 0.85 ** 2
        d = 2 * (z0 - zs) / (z0x + 1)
        self.k = (z0x + 1) / (2 * d)
        self.xr = xs - d
        self.cr = cr
        e = 2 * seam_d(yy) / (1 + GS_DZ)
        self.mu = (1 + GS_DZ) / (2 * e)
        self.zr = zs - e
        if y > Y_FOOT:                     # in front of the A-pillar foot the outline runs to the cowl corner
            t = (y - Y_FOOT) / (Y_COWL - Y_FOOT)
            xs = xs + (X_COWL - xs) * t
        self.zs, self.xs = zs, xs


_ST = {}


def station(y):
    key = round(y, 6)
    s = _ST.get(key)
    if s is None:
        s = _ST[key] = _Station(y)
    return s


def top_z_raw(x, y):
    s = station(y)
    ax = abs(x)
    return zc(y) - s.cr * (ax / 0.85) ** 2 - s.k * max(0.0, ax - s.xr) ** 2


def top_z(x, y):
    return max(top_z_raw(x, y), Z_COWL)


def side_xs(y, zg):
    """Side skin x (right side) at height zg, including the roll into the seam and the C-pillar bulge at the belt."""
    s = station(y)
    x = glass_side(zg) - s.mu * max(0.0, zg - s.zr) ** 2
    # behind the rear door the C-pillar is one painted panel with the cab side: bulge out to meet it at the belt
    w = smoothstep(y_rdr(zg) - 0.004, y_rdr(zg) - 0.012, y)
    if w > 0:
        x += w * (door_x(y, Z_BELT) - glass_side(Z_BELT)) * (1 - smoothstep(Z_BELT, 1.66, zg)) ** 2
    return x


def _section_pt(u, y):
    """Un-rolled point (no back roll): returns (x, z)."""
    s = station(y)
    au = abs(u)
    if au <= s.xs:
        return u, top_z(u, y)
    z = s.zs - (au - s.xs)
    return math.copysign(side_xs(y, z), u), z


def gh_point(u, y):
    x, z = _section_pt(u, y)
    yb0 = y_bseam(min(z, 1.90)) + R_CORNER
    if y < yb0:
        e = 1e-3
        xa, za = _section_pt(u - e, y)
        xb, zb = _section_pt(u + e, y)
        tx, tz = xb - xa, zb - za
        L = math.hypot(tx, tz) or 1.0
        nx, nz = -tz / L, tx / L
        if abs(u) > station(y).xs:          # pull straight inwards near the belt (meets the cab side panel)
            w = smoothstep(Z_BELT, Z_BELT + 0.12, z)
            nx, nz = math.copysign(1 - w, u) + w * nx, w * nz
            L = math.hypot(nx, nz)
            nx, nz = nx / L, nz / L
        p = (yb0 - y) ** 2 / (2 * R_CORNER)
        x -= nx * p
        z -= nz * p
    return Vector((x, y, G(z)))


def u_of(y, zg, sgn=1):
    """Domain u of a side-view point (y, zg) on the side skin."""
    s = station(y)
    return sgn * (s.xs + s.zs - zg)


def z_of(u, y):
    s = station(y)
    return s.zs - (abs(u) - s.xs)


# ---------------------------------------------------------------------------------------------- 2D helpers

def _round(pts, radii, seg=6):
    """Closed polygon with per-corner fillet radii (quadratic fillets)."""
    n = len(pts)
    out = []
    for i in range(n):
        a, b, c = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        r = radii[i] if isinstance(radii, (list, tuple)) else radii
        d1, d2 = (a - b), (c - b)
        if r <= 0 or d1.length < 1e-9 or d2.length < 1e-9:
            out.append(tuple(b))
            continue
        d1n, d2n = d1.normalized(), d2.normalized()
        ang = math.acos(max(-1.0, min(1.0, d1n.dot(d2n))))
        if ang < 1e-3 or abs(ang - math.pi) < 1e-3:
            out.append(tuple(b))
            continue
        t = min(r / math.tan(ang / 2), d1.length * 0.49, d2.length * 0.49)
        p1, p2 = b + d1n * t, b + d2n * t
        for k in range(seg + 1):
            w = k / seg
            out.append(tuple((1 - w) ** 2 * p1 + 2 * (1 - w) * w * b + w ** 2 * p2))
    return out


def _offset(poly, d, closed=True):
    """Offset a polyline by d along its left normal (counter-clockwise loop: d > 0 moves inwards)."""
    n = len(poly)
    out = []
    for i in range(n):
        if closed:
            a, c = Vector(poly[i - 1]), Vector(poly[(i + 1) % n])
        else:
            a, c = Vector(poly[max(i - 1, 0)]), Vector(poly[min(i + 1, n - 1)])
        t = (c - a)
        if t.length < 1e-12:
            out.append(tuple(poly[i]))
            continue
        t.normalize()
        out.append((poly[i][0] - t.y * d, poly[i][1] + t.x * d))
    return out


def _signed_area(poly):
    return 0.5 * sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))


def _ccw(poly):
    return list(poly) if _signed_area(poly) > 0 else list(reversed(poly))


def _grow(poly, d):
    """Closed polygon grown outwards by d."""
    return _offset(_ccw(poly), -d)


def _pl_dist(p, pl, closed=False):
    best = 1e18
    n = len(pl)
    segs = n if closed else n - 1
    px, py = p
    for i in range(segs):
        ax, ay = pl[i]
        bx, by = pl[(i + 1) % n]
        if (ax - px > 0.15 and bx - px > 0.15) or (px - ax > 0.15 and px - bx > 0.15):
            continue
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
        qx, qy = ax + t * dx - px, ay + t * dy - py
        d = qx * qx + qy * qy
        if d < best:
            best = d
    return math.sqrt(best)


class _Poly:
    """Polygon with a bounding box for fast rejection."""

    def __init__(self, pts):
        self.p = [tuple(q) for q in pts]
        xs = [q[0] for q in self.p]
        ys = [q[1] for q in self.p]
        self.box = (min(xs), min(ys), max(xs), max(ys))

    def __contains__(self, q):
        x0, y0, x1, y1 = self.box
        if not (x0 <= q[0] <= x1 and y0 <= q[1] <= y1):
            return False
        return point_in_poly(q, self.p)

    def near(self, q, d):
        return _pl_dist(q, self.p, closed=True) < d


def _loop(pl, spacing=0.012):
    q = densify(pl, spacing)
    return q + q[:1]


# ---------------------------------------------------------------------------------------------- side features (y, zg)

def _glass_front_y(zg):
    """Front edge of the front door glass along the A-pillar (photo consumer_006)."""
    return 1.098 + (1.606 - zg) * 1.69


_A_N = math.sqrt(1 + 1.69 ** 2)
Y_SAIL = 1.098                    # vertical front edge of the glass below the mirror sail
Z_SAIL = 1.606
Z_FG_TOP, Z_RG_TOP = 1.870, 1.876
Y_FG_R = Y_B + 0.100              # front door glass rear edge (B-pillar applique)
Y_RG_F = Y_B - 0.135              # rear door glass front edge (rear-door applique)


def _y_rg_r():
    return Y_CAB_R + 0.225        # rear door glass rear edge


def _a_line_y(zg, off):
    """Line parallel to the glass front edge, `off` metres further out (perpendicular)."""
    return _glass_front_y(zg) + off * _A_N


def side_features():
    """All side-view outlines of the right-hand greenhouse side (y, zg)."""
    f = {}
    y_ft = _glass_front_y(Z_FG_TOP)
    fw = [(Y_SAIL, 1.452), (Y_FG_R, 1.452), (Y_FG_R, Z_FG_TOP), (y_ft, Z_FG_TOP), (Y_SAIL, Z_SAIL)]
    f["FW"] = _round(fw, [0.012, 0.012, 0.035, 0.05, 0.03], seg=6)
    # black glass run + mirror sail + B-pillar applique of the front door
    zt = Z_FG_TOP + 0.016
    fo_i = [(Y_B, Z_BELT), (Y_B, zt), (_a_line_y(zt, 0.015), zt), (_a_line_y(Z_BELT, 0.015), Z_BELT)]
    f["FOi"] = _round(fo_i, [0, 0.0, 0.06, 0.0], seg=7)
    # door opening (groove centre) of the front door
    off = (Y_FDOOR_F - _glass_front_y(Z_BELT)) / _A_N
    fo = [(Y_B, Z_BELT), (Y_B, z_gap(Y_B)), (_a_line_y(z_gap(0.7), off), z_gap(0.7)), (Y_FDOOR_F, Z_BELT)]
    f["FO"] = _round(fo, [0, 0, 0.10, 0], seg=10)

    y_rgr = _y_rg_r()
    rw = [(Y_RG_F, 1.460), (Y_RG_F, Z_RG_TOP), (y_rgr, Z_RG_TOP), (y_rgr, 1.492), (Y_RG_F - 0.30, 1.476)]
    f["RW"] = _round(rw, [0.010, 0.012, 0.045, 0.14, 0.30], seg=8)
    zt = Z_RG_TOP + 0.015
    ro_i = [(Y_B, Z_BELT), (Y_B, zt), (y_rgr - 0.015, zt), (y_rgr - 0.015, 1.477), (Y_RG_F - 0.30, 1.4612),
            (Y_RG_F + 0.02, Z_BELT)]
    f["ROi"] = _round(ro_i, [0, 0, 0.06, 0.155, 0.30, 0], seg=8)
    zs = [Z_BELT + (z_gap(-0.7) - Z_BELT) * k / 12 for k in range(13)]
    ro = [(Y_B, Z_BELT)] + [(y_rdr(z), z) for z in zs] + [(Y_B, z_gap(Y_B))]
    f["RO"] = _round(ro, [0] * 13 + [0.07, 0], seg=8)
    y_div = y_rgr + 0.042                     # run channel of the drop glass (fixed glass sliver behind it)
    f["DIV"] = [(y_div - 0.007, 1.40), (y_div + 0.007, 1.40), (y_div + 0.007, 1.95), (y_div - 0.007, 1.95)]
    return f


SIDE = side_features()


def _groove_lines():
    """Open polylines of the door shut lines above the belt (y, zg)."""
    fo, ro = SIDE["FO"], SIDE["RO"]
    front = fo[1:]                 # (Y_B, gap) forward and down the A-pillar to the belt
    rear = list(reversed(ro[1:]))  # (Y_B, gap) back and down the C-pillar to the belt
    top_ap = list(reversed(rear)) + front[1:]
    bpil = [(Y_B, Z_BELT), (Y_B, z_gap(Y_B))]
    return [densify(top_ap, 0.02, closed=False), densify(bpil, 0.02, closed=False)]


GROOVES = _groove_lines()
GROOVE_W = 0.0028
GROOVE_D = 0.0035


def _groove_dist(y, zg):
    return min(_pl_dist((y, zg), g) for g in GROOVES)


# ---------------------------------------------------------------------------------------------- windshield (plan)

Y_WS_GLASS_TOP = 0.765


def _ws_outline():
    """Windshield glass outline in plan (x, y) incl. frit; the bottom runs under the cowl."""
    y_bot = Y_COWL + 0.05
    ys = [y_bot - k * (y_bot - Y_WS_GLASS_TOP) / 40 for k in range(41)]
    right = [(station(y).xr - 0.034, y) for y in ys]
    top = [(x, Y_WS_GLASS_TOP - 0.006 * (x / 0.6) ** 2) for x in (0.45, 0.15, -0.15, -0.45)]
    pts = right + top + [(-x, y) for x, y in reversed(right)]
    radii = [0.0] * len(pts)
    radii[len(right) - 1] = 0.11
    radii[len(right) + len(top)] = 0.11
    return _round(pts, radii, seg=10)


WS = _ws_outline()


def _contour(zv, x0, x1, n=40):
    """Plan polyline where the top skin crosses height zv (x from x0 to x1)."""
    pts = []
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        lo, hi = 1.2, Y_COWL
        if top_z_raw(x, hi) > zv:
            pts.append((x, hi))
            continue
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if top_z_raw(x, mid) > zv:
                lo = mid
            else:
                hi = mid
        pts.append((x, lo))
    return pts


def _cowl_line():
    """Where the windshield surface dips under the cowl (plan polyline from -X_COWL to X_COWL)."""
    return _contour(Z_COWL, -X_COWL, X_COWL)


COWL = _cowl_line()
CAP_DZ, CAP_X = 0.040, 0.70            # black cowl-end cap over the A-pillar foot (outboard of CAP_X, below +CAP_DZ)
CAP_LINE = _contour(Z_COWL + CAP_DZ, CAP_X, X_COWL, n=16)


def cap_y(x):
    ax = min(abs(x), X_COWL)
    t = (ax - CAP_X) / (X_COWL - CAP_X) * (len(CAP_LINE) - 1)
    i = max(0, min(int(t), len(CAP_LINE) - 2))
    w = t - i
    return CAP_LINE[i][1] * (1 - w) + CAP_LINE[i + 1][1] * w
FRIT_BOT = 0.045


def cowl_y(x):
    ax = min(abs(x), X_COWL)
    t = (ax + X_COWL) / (2 * X_COWL) * (len(COWL) - 1)
    i = min(int(t), len(COWL) - 2)
    w = t - i
    return COWL[i][1] * (1 - w) + COWL[i + 1][1] * w


# ---------------------------------------------------------------------------------------------- greenhouse skin

def greenhouse(mb):
    f = SIDE
    yb_t = y_bseam(1.90)            # rear edge of the roof skin (domain)
    y0 = y_bseam(Z_BELT)
    right_belt = [(u_of(y, Z_BELT), y) for y in (y0 + (Y_FOOT - y0) * k / 80 for k in range(81))]
    zs_back = station(yb_t).zs
    rear_side = []                  # right side skin rear edge, belt -> seam
    for k in range(15):
        z = Z_BELT + (zs_back - Z_BELT) * k / 14
        y = y_bseam(z)
        rear_side.append((u_of(y, z), y))
    xs_back = station(yb_t).xs
    rear_top = [(-xs_back + 2 * xs_back * k / 30, yb_t) for k in range(1, 30)]
    front = [(station(y).xs, y) for y in (Y_FOOT + (Y_COWL - Y_FOOT) * k / 6 for k in range(1, 6))]
    outline = (right_belt + front + [(X_COWL, Y_COWL), (-X_COWL, Y_COWL)] +
               [(-u, y) for u, y in reversed(front)] + [(-u, y) for u, y in reversed(right_belt)] +
               [(-u, y) for u, y in rear_side[1:]] + rear_top + list(reversed(rear_side))[:-1])

    # ---- creases (domain)
    def to_dom(pl, sgn, closed=True):
        q = densify(pl, 0.022, closed=closed)
        return [(u_of(y, z, sgn), y) for y, z in q if z >= Z_BELT - 1e-6]

    creases, glass_creases = [], []
    for sgn in (1, -1):
        for key in ("FW", "FOi", "FO", "RW", "ROi", "RO"):
            c = to_dom(f[key], sgn)
            creases.append(c + c[:1])
            if key in ("FW", "RW"):
                glass_creases.append(c + c[:1])
        for g in GROOVES:
            for off in (-GROOVE_W, GROOVE_W):
                creases.append(to_dom(_offset(g, off, closed=False), sgn, closed=False))
        for key in ("FW", "RW"):                             # outer edge of the glass inset step
            c = to_dom(_grow(f[key], 0.004), sgn)
            creases.append(c + c[:1])
        d = f["DIV"]
        for yy in (d[0][0], d[1][0]):
            creases.append(to_dom([(yy, 1.47), (yy, 1.87)], sgn, closed=False))
    frit = _offset(_ccw(WS), 0.046)
    ws_creases = [_loop(WS, 0.02), _loop(frit, 0.02), densify(COWL, 0.02, closed=False),
                  densify([(x, y - FRIT_BOT) for x, y in COWL], 0.02, closed=False)]
    creases += ws_creases
    glass_creases += ws_creases
    for sx in (1, -1):
        creases.append(densify([(sx * x, y) for x, y in CAP_LINE], 0.015, closed=False))
        creases.append(densify([(sx * CAP_X, CAP_LINE[0][1]), (sx * CAP_X, Y_COWL)], 0.015, closed=False))

    P = {k: _Poly(f[k]) for k in ("FW", "FOi", "FO", "RW", "ROi", "RO", "DIV")}
    P_ws, P_frit = _Poly(WS), _Poly(frit)

    def side_region(y, z, sgn):
        sd, lr = ("p", "r") if sgn > 0 else ("d", "l")
        q = (y, z)
        if q in P["FW"]:
            return "glass", f"window_{lr}f"
        if q in P["RW"]:
            if q in P["DIV"]:
                return "black", f"door_{sd}side_r"
            return "glass", f"window_{lr}r"
        in_fo = q in P["FO"]
        in_ro = (not in_fo) and q in P["RO"]
        bone = f"door_{sd}side_f" if in_fo else (f"door_{sd}side_r" if in_ro else "chassis")
        if _groove_dist(y, z) < GROOVE_W:
            return "black", bone
        if in_fo:
            return ("gloss_black" if q in P["FOi"] else "paint"), bone
        if in_ro:
            return ("gloss_black" if q in P["ROi"] else "paint"), bone
        return "paint", "chassis"

    def region(u, y):
        s = station(y)
        if abs(u) <= s.xs:
            if top_z_raw(u, y) < Z_COWL:
                return "plastic", "chassis"
            q = (u, y)
            if abs(u) > CAP_X and y > cap_y(u) and q not in P_frit:
                return "plastic", "chassis"
            if q in P_ws:
                if q in P_frit and y < cowl_y(u) - FRIT_BOT:
                    return "glass", "windscreen"
                return "gloss_black", "chassis"
            return "paint", "chassis"
        return side_region(y, z_of(u, y), 1 if u > 0 else -1)

    def in_glass(y, z):
        q = (y, z)
        for k in ("FW", "RW"):
            if q in P[k] or P[k].near(q, 0.0008):
                return True
        return False

    def lift(u, y):
        p = gh_point(u, y)
        s = station(y)
        if abs(u) > s.xs:
            z = z_of(u, y)
            sgn = 1 if u > 0 else -1
            dg = _groove_dist(y, z)
            dx = GROOVE_D * (1 - dg / GROOVE_W) if dg < GROOVE_W else 0.0
            if in_glass(y, z):
                dx += 0.006
            p.x -= sgn * dx
        return p

    def out_fn(p):
        return Vector((p.x, 0.15, max(p.z - G(1.5), 0.05) * 3))

    panel(mb, outline, lift, "paint", "chassis", out=out_fn, spacing=0.03, creases=creases, regions=region)

    # inner faces of the glass (seen from the cabin)
    def inner_region(u, y):
        r = region(u, y)
        return ("glass_in", r[1]) if r and r[0] == "glass" else None

    def inner_lift(u, y):
        p = lift(u, y)
        if abs(u) > station(y).xs:
            p.x -= math.copysign(0.005, u)
        else:
            p.z -= 0.006
        return p
    panel(mb, outline, inner_lift, "glass_in", "chassis", out=lambda p: -out_fn(p), spacing=0.05,
          creases=glass_creases, regions=inner_region)


def _gh_edge(y):
    """Lower outer edge of the greenhouse skin at station y (A-pillar foot / cowl corner): (x, zg)."""
    if y <= Y_FOOT:
        return side_xs(y, Z_BELT), Z_BELT
    s = station(y)
    return s.xs, top_z(s.xs, y)


def headliner(mb):
    """Headliner following the roof underside (replaces the flat interior box, which would cut through the rounded
    roof edges and the windshield header)."""
    y0 = y_bseam(1.90) + R_CORNER + 0.015
    y1 = Y_WS_GLASS_TOP - 0.035
    ys = [y0 + (y1 - y0) * k / 16 for k in range(17)]
    w = lambda y: station(y).xr - 0.02
    outline = [(w(y), y) for y in ys] + [(-w(y), y) for y in reversed(ys)]
    panel(mb, outline, lambda u, y: gh_point(u, y) - Vector((0, 0, 0.022)), "carpet", "chassis", out=(0, 0, -1),
          spacing=0.10)


def cowl_caps(mb):
    """Black cowl-end caps closing the corner between the A-pillar foot, the fender top and the hood rear corner."""
    def cap(m):
        ys = [Y_FDOOR_F + 0.004 + (Y_HOOD_R - Y_FDOOR_F - 0.004) * k / 10 for k in range(11)]
        rings = []
        for y in ys:
            t = (y - Y_FDOOR_F) / (Y_HOOD_R - Y_FDOOR_F)
            zf = 1.432 + (hood_line(Y_HOOD_R) - 0.032 - 1.432) * t        # fender top edge (ext_front outline)
            xf = side_x(y, zf) - 0.050
            xg, zgh = _gh_edge(y)
            xo = max(xf, xg + 0.004)
            rings.append([(0.880, y, G(zf - 0.030)), (xo, y, G(zf - 0.012)), (xo + 0.002, y, G(zf + 0.004)),
                          (0.5 * (xo + xg), y, G(max(zf, zgh) + 0.006)), (xg - 0.010, y, G(zgh + 0.003)),
                          (0.880, y, G(zgh - 0.004))])
        m.loft(rings, "plastic", "chassis")
    mirror_side(mb, cap)


# ---------------------------------------------------------------------------------------------- cab back

def back_outline():
    """Back panel outline (x, zg): lower cab-side seams, greenhouse rear seam over the roof, closing bottom edge."""
    yb_t = y_bseam(1.90)
    low = []
    for k in range(13):
        z = 0.62 + (Z_BELT - 0.62) * k / 12
        y = y_bseam(z)
        low.append((door_x(y, z) - R_CORNER / 2, z))
    zs_back = station(yb_t).zs
    side = []
    for k in range(1, 15):
        z = Z_BELT + (zs_back - Z_BELT) * k / 14
        y = y_bseam(z)
        p = gh_point(u_of(y, z), y)
        side.append((p.x, p.z - GROUND))
    xs_back = station(yb_t).xs
    top = []
    for k in range(1, 30):
        u = xs_back - 2 * xs_back * k / 30
        p = gh_point(u, yb_t)
        top.append((p.x, p.z - GROUND))
    return low + side + top + [(-x, z) for x, z in reversed(side)] + [(-x, z) for x, z in reversed(low)]


BACK_GLASS = _round([(-0.862, 1.542), (0.862, 1.542), (0.782, 1.900), (-0.782, 1.900)], [0.05, 0.05, 0.08, 0.08],
                    seg=6)


def cab_back(mb):
    out = back_outline()

    def lift(x, zg):
        d = _pl_dist((x, zg), out, closed=False)
        y = y_plane(zg) + max(0.0, R_CORNER - d) ** 2 / (2 * R_CORNER)
        return Vector((x, y, G(zg)))
    # back glass (flush, wide black frit), three-panel power slider
    glass = BACK_GLASS
    frit = _offset(_ccw(glass), 0.036)
    sl_in = _round([(-0.200, 1.582), (0.200, 1.582), (0.198, 1.862), (-0.198, 1.862)], 0.02, seg=4)
    sl_out = _grow(sl_in, 0.014)
    P_g, P_f, P_si, P_so = _Poly(glass), _Poly(frit), _Poly(sl_in), _Poly(sl_out)

    def region(x, zg):
        q = (x, zg)
        if q in P_g:
            if q in P_si:
                return "glass", "windscreen_r"
            if q in P_so:
                return "gloss_black", "windscreen_r"
            if q in P_f:
                return "glass", "windscreen_r"
            return "gloss_black", "windscreen_r"
        return "paint", "chassis"
    creases = [_loop(c) for c in (glass, frit, sl_in, sl_out)]
    panel(mb, out, lift, "paint", "chassis", out=(0, -1, 0), spacing=0.035, creases=creases, regions=region)
    panel(mb, glass, lambda x, z: lift(x, z) + Vector((0, 0.006, 0)), "glass_in", "windscreen_r", out=(0, 1, 0),
          spacing=0.06)
    roof_spoiler(mb)


def _roof_zg(x, y):
    return gh_point(x, y).z - GROUND


def roof_spoiler(mb):
    """Rear roof spoiler: the roof kicks up ~2 cm at its rear edge and overhangs the cab back; its black back face
    carries the CHMSL (red, centre), the two cargo lamps and the bed camera."""
    yb0 = y_bseam(1.90) + R_CORNER                # roof starts rolling down into the back here
    shell, face = [], []
    nx = 26
    for k in range(nx + 1):
        x = -0.76 + 1.52 * k / nx
        e = 0.35 + 0.65 * smoothstep(0.76, 0.58, abs(x))
        zf = _roof_zg(x, yb0)
        y_c = y_plane(1.95) - 0.030 * e
        z_c = zf + 0.014 * e
        z_d = zf - 0.060 * e
        z_in = zf - 0.03
        top = [(yb0 + 0.12, _roof_zg(x, yb0 + 0.12) - 0.004), (yb0 + 0.12, _roof_zg(x, yb0 + 0.12) + 0.0005),
               (yb0 + 0.04, _roof_zg(x, yb0 + 0.04) + 0.010 * e), (yb0 - 0.02, zf + 0.020 * e),
               (y_c + 0.012, z_c + 0.004), (y_c, z_c - 0.004), (yb0 - 0.03, z_in)]
        back = [(y_c, z_c - 0.004), (y_c + 0.004, z_d), (y_plane(z_d) + 0.006, z_d - 0.004),
                (y_plane(z_in) + 0.006, z_in), (yb0 - 0.03, z_in)]
        shell.append([(x, y, G(z)) for y, z in top])
        face.append([(x, y, G(z)) for y, z in back])
    mb.loft(shell, "paint", "chassis")
    mb.loft(face, "gloss_black", "chassis")
    # lamps on the black back face (it leans ~5 deg; lamps are thin boxes proud of it)
    zf = _roof_zg(0.0, yb0)
    y_c = y_plane(1.95) - 0.030
    zc = zf - 0.022
    mb.box((-0.19, y_c - 0.006, G(zc - 0.014)), (0.19, y_c + 0.002, G(zc + 0.014)), "light_red", "chassis",
           light=11)
    for sx in (-1, 1):                                  # cargo lamps at the ends of the same lens
        mb.box((sx * 0.20, y_c - 0.005, G(zc - 0.012)), (sx * 0.28, y_c + 0.002, G(zc + 0.012)), "light_clear",
               "chassis")
    mb.cylinder((0.0, y_c + 0.001, G(zc - 0.034)), (0.0, y_c - 0.006, G(zc - 0.034)), 0.007, "black", "chassis",
                seg=10)


# ---------------------------------------------------------------------------------------------- doors (below belt)

HANDLE_Z = 1.285


def _handle_y(which):
    if which == "f":
        return Y_B + 0.205
    return y_rdr(HANDLE_Z) + 0.178


POCKET_A, POCKET_B, POCKET_D = 0.130, 0.042, 0.026      # finger pocket half-length, half-height, depth
POCKET_DZ = -0.010                                    # pocket centre below the handle axis


def _pocket_depth(y, zg, yc):
    """Finger recess behind / under the pull handle."""
    dy, dz = (y - yc) / POCKET_A, (zg - HANDLE_Z - POCKET_DZ) / POCKET_B
    r2 = dy * dy + dz * dz
    if r2 >= 1:
        return 0.0
    return POCKET_D * (1 - r2) ** 1.5


def _pocket_outline(yc, s=1.0):
    return [(yc + POCKET_A * s * math.cos(a), HANDLE_Z + POCKET_DZ + POCKET_B * s * math.sin(a))
            for a in (2 * math.pi * k / 32 for k in range(32))]


def doors(mb):
    def door_panel(m, outline, bone, yc, y_front, y_rear):
        def lift(y, zg):
            return Vector((door_x(y, zg) - _pocket_depth(y, zg, yc), y, G(zg)))
        pk, pk_in = _pocket_outline(yc), _pocket_outline(yc, 0.55)
        cr = [[(y_front - 0.003, Z_CREASE), (y_rear + 0.003, Z_CREASE)], pk + pk[:1], pk_in + pk_in[:1]]
        panel(m, outline, lift, "paint", bone, out=(1, 0, 0), spacing=0.024, creases=cr,
              flange=(0.028, lambda p: IN_X))

    def front(m, s):
        bone = f"door_{s}side_f"
        y0, y1 = Y_FDOOR_F, Y_FD_R
        outline = _round([(y1, Z_DOOR_BOT), (y0, Z_DOOR_BOT), (y0, Z_BELT), (y1, Z_BELT)], [0.025, 0.025, 0, 0],
                         seg=4)
        door_panel(m, outline, bone, _handle_y("f"), y0, y1)
        _belt_moulding(m, y1 + 0.003, y0 - 0.003, bone)
        _handle(m, _handle_y("f"), bone)
        mirror(m, bone)
        m.decal((door_x(1.10, 0.796) + 0.003, 1.10, G(0.796)), (1, 0, 0), (0, 0, 1), 0.31, 0.078, "badge_at4x",
                bone)

    def rear(m, s):
        bone = f"door_{s}side_r"
        zs = [Z_DOOR_BOT + (Z_BELT - Z_DOOR_BOT) * k / 10 for k in range(11)]
        outline = [(Y_RD_F, Z_BELT), (Y_RD_F, Z_DOOR_BOT)] + [(y_rdr(z), z) for z in zs]
        outline = _round(outline, [0, 0.025, 0.025] + [0] * 10, seg=4)
        door_panel(m, outline, bone, _handle_y("r"), Y_RD_F, y_rdr(Z_CREASE))
        _belt_moulding(m, y_rdr(Z_BELT) + 0.003, Y_RD_F - 0.003, bone)
        _handle(m, _handle_y("r"), bone)

    front(mb, "p")
    rear(mb, "p")
    with mb.mirrored():
        front(mb, "d")
        rear(mb, "d")


def _belt_moulding(m, y0, y1, bone):
    """Black belt seal between the door skin top and the glass."""
    rings = []
    for k in range(9):
        y = y0 + (y1 - y0) * k / 8
        xo = door_x(y, Z_BELT)
        xg = glass_side(1.452)
        rings.append([(xo - 0.004, y, G(Z_BELT - 0.006)), (xo - 0.0005, y, G(Z_BELT + 0.001)),
                      (xo - 0.006, y, G(Z_BELT + 0.008)), (xg + 0.002, y, G(1.453)), (xg - 0.006, y, G(1.449)),
                      (xg - 0.006, y, G(Z_BELT - 0.010))])
    m.loft(rings, "gloss_black", bone)


def _handle(m, yc, bone):
    """Body-colour pull handle (GM 2019+ style): a thick bar bridging the pocket, rounded front end, flat rear cap
    carrying the keyless-entry button."""
    z = HANDLE_Z
    L = 0.236
    rings = []
    n = 18
    for k in range(n + 1):
        t = k / n
        y = yc + L / 2 - L * t                  # rear (t=0) -> front (t=1)
        xs = door_x(y, z)
        a = min(1.0, t / 0.06)                  # rear cap: steps out quickly
        b = min(1.0, (1 - t) / 0.16)            # front end: long rounded nose into the door
        prof = math.sin(math.pi / 2 * a) * math.sin(math.pi / 2 * b) ** 0.7
        out = 0.004 + 0.026 * prof
        hh = 0.0150 + 0.0040 * math.sin(math.pi * t) ** 0.5
        hw = 0.012 * (0.6 + 0.4 * prof)
        sec = rrect(0, 0, hw, hh * (0.55 + 0.45 * prof), 0.010, 3)
        rings.append([(xs + out - hw + dx, y, G(z + 0.002 * t + dz)) for dx, dz in sec])
    m.loft(rings, "paint", bone)
    # keyless-entry request button on the rear cap
    y_cap = yc + L / 2 - 0.034
    xs = door_x(y_cap, z)
    m.cylinder((xs + 0.0275, y_cap, G(z + 0.002)), (xs + 0.0302, y_cap, G(z + 0.002)), 0.0042, "black", bone, seg=10)


def cab_side_lower(mb):
    """Painted cab side behind the rear door (C-pillar below the belt), rolling into the cab back."""
    zs = [0.62 + (Z_BELT - 0.62) * k / 12 for k in range(13)]
    gap = 0.004
    outline = [(y_rdr(z) - gap, z) for z in zs] + [(y_bseam(z), z) for z in reversed(zs)]

    def lift(y, zg):
        x = door_x(y, zg)
        yb0 = y_bseam(zg) + R_CORNER
        if y < yb0:
            x -= (yb0 - y) ** 2 / (2 * R_CORNER)
        return Vector((x, y, G(zg)))
    cr = [[(y_rdr(Z_CREASE) - gap, Z_CREASE), (y_bseam(Z_CREASE), Z_CREASE)]]
    mirror_side(mb, lambda m: panel(m, outline, lift, "paint", "chassis", out=(1, 0, 0), spacing=0.022, creases=cr))

    def flange(m):
        rings = [[(door_x(y_rdr(z) - gap, z), y_rdr(z) - gap, G(z)),
                  (door_x(y_rdr(z) - gap, z) - 0.03, y_rdr(z) - gap - 0.004, G(z))] for z in zs]
        m.loft(rings, "paint", "chassis", closed=False)
    mirror_side(mb, flange)


def rocker(mb):
    """Painted rocker under the doors, rolling under to the black pinch-weld cover."""
    def build(m):
        y0, y1 = Y_FDOOR_F + 0.02, Y_CAB_R + 0.02
        rings = []
        for k in range(25):
            y = y0 + (y1 - y0) * k / 24
            xt = door_x(y, Z_DOOR_BOT) - 0.006
            rings.append([(0.80, y, G(Z_DOOR_BOT - 0.004)), (xt, y, G(Z_DOOR_BOT - 0.004)),
                          (xt + 0.004, y, G(0.565)), (xt + 0.002, y, G(0.525)), (xt - 0.012, y, G(0.500)),
                          (xt - 0.040, y, G(0.488)), (0.80, y, G(0.488))])
        m.loft(rings, "paint", "chassis")
        m.box((0.70, y1, G(0.455)), (0.93, y0, G(0.49)), "black", "chassis")
    mirror_side(mb, build)


# ---------------------------------------------------------------------------------------------- mirrors

def _rr4(cy, cz, y0, y1, z0, z1, radii, seg=4):
    """Rounded rectangle in (y, z) with corner radii (y0z0, y1z0, y1z1, y0z1), counter-clockwise."""
    pts = []
    corners = [(y0, z0, 180), (y1, z0, 270), (y1, z1, 0), (y0, z1, 90)]
    for (cyy, czz, start), r in zip(corners, radii):
        oy = cyy + (r if cyy == y0 else -r)
        oz = czz + (r if czz == z0 else -r)
        for k in range(seg + 1):
            a = math.radians(start + 90 * k / seg)
            pts.append((oy + r * math.cos(a), oz + r * math.sin(a)))
    return pts


MIR_X0, MIR_X1 = 1.075, 1.345          # head inboard / outboard ends
MIR_Z0, MIR_Z1 = 1.442, 1.594          # head bottom / top (photos consumer_006 and 02)


def _mir_back(t):
    """y of the mirror-glass face at fraction t of the head width (toe: outboard end further back)."""
    return 1.106 - 0.045 * t


def mirror(mb, bone):
    """2022 Sierra power-folding mirror: black sail mount on the door skin, short neck, deep rectangular head with a
    gloss-black cap rounded over the top-front edge, glass facing back, clear turn-signal strip on the cap face."""
    # ---- sail mount on the door skin below the belt (rounded block, y 1.16..1.325, zg 1.30..1.415)
    yf0, yf1 = 1.160, 1.325
    rings = []
    ny = 10
    for k in range(ny + 1):
        t = k / ny
        y = yf1 - (yf1 - yf0) * t
        e = math.sin(math.pi * t) ** 0.35
        zt = 1.416
        zb = 1.300 + 0.045 * (1 - math.sin(math.pi / 2 * min(1.0, t / 0.5))) if t < 0.5 else 1.300
        xs = door_x(y, 1.36) - 0.003
        bulge = 0.010 + 0.034 * e
        sec = [(xs, zb), (xs + bulge * 0.55, zb + 0.004), (xs + bulge * 0.92, zb + 0.35 * (zt - zb)),
               (xs + bulge, zt - 0.018), (xs + bulge * 0.8, zt - 0.003), (xs + bulge * 0.4, zt), (xs, zt)]
        rings.append([(x, y, G(z)) for x, z in sec])
    mb.loft(rings, "black", bone)
    # ---- neck: from the mount up and out to the head (pivot)
    n0 = [(1.022, 1.300, 1.404), (1.022, 1.190, 1.404), (1.022, 1.190, 1.430), (1.022, 1.300, 1.430)]
    n1 = [(1.110, 1.270, 1.430), (1.110, 1.150, 1.430), (1.110, 1.150, 1.452), (1.110, 1.270, 1.452)]
    mb.loft([[(x, y, G(z)) for x, y, z in n0], [(x, y, G(z)) for x, y, z in n1]], "black", bone)
    # ---- head
    rings = []
    nx = 14
    for k in range(nx + 1):
        t = k / nx
        x = MIR_X0 + (MIR_X1 - MIR_X0) * t
        if t < 0.07:
            end = math.sin(math.pi / 2 * t / 0.07)
        elif t > 0.92:
            end = math.sin(math.pi / 2 * (1 - t) / 0.08)
        else:
            end = 1.0
        yb = _mir_back(t)
        depth = (0.175 - 0.030 * t) * (0.70 + 0.30 * end)
        z0 = MIR_Z0 + 0.004 * t + 0.012 * (1 - end)
        z1 = MIR_Z1 + 0.003 * t - 0.014 * (1 - end)
        sec = _rr4(0, 0, yb, yb + depth, z0, z1, (0.018, 0.034, 0.070, 0.018))
        rings.append([(x, y, G(z)) for y, z in sec])
    mb.loft(rings, "gloss_black", bone)
    # ---- mirror glass in a black bezel on the back face (follows the toe)
    ang = math.atan2(0.045, MIR_X1 - MIR_X0)
    n = Vector((-math.sin(ang), -math.cos(ang), 0))
    xc = 0.5 * (MIR_X0 + MIR_X1) + 0.003
    zc_ = 0.5 * (MIR_Z0 + MIR_Z1) + 0.002
    for w, h, mat, off in ((0.252, 0.134, "black", 0.0012), (0.240, 0.122, "chrome", 0.0024)):
        mb.decal((xc, _mir_back(0.5 + 0.003 / (MIR_X1 - MIR_X0)) - off, G(zc_)), n, (0, 0, 1), w, h, mat, bone)
    # ---- turn-signal lens: vertical strip on the front face of the cap, outboard third
    for xl in (1.258,):
        tl = (xl - MIR_X0) / (MIR_X1 - MIR_X0)
        yl = _mir_back(tl) + 0.175 - 0.030 * tl
        mb.rbox((xl - 0.017, yl - 0.010, G(MIR_Z0 + 0.028)), (xl + 0.017, yl + 0.003, G(MIR_Z1 - 0.040)), 0.008,
                "light_amber", bone, light=6)


# ---------------------------------------------------------------------------------------------- running boards

def running_boards(mb):
    """AT4X assist steps (misc_a): tubular outer frame bent in at both ends, ribbed black step plate, 3 brackets."""
    def board(m):
        yf, yr = 1.340, -1.085
        xo, zt = 1.068, 0.478
        r = 0.026
        bend = 0.10
        path = [(xo - bend - 0.06, yf - 0.002, zt + 0.02)]
        for k in range(7):                           # front bend: from the rocker out to the outer rail
            a = math.pi / 2 * k / 6
            path.append((xo - bend + bend * math.sin(a), yf - bend + bend * math.cos(a), zt + 0.012 * (1 - k / 6)))
        for k in range(1, 12):
            path.append((xo, yf - bend - (yf - yr - 2 * bend) * k / 12, zt))
        for k in range(7):
            a = math.pi / 2 * k / 6
            path.append((xo - bend + bend * math.cos(a), yr + bend - bend * math.sin(a), zt + 0.012 * k / 6))
        path.append((xo - bend - 0.06, yr + 0.002, zt + 0.02))
        m.tube([(x, y, G(z)) for x, y, z in path], r, "black", "misc_a", seg=10)
        # step plate (between rocker and tube) with raised ribs
        y0, y1 = yf - 0.06, yr + 0.06
        m.box((0.925, y1, G(zt - 0.006)), (xo - 0.012, y0, G(zt + 0.016)), "black", "misc_a")
        for k in range(4):
            xc = 0.950 + k * 0.030
            m.box((xc - 0.007, y1 + 0.03, G(zt + 0.016)), (xc + 0.007, y0 - 0.03, G(zt + 0.024)), "plastic",
                  "misc_a")
        m.box((0.915, y1 + 0.05, G(zt - 0.03)), (0.935, y0 - 0.05, G(zt + 0.012)), "black", "misc_a")
        for y in (yf - 0.20, 0.5 * (yf + yr), yr + 0.20):
            m.loft([[(0.55, y - 0.035, G(0.43)), (0.55, y + 0.035, G(0.43)), (0.55, y + 0.035, G(0.49)),
                     (0.55, y - 0.035, G(0.49))],
                    [(0.93, y - 0.03, G(zt - 0.03)), (0.93, y + 0.03, G(zt - 0.03)), (0.93, y + 0.03, G(zt - 0.005)),
                     (0.93, y - 0.03, G(zt - 0.005))]], "black", "misc_a")
    mirror_side(mb, board)


# ---------------------------------------------------------------------------------------------- assembly

def build_cab(mb):
    greenhouse(mb)
    headliner(mb)
    cowl_caps(mb)
    cab_back(mb)
    doors(mb)
    cab_side_lower(mb)
    rocker(mb)
    running_boards(mb)
