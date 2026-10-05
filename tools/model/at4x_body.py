"""Factory-master 2022 GMC Sierra 1500 AT4X (crew cab, 5'8" box), built at 1:1 scale.

Space: metres, origin at the centre of the truck, +Y forward, +X passenger side, +Z up. Heights in this file are
written above ground ("zg") and converted with G(zg).

Reference figures (2022 AT4X crew cab short box): overall length 232.9 in (5.916 m), wheelbase 147.5 in (3.747 m),
width 81.24 in (2.063 m), height 78.35 in (1.990 m), ground clearance 11.1 in, approach 25.5 deg,
departure 23 deg, tyres LT275/70R18 (0.842 m diameter).
"""
import math

from mathutils import Matrix, Vector

from geom import MeshBuilder, arc, rrect
from surf import panel, pchip, smoothstep, densify

# ---------------------------------------------------------------------------------------------- layout

GROUND = -0.80
FRONT, REAR = 2.958, -2.958
FAX, RAX = 1.988, -1.759
TRACK = 0.873
TIRE_R = 0.4211
TIRE_W = 0.275
RIM_R = 0.2286
WC = TIRE_R                     # wheel centre height above ground
WZ = GROUND + WC

# side-view stations
Y_FENDER_F = 2.745              # front end of the fender (behind headlamp)
Y_HOOD_F, Y_HOOD_R = 2.785, 1.300
Y_WS = 1.255                    # windshield base
Y_FDOOR_F, Y_FDOOR_R = 1.198, 0.180
Y_RDOOR_F, Y_RDOOR_R = 0.168, -0.795
Y_CAB_R = -0.945
Y_BED_F, Y_BED_R = -0.960, -2.797
Y_ROOF_F = 0.445

# heights above ground
ZG_BODY = 0.58                  # lower edge of doors / fenders
ZG_CREASE = 1.165               # shoulder character line
ZG_BELT = 1.448                 # beltline
ZG_RAIL = 1.425                 # bed rail
ZG_ROOF = 1.990

# wheel openings (squared superellipse) and the stamped arch "flare" around them
ARCH_A, ARCH_B, ARCH_N = 0.552, 0.525, 3.4
FLARE_PAD, FLARE_RAMP, FLARE_OUT = 0.080, 0.020, 0.024


def G(zg):
    return GROUND + zg


def hood_line(y):
    """Hood surface height at the centreline, above ground."""
    t = (Y_HOOD_F - y) / (Y_HOOD_F - Y_HOOD_R)
    return 1.338 + 0.108 * max(0.0, min(1.0, t))


# ---------------------------------------------------------------------------------------------- side surface

_S_LOW = pchip([(0.40, 0.940), (0.50, 0.958), (0.58, 0.990), (0.66, 1.001), (0.80, 1.005), (1.00, 1.007),
                (ZG_CREASE, 1.0125)])
_S_HIGH = pchip([(ZG_CREASE, 1.0125), (1.185, 1.0035), (1.28, 0.9995), (1.38, 0.992), (1.43, 0.982),
                 (1.47, 0.962)])


def side_base(zg):
    return _S_LOW(zg) if zg <= ZG_CREASE else _S_HIGH(zg)


def front_taper(y):
    return 0.075 * smoothstep(2.48, Y_FENDER_F + 0.01, y) ** 2


def _se_radius(y, zg, cy, a, b):
    dy = abs(y - cy) / a
    if zg <= WC:
        return dy
    dz = (zg - WC) / b
    return (dy ** ARCH_N + dz ** ARCH_N) ** (1.0 / ARCH_N)


def flare(y, zg, cy):
    """Stamped squared arch bulge around a wheel opening."""
    a, b = ARCH_A + FLARE_PAD, ARCH_B + FLARE_PAD
    r = _se_radius(y, zg, cy, a, b)
    ramp = FLARE_RAMP / a
    return FLARE_OUT * (1.0 - smoothstep(1.0, 1.0 + ramp, r))


def arch_outline(cy, z_front, z_rear, a=ARCH_A, b=ARCH_B, seg=44):
    """Wheel opening from the front foot, over the top, to the rear foot (y, zg)."""
    pts = [(cy + a, z_front)]
    for k in range(seg + 1):
        t = math.pi * k / seg
        c, s = math.cos(t), math.sin(t)
        y = cy + a * math.copysign(abs(c) ** (2 / ARCH_N), c)
        z = WC + b * abs(s) ** (2 / ARCH_N)
        pts.append((y, z))
    pts.append((cy - a, z_rear))
    return pts


def flare_creases(cy, z_lo):
    out = []
    for pad in (FLARE_PAD, FLARE_PAD + FLARE_RAMP):
        a, b = ARCH_A + pad, ARCH_B + pad
        pts = arch_outline(cy, z_lo, z_lo, a, b, seg=48)
        out.append(pts)
    return out


IN_X = Vector((-1, 0, 0))


def side_panel(mb, outline, bone, x_fn, holes=(), creases=(), flange=0.028, mat="paint", spacing=0.028):
    def lift(y, zg):
        return Vector((x_fn(y, zg), y, G(zg)))
    panel(mb, outline, lift, mat, bone, out=(1, 0, 0), spacing=spacing, holes=holes, creases=creases,
          flange=(flange, lambda p: IN_X))


def mirror_side(mb, fn):
    fn(mb)
    with mb.mirrored():
        fn(mb)


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
        dict(name="window_lf", pos=(-0.92, 0.66, G(1.70)), parent="door_dside_f"),
        dict(name="window_rf", pos=(0.92, 0.66, G(1.70)), parent="door_pside_f"),
        dict(name="window_lr", pos=(-0.92, -0.32, G(1.70)), parent="door_dside_r"),
        dict(name="window_rr", pos=(0.92, -0.32, G(1.70)), parent="door_pside_r"),
        dict(name="windscreen", pos=(0, 0.86, G(1.70)), parent="chassis"),
        dict(name="windscreen_r", pos=(0, Y_CAB_R, G(1.68)), parent="chassis"),
        dict(name="bonnet", pos=(0, Y_HOOD_R + 0.02, G(1.43)), parent="chassis", limit_rot=((0, 0, 0), (1.0, 0, 0))),
        dict(name="boot", pos=(0, Y_BED_R - 0.01, G(0.955)), parent="chassis", limit_rot=((0, 0, 0), (1.57, 0, 0))),
        dict(name="bumper_f", pos=(0, 2.86, G(0.62)), parent="chassis"),
        dict(name="bumper_r", pos=(0, -2.88, G(0.62)), parent="chassis"),
        dict(name="steeringwheel", pos=(-0.42, 0.80, G(1.30)), parent="chassis",
             rot=Matrix.Rotation(math.radians(-24), 3, "X")),
        dict(name="seat_dside_f", pos=(-0.42, 0.24, G(0.86)), parent="chassis"),
        dict(name="seat_pside_f", pos=(0.42, 0.24, G(0.86)), parent="chassis"),
        dict(name="seat_dside_r", pos=(-0.42, -0.56, G(0.88)), parent="chassis"),
        dict(name="seat_pside_r", pos=(0.42, -0.56, G(0.88)), parent="chassis"),
        dict(name="engine", pos=(0, 1.95, G(1.05)), parent="chassis"),
        dict(name="overheat", pos=(0, 2.10, G(1.30)), parent="chassis"),
        dict(name="petrolcap", pos=(-1.0, -1.30, G(1.27)), parent="chassis"),
        dict(name="petroltank", pos=(0.55, -1.25, G(0.45)), parent="chassis"),
        dict(name="exhaust", pos=(-0.60, -2.92, G(0.40)), parent="chassis", rot=Matrix.Rotation(math.pi, 3, "Z")),
        dict(name="exhaust_2", pos=(0.60, -2.92, G(0.40)), parent="chassis", rot=Matrix.Rotation(math.pi, 3, "Z")),
        dict(name="headlight_l", pos=(-0.80, 2.80, G(1.23)), parent="chassis"),
        dict(name="headlight_r", pos=(0.80, 2.80, G(1.23)), parent="chassis"),
        dict(name="indicator_lf", pos=(-0.95, 2.76, G(1.22)), parent="chassis"),
        dict(name="indicator_rf", pos=(0.95, 2.76, G(1.22)), parent="chassis"),
        dict(name="taillight_l", pos=(-0.92, Y_BED_R - 0.02, G(1.32)), parent="chassis"),
        dict(name="taillight_r", pos=(0.92, Y_BED_R - 0.02, G(1.32)), parent="chassis"),
        dict(name="brakelight_l", pos=(-0.92, Y_BED_R - 0.02, G(1.25)), parent="chassis"),
        dict(name="brakelight_r", pos=(0.92, Y_BED_R - 0.02, G(1.25)), parent="chassis"),
        dict(name="brakelight_m", pos=(0, Y_CAB_R - 0.01, G(1.95)), parent="chassis"),
        dict(name="indicator_lr", pos=(-0.92, Y_BED_R - 0.02, G(1.15)), parent="chassis"),
        dict(name="indicator_rr", pos=(0.92, Y_BED_R - 0.02, G(1.15)), parent="chassis"),
        dict(name="reversinglight_l", pos=(-0.92, Y_BED_R - 0.02, G(1.05)), parent="chassis"),
        dict(name="reversinglight_r", pos=(0.92, Y_BED_R - 0.02, G(1.05)), parent="chassis"),
        dict(name="platelight", pos=(0, -2.93, G(0.78)), parent="chassis"),
        dict(name="interiorlight", pos=(0, -0.10, G(1.92)), parent="chassis"),
        dict(name="dashglow", pos=(-0.42, 1.02, G(1.40)), parent="chassis"),
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


# ---------------------------------------------------------------------------------------------- side sheet metal

def front_fender(mb):
    top = lambda y: hood_line(min(y, Y_HOOD_F)) - 0.034

    def x_fn(y, zg):
        x = side_base(zg) - front_taper(y) + flare(y, zg, FAX)
        t = top(max(y, Y_HOOD_R))
        x -= 0.050 * smoothstep(t - 0.075, t, zg) ** 1.5      # roll into the hood gutter
        return x

    arch = arch_outline(FAX, 0.80, ZG_BODY)
    outline = [(Y_FDOOR_F + 0.006, ZG_BODY)] + list(reversed(arch))
    outline += [(Y_FENDER_F, 0.80)]
    tops = [Y_FENDER_F - k * (Y_FENDER_F - Y_HOOD_R) / 24 for k in range(25)]
    outline += [(y, top(y)) for y in tops]
    outline += [(Y_FDOOR_F + 0.006, 1.452)]
    creases = [[(Y_FDOOR_F + 0.01, ZG_CREASE), (Y_FENDER_F - 0.01, ZG_CREASE)]] + flare_creases(FAX, 0.80)
    mirror_side(mb, lambda m: side_panel(m, outline, "chassis", x_fn, creases=creases))
    # inner arch lip / wheelhouse liner
    mirror_side(mb, lambda m: _wheelhouse(m, FAX, 0.80, ZG_BODY))


def _wheelhouse(mb, cy, z_front, z_rear):
    pts = arch_outline(cy, z_front, z_rear, ARCH_A - 0.01, ARCH_B - 0.01, seg=30)
    rings = []
    for x in (0.985, 0.62):
        rings.append([(x, y, G(z)) for y, z in pts])
    mb.loft(rings, "black", "chassis", closed=False)


def doors(mb):
    def door(m, y0, y1, bone, front):
        outline = [(y0, ZG_BODY + 0.02), (y0 - 0.03, ZG_BODY), (y1 + 0.03, ZG_BODY), (y1, ZG_BODY + 0.02),
                   (y1, ZG_BELT), (y0, ZG_BELT)]
        x_fn = lambda y, zg: side_base(zg)
        side_panel(m, outline, bone, x_fn, creases=[[(y0 - 0.005, ZG_CREASE), (y1 + 0.005, ZG_CREASE)]])
        # belt moulding + window seal
        m.loft([[(side_base(ZG_BELT) - 0.002, y, G(ZG_BELT)), (side_base(ZG_BELT) - 0.02, y, G(ZG_BELT + 0.012)),
                 (0.94, y, G(ZG_BELT + 0.012)), (0.94, y, G(ZG_BELT - 0.01))] for y in (y0 - 0.004, y1 + 0.004)],
               "gloss_black", bone)
        # inner trim panel (visible when open)
        m.box((0.905, y1 + 0.02, G(ZG_BODY + 0.05)), (0.955, y0 - 0.02, G(ZG_BELT - 0.01)), "trim", bone)
        # handle with pocket
        hy = y1 + 0.20
        m.rbox((side_base(1.30) - 0.004, hy - 0.16, G(1.285)), (side_base(1.30) + 0.020, hy - 0.01, G(1.320)), 0.012,
               "paint", bone)
        m.box((side_base(1.30) - 0.006, hy - 0.15, G(1.280)), (side_base(1.30) - 0.002, hy - 0.02, G(1.325)),
              "gloss_black", bone)
        # window frame (black) around the glass opening
        frame_top = 1.915
        if front:
            path = [(0.962, Y_FDOOR_F - 0.12, G(ZG_BELT + 0.01)), (_glass_x(1.80), _a_pillar_y(1.80) - 0.02, G(1.80)),
                    (_glass_x(frame_top), Y_ROOF_F + 0.02, G(frame_top)), (_glass_x(frame_top), y1 + 0.012, G(frame_top)),
                    (0.962, y1 + 0.012, G(ZG_BELT + 0.01))]
        else:
            path = [(0.962, y0 - 0.012, G(ZG_BELT + 0.01)), (_glass_x(frame_top), y0 - 0.012, G(frame_top)),
                    (_glass_x(frame_top), y1 + 0.012, G(frame_top)), (0.962, y1 + 0.012, G(ZG_BELT + 0.01))]
        m.tube(path, 0.016, "gloss_black", bone, seg=6)
        if front:
            mirror(m, bone)
            m.decal((side_base(0.84) + 0.003, y0 - 0.26, G(0.84)), (1, 0, 0), (0, 0, 1), 0.26, 0.065, "badge_at4x", bone)

    def build(m, l_or_r):
        door(m, Y_FDOOR_F, Y_FDOOR_R, f"door_{l_or_r}side_f", True)
        door(m, Y_RDOOR_F, Y_RDOOR_R, f"door_{l_or_r}side_r", False)
    build(mb, "p")
    with mb.mirrored():
        build(mb, "d")


def cab_sheetmetal(mb):
    # lower C-pillar behind the rear doors
    outline = [(Y_RDOOR_R - 0.007, ZG_BODY), (Y_CAB_R, ZG_BODY), (Y_CAB_R, ZG_BELT), (Y_RDOOR_R - 0.007, ZG_BELT)]
    x_fn = lambda y, zg: side_base(zg)
    mirror_side(mb, lambda m: side_panel(m, outline, "chassis", x_fn,
                                         creases=[[(Y_RDOOR_R - 0.01, ZG_CREASE), (Y_CAB_R + 0.005, ZG_CREASE)]]))

    # upper C-pillar (tumbling inwards to the roof)
    def cpil(m):
        rings = []
        for zg in (ZG_BELT, 1.60, 1.75, 1.90, ZG_ROOF - 0.035):
            x = _glass_x(zg) + 0.012
            rings.append([(x - 0.05, Y_RDOOR_R - 0.004, G(zg)), (x, Y_RDOOR_R - 0.004, G(zg)), (x, Y_CAB_R, G(zg)),
                          (x - 0.05, Y_CAB_R, G(zg))])
        m.loft(rings, "paint", "chassis")
    mirror_side(mb, cpil)
    # rockers (black, with AT4X rocker guards)
    def rocker(m):
        m.loft([[(0.86, y, G(0.45)), (0.985, y, G(0.47)), (0.995, y, G(ZG_BODY + 0.01)), (0.86, y, G(ZG_BODY + 0.01))]
                for y in (Y_FDOOR_F - 0.01, Y_CAB_R)], "plastic", "chassis")
    mirror_side(mb, rocker)
    # B-pillar applique
    def bpil(m):
        m.loft([[(_glass_x(zg) + 0.004, Y_FDOOR_R - 0.006, G(zg)), (_glass_x(zg) + 0.004, Y_RDOOR_F + 0.006, G(zg)),
                 (_glass_x(zg) - 0.04, Y_RDOOR_F + 0.006, G(zg)), (_glass_x(zg) - 0.04, Y_FDOOR_R - 0.006, G(zg))]
                for zg in (ZG_BELT, ZG_ROOF - 0.07)], "gloss_black", "chassis")
    mirror_side(mb, bpil)


def bed_sides(mb):
    def x_fn(y, zg):
        x = side_base(zg) + flare(y, zg, RAX)
        x -= 0.012 * smoothstep(ZG_RAIL - 0.04, ZG_RAIL, zg)
        return x
    arch = arch_outline(RAX, 0.62, 0.62)
    outline = [(Y_BED_F, 0.62)] + [(Y_BED_F, ZG_RAIL)] + [(Y_BED_R + 0.052, ZG_RAIL), (Y_BED_R + 0.052, 0.985),
                                                          (Y_BED_R, 0.985), (Y_BED_R, 0.62)]
    outline += arch
    creases = [[(Y_BED_F - 0.005, ZG_CREASE), (Y_BED_R + 0.055, ZG_CREASE)]] + flare_creases(RAX, 0.62)
    mirror_side(mb, lambda m: side_panel(m, list(reversed(outline)), "chassis", x_fn, creases=creases))
    mirror_side(mb, lambda m: _wheelhouse(m, RAX, 0.62, 0.62))

    # rail cap with black protector
    def rail(m):
        y0, y1 = Y_BED_F - 0.002, Y_BED_R + 0.054
        m.loft([[(0.83, y, G(ZG_RAIL - 0.02)), (0.83, y, G(ZG_RAIL + 0.008)), (0.97, y, G(ZG_RAIL + 0.012)),
                 (side_base(ZG_RAIL) - 0.012, y, G(ZG_RAIL - 0.004)), (side_base(ZG_RAIL) - 0.04, y, G(ZG_RAIL - 0.02))]
                for y in (y0, y1)], "paint", "chassis")
        m.box((0.835, y1, G(ZG_RAIL + 0.008)), (0.96, y0, G(ZG_RAIL + 0.016)), "plastic", "chassis")
    mirror_side(mb, rail)
    # bed box: inner walls, front wall, floor, wheel tubs
    mirror_side(mb, lambda m: m.box((0.80, Y_BED_R + 0.02, G(0.94)), (0.835, Y_BED_F, G(ZG_RAIL)), "bedliner", "chassis"))
    mb.box((-0.835, Y_BED_F - 0.04, G(0.94)), (0.835, Y_BED_F, G(ZG_RAIL)), "bedliner", "chassis")
    mb.box((-0.835, Y_BED_R + 0.02, G(0.90)), (0.835, Y_BED_F, G(0.94)), "bedliner", "chassis")
    for k in range(-6, 7):
        mb.box((k * 0.12 - 0.02, Y_BED_R + 0.03, G(0.94)), (k * 0.12 + 0.02, Y_BED_F - 0.04, G(0.952)), "bedliner",
               "chassis")
    mirror_side(mb, lambda m: m.rbox((0.56, RAX - 0.47, G(0.94)), (0.80, RAX + 0.47, G(1.16)), 0.06, "bedliner", "chassis"))
    # bed-side outer face behind the tail lamps (lower corner) and bed front panel
    mb.box((-0.99, Y_BED_F + 0.0, G(0.62)), (0.99, Y_BED_F + 0.008, G(ZG_RAIL - 0.01)), "black", "chassis")
    # fuel door (driver side)
    with mb.mirrored():
        mb.rbox((side_base(1.27) - 0.002, -1.42, G(1.19)), (side_base(1.27) + 0.003, -1.22, G(1.35)), 0.02, "paint",
                "petrolcap")


# ---------------------------------------------------------------------------------------------- hood / cowl

HOOD_HW_F, HOOD_HW_R = 0.937, 0.918


def hood_z(x, y):
    ax = abs(x)
    t = max(0.0, min(1.0, (Y_HOOD_F - y) / (Y_HOOD_F - Y_HOOD_R)))
    base = hood_line(y)
    crown = 0.014 * (1 - (ax / HOOD_HW_F) ** 2)
    dome = 0.032 * (1 - smoothstep(0.355, 0.415, ax)) * (0.55 + 0.45 * smoothstep(0.0, 0.25, t))
    edge = -0.030 * smoothstep(0.79, HOOD_HW_F, ax) ** 1.4
    nose = -0.045 * smoothstep(Y_HOOD_F - 0.05, Y_HOOD_F, y) ** 2
    return base + crown + dome + edge + nose


def hood(mb):
    hw = lambda y: HOOD_HW_R + (HOOD_HW_F - HOOD_HW_R) * (y - Y_HOOD_R) / (Y_HOOD_F - Y_HOOD_R)
    outline = []
    ys = [Y_HOOD_R + k * (Y_HOOD_F - Y_HOOD_R) / 30 for k in range(31)]
    outline += [(hw(y), y) for y in ys]
    outline += [(-hw(y), y) for y in reversed(ys)]
    creases = []
    for xc in (0.355, 0.415, 0.79):
        for s in (-1, 1):
            creases.append([(s * xc, Y_HOOD_R + 0.01), (s * xc, Y_HOOD_F - 0.01)])

    def lift(x, y):
        return Vector((x, y, G(hood_z(x, y))))
    panel(mb, outline, lift, "paint", "bonnet", out=(0, 0, 1), spacing=0.03, creases=creases,
          flange=(0.035, lambda p: Vector((0, 0, -1))))
    # underside skin / insulation
    panel(mb, outline, lambda x, y: Vector((x, y, G(hood_z(x, y) - 0.04))), "black", "bonnet", out=(0, 0, -1),
          spacing=0.12)


def cowl(mb):
    mb.loft([[(x, Y_WS - 0.01, G(1.445)), (x, Y_HOOD_R - 0.005, G(1.435)), (x, Y_HOOD_R - 0.005, G(1.41)),
              (x, Y_WS - 0.01, G(1.40))] for x in (-0.905, 0.905)], "plastic", "chassis")


# ---------------------------------------------------------------------------------------------- greenhouse

def _glass_x(zg):
    """Side glass plane (tumblehome)."""
    t = (zg - ZG_BELT) / (1.92 - ZG_BELT)
    return 0.966 - 0.106 * t


def _a_pillar_y(zg):
    t = (zg - 1.455) / (1.925 - 1.455)
    return Y_WS - (Y_WS - Y_ROOF_F) * t


def greenhouse(mb):
    # windshield (slightly curved in plan), outer + inner
    def ws_pt(u, v):
        zg = 1.455 + v * (1.925 - 1.455)
        y = _a_pillar_y(zg) + 0.025 * (1 - u * u) * math.sin(math.pi * v) * 0.6 + 0.02 * (1 - u * u)
        hw = 0.905 - 0.095 * v
        return Vector((u * hw, y, G(zg)))
    _glass_grid(mb, ws_pt, "windscreen", out=Vector((0, 1, 0.6)))
    # A-pillars (body colour)
    def apil(m):
        rings = []
        for k in range(7):
            zg = 1.445 + k * (1.93 - 1.445) / 6
            y = _a_pillar_y(zg)
            hw = 0.905 - 0.095 * (zg - 1.455) / 0.47
            rings.append([(hw - 0.005, y + 0.01, G(zg)), (hw + 0.07, y - 0.03, G(zg)), (hw + 0.05, y - 0.11, G(zg)),
                          (hw - 0.02, y - 0.05, G(zg))])
        m.loft(rings, "paint", "chassis")
    mirror_side(mb, apil)
    # roof
    def roof_z(x, y):
        rf = 0.028 * (x / 0.86) ** 2
        f = 0.03 * smoothstep(Y_ROOF_F - 0.10, Y_ROOF_F + 0.02, y) ** 2
        r = 0.03 * smoothstep(Y_CAB_R + 0.10, Y_CAB_R - 0.005, y) ** 2
        return ZG_ROOF - rf - f - r
    hw = lambda y: 0.835 if y < Y_ROOF_F - 0.08 else 0.835 - 0.03 * (y - (Y_ROOF_F - 0.08)) / 0.10
    ys = [Y_CAB_R - 0.005 + k * (Y_ROOF_F + 0.02 - Y_CAB_R + 0.005) / 30 for k in range(31)]
    outline = [(hw(y), y) for y in ys] + [(-hw(y), y) for y in reversed(ys)]
    panel(mb, outline, lambda x, y: Vector((x, y, G(roof_z(x, y)))), "paint", "chassis", out=(0, 0, 1),
          spacing=0.04, flange=(0.06, lambda p: Vector((0.55 * (1 if p.x > 0 else -1), 0, -1)).normalized()))
    # drip mouldings
    mirror_side(mb, lambda m: m.tube([(0.845, Y_ROOF_F - 0.02, G(ZG_ROOF - 0.04)), (0.86, Y_CAB_R + 0.01,
                                                                                   G(ZG_ROOF - 0.045))],
                                     0.009, "gloss_black", "chassis", seg=6))
    # side glass
    def side_glass(m, l_or_r):
        def pane(pts2d, bone):
            def pt(u, v):
                (y0, z0), (y1, z1), (y2, z2), (y3, z3) = pts2d
                yb = y0 + (y1 - y0) * u
                zb = z0 + (z1 - z0) * u
                yt = y3 + (y2 - y3) * u
                zt = z3 + (z2 - z3) * u
                y = yb + (yt - yb) * v
                zg = zb + (zt - zb) * v
                return Vector((_glass_x(zg), y, G(zg)))
            _glass_grid(m, pt, bone, out=Vector((1, 0, 0.1)), nu=4, nv=4, centered=False)
        zt = 1.905
        pane([(Y_FDOOR_F - 0.13, ZG_BELT + 0.01), (Y_FDOOR_R + 0.025, ZG_BELT + 0.01),
              (Y_FDOOR_R + 0.025, zt), (_a_pillar_y(zt) - 0.03, zt)], f"window_{l_or_r}f")
        pane([(Y_RDOOR_F - 0.025, ZG_BELT + 0.01), (Y_RDOOR_R + 0.03, ZG_BELT + 0.01), (Y_RDOOR_R + 0.03, zt),
              (Y_RDOOR_F - 0.025, zt)], f"window_{l_or_r}r")
        # mirror sail (black triangle at the front of the front door glass)
        m.loft([[(0.965, Y_FDOOR_F - 0.02, G(ZG_BELT)), (0.965, Y_FDOOR_F - 0.135, G(ZG_BELT)),
                 (_glass_x(1.62), _a_pillar_y(1.62) - 0.015, G(1.62))],
                [(0.945, Y_FDOOR_F - 0.02, G(ZG_BELT)), (0.945, Y_FDOOR_F - 0.135, G(ZG_BELT)),
                 (_glass_x(1.62) - 0.02, _a_pillar_y(1.62) - 0.015, G(1.62))]], "gloss_black", f"door_{l_or_r}side_f")
    side_glass(mb, "r")
    with mb.mirrored():
        side_glass(mb, "l")
    # back glass with slider frame
    def bg(u, v):
        zg = 1.49 + v * (1.875 - 1.49)
        return Vector((u * (0.70 - 0.05 * v), Y_CAB_R - 0.012 - 0.01 * v, G(zg)))
    _glass_grid(mb, bg, "windscreen_r", out=Vector((0, -1, 0)), nu=4, nv=3)
    for u in (-0.24, 0.24):
        mb.box((u - 0.01, Y_CAB_R - 0.03, G(1.49)), (u + 0.01, Y_CAB_R - 0.012, G(1.875)), "gloss_black", "chassis")
    # cab back panel (body colour) with back-light opening
    outline = [(-0.985, 0.62), (0.985, 0.62), (0.985, ZG_BELT), (0.88, 1.93), (-0.88, 1.93), (-0.985, ZG_BELT)]
    hole = [(-0.72, 1.48), (0.72, 1.48), (0.67, 1.885), (-0.67, 1.885)]
    panel(mb, outline, lambda x, zg: Vector((x, Y_CAB_R, G(zg))), "paint", "chassis", out=(0, -1, 0),
          spacing=0.06, holes=[hole])
    mb.box((-0.12, Y_CAB_R - 0.03, G(1.935)), (0.12, Y_CAB_R - 0.005, G(1.965)), "light_red", "chassis", light=11)
    mb.cylinder((0.0, Y_CAB_R - 0.03, G(1.95)), (0.0, Y_CAB_R - 0.036, G(1.95)), 0.008, "gloss_black", "chassis", seg=10)


def _glass_grid(mb, fn, bone, out, nu=8, nv=6, centered=True):
    """Outer (vehglass) and inner (vehglass_inner) skin from a parametric surface."""
    us = [(-1 + 2 * i / nu) if centered else i / nu for i in range(nu + 1)]
    vs = [j / nv for j in range(nv + 1)]
    grid = [[fn(u, v) for u in us] for v in vs]
    for mat, off, flip in (("glass", 0.0, False), ("glass_in", -0.004, True)):
        ids = [[mb._vert(p + out.normalized() * off, bone) for p in row] for row in grid]
        for j in range(nv):
            for i in range(nu):
                q = [ids[j][i], ids[j][i + 1], ids[j + 1][i + 1], ids[j + 1][i]]
                a, b, c = grid[j][i], grid[j][i + 1], grid[j + 1][i + 1]
                n = (b - a).cross(c - a)
                if (n.dot(out) < 0) != flip:
                    q.reverse()
                mb.face(q, mat, None, fixed=True)


# ---------------------------------------------------------------------------------------------- front end

def _corner_y(x):
    """Plan-view wrap of the fascia corners."""
    return 0.075 * smoothstep(0.86, 1.0, abs(x)) ** 2


def front_end(mb):
    # fascia corner caps (body colour) below the headlamps, outboard of the DRL drop
    def corner(m):
        outline = [(0.655, 0.80), (0.995, 0.80), (0.995, 1.11), (0.655, 1.11)]

        def lift(x, zg):
            return Vector((x - 0.018 * smoothstep(0.93, 0.995, x) ** 2, 2.792 - _corner_y(x) - 0.012 * (1.11 - zg),
                           G(zg)))
        panel(m, outline, lift, "paint", "chassis", out=(0, 1, 0), spacing=0.03,
              flange=(0.03, lambda p: Vector((0, -1, 0))))
    mirror_side(mb, corner)
    # radiator support / headlamp backing
    mb.box((-0.98, 2.62, G(0.78)), (0.98, 2.70, G(1.33)), "black", "chassis")
    headlamps(mb)


def headlamps(mb):
    def lamp(m, lid, ind):
        x0, x1, z0, z1 = 0.612, 0.988, 1.112, 1.318
        # lens surface: proud in the middle, wrapping back at the outer corner
        def lift(x, zg):
            y = 2.795 - _corner_y(x) * 1.1 - 0.012 * ((zg - 1.22) / 0.1) ** 2 + 0.006
            return Vector((x - 0.012 * smoothstep(0.95, x1, x) ** 2, y, G(zg)))
        outline = [(x0, z0), (x1 - 0.03, z0), (x1, z0 + 0.04), (x1, z1 - 0.02), (x1 - 0.02, z1), (x0, z1)]
        panel(m, outline, lift, "glass", "chassis", out=(0, 1, 0), spacing=0.03)
        # housing behind the lens
        m.box((x0, 2.70, G(z0 + 0.005)), (x1 - 0.02, 2.735, G(z1 - 0.005)), "black", "chassis")
        # titanium-rush trim blade across the lamp
        m.box((x0 + 0.02, 2.76, G(1.232)), (x1 - 0.04, 2.775, G(1.248)), "titanium", "chassis")
        # dual LED projectors
        m.box((x0 + 0.01, 2.735, G(z0 + 0.01)), (x1 - 0.03, 2.745, G(1.268)), "reflector", "chassis")
        for x in (0.705, 0.845):
            m.cylinder((x, 2.74, G(1.165)), (x, 2.776, G(1.165)), 0.050, "chrome", "chassis", seg=24)
            m.cylinder((x, 2.776, G(1.165)), (x, 2.783, G(1.165)), 0.036, "light_clear", "chassis", seg=24, light=lid)
            m.cylinder((x, 2.783, G(1.165)), (x, 2.786, G(1.165)), 0.012, "chrome", "chassis", seg=12)
        # upper LED signature bar
        m.box((x0 + 0.01, 2.772, G(1.278)), (x1 - 0.035, 2.786, G(1.296)), "light_led", "chassis", light=lid)
        # high-beam reflector block
        m.box((0.89, 2.745, G(1.15)), (0.96, 2.77, G(1.20)), "reflector", "chassis")
        # amber side marker / indicator wrapping the corner
        m.box((0.935, 2.70, G(1.236)), (0.99, 2.77, G(1.262)), "light_amber", "chassis", light=ind)
        # C-shaped DRL drop beside the grille
        m.box((0.615, 2.778, G(0.86)), (0.642, 2.800, G(1.112)), "light_led", "chassis", light=lid)
        m.box((0.615, 2.778, G(0.84)), (0.735, 2.800, G(0.866)), "light_led", "chassis", light=lid)
        m.box((0.605, 2.70, G(0.83)), (0.652, 2.778, G(1.112)), "gloss_black", "chassis")
    lamp(mb, 2, 6)
    with mb.mirrored():
        lamp(mb, 1, 5)


def grille(mb):
    """AT4X grille (misc_c): bezel that runs out to the lamps and bumper, mesh insert, titanium blades, GMC emblem."""
    b = "misc_c"
    outline = [(-0.645, 0.80), (0.645, 0.80), (0.645, 1.128), (0.612, 1.128), (0.612, 1.318), (-0.612, 1.318),
               (-0.612, 1.128), (-0.645, 1.128)]
    # bezel ring: outer edge at the outline, inner edge 5 cm in, face at y 2.835
    inner = [(-0.585, 0.85), (0.585, 0.85), (0.585, 1.275), (-0.585, 1.275)]
    outer_d = densify(outline, 0.08)
    # build bezel as a front-facing panel with a hole + side walls
    panel(mb, outline, lambda x, zg: Vector((x, 2.836 + 0.004 * (1 - (x / 0.65) ** 2), G(zg))), "gloss_black", b,
          out=(0, 1, 0), spacing=0.035, holes=[inner], flange=(0.10, lambda p: Vector((0, -1, 0))))
    # inner returns of the opening (depth)
    rings = [[(x, 2.836, G(z)) for x, z in inner], [(x * 0.99, 2.78, G(z)) for x, z in inner]]
    mb.loft(rings, "gloss_black", b, cap0=False, cap1=False)
    # mesh insert
    mb.box((-0.585, 2.77, G(0.85)), (0.585, 2.782, G(1.275)), "grille", b)
    # titanium horizontal blades
    for z in (0.93, 1.02, 1.19):
        mb.rbox((-0.58, 2.79, G(z - 0.012)), (0.58, 2.83, G(z + 0.012)), 0.008, "titanium", b)
    # emblem: chrome surround + red lettering decal
    mb.rbox((-0.235, 2.832, G(1.045)), (0.235, 2.852, G(1.165)), 0.02, "chrome", b)
    mb.box((-0.225, 2.852, G(1.053)), (0.225, 2.856, G(1.157)), "gloss_black", b)
    mb.decal((0, 2.8575, G(1.105)), (0, 1, 0), (0, 0, 1), 0.44, 0.11, "badge_gmc", b)
    # top filler to the hood
    mb.box((-0.612, 2.70, G(1.318)), (0.612, 2.84, G(1.33)), "black", b)


def front_bumper(mb):
    """AT4X front bumper (bumper_f): body-colour upper cover, black lower valance, skid, red recovery hooks, fogs."""
    b = "bumper_f"
    xs = [-1.002, -0.99, -0.96, -0.90, -0.80, -0.6, -0.3, 0.0, 0.3, 0.6, 0.80, 0.90, 0.96, 0.99, 1.002]

    def yfront(x):
        ax = abs(x)
        return FRONT - 0.012 * (ax / 0.8) ** 2 - 0.24 * smoothstep(0.80, 1.002, ax) ** 1.6

    # upper cover cross-section (y offset from front, zg)
    up = [(-0.17, 0.80), (-0.02, 0.80), (0.0, 0.775), (0.004, 0.70), (0.0, 0.655), (-0.03, 0.645), (-0.17, 0.645)]
    rings = [[(x, yfront(x) + dy, G(z)) for dy, z in up] for x in xs]
    mb.loft(rings, "paint", b)
    # lower valance (textured black), slightly recessed, tucked up for approach angle
    low = [(-0.25, 0.645), (-0.035, 0.645), (-0.05, 0.56), (-0.08, 0.47), (-0.13, 0.44), (-0.25, 0.44)]
    rings = [[(x * 0.985, yfront(x) + dy, G(z)) for dy, z in low] for x in xs[1:-1]]
    mb.loft(rings, "plastic", b)
    # skid plate (titanium finish)
    mb.loft([[(x, FRONT - 0.07, G(0.50)), (x, FRONT - 0.11, G(0.445)), (x, 2.45, G(0.40)), (x, 2.45, G(0.385)),
              (x, FRONT - 0.12, G(0.43)), (x, FRONT - 0.085, G(0.49))] for x in (-0.55, 0.55)], "alu", "misc_g")
    # recovery-hook pockets and vertical red hooks
    for s in (-1, 1):
        x = s * 0.40
        mb.box((x - 0.065, FRONT - 0.07, G(0.50)), (x + 0.065, FRONT - 0.045, G(0.625)), "black", b)
        mb.tube([(x, FRONT - 0.10, G(0.52)), (x, FRONT - 0.02, G(0.52)), (x, FRONT + 0.01, G(0.565)),
                 (x, FRONT - 0.005, G(0.61))], 0.019, "red", b, seg=10)
    # fog lamps low in the bumper
    for s in (-1, 1):
        x = s * 0.76
        y = yfront(x) - 0.05
        mb.rbox((x - 0.075, y - 0.02, G(0.505)), (x + 0.075, y + 0.008, G(0.56)), 0.02, "gloss_black", b)
        mb.rbox((x - 0.062, y + 0.004, G(0.515)), (x + 0.062, y + 0.012, G(0.55)), 0.015, "light_clear", b,
                light=14 if s < 0 else 15)
    # licence-plate mount area + AT4X badge on the lower valance
    mb.decal((0, yfront(0) - 0.034, G(0.60)), (0, 1, -0.3), (0, 0.3, 1), 0.20, 0.05, "badge_at4x", b)


# ---------------------------------------------------------------------------------------------- rear end

def tailgate(mb):
    """MultiPro tailgate: outer gate (boot) with a separate inner gate panel (misc_j)."""
    def gy(x, zg):
        return Y_BED_R - 0.006 - 0.012 * (1 - (x / 0.82) ** 2) - 0.004 * (zg - 0.95)
    outer = [(-0.818, 0.96), (0.818, 0.96), (0.818, 1.41), (0.648, 1.41), (0.648, 1.168), (-0.648, 1.168),
             (-0.648, 1.41), (-0.818, 1.41)]
    panel(mb, outer, lambda x, zg: Vector((x, gy(x, zg), G(zg))), "paint", "boot", out=(0, -1, 0), spacing=0.03,
          creases=[[(-0.80, 1.07), (0.80, 1.07)]], flange=(0.045, lambda p: Vector((0, 1, 0))))
    inner = [(-0.642, 1.174), (0.642, 1.174), (0.642, 1.41), (-0.642, 1.41)]
    panel(mb, inner, lambda x, zg: Vector((x, gy(x, zg) - 0.002, G(zg))), "paint", "misc_j", out=(0, -1, 0),
          spacing=0.03, flange=(0.04, lambda p: Vector((0, 1, 0))))
    # top cap with black step and centre handle
    mb.loft([[(x, Y_BED_R + 0.0, G(1.41)), (x, Y_BED_R - 0.03, G(1.425)), (x, Y_BED_R - 0.06, G(1.41)),
              (x, Y_BED_R - 0.06, G(1.40)), (x, Y_BED_R + 0.0, G(1.395))] for x in (-0.818, 0.818)], "plastic", "boot")
    mb.rbox((-0.13, gy(0, 1.36) - 0.016, G(1.355)), (0.13, gy(0, 1.36) - 0.004, G(1.39)), 0.008, "gloss_black", "misc_j")
    # inner face of the gate (bed side)
    mb.box((-0.80, Y_BED_R - 0.002, G(0.97)), (0.80, Y_BED_R + 0.015, G(1.40)), "plastic", "boot")
    # badges: GMC on the inner gate, AT4X lower right
    mb.decal((0, gy(0, 1.285) - 0.006, G(1.285)), (0, -1, 0), (0, 0, 1), 0.40, 0.10, "badge_gmc", "misc_j")
    mb.decal((-0.60, gy(0.6, 1.02) - 0.004, G(1.02)), (0, -1, 0), (0, 0, 1), 0.24, 0.06, "badge_at4x", "boot")
    mb.cylinder((0, gy(0, 1.36) - 0.014, G(1.33)), (0, gy(0, 1.36) - 0.022, G(1.33)), 0.009, "gloss_black", "boot",
                seg=10)


def taillamps(mb):
    def lamp(m, tail, brake, ind, rev):
        y = Y_BED_R
        z0, z1 = 0.985, 1.418
        x0, x1 = 0.832, side_base(1.2) - 0.004
        # lens (wraps 5 cm around the corner)
        rings = []
        for k in range(9):
            zg = z0 + k * (z1 - z0) / 8
            xo = side_base(zg) - 0.006
            rings.append([(x0, y - 0.004, G(zg)), (xo - 0.03, y - 0.010, G(zg)), (xo, y + 0.02, G(zg)),
                          (xo - 0.002, y + 0.054, G(zg)), (xo - 0.04, y + 0.054, G(zg)), (x0, y + 0.02, G(zg))])
        m.loft(rings, "light_red", "chassis", light=tail)
        # C-shaped LED signature
        m.box((0.955, y - 0.016, G(1.04)), (0.975, y - 0.008, G(1.37)), "light_led", "chassis", light=brake)
        m.box((0.88, y - 0.016, G(1.355)), (0.975, y - 0.008, G(1.375)), "light_led", "chassis", light=brake)
        m.box((0.88, y - 0.016, G(1.035)), (0.975, y - 0.008, G(1.055)), "light_led", "chassis", light=brake)
        # turn (red, US spec) and reverse sections
        m.box((0.86, y - 0.013, G(1.22)), (0.935, y - 0.008, G(1.33)), "light_red", "chassis", light=ind)
        m.box((0.86, y - 0.013, G(1.08)), (0.935, y - 0.008, G(1.20)), "light_clear", "chassis", light=rev)
    lamp(mb, 4, 10, 8, 13)
    with mb.mirrored():
        lamp(mb, 3, 9, 7, 12)


def rear_bumper(mb):
    """Rear bumper (bumper_r): body-colour top with corner steps, black lower, plate recess, hitch."""
    b = "bumper_r"
    xs = [-1.0, -0.98, -0.94, -0.86, -0.6, -0.25, 0.0, 0.25, 0.6, 0.86, 0.94, 0.98, 1.0]

    def yrear(x):
        ax = abs(x)
        return REAR + 0.01 * (ax / 0.86) ** 2 + 0.17 * smoothstep(0.86, 1.0, ax) ** 1.8

    sec = [(0.20, 0.79), (0.03, 0.79), (0.0, 0.77), (-0.004, 0.66), (0.0, 0.60), (0.02, 0.585), (0.20, 0.585)]
    rings = [[(x, yrear(x) + dy, G(z)) for dy, z in sec] for x in xs]
    mb.loft(rings, "paint", b)
    low = [(0.22, 0.585), (0.025, 0.585), (0.035, 0.50), (0.07, 0.46), (0.22, 0.46)]
    rings = [[(x * 0.985, yrear(x) + dy, G(z)) for dy, z in low] for x in xs[1:-1]]
    mb.loft(rings, "plastic", b)
    # corner steps (black pads)
    for s in (-1, 1):
        mb.box((min(s * 0.80, s * 0.97), REAR + 0.03, G(0.79)), (max(s * 0.80, s * 0.97), REAR + 0.20, G(0.80)),
               "plastic", b)
        mb.box((min(s * 0.82, s * 0.95), REAR - 0.003, G(0.62)), (max(s * 0.82, s * 0.95), REAR + 0.01, G(0.74)),
               "plastic", b)
    # plate recess + plate + lamp
    mb.box((-0.17, REAR - 0.004, G(0.61)), (0.17, REAR + 0.01, G(0.775)), "black", b)
    mb.decal((0, REAR - 0.005, G(0.69)), (0, -1, 0), (0, 0, 1), 0.305, 0.152, "plate", b)
    # receiver hitch, sensors
    mb.box((-0.045, REAR - 0.03, G(0.43)), (0.045, REAR + 0.20, G(0.52)), "steel", b)
    mb.box((-0.030, REAR - 0.032, G(0.445)), (0.030, REAR - 0.025, G(0.505)), "black", b)
    for x in (-0.55, -0.2, 0.2, 0.55):
        mb.cylinder((x, yrear(x) - 0.004, G(0.715)), (x, yrear(x) + 0.004, G(0.715)), 0.011, "paint", b, seg=10)


# ---------------------------------------------------------------------------------------------- mirrors

def mirror(mb, bone):
    """Door mirror: large housing on a sail mount, glass to the rear, turn-signal strip (front door bone)."""
    y_m = Y_FDOOR_F - 0.10
    z_m = 1.60
    # arm
    mb.loft([[(0.95, y_m + dy, G(z)) for dy, z in ((0.04, 1.47), (-0.06, 1.47), (-0.06, 1.53), (0.04, 1.53))],
             [(1.06, y_m + dy, G(z)) for dy, z in ((0.03, 1.50), (-0.05, 1.50), (-0.05, 1.56), (0.03, 1.56))]],
            "gloss_black", bone)
    # housing: loft along X of rounded cross-sections (Y depth, Z height)
    rings = []
    for k, x in enumerate((1.04, 1.07, 1.14, 1.22, 1.275, 1.29)):
        t = k / 5
        hh = 0.115 + 0.01 * math.sin(math.pi * t)
        d = 0.075 - 0.02 * t
        sec = rrect(0, 0, d, hh, 0.045, 3)
        rings.append([(x, y_m - 0.06 + dy * (1.0 if dy > 0 else 0.6), G(z_m + dz)) for dy, dz in sec])
    mb.loft(rings, "gloss_black", bone)
    # glass
    mb.decal((1.165, y_m - 0.112, G(z_m)), (0, -1, 0), (0, 0, 1), 0.20, 0.205, "chrome", bone)
    # turn signal (front lower edge)
    mb.box((1.15, y_m + 0.0, G(z_m - 0.12)), (1.28, y_m + 0.012, G(z_m - 0.108)), "light_amber", bone, light=6)


# ---------------------------------------------------------------------------------------------- engine bay

def engine_bay(mb):
    k = "black"
    mirror_side(mb, lambda m: m.box((0.86, Y_HOOD_R, G(0.78)), (0.92, 2.62, G(1.30)), k, "chassis"))  # aprons
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
    for s in (-1, 1):
        mb.cylinder((s * 0.60, -2.76, G(0.40)), (s * 0.60, -2.93, G(0.40)), 0.05, "chrome", "misc_b", seg=18)
        mb.cylinder((s * 0.60, -2.928, G(0.40)), (s * 0.60, -2.80, G(0.40)), 0.042, "black", "misc_b", seg=18)


def rock_rails(mb):
    """Factory AT4X rocker guards (misc_a)."""
    def r(m):
        y0, y1 = Y_FDOOR_F - 0.04, Y_RDOOR_R + 0.04
        rings = []
        for y in (y0, y0 - 0.05, y1 + 0.05, y1):
            e = 0.0 if y in (y0, y1) else 1.0
            rings.append([(0.93, y, G(0.44)), (0.93 + 0.11 * e + 0.02, y, G(0.43)), (0.95 + 0.12 * e, y, G(0.48)),
                          (0.93 + 0.11 * e, y, G(0.53)), (0.93, y, G(0.53))])
        m.loft(rings, "black", "misc_a")
        for y in (y0 - 0.20, Y_FDOOR_R, Y_RDOOR_R + 0.25):
            m.box((0.55, y - 0.03, G(0.44)), (0.94, y + 0.03, G(0.50)), "black", "misc_a")
    mirror_side(mb, r)


def flares(mb):
    """AT4X has body-colour stamped arches; misc_d carries only the thin black arch liner lips."""
    for cy, zf, zr in ((FAX, 0.80, ZG_BODY), (RAX, 0.62, 0.62)):
        def f(m, cy=cy, zf=zf, zr=zr):
            pts = arch_outline(cy, zf, zr, ARCH_A + 0.004, ARCH_B + 0.004, seg=36)[1:-1]
            rings = [[(x, y, G(z)) for y, z in pts] for x in (side_base(1.0) - 0.004, side_base(1.0) - 0.05)]
            m.loft(rings, "plastic", "misc_d", closed=False)
        mirror_side(mb, f)


def mudflaps(mb):
    def f(m):
        m.box((0.80, FAX - ARCH_A - 0.02, G(0.38)), (0.98, FAX - ARCH_A - 0.008, G(0.62)), "plastic", "chassis")
    mirror_side(mb, f)


# ---------------------------------------------------------------------------------------------- interior

def interior(mb):
    mb.box((-0.90, Y_CAB_R + 0.02, G(0.62)), (0.90, Y_WS - 0.04, G(0.66)), "carpet", "chassis")
    # dashboard: lower, upper pad, binnacle
    mb.loft([[(x, Y_WS - 0.04, G(z)) for x, z in rrect(0, 1.18, 0.90, 0.26, 0.05, 2)],
             [(x, 0.98, G(z)) for x, z in rrect(0, 1.20, 0.90, 0.22, 0.08, 2)],
             [(x, 0.90, G(z)) for x, z in rrect(0, 1.10, 0.86, 0.12, 0.06, 2)]], "trim", "chassis")
    mb.rbox((-0.62, 0.92, G(1.36)), (-0.22, 1.02, G(1.47)), 0.03, "black", "chassis")
    mb.decal((-0.42, 0.918, G(1.405)), (0, -1, 0.15), (0, 0.15, 1), 0.36, 0.10, "dash", "chassis")
    mb.decal((0.0, 0.915, G(1.30)), (0, -1, 0.25), (0, 0.25, 1), 0.33, 0.20, "screen", "chassis")
    mb.box((-0.14, -0.15, G(0.66)), (0.14, 0.95, G(1.02)), "trim", "chassis")          # console
    mb.cylinder((-0.42, 0.98, G(1.22)), (-0.42, 0.82, G(1.29)), 0.04, "black", "chassis", seg=12)
    # headliner
    mb.box((-0.84, Y_CAB_R + 0.03, G(1.935)), (0.84, Y_ROOF_F, G(1.95)), "carpet", "chassis")


def seats(mb):
    b = "misc_h"
    for s in (-1, 1):
        x = 0.42 * s
        mb.rbox((x - 0.26, 0.02, G(0.80)), (x + 0.26, 0.56, G(0.92)), 0.05, "leather", b)
        mb.loft([[(x + dx, 0.03, G(0.92 + dz)) for dx, dz in rrect(0, 0.05, 0.25, 0.05, 0.04, 2)],
                 [(x + dx, -0.09, G(1.55 + dz)) for dx, dz in rrect(0, 0.05, 0.23, 0.05, 0.04, 2)]], "leather", b)
        mb.rbox((x - 0.13, -0.12, G(1.58)), (x + 0.13, -0.04, G(1.76)), 0.035, "leather", b)
        mb.box((x - 0.19, -0.13, G(1.10)), (x + 0.19, -0.115, G(1.12)), "leather_red", b)
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
    front_fender(mb)
    doors(mb)
    cab_sheetmetal(mb)
    bed_sides(mb)
    hood(mb)
    cowl(mb)
    greenhouse(mb)
    front_end(mb)
    grille(mb)
    front_bumper(mb)
    tailgate(mb)
    taillamps(mb)
    rear_bumper(mb)
    engine_bay(mb)
    engine_cover(mb)
    airbox(mb)
    underbody(mb)
    exhaust_tips(mb)
    rock_rails(mb)
    flares(mb)
    interior(mb)
    seats(mb)
    steering_wheel(mb)


# ---------------------------------------------------------------------------------------------- wheel

def build_wheel(mb, bone="wheel_lf", rwl=False, rim_style="at4x", tire_r=TIRE_R, rim_r=RIM_R, width=TIRE_W):
    """Left-front wheel centred on its bone, outer face towards -X: LT275/70R18 M/T on an 18in gloss-black wheel."""
    hw = width / 2
    side = "sidewall_rwl" if rwl else "sidewall"
    seg = 64
    prof_out = [(rim_r + 0.012, -hw + 0.035), (rim_r + 0.04, -hw + 0.012), (rim_r + 0.09, -hw - 0.004),
                (tire_r - 0.07, -hw - 0.010), (tire_r - 0.035, -hw - 0.006), (tire_r - 0.012, -hw + 0.012)]
    mb.lathe(prof_out, side, bone, seg=seg, polar_uv=(rim_r, tire_r, 4))
    mb.lathe([(tire_r - 0.012, -hw + 0.012), (tire_r - 0.006, -hw + 0.04), (tire_r - 0.006, hw - 0.04),
              (tire_r - 0.012, hw - 0.012)], "tire", bone, seg=seg)
    prof_in = [(x_r, -x) for x_r, x in reversed(prof_out)]
    mb.lathe(prof_in, "sidewall", bone, seg=seg)
    # M/T tread: staggered centre blocks, big shoulder blocks, sidewall lugs
    n = 22
    for i in range(n):
        a = 2 * math.pi * i / n
        for sgn, off in ((-1, 0.0), (1, 0.5)):
            aa = a + off * 2 * math.pi / n
            with mb.push_ctx(Matrix.Rotation(aa, 4, "X")):
                # shoulder block
                mb.loft([[(sgn * hw * 0.98, -0.05, tire_r - 0.01), (sgn * hw * 0.98, 0.04, tire_r - 0.01),
                          (sgn * hw * 0.98, 0.04, tire_r + 0.012), (sgn * hw * 0.98, -0.05, tire_r + 0.012)],
                         [(sgn * 0.035, -0.035, tire_r - 0.01), (sgn * 0.035, 0.05, tire_r - 0.01),
                          (sgn * 0.035, 0.05, tire_r + 0.016), (sgn * 0.035, -0.035, tire_r + 0.016)]], "tire", bone)
                # sidewall lug
                mb.box((sgn * hw - (0.012 if sgn > 0 else -0.012) * 0 + (-0.014 if sgn < 0 else -0.004), -0.03,
                        tire_r - 0.075), (sgn * hw + (0.004 if sgn < 0 else 0.014), 0.03, tire_r - 0.02), "tire", bone)
        with mb.push_ctx(Matrix.Rotation(a + math.pi / n, 4, "X")):
            mb.box((-0.025, -0.022, tire_r - 0.006), (0.025, 0.022, tire_r + 0.014), "tire", bone)
    build_rim(mb, bone, rim_style, rim_r, hw)


def build_rim(mb, bone, style, rim_r, hw):
    x_face = -hw + 0.04
    seg = 48
    mb.lathe([(rim_r + 0.014, x_face - 0.006), (rim_r + 0.022, x_face + 0.002), (rim_r + 0.004, x_face + 0.018),
              (rim_r - 0.006, x_face + 0.05), (rim_r - 0.012, hw - 0.05), (rim_r + 0.012, hw - 0.03)], "rim", bone, seg=seg)
    mb.lathe([(rim_r - 0.014, hw - 0.06), (0.08, hw - 0.07)], "rim_black", bone, seg=24)
    spokes = {"at4x": 6, "salta": 6, "bead": 6, "steelie": 0, "forged": 10, "denali": 7}.get(style, 6)
    if style == "steelie":
        mb.lathe([(rim_r - 0.01, x_face + 0.03), (0.15, x_face + 0.05), (0.12, x_face + 0.02), (0.06, x_face + 0.02)],
                 "rim", bone, seg=40)
    else:
        split = style == "at4x"
        for i in range(spokes):
            a = 2 * math.pi * i / spokes
            for side_off in ((-0.026, 0.026) if split else (0.0,)):
                with mb.push_ctx(Matrix.Rotation(a + side_off * 0.0, 4, "X")):
                    w0, w1 = (0.016, 0.022) if split else (0.03, 0.04)
                    c0 = side_off * 0.9
                    c1 = side_off * 2.6
                    mb.loft([[(x_face + 0.012, c0 - w0, 0.075), (x_face + 0.055, c0 - w0, 0.075),
                              (x_face + 0.055, c0 + w0, 0.075), (x_face + 0.012, c0 + w0, 0.075)],
                             [(x_face + 0.004, (c0 + c1) / 2 - w0, 0.15), (x_face + 0.05, (c0 + c1) / 2 - w0, 0.15),
                              (x_face + 0.05, (c0 + c1) / 2 + w0, 0.15), (x_face + 0.004, (c0 + c1) / 2 + w0, 0.15)],
                             [(x_face - 0.002, c1 - w1, rim_r - 0.008), (x_face + 0.045, c1 - w1, rim_r - 0.008),
                              (x_face + 0.045, c1 + w1, rim_r - 0.008), (x_face - 0.002, c1 + w1, rim_r - 0.008)]],
                            "rim", bone)
    if style in ("bead", "salta"):
        mb.lathe([(rim_r + 0.024, x_face - 0.014), (rim_r - 0.014, x_face - 0.014)], "rim_black", bone, seg=seg)
        for i in range(24):
            a = 2 * math.pi * i / 24
            p = ((rim_r + 0.005) * math.cos(a), (rim_r + 0.005) * math.sin(a))
            mb.cylinder((x_face - 0.014, *p), (x_face - 0.024, *p), 0.006, "chrome", bone, seg=6)
    # hub, centre cap, lug nuts
    mb.lathe([(0.082, x_face + 0.014), (0.072, x_face - 0.004), (0.0, x_face - 0.004)], "rim", bone, seg=32)
    mb.decal((x_face - 0.006, 0, 0), (-1, 0, 0), (0, 0, 1), 0.10, 0.025, "badge_gmc", bone)
    for i in range(6):
        a = 2 * math.pi * i / 6 + math.pi / 6
        mb.cylinder((x_face + 0.012, 0.105 * math.cos(a), 0.105 * math.sin(a)),
                    (x_face - 0.006, 0.105 * math.cos(a), 0.105 * math.sin(a)), 0.013, "chrome", bone, seg=6)
