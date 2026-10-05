"""Front of the AT4X: front fenders + arch moulding, hood, cowl, fascia, headlamps, grille, front bumper."""
import math

from mathutils import Matrix, Vector

from at4x_dims import *  # noqa: F401,F403
from geom import rrect
from surf import densify, panel, pchip, point_in_poly, smoothstep
from ext_common import *  # noqa: F401,F403
from ext_common import _glass_grid, _lifted, _rounded_loop, _wheelhouse


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
    mb.loft([[(x, y, G(z)) for x, y, z in ((-0.03, Y_WS_TOP - 0.22, 1.99), (0.03, Y_WS_TOP - 0.22, 1.99),
                                           (0.012, Y_WS_TOP - 0.36, 2.05), (-0.012, Y_WS_TOP - 0.36, 2.05))],
             [(x, y, G(z)) for x, y, z in ((-0.03, Y_WS_TOP - 0.40, 1.99), (0.03, Y_WS_TOP - 0.40, 1.99),
                                           (0.012, Y_WS_TOP - 0.39, 2.05), (-0.012, Y_WS_TOP - 0.39, 2.05))]],
            "gloss_black", "chassis")


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


def front_flares(mb):
    mirror_side(mb, lambda m: arch_flare(m, FAX, FRONT_ARCH_EXT,
                                         lambda y, z: side_x(y, z) + arch_swell(y, z, FAX, FRONT_ARCH)))


def build_front(mb):
    front_fender(mb)
    front_flares(mb)
    hood(mb)
    cowl(mb)
    with _lifted(mb, FRONT_DROP):
        front_end(mb)
        grille(mb)
    front_bumper(mb)
