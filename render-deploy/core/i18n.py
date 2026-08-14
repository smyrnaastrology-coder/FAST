"""FBST i18n katmani - istek bazli (thread-local) aktif dil + sozluk proxy."""

import os
import json
import threading

_LANG = threading.local()


def set_lang(lang):
    """Aktif cikti dilini ayarlar (tr/en; digerleri tr'ye duser)."""
    _LANG.lang = "en" if lang == "en" else "tr"


def get_lang():
    """Thread-local aktif dili doner (varsayilan: tr)."""
    return getattr(_LANG, "lang", "tr")


# ── Resmi terminoloji: fast_glossary.json (TR -> EN) ──
# Kastan torunlarıyla yuklenir; tum PDF/UI etiketleri buradan beslenir.
_GLOSSARY = {}
try:
    _glossary_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fast_glossary.json")
    if os.path.exists(_glossary_path):
        with open(_glossary_path, encoding="utf-8") as _f:
            _raw = json.load(_f)
        for _cat in ("brand", "concepts", "planets", "signs", "elements", "modes", "structural"):
            for _k, _v in (_raw.get(_cat) or {}).items():
                _GLOSSARY[_k] = _v
except Exception:
    _GLOSSARY = {}


def pdf_label(tr_text):
    """PDF yapisal etiketi aktif dile cevirir (bilinmeyen TR kalir)."""
    if get_lang() != "en":
        return tr_text
    return _GLOSSARY.get(tr_text, tr_text)


class LangDict(dict):
    """TR sozlugun EN kopyasini 'en' aktifken donduren dict proxy.

    Anahtarlar ayni olmalidir; EN'de olmayan anahtar TR'ye duser.
    """

    def __init__(self, data, en_data=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update(data or {})
        self._en = en_data or {}

    def __getitem__(self, key):
        if get_lang() == "en":
            val = self._en.get(key, _MISSING)
            if val is not _MISSING:
                return val
        return dict.__getitem__(self, key)

    def __contains__(self, key):
        if get_lang() == "en" and key in self._en:
            return True
        return dict.__contains__(self, key)

    def get(self, key, default=None):
        if get_lang() == "en":
            val = self._en.get(key, _MISSING)
            if val is not _MISSING:
                return val
        return dict.get(self, key, default)


class _Missing:
    def __repr__(self):
        return "<missing>"


_MISSING = _Missing()