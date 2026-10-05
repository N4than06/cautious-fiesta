"""Render preview images of the AT4X with Cycles (no Sollumz needed).

    python tools/model/preview.py OUT_DIR [--color R,G,B]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
from mathutils import Matrix, Vector

import at4x_body as body
import textures
from geom import MeshBuilder, finalize_mesh

LOOK = {
    # key: (texture or None, base colour, metallic, roughness, emission strength)
    "paint": (None, None, 0.6, 0.28, 0),
    "paint2": (None, (0.05, 0.05, 0.05), 0.4, 0.35, 0),
    "plastic": ("at4x_plastic", None, 0.0, 0.75, 0),
    "black": ("at4x_black", None, 0.0, 0.6, 0),
    "gloss_black": ("at4x_black", None, 0.2, 0.25, 0),
    "steel": ("at4x_steel", None, 0.8, 0.45, 0),
    "chrome": (None, (0.85, 0.86, 0.88), 1.0, 0.06, 0),
    "alu": ("at4x_alu", None, 0.9, 0.35, 0),
    "red": (None, (0.55, 0.01, 0.015), 0.1, 0.3, 0),
    "gold": (None, (0.75, 0.55, 0.12), 1.0, 0.25, 0),
    "grille": ("at4x_grille", None, 0.3, 0.4, 0),
    "mesh": ("at4x_mesh", None, 0.3, 0.4, 0),
    "bedliner": ("at4x_bedliner", None, 0.0, 0.9, 0),
    "engine_cover": ("at4x_engine_cover", None, 0.0, 0.5, 0),
    "whipple": ("at4x_whipple", None, 0.6, 0.3, 0),
    "reflector": (None, (0.6, 0.62, 0.65), 1.0, 0.15, 0),
    "tire": ("at4x_tire", None, 0.0, 0.85, 0),
    "sidewall": ("at4x_sidewall", None, 0.0, 0.8, 0),
    "sidewall_rwl": ("at4x_sidewall_rwl", None, 0.0, 0.8, 0),
    "rim": (None, (0.03, 0.03, 0.035), 0.5, 0.35, 0),
    "rim_black": (None, (0.02, 0.02, 0.02), 0.3, 0.4, 0),
    "glass": (None, (0.02, 0.025, 0.03), 0.0, 0.02, 0),
    "glass_in": (None, (0.02, 0.025, 0.03), 0.0, 0.02, 0),
    "light_clear": (None, (0.9, 0.92, 0.95), 0.0, 0.05, 2.0),
    "light_led": (None, (1.0, 1.0, 1.0), 0.0, 0.05, 6.0),
    "light_red": (None, (0.6, 0.01, 0.01), 0.0, 0.1, 1.5),
    "light_amber": (None, (0.9, 0.35, 0.02), 0.0, 0.1, 1.0),
    "leather": ("at4x_leather", None, 0.0, 0.6, 0),
    "leather_red": ("at4x_leather_red", None, 0.0, 0.6, 0),
    "carpet": ("at4x_carpet", None, 0.0, 0.95, 0),
    "trim": ("at4x_plastic", None, 0.0, 0.6, 0),
    "dash": ("at4x_dash", None, 0.0, 0.4, 1.0),
    "screen": ("at4x_screen", None, 0.0, 0.3, 1.0),
    "badge_gmc": ("at4x_badge_gmc", None, 0.3, 0.3, 0),
    "badge_at4x": ("at4x_badge_at4x", None, 0.3, 0.3, 0),
    "badge_sierra": ("at4x_badge_sierra", None, 0.3, 0.3, 0),
}


class PreviewMaterials(dict):
    def __init__(self, tex_dir, paint_rgb):
        super().__init__()
        self.tex_dir, self.paint_rgb = tex_dir, paint_rgb

    def __missing__(self, key):
        tex, col, met, rough, emis = LOOK[key]
        m = bpy.data.materials.new(key)
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        if key.startswith("paint") and col is None:
            col = self.paint_rgb
        if tex:
            img = bpy.data.images.load(os.path.join(self.tex_dir, tex + ".png"), check_existing=True)
            node = nt.nodes.new("ShaderNodeTexImage")
            node.image = img
            uv = nt.nodes.new("ShaderNodeUVMap")
            uv.uv_map = "UVMap 0"
            nt.links.new(uv.outputs[0], node.inputs[0])
            nt.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
            if key.startswith("badge") or key == "badge_sierra":
                nt.links.new(node.outputs["Alpha"], bsdf.inputs["Alpha"])
        else:
            bsdf.inputs["Base Color"].default_value = (*col, 1)
        bsdf.inputs["Metallic"].default_value = met
        bsdf.inputs["Roughness"].default_value = rough
        if key.startswith("paint"):
            bsdf.inputs["Coat Weight"].default_value = 1.0
            bsdf.inputs["Coat Roughness"].default_value = 0.03
        if key in ("glass", "glass_in"):
            bsdf.inputs["Transmission Weight"].default_value = 0.6
            bsdf.inputs["Alpha"].default_value = 0.75
        if emis:
            bsdf.inputs["Emission Color"].default_value = (*(col or (1, 1, 1)), 1)
            bsdf.inputs["Emission Strength"].default_value = emis
        self[key] = m
        return m


def build_scene(tex_dir, paint_rgb, wheel_style="at4x", extra_builders=()):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = PreviewMaterials(tex_dir, paint_rgb)
    mb = MeshBuilder()
    body.build_body(mb)
    for fn in extra_builders:
        fn(mb)
    mesh = mb.to_mesh("at4x", mats)
    finalize_mesh(mesh)
    obj = bpy.data.objects.new("at4x", mesh)
    bpy.context.collection.objects.link(obj)

    wb = MeshBuilder()
    body.build_wheel(wb, rim_style=wheel_style)
    wmesh = wb.to_mesh("wheel", mats)
    finalize_mesh(wmesh)
    for sx in (-1, 1):
        for y in (body.FAX, body.RAX):
            w = bpy.data.objects.new("wheel", wmesh)
            w.location = (sx * body.TRACK, y, body.WZ)
            if sx > 0:
                w.rotation_euler = (0, 0, math.pi)
            bpy.context.collection.objects.link(w)
    return obj, mats


def setup_render(res=(1600, 900), samples=48):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("w")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    sky = world.node_tree.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA" if hasattr(sky, "sky_type") else sky.sky_type
    try:
        sky.sun_elevation = math.radians(35)
        sky.sun_rotation = math.radians(140)
    except Exception:
        pass
    world.node_tree.links.new(sky.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = 0.08
    # ground
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, body.GROUND))
    g = bpy.context.object
    gm = bpy.data.materials.new("ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.115, 0.11, 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    g.data.materials.append(gm)
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 2.2
    sun.angle = math.radians(3)
    so = bpy.data.objects.new("sun", sun)
    so.rotation_euler = (math.radians(50), 0, math.radians(140))
    bpy.context.collection.objects.link(so)
    for loc, e in (((6, 6, 4), 250), ((-6, -5, 3), 150), ((-4, 7, 2), 120)):
        L = bpy.data.lights.new("area", "AREA")
        L.energy = e
        L.size = 4
        lo = bpy.data.objects.new("area", L)
        lo.location = loc
        bpy.context.collection.objects.link(lo)
        d = Vector((0, 0, 0)) - Vector(loc)
        lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def shoot(path, loc, target=(0, 0, 0.1), lens=50):
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)


VIEWS = {
    "front_34": ((7.2, 7.6, 1.6), (0, 0.3, 0.0), 50),
    "rear_34": ((-6.8, -8.0, 2.2), (0, -0.4, 0.0), 50),
    "side": ((10.5, 0.0, 0.6), (0, 0, 0.1), 50),
    "front": ((0.0, 10.0, 0.9), (0, 0, 0.15), 50),
    "rear": ((0.0, -10.0, 1.2), (0, 0, 0.15), 50),
    "top": ((0.01, 0.0, 13.0), (0, 0, 0), 45),
}

if __name__ == "__main__":
    out = sys.argv[1]
    rgb = (0.06, 0.065, 0.07)
    if "--color" in sys.argv:
        rgb = tuple(float(c) for c in sys.argv[sys.argv.index("--color") + 1].split(","))
    views = sys.argv[sys.argv.index("--views") + 1].split(",") if "--views" in sys.argv else list(VIEWS)
    samples = int(sys.argv[sys.argv.index("--samples") + 1]) if "--samples" in sys.argv else 48
    tex_png = os.path.join(out, "_tex")
    textures.write_all(os.path.join(out, "_dds"), tex_png)
    build_scene(tex_png, rgb)
    setup_render(samples=samples)
    for v in views:
        loc, tgt, lens = VIEWS[v]
        shoot(os.path.join(out, f"at4x_{v}.png"), loc, tgt, lens)
        print("rendered", v, flush=True)
    sys.stdout.flush()
    os._exit(0)
