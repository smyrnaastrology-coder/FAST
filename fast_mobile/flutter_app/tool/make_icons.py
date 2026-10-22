"""
Holavon ikon seti üretici.

Kaynak görsel : tool/brand/holavon_master.png  (varsayılan)
Başka kaynak  : python tool/make_icons.py <yol.png>

Kaynak görsel DÜZENLENMEZ; beyaz/düz arka planı yumuşak alfa ile
şeffaflaştırılır, işaret kendi karesine kırpılır ve tüm ikon setleri
yeniden boyutlanarak üretilir.

Üretilenler:
  assets/holavon_logo.png             512  (şeffaf işaret — koyu zeminde)
  assets/holavon_logo_light.png       512  (beyaz zemin üstünde işaret)
  android/.../mipmap-*/ic_launcher.png             (48/72/96/144/192)
  android/.../mipmap-*/ic_launcher_foreground.png  (adaptive 108/162/216/324/432)
  android/.../mipmap-anydpi-v26/ic_launcher*.xml   (adaptive ikon)
  android/.../drawable/ic_launcher_background.xml  (mor degrade zemin)
  ios/Runner/Assets.xcassets/AppIcon.appiconset/*  (tüm iOS boyutları)
  web/favicon.png, web/icons/Icon-*.png
  marketing/play_app_icon.png         512  (Play Store — mor zemin)
  marketing/play_app_icon_white.png   512  (Play Store — beyaz zemin)
"""

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SRC = os.path.join(ROOT, "tool", "brand", "holavon_master.png")
SRC = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC

# ── Marka renkleri ──────────────────────────────────────────────────────────
VIOLET_DEEP = (24, 16, 38)      # #181026  (Holavon koyu mor)
VIOLET_MID = (31, 21, 48)       # #1F1530
VIOLET_LIGHT = (70, 50, 98)     # #463262
WHITE = (255, 255, 255)


# ── Kaynak işleme ───────────────────────────────────────────────────────────
def load_source():
    im = Image.open(SRC)
    print(f"kaynak: {os.path.relpath(SRC, ROOT)} {im.size} mod={im.mode}")
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        return im.convert("RGBA")
    return im.convert("RGB")


def knock_out_flat_bg(im):
    """Düz (beyaz) arka planı yumuşak alfa ile şeffaflaştırır.

    Renk kenar yumuşatması (unpremultiply) yapılır; aksi halde beyaz
    halos kalır ve koyu zeminde kirli görünür.
    """
    if im.mode == "RGBA":
        arr = np.asarray(im).astype(float)
        if (arr[:, :, 3] < 250).any():
            print("  kaynakta zaten alfa var — arka plan temizlenmedi")
            return im

    a = np.asarray(im.convert("RGB")).astype(float)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    chroma = a.max(axis=2) - a.min(axis=2)
    lum = a.mean(axis=2)

    # Düz, doymamış, açık arka plan
    bg = (chroma < 28) & (lum > 185)

    # Sadece kenar ile bağlantılı arka plan bölgesini kaldır (işaret içindeki
    # beyaz detaylar korunur).
    lab, n = ndimage.label(bg)
    if n:
        border = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
        border.discard(0)
        bg = bg & np.isin(lab, list(border)) if border else bg

    alpha = (~bg).astype(float)
    alpha = ndimage.gaussian_filter(alpha, sigma=0.85)
    alpha = np.clip(alpha, 0.0, 1.0)

    out = a.copy()
    m = (alpha > 0.02) & (alpha < 0.985)
    if m.any():
        for c in range(3):
            out[:, :, c][m] = np.clip(
                (a[:, :, c][m] - (1.0 - alpha[m]) * 255.0) / alpha[m], 0, 255
            )
    rgba = np.dstack([out, alpha * 255.0]).astype("uint8")
    print(f"  arka plan temizlendi: {bg.mean() * 100:.1f}% saydam")
    return Image.fromarray(rgba, "RGBA")


def mark_box(im):
    """İşaretin (alfa > 10) kutu içindeki sınırları."""
    a = np.asarray(im)[:, :, 3]
    ys, xs = np.where(a > 10)
    if not len(xs):
        raise SystemExit("HATA: işaret bulunamadı (tamamen saydam kaynak)")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def fit_mark(im, size, pad_ratio=0.0):
    """İşareti kareye kırpar; [pad_ratio] oranında boşluk bırakır."""
    l, t, r, b = mark_box(im)
    side = max(r - l, b - t)
    cx, cy = (l + r) // 2, (t + b) // 2
    half = side / 2.0
    half += side * pad_ratio
    box = (int(cx - half), int(cy - half), int(cx + half), int(cy + half))
    return im.crop(box).resize((size, size), Image.LANCZOS)


def fit_diag(im, canvas, diag):
    """İşareti, kutu DİYAGONALİ [diag] olacak şekilde ölçekleyip ortalar.

    Android adaptive ikonunda görünen alan bir daire olabilir; daireye
    sığan en büyük dikdörtgen kare olduğundan, uzunca bir işaret (bizim
    "h" harfi) köşelerden kırpılmasın diye diyagonal baz alınır.
    """
    l, t, r, b = mark_box(im)
    cropped = im.crop((l, t, r, b))
    w, h = cropped.size
    cur = math.hypot(w, h)
    target_w = max(1, int(round(w * diag / cur)))
    target_h = max(1, int(round(h * diag / cur)))
    m = cropped.resize((target_w, target_h), Image.LANCZOS)
    out = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    out.alpha_composite(m, ((canvas - target_w) // 2, (canvas - target_h) // 2))
    return out


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("  ->", os.path.relpath(path, ROOT), f"({img.size[0]}px)")


def gradient_bg(size, c1=VIOLET_DEEP, c2=VIOLET_MID):
    """Dikey degrade zemin (iyOS/Android tam kaplama ikonları için)."""
    grad = np.linspace(0, 1, size)[:, None]
    arr = np.zeros((size, size, 3), dtype=float)
    for c in range(3):
        arr[:, :, c] = c1[c] + (c2[c] - c1[c]) * grad
    return Image.fromarray(arr.astype("uint8"), "RGB")


def on_bg(mark, size, bg=None, pad_ratio=0.10, radius=0):
    """İşareti zemin üzerine yerleştirir."""
    if bg is None:
        bg = gradient_bg(size)
    canvas = bg.convert("RGBA").resize((size, size), Image.LANCZOS)
    if radius:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
        canvas.putalpha(mask)
    m = fit_mark(mark, int(size * (1 - pad_ratio * 2)))
    canvas.alpha_composite(m, ((size - m.size[0]) // 2, (size - m.size[1]) // 2))
    return canvas


# ── Üreticiler ──────────────────────────────────────────────────────────────
def make_assets(mark):
    out = os.path.join(ROOT, "assets")
    # Uygulama içi: şeffaf işaret (koyu uygulama zeminine oturur)
    save(fit_mark(mark, 512, pad_ratio=0.06), os.path.join(out, "holavon_logo.png"))
    # Açık zemin: beyaz zemin üstünde işaret
    save(on_bg(mark, 512, bg=Image.new("RGB", (512, 512), WHITE), pad_ratio=0.08),
         os.path.join(out, "holavon_logo_light.png"))


ANDROID_DPI = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}


def make_android(mark):
    res = os.path.join(ROOT, "android", "app", "src", "main", "res")
    for dpi, k in ANDROID_DPI.items():
        d = os.path.join(res, f"mipmap-{dpi}")
        # Eski (legacy) ikon: tam kaplama kare — launcher kendi maskesini uygular
        save(on_bg(mark, int(48 * k), pad_ratio=0.14), os.path.join(d, "ic_launcher.png"))
        # Adaptive foreground: 108dp tuval, isaret diyagonal 72dp (daire maske guvenligi)
        save(fit_diag(mark, int(108 * k), int(72 * k)),
             os.path.join(d, "ic_launcher_foreground.png"))

    anydpi = os.path.join(res, "mipmap-anydpi-v26")
    os.makedirs(anydpi, exist_ok=True)
    for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
        with open(os.path.join(anydpi, name), "w", encoding="utf-8") as f:
            f.write(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                '    <background android:drawable="@drawable/ic_launcher_background"/>\n'
                '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
                '    <monochrome android:drawable="@mipmap/ic_launcher_foreground"/>\n'
                "</adaptive-icon>\n"
            )
        print("  ->", os.path.relpath(os.path.join(anydpi, name), ROOT))

    draw = os.path.join(res, "drawable")
    os.makedirs(draw, exist_ok=True)
    with open(os.path.join(draw, "ic_launcher_background.xml"), "w", encoding="utf-8") as f:
        f.write(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<shape xmlns:android="http://schemas.android.com/apk/res/android"\n'
            '    android:shape="rectangle">\n'
            '    <gradient\n'
            '        android:startColor="#181026"\n'
            '        android:endColor="#1F1530"\n'
            '        android:angle="270"/>\n'
            "</shape>\n"
        )
    print("  ->", os.path.relpath(os.path.join(draw, "ic_launcher_background.xml"), ROOT))


IOS_SIZES = [
    ("Icon-App-20x20@1x.png", 20), ("Icon-App-20x20@2x.png", 40), ("Icon-App-20x20@3x.png", 60),
    ("Icon-App-29x29@1x.png", 29), ("Icon-App-29x29@2x.png", 58), ("Icon-App-29x29@3x.png", 87),
    ("Icon-App-40x40@1x.png", 40), ("Icon-App-40x40@2x.png", 80), ("Icon-App-40x40@3x.png", 120),
    ("Icon-App-60x60@2x.png", 120), ("Icon-App-60x60@3x.png", 180),
    ("Icon-App-76x76@1x.png", 76), ("Icon-App-76x76@2x.png", 152),
    ("Icon-App-83.5x83.5@2x.png", 167),
    ("Icon-App-1024x1024@1x.png", 1024),
]


def make_ios(mark):
    d = os.path.join(ROOT, "ios", "Runner", "Assets.xcassets", "AppIcon.appiconset")
    for name, size in IOS_SIZES:
        # iOS ikonu tam kaplama kare olmalı (sistemin maskesi uygulanır),
        # saydamlık ve önceden yuvarlatılmış köşe YASAK.
        save(on_bg(mark, size, pad_ratio=0.16), os.path.join(d, name))


def make_web(mark):
    web = os.path.join(ROOT, "web")
    save(on_bg(mark, 32, pad_ratio=0.14), os.path.join(web, "favicon.png"))
    icons = os.path.join(web, "icons")
    save(on_bg(mark, 192, pad_ratio=0.14), os.path.join(icons, "Icon-192.png"))
    save(on_bg(mark, 512, pad_ratio=0.14), os.path.join(icons, "Icon-512.png"))
    # Maskable: güvenli alan %80
    for size in (192, 512):
        save(on_bg(mark, size, pad_ratio=0.22), os.path.join(icons, f"Icon-maskable-{size}.png"))


def make_marketing(mark):
    d = os.path.join(os.path.dirname(os.path.dirname(ROOT)), "marketing")
    os.makedirs(d, exist_ok=True)
    save(on_bg(mark, 512, pad_ratio=0.16), os.path.join(d, "play_app_icon.png"))
    save(on_bg(mark, 512, bg=Image.new("RGB", (512, 512), WHITE), pad_ratio=0.08),
         os.path.join(d, "play_app_icon_white.png"))


if __name__ == "__main__":
    src = load_source()
    mark = knock_out_flat_bg(src)
    print("assets:")
    make_assets(mark)
    print("android:")
    make_android(mark)
    print("ios:")
    make_ios(mark)
    print("web:")
    make_web(mark)
    print("marketing:")
    make_marketing(mark)
    print("\nTamam.")
