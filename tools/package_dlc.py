#!/usr/bin/env python3
"""Package dlc/at4x plus built model files into a drop-in dlc.rpf (unencrypted RPF7, as OpenIV writes them).

    python3 tools/package_dlc.py STREAM_DIR OUT/dlc.rpf

STREAM_DIR holds the binary stream files (at4x.yft, at4x_hi.yft, at4x.ytd and any mod-part .yft). Visible mod-kit
entries whose model file is not in STREAM_DIR are left out of carcols.meta (stat upgrades, horns etc. stay), so the
pack never references a model that does not exist.
"""
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DLC = os.path.join(ROOT, "dlc", "at4x")


# ---------------------------------------------------------------------------------------------- RPF7 writer

class Dir:
    def __init__(self):
        self.items = {}       # name -> Dir | bytes


def _rsc_flags(data):
    if data[:4] == b"RSC7":
        ver, sysf, gfxf = struct.unpack_from("<III", data, 4)
        return sysf, gfxf
    return None


def build_rpf_bfs(root):
    """Breadth-first layout: every directory's children are contiguous, as RPF7 requires."""
    names = bytearray(b"\0")
    name_off = {"": 0}

    def name(n):
        if n not in name_off:
            name_off[n] = len(names)
            names.extend(n.encode() + b"\0")
        return name_off[n]

    entries = [["dir", 0, 0, 0, root]]
    queue = [0]
    while queue:
        i = queue.pop(0)
        d = entries[i][4]
        kids = sorted(d.items.items(), key=lambda kv: kv[0].lower())
        entries[i][2], entries[i][3] = len(entries), len(kids)
        for cn, cv in kids:
            if isinstance(cv, Dir):
                entries.append(["dir", name(cn), 0, 0, cv])
                queue.append(len(entries) - 1)
            else:
                entries.append(["file", name(cn), cv])
    while len(names) % 16:
        names.append(0)
    header_len = 16 + 16 * len(entries) + len(names)
    pos = (header_len + 511) // 512 * 512
    body = bytearray()
    table = bytearray()
    for e in entries:
        if e[0] == "dir":
            table += struct.pack("<IIII", e[1], 0x7FFFFF00, e[2], e[3])
            continue
        data = e[2]
        off = pos + len(body)
        assert off % 512 == 0
        flags = _rsc_flags(data)
        if flags:
            size = len(data) if len(data) < 0xFFFFFF else 0xFFFFFF
            table += struct.pack("<H", e[1]) + size.to_bytes(3, "little") + \
                ((off // 512) | 0x800000).to_bytes(3, "little") + struct.pack("<II", *flags)
        else:
            table += struct.pack("<H", e[1]) + (0).to_bytes(3, "little") + (off // 512).to_bytes(3, "little") + \
                struct.pack("<II", len(data), 0)
        body += data
        body += b"\0" * ((-len(body)) % 512)
    head = struct.pack("<4sIII", b"7FPR", len(entries), len(names), 0x4E45504F) + table + bytes(names)
    head += b"\0" * (pos - len(head))
    return bytes(head + body)


def put(root, path, data):
    parts = path.split("/")
    d = root
    for p in parts[:-1]:
        d = d.items.setdefault(p, Dir())
    d.items[parts[-1]] = data


# ---------------------------------------------------------------------------------------------- carcols filter

def filter_carcols(xml, available):
    """Drop <visibleMods> items whose modelName has no file; keep everything else."""
    def keep(m):
        model = re.search(r"<modelName>([^<]*)</modelName>", m.group(0))
        return m.group(0) if model is None or model.group(1).lower() in available else ""
    out = re.sub(r"<visibleMods>(.*?)</visibleMods>",
                 lambda vm: "<visibleMods>" + re.sub(r"\s*<Item>.*?</Item>", lambda it: keep(it), vm.group(1),
                                                    flags=re.S) + "</visibleMods>", xml, flags=re.S)
    return out


def main():
    stream, out = sys.argv[1], sys.argv[2]
    files = {f: open(os.path.join(stream, f), "rb").read() for f in sorted(os.listdir(stream))
             if f.endswith((".yft", ".ytd", ".ydr"))}
    available = {f.rsplit(".", 1)[0].lower() for f in files}
    vehicles = Dir()
    for f, data in files.items():
        put(vehicles, f, data)
    lang = Dir()
    put(lang, "global.gxt2", open(os.path.join(DLC, "x64", "data", "lang", "americandlc.rpf", "global.gxt2"), "rb").read())

    root = Dir()
    put(root, "content.xml", open(os.path.join(DLC, "content.xml"), "rb").read())
    put(root, "setup2.xml", open(os.path.join(DLC, "setup2.xml"), "rb").read())
    for f in sorted(os.listdir(os.path.join(DLC, "common", "data"))):
        data = open(os.path.join(DLC, "common", "data", f), "rb").read()
        if f == "carcols.meta":
            text = data.decode("utf-8")
            before = text.count("<modelName>")
            text = filter_carcols(text, available)
            print(f"carcols.meta: kept {text.count('<modelName>')} of {before} visible mods (models present)")
            data = text.encode("utf-8")
        put(root, f"common/data/{f}", data)
    put(root, "x64/vehicles.rpf", build_rpf_bfs(vehicles))
    put(root, "x64/data/lang/americandlc.rpf", build_rpf_bfs(lang))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    blob = build_rpf_bfs(root)
    open(out, "wb").write(blob)
    print(f"wrote {out} ({len(blob) // 1024} KiB): {', '.join(files)}")


if __name__ == "__main__":
    main()
