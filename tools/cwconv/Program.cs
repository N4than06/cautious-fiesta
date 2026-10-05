using System;
using System.IO;
using CodeWalker.GameFiles;

class P {
    static void Main(string[] a) {
        string inp = a[0], outDir = a[1];
        Directory.CreateDirectory(outDir);
        var data = File.ReadAllBytes(inp);
        string name = Path.GetFileName(inp);
        string texDir = Path.Combine(outDir, Path.GetFileNameWithoutExtension(inp));
        Directory.CreateDirectory(texDir);
        string xml;
        if (inp.EndsWith(".yft")) {
            var f = new YftFile(); RpfFile.LoadResourceFile(f, data, 162);
            xml = YftXml.GetXml(f, texDir);
        } else if (inp.EndsWith(".ytd")) {
            var f = new YtdFile(); RpfFile.LoadResourceFile(f, data, 13);
            xml = YtdXml.GetXml(f, texDir);
        } else throw new Exception("unsupported");
        File.WriteAllText(Path.Combine(outDir, name + ".xml"), xml);
        Console.WriteLine($"{name}: {xml.Length} chars");
    }
}
