"""Build the factory AT4X as a GTA V vehicle fragment (CodeWalker XML) with Sollumz.

    python tools/model/build_yft.py OUT_DIR [--no-lods]

Writes OUT_DIR/at4x.yft.xml (+ at4x_hi.yft.xml and the embedded textures folder). Import the XML with CodeWalker
(RPF Explorer > Import XML) into dlc/at4x/x64/vehicles.rpf to get the binary at4x.yft / at4x_hi.yft.

What gets built:
  * skeleton from at4x_body.bones() (doors, bonnet, boot, windows, bumpers, wheels, lights, misc_a..j)
  * one skinned body model (every part is weighted to its bone) with four LODs:
        VERYHIGH (full detail -> at4x_hi.yft), HIGH, MEDIUM, LOW (collapse-decimated copies)
  * the left-front wheel as a physics-child mesh (the game re-uses it for every wheel)
  * collision: convex hulls per physics bone (chassis split into nose / cab / bed so the bed is not one block),
    breakable glass on the windows and windscreens, a 16-sided cylinder per wheel
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402  (must come first: provides bmesh / mathutils)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import at4x_body as body  # noqa: E402
import materials  # noqa: E402
import sz  # noqa: E402
import textures  # noqa: E402
from at4x_dims import FAX, RAX, TIRE_R, TIRE_W, TRACK, WZ, Y_BED_F, Y_CAB_R, Y_HOOD_R  # noqa: E402
from geom import MeshBuilder, finalize_mesh  # noqa: E402

LOD_RATIOS = {"HIGH": 0.5, "MEDIUM": 0.2, "LOW": 0.06}

# physics bones: (collision material, mass kg, breakable glass)
PHYSICS = {
    "door_dside_f": ("CAR_METAL", 30.0, False), "door_pside_f": ("CAR_METAL", 30.0, False),
    "door_dside_r": ("CAR_METAL", 28.0, False), "door_pside_r": ("CAR_METAL", 28.0, False),
    "bonnet": ("CAR_METAL", 22.0, False), "boot": ("CAR_METAL", 30.0, False),
    "bumper_f": ("CAR_PLASTIC", 18.0, False), "bumper_r": ("CAR_METAL", 20.0, False),
    "windscreen": ("CAR_GLASS_MEDIUM", 10.0, True), "windscreen_r": ("CAR_GLASS_MEDIUM", 6.0, True),
    "window_lf": ("CAR_GLASS_WEAK", 4.0, True), "window_rf": ("CAR_GLASS_WEAK", 4.0, True),
    "window_lr": ("CAR_GLASS_WEAK", 4.0, True), "window_rr": ("CAR_GLASS_WEAK", 4.0, True),
}
CHASSIS_MASS = 2300.0
WHEEL_MASS = 35.0


def decimated(mesh, ratio, name, groups=()):
    """Collapse-decimated copy of `mesh` (keeps UVs, colours, materials and vertex weights; the temporary object
    needs the vertex groups or the evaluated mesh drops the skin weights)."""
    obj = bpy.data.objects.new("_dec", mesh)
    for g in groups:
        if g not in obj.vertex_groups:
            obj.vertex_groups.new(name=g)
    bpy.context.collection.objects.link(obj)
    mod = obj.modifiers.new("dec", "DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    out = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    out.name = name
    bpy.data.objects.remove(obj)
    finalize_mesh(out)
    return out


def add_uv2(mesh):
    """Vehicle shaders sample a third UV set; reuse UVMap 0 for it."""
    if "UVMap 2" not in mesh.uv_layers:
        src = mesh.uv_layers["UVMap 0"].data
        dst = mesh.uv_layers.new(name="UVMap 2").data
        buf = [0.0] * (len(src) * 2)
        src.foreach_get("uv", buf)
        dst.foreach_set("uv", buf)


def bone_vertices(mesh, group_index):
    """{group index: [world-space co]} from the deform weights written by MeshBuilder.to_mesh."""
    bm = bmesh.new()
    bm.from_mesh(mesh)
    dl = bm.verts.layers.deform.active
    out = {}
    for v in bm.verts:
        for gi in v[dl].keys():
            out.setdefault(gi, []).append(v.co.copy())
    bm.free()
    return out


def hull_mesh(points, origin, name):
    """Convex hull of points as a mesh in the space of a bone whose head is at `origin`."""
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p - origin)
    bmesh.ops.convex_hull(bm, input=bm.verts[:])
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def cylinder_mesh(radius, half_w, name, seg=16):
    bm = bmesh.new()
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for x in (-half_w, half_w):
            bm.verts.new((x, radius * math.cos(a), radius * math.sin(a)))
    bmesh.ops.convex_hull(bm, input=bm.verts[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def main():
    out_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "build/at4x")
    with_lods = "--no-lods" not in sys.argv
    sz.init()
    logs = sz.capture_logs()
    L = sz.SZ["LODLevel"]

    tex_dir = os.path.join(out_dir, "_dds")
    textures.write_all(tex_dir)
    mats = sz.Materials(materials.SPEC, sz.load_dds_images(tex_dir))

    frag = sz.Fragment("at4x", body.bones())
    gi = frag.group_index()

    # ---------------------------------------------------------------- body
    mb = MeshBuilder()
    body.build_body(mb)
    full = mb.to_mesh("at4x_body", mats, group_index=gi)
    finalize_mesh(full)
    add_uv2(full)
    lods = {L.VERYHIGH: full, L.HIGH: full}
    if with_lods:
        for lvl, r in LOD_RATIOS.items():
            lods[getattr(L, lvl)] = decimated(full, r, f"at4x_body_{lvl.lower()}", groups=list(gi))
    frag.add_skinned_model("at4x_body", lods)

    # ---------------------------------------------------------------- wheel (instanced by the game)
    wb = MeshBuilder()
    body.build_wheel(wb, bone="wheel_lf")
    wfull = wb.to_mesh("wheel_lf", mats)
    finalize_mesh(wfull)
    add_uv2(wfull)
    wlods = {L.VERYHIGH: wfull, L.HIGH: wfull}
    if with_lods:
        wlods[L.MEDIUM] = decimated(wfull, 0.3, "wheel_lf_medium")
        wlods[L.LOW] = decimated(wfull, 0.08, "wheel_lf_low")
    frag.add_bone_model("wheel_lf.child", "wheel_lf", wlods, physics_child=True)

    # ---------------------------------------------------------------- physics + collision
    names = list(gi)
    verts = bone_vertices(full, gi)
    frag.enable_physics("chassis")
    chassis_pts = []
    for name, idx in gi.items():
        if name not in PHYSICS and not name.startswith("wheel_"):
            chassis_pts += verts.get(idx, [])
    origin = frag.bone_head("chassis")
    for part, (lo, hi) in {"nose": (Y_HOOD_R - 0.05, 9.0), "cab": (Y_CAB_R - 0.03, Y_HOOD_R + 0.05),
                           "bed": (-9.0, Y_BED_F + 0.03)}.items():
        pts = [p for p in chassis_pts if lo <= p.y <= hi]
        if len(pts) >= 4:
            frag.add_bound("chassis", hull_mesh(pts, origin, f"chassis_{part}"), "CAR_METAL",
                           CHASSIS_MASS * {"nose": 0.35, "cab": 0.4, "bed": 0.25}[part])
    for bone, (cmat, mass, glass) in PHYSICS.items():
        pts = verts.get(gi[bone], [])
        if len(pts) < 4:
            print(f"warning: no geometry on {bone}, no collision", flush=True)
            continue
        frag.enable_physics(bone, strength=-1.0 if glass else 100.0)
        frag.add_bound(bone, hull_mesh(pts, frag.bone_head(bone), f"{bone}_col"), cmat, mass, window=glass)
    for side, x in (("l", -TRACK), ("r", TRACK)):
        for end, y in (("f", FAX), ("r", RAX)):
            bone = f"wheel_{side}{end}"
            frag.enable_physics(bone)
            frag.add_bound(bone, cylinder_mesh(TIRE_R, TIRE_W / 2, f"{bone}_col"), "RUBBER", WHEEL_MASS)

    tris = sum(len(p.vertices) - 2 for p in full.polygons)
    print(f"body: {tris} triangles (VERYHIGH), {len(names)} bones", flush=True)
    for lvl in ("HIGH", "MEDIUM", "LOW"):
        m = lods.get(getattr(L, lvl))
        if m is not None and m is not full:
            print(f"  {lvl}: {sum(len(p.vertices) - 2 for p in m.polygons)} triangles", flush=True)

    sz.export_selected([frag.obj], out_dir)
    for level, msg in logs:
        print(f"sollumz {level}: {msg}", flush=True)
    for root, _, files in os.walk(out_dir):
        for f in files:
            if f.endswith(".xml"):
                p = os.path.join(root, f)
                print(f"wrote {p} ({os.path.getsize(p) // 1024} KiB)", flush=True)
    sz.force_exit(1 if any(level == "error" for level, _ in logs) else 0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sz.force_exit(1)    # bpy hangs on a normal interpreter exit
