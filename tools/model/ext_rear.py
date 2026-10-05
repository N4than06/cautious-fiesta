"""Rear of the AT4X: bedsides + bed tub, rear arch moulding, MultiPro tailgate, taillamps, rear bumper."""
import math

from mathutils import Matrix, Vector

from at4x_dims import *  # noqa: F401,F403
from geom import rrect
from surf import densify, panel, pchip, point_in_poly, smoothstep
from ext_common import *  # noqa: F401,F403
from ext_common import _glass_grid, _lifted, _rounded_loop, _wheelhouse


def bed_sides(mb):
    def x_fn(y, zg):
        x = side_x(y, zg) + arch_swell(y, zg, RAX, REAR_ARCH)
        x -= 0.014 * smoothstep(ZG_RAIL - 0.035, ZG_RAIL, zg)
        return x
    y_tl = Y_BED_R + 0.050                   # front edge of the taillamp pocket
    arch = arch_outline(RAX, REAR_ARCH)
    outline = [(Y_BED_F, 0.62), (Y_BED_F, ZG_RAIL), (y_tl, ZG_RAIL), (y_tl, TL_Z0), (Y_BED_R, TL_Z0),
               (Y_BED_R, 0.62)] + list(reversed(arch))
    creases = [crease_line(Y_BED_F - 0.005, y_tl + 0.005)]
    mirror_side(mb, lambda m: side_panel(m, outline, "chassis", x_fn, creases=creases))
    mirror_side(mb, lambda m: _wheelhouse(m, RAX, REAR_ARCH))

    def rail(m):
        y0, y1 = Y_BED_F - 0.002, y_tl
        rings = []
        for k in range(13):
            y = y0 + (y1 - y0) * k / 12
            xo = x_fn(y, ZG_RAIL) - 0.004
            rings.append([(0.83, y, G(ZG_RAIL - 0.02)), (0.83, y, G(ZG_RAIL + 0.010)), (xo - 0.03, y, G(ZG_RAIL + 0.013)),
                          (xo, y, G(ZG_RAIL - 0.002)), (xo - 0.02, y, G(ZG_RAIL - 0.02))])
        m.loft(rings, "paint", "chassis")
    mirror_side(mb, rail)
    # bed tub (spray-in liner): walls, front, floor ribs, wheel tubs
    fl = BED_FLOOR
    mirror_side(mb, lambda m: m.box((0.80, Y_BED_R + 0.02, G(fl)), (0.835, Y_BED_F, G(ZG_RAIL)), "bedliner", "chassis"))
    mb.box((-0.835, Y_BED_F - 0.04, G(fl)), (0.835, Y_BED_F, G(ZG_RAIL)), "bedliner", "chassis")
    mb.box((-0.835, Y_BED_R + 0.02, G(fl - 0.04)), (0.835, Y_BED_F, G(fl)), "bedliner", "chassis")
    for k in range(-6, 7):
        mb.box((k * 0.12 - 0.02, Y_BED_R + 0.03, G(fl)), (k * 0.12 + 0.02, Y_BED_F - 0.04, G(fl + 0.012)), "bedliner",
               "chassis")
    mirror_side(mb, lambda m: m.rbox((0.56, RAX - 0.50, G(fl)), (0.80, RAX + 0.45, G(fl + 0.24)), 0.07, "bedliner",
                                     "chassis"))
    mb.box((-0.99, Y_BED_F + 0.0, G(0.62)), (0.99, Y_BED_F + 0.008, G(ZG_RAIL - 0.01)), "black", "chassis")
    # bed-corner pocket behind the taillamp
    mirror_side(mb, lambda m: m.box((0.83, Y_BED_R - 0.002, G(TL_Z0)), (x_fn(Y_BED_R, 1.2) - 0.01, y_tl,
                                                                         G(ZG_RAIL)), "black", "chassis"))
    # fuel door (driver side, behind the cab)
    with mb.mirrored():
        y = -1.08
        mb.rbox((x_fn(y, 1.27) - 0.003, y - 0.10, G(1.19)), (x_fn(y, 1.27) + 0.003, y + 0.10, G(1.35)), 0.03,
                "paint", "petrolcap")


def tailgate(mb):
    """MultiPro tailgate: outer gate (boot), rounded inner gate (misc_j) with GMC letters, SIERRA ledge, AT4X badge."""
    def gy(x, zg):
        ledge = 0.012 * smoothstep(1.135, 1.115, zg)          # lower section steps back slightly
        return Y_BED_R - 0.006 - 0.014 * (1 - (x / 0.82) ** 2) - 0.004 * (zg - 0.93) + ledge
    tg_top = 1.435      # authored at the original rail height; build_exterior lifts the rear end
    outer = [(-0.818, 0.93), (0.818, 0.93), (0.818, tg_top), (-0.818, tg_top)]
    ig = rrect(0, 0, 0.605, (tg_top - 1.15) / 2 + 0.02, 0.07, 4)
    inner_outline = [(x, z + (tg_top + 1.15) / 2 - 0.02) for x, z in ig]
    inner_outline = [(x, min(z, tg_top)) for x, z in inner_outline]
    panel(mb, outer, lambda x, zg: Vector((x, gy(x, zg), G(zg))), "paint", "boot", out=(0, -1, 0), spacing=0.028,
          holes=[inner_outline], creases=[[(-0.80, 1.125), (0.80, 1.125)]], flange=(0.045, lambda p: Vector((0, 1, 0))))
    shrink = [(x * 0.994, 1.15 + (z - 1.15) * 0.99) for x, z in inner_outline]
    panel(mb, shrink, lambda x, zg: Vector((x, gy(x, zg) + 0.004, G(zg))), "paint", "misc_j", out=(0, -1, 0),
          spacing=0.028, flange=(0.04, lambda p: Vector((0, 1, 0))))
    # top cap with the release handle
    mb.loft([[(x, Y_BED_R + 0.0, G(tg_top)), (x, Y_BED_R - 0.03, G(tg_top + 0.016)), (x, Y_BED_R - 0.06, G(tg_top)),
              (x, Y_BED_R - 0.06, G(tg_top - 0.01)), (x, Y_BED_R + 0.0, G(tg_top - 0.015))] for x in (-0.818, 0.818)],
            "plastic", "boot")
    mb.rbox((-0.12, gy(0, 1.38) - 0.012, G(1.36)), (0.12, gy(0, 1.38) + 0.004, G(1.405)), 0.01, "gloss_black", "misc_j")
    mb.box((-0.80, Y_BED_R - 0.002, G(0.95)), (0.80, Y_BED_R + 0.015, G(tg_top - 0.01)), "plastic", "boot")
    # badges
    mb.decal((0, gy(0, 1.27) - 0.002, G(1.27)), (0, -1, 0), (0, 0, 1), 0.52, 0.13, "badge_gmc", "misc_j")
    mb.decal((0, gy(0, 1.07) - 0.003, G(1.07)), (0, -1, 0), (0, 0, 1), 0.42, 0.052, "badge_sierra", "boot")
    mb.decal((0.56, gy(0.56, 0.975) - 0.003, G(0.975)), (0, -1, 0), (0, 0, 1), 0.24, 0.06, "badge_at4x", "boot")


def taillamps(mb):
    def lamp(m, tail, brake, ind, rev):
        y = Y_BED_R
        z0, z1 = 0.975, 1.44
        x0 = 0.832

        def xo(zg):
            return side_x(y + 0.03, zg) - 0.012
        # outer lens: rear face + 5 cm wrap onto the side, rounded top-outer corner
        rings = []
        for k in range(11):
            zg = z0 + k * (z1 - z0) / 10
            cut = 0.035 * smoothstep(z1 - 0.06, z1, zg)
            xx = xo(zg) - cut
            rings.append([(x0, y - 0.004, G(zg)), (xx - 0.04, y - 0.016, G(zg)), (xx - 0.004, y - 0.004, G(zg)),
                          (xx, y + 0.02, G(zg)), (xx - 0.002, y + 0.052, G(zg)), (xx - 0.05, y + 0.052, G(zg)),
                          (x0, y + 0.03, G(zg))])
        m.loft(rings, "light_red", "chassis", light=tail)
        yi = y - 0.018
        # black inner housing with horizontal slats
        m.box((0.85, yi + 0.006, G(z0 + 0.02)), (xo(1.2) - 0.03, yi + 0.012, G(z1 - 0.02)), "black", "chassis")
        for k in range(7):
            z = 1.04 + k * 0.05
            m.box((0.885, yi - 0.004, G(z)), (xo(z) - 0.035, yi + 0.006, G(z + 0.012)), "light_red", "chassis",
                  light=brake)
        # C-shaped LED signature (inner vertical bar with top and bottom returns)
        m.box((0.852, yi - 0.006, G(1.00)), (0.872, yi + 0.006, G(1.41)), "light_led", "chassis", light=tail)
        m.box((0.852, yi - 0.006, G(1.395)), (xo(1.40) - 0.03, yi + 0.006, G(1.415)), "light_led", "chassis", light=tail)
        m.box((0.852, yi - 0.006, G(0.995)), (xo(1.0) - 0.04, yi + 0.006, G(1.015)), "light_led", "chassis", light=tail)
        # amber/turn and clear reverse sections
        m.box((0.93, yi - 0.005, G(1.33)), (xo(1.35) - 0.035, yi + 0.006, G(1.385)), "light_amber", "chassis", light=ind)
        m.box((0.885, yi - 0.005, G(1.15)), (0.93, yi + 0.006, G(1.24)), "light_clear", "chassis", light=rev)
    lamp(mb, 4, 10, 8, 13)
    with mb.mirrored():
        lamp(mb, 3, 9, 7, 12)


def rear_bumper(mb):
    """Rear bumper (bumper_r): sculpted ends with large corner-step openings, ribbed step pad, plate box, hitch."""
    b = "bumper_r"
    xs = [-1.0, -0.99, -0.96, -0.90, -0.80, -0.60, -0.30, 0.0, 0.30, 0.60, 0.80, 0.90, 0.96, 0.99, 1.0]

    def yrear(x):
        ax = abs(x)
        return REAR + 0.012 * (ax / 0.8) ** 2 + 0.20 * smoothstep(0.80, 1.0, ax) ** 1.7

    sec = [(0.22, 0.815), (0.06, 0.815), (0.03, 0.805), (0.0, 0.78), (-0.006, 0.70), (0.0, 0.60), (0.025, 0.565),
           (0.22, 0.565)]
    mb.loft([[(x, yrear(x) + dy, G(z)) for dy, z in sec] for x in xs], "paint", b)
    # ribbed step pad across the top
    for k in range(12):
        y = REAR + 0.04 + k * 0.012
        mb.box((-0.78, y, G(0.815)), (0.78, y + 0.006, G(0.822)), "plastic", b)
    # corner steps: big openings in the bumper ends with a step tread inside
    def step(m):
        x0, x1 = 0.80, 0.97
        m.rbox((x0, REAR + 0.02, G(0.60)), (x1, REAR + 0.20, G(0.715)), 0.03, "black", b)
        m.box((x0 + 0.01, REAR + 0.04, G(0.60)), (x1 - 0.01, REAR + 0.19, G(0.612)), "plastic", b)
        # rim around the opening
        m.tube([(x0, yrear(x0) - 0.002, G(0.60)), (x1, yrear(x1) - 0.002, G(0.60)), (x1, yrear(x1) - 0.002, G(0.715)),
                (x0, yrear(x0) - 0.002, G(0.715)), (x0, yrear(x0) - 0.002, G(0.60))], 0.008, "gloss_black", b, seg=6)
    mirror_side(mb, step)
    # lower black valance
    low = [(0.24, 0.565), (0.03, 0.565), (0.04, 0.49), (0.08, 0.46), (0.24, 0.46)]
    mb.loft([[(x * 0.985, yrear(x) + dy, G(z)) for dy, z in low] for x in xs[1:-1]], "plastic", b)
    # licence plate box with lamps
    mb.rbox((-0.18, REAR - 0.004, G(0.615)), (0.18, REAR + 0.03, G(0.785)), 0.012, "black", b)
    mb.decal((0, REAR - 0.006, G(0.70)), (0, -1, 0), (0, 0, 1), 0.305, 0.152, "plate", b)
    # receiver hitch and sensors
    mb.box((-0.045, REAR - 0.04, G(0.43)), (0.045, REAR + 0.25, G(0.52)), "steel", b)
    mb.box((-0.031, REAR - 0.042, G(0.444)), (0.031, REAR - 0.035, G(0.506)), "black", b)
    for x in (-0.52, -0.2, 0.2, 0.52):
        mb.cylinder((x, yrear(x) - 0.006, G(0.735)), (x, yrear(x) + 0.004, G(0.735)), 0.011, "paint", b, seg=10)


def rear_flares(mb):
    mirror_side(mb, lambda m: arch_flare(m, RAX, REAR_ARCH,
                                         lambda y, z: side_x(y, z) + arch_swell(y, z, RAX, REAR_ARCH)))


def build_rear(mb):
    bed_sides(mb)
    rear_flares(mb)
    with _lifted(mb, REAR_LIFT):
        tailgate(mb)
        taillamps(mb)
        rear_bumper(mb)
