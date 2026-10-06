"""Minimal reader for unencrypted (OPEN) GTA V RPF7 archives. Extracts files; nested .rpf are recursed."""
import os, struct, sys, zlib

def extract(data, out, depth=0):
    magic, count, names_len, enc = struct.unpack_from("<4sIII", data, 0)
    assert magic == b"7FPR", magic
    assert enc in (0, 0x4E45504F), hex(enc)
    ents = data[16:16 + count * 16]
    names = data[16 + count * 16:16 + count * 16 + names_len]
    def name(off):
        e = names.index(b"\0", off); return names[off:e].decode()
    def walk(idx, path):
        raw = ents[idx * 16:(idx + 1) * 16]
        h = struct.unpack_from("<I", raw, 4)[0]
        if h == 0x7FFFFF00:
            noff, _, first, n = struct.unpack("<IIII", raw)
            p = os.path.join(path, name(noff)) if idx else path
            os.makedirs(p, exist_ok=True)
            for i in range(first, first + n):
                walk(i, p)
            return
        noff = struct.unpack_from("<H", raw, 0)[0]
        size = int.from_bytes(raw[2:5], "little")
        off3 = int.from_bytes(raw[5:8], "little")
        nm = name(noff)
        if off3 & 0x800000:   # resource
            off = (off3 & 0x7FFFFF) * 512
            sysf, gfxf = struct.unpack_from("<II", raw, 8)
            if size == 0xFFFFFF:
                hd = data[off:off + 16]
                size = hd[7] | (hd[14] << 8) | (hd[5] << 16) | (hd[2] << 24)
            blob = data[off:off + size]
        else:
            off = off3 * 512
            usize, fenc = struct.unpack_from("<II", raw, 8)
            blob = data[off:off + (size or usize)]
            if size and size != usize:
                blob = zlib.decompress(blob, -15)
        fp = os.path.join(path, nm)
        with open(fp, "wb") as f:
            f.write(blob)
        print("  " * depth + fp, len(blob))
        if nm.endswith(".rpf"):
            extract(blob, fp + "_x", depth + 1)
    walk(0, out)

if __name__ == "__main__":
    extract(open(sys.argv[1], "rb").read(), sys.argv[2])
