# Installing the AT4X

The steps below are for GTA V Story Mode with OpenIV's `mods` folder.

## 1. Requirements

| Tool | Why |
|---|---|
| [OpenIV](https://openiv.com/) (or CodeWalker RPF Explorer) | Builds `dlc.rpf` and edits `dlclist.xml` |
| OpenIV **ASI Manager**: ASI Loader + OpenIV.ASI | Lets the game load the `mods` folder |
| [ScriptHookV](http://www.dev-c.com/gtav/scripthookv/) | Needed by every script mod. It must match your game build |
| [ScriptHookVDotNet 3](https://github.com/scripthookvdotnet/scripthookvdotnet/releases) | Runs the garage script |
| [LemonUI (SHVDN3)](https://github.com/LemonUIbyLemon/LemonUI/releases) | Draws the menu. Copy `LemonUI.SHVDN3.dll` into `scripts/` |

Check that ScriptHookV supports your exact game build (Legacy or Enhanced). Script mods stop working
after a GTA update until ScriptHookV is updated too.

## 2. Build `dlc.rpf`

In OpenIV, with **Edit mode** on:

1. Go to `mods/update/x64/dlcpacks/` and create a folder named **`at4x`**.
2. Inside it, right-click → **New → RPF archive** and name it **`dlc.rpf`**.
3. Recreate this repo's `dlc/at4x/` folder **inside `dlc.rpf`**. Every folder whose name ends in `.rpf` must be
   created as an RPF archive, not a plain folder:

```
dlc.rpf
├── content.xml
├── setup2.xml
├── common/
│   └── data/
│       ├── handling.meta
│       ├── vehicles.meta
│       ├── carcols.meta
│       ├── carvariations.meta
│       └── carcols_wheels.meta        (optional, see step 5)
└── x64/
    ├── vehicles.rpf                    ← RPF archive
    │   ├── at4x.yft  at4x_hi.yft  at4x.ytd
    │   └── at4x_fb_aev.yft ... (every mod part in MODEL_CHECKLIST.txt)
    └── data/
        └── lang/
            └── americandlc.rpf         ← RPF archive
                └── global.gxt2
```

You can also use CodeWalker: **Tools → RPF Explorer → New RPF**, then drag the folders in.

## 3. Register the DLC

1. Copy `update/update.rpf` into `mods/` if it isn't there yet. OpenIV offers to do this for you.
2. Open `mods/update/update.rpf/common/data/dlclist.xml`.
3. Add this line before `</Paths>`:

```xml
    <Item>dlcpacks:/at4x/</Item>
```

## 4. Install the garage script

Copy these into `Grand Theft Auto V/scripts/`:

- `scripts/AT4XGarage.cs`. ScriptHookVDotNet compiles it on load. If you prefer a DLL, build
  `scripts/build/AT4XGarage.csproj` with `dotnet build -c Release`
- `scripts/AT4XGarage.ini`
- `LemonUI.SHVDN3.dll` (from the LemonUI release)

## 5. Optional: add-on rims

The rim and tire packages in `carcols_wheels.meta` are **off by default**. Turn them on only after the wheel
`.ydr` models from `MODEL_CHECKLIST.txt` are in `vehicles.rpf`; otherwise those rims render invisible.
To turn them on, uncomment the two marked blocks in `content.xml`.

Vanilla off-road, SUV, high-end and the other wheel categories work without this step.

## 6. Play

- **F7** opens the AT4X Garage. Pick **Spawn AT4X**, or tune whatever you're driving.
- The trainer spawn name is **`at4x`**.
- At **Los Santos Customs**, every AT4X part shows under its own slot name: Power Rails, Supercharger,
  Ditch Lights and so on.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Model 'at4x' isn't installed" | Check the `dlclist.xml` line and the folder name `dlcpacks/at4x/dlc.rpf`. Also check that `vehicles.rpf` is an **RPF archive** containing `at4x.yft` |
| Game crashes on load | Usually a broken `.meta`. Re-copy the files from this repo, and make sure no other add-on uses mod kit id **4210** (change `kit.id` in `src/parts.json` and rebuild if one does) |
| Part names show as `NULL` or labels | `global.gxt2` isn't in `x64/data/lang/americandlc.rpf`. It must be an RPF archive, not a folder |
| A part is invisible | That part's `.yft` is missing. Run `python3 tools/build.py --check <folder>` |
| F7 does nothing | Check `ScriptHookVDotNet.log` in the game folder. Usually LemonUI is missing or ScriptHookV is outdated |
| Power rails don't move | Fit Power Rails (Black or Chrome) in the garage. Rock rails and nerf bars don't animate |
