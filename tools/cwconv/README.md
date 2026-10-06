# cwconv — binary YFT/YTD -> CodeWalker XML on any OS

Uses CodeWalker.Core (netstandard2.0) so binary GTA V resources can be converted to the XML that Sollumz imports,
without Windows or PyMateria.

    git clone --depth 1 https://github.com/dexyfex/CodeWalker.git
    dotnet build -c Release -p:CODEWALKER_DIR=/path/to/CodeWalker tools/cwconv
    dotnet tools/cwconv/bin/Release/net8.0/cwconv.dll model.yft out_dir     # -> out_dir/model.yft.xml + textures
    dotnet tools/cwconv/bin/Release/net8.0/cwconv.dll model.ytd out_dir

`tools/rpf7.py ARCHIVE.rpf OUT_DIR` extracts unencrypted (OPEN) RPF7 archives such as add-on dlc.rpf files.
Donor/purchased models are never committed to this repository.
