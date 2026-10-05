"""Procedural textures for the AT4X (written as DDS for GTA, plus PNG copies for previews)."""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from dds import write_dds


def _noise(size, base, amp, seed, blur=0.0):
    rnd = random.Random(seed)
    img = Image.new("RGBA", size)
    px = img.load()
    for y in range(size[1]):
        for x in range(size[0]):
            d = rnd.uniform(-amp, amp)
            px[x, y] = tuple(max(0, min(255, int(c + d))) for c in base[:3]) + (base[3] if len(base) > 3 else 255,)
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    return img


def _font(size):
    return ImageFont.load_default(size=size)


def _text(img, xy, text, size, fill, anchor="mm", stroke=0, stroke_fill=None):
    d = ImageDraw.Draw(img)
    d.text(xy, text, font=_font(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)


def solid(c, n=8):
    return Image.new("RGBA", (n, n), c)


def honeycomb(n=128):
    img = Image.new("RGBA", (n, n), (8, 8, 9, 255))
    d = ImageDraw.Draw(img)
    r = n / 8
    h = r * math.sqrt(3)
    for row in range(-1, int(n / h) + 2):
        for col in range(-1, int(n / (1.5 * r)) + 2):
            cx = col * 1.5 * r
            cy = row * h + (h / 2 if col % 2 else 0)
            pts = [(cx + r * 0.82 * math.cos(math.radians(60 * k)), cy + r * 0.82 * math.sin(math.radians(60 * k)))
                   for k in range(6)]
            d.polygon(pts, fill=(28, 28, 30, 255), outline=(70, 70, 74, 255))
    return img


def tire(n=128):
    img = _noise((n, n), (34, 34, 36, 255), 10, 7, 0.6)
    d = ImageDraw.Draw(img)
    for k in range(0, n, 16):
        d.line([(0, k), (n, k)], fill=(26, 26, 27, 255), width=2)
    return img


def tire_sidewall(letters=False, n=256):
    """Polar-mapped sidewall strip: u = angle, v = radius (0 = rim, 1 = tread)."""
    img = _noise((n * 2, n // 2), (36, 36, 38, 255), 8, 11, 0.5)
    if letters:
        for k in range(4):
            _text(img, ((k + 0.5) * n / 2, n // 4), "AT4X  MUD-TERRAIN", 22, (236, 236, 230, 255))
    else:
        for k in range(4):
            _text(img, ((k + 0.5) * n / 2, n // 4), "AT4X  MUD-TERRAIN", 22, (52, 52, 54, 255))
    return img


def grain(c, seed, n=64, amp=10):
    return _noise((n, n), c, amp, seed, 0.7)


def bedliner(n=64):
    img = _noise((n, n), (30, 30, 32, 255), 22, 3, 0.4)
    return img


def lens(c, n=32, ribs=True):
    img = Image.new("RGBA", (n, n), c)
    if ribs:
        d = ImageDraw.Draw(img)
        lighter = tuple(min(255, int(v * 1.25)) for v in c[:3]) + (c[3],)
        for k in range(0, n, 4):
            d.line([(k, 0), (k, n)], fill=lighter, width=1)
    return img


def badge_gmc(w=512, h=128):
    """GMC emblem: red letters with a bright chrome outline on a transparent background."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    font = ImageFont.load_default(size=118)
    d = ImageDraw.Draw(img)
    d.text((w / 2, h / 2 + 6), "GMC", font=font, fill=(196, 16, 24, 255), anchor="mm", stroke_width=6,
           stroke_fill=(222, 224, 228, 255))
    # stretch horizontally like the real wide emblem
    bbox = img.getbbox()
    if bbox:
        crop = img.crop(bbox).resize((w - 8, h - 8), Image.LANCZOS)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        img.paste(crop, (4, 4))
    return img


def plate(w=256, h=128):
    img = Image.new("RGBA", (w, h), (236, 238, 240, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, w - 3, h - 3], outline=(40, 60, 120, 255), width=4)
    _text(img, (w / 2, 22), "SAN ANDREAS", 18, (40, 60, 120, 255))
    _text(img, (w / 2, h / 2 + 10), "AT4X 22", 54, (24, 40, 110, 255))
    return img


def badge_at4x(w=256, h=64):
    img = Image.new("RGBA", (w, h), (14, 14, 16, 255))
    _text(img, (w / 2 - 20, h / 2 + 2), "AT4", 50, (215, 215, 220, 255))
    _text(img, (w / 2 + 62, h / 2 + 2), "X", 54, (200, 20, 26, 255))
    return img


def badge_sierra(w=512, h=64):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    _text(img, (w / 2, h / 2), "S I E R R A", 48, (20, 20, 22, 255))
    return img


def dash(n=256):
    img = Image.new("RGBA", (n, n // 2), (6, 6, 8, 255))
    d = ImageDraw.Draw(img)
    for cx in (n * 0.22, n * 0.78):
        d.ellipse([cx - 44, 20, cx + 44, 108], outline=(220, 220, 230, 255), width=3)
        for k in range(9):
            a = math.radians(135 + k * 33.75)
            d.line([(cx + 34 * math.cos(a), 64 + 34 * math.sin(a)), (cx + 42 * math.cos(a), 64 + 42 * math.sin(a))],
                   fill=(230, 60, 50, 255) if k > 6 else (220, 220, 230, 255), width=2)
    d.rectangle([n * 0.38, 26, n * 0.62, 102], fill=(20, 40, 60, 255), outline=(90, 140, 190, 255), width=2)
    _text(img, (n / 2, 64), "AT4X", 18, (220, 230, 240, 255))
    return img


def screen(n=128):
    img = Image.new("RGBA", (n, n), (12, 22, 34, 255))
    d = ImageDraw.Draw(img)
    for k in range(4):
        d.rectangle([8 + k * 30, 90, 30 + k * 30, 116], fill=(40, 70, 100, 255))
    d.rectangle([8, 8, n - 8, 80], fill=(30, 60, 50, 255))
    _text(img, (n / 2, 44), "4WD HI", 20, (230, 230, 230, 255))
    return img


def engine_cover(n=128):
    img = grain((22, 22, 24, 255), 21, n, 8)
    _text(img, (n / 2, n / 2), "6.2 V8", 30, (150, 150, 155, 255))
    return img


def whipple_lid(n=128):
    img = grain((18, 18, 20, 255), 31, n, 6)
    _text(img, (n / 2, n / 2 - 14), "WHIPPLE", 26, (210, 210, 215, 255))
    _text(img, (n / 2, n / 2 + 18), "3.0L", 22, (200, 30, 30, 255))
    return img


def all_textures():
    return {
        "at4x_white": solid((255, 255, 255, 255)),
        "at4x_nrm": solid((128, 128, 255, 255)),
        "at4x_spec": solid((200, 200, 200, 255)),
        "at4x_spec_low": solid((50, 50, 50, 255)),
        "at4x_dirt": _noise((64, 64), (120, 100, 70, 255), 40, 1, 1.2),
        "at4x_damage": _noise((64, 64), (128, 128, 128, 255), 30, 2, 0.8),
        "at4x_black": grain((22, 22, 24, 255), 4),
        "at4x_plastic": grain((34, 34, 36, 255), 5, amp=14),
        "at4x_steel": grain((60, 62, 64, 255), 6, amp=8),
        "at4x_chrome": solid((215, 218, 222, 255)),
        "at4x_alu": grain((150, 152, 156, 255), 8, amp=10),
        "at4x_red": solid((170, 14, 20, 255)),
        "at4x_gold": solid((190, 150, 40, 255)),
        "at4x_grille": honeycomb(),
        "at4x_tire": tire(),
        "at4x_sidewall": tire_sidewall(False),
        "at4x_sidewall_rwl": tire_sidewall(True),
        "at4x_rim": solid((235, 235, 235, 255)),
        "at4x_glass": solid((34, 40, 44, 96)),
        "at4x_lens_clear": lens((215, 220, 230, 160)),
        "at4x_lens_red": lens((170, 10, 14, 200)),
        "at4x_lens_amber": lens((230, 120, 10, 200)),
        "at4x_led": solid((255, 255, 250, 255)),
        "at4x_reflector": lens((40, 42, 46, 255), ribs=True),
        "at4x_leather": grain((24, 24, 26, 255), 9, amp=6),
        "at4x_leather_red": grain((110, 18, 22, 255), 10, amp=6),
        "at4x_carpet": grain((26, 26, 28, 255), 12, amp=12),
        "at4x_bedliner": bedliner(),
        "at4x_badge_gmc": badge_gmc(),
        "at4x_plate": plate(),
        "at4x_titanium": grain((68, 78, 92, 255), 13, amp=6),
        "at4x_badge_at4x": badge_at4x(),
        "at4x_badge_sierra": badge_sierra(),
        "at4x_dash": dash(),
        "at4x_screen": screen(),
        "at4x_engine_cover": engine_cover(),
        "at4x_whipple": whipple_lid(),
        "at4x_mesh": honeycomb(64),
    }


def write_all(out_dir, preview_dir=None):
    os.makedirs(out_dir, exist_ok=True)
    texs = all_textures()
    for name, img in texs.items():
        write_dds(os.path.join(out_dir, name + ".dds"), img)
        if preview_dir:
            os.makedirs(preview_dir, exist_ok=True)
            img.save(os.path.join(preview_dir, name + ".png"))
    return sorted(texs)
