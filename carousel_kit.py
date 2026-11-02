# Набір для каруселей @tsebakk (стиль v2, листопад 2026): слайди 1080x1350.
# Фото на весь кадр, текст прямо на фото, рукописний акцент, молочні пігулки, теракотова плашка.
# Використання:  python carousel_kit.py spec.json <папка виходу>
# Шляхи до фото — відносно spec.json. Опис полів — в ІНСТРУКЦІЯ.md, розділ 8.
import sys, os, json, glob
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

W, H = 1080, 1350
MILK = (244, 236, 224)
CHOC = (59, 42, 34)
CARAMEL_L = (224, 180, 138)
TERRA = (160, 72, 46)
HANDLE = "@tsebakk"
FONT_FILES = {"mont": "Montserrat.ttf", "script": "GreatVibes-Regular.ttf"}
_font_paths = {}


# ---------- шрифти ----------

def find_font(key):
    if key in _font_paths:
        return _font_paths[key]
    name = FONT_FILES[key]
    here = os.path.dirname(os.path.abspath(__file__))
    for d in [os.path.join(here, "fonts"), here, os.getcwd()]:
        hits = glob.glob(os.path.join(d, "**", name), recursive=True)
        if hits:
            _font_paths[key] = hits[0]
            return hits[0]
    raise SystemExit(f"Шрифт {name} не знайдено — поклади його в папку fonts/ поруч зі скриптом")


def mont(size, var="Regular"):
    f = ImageFont.truetype(find_font("mont"), size)
    f.set_variation_by_name(var)
    return f


def script(size):
    return ImageFont.truetype(find_font("script"), size)


def typo(t):
    # гарний апостроф для рукописного шрифту
    return t.replace("'", "’")


# ---------- фото ----------

def grade(im):
    # Єдиний теплий тон для всієї серії: трохи тепліше, м'якше, менше насиченості.
    im = ImageOps.exif_transpose(im).convert("RGB")
    r, g, b = im.split()
    r = r.point(lambda v: min(255, int(v * 1.04 + 4)))
    b = b.point(lambda v: int(v * 0.90))
    im = Image.merge("RGB", (r, g, b))
    im = ImageEnhance.Color(im).enhance(0.9)
    return ImageEnhance.Contrast(im).enhance(0.96)


def load(path):
    if path.lower().endswith((".heic", ".heif")):
        import pillow_heif
        pillow_heif.register_heif_opener()
    return grade(Image.open(path))


def background(s, base, darken=0):
    if s.get("photo"):
        c = ImageOps.fit(load(os.path.join(base, s["photo"])), (W, H), Image.LANCZOS,
                         centering=tuple(s.get("focus", (0.5, 0.5)))).convert("RGBA")
        if darken:
            c.alpha_composite(Image.new("RGBA", (W, H), (28, 20, 16, darken)))
        return c
    return Image.new("RGBA", (W, H), CHOC + (255,))


def shade(c, top, bottom, alpha, up=False):
    # м'яке затемнення смуги, щоб текст читався; up=True — темніше вгорі
    top, bottom = max(0, int(top)), min(H, int(bottom))
    if bottom <= top:
        return
    g = Image.new("RGBA", c.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    for y in range(top, bottom):
        t = (y - top) / (bottom - top)
        t = 1 - t if up else t
        d.line([(0, y), (W, y)], fill=(28, 20, 16, int(alpha * min(1, t ** 0.9 * 1.3))))
    c.alpha_composite(g)


# ---------- текст ----------

def wrap(text, f, maxw):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            t = (cur + " " + word).strip()
            if d.textlength(t, font=f) <= maxw or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def soft_text(c, xy, txt, f, fill, anchor="mm"):
    # текст з м'якою тінню для читабельності на фото
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0], xy[1] + 2), txt, font=f, fill=(20, 14, 10, 150), anchor=anchor)
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(c).text(xy, txt, font=f, fill=fill, anchor=anchor)


def centered(c, y, text, f, fill, lh, maxw=900):
    # центровані рядки; y — центр першого рядка; повертає центр «наступного» рядка
    for line in wrap(text, f, maxw):
        soft_text(c, (W / 2, y), line, f, fill)
        y += lh
    return y


def drop_shadow(c, box, radius, alpha=100, blur=12):
    x0, y0, x1, y1 = box
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x0 + 4, y0 + 10, x1 + 4, y1 + 10), radius=radius, fill=(20, 14, 10, alpha))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))


def pill(c, text, side, y, size=28, bg=MILK, fg=CHOC, font_var="Medium"):
    # молочна «пігулка»; side: "l" — від лівого поля, "r" — від правого, "c" — по центру
    f = mont(size, font_var)
    d = ImageDraw.Draw(c)
    padx, h = 24, int(size * 1.8)
    w = d.textlength(text, font=f) + 2 * padx
    x = {"l": 70, "r": W - 70 - w, "c": (W - w) / 2}[side]
    drop_shadow(c, (x, y, x + w, y + h), h // 2, alpha=90, blur=10)
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=bg)
    d.text((x + padx, y + h / 2), text, font=f, fill=fg, anchor="lm")
    return y + h


def block(c, label, text, side="r", y=None, width=380):
    # теракотова плашка: дрібна мітка ВЕЛИКИМИ + 2–3 рядки
    f = mont(26, "Medium")
    lines = wrap(text, f, width - 52)
    h = (54 if label else 22) + len(lines) * 37 + 20
    y = H - 110 - h if y is None else y
    x = {"l": 70, "r": W - 70 - width, "c": (W - width) / 2}[side]
    drop_shadow(c, (x, y, x + width, y + h), 22, alpha=110)
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((x, y, x + width, y + h), radius=22, fill=TERRA)
    ty = y + 20
    if label:
        d.text((x + 26, ty), label.upper(), font=mont(19, "Bold"), fill=CARAMEL_L)
        ty += 34
    for i, line in enumerate(lines):
        d.text((x + 26, ty + i * 37), line, font=f, fill=MILK)


def handle(c):
    soft_text(c, (W / 2, H - 50), HANDLE, mont(22, "Medium"), MILK)


def header(c, s, y=105):
    # «01 / фраза» + заголовок + рукописний рядок; повертає низ текстової зони
    if s.get("number"):
        soft_text(c, (W / 2, y), f"{s['number']}  /  {s.get('label', '')}".strip(" /"), mont(22, "Medium"), CARAMEL_L)
        y += 72
    size = s.get("title_size", 60)
    y = centered(c, y, s["title"], mont(size, "SemiBold"), MILK, int(size * 1.18))
    if s.get("script"):
        ss = s.get("script_size", 70)
        y = centered(c, y + int(ss * 0.18), typo(s["script"]), script(ss), CARAMEL_L, int(ss * 1.05))
    return y


# ---------- типи слайдів ----------

def s_cover(s, base):
    # Обкладинка: фото на весь кадр, затемнення знизу, 1–2 рядки + рукописний акцент + підзаголовок.
    c = background(s, base)
    shade(c, s.get("shade_top", 640), H, 240)
    lines = s["title"]
    y = s.get("title_y", 890)
    for line in lines:
        soft_text(c, (W / 2, y), line, mont(s.get("title_size", 54), "SemiBold"), MILK)
        y += 66
    if s.get("script"):
        soft_text(c, (W / 2, y + 38), typo(s["script"]), script(s.get("script_size", 140)), CARAMEL_L)
        y += 135
    if s.get("subtitle"):
        soft_text(c, (W / 2, y + 30), s["subtitle"], mont(26, "Light"), MILK)
    handle(c)
    return c


def s_point(s, base):
    # Пункт: номер, фраза, рукописний рядок, пігулки навколо людини в кадрі, плашка внизу.
    c = background(s, base)
    shade(c, 0, s.get("shade_top_h", 560), 200, up=True)
    shade(c, s.get("shade_bottom", 1000), H, 170)
    header(c, s)
    ys = {"l": 640, "r": 790}
    for p in s.get("pills", []):
        p = {"text": p} if isinstance(p, str) else p
        side = p.get("side", "l")
        y = p.get("y", ys.get(side, 700))
        pill(c, p["text"], side, y, p.get("size", 28))
        ys[side] = y + 120
    if s.get("block"):
        b = s["block"]
        block(c, b.get("label", ""), b["text"], b.get("side", "r"), b.get("y"), b.get("width", 380))
    handle(c)
    return c


def s_text(s, base):
    # Текстовий слайд: затемнене фото (або шоколадний фон), думка по центру, акцент, кроки на пігулках.
    c = background(s, base, darken=s.get("darken", 150))
    y = s.get("top", 300 if s.get("steps") else 470)
    if s.get("kicker"):
        soft_text(c, (W / 2, y - 80), s["kicker"].upper(), mont(21, "Bold"), CARAMEL_L)
    size = s.get("title_size", 58)
    y = centered(c, y, s["title"], mont(size, "SemiBold"), MILK, int(size * 1.2))
    if s.get("script"):
        ss = s.get("script_size", 74)
        y = centered(c, y + 10, typo(s["script"]), script(ss), CARAMEL_L, int(ss * 1.05))
    if s.get("body"):
        y = centered(c, y + 30, s["body"], mont(28, "Light"), MILK, 42, 820)
    if s.get("steps"):
        y += 40
        for k, st in enumerate(s["steps"], 1):
            for j, line in enumerate(wrap(f"{k}. {st}", mont(26, "Medium"), 820)):
                y = pill(c, line, "c", y, 26) + 16
    handle(c)
    return c


def s_cta(s, base):
    # Заклик: фото, питання для коментарів, рукописний рядок, пояснення, кодове слово на пігулці.
    c = background(s, base)
    shade(c, s.get("shade_top", 560), H, 245)
    y = s.get("title_y", 820)
    size = s.get("title_size", 54)
    y = centered(c, y, s["title"], mont(size, "SemiBold"), MILK, int(size * 1.18))
    if s.get("script"):
        y = centered(c, y + 10, typo(s["script"]), script(66), CARAMEL_L, 70)
    if s.get("body"):
        y = centered(c, y + 20, s["body"], mont(26, "Light"), MILK, 38, 800)
    if s.get("keyword"):
        pill(c, s["keyword"], "c", y + 10, 34, bg=MILK, fg=TERRA, font_var="Black")
    handle(c)
    return c


TYPES = {"cover": s_cover, "point": s_point, "text": s_text, "cta": s_cta}


def build(spec_path, out):
    spec = json.load(open(spec_path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(spec_path))
    os.makedirs(out, exist_ok=True)
    files = []
    for n, s in enumerate(spec["slides"], 1):
        img = TYPES[s["type"]](s, base).convert("RGB")
        p = os.path.join(out, f"{n:02d}.jpg")
        img.save(p, quality=95, subsampling=0)
        files.append(img)
    # контактний аркуш для самоперевірки
    cols = 3
    rows = (len(files) + cols - 1) // cols
    tw, th = W // 3, H // 3
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 12, rows * th + (rows + 1) * 12), (255, 255, 255))
    for i, im in enumerate(files):
        sheet.paste(im.resize((tw, th), Image.LANCZOS), (12 + (i % cols) * (tw + 12), 12 + (i // cols) * (th + 12)))
    sheet.save(os.path.join(out, "_аркуш.jpg"), quality=90)
    print("готово:", len(files), "слайдів у", out)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
