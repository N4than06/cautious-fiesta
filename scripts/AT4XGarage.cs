// AT4X Garage - in-game customization for the GMC Sierra AT4X add-on.
// Requires ScriptHookV, ScriptHookVDotNet 3 and LemonUI (SHVDN3 build).
// Drop this file plus AT4XGarage.ini into "Grand Theft Auto V/scripts".
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using GTA;
using GTA.Math;
using GTA.Native;
using LemonUI;
using LemonUI.Menus;

namespace AT4X
{
    /// <summary>Native hashes, verified against the alloc8or native DB.</summary>
    internal static class N
    {
        public const ulong SET_VEHICLE_MOD_KIT = 0x1F2AA07F00B3217A;
        public const ulong SET_VEHICLE_MOD = 0x6AF0636DDEDCB6DD;
        public const ulong GET_VEHICLE_MOD = 0x772960298DA26FDB;
        public const ulong GET_VEHICLE_MOD_VARIATION = 0xB3924ECD70E095DC;
        public const ulong GET_NUM_VEHICLE_MODS = 0xE38E9162A2500646;
        public const ulong GET_MOD_TEXT_LABEL = 0x8935624F8C5592CC;
        public const ulong SET_VEHICLE_WHEEL_TYPE = 0x487EB21CC7295BA1;
        public const ulong GET_VEHICLE_WHEEL_TYPE = 0xB3ED1BFB4BE636DC;
        public const ulong TOGGLE_VEHICLE_MOD = 0x2A1F4F37F95BAD08;
        public const ulong IS_TOGGLE_MOD_ON = 0x84B233A8C8FC8AE7;
        public const ulong SET_VEHICLE_TYRE_SMOKE_COLOR = 0xB5BA80F839791C0F;
        public const ulong SET_VEHICLE_TYRES_CAN_BURST = 0xEB9DC3C7D8596C46;
        public const ulong GET_VEHICLE_TYRES_CAN_BURST = 0x678B9BB8C3F58FEB;
        public const ulong SET_DRIFT_TYRES = 0x5AC79C98C5C17F05;
        public const ulong GET_DRIFT_TYRES_SET = 0x2F5A72430E78C8D3;
        public const ulong SET_VEHICLE_MOD_COLOR_1 = 0x43FEB945EE7F85B8;
        public const ulong SET_VEHICLE_MOD_COLOR_2 = 0x816562BADFDEC83E;
        public const ulong SET_VEHICLE_CUSTOM_PRIMARY_COLOUR = 0x7141766F91D15BEA;
        public const ulong SET_VEHICLE_CUSTOM_SECONDARY_COLOUR = 0x36CED73BFED89754;
        public const ulong SET_VEHICLE_EXTRA_COLOURS = 0x2036F561ADD12E33;
        public const ulong SET_VEHICLE_WINDOW_TINT = 0x57C51E6BAD752696;
        public const ulong GET_VEHICLE_WINDOW_TINT = 0x0EE21293DAD47C95;
        public const ulong SET_VEHICLE_XENON_LIGHT_COLOR_INDEX = 0xE41033B25D003A07;
        public const ulong GET_VEHICLE_XENON_LIGHT_COLOR_INDEX = 0x3DFF319A831E0CDB;
        public const ulong SET_VEHICLE_NEON_ENABLED = 0x2AA720E4287BF269;
        public const ulong SET_VEHICLE_NEON_COLOUR = 0x8E0A582209A62695;
        public const ulong SET_VEHICLE_LIVERY = 0x60BF608F1B8CD1B6;
        public const ulong GET_VEHICLE_LIVERY = 0x2BB9230590DA5E8A;
        public const ulong GET_VEHICLE_LIVERY_COUNT = 0x87B63E25A529D526;
        public const ulong SET_VEHICLE_EXTRA = 0x7EE3A3C5E4A40CC9;
        public const ulong DOES_EXTRA_EXIST = 0x1262D55792428154;
        public const ulong IS_VEHICLE_EXTRA_TURNED_ON = 0xD2E6822DBFD6C8BD;
        public const ulong GET_VEHICLE_DOOR_ANGLE_RATIO = 0xFE3F9C29F7B32BD5;
        public const ulong GET_VEHICLE_PED_IS_TRYING_TO_ENTER = 0x814FA8BE5449445D;
        public const ulong FORCE_USE_AUDIO_GAME_OBJECT = 0x4F0C413926060B38;
        public const ulong ENABLE_VEHICLE_EXHAUST_POPS = 0x2BE4BC731D039D5A;
        public const ulong SET_VEHICLE_CHEAT_POWER_INCREASE = 0xB59E4BD37AE292DB;
        public const ulong MODIFY_VEHICLE_TOP_SPEED = 0x93A3996368C94158;
        public const ulong SET_VEHICLE_FIXED = 0x115722B1B9C14C1C;
        public const ulong SET_VEHICLE_DEFORMATION_FIXED = 0x953DA1E1B12C0491;
        public const ulong SET_VEHICLE_DIRT_LEVEL = 0x79D3B596FE44EE8B;
        public const ulong DOES_TEXT_LABEL_EXIST = 0xAC09CA973C564252;
    }

    /// <summary>GTA mod slot ids (SET_VEHICLE_MOD modType).</summary>
    internal static class Slot
    {
        public const int Spoiler = 0, FrontBumper = 1, RearBumper = 2, Skirt = 3, Exhaust = 4, Chassis = 5,
            Grille = 6, Hood = 7, FenderL = 8, FenderR = 9, Roof = 10, Engine = 11, Brakes = 12,
            Transmission = 13, Horn = 14, Suspension = 15, Armor = 16, Turbo = 18, TireSmoke = 20, Xenon = 22,
            FrontWheels = 23, PlateHolder = 25, Interior1 = 27, Seats = 32, Steering = 33, Trunk = 37,
            EngineBay1 = 39, EngineBay2 = 40, EngineBay3 = 41, Chassis2 = 42, Chassis3 = 43, Chassis4 = 44,
            Chassis5 = 45, Livery = 48;

        /// <summary>Visual slots shown in "Body &amp; Parts", with the names used by the AT4X kit.</summary>
        public static readonly KeyValuePair<int, string>[] Body =
        {
            new KeyValuePair<int, string>(FrontBumper, "Front Bumper"),
            new KeyValuePair<int, string>(RearBumper, "Rear Bumper"),
            new KeyValuePair<int, string>(Grille, "Grille"),
            new KeyValuePair<int, string>(Hood, "Hood"),
            new KeyValuePair<int, string>(FenderL, "Fender Flares"),
            new KeyValuePair<int, string>(FenderR, "Ditch Lights"),
            new KeyValuePair<int, string>(Roof, "Roof"),
            new KeyValuePair<int, string>(Chassis, "Bed Rack / Sport Bar"),
            new KeyValuePair<int, string>(Spoiler, "Bed Cover / Cap"),
            new KeyValuePair<int, string>(Trunk, "Tailgate"),
            new KeyValuePair<int, string>(Chassis2, "Skid Plates"),
            new KeyValuePair<int, string>(Chassis3, "Snorkel / Antennas"),
            new KeyValuePair<int, string>(Chassis4, "Mud Flaps"),
            new KeyValuePair<int, string>(Chassis5, "Spare Tire"),
            new KeyValuePair<int, string>(PlateHolder, "Plate Mount"),
            new KeyValuePair<int, string>(EngineBay2, "Air Intake"),
            new KeyValuePair<int, string>(EngineBay3, "Engine Dress-Up"),
            new KeyValuePair<int, string>(Seats, "Seats"),
            new KeyValuePair<int, string>(Steering, "Steering Wheel"),
            new KeyValuePair<int, string>(Interior1, "Interior Trim"),
            new KeyValuePair<int, string>(Livery, "Livery Parts"),
        };

        /// <summary>Every slot a build remembers.</summary>
        public static readonly int[] Saved =
        {
            Spoiler, FrontBumper, RearBumper, Skirt, Exhaust, Chassis, Grille, Hood, FenderL, FenderR, Roof,
            Engine, Brakes, Transmission, Horn, Suspension, Armor, PlateHolder, Interior1, Seats, Steering,
            Trunk, EngineBay1, EngineBay2, EngineBay3, Chassis2, Chassis3, Chassis4, Chassis5, Livery,
        };
    }

    /// <summary>Minimal INI reader/writer (keeps us independent of ScriptSettings comment handling).</summary>
    internal sealed class Ini
    {
        private readonly Dictionary<string, Dictionary<string, string>> data =
            new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase);

        public static Ini Load(string path)
        {
            var ini = new Ini();
            if (!File.Exists(path)) return ini;
            string section = "";
            foreach (string raw in File.ReadAllLines(path))
            {
                string line = raw.Trim();
                if (line.Length == 0 || line[0] == ';' || line[0] == '#') continue;
                if (line[0] == '[' && line[line.Length - 1] == ']')
                {
                    section = line.Substring(1, line.Length - 2).Trim();
                    continue;
                }
                int eq = line.IndexOf('=');
                if (eq > 0) ini.Set(section, line.Substring(0, eq).Trim(), line.Substring(eq + 1).Trim());
            }
            return ini;
        }

        public IEnumerable<string> Sections { get { return data.Keys; } }

        public bool HasSection(string section) { return data.ContainsKey(section); }

        public void RemoveSection(string section) { data.Remove(section); }

        public void Set(string section, string key, string value)
        {
            Dictionary<string, string> sec;
            if (!data.TryGetValue(section, out sec))
            {
                sec = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
                data[section] = sec;
            }
            sec[key] = value;
        }

        public string Get(string section, string key, string fallback)
        {
            Dictionary<string, string> sec;
            string v;
            return data.TryGetValue(section, out sec) && sec.TryGetValue(key, out v) ? v : fallback;
        }

        public int GetInt(string section, string key, int fallback)
        {
            int v;
            return int.TryParse(Get(section, key, ""), NumberStyles.Integer, CultureInfo.InvariantCulture, out v) ? v : fallback;
        }

        public float GetFloat(string section, string key, float fallback)
        {
            float v;
            return float.TryParse(Get(section, key, ""), NumberStyles.Float, CultureInfo.InvariantCulture, out v) ? v : fallback;
        }

        public bool GetBool(string section, string key, bool fallback)
        {
            bool v;
            return bool.TryParse(Get(section, key, ""), out v) ? v : fallback;
        }

        public void Save(string path, string header)
        {
            var sb = new StringBuilder(header);
            foreach (var sec in data)
            {
                sb.AppendLine().Append('[').Append(sec.Key).AppendLine("]");
                foreach (var kv in sec.Value) sb.Append(kv.Key).Append('=').AppendLine(kv.Value);
            }
            File.WriteAllText(path, sb.ToString());
        }
    }

    /// <summary>Everything that makes up one truck build. Visual mods live on the vehicle itself;
    /// the rest (sound, boost, paint RGB, rails) is script-side and re-applied by us.</summary>
    internal sealed class Build
    {
        public readonly Dictionary<int, int> Mods = new Dictionary<int, int>();
        public int WheelType = 4;
        public int Rim = -1;
        public bool CustomTires, DriftTires, BulletproofTires, Turbo, Xenon, Underglow, ExhaustPops, Whipple;
        public bool TireSmoke;
        public int XenonColor = 255, WindowTint = -1, Livery = -1, Pearl = -1, WheelColor = -1;
        public int PrimaryFinish = 1, SecondaryFinish = 1;
        public Color? Primary, Secondary;
        public Color SmokeColor = Color.White, UnderglowColor = Color.White;
        public string Sound = "";
        public float Torque = 1f, TopSpeed = 0f;
        public readonly Dictionary<int, bool> Extras = new Dictionary<int, bool>();

        private static string C(Color? c) { return c.HasValue ? c.Value.R + "," + c.Value.G + "," + c.Value.B : ""; }

        private static Color? ParseColor(string s)
        {
            var p = s.Split(',');
            int r, g, b;
            if (p.Length == 3 && int.TryParse(p[0], out r) && int.TryParse(p[1], out g) && int.TryParse(p[2], out b))
                return Color.FromArgb(Clamp(r), Clamp(g), Clamp(b));
            return null;
        }

        private static int Clamp(int v) { return Math.Max(0, Math.Min(255, v)); }

        public void Write(Ini ini, string s)
        {
            var inv = CultureInfo.InvariantCulture;
            ini.RemoveSection(s);
            ini.Set(s, "Mods", string.Join(",", Mods.Select(kv => kv.Key + ":" + kv.Value)));
            ini.Set(s, "WheelType", WheelType.ToString(inv));
            ini.Set(s, "Rim", Rim.ToString(inv));
            ini.Set(s, "CustomTires", CustomTires.ToString());
            ini.Set(s, "DriftTires", DriftTires.ToString());
            ini.Set(s, "BulletproofTires", BulletproofTires.ToString());
            ini.Set(s, "Turbo", Turbo.ToString());
            ini.Set(s, "TireSmoke", TireSmoke.ToString());
            ini.Set(s, "SmokeColor", C(SmokeColor));
            ini.Set(s, "Xenon", Xenon.ToString());
            ini.Set(s, "XenonColor", XenonColor.ToString(inv));
            ini.Set(s, "Underglow", Underglow.ToString());
            ini.Set(s, "UnderglowColor", C(UnderglowColor));
            ini.Set(s, "ExhaustPops", ExhaustPops.ToString());
            ini.Set(s, "Whipple", Whipple.ToString());
            ini.Set(s, "Sound", Sound);
            ini.Set(s, "Torque", Torque.ToString(inv));
            ini.Set(s, "TopSpeed", TopSpeed.ToString(inv));
            ini.Set(s, "Primary", C(Primary));
            ini.Set(s, "Secondary", C(Secondary));
            ini.Set(s, "PrimaryFinish", PrimaryFinish.ToString(inv));
            ini.Set(s, "SecondaryFinish", SecondaryFinish.ToString(inv));
            ini.Set(s, "Pearl", Pearl.ToString(inv));
            ini.Set(s, "WheelColor", WheelColor.ToString(inv));
            ini.Set(s, "WindowTint", WindowTint.ToString(inv));
            ini.Set(s, "Livery", Livery.ToString(inv));
            ini.Set(s, "Extras", string.Join(",", Extras.Select(kv => kv.Key + ":" + (kv.Value ? 1 : 0))));
        }

        public static Build Read(Ini ini, string s)
        {
            var b = new Build();
            foreach (var pair in ini.Get(s, "Mods", "").Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries))
            {
                var p = pair.Split(':');
                int slot, idx;
                if (p.Length == 2 && int.TryParse(p[0], out slot) && int.TryParse(p[1], out idx)) b.Mods[slot] = idx;
            }
            foreach (var pair in ini.Get(s, "Extras", "").Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries))
            {
                var p = pair.Split(':');
                int id;
                if (p.Length == 2 && int.TryParse(p[0], out id)) b.Extras[id] = p[1] == "1";
            }
            b.WheelType = ini.GetInt(s, "WheelType", 4);
            b.Rim = ini.GetInt(s, "Rim", -1);
            b.CustomTires = ini.GetBool(s, "CustomTires", false);
            b.DriftTires = ini.GetBool(s, "DriftTires", false);
            b.BulletproofTires = ini.GetBool(s, "BulletproofTires", false);
            b.Turbo = ini.GetBool(s, "Turbo", false);
            b.TireSmoke = ini.GetBool(s, "TireSmoke", false);
            b.SmokeColor = ParseColor(ini.Get(s, "SmokeColor", "")) ?? Color.White;
            b.Xenon = ini.GetBool(s, "Xenon", false);
            b.XenonColor = ini.GetInt(s, "XenonColor", 255);
            b.Underglow = ini.GetBool(s, "Underglow", false);
            b.UnderglowColor = ParseColor(ini.Get(s, "UnderglowColor", "")) ?? Color.White;
            b.ExhaustPops = ini.GetBool(s, "ExhaustPops", false);
            b.Whipple = ini.GetBool(s, "Whipple", false);
            b.Sound = ini.Get(s, "Sound", "");
            b.Torque = ini.GetFloat(s, "Torque", 1f);
            b.TopSpeed = ini.GetFloat(s, "TopSpeed", 0f);
            b.Primary = ParseColor(ini.Get(s, "Primary", ""));
            b.Secondary = ParseColor(ini.Get(s, "Secondary", ""));
            b.PrimaryFinish = ini.GetInt(s, "PrimaryFinish", 1);
            b.SecondaryFinish = ini.GetInt(s, "SecondaryFinish", 1);
            b.Pearl = ini.GetInt(s, "Pearl", -1);
            b.WheelColor = ini.GetInt(s, "WheelColor", -1);
            b.WindowTint = ini.GetInt(s, "WindowTint", -1);
            b.Livery = ini.GetInt(s, "Livery", -1);
            return b;
        }
    }

    public class AT4XGarage : Script
    {
        private const string BuildsHeader =
            "; AT4X Garage saved builds. Written by the game - safe to edit or delete while the game is closed.\r\n" +
            "; [Active] is re-applied when you get into an AT4X (if AutoApplyBuild=true).\r\n";

        private static readonly string[] WheelTypes =
        {
            "Sport", "Muscle", "Lowrider", "SUV", "Offroad", "Tuner", "Bike", "High End",
            "Benny's Originals", "Benny's Bespoke", "Open Wheel", "Street", "Track",
        };
        private static readonly string[] XenonColors =
        {
            "Stock", "White", "Blue", "Electric Blue", "Mint Green", "Lime Green", "Yellow", "Golden Shower",
            "Orange", "Red", "Pony Pink", "Hot Pink", "Purple", "Blacklight",
        };
        private static readonly string[] Tints = { "None", "Pure Black", "Dark Smoke", "Light Smoke", "Stock", "Limo", "Green" };
        private static readonly string[] Finishes = { "Normal", "Metallic", "Pearl", "Matte", "Brushed Metal", "Chrome" };
        // A useful subset of GTA's paint index table for pearl / rim colors.
        private static readonly KeyValuePair<int, string>[] IndexColors =
        {
            new KeyValuePair<int, string>(-1, "Stock"),
            new KeyValuePair<int, string>(0, "Black"), new KeyValuePair<int, string>(1, "Graphite"),
            new KeyValuePair<int, string>(4, "Silver"), new KeyValuePair<int, string>(5, "Blue Silver"),
            new KeyValuePair<int, string>(111, "Ice White"), new KeyValuePair<int, string>(27, "Red"),
            new KeyValuePair<int, string>(38, "Orange"), new KeyValuePair<int, string>(88, "Yellow"),
            new KeyValuePair<int, string>(70, "Ultra Blue"),
            new KeyValuePair<int, string>(117, "Brushed Steel"),
            new KeyValuePair<int, string>(118, "Brushed Black Steel"), new KeyValuePair<int, string>(120, "Chrome"),
            new KeyValuePair<int, string>(158, "Pure Gold"),
            new KeyValuePair<int, string>(12, "Matte Black"), new KeyValuePair<int, string>(152, "Matte Olive Drab"),
            new KeyValuePair<int, string>(153, "Matte Dark Earth"), new KeyValuePair<int, string>(154, "Matte Desert Tan"),
        };
        private static readonly KeyValuePair<string, Color>[] LightColors =
        {
            new KeyValuePair<string, Color>("White", Color.White),
            new KeyValuePair<string, Color>("Red", Color.FromArgb(255, 1, 1)),
            new KeyValuePair<string, Color>("Amber", Color.FromArgb(255, 126, 0)),
            new KeyValuePair<string, Color>("Yellow", Color.FromArgb(255, 255, 0)),
            new KeyValuePair<string, Color>("Green", Color.FromArgb(0, 255, 0)),
            new KeyValuePair<string, Color>("Ice Blue", Color.FromArgb(2, 21, 255)),
            new KeyValuePair<string, Color>("Purple", Color.FromArgb(35, 1, 255)),
            new KeyValuePair<string, Color>("Pink", Color.FromArgb(255, 5, 190)),
            new KeyValuePair<string, Color>("Black (no smoke color)", Color.FromArgb(1, 1, 1)),
        };

        private readonly string iniPath, buildsPath;
        private readonly Ini cfg;
        private readonly ObjectPool pool = new ObjectPool();
        private readonly NativeMenu main;
        private readonly Keys menuKey;
        private readonly Model truckModel;

        // Per-vehicle runtime state.
        private Vehicle current;
        private Build build = new Build();
        private readonly HashSet<int> autoApplied = new HashSet<int>();

        // Power rails animation.
        private readonly List<int[]> railSequences = new List<int[]>();
        private int[] railSeq;
        private int railFrame, railTarget, railNextFrameAt;
        private int railLastWantedAt;

        public AT4XGarage()
        {
            iniPath = Path.Combine(BaseDirectory, "AT4XGarage.ini");
            buildsPath = Path.Combine(BaseDirectory, "AT4XGarage.builds.ini");
            cfg = Ini.Load(iniPath);

            Keys k;
            menuKey = Enum.TryParse(cfg.Get("General", "MenuKey", "F7"), true, out k) ? k : Keys.F7;
            truckModel = new Model(cfg.Get("General", "Model", "at4x"));

            foreach (var seq in cfg.Get("PowerRails", "Sequences", "").Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries))
            {
                var frames = new List<int>();
                foreach (var f in seq.Split('>'))
                {
                    int i;
                    if (int.TryParse(f.Trim(), out i)) frames.Add(i);
                }
                if (frames.Count >= 2) railSequences.Add(frames.ToArray());
            }

            main = new NativeMenu("AT4X Garage", "GMC SIERRA AT4X CUSTOMS");
            pool.Add(main);
            BuildMainMenu();

            Tick += OnTick;
            KeyDown += OnKeyDown;
        }

        // ------------------------------------------------------------------ helpers

        private static int Int(ulong hash, params InputArgument[] args) { return Function.Call<int>((Hash)hash, args); }
        private static bool Bool(ulong hash, params InputArgument[] args) { return Function.Call<bool>((Hash)hash, args); }
        private static void Call(ulong hash, params InputArgument[] args) { Function.Call((Hash)hash, args); }

        private bool IsTruck(Vehicle v) { return v != null && v.Exists() && v.Model.Hash == truckModel.Hash; }

        private static bool Same(Vehicle a, Vehicle b) { return a != null && b != null && a.Handle == b.Handle; }

        /// <summary>The vehicle the menus edit: must exist, and must be the AT4X when OnlyInAT4X=true.</summary>
        private bool CanTune()
        {
            return current != null && current.Exists() && (!cfg.GetBool("General", "OnlyInAT4X", false) || IsTruck(current));
        }

        private string StockSound { get { return cfg.Get("Sounds", "Stock", "SANDKING"); } }

        private static void Notify(string msg) { GTA.UI.Notification.Show("~y~AT4X Garage~s~~n~" + msg); }

        private Vehicle PlayerVehicle()
        {
            Ped p = Game.Player.Character;
            return p.IsInVehicle() ? p.CurrentVehicle : null;
        }

        private int ModCount(int slot) { return current == null ? 0 : Int(N.GET_NUM_VEHICLE_MODS, current.Handle, slot); }

        private int GetMod(int slot) { return Int(N.GET_VEHICLE_MOD, current.Handle, slot); }

        private void SetMod(int slot, int index)
        {
            bool custom = slot == Slot.FrontWheels && build.CustomTires;
            Call(N.SET_VEHICLE_MOD, current.Handle, slot, index, custom);
            if (slot != Slot.FrontWheels) build.Mods[slot] = index;
        }

        private string ModName(int slot, int index)
        {
            string label = Function.Call<string>((Hash)N.GET_MOD_TEXT_LABEL, current.Handle, slot, index);
            if (!string.IsNullOrEmpty(label) && label != "NULL" && Bool(N.DOES_TEXT_LABEL_EXIST, label))
                return Game.GetLocalizedString(label);
            return "Option " + (index + 1);
        }

        private static List<KeyValuePair<string, string>> ParsePairs(string raw, char itemSep)
        {
            var list = new List<KeyValuePair<string, string>>();
            foreach (var item in raw.Split(new[] { itemSep }, StringSplitOptions.RemoveEmptyEntries))
            {
                int c = item.IndexOf(':');
                if (c > 0) list.Add(new KeyValuePair<string, string>(item.Substring(0, c).Trim(), item.Substring(c + 1).Trim()));
            }
            return list;
        }

        private string[] Names(string key, int count, string fallbackPrefix)
        {
            var given = cfg.Get("Names", key, "").Split(',').Select(s => s.Trim()).Where(s => s.Length > 0).ToArray();
            var result = new string[count];
            for (int i = 0; i < count; i++) result[i] = i < given.Length ? given[i] : fallbackPrefix + " " + (i + 1);
            return result;
        }

        // ------------------------------------------------------------------ build apply / capture

        /// <summary>Start a new Build from what's currently fitted to the vehicle.
        /// Script-only values (sound, boost, custom RGB paint) start at their defaults.</summary>
        private void CaptureFromVehicle()
        {
            build = new Build();
            foreach (int slot in Slot.Saved) build.Mods[slot] = GetMod(slot);
            // Store power rails as their retracted frame so a build never saves them half-deployed.
            int seq = RailSequenceIndexFor(build.Mods[Slot.Skirt]);
            if (seq >= 0) build.Mods[Slot.Skirt] = railSequences[seq][0];
            build.WheelType = Int(N.GET_VEHICLE_WHEEL_TYPE, current.Handle);
            build.Rim = GetMod(Slot.FrontWheels);
            build.CustomTires = Bool(N.GET_VEHICLE_MOD_VARIATION, current.Handle, Slot.FrontWheels);
            build.DriftTires = Bool(N.GET_DRIFT_TYRES_SET, current.Handle);
            build.BulletproofTires = !Bool(N.GET_VEHICLE_TYRES_CAN_BURST, current.Handle);
            build.Turbo = Bool(N.IS_TOGGLE_MOD_ON, current.Handle, Slot.Turbo);
            build.TireSmoke = Bool(N.IS_TOGGLE_MOD_ON, current.Handle, Slot.TireSmoke);
            build.Xenon = Bool(N.IS_TOGGLE_MOD_ON, current.Handle, Slot.Xenon);
            build.XenonColor = Int(N.GET_VEHICLE_XENON_LIGHT_COLOR_INDEX, current.Handle);
            build.WindowTint = Int(N.GET_VEHICLE_WINDOW_TINT, current.Handle);
            build.Livery = Int(N.GET_VEHICLE_LIVERY, current.Handle);
            for (int id = 1; id <= 14; id++)
                if (Bool(N.DOES_EXTRA_EXIST, current.Handle, id))
                    build.Extras[id] = Bool(N.IS_VEHICLE_EXTRA_TURNED_ON, current.Handle, id);
        }

        private void ApplyBuild(Vehicle v, Build b)
        {
            current = v;
            build = b;
            int h = v.Handle;
            Call(N.SET_VEHICLE_MOD_KIT, h, 0);
            Call(N.SET_VEHICLE_WHEEL_TYPE, h, b.WheelType);
            foreach (var kv in b.Mods) Call(N.SET_VEHICLE_MOD, h, kv.Key, kv.Value, false);
            Call(N.SET_VEHICLE_MOD, h, Slot.FrontWheels, b.Rim, b.CustomTires);
            Call(N.SET_DRIFT_TYRES, h, b.DriftTires);
            Call(N.SET_VEHICLE_TYRES_CAN_BURST, h, !b.BulletproofTires);
            Call(N.TOGGLE_VEHICLE_MOD, h, Slot.Turbo, b.Turbo);
            Call(N.TOGGLE_VEHICLE_MOD, h, Slot.TireSmoke, b.TireSmoke);
            Call(N.SET_VEHICLE_TYRE_SMOKE_COLOR, h, (int)b.SmokeColor.R, (int)b.SmokeColor.G, (int)b.SmokeColor.B);
            Call(N.TOGGLE_VEHICLE_MOD, h, Slot.Xenon, b.Xenon);
            Call(N.SET_VEHICLE_XENON_LIGHT_COLOR_INDEX, h, b.XenonColor);
            ApplyUnderglow();
            if (b.WindowTint >= 0) Call(N.SET_VEHICLE_WINDOW_TINT, h, b.WindowTint);
            if (b.Livery >= 0) Call(N.SET_VEHICLE_LIVERY, h, b.Livery);
            foreach (var kv in b.Extras)
                if (Bool(N.DOES_EXTRA_EXIST, h, kv.Key)) Call(N.SET_VEHICLE_EXTRA, h, kv.Key, !kv.Value);
            ApplyPaint();
            ApplySound();
            Call(N.ENABLE_VEHICLE_EXHAUST_POPS, h, b.ExhaustPops);
            Call(N.MODIFY_VEHICLE_TOP_SPEED, h, b.TopSpeed);
            ResetRails();
        }

        private void ApplyPaint()
        {
            int h = current.Handle;
            if (build.Primary.HasValue)
            {
                Call(N.SET_VEHICLE_MOD_COLOR_1, h, build.PrimaryFinish, 0, 0);
                var c = build.Primary.Value;
                Call(N.SET_VEHICLE_CUSTOM_PRIMARY_COLOUR, h, (int)c.R, (int)c.G, (int)c.B);
            }
            if (build.Secondary.HasValue)
            {
                Call(N.SET_VEHICLE_MOD_COLOR_2, h, build.SecondaryFinish, 0);
                var c = build.Secondary.Value;
                Call(N.SET_VEHICLE_CUSTOM_SECONDARY_COLOUR, h, (int)c.R, (int)c.G, (int)c.B);
            }
            if (build.Pearl >= 0 || build.WheelColor >= 0)
            {
                // SET_VEHICLE_EXTRA_COLOURS sets both at once; 0 keeps a sane default for the unset one.
                Call(N.SET_VEHICLE_EXTRA_COLOURS, h, Math.Max(0, build.Pearl), Math.Max(0, build.WheelColor));
            }
        }

        private void ApplySound()
        {
            if (!string.IsNullOrEmpty(build.Sound)) Call(N.FORCE_USE_AUDIO_GAME_OBJECT, current.Handle, build.Sound);
        }

        private void ApplyUnderglow()
        {
            int h = current.Handle;
            for (int i = 0; i < 4; i++) Call(N.SET_VEHICLE_NEON_ENABLED, h, i, build.Underglow);
            var c = build.UnderglowColor;
            Call(N.SET_VEHICLE_NEON_COLOUR, h, (int)c.R, (int)c.G, (int)c.B);
        }

        // ------------------------------------------------------------------ builds on disk

        private void SaveBuild(string name)
        {
            var ini = Ini.Load(buildsPath);
            build.Write(ini, name);
            if (name != "Active") build.Write(ini, "Active");
            ini.Save(buildsPath, BuildsHeader);
            Notify("Saved build ~g~" + name + "~s~.");
        }

        private bool LoadBuild(Vehicle v, string name, bool quiet)
        {
            var ini = Ini.Load(buildsPath);
            if (!ini.HasSection(name))
            {
                if (!quiet) Notify("No build saved in ~r~" + name + "~s~ yet.");
                return false;
            }
            ApplyBuild(v, Build.Read(ini, name));
            if (!quiet) Notify("Loaded build ~g~" + name + "~s~.");
            return true;
        }

        // ------------------------------------------------------------------ menus

        private NativeMenu Sub(string title, Action<NativeMenu> fill)
        {
            var m = new NativeMenu("AT4X Garage", title);
            pool.Add(m);
            main.AddSubMenu(m);
            m.Opening += (s, e) =>
            {
                m.Clear();
                if (CanTune()) fill(m);
                else m.Add(new NativeItem("Get in your AT4X first", "Or use Spawn AT4X on the main menu."));
            };
            return m;
        }

        private void BuildMainMenu()
        {
            var spawn = new NativeItem("Spawn AT4X", "Spawn a fresh GMC Sierra AT4X and apply your Active build.");
            spawn.Activated += (s, e) => SpawnTruck();
            main.Add(spawn);

            var fix = new NativeItem("Repair & Wash", "Fix all damage and clean the truck.");
            fix.Activated += (s, e) =>
            {
                if (current == null) return;
                Call(N.SET_VEHICLE_FIXED, current.Handle);
                Call(N.SET_VEHICLE_DEFORMATION_FIXED, current.Handle);
                Call(N.SET_VEHICLE_DIRT_LEVEL, current.Handle, 0f);
            };
            main.Add(fix);

            Sub("Body & Parts", FillBody);
            Sub("Rims & Tires", FillWheels);
            Sub("Power Rails", FillRails);
            Sub("Exhaust & Sound", FillSound);
            Sub("Whipple Supercharger", FillWhipple);
            Sub("Performance", FillPerformance);
            Sub("Paint", FillPaint);
            Sub("Lights", FillLights);
            Sub("Extras & Livery", FillExtras);
            Sub("Saved Builds", FillBuilds);
        }

        /// <summary>A Stock + parts list for one mod slot, or null when the kit has nothing there.</summary>
        private NativeListItem<string> SlotList(string title, int slot, string[] names = null)
        {
            int count = names != null ? names.Length : ModCount(slot);
            if (names != null) count = Math.Min(count, ModCount(slot));
            if (count <= 0) return null;
            var items = new List<string> { "Stock" };
            for (int i = 0; i < count; i++) items.Add(names != null ? names[i] : ModName(slot, i));
            var li = new NativeListItem<string>(title, items.ToArray());
            int cur = GetMod(slot);
            li.SelectedIndex = cur >= 0 && cur < count ? cur + 1 : 0;
            li.ItemChanged += (s, e) => SetMod(slot, e.Index - 1);
            return li;
        }

        private void FillBody(NativeMenu m)
        {
            foreach (var kv in Slot.Body)
            {
                var li = SlotList(kv.Value, kv.Key);
                if (li != null) m.Add(li);
            }
            if (m.Items.Count == 0) m.Add(new NativeItem("No body parts found", "This vehicle has no visual mod kit parts installed."));
        }

        private void FillWheels(NativeMenu m)
        {
            var type = new NativeListItem<string>("Wheel Category", WheelTypes);
            type.SelectedIndex = Math.Max(0, Math.Min(WheelTypes.Length - 1, Int(N.GET_VEHICLE_WHEEL_TYPE, current.Handle)));
            m.Add(type);

            var rims = new NativeListItem<string>("Rims", "Stock");
            Action refillRims = () =>
            {
                rims.Clear();
                rims.Add("Stock (AT4X factory)");
                int n = ModCount(Slot.FrontWheels);
                for (int i = 0; i < n; i++) rims.Add(ModName(Slot.FrontWheels, i));
            };
            refillRims();
            int cur = GetMod(Slot.FrontWheels);
            rims.SelectedIndex = cur >= 0 && cur + 1 < rims.Items.Count ? cur + 1 : 0;
            rims.ItemChanged += (s, e) => { build.Rim = e.Index - 1; SetMod(Slot.FrontWheels, build.Rim); };
            m.Add(rims);

            type.ItemChanged += (s, e) =>
            {
                build.WheelType = e.Index;
                build.Rim = -1;
                Call(N.SET_VEHICLE_WHEEL_TYPE, current.Handle, e.Index);
                SetMod(Slot.FrontWheels, -1);
                refillRims();
                rims.SelectedIndex = 0;
            };

            var custom = new NativeCheckboxItem("Raised-Letter Tires", "Custom tire sidewalls for the selected rim.", build.CustomTires);
            custom.CheckboxChanged += (s, e) => { build.CustomTires = custom.Checked; SetMod(Slot.FrontWheels, build.Rim); };
            m.Add(custom);

            var drift = new NativeCheckboxItem("Drift Tires", "Low-grip compound.", build.DriftTires);
            drift.CheckboxChanged += (s, e) => { build.DriftTires = drift.Checked; Call(N.SET_DRIFT_TYRES, current.Handle, drift.Checked); };
            m.Add(drift);

            var bp = new NativeCheckboxItem("Run-Flat / Bulletproof", "Tires can't be popped.", build.BulletproofTires);
            bp.CheckboxChanged += (s, e) => { build.BulletproofTires = bp.Checked; Call(N.SET_VEHICLE_TYRES_CAN_BURST, current.Handle, !bp.Checked); };
            m.Add(bp);

            var smoke = new NativeListItem<string>("Tire Smoke", new[] { "Off" }.Concat(LightColors.Select(c => c.Key)).ToArray());
            smoke.SelectedIndex = build.TireSmoke ? 1 + Math.Max(0, Array.FindIndex(LightColors, c => c.Value.ToArgb() == build.SmokeColor.ToArgb())) : 0;
            smoke.ItemChanged += (s, e) =>
            {
                build.TireSmoke = e.Index > 0;
                Call(N.TOGGLE_VEHICLE_MOD, current.Handle, Slot.TireSmoke, build.TireSmoke);
                if (build.TireSmoke)
                {
                    build.SmokeColor = LightColors[e.Index - 1].Value;
                    Call(N.SET_VEHICLE_TYRE_SMOKE_COLOR, current.Handle, (int)build.SmokeColor.R, (int)build.SmokeColor.G, (int)build.SmokeColor.B);
                }
            };
            m.Add(smoke);

            var rimColor = new NativeListItem<string>("Rim Color", IndexColors.Select(c => c.Value).ToArray());
            rimColor.SelectedIndex = Math.Max(0, Array.FindIndex(IndexColors, c => c.Key == build.WheelColor));
            rimColor.ItemChanged += (s, e) => { build.WheelColor = IndexColors[e.Index].Key; ApplyPaint(); };
            m.Add(rimColor);
        }

        private int RailSequenceIndexFor(int skirtIndex)
        {
            for (int i = 0; i < railSequences.Count; i++)
                if (Array.IndexOf(railSequences[i], skirtIndex) >= 0) return i;
            return -1;
        }

        private void FillRails(NativeMenu m)
        {
            // Hide the in-between animation frames: show stock, every non-rail part and each sequence's retracted frame.
            int n = ModCount(Slot.Skirt);
            var choices = new List<int> { -1 };
            for (int i = 0; i < n; i++)
            {
                int seq = RailSequenceIndexFor(i);
                if (seq < 0 || railSequences[seq][0] == i) choices.Add(i);
            }
            var names = choices.Select(i => i < 0 ? "Stock" : ModName(Slot.Skirt, i)).ToArray();
            var style = new NativeListItem<string>("Running Boards", "Pick rails, steps or sliders.", names);
            int cur = GetMod(Slot.Skirt);
            int seqCur = RailSequenceIndexFor(cur);
            if (seqCur >= 0) cur = railSequences[seqCur][0];
            style.SelectedIndex = Math.Max(0, choices.IndexOf(cur));
            style.ItemChanged += (s, e) => { SetMod(Slot.Skirt, choices[e.Index]); ResetRails(); };
            m.Add(style);

            var auto = new NativeCheckboxItem("Auto Deploy", "Power rails fold out when a door opens and tuck away when you drive off.",
                cfg.GetBool("PowerRails", "AutoDeploy", true));
            auto.CheckboxChanged += (s, e) => cfg.Set("PowerRails", "AutoDeploy", auto.Checked.ToString());
            m.Add(auto);

            var deploy = new NativeItem("Deploy Now", "Fold the power rails out.");
            deploy.Activated += (s, e) => { if (StartRails(true)) railLastWantedAt = Game.GameTime + 5000; };
            m.Add(deploy);

            var retract = new NativeItem("Retract Now", "Tuck the power rails away.");
            retract.Activated += (s, e) => { railLastWantedAt = 0; StartRails(false); };
            m.Add(retract);

            if (railSequences.Count == 0)
                m.Add(new NativeItem("(No power rail sequences configured)", "Set [PowerRails] Sequences in AT4XGarage.ini."));
        }

        private void FillSound(NativeMenu m)
        {
            var ex = SlotList("Exhaust", Slot.Exhaust);
            if (ex != null) m.Add(ex);

            var presets = ParsePairs(cfg.Get("Sounds", "Presets", "SANDKING:Big-Block V8 Truck"), ',');
            var labels = new List<string> { "Stock (" + StockSound + ")" };
            labels.AddRange(presets.Select(p => p.Value));
            var sound = new NativeListItem<string>("Engine Sound", "Swap the engine note. Add-on sound packs can be added in the INI.", labels.ToArray());
            int soundSel = presets.FindIndex(p => p.Key.Equals(build.Sound, StringComparison.OrdinalIgnoreCase));
            sound.SelectedIndex = build.Sound.Equals(StockSound, StringComparison.OrdinalIgnoreCase) ? 0 : soundSel + 1;
            sound.ItemChanged += (s, e) =>
            {
                build.Sound = e.Index == 0 ? StockSound : presets[e.Index - 1].Key;
                ApplySound();
            };
            m.Add(sound);

            var pops = new NativeCheckboxItem("Pops & Crackles", "Exhaust pops on lift-off.", build.ExhaustPops);
            pops.CheckboxChanged += (s, e) => { build.ExhaustPops = pops.Checked; Call(N.ENABLE_VEHICLE_EXHAUST_POPS, current.Handle, pops.Checked); };
            m.Add(pops);

            var horn = SlotList("Horn", Slot.Horn, new[] { "Air Horn", "Police", "Clown", "Musical 1", "Musical 2", "Musical 3", "Sad Trombone" });
            if (horn != null) m.Add(horn);
        }

        private void FillWhipple(NativeMenu m)
        {
            var boosts = ParsePairs(cfg.Get("Whipple", "Boost", "12 psi (700 hp):1.60"), ',');
            if (boosts.Count == 0) boosts.Add(new KeyValuePair<string, string>("12 psi (700 hp)", "1.60"));
            Func<int, float> torqueOf = i =>
            {
                float t;
                return float.TryParse(boosts[i].Value, NumberStyles.Float, CultureInfo.InvariantCulture, out t) ? t : 1.6f;
            };

            var install = new NativeCheckboxItem("Whipple 3.0L Installed",
                "One-click package: blower, cut-out hood, big-mouth intake, boost and blower sound.", build.Whipple);
            m.Add(install);

            var boost = new NativeListItem<string>("Boost", "Torque multiplier applied while supercharged.", boosts.Select(b => b.Key).ToArray());
            int sel = -1;
            for (int i = 0; i < boosts.Count && build.Whipple; i++)
                if (Math.Abs(torqueOf(i) - build.Torque) < 0.001f) sel = i;
            boost.SelectedIndex = sel >= 0 ? sel : Math.Max(0, Math.Min(boosts.Count - 1, cfg.GetInt("Whipple", "DefaultBoost", 0)));
            boost.ItemChanged += (s, e) => { if (build.Whipple) build.Torque = torqueOf(e.Index); };
            m.Add(boost);

            var look = SlotList("Blower Finish", Slot.EngineBay1);
            var intake = SlotList("Intake", Slot.EngineBay2);
            // The blower/hood/intake part indices only mean something on the AT4X's own mod kit.
            bool parts = IsTruck(current);

            install.CheckboxChanged += (s, e) =>
            {
                build.Whipple = install.Checked;
                if (build.Whipple)
                {
                    if (parts)
                    {
                        SetMod(Slot.EngineBay1, cfg.GetInt("Whipple", "SuperchargerIndex", 0));
                        SetMod(Slot.Hood, cfg.GetInt("Whipple", "HoodIndex", -1));
                        SetMod(Slot.EngineBay2, cfg.GetInt("Whipple", "IntakeIndex", -1));
                    }
                    build.Torque = torqueOf(boost.SelectedIndex);
                    build.TopSpeed = cfg.GetFloat("Whipple", "TopSpeedPercent", 6f);
                    build.Sound = cfg.Get("Whipple", "Sound", build.Sound);
                    ApplySound();
                    Notify("Whipple installed: ~g~" + boosts[boost.SelectedIndex].Key + "~s~.");
                }
                else
                {
                    if (parts)
                    {
                        SetMod(Slot.EngineBay1, -1);
                        SetMod(Slot.Hood, -1);
                        SetMod(Slot.EngineBay2, -1);
                    }
                    build.Torque = 1f;
                    build.TopSpeed = 0f;
                    build.Sound = StockSound;
                    ApplySound();
                    Notify("Whipple removed - back to the naturally aspirated 6.2L.");
                }
                Call(N.MODIFY_VEHICLE_TOP_SPEED, current.Handle, build.TopSpeed);
                if (look != null) look.SelectedIndex = Math.Max(0, GetMod(Slot.EngineBay1) + 1);
                if (intake != null) intake.SelectedIndex = Math.Max(0, GetMod(Slot.EngineBay2) + 1);
            };

            if (look != null) m.Add(look);
            if (intake != null) m.Add(intake);
        }

        private void FillPerformance(NativeMenu m)
        {
            Action<string, int, string> add = (title, slot, key) =>
            {
                var li = SlotList(title, slot, Names(key, ModCount(slot), title));
                if (li != null) m.Add(li);
            };
            add("Engine", Slot.Engine, "Engine");
            add("Brakes", Slot.Brakes, "Brakes");
            add("Transmission", Slot.Transmission, "Transmission");
            add("Suspension / Lift", Slot.Suspension, "Suspension");
            add("Armor", Slot.Armor, "Armor");

            var turbo = new NativeCheckboxItem("Forced-Induction Sounds", "GTA's turbo toggle: extra power plus spool/blow-off sounds.", build.Turbo);
            turbo.CheckboxChanged += (s, e) => { build.Turbo = turbo.Checked; Call(N.TOGGLE_VEHICLE_MOD, current.Handle, Slot.Turbo, turbo.Checked); };
            m.Add(turbo);
        }

        private void FillPaint(NativeMenu m)
        {
            var colors = ParsePairs(cfg.Get("Paint", "Colors", "Summit White:236,237,235"), '|')
                .Select(p => new KeyValuePair<string, Color?>(p.Key, ParseRgb(p.Value)))
                .Where(p => p.Value.HasValue).ToList();
            var names = new[] { "Stock" }.Concat(colors.Select(c => c.Key)).ToArray();

            Func<Color?, int> indexOf = c => c.HasValue ? colors.FindIndex(p => p.Value.Value.ToArgb() == c.Value.ToArgb()) + 1 : 0;

            var primary = new NativeListItem<string>("Primary Color", names) { SelectedIndex = Math.Max(0, indexOf(build.Primary)) };
            primary.ItemChanged += (s, e) =>
            {
                if (e.Index == 0) { build.Primary = null; Notify("Stock paint returns next time the truck spawns."); return; }
                build.Primary = colors[e.Index - 1].Value;
                ApplyPaint();
            };
            m.Add(primary);

            var pFinish = new NativeListItem<string>("Primary Finish", Finishes) { SelectedIndex = Math.Max(0, Math.Min(5, build.PrimaryFinish)) };
            pFinish.ItemChanged += (s, e) => { build.PrimaryFinish = e.Index; ApplyPaint(); };
            m.Add(pFinish);

            var secondary = new NativeListItem<string>("Secondary Color", names) { SelectedIndex = Math.Max(0, indexOf(build.Secondary)) };
            secondary.ItemChanged += (s, e) =>
            {
                if (e.Index == 0) { build.Secondary = null; return; }
                build.Secondary = colors[e.Index - 1].Value;
                ApplyPaint();
            };
            m.Add(secondary);

            var sFinish = new NativeListItem<string>("Secondary Finish", Finishes) { SelectedIndex = Math.Max(0, Math.Min(5, build.SecondaryFinish)) };
            sFinish.ItemChanged += (s, e) => { build.SecondaryFinish = e.Index; ApplyPaint(); };
            m.Add(sFinish);

            var pearl = new NativeListItem<string>("Pearlescent", IndexColors.Select(c => c.Value).ToArray());
            pearl.SelectedIndex = Math.Max(0, Array.FindIndex(IndexColors, c => c.Key == build.Pearl));
            pearl.ItemChanged += (s, e) => { build.Pearl = IndexColors[e.Index].Key; ApplyPaint(); };
            m.Add(pearl);

            var tint = new NativeListItem<string>("Window Tint", Tints);
            tint.SelectedIndex = Math.Max(0, Math.Min(Tints.Length - 1, Int(N.GET_VEHICLE_WINDOW_TINT, current.Handle)));
            tint.ItemChanged += (s, e) => { build.WindowTint = e.Index; Call(N.SET_VEHICLE_WINDOW_TINT, current.Handle, e.Index); };
            m.Add(tint);
        }

        private static Color? ParseRgb(string s)
        {
            var p = s.Split(',');
            int r, g, b;
            if (p.Length == 3 && int.TryParse(p[0].Trim(), out r) && int.TryParse(p[1].Trim(), out g) && int.TryParse(p[2].Trim(), out b))
                return Color.FromArgb(Math.Max(0, Math.Min(255, r)), Math.Max(0, Math.Min(255, g)), Math.Max(0, Math.Min(255, b)));
            return null;
        }

        private void FillLights(NativeMenu m)
        {
            var xenon = new NativeListItem<string>("Headlights", new[] { "Halogen" }.Concat(XenonColors.Select(c => "LED - " + c)).ToArray());
            int xi = build.XenonColor >= 0 && build.XenonColor <= 12 ? build.XenonColor + 2 : 1;
            xenon.SelectedIndex = build.Xenon ? xi : 0;
            xenon.ItemChanged += (s, e) =>
            {
                build.Xenon = e.Index > 0;
                build.XenonColor = e.Index <= 1 ? 255 : e.Index - 2;
                Call(N.TOGGLE_VEHICLE_MOD, current.Handle, Slot.Xenon, build.Xenon);
                Call(N.SET_VEHICLE_XENON_LIGHT_COLOR_INDEX, current.Handle, build.XenonColor);
            };
            m.Add(xenon);

            var glow = new NativeListItem<string>("Rock Lights / Underglow", new[] { "Off" }.Concat(LightColors.Select(c => c.Key)).ToArray());
            glow.SelectedIndex = build.Underglow ? 1 + Math.Max(0, Array.FindIndex(LightColors, c => c.Value.ToArgb() == build.UnderglowColor.ToArgb())) : 0;
            glow.ItemChanged += (s, e) =>
            {
                build.Underglow = e.Index > 0;
                if (build.Underglow) build.UnderglowColor = LightColors[e.Index - 1].Value;
                ApplyUnderglow();
            };
            m.Add(glow);
        }

        private void FillExtras(NativeMenu m)
        {
            int h = current.Handle;
            for (int id = 1; id <= 14; id++)
            {
                if (!Bool(N.DOES_EXTRA_EXIST, h, id)) continue;
                int extra = id;
                var cb = new NativeCheckboxItem("Extra " + id, "Toggle model extra_" + id + ".", Bool(N.IS_VEHICLE_EXTRA_TURNED_ON, h, id));
                cb.CheckboxChanged += (s, e) => { build.Extras[extra] = cb.Checked; Call(N.SET_VEHICLE_EXTRA, current.Handle, extra, !cb.Checked); };
                m.Add(cb);
            }
            int liveries = Int(N.GET_VEHICLE_LIVERY_COUNT, h);
            if (liveries > 0)
            {
                var names = Enumerable.Range(0, liveries).Select(i => "Livery " + (i + 1)).ToArray();
                var li = new NativeListItem<string>("Livery / Decals", names) { SelectedIndex = Math.Max(0, Math.Min(liveries - 1, Int(N.GET_VEHICLE_LIVERY, h))) };
                li.ItemChanged += (s, e) => { build.Livery = e.Index; Call(N.SET_VEHICLE_LIVERY, current.Handle, e.Index); };
                m.Add(li);
            }
            var livParts = SlotList("Livery Parts", Slot.Livery);
            if (livParts != null) m.Add(livParts);
            if (m.Items.Count == 0) m.Add(new NativeItem("No extras or liveries on this model"));
        }

        private void FillBuilds(NativeMenu m)
        {
            for (int i = 1; i <= 5; i++)
            {
                string name = "Build" + i;
                var save = new NativeItem("Save to Slot " + i, "Also becomes your Active build.");
                save.Activated += (s, e) => SaveBuild(name);
                m.Add(save);
                var load = new NativeItem("Load Slot " + i);
                load.Activated += (s, e) => { if (LoadBuild(current, name, false)) SaveBuild("Active"); };
                m.Add(load);
            }
            var reset = new NativeItem("Reset to Factory AT4X", "Removes every mod and script tune from this truck.");
            reset.Activated += (s, e) =>
            {
                var b = new Build();
                foreach (int slot in Slot.Saved) b.Mods[slot] = -1;
                b.Sound = StockSound;
                ApplyBuild(current, b);
                Notify("Reset to factory spec. Stock paint returns on next spawn.");
            };
            m.Add(reset);
        }

        // ------------------------------------------------------------------ spawn

        private void SpawnTruck()
        {
            if (!truckModel.IsInCdImage || !truckModel.IsVehicle)
            {
                Notify("~r~Model '" + cfg.Get("General", "Model", "at4x") + "' isn't installed.~s~ Check dlclist.xml and the dlc.rpf.");
                return;
            }
            if (!truckModel.Request(5000))
            {
                Notify("~r~Timed out loading the model.");
                return;
            }
            Ped p = Game.Player.Character;
            Vector3 pos = p.Position + p.ForwardVector * 6f;
            Vehicle v = World.CreateVehicle(truckModel, pos, p.Heading + 90f);
            truckModel.MarkAsNoLongerNeeded();
            if (v == null) return;
            v.PlaceOnGround();
            Call(N.SET_VEHICLE_MOD_KIT, v.Handle, 0);
            p.SetIntoVehicle(v, VehicleSeat.Driver);
            current = v;
            autoApplied.Add(v.Handle);
            if (!LoadBuild(v, "Active", true))
            {
                CaptureFromVehicle();
                ResetRails();
            }
        }

        // ------------------------------------------------------------------ power rails

        private void ResetRails()
        {
            railSeq = null;
            if (!IsTruck(current)) return;
            int seq = RailSequenceIndexFor(GetMod(Slot.Skirt));
            if (seq < 0) return;
            railSeq = railSequences[seq];
            railFrame = Array.IndexOf(railSeq, GetMod(Slot.Skirt));
            railTarget = railFrame;
        }

        /// <summary>Begin animating toward deployed (true) or retracted (false). Returns false if no power rails are fitted.</summary>
        private bool StartRails(bool deploy)
        {
            if (railSeq == null) ResetRails();
            if (railSeq == null) return false;
            railTarget = deploy ? railSeq.Length - 1 : 0;
            return true;
        }

        private void UpdateRails()
        {
            if (railSeq == null || current == null || !current.Exists()) return;
            int now = Game.GameTime;

            if (cfg.GetBool("PowerRails", "AutoDeploy", true))
            {
                Ped p = Game.Player.Character;
                bool doorOpen = false;
                for (int d = 0; d < 4 && !doorOpen; d++)
                    doorOpen = Function.Call<float>((Hash)N.GET_VEHICLE_DOOR_ANGLE_RATIO, current.Handle, d) > 0.05f;
                bool entering = Int(N.GET_VEHICLE_PED_IS_TRYING_TO_ENTER, p.Handle) == current.Handle;
                bool slow = current.Speed * 3.6f < cfg.GetFloat("PowerRails", "MaxSpeedKph", 8f);
                if ((doorOpen || entering) && slow) railLastWantedAt = now;
                bool wanted = slow && now - railLastWantedAt < cfg.GetInt("PowerRails", "RetractDelayMs", 1500);
                railTarget = wanted ? railSeq.Length - 1 : 0;
            }
            else if (current.Speed * 3.6f >= cfg.GetFloat("PowerRails", "MaxSpeedKph", 8f))
            {
                railTarget = 0;
            }

            if (railFrame == railTarget || now < railNextFrameAt) return;
            railFrame += railTarget > railFrame ? 1 : -1;
            Call(N.SET_VEHICLE_MOD, current.Handle, Slot.Skirt, railSeq[railFrame], false);
            railNextFrameAt = now + cfg.GetInt("PowerRails", "FrameMs", 90);
        }

        // ------------------------------------------------------------------ loop

        private void SwitchTo(Vehicle v)
        {
            current = v;
            Call(N.SET_VEHICLE_MOD_KIT, v.Handle, 0);
            bool applied = false;
            if (IsTruck(v) && cfg.GetBool("General", "AutoApplyBuild", true) && autoApplied.Add(v.Handle))
                applied = LoadBuild(v, "Active", true);
            if (!applied) CaptureFromVehicle();
            ResetRails();
        }

        private void OnTick(object sender, EventArgs e)
        {
            pool.Process();

            Vehicle v = PlayerVehicle();
            if (v == null)
            {
                // Walking up to a different AT4X: adopt it so its power rails fold out for you.
                int entering = Int(N.GET_VEHICLE_PED_IS_TRYING_TO_ENTER, Game.Player.Character.Handle);
                Vehicle target = entering != 0 ? Entity.FromHandle(entering) as Vehicle : null;
                if (IsTruck(target)) v = target;
            }
            if (v != null && !Same(v, current)) SwitchTo(v);
            if (current != null && !current.Exists())
            {
                current = null;
                railSeq = null;
                pool.HideAll();
                return;
            }
            if (current == null) return;

            // The torque boost only lasts one frame, so it's re-applied every tick while you drive.
            if (build.Torque != 1f && Game.Player.Character.IsInVehicle(current))
                Call(N.SET_VEHICLE_CHEAT_POWER_INCREASE, current.Handle, build.Torque);

            UpdateRails();
        }

        private void OnKeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode != menuKey) return;
            if (pool.AreAnyVisible)
            {
                pool.HideAll();
                return;
            }
            // The main menu always opens (Spawn works on foot); submenus explain when there's nothing to tune.
            if (!CanTune()) Notify("Get in your AT4X to tune it, or use ~g~Spawn AT4X~s~.");
            main.Visible = true;
        }
    }
}
