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


def tire(n=256):
    """Tread rubber. u runs across the tread (0.064 m per tile), v around it (0.048 m per tile): three wavy sipes
    per tile (the DuraTrac RT siping); the band around v = 0 stays plain (groove floors, walls, lugs)."""
    img = _noise((n, n), (33, 33, 35, 255), 7, 7, 0.8)
    d = ImageDraw.Draw(img)
    for v in (0.30, 0.55, 0.80):
        y0 = (1.0 - v) * n
        pts = []
        for x in range(-4, n + 5, 2):
            # zig-zag sipe: ~6 mm pitch, 1.4 mm amplitude, slightly rounded
            ph = (x / (n / 10.0)) % 1.0
            tri = 4.0 * abs(ph - 0.5) - 1.0
            pts.append((x, y0 + 0.022 * n * tri))
        d.line(pts, fill=(14, 14, 15, 255), width=max(2, n // 96))
        d.line([(x, y + max(2, n // 96)) for x, y in pts], fill=(44, 44, 46, 255), width=1)
    return img.filter(ImageFilter.GaussianBlur(0.5))


def tire_sidewall(letters=False, n=2048):
    """Polar-mapped outer sidewall, half the circumference (the mesh repeats it twice): u = angle, v = radius
    (0 = rim flange, 1 = shoulder). Goodyear moulding: GOODYEAR (wingfoot) and WRANGLER in big raised letters,
    DURATRAC smaller, size / load / DOT print, the rim-protector rib and a fine moulding ring."""
    def _tire_font(size):
        for name in ("DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf",
                     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                     "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"):
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                continue
        return ImageFont.load_default(size=size)


    def _tire_word(text, height, squash, fill, edge, shade, slant=0.0, outline=0):
        """Raised moulded lettering: face colour, a lit upper edge and a shadowed lower edge (u squashed because the
        texture covers half the circumference)."""
        font = _tire_font(height * 2)
        tmp = Image.new("L", (int(height * 2 * len(text) * 1.1) + 40, height * 3), 0)
        ImageDraw.Draw(tmp).text((20, height // 2), text, font=font, fill=255, stroke_width=max(1, height // 18),
                                 stroke_fill=255)
        bbox = tmp.getbbox()
        tmp = tmp.crop(bbox)
        w = max(1, int(tmp.width * height / tmp.height * squash))
        if slant:
            tmp = tmp.transform(tmp.size, Image.AFFINE, (1, slant, -slant * tmp.height, 0, 1, 0), Image.BILINEAR)
        mask = tmp.resize((w, height), Image.LANCZOS)
        out = Image.new("RGBA", (w + 4, height + 4), (0, 0, 0, 0))
        out.paste(shade, (1, 2, 1 + w, 2 + height), mask)
        out.paste(edge, (0, 0, w, height), mask)
        out.paste(fill, (0, 1, w, 1 + height), mask)
        if outline:
            inner = mask.filter(ImageFilter.MinFilter(outline * 2 + 1))
            hollow = tuple(int(a * 0.45 + b * 0.55) for a, b in zip(shade[:3], fill[:3])) + (255,)
            out.paste(hollow, (0, 1, w, 1 + height), inner)
        return out


    def _wingfoot(height, fill, edge):
        """Small stylised Goodyear wingfoot between GOOD and YEAR."""
        w = int(height * 1.1)
        img = Image.new("RGBA", (w, height), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        h = height
        foot = [(0.10 * w, 0.95 * h), (0.55 * w, 0.95 * h), (0.62 * w, 0.80 * h), (0.40 * w, 0.72 * h),
                (0.36 * w, 0.40 * h), (0.22 * w, 0.40 * h), (0.24 * w, 0.75 * h)]
        wing = [(0.36 * w, 0.42 * h), (0.95 * w, 0.05 * h), (0.80 * w, 0.30 * h), (0.98 * w, 0.22 * h),
                (0.78 * w, 0.48 * h), (0.95 * w, 0.42 * h), (0.60 * w, 0.66 * h), (0.40 * w, 0.66 * h)]
        d.polygon(foot, fill=fill, outline=edge)
        d.polygon(wing, fill=fill, outline=edge)
        return img


    h = n // 8
    img = _noise((n, h), (30, 30, 32, 255), 5, 11, 0.6)
    d = ImageDraw.Draw(img)

    def row(v):
        return int(round((1.0 - v) * (h - 1)))
    # rim protector rib (lit top edge, shadowed lower edge) and moulding rings
    d.rectangle([0, row(0.17), n, row(0.10)], fill=(36, 36, 38, 255))
    d.line([(0, row(0.17)), (n, row(0.17))], fill=(50, 50, 53, 255), width=2)
    d.line([(0, row(0.10)), (n, row(0.10))], fill=(18, 18, 19, 255), width=2)
    d.line([(0, row(0.205)), (n, row(0.205))], fill=(24, 24, 25, 255), width=1)
    d.line([(0, row(0.70)), (n, row(0.70))], fill=(24, 24, 25, 255), width=1)
    if letters:
        fill, edge, shade = (226, 226, 220, 255), (250, 250, 246, 255), (120, 120, 118, 255)
    else:
        fill, edge, shade = (44, 44, 47, 255), (66, 66, 70, 255), (14, 14, 15, 255)
    big = int(h * 0.235)           # ~35 mm letters
    small = int(h * 0.105)         # ~16 mm
    tiny = max(8, int(h * 0.045))  # ~7 mm print

    def put(word, x, v, size, squash=1.0, outline=0):
        im = _tire_word(word, size, squash, fill, edge, shade, outline=outline)
        img.alpha_composite(im, (int(x - im.width / 2), row(v) - im.height // 2))
        return im.width
    # GOODYEAR with the wingfoot
    x0 = int(n * 0.20)
    wg = _wingfoot(big, fill, edge)
    gw = _tire_word("GOOD", big, 1.05, fill, edge, shade, outline=max(1, big // 14))
    yw = _tire_word("YEAR", big, 1.05, fill, edge, shade, outline=max(1, big // 14))
    total = gw.width + wg.width + yw.width + 8
    x = x0 - total // 2
    vy = row(0.50) - big // 2
    img.alpha_composite(gw, (x, vy))
    img.alpha_composite(wg, (x + gw.width + 4, vy + 2))
    img.alpha_composite(yw, (x + gw.width + wg.width + 8, vy))
    put("DURATRAC", int(n * 0.47), 0.36, small, 1.15)
    put("WRANGLER", int(n * 0.73), 0.50, big, 1.05, outline=max(1, big // 14))
    # small print
    put("LT275/70R18  121/118Q  LOAD RANGE E", int(n * 0.92), 0.30, tiny)
    put("M+S", int(n * 0.39), 0.64, tiny)
    put("TPC SPEC 2852MS", int(n * 0.06), 0.64, tiny)
    put("DOT 3D MJ XRT 4221", int(n * 0.60), 0.24, tiny)
    put("TUBELESS  RADIAL", int(n * 0.90), 0.62, tiny)
    # 3PMSF mountain/snowflake mark
    mx, my = int(n * 0.43), row(0.64)
    s = tiny
    d.polygon([(mx - s, my + s // 2), (mx - s // 3, my - s // 2), (mx, my), (mx + s // 3, my - s // 3),
               (mx + s, my + s // 2)], outline=edge, fill=fill)
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


def _lettering(text, w, h, fill, stroke, accent=None, size=None):
    img = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=size or int(h * 1.5))
    d.text((w, h), text, font=font, fill=fill, anchor="mm", stroke_width=3, stroke_fill=stroke)
    bbox = img.getbbox()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if bbox:
        crop = img.crop(bbox).resize((w - 4, h - 4), Image.LANCZOS)
        out.paste(crop, (2, 2))
    return out


def badge_at4x(w=256, h=64):
    """AT4X: chrome letters, red-accented 4."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    left = _lettering("AT", w // 2, h, (205, 207, 212, 255), (90, 92, 96, 255))
    four = _lettering("4", w // 4, h, (200, 22, 30, 255), (120, 10, 14, 255))
    x = _lettering("X", w // 4, h, (205, 207, 212, 255), (90, 92, 96, 255))
    img.paste(left, (0, 0))
    img.paste(four, (w // 2, 0))
    img.paste(x, (3 * w // 4, 0))
    return img


def badge_sierra(w=512, h=64):
    return _lettering("SIERRA", w, h, (200, 202, 208, 255), (80, 82, 86, 255))


def badge_v8(w=256, h=64):
    img = Image.new("RGBA", (w, h), (18, 18, 20, 255))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([1, 1, w - 2, h - 2], radius=14, outline=(190, 192, 196, 255), width=4)
    t = _lettering("6.2L", w // 2 - 16, h - 20, (205, 30, 36, 255), (110, 10, 14, 255))
    v = _lettering("V8", w // 2 - 40, h - 20, (205, 207, 212, 255), (90, 92, 96, 255))
    img.paste(t, (12, 10), t)
    img.paste(v, (w // 2 + 20, 10), v)
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
        "at4x_lens_glass": solid((235, 238, 242, 28)),
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
        "at4x_titanium": grain((150, 132, 112, 255), 13, amp=6),
        "at4x_badge_at4x": badge_at4x(),
        "at4x_badge_sierra": badge_sierra(),
        "at4x_badge_v8": badge_v8(),
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
