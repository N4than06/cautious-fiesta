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
        dict(name="exhaust", pos=(-0.60, -2.92, G(0.40)), parent="chassis", rot=Matrix.Rotation(math.pi, 3, "Z")),
        dict(name="exhaust_2", pos=(0.60, -2.92, G(0.40)), parent="chassis", rot=Matrix.Rotation(math.pi, 3, "Z")),
        dict(name="headlight_l", pos=(-0.80, 2.80, G(1.23)), parent="chassis"),
        dict(name="headlight_r", pos=(0.80, 2.80, G(1.23)), parent="chassis"),
        dict(name="indicator_lf", pos=(-0.95, 2.76, G(1.22)), parent="chassis"),
        dict(name="indicator_rf", pos=(0.95, 2.76, G(1.22)), parent="chassis"),
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


def interior(mb):
    """Cabin shell parts that follow the cab layout directly (floor, headliner, back wall trim)."""
    mb.box((-0.90, Y_CAB_R + 0.02, G(0.62)), (0.90, Y_WS - 0.04, G(0.66)), "carpet", "chassis")
    mb.box((-0.84, Y_CAB_R + 0.03, G(1.935)), (0.84, Y_ROOF_F, G(1.95)), "carpet", "chassis")
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
                    c1 = side_off * 3.3
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
