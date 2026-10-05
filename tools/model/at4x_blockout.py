"""The stock 2024+ GMC Sierra 1500 AT4X (crew cab, short box), built procedurally at 1:1 scale.

Space: metres, origin at the centre of the truck's footprint, +Y forward, +X passenger side, +Z up.
Key real-world figures (see docs/MODELING_SPEC.md): length 5.89 m, wheelbase 3.744 m, width 2.063 m,
height 2.02 m, track 1.75 m, 33.2 in (0.843 m) tires.
"""
import math

from mathutils import Matrix, Vector

from geom import MeshBuilder, arc, rrect

# ---------------------------------------------------------------------------------------------- layout

GROUND = -0.80                 # ground plane
TIRE_R = 0.4215                # 33.2 in tire
TIRE_W = 0.28                  # 275 mm section
RIM_R = 0.2286                 # 18 in wheel
WZ = GROUND + TIRE_R           # wheel centre height
FAX, RAX = 1.995, -1.749       # front / rear axle (3.744 m wheelbase)
TRACK = 0.875                  # half track (1.75 m)
ARCH_R = 0.535                 # wheel opening radius
FRONT, REAR = 2.945, -2.945    # bumper extremes (5.89 m)
SIDE = 1.012                   # body side (2.063 m with flares)

# Y stations
Y_FASCIA = 2.80                # front of fenders / hood
Y_COWL = 1.27                  # windshield base
Y_FDOOR = 1.17                 # front door leading edge
Y_BPIL = 0.165                 # B-pillar / door split
Y_CDOOR = -0.82                # rear door trailing edge
Y_ROOF_F, Y_ROOF_R = 0.50, -0.80
Y_CAB = -0.93                  # back of cab
Y_BED_F, Y_BED_R = -0.955, -2.80

# Z heights (from ground)
def h(z):
    return GROUND + z

Z_BOT = h(0.62)                # body lower edge
Z_BAND = h(1.06)               # top of the arch band / shoulder crease start
Z_BELT = h(1.42)               # beltline / bed rail
Z_HOOD_F, Z_HOOD_R = h(1.34), h(1.46)
Z_ROOF = h(2.02)


def hood_z(y):
    t = (Y_FASCIA - y) / (Y_FASCIA - Y_COWL)
    return Z_HOOD_F + (Z_HOOD_R - Z_HOOD_F) * max(0.0, min(1.0, t))


# ---------------------------------------------------------------------------------------------- bones

def bones():
    """Vehicle skeleton (names/tags follow GTA conventions)."""
    door_l = ((0, 0, -1.25), (0, 0, 0))
    door_r = ((0, 0, 0), (0, 0, 1.25))
    B = [
        dict(name="chassis", pos=(0, 0, 0)),
        dict(name="bodyshell", pos=(0, 0, 0), parent="chassis"),
        dict(name="chassis_dummy", pos=(0, 0, 0), parent="chassis"),
        dict(name="door_dside_f", pos=(-1.0, Y_FDOOR - 0.02, h(1.20)), parent="chassis", limit_rot=door_l),
        dict(name="door_pside_f", pos=(1.0, Y_FDOOR - 0.02, h(1.20)), parent="chassis", limit_rot=door_r),
        dict(name="door_dside_r", pos=(-1.0, Y_BPIL - 0.02, h(1.20)), parent="chassis", limit_rot=door_l),
        dict(name="door_pside_r", pos=(1.0, Y_BPIL - 0.02, h(1.20)), parent="chassis", limit_rot=door_r),
        dict(name="window_lf", pos=(-0.93, 0.66, h(1.72)), parent="door_dside_f"),
        dict(name="window_rf", pos=(0.93, 0.66, h(1.72)), parent="door_pside_f"),
        dict(name="window_lr", pos=(-0.93, -0.33, h(1.72)), parent="door_dside_r"),
        dict(name="window_rr", pos=(0.93, -0.33, h(1.72)), parent="door_pside_r"),
        dict(name="windscreen", pos=(0, 0.88, h(1.74)), parent="chassis"),
        dict(name="windscreen_r", pos=(0, Y_CAB, h(1.70)), parent="chassis"),
        dict(name="bonnet", pos=(0, Y_COWL + 0.03, Z_HOOD_R), parent="chassis", limit_rot=((0, 0, 0), (1.0, 0, 0))),
        dict(name="boot", pos=(0, Y_BED_R - 0.03, h(0.93)), parent="chassis", limit_rot=((0, 0, 0), (1.57, 0, 0))),
        dict(name="bumper_f", pos=(0, 2.86, h(0.62)), parent="chassis"),
        dict(name="bumper_r", pos=(0, -2.88, h(0.60)), parent="chassis"),
        dict(name="steeringwheel", pos=(-0.42, 0.78, h(1.32)), parent="chassis",
             rot=Matrix.Rotation(math.radians(-24), 3, "X")),
        dict(name="seat_dside_f", pos=(-0.42, 0.22, h(0.86)), parent="chassis"),
        dict(name="seat_pside_f", pos=(0.42, 0.22, h(0.86)), parent="chassis"),
        dict(name="seat_dside_r", pos=(-0.42, -0.58, h(0.88)), parent="chassis"),
        dict(name="seat_pside_r", pos=(0.42, -0.58, h(0.88)), parent="chassis"),
        dict(name="engine", pos=(0, 1.95, h(1.05)), parent="chassis"),
        dict(name="overheat", pos=(0, 2.10, h(1.30)), parent="chassis"),
        dict(name="petrolcap", pos=(-SIDE, -1.32, h(1.25)), parent="chassis"),
        dict(name="petroltank", pos=(0.55, -1.25, h(0.45)), parent="chassis"),
        dict(name="exhaust", pos=(-0.62, -2.90, h(0.42)), parent="chassis",
             rot=Matrix.Rotation(math.pi, 3, "Z")),
        dict(name="exhaust_2", pos=(0.62, -2.90, h(0.42)), parent="chassis",
             rot=Matrix.Rotation(math.pi, 3, "Z")),
        dict(name="headlight_l", pos=(-0.80, 2.86, h(1.20)), parent="chassis"),
        dict(name="headlight_r", pos=(0.80, 2.86, h(1.20)), parent="chassis"),
        dict(name="indicator_lf", pos=(-0.94, 2.82, h(1.18)), parent="chassis"),
        dict(name="indicator_rf", pos=(0.94, 2.82, h(1.18)), parent="chassis"),
        dict(name="taillight_l", pos=(-0.93, Y_BED_R - 0.04, h(1.30)), parent="chassis"),
        dict(name="taillight_r", pos=(0.93, Y_BED_R - 0.04, h(1.30)), parent="chassis"),
        dict(name="brakelight_l", pos=(-0.93, Y_BED_R - 0.04, h(1.26)), parent="chassis"),
        dict(name="brakelight_r", pos=(0.93, Y_BED_R - 0.04, h(1.26)), parent="chassis"),
        dict(name="brakelight_m", pos=(0, Y_CAB + 0.02, Z_ROOF - 0.04), parent="chassis"),
        dict(name="indicator_lr", pos=(-0.93, Y_BED_R - 0.04, h(1.12)), parent="chassis"),
        dict(name="indicator_rr", pos=(0.93, Y_BED_R - 0.04, h(1.12)), parent="chassis"),
        dict(name="reversinglight_l", pos=(-0.93, Y_BED_R - 0.04, h(1.00)), parent="chassis"),
        dict(name="reversinglight_r", pos=(0.93, Y_BED_R - 0.04, h(1.00)), parent="chassis"),
        dict(name="platelight", pos=(0, -2.95, h(0.80)), parent="chassis"),
        dict(name="interiorlight", pos=(0, -0.10, Z_ROOF - 0.08), parent="chassis"),
        dict(name="dashglow", pos=(-0.42, 1.02, h(1.40)), parent="chassis"),
        dict(name="neon_l", pos=(-0.80, -0.30, h(0.40)), parent="chassis"),
        dict(name="neon_r", pos=(0.80, -0.30, h(0.40)), parent="chassis"),
        dict(name="neon_f", pos=(0, 2.40, h(0.38)), parent="chassis"),
        dict(name="neon_b", pos=(0, -2.40, h(0.45)), parent="chassis"),
    ]
    for side, x in (("l", -TRACK), ("r", TRACK)):
        for end, y in (("f", FAX), ("r", RAX)):
            B.append(dict(name=f"wheel_{side}{end}", pos=(x, y, WZ), parent="chassis"))
            B.append(dict(name=f"suspension_{side}{end}", pos=(x * 0.62, y, WZ + 0.04), parent="chassis"))
            B.append(dict(name=f"hub_{side}{end}", pos=(x, y, WZ), parent="chassis"))
    for c in "abcdefghij":
        B.append(dict(name=f"misc_{c}", pos=(0, 0, 0), parent="chassis"))
    return B


# ---------------------------------------------------------------------------------------------- helpers

def side_band(mb, y0, y1, arch_y=None, bone="chassis", mat="paint", x_in=0.93, x_out=SIDE, z0=Z_BOT, z1=Z_BAND,
              sides=(1, -1)):
    """Lower body band in the YZ plane, optionally with a wheel arch cut out."""
    yf, yr = max(y0, y1), min(y0, y1)
    outline = [(yr, z0)]
    if arch_y is not None:
        dz = z0 - WZ
        dy = math.sqrt(max(ARCH_R ** 2 - dz ** 2, 0.0))
        a = math.degrees(math.atan2(dz, dy))
        outline.append((arch_y - dy, z0))
        outline += arc(arch_y, WZ, ARCH_R, 180 - a, a, 18)[1:-1]
        outline.append((arch_y + dy, z0))
    outline += [(yf, z0), (yf, z1), (yr, z1)]
    for s in sides:
        if s > 0:
            mb.extrude_yz(outline, x_in, x_out, mat, bone)
        else:
            with mb.mirrored():
                mb.extrude_yz(outline, x_in, x_out, mat, bone)


def shoulder(mb, y0, y1, top_fn, bone="chassis", mat="paint", x_in=0.93, x_out=SIDE, steps=6, round_top=0.045,
             sides=(1, -1)):
    """Upper body side from the crease to the beltline/hood line, lofted along Y (both sides)."""
    def ring(y):
        top = top_fn(y)
        return [(x_in, y, Z_BAND), (x_out, y, Z_BAND), (x_out + 0.004, y, Z_BAND + (top - Z_BAND) * 0.45),
                (x_out - 0.012, y, top - round_top), (x_out - 0.045, y, top), (x_in, y, top)]
    rings = [ring(y0 + (y1 - y0) * k / steps) for k in range(steps + 1)]
    for s in sides:
        if s > 0:
            mb.loft(rings, mat, bone)
        else:
            with mb.mirrored():
                mb.loft(rings, mat, bone)


def both(mb, fn):
    fn(mb)
    with mb.mirrored():
        fn(mb)


# ---------------------------------------------------------------------------------------------- parts

def front_clip(mb):
    # fenders
    side_band(mb, Y_FASCIA, Y_FDOOR + 0.005, arch_y=FAX)
    shoulder(mb, Y_FASCIA, Y_FDOOR + 0.005, lambda y: hood_z(max(y, Y_COWL)) - 0.012)
    # inner fender walls / engine bay sides (black)
    both(mb, lambda m: m.box((0.86, Y_COWL, h(0.78)), (0.93, Y_FASCIA - 0.06, hood_z(2.0) - 0.04), "black", "chassis"))
    # firewall + cowl panel
    mb.box((-0.93, Y_COWL - 0.03, h(0.70)), (0.93, Y_COWL, Z_HOOD_R - 0.01), "black", "chassis")
    mb.box((-0.92, Y_FDOOR + 0.0, Z_HOOD_R - 0.03), (0.92, Y_COWL + 0.02, Z_HOOD_R + 0.005), "plastic", "chassis")
    # radiator support / core
    mb.box((-0.72, 2.60, h(0.72)), (0.72, 2.68, Z_HOOD_F - 0.05), "black", "chassis")
    # engine block (V8) + heads + accessories
    mb.box((-0.30, 1.55, h(0.62)), (0.30, 2.40, h(1.05)), "steel", "chassis")
    both(mb, lambda m: m.box((0.22, 1.60, h(0.95)), (0.42, 2.35, h(1.16)), "steel", "chassis"))
    mb.cylinder((0, 2.42, h(0.95)), (0, 2.50, h(0.95)), 0.20, "black", "chassis", seg=20)
    mb.box((-0.88, 2.05, h(1.05)), (-0.62, 2.35, h(1.28)), "black", "chassis")          # battery
    mb.box((-0.20, 1.40, h(1.00)), (0.20, 1.55, h(1.12)), "black", "chassis")            # throttle body area


def engine_cover(mb):
    """Stock engine cover (misc_e) — hidden when a supercharger is fitted."""
    mb.rbox((-0.26, 1.62, h(1.15)), (0.26, 2.30, h(1.24)), 0.03, "engine_cover", "misc_e")


def airbox(mb):
    """Stock airbox and intake tube (misc_f)."""
    mb.rbox((0.48, 2.10, h(1.02)), (0.84, 2.58, h(1.26)), 0.04, "black", "misc_f")
    mb.tube([(0.60, 2.10, h(1.16)), (0.45, 1.85, h(1.18)), (0.15, 1.55, h(1.10))], 0.055, "black", "misc_f")


def hood(mb):
    """Hood with the AT4X power dome (bonnet bone)."""
    ys = [Y_FASCIA + 0.02 - k * (Y_FASCIA + 0.02 - Y_COWL - 0.02) / 8 for k in range(9)]
    rings = []
    for y in ys:
        zt = hood_z(min(y, Y_FASCIA)) + 0.012
        dome = 0.045 * math.sin(math.pi * min(1.0, max(0.0, (Y_FASCIA - y) / (Y_FASCIA - Y_COWL))) ** 0.6)
        ring = [(-0.955, y, zt - 0.045), (0.955, y, zt - 0.045), (0.958, y, zt - 0.01), (0.90, y, zt + 0.012),
                (0.42, y, zt + 0.02), (0.30, y, zt + 0.02 + dome), (-0.30, y, zt + 0.02 + dome),
                (-0.42, y, zt + 0.02), (-0.90, y, zt + 0.012), (-0.958, y, zt - 0.01)]
        rings.append(ring)
    mb.loft(rings, "paint", "bonnet")


def fascia(mb):
    """Grille (misc_c), headlights, fascia plastics."""
    # fascia upper body-colour header between headlights and above grille
    mb.box((-0.96, Y_FASCIA - 0.02, Z_HOOD_F - 0.10), (0.96, Y_FASCIA + 0.04, Z_HOOD_F - 0.005), "paint", "chassis")
    # black lower fascia behind bumper
    mb.box((-0.98, Y_FASCIA - 0.05, h(0.62)), (0.98, Y_FASCIA + 0.02, h(0.80)), "plastic", "chassis")
    # headlight housings
    def headlight(m):
        x0, x1 = 0.60, 0.975
        m.box((x0, Y_FASCIA - 0.06, h(1.05)), (x1, Y_FASCIA + 0.045, h(1.25)), "reflector", "chassis")
        # projector lens (headlight beam)
        m.cylinder((0.74, Y_FASCIA + 0.045, h(1.15)), (0.74, Y_FASCIA + 0.06, h(1.15)), 0.045, "light_clear",
                   "chassis", seg=16, light=1)
        m.cylinder((0.86, Y_FASCIA + 0.045, h(1.15)), (0.86, Y_FASCIA + 0.06, h(1.15)), 0.040, "light_clear",
                   "chassis", seg=16, light=1)
        # signature C-shaped LED: top bar, outboard drop, lower return into the fascia
        m.box((0.62, Y_FASCIA + 0.045, h(1.235)), (0.97, Y_FASCIA + 0.065, h(1.255)), "light_led", "chassis", light=1)
        m.box((0.615, Y_FASCIA + 0.02, h(0.86)), (0.645, Y_FASCIA + 0.07, h(1.255)), "light_led", "chassis", light=1)
        m.box((0.615, Y_FASCIA + 0.02, h(0.84)), (0.80, Y_FASCIA + 0.07, h(0.865)), "light_led", "chassis", light=1)
        # amber indicator wrapping the corner
        m.box((0.93, Y_FASCIA - 0.10, h(1.06)), (0.985, Y_FASCIA + 0.045, h(1.11)), "light_amber", "chassis", light=5)
    headlight(mb)
    with mb.mirrored():
        # mirrored copy uses right-side light ids
        mb_r = mb
        x0, x1 = 0.60, 0.975
        mb_r.box((x0, Y_FASCIA - 0.06, h(1.05)), (x1, Y_FASCIA + 0.045, h(1.25)), "reflector", "chassis")
        for x, r in ((0.74, 0.045), (0.86, 0.040)):
            mb_r.cylinder((x, Y_FASCIA + 0.045, h(1.15)), (x, Y_FASCIA + 0.06, h(1.15)), r, "light_clear",
                          "chassis", seg=16, light=2)
        mb_r.box((0.62, Y_FASCIA + 0.045, h(1.235)), (0.97, Y_FASCIA + 0.065, h(1.255)), "light_led", "chassis", light=2)
        mb_r.box((0.615, Y_FASCIA + 0.02, h(0.86)), (0.645, Y_FASCIA + 0.07, h(1.255)), "light_led", "chassis", light=2)
        mb_r.box((0.615, Y_FASCIA + 0.02, h(0.84)), (0.80, Y_FASCIA + 0.07, h(0.865)), "light_led", "chassis", light=2)
        mb_r.box((0.93, Y_FASCIA - 0.10, h(1.06)), (0.985, Y_FASCIA + 0.045, h(1.11)), "light_amber", "chassis",
                 light=6)


def grille(mb):
    """Stock AT4X grille: black frame, honeycomb insert, centred red badge (misc_c)."""
    b = "misc_c"
    y = Y_FASCIA + 0.06
    mb.rbox((-0.60, Y_FASCIA - 0.02, h(0.80)), (0.60, y, Z_HOOD_F - 0.08), 0.03, "gloss_black", b)
    mb.box((-0.56, y, h(0.84)), (0.56, y + 0.012, Z_HOOD_F - 0.12), "grille", b)
    mb.box((-0.58, y, h(1.04)), (0.58, y + 0.03, h(1.08)), "gloss_black", b)       # horizontal bar
    mb.decal((0, y + 0.035, h(1.065)), (0, 1, 0), (0, 0, 1), 0.34, 0.17, "badge_gmc", b)
    mb.box((-0.175, y + 0.01, h(0.975)), (0.175, y + 0.033, h(1.155)), "chrome", b)


def front_bumper(mb):
    """AT4X front bumper with red recovery hooks and fog lamps (bumper_f)."""
    b = "bumper_f"
    sec = rrect(0, 0, 0.09, 0.13, 0.05, 3)
    ys = [2.70, 2.83, 2.90, 2.93, 2.945]
    xs = [0.995, 0.985, 0.94, 0.86, 0.0]
    # wraparound: build as a curved loft across X (cross-section in YZ)
    rings = []
    for x in [-0.995, -0.98, -0.93, -0.80, 0.0, 0.80, 0.93, 0.98, 0.995]:
        ax = abs(x)
        yf = 2.945 - 0.20 * max(0.0, (ax - 0.80) / 0.195) ** 2
        rings.append([(x, yf - 0.20 + dy, h(0.62) + dz) for dy, dz in
                      [(0, 0.03), (0.20, 0.03), (0.20, 0.26), (0.14, 0.33), (0, 0.33)]])
    mb.loft(rings, "paint", b)
    # lower black valance + skid lip
    mb.box((-0.90, 2.62, h(0.42)), (0.90, 2.90, h(0.66)), "plastic", b)
    # fog lamps
    for s in (-1, 1):
        mb.cylinder((s * 0.76, 2.905, h(0.55)), (s * 0.76, 2.925, h(0.55)), 0.045, "light_clear", b, seg=14,
                    light=14 if s < 0 else 15)
    # red recovery hooks
    for s in (-1, 1):
        mb.tube([(s * 0.42, 2.84, h(0.47)), (s * 0.42, 2.96, h(0.47)), (s * 0.42, 2.98, h(0.53)),
                 (s * 0.42, 2.95, h(0.58))], 0.022, "red", b)
    # AT4X badge on the bumper
    mb.decal((0, 2.947, h(0.905)), (0, 1, 0), (0, 0, 1), 0.22, 0.055, "badge_at4x", b)


def skids(mb):
    """Factory skid plates (misc_g)."""
    mb.box((-0.62, 2.10, h(0.36)), (0.62, 2.75, h(0.40)), "alu", "misc_g")
    mb.box((-0.35, 0.40, h(0.36)), (0.35, 1.30, h(0.40)), "alu", "misc_g")


def cab(mb):
    # cab side behind the rear doors (lower C-pillar)
    side_band(mb, Y_CDOOR - 0.004, Y_CAB - 0.04)
    shoulder(mb, Y_CDOOR - 0.004, Y_CAB - 0.04, lambda y: Z_BELT)
    # rocker panels under the doors
    both(mb, lambda m: m.box((0.84, Y_CDOOR - 0.06, h(0.56)), (0.99, Y_FDOOR + 0.0, Z_BOT + 0.02), "plastic", "chassis"))
    # A-pillars, roof, C-pillars (paint)
    def pillars(m):
        m.tube([(0.93, Y_COWL - 0.02, Z_HOOD_R + 0.02), (0.84, Y_ROOF_F, Z_ROOF - 0.06)], 0.045, "paint", "chassis", seg=8)
        m.box((0.80, Y_CAB, Z_BELT - 0.02), (0.97, Y_CAB + 0.14, Z_BELT + 0.02), "paint", "chassis")
        m.loft([[(0.80, Y_CAB, Z_BELT), (0.97, Y_CAB, Z_BELT), (0.97, Y_CAB + 0.14, Z_BELT), (0.80, Y_CAB + 0.14, Z_BELT)],
                [(0.76, Y_CAB, Z_ROOF - 0.06), (0.84, Y_CAB, Z_ROOF - 0.06), (0.84, Y_ROOF_R, Z_ROOF - 0.06),
                 (0.76, Y_ROOF_R, Z_ROOF - 0.06)]], "paint", "chassis")
        # B-pillar (black)
        m.box((0.86, Y_BPIL - 0.05, Z_BELT), (0.90, Y_BPIL + 0.05, Z_ROOF - 0.06), "gloss_black", "chassis")
    both(mb, pillars)
    rings = []
    for y in (Y_ROOF_F + 0.02, Y_ROOF_F - 0.10, Y_ROOF_R + 0.05, Y_CAB):
        sec = rrect(0, Z_ROOF - 0.03, 0.86, 0.035, 0.03, 2)
        rings.append([(x, y, z) for x, z in sec])
    mb.loft(rings, "paint", "chassis")
    # back wall of cab (paint) with rear-window opening
    mb.box((-0.99, Y_CAB - 0.04, Z_BOT), (0.99, Y_CAB, Z_BELT + 0.04), "paint", "chassis")
    mb.box((-0.80, Y_CAB - 0.03, Z_ROOF - 0.12), (0.80, Y_CAB + 0.01, Z_ROOF - 0.04), "paint", "chassis")
    both(mb, lambda m: m.box((0.72, Y_CAB - 0.03, Z_BELT), (0.82, Y_CAB + 0.01, Z_ROOF - 0.08), "paint", "chassis"))
    # centre high-mount stop lamp + cargo lamp
    mb.box((-0.12, Y_CAB - 0.05, Z_ROOF - 0.07), (0.12, Y_CAB - 0.03, Z_ROOF - 0.04), "light_red", "chassis", light=11)


def windows(mb):
    """Glass: windscreen, rear slider, four door windows (outer + inner shaders)."""
    def pane(m, pts, bone):
        n = (Vector(pts[1]) - Vector(pts[0])).cross(Vector(pts[2]) - Vector(pts[0])).normalized()
        centroid = sum((Vector(p) for p in pts), Vector()) / len(pts)
        if n.dot(centroid - Vector((0, -0.2, h(1.5)))) < 0:   # outer face must point away from the cabin
            pts = list(reversed(pts))
            n = -n
        n = n * 0.004
        m.poly(pts, "glass", bone, fixed=True)
        m.poly([tuple(Vector(p) - n) for p in reversed(pts)], "glass_in", bone, fixed=True)
    zb = Z_HOOD_R + 0.01
    pane(mb, [(-0.90, Y_COWL - 0.01, zb), (0.90, Y_COWL - 0.01, zb), (0.78, Y_ROOF_F + 0.02, Z_ROOF - 0.07),
              (-0.78, Y_ROOF_F + 0.02, Z_ROOF - 0.07)], "windscreen")
    pane(mb, [(0.72, Y_CAB - 0.02, Z_BELT + 0.04), (-0.72, Y_CAB - 0.02, Z_BELT + 0.04),
              (-0.72, Y_CAB - 0.02, Z_ROOF - 0.13), (0.72, Y_CAB - 0.02, Z_ROOF - 0.13)], "windscreen_r")

    def door_glass(m, side):
        bf, br = ("window_lf", "window_lr") if side < 0 else ("window_rf", "window_rr")
        xb, xt = 0.955, 0.83
        pts_f = [(xb, Y_FDOOR - 0.08, Z_BELT + 0.02), (xb, Y_BPIL + 0.06, Z_BELT + 0.02),
                 (xt, Y_BPIL + 0.06, Z_ROOF - 0.09), (xt, Y_ROOF_F - 0.03, Z_ROOF - 0.09)]
        pts_r = [(xb, Y_BPIL - 0.06, Z_BELT + 0.02), (xb, Y_CDOOR + 0.06, Z_BELT + 0.02),
                 (xt, Y_CDOOR + 0.10, Z_ROOF - 0.09), (xt, Y_BPIL - 0.06, Z_ROOF - 0.09)]
        pane(m, pts_f, bf)
        pane(m, pts_r, br)
    door_glass(mb, 1)
    with mb.mirrored():
        door_glass(mb, -1)


def doors(mb):
    def door(m, y0, y1, bone, front, mirror_side):
        side_band(m, y0, y1, bone=bone, sides=(1,))
        shoulder(m, y0, y1, lambda y: Z_BELT, bone=bone, sides=(1,))
        # window frame (black) — top rail following the roof and rear upright
        xt = 0.84
        top_f = Y_ROOF_F - 0.03 if front else Y_BPIL - 0.06
        m.tube([(0.955, y0 - 0.02, Z_BELT + 0.02), (xt, top_f if front else y0 - 0.02, Z_ROOF - 0.085),
                (xt, y1 + 0.02, Z_ROOF - 0.085), (0.955, y1 + 0.02, Z_BELT + 0.02)], 0.018, "gloss_black", bone, seg=6)
        # inner door trim
        m.box((0.88, y1 + 0.03, Z_BOT + 0.05), (0.93, y0 - 0.03, Z_BELT - 0.01), "trim", bone)
        # handle
        hy = y1 + 0.18
        m.rbox((SIDE - 0.002, hy - 0.14, h(1.27)), (SIDE + 0.022, hy, h(1.31)), 0.012, "gloss_black", bone)
        # AT4X badge on the front doors
        if front:
            m.decal((SIDE + 0.002, y0 - 0.25, h(0.82)), (1, 0, 0), (0, 0, 1), 0.30, 0.075, "badge_at4x", bone)
            # mirror
            m.box((0.97, y0 - 0.20, h(1.44)), (1.06, y0 - 0.10, h(1.50)), "gloss_black", bone)
            m.rbox((1.04, y0 - 0.26, h(1.42)), (1.25, y0 - 0.12, h(1.66)), 0.04, "gloss_black", bone)
            m.box((1.06, y0 - 0.27, h(1.44)), (1.23, y0 - 0.262, h(1.64)), "chrome", bone)
            m.box((1.20, y0 - 0.20, h(1.425)), (1.245, y0 - 0.12, h(1.44)), "light_amber", bone, light=5 if not mirror_side else 6)
    for side in (1, -1):
        def build(m, side=side):
            door(m, Y_FDOOR - 0.005, Y_BPIL + 0.005, "door_pside_f" if side > 0 else "door_dside_f", True, side < 0)
            door(m, Y_BPIL - 0.005, Y_CDOOR, "door_pside_r" if side > 0 else "door_dside_r", False, side < 0)
        if side > 0:
            build(mb)
        else:
            with mb.mirrored():
                build(mb)


def bed(mb):
    side_band(mb, Y_BED_F, Y_BED_R, arch_y=RAX, x_in=0.86)
    shoulder(mb, Y_BED_F, Y_BED_R, lambda y: Z_BELT, x_in=0.86)
    # bed rail caps
    both(mb, lambda m: m.box((0.80, Y_BED_R, Z_BELT - 0.01), (0.90, Y_BED_F, Z_BELT + 0.012), "plastic", "chassis"))
    # inner walls, front wall, floor, wheel tubs
    both(mb, lambda m: m.box((0.80, Y_BED_R, h(0.95)), (0.86, Y_BED_F, Z_BELT), "bedliner", "chassis"))
    mb.box((-0.86, Y_BED_F - 0.05, h(0.95)), (0.86, Y_BED_F, Z_BELT), "bedliner", "chassis")
    mb.box((-0.86, Y_BED_R, h(0.92)), (0.86, Y_BED_F, h(0.95)), "bedliner", "chassis")
    both(mb, lambda m: m.box((0.58, RAX - 0.48, h(0.95)), (0.80, RAX + 0.48, h(1.18)), "bedliner", "chassis"))
    # rear corner caps carry the tail lamps
    def tail(m, l):
        y = Y_BED_R
        m.box((0.86, y - 0.04, h(0.92)), (SIDE, y + 0.02, Z_BELT), "paint", "chassis")
        m.box((0.875, y - 0.055, h(1.22)), (SIDE - 0.01, y - 0.035, h(1.40)), "light_red", "chassis", light=l["tail"])
        m.box((0.875, y - 0.058, h(1.30)), (SIDE - 0.01, y - 0.054, h(1.38)), "light_red", "chassis", light=l["brake"])
        m.box((0.875, y - 0.055, h(1.10)), (SIDE - 0.01, y - 0.035, h(1.21)), "light_amber", "chassis", light=l["ind"])
        m.box((0.875, y - 0.055, h(0.95)), (SIDE - 0.01, y - 0.035, h(1.09)), "light_clear", "chassis", light=l["rev"])
    tail(mb, dict(tail=4, brake=10, ind=8, rev=13))
    with mb.mirrored():
        tail(mb, dict(tail=3, brake=9, ind=7, rev=12))
    # fuel door (driver side)
    with mb.mirrored():
        mb.rbox((SIDE - 0.003, -1.42, h(1.18)), (SIDE + 0.004, -1.22, h(1.34)), 0.02, "paint", "petrolcap")


def tailgate(mb):
    b = "boot"
    y0, y1 = Y_BED_R - 0.065, Y_BED_R - 0.005
    mb.box((-0.86, y0, h(0.93)), (0.86, y1, Z_BELT - 0.005), "paint", b)
    mb.box((-0.86, y0 - 0.005, Z_BELT - 0.03), (0.86, y1, Z_BELT + 0.01), "plastic", b)
    mb.rbox((-0.14, y0 - 0.012, h(1.33)), (0.14, y0, h(1.37)), 0.01, "gloss_black", b)
    mb.decal((0, y0 - 0.002, h(1.17)), (0, -1, 0), (0, 0, 1), 0.30, 0.15, "badge_gmc", b)
    mb.decal((-0.49, y0 - 0.002, h(1.035)), (0, -1, 0), (0, 0, 1), 0.26, 0.065, "badge_at4x", b)
    mb.decal((0, y0 - 0.002, h(1.30)), (0, -1, 0), (0, 0, 1), 0.90, 0.11, "badge_sierra", b)


def rear_bumper(mb):
    b = "bumper_r"
    rings = []
    for x in [-1.0, -0.96, -0.86, 0.0, 0.86, 0.96, 1.0]:
        ax = abs(x)
        yr = -2.945 + 0.12 * max(0.0, (ax - 0.86) / 0.14) ** 2
        rings.append([(x, yr + dy, h(0.48) + dz) for dy, dz in [(0.20, 0.0), (0.0, 0.0), (0.0, 0.24), (0.06, 0.28),
                                                                   (0.20, 0.28)]])
    mb.loft(rings, "steel", b)
    # corner step pads
    for s in (-1, 1):
        mb.box((s * 0.98 if s < 0 else 0.70, -2.955, h(0.74)), (-0.70 if s < 0 else 0.98, -2.80, h(0.765)), "plastic", b)
    # licence plate recess + hitch receiver
    mb.box((-0.18, -2.95, h(0.50)), (0.18, -2.93, h(0.70)), "black", b)
    mb.box((-0.04, -2.98, h(0.38)), (0.04, -2.85, h(0.46)), "steel", b)


def underbody(mb):
    k = "black"
    # frame rails
    both(mb, lambda m: m.box((0.44, -2.75, h(0.42)), (0.54, 2.62, h(0.62)), k, "chassis"))
    for y in (2.4, 1.2, 0.0, -1.2, -2.4):
        mb.box((-0.48, y - 0.04, h(0.46)), (0.48, y + 0.04, h(0.58)), k, "chassis")
    # front IFS: half shafts, control arms
    for s in (-1, 1):
        mb.cylinder((s * 0.15, FAX, WZ), (s * (TRACK - 0.10), FAX, WZ), 0.035, "steel", "chassis", seg=8)
        mb.box((s * 0.30 if s > 0 else -(TRACK - 0.12), FAX - 0.20, WZ - 0.12),
               (TRACK - 0.12 if s > 0 else -0.30, FAX + 0.10, WZ - 0.08), k, "chassis")
        # DSSV dampers (gold)
        mb.cylinder((s * 0.62, FAX - 0.05, WZ - 0.05), (s * 0.58, FAX - 0.05, WZ + 0.38), 0.035, "gold", "chassis", seg=10)
        mb.cylinder((s * 0.62, RAX + 0.18, WZ - 0.05), (s * 0.56, RAX + 0.25, WZ + 0.30), 0.035, "gold", "chassis", seg=10)
    mb.box((-0.16, FAX - 0.12, WZ - 0.12), (0.16, FAX + 0.12, WZ + 0.10), "steel", "chassis")    # front diff
    # rear solid axle + diff + leaf springs
    mb.cylinder((-TRACK + 0.10, RAX, WZ), (TRACK - 0.10, RAX, WZ), 0.055, "steel", "chassis", seg=12)
    mb.cylinder((0, RAX - 0.05, WZ), (0, RAX + 0.16, WZ), 0.15, "steel", "chassis", seg=16)
    for s in (-1, 1):
        mb.tube([(s * 0.50, RAX + 0.72, WZ + 0.14), (s * 0.50, RAX, WZ + 0.02), (s * 0.50, RAX - 0.70, WZ + 0.14)],
                0.035, k, "chassis", seg=6)
    # transmission, transfer case, driveshaft
    mb.cylinder((0, 1.45, h(0.78)), (0, 0.55, h(0.70)), 0.17, "steel", "chassis", seg=12, r1=0.12)
    mb.box((-0.18, 0.25, h(0.58)), (0.18, 0.55, h(0.80)), "steel", "chassis")
    mb.cylinder((0, 0.25, h(0.66)), (0, RAX + 0.15, WZ + 0.02), 0.045, "steel", "chassis", seg=10)
    mb.cylinder((0, FAX - 0.12, WZ), (0.05, 0.55, h(0.66)), 0.035, "steel", "chassis", seg=8)
    # fuel tank
    mb.rbox((0.12, -1.65, h(0.40)), (0.86, -0.95, h(0.62)), 0.04, k, "chassis")
    # exhaust: from the engine, muffler under the cab, dual tips under the rear bumper
    mb.tube([(0.30, 1.55, h(0.85)), (0.30, 1.20, h(0.50)), (0.25, 0.20, h(0.48)), (0.25, -0.40, h(0.48))],
            0.035, "steel", "chassis", seg=8)
    mb.rbox((0.05, -0.85, h(0.38)), (0.40, -0.40, h(0.56)), 0.05, "steel", "chassis")
    for s in (-1, 1):
        mb.tube([(s * 0.20, -0.85, h(0.46)), (s * 0.50, -1.30, h(0.46)), (s * 0.62, -2.10, h(0.44)),
                 (s * 0.62, -2.80, h(0.42))], 0.033, "steel", "chassis", seg=8)
    # spare tire under the bed
    with mb.at((0, -2.35, h(0.50)), Matrix.Rotation(math.pi / 2, 3, "Y")):
        mb.lathe([(0.20, -0.13), (0.40, -0.12), (0.42, 0.0), (0.40, 0.12), (0.20, 0.13)], "tire", "chassis", seg=20,
                 close=True)
    # wheel-well liners
    for y in (FAX, RAX):
        for s in (-1, 1):
            m = Matrix.Scale(-1, 4, (1, 0, 0)) if s < 0 else Matrix.Identity(4)
            with mb.at((0, 0, 0)) if s > 0 else mb.mirrored():
                mb.arch_band(y, WZ, ARCH_R + 0.01, ARCH_R + 0.03, 0.62, 0.995, -8, 188, "black", "chassis", seg=18)


def exhaust_tips(mb):
    """Stock dual rear exhaust tips (misc_b)."""
    for s in (-1, 1):
        mb.cylinder((s * 0.62, -2.80, h(0.42)), (s * 0.62, -2.93, h(0.42)), 0.048, "chrome", "misc_b", seg=14)


def flares(mb):
    """Black arch mouldings (misc_d)."""
    for y in (FAX, RAX):
        def f(m, y=y):
            m.arch_band(y, WZ, ARCH_R - 0.005, ARCH_R + 0.055, SIDE - 0.01, SIDE + 0.03,
                        -4 if y == FAX else -2, 184, "plastic", "misc_d", seg=20)
        both(mb, f)


def rock_rails(mb):
    """Factory AT4X rock rails (misc_a)."""
    def r(m):
        m.tube([(1.035, Y_FDOOR - 0.05, h(0.58)), (1.06, Y_FDOOR - 0.15, h(0.52)), (1.06, Y_CDOOR + 0.10, h(0.52)),
                (1.035, Y_CDOOR, h(0.58))], 0.04, "black", "misc_a", seg=10)
        for y in (Y_FDOOR - 0.25, Y_BPIL, Y_CDOOR + 0.25):
            m.box((0.88, y - 0.03, h(0.50)), (1.04, y + 0.03, h(0.56)), "black", "misc_a")
    both(mb, r)


def interior(mb):
    # floor
    mb.box((-0.88, Y_CAB + 0.02, h(0.62)), (0.88, Y_COWL - 0.04, h(0.66)), "carpet", "chassis")
    # dashboard
    mb.loft([[(x, Y_COWL - 0.04, z) for x, z in rrect(0, h(1.20), 0.90, 0.24, 0.05, 2)],
             [(x, 0.95, z) for x, z in rrect(0, h(1.24), 0.90, 0.20, 0.08, 2)]], "trim", "chassis")
    mb.decal((-0.42, 0.945, h(1.35)), (0, -1, 0.3), (0, 0.3, 1), 0.40, 0.18, "dash", "chassis")
    mb.decal((0, 0.94, h(1.30)), (0, -1, 0.2), (0, 0.2, 1), 0.28, 0.20, "screen", "chassis")
    # centre console
    mb.box((-0.12, -0.10, h(0.66)), (0.12, 0.95, h(1.02)), "trim", "chassis")
    # steering column
    mb.cylinder((-0.42, 0.95, h(1.22)), (-0.42, 0.80, h(1.30)), 0.04, "black", "chassis", seg=10)


def seats(mb):
    """Front buckets and rear bench (misc_h)."""
    b = "misc_h"
    for s in (-1, 1):
        x = 0.42 * s
        mb.rbox((x - 0.26, 0.00, h(0.78)), (x + 0.26, 0.55, h(0.90)), 0.04, "leather", b)
        mb.loft([[(x + dx, 0.02, h(0.90) + dz) for dx, dz in rrect(0, 0.04, 0.25, 0.04, 0.03, 2)],
                 [(x + dx, -0.10, h(1.55) + dz) for dx, dz in rrect(0, 0.04, 0.23, 0.04, 0.03, 2)]], "leather", b)
        mb.rbox((x - 0.13, -0.13, h(1.58)), (x + 0.13, -0.05, h(1.76)), 0.03, "leather", b)
        mb.box((x - 0.20, -0.14, h(1.10)), (x + 0.20, -0.12, h(1.12)), "leather_red", b)
    mb.rbox((-0.80, -0.82, h(0.80)), (0.80, -0.35, h(0.92)), 0.04, "leather", b)
    mb.loft([[(dx, -0.80, h(0.92) + dz) for dx, dz in rrect(0, 0.04, 0.78, 0.04, 0.03, 2)],
             [(dx, -0.88, h(1.55) + dz) for dx, dz in rrect(0, 0.04, 0.76, 0.04, 0.03, 2)]], "leather", b)


def steering_wheel(mb):
    """Steering wheel modelled around its bone (rotates with steering input)."""
    b = "steeringwheel"
    c = Vector((-0.42, 0.78, h(1.32)))
    rot = Matrix.Rotation(math.radians(-24), 4, "X")
    with mb.push_ctx(Matrix.Translation(c) @ rot):
        # rim: lathe around Y axis -> rotate lathe (X axis) into Y
        with mb.push_ctx(Matrix.Rotation(math.radians(90), 4, "Z")):
            mb.lathe([(0.175, -0.015), (0.19, -0.02), (0.20, 0.0), (0.19, 0.02), (0.175, 0.015)], "leather", b,
                     seg=24, close=True)
        mb.cylinder((0, -0.01, 0), (0, 0.04, 0), 0.06, "black", b, seg=12)
        for a in (180, 270, 0):
            ra = math.radians(a)
            mb.cylinder((0, 0, 0), (0.18 * math.cos(ra), 0, 0.18 * math.sin(ra)), 0.014, "black", b, seg=6)


def build_body(mb):
    """Everything on the main skinned model (except the wheels)."""
    front_clip(mb)
    engine_cover(mb)
    airbox(mb)
    hood(mb)
    fascia(mb)
    grille(mb)
    front_bumper(mb)
    skids(mb)
    cab(mb)
    windows(mb)
    doors(mb)
    bed(mb)
    tailgate(mb)
    rear_bumper(mb)
    underbody(mb)
    exhaust_tips(mb)
    flares(mb)
    rock_rails(mb)
    interior(mb)
    seats(mb)
    steering_wheel(mb)


# ---------------------------------------------------------------------------------------------- wheel

def build_wheel(mb, bone="wheel_lf", rwl=False, rim_style="at4x", tire_r=TIRE_R, rim_r=RIM_R, width=TIRE_W):
    """Left-front wheel centred on its bone: outer face towards -X. Tyre + rim + lugs."""
    hw = width / 2
    side = "sidewall_rwl" if rwl else "sidewall"
    # tyre carcass: outer sidewall, tread, inner sidewall
    mb.lathe([(rim_r + 0.012, -hw + 0.03), (rim_r + 0.05, -hw + 0.005), (tire_r - 0.05, -hw - 0.004),
              (tire_r - 0.015, -hw + 0.012)], side, bone, seg=40, polar_uv=(rim_r, tire_r, 4))
    mb.lathe([(tire_r - 0.015, -hw + 0.012), (tire_r, -hw + 0.04), (tire_r, hw - 0.04), (tire_r - 0.015, hw - 0.012)],
             "tire", bone, seg=40)
    mb.lathe([(tire_r - 0.015, hw - 0.012), (tire_r - 0.05, hw + 0.004), (rim_r + 0.05, hw - 0.005),
              (rim_r + 0.012, hw - 0.03)], "sidewall", bone, seg=40)
    # mud-terrain tread blocks (two staggered rows + shoulder lugs)
    n = 26
    for i in range(n):
        a = 2 * math.pi * i / n
        for row, (x0, x1, off) in enumerate(((-hw + 0.02, -0.01, 0.0), (0.01, hw - 0.02, 0.5))):
            aa = a + off * 2 * math.pi / n
            with mb.push_ctx(Matrix.Rotation(aa, 4, "X")):
                mb.box((x0, -0.035, tire_r - 0.003), (x1, 0.035, tire_r + 0.018), "tire", bone)
        with mb.push_ctx(Matrix.Rotation(a + math.pi / n, 4, "X")):
            mb.box((-hw - 0.01, -0.03, tire_r - 0.07), (-hw + 0.03, 0.03, tire_r - 0.01), "tire", bone)
            mb.box((hw - 0.03, -0.03, tire_r - 0.07), (hw + 0.01, 0.03, tire_r - 0.01), "tire", bone)
    build_rim(mb, bone, rim_style, rim_r, hw)


def build_rim(mb, bone, style, rim_r, hw):
    x_face = -hw + 0.035
    # barrel + lip
    mb.lathe([(rim_r + 0.012, x_face - 0.005), (rim_r + 0.02, x_face), (rim_r, x_face + 0.02),
              (rim_r - 0.01, hw - 0.04), (rim_r + 0.012, hw - 0.03)], "rim", bone, seg=36)
    mb.lathe([(rim_r - 0.012, hw - 0.05), (0.07, hw - 0.06)], "rim_black", bone, seg=24)
    spokes = {"at4x": 6, "salta": 6, "bead": 6, "steelie": 0, "forged": 10, "denali": 7}.get(style, 6)
    if style == "steelie":
        mb.lathe([(rim_r - 0.01, x_face + 0.03), (0.15, x_face + 0.05), (0.12, x_face + 0.02), (0.06, x_face + 0.02)],
                 "rim", bone, seg=32)
        for i in range(8):
            a = 2 * math.pi * i / 8
            mb.cylinder((x_face + 0.03, 0.17 * math.cos(a), 0.17 * math.sin(a)),
                        (x_face + 0.06, 0.17 * math.cos(a), 0.17 * math.sin(a)), 0.018, "rim_black", bone, seg=8)
    else:
        for i in range(spokes):
            a = 2 * math.pi * i / spokes
            with mb.push_ctx(Matrix.Rotation(a, 4, "X")):
                w = 0.026 if spokes > 7 else 0.038
                mb.loft([[(x_face + 0.01, -w, 0.07), (x_face + 0.05, -w, 0.07), (x_face + 0.05, w, 0.07),
                          (x_face + 0.01, w, 0.07)],
                         [(x_face - 0.002, -w * 1.3, rim_r - 0.01), (x_face + 0.04, -w * 1.3, rim_r - 0.01),
                          (x_face + 0.04, w * 1.3, rim_r - 0.01), (x_face - 0.002, w * 1.3, rim_r - 0.01)]],
                        "rim", bone)
    if style in ("bead", "salta"):
        mb.lathe([(rim_r + 0.022, x_face - 0.012), (rim_r - 0.012, x_face - 0.012)], "rim_black", bone, seg=36)
        for i in range(24):
            a = 2 * math.pi * i / 24
            mb.cylinder((x_face - 0.012, (rim_r + 0.005) * math.cos(a), (rim_r + 0.005) * math.sin(a)),
                        (x_face - 0.022, (rim_r + 0.005) * math.cos(a), (rim_r + 0.005) * math.sin(a)), 0.006,
                        "chrome", bone, seg=6)
    # hub + centre cap + lug nuts
    mb.lathe([(0.075, x_face + 0.01), (0.065, x_face - 0.005), (0.0, x_face - 0.005)], "rim_black", bone, seg=20)
    mb.decal((x_face - 0.006, 0, 0), (-1, 0, 0), (0, 0, 1), 0.08, 0.04, "badge_gmc", bone)
    for i in range(6):
        a = 2 * math.pi * i / 6 + math.pi / 6
        mb.cylinder((x_face + 0.01, 0.1 * math.cos(a), 0.1 * math.sin(a)),
                    (x_face - 0.01, 0.1 * math.cos(a), 0.1 * math.sin(a)), 0.012, "chrome", bone, seg=6)
