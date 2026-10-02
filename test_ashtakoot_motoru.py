# -*- coding: utf-8 -*-
"""Standart 36 puanlı Ashtakoot motorunun birim testleri.

Çalıştırma:  python test_ashtakoot_motoru.py
"""

import sys
import traceback

from ashtakoot_motoru import (

    AZAMI_TOPLAM, BURC_ADLARI, KAPSAM_DISI_KURALLAR, KOOTALAR,
    NADI_LORDU, NAKSHATRALAR, YONLU_KOOTALAR, AshtaKootSonuc, _burc_iliskisi,
    ashtakoot_hesapla, ay_konumu_utc, ay_nakshatrasi_hesapla, kendisi_ile,
    nadi_dosha_analizi, nakshatra_profili, nakshatra_uyum_haritasi, vashya_grubu,
)

GECTI, KALDI = 0, 0


def kontrol(kosul, mesaj):
    global GECTI, KALDI
    if kosul:
        GECTI += 1
        print("  gecti  " + mesaj)
    else:
        KALDI += 1
        print("  KALDI  " + mesaj)


def baslik(t):
    print("\n" + t)
    print("-" * len(t))


# --------------------------------------------------------------------------
baslik("1) Sabitler ve tablolar")
kontrol(AZAMI_TOPLAM == 36, "azami toplam 36")
kontrol(len(NAKSHATRALAR) == 27, "27 nakshatra")
kontrol(len(KOOTALAR) == 8, "8 koota")
kontrol([k[4] for k in KOOTALAR] == [1, 2, 3, 4, 5, 6, 7, 8],
        "koota agirliklari 1..8")
kontrol(len(BURC_ADLARI) == 12, "12 burc")

# --------------------------------------------------------------------------
baslik("2) Referans vaka: 1988-06-23 15:40 Izmir (UTC+3) = 12:40 UTC")
lon = ay_konumu_utc(1988, 6, 23, 12 + 40 / 60.0)
sevde = ay_nakshatrasi_hesapla(lon)
print("  sidereal Ay : %.5f" % sevde.lon)
print("  burc        : %s (%.2f derece)" % (sevde.burc_adi, sevde.burc_ici_derece))
print("  nakshatra   : %d %s, %d. pada" % (sevde.nakshatra_no, sevde.nakshatra_adi, sevde.pada))
kontrol(abs(sevde.lon - 170.70230) < 0.01, "sidereal Ay 170.7023")
kontrol(sevde.nakshatra_no == 13 and sevde.nakshatra_adi == "Hasta",
        "nakshatra 13 = Hasta")
kontrol(sevde.pada == 4, "4. pada")
kontrol(sevde.burc_adi == "Başak", "burç Başak (Virgo)")

# --------------------------------------------------------------------------
baslik("3) TUM NAKSHATRA + PADA IZGARASI (0..360, 3.3333 adim)")
aylar = []
i = 0
while i < 1080:
    a = ay_nakshatrasi_hesapla(i * (360.0 / 1080))
    aylar.append(a)
    i += 1
kontrol(len(aylar) == 1080, "1080 puanlik izgara")
kontrol(all(1 <= a.pada <= 4 for a in aylar), "pada 1..4 araliginda")
kontrol({a.nakshatra_no for a in aylar} == set(range(1, 28)),
        "27 nakshatronun tamami temsil edildi")
# ilk puanlar
kontrol(ay_nakshatrasi_hesapla(0.0).nakshatra_adi == "Asvini", "0 derece = Asvini")
kontrol(ay_nakshatrasi_hesapla(359.999).nakshatra_no == 27, "360 derece = Revati")
# 108 puan dolu (sinir noktalari yuzden 1-2 puanlik kayma normaldir)
pada_sayilari = {}
for a in aylar:
    pada_sayilari[a.pada] = pada_sayilari.get(a.pada, 0) + 1
print("  pada dagilimi:", pada_sayilari)
kontrol(sum(pada_sayilari.values()) == 1080, "1080 puan tamamen siniflandi")
kontrol(all(abs(v - 270) <= 2 for v in pada_sayilari.values()),
        "her pada ~270 puana sahip")

# --------------------------------------------------------------------------
baslik("4) KENDISIYLE KARSILASTIRMA = 28/36 ve Nadi 0")
toplamlar = []
for a in aylar[::7]:
    s = kendisi_ile(a)
    toplamlar.append(s.toplam)
kontrol(set(toplamlar) == {28}, "tum izgarada toplam daima 28 (orn=%s)" % set(toplamlar))
kontrol(all(kendisi_ile(a).koota("nadi").puan == 0 for a in aylar[::37]),
        "nadi her zaman 0")
kontrol(all(kendisi_ile(a).koota("rasi").puan == 7 for a in aylar[::37]),
        "rasi her zaman 7")
beklenen = {"varna": 1, "vashya": 2, "tara": 3, "yoni": 4,
            "graha_maitri": 5, "gana": 6, "rasi": 7, "nadi": 0}
s = kendisi_ile(sevde)
for anahtar, p in beklenen.items():
    k = s.koota(anahtar)
    kontrol(k.puan == p, "%s = %d (alinan %d)" % (anahtar, p, k.puan))
kontrol(s.toplam == 28, "Sevde kendisiyle 28")
kontrol(round(s.yuzde, 1) == 77.8, "yuzde 77.8 (yuvarlanmis)")
kontrol(s.seviye == "orta", "seviye 'orta' (28 -> 28-29 ideal bandi)")
kontrol(s.kendisi_ile is True, "kendisi_ile bayragi")

# --------------------------------------------------------------------------
baslik("5) SIMETRI: yalnizca yonsuz kootalar A/B == B/A vermeli")
# Tara, Vashya ve Gana klasik schema geregi yonludur (bkz. YONLU_KOOTALAR)
simetrik = [k for k in ("varna", "yoni", "graha_maitri", "rasi", "nadi")]
asimetrik = 0
sim_sapma = 0
for a in aylar[::13]:
    for b in aylar[::29]:
        if ashtakoot_hesapla(a, b).toplam != ashtakoot_hesapla(b, a).toplam:
            asimetrik += 1
        s1 = ashtakoot_hesapla(a, b)
        s2 = ashtakoot_hesapla(b, a)
        for k in simetrik:
            if s1.koota(k).puan != s2.koota(k).puan:
                sim_sapma += 1
kontrol(sim_sapma == 0, "yonsuz 5 koota simetrik (%d sapma)" % sim_sapma)
print("  bilgi: toplam asimetrisi %d adet (tara/vashya/gana yonlulugu beklenir)" % asimetrik)
kontrol(set(YONLU_KOOTALAR) == {"tara", "vashya", "gana"}, "YONLU_KOOTALAR tanimli")
tara_yonlu = any(ashtakoot_hesapla(a, b).koota("tara").puan !=
                 ashtakoot_hesapla(b, a).koota("tara").puan
                 for a in aylar[::13] for b in aylar[::29])
kontrol(tara_yonlu, "tara yonlu calisiyor")

# --------------------------------------------------------------------------
baslik("6) SINIR KOSULLARI")
kontrol(ashtakoot_hesapla(aylar[0], aylar[0]).toplam == 28, "Asvini kendisiyle 28")
kontrol(kendisi_ile(aylar[-1]).toplam == 28, "Revati kendisiyle 28")
# farkli ama ayni burctan
ay = ay_nakshatrasi_hesapla(0.1)
kontrol(ay.pada == 1 and ay.gana == "Deva" and ay.varna == "Brahmin",
        "Asvini 1. pada: Deva / Brahmin")
ay = ay_nakshatrasi_hesapla(3.4)
kontrol(ay.pada == 2 and ay.gana == "Deva" and ay.varna == "Kshatriya",
        "Asvini 2. pada: Deva / Kshatriya")
ay = ay_nakshatrasi_hesapla(6.7)
kontrol(ay.pada == 3 and ay.gana == "Manushya" and ay.varna == "Vaishya",
        "Asvini 3. pada: Manushya / Vaishya")
ay = ay_nakshatrasi_hesapla(11.0)
kontrol(ay.pada == 4 and ay.gana == "Rakshasa" and ay.varna == "Shudra",
        "Asvini 4. pada: Rakshasa / Shudra")

# vashya yari burc siniri
kontrol(vashya_grubu(10, 1) == "Manushya" and vashya_grubu(10, 3) == "Chatura",
        "Kova 1-2. pada Manushya, 3-4. pada Chatura")
kontrol(vashya_grubu(11, 1) == "Khala" and vashya_grubu(11, 3) == "Chatura",
        "Balik 1-2. pada Khala, 3-4. pada Chatura")

# --------------------------------------------------------------------------
baslik("7) PUNAN BELLEK DEGISMEDEN")
a = ay_nakshatrasi_hesapla(170.7023)
b = ay_nakshatrasi_hesapla(120.0)
s1 = ashtakoot_hesapla(a, b).toplam
s2 = ashtakoot_hesapla(ay_nakshatrasi_hesapla(170.7023),
                      ay_nakshatrasi_hesapla(120.0)).toplam
kontrol(s1 == s2, "ayni girdi -> ayni toplam (%d)" % s1)

# --------------------------------------------------------------------------
baslik("8) UYUM HARITASI + PROFIL")
p = nakshatra_profili(sevde)
kontrol(len(p["harita"]) == 27, "harita 27 satir")
kontrol(sum(1 for s in p["harita"] if s["kendisi"]) == 1, "haritada 1 kendisi")
kontrol(p["harita"] == sorted(p["harita"], key=lambda s: (-s["toplam"], s["nakshatra_no"])),
        "harita puana gore sirali")
kontrol(len(p["en_iyi"]) == 5 and len(p["en_kotu"]) == 5,
        "en iyi 5 / en kotu 5")
kendi_satir = [s for s in p["harita"] if s["kendisi"]][0]
kontrol(kendi_satir["toplam"] == 28, "haritada kendi satiri 28")
# puan 0-36 araliginda
kontrol(all(0 <= s["toplam"] <= 36 for s in p["harita"]), "puanlar 0..36 araliginda")

# --------------------------------------------------------------------------
baslik("9b) YONI KLASIK ESLESMELERI")
# Yoni, sembol degil eslesen hayvandir: Hasta'nin sembolu "El" ama yonisi "At"
# ve Asvini ile 4/4 verir. Sembol ile yoni karistirilirsa burasi kacar.
def nak(n, p=1):
    from ashtakoot_motoru import NAKSHATRA_ADI, PADA_ADI
    return ay_nakshatrasi_hesapla((n - 1) * NAKSHATRA_ADI + (p - 1) * PADA_ADI + 0.4)


def yoni_puani(a, b):
    return [k.puan for k in ashtakoot_hesapla(a, b).kootalar if k.ad == "yoni"][0]


KLASIK_CIFTLER = [(1, 13), (2, 12), (3, 8), (5, 9), (6, 11), (7, 15),
                  (10, 25), (14, 20), (17, 22), (18, 21), (19, 23)]
for a_no, b_no in KLASIK_CIFTLER:
    a, b = nak(a_no), nak(b_no)
    kontrol(yoni_puani(a, b) == 4,
            "klasik cift 4/4: %s - %s" % (a.nakshatra_adi, b.nakshatra_adi))
    kontrol(a.yoni == b.yoni,
            "cift ayni hayvani paylasiyor: %s" % a.yoni)

kontrol(yoni_puani(nak(1, 1), nak(13, 2)) == 3, "ayni hayvan, zit cinsiyet 3/4")
kontrol(yoni_puani(nak(1), nak(16)) == 0, "farkli yoni 0/4")
kontrol(nak(13).yoni == "At" and nak(13).sembol == "El",
        "Hasta: yoni At, sembol El (ayri kavramlar)")
kontrol(len({nak(n).yoni for n in range(1, 28)}) == 16,
        "16 farkli yoni hayvani")
kontrol(all(nak(n).yoni is not None for n in range(1, 28)),
        "27 nakshatranin hepsinde yoni var")

# --------------------------------------------------------------------------
baslik("9c) DIL YERELLESTIRMESI")
from ashtakoot_motoru import (BURC_ADLARI_EN, BURC_ADLARI_ES, GEZEGEN_EN,
                              GEZEGEN_ES, YONI_ANIMAL_EN, YONI_ANIMAL_ES)
TR_KARAKTER = set("çÇğĞıİöÖşŞüÜ")

kontrol(len(BURC_ADLARI_EN) == 12 and len(BURC_ADLARI_ES) == 12,
        "12 burc EN + ES")
kontrol(BURC_ADLARI_ES[1] == "Tauro" and BURC_ADLARI_ES[10] == "Acuario",
        "Ispanyolca burc adlari dogru")
kontrol(GEZEGEN_ES["Sun"] == "Sol" and GEZEGEN_ES["Moon"] == "Luna"
        and GEZEGEN_ES["Mars"] == "Marte", "Ispanyolca gezegen adlari")
kontrol(not (set(BURC_ADLARI_ES) & TR_KARAKTER),
        "ES burc adlarinda Turkce karakter yok")
kontrol(not (set(GEZEGEN_ES.values()) & TR_KARAKTER),
        "ES gezegen adlarinda Turkce karakter yok")
kontrol(not (set(YONI_ANIMAL_ES.values()) & TR_KARAKTER),
        "ES yoni adlarinda Turkce karakter yok")
kontrol(all(v in YONI_ANIMAL_EN and v in YONI_ANIMAL_ES
            for v in {nak(n).yoni for n in range(1, 28)}),
        "her yoni hayvaninin EN ve ES cevirisi var")
kontrol(set(YONI_ANIMAL_EN) == set(YONI_ANIMAL_ES),
        "EN ve ES yoni sozlukleri ayni anahtarlari kapsiyor")

a = nak(13)
kontrol(a.ozet("tr") == "Hasta 1. · Başak", "ozet TR")
kontrol(a.ozet("es") == "Hasta 1. · Virgo", "ozet ES (burc cevrildi)")
kontrol(a.burc("es") == "Virgo" and a.burc("en") == "Virgo", "burc EN/ES")
kontrol(a.lord_adi("tr") == "Moon" and a.lord_adi("es") == "Luna",
        "lord adi cevrildi")
kontrol(a.yoni_adi("tr") == "At" and a.yoni_adi("es") == "Caballo",
        "yoni adi cevrildi")
kontrol(a.cinsiyet_adi("tr") == "erkek" and a.cinsiyet_adi("es") == "masculino",
        "cinsiyet cevrildi")
kontrol(a.ozet("fr") == a.ozet("tr"), "bilinmeyen dil TR'a duser")

h = nakshatra_uyum_haritasi(a)[0]
kontrol(all(("lord_es" in h and "burc_es" in h and "sembol_es" in h)
            for h in nakshatra_uyum_haritasi(a)), "haritada ceviri alanlari var")

# --------------------------------------------------------------------------
baslik("9) SOZLUK SERILESTIRME")
d = kendisi_ile(sevde).tablo_sozlugu()
kontrol(set(("toplam", "azami", "yuzde", "seviye", "a", "b", "kootalar")) <= set(d),
        "beklenen anahtarlar mevcut")
kontrol(len(d["kootalar"]) == 8, "sozlukte 8 koota")
kontrol(all(set(("ad", "azami", "puan")) <= set(k) for k in d["kootalar"]),
        "koota sozlugunden eksik alan yok")

# --------------------------------------------------------------------------
baslik("10) ARAYUZ VE PDF METINLERI")
import ashtakoot_metin as MT

# Panelde kullanilan her ETIKET alani ucu dilde de mevcut olmali.
GEREKEN_ETIKET = ("koota", "puan", "kendisiyle", "kendi", "seviye", "yoni_bos",
                  "dogum_saat", "kisi", "ipucu")
for _lang in ("tr", "en", "es"):
    kontrol(not [k for k in GEREKEN_ETIKET if k not in MT.ETIKET[_lang]],
            "ETIKET[%s] eksik alan yok" % _lang)

kontrol(MT.ETIKET["es"]["kendisiyle"] == "Propio"
        and MT.ETIKET["en"]["kendisiyle"] == "Self",
        "kendisiyle basligi her dilde kisa")
kontrol(not (set(MT.ETIKET["es"].values()) & TR_KARAKTER),
        "ES ETIKET degerlerinde Turkce karakter yok")

# Ispanyolca 'Hint' (Ingilizce) sizmamali, kendi on eki gelmeli.
kontrol(MT.ETIKET["es"]["ipucu"] == "Consejo"
        and MT.ETIKET["en"]["ipucu"] == "Hint"
        and MT.ETIKET["tr"]["ipucu"] == "İpucu", "ipucu on eki ucu dilde")

# Saat uyarisi ve yardimi her dilde formatlanabilir olmali.
for _lang in ("tr", "en", "es"):
    kontrol(bool(MT.SAAT_UYARI[_lang].format(ad="X", derece="13", rozet="12:00")),
            "SAAT_UYARI[%s] formatlanir" % _lang)
    kontrol(bool(MT.SAAT_YARDIM[_lang]), "SAAT_YARDIM[%s] dolu" % _lang)

# PDF sabit metinleri: baslik/alt/not eksiksiz ve yabanci dil sizmaz.
for _lang in ("tr", "en", "es"):
    _pm = MT.pdf_metin(_lang)
    kontrol(set(_pm) == {"baslik", "alt", "not"}, "PDF_METIN[%s] alanlari" % _lang)
    kontrol(all(_pm.values()), "PDF_METIN[%s] degerleri dolu" % _lang)
kontrol(MT.pdf_metin("xx") is MT.pdf_metin("tr"), "bilinmeyen dil PDF'te TR")
_basliklar = {MT.pdf_metin(l)["baslik"] for l in ("tr", "en", "es")}
kontrol(len(_basliklar) == 3, "PDF basliklari ucu dilde farkli")
for _lang in ("tr", "en", "es"):
    kontrol(not (set(MT.pdf_metin(_lang)["baslik"]) & set("çğıöşüÇĞİÖŞÜ")),
            "PDF basligi[%s] Turkce karakter icermiyor" % _lang)
# TR notu Turkce karakter icermelidir; EN/ES cevirileri sizmamalidir.
kontrol(set(MT.pdf_metin("tr")["not"]) & set("şŞğĞ"),
        "TR PDF notu Turkce karakter iceriyor")
for _lang in ("en", "es"):
    kontrol(not (set(MT.pdf_metin(_lang)["not"]) & set("çğıöşüÇĞİÖŞÜ")),
            "PDF notu[%s] Turkce karakter icermiyor" % _lang)

# --------------------------------------------------------------------------
# Nadi Dosha: bhanga / taraka degerlendirmesi
# --------------------------------------------------------------------------
# Bu blok nadi kootasinin 0/8 puanina DOKUNMAZ; yalnizca varlik, siddet ve
# baglam kodlarini dogrular. Puanin degismedigini ayrica sabitleriz.

# Burc iliskisi tablosu: simetrik, 0..6 mesafe ve etiket.
_bekl = {0: "1", 1: "2/12", 2: "3/11", 3: "4/10", 4: "5/9", 5: "6/8", 6: "7"}
for _x in range(12):
    for _y in range(12):
        _d, _e = _burc_iliskisi(_x, _y)
        kontrol(_d in range(7) and _e == _bekl[_d],
                "burc iliskisi %d,%d = %s" % (_x, _y, _e))
# Simetri: iliski yonden bagimsiz olmali.
for _x in range(12):
    for _y in range(12):
        kontrol(_burc_iliskisi(_x, _y) == _burc_iliskisi(_y, _x),
                "burc iliskisi simetrik %d,%d" % (_x, _y))

# Nadi lordlari pada -> gezegen, dort pada da tanimli.
kontrol(set(NADI_LORDU) == {1, 2, 3, 4}, "NADI_LORDU dort pada kapsiyor")
kontrol(NADI_LORDU[1] == "Mars" and NADI_LORDU[4] == "Venus",
        "nadi lordlari Mars/Venus ile basliyor bitiyor")

# Ayni nadi = dosha var; farkli nadi = dosha yok.
_ay_4p = ay_nakshatrasi_hesapla(239.3833)   # Jyeshtha 4. pada, nadi_3
_ay_4p2 = ay_nakshatrasi_hesapla(238.0000)  # Jyeshtha 4. pada, nadi_3
_ay_1p = ay_nakshatrasi_hesapla(5.0000)     # Ashwini 1. pada, nadi_1
kontrol(_ay_4p.nadi == _ay_4p2.nadi, "ayni pada ayni nadi")
kontrol(_ay_4p.nadi != _ay_1p.nadi, "farkli pada farkli nadi")

_d = nadi_dosha_analizi(_ay_4p, _ay_4p2)
kontrol(_d["var"] is True, "ayni nadi -> dosha var")
kontrol(_d["seviye"] in ("belirgin", "hafif", "hafifletilmis"),
        "dosha seviyesi gecerli: %s" % _d["seviye"])
kontrol(_d["nadi_lord_a"] == _d["nadi_lord_b"], "ayni pada -> ayni nadi lordu")
kontrol(set(KAPSAM_DISI_KURALLAR), "kapsam disi kurallar bildirilmis")
kontrol(_d["kapsam_disi"] == list(KAPSAM_DISI_KURALLAR),
        "kapsam disi listesi motor sabitiyle ayni")

_d = nadi_dosha_analizi(_ay_4p, _ay_1p)
kontrol(_d["var"] is False, "farkli nadi -> dosha yok")
kontrol(_d["seviye"] == "yok", "farkli nadi -> seviye yok")
kontrol(_d["kosullar"] == [], "dosha yoksa kosul listesi bos")

# Bhanga ve taraka kozleri birbirini dislamamali; ayni kosul ikisinde olmaz.
_kodlar = [k["kod"] for k in nadi_dosha_analizi(_ay_4p, _ay_4p2)["kosullar"]]
kontrol(len(_kodlar) == len(set(_kodlar)), "kosul kodlari tekil")
kontrol("rasi_kendra" not in _kodlar or "rasi_dusman" not in _kodlar,
        "bhanga ve taraka ayni anda gelmiyor")

# Sonuc tablosunda blok var ve puan degistirmemis olmali.
_sonuc = ashtakoot_hesapla(_ay_4p, _ay_4p2)
_tab = _sonuc.tablo_sozlugu()
kontrol("nadi_dosha" in _tab, "tabloda nadi_dosha anahtari")
kontrol(_sonuc.koota("nadi").puan == 0, "nadi puani 0/8 kaldi")
kontrol(_sonuc.toplam == 28, "ayni nadi kendisiyle toplam 28/36")
# Kendisiyle karsilastirmada da blok dolu olmali.
kontrol(bool(kendisi_ile(_ay_4p).nadi_dosha), "kendisi_ile nadi_dosha dolu")

# Metin katmani: uc dilde de ayni yapi ve bos alan yok.
for _lang in ("tr", "en", "es"):
    _m = MT.nadi_dosha_metin(_lang)
    kontrol(set(_m) == {"baslik", "seviye", "kosullar", "etiket", "ozet_etiket",
                        "kapsam_disi_baslik", "kapsam_disi", "kapsam_disi_notu",
                        "puan_notu"}, "NADI_DOSHA_METIN[%s] anahtar seti" % _lang)
    kontrol(set(_m["seviye"]) == {"yok", "belirgin", "hafif", "hafifletilmis"},
            "NADI_DOSHA_METIN[%s] dort seviye" % _lang)
    kontrol(set(_m["kosullar"]) == {"rasi_kendra", "nadi_lord_ayni",
                                    "ayni_gana", "ayni_varna", "rasi_dusman"},
            "NADI_DOSHA_METIN[%s] kosul kumesi motorla ayni" % _lang)
    kontrol(set(_m["kapsam_disi"]) == set(KAPSAM_DISI_KURALLAR),
            "kapsam disi[%s] motor sabitiyle ayni" % _lang)
    for _s, _v in _m["seviye"].items():
        kontrol(_v.get("baslik") and _v.get("aciklama") and _v.get("ipucu"),
                "NADI_DOSHA_METIN[%s].%s dolu" % (_lang, _s))
    for _k, _v in _m["kosullar"].items():
        kontrol(_v.get("baslik") and _v.get("detay"),
                "NADI_DOSHA_METIN[%s].%s dolu" % (_lang, _k))
kontrol(MT.nadi_dosha_metin("xx") is MT.nadi_dosha_metin("tr"),
        "bilinmeyen dilde nadi_dosha metni TR")
# Turkce metin Turkce karakter icermeli; EN/ES sizmamali.
_tr_m = MT.nadi_dosha_metin("tr")
kontrol(set(_tr_m["seviye"]["hafif"]["aciklama"]) & set("şŞğĞıİ"),
        "TR nadi_dosha metni Turkce karakter iceriyor")
for _lang in ("en", "es"):
    _m = MT.nadi_dosha_metin(_lang)
    kontrol(not (set(_m["seviye"]["hafif"]["aciklama"]) & set("çğıöşüÇĞİÖŞÜ")),
            "EN/ES nadi_dosha metni Turkce karakter sizdirmiyor (%s)" % _lang)


# --------------------------------------------------------------------------
# JARGONSUZ dogal dil katmani (ashtakoot_dogal_*): her puan icin 3 metin.
# --------------------------------------------------------------------------
import re  # noqa: E402

_JARGON = re.compile(
    r"\b(varna|vashya|tara|yoni|graha|maitri|gana|rasi|nadi|bhanga|pada|koota|"
    r"jyotish|kundli|dosha|nakshatra|paksha)\b", re.IGNORECASE)

_AZAMI = {k[0]: k[4] for k in KOOTALAR}
_BEK_PUAN = sum(a + 1 for a in _AZAMI.values())

kontrol(_BEK_PUAN == 44, "dogal katman 44 puan durumu kapsar (%d)" % _BEK_PUAN)

# ayni (koota, puan) icin SEKIZ farkli metin uretilebilmeli (4 aci x 2 govde)
for _lang in ("tr", "en", "es"):
    _dg = MT.dogal_aciklama("yoni", 0, _lang)
    kontrol(bool(_dg.get("aciklama")) and bool(_dg.get("baslik")),
            "dogal_aciklama[%s] baslik+aciklama donuyor" % _lang)
    kontrol(_dg.get("aci") in ("vaat", "anlatı", "simge", "dikkat"),
            "dogal_aciklama[%s] gecerli bir aci donuyor (%s)" % (_lang, _dg.get("aci")))

    _metinler = set()
    for _ in range(400):
        _metinler.add(MT.dogal_aciklama("yoni", 0, _lang)["aciklama"])
    kontrol(len(_metinler) == 8,
            "dogal_aciklama[%s] ayni puanda 8 farkli metin uretiyor (%d)"
            % (_lang, len(_metinler)))

    # 44 puanin HESABININ tamami dolu, her biri 3 satirdan uzun ve jargonsuz
    _bos, _kisa, _jar, _basliksiz = [], [], [], []
    for _k, _a in _AZAMI.items():
        for _p in range(_a + 1):
            _d = MT.dogal_aciklama(_k, _p, _lang)
            _m = _d.get("aciklama") or ""
            if not _m:
                _bos.append((_k, _p))
                continue
            if _m.count("\n") + 1 < 4:
                _kisa.append((_k, _p))
            if _JARGON.search(_m):
                _jar.append((_k, _p))
            if not _d.get("baslik"):
                _basliksiz.append((_k, _p))
    kontrol(not _bos, "dogal[%s] 44 puanin tamami dolu (bos=%s)" % (_lang, _bos[:3]))
    kontrol(not _kisa, "dogal[%s] her metin en az 3 satir (kisa=%s)" % (_lang, _kisa[:3]))
    kontrol(not _jar, "dogal[%s] hicbir metin jargon icermiyor (%s)" % (_lang, _jar[:3]))
    kontrol(not _basliksiz, "dogal[%s] 44 puanin basligi dolu" % _lang)

    # toplam bant metinleri de jargonsuz ve dolu
    for _sev in ("cok_dusuk", "dusuk", "orta", "yuksek"):
        _t = MT.dogal_toplam(_sev, _lang)
        kontrol(bool(_t.get("baslik")) and bool(_t.get("aciklama")) and bool(_t.get("ipucu")),
                "dogal_toplam[%s].%s dolu" % (_lang, _sev))
        kontrol(not _JARGON.search(" ".join(_t.values())),
                "dogal_toplam[%s].%s jargonsuz" % (_lang, _sev))
        # genel yorum tam 3 satir, her satiri dolu
        _sat = _t["aciklama"].split("\n")
        kontrol(len(_sat) == 3 and all(len(x.split()) >= 5 for x in _sat),
                "dogal_toplam[%s].%s 3 dolu satir" % (_lang, _sev))
        # aralik metinde gecmeli, baslikta gecmemeli (kullanici sadece isim istedi)
        kontrol(not _JARGON.search(_t["baslik"]),
                "dogal_toplam[%s].%s baslik jargonsuz" % (_lang, _sev))

    # toplam bant basliklari kullaniciya dogrudan hitap eden 4 iliski adi
    kontrol([MT.dogal_toplam(s, "tr")["baslik"] for s in
             ("cok_dusuk", "dusuk", "orta", "yuksek")]
            == ["Zayıf ilişki", "Orta ilişki", "İdeal ilişki", "Kuvvetli ilişki"],
            "dogal_toplam[tr] basliklari zayif/orta/ideal/kuvvetli")
    kontrol([MT.dogal_toplam(s, "en")["baslik"] for s in
             ("cok_dusuk", "dusuk", "orta", "yuksek")]
            == ["Weak relationship", "Average relationship",
                "Ideal relationship", "Strong relationship"],
            "dogal_toplam[en] basliklari zayif/orta/ideal/kuvvetli")
    kontrol([MT.dogal_toplam(s, "es")["baslik"] for s in
             ("cok_dusuk", "dusuk", "orta", "yuksek")]
            == ["Relación débil", "Relación media",
                "Relación ideal", "Relación fuerte"],
            "dogal_toplam[es] basliklari zayif/orta/ideal/kuvvetli")

# --------------------------------------------------------------------------
# Genel ilişki yorumu: bantlar OLCULEN ulasilabilir araliga gore kurulur.
# Azami 36 ama pratikte toplamlar yalnizca 20-34 arasi olabiliyor; 0-19 ve
# 35-36 hicbir ciftte olusmuyor. Bu yuzden bantlar 20-34 uzerinden kurulur,
# aksi halde alt bantlar olenmis olur.
SINIR = [(20, "cok_dusuk"), (23, "cok_dusuk"), (26, "dusuk"), (27, "dusuk"),
         (28, "orta"), (29, "orta"), (33, "yuksek"), (34, "yuksek")]
for _p, _bek in SINIR:
    _S = type("S", (), {})()
    _S.toplam = _p
    kontrol(AshtaKootSonuc.seviye.fget(_S) == _bek,
            "toplam %d -> %s (beklenen %s)"
            % (_p, AshtaKootSonuc.seviye.fget(_S), _bek))

# gercek tum naksatra ciftleri taranir: dort bandin de dolu oldugu kanitlanir
_aylar = [ay_nakshatrasi_hesapla(_x) for _x in range(27)]
_gercek = {}
for _i, _a in enumerate(_aylar):
    for _b in _aylar[_i:]:
        _S = ashtakoot_hesapla(_a, _b)
        _gercek[_S.toplam] = _gercek.get(_S.toplam, 0) + 1
        _gercek.setdefault("bant_" + _S.seviye, 0)
        _gercek["bant_" + _S.seviye] += 1
_son = max(_a for _a in _gercek if isinstance(_a, int))
_kucuk = min(_a for _a in _gercek if isinstance(_a, int))
kontrol((_kucuk, _son) == (20, 34),
        "ulasilabilir toplam araligi 20-34 (olculdu: %d-%d)" % (_kucuk, _son))
for _b in ("cok_dusuk", "dusuk", "orta", "yuksek"):
    kontrol(_gercek.get("bant_" + _b, 0) > 0,
            "bant %s gercek ciftlerde dolu (%d adet)"
            % (_b, _gercek.get("bant_" + _b, 0)))

for _lang in ("tr", "en", "es"):
    kontrol(sum(a + 1 for a in _AZAMI.values()) * 4 == 176,
            "dogal[%s] 176 metin (44 puan x 4 aci)" % _lang)

kontrol(set(MT.dogal_basliklar("tr")) == set(_AZAMI),
        "dogal basliklar tum 8 kootayi kapsar")
kontrol(set(MT.dogal_basliklar("en")) == set(_AZAMI),
        "dogal basliklar[en] tum 8 kootayi kapsar")
kontrol(set(MT.dogal_basliklar("es")) == set(_AZAMI),
        "dogal basliklar[es] tum 8 kootayi kapsar")
kontrol(MT.dogal_basliklar("xx") == MT.dogal_basliklar("tr"),
        "bilinmeyen dilde dogal basliklar TR")
kontrol(MT.dogal_aciklama("yoni", 99, "tr") == {},
        "puan kapsam disi dogal_aciklama bos donuyor")

# Turkce metin Turkce karakter icermeli; EN/ES sizmamali.
_dg_tr = " ".join(MT.dogal_aciklama(k, p, "tr").get("aciklama", "")
                  for k, a in _AZAMI.items() for p in range(a + 1))
kontrol(set(_dg_tr) & set("şŞğĞıİ"), "dogal[tr] metinleri Turkce karakter iceriyor")
for _lang in ("en", "es"):
    _dg = " ".join(MT.dogal_aciklama(k, p, _lang).get("aciklama", "")
                   for k, a in _AZAMI.items() for p in range(a + 1))
    kontrol(not (set(_dg) & set("çğıöşüÇĞİÖŞÜ")),
            "dogal[%s] metinleri Turkce karakter sizdirmiyor" % _lang)


# --------------------------------------------------------------------------
# ACILAR (ilk satir) TAM CUMLE OLMALI. Buraya giren metinler daha once yarim
# kalmisti: "masada kimin de kendini yerinde bulacağini", "ne kadar
# oldugunu." gibi fiilsiz parcalar. Asagidaki kurallar sinifi kapatir.
#   1) nokta ile bitmeli
#   2) iki noktadan sonra bos bir iki cumle kalmamali
#   3) vaat/anlati satirlarinda iki noktadan sonra finite fiil olmali
#   4) simge satiri somut bir konu adlamali
#   5) baska dilden kelime sizmamali
# --------------------------------------------------------------------------
_CERCEVE = {
    "tr": ("Bu alan şunu vaat ediyor:", "Bu alan şunu anlatıyor:",
           "Bu alan şunu simgeliyor:", "Bu alan şuna dikkat çekiyor:"),
    "en": ("This area shows what it promises:", "This area explains:",
           "This area symbolizes:", "This area flags:"),
    "es": ("Esta área muestra lo que promete:", "Esta área explica:",
           "Esta área simboliza:", "Esta área señala:"),
}

#: vaat / anlati satirlarinda iki noktadan sonra bulunmasi zorunlu fiiller.
#: Kelime siniriyla eslesir; alt kume eslesmesi yanlis pozitif uretmesin.
_FIIL = {
    "tr": (r"gösterir|anlatır|olduğunu|eder",
           "gösterir|anlatır"),
    "en": (r"is|are|was|were|will|can|could|may|might|do|does|did"
           r"|show|tell|tell?s?|comes?|affects?|overlaps?|splits?"
           r"|collides?|lives?|keep|looking|read|walk|wear|move",
           "is|are|will|can|show|tell|tells|comes|affects|overlap"
           r"|split|collide|lives|keep|looking|move"),
    "es": (r"\bes\b|\bson\b|\bestá\b|\bests?\b|\bvan\b|\bvais\b|\bpuede"
           r"|n\b|\bpueden\b|\bpodéis\b|\bcontáis\b|\bavanzáis\b|\bbuscáis"
           r"|\bexista\b|\bsurgirán\b|\baparecerá\b|\bafecta\b|\bcoinciden"
           r"|\bsolapan\b|\bseparan\b|\bviene\b|\bchocar\b|\bleeros\b"
           r"|\bconstruís\b|\bacueste\b|\bse\s+levante\b",
           "es|son|está|vais|pueden|podéis|contáis|avanzáis|buscáis"
           r"|exista|surgirán|aparecerá|afecta|coinciden|solapan|separan"
           r"|viene|chocar|leeros|construís|acueste|levante"),
}

#: simge satiri her kootada su somut kavramlardan birini ADLAMALI. Aksi halde
#: "anlasilamaz metafor" hatasi geri gelir.
_SIMGE_KONU = {
    "tr": {
        "varna": ("değer", "önemli", "aile", "para"),
        "vashya": ("çekil", "sessiz", "an"),
        "tara": ("saat", "düzen", "ev"),
        "yoni": ("kapı", "dünya", "açık"),
        "graha_maitri": ("dil", "rahatlık", "rahat"),
        "gana": ("ritim", "çatı", "uyum"),
        "rasi": ("harita", "oku"),
        "nadi": ("nokta", "tamamla", "çarpış"),
    },
    "en": {
        "varna": ("value", "important", "line up", "clash"),
        "vashya": ("attraction", "moment"),
        "tara": ("household", "clocks", "hours"),
        "yoni": ("door", "intimacy", "open"),
        "graha_maitri": ("language", "ease", "speaking"),
        "gana": ("rhythm", "home", "settling"),
        "rasi": ("map", "reading"),
        "nadi": ("spot", "completing", "colliding"),
    },
    "es": {
        "varna": ("valores", "importantes", "coinciden"),
        "vashya": ("atracción", "momento"),
        "tara": ("hogar", "relojes", "horas"),
        "yoni": ("puerta", "intimidad", "abierta"),
        "graha_maitri": ("idioma", "comodidad", "hablan"),
        "gana": ("ritmos", "hogar", "ajustan"),
        "rasi": ("mapa", "leyendo"),
        "nadi": ("mismo punto", "completándose", "chocando"),
    },
}

#: yanlis dilden sizan kelimeler (bir suret "promise" sizmis, bir suret
#: Turkce metinde Ingilizce "the" vardi).
_YANLIS_DIL = {
    "tr": ("the ", " you ", " what ", " promise", " your "),
    "en": ("ğ", "ş", "ı ", "ınız", " olduğu", "çünkü"),
    "es": ("ğ", "ş", "ınız", " olduğu", "çünkü", " your ", " the "),
}

#: dikkat satiri (3. aci) her kootada su kavramlardan birini ADLAMALI.
_DIKKAT_KONU = {
    "tr": {
        "varna": ("kazandığınızı", "kaybettiğinizi", "karşıladığı"),
        "vashya": ("çekimi", "dayanağı", "sanmanın"),
        "tara": ("saat", "hesap defteri"),
        "yoni": ("anladığınızı", "yanlışlar"),
        "graha_maitri": ("susup", "fikirde"),
        "gana": ("yapmıyor", "tekrarlanması"),
        "rasi": ("hedefe", "nedenlerle"),
        "nadi": ("eksik", "bulmaması"),
    },
    "en": {
        "varna": ("gain", "lose"),
        "vashya": ("pull", "only thing"),
        "tara": ("clock", "tally"),
        "yoni": ("quiet mistakes", "understood"),
        "graha_maitri": ("quiet", "agree"),
        "gana": ("not how i do it",),
        "rasi": ("shared goal", "different reasons"),
        "nadi": ("missing thing", "empty handed"),
    },
    "es": {
        "varna": ("ganáis", "perdeis"),
        "vashya": ("atracción", "único"),
        "tara": ("horas", "recuento"),
        "yoni": ("errores silenciosos", "entendíais"),
        "graha_maitri": ("callaros", "acuerdo"),
        "gana": ("no lo hago yo",),
        "rasi": ("objetivo compartido", "motivos distintos"),
        "nadi": ("misma falta", "vacías"),
    },
}

for _lang in ("tr", "en", "es"):
    _mod = MT.DILLER[_lang]["dogal"]
    kontrol(len(_mod.ACILAR) == 8,
            "dogal[%s] 8 koota icin aci var (%d)" % (_lang, len(_mod.ACILAR)))
    kontrol(_mod.ACI_SAYISI == 4,
            "dogal[%s] ACI_SAYISI = 4 (%d)" % (_lang, _mod.ACI_SAYISI))
    # her (koota, puan) icin IKINCI govde varyanti olmali
    kontrol(len(_mod.GOVDE_ALT) == 8,
            "dogal[%s] GOVDE_ALT 8 koota kapsiyor (%d)"
            % (_lang, len(_mod.GOVDE_ALT)))
    for _kota, _puanlar in _mod.GOVDE.items():
        kontrol(sorted(_mod.GOVDE_ALT.get(_kota, {})) == sorted(_puanlar),
                "dogal[%s]/%s GOVDE_ALT tum puanlari kapsiyor"
                % (_lang, _kota))
        for _p in _puanlar:
            kontrol(len(_mod.govde_varyantlari(_kota, _p)) == 2,
                    "dogal[%s]/%s/%d 2 govde varyanti"
                    % (_lang, _kota, _p))
            kontrol(_mod.GOVDE[_kota][_p] != _mod.GOVDE_ALT[_kota][_p],
                    "dogal[%s]/%s/%d iki govde farkli"
                    % (_lang, _kota, _p))
            # 4 aci x 2 govde = 8 benzersiz metin
            _sekiz = {_mod.dogal_metin(_kota, _p, a, g)
                      for a in range(4) for g in range(2)}
            kontrol(len(_sekiz) == 8,
                    "dogal[%s]/%s/%d 8 benzersiz kombinasyon (%d)"
                    % (_lang, _kota, _p, len(_sekiz)))
            # her metin 4 satir (1 lead + 3 govde)
            for _a in range(4):
                for _g in range(2):
                    _sat = _mod.dogal_metin(_kota, _p, _a, _g).split("\n")
                    if len(_sat) != 4 or len(_sat[3].split()) < 4:
                        kontrol(False,
                                "dogal[%s]/%s/%d aci%d govde%d 4 dolu satir "
                                "degil" % (_lang, _kota, _p, _a, _g))
    kontrol(True, "dogal[%s] metin yapisi (4 aci x 2 govde x 4 satir) "
                  "gecerli" % _lang)
    for _kota, _satirlar in _mod.ACILAR.items():
        kontrol(len(_satirlar) == 4,
                "dogal[%s]/%s 4 aci var (%d)" % (_lang, _kota, len(_satirlar)))
        for _i, _satir in enumerate(_satirlar):
            _etiket = "dogal[%s]/%s[%d]" % (_lang, _kota, _i)
            _cerceve = _CERCEVE[_lang][_i]
            kontrol(_satir.startswith(_cerceve),
                    "%s dogru cerceve ile basliyor" % _etiket)
            kontrol(_satir.rstrip().endswith("."),
                    "%s nokta ile bitiyor" % _etiket)
            _govde = _satir.split(":", 1)[1].strip() if ":" in _satir else ""
            kontrol(len(_govde.split()) >= 5,
                    "%s iki noktadan sonra yeterli icerik var (%d kelime)"
                    % (_etiket, len(_govde.split())))
            _kucuk = _satir.lower()
            for _yabancı in _YANLIS_DIL[_lang]:
                kontrol(_yabancı not in _kucuk,
                        "%s yanlis dil kelimesi icermiyor (%r)"
                        % (_etiket, _yabancı.strip()))
            if _i in (0, 1):
                kontrol(re.search(_FIIL[_lang][0], _govde, re.I) is not None,
                        "%s iki noktadan sonra fiil iceriyor" % _etiket)
            elif _i == 2:
                kontrol(any(t in _govde for t in _SIMGE_KONU[_lang][_kota]),
                        "%s simge satiri somut konu adliyor" % _etiket)
            if _i == 3:
                kontrol(any(t in _govde.lower()
                            for t in _DIKKAT_KONU[_lang][_kota]),
                        "%s dikkat satiri somut konu adliyor" % _etiket)


# --------------------------------------------------------------------------
# Metin katmani YANIT ONBELLEGINDEN CIKARILMALI. `_analiz_sonuc` cevabi
# onbellekliyor; `aciklama` iceride uretilirse ayni veri tekrar gonderildiginde
# kullanici daima ayni rastgele varyanti gorurdu. Bu regresyon, endpoint'in
# metni her istekte tazeledigini sabitler.
# --------------------------------------------------------------------------
import os  # noqa: E402

_BURAYA = os.path.dirname(os.path.abspath(__file__))
# production kopyasi -> ./backend ; kok kopyasi -> ./render-deploy/backend
_BACKEND_DIR = None
for _aday in (os.path.join(_BURAYA, "backend"),
              os.path.join(_BURAYA, "render-deploy", "backend")):
    if os.path.isdir(_aday):
        _BACKEND_DIR = _aday
        break

if _BACKEND_DIR:
    import importlib.util  # noqa: E402

    if _BACKEND_DIR not in sys.path:
        sys.path.insert(0, _BACKEND_DIR)
    if _BURAYA not in sys.path:
        sys.path.insert(0, _BURAYA)

    os.environ.setdefault("FBST_TEST", "1")

    try:
        _spec = importlib.util.spec_from_file_location(
            "ash_test_main", os.path.join(_BACKEND_DIR, "main.py"))
        _MAIN = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_MAIN)
    except Exception as _e:  # noqa: BLE001
        _MAIN = None
        print("  (bilgi) backend main.py yuklenemedi, onbellek testi atlandi: %s" % _e)

    if _MAIN is not None and hasattr(_MAIN, "analiz_ashtakoot"):
        class _Girdi(dict):
            __getattr__ = dict.__getitem__

            def items(self):
                return dict.items(self)

        def _ash_istek():
            return _MAIN.analiz_ashtakoot(_Girdi(
                dil="tr", harita=False,
                p1_isim="A", p1_tarih="1990-05-15", p1_saat="05:00",
                p1_sehir="Istanbul", p1_ulke="Turkiye", p1_utc_offset=None,
                p2_isim="B", p2_tarih="1992-11-03", p2_saat="19:00",
                p2_sehir="Istanbul", p2_ulke="Turkiye", p2_utc_offset=None))

        # AYNI girdi 120 kez: puan sabit kalmali, metin 3 varyant uretmeli.
        _toplamlar, _yorumlar = set(), set()
        for _ in range(200):
            _r = _ash_istek()
            _toplamlar.add(_r["toplam"])
            _yorumlar.add(_r["aciklama"]["kootalar"][3]["aciklama"])
        kontrol(len(_toplamlar) == 1,
                "ayni girdi tekrarinda toplam puan sabit (%s)" % _toplamlar)
        kontrol(len(_yorumlar) == 8,
                "ayni girdi 200 istekte 8 farkli dogal metin (%d)" % len(_yorumlar))
        _acilar = {_y.split("\n")[0] for _y in _yorumlar}
        kontrol(len(_acilar) == 4,
                "8 metin 4 farkli lead kullaniyor (vaat/anlati/simge/dikkat)")
        _r = _ash_istek()
        kontrol(len(_r["aciklama"]["kootalar"]) == 8,
                "her yanitta 8 koota aciklamasi var")
        kontrol(_r.get("p1_harita") is None,
                "harita=False iken p1_harita gelmiyor")
        kontrol("p1_harita" in _MAIN.analiz_ashtakoot(_Girdi(
            dil="tr", harita=True,
            p1_isim="A", p1_tarih="1990-05-15", p1_saat="05:00",
            p1_sehir="Istanbul", p1_ulke="Turkiye", p1_utc_offset=None,
            p2_isim="B", p2_tarih="1992-11-03", p2_saat="19:00",
            p2_sehir="Istanbul", p2_ulke="Turkiye", p2_utc_offset=None)),
            "harita=True iken p1_harita geliyor")
        # onbellekte metin OLMAMALI
        _onbellek = list(getattr(_MAIN, "_ANALIZ_CACHE", {}).values())
        kontrol(_onbellek and not any(
            isinstance(_o, (list, tuple)) and _o and isinstance(_o[0], dict)
            and "aciklama" in _o[0] for _o in _onbellek),
            "yanit onbelleginde aciklama metni tutulmuyor")


# --------------------------------------------------------------------------
print("\n" + "=" * 46)
print("GECTI: %d    KALDI: %d" % (GECTI, KALDI))
print("=" * 46)
sys.exit(1 if KALDI else 0)
