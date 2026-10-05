"""Shared dimensions and body-surface functions for the 2022 Sierra 1500 AT4X (crew cab, 5'8" box).

Space: metres, origin at the centre of the truck, +Y forward, +X passenger side, +Z up. Heights are written
above ground ("zg") and converted with G(zg).

Published figures: length 232.9 in (5.916 m), wheelbase 147.5 in (3.747 m), width 81.24 in (2.063 m),
height 78.35 in (1.990 m), ground clearance 11.1 in, approach 25.5 deg, departure 23 deg,
LT275/70R18 tyres (0.842 m). Shapes are matched to dealer photos of an Onyx Black 2022 AT4X (VIN ...567393).
"""
import math

from surf import pchip, smoothstep

GROUND = -0.80
FRONT, REAR = 2.958, -2.958
FAX, RAX = 1.988, -1.759
TRACK = 0.873
TIRE_R = 0.4211
TIRE_W = 0.275
RIM_R = 0.2286
WC = TIRE_R
WZ = GROUND + WC

# side-view stations
# (side-view stations measured from reference photo 02 via a wheel-anchored homography)
Y_FENDER_F = 2.745
Y_HOOD_F, Y_HOOD_R = 2.80, 1.62
Y_WS = 1.585
Y_FDOOR_F, Y_FDOOR_R = 1.460, 0.224
Y_RDOOR_F, Y_RDOOR_R = 0.216, -0.750
Y_CAB_R = -0.850
Y_BED_F, Y_BED_R = -0.875, -2.797
Y_ROOF_F = 0.600         # roof front corner above the side glass (top of the A-pillar)
Y_WS_TOP = 0.880         # windshield top on the centreline (the top edge wraps back to the pillars in plan)
ZG_WS_TOP = 1.930
WS_HW_BASE, WS_HW_TOP = 0.900, 0.720
CAB_SHIFT = 0.30         # interior moved forward with the cab (relative to the first layout)

# heights above ground
ZG_BODY = 0.600          # lower edge of doors / rear of fenders
ZG_CREASE = 1.150        # shoulder crease: crisp line just under the door-handle pockets, headlamp -> taillamp
                         # (consumer_006 profile: reflection edge at 1.15 on both doors and the bedside)
ZG_RIDGE = 0.820         # lower body-side ridge between the wheel openings (AT4X door badge sits under it)
ZG_ROCKER = 0.555        # rocker crease: below it the door skin turns under towards the sill
ZG_BELT = 1.440          # beltline (bottom of side glass)
ZG_RAIL = 1.530          # bed rail (sits above the cab beltline)
ZG_ROOF = 1.990
BED_FLOOR = ZG_RAIL - 0.57   # 22.4 in bed walls
TL_Z0, TL_Z1 = 1.06, ZG_RAIL - 0.005   # taillamp

FLARE_W = 0.070          # black arch moulding width


def G(zg):
    return GROUND + zg


def hood_line(y):
    t = (Y_HOOD_F - y) / (Y_HOOD_F - Y_HOOD_R)
    return 1.305 + 0.140 * max(0.0, min(1.0, t))


def gauss(x, mu, s):
    return math.exp(-((x - mu) / s) ** 2)


# ---------------------------------------------------------------------------------------------- side surface
#
# Body-side section, measured on the light-paint photos (consumer_006 red profile: reflection edges at 1.15 / 0.92 /
# 0.82 / 0.57 m on both doors; consumer_001/002 3/4 views; rear34_sand; kelley_041 white bed view). From the top:
#   belt -> shoulder crease   tumblehome, convex: ~3.5 deg just above the crease rolling to ~10 deg at the belt
#                             (the bright sky band in every photo)
#   shoulder crease (1.15)    crisp, ~8.5 deg change of direction (just under the handles' finger pockets)
#   crease -> valley (0.905)  faces ~5 deg down (the dark band under the crease)
#   valley (0.905)            crisp concave line (drops towards the ridge as the ridge fades over the front door)
#   valley -> lower ridge     facet facing ~10 deg up (the light band above the AT4X badge)
#   lower ridge (0.82)        crisp horizontal ridge
#   ridge -> rocker crease    lower door, undercut ~5 deg (dark in every photo; the AT4X badge sits here)
#   rocker crease (0.555)     the skin turns under to the sill
# The ridge / rocker features only exist between the wheel openings (doors, cab side, bed front, fender behind the
# front arch; low_w); around the openings the side runs straight down under the hollow. The ridge facet narrows
# towards the front of the front door (ridge_w). Profiles are blended so x at the crease and the sill never moves.
#
# The section is a slope profile dx/dz built from smoothed steps (each crease = a slope jump blended over +-w, i.e. a
# small fillet), integrated in closed form so it is exact, C1 and cheap.

X_CREASE = 1.008          # half-width of the side at the shoulder crease (before the plan bow)
CREASE_W = 0.006          # half-width of the crisp crease fillets (shoulder crease, lower ridge, rocker crease)
_SLOPE_UP = -0.060        # dx/dz just above the shoulder crease (leans in ~3.5 deg) ...
_TUMBLE_B = 0.19          # ... rolling in further towards the belt: dx -= b u^2, u = zg - ZG_CREASE (~10 deg at the belt)


def _si(a, b, z):
    """Integral of smoothstep(a, b, t) dt from a to z (0 below a, grows linearly above b)."""
    w = b - a
    s = (z - a) / w
    if s <= 0.0:
        return 0.0
    if s >= 1.0:
        return w * (s - 0.5)
    return w * (s * s * s - 0.5 * s * s * s * s)


# Slope profile dx/dz, from the bottom up, where the full lower-body features exist (between the openings):
#   below the rocker crease        _SLOPE_BOTTOM           (turn-under to the sill)
#   rocker crease -> lower ridge   _UNDERCUT               (lower door faces ~5 deg down; dark in every photo)
#   lower ridge -> valley          _FACET                  (faces ~10 deg up; the light band above the AT4X badge)
#   valley -> shoulder crease      _HOLLOW                 (faces ~5 deg down; the dark band under the crease)
#   above the shoulder crease      _SLOPE_UP - 2 _TUMBLE_B u  (tumblehome)
# The profile is a blend of three slope profiles with the same shoulder crease, so x stays put at the crease and
# at the sill whatever the blend (no waist in plan where the ridge fades):
#   P1  full ridge (doors, cab side, bed front)   ridge/valley; the valley drops towards the ridge as it fades
#       (consumer_006: the light band narrows towards the front of the front door)
#   P0  no ridge (front of the front door, fender behind the arch): one band leaning in under the crease, easing
#       to a near-vertical lower door
#   PN  no lower body (fenders / bedside around the openings): hollow under the crease, then vertical
_SLOPE_BOTTOM = 0.60
_UNDERCUT = 0.090
_FACET = -0.180
_HOLLOW = 0.085
VALLEY_H = 0.085          # height of the valley above the lower ridge where the ridge is full
VALLEY_W = 0.012          # half-width of the valley fillet (a touch softer than the convex creases)
_Z_SILL = 0.60            # height at which P0 and P1 meet (just above the door bottoms)


def _p1_hollow(zv):
    """Hollow slope of P1 for a valley at zv, keeping x(_Z_SILL) where it is with the full ridge."""
    ref = _HOLLOW * (ZG_CREASE - (ZG_RIDGE + VALLEY_H)) + _FACET * VALLEY_H     # drop crease -> ridge (full)
    return (ref - _FACET * (zv - ZG_RIDGE)) / (ZG_CREASE - zv)


# P0 lower slope chosen so x(_Z_SILL) matches P1
_P0_LOW = ((_HOLLOW * (ZG_CREASE - ZG_RIDGE - VALLEY_H) + _FACET * VALLEY_H + _UNDERCUT * (ZG_RIDGE - _Z_SILL))
           - _HOLLOW * (ZG_CREASE - 1.03)) / (1.03 - _Z_SILL)


def _features(low, ridge):
    """(centre, half width, slope jump) list of the blended profile (weights (1-low) PN + low ((1-ridge) P0 + ridge P1))."""
    zv = ZG_RIDGE + VALLEY_H * (0.4 + 0.6 * ridge)
    h1 = _p1_hollow(zv)
    w1, w0, wn = low * ridge, low * (1.0 - ridge), 1.0 - low
    f = [
        (ZG_ROCKER, CREASE_W, w1 * (_UNDERCUT - _SLOPE_BOTTOM) + w0 * (_P0_LOW - _SLOPE_BOTTOM)),
        (ZG_RIDGE, CREASE_W, w1 * (_FACET - _UNDERCUT)),
        (zv, VALLEY_W, w1 * (h1 - _FACET)),
        (1.03, 0.10, w0 * (_HOLLOW - _P0_LOW) + wn * _HOLLOW),
        (ZG_CREASE, CREASE_W, w1 * (_SLOPE_UP - h1) + (w0 + wn) * (_SLOPE_UP - _HOLLOW)),
    ]
    return f, low * _SLOPE_BOTTOM


def _section_raw(zg, low, ridge):
    feats, s0 = _features(low, ridge)
    x = s0 * zg
    for c, w, ds in feats:
        if ds:
            x += ds * _si(c - w, c + w, zg)
    u = zg - (ZG_CREASE + CREASE_W)
    if u > 0.0:
        x -= _TUMBLE_B * u * u
    return x


_SEC_CACHE = {}


def side_base(zg, low=1.0, ridge=1.0):
    """Body-side section x(zg) (no plan bow). low (0..1) scales the lower-body features (rocker crease and the
    undercut lower door): 1 between the wheel openings, 0 elsewhere (low_w). ridge (0..1) scales the lower ridge and
    the up-facing facet above it: it fades out over the front door (ridge_w)."""
    key = (round(low, 4), round(ridge, 4))
    ref = _SEC_CACHE.get(key)
    if ref is None:
        ref = _SEC_CACHE[key] = _section_raw(ZG_CREASE, low, ridge)
    return X_CREASE + _section_raw(zg, low, ridge) - ref


def low_w(y):
    """Weight of the lower-body features along the truck: 1 from behind the front opening to ahead of the rear one."""
    return smoothstep(FAX - 0.30, FAX - 0.50, y) * smoothstep(RAX + 0.30, RAX + 0.50, y)


# strength of the lower ridge along the truck: full over the bed front and the rear door, tapering over the front
# door and gone ~15 cm behind its leading edge (the up-facing band above the ridge narrows to a point there)
_RIDGE_W = pchip([(0.40, 1.0), (0.82, 0.80), (1.03, 0.62), (1.165, 0.42), (1.28, 0.0)])


def ridge_w(y):
    if y <= 0.40:
        return 1.0
    if y >= 1.28:
        return 0.0
    return max(0.0, min(1.0, _RIDGE_W(y)))


def haunch(y):
    """0..1 weight of the rear haunch: the bedside swells over the rear wheel and rolls into the taillight."""
    return gauss(y, RAX - 0.20, 0.70)


def fender_swell(y):
    """0..1 weight of the front-fender swell over the front wheel."""
    return gauss(y, FAX - 0.05, 0.58)


def bow(y):
    """Plan-view curvature shared by every side panel, so reflections run continuously along the body: a swell over
    the front wheel, straight doors, the haunch over the rear wheel (kelley_041: the bedside stands ~2 cm proud of
    the rear door), nose and tail tapers."""
    front = 0.008 * fender_swell(y)
    rear = 0.018 * haunch(y)
    nose = -0.075 * smoothstep(2.48, Y_FENDER_F + 0.01, y) ** 2
    tail = -0.010 * smoothstep(-2.55, -2.80, y)
    return front + rear + nose + tail


def side_x(y, zg, top=None):
    """Body side surface: section (with the lower-body features where they exist) + plan bow. Over the wheels the
    swell is fullest just under the shoulder crease and rolls in above it (extra tumblehome on the haunch and the
    front fender), so the haunch reads as a rounded shoulder rather than a slab pushed outwards."""
    x = side_base(zg, low_w(y), ridge_w(y)) + bow(y)
    h = haunch(y)
    f = fender_swell(y)
    if zg > ZG_CREASE:
        k = (zg - ZG_CREASE) / (ZG_RAIL - ZG_CREASE)
        x -= (0.016 * h + 0.004 * f) * k * k
    else:
        # below the crease the swell eases off towards the sill (the openings cut most of it away)
        k = min(1.0, (ZG_CREASE - zg) / (ZG_CREASE - 0.55))
        x -= (0.006 * h + 0.003 * f) * k * k
    return x


def _inside_spans(outline, zc):
    """y-intervals where the horizontal line z = zc runs inside a closed (y, z) outline."""
    ys = []
    n = len(outline)
    for i in range(n):
        (ya, za), (yb, zb) = outline[i], outline[(i + 1) % n]
        if (za > zc) != (zb > zc):
            ys.append(ya + (zc - za) * (yb - ya) / (zb - za))
    ys.sort()
    return [(ys[i], ys[i + 1]) for i in range(0, len(ys) - 1, 2)]


def side_creases(y0, y1, fine=True, z_lo=0.0, z_hi=9.0, outline=None, inset=0.004):
    """Crease polylines (side view, (y, zg)) that a body-side panel spanning y0..y1 should pass to surf.panel so the
    character lines stay crisp: the shoulder crease everywhere, the lower ridge / valley / rocker crease where they
    exist.
    fine=True adds lines at +-CREASE_W so each fillet gets its own narrow triangle rows (a crisp highlight edge
    instead of a soft 5 cm band). Lines outside z_lo..z_hi are left out. With `outline` (the panel's closed (y, zg)
    outline) every line is clipped to the parts inside it, `inset` short of the edges (no T-junctions at the
    flange); otherwise keep y0..y1 a few mm inside the panel."""
    lo, hi = min(y0, y1), max(y0, y1)
    offs = (-CREASE_W, 0.0, CREASE_W) if fine else (0.0,)
    lines = []

    def add(a, b, zc):
        if not z_lo + 0.012 < zc < z_hi - 0.012:
            return
        for o in offs:
            z = zc + o
            spans = [(a, b)] if outline is None else \
                [(max(a, s0 + inset), min(b, s1 - inset)) for s0, s1 in _inside_spans(outline, z)]
            lines.extend([[(s0, z), (s1, z)] for s0, s1 in spans if s1 - s0 > 0.02])
    add(lo, hi, ZG_CREASE)
    a, b = max(lo, RAX + 0.40), min(hi, FAX - 0.40)      # lower features only where low_w ~ 1
    add(a, min(b, 1.20), ZG_RIDGE)                       # the ridge fades out over the front door
    add(a, b, ZG_ROCKER)
    # the valley above the ridge: a gently sloping line (it drops towards the ridge as the ridge fades)
    if z_lo + 0.012 < ZG_RIDGE + VALLEY_H and ZG_RIDGE + 0.03 < z_hi - 0.012:
        from surf import point_in_poly
        yb = min(b, 1.24)
        n = max(2, int((yb - a) / 0.03) + 1)
        run = []
        for k in range(n):
            y = a + (yb - a) * k / (n - 1)
            z = valley_z(y)
            ok = outline is None or all(point_in_poly((y + dy, z + dz), outline)
                                        for dy, dz in ((inset, 0), (-inset, 0), (0, inset), (0, -inset)))
            if ok:
                run.append((y, z))
            else:
                if len(run) > 1:
                    lines.append(run)
                run = []
        if len(run) > 1:
            lines.append(run)
    return lines


def valley_z(y):
    """Height of the concave valley line above the lower ridge at station y (see _features)."""
    return ZG_RIDGE + VALLEY_H * (0.4 + 0.6 * ridge_w(y) * low_w(y))


# Wheel openings (inner edge of the black moulding), relative to the axle (dy forward, zg), traced on the
# consumer_006 profile (tyre-top anchored, wheelbase-scaled): squared openings with a flat top, a long sweeping
# front-upper corner, a tighter rear-upper corner and near-vertical legs. Front top ~1.03 m, rear top ~1.075 m
# (factory rake + the bigger rear opening).
FRONT_ARCH = [(0.466, 0.813), (0.432, 0.856), (0.394, 0.894), (0.352, 0.930), (0.307, 0.962), (0.258, 0.989),
              (0.207, 1.007), (0.154, 1.018), (0.100, 1.024), (0.000, 1.029), (-0.110, 1.032), (-0.215, 1.032),
              (-0.275, 1.027), (-0.330, 1.010), (-0.378, 0.979), (-0.414, 0.934), (-0.437, 0.877),
              (-0.452, 0.812), (-0.463, 0.745), (-0.472, 0.672), (-0.480, ZG_BODY)]
# the front leg continues down the fascia end to the bumper (used by the moulding and the bumper cut)
FRONT_ARCH_EXT = [(0.540, 0.600), (0.512, 0.680), (0.497, 0.725), (0.486, 0.765)] + FRONT_ARCH
REAR_ARCH = [(0.484, 0.540), (0.481, 0.605), (0.476, 0.653), (0.470, 0.703), (0.462, 0.757), (0.450, 0.812),
             (0.428, 0.862), (0.395, 0.906), (0.356, 0.945), (0.314, 0.983), (0.268, 1.017), (0.218, 1.043),
             (0.164, 1.058), (0.110, 1.066), (0.000, 1.072), (-0.120, 1.075), (-0.230, 1.075), (-0.293, 1.070),
             (-0.345, 1.054), (-0.385, 1.022), (-0.414, 0.973), (-0.432, 0.915), (-0.445, 0.860),
             (-0.456, 0.812), (-0.468, 0.760), (-0.477, 0.705), (-0.484, 0.650), (-0.489, 0.600), (-0.492, 0.540)]
ARCH_FILLET = 0.05        # the outlines above are already rounded; this only eases the sampled vertices
ARCH_FILLET_COARSE = 0.13  # corner radius for coarse (few-vertex) opening polygons passed in by the region modules


def arch_fillet(shape):
    """Fillet radius for an opening polygon: dense traced outlines only need easing, coarse polygons (<= 10 vertices,
    e.g. a module's own straight-legged opening) get real rounded corners."""
    return ARCH_FILLET if len(shape) > 10 else ARCH_FILLET_COARSE


def rounded_poly(pts, r, seg=6, closed=False):
    """Polyline with filleted interior corners (endpoints kept)."""
    from mathutils import Vector
    P = [Vector(p) for p in pts]
    out = [tuple(P[0])]
    for i in range(1, len(P) - 1):
        a, b, c = P[i - 1], P[i], P[i + 1]
        d1, d2 = (a - b).normalized(), (c - b).normalized()
        ang = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        if ang < 1e-3 or abs(ang - math.pi) < 1e-3:
            out.append(tuple(b))
            continue
        t = min(r / math.tan(ang / 2), (a - b).length * 0.45, (c - b).length * 0.45)
        p1, p2 = b + d1 * t, b + d2 * t
        for k in range(seg + 1):
            u = k / seg
            q = (1 - u) ** 2 * p1 + 2 * (1 - u) * u * b + u ** 2 * p2
            out.append(tuple(q))
    out.append(tuple(P[-1]))
    return out


def arch_outline(cy, shape, offset=0.0):
    """Wheel opening outline in (y, zg), front foot -> over the top -> rear foot, optionally offset outwards."""
    pts = rounded_poly([(cy + dy, z) for dy, z in shape], arch_fillet(shape), seg=8)
    if offset == 0.0:
        return pts
    from mathutils import Vector
    cz = 0.5
    out = []
    for i, p in enumerate(pts):
        a = Vector(pts[max(i - 1, 0)])
        b = Vector(pts[min(i + 1, len(pts) - 1)])
        t = (b - a).normalized()
        n = Vector((t.y, -t.x))
        if n.dot(Vector(p) - Vector((cy, cz))) < 0:
            n = -n
        out.append((p[0] + n.x * offset, p[1] + n.y * offset))
    return out


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.hypot(ax + t * dx - p[0], ay + t * dy - p[1])


_SWELL_CACHE = {}


SWELL_A = 0.014           # sheet-metal flare around the openings: height of the plateau
SWELL_LIP = 0.35          # fraction of it left where the skin rolls in under the moulding


def arch_swell(y, zg, cy, shape):
    """Sheet-metal flare around a wheel opening (d = distance from the opening's inner edge): the skin rolls in
    under the black moulding (d < 0.075, hidden by the ~7 cm moulding), stands at a plateau just outside it (the
    near-vertical band between the moulding and the shoulder crease in consumer_006) and fades back into the body
    side by d ~ 0.30. Zero towards the
    door / bed-front shut lines so the fender and bedside stay flush with the doors."""
    key = (cy, id(shape))
    if key not in _SWELL_CACHE:
        _SWELL_CACHE[key] = arch_outline(cy, shape)
    pts = _SWELL_CACHE[key]
    if cy > 0:
        w = smoothstep(Y_FDOOR_F + 0.002, Y_FDOOR_F + 0.100, y)
    else:
        w = smoothstep(Y_BED_F - 0.002, Y_BED_F - 0.120, y)
    if w <= 0.0:
        return 0.0
    d = min(_seg_dist((y, zg), pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    if d >= 0.30:
        return 0.0
    lip = SWELL_LIP + (1.0 - SWELL_LIP) * smoothstep(0.040, 0.078, d)
    return w * SWELL_A * lip * (1.0 - smoothstep(0.120, 0.30, d))


def glass_x(zg):
    t = (zg - ZG_BELT) / (1.92 - ZG_BELT)
    return 0.962 - 0.105 * t


def a_pillar_y(zg):
    """Rear edge of the A-pillar in side view (= front edge of the door glass). Photo 02: ~59 deg from vertical."""
    t = (zg - ZG_BELT) / (ZG_WS_TOP - ZG_BELT)
    return 1.400 - (1.400 - Y_ROOF_F) * t


def ws_edge_y(zg):
    """Front edge of the A-pillar (= windshield side edge)."""
    return a_pillar_y(zg) + 0.09


def ws_hw(zg):
    t = (zg - ZG_BELT) / (ZG_WS_TOP - ZG_BELT)
    return WS_HW_BASE + (WS_HW_TOP - WS_HW_BASE) * t


def roof_front_y(x):
    """Roof front edge in plan: on the centreline above the windshield, sweeping back to the A-pillar tops."""
    t = min(1.0, abs(x) / 0.84)
    return Y_WS_TOP + 0.01 - (Y_WS_TOP + 0.01 - Y_ROOF_F) * t * t
