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
    "titanium": (None, (0.07, 0.09, 0.12), 0.9, 0.28, 0),
    "plate": ("at4x_plate", None, 0.0, 0.4, 0),
    "grille": ("at4x_grille", None, 0.3, 0.4, 0),
    "mesh": ("at4x_mesh", None, 0.3, 0.4, 0),
    "bedliner": ("at4x_bedliner", None, 0.0, 0.9, 0),
    "engine_cover": ("at4x_engine_cover", None, 0.0, 0.5, 0),
    "whipple": ("at4x_whipple", None, 0.6, 0.3, 0),
    "reflector": (None, (0.6, 0.62, 0.65), 1.0, 0.15, 0),
    "tire": ("at4x_tire", None, 0.0, 0.85, 0),
    "sidewall": ("at4x_sidewall", None, 0.0, 0.8, 0),
    "sidewall_rwl": ("at4x_sidewall_rwl", None, 0.0, 0.8, 0),
    "rim": (None, (0.012, 0.012, 0.014), 0.3, 0.12, 0),
    "rim_black": (None, (0.02, 0.02, 0.02), 0.3, 0.4, 0),
    "glass": (None, (0.015, 0.018, 0.02), 0.0, 0.02, 0),
    "glass_in": (None, (0.015, 0.018, 0.02), 0.0, 0.02, 0),
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
    "badge_gmc": ("at4x_badge_gmc", None, 0.8, 0.2, 0),
    "badge_at4x": ("at4x_badge_at4x", None, 0.8, 0.2, 0),
    "badge_sierra": ("at4x_badge_sierra", None, 0.8, 0.2, 0),
    "badge_v8": ("at4x_badge_v8", None, 0.3, 0.3, 0),
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
            if key.startswith("badge"):
                nt.links.new(node.outputs["Alpha"], bsdf.inputs["Alpha"])
                m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
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


def setup_render(res=(1600, 900), samples=48, studio="grey"):
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
    # neutral studio gradient: bright overhead, darker horizon
    grad = world.node_tree.nodes.new("ShaderNodeTexGradient")
    coord = world.node_tree.nodes.new("ShaderNodeTexCoord")
    mapn = world.node_tree.nodes.new("ShaderNodeMapping")
    mapn.inputs["Rotation"].default_value = (0, math.radians(-90), 0)
    ramp = world.node_tree.nodes.new("ShaderNodeValToRGB")
    if studio == "white":
        ramp.color_ramp.elements[0].color = (0.55, 0.56, 0.58, 1)
        ramp.color_ramp.elements[1].color = (1.6, 1.6, 1.62, 1)
    else:
        ramp.color_ramp.elements[0].color = (0.30, 0.31, 0.33, 1)
        ramp.color_ramp.elements[1].color = (0.95, 0.96, 0.98, 1)
    nt = world.node_tree
    nt.links.new(coord.outputs["Generated"], mapn.inputs["Vector"])
    nt.links.new(mapn.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs[1].default_value = 0.9
    # ground
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, body.GROUND))
    g = bpy.context.object
    gm = bpy.data.materials.new("ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (
        (0.75, 0.75, 0.76, 1) if studio == "white" else (0.18, 0.18, 0.18, 1))
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


def shoot(path, loc, target=(0, 0, 0.1), lens=50, roll=0.0):
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = loc
    d = Vector(target) - Vector(loc)
    rot = d.to_track_quat("-Z", "Y").to_matrix() @ Matrix.Rotation(roll, 3, "Z")
    cam.rotation_euler = rot.to_euler()
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

# Approximate cameras of the dealer reference photos (1024x768): name -> (location, target, lens)
PHOTO_CAMS = {
    "02": ((8.6, 1.9, 0.15), (0.0, 0.15, -0.05), 38),
    "06": ((-5.6, 6.6, 0.05), (0.0, 0.25, -0.05), 32),
    "01": ((6.3, 5.2, 0.25), (0.0, 0.15, -0.05), 32),
    "03": ((5.0, -7.2, 1.15), (0.0, -0.55, -0.1), 32),
    "04": ((-6.4, -6.0, 0.35), (0.0, -0.4, -0.05), 32),
}


def compare(out, photo_dir, keys):
    from PIL import Image
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1024, 768
    cams = {}
    cam_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference_cameras.json")
    if os.path.exists(cam_file):
        import json
        cams = json.load(open(cam_file))
    for k in keys:
        roll = 0.0
        if k in cams:
            p = cams[k]["params"]
            loc, tgt, roll, lens = p[0:3], p[3:6], p[6], p[7]
        else:
            loc, tgt, lens = PHOTO_CAMS[k]
        path = os.path.join(out, f"render_{k}.png")
        shoot(path, loc, tgt, lens, roll)
        a = Image.open(os.path.join(photo_dir, f"AT4X_{k}.jpg")).convert("RGB").resize((1024, 768))
        b = Image.open(path).convert("RGB")
        c = Image.new("RGB", (2048, 768), "white")
        c.paste(a, (0, 0))
        c.paste(b, (1024, 0))
        c.save(os.path.join(out, f"compare_{k}.jpg"), quality=90)
        print("compared", k, flush=True)


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
    studio = "white" if "--white" in sys.argv else "grey"
    setup_render(samples=samples, studio=studio)
    if "--compare" in sys.argv:
        compare(out, sys.argv[sys.argv.index("--compare") + 1], sys.argv[sys.argv.index("--compare") + 2].split(","))
        views = []
    for v in views:
        loc, tgt, lens = VIEWS[v]
        shoot(os.path.join(out, f"at4x_{v}.png"), loc, tgt, lens)
        print("rendered", v, flush=True)
    sys.stdout.flush()
    os._exit(0)
