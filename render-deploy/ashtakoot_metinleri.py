# -*- coding: utf-8 -*-
"""
Standart 36 puanlı Ashtakoot yorum metinleri — Türkçe.

Yapı
----
`KOOTA_METIN_TR[koota] = {"soru": str, "bantlar": [...5...], "mod": {...}}`

Bant sırası `BANTLAR` sabitiyle tanımlıdır ve **her koota için aynıdır**;
koota başına metin `bant_bul(puan, azami)` ile seçilir.

Metinler genişletilebilir: yeni bir koota eklemek için `ashtakoot_motoru.KOOTALAR`
 listesine bir giriş, buraya da aynı anahtarla bir sözlük eklemek yeterlidir.
"""

from typing import Dict, List, Optional

#: Puan oranına göre 5 bant (üstte en iyi).
BANTLAR = ["mukemmel", "yuksek", "orta", "dusuk", "yok"]


def bant_bul(puan: int, azami: int) -> str:
    """Puanı 5 banttan birine eşler."""
    if azami <= 0 or puan <= 0:
        return "yok"
    oran = puan / azami
    if oran >= 1.0:
        return "mukemmel"
    if oran >= 0.70:
        return "yuksek"
    if oran >= 0.45:
        return "orta"
    return "dusuk"


KOOTA_METIN_TR: Dict[str, dict] = {

    # ---------------------------------------------------------------- Varna
    "varna": {
        "ad": "Varna",
        "baslik": "Varna — Kasta Uyumu",
        "soru": "İki kişinin toplumsal ve değer dünyası birbirini anlıyor mu?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Birebir aynı kasta",
                "aciklama": "İkinizin de Ay'ı aynı varna'da (Brahmin, Kshatriya, Vaishya veya Shudra). "
                            "Bu, gösterge için en yüksek puanı (1/1) alır.",
                "ipucu": "Kadim Jyotish'te kasta, soy değil; kişinin doğuş anındaki Ay'ının "
                         "kaçıncı pada düştüğüyle ölçülen bir nitelik sayılır. Günlük hayatta "
                         "benzer değer ölçütleri, aynı soyluluk veya aynı sosyal konum "
                         "beklenmez.",
            },
            "yuksek": {
                "baslik": "Yakın kastalar",
                "aciklama": "Kastalar farklı ama komşu. Günlük uyumde çoğu zaman fark "
                            "hissedilmez.",
                "ipucu": "Ortak aile geçmişi ya da benzer değer önceliği bu açığı kapatır.",
            },
            "orta": {
                "baslik": "Uzak ama çatışmayan kastalar",
                "aciklama": "Farklı kastalar; ne bir çatışma ne de güçlü bir çekim.",
                "ipucu": "Uzun vadeli uyum, bilinçli iletişimle kurulur.",
            },
            "dusuk": {
                "baslik": "En uzak iki kasta",
                "aciklama": "Varna skalasının iki ucu. Kültürel bakış açılarınızın "
                            "farklı olabileceğine işaret eder.",
                "ipucu": "Bu puan tek başına yargılanacak bir ölçüt değildir; Varna, "
                         "36 puanlık toplamın yalnızca 1'ini oluşturur.",
            },
            "yok": {
                "baslik": "Varna uyuşmazlığı",
                "aciklama": "Ay'lar farklı varna'lara düşüyor.",
                "ipucu": "Nara (Nadi) ve Rasi gibi daha yüksek ağırlıklı kootalara bakın.",
            },
        },
        "mod": {
            "es_sevgili": "Aile kökeni ve değer dünyası karşılıklı saygı çerçevesinde.",
            "ebeveyn_cocuk": "Aile değerlerinin aktarım kanalı. Çocuğun kastası ile ebeveyninki "
                             "arasındaki mesafe, değerlerin kuşaklar arasında nasıl "
                             "aktarıldığını gösterir.",
        },
    },

    # --------------------------------------------------------------- Vashya
    "vashya": {
        "ad": "Vashya",
        "baslik": "Vashya — Kuş/Yerdeş Yaşam Biçimi",
        "soru": "İkinizin yaşam ritmi ve avcı/av olma dinamiği uyumlu mu?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Aynı vashya grubu (2/2)",
                "aciklama": "Ay burçlarınız aynı yaşam kategorisine giriyor: aynı anda "
                            "avcı, aynı anda av, ya da ikisi de topal.",
                "ipucu": "Vashya, Jyotish'te tarihî bir yemek kültürü sınıflandırmasından "
                         "gelir: Chatura (kuş), Chatushpada (dört ayaklı), Manushya (insan), "
                         "Khala (sürüngen/ böcek).",
            },
            "yuksek": {
                "baslik": "Gezegen aracılığıyla uyum (1/2)",
                "aciklama": "Kategoriler farklı ama birinin burç lordu diğerinin kategorisine "
                            "giriyor. Kısmi bir yakınlık var.",
                "ipucu": "Bu puan, doğrudan benzerlikten çok aracılıkla gelen uyumu gösterir.",
            },
            "orta": {
                "baslik": "Komşu kategoriler",
                "aciklama": "Gruplar arasında bir köprü bulunamadı; uyum nötr.",
                "ipucu": "Ortak yaşam alışkanlıkları bu mesafeyi kolayca kapatabilir.",
            },
            "dusuk": {
                "baslik": "Zayıf vashya bağı",
                "aciklama": "Vashya kategorileri birbirinden uzak.",
                "ipucu": "Zayıf puan, ilişkinin niteliğini değil ritmini tanımlar.",
            },
            "yok": {
                "baslik": "Karşıt kategoriler",
                "aciklama": "Bir tarafın grubu diğerinin burç lordunun grubuyla da örtüşmüyor.",
                "ipucu": "Farklı yaşam tempolarının en güçlü göstergelerinden biridir.",
            },
        },
        "mod": {
            "es_sevgili": "Günlük ritim ve yaşam biçimi uyumu.",
            "ebeveyn_cocuk": "Çocuğun gelişim ihtiyacının ebeveynin verdiği düzenle ne kadar "
                             "örtüştüğü.",
        },
    },

    # ----------------------------------------------------------------- Tara
    "tara": {
        "ad": "Tara",
        "baslik": "Tara — Şans ve Zaman Uyumu",
        "soru": "Birinizin zamanlaması diğerininkine uyuyor mu?",
        "bantlar": {
            "mukemmel": {
                "baslik": "En iyi tara (3/3)",
                "aciklama": "İkinizin nakṣatra'ları arasındaki 9'lu döngüde A'nın yeri B'nin "
                            "en uğurlu tara'sına denk geliyor.",
                "ipucu": "Tara dokuzludur ve dokuz nakṣatra'da bir tekrar eder. Herkesin bir "
                         "tara'sı vardır; soru, sizin iki taranızın örtüşüp örtüşmediğidir.",
            },
            "yuksek": {
                "baslik": "Orta tara (1/3)",
                "aciklama": "Döngüde orta bir konum. Zamanlama çoğu zaman işe yarar, "
                            "ama zorlu dönemlerde sıkışabilir.",
                "ipucu": "Tara tek başına yazılı kısmeti temsil eder.",
            },
            "orta": {
                "baslik": "Alt tara",
                "aciklama": "Döngünün alt bölümü. Birlikte alınan kararlarda tempo farkı "
                            "oluşabilir.",
                "ipucu": "Karar verme hızını bilinçli biçimde eşitlemek yeterlidir.",
            },
            "dusuk": {
                "baslik": "Zayıf tara",
                "aciklama": "Tara döngüsünde karşı uçtasiniz.",
                "ipucu": "Sabır gerektiren bir alan; aceleye getirilmemeli.",
            },
            "yok": {
                "baslik": "En düşük tara (0/3)",
                "aciklama": "A'nın nakṣatra'sı B'nin döngüsünde en düşük sırada.",
                "ipucu": "Bu koota yönlüdür: A/B ile B/A farklı sonuç verebilir.",
            },
        },
        "mod": {
            "es_sevgili": "Kader ve zamanlama uyumu — ilişkinin zaman çizelgesiyle ilgili boyutu.",
            "ebeveyn_cocuk": "Ebeveynin çocuğa zamanlama açısından ne kadar uygun olduğu; "
                             "çocuğun farklı dönemlerdeki ihtiyaçlarına ne zaman cevap "
                             "verilebileceği.",
        },
    },

    # ----------------------------------------------------------------- Yoni
    "yoni": {
        "ad": "Yoni",
        "baslik": "Yoni — Fiziksel Çekim ve Karakter",
        "soru": "Fiziksel ve duygusal çekiminiz ne kadar?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Aynı hayvan, aynı cinsiyet (4/4)",
                "aciklama": "İki Ay nakṣatra'sı aynı yoni hayvanını gösteriyor. Yoni, "
                            "36 puanın 4'üyle fiziksel çekimin en güçlü göstergesidir.",
                "ipucu": "Cinsiyet, pada numarasıyla belirlenir: tek padalar erkek, çift "
                         "padalar kadın olarak yorumlanır.",
            },
            "yuksek": {
                "baslik": "Aynı hayvan, zıt cinsiyet (3/4)",
                "aciklama": "Yoni hayvanı aynı ama padaların cinsiyeti farklı. Klasik "
                            "yorumda bu, eşit değil ama tamamen reddedilmeyen bir çekimdir.",
                "ipucu": "Jaimini'de karşı cinsiyet eşleşmesi 'eşit olmayan ama bağışlanan' "
                         "kategorisindedir.",
            },
            "orta": {
                "baslik": "Farklı hayvanlar",
                "aciklama": "İki nakṣatra farklı yoni hayvanına işaret ediyor.",
                "ipucu": "Farklı yoni, farklı çekim dilini gösterir; toplam puanı "
                         "Gana, Graha Maitri ve Rasi belirler.",
            },
            "dusuk": {
                "baslik": "Yakın ama eşleşmeyen hayvanlar",
                "aciklama": "Hayvanlar aynı aileden olsa da farklı.",
                "ipucu": "Yoni tek başına yeterli değildir.",
            },
            "yok": {
                "baslik": "Yoni uyuşmazlığı (0/4)",
                "aciklama": "Hiçbir yoni ortaklığı yok. Bazı nakṣatraların (tekne, davul, "
                            "el, boşluk) yoni karşılığı yoktur ve bunlar yalnızca kendisiyle "
                            "eşleşir.",
                "ipucu": "Yastır, eski Hint tablolarında yalnızca 15 hayvan çifti üzerinden "
                         "kurulur; kapsamı bu yüzden dar tutulur.",
            },
        },
        "mod": {
            "es_sevgili": "Fiziksel çekim ve romantik eğilim.",
            "ebeveyn_cocuk": "Ebeveyn-çocuk arasındaki doğal yakınlık ve koruma içgüdüsü; "
                             "çocuğun hangi ebeveyn yönüne daha rahat bağlandığını gösterir.",
        },
    },

    # -------------------------------------------------------- Graha Maitri
    "graha_maitri": {
        "ad": "Graha Maitri",
        "baslik": "Graha Maitri — Gezegen Dostluğu",
        "soru": "Birinizin hayat yorumu diğerininkine yakın mı?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Aynı burç (5/5)",
                "aciklama": "İki Ay burçlarınız aynı. Burç lordu aynı gezegen olduğu için "
                            "temel dünya görüşü örtüşüyor.",
                "ipucu": "Aynı burç, aynı gezegeni ifade eder; aynı element (Ateş/Toprak/"
                         "Hava/Su) burada belirleyici değildir.",
            },
            "yuksek": {
                "baslik": "Lordlar dost (4/5)",
                "aciklama": "Burçlar farklı ama lordları doğal dostluk ilişkisinde.",
                "ipucu": "Dostluk tablosu Naisargika (doğal) dostluktur; geçmiş yaşamdan "
                         "gelen karmik dostluk değil.",
            },
            "orta": {
                "baslik": "Lordlar nötr (3/5)",
                "aciklama": "Lordlar arasında doğal bir yakınlık ya da düşmanlık yok.",
                "ipucu": "Nötr ilişki, çoğu uzun soluklu birliktelikte sorunsuz işler.",
            },
            "dusuk": {
                "baslik": "Lordlar düşman (1/5)",
                "aciklama": "Burç lordları doğal düşmanlık ilişkisinde. Temel dünya "
                            "görüşleri farklı olabilir.",
                "ipucu": "Örneğin Güneş (Aslan) ile Satürn (Oğlak/Kova) klasik düşman "
                         "çiftidir.",
            },
            "yok": {
                "baslik": "Zayıf dostluk",
                "aciklama": "Yönlü tabloda en düşük puan.",
                "ipucu": "Kararsız kalan tek koota: Vashya'nın 2 puanına denk gelir.",
            },
        },
        "mod": {
            "es_sevgili": "Değerler, hedefler ve hayat önceliklerinin örtüşmesi.",
            "ebeveyn_cocuk": "Ebeveynin çocuğa dünya görüşünü aktarma kapasitesi.",
        },
    },

    # ----------------------------------------------------------------- Gana
    "gana": {
        "ad": "Gana",
        "baslik": "Gana — Temel Karakter",
        "soru": "İkinizin karakter yapısı birbirini tamamlıyor mu?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Aynı gana (6/6)",
                "aciklama": "İki Ay da aynı temel karakter sınıfında (Deva, Manushya veya "
                            "Rakshasa).",
                "ipucu": "Gana, Jaimini'den gelen üçlü bir sınıflandırmadır: Deva (olgun), "
                         "Manushya (dengeci), Rakshasa (dürtüsel).",
            },
            "yuksek": {
                "baslik": "Deva – Manushya (5/6)",
                "aciklama": "Olgunluk ve denge birbirini destekliyor. Klasik yorumda bu, "
                            "biri diğerine saygı duyan tamamlayıcı bir eşleşmedir.",
                "ipucu": "Bu, Jaimini'de 'her şey yerinde' kabul edilen çiftlerdendir.",
            },
            "orta": {
                "baslik": "Zayıf karakter uyumu",
                "aciklama": "Rakşasa ile Manushya arasındaki asimetrik eşleşme. Puan düşük "
                            "ama tamamen reddedilen bir çift değildir.",
                "ipucu": "Gana tablosu yönlüdür; A/B ile B/A farklı puan verebilir.",
            },
            "dusuk": {
                "baslik": "Karşıt karakterler",
                "aciklama": "Deva ile Rakşasa karşı karşıya. Klasik metinlerde bu, "
                            "kadim düşmanlık (şatru)'un işareti sayılır.",
                "ipucu": "36 puanın 6'sı bu tek kaleme ayrılır; yüksek ağırlığı nedeniyle "
                         "toplamı belirgin biçimde etkiler.",
            },
            "yok": {
                "baslik": "Gana uyuşmazlığı (0/6)",
                "aciklama": "Yönlü tabloda bu sıralama için puan yok.",
                "ipucu": "Rakşasa – Manushya sırası klasik tabloda da 0'dır.",
            },
        },
        "mod": {
            "es_sevgili": "Karakter uyumu ve tahammül sınırları.",
            "ebeveyn_cocuk": "Çocuğun mizacının ebeveyninkiyle ne kadar örtüştüğü; "
                             "terbiye biçiminin doğal eğilimle çakışma noktaları.",
        },
    },

    # ----------------------------------------------------------------- Rasi
    "rasi": {
        "ad": "Rasi",
        "baslik": "Rasi — Duygusal ve Zihinsel Yakınlık",
        "soru": "Duygusal dünyalarınız ne kadar benzer?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Aynı burç (7/7)",
                "aciklama": "En yüksek ağırlıklı koota ve tam puanı. Duygusal dilleriniz "
                            "birebir aynı.",
                "ipucu": "Rasi 7 puanla Ashtakoot'un ağırlık merkezidir; Nadi ile birlikte "
                         "toplamın 15'ini oluşturur.",
            },
            "yuksek": {
                "baslik": "2./4. dost veya 3./12. taraf (5/7)",
                "aciklama": "Burçlar arası 2-3-4 veya 10-11-12 derece mesafe. Birçok geleneksel "
                            "yöntemde bunlar da 'çok uyumlu' sayılır.",
                "ipucu": "Aynı element ya da aynı kalite (kardinal/fixed/değişken) burada "
                         "değerlendirilmez; yalnızca burç mesafesi sayılır.",
            },
            "orta": {
                "baslik": "5. veya 9. taraf (3/7)",
                "aciklama": "Mesafe orta. Duygular var ama ifade biçimi farklı.",
                "ipucu": "Bu mesafe, birlikte yaşamayı zorlaştırmaz; çeviri ister.",
            },
            "dusuk": {
                "baslik": "6. veya 8. taraf (1/7)",
                "aciklama": "Karşı burç ekseninin yakını. Klasik yorumda çatışma ve dönüşüm "
                            "alanıdır.",
                "ipucu": "Eksende karşılaşmak, mesafeden daha çok dönüştürücüdür.",
            },
            "yok": {
                "baslik": "Tam karşı burç (0/7)",
                "aciklama": "Burçlar birbirinin tam karşısı (1-7, 2-8, 3-9, 4-10, 5-11, 6-12). "
                            "Duygusal yansıma güçlüdür ama puan verilmez.",
                "ipucu": "Karma şemaların tamamı bu eksende en yüksek gerginliği gösterir.",
            },
        },
        "mod": {
            "es_sevgili": "Duygusal yakınlık ve iletişim dili.",
            "ebeveyn_cocuk": "Ebeveyn-çocuk duygusal bağı ve karşılıklı anlaşılma.",
        },
    },

    # ----------------------------------------------------------------- Nadi
    "nadi": {
        "ad": "Nadi",
        "baslik": "Nadi — Kader Uyuşmazlığı",
        "soru": "Kaderleriniz çakışıyor mu?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Farklı nadi (8/8)",
                "aciklama": "Nadi uyuşmuştur. Bu, 36 puanın 8'idir ve Astakoot'un en yüksek "
                            "tek puanıdır.",
                "ipucu": "Nadi üçlüdür (nadi_1, nadi_2, nadi_3). Aynı nadi'ye düşmek "
                         "kader çakışması sayılır.",
            },
            "yok": {
                "baslik": "Aynı nadi — puan yok (0/8)",
                "aciklama": "İki kişi aynı nadi'de. Ashtakoot'un tek 'sıfır puanlı' ve tek "
                            "8 puanlı kalemi budur.",
                "ipucu": "Bir kişi kendisiyle karşılaştırıldığında daima Nadi 0 çıkar ve "
                         "toplam 28/36 olur. 36 puanlık şemada bu, sistemin üst sınırıdır: "
                         "pratikte en iyi eşleşmeler 30-34 arasındadır.",
            },
        },
        "mod": {
            "es_sevgili": "Yaşam çizgilerinin kesişimi. Klasik yorumda aynı nadi, alınmış "
                          "evlilikten gelen bir ilişki olarak yorumlanır.",
            "ebeveyn_cocuk": "Kuşaklar arası kader sürekliliği. Ebeveyn ve çocuk aynı nadi'de "
                             "ise aktarım güçlü ama kısıtlayıcı bulunur.",
        },
    },
}

#: Toplam puan için genel bant yorumları.
TOPLAM_BANTLARI = {
    "cok_dusuk": {
        "baslik": "20–23 · Zayıf ilişki",
        "aciklama": "Sistem içi uyum düşük. Bu, ilişkinin ya da ebeveyn-çocuk bağının "
                    "olmadığı anlamına gelmez; yalnızca Ay nakṣatra'larının sekiz kriterde "
                    "örtüşmediğini gösterir.",
        "ipucu": "Diğer analiz katmanlarına bakın: Nadi, Rasi ve Gana ağırlıklıdır.",
    },
    "dusuk": {
        "baslik": "26–27 · Orta ilişki",
        "aciklama": "Kısmi uyum. Bazı kootalar güçlü, bazıları zayıf.",
        "ipucu": "Güçlü kootalar ilişkinin doğal olarak dayandığı alanlardır.",
    },
    "orta": {
        "baslik": "28–29 · İdeal ilişki",
        "aciklama": "Sağlıklı bir uyum. Klasik metinlerin 'iyi eşleşme' aralığı.",
        "ipucu": "Çoğu uzun soluklu birliktelik bu aralıktadır.",
    },
    "yuksek": {
        "baslik": "33–34 · Kuvvetli ilişki",
        "aciklama": "Nadir görülen güçlü uyum. 33 üzeri sonuçlar seyrektir.",
        "ipucu": "Pratikte 36 mümkün değildir; aynı nadi nedeniyle üst sınır 34'tür.",
    },
}

#: Kendisiyle karşılaştırma için açıklama.
KENDISI_NOTU = {
    "baslik": "Kendisiyle Karşılaştırma",
    "aciklama": "Bu tablo, kişinin kendi Ay nakṣatra'sıyla karşılaştırılmasıdır. "
                "Sistem içi tutarlılığın referans değeridir ve her zaman 28/36 çıkar.",
    "ipucu": "Varna, Vashya, Tara, Yoni, Graha Maitri, Gana ve Rasi tam puan alırken Nadi "
             "sıfır verir. Bu yüzden 36 değil 28 çıkar.",
}


def metin_getir(koota: str, puan: int, azami: int) -> dict:
    """Verilen koota için puan bandına ait metni döndürür."""
    k = KOOTA_METIN_TR.get(koota)
    if not k:
        return {"baslik": koota, "aciklama": "", "ipucu": ""}
    bant = bant_bul(puan, azami)
    m = k["bantlar"].get(bant)
    if m is None:                       # ara bant eksikse en yakın dolu bandı seç
        sira = BANTLAR.index(bant)
        for adim in range(1, len(BANTLAR)):
            for hedef in (sira - adim, sira + adim):
                if 0 <= hedef < len(BANTLAR):
                    m = k["bantlar"].get(BANTLAR[hedef])
                    if m:
                        return dict(m, _bant=bant)
        return {"baslik": koota, "aciklama": "", "ipucu": ""}
    return dict(m, _bant=bant)


def mod_yorumu(koota: str, mod: str) -> str:
    """Koota için mod bazlı (çift / anne-çocuk) tek cümlelik yorum."""
    k = KOOTA_METIN_TR.get(koota)
    if not k:
        return ""
    return k.get("mod", {}).get(mod, "")


def toplam_metni(seviye: str) -> dict:
    """Toplam puan bandının açıklamasını döndürür."""
    return TOPLAM_BANTLARI.get(seviye, {"baslik": seviye, "aciklama": "", "ipucu": ""})


def tum_metinler(lang: str = "tr") -> Dict[str, dict]:
    """Dil belirleyicisine göre metin sözlüğünü döndürür.

    TR kaynak modülden okunur; EN/ES ayrı modüllerde yaşar ve burada
    dinamik olarak içe aktarılır.
    """
    if lang == "tr":
        return KOOTA_METIN_TR
    mod_adi = {"en": "ashtakoot_metinleri_EN", "es": "ashtakoot_metinleri_ES"}.get(lang)
    if not mod_adi:
        return KOOTA_METIN_TR
    try:
        mod = __import__(mod_adi)
        return mod.KOOTA_METIN
    except (ImportError, AttributeError):
        return KOOTA_METIN_TR


#: Nadi Dosha değerlendirmesi. `ashtakoot_motoru.nadi_dosha_analizi` yalnızca
#: dilden bağımsız kod üretir; buradaki `kosullar` sözlüğü o kodları dile
#: çevirir.
#:
#: DÜZEN: Bu blok `nadi` kootasının 0/8 puanını DEĞİŞTİRMEZ. Doshanın varlığı,
#: şiddeti ve hafifletici/şiddetlendirici etkenleri ayrıca raporlanır.
NADI_DOSHA_METIN = {
    "baslik": "Nadi Dosha",

    "seviye": {
        "yok": {
            "baslik": "Nadi doshası yok",
            "aciklama": "Ay'lar farklı nadi grubunda. Nadi kootası tam puan "
                        "(8/8) alır ve dosha tartışması gündeme gelmez.",
            "ipucu": "Bu tek kalem, 36 puanlık tabloda en yüksek ağırlıklıdır; "
                     "tam alınması nadir değildir ama mümkündür.",
        },
        "belirgin": {
            "baslik": "Nadi doshası belirgin",
            "aciklama": "Ay'lar aynı nadi grubunda ve hiçbir hafifletici koşul "
                        "sağlamıyor. Nadi 0/8 verir.",
            "ipucu": "Bu tek başına bir hüküm değildir. Bazı okullar bu doshayı "
                     "eş geçirilerek değerlendirir; bunu doğru yapmak tam bir "
                     "doğum haritası gerektirir.",
        },
        "hafif": {
            "baslik": "Nadi doshası hafif",
            "aciklama": "Ay'lar aynı nadi grubunda, ancak bir hafifletici "
                        "koşul sağlıyor.",
            "ipucu": "Hafifletici koşul doshayı ortadan kaldırmaz; etkisini "
                     "azaltır.",
        },
        "hafifletilmis": {
            "baslik": "Nadi doshası hafifletilmiş",
            "aciklama": "Ay'lar aynı nadi grubunda, ancak birden fazla "
                        "hafifletici koşul sağlıyor.",
            "ipucu": "Ham puan yine 0/8'dir; hafifletme puanı değil, "
                     "yorumun çerçevesidir.",
        },
    },

    "kosullar": {
        "rasi_kendra": {
            "baslik": "Ay burçları 2/12, 4/10 veya 6/8 konumunda",
            "detay": "En sık örneklenen hafifleticidir. Dosha, Ay burçlarının "
                     "bu konum çiftlerinde olmasıyla dengelenir.",
        },
        "nadi_lord_ayni": {
            "baslik": "Nadi lordları aynı gezegen",
            "detay": "İki tarafın da nadi'sini yöneten gezegen aynıysa "
                     "doshanın aracısı ortaklaşır.",
        },
        "ayni_gana": {
            "baslik": "Aynı gana",
            "detay": "Ay'ın temel karakter sınıfı aynıysa dosha bağlamında "
                     "zayıflar.",
        },
        "ayni_varna": {
            "baslik": "Aynı varna",
            "detay": "Ay'ın varna'sı aynıysa kasta katmanında örtüşme vardır.",
        },
        "rasi_dusman": {
            "baslik": "Ay burçları 3/11 veya 5/9 konumunda",
            "detay": "Dosha bu konum çiftlerinde en ağır kabul edilir. Hafifletici "
                     "koşul varsa denge kurulur.",
        },
    },

    "etiket": {
        "bhanga": "Hafifletici (bhanga)",
        "taraka": "Şiddetlendirici (taraka)",
    },

    "ozet_etiket": {
        "iliski": "Ay burç konumu",
        "pada": "Pada",
        "nadi": "Nadi",
        "lord": "Nadi lordu",
        "bhanga": "Hafifletici",
        "taraka": "Şiddetlendirici",
    },

    "kapsam_disi_baslik": "Değerlendirilmeyen klasik alt kurallar",
    "kapsam_disi": {
        "nadi_lord_kendra": "Nadi lordlarının 2/12, 4/10 veya 6/8 konumunda olması",
        "rasi_lord_kendra": "Ay burçlarının lordlarının 2/12, 4/10 veya 6/8 olması",
        "nadi_lord_dusthana": "Her iki nadi lordunun da 6/8/12'de bulunması",
        "kendra_lagna": "Lagna'nın her iki Ay'a 2/12, 4/10 veya 6/8 olması",
    },
    "kapsam_disi_notu": ("Bu motor yalnızca Ay konumu üzerinden çalışır; doğum "
                         "anındaki diğer gezegenleri ve lagna'yı hesaplamaz. "
                         "Yukarıdaki klasik alt kurallar bu yüzden uygulanmadı."),

    "puan_notu": ("Nadi doshası puanı değiştirmez. Ashtakoot'un 36 puanlık "
                  "tablosu tek bir okulun sayısıdır; bu blok o puanı "
                  "saklamadan yorumun çerçevesini verir."),
}
