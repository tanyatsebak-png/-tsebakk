# Набір для каруселей @tsebakk: слайди 1080x1350 у фірмовому стилі.
# Використання:  python carousel_kit.py spec.json <папка виходу>
# spec.json описує слайди (див. приклад_spec.json). Шляхи до фото — відносно spec.json.
import sys, os, json, glob, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance, ImageColor

W, H = 1080, 1350
MILK, CHOC, CARAMEL, CARAMEL_L = "#EFE6DA", "#3B2A22", "#A0673E", "#E0B48A"
PAPER = "#F7F1E8"
HANDLE = "@tsebakk"

FONT_FILES = {
    "play": "PlayfairDisplay-Italic.ttf",
    "mont": "Montserrat.ttf",
}
FONT_URLS = {
    "play": "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay-Italic%5Bwght%5D.ttf",
    "mont": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf",
}
_font_paths = {}


def find_font(key):
    # 1) поруч зі скриптом / у поточній папці / серед завантажених файлів; 2) Google Fonts; 3) запасний.
    if key in _font_paths:
        return _font_paths[key]
    name = FONT_FILES[key]
    here = os.path.dirname(os.path.abspath(__file__))
    for d in [here, os.getcwd(), os.path.join(here, "fonts"), "/mnt/user-data/uploads", "/mnt/data"]:
        hits = glob.glob(os.path.join(d, "**", name), recursive=True)
        if hits:
            _font_paths[key] = hits[0]
            return hits[0]
    try:
        path = os.path.join(here, name)
        urllib.request.urlretrieve(FONT_URLS[key], path)
        _font_paths[key] = path
        return path
    except Exception:
        print(f"УВАГА: шрифт {name} не знайдено — використано запасний, стиль буде неточним")
        _font_paths[key] = None
        return None


def font(key, size, var):
    path = find_font(key)
    if path is None:
        fallback = "DejaVuSerif-Italic.ttf" if key == "play" else "DejaVuSans.ttf"
        try:
            return ImageFont.truetype(fallback, size)
        except OSError:
            return ImageFont.load_default(size)
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_name(var)
    except Exception:
        pass
    return f


def play(size, var="Italic"):
    return font("play", size, var)


def mont(size, var="Regular"):
    return font("mont", size, var)


def grade(im):
    # Єдиний теплий тон для всієї серії: трохи тепліше, м'якше, менше насиченості.
    im = ImageOps.exif_transpose(im).convert("RGB")
    r, g, b = im.split()
    r = r.point(lambda v: min(255, int(v * 1.04 + 4)))
    b = b.point(lambda v: int(v * 0.90))
    im = Image.merge("RGB", (r, g, b))
    im = ImageEnhance.Color(im).enhance(0.88)
    return ImageEnhance.Contrast(im).enhance(0.95)


def load(path):
    if path.lower().endswith((".heic", ".heif")):
        import pillow_heif
        pillow_heif.register_heif_opener()
    return grade(Image.open(path))


def fit(im, w, h, focus=(0.5, 0.5)):
    return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=tuple(focus))


def wrap(draw, text, f, maxw):
    lines, cur = [], ""
    for word in text.split(" "):
        t = (cur + " " + word).strip()
        if draw.textlength(t, font=f) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def text_block(draw, xy, text, f, fill, maxw, lh):
    x, y = xy
    for para in text.split("\n"):
        for line in wrap(draw, para, f, maxw):
            draw.text((x, y), line, font=f, fill=fill)
            y += lh
    return y


def colors(dark):
    return (CHOC, MILK, CARAMEL_L) if dark else (MILK, CHOC, CARAMEL)


def footer(draw, n, total, dark):
    c = CARAMEL_L if dark else CARAMEL
    f = mont(22, "Medium")
    draw.text((80, H - 78), f"{n}/{total}", font=f, fill=c)
    draw.text((W - 80 - draw.textlength(HANDLE, font=f), H - 78), HANDLE, font=f, fill=c)


def print_photo(canvas, im, box, angle, focus=(0.5, 0.5)):
    # Фото як відбиток в альбомі: молочне паспарту, легкий нахил, м'яка тінь.
    x, y, w, h = box
    pad = 16
    card = Image.new("RGB", (w + 2 * pad, h + 2 * pad), PAPER)
    card.paste(fit(im, w, h, focus), (pad, pad))
    card = card.convert("RGBA").rotate(angle, resample=Image.BICUBIC, expand=True)
    ox = x - (card.width - w - 2 * pad) // 2
    oy = y - (card.height - h - 2 * pad) // 2
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (28, 23, 20, 0))
    sh.putalpha(card.split()[3].point(lambda v: 90 if v else 0))
    shadow.paste(sh, (ox + 8, oy + 14), sh)
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))
    canvas.alpha_composite(card, (ox, oy))


def gradient(canvas, top, color, max_alpha=235):
    g = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    rgb = ImageColor.getrgb(color)
    for yy in range(top, H):
        a = int(max_alpha * min(1, ((yy - top) / (H - top)) ** 0.8 * 1.25))
        d.line([(0, yy), (W, yy)], fill=rgb + (a,))
    canvas.alpha_composite(g)


ANGLES = [-1.6, 1.3, -1.1, 1.5, -1.3, 1.2]


# ---------- типи слайдів ----------

def s_cover(s, n, total, base):
    # Обкладинка: фото на весь слайд, шоколадний градієнт знизу, заголовок курсивом.
    c = fit(load(os.path.join(base, s["photo"])), W, H, s.get("focus", (0.5, 0.35))).convert("RGBA")
    gradient(c, s.get("gradient_top", 640), CHOC)
    d = ImageDraw.Draw(c)
    lines = s["title"]  # список рядків; останній — карамельний акцент
    y = H - 140 - 100 * (len(lines) - 1) - 110
    for i, line in enumerate(lines):
        last = i == len(lines) - 1
        f = play(96, "SemiBold Italic") if last else play(84)
        d.text((80, y), line, font=f, fill=CARAMEL_L if last else MILK)
        y += 100
    f = mont(24, "SemiBold")
    t = "ГОРТАЙ  →"
    d.text((W - 80 - d.textlength(t, font=f), H - 82), t, font=f, fill=MILK)
    d.text((80, H - 82), HANDLE, font=mont(22, "Medium"), fill=CARAMEL_L)
    return c


def s_text(s, n, total, base):
    # Текстовий слайд: надзаголовок, велика думка, акцент, пояснення і/або кроки вправи.
    dark = s.get("dark", True)
    bg, fg, acc = colors(dark)
    c = Image.new("RGBA", (W, H), bg)
    d = ImageDraw.Draw(c)
    y = s.get("top", 220 if s.get("steps") else 380)
    if s.get("kicker"):
        d.text((80, y - 70), s["kicker"].upper(), font=mont(28, "Bold"), fill=acc)
    y = text_block(d, (80, y), s["title"], play(s.get("title_size", 88)), fg, 920, int(s.get("title_size", 88) * 1.2))
    if s.get("accent"):
        y = text_block(d, (80, y + 20), s["accent"], play(64, "SemiBold Italic"), acc, 920, 80)
    if s.get("body"):
        y += 60
        d.line([(80, y), (200, y)], fill=CARAMEL, width=3)
        y = text_block(d, (80, y + 50), s["body"], mont(34), fg, 900, 52)
    if s.get("steps"):
        y += 70
        top = y
        yy = y + 50
        d.text((130, yy), s.get("steps_title", "Спробуй просто зараз"), font=play(46, "SemiBold Italic"), fill=fg)
        yy += 90
        for k, st in enumerate(s["steps"], 1):
            d.text((130, yy - 4), str(k), font=play(46, "Bold Italic"), fill=acc)
            yy = text_block(d, (190, yy), st, mont(32), fg, 760, 46) + 26
        d.rounded_rectangle((80, top, W - 80, yy + 24), radius=28, outline=CARAMEL, width=2)
    footer(d, n, total, dark)
    return c


def s_photo(s, n, total, base):
    # Слайд-пункт: номер, фраза/теза курсивом, фото-відбиток, 1–2 рядки з підписами.
    dark = s.get("dark", n % 2 == 0)
    bg, fg, acc = colors(dark)
    c = Image.new("RGBA", (W, H), bg)
    d = ImageDraw.Draw(c)
    if s.get("number"):
        d.text((80, 84), s["number"], font=play(54, "SemiBold Italic"), fill=acc)
    title = s["title"]
    long_ = len(title) >= 30
    y = text_block(d, (80, 160), title, play(58 if long_ else 70), fg, 920, 70 if long_ else 84)
    rows = s.get("rows", [])
    y += 36
    ph = H - 270 - 66 * max(1, len(rows)) - y
    print_photo(c, load(os.path.join(base, s["photo"])), (110, y, 860, ph),
                s.get("angle", ANGLES[n % len(ANGLES)]), s.get("focus", (0.5, 0.6)))
    d = ImageDraw.Draw(c)
    y = y + ph + 70
    lab, txt = mont(24, "Bold"), mont(32)
    for label, text in rows:
        lw = d.textlength(label.upper() + "  ", font=lab) if label else 0
        if label:
            d.text((80, y), label.upper(), font=lab, fill=acc)
        y = text_block(d, (80 + lw, y - 6), text, txt, fg, 920 - lw, 46) + 20
    footer(d, n, total, dark)
    return c


def s_cta(s, n, total, base):
    # Заклик: фото-відбиток зверху, питання для коментарів, кодове слово в «пігулці».
    dark = s.get("dark", False)
    bg, fg, acc = colors(dark)
    c = Image.new("RGBA", (W, H), bg)
    print_photo(c, load(os.path.join(base, s["photo"])), (110, 110, 860, 560), 1.2, s.get("focus", (0.5, 0.6)))
    d = ImageDraw.Draw(c)
    y = text_block(d, (80, 760), s["title"], play(78), fg, 920, 94)
    if s.get("subtitle"):
        y = text_block(d, (80, y + 4), s["subtitle"], mont(34, "SemiBold"), acc, 920, 50)
    if s.get("body"):
        y = text_block(d, (80, y + 40), s["body"], mont(32), fg, 900, 48)
    word = s.get("keyword", "ГОЛОС")
    f = mont(40, "Black")
    tw = d.textlength(word, font=f)
    y += 20
    d.rounded_rectangle((80, y, 80 + tw + 60, y + 76), radius=38, fill=fg)
    d.text((110, y + 14), word, font=f, fill=CARAMEL_L if not dark else CHOC)
    footer(d, n, total, dark)
    return c


TYPES = {"cover": s_cover, "text": s_text, "photo": s_photo, "cta": s_cta}


def build(spec_path, out):
    spec = json.load(open(spec_path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(spec_path))
    slides = spec["slides"]
    os.makedirs(out, exist_ok=True)
    for n, s in enumerate(slides, 1):
        img = TYPES[s["type"]](s, n, len(slides), base)
        img.convert("RGB").save(os.path.join(out, f"{n:02d}.jpg"), quality=95, subsampling=0)
    print("готово:", len(slides), "слайдів у", out)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
