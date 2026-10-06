using System;
using System.IO;
using CodeWalker.GameFiles;

class P {
    static void Main(string[] a) {
        string inp = a[0], outDir = a[1];
        Directory.CreateDirectory(outDir);
        var data = File.ReadAllBytes(inp);
        string name = Path.GetFileName(inp);
        if (inp.EndsWith(".yft.xml")) {      // XML -> binary (textures folder next to the XML)
            string folder = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(inp)), name.Substring(0, name.Length - 8));
            var yft = XmlYft.GetYft(File.ReadAllText(inp), folder);
            var bin = yft.Save();
            File.WriteAllBytes(Path.Combine(outDir, name.Substring(0, name.Length - 4)), bin);
            Console.WriteLine($"{name}: {bin.Length} bytes");
            return;
        }
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
