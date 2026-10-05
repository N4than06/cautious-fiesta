# GMC Sierra 1500 AT4X — GTA V Add-On + In-Game Garage

A fully customizable add-on **GMC Sierra 1500 AT4X** for GTA V Story Mode. You get:

- **An add-on DLC pack** (`dlc/at4x`). It doesn't replace any vanilla car and includes handling tuned to the real truck.
- **A 23-slot mod kit with 92 parts.** That covers bumpers, power rails, exhausts, Whipple superchargers, hoods, grilles, racks, lights, interior and more. All of it shows up in Los Santos Customs.
- **Optional add-on rims and tires**, with every rim offered in several tire sizes (33/35/37 in).
- **The AT4X Garage script** (press **F7**). It adds the things LS Customs can't do:
  - **Power rails that deploy** when a door opens or you walk up to the truck, and tuck away when you drive off.
  - **A one-click Whipple 3.0L package**: blower, cut-out hood, intake, boost presets (550–800 hp) and a blown-V8 sound.
  - **Engine-sound swapping**, including any add-on sound pack you install.
  - **Exhausts**, pops and crackles, and horns.
  - **Rims, raised-letter tires**, drift and run-flat tires, and tire smoke.
  - **Factory-style RGB paints**, finishes, pearl, rim color and tint.
  - **Lights**: LED headlight colors and rock lights.
  - **Extras and liveries.**
  - **Lift and lowering kits** plus engine, brake and transmission stages.
  - **5 saved build slots.** Your build is re-applied every time you get in.

Every list in the mod is data-driven. You can add parts, sounds, colors and boost levels by editing
`src/parts.json` or `scripts/AT4XGarage.ini`. Nothing is hard-coded to a fixed set.

## ⚠️ What's not in this repo: the 3D model

GTA vehicles need a 3D model (`at4x.yft`, `at4x_hi.yft`) and textures (`at4x.ytd`), plus one model per
mod part. Those are binary art assets made in Blender (with the Sollumz add-on) or ZModeler3, so they can't be
generated as code. This repo is everything around the model: data, mod kit, text, handling and the script.
It's laid out so a model drops straight in.

You have three options:
1. **Build it yourself** using [`docs/MODELING_SPEC.md`](docs/MODELING_SPEC.md), which has 1:1 dimensions, the bone list,
   which stock part goes on which bone, and the power-rail animation frames.
2. **Use an existing AT4X / Sierra model you have permission to use.** Rename it to `at4x` and rig the
   `misc_*` bones from the spec. If you're missing parts, trim `src/parts.json` to the parts you have.
3. **Commission a modeler** and hand them `docs/MODELING_SPEC.md` plus
   `dlc/at4x/x64/vehicles.rpf/MODEL_CHECKLIST.txt`.

The garage script works on **any** vehicle right away (`OnlyInAT4X=false`). You can try sounds, rims, paint,
boost and builds before the AT4X model exists.

## Repo layout

| Path | What it is |
|---|---|
| `dlc/at4x/` | Contents of `dlc.rpf`: `content.xml`, `setup2.xml`, `common/data/*.meta`, `x64/...` |
| `dlc/at4x/common/data/handling.meta` | Handling based on the real truck (L87 6.2L V8, 4WD, DSSV, 33" MTs, ~2,640 kg) |
| `dlc/at4x/common/data/carcols.meta` | Mod kit `4210_at4x_modkit` (**generated**) |
| `dlc/at4x/common/data/carcols_wheels.meta` | Optional add-on rims and tires (**generated**, off by default) |
| `dlc/at4x/x64/data/lang/americandlc.rpf/global.gxt2` | In-game part names (**generated**) |
| `dlc/at4x/x64/vehicles.rpf/MODEL_CHECKLIST.txt` | Every model file the pack expects (**generated**) |
| `src/parts.json` | **Master parts catalog.** Edit this to add, remove or rename parts |
| `tools/build.py` | Regenerates every generated file from `parts.json` |
| `scripts/AT4XGarage.cs` / `.ini` | The in-game garage script and its settings |
| `docs/` | Install guide, 1:1 modeling spec, customization guide |

## Quick start

1. Install it: see [`docs/INSTALL.md`](docs/INSTALL.md).
2. In game, press **F7**, then **Spawn AT4X**.
3. To customize further, see [`docs/CUSTOMIZING.md`](docs/CUSTOMIZING.md).

```sh
# after editing src/parts.json
python3 tools/build.py
# check your exported models against what the pack expects
python3 tools/build.py --check path/to/exported/models
```

*GMC, Sierra, AT4X and Whipple are trademarks of their owners. This is a non-commercial fan mod for
single-player use and isn't affiliated with or endorsed by them.*
