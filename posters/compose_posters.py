#!/usr/bin/env python3
"""Kanji Emporium poster composer — HeyShape-demo style, pink branding."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

BASE = "/home/user/posters"
FONT_BOLD   = f"{BASE}/assets/fonts/Montserrat-ExtraBold.ttf"
FONT_MED    = f"{BASE}/assets/fonts/Montserrat-Bold.ttf"
FONT_SCRIPT = f"{BASE}/assets/fonts/Parisienne-Regular.ttf"
LOGO = "/home/user/uploads/853368274_1586970383446247_5657712772498553755_n.jpg"

W, H = 1080, 1350

# ---------- colour sampled from the logo ----------
def sample_pink(path):
    im = Image.open(path).convert("RGB").resize((300, 300))
    px = list(im.getdata())
    hits = [(r, g, b) for (r, g, b) in px if r > 200 and (r - g) > 60 and (r - b) > 30 and b > 100]
    if not hits:
        return (233, 30, 140)
    hits.sort()
    rs = sorted(h[0] for h in hits); gs = sorted(h[1] for h in hits); bs = sorted(h[2] for h in hits)
    return (rs[len(rs)//2], gs[len(gs)//2], bs[len(bs)//2])

PINK = sample_pink(LOGO)
DARK_PINK = tuple(max(0, int(c * 0.75)) for c in PINK)
LIGHT_PINK = tuple(min(255, int(c + (255 - c) * 0.45)) for c in PINK)
print("logo pink:", PINK)

def clean_white(im, thr=246):
    """Push near-white pixels to pure white so pasted rectangles vanish on the poster."""
    im = im.convert("RGB")
    data = im.getdata()
    out = [(255, 255, 255) if (r >= thr and g >= thr and b >= thr) else (r, g, b) for (r, g, b) in data]
    im.putdata(out)
    return im

def content_crop(im, thr=244, pad=10):
    px = im.load()
    w, h = im.size
    minx, miny, maxx, maxy = w, h, 0, 0
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r < thr or g < thr or b < thr:
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
    if maxx <= minx:
        return im
    minx = max(0, minx - pad); miny = max(0, miny - pad)
    maxx = min(w, maxx + pad); maxy = min(h, maxy + pad)
    return im.crop((minx, miny, maxx, maxy))

def load_logo():
    im = clean_white(Image.open(LOGO))
    im = content_crop(im, thr=243, pad=6)
    return im

def draw_centered(draw, y, text, font, fill, cx=W // 2):
    draw.text((cx, y), text, font=font, fill=fill, anchor="mm")

def draw_letterspaced(draw, y, text, font, fill, spacing=8, cx=W // 2):
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = cx - total / 2
    for ch, wch in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill, anchor="lm")
        x += wch + spacing

def draw_price(draw, y, bold_font, fill):
    """Reserved price slot: 'PRICE:  K ________'"""
    label = "PRICE:  K"
    w_label = draw.textlength(label, font=bold_font)
    line_len = 235
    gap = 18
    total = w_label + gap + line_len
    x0 = W / 2 - total / 2
    draw.text((x0, y), label, font=bold_font, fill=fill, anchor="lm")
    line_y = y + 18
    draw.line([(x0 + w_label + gap, line_y), (x0 + w_label + gap + line_len, line_y)],
              fill=fill, width=4)
    # small tick at the end of the line
    draw.line([(x0 + w_label + gap + line_len, line_y - 10),
               (x0 + w_label + gap + line_len, line_y)], fill=fill, width=4)

def add_shadow(canvas, cx, cy, w):
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    ew, eh = int(w * 0.62), 38
    d.ellipse([cx - ew // 2, cy - eh // 2, cx + ew // 2, cy + eh // 2], fill=(60, 20, 45, 78))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), sh).convert("RGB"), (0, 0))

def base_poster(logo_img, f_med, f_bold):
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    # logo top centre
    lh = 140
    lw = int(logo_img.width * lh / logo_img.height)
    logo = logo_img.resize((lw, lh), Image.LANCZOS)
    im.paste(logo, (W // 2 - lw // 2, 36))
    # tagline bottom
    draw_letterspaced(d, 1293, "ALL YOU NEED IN ONE PLACE", f_med, LIGHT_PINK, spacing=7)
    # price placeholder
    draw_price(d, 1178, f_bold, DARK_PINK)
    return im

def make_poster(item_path, line1, line2, out_path, garment_h=600):
    f_bold = ImageFont.truetype(FONT_BOLD, 56)
    f_script = ImageFont.truetype(FONT_SCRIPT, 88)
    f_med = ImageFont.truetype(FONT_MED, 27)
    f_price = ImageFont.truetype(FONT_BOLD, 42)

    im = base_poster(load_logo(), f_med, f_price)
    d = ImageDraw.Draw(im)

    # headline
    draw_centered(d, 232, line1, f_bold, DARK_PINK)
    draw_centered(d, 324, line2, f_script, PINK)

    # garment
    g = clean_white(Image.open(item_path))
    g = content_crop(g)
    ratio = garment_h / g.height
    gw = int(g.width * ratio)
    if gw > 640:
        ratio = 640 / g.width
        garment_h = int(g.height * ratio)
        gw = 640
    g = g.resize((gw, garment_h), Image.LANCZOS)
    gx, gy = W // 2 - gw // 2, 1015 - garment_h
    add_shadow(im, W // 2, 1047, gw)
    im.paste(g, (gx, gy))

    im.save(out_path, quality=95)
    print("saved", out_path)

def make_blank(out_path):
    f_med = ImageFont.truetype(FONT_MED, 27)
    f_price = ImageFont.truetype(FONT_BOLD, 42)
    f_bold = ImageFont.truetype(FONT_BOLD, 58)
    im = base_poster(load_logo(), f_med, f_price)
    im.save(out_path, quality=95)
    print("saved", out_path)

ITEMS = [
    ("assets/item1_pink_shirtdress.png",  "What's Your",    "Brunch Vibe?",     "poster_01_pink_shirt_dress.png"),
    ("assets/item2_cream_pearl_dress.png","Pearls of",      "Pure Grace.",      "poster_02_cream_pearl_dress.png"),
    ("assets/item3_grey_pearl_dress.png", "After-Dark",     "Pearl Glam.",      "poster_03_grey_pearl_dress.png"),
    ("assets/item4_print_set.png",        "Bold Prints,",   "Bolder You.",      "poster_04_abstract_print_set.png"),
    ("assets/item5_ivory_drape_dress.png","Ivory",          "Daydreams.",       "poster_05_ivory_drape_dress.png"),
    ("assets/item6_red_drape_dress.png",  "Main Character", "Energy.",          "poster_06_red_drape_dress.png"),
    ("assets/item7_red_pattern_dress.png","Printed to",     "Perfection.",      "poster_07_red_pattern_dress.png"),
]

if __name__ == "__main__":
    for item, l1, l2, out in ITEMS:
        make_poster(os.path.join(BASE, item), l1, l2, os.path.join(BASE, out))
    make_blank(os.path.join(BASE, "poster_00_blank_template.png"))
    print("done")
