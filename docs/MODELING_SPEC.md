# AT4X 1:1 Modeling Spec

This is the handoff sheet for whoever builds the 3D model in Blender with the
[Sollumz](https://github.com/Sollumz/Sollumz) add-on, or in ZModeler3.

## Scale and orientation

- **1 Blender unit = 1 metre.** GTA works in metres, so 1:1 means modeling at real size.
- Forward is **+Y**, up is **+Z**, and the driver sits on the **−X** (left) side.
- Put the origin at the vehicle's centre: halfway along the wheelbase, on the centreline, with the
  ground at roughly `z = −(wheel radius + ride height)`. Copy the origin placement from a vanilla truck such as `sandking`.

## Reference dimensions

These are for the 2024+ GMC Sierra 1500 AT4X Crew Cab, short box. The figures are approximate, so
**check them against GMC's official spec sheet for your exact model year** and against blueprints or photos.

| | Imperial | Metric |
|---|---|---|
| Overall length | ~231.9 in | ~5,890 mm |
| Wheelbase | 147.4 in | 3,744 mm |
| Body width (no mirrors) | ~81.2 in | ~2,063 mm |
| Overall height | ~79.5 in | ~2,020 mm |
| Track width (front and rear) | ~68.9 in | ~1,750 mm |
| Ground clearance | ~11.2 in | ~284 mm |
| Bed length | 5 ft 8 in | ~1,776 mm |
| Stock tire | LT275/70R18, ~33.2 in | ~843 mm diameter, **0.42 m radius** |
| Stock wheel | 18 in | 0.2286 m rim radius |
| Curb weight | ~5,800 lb | ~2,640 kg (already set in `handling.meta`) |

These drivetrain facts are already reflected in `handling.meta`: 6.2 L L87 V8 (420 hp / 460 lb-ft),
10-speed automatic, 2-speed transfer case, front and rear e-lockers, Multimatic DSSV dampers.

After modeling, update `wheelScale` / `wheelScaleRear` in `vehicles.meta` from your stock wheel.

## Files to produce

The full list is generated in `dlc/at4x/x64/vehicles.rpf/MODEL_CHECKLIST.txt`. In short:

- `at4x.yft`: the base vehicle (LODs L0–L3)
- `at4x_hi.yft`: the high-detail version
- `at4x.ytd`: textures, including liveries `sign_1`, `sign_2` and so on if you want decal liveries
- one `.yft` per mod part in `src/parts.json`, e.g. `at4x_fb_aev.yft`
- optional rim and tire `.ydr`s for `carcols_wheels.meta`

Don't want to model a part? Delete it from `src/parts.json` and run `python3 tools/build.py`.
The kit, the text and the checklist all update to match.

## Skeleton (base model)

Use the standard GTA car bones: `chassis`, `bodyshell`, `door_dside_f`, `door_pside_f`, `door_dside_r`, `door_pside_r`,
`bonnet`, `boot` (tailgate), `bumper_f`, `bumper_r`, `wheel_lf` / `wheel_rf` / `wheel_lr` / `wheel_rr`,
the `suspension_*` and `hub_*` bones, `steeringwheel`, `seat_dside_f` / `seat_pside_f` / `seat_dside_r` / `seat_pside_r`,
`windscreen`, `windscreen_r`, `window_lf` / `window_rf` / `window_lr` / `window_rr`, the `headlight_*`, `taillight_*`,
`indicator_*`, `brakelight_*` and `reversinglight_*` bones, `platelight`, `engine`, `petrolcap`,
`exhaust` and `exhaust_2` (dual exit), and `extra_1`… as needed.

### Stock parts that mods replace

When a mod is fitted, the game hides geometry on these bones (`turnOffBones` in `carcols.meta`). So
**put the stock version of each part on its bone below**, and nothing else:

| Bone | Stock AT4X part on it | Hidden by slot |
|---|---|---|
| `bumper_f` | Factory front bumper | Front Bumper |
| `bumper_r` | Factory rear bumper | Rear Bumper |
| `bonnet` | Factory hood | Hood |
| `boot` | Factory tailgate | Tailgate |
| `steeringwheel` | Factory steering wheel | Steering Wheel |
| `misc_a` | Factory rock rails | Running Boards / Power Rails |
| `misc_b` | Factory exhaust tips | Exhaust |
| `misc_c` | Factory grille | Grille |
| `misc_d` | Factory fender flares | Fender Flares |
| `misc_e` | Factory engine cover | Supercharger |
| `misc_f` | Factory airbox / intake | Air Intake |
| `misc_g` | Factory skid plates | Skid Plates |
| `misc_h` | Factory seats | Seats |
| `misc_i` | Factory interior trim | Interior Trim |

The other slots (roof, racks, ditch lights, bed covers, snorkel, mud flaps, spare, plate mount, engine dress-up)
are **add-ons**. They hide nothing, so the stock model just doesn't have them.

### Mod parts

- Each mod part is its own `.yft`, exported with the **same skeleton** as the base model.
- Model each part **in place**, positioned exactly where it sits on the base truck. Skin or parent it to the
  slot's bone (see `bone` per slot in `src/parts.json`). For example, front bumpers go on `bumper_f` and the hood on `bonnet`.
- **Whipple cut-out hood** (`at4x_hd_whipple`): leave an opening for the blower lid (`at4x_sc_whip_*`) to
  poke through.
- **Exhaust mods**: real exhaust smoke and pops come from the base model's `exhaust` / `exhaust_2` bones.
  For side exits or bed stacks, you can also add `exhaust_3` / `exhaust_4` at the new tip positions.

## Power rails: animation frames

GTA mod parts can't animate on their own. The garage script fakes it by stepping through 2–3
models of the same rail. Build each style as:

| File | Pose |
|---|---|
| `at4x_pr_pwr_ret.yft` | Tucked up under the rocker |
| `at4x_pr_pwr_mid.yft` | About 50% of the swing: arms rotated down and out halfway |
| `at4x_pr_pwr_dep.yft` | Fully out and down, step about 3 in below the rocker |

The chrome style is the same with the `pwrc_` prefix. Want a smoother animation? Add more frames to the
sequence in `src/parts.json` (`powerRails`). The build script renumbers them and updates
`AT4XGarage.ini` for you, and `FrameMs` sets the speed.

## Rims and tires

In GTA, the rim and the tire are **one model**, so each tire size is its own wheel model.

- `at4x_whl_*.ydr`: the normal tire.
- `at4x_whl_*_b.ydr`: the same wheel with raised white lettering. This is the "custom tires" variant.
- Set `rimRadius` in `parts.json` to the real rim radius in metres.

## Liveries

Add `sign_1`, `sign_2`… textures to `at4x.ytd` (with `FLAG_HAS_LIVERY`, already set) to get side graphics,
an "AT4X" bedside stripe and so on. The garage lists them under **Extras & Livery**.
