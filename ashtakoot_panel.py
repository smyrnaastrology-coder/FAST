# -*- coding: utf-8 -*-
"""
Ashtakoot paneli — app.py içine tek çağrıyla bağlanan kendi kendine yetenekli bölüm.

`app.py` çok büyük olduğu için doğum saati/yeri girişleri, hesap ve gösterim
tek bir fonksiyonda toplanmıştır. Panel, app.py'den gelen `ctx` sözlüğündeki
geocoder yardımcılarını (`ULKE_SEHIR_DB`, `sehir_bul`, `otomatik_utc_offset`)
kullanır; böylece mevcut şehir çözümleyicisi yeniden kullanılır ve iki ayrı
şehir veri tabanı tutulmaz.

Kullanım (app.py içinde):

    st.divider()
    ashtakoot_panel.goster(ctx)
"""

from datetime import datetime
from typing import Dict, Optional, Tuple

import streamlit as st

import ashtakoot_metin as MT
import ashtakoot_ui as UI
from ashtakoot_motoru import (
    AZAMI_TOPLAM, ashtakoot_hesapla, ay_konumu_utc, ay_nakshatrasi_hesapla,
    kendisi_ile,
)

#: Ay'ın doğuş saatinde yaklaşık kaç derece yol aldığı (yaklaşık zaman uyarısı).
AY_DEGREE_PER_HOUR = 13.0

MOD_ETIKET = {
    "es_sevgili": ("Eş / Sevgili", "İki kişinin Ay nakṣatra uyumu"),
    "ebeveyn_cocuk": ("Ebeveyn / Çocuk", "Ebeveyn ile çocuğun Ay nakṣatra bağı"),
    "potansiyel_yetenek": ("Potansiyel & Yetenek", "Tek kişi Ay nakṣatra profili"),
}


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------
def _saat_coz(girdi: str) -> Tuple[int, int, bool]:
    """'1430', '9:15', '915' gibi girdileri (saat, dakika, bilindi_mi) tuple'ına çevirir.

    Boş veya sayı olmayan girdi saatin **bilinmediği** anlamına gelir: 12:00
    kabul edilir ve `bilindi_mi=False` döner, böylece panel uyarıyı gösterebilir.
    """
    g = (girdi or "").strip().replace(":", "")
    if not g.isdigit():
        return 12, 0, False
    if len(g) == 1:
        h, m = int(g), 0
    elif len(g) == 2:
        h, m = int(g), 0
    elif len(g) == 3:
        h, m = int(g[:1]), int(g[1:])
    elif len(g) >= 4:
        h, m = int(g[:2]), int(g[2:4])
    else:
        h, m = 12, 0
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return 12, 0, False
    return h, m, True


def _saat_rozet(h: int, m: int) -> str:
    return "%02d:%02d" % (h, m)


def _ulke_liste(ctx: dict):
    return sorted(ctx["ULKE_SEHIR_DB"].keys())


# ---------------------------------------------------------------------------
# Kişi başına giriş
# ---------------------------------------------------------------------------
def _kisi_girisi(ctx: dict, etiket: str, varsayilan_tarih, anahtar_onek: str,
                 lang: str) -> Optional[dict]:
    """Bir kişinin doğum tarihi, saati ve yeri girişini yapar."""
    min_tarih, max_tarih = ctx["min_tarih"], ctx["max_tarih"]

    c1 = st.columns([1, 1])
    with c1[0]:
        ad = st.text_input(f"{etiket} · İsim", key=f"{anahtar_onek}_ad",
                           placeholder="Opsiyonel").strip()
    with c1[1]:
        tarih = st.date_input(f"{etiket} · Doğum Tarihi",
                              value=varsayilan_tarih, min_value=min_tarih,
                              max_value=max_tarih, format="DD/MM/YYYY",
                              key=f"{anahtar_onek}_tarih")

    c2 = st.columns([1, 1])
    with c2[0]:
        E = MT.ETIKET[lang]
        saat_girdi = st.text_input(
            f"{etiket} · {E['dogum_saat']}", value="", key=f"{anahtar_onek}_saat",
            placeholder="12:00 / 1430",
            help=MT.SAAT_YARDIM[lang])
    saat_h, saat_m, saat_gercek = _saat_coz(saat_girdi)
    with c2[1]:
        ulkeler = _ulke_liste(ctx)
        varsayilan_ulke = "Türkiye" if "Türkiye" in ulkeler else ulkeler[0]
        ulke = st.selectbox(f"{etiket} · Ülke", ulkeler,
                            index=ulkeler.index(varsayilan_ulke),
                            key=f"{anahtar_onek}_ulke")

    sehirler = ctx["ULKE_SEHIR_DB"].get(ulke) or []
    with c2[1]:
        if sehirler:
            sehir = st.selectbox(f"{etiket} · Şehir", sehirler,
                                 key=f"{anahtar_onek}_sehir")
        else:
            sehir = st.text_input(f"{etiket} · Şehir", placeholder="Şehir adı",
                                  key=f"{anahtar_onek}_sehir_yazi").strip()
            if not sehir:
                st.info("Bu ülke için şehir listesi yok. Şehir adını yazın.")
                return None

    if not sehir:
        return None

    geo = ctx["sehir_bul"](f"{sehir}, {ulke}")
    if not geo:
        st.error(f"{etiket} · Şehir bulunamadı: {sehir}, {ulke}. Koordinatlar "
                 f"girilemiyor.")
        return None

    lat, lon = float(geo["lat"]), float(geo["lon"])
    uo = ctx["otomatik_utc_offset"](
        lat, lon, tarih.year, tarih.month, tarih.day, saat_h)
    st.caption(f"{etiket} · {geo['sehir']}, {geo['ulke'] or ulke} · "
               f"{lat:.4f}, {lon:.4f} · UTC{uo:+g}")

    return {"ad": ad, "tarih": tarih, "saat": (saat_h, saat_m),
            "sehir": geo["sehir"], "ulke": geo["ulke"] or ulke,
            "lat": lat, "lon": lon, "uo": uo,
            "saat_gercek": saat_gercek,
            "saat_rozet": _saat_rozet(saat_h, saat_m)}


# ---------------------------------------------------------------------------
# Hesap
# ---------------------------------------------------------------------------
def _ay_hesapla(kisi: dict):
    """Doğum verisinden sidereal Ay bilgisini üretir.

    Saat bilinmiyorsa `yaklasik=True` işaretlenir; motor bunu sonucun
    `uyari` listesine yazar.
    """
    y, ay_, g = kisi["tarih"].year, kisi["tarih"].month, kisi["tarih"].day
    h, m = kisi["saat"]
    # Yerel saat -> UTC -> sidereal Lahiri Ay
    utc = ay_konumu_utc(y, ay_, g, h + m / 60.0 - kisi["uo"])
    return ay_nakshatrasi_hesapla(utc, yaklasik=not kisi.get("saat_gercek", True))


def _uyari_koy(kisi: dict, ay, lang: str = "tr") -> None:
    """Saat belirsizliğine bağlı yaklaşık konum uyarısı."""
    if kisi.get("saat_gercek", True):
        return
    E = MT.ETIKET[lang]
    st.warning(MT.SAAT_UYARI[lang].format(
        ad=kisi["ad"] or E["kisi"],
        derece=f"{AY_DEGREE_PER_HOUR:.0f}",
        rozet=kisi["saat_rozet"]))


# ---------------------------------------------------------------------------
# Bölüm
# ---------------------------------------------------------------------------
def goster(ctx: dict) -> None:
    """Ashtakoot bölümünü Streamlit'e basar."""
    mod = st.session_state.get("sim_modu", "potansiyel_yetenek")
    if mod not in MOD_ETIKET:
        return

    baslik, alt_baslik = MOD_ETIKET[mod]
    iki_kisi = mod in ("es_sevgili", "ebeveyn_cocuk")

    st.divider()
    st.markdown(
        f"<div style='text-align:center;margin:8px 0 4px 0'>"
        f"<div style='color:#C9A96E;font-size:1.5em'>✦</div>"
        f"<h2 style='color:#12263A;margin:2px 0'>Ashtakoot · 36</h2>"
        f"<div style='color:#5B6B7A;font-size:0.95em'>{alt_baslik}</div></div>",
        unsafe_allow_html=True,
    )

    # `lang` her zaman dil KODUDUR ('tr'/'en'/'es'); selectbox ise (kod, ad)
    # çifti döndürür, bu yüzden yalnızca kod tarafı kullanılır.
    kod2ad = MT.dil_secenekleri()
    ad2kod = {ad: kod for kod, ad in kod2ad}
    adlar = [ad for _, ad in kod2ad]
    kayitli = st.session_state.get("ashtakoot_lang", "tr")
    sec = st.columns([3, 1])
    with sec[1]:
        idx = ad2kod.get(kayitli, 0)
        # Seçici düz dil adları gösterir; sonuç kod karşılığına çevrilir.
        lang = ad2kod[st.selectbox("Ashtakoot dili", adlar, index=idx,
                                   key="ashtakoot_lang_box",
                                   label_visibility="collapsed")]
        st.session_state["ashtakoot_lang"] = lang

    with st.expander(f"🌙 Doğum verisi · {baslik}", expanded=True):
        if iki_kisi:
            c = st.columns(2)
            with c[0]:
                k1 = _kisi_girisi(ctx, "1. Kişi", ctx["varsayilan_tarih_1"], "ash_k1", lang)
            with c[1]:
                k2 = _kisi_girisi(ctx, "2. Kişi", ctx["varsayilan_tarih_2"], "ash_k2", lang)
        else:
            k1 = _kisi_girisi(ctx, "Kişi", ctx["varsayilan_tarih_1"], "ash_k1", lang)
            k2 = None

    if not k1:
        st.info("Ashtakoot için doğum verisi tamamlanmalı.")
        return

    try:
        ay1 = _ay_hesapla(k1)
    except Exception as e:                                # noqa: BLE001
        st.error(f"Ashtakoot hesaplanamadı: {e}")
        return

    ay2 = _ay_hesapla(k2) if k2 else None
    if ay2 is None:
        sonuc = kendisi_ile(ay1)
    else:
        sonuc = ashtakoot_hesapla(ay1, ay2)

    _uyari_koy(k1, ay1, lang)
    if k2:
        _uyari_koy(k2, ay2, lang)

# Özet
    UI.puan_grafik(sonuc, lang, mod)
    UI.kutu_goster(sonuc, lang, mod)

    # Karşılaştırma tablosu: koota puanı + her kişinin kendisiyle katkısı
    if ay2 is None:
        UI.tablo_goster(sonuc, lang, mod, ay_a=ay1)
    else:
        UI.tablo_goster(sonuc, lang, mod, ay_a=ay1, ay_b=ay2)

    st.markdown("**Koota ayrıntıları**")
    for k in sonuc.kootalar:
        m = MT.metin_getir(k.ad, k.puan, k.azami, lang)
        mod_notu = MT.mod_yorumu(k.ad, mod, lang)
        with st.expander(
            f"{UI.koota_adi(k, lang)} · {k.puan}/{k.azami} · {m['baslik']}",
            expanded=False,
        ):
            st.markdown(f"**{m['baslik']}**")
            st.markdown(m["aciklama"])
            if mod_notu:
                st.markdown(f"*{mod_notu}*")
            if m.get("ipucu"):
                st.caption(f"{MT.ETIKET[lang]['ipucu']} · {m['ipucu']}")

    if ay2 is None:
        st.markdown("---")
        UI.profil_goster(ay1, lang)
        st.markdown("---")
        UI.uyum_haritasi_goster(ay1, lang, mod)
    else:
        st.caption(
            "Tara, Vashya ve Gana yönlü kootalardır: A/B ile B/A sırası "
            "değiştiğinde puanlar da değişebilir.")
        st.caption("Pratikte en yüksek ulaşılabilir toplam 34'dür (Nadi aynı ise 28).")

    _kaydet(k1, k2, ay1, ay2, sonuc, lang, mod)


def _kaydet(k1, k2, ay1, ay2, sonuc, lang, mod) -> None:
    """Hesaplanan sonucu PDF üretimi için session_state'e yazar.

    PDF fonksiyonları Streamlit olmadan da çalışabildiği için sonuç, ekrana
    basılan görselden değil bu kayıttan okunur. Panel hiç çalıştırılmadıysa
    anahtar oluşmaz ve PDF bölümü sessizce atlanır.
    """
    def kisi(k, ay):
        return None if k is None else {
            "isim": k.get("ad") or "",
            "tarih": f"{k['tarih'].day:02d}.{k['tarih'].month:02d}.{k['tarih'].year}",
            "saat": k["saat_rozet"],
            "sehir": k["sehir"],
            "ulke": k["ulke"],
            "nakshatra": f"{ay.nakshatra(lang)} {ay.pada}. pada",
            "burc": ay.burc(lang),
            "lon": ay.lon,
        }

    # Her kişinin kendisiyle karşılaştırması: PDF tablosunda "A · Kendisiyle"
    # sütunları bu değerleri gösterir (toplam tanım gereği 28/36).
    def katki(ay):
        if ay is None:
            return None
        return {k.ad: k.puan for k in ashtakoot_hesapla(ay, ay).kootalar}

    st.session_state["ashtakoot_sonuc"] = {
        "lang": lang,
        "mod": mod,
        "katki_a": katki(ay1),
        "katki_b": katki(ay2),
        "toplam": sonuc.toplam,
        "azami": AZAMI_TOPLAM,
        "yuzde": round(sonuc.yuzde, 1),
        "seviye": sonuc.seviye,
        "kendisi_ile": sonuc.kendisi_ile,
        "a": kisi(k1, ay1),
        "b": kisi(k2, ay2) if k2 is not None else None,
        "kootalar": [
            {"ad": UI.koota_adi(k, lang), "anahtar": k.ad, "ad_tr": k.ad_tr,
             "puan": k.puan, "azami": k.azami,
             "baslik": MT.metin_getir(k.ad, k.puan, k.azami, lang)["baslik"],
             "not": k.not_ or ""}
            for k in sonuc.kootalar
        ],
        "toplam_baslik": MT.toplam_metni(sonuc.seviye, lang)["baslik"],
        "toplam_aciklama": MT.toplam_metni(sonuc.seviye, lang)["aciklama"],
    }
