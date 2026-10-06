# Customizing the AT4X

You can change everything from two files:

- **`src/parts.json`** controls what parts exist: names, slots, model files, rims, stat upgrade strength, horns,
  power-rail frames and which parts the Whipple package uses. Run `python3 tools/build.py` after editing it.
- **`scripts/AT4XGarage.ini`** controls the garage's behaviour: menu key, sounds, boost levels, paints and rail timing.
  Edit it while the game is closed.

## In-game menu (F7)

| Menu | What you can change |
|---|---|
| Body & Parts | Front/rear bumpers, grille, hood, fender flares, ditch lights, roof, bed rack, bed cover, tailgate, skid plates, snorkel/antennas, mud flaps, spare tire, plate mount, intake, engine dress-up, seats, steering wheel, interior trim |
| Rims & Tires | Wheel category (all 13 GTA categories), rim, raised-letter tires, drift tires, run-flat tires, tire smoke color, rim color |
| Power Rails | Style (rock rails / power rails / nerf bars / sliders / delete), auto-deploy, deploy now, retract now |
| Exhaust & Sound | Exhaust style, engine sound, pops & crackles, horn |
| Whipple Supercharger | One-click install or remove, boost level, blower finish, intake |
| Performance | Engine stages, brakes, transmission, suspension lift or drop, armor, turbo/forced-induction sounds |
| Paint | Factory-style RGB colors, finish (metallic, matte, chrome…), pearlescent, window tint |
| Lights | Headlight LED color, rock lights / underglow |
| Extras & Livery | Every model extra, liveries, livery parts |
| Saved Builds | 5 save slots plus a factory reset. The last saved or loaded build becomes **Active** and is re-applied when you get in |

## Adding a part

1. Model it (see `MODELING_SPEC.md`) and name it, e.g. `at4x_fb_ranch.yft`.
2. Add it to its slot in `src/parts.json`:
   ```json
   { "model": "at4x_fb_ranch", "name": "Ranch Hand Front Bumper" }
   ```
3. Run `python3 tools/build.py`, then copy the new `carcols.meta`, `global.gxt2` and the `.yft` into `dlc.rpf`.

The part appears at Los Santos Customs and in the garage menu with its name. If you reorder or insert
parts in the Running Boards, Supercharger, Hood or Intake slots, the build script updates the
power-rail and Whipple indices in `AT4XGarage.ini` for you.

## Adding a whole new slot

You can use any free `VMT_*` slot, for example `VMT_DOOR_L` or `VMT_INTERIOR2`. Add a new entry to `slots` with a unique
`code`, then add the matching slot id and name to `Slot.Body` at the top of `scripts/AT4XGarage.cs` so the
garage menu shows it. LS Customs picks it up automatically.

## Engine sounds

The garage plays the vehicle's engine sound through `FORCE_USE_AUDIO_GAME_OBJECT`, so a sound is just a name:

```ini
[Sounds]
Presets=SANDKING:Big-Block V8 Truck,GAUNTLET4:Supercharged V8,MYL87WHIPPLE:L87 + Whipple (add-on)
```

- Vanilla names are a vehicle's `audioNameHash`, usually its spawn name.
- **For a true Whipple whine** or a real L87 recording, install an add-on engine sound pack.
  Those ship as their own DLC with `.awc` + `.rel` files. Then put the pack's audio name in `Presets`
  and in `[Whipple] Sound=`.
- The `Stock=` key sets the sound that "Stock" restores. Keep it in sync with `audioNameHash` in `vehicles.meta`.

## Boost, lift and power

- `[Whipple] Boost=` takes `name:torque multiplier` entries. Stock is 1.0, and 1.6 is about a 700 hp Whipple build.
  `TopSpeedPercent` adds top speed while the blower is fitted.
- Lift and lowering strength comes from `statMods.VMT_SUSPENSION` in `parts.json`. **Negative values lift**
  the truck and positive values lower it. Rename them under `[Names] Suspension=` in the INI.
- The stock truck's feel lives in `dlc/at4x/common/data/handling.meta`.

## Paint

```ini
[Paint]
Colors=Summit White:236,237,235|My Custom Blue:20,60,140
```

Any `Label:R,G,B` works, separated by `|`. The finish (metallic, matte, chrome…) is picked separately in-game.
