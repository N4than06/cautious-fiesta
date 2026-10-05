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
Y_FDOOR_F, Y_FDOOR_R = 1.460, 0.318
Y_RDOOR_F, Y_RDOOR_R = 0.306, -0.700
Y_CAB_R = -0.850
Y_BED_F, Y_BED_R = -0.875, -2.797
Y_ROOF_F = 0.600         # roof front corner above the side glass (top of the A-pillar)
Y_WS_TOP = 0.880         # windshield top on the centreline (the top edge wraps back to the pillars in plan)
ZG_WS_TOP = 1.930
WS_HW_BASE, WS_HW_TOP = 0.900, 0.720
CAB_SHIFT = 0.30         # interior moved forward with the cab (relative to the first layout)

# heights above ground
ZG_BODY = 0.600          # lower edge of doors / rear of fenders
ZG_CREASE = 1.050        # shoulder character line (below the door handles, taillight -> fender)
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

_S_LOW = pchip([(0.40, 0.935), (0.50, 0.955), (0.60, 0.988), (0.70, 1.000), (0.85, 1.006), (ZG_CREASE, 1.0125)])
_S_HIGH = pchip([(ZG_CREASE, 1.0125), (1.07, 1.0075), (1.18, 1.005), (1.30, 1.000), (1.40, 0.992), (1.47, 0.978),
                 (1.53, 0.958), (1.57, 0.935)])


def side_base(zg):
    return _S_LOW(zg) if zg <= ZG_CREASE else _S_HIGH(zg)


def haunch(y):
    """0..1 weight of the rear haunch: the bedside swells over the rear wheel and rolls into the taillight."""
    return gauss(y, RAX - 0.25, 0.75)


def bow(y):
    """Plan-view curvature shared by every side panel, so reflections run continuously along the body."""
    front = 0.011 * gauss(y, FAX - 0.05, 0.62)
    doors = -0.004 * gauss(y, 0.15, 0.70)
    rear = 0.020 * haunch(y)
    nose = -0.075 * smoothstep(2.48, Y_FENDER_F + 0.01, y) ** 2
    tail = -0.010 * smoothstep(-2.55, -2.80, y)
    return front + doors + rear + nose + tail


def side_x(y, zg, top=None):
    """Body side surface: profile + plan bow + extra tumblehome above the crease on the haunch."""
    x = side_base(zg) + bow(y)
    if zg > ZG_CREASE:
        k = (zg - ZG_CREASE) / (ZG_RAIL - ZG_CREASE)
        x -= 0.016 * haunch(y) * k * k
    return x


# Wheel openings (inner edge), relative to the axle (dy, zg): vertical rear edge, flat top set behind the axle,
# long diagonal front edge sweeping down into the bumper. Rear opening is taller (factory rake).
FRONT_ARCH = [(0.34, 0.80), (0.08, 0.945), (-0.30, 0.945), (-0.43, 0.83), (-0.43, ZG_BODY)]
# the diagonal continues down the bumper end (used by the moulding and the bumper cut)
FRONT_ARCH_EXT = [(0.56, 0.60)] + FRONT_ARCH
REAR_ARCH = [(0.53, 0.62), (0.53, 0.80), (0.04, 1.105), (-0.48, 1.105), (-0.62, 0.95), (-0.62, 0.62)]
ARCH_FILLET = 0.13


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
    pts = rounded_poly([(cy + dy, z) for dy, z in shape], ARCH_FILLET, seg=8)
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


def arch_swell(y, zg, cy, shape):
    """Soft sheet-metal swell around a wheel opening (under the black moulding)."""
    key = (cy, id(shape))
    if key not in _SWELL_CACHE:
        _SWELL_CACHE[key] = arch_outline(cy, shape)
    pts = _SWELL_CACHE[key]
    d = min(_seg_dist((y, zg), pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    return 0.010 * (1.0 - smoothstep(0.04, 0.20, d))


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
