# -*- coding: utf-8 -*-
"""Streamlit AppTest ile cikti dili secicisini uctan uca dogrular.

Her dil icin: uygulama render edilir, secici dogrudan session_state
uzerinden degistirilir, uygulama yeniden calistirilir ve oturum
durumu + i18n katmaninin senkron oldugu gorulur.
"""
import sys

from streamlit.testing.v1 import AppTest

UYGULAMA = "app.py"
KUTU = "cikti_dili_kutu"
AD2KOD = {"🇹🇷 Türkçe": "tr", "🇬🇧 English": "en", "🇪🇸 Español": "es"}
HATA = []


def kontrol(mesaj):
    HATA.append(mesaj)


def state_al(at, anahtar):
    try:
        return at.session_state[anahtar]
    except Exception:
        return None


for ad, kod in AD2KOD.items():
    at = AppTest.from_file(UYGULAMA, default_timeout=180)
    at.run()
    if at.exception:
        kontrol("%s: ilk render exception -> %s" % (kod, at.exception[0].message))

    at.session_state[KUTU] = ad
    at.run()
    if at.exception:
        kontrol("%s: dil degisiminden sonra exception -> %s"
                % (kod, at.exception[0].message))

    st_dil = state_al(at, "cikti_dili")
    ash_dil = state_al(at, "ashtakoot_lang")
    print("  secildi %-4s -> cikti_dili=%r ashtakoot_lang=%r"
          % (ad, st_dil, ash_dil))

    if st_dil != kod:
        kontrol("%s: session_state['cikti_dili']=%r olmali" % (kod, st_dil))
    if ash_dil != kod:
        kontrol("%s: session_state['ashtakoot_lang']=%r olmali" % (kod, ash_dil))

    # Not: i18n.get_lang() thread-local oldugu icin AppTest'in script
    # thread'inde ayarlanan dil burada (ana thread) gorunmez; dogrulama
    # oturum durumu uzerinden yapilir. Ayrica metin katalogu gercekten
    # farkli mi, kontrol edilir.
    import sinastri_metin
    if kod == "tr":
        continue
    if sinastri_metin.m(kod) == sinastri_metin.m("tr"):
        kontrol("%s: sinastri metin katalogu TR ile ayni cikti" % kod)

# --- ayrica secici sunumunu dogrula (salt-okunur agac gezintisi) ---
at = AppTest.from_file(UYGULAMA, default_timeout=180)
at.run()
bulundu = False
for sb in at.sidebar:
    if sb.key == KUTU:
        adlar = {str(o) for o in sb.options}
        print("  secici secenekleri = %s" % sorted(adlar))
        if adlar != set(AD2KOD):
            kontrol("beklenmeyen secenekler -> %s" % sorted(adlar))
        bulundu = True
if not bulundu:
    kontrol("'%s' secicisi sidebar'da bulunamadi" % KUTU)

if HATA:
    print("HATA (%d):" % len(HATA))
    for h in HATA:
        print("  -", h)
    sys.exit(1)
print("GECTI: cikti dili secicisi 3 dilde calisiyor, i18n ile senkron")
