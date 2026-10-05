"""Thin layer over the Sollumz add-on: builds GTA V fragments (vehicles and mod parts) in a Blender
scene and exports them as CodeWalker XML (.yft.xml + textures).

Must run inside Blender's Python (the `bpy` module) with Sollumz installed as an add-on named "Sollumz".
"""
import os
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

SZ = {}


def init():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    res = bpy.ops.preferences.addon_enable(module="Sollumz")
    if res != {"FINISHED"}:
        raise RuntimeError("Could not enable the Sollumz add-on")
    from Sollumz.sollumz_properties import SollumType, MaterialType, LODLevel
    from Sollumz.ydr.shader_materials import create_shader, set_vehicle_material_paint_layer
    from Sollumz.ybn.collision_materials import create_collision_material_from_index, collisionmats
    from Sollumz.tools.drawablehelper import set_recommended_bone_properties
    from Sollumz.tools.blenderhelper import add_child_of_bone_constraint, create_empty_object
    from Sollumz.ydr.properties import BoneProperties
    SZ.update(locals())


def clear_scene():
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.armatures, bpy.data.materials):
        for item in list(coll):
            coll.remove(item)


# ---------------------------------------------------------------------- materials

class Materials:
    """Creates Sollumz shader materials on demand.

    spec: key -> dict(shader=..., tex={sampler: image}, paint=layer int, params={name: value or tuple})
    """

    def __init__(self, spec, images):
        self.spec = spec
        self.images = images
        self.cache = {}

    def __getitem__(self, key):
        if key not in self.cache:
            self.cache[key] = self._make(key, self.spec[key])
        return self.cache[key]

    def _make(self, key, s):
        mat = SZ["create_shader"](s["shader"] + ".sps")
        mat.name = key
        nodes = mat.node_tree.nodes
        for sampler, tex_name in s.get("tex", {}).items():
            node = nodes.get(sampler)
            if node is None:
                continue
            img = self.images.get(tex_name)
            if img is None:
                raise KeyError(f"texture {tex_name} missing for material {key}")
            node.image = img
            node.texture_properties.embedded = True
        for name, value in s.get("params", {}).items():
            node = nodes.get(name)
            if node is None:
                continue
            vals = value if isinstance(value, (tuple, list)) else (value,)
            for comp, v in zip("XYZW", vals):
                node.set(comp, float(v))
        if "paint" in s:
            SZ["set_vehicle_material_paint_layer"](mat, s["paint"])
        return mat


def load_dds_images(folder):
    images = {}
    for f in sorted(Path(folder).glob("*.dds")):
        img = bpy.data.images.load(str(f), check_existing=True)
        img.name = f.stem
        images[f.stem] = img
    return images


# ---------------------------------------------------------------------- fragment

class Fragment:
    """A fragment (.yft) with a vehicle skeleton.

    bones: list of dicts {name, pos, parent, limit_rot: ((minx,miny,minz),(maxx,maxy,maxz)) | None,
                          limit_trans: same | None, rot: Matrix | None}
    """

    def __init__(self, name, bones):
        ST = SZ["SollumType"]
        self.name = name
        arm = bpy.data.armatures.new(name)
        self.obj = bpy.data.objects.new(name, arm)
        self.obj.sollum_type = ST.FRAGMENT
        bpy.context.collection.objects.link(self.obj)
        bpy.context.view_layer.objects.active = self.obj
        bpy.ops.object.mode_set(mode="EDIT")
        for b in bones:
            eb = arm.edit_bones.new(b["name"])
            eb.head = (0, 0, 0)
            eb.tail = (0, 0.05, 0)
            m = Matrix.Translation(Vector(b["pos"]))
            if b.get("rot") is not None:
                m = m @ b["rot"].to_4x4()
            eb.matrix = m
            if b.get("parent"):
                eb.parent = arm.edit_bones[b["parent"]]
        bpy.ops.object.mode_set(mode="OBJECT")

        for b in bones:
            bone = arm.bones[b["name"]]
            SZ["set_recommended_bone_properties"](bone)
            if b["name"] not in _KNOWN_TAGS_CACHE.setdefault("names", _known_bone_names()):
                bone.bone_properties.tag = SZ["BoneProperties"].calc_tag_hash(b["name"])
            pb = self.obj.pose.bones[b["name"]]
            if b.get("limit_rot"):
                (mn, mx) = b["limit_rot"]
                c = pb.constraints.new("LIMIT_ROTATION")
                c.owner_space = "LOCAL"
                c.use_limit_x = c.use_limit_y = c.use_limit_z = True
                c.min_x, c.min_y, c.min_z = mn
                c.max_x, c.max_y, c.max_z = mx
            if b.get("limit_trans"):
                (mn, mx) = b["limit_trans"]
                c = pb.constraints.new("LIMIT_LOCATION")
                c.owner_space = "LOCAL"
                c.use_min_x = c.use_min_y = c.use_min_z = True
                c.use_max_x = c.use_max_y = c.use_max_z = True
                c.min_x, c.min_y, c.min_z = mn
                c.max_x, c.max_y, c.max_z = mx

        self.drawable = SZ["create_empty_object"](ST.DRAWABLE, f"{name}.mesh")
        self.drawable.parent = self.obj
        self.composite = None

    # -------------------------------------------------------------- drawable models

    def group_index(self):
        """Vertex group index per bone name (same order as the armature) for skinned meshes."""
        return {b.name: i for i, b in enumerate(self.obj.data.bones)}

    def add_skinned_model(self, name, lod_meshes):
        """lod_meshes: {LODLevel: bpy Mesh} built with group_index=self.group_index()."""
        ST, LOD = SZ["SollumType"], SZ["LODLevel"]
        first = next(iter(lod_meshes.values()))
        obj = bpy.data.objects.new(name, first)
        for b in self.obj.data.bones:
            if b.name not in obj.vertex_groups:      # group names live on the mesh (shared by LOD copies)
                obj.vertex_groups.new(name=b.name)
        obj.sollum_type = ST.DRAWABLE_MODEL
        bpy.context.collection.objects.link(obj)
        obj.parent = self.drawable
        for lod, mesh in lod_meshes.items():
            obj.sz_lods.get_lod(lod).mesh = mesh
        obj.sz_lods.active_lod_level = LOD.HIGH if LOD.HIGH in lod_meshes else next(iter(lod_meshes))
        mod = obj.modifiers.new("Armature", "ARMATURE")
        mod.object = self.obj
        return obj

    def add_bone_model(self, name, bone, lod_meshes, physics_child=False):
        """Rigid model following a single bone (used for wheels)."""
        ST, LOD = SZ["SollumType"], SZ["LODLevel"]
        first = next(iter(lod_meshes.values()))
        obj = bpy.data.objects.new(name, first)
        obj.sollum_type = ST.DRAWABLE_MODEL
        bpy.context.collection.objects.link(obj)
        obj.parent = self.drawable
        for lod, mesh in lod_meshes.items():
            obj.sz_lods.get_lod(lod).mesh = mesh
        obj.sz_lods.active_lod_level = LOD.HIGH if LOD.HIGH in lod_meshes else next(iter(lod_meshes))
        SZ["add_child_of_bone_constraint"](obj, self.obj, bone)
        obj.sollumz_is_physics_child_mesh = physics_child
        return obj

    # -------------------------------------------------------------- physics

    def enable_physics(self, bone, strength=-1.0, **props):
        b = self.obj.data.bones[bone]
        b.sollumz_use_physics = True
        gp = b.group_properties
        gp.strength = strength
        for k, v in props.items():
            if k == "flags":
                for i, f in v.items():
                    gp.flags[i] = f
            else:
                setattr(gp, k, v)

    def add_bound(self, bone, mesh, material, mass, window=False):
        """Bound Geometry (convex-ish triangle mesh) attached to `bone`. `mesh` is in bone-local space."""
        ST = SZ["SollumType"]
        if self.composite is None:
            self.composite = SZ["create_empty_object"](ST.BOUND_COMPOSITE, f"{self.name}.col")
            self.composite.parent = self.obj
        mesh.materials.clear()
        mesh.materials.append(_collision_material(material))
        obj = bpy.data.objects.new(f"{bone}.col", mesh)
        obj.sollum_type = ST.BOUND_GEOMETRY
        bpy.context.collection.objects.link(obj)
        obj.parent = self.composite
        SZ["add_child_of_bone_constraint"](obj, self.obj, bone)
        obj.child_properties.mass = mass
        obj.child_properties.shattermap_mode = "MANUAL_NO_SHATTERMAP" if window else "NO"
        f1, f2 = obj.composite_flags1, obj.composite_flags2
        f1.vehicle_not_bvh = True
        for flag in ("map_weapon", "map_dynamic", "map_animal", "map_cover", "map_vehicle", "vehicle_not_bvh",
                     "vehicle_bvh", "ped", "ragdoll", "animal", "animal_ragdoll", "object", "plant", "projectile",
                     "explosion", "forklift_forks", "test_weapon", "test_camera", "test_ai", "test_script", "glass"):
            setattr(f2, flag, True)
        return obj

    def bone_head(self, bone):
        return self.obj.data.bones[bone].head_local.copy()


_KNOWN_TAGS_CACHE = {}


def _known_bone_names():
    from Sollumz.tools.drawablehelper import BonePropertiesManager
    if not BonePropertiesManager.bones:
        BonePropertiesManager.load_bones()
    return set(BonePropertiesManager.bones)


_COLLISION_MATS = {}


def _collision_material(name):
    if name not in _COLLISION_MATS or _COLLISION_MATS[name].name not in bpy.data.materials:
        idx = next(i for i, m in enumerate(SZ["collisionmats"]) if m.name == name)
        _COLLISION_MATS[name] = SZ["create_collision_material_from_index"](idx)
    return _COLLISION_MATS[name]


# ---------------------------------------------------------------------- export

def export_selected(objs, out_dir):
    """Export the given root objects as CodeWalker XML (GEN8 / legacy PC) into out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    res = bpy.ops.sollumz.export_assets(
        directory=str(out_dir),
        direct_export=True,
        use_custom_settings=True,
        target_formats={"CWXML"},
        target_versions={"GEN8"},
        limit_to_selected=True,
        exclude_skeleton=False,
        apply_transforms=False,
        mesh_domain="FACE_CORNER",
        export_ytyps=False,
        export_ymaps=False,
        export_ytds=False,
    )
    if res != {"FINISHED"}:
        raise RuntimeError(f"export failed: {res}")


def capture_logs():
    """Collect Sollumz warnings/errors so the build can fail loudly."""
    from Sollumz import logger
    msgs = []
    orig = {}
    for level in ("warning", "error"):
        orig[level] = getattr(logger, level)

        def make(level):
            def f(msg, *a, **k):
                msgs.append((level, str(msg)))
                return orig[level](msg, *a, **k)
            return f
        setattr(logger, level, make(level))
    return msgs


def force_exit(code=0):
    """bpy-as-a-module can hang on interpreter shutdown; leave immediately."""
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
