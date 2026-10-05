"""Material catalogue: material key -> GTA vehicle shader, textures and paint layer.

Paint layers (Sollumz VehiclePaintLayer): 0 custom RGB, 1 primary, 2 secondary, 3 pearlescent, 4 wheel,
5 default (not paintable), 6 interior trim, 7 dashboard.
"""
PRIMARY, SECONDARY, WHEEL, DEFAULT, TRIM, DASH = 1, 2, 4, 5, 6, 7

_SAMPLERS = {
    "vehicle_paint1": ("DiffuseSampler", "DamageSampler", "DirtSampler", "SpecSampler"),
    "vehicle_mesh": ("DiffuseSampler", "DamageSampler", "DirtSampler", "BumpSampler", "SpecSampler"),
    "vehicle_tire": ("DiffuseSampler", "DirtSampler", "BumpSampler", "SpecSampler"),
    "vehicle_vehglass": ("DiffuseSampler", "DamageSampler", "DirtSampler", "SpecSampler"),
    "vehicle_vehglass_inner": ("DiffuseSampler", "DamageSampler", "DirtSampler", "SpecSampler"),
    "vehicle_lightsemissive": ("DiffuseSampler", "DamageSampler", "DirtSampler", "SpecSampler"),
    "vehicle_interior2": ("DiffuseSampler", "DamageSampler", "SpecSampler"),
    "vehicle_dash_emissive": ("DiffuseSampler", "DamageSampler", "SpecSampler"),
    "vehicle_badges": ("DiffuseSampler", "DamageSampler", "BumpSampler", "SpecSampler"),
}

_DEFAULT_TEX = {
    "DamageSampler": "at4x_damage",
    "DirtSampler": "at4x_dirt",
    "BumpSampler": "at4x_nrm",
    "SpecSampler": "at4x_spec",
}


def _m(shader, diffuse, paint=DEFAULT, spec="at4x_spec", **params):
    tex = {}
    for s in _SAMPLERS[shader]:
        if s == "DiffuseSampler":
            tex[s] = diffuse
        elif s == "SpecSampler":
            tex[s] = spec
        else:
            tex[s] = _DEFAULT_TEX[s]
    out = dict(shader=shader, tex=tex, paint=paint)
    if params:
        out["params"] = params
    return out


SPEC = {
    # body
    "paint": _m("vehicle_paint1", "at4x_white", PRIMARY),
    "paint2": _m("vehicle_paint1", "at4x_white", SECONDARY),
    "plastic": _m("vehicle_mesh", "at4x_plastic", spec="at4x_spec_low"),
    "black": _m("vehicle_mesh", "at4x_black", spec="at4x_spec_low"),
    "gloss_black": _m("vehicle_mesh", "at4x_black"),
    "steel": _m("vehicle_mesh", "at4x_steel"),
    "chrome": _m("vehicle_mesh", "at4x_chrome"),
    "alu": _m("vehicle_mesh", "at4x_alu"),
    "red": _m("vehicle_mesh", "at4x_red"),
    "gold": _m("vehicle_mesh", "at4x_gold"),
    "titanium": _m("vehicle_mesh", "at4x_titanium"),
    "plate": _m("vehicle_mesh", "at4x_plate", spec="at4x_spec_low"),
    "grille": _m("vehicle_mesh", "at4x_grille", spec="at4x_spec_low"),
    "mesh": _m("vehicle_mesh", "at4x_mesh", spec="at4x_spec_low"),
    "bedliner": _m("vehicle_mesh", "at4x_bedliner", spec="at4x_spec_low"),
    "engine_cover": _m("vehicle_mesh", "at4x_engine_cover", spec="at4x_spec_low"),
    "whipple": _m("vehicle_mesh", "at4x_whipple"),
    "reflector": _m("vehicle_mesh", "at4x_reflector"),
    # wheels
    "tire": _m("vehicle_tire", "at4x_tire", spec="at4x_spec_low"),
    "sidewall": _m("vehicle_tire", "at4x_sidewall", spec="at4x_spec_low"),
    "sidewall_rwl": _m("vehicle_tire", "at4x_sidewall_rwl", spec="at4x_spec_low"),
    "rim": _m("vehicle_mesh", "at4x_rim", WHEEL),
    "rim_black": _m("vehicle_mesh", "at4x_black"),
    # glass and lights
    "glass": _m("vehicle_vehglass", "at4x_glass"),
    "glass_in": _m("vehicle_vehglass_inner", "at4x_glass"),
    "light_clear": _m("vehicle_lightsemissive", "at4x_lens_clear"),
    "light_led": _m("vehicle_lightsemissive", "at4x_led"),
    "light_red": _m("vehicle_lightsemissive", "at4x_lens_red"),
    "light_amber": _m("vehicle_lightsemissive", "at4x_lens_amber"),
    # interior
    "leather": _m("vehicle_interior2", "at4x_leather", spec="at4x_spec_low"),
    "leather_red": _m("vehicle_interior2", "at4x_leather_red", spec="at4x_spec_low"),
    "carpet": _m("vehicle_interior2", "at4x_carpet", spec="at4x_spec_low"),
    "trim": _m("vehicle_interior2", "at4x_plastic", TRIM, spec="at4x_spec_low"),
    "dash": _m("vehicle_dash_emissive", "at4x_dash"),
    "screen": _m("vehicle_dash_emissive", "at4x_screen"),
    # badges
    "badge_gmc": _m("vehicle_badges", "at4x_badge_gmc"),
    "badge_at4x": _m("vehicle_badges", "at4x_badge_at4x"),
    "badge_sierra": _m("vehicle_badges", "at4x_badge_sierra"),
    "badge_v8": _m("vehicle_badges", "at4x_badge_v8"),
}
