# -*- coding: utf-8 -*-
"""app.py icindeki gercek sinastri_hesapla fonksiyonunu uctan uca calistirir.

Sinastri motoru sinifini app.py'den AST ile kirpar, gerekli modul
degiskenlerini kurar ve ucu dilde cikti uretir. Streamlit'siz calisir.
"""
import ast
import io
import os
import re
import sys

KOK = os.path.dirname(os.path.abspath(__file__))
if KOK not in sys.path:
    sys.path.insert(0, KOK)

APP = os.path.join(KOK, "app.py")

# ------------------------------------------------------------ yardimcilar
def _yukle_ilk(dosya):
    import importlib.util as iu
    yol = os.path.join(KOK, dosya)
    sp = iu.spec_from_file_location("_h_" + dosya, yol)
    m = iu.module_from_spec(sp)
    sp.loader.exec_module(m)
    for k, v in vars(m).items():
        if isinstance(v, dict) and not k.startswith("_"):
            return v
    return {}


def _yukle_adli(dosya, ad):
    import importlib.util as iu
    yol = os.path.join(KOK, dosya)
    sp = iu.spec_from_file_location("_hn_" + ad + "_" + dosya, yol)
    m = iu.module_from_spec(sp)
    sp.loader.exec_module(m)
    v = getattr(m, ad, None)
    return v if isinstance(v, dict) else {}


# ------------------------------------------------- app.py'den parca calistir
src = io.open(APP, encoding="utf-8").read()
lines = src.split("\n")
tree = ast.parse(src)

# sinastri_hesapla icindeki govdeye ait AST parcalarini topla
fn = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "sinastri_hesapla":
        fn = node
assert fn is not None, "sinastri_hesapla bulunamadi"


def _yig(bas, bit):
    # sinastri_hesapla bir sinif metodu oldugu icin 4 bosluk girintilidir;
    # modul seviyesine cekmeden exec edebilmek icin dedent uygulanir.
    import textwrap
    return textwrap.dedent("\n".join(lines[bas - 1:bit]))


def _fonksiyon_olustur(ad, *bagimli):
    """app.py icindeki bir fonksiyonu bagimli fonksiyonlarla birlikte
    gercek bir fonksiyon nesnesine cevirir."""
    parcalar = []
    for ad2 in list(bagimli) + [ad]:
        hedef = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == ad2:
                hedef = node
                break
        assert hedef is not None, "%s bulunamadi" % ad2
        parcalar.append(_yig(hedef.lineno, hedef.end_lineno))
    ns = {}
    exec("import swisseph as swe\n"
         "from datetime import datetime, date\n"
         "import re\n" + "\n\n".join(parcalar), ns)
    return ns[ad]


def _mod_degisken(ad):
    """app.py'deki modul seviyesi bir dict/list degiskenini deger olarak alir."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == ad:
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        pass
    raise AssertionError("%s bulunamadi" % ad)


get_safe_flags = _fonksiyon_olustur("get_safe_flags")
asteroit_tahmini_derece = _fonksiyon_olustur("asteroit_tahmini_derece")
sinastri_hesapla = _fonksiyon_olustur("sinastri_hesapla",
                                      "get_safe_flags", "asteroit_tahmini_derece")

# ------------------------------------------------- sinastri_hesapla icin stub
import i18n as _i18n
import sinastri_metin as _sinastri_metin
from datetime import date, datetime


class _Fake:
    """sinastri_hesapla'nin self'e ihtiyaç duyduğu alanlar."""

    def __init__(self, mod):
        self.mod = mod
        self.p1 = date(1990, 8, 22)
        self.p2 = date(1985, 4, 15)
        self.p1_isim = "ALFA"
        self.p2_isim = "BETA"
        self.enlem = 39.9334
        self.boylam = 32.8597
        self.city = "Ankara"
        self.country = "Türkiye"

    sinastri_hesapla = sinastri_hesapla


# ------------------------------------------------------ modul degiskenleri
def _langdict(tr, en, es):
    return _i18n.LangDict(tr, en, es)


OZEL = _langdict(_yukle_ilk("FBST_SINASTRI_OZEL.py"),
                 _yukle_ilk("FBST_SINASTRI_OZEL_EN.py"),
                 _yukle_ilk("FBST_SINASTRI_OZEL_ES.py"))
EBEV = _langdict(_yukle_ilk("FBST_YORUMLAR_EBEVEYN.py"),
                 _yukle_ilk("FBST_YORUMLAR_EBEVEYN_EN.py"),
                 _yukle_ilk("FBST_YORUMLAR_EBEVEYN_ES.py"))
REC = _langdict(_yukle_adli("sifa_receteler.py", "FBST_RECETELER"),
                _yukle_adli("sifa_receteler_en.py", "FBST_RECETELER_EN"),
                _yukle_adli("sifa_receteler_es.py", "FBST_RECETELER_ES"))
REC_E = _langdict(_yukle_adli("sifa_receteler.py", "FBST_RECETELER_EBEVEYN"),
                  _yukle_adli("sifa_receteler_en.py", "FBST_RECETELER_EBEVEYN_EN"),
                  _yukle_adli("sifa_receteler_es.py", "FBST_RECETELER_EBEVEYN_ES"))

# fonksiyonun global isim alanina sokulacaklar
import swisseph as _swe
import swisseph as swe
_F = _Fake.__dict__["sinastri_hesapla"].__globals__
_F.update({
    "FBST_SINASTRI_OZEL": OZEL,
    "FBST_YORUMLAR_EBEVEYN": EBEV,
    "FBST_RECETELER": REC,
    "FBST_RECETELER_EBEVEYN": REC_E,
    "get_safe_flags": get_safe_flags,
    "asteroit_tahmini_derece": asteroit_tahmini_derece,
    "ASTEROIT_MEAN_ELEMENTS": _mod_degisken("ASTEROIT_MEAN_ELEMENTS"),
    "_i18n": _i18n,
    "_sinastri_metin": _sinastri_metin,
})
# AKTIF_DIL / _aktif_dil kullanimini basitlestir
_F["_aktif_dil"] = lambda: _i18n.get_lang()
_F["AKTIF_DIL"] = "tr"

# --------------------------------------------------------------- kontroller
TR_ONLY = re.compile(r"[çğıöşüÇĞİÖŞÜ]|(?<![a-zA-Z])[ıİ](?![a-zA-Z])")
YASAK_TR = ["Mühür", "Dersi", "Şifası", "Teması", "Enerjisi", "Kavuşum",
            "Kare", "Üçgen", "Sekstil", "Karşıt", "Öneri", "Majör",
            "saptanmadı", "gerektirmemektedir", "Doğal akışınızda",
            "KADERSEL", "REÇETELERİ", "ÖNERİLERİ", "temel yapıları",
            "Pedagojik Protokol", "yer alan", "birleşerek"]

hata = []
ozet = {}
for d in ("tr", "en", "es"):
    _i18n.set_lang(d)
    SM = _sinastri_metin.m(d)
    for mod in ("es_sevgili", "ebeveyn_cocuk"):
        html = _Fake(mod).sinastri_hesapla(sessiz=True)
        etiket = "%s/%s" % (d, mod)
        if len(html) < 400:
            hata.append("%s: cikti cok kisa (%d)" % (etiket, len(html)))
        ozet[etiket] = len(html)
        # doldurulmamis sablon kaldi mi?
        for ph in re.findall(r"\{(\w+)\}", html):
            hata.append("%s: doldurulmamis sablon %s" % (etiket, ph))
        # beklenen basliklar
        beklenen = (SM["baslik_dersler"] if mod == "ebeveyn_cocuk"
                    else SM["baslik_receteler"])
        if beklenen not in html:
            hata.append("%s: baslik bulunamadi -> %s" % (etiket, beklenen))
        # etiketler: hangi etiket hangi modda gorunur
        if mod == "ebeveyn_cocuk":
            beklenen_etiketler = [SM["ders"]]
        else:
            # "temas" yalnizca ozel yorum bulunamayan (ACI_DINAMIKLERI) dali
            # icin kullanilir; 210 ciftlik sozluk her aciyi karsiladigi icin
            # bu veride gorunmeyebilir.
            beklenen_etiketler = [SM["sifa"], SM["muhur"]]
        for et in beklenen_etiketler:
            if et not in html:
                hata.append("%s: etiket bulunamadi -> %s" % (etiket, et))
        # yanlis mod etiketi sizmasin
        yasak_etiket = SM["sifa"] if mod == "ebeveyn_cocuk" else SM["ders"]
        if yasak_etiket in html:
            hata.append("%s: yanlis mod etiketi sizdi -> %s" % (etiket, yasak_etiket))
        # aci adlari
        for aci in (0, 180, 90, 120, 60):
            if SM["acilar"][aci]["isim"] not in html:
                hata.append("%s: aci adi yok -> %s" % (etiket, SM["acilar"][aci]["isim"]))
        # EN/ES: turkce sizinti ve yasakli sozcuk
        if d != "tr":
            m = TR_ONLY.search(html)
            if m:
                i = max(0, m.start() - 60)
                hata.append("%s: TR karakteri %r -> ...%s..."
                            % (etiket, m.group(), html[i:m.end() + 40]))
            for y in YASAK_TR:
                if y in html:
                    i = html.find(y)
                    hata.append("%s: yasakli %r -> ...%s..."
                                % (etiket, y, html[max(0, i - 50):i + 50]))
        # HTML etiketleri dengeli mi?
        if html.count("<p ") != html.count("</p>"):
            hata.append("%s: <p> dengesiz (%d/%d)"
                        % (etiket, html.count("<p "), html.count("</p>")))

        # PDF'teki aci sayim mantigi (app.py _aci_say) sifir vermemeli
        if mod == "es_sevgili":
            say = {}
            for aci in (0, 90, 120, 180, 60):
                ad = SM["acilar"][aci]["isim"]
                say[ad] = len(re.findall(re.escape(ad), html))
            print("  aci sayimi[%s] = %s" % (d, say))
            if not any(say.values()):
                hata.append("%s: PDF aci sayimi tum sifir" % etiket)

print("ucu dil x iki mod cikti uzunlugu:")
for k, v in sorted(ozet.items()):
    print("   %-22s %6d karakter" % (k, v))
if hata:
    print("HATA (%d):" % len(hata))
    for h in hata[:30]:
        print("  -", h)
    sys.exit(1)
print("GECTI: sinastri_hesapla gercek fonksiyonu 3 dilde temiz")
