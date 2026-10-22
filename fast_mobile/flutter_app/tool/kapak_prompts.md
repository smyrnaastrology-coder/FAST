# Holavon — Kapak / Görsel Promptları (ChatGPT Image)

> Kullanım: ChatGPT → *Create image* modunda aşağıdaki metni **tek parça** yapıştır.
> Üretilen görseli indirip `fast_mobile/flutter_app/assets/` içine verilen isimle kaydet.
> Daha sonra `pubspec.yaml` assets listesine ekle ve ilgili ekranda `Image.asset(...)` ile göster.

Renk paleti (tüm promptlarda sabit):
- Altın / Altın sarısı: `#C9A96E`, açık altın `#E0C68A`
- Koyu mor-siyah zemin: `#1A1423`, ikinci koyu ton `#251C33`
- Sıcak fener ışığı / kehribar: `#F2C57C`

---

## 1) Play Store "Feature Graphic" (kapak) — 1024 × 500 px
> Play Console → Store presence → Main store listing → **Feature graphic**. Zorunlu oran 2:1.

```
Create a premium dark celestial "feature graphic" banner for an astrology app called HOLAVON.

Canvas: 1024 x 500 pixels, exactly 2:1 aspect ratio, landscape orientation.

Scene: a deep midnight-violet night sky gradient (from #1A1423 at the top to #251C33 at the bottom), filled with a subtle field of small warm gold stars. On the right third, a large elegant gold astrolabe / horary chart circle rendered as fine luminous line art: two concentric rings, 12 zodiac-house tick marks around the outer ring, faint constellation lines and a delicate crescent moon in the upper-left of the circle. Thin gold geometric "orbit" arcs sweep across the whole banner from the left edge, very subtle, like engraved constellation diagrams. Soft warm amber light glows from behind the astrolabe circle, and a faint nebula haze in gold and plum tones.

Style: premium editorial, minimal, luxurious, dark luxury branding, high-end magazine cover aesthetic, extremely clean, no clutter, cinematic soft light, high detail, 8k, sharp vector-like line art.

Composition: leave the entire LEFT HALF of the image calm, dark and mostly empty (this space is reserved for text that will be overlaid later). Place all celestial line art and the astrolabe on the RIGHT side.

ABSOLUTELY NO text, no letters, no numbers, no logo, no watermark, no frame, no border, no phone mockup, no people, no hands.
```

---

## 2) Landing sayfası kapak / hero — 1600 × 900 px (yatay, 16:9)
> `fast_mobile/flutter_app/assets/kapak.png` olarak kaydedilecek; landing hero arka planı.

```
Create a cinematic dark celestial background for a luxury astrology app landing page.

Canvas: 1600 x 900 pixels, 16:9.

Scene: an endless deep-space night in violet-black (#1A1423) with a soft radial glow of warm gold (#C9A96E) emanating from the lower-right area. Delicate thin gold constellation lines and small stars fill the upper-left, fading into darkness. A very large, faint, elegant gold astrolabe ring sits partially off-canvas on the right edge, only its left arc visible, rendered as extremely thin luminous line art. A thin crescent moon floats in the upper-left corner. Soft amber bokeh particles drift like slow golden dust. Subtle film grain for depth.

Mood: mystical, calm, expensive, spiritual, deep night, stargazing, premium dark-luxury web design background.

Layout: mostly empty and uncluttered in the center-left, so that a headline and buttons can be placed on top. Very low contrast in the center so white text stays readable.

ABSOLUTELY NO text, no letters, no numbers, no logo, no watermark, no border, no people, no faces, no zodiac symbols as text.
```

---

## 3) Sosyal medya kapak (Instagram post) — 1080 × 1350 px (4:5)
> `fast_mobile/flutter_app/assets/kapak_sosyal.png`

```
Create a vertical dark celestial poster background for a social media post about astrology.

Canvas: 1080 x 1350 pixels, 4:5 portrait.

Scene: a deep violet-to-black vertical gradient sky (#1A1423 top, #251C33 bottom) with a scattered field of tiny gold stars. In the upper half, a centered elegant gold horary chart / astrolabe drawn in fine thin luminous line art: concentric rings, 12 house ticks, a small crescent moon, and faint constellation geometry. The lower third is dark and calm, with soft warm amber light haze and a few drifting golden dust particles.

Style: premium, minimalist, mystical, dark luxury, high-end editorial, cinematic, 8k detail.

The upper-middle area around the astrolabe and the whole lower third must stay clean and dark for text overlay.

ABSOLUTELY NO text, no letters, no numbers, no logo, no watermark, no border.
```

---

## 4) Uygulama ikonu (Play listing 512 × 512) — opsiyonel
> Mevcut vektör amblem çok temiz; sadece Play listing görseli olarak PNG üretmek istersen:

```
Create a minimal luxury app icon for an astrology app.

Canvas: 512 x 512 pixels, square.

Design: a single thin gold (#C9A96E) circle outline centered on a deep violet-black (#1A1423) background with a very subtle radial gradient. Inside the circle, 12 short tick marks divide the ring into twelve segments (like an astrolabe / horary chart), and in the center a clean geometric letter H drawn with two straight vertical bars and a small horizontal crossbar, all in the same gold. A small thin crescent moon sits in the upper-left area inside the ring.

Style: flat vector, perfectly symmetric, crisp 2px-equivalent strokes, high contrast, no gradient on the symbol itself, modern premium iOS app icon, no rounding of the canvas.

ABSOLUTELY NO text, no letters other than the single geometric H, no extra ornaments, no shadow, no border, no mockup.
```

---

## Dosya adları / hedefler

| Prompt | Kaydedilecek yol | Nereye kullanılır |
|---|---|---|
| 1 | `marketing/play_feature_graphic.png` | Play Console → Feature graphic (1024×500) |
| 2 | `fast_mobile/flutter_app/assets/kapak.png` | Landing hero arka planı (pubspec assets'e ekle) |
| 3 | `fast_mobile/flutter_app/assets/kapak_sosyal.png` | Instagram / sosyal medya paylaşımı |
| 4 | `marketing/play_app_icon.png` | Play Console → App icon (512×512) |

## Notlar
- ChatGPT "Create image" çıktısı genelde 1024 kare verir; 1) ve 2) için en-boy oranını koruyup
  gerekirse `1024×500` / `1600×900` olacak şekilde kırp veya ImageMagick ile resize et.
- Promptlarda **metin istemiyoruz**; başlıklar uygulama içinde Flutter `Text` ile bindirilir (çok dillilik için).
- Üretilen PNG'ler şeffaf olmamalı (JPEG/PNG opak).
