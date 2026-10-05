"""Fit a Blender camera to a reference photo by silhouette matching.

The dealer photos show a black truck on a white studio background, so the truck's silhouette can be extracted by
thresholding. We render the model's alpha at low resolution and search camera azimuth / elevation / distance /
target height / focal length (Nelder-Mead) to maximise silhouette IoU.

    python tools/model/fitcam.py OUT_DIR PHOTO_DIR 02,06,03,04
Writes OUT_DIR/cams.json and overlay images (photo silhouette vs render silhouette).
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
from mathutils import Vector
from PIL import Image, ImageChops, ImageFilter, ImageOps

import preview
import textures

W, H = 256, 192

INITIAL = {   # azimuth deg (0 = +X side, 90 = front), elevation deg, distance m, target z, lens mm
    "02": (12.0, 2.0, 8.0, -0.05, 35.0),
    "06": (130.0, 4.0, 7.0, -0.05, 32.0),
    "01": (40.0, 5.0, 7.0, -0.05, 32.0),
    "03": (-55.0, 9.0, 7.5, -0.10, 32.0),
    "04": (-140.0, 4.0, 7.5, -0.05, 32.0),
}


def photo_mask(path):
    im = Image.open(path).convert("L").resize((W, H), Image.LANCZOS)
    m = im.point(lambda v: 255 if v < 95 else 0)
    m = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    return fill_holes(m)


def fill_holes(m):
    inv = ImageOps.invert(m)
    # flood fill background from the border on the inverted mask; whatever isn't reached is a hole
    from PIL import ImageDraw
    filled = inv.copy()
    ImageDraw.floodfill(filled, (0, 0), 128)
    ImageDraw.floodfill(filled, (W - 1, 0), 128)
    holes = filled.point(lambda v: 255 if v == 255 else 0)
    return ImageChops.lighter(m, holes)


def cam_from_params(p):
    az, el, dist, tz, lens = p
    a, e = math.radians(az), math.radians(el)
    target = Vector((0.0, 0.0, tz))
    loc = target + Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))) * dist
    return loc, target, lens


class Renderer:
    def __init__(self, out):
        self.out = out
        sc = bpy.context.scene
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 1
        sc.cycles.use_denoising = False
        sc.render.film_transparent = True
        sc.render.resolution_x, sc.render.resolution_y = W, H
        sc.render.image_settings.color_mode = "RGBA"
        cd = bpy.data.cameras.new("fitcam")
        cd.sensor_width = 36
        self.cam = bpy.data.objects.new("fitcam", cd)
        bpy.context.collection.objects.link(self.cam)
        sc.camera = self.cam
        self.path = os.path.join(out, "_fit.png")

    def mask(self, p):
        loc, tgt, lens = cam_from_params(p)
        self.cam.location = loc
        self.cam.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
        self.cam.data.lens = lens
        bpy.context.scene.render.filepath = self.path
        bpy.ops.render.render(write_still=True)
        a = Image.open(self.path).split()[-1]
        return fill_holes(a.point(lambda v: 255 if v > 128 else 0))


def iou(a, b):
    inter = ImageChops.multiply(a, b).histogram()[255]
    union = ImageChops.lighter(a, b).histogram()[255]
    return inter / max(union, 1)


def nelder_mead(f, x0, steps, iters=70):
    pts = [list(x0)] + [[x0[j] + (steps[j] if j == i else 0) for j in range(len(x0))] for i in range(len(x0))]
    vals = [f(p) for p in pts]
    for _ in range(iters):
        order = sorted(range(len(pts)), key=lambda i: vals[i])
        pts = [pts[i] for i in order]
        vals = [vals[i] for i in order]
        n = len(x0)
        c = [sum(p[j] for p in pts[:-1]) / n for j in range(n)]
        xr = [c[j] + (c[j] - pts[-1][j]) for j in range(n)]
        fr = f(xr)
        if fr < vals[0]:
            xe = [c[j] + 2 * (c[j] - pts[-1][j]) for j in range(n)]
            fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = [c[j] + 0.5 * (pts[-1][j] - c[j]) for j in range(n)]
            fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                for i in range(1, len(pts)):
                    pts[i] = [pts[0][j] + 0.5 * (pts[i][j] - pts[0][j]) for j in range(n)]
                    vals[i] = f(pts[i])
    best = min(range(len(pts)), key=lambda i: vals[i])
    return pts[best], vals[best]


def main():
    out, photo_dir, keys = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    os.makedirs(out, exist_ok=True)
    tex_png = os.path.join(out, "_tex")
    textures.write_all(os.path.join(out, "_dds"), tex_png)
    preview.build_scene(tex_png, (0.01, 0.01, 0.01))
    r = Renderer(out)
    cams = {}
    cam_file = os.path.join(out, "cams.json")
    if os.path.exists(cam_file):
        cams = json.load(open(cam_file))
    for k in keys:
        target = photo_mask(os.path.join(photo_dir, f"AT4X_{k}.jpg"))
        f = lambda p: -iou(target, r.mask(p))
        x0 = cams.get(k, {}).get("params", INITIAL[k])
        best, val = nelder_mead(f, x0, [8.0, 3.0, 1.0, 0.15, 4.0], iters=60)
        best, val = nelder_mead(f, best, [2.0, 1.0, 0.3, 0.05, 1.5], iters=40)
        loc, tgt, lens = cam_from_params(best)
        cams[k] = dict(params=best, iou=-val, location=list(loc), target=list(tgt), lens=lens)
        rm = r.mask(best)
        overlay = Image.merge("RGB", (target, rm, Image.new("L", (W, H), 0)))
        overlay.resize((W * 3, H * 3)).save(os.path.join(out, f"fit_{k}.png"))
        print(f"{k}: IoU {-val:.3f} params {[round(v, 3) for v in best]}", flush=True)
        json.dump(cams, open(cam_file, "w"), indent=1)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
