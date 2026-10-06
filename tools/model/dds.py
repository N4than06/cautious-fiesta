"""Minimal uncompressed DDS writer (32-bit BGRA, full mip chain).

GTA V / CodeWalker accept uncompressed A8R8G8B8 textures. Our textures are small and procedural, so no
block compression is needed.
"""
import struct

from PIL import Image

DDSD_CAPS, DDSD_HEIGHT, DDSD_WIDTH, DDSD_PITCH = 0x1, 0x2, 0x4, 0x8
DDSD_PIXELFORMAT, DDSD_MIPMAPCOUNT = 0x1000, 0x20000
DDPF_ALPHAPIXELS, DDPF_RGB = 0x1, 0x40
DDSCAPS_COMPLEX, DDSCAPS_TEXTURE, DDSCAPS_MIPMAP = 0x8, 0x1000, 0x400000


def _mips(img):
    img = img.convert("RGBA")
    out = [img]
    w, h = img.size
    while w > 1 or h > 1:
        w, h = max(1, w // 2), max(1, h // 2)
        out.append(img.resize((w, h), Image.LANCZOS))
    return out


def write_dds(path, img):
    """Write a PIL image as an uncompressed BGRA DDS with mipmaps."""
    w, h = img.size
    assert w & (w - 1) == 0 and h & (h - 1) == 0, "texture sizes must be powers of two"
    levels = _mips(img)
    flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PITCH | DDSD_PIXELFORMAT | DDSD_MIPMAPCOUNT
    pixel_format = struct.pack(
        "<II4sIIIII", 32, DDPF_RGB | DDPF_ALPHAPIXELS, b"\0\0\0\0", 32,
        0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000,
    )
    header = struct.pack("<4sIIIIIII", b"DDS ", 124, flags, h, w, w * 4, 0, len(levels))
    header += b"\0" * 44 + pixel_format
    header += struct.pack("<IIIII", DDSCAPS_COMPLEX | DDSCAPS_TEXTURE | DDSCAPS_MIPMAP, 0, 0, 0, 0)
    assert len(header) == 128
    with open(path, "wb") as f:
        f.write(header)
        for level in levels:
            r, g, b, a = level.split()
            f.write(Image.merge("RGBA", (b, g, r, a)).tobytes())
