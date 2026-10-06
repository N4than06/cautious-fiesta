"""Factory-master 2022 GMC Sierra 1500 AT4X: skeleton, mechanical parts, interior, wheels and assembly.

Dimensions live in at4x_dims.py; the exterior body is built in at4x_exterior.py.
"""
import math

from mathutils import Matrix, Vector

from at4x_dims import *  # noqa: F401,F403
from at4x_exterior import build_exterior, mirror_side
from geom import rrect


# ---------------------------------------------------------------------------------------------- bones

def bones():
    door_l = ((0, 0, -1.25), (0, 0, 0))
    door_r = ((0, 0, 0), (0, 0, 1.25))
    B = [
        dict(name="chassis", pos=(0, 0, 0)),
        dict(name="bodyshell", pos=(0, 0, 0), parent="chassis"),
        dict(name="door_dside_f", pos=(-1.0, Y_FDOOR_F - 0.02, G(1.20)), parent="chassis", limit_rot=door_l),
        dict(name="door_pside_f", pos=(1.0, Y_FDOOR_F - 0.02, G(1.20)), parent="chassis", limit_rot=door_r),
        dict(name="door_dside_r", pos=(-1.0, Y_RDOOR_F - 0.02, G(1.20)), parent="chassis", limit_rot=door_l),
        dict(name="door_pside_r", pos=(1.0, Y_RDOOR_F - 0.02, G(1.20)), parent="chassis", limit_rot=door_r),
        dict(name="window_lf", pos=(-0.92, 0.90, G(1.70)), parent="door_dside_f"),
        dict(name="window_rf", pos=(0.92, 0.90, G(1.70)), parent="door_pside_f"),
        dict(name="window_lr", pos=(-0.92, -0.20, G(1.70)), parent="door_dside_r"),
        dict(name="window_rr", pos=(0.92, -0.20, G(1.70)), parent="door_pside_r"),
        dict(name="windscreen", pos=(0, 1.27, G(1.70)), parent="chassis"),
        dict(name="windscreen_r", pos=(0, Y_CAB_R, G(1.68)), parent="chassis"),
        dict(name="bonnet", pos=(0, Y_HOOD_R + 0.02, G(1.43)), parent="chassis", limit_rot=((0, 0, 0), (1.0, 0, 0))),
        dict(name="boot", pos=(0, Y_BED_R - 0.01, G(0.955)), parent="chassis", limit_rot=((0, 0, 0), (1.57, 0, 0))),
        dict(name="bumper_f", pos=(0, 2.86, G(0.62)), parent="chassis"),
        dict(name="bumper_r", pos=(0, -2.88, G(0.62)), parent="chassis"),
        dict(name="steeringwheel", pos=(-0.42, 1.10, G(1.30)), parent="chassis",
             rot=Matrix.Rotation(math.radians(-24), 3, "X")),
        dict(name="seat_dside_f", pos=(-0.42, 0.54, G(0.86)), parent="chassis"),
        dict(name="seat_pside_f", pos=(0.42, 0.54, G(0.86)), parent="chassis"),
        dict(name="seat_dside_r", pos=(-0.42, -0.46, G(0.88)), parent="chassis"),
        dict(name="seat_pside_r", pos=(0.42, -0.46, G(0.88)), parent="chassis"),
        dict(name="engine", pos=(0, 1.95, G(1.05)), parent="chassis"),
        dict(name="overheat", pos=(0, 2.10, G(1.30)), parent="chassis"),
        dict(name="petrolcap", pos=(-1.0, -1.08, G(1.27)), parent="chassis"),
        dict(name="petroltank", pos=(0.55, -1.25, G(0.45)), parent="chassis"),
        dict(name="exhaust", pos=(-0.60, -2.63, G(0.33)), parent="chassis", rot=Matrix.Rotation(math.pi, 3, "Z")),
        dict(name="exhaust_2", pos=(0.60, -2.63, G(0.33)), parent="chassis", rot=Matrix.Rotation(math.pi, 3, "Z")),
        dict(name="headlight_l", pos=(-0.77, 2.79, G(1.13)), parent="chassis"),
        dict(name="headlight_r", pos=(0.77, 2.79, G(1.13)), parent="chassis"),
        dict(name="indicator_lf", pos=(-0.93, 2.56, G(1.25)), parent="chassis"),
        dict(name="indicator_rf", pos=(0.93, 2.56, G(1.25)), parent="chassis"),
        dict(name="taillight_l", pos=(-0.92, Y_BED_R - 0.02, G(1.40)), parent="chassis"),
        dict(name="taillight_r", pos=(0.92, Y_BED_R - 0.02, G(1.40)), parent="chassis"),
        dict(name="brakelight_l", pos=(-0.92, Y_BED_R - 0.02, G(1.25)), parent="chassis"),
        dict(name="brakelight_r", pos=(0.92, Y_BED_R - 0.02, G(1.25)), parent="chassis"),
        dict(name="brakelight_m", pos=(0, Y_CAB_R - 0.01, G(1.95)), parent="chassis"),
        dict(name="indicator_lr", pos=(-0.92, Y_BED_R - 0.02, G(1.15)), parent="chassis"),
        dict(name="indicator_rr", pos=(0.92, Y_BED_R - 0.02, G(1.15)), parent="chassis"),
        dict(name="reversinglight_l", pos=(-0.92, Y_BED_R - 0.02, G(1.05)), parent="chassis"),
        dict(name="reversinglight_r", pos=(0.92, Y_BED_R - 0.02, G(1.05)), parent="chassis"),
        dict(name="platelight", pos=(0, -2.93, G(0.78)), parent="chassis"),
        dict(name="interiorlight", pos=(0, 0.15, G(1.92)), parent="chassis"),
        dict(name="dashglow", pos=(-0.42, 1.32, G(1.40)), parent="chassis"),
        dict(name="neon_l", pos=(-0.80, -0.30, G(0.40)), parent="chassis"),
        dict(name="neon_r", pos=(0.80, -0.30, G(0.40)), parent="chassis"),
        dict(name="neon_f", pos=(0, 2.40, G(0.38)), parent="chassis"),
        dict(name="neon_b", pos=(0, -2.40, G(0.45)), parent="chassis"),
    ]
    for side, x in (("l", -TRACK), ("r", TRACK)):
        for end, y in (("f", FAX), ("r", RAX)):
            B.append(dict(name=f"wheel_{side}{end}", pos=(x, y, WZ), parent="chassis"))
            B.append(dict(name=f"suspension_{side}{end}", pos=(x * 0.62, y, WZ + 0.04), parent="chassis"))
            B.append(dict(name=f"hub_{side}{end}", pos=(x, y, WZ), parent="chassis"))
    for c in "abcdefghij":
        B.append(dict(name=f"misc_{c}", pos=(0, 0, 0), parent="chassis"))
    return B



# ---------------------------------------------------------------------------------------------- mechanical / interior

def engine_bay(mb):
    k = "black"
    mirror_side(mb, lambda m: m.box((0.78, Y_HOOD_R, G(0.78)), (0.84, 2.40, G(1.30)), k, "chassis"))  # aprons
    mb.box((-0.92, Y_WS - 0.03, G(0.70)), (0.92, Y_WS, G(1.40)), k, "chassis")                    # firewall
    mb.box((-0.72, 2.56, G(0.80)), (0.72, 2.62, G(1.26)), "steel", "chassis")                    # radiator
    # 6.2L V8: block, heads, valve covers, intake plenum
    mb.box((-0.24, 1.60, G(0.70)), (0.24, 2.30, G(1.02)), "steel", "chassis")
    for s in (-1, 1):
        mb.loft([[(s * 0.12, y, G(0.98)), (s * 0.40, y, G(1.10)), (s * 0.36, y, G(1.19)), (s * 0.10, y, G(1.07))]
                 for y in (1.62, 2.28)], "steel", "chassis")
        mb.rbox((s * 0.36 - 0.07, 1.64, G(1.13)), (s * 0.36 + 0.07, 2.26, G(1.20)), 0.02, "gloss_black", "chassis")
    mb.rbox((-0.16, 1.65, G(1.05)), (0.16, 2.22, G(1.16)), 0.03, "steel", "chassis")
    mb.cylinder((0, 2.30, G(0.95)), (0, 2.36, G(0.95)), 0.17, "black", "chassis", seg=24)  # front cover / balancer
    mb.rbox((-0.88, 2.10, G(1.08)), (-0.64, 2.36, G(1.28)), 0.02, "black", "chassis")   # battery
    mb.cylinder((0.70, 1.55, G(1.20)), (0.70, 1.55, G(1.29)), 0.065, "black", "chassis", seg=16)  # coolant
    mb.cylinder((-0.70, 1.48, G(1.22)), (-0.70, 1.48, G(1.30)), 0.05, "black", "chassis", seg=16)  # brake fluid


def engine_cover(mb):
    mb.rbox((-0.25, 1.64, G(1.18)), (0.25, 2.26, G(1.26)), 0.035, "engine_cover", "misc_e")


def airbox(mb):
    mb.rbox((0.47, 2.12, G(1.05)), (0.84, 2.56, G(1.28)), 0.04, "black", "misc_f")
    mb.tube([(0.58, 2.12, G(1.18)), (0.44, 1.88, G(1.20)), (0.15, 1.62, G(1.12))], 0.055, "black", "misc_f")


# ---------------------------------------------------------------------------------------------- underbody

def underbody(mb):
    k = "black"
    mirror_side(mb, lambda m: m.box((0.44, -2.75, G(0.40)), (0.53, 2.60, G(0.60)), k, "chassis"))
    for y in (2.40, 1.25, 0.0, -1.20, -2.45):
        mb.box((-0.46, y - 0.04, G(0.44)), (0.46, y + 0.04, G(0.56)), k, "chassis")
    # front IFS: upper and lower control arms, knuckles, half shafts, DSSV coil-overs
    def ifs(m):
        m.loft([[(0.30, FAX + dy, WZ - 0.14 + dz) for dy, dz in ((0.18, 0), (-0.22, 0), (-0.22, 0.04), (0.18, 0.04))],
                [(TRACK - 0.13, FAX + dy, WZ - 0.12 + dz) for dy, dz in ((0.04, 0), (-0.04, 0), (-0.04, 0.04), (0.04, 0.04))]],
               "black", "chassis")
        m.loft([[(0.42, FAX + dy, WZ + 0.18 + dz) for dy, dz in ((0.12, 0), (-0.14, 0), (-0.14, 0.03), (0.12, 0.03))],
                [(TRACK - 0.16, FAX + dy, WZ + 0.16 + dz) for dy, dz in ((0.03, 0), (-0.03, 0), (-0.03, 0.03), (0.03, 0.03))]],
               "alu", "chassis")
        m.cylinder((TRACK - 0.15, FAX, WZ - 0.14), (TRACK - 0.17, FAX, WZ + 0.20), 0.05, "steel", "chassis", seg=10)
        m.cylinder((0.16, FAX, WZ), (TRACK - 0.12, FAX, WZ), 0.032, "steel", "chassis", seg=10)
        m.cylinder((0.60, FAX - 0.05, WZ - 0.10), (0.56, FAX - 0.05, WZ + 0.36), 0.040, "gold", "chassis", seg=12)
        m.cylinder((0.56, FAX - 0.05, WZ + 0.22), (0.555, FAX - 0.05, WZ + 0.30), 0.07, "gold", "chassis", seg=14)
        m.cylinder((0.62, FAX - 0.15, WZ + 0.10), (0.62, FAX - 0.15, WZ + 0.34), 0.03, "gold", "chassis", seg=10)
    mirror_side(mb, ifs)
    mb.rbox((-0.17, FAX - 0.13, WZ - 0.12), (0.17, FAX + 0.13, WZ + 0.12), 0.05, "steel", "chassis")
    # rear axle, diff, leaf springs, DSSV shocks
    mb.cylinder((-TRACK + 0.10, RAX, WZ), (TRACK - 0.10, RAX, WZ), 0.055, "steel", "chassis", seg=14)
    mb.lathe([(0.10, -0.08), (0.17, -0.02), (0.17, 0.06), (0.12, 0.12)], "steel", "chassis", seg=20) \
        if False else mb.cylinder((0, RAX - 0.08, WZ), (0, RAX + 0.14, WZ), 0.16, "steel", "chassis", seg=20)
    def rear(m):
        m.tube([(0.50, RAX + 0.72, WZ + 0.13), (0.50, RAX + 0.3, WZ + 0.0), (0.50, RAX, WZ - 0.03),
                (0.50, RAX - 0.3, WZ + 0.0), (0.50, RAX - 0.72, WZ + 0.13)], 0.032, k, "chassis", seg=8)
        m.cylinder((0.62, RAX + 0.16, WZ - 0.08), (0.56, RAX + 0.24, WZ + 0.32), 0.04, "gold", "chassis", seg=12)
        m.cylinder((0.66, RAX + 0.30, WZ + 0.18), (0.66, RAX + 0.30, WZ + 0.40), 0.03, "gold", "chassis", seg=10)
    mirror_side(mb, rear)
    # 10-speed transmission, transfer case, driveshafts
    mb.cylinder((0, 1.55, G(0.80)), (0, 0.55, G(0.70)), 0.18, "steel", "chassis", seg=16, r1=0.12)
    mb.rbox((-0.17, 0.25, G(0.58)), (0.17, 0.55, G(0.80)), 0.04, "steel", "chassis")
    mb.cylinder((0, 0.25, G(0.66)), (0, RAX + 0.14, WZ + 0.02), 0.048, "steel", "chassis", seg=12)
    mb.cylinder((0.05, 0.55, G(0.66)), (0, FAX - 0.13, WZ), 0.035, "steel", "chassis", seg=10)
    # skid plates (misc_g): transfer case + front
    mb.rbox((-0.36, 0.25, G(0.34)), (0.36, 1.35, G(0.37)), 0.02, "alu", "misc_g")
    # fuel tank
    mb.rbox((0.10, -1.66, G(0.38)), (0.86, -0.96, G(0.62)), 0.05, k, "chassis")
    # exhaust
    mb.tube([(0.32, 1.62, G(0.88)), (0.32, 1.22, G(0.50)), (0.26, 0.20, G(0.48)), (0.26, -0.40, G(0.48))],
            0.036, "steel", "chassis", seg=10)
    mb.rbox((0.05, -0.86, G(0.37)), (0.42, -0.40, G(0.56)), 0.06, "steel", "chassis")
    for s in (-1, 1):
        mb.tube([(s * 0.20, -0.86, G(0.45)), (s * 0.48, -1.30, G(0.45)), (s * 0.60, -2.10, G(0.42)),
                 (s * 0.60, -2.78, G(0.40))], 0.033, "steel", "chassis", seg=10)
    # spare under the bed
    with mb.at((0, -2.35, G(0.50)), Matrix.Rotation(math.pi / 2, 3, "Y")):
        mb.lathe([(0.20, -0.13), (0.40, -0.12), (0.42, 0.0), (0.40, 0.12), (0.20, 0.13)], "tire", "chassis", seg=24,
                 close=True)


def exhaust_tips(mb):
    """Factory 6.2L AT4X: dual exits tucked behind the rear bumper, turned down -- not visible from behind
    (photos 03/04, kelley_005, royal_004)."""
    for s in (-1, 1):
        mb.tube([(s * 0.60, -2.10, G(0.42)), (s * 0.60, -2.50, G(0.41)), (s * 0.60, -2.60, G(0.38)),
                 (s * 0.60, -2.63, G(0.33))], 0.038, "black", "misc_b", seg=14)


def interior(mb):
    """Cabin shell parts that follow the cab layout directly (floor, headliner, back wall trim)."""
    mb.box((-0.90, Y_CAB_R + 0.02, G(0.62)), (0.90, Y_WS - 0.04, G(0.66)), "carpet", "chassis")
    # headliner: built by ext_cab.headliner() (follows the roof underside)
    mb.box((-0.90, Y_CAB_R + 0.005, G(0.66)), (0.90, Y_CAB_R + 0.03, G(1.47)), "trim", "chassis")


def front_row(mb):
    """Dashboard, console and front seats (authored around the original layout; build_body moves them)."""
    mb.loft([[(x, 1.215, G(z)) for x, z in rrect(0, 1.18, 0.90, 0.26, 0.05, 2)],
             [(x, 0.98, G(z)) for x, z in rrect(0, 1.20, 0.90, 0.22, 0.08, 2)],
             [(x, 0.90, G(z)) for x, z in rrect(0, 1.10, 0.86, 0.12, 0.06, 2)]], "trim", "chassis")
    mb.rbox((-0.62, 0.92, G(1.36)), (-0.22, 1.02, G(1.47)), 0.03, "black", "chassis")
    mb.decal((-0.42, 0.918, G(1.405)), (0, -1, 0.15), (0, 0.15, 1), 0.36, 0.10, "dash", "chassis")
    mb.decal((0.0, 0.915, G(1.30)), (0, -1, 0.25), (0, 0.25, 1), 0.33, 0.20, "screen", "chassis")
    mb.box((-0.14, -0.15, G(0.66)), (0.14, 0.95, G(1.02)), "trim", "chassis")          # console
    mb.cylinder((-0.42, 0.98, G(1.22)), (-0.42, 0.82, G(1.29)), 0.04, "black", "chassis", seg=12)
    b = "misc_h"
    for s in (-1, 1):
        x = 0.42 * s
        mb.rbox((x - 0.26, 0.02, G(0.80)), (x + 0.26, 0.56, G(0.92)), 0.05, "leather", b)
        mb.loft([[(x + dx, 0.03, G(0.92 + dz)) for dx, dz in rrect(0, 0.05, 0.25, 0.05, 0.04, 2)],
                 [(x + dx, -0.09, G(1.55 + dz)) for dx, dz in rrect(0, 0.05, 0.23, 0.05, 0.04, 2)]], "leather", b)
        mb.rbox((x - 0.13, -0.12, G(1.58)), (x + 0.13, -0.04, G(1.76)), 0.035, "leather", b)
        mb.box((x - 0.19, -0.13, G(1.10)), (x + 0.19, -0.115, G(1.12)), "leather_red", b)


def rear_row(mb):
    b = "misc_h"
    mb.rbox((-0.80, -0.82, G(0.80)), (0.80, -0.35, G(0.93)), 0.05, "leather", b)
    mb.loft([[(dx, -0.80, G(0.93 + dz)) for dx, dz in rrect(0, 0.05, 0.78, 0.05, 0.04, 2)],
             [(dx, -0.88, G(1.56 + dz)) for dx, dz in rrect(0, 0.05, 0.76, 0.05, 0.04, 2)]], "leather", b)


def steering_wheel(mb):
    b = "steeringwheel"
    c = Vector((-0.42, 0.80, G(1.30)))
    rot = Matrix.Rotation(math.radians(-24), 4, "X")
    with mb.push_ctx(Matrix.Translation(c) @ rot):
        with mb.push_ctx(Matrix.Rotation(math.radians(90), 4, "Z")):
            mb.lathe([(0.172, -0.016), (0.188, -0.022), (0.198, 0.0), (0.188, 0.022), (0.172, 0.016)], "leather", b,
                     seg=32, close=True)
        mb.rbox((-0.07, -0.02, -0.06), (0.07, 0.05, 0.05), 0.03, "black", b)
        for a in (180, 0):
            ra = math.radians(a)
            mb.cylinder((0.06 * math.cos(ra), 0.0, 0.0), (0.18 * math.cos(ra), 0, -0.01), 0.016, "black", b, seg=8)
        mb.cylinder((0, 0.0, -0.05), (0, 0.0, -0.175), 0.016, "black", b, seg=8)


# ---------------------------------------------------------------------------------------------- assembly

def build_body(mb):
    build_exterior(mb)
    with mb.push_ctx(Matrix.Translation((0, 0.15, -0.03))):      # engine sits further forward under the hood
        engine_bay(mb)
        engine_cover(mb)
        airbox(mb)
    underbody(mb)
    exhaust_tips(mb)
    interior(mb)
    with mb.push_ctx(Matrix.Translation((0, CAB_SHIFT, 0))):
        front_row(mb)
        steering_wheel(mb)
    with mb.push_ctx(Matrix.Translation((0, 0.10, 0))):
        rear_row(mb)


# ---------------------------------------------------------------------------------------------- wheel
#
# Factory AT4X wheel and tyre, modelled once as the left-front wheel (outer face towards -X) and instanced.
#   * Tyre: LT275/70R18 Goodyear Wrangler DuraTrac RT (what the reference trucks wear -- the sidewalls read
#     GOODYEAR / WRANGLER / DURATRAC): 46 tread pitches; staggered long/short shoulder blocks with a chevron inner
#     end that wrap over the shoulder, slanted centre blocks forming the chevron / diamond chain, and on the outer
#     sidewall big framed shield lugs (sunk field + raised tab) alternating with small stepped tongues. Every block
#     has rolled top edges and drafted walls; sipes and the sidewall lettering are textures.
#   * Wheel: 18x8.5 gloss-black aluminium, 6 split spokes (12 arms with a soft ridge and an angular kink near the
#     rim), rolled window edges, concave face, rolled lip, barrel, GMC centre cap, 6 chrome capped lug nuts on
#     6x139.7, valve stem and brake rotor behind.

_W_PITCHES = 46               # tread pitches around the tyre
_W_TREAD = 0.012              # tread depth (15/32 in)
_W_REF = 0.4211               # reference radius for circumferential lengths
_W_PLAIN_UV = (0.5, 0.045)    # a patch of plain rubber in the tyre textures (walls, groove floors, lugs)


def _w_spline(ctrl, sub=10):
    """Uniform Catmull-Rom through 2D control points (end points duplicated)."""
    pts = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(sub):
            s = k / sub
            s2, s3 = s * s, s * s * s
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * s + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * s2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * s3) for j in range(2)))
    out.append(tuple(ctrl[-1]))
    return out


class _TyreSection:
    """Carcass cross-section (groove floor / sidewall surface) parameterised by arc length t from the crown centre.

    q = lateral distance from the wheel centre plane, r = radius. t > 0 is the outer (-X) half, t < 0 the inner half.
    """

    # nominal LT275/70R18 carcass, (q, r): flat crown, rounded shoulder, sidewall bulge (283 mm section),
    # rim-protector bead and the bead tucked behind the rim flange.
    CTRL = [(0.0, 0.4091), (0.040, 0.4089), (0.080, 0.4078), (0.100, 0.4062), (0.112, 0.4033), (0.1215, 0.3982),
            (0.1283, 0.3910), (0.1332, 0.3815), (0.1367, 0.3695), (0.1390, 0.3545), (0.1402, 0.3380), (0.1405, 0.3200),
            (0.1400, 0.3030), (0.1386, 0.2880), (0.1366, 0.2765), (0.1356, 0.2700), (0.1365, 0.2630), (0.1352, 0.2555),
            (0.1300, 0.2490), (0.1235, 0.2452), (0.1175, 0.2410)]

    def __init__(self, tire_r, rim_r, width):
        sx = width / 0.275
        sr = (tire_r - rim_r) / (0.4211 - 0.2286)
        ctrl = [(q * sx, rim_r + (r - 0.2286) * sr) for q, r in self.CTRL]
        self.pts = _w_spline(ctrl, 12)
        self.ts = [0.0]
        for a, b in zip(self.pts, self.pts[1:]):
            self.ts.append(self.ts[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        self.length = self.ts[-1]

    def at(self, t):
        """(q, r, nq, nr) at arc length |t| (outward unit normal in the q/r plane)."""
        t = min(max(abs(t), 0.0), self.length)
        ts = self.ts
        lo, hi = 0, len(ts) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if ts[mid] <= t:
                lo = mid
            else:
                hi = mid
        a, b = self.pts[lo], self.pts[hi]
        f = (t - ts[lo]) / max(1e-12, ts[hi] - ts[lo])
        q, r = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        # normal from a slightly wider stencil for smoothness
        i0, i1 = max(0, lo - 1), min(len(self.pts) - 1, hi + 1)
        dq, dr = self.pts[i1][0] - self.pts[i0][0], self.pts[i1][1] - self.pts[i0][1]
        n = math.hypot(dq, dr)
        return q, r, -dr / n, dq / n

    def t_at_r(self, r_target):
        """Arc length on the sidewall where the carcass reaches radius r_target (searching from the shoulder)."""
        for (a, b, ta, tb) in zip(self.pts, self.pts[1:], self.ts, self.ts[1:]):
            if a[1] >= r_target > b[1] and a[0] > 0.05:
                return ta + (tb - ta) * (a[1] - r_target) / max(1e-12, a[1] - b[1])
        return self.length

    def point(self, t, th, h=0.0):
        q, r, nq, nr = self.at(t)
        q, r = q + h * nq, r + h * nr
        x = -q if t >= 0 else q
        return Vector((x, r * math.cos(th), r * math.sin(th)))

    def normal(self, t, th):
        _, _, nq, nr = self.at(t)
        return Vector((-nq if t >= 0 else nq, nr * math.cos(th), nr * math.sin(th)))

    def radius(self, t):
        return self.at(t)[1]


def _w_face(mb, ids, pts, out, mat, uv=None):
    """Add a face oriented so its normal points along `out` (explicit winding, like decals)."""
    n = Vector((0.0, 0.0, 0.0))
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        n += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
    ids = list(ids)
    if uv is not None:
        uv = list(uv)
    if n.dot(out) < 0:
        ids.reverse()
        if uv is not None:
            uv.reverse()
    mb.face(ids, mat, None, 1.0, uv=uv, fixed=True)


def _w_loop_normals(loop):
    """Outward unit normals (2D, metric) at the vertices of a closed loop, whatever its winding."""
    n = len(loop)
    area = sum(loop[i][0] * loop[(i + 1) % n][1] - loop[(i + 1) % n][0] * loop[i][1] for i in range(n))
    sgn = 1.0 if area < 0 else -1.0          # CCW loop: outward = right-hand normal
    out = []
    for i in range(n):
        a, b, c = loop[i - 1], loop[i], loop[(i + 1) % n]
        e1 = (b[0] - a[0], b[1] - a[1])
        e2 = (c[0] - b[0], c[1] - b[1])
        n1 = (e1[1], -e1[0])
        n2 = (e2[1], -e2[0])
        l1, l2 = math.hypot(*n1) or 1.0, math.hypot(*n2) or 1.0
        v = (n1[0] / l1 + n2[0] / l2, n1[1] / l1 + n2[1] / l2)
        lv = math.hypot(*v) or 1.0
        out.append((-sgn * v[0] / lv, -sgn * v[1] / lv))
    return out


def _w_poly_resample(poly, seg):
    """Split every edge of a closed polygon into pieces no longer than `seg` (corners kept)."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        k = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / seg)))
        for j in range(k):
            out.append((a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k))
    return out


def _w_ccw(poly):
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
               for i in range(len(poly)))
    return poly if area > 0 else list(reversed(poly))


def _w_out_normals(poly):
    """Outward mitre vectors (unit offset) at the vertices of a CCW polygon."""
    ins = _w_inset(poly, 1.0)
    return [(p[0] - q[0], p[1] - q[1]) for p, q in zip(poly, ins)]


def _w_inset(poly, d):
    """Offset a CCW polygon inwards by d (mitred, for small d)."""
    n = len(poly)
    out = []
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        e1 = (b[0] - a[0], b[1] - a[1])
        e2 = (c[0] - b[0], c[1] - b[1])
        l1, l2 = math.hypot(*e1) or 1.0, math.hypot(*e2) or 1.0
        n1 = (-e1[1] / l1, e1[0] / l1)          # left normals = inwards for CCW
        n2 = (-e2[1] / l2, e2[0] / l2)
        m = (n1[0] + n2[0], n1[1] + n2[1])
        lm = math.hypot(*m) or 1.0
        m = (m[0] / lm, m[1] / lm)
        cosh = max(0.35, m[0] * n1[0] + m[1] * n1[1])
        out.append((b[0] + m[0] * d / cosh, b[1] + m[1] * d / cosh))
    return out


class _Solid:
    """A raised rubber feature (tread block, sidewall lug) standing on the carcass.

    Drawn in (t, m): t = section arc length (signed, +outer side), m = circumferential distance at the feature's
    own radius (so offsets are metric). s0 is the circumferential position (arc length at _W_REF) of m = 0."""

    def __init__(self, mb, sec, bone, s0, t_mid):
        self.mb, self.sec, self.bone, self.s0 = mb, sec, bone, s0
        self.k = _W_REF / sec.radius(t_mid)         # m -> s

    def p3(self, t, m, h):
        return self.sec.point(t, (self.s0 + m * self.k) / _W_REF, h)

    def nrm(self, t, m):
        return self.sec.normal(t, (self.s0 + m * self.k) / _W_REF)

    def lateral(self, t, m, dt, dm):
        a = self.p3(t, m, 0.0)
        b = self.p3(t + dt * 0.01, m + dm * 0.01, 0.0)
        return (b - a).normalized()

    def build(self, poly, hfun, rho=0.0012, nround=2, draft=0.0012, base_h=-0.0015, seg=0.009, spacing=0.011,
              pockets=(), mat="tire", uv=None):
        """poly: (t, m) outline; hfun(t, m) -> height above the carcass. pockets: (loop, depth, rho) sunk into
        the top face. uv(t, m) -> texture coordinate for the top / rolled faces (plain rubber elsewhere)."""
        mb, bone = self.mb, self.bone
        poly = _w_ccw(_w_poly_resample(_w_ccw(poly), seg))
        uvf = uv or (lambda t, m: _W_PLAIN_UV)
        n = len(poly)
        out2 = _w_out_normals(poly)
        # rolled top edge: rings from the top face (inset rho) round to the wall (at the outline, h - rho)
        rings2, ringsh = [], []
        for kk in range(nround + 1):
            ph = 0.5 * math.pi * kk / nround
            ins = rho * (1.0 - math.sin(ph))
            ring = _w_inset(poly, ins) if ins > 1e-7 else list(poly)
            rings2.append(ring)
            ringsh.append([hfun(t, m) - rho * (1.0 - math.cos(ph)) for t, m in ring])
        base = [(t + o[0] * draft, m + o[1] * draft) for (t, m), o in zip(poly, out2)]
        rings2.append(base)
        ringsh.append([base_h] * n)
        pts = [[self.p3(t, m, h) for (t, m), h in zip(r2, rh)] for r2, rh in zip(rings2, ringsh)]
        ids = [[mb._vert(p, bone) for p in ring] for ring in pts]
        for kk in range(len(pts) - 1):
            ph = 0.5 * math.pi * min(nround, kk + 0.5) / nround
            for i in range(n):
                j = (i + 1) % n
                t, m = poly[i]
                o = ((out2[i][0] + out2[j][0]) * 0.5, (out2[i][1] + out2[j][1]) * 0.5)
                out = self.nrm(t, m) * math.cos(ph) + self.lateral(t, m, o[0], o[1]) * math.sin(ph)
                uvq = None
                if kk < nround:
                    uvq = [uvf(*rings2[kk][i]), uvf(*rings2[kk][j]), uvf(*rings2[kk + 1][j]), uvf(*rings2[kk + 1][i])]
                else:
                    uvq = [_W_PLAIN_UV] * 4
                _w_face(mb, [ids[kk][i], ids[kk][j], ids[kk + 1][j], ids[kk + 1][i]],
                        [pts[kk][i], pts[kk][j], pts[kk + 1][j], pts[kk + 1][i]], out, mat, uv=uvq)
        # pockets: rolled rim, wall, floor
        holes = []
        for loop, depth, rp in pockets:
            loop = _w_ccw(_w_poly_resample(_w_ccw(loop), seg))
            ln = len(loop)
            lo2 = _w_out_normals(loop)
            prings = []
            for kk in range(nround + 1):
                ph = 0.5 * math.pi * kk / nround
                d = rp * (1.0 - math.sin(ph))
                prings.append([((t + o[0] * d, m + o[1] * d), hfun(t, m) - rp * (1.0 - math.cos(ph)))
                               for (t, m), o in zip(loop, lo2)])
            prings.append([((t, m), hfun(t, m) - depth) for (t, m) in loop])
            holes.append([q for q, _ in prings[0]])
            pp = [[self.p3(t, m, h) for (t, m), h in ring] for ring in prings]
            pid = [[mb._vert(p, bone) for p in ring] for ring in pp]
            for kk in range(len(pp) - 1):
                ph = 0.5 * math.pi * min(nround, kk + 0.5) / nround
                for i in range(ln):
                    j = (i + 1) % ln
                    t, m = loop[i]
                    o = ((lo2[i][0] + lo2[j][0]) * 0.5, (lo2[i][1] + lo2[j][1]) * 0.5)
                    out = self.nrm(t, m) * math.cos(ph) - self.lateral(t, m, o[0], o[1]) * math.sin(ph)
                    _w_face(mb, [pid[kk][i], pid[kk][j], pid[kk + 1][j], pid[kk + 1][i]],
                            [pp[kk][i], pp[kk][j], pp[kk + 1][j], pp[kk + 1][i]], out, mat, uv=[_W_PLAIN_UV] * 4)
            self._cap(loop, [], lambda t, m, dd=depth: hfun(t, m) - dd, spacing, mat, lambda t, m: _W_PLAIN_UV,
                      guard=0.0)
        self._cap(rings2[0], holes, hfun, spacing, mat, uvf, guard=0.0007 if nround > 1 else 0.0)

    def _cap(self, outline, holes, hfun, spacing, mat, uvf, guard=0.0007):
        """CDT-triangulated top face of an outline (with holes), points lifted by hfun."""
        from mathutils.geometry import delaunay_2d_cdt
        from surf import point_in_poly
        mb, bone = self.mb, self.bone
        verts, edges = [], []
        # guard loops 0.7 mm inside the boundaries keep the rolled-edge normals in a narrow band
        guards = ([_w_inset(_w_ccw(outline), guard)] + [_w_inset(_w_ccw(h), -guard) for h in holes]) if guard else []
        loops = [outline] + list(holes) + guards
        for loop in loops:
            b = len(verts)
            verts += loop
            edges += [(b + i, b + (i + 1) % len(loop)) for i in range(len(loop))]
        ts = [p[0] for p in outline]
        ms = [p[1] for p in outline]
        t = min(ts) + spacing * 0.5
        while t < max(ts):
            m = min(ms) + spacing * 0.5
            while m < max(ms):
                if point_in_poly((t, m), outline) and not any(point_in_poly((t, m), h) for h in holes):
                    near = any(math.hypot(t - a, m - b) < spacing * 0.55 for loop in loops for a, b in loop)
                    if not near:
                        verts.append((t, m))
                m += spacing
            t += spacing
        ov, _, of, _, _, _ = delaunay_2d_cdt([Vector(p) for p in verts], edges, [], 0, 1e-9)
        p3 = [self.p3(v.x, v.y, hfun(v.x, v.y)) for v in ov]
        ids = {}
        for f in of:
            a, b, c3 = ov[f[0]], ov[f[1]], ov[f[2]]
            if abs((b.x - a.x) * (c3.y - a.y) - (b.y - a.y) * (c3.x - a.x)) < 2e-9:
                continue                              # sliver between collinear boundary points
            c = (sum(ov[i].x for i in f) / len(f), sum(ov[i].y for i in f) / len(f))
            if not point_in_poly(c, outline) or any(point_in_poly(c, h) for h in holes):
                continue
            for i in f:
                if i not in ids:
                    ids[i] = mb._vert(p3[i], bone)
            _w_face(mb, [ids[i] for i in f], [p3[i] for i in f], self.nrm(*c), mat,
                    uv=[uvf(ov[i].x, ov[i].y) for i in f])


def _w_tread(mb, sec, bone):
    """DuraTrac RT tread. Per pitch and side: a big shoulder block (alternately long / short) wrapping over the
    shoulder and a slanted centre block; on the sidewall below every shoulder block a lug -- alternately the big
    framed shield (sunk field with a raised tab) and a small stepped tongue.
    The inner half is the outer half mirrored and shifted half a pitch."""
    P = 2 * math.pi * _W_REF / _W_PITCHES
    t_lug0 = sec.t_at_r(sec.radius(0.0) - 0.0175)       # top of the sidewall lugs, just below the shoulder
    t_sh = t_lug0 - 0.0015                              # outer end of the shoulder blocks
    R0 = sec.radius(0.0)

    def lean(t):
        return 0.16 * t                                  # lateral grooves lean a little (s shift per t)

    def sipe_uv(phase):
        return lambda t, m: (abs(t) / 0.064, phase + m / 0.048)

    for k in range(_W_PITCHES):
        even = k % 2 == 0
        for side in (1, -1):
            sb = (k + (0.0 if side > 0 else 0.5)) * P
            alt = even if side > 0 else not even
            uvb = sipe_uv(0.13 * ((k * 7 + (3 if side > 0 else 0)) % 5))

            # ---- shoulder block: chevron inner end on the zig-zag groove, wraps down to the sidewall lugs
            t_in = 0.049 if alt else 0.057
            w = 0.82 * P
            ts = [t for t in (0.085, 0.108, 0.122) if t_in < t < t_sh - 0.002]
            ts = [t_in] + ts + [t_sh]
            left = [(side * t, lean(t)) for t in ts]
            right = [(side * t, lean(t) + w) for t in reversed(ts)]
            tip = (side * (t_in - 0.0045), lean(t_in) + w * 0.55)
            poly = left + right + [tip]
            sol = _Solid(mb, sec, bone, sb, side * 0.09)
            sol.k = _W_REF / R0
            hs = lambda t, m: _W_TREAD + 0.0030 * smoothstep(0.098, t_sh - 0.002, abs(t))
            sol.build(poly, hs, rho=0.0014, nround=2 if side > 0 else 1, seg=0.022, spacing=0.02, uv=uvb)

            # ---- centre block: slanted parallelogram from the zig-zag groove to the centre line; with the other
            #      half (mirrored, half a pitch on) the centre blocks form the chevron / diamond chain
            L = 0.62                                     # slant: s shift per unit t
            t_o, t_i = t_in - 0.0075, 0.0042
            wc = 0.60 * P
            s_o = 0.10 * P + lean(t_in)
            poly = [(side * t_o, s_o), (side * (t_o + 0.0035), s_o + 0.5 * wc), (side * t_o, s_o + wc),
                    (side * t_i, s_o + wc - L * (t_o - t_i)), (side * t_i, s_o - L * (t_o - t_i))]
            sol = _Solid(mb, sec, bone, sb, side * 0.03)
            sol.k = _W_REF / R0
            ph = 0.13 * ((k * 3 + (1 if side > 0 else 0)) % 4)
            sol.build(poly, lambda t, m: _W_TREAD, rho=0.0012, nround=1, seg=0.03, spacing=0.02,
                      uv=lambda t, m, ph=ph: (abs(t) / 0.064, ph + (m + L * abs(t)) / 0.048))

            # ---- sidewall lug under the shoulder block
            sol = _Solid(mb, sec, bone, sb + lean(t_sh) + w * 0.5, side * (t_lug0 + 0.025))
            mc = 0.0
            if side > 0 and alt:          # big framed shield
                H = 0.058
                wt, wb, c = 0.038, 0.026, 0.008
                tt, tb = t_lug0, t_lug0 + H
                poly = [(tt, mc - wt / 2), (tb - c, mc - wb / 2), (tb, mc - wb / 2 + c), (tb, mc + wb / 2 - c),
                        (tb - c, mc + wb / 2), (tt, mc + wt / 2)]
                hl = lambda t, m: 0.0080 - 0.0040 * (t - t_lug0) / H
                pocket = _w_inset(_w_ccw(poly), 0.0058)
                sol.build(poly, hl, rho=0.0010, nround=2, draft=0.0010, seg=0.02, spacing=0.016,
                          pockets=[(pocket, 0.0034, 0.0008)])
                # raised tab in the lower part of the sunk field
                tab = [(tt + 0.029, mc - 0.0075), (tb - 0.013, mc - 0.0058), (tb - 0.013, mc + 0.0058),
                       (tt + 0.029, mc + 0.0075)]
                sol.build(tab, lambda t, m: hl(t, m) - 0.0034 + 0.0028, rho=0.0007, nround=1, draft=0.0006,
                          base_h=hl(tt + 0.035, 0) - 0.0042, seg=0.012, spacing=0.02)
            elif side > 0:                # small tongue with a sunk step near its foot
                H = 0.040
                tt, tb = t_lug0, t_lug0 + H
                poly = [(tt, mc - 0.0125), (tb - 0.005, mc - 0.0078), (tb, mc - 0.0055), (tb, mc + 0.0055),
                        (tb - 0.005, mc + 0.0078), (tt, mc + 0.0125)]
                step = [(tt + 0.020, mc - 0.0062), (tb - 0.006, mc - 0.0045), (tb - 0.006, mc + 0.0045),
                        (tt + 0.020, mc + 0.0062)]
                sol.build(poly, lambda t, m: 0.0068 - 0.0030 * (t - t_lug0) / H, rho=0.0010, nround=2,
                          draft=0.0010, seg=0.02, spacing=0.02, pockets=[(step, 0.0022, 0.0006)])
            else:                         # inner sidewall: plain lugs
                H = 0.046 if alt else 0.034
                tt, tb = -t_lug0, -(t_lug0 + H)
                wt, wb = (0.032, 0.020) if alt else (0.023, 0.014)
                poly = [(tt, mc - wt / 2), (tb, mc - wb / 2), (tb, mc + wb / 2), (tt, mc + wt / 2)]
                sol.build(poly, lambda t, m, H=H: 0.0070 - 0.0035 * (abs(t) - t_lug0) / H, rho=0.0012, nround=1,
                          seg=0.014, spacing=0.02)


def _w_carcass(mb, sec, bone, side_mat, seg):
    """Groove floor across the tread and the two sidewalls (outer one carries the lettering texture)."""
    t_sh = sec.t_at_r(sec.radius(0.0) - 0.0175)
    L = sec.length
    tread_ts = [0.0, 0.03, 0.06, 0.085, 0.10, 0.11, 0.118, 0.125, t_sh - 0.004, t_sh + 0.004]
    wall_ts = [t_sh + 0.004 + (L - t_sh - 0.004) * k / 13 for k in range(1, 14)]
    wall_ts = sorted(set(round(t, 5) for t in wall_ts))
    # groove floor (plain rubber band of the tread texture)
    prof = []
    for t in [-x for x in reversed(tread_ts[1:])] + tread_ts:
        q, r, _, _ = sec.at(t)
        prof.append((r, -q if t >= 0 else q))
    mb.lathe(prof, "tire", bone, seg=seg, polar_uv=(0.37, 0.37 + 0.6, 1))
    # outer sidewall: polar-mapped lettering (v = 0 at the rim flange, 1 at the shoulder), twice around
    r_in, r_out = sec.radius(L), sec.radius(t_sh)
    prof = []
    for t in [t_sh + 0.004] + wall_ts:
        q, r, _, _ = sec.at(t)
        prof.append((r, -q))
    mb.lathe(prof, side_mat, bone, seg=seg, polar_uv=(r_in, r_out, 2))
    # inner sidewall: plain rubber
    prof = []
    for t in [t_sh + 0.004] + wall_ts[::2] + ([wall_ts[-1]] if len(wall_ts) % 2 == 0 else []):
        q, r, _, _ = sec.at(t)
        prof.append((r, q))
    mb.lathe(prof, "sidewall", bone, seg=seg, polar_uv=(r_in - 0.5, r_in + 3.5, 1))


def build_wheel(mb, bone="wheel_lf", rwl=False, rim_style="at4x", tire_r=TIRE_R, rim_r=RIM_R, width=TIRE_W):
    """Left-front wheel centred on its bone, outer face towards -X: LT275/70R18 Wrangler DuraTrac on the 18in
    gloss-black AT4X wheel (tyre ~20k triangles, wheel ~12k)."""
    start = len(mb.verts)
    sec = _TyreSection(tire_r, rim_r, width)
    _w_carcass(mb, sec, bone, "sidewall_rwl" if rwl else "sidewall", seg=2 * _W_PITCHES)
    _w_tread(mb, sec, bone)
    build_rim(mb, bone, rim_style, rim_r, width / 2)
    _r_weld(mb, start)


# ---------------------------------------------------------------------------------------------- rim
#
# AT4X 18x8.5 wheel, measured from a rectified near-frontal photo (plaza_021, scaled by the 6x139.7 lug circle):
#   * 6 lug nuts; the 6 split spokes sit midway between them, so the face has 12 arms at ~+-14.5 deg about
#     each spoke axis and two kinds of window: a "between" window right under each lug (radial sides at
#     +-11 deg, flat inner end at r ~97 mm) and the "split" window inside each spoke (tip at r ~92 mm,
#     sides diverging 15 deg each).
#   * at r ~178-197 mm every arm jogs ~12 mm towards its partner: the split window necks down to ~43 mm and the
#     between window opens out to +-14.5 deg -- the angular "kink" that makes the design.
#   * arms carry a soft central ridge (two facets), all window / pocket edges are rolled with a ~3 mm fillet,
#     the face is concave (hub pad ~36 mm behind the lip) and the arms are 27-45 mm deep.

_R_LUG_PCD = 0.06985          # 6 x 139.7 mm
_R_CAP = 0.0425               # centre cap opening
_R_LUG_ANG = [math.radians(90 + 60 * j) for j in range(6)]      # one lug at 12 o'clock
_R_FILLET = 0.0020            # rolled window edges
_R_WIN_OUT = 0.2290           # windows run out under the lip (face level)
_R_BARREL_IN = 0.2195         # inner barrel radius (window end walls slope back to it)
_R_RIDGE = 0.20               # facet slope of the arm ridge (~11 deg)


_R_FACE = pchip(  # concave face: hub pad recessed, arms sweep forward to the lip
    [(0.030, -0.0790), (0.060, -0.0796), (0.088, -0.0794), (0.105, -0.0822), (0.130, -0.0902),
     (0.160, -0.0990), (0.190, -0.1060), (0.2186, -0.1112), (0.2340, -0.1160)])
_R_BACK = pchip([(0.030, -0.0262), (0.086, -0.0262), (0.120, -0.0600), (0.170, -0.0740), (0.2186, -0.0830),
                 (0.2321, -0.0900)])


def _r_bezier(p0, p1, p2, p3, n):
    out = []
    for k in range(n + 1):
        s = k / n
        a, b, c, d = (1 - s) ** 3, 3 * s * (1 - s) ** 2, 3 * s * s * (1 - s), s ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def _r_chaikin(loop, iters=2):
    for _ in range(iters):
        out = []
        n = len(loop)
        for i in range(n):
            a, b = loop[i], loop[(i + 1) % n]
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        loop = out
    return loop


def _r_resample(loop, step):
    """Uniformly resample a closed loop with segments of at most `step`."""
    n = len(loop)
    cum = [0.0]
    for i in range(n):
        a, b = loop[i], loop[(i + 1) % n]
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    L = cum[-1]
    m = max(8, int(math.ceil(L / step)))
    out, j = [], 0
    for k in range(m):
        d = L * k / m
        while cum[j + 1] < d:
            j += 1
        a, b = loop[j], loop[(j + 1) % n]
        f = (d - cum[j]) / max(1e-12, cum[j + 1] - cum[j])
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def _r_side_local(kind):
    """b > 0 side of a window in its own frame (a along the window axis, b across), inner end -> past the rim (m)."""
    pts = []
    if kind == "split":                         # window inside a split spoke
        for k in range(17):
            a = 100.0 + 78.0 * k / 16
            pts.append((a, 12.0 + 0.252 * (a - 100.0)))
        for k in range(1, 7):                   # kink: the arms step towards each other
            f = k / 6
            pts.append((178.0 + 18.0 * f, 31.7 - 11.2 * f))
        for k in range(1, 9):
            a = 196.0 + 44.0 * k / 8
            pts.append((a, 20.5 + 0.06 * (a - 196.0)))
    else:                                       # window between two split spokes, under a lug
        t1, t2 = math.tan(math.radians(9.4)), math.tan(math.radians(14.0))
        for k in range(17):
            a = 97.0 + 81.0 * k / 16
            pts.append((a, a * t1))
        b0 = 178.0 * t1
        for k in range(1, 7):                   # kink: the window opens out
            f = k / 6
            pts.append((178.0 + 19.0 * f, b0 + (197.0 * t2 - b0) * f))
        for k in range(1, 9):
            a = 197.0 + 43.0 * k / 8
            pts.append((a, a * t2))
    return [(a / 1000.0, b / 1000.0) for a, b in pts]


def _r_window(kind, axis):
    """Closed window outline (global face-plane coordinates u = Y, v = Z), rounded corners, ~2 mm segments."""
    side = _r_side_local(kind)
    # clip the side where it reaches the inner barrel
    clip = []
    for p, q in zip(side, side[1:]):
        clip.append(p)
        rp, rq = math.hypot(*p), math.hypot(*q)
        if rp < _R_WIN_OUT <= rq:
            f = (_R_WIN_OUT - rp) / (rq - rp)
            clip.append((p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f))
            break
    end = clip[-1]
    beta = math.atan2(end[1], end[0])
    arc = [(_R_WIN_OUT * math.cos(beta - 2 * beta * k / 10), _R_WIN_OUT * math.sin(beta - 2 * beta * k / 10))
           for k in range(1, 10)]
    left = [(a, -b) for a, b in reversed(clip)]
    a0, b0 = clip[0]
    if kind == "split":
        cap = _r_bezier((a0, -b0), (a0 - 0.010, -b0), (a0 - 0.010, b0), (a0, b0), 8)
    else:
        cap = _r_bezier((a0, -b0), (a0 - 0.0035, -b0 * 0.45), (a0 - 0.0035, b0 * 0.45), (a0, b0), 8)
    loop = clip + arc + left + cap[1:-1]
    loop = _r_resample(_r_chaikin(_r_resample(loop, 0.005), 4), 0.0038)
    ca, sa = math.cos(axis), math.sin(axis)
    return [(a * ca - b * sa, a * sa + b * ca) for a, b in loop]


def _r_offset_loop(loop, d):
    """Offset a closed loop outwards (away from its interior) by d."""
    nrm = _w_loop_normals(loop)
    return [(p[0] + n[0] * d, p[1] + n[1] * d) for p, n in zip(loop, nrm)]


def _r_circle(cx, cy, r, n, a0=0.0):
    return [(cx + r * math.cos(a0 + 2 * math.pi * k / n), cy + r * math.sin(a0 + 2 * math.pi * k / n)) for k in range(n)]


def _r_rot(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def _r_dist_poly(p, poly):
    best = 1e9
    px, py = p
    for (ax, ay), (bx, by) in zip(poly, poly[1:]):
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
        qx, qy = ax + t * dx - px, ay + t * dy - py
        d = qx * qx + qy * qy
        if d < best:
            best = d
    return math.sqrt(best)


class _RimFace:
    """Face of the AT4X wheel: window outlines, arm ridge field and the lifted face surface."""

    def __init__(self):
        lug0 = _R_LUG_ANG[0]
        self.windows = []
        for j in range(6):
            self.windows.append(_r_window("between", lug0 + math.radians(60 * j)))
            self.windows.append(_r_window("split", lug0 + math.radians(30 + 60 * j)))
        # bounding edges of the two arms of the canonical sector (lug at 90 deg, split spoke at 120 deg)
        def side(kind, axis, sgn):
            pts = [(a, sgn * b) for a, b in _r_side_local(kind)]
            pts = [p for p in pts if math.hypot(*p) < _R_WIN_OUT + 0.004]
            return [_r_rot(p, axis) for p in pts]
        L, P = lug0, lug0 + math.radians(30)
        self.arms = [(side("between", L, +1), side("split", P, -1)),                       # arm at ~105 deg
                     (side("split", P, +1), side("between", L + math.radians(60), -1))]    # arm at ~135 deg

    def _canon(self, u, v):
        ang = math.atan2(v, u) - _R_LUG_ANG[0]
        k = math.floor(ang / (math.pi / 3))
        return _r_rot((u, v), -k * math.pi / 3), ang - k * math.pi / 3

    def ridge_offset(self, u, v):
        """(signed distance from the arm ridge, arm half width) at a face point."""
        p, a = self._canon(u, v)
        e1, e2 = self.arms[0] if a < math.pi / 6 else self.arms[1]
        d1, d2 = _r_dist_poly(p, e1), _r_dist_poly(p, e2)
        return (d1 - d2) * 0.5, (d1 + d2) * 0.5

    def crown(self, u, v):
        r = math.hypot(u, v)
        w = smoothstep(0.094, 0.118, r) * (1.0 - smoothstep(0.218, 0.229, r))
        if w <= 0.0:
            return 0.0
        e, _ = self.ridge_offset(u, v)
        c = 0.0012
        return -w * _R_RIDGE * (math.sqrt(e * e + c * c) - c)

    def x(self, u, v):
        r = math.hypot(u, v)
        bezel = 0.0018 * (1.0 - smoothstep(0.0490, 0.0545, r)) if r < 0.0545 else 0.0   # raised ring round the cap
        return _R_FACE(r) - self.crown(u, v) - bezel

    def lift(self, u, v):
        return Vector((self.x(u, v), u, v))

    def ridges(self):
        """Ridge polylines (and +-2.5 mm companions) of all 12 arms, for the face triangulation."""
        lines = []
        for arm_i, (e1, e2) in enumerate(self.arms):
            lo, hi = (math.radians(91), math.radians(119)) if arm_i == 0 else (math.radians(121), math.radians(149))
            mid, side_p, side_m = [], [], []
            r = 0.104
            while r < 0.2235:
                a0, a1 = lo, hi
                for _ in range(30):
                    am = (a0 + a1) / 2
                    p = (r * math.cos(am), r * math.sin(am))
                    if _r_dist_poly(p, e1) < _r_dist_poly(p, e2):
                        a0 = am
                    else:
                        a1 = am
                am = (a0 + a1) / 2
                mid.append((r * math.cos(am), r * math.sin(am)))
                for lst, s in ((side_p, 0.0025), (side_m, -0.0025)):
                    aa = am + s / r
                    lst.append((r * math.cos(aa), r * math.sin(aa)))
                r += 0.0050
            for j in range(6):
                rot = math.radians(60 * j)
                for line in (mid,):
                    lines.append([_r_rot(p, rot) for p in line])
        return lines


def _r_fillet_wall(mb, bone, face, loop, f, x_back, segs=3, mat="rim"):
    """Rolled edge (quarter round of radius f) from the face down into a hole, then the wall to x_back(u, v) (3D).

    loop: the hole outline at the wall; the face is cut at the loop offset outwards by f."""
    nrm = _w_loop_normals(loop)
    n = len(loop)
    rings = []
    for k in range(segs + 1):
        th = 0.5 * math.pi * k / segs
        d, z = f * (1.0 - math.sin(th)), f * (1.0 - math.cos(th))
        ring = []
        for p, nn in zip(loop, nrm):
            q = (p[0] + nn[0] * d, p[1] + nn[1] * d)
            ring.append(face.lift(*q) + Vector((z, 0.0, 0.0)))
        rings.append(ring)
    rings.append([x_back(*p) for p in loop])
    ids = [[mb._vert(p, bone) for p in ring] for ring in rings]
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        th = 0.5 * math.pi * (k + 0.5) / segs if k < segs else 0.5 * math.pi
        for i in range(n):
            j = (i + 1) % n
            nn = ((nrm[i][0] + nrm[j][0]) * 0.5, (nrm[i][1] + nrm[j][1]) * 0.5)
            # outward: towards the viewer (-X) on the face, towards the hole on the wall
            out = Vector((-math.cos(th), -nn[0] * math.sin(th), -nn[1] * math.sin(th)))
            _w_face(mb, [ids[k][i], ids[k][j], ids[k + 1][j], ids[k + 1][i]], [a[i], a[j], b[j], b[i]], out, mat)
    return rings


def _r_spokes_at4x(mb, bone, rim_r):
    """Face of the wheel as one CDT surface cut by the windows, lug pockets and cap opening, with rolled edges,
    deep window walls, lug pockets and a back skin."""
    from surf import panel
    face = _RimFace()
    f = _R_FILLET
    r_face = rim_r + 0.0054          # face meets the lip curl
    lugs = [_r_circle(_R_LUG_PCD * math.cos(a), _R_LUG_PCD * math.sin(a), 0.0150, 28) for a in _R_LUG_ANG]
    f_lug = 0.0018
    cap = _r_circle(0.0, 0.0, _R_CAP, 64)
    outline = _r_circle(0.0, 0.0, r_face, 144)          # same ring as the lip lathe (welded)
    holes = [_r_offset_loop(w, f) for w in face.windows] + [_r_offset_loop(h, f_lug) for h in lugs] + [cap]
    f0 = len(mb.faces)
    rings = [_r_circle(0.0, 0.0, rr, 48) for rr in (0.0475, 0.0505, 0.0530, 0.0560)]
    panel(mb, outline, face.lift, "rim", bone, Vector((-1, 0, 0)), spacing=0.0068, holes=holes,
          creases=face.ridges() + [c + c[:1] for c in rings])
    # drop the slivers the triangulation leaves between collinear points of the densified outer circle
    keep = [k for k in range(f0, len(mb.faces))
            if not all(math.hypot(mb.verts[i].y, mb.verts[i].z) > r_face - 0.0003 for i in mb.faces[k][0])]
    mb.faces[f0:], mb.fixed[f0:] = [mb.faces[k] for k in keep], [mb.fixed[k] for k in keep]

    def back(u, v):
        return _R_BACK(math.hypot(u, v))

    def wall_end(u, v):
        # window walls end on the back of the arms; under the lip they slope out to the inner barrel
        r = math.hypot(u, v)
        x = back(u, v) + (-0.0905 - back(u, v)) * smoothstep(_R_BARREL_IN - 0.010, _R_BARREL_IN, r)
        if r > _R_BARREL_IN:
            return Vector((x, u * _R_BARREL_IN / r, v * _R_BARREL_IN / r))
        return Vector((x, u, v))
    for w in face.windows:
        _r_fillet_wall(mb, bone, face, w, f, wall_end)
    x_seat = _R_FACE(_R_LUG_PCD) + 0.0135
    for h in lugs:
        rings = _r_fillet_wall(mb, bone, face, h, f_lug, lambda u, v: Vector((x_seat, u, v)), segs=2)
        ids = [mb._vert(p, bone) for p in rings[-1]]
        _w_face(mb, ids, rings[-1], Vector((-1, 0, 0)), "rim")
    # cap opening: short wall down to the cap seat
    fr = [face.lift(*p) for p in cap]
    bk = [Vector((_R_FACE(_R_CAP) + 0.012, p[0], p[1])) for p in cap]
    ti = [mb._vert(p, bone) for p in fr]
    bi = [mb._vert(p, bone) for p in bk]
    for i in range(len(cap)):
        j = (i + 1) % len(cap)
        _w_face(mb, [ti[i], ti[j], bi[j], bi[i]], [fr[i], fr[j], bk[j], bk[i]],
                Vector((0.0, -(fr[i].y + fr[j].y), -(fr[i].z + fr[j].z))), "rim")
    # back skin of the spokes (seen through the windows from the chassis side)
    panel(mb, outline, lambda u, v: Vector((back(u, v), u, v)), "rim", bone, Vector((1, 0, 0)), spacing=0.05,
          holes=face.windows + [cap])
    return x_seat


def _r_barrel(mb, bone, rim_r):
    """Outer lip ring + flange curl, bead seats, drop centre and the inner barrel (one closed section)."""
    k = rim_r / 0.2286
    lip = [(0.2340, -0.1160), (0.2372, -0.1180), (0.2405, -0.1194), (0.2436, -0.1200), (0.2456, -0.1195),
           (0.2468, -0.1181), (0.2474, -0.1161), (0.2471, -0.1140), (0.2460, -0.1121), (0.2440, -0.1108),
           (0.2410, -0.1100), (0.2310, -0.1093)]
    # the outer barrel surface is hidden inside the tyre: only the lip, the inner barrel and the back flange show
    body_ = [(0.2310, -0.1093), (0.2290, -0.0950), (0.2295, 0.1080), (0.2442, 0.1104), (0.2474, 0.1160),
             (0.2420, 0.1200), (0.2250, 0.1196), (0.2195, 0.1150), (0.2195, 0.0850), (0.1960, 0.0650),
             (0.1960, 0.0200), (0.2195, -0.0050), (0.2195, -0.0900), (0.2340, -0.1160)]
    mb.lathe([(r * k, x) for r, x in lip], "rim", bone, seg=144)
    mb.lathe([(r * k, x) for r, x in body_], "rim", bone, seg=72)


def _r_lug_nuts(mb, bone, x_seat):
    """GM chrome-capped lug nuts: 22 mm hex (corners softened), chamfered top and a low domed end."""
    n = 18
    prof = []
    for i in range(n):
        ang = (2 * math.pi * i / n) % (math.pi / 3) - math.pi / 6
        prof.append(min(0.0110 / math.cos(ang), 0.0121))
    for a in _R_LUG_ANG:
        with mb.push_ctx(Matrix.Translation((0, _R_LUG_PCD * math.cos(a), _R_LUG_PCD * math.sin(a)))):
            def hex_ring(x, scale):
                return [(x, prof[i] * scale * math.cos(2 * math.pi * i / n + a),
                         prof[i] * scale * math.sin(2 * math.pi * i / n + a)) for i in range(n)]
            mb.loft([hex_ring(x_seat + 0.0010, 0.93), hex_ring(x_seat - 0.0008, 1.0), hex_ring(x_seat - 0.0158, 1.0),
                     hex_ring(x_seat - 0.0172, 0.96), hex_ring(x_seat - 0.0182, 0.88)], "chrome", bone,
                    cap0=False, cap1=True)
            mb.lathe([(0.0092, x_seat - 0.0181), (0.0088, x_seat - 0.0192), (0.0077, x_seat - 0.0204),
                      (0.0058, x_seat - 0.0214), (0.0032, x_seat - 0.0220), (0.0000, x_seat - 0.0222)],
                     "chrome", bone, seg=18)


def _r_cap(mb, bone):
    """Gloss-black GMC centre cap, slightly domed, red GMC emblem with a chrome edge."""
    dx = _R_FACE(_R_CAP) + 0.0868
    prof = [(0.0000, -0.0922), (0.0120, -0.0921), (0.0240, -0.0916), (0.0330, -0.0905), (0.0395, -0.0890),
            (0.0430, -0.0874), (0.0444, -0.0856), (0.0447, -0.0836), (0.0444, -0.0800)]
    mb.lathe([(r, x + dx) for r, x in prof], "gloss_black", bone, seg=48)
    mb.decal((-0.0924 + dx, 0, 0), (-1, 0, 0), (0, 0, 1), 0.066, 0.0170, "badge_gmc", bone)


def _r_valve(mb, bone):
    """TPMS valve stem: nut on the inner barrel under one lug window, metal stem leaning out, black cap."""
    a = _R_LUG_ANG[5]
    ca, sa = math.cos(a), math.sin(a)

    def P(r, x):
        return Vector((x, r * ca, r * sa))
    base, tip = P(_R_BARREL_IN - 0.0005, -0.0872), P(0.2035, -0.1085)
    axis = (tip - base).normalized()
    mb.cylinder(base - axis * 0.002, base + axis * 0.0045, 0.0062, "steel", bone, seg=6)
    mb.cylinder(base + axis * 0.0045, tip - axis * 0.0108, 0.0036, "steel", bone, seg=12, r1=0.0030, caps=False)
    with mb.push_ctx(Matrix.Translation(tip)):
        # black cap: lathe along the stem axis (local X -> axis)
        rot = Vector((1, 0, 0)).rotation_difference(axis).to_matrix().to_4x4()
        with mb.push_ctx(rot):
            mb.lathe([(0.0, -0.0112), (0.0040, -0.0112), (0.0043, -0.0100), (0.0043, -0.0018), (0.0038, -0.0004),
                      (0.0026, 0.0), (0.0, 0.0)], "black", bone, seg=12)


def _r_rotor(mb, bone):
    """Front brake rotor (13.5 in) and hat behind the wheel -- it turns with the wheel, seen through the spokes."""
    mb.lathe([(0.0880, -0.0255), (0.0960, -0.0255), (0.0985, 0.0160), (0.1715, 0.0170), (0.1715, 0.0480),
              (0.1060, 0.0480), (0.0880, 0.0320)], "steel", bone, seg=48, close=True)


def _r_weld(mb, start, tol=2e-5):
    """Merge coincident vertices created since `start` so rolled edges and surfaces shade as one piece (hard
    edges are left to the angle-based sharp edges)."""
    cells, rep = {}, {}
    for i in range(start, len(mb.verts)):
        p = mb.verts[i]
        c = (math.floor(p.x / tol), math.floor(p.y / tol), math.floor(p.z / tol))
        hit = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in cells.get((c[0] + dx, c[1] + dy, c[2] + dz), ()):
                        if mb.vgroup[j] == mb.vgroup[i] and (mb.verts[j] - p).length < tol:
                            hit = j
                            break
                    if hit is not None:
                        break
                if hit is not None:
                    break
        if hit is None:
            cells.setdefault(c, []).append(i)
            rep[i] = i
        else:
            rep[i] = hit
    new_index = {}
    verts, groups = mb.verts[:start], mb.vgroup[:start]
    for i in range(start, len(mb.verts)):
        if rep[i] == i:
            new_index[i] = len(verts)
            verts.append(mb.verts[i])
            groups.append(mb.vgroup[i])
    faces, fixed = [], []
    for (idx, mat, alpha, uvs, uv), fx in zip(mb.faces, mb.fixed):
        nidx = [new_index[rep[i]] if i >= start else i for i in idx]
        if len(set(nidx)) != len(nidx):
            seen, ii, uu = set(), [], []
            for k, v in enumerate(nidx):
                if v not in seen:
                    seen.add(v)
                    ii.append(v)
                    if uv is not None:
                        uu.append(uv[k])
            if len(ii) < 3:
                continue
            nidx, uv = ii, (uu if uv is not None else None)
        if len(nidx) == 3 and nidx[0] >= start:
            a, b, c = (verts[i] for i in nidx)
            if (b - a).cross(c - a).length < 4e-9:
                continue                              # zero-area sliver (spoils the smooth normals)
        faces.append((nidx, mat, alpha, uvs, uv))
        fixed.append(fx)
    mb.verts[:], mb.vgroup[:] = verts, groups
    mb.faces[:], mb.fixed[:] = faces, fixed


def build_rim(mb, bone, style, rim_r, hw):
    if style != "at4x":
        return _r_legacy(mb, bone, style, rim_r, hw)
    _r_barrel(mb, bone, rim_r)
    x_seat = _r_spokes_at4x(mb, bone, rim_r)
    _r_lug_nuts(mb, bone, x_seat)
    _r_cap(mb, bone)
    _r_valve(mb, bone)
    _r_rotor(mb, bone)


def _r_legacy(mb, bone, style, rim_r, hw):
    """Simple placeholder rims for the other (non-factory) wheel styles."""
    x_face = -hw + 0.04
    seg = 48
    mb.lathe([(rim_r + 0.014, x_face - 0.006), (rim_r + 0.022, x_face + 0.002), (rim_r + 0.004, x_face + 0.018),
              (rim_r - 0.006, x_face + 0.05), (rim_r - 0.012, hw - 0.05), (rim_r + 0.012, hw - 0.03)], "rim", bone, seg=seg)
    mb.lathe([(rim_r - 0.014, hw - 0.06), (0.08, hw - 0.07)], "rim_black", bone, seg=24)
    spokes = {"salta": 6, "bead": 6, "steelie": 0, "forged": 10, "denali": 7}.get(style, 6)
    if style == "steelie":
        mb.lathe([(rim_r - 0.01, x_face + 0.03), (0.15, x_face + 0.05), (0.12, x_face + 0.02), (0.06, x_face + 0.02)],
                 "rim", bone, seg=40)
    else:
        for i in range(spokes):
            a = 2 * math.pi * i / spokes
            with mb.push_ctx(Matrix.Rotation(a, 4, "X")):
                w0, w1 = 0.03, 0.04
                mb.loft([[(x_face + 0.012, -w0, 0.075), (x_face + 0.055, -w0, 0.075),
                          (x_face + 0.055, w0, 0.075), (x_face + 0.012, w0, 0.075)],
                         [(x_face + 0.004, -w0, 0.15), (x_face + 0.05, -w0, 0.15),
                          (x_face + 0.05, w0, 0.15), (x_face + 0.004, w0, 0.15)],
                         [(x_face - 0.002, -w1, rim_r - 0.008), (x_face + 0.045, -w1, rim_r - 0.008),
                          (x_face + 0.045, w1, rim_r - 0.008), (x_face - 0.002, w1, rim_r - 0.008)]],
                        "rim", bone)
    if style in ("bead", "salta"):
        mb.lathe([(rim_r + 0.024, x_face - 0.014), (rim_r - 0.014, x_face - 0.014)], "rim_black", bone, seg=seg)
        for i in range(24):
            a = 2 * math.pi * i / 24
            p = ((rim_r + 0.005) * math.cos(a), (rim_r + 0.005) * math.sin(a))
            mb.cylinder((x_face - 0.014, *p), (x_face - 0.024, *p), 0.006, "chrome", bone, seg=6)
    mb.lathe([(0.082, x_face + 0.014), (0.072, x_face - 0.004), (0.0, x_face - 0.004)], "rim", bone, seg=32)
    mb.decal((x_face - 0.006, 0, 0), (-1, 0, 0), (0, 0, 1), 0.10, 0.025, "badge_gmc", bone)
    for i in range(6):
        a = 2 * math.pi * i / 6 + math.pi / 6
        mb.cylinder((x_face + 0.012, 0.105 * math.cos(a), 0.105 * math.sin(a)),
                    (x_face - 0.006, 0.105 * math.cos(a), 0.105 * math.sin(a)), 0.013, "chrome", bone, seg=6)
