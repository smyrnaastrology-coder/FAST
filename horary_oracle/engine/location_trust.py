# -*- coding: utf-8 -*-
"""Guven katmani: kalibrasyon verisi ne kadar destekliyor?

NEDEN VAR:22 kayit var ama lost_object icin sadece 1 kayit. Bu kayit
k=0.00069 donduruyor, motor 1339 km'yi 0.9 km'ye indiriyor. Kullanici
"50-100 m" diyor, motorun ham verisi 1339 km. Bu celiskiyi gizlemek
guveni bitirir; olceme gore konusmak gerekir.

Uc seviye:
  guclu  : ayni soru tipinden >=4 kayit, yon hatasi <=22.5 derece
  orta   : >=2 kayit veya hatasi <=45 derece
  zayif  : geri kalan (1 kayit veya 45+ derece hata)

ZAYIFTA YAPILAN: mesafe rakami verilmez, yon 'tahmini' diye sunulur,
kullaniciya 'guven yok, elinizle arayin' denir. Guclu/ortada rakam verilir
ama 'yaklasik' ve 'tahmini' diliyle.
"""
import math

DIR_STRONG = 22.5      # derece: bu esigin altinda yon guvenilir
DIR_MID = 45.0
MIN_RECORDS_STRONG = 4


def _circ(a, b):
    d = abs(a - b) % 360
    return d if d <= 180 else 360 - d


def assess(cal, question_type=None):
    """Kalibrasyon nesnesinden guven raporu dondurur."""
    recs = [r for r in cal.records
            if question_type is None or r.get("question_type") == question_type]
    n_type = len(recs)
    n_all = len(cal.records)

    usable = [r for r in recs
              if r.get("components") and r.get("real_bearing") is not None
              and float(r.get("real_distance_km", 0)) >= 1.0]
    if usable:
        from engine.horary_distance import load_weights, _direction_predict
        w = load_weights()
        errs = [_circ(_direction_predict(r["components"], w), r["real_bearing"])
                for r in usable]
        mean_err = sum(errs) / len(errs)
    else:
        mean_err = None

    if mean_err is None:
        level = "zayif"
        reason = "bu soru tipi icin yon dogrulamasi hic yok"
    elif n_type >= MIN_RECORDS_STRONG and mean_err <= DIR_STRONG:
        level = "guclu"
        reason = f"{n_type} dogrulanmis vaka, yon hatasi {mean_err:.0f} derece"
    elif mean_err <= DIR_MID and n_type >= 2:
        level = "orta"
        reason = f"{n_type} vaka, yon hatasi {mean_err:.0f} derece"
    elif mean_err is not None:
        # kayit sayisi yuksek olsa bile hata 45 dereceyi asiyorsa veri
        # gercekten yon gosteremiyor demektir. Bu durumda en kaliteli model
        # bile yanlis yon soyluyor olur, bu yuzden zayif.
        level = "zayif"
        if mean_err > DIR_MID:
            reason = (f"{n_type} vaka ama yon hatasi {mean_err:.0f} derece - "
                      "yon tahmini bu veriyle yapilamaz")
        else:
            reason = f"sadece {n_type} vaka, istatistiksel olarak anlamli degil"
    else:
        level = "zayif"
        reason = f"sadece {n_type} vaka, yon dogrulamasi yok"

    return {
        "level": level,
        "n_type": n_type,
        "n_all": n_all,
        "mean_dir_err_deg": round(mean_err, 1) if mean_err is not None else None,
        "reason": reason,
        "give_km": level in ("guclu", "orta"),
        "give_direction": True,          # yon her zaman verilir, ama dil degisir
        "must_hedge": level == "zayif",
        "must_advise_manual": level == "zayif",
    }


def prompt_text(trust, question_type_label=""):
    """Prompt'a eklenecek guven talimati."""
    lv = trust["level"]
    head = f"- Guven seviyesi: {lv.upper()} ({trust['reason']})."
    if not trust["give_km"]:
        return head + (
            " BU SORU TIPI icin mesafe hesabi kalibre edilmedi. "
            "KESIN KM/METRE RAKAMI YAZMA, HICBIR SAYI VERME. "
            "Yonu ve ortami yalnizca 'harita su yone isaret ediyor' diye, "
            "tahmin olarak sun. Rakam vermek yerine alani tarif et."
        )
    if trust["must_hedge"]:
        return head + (
            " Yon ve mesafe YALNIZCA tahmin olarak sunulabilir; "
            "'kesinlikle burada' gibi kesif dili kullanma. "
            "Cevabin SONUNA su uyariyi ekle: 'Harita tahmini bir yon gosterir; "
            "gercek yer arama calismasiyla farkli olabilir, elinizle "
            "kontrol ederek arayin.'"
        )
    return head + (
        " Mesafeyi 'yaklasik' diye ver. Kesin ('tam olarak', 'mutlaka burada') "
        "diyebilme."
    )


def engine_fields(trust):
    """engine_json'ya eklenecek alanlar (arayuz de gosterebilir)."""
    return {
        "trust_level": trust["level"],
        "trust_reason": trust["reason"],
        "trust_n_type": trust["n_type"],
        "trust_dir_err_deg": trust["mean_dir_err_deg"],
    }