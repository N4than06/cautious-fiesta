"""Cab of the AT4X: doors, cab side sheet metal, greenhouse (roof / windshield / pillars / glass), mirrors, running boards."""
import math

from mathutils import Matrix, Vector

from at4x_dims import *  # noqa: F401,F403
from geom import rrect
from surf import densify, panel, pchip, point_in_poly, smoothstep
from ext_common import *  # noqa: F401,F403
from ext_common import _glass_grid, _lifted, _rounded_loop, _wheelhouse


def doors(mb):
    def door(m, y0, y1, bone, front):
        outline = [(y0, ZG_BODY + 0.02), (y0 - 0.03, ZG_BODY), (y1 + 0.03, ZG_BODY), (y1, ZG_BODY + 0.02),
                   (y1, ZG_BELT), (y0, ZG_BELT)]
        side_panel(m, outline, bone, side_x, creases=[crease_line(y0 - 0.005, y1 + 0.005)])
        # belt moulding + window seal
        m.loft([[(side_x(y, ZG_BELT) - 0.003, y, G(ZG_BELT)), (side_x(y, ZG_BELT) - 0.018, y, G(ZG_BELT + 0.012)),
                 (0.935, y, G(ZG_BELT + 0.012)), (0.935, y, G(ZG_BELT - 0.01))] for y in (y0 - 0.004, y1 + 0.004)],
               "gloss_black", bone)
        m.box((0.900, y1 + 0.02, G(ZG_BODY + 0.05)), (0.950, y0 - 0.02, G(ZG_BELT - 0.01)), "trim", bone)
        # handle in a pocket
        hy = y1 + 0.20
        xs = side_x(hy, 1.30)
        m.rbox((xs - 0.012, hy - 0.17, G(1.282)), (xs - 0.004, hy, G(1.328)), 0.012, "gloss_black", bone)
        m.rbox((xs - 0.004, hy - 0.16, G(1.29)), (xs + 0.020, hy - 0.01, G(1.322)), 0.012, "paint", bone)
        if front:
            with _lifted(m, MIRROR_DROP):
                mirror(m, bone)
            m.decal((side_x(y0 - 0.30, 0.86) + 0.004, y0 - 0.30, G(0.86)), (1, 0, 0), (0, 0, 1), 0.27, 0.068,
                    "badge_at4x", bone)

    def build(m, s):
        door(m, Y_FDOOR_F, Y_FDOOR_R, f"door_{s}side_f", True)
        door(m, Y_RDOOR_F, Y_RDOOR_R, f"door_{s}side_r", False)
    build(mb, "p")
    with mb.mirrored():
        build(mb, "d")


def cab_sheetmetal(mb):
    outline = [(Y_RDOOR_R - 0.007, ZG_BODY), (Y_CAB_R, ZG_BODY), (Y_CAB_R, ZG_BELT), (Y_RDOOR_R - 0.007, ZG_BELT)]
    mirror_side(mb, lambda m: side_panel(m, outline, "chassis", side_x,
                                         creases=[crease_line(Y_RDOOR_R - 0.01, Y_CAB_R + 0.005)]))

    # black rocker under the doors (seen behind the running boards)
    def rocker(m):
        m.loft([[(0.86, y, G(0.43)), (0.965, y, G(0.45)), (0.985 + bow(y), y, G(ZG_BODY + 0.01)),
                 (0.86, y, G(ZG_BODY + 0.01))] for y in (Y_FDOOR_F - 0.01, Y_CAB_R)], "plastic", "chassis")
    mirror_side(mb, rocker)


Y_A_BASE = 1.400                       # A-pillar base at the belt (side view)


_CL = pchip([(Y_CAB_R - 0.012, 1.925), (Y_CAB_R + 0.06, 1.968), (Y_CAB_R + 0.30, 1.988), (0.20, 1.993),
             (0.62, 1.986), (Y_WS_TOP - 0.05, 1.968), (Y_WS_TOP + 0.04, 1.936), (Y_WS_TOP + 0.16, 1.862),
             (1.20, 1.742), (1.40, 1.598), (Y_WS, ZG_BELT)])


def gh_side_z(y):
    """Height where the top skin meets the side skin."""
    if y <= Y_ROOF_F:
        return ZG_WS_TOP - 0.006 * smoothstep(Y_CAB_R + 0.12, Y_CAB_R, y)
    if y >= Y_A_BASE:
        return ZG_BELT
    return ZG_BELT + (Y_A_BASE - y) / (Y_A_BASE - Y_ROOF_F) * (ZG_WS_TOP - ZG_BELT)


def gh_hw(y):
    if y <= Y_A_BASE:
        return glass_x(gh_side_z(y))
    return glass_x(ZG_BELT) * math.sqrt(max(0.0, (Y_WS - y) / (Y_WS - Y_A_BASE)))


def gh_z(x, y):
    hw = max(gh_hw(y), 1e-4)
    s = min(1.0, abs(x) / hw)
    zs = gh_side_z(y)
    p = 7.0 - 4.6 * smoothstep(Y_WS_TOP - 0.30, Y_WS_TOP + 0.12, y)
    return zs + (_CL(y) - zs) * (1 - s ** p)


def ws_top_y(x):
    return Y_WS_TOP - 0.215 * (abs(x) / 0.74) ** 2


A_PILLAR_W = 0.115                     # visible A-pillar width across the top skin (plan)


FRIT = 0.045                           # black ceramic band round the windshield


def greenhouse(mb):
    y_lo, y_hi = Y_CAB_R - 0.012, Y_WS - 0.001
    ys = [y_lo + (y_hi - y_lo) * k / 90 for k in range(91)]
    outline = [(gh_hw(y), y) for y in ys] + [(-gh_hw(y), y) for y in reversed(ys)]

    def ws_side(y, inset):
        return max(0.0, gh_hw(y) - A_PILLAR_W - inset)

    def base_y(x):
        return Y_WS - (Y_WS - Y_A_BASE) * (abs(x) / glass_x(ZG_BELT)) ** 2

    def ws_outline(inset):
        top = []
        for k in range(41):
            x = -0.80 + 1.60 * k / 40
            y = ws_top_y(x) + inset
            if abs(x) <= ws_side(y, inset):
                top.append((x, y))
        y0, y1 = top[-1][1], Y_A_BASE - 0.05
        right = [(ws_side(y, inset), y) for y in [y0 + (y1 - y0) * k / 24 for k in range(25)]]
        xr = right[-1][0]
        base = [(xr - 2 * xr * k / 30, base_y(xr - 2 * xr * k / 30) - 0.012 - 0.3 * inset) for k in range(31)]
        left = [(-x, y) for x, y in reversed(right)]
        return top + right + base + left, None

    glass, _ = ws_outline(FRIT)
    frit, _ = ws_outline(0.0)

    def region(x, y):
        if point_in_poly((x, y), glass):
            return "glass", "windscreen"
        if point_in_poly((x, y), frit):
            return "gloss_black", "chassis"
        return "paint", "chassis"
    lift = lambda x, y: Vector((x, y, G(gh_z(x, y))))
    panel(mb, outline, lift, "paint", "chassis", out=(0, 0.3, 1), spacing=0.035,
          creases=[glass + glass[:1], frit + frit[:1]], regions=region,
          flange=(0.05, lambda p: Vector((-0.6 * (1 if p.x > 0 else -1), 0, -1)).normalized()))
    # inner face of the windshield
    panel(mb, glass, lambda x, y: lift(x, y) - Vector((0, 0.003, 0.005)), "glass_in", "windscreen", out=(0, -0.3, -1),
          spacing=0.08)
    # drip moulding along the roof side
    mirror_side(mb, lambda m: m.tube([(glass_x(gh_side_z(y)) + 0.004, y, G(gh_side_z(y) + 0.004))
                                      for y in (Y_CAB_R + 0.03, -0.3, 0.2, Y_ROOF_F, Y_ROOF_F + 0.12)],
                                     0.007, "gloss_black", "chassis", seg=6))
    _side_glass(mb, "p")
    with mb.mirrored():
        _side_glass(mb, "d")
    _back_glass(mb)


def _side_glass(mb, side):
    """Side skin above the belt: door glass, black frames / B-pillar / mirror sail, painted C-pillar and rails."""
    lr = "r" if side == "p" else "l"
    y_split_f = 0.5 * (Y_FDOOR_R + Y_RDOOR_F)
    y_split_r = Y_RDOOR_R - 0.004
    zb, zt = ZG_BELT + 0.015, 1.885

    def fw(d):
        return _rounded_loop([(Y_FDOOR_R + 0.04 - d, zb - d), (1.13 + d, zb - d),
                              (a_pillar_y(1.62) - 0.035 + d, 1.62), (a_pillar_y(zt) - 0.035 + d, zt + d),
                              (Y_FDOOR_R + 0.04 - d, zt + d)], 0.03 + d)

    def rw(d):
        return _rounded_loop([(Y_RDOOR_R + 0.035 - d, zb - d), (Y_RDOOR_F - 0.04 + d, zb - d),
                              (Y_RDOOR_F - 0.04 + d, zt + d), (Y_RDOOR_R + 0.10 - d, zt + d),
                              (Y_RDOOR_R + 0.035 - d, 1.79)], 0.05 + d)
    FW, RW, FWo, RWo = fw(0.0), rw(0.0), fw(0.028), rw(0.028)
    sail = [(1.16, ZG_BELT - 0.01), (Y_A_BASE + 0.01, ZG_BELT - 0.01), (a_pillar_y(1.62) + 0.01, 1.63)]

    def bone(y):
        if y > y_split_f:
            return f"door_{side}side_f"
        if y > y_split_r:
            return f"door_{side}side_r"
        return "chassis"

    def region(y, zg):
        if point_in_poly((y, zg), FW):
            return "glass", f"window_{lr}f"
        if point_in_poly((y, zg), RW):
            return "glass", f"window_{lr}r"
        b = bone(y)
        if point_in_poly((y, zg), FWo) or point_in_poly((y, zg), RWo) or point_in_poly((y, zg), sail):
            return "gloss_black", b
        if Y_RDOOR_F - 0.07 < y < Y_FDOOR_R + 0.07:          # B-pillar applique
            return "gloss_black", b
        return "paint", b

    ys = [Y_ROOF_F - (Y_ROOF_F - Y_CAB_R) * k / 50 for k in range(51)]
    outline = [(Y_CAB_R, ZG_BELT), (Y_A_BASE, ZG_BELT), (Y_ROOF_F, gh_side_z(Y_ROOF_F))] + \
              [(y, gh_side_z(y)) for y in ys[1:]]
    zs = [ZG_BELT + (gh_side_z(Y_CAB_R) - ZG_BELT) * k / 30 for k in range(31)]
    creases = [FW + FW[:1], RW + RW[:1], FWo + FWo[:1], RWo + RWo[:1], sail + sail[:1],
               [(y_split_f, z) for z in zs], [(y_split_r, z) for z in zs],
               [(Y_RDOOR_F - 0.07, z) for z in zs], [(Y_FDOOR_R + 0.07, z) for z in zs]]
    lift = lambda y, zg: Vector((glass_x(zg), y, G(zg)))
    panel(mb, outline, lift, "paint", "chassis", out=(1, 0, 0), spacing=0.03, creases=creases, regions=region)

    def inner(y, zg):
        r = region(y, zg)
        return ("glass_in", r[1]) if r and r[0] == "glass" else None
    panel(mb, outline, lambda y, zg: lift(y, zg) - Vector((0.005, 0, 0)), "glass_in", "chassis", out=(-1, 0, 0),
          spacing=0.03, creases=creases, regions=inner)


def _back_glass(mb):
    def bg(u, v):
        zg = 1.49 + v * (1.875 - 1.49)
        return Vector((u * (0.70 - 0.05 * v), Y_CAB_R - 0.012 - 0.012 * v, G(zg)))
    _glass_grid(mb, bg, "windscreen_r", out=Vector((0, -1, 0)), nu=4, nv=3)
    for u in (-0.24, 0.24):
        mb.box((u - 0.01, Y_CAB_R - 0.03, G(1.49)), (u + 0.01, Y_CAB_R - 0.012, G(1.875)), "gloss_black", "chassis")
    outline = [(-0.985, 0.62), (0.985, 0.62), (0.985, ZG_BELT), (0.86, 1.94), (-0.86, 1.94), (-0.985, ZG_BELT)]
    hole = [(-0.72, 1.48), (0.72, 1.48), (0.67, 1.885), (-0.67, 1.885)]
    panel(mb, outline, lambda x, zg: Vector((x, Y_CAB_R, G(zg))), "paint", "chassis", out=(0, -1, 0), spacing=0.06,
          holes=[hole])
    # CHMSL with integrated bed camera
    mb.rbox((-0.13, Y_CAB_R - 0.035, G(1.925)), (0.13, Y_CAB_R - 0.004, G(1.965)), 0.012, "gloss_black", "chassis")
    mb.box((-0.11, Y_CAB_R - 0.038, G(1.932)), (0.11, Y_CAB_R - 0.034, G(1.958)), "light_red", "chassis", light=11)
    mb.cylinder((0.0, Y_CAB_R - 0.034, G(1.945)), (0.0, Y_CAB_R - 0.042, G(1.945)), 0.008, "black", "chassis", seg=10)


def mirror(mb, bone):
    """Large door mirror (gloss black housing), glass to the rear, turn-signal strip on the leading edge."""
    y_m = Y_FDOOR_F - 0.10
    z_m = 1.60
    mb.loft([[(0.94, y_m + dy, G(z)) for dy, z in ((0.05, 1.45), (-0.07, 1.45), (-0.07, 1.52), (0.05, 1.52))],
             [(1.07, y_m + dy, G(z)) for dy, z in ((0.03, 1.49), (-0.05, 1.49), (-0.05, 1.55), (0.03, 1.55))]],
            "gloss_black", bone)
    rings = []
    for k, x in enumerate((1.04, 1.06, 1.12, 1.20, 1.27, 1.30, 1.305)):
        t = k / 6
        hh = 0.120 + 0.012 * math.sin(math.pi * t) - 0.03 * t * t
        d = 0.085 - 0.03 * t
        sec = rrect(0, 0, d, hh, 0.05, 3)
        rings.append([(x, y_m - 0.065 + dy * (1.0 if dy > 0 else 0.55), G(z_m + dz - 0.012 * t)) for dy, dz in sec])
    mb.loft(rings, "gloss_black", bone)
    mb.decal((1.17, y_m - 0.113, G(z_m - 0.005)), (0, -1, 0), (0, 0, 1), 0.21, 0.215, "chrome", bone)
    mb.box((1.14, y_m + 0.012, G(z_m - 0.125)), (1.29, y_m + 0.022, G(z_m - 0.112)), "light_amber", bone, light=6)


def running_boards(mb):
    """Factory assist steps (misc_a) — black boards with tread strip and three brackets."""
    def board(m):
        y0, y1 = FAX - 0.48, RAX + 0.58
        rings = []
        for y in (y0, y0 - 0.04, y1 + 0.04, y1):
            e = 0.0 if y in (y0, y1) else 1.0
            rings.append([(1.02, y, G(0.405)), (1.02 + 0.14 * e + 0.01, y, G(0.405)), (1.04 + 0.145 * e, y, G(0.43)),
                          (1.03 + 0.145 * e, y, G(0.455)), (1.02, y, G(0.455))])
        m.loft(rings, "gloss_black", "misc_a")
        m.box((1.05, y1 + 0.06, G(0.456)), (1.14, y0 - 0.06, G(0.462)), "plastic", "misc_a")
        for y in (y0 - 0.15, (y0 + y1) / 2, y1 + 0.15):
            m.loft([[(0.52, y - 0.03, G(0.44)), (0.52, y + 0.03, G(0.44)), (0.52, y + 0.03, G(0.50)),
                     (0.52, y - 0.03, G(0.50))],
                    [(1.05, y - 0.025, G(0.41)), (1.05, y + 0.025, G(0.41)), (1.05, y + 0.025, G(0.45)),
                     (1.05, y - 0.025, G(0.45))]], "black", "misc_a")
    mirror_side(mb, board)


def build_cab(mb):
    doors(mb)
    cab_sheetmetal(mb)
    greenhouse(mb)
    running_boards(mb)
