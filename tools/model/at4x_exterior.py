"""Exterior of the factory 2022 GMC Sierra 1500 AT4X, matched to reference photos.

Every visible body panel is a dense curved surface (surf.panel) lifted from an exact outline, so the doors,
fenders and bedside share one continuous side surface with plan-view curvature (at4x_dims.bow), a crisp shoulder
crease and the rear haunch. Trim pieces (lamps, grille bars, bumpers) are lofted solids.
"""
import math

from mathutils import Matrix, Vector

from at4x_dims import *  # noqa: F401,F403
from geom import rrect
from surf import densify, panel, smoothstep

IN_X = Vector((-1, 0, 0))


def mirror_side(mb, fn):
    fn(mb)
    with mb.mirrored():
        fn(mb)


def side_panel(mb, outline, bone, x_fn, holes=(), creases=(), flange=0.028, mat="paint", spacing=0.026):
    def lift(y, zg):
        return Vector((x_fn(y, zg), y, G(zg)))
    panel(mb, outline, lift, mat, bone, out=(1, 0, 0), spacing=spacing, holes=holes, creases=creases,
          flange=(flange, lambda p: IN_X))


def crease_line(y0, y1):
    return [(y0, ZG_CREASE), (y1, ZG_CREASE)]


# ================================================================================================ side sheet metal

def front_fender(mb):
    top = lambda y: hood_line(min(y, Y_HOOD_F)) - 0.032

    def x_fn(y, zg):
        x = side_x(y, zg) + arch_swell(y, zg, FAX, FRONT_ARCH)
        t = top(max(y, Y_HOOD_R))
        x -= 0.055 * smoothstep(t - 0.08, t, zg) ** 1.5
        return x

    arch = arch_outline(FAX, FRONT_ARCH)
    outline = [(Y_FDOOR_F + 0.006, ZG_BODY)] + list(reversed(arch)) + [(Y_FENDER_F, 0.80)]
    tops = [Y_FENDER_F - k * (Y_FENDER_F - Y_HOOD_R) / 26 for k in range(27)]
    outline += [(y, top(y)) for y in tops] + [(Y_FDOOR_F + 0.006, 1.432)]
    creases = [crease_line(Y_FDOOR_F + 0.01, Y_FENDER_F - 0.02)]
    mirror_side(mb, lambda m: side_panel(m, outline, "chassis", x_fn, creases=creases))
    mirror_side(mb, lambda m: _wheelhouse(m, FAX, FRONT_ARCH_EXT))
    # "6.2L V8" fender badge (ahead of the front door, just above the crease)
    mirror_side(mb, lambda m: m.decal((side_x(Y_FDOOR_F + 0.21, 1.25) + 0.004, Y_FDOOR_F + 0.21, G(1.25)),
                                      (1, 0, 0), (0, 0, 1), 0.17, 0.045, "badge_v8", "chassis"))


def _wheelhouse(mb, cy, shape):
    pts = arch_outline(cy, shape, offset=-0.012)
    rings = [[(x, y, G(z)) for y, z in pts] for x in (0.975, 0.60)]
    mb.loft(rings, "black", "chassis", closed=False)


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
        # window frame (black) around the glass
        zt = 1.912
        if front:
            path = [(0.955, Y_FDOOR_F - 0.12, G(ZG_BELT + 0.01)), (glass_x(1.78), a_pillar_y(1.78) - 0.02, G(1.78)),
                    (glass_x(zt), Y_ROOF_F + 0.03, G(zt)), (glass_x(zt), y1 + 0.012, G(zt)),
                    (0.955, y1 + 0.012, G(ZG_BELT + 0.01))]
        else:
            path = [(0.955, y0 - 0.012, G(ZG_BELT + 0.01)), (glass_x(zt), y0 - 0.012, G(zt)),
                    (glass_x(zt), y1 + 0.075, G(zt)), (glass_x(zt - 0.03), y1 + 0.022, G(zt - 0.035)),
                    (glass_x(1.80), y1 + 0.012, G(1.80)), (0.955, y1 + 0.012, G(ZG_BELT + 0.01))]
        m.tube(path, 0.017, "gloss_black", bone, seg=6)
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

    # C-pillar rolling into the roof
    def cpil(m):
        rings = []
        for zg in (ZG_BELT, 1.58, 1.72, 1.86, ZG_ROOF - 0.04):
            x = glass_x(zg) + 0.014
            r = 0.02 * smoothstep(1.80, ZG_ROOF, zg)
            rings.append([(x - 0.06, Y_RDOOR_R - 0.004, G(zg)), (x, Y_RDOOR_R - 0.004, G(zg)),
                          (x - r, Y_CAB_R + 0.02, G(zg)), (x - 0.03 - r, Y_CAB_R - 0.004, G(zg)),
                          (x - 0.06, Y_CAB_R - 0.004, G(zg))])
        m.loft(rings, "paint", "chassis")
    mirror_side(mb, cpil)

    # black rocker under the doors (seen behind the running boards)
    def rocker(m):
        m.loft([[(0.86, y, G(0.43)), (0.965, y, G(0.45)), (0.985 + bow(y), y, G(ZG_BODY + 0.01)),
                 (0.86, y, G(ZG_BODY + 0.01))] for y in (Y_FDOOR_F - 0.01, Y_CAB_R)], "plastic", "chassis")
    mirror_side(mb, rocker)

    def bpil(m):
        m.loft([[(glass_x(zg) + 0.004, Y_FDOOR_R - 0.006, G(zg)), (glass_x(zg) + 0.004, Y_RDOOR_F + 0.006, G(zg)),
                 (glass_x(zg) - 0.04, Y_RDOOR_F + 0.006, G(zg)), (glass_x(zg) - 0.04, Y_FDOOR_R - 0.006, G(zg))]
                for zg in (ZG_BELT, ZG_ROOF - 0.07)], "gloss_black", "chassis")
    mirror_side(mb, bpil)


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


def arch_flares(mb):
    """Factory black arch mouldings (misc_d) following the wheel openings (front one runs down the bumper end)."""
    def flare(m, cy, shape, x_fn):
        pts = arch_outline(cy, shape)
        rings = []
        for i, (y, z) in enumerate(pts):
            a = Vector(pts[max(i - 1, 0)])
            b = Vector(pts[min(i + 1, len(pts) - 1)])
            t = (b - a).normalized()
            n = Vector((t.y, -t.x))
            if n.dot(Vector((y - cy, z - 0.5))) < 0:
                n = -n
            xb = x_fn(y + n.x * 0.035, z + n.y * 0.035)
            sec = [(0.0, -0.04), (0.0, 0.018), (0.02, 0.028), (0.048, 0.022), (FLARE_W, 0.004),
                   (FLARE_W + 0.002, -0.008), (0.04, -0.035)]
            rings.append([(xb + dx, y + n.x * d, G(z + n.y * d)) for d, dx in sec])
        m.loft(rings, "plastic", "misc_d")
    mirror_side(mb, lambda m: flare(m, FAX, FRONT_ARCH_EXT,
                                    lambda y, z: side_x(y, z) + arch_swell(y, z, FAX, FRONT_ARCH)))
    mirror_side(mb, lambda m: flare(m, RAX, REAR_ARCH, lambda y, z: side_x(y, z) + arch_swell(y, z, RAX, REAR_ARCH)))


# ================================================================================================ hood / cowl / roof

HOOD_HW_F, HOOD_HW_R = 0.930, 0.915


def dome_hw(y):
    t = (Y_HOOD_F - y) / (Y_HOOD_F - Y_HOOD_R)
    return 0.47 - 0.12 * max(0.0, min(1.0, t))


def hood_z(x, y):
    ax = abs(x)
    t = max(0.0, min(1.0, (Y_HOOD_F - y) / (Y_HOOD_F - Y_HOOD_R)))
    w = dome_hw(y)
    base = hood_line(y)
    crown = 0.012 * (1 - (ax / HOOD_HW_F) ** 2)
    dome = (0.036 - 0.014 * t) * (1 - smoothstep(w - 0.015, w + 0.025, ax))
    edge = -0.032 * smoothstep(0.78, HOOD_HW_F, ax) ** 1.4
    nose = -0.050 * smoothstep(Y_HOOD_F - 0.08, Y_HOOD_F, y) ** 2
    return base + crown + dome + edge + nose


def hood(mb):
    hw = lambda y: HOOD_HW_R + (HOOD_HW_F - HOOD_HW_R) * (y - Y_HOOD_R) / (Y_HOOD_F - Y_HOOD_R)
    ys = [Y_HOOD_R + k * (Y_HOOD_F - Y_HOOD_R) / 32 for k in range(33)]
    outline = [(hw(y), y) for y in ys] + [(-hw(y), y) for y in reversed(ys)]
    creases = []
    for s in (-1, 1):
        for off in (-0.015, 0.025):
            creases.append([(s * (dome_hw(y) + off), y) for y in ys[1:-1]])
        creases.append([(s * 0.78, y) for y in (ys[1], ys[-2])])
    panel(mb, outline, lambda x, y: Vector((x, y, G(hood_z(x, y)))), "paint", "bonnet", out=(0, 0, 1), spacing=0.028,
          creases=creases, flange=(0.035, lambda p: Vector((0, 0, -1))))
    panel(mb, outline, lambda x, y: Vector((x, y, G(hood_z(x, y) - 0.04))), "black", "bonnet", out=(0, 0, -1),
          spacing=0.12)


def cowl(mb):
    mb.loft([[(x, Y_WS - 0.01, G(ZG_BELT - 0.01)), (x, Y_HOOD_R - 0.005, G(ZG_BELT - 0.02)),
              (x, Y_HOOD_R - 0.005, G(ZG_BELT - 0.045)), (x, Y_WS - 0.01, G(ZG_BELT - 0.055))] for x in (-0.905, 0.905)],
            "plastic", "chassis")
    # wipers
    for x0 in (-0.70, 0.02):
        mb.box((x0, Y_WS - 0.035, G(ZG_BELT - 0.008)), (x0 + 0.62, Y_WS - 0.02, G(ZG_BELT + 0.002)), "black", "chassis")
    # whip antenna (driver side, hood/cowl corner) and roof shark fin
    mb.cylinder((-0.86, Y_HOOD_R + 0.02, G(1.43)), (-0.86, Y_HOOD_R + 0.08, G(2.25)), 0.004, "black", "chassis", seg=6)
    mb.loft([[(x, y, G(z)) for x, y, z in ((-0.03, Y_ROOF_F - 0.12, 1.99), (0.03, Y_ROOF_F - 0.12, 1.99),
                                           (0.012, Y_ROOF_F - 0.26, 2.05), (-0.012, Y_ROOF_F - 0.26, 2.05))],
             [(x, y, G(z)) for x, y, z in ((-0.03, Y_ROOF_F - 0.30, 1.99), (0.03, Y_ROOF_F - 0.30, 1.99),
                                           (0.012, Y_ROOF_F - 0.29, 2.05), (-0.012, Y_ROOF_F - 0.29, 2.05))]],
            "gloss_black", "chassis")


def greenhouse(mb):
    def ws_pt(u, v):
        zg = ZG_BELT + v * (1.925 - ZG_BELT)
        y = a_pillar_y(zg) + 0.03 * (1 - u * u) * (0.6 + 0.4 * math.sin(math.pi * v))
        hw = 0.900 - 0.095 * v
        return Vector((u * hw, y, G(zg)))
    _glass_grid(mb, ws_pt, "windscreen", out=Vector((0, 1, 0.6)))

    def apil(m):
        rings = []
        for k in range(8):
            zg = ZG_BELT - 0.01 + k * (1.935 - ZG_BELT + 0.01) / 7
            y = a_pillar_y(zg)
            hw = 0.900 - 0.095 * (zg - ZG_BELT) / 0.48
            rings.append([(hw - 0.006, y + 0.012, G(zg)), (hw + 0.045, y - 0.005, G(zg)), (hw + 0.068, y - 0.05, G(zg)),
                          (hw + 0.05, y - 0.11, G(zg)), (hw - 0.02, y - 0.05, G(zg))])
        m.loft(rings, "paint", "chassis")
    mirror_side(mb, apil)

    def roof_z(x, y):
        ax = abs(x)
        side = 0.045 * smoothstep(0.62, 0.86, ax) ** 1.8
        crown = 0.012 * (1 - (ax / 0.86) ** 2)
        f = 0.035 * smoothstep(Y_ROOF_F - 0.14, Y_ROOF_F + 0.03, y) ** 2
        r = 0.045 * smoothstep(Y_CAB_R + 0.16, Y_CAB_R - 0.01, y) ** 2
        return ZG_ROOF - 0.012 + crown - side - f - r
    hw = lambda y: 0.86 - 0.03 * smoothstep(Y_ROOF_F - 0.10, Y_ROOF_F + 0.03, y)
    ys = [Y_CAB_R - 0.01 + k * (Y_ROOF_F + 0.03 - Y_CAB_R + 0.01) / 34 for k in range(35)]
    outline = [(hw(y), y) for y in ys] + [(-hw(y), y) for y in reversed(ys)]
    panel(mb, outline, lambda x, y: Vector((x, y, G(roof_z(x, y)))), "paint", "chassis", out=(0, 0, 1), spacing=0.04,
          flange=(0.06, lambda p: Vector((0.5 * (1 if p.x > 0 else -1), 0, -1)).normalized()))
    mirror_side(mb, lambda m: m.tube([(0.835, Y_ROOF_F - 0.04, G(ZG_ROOF - 0.055)),
                                      (0.85, Y_CAB_R + 0.03, G(ZG_ROOF - 0.06))], 0.008, "gloss_black", "chassis", seg=6))

    def side_glass(m, s):
        def pane(pts2d, bone):
            def pt(u, v):
                (y0, z0), (y1, z1), (y2, z2), (y3, z3) = pts2d
                yb, zb = y0 + (y1 - y0) * u, z0 + (z1 - z0) * u
                yt, zt = y3 + (y2 - y3) * u, z3 + (z2 - z3) * u
                y, zg = yb + (yt - yb) * v, zb + (zt - zb) * v
                return Vector((glass_x(zg), y, G(zg)))
            _glass_grid(m, pt, bone, out=Vector((1, 0, 0.1)), nu=4, nv=4, centered=False)
        zt = 1.90
        pane([(Y_FDOOR_F - 0.13, ZG_BELT + 0.01), (Y_FDOOR_R + 0.025, ZG_BELT + 0.01), (Y_FDOOR_R + 0.025, zt),
              (a_pillar_y(zt) - 0.03, zt)], f"window_{s}f")
        pane([(Y_RDOOR_F - 0.025, ZG_BELT + 0.01), (Y_RDOOR_R + 0.03, ZG_BELT + 0.01), (Y_RDOOR_R + 0.06, zt),
              (Y_RDOOR_F - 0.025, zt)], f"window_{s}r")
        m.loft([[(0.955, Y_FDOOR_F - 0.02, G(ZG_BELT)), (0.955, Y_FDOOR_F - 0.135, G(ZG_BELT)),
                 (glass_x(1.60), a_pillar_y(1.60) - 0.015, G(1.60))],
                [(0.935, Y_FDOOR_F - 0.02, G(ZG_BELT)), (0.935, Y_FDOOR_F - 0.135, G(ZG_BELT)),
                 (glass_x(1.60) - 0.02, a_pillar_y(1.60) - 0.015, G(1.60))]], "gloss_black", f"door_{s}side_f")
    side_glass(mb, "p")
    with mb.mirrored():
        side_glass(mb, "d")

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


def _glass_grid(mb, fn, bone, out, nu=8, nv=6, centered=True):
    us = [(-1 + 2 * i / nu) if centered else i / nu for i in range(nu + 1)]
    vs = [j / nv for j in range(nv + 1)]
    grid = [[fn(u, v) for u in us] for v in vs]
    for mat, off, flip in (("glass", 0.0, False), ("glass_in", -0.004, True)):
        ids = [[mb._vert(p + out.normalized() * off, bone) for p in row] for row in grid]
        for j in range(nv):
            for i in range(nu):
                q = [ids[j][i], ids[j][i + 1], ids[j + 1][i + 1], ids[j + 1][i]]
                a, b, c = grid[j][i], grid[j][i + 1], grid[j + 1][i + 1]
                if ((b - a).cross(c - a).dot(out) < 0) != flip:
                    q.reverse()
                mb.face(q, mat, None, fixed=True)


# ================================================================================================ front end

def corner_y(x):
    return 0.080 * smoothstep(0.84, 1.0, abs(x)) ** 2


def front_end(mb):
    """Fascia corners below the lamps (with the vertical air-curtain vents) and the lamp backing."""
    def corner(m):
        outline = [(0.70, 0.80), (0.995, 0.80), (0.995, 1.04), (0.87, 0.965), (0.70, 0.905)]

        def lift(x, zg):
            return Vector((x - 0.02 * smoothstep(0.93, 0.995, x) ** 2, 2.79 - corner_y(x) - 0.03 * (1.04 - zg) ** 0.5,
                           G(zg)))
        panel(m, outline, lift, "paint", "chassis", out=(0, 1, 0), spacing=0.025,
              flange=(0.03, lambda p: Vector((0, -1, 0))))
        # air-curtain vent with vertical slats
        x0, x1, z0, z1 = 0.885, 0.935, 0.83, 0.955
        yv = 2.79 - corner_y(0.91) - 0.02
        m.box((x0, yv - 0.04, G(z0)), (x1, yv + 0.004, G(z1)), "black", "chassis")
        for k in range(5):
            z = z0 + 0.012 + k * (z1 - z0 - 0.02) / 4
            m.box((x0 + 0.004, yv - 0.02, G(z)), (x1 - 0.004, yv + 0.006, G(z + 0.008)), "gloss_black", "chassis")
    mirror_side(mb, corner)
    mb.box((-0.98, 2.60, G(0.78)), (0.98, 2.68, G(1.31)), "black", "chassis")
    headlamps(mb)


def headlamps(mb):
    def lamp(m, lid, ind):
        # lens outline (front view): full top, wrapping corner, lower edge stepping down along the DRL hook
        outline = [(0.665, 1.302), (0.985, 1.302), (1.002, 1.27), (0.995, 1.07), (0.875, 0.985), (0.86, 0.95),
                   (0.70, 0.912), (0.68, 0.935), (0.665, 1.08)]

        def lens(x, zg):
            y = 2.808 - corner_y(x) * 1.15 + 0.006 * (1 - ((zg - 1.15) / 0.2) ** 2)
            return Vector((x - 0.015 * smoothstep(0.95, 1.0, x) ** 2, y, G(zg)))
        panel(m, outline, lens, "glass", "chassis", out=(0, 1, 0), spacing=0.022)
        yb = 2.745
        # housing back
        m.box((0.665, yb - 0.03, G(0.915)), (0.985, yb, G(1.30)), "black", "chassis")
        # projector box (dark chrome) with the LED module and lower reflector
        m.rbox((0.672, yb, G(1.085)), (0.828, yb + 0.03, G(1.272)), 0.012, "reflector", "chassis")
        m.rbox((0.69, yb + 0.03, G(1.175)), (0.81, yb + 0.05, G(1.255)), 0.02, "light_clear", "chassis", light=lid)
        for k in range(3):
            z = 1.10 + k * 0.024
            m.box((0.69, yb + 0.03, G(z)), (0.81, yb + 0.045, G(z + 0.008)), "chrome", "chassis")
        # C / hockey-stick DRL: top bar, outboard drop, hook inward under the projector box
        led = "light_led"
        m.box((0.665, yb + 0.045, G(1.282)), (0.858, yb + 0.062, G(1.298)), led, "chassis", light=lid)
        m.box((0.838, yb + 0.04, G(1.00)), (0.858, yb + 0.062, G(1.298)), led, "chassis", light=lid)
        pts = [(0.848, 1.005), (0.84, 0.975), (0.80, 0.950), (0.74, 0.932), (0.705, 0.925)]
        for (xa, za), (xb, zb) in zip(pts, pts[1:]):
            m.tube([(xa, yb + 0.05, G(za)), (xb, yb + 0.05, G(zb))], 0.009, led, "chassis", seg=6)
        # outboard fin section with chrome blades and the amber marker in the top corner
        m.box((0.862, yb - 0.01, G(1.03)), (0.98, yb + 0.01, G(1.27)), "black", "chassis")
        for k in range(4):
            z = 1.07 + k * 0.045
            m.box((0.87, yb + 0.01, G(z)), (0.975 - 0.01 * k, yb + 0.035, G(z + 0.01)), "chrome", "chassis")
        m.box((0.87, yb + 0.01, G(1.255)), (0.995, yb + 0.05, G(1.29)), "light_amber", "chassis", light=ind)
    lamp(mb, 2, 6)
    with mb.mirrored():
        lamp(mb, 1, 5)


def grille(mb):
    """AT4X grille (misc_c): Titanium surround under the hood brow, chunky stepped Titanium bars, GMC emblem."""
    b = "misc_c"
    y0 = 2.80
    top, bot = 1.300, 0.845

    def gx(zg):
        return 0.662 - 0.05 * (top - zg) / (top - bot)
    # gloss black frame ring around the opening
    outline = [(-gx(bot), bot), (gx(bot), bot), (gx(top), top), (-gx(top), top)]
    inner = [(-gx(bot) + 0.035, bot + 0.035), (gx(bot) - 0.035, bot + 0.035), (gx(top - 0.06) - 0.035, top - 0.06),
             (-gx(top - 0.06) + 0.035, top - 0.06)]
    panel(mb, outline, lambda x, zg: Vector((x, y0 + 0.045 - 0.04 * (top - zg), G(zg))), "gloss_black", b,
          out=(0, 1, 0), spacing=0.03, holes=[inner], flange=(0.08, lambda p: Vector((0, -1, 0))))
    # Titanium surround bar along the top (under the hood brow)
    mb.loft([[(x, y0 + 0.055, G(top - 0.005)), (x, y0 + 0.07, G(top - 0.045)), (x, y0 + 0.02, G(top - 0.065)),
              (x, y0 - 0.02, G(top - 0.02))] for x in (-gx(top), -0.3, 0.0, 0.3, gx(top))], "titanium", b)
    # black mesh behind
    mb.box((-gx(bot), y0 - 0.05, G(bot)), (gx(bot), y0 - 0.035, G(top - 0.05)), "grille", b)
    # four stepped Titanium bars (chamfered section, dropping towards the centre)
    for k, zc in enumerate((1.165, 1.075, 0.985, 0.900)):
        rings = []
        xs = [-0.62 + i * 1.24 / 40 for i in range(41)]
        for x in xs:
            hwx = gx(zc) - 0.03
            if abs(x) > hwx:
                x = math.copysign(hwx, x)
            dz = -0.028 * (1 - smoothstep(0.17, 0.27, abs(x)))
            z = zc + dz
            yf = y0 + 0.030 - 0.04 * (top - zc)
            rings.append([(x, yf - 0.06, G(z - 0.02)), (x, yf, G(z - 0.018)), (x, yf + 0.012, G(z + 0.006)),
                          (x, yf - 0.01, G(z + 0.026)), (x, yf - 0.06, G(z + 0.022))])
        mb.loft(rings, "titanium", b)
    # GMC emblem (chrome letters with red fill) over the upper bars
    mb.decal((0, y0 + 0.055, G(1.12)), (0, 1, 0.1), (0, -0.1, 1), 0.50, 0.125, "badge_gmc", b)
    mb.decal((0, y0 + 0.054, G(1.12)), (0, 1, 0.1), (0, -0.1, 1), 0.50, 0.125, "badge_gmc", b)
    # small AT4X badge at the lower driver-side corner of the grille
    mb.decal((-0.42, y0 + 0.045 - 0.04 * (top - 0.875), G(0.875)), (0, 1, 0), (0, 0, 1), 0.16, 0.04, "badge_at4x", b)


def front_bumper(mb):
    """AT4X front bumper (bumper_f): painted upper with a crease, textured lower valance, red hooks, fog lamps."""
    b = "bumper_f"
    xs = [-1.006, -0.995, -0.97, -0.92, -0.85, -0.7, -0.45, -0.2, 0.0, 0.2, 0.45, 0.7, 0.85, 0.92, 0.97, 0.995, 1.006]

    def yfront(x):
        ax = abs(x)
        return FRONT - 0.018 * (ax / 0.85) ** 2 - 0.25 * smoothstep(0.82, 1.006, ax) ** 1.5

    up = [(-0.17, 0.81), (-0.04, 0.81), (-0.012, 0.80), (0.0, 0.76), (0.004, 0.72), (-0.004, 0.70),
          (0.0, 0.66), (-0.02, 0.625), (-0.17, 0.625)]
    mb.loft([[(x, yfront(x) + dy, G(z)) for dy, z in up] for x in xs], "paint", b)
    low = [(-0.25, 0.625), (-0.03, 0.625), (-0.04, 0.56), (-0.07, 0.49), (-0.12, 0.445), (-0.25, 0.445)]
    mb.loft([[(x * 0.985, yfront(x) + dy, G(z)) for dy, z in low] for x in xs[1:-1]], "plastic", b)
    # red recovery hooks (vertical loops) in pockets
    for s in (-1, 1):
        x = s * 0.40
        y = yfront(x)
        mb.rbox((x - 0.06, y - 0.08, G(0.47)), (x + 0.06, y - 0.05, G(0.57)), 0.015, "black", b)
        mb.tube([(x, y - 0.10, G(0.48)), (x, y - 0.02, G(0.49)), (x, y + 0.005, G(0.52)), (x, y - 0.005, G(0.555)),
                 (x, y - 0.06, G(0.56))], 0.018, "red", b, seg=10)
    # fog lamps at the lower outer corners
    for s in (-1, 1):
        x = s * 0.79
        y = yfront(x) - 0.06
        mb.rbox((x - 0.07, y - 0.02, G(0.47)), (x + 0.07, y + 0.012, G(0.53)), 0.015, "gloss_black", b)
        mb.rbox((x - 0.058, y + 0.008, G(0.48)), (x + 0.058, y + 0.016, G(0.52)), 0.012, "light_clear", b,
                light=14 if s < 0 else 15)
    # front plate on the upper bumper, parking sensors
    mb.decal((0, yfront(0) + 0.006, G(0.715)), (0, 1, 0), (0, 0, 1), 0.305, 0.152, "plate", b)
    for x in (-0.62, -0.25, 0.25, 0.62):
        mb.cylinder((x, yfront(x) - 0.003, G(0.67)), (x, yfront(x) + 0.004, G(0.67)), 0.011, "paint", b, seg=10)
    # skid plate (misc_g) under the valance
    mb.loft([[(x, FRONT - 0.13, G(0.455)), (x, FRONT - 0.17, G(0.42)), (x, 2.40, G(0.38)), (x, 2.40, G(0.365)),
              (x, FRONT - 0.17, G(0.405)), (x, FRONT - 0.14, G(0.44))] for x in (-0.55, 0.55)], "alu", "misc_g")


# ================================================================================================ rear end

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


# ================================================================================================ mirrors / steps

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


REAR_LIFT = ZG_RAIL - 1.445        # tailgate / lamps / rear bumper were authored for a 1.445 m rail
FRONT_DROP = -0.04                 # lamps / grille authored for a slightly higher hood nose
MIRROR_DROP = -0.12


def _lifted(mb, dz):
    return mb.push_ctx(Matrix.Translation((0, 0, dz)))


def build_exterior(mb):
    front_fender(mb)
    doors(mb)
    cab_sheetmetal(mb)
    bed_sides(mb)
    arch_flares(mb)
    hood(mb)
    cowl(mb)
    greenhouse(mb)
    with _lifted(mb, FRONT_DROP):
        front_end(mb)
        grille(mb)
    front_bumper(mb)
    with _lifted(mb, REAR_LIFT):
        tailgate(mb)
        taillamps(mb)
        rear_bumper(mb)
    running_boards(mb)
