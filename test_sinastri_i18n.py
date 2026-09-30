# -*- coding: utf-8 -*-
"""Sinastri metin zincirini TR/EN/ES icinde uctan uca dener (Streamlit'siz)."""
import io, os, re, sys, importlib.util as iu

KOK = os.path.dirname(os.path.abspath(__file__))
if KOK not in sys.path:
    sys.path.insert(0, KOK)

import i18n
import sinastri_metin as sm


def yukle_adli(dosya, ad):
    yol = os.path.join(KOK, dosya)
    sp = iu.spec_from_file_location("_t_" + ad + "_" + dosya, yol)
    m = iu.module_from_spec(sp)
    sp.loader.exec_module(m)
    v = getattr(m, ad, None)
    return v if isinstance(v, dict) else {}


def yukle_ilk(dosya):
    yol = os.path.join(KOK, dosya)
    sp = iu.spec_from_file_location("_t_" + dosya, yol)
    m = iu.module_from_spec(sp)
    sp.loader.exec_module(m)
    for k, v in vars(m).items():
        if isinstance(v, dict) and not k.startswith("_"):
            return v
    return {}


def langdict(tr_d, en_d, es_d):
    return i18n.LangDict(tr_d, en_d, es_d)


OZEL = langdict(yukle_ilk("FBST_SINASTRI_OZEL.py"),
                yukle_ilk("FBST_SINASTRI_OZEL_EN.py"),
                yukle_ilk("FBST_SINASTRI_OZEL_ES.py"))
EBEV = langdict(yukle_ilk("FBST_YORUMLAR_EBEVEYN.py"),
                yukle_ilk("FBST_YORUMLAR_EBEVEYN_EN.py"),
                yukle_ilk("FBST_YORUMLAR_EBEVEYN_ES.py"))
REC = langdict(yukle_adli("sifa_receteler.py", "FBST_RECETELER"),
               yukle_adli("sifa_receteler_en.py", "FBST_RECETELER_EN"),
               yukle_adli("sifa_receteler_es.py", "FBST_RECETELER_ES"))
REC_E = langdict(yukle_adli("sifa_receteler.py", "FBST_RECETELER_EBEVEYN"),
                 yukle_adli("sifa_receteler_en.py", "FBST_RECETELER_EBEVEYN_EN"),
                 yukle_adli("sifa_receteler_es.py", "FBST_RECETELER_EBEVEYN_ES"))

# Turkce sizinti tespiti: Turkce'ye ozgu karekterler
TR_ONLY = re.compile(r"[çğıöşüÇĞİÖŞÜ]|(?<![a-zA-Z])[ıİ](?![a-zA-Z])")
# Ceviri metinlerinde yasakli TR sozcukleri (yer tutucu disi gercek sizinti)
YASAK = [
    "Mühür", "Dersi", "Şifası", "Teması", "Enerjisi", "Kavuşum", "Kare",
    "Üçgen", "Sekstil", "Karşıt", "Öneri", "Güçlü Birleşme", "Majör",
    "saptanmadı", "gerektirmemektedir", "Doğal akışınızda",
    "KADERSEL", "REÇETELERİ", "ÖNERİLERİ", "temel yapıları", "enerji",
    "Pedagojik Protokol", "olan", "yapıları",
]

hata = []
sayac = {}


def kontrol(etiket, metin):
    sayac[etiket] = sayac.get(etiket, 0) + 1
    if "{p1}" in metin or "{p2}" in metin or "{konu}" in metin \
            or "{g1_burc}" in metin or "{g1_ev}" in metin or "{anlam1}" in metin:
        hata.append("%s: doldurulmamis sablon kaldi -> %s" % (etiket, metin[:90]))
    if "{" in metin and "}" in metin:
        kalan = re.findall(r"\{(\w+)\}", metin)
        if kalan:
            hata.append("%s: beklenmeyen sablon %s -> %s" % (etiket, kalan, metin[:90]))


for d in ("tr", "en", "es"):
    i18n.set_lang(d)
    SM = sm.m(d)
    kontrol("baslik_dersler", SM["baslik_dersler"])
    kontrol("baslik_receteler", SM["baslik_receteler"])
    kontrol("bos_mesaj", SM["bos_mesaj"])
    kontrol("recete_yok", SM["recete_yok"])

    for mod in ("ebeveyn", "normal"):
        # aci turu + etki
        for aci in (0, 180, 90, 120, 60):
            kontrol("acilar[%s].isim" % aci, SM["acilar"][aci]["isim"])
            kontrol("acilar[%s].etki" % aci, SM["acilar"][aci]["etki"])
        # gezegen anlamlari + aciklama sablonu
        for g, anlam in SM["gezegen"][mod].items():
            kontrol("gezegen/%s/%s" % (mod, g), anlam)
        for aci in (0, 180, 90, 120, 60):
            v = SM["dinamik"][mod][aci]
            kontrol("dinamik/%s/%s/baslik" % (mod, aci), v["baslik"])
            for g, konu in v["konu_map"].items():
                kontrol("dinamik/%s/%s/konu/%s" % (mod, aci, g), konu)
            d1 = SM["gezegen"][mod]["Güneş"]
            d2 = SM["gezegen"][mod]["Ay"]
            metin = v["aciklama"].format(p1="ALFA", p2="BETA",
                                         anlam1=d1, anlam2=d2,
                                         konu=v["konu_map"]["Mars"])
            kontrol("dinamik/%s/%s/aciklama" % (mod, aci), metin)
            if d != "tr" and TR_ONLY.search(metin):
                hata.append("TR sizinti aciklama %s/%s: %s" % (mod, aci, metin[:90]))

    # ozel yorumlar: 5 sanat acisi x ornek planet ciftleri
    ornek = [("Güneş", "Ay"), ("Venüs", "Mars"), ("Merkür", "Plüton"),
             ("Chiron", "Juno"), ("Amor", "Psyche")]
    for aci in (0, 180, 90, 120, 60):
        for g1, g2 in ornek:
            for sozluk, ad in ((OZEL, "ozel"), (EBEV, "ebeveyn")):
                k1, k2 = "%s-%s" % (g1, g2), "%s-%s" % (g2, g1)
                if k1 in sozluk and aci in sozluk[k1]:
                    ham = sozluk[k1][aci]
                elif k2 in sozluk and aci in sozluk[k2]:
                    ham = sozluk[k2][aci]
                else:
                    continue
                m = ham.format(p1="ALFA", p2="BETA", g1=i18n.pdf_label(g1),
                               g2=i18n.pdf_label(g2),
                               g1_burc=i18n.pdf_label("Boğa"),
                               g2_burc=i18n.pdf_label("Akrep"),
                               g1_ev=3, g2_ev=9)
                kontrol("%s/%s-%s-%s" % (ad, g1, g2, aci), m)
                if d != "tr" and TR_ONLY.search(m):
                    hata.append("TR sizinti %s %s-%s-%s: %s" % (d, ad, g1, g2, m[:90]))

    # receteler
    for kaynak, ad in ((REC, "recete"), (REC_E, "recete_ebeveyn")):
        for k in list(kaynak.keys())[:60]:
            m = kaynak[k]
            kontrol("%s/%s" % (ad, k), m)
            if d != "tr" and TR_ONLY.search(m):
                hata.append("TR sizinti %s %s: %s" % (ad, k, m[:90]))

    # EN/ES icin yasakli sozcuk taramasi (orneklemeli)
    if d != "tr":
        ornek_metin = []
        for g, a in SM["gezegen"]["normal"].items():
            ornek_metin.append(a)
        for mod in ("ebeveyn", "normal"):
            for aci in SM["dinamik"][mod]:
                v = SM["dinamik"][mod][aci]
                ornek_metin.append(v["baslik"])
                ornek_metin.extend(v["konu_map"].values())
        ornek_metin.append(SM["baslik_receteler"])
        ornek_metin.append(SM["recete_yok"])
        for k in list(OZEL.keys())[:40]:
            ornek_metin.append(OZEL[k][0])
        for k in list(REC.keys())[:40]:
            ornek_metin.append(REC[k])
        for m in ornek_metin:
            for y in YASAK:
                if y in m:
                    hata.append("yasakli sozcuk %r [%s]: %s" % (y, d, m[:90]))

print("kontrol edilen metin:", sum(sayac.values()))
print("kume TR/EN/ES esitligi:", set(OZEL.keys()) == set(yukle_ilk("FBST_SINASTRI_OZEL_EN.py").keys())
      == set(yukle_ilk("FBST_SINASTRI_OZEL_ES.py").keys()))
if hata:
    print("HATA (%d):" % len(hata))
    for h in hata[:40]:
        print("  -", h)
    sys.exit(1)
print("GECTI: sinastri metin zinciri 3 dilde temiz")
