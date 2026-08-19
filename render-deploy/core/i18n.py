"""FBST i18n katmani - istek bazli (thread-local) aktif dil + sozluk proxy."""

import os
import json
import threading

_LANG = threading.local()

_VALID = ("tr", "en", "es")


def set_lang(lang):
    """Aktif cikti dilini ayarlar (tr/en/es; bilinmeyen tr'ye duser)."""
    _LANG.lang = lang if lang in _VALID else "tr"


def get_lang():
    """Thread-local aktif dili doner (varsayilan: tr)."""
    return getattr(_LANG, "lang", "tr")


def _load_glossary(filename):
    _out = {}
    _path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if not os.path.exists(_path):
        return _out
    try:
        with open(_path, encoding="utf-8") as _f:
            _raw = json.load(_f)
        for _cat in ("brand", "concepts", "planets", "signs", "elements", "modes", "structural"):
            for _k, _v in (_raw.get(_cat) or {}).items():
                _out[_k] = _v
    except Exception:
        _out = {}
    return _out


# ── Resmi terminoloji: fast_glossary.json (TR -> EN), fast_glossary_es.json (TR -> ES) ──
# Kastan torunlarıyla yuklenir; tum PDF/UI etiketleri buradan beslenir.
_GLOSSARY = _load_glossary("fast_glossary.json")
_GLOSSARY_ES = _load_glossary("fast_glossary_es.json")


def pdf_label(tr_text):
    """PDF yapisal etiketi aktif dile cevirir (es -> en -> tr fallback, bilinmeyen TR kalir)."""
    lang = get_lang()
    if lang == "tr":
        return tr_text
    if lang == "es":
        val = _GLOSSARY_ES.get(tr_text, _MISSING)
        if val is not _MISSING:
            return val
        val = _GLOSSARY.get(tr_text, _MISSING)
        if val is not _MISSING:
            return val
        return tr_text
    return _GLOSSARY.get(tr_text, tr_text)


class LangDict(dict):
    """TR sozlugun EN/ES kopyalarini aktif dile gore donduren dict proxy.

    Anahtarlar ayni olmalidir; ES'de olmayan anahtar EN'e, EN'de olmayan TR'ye duser.
    """

    def __init__(self, data, en_data=None, es_data=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update(data or {})
        self._en = en_data or {}
        self._es = es_data or {}

    def __getitem__(self, key):
        if get_lang() == "es":
            val = self._es.get(key, _MISSING)
            if val is not _MISSING:
                return val
            val = self._en.get(key, _MISSING)
            if val is not _MISSING:
                return val
        elif get_lang() == "en":
            val = self._en.get(key, _MISSING)
            if val is not _MISSING:
                return val
        return dict.__getitem__(self, key)

    def __contains__(self, key):
        if get_lang() == "es" and (key in self._es or key in self._en):
            return True
        if get_lang() == "en" and key in self._en:
            return True
        return dict.__contains__(self, key)

    def get(self, key, default=None):
        if get_lang() == "es":
            val = self._es.get(key, _MISSING)
            if val is not _MISSING:
                return val
            val = self._en.get(key, _MISSING)
            if val is not _MISSING:
                return val
        elif get_lang() == "en":
            val = self._en.get(key, _MISSING)
            if val is not _MISSING:
                return val
        return dict.get(self, key, default)

    def items(self):
        for key in dict.keys(self):
            yield key, self[key]

    def values(self):
        for key in dict.keys(self):
            yield self[key]


class LangList(list):
    """TR listesinin EN/ES kopyasini aktif dile gore donduren liste proxy.

    Elemanlar esit sayida ve ayni sirada olmalidir; bos eleman ust dil zincirine duser.
    """

    def __init__(self, data, en_data=None, es_data=None):
        super().__init__(data or [])
        self._en = en_data or []
        self._es = es_data or []

    def __getitem__(self, index):
        item = list.__getitem__(self, index)
        if get_lang() == "es":
            if index < len(self._es):
                es_item = self._es[index]
                if es_item:
                    return es_item
            if index < len(self._en):
                en_item = self._en[index]
                if en_item:
                    return en_item
        elif get_lang() == "en":
            if index < len(self._en):
                en_item = self._en[index]
                if en_item:
                    return en_item
        return item

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]


class _Missing:
    def __repr__(self):
        return "<missing>"


_MISSING = _Missing()