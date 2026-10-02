# -*- coding: utf-8 -*-
"""Ashtakoot kootaları için JARGONSUZ doğal dil açıklamaları (TR).

Neden ayrı bir katman:
    Kullanıcı "varna", "bhanga", "nadi", "pada", "gana" gibi terimleri
    bilmez ve öğrenmek zorunda değildir. `ashtakoot_metin.KOOTA_METIN_*`
    hâlâ teknik/bant metinlerini taşır (PDF, geliştirici ekranı); bu
    modül yalnızca KULLANICIYA gösterilen sade anlatımı üretir.

Yapı
----
    KOOTA_BASLIK[koota]      : kootanın sade karşılığı ("Toplumsal ve değer uyumu")
    ACILAR[koota][i]        : üç bakış açısı giriş cümlesi
                               0 = ne VAAT ediyor
                               1 = ne ANLATIYOR
                               2 = neyi SİMGELİYOR
    GOVDE[koota][puan]      : o puan için üç satırlık öz (substance)

    toplam metin = ACILAR[koota][i] + GOVDE[koota][puan]

`puan`, `ashtakoot_motoru.KOOTALAR` içindeki azami değere göre 0..azami
aralığındadır; her puan için AYRI bir metin vardır (bant yaklaşımı değil).

Kural: hiçbir metinde Sanskrit/Jyotish terimi geçmez; her metin
ilişkinin günlük hayatında ne demek olduğunu söyler.
"""

from typing import Dict, List

#: Kootanın teknik adı yerine kullanıcıya gösterilen sade karşılığı.
KOOTA_BASLIK: Dict[str, str] = {
    "varna": "Toplumsal ve değer uyumu",
    "vashya": "Karşılıklı çekim",
    "tara": "Zaman ve ritim uyumu",
    "yoni": "İç dünya ve mahremiyet",
    "graha_maitri": "Düşünce ve iletişim",
    "gana": "Karakter ve günlük uyum",
    "rasi": "Ortak yön ve işleyiş",
    "nadi": "İç dürtü ve iç çatışma",
}

#: Üç bakış açısının giriş cümleleri: 0 vaat, 1 anlatı, 2 simge.
ACILAR: Dict[str, List[str]] = {
    "varna": [
        "Bu alan şunu vaat ediyor: birlikte hayat kurarken değer "
        "çatışması yaşamayacağınızı gösterir.",
        "Bu alan şunu anlatıyor: hayatınızda \"kimin haklı\" tartışmasının "
        "çıkıp çıkmayacağını gösterir.",
        "Bu alan şunu simgeliyor: sizin de onun da \"bu önemli\" dediği "
        "şeylerin örtüşmesi.",
    ],
    "vashya": [
        "Bu alan şunu vaat ediyor: karşınızdakine çekilme gücünüzün ne "
        "kadar güçlü olduğunu gösterir.",
        "Bu alan şunu anlatıyor: \"gördüğümde içimde bir şey kıpırdadı\" "
        "hissinin nereden geldiğini gösterir.",
        "Bu alan şunu simgeliyor: birbirinize ilk çekildiğiniz o sessiz an.",
    ],
    "tara": [
        "Bu alan şunu vaat ediyor: günlük ritimlerinizin ne kadar "
        "örtüştüğünü gösterir.",
        "Bu alan şunu anlatıyor: birinizin geç yatıp diğerinin erkenden "
        "kalkmasının ilişkiye etkisini gösterir.",
        "Bu alan şunu simgeliyor: aynı evde farklı saatlerin çalıştığı bir "
        "düzen.",
    ],
    "yoni": [
        "Bu alan şunu vaat ediyor: birbirinizin iç dünyasını ne kadar kolay "
        "anlayacağınızı gösterir.",
        "Bu alan şunu anlatıyor: \"acaba şu an ne hissediyor?\" sorusunun ne "
        "sıklıkta doğacağını gösterir.",
        "Bu alan şunu simgeliyor: iç dünyanızın kapısının size ne kadar açık "
        "durduğu.",
    ],
    "graha_maitri": [
        "Bu alan şunu vaat ediyor: birbirinin aklını ne kadar kolay "
        "okuyabileceğinizi gösterir.",
        "Bu alan şunu anlatıyor: aynı olayı neden farklı anlattığınızı "
        "gösterir.",
        "Bu alan şunu simgeliyor: aynı dili konuşan iki kişinin rahatlığı.",
    ],
    "gana": [
        "Bu alan şunu vaat ediyor: günlük hayatta birbirinizi yormadan "
        "yaşama ihtimalinizi gösterir.",
        "Bu alan şunu anlatıyor: tepkilerinizin neden bazen aynı anda "
        "çarpıştığını gösterir.",
        "Bu alan şunu simgeliyor: iki farklı ritmin aynı çatı altında "
        "buluşması.",
    ],
    "rasi": [
        "Bu alan şunu vaat ediyor: birlikte bir hedefe yürüyüp "
        "yürüyemeyeceğinizi gösterir.",
        "Bu alan şunu anlatıyor: hayatın hangi alanlarında aynı hızda "
        "olduğunuzu gösterir.",
        "Bu alan şunu simgeliyor: iki kişinin aynı haritayı "
        "okuyabilmesi.",
    ],
    "nadi": [
        "Bu alan şunu vaat ediyor: aynı eksiğin ikinizde de bulunma "
        "ihtimalini gösterir.",
        "Bu alan şunu anlatıyor: aynı şeyi neden hep birbirinizde "
        "aradığınızı gösterir.",
        "Bu alan şunu simgeliyor: aynı noktada duran iki kişinin birbirini "
        "tamamlaması ya da çarpışması.",
    ],
}

#: Her koota için, her puan değerinde üç satırlık öz.
GOVDE: Dict[str, Dict[int, str]] = {

    # ------------------------------------------------ toplumsal / değer
    "varna": {
        0: ("İkinizin değer dünyası belirgin biçimde farklı.\n"
            "Aile, para ve otorite konusunda farklı beklentileriniz "
            "olabilir.\n"
            "Bu fark çatışma yaratmaz ama küçük konularda aynı tartışmayı "
            "tekrar ettirir."),
        1: ("Değer dünyanız birbirine çok yakın.\n"
            "Aile, para ve sorumluluk konularında aynı yerde durmanız "
            "kolay.\n"
            "Bu uyum, günlük hayatınızın sessiz ve rahat bir zeminidir."),
    },

    # ------------------------------------------------------- karşılıklı çekim
    "vashya": {
        0: ("İkiniz arasında çekimden çok alışkanlık var.\n"
            "Birbirinizi tanıyorsunuz ama “karşılaştığımda içimde bir şey "
            "kıpırdadı” hissi zayıf.\n"
            "Bu eksik değildir; birlikte yaşanan güven zamanla kıpırdamaya "
            "dönüşebilir."),
        1: ("Karşılıklı çekim dengeli.\n"
            "Biriniz diğerine ilgi duyarken karşılığı da var; ne çok fazla "
            "ne de eksik.\n"
            "Bu denge, ilişkinin sürdürülebilir olmasında belirleyicidir."),
        2: ("Karşılıklı çekim güçlü ve karşılıklı.\n"
            "Birbirinizi fark ettiğiniz an ikisi de “tamam” diyor.\n"
            "Bu, ilişkinin enerjisini doğrudan besler; zorluklar olsa da "
            "dönüp birbirinize çekilmek kolaylaşır."),
    },

    # ------------------------------------------------------------ zaman / ritim
    "tara": {
        0: ("Hayat ritimleriniz zıt yönlerde.\n"
            "Biri sabahları ve planlı çalışırken diğeri geceye ve "
            "sürprize yakındır.\n"
            "Aynı çatı altında farklı saatlerde yaşamak, kültürel farktan "
            "çok zamanlama farkı yaratabilir."),
        1: ("Hayat ritimleriniz kısmen örtüşüyor.\n"
            "Bazı dönemler birebir aynı, bazı dönemler tamamen farklı "
            "ilerliyor.\n"
            "Bu ilişkiyi zayıflatmaz; yalnızca dönemsel bir uyumsuzluk "
            "yaratır."),
        2: ("Hayat ritimleriniz büyük ölçüde örtüşüyor.\n"
            "Günün hangi saatlerinde birlikte olduğunuz benzer.\n"
            "Ortak işler ve ortak boş zaman için sağlam bir zemin oluşur."),
        3: ("Hayat ritimleriniz neredeyse aynı.\n"
            "Biri geç kalkıyorsa diğeri de geç kalkıyor; biri yoğundaysa "
            "diğeri de yoğun.\n"
            "Bu, ilişkinin kırılma noktası olabilecek en zorlu alanlardan "
            "biri; ama aynı zamanda en çok zaman kazandıranı."),
    },

    # ------------------------------------------------------------ iç dünya
    "yoni": {
        0: ("İç dünyanız birbirine kapalı.\n"
            "Karşınızdakinin ne hissettiğini tahmin etmekte zorlanıyorsunuz "
            "ve o da sizinle aynı zorluğu yaşıyor.\n"
            "Duyguları tahmin etmek yerine söylemeyi denemek bu mesafeyi "
            "kısaltır."),
        1: ("İç dünyalarınız kısmen açık.\n"
            "Birçok şeyi birbirinizden anlıyorsunuz ama bazı duygular hâlâ "
            "gizli kalıyor.\n"
            "Mahremiyetin sıfır olduğu değil, henüz tüm katmanlarının "
            "açılmadığı anlamına gelir."),
        2: ("İç dünyalarınız orta düzeyde açık.\n"
            "Mutluluk ve üzüntüyü çoğu zaman birbirinizden okuyabiliyorsunuz.\n"
            "Karanlıkta kalan kısımlar daha çok gizli geçmişlerden kaynaklanıyor."),
        3: ("İç dünyalarınız birbirini kolay okuyor.\n"
            "Söylenmeden anlaşılan çok şey var; birinin hüzünlü olduğu çoğu "
            "zaman ilk bakışta belli olur.\n"
            "Karşılığında beklenti de yükselir: karşınızı bu kadar "
            "okuyabiliyorsan, kendi içini de açık tutman gerekir."),
        4: ("İç dünyalarınız neredeyse şeffaf.\n"
            "Söylenmeden her şey anlaşılır; birinin ihtiyacı karşı tarafta "
            "karşılığını bulur.\n"
            "Bu düzeyde mahremiyet nadirdir ve ilişkinin en güçlü güven "
            "kaynağıdır."),
    },

    # ------------------------------------------------------ düşünce / iletişim
    "graha_maitri": {
        0: ("Düşünme biçimleriniz neredeyse zıt.\n"
            "Siz daha soğukkanlı ve analitik yaklaşırken karşı taraf daha "
            "duygusal ve sezgisel.\n"
            "İlk bakışta çatışma gibi görünse de aslında farklı bir dil "
            "konuşuyorsunuz."),
        1: ("Düşüncelerinizin çoğu örtüşüyor ama birkaç temel noktada farklı "
            "yoldasınız.\n"
            "Günlük konuşmalar rahat geçer, derin tartışmalarda sınırlar "
            "belirginleşir.\n"
            "Farkı engel değil, tamamlayıcı bir zenginlik olarak okumak bu "
            "alanı güçlendirir."),
        2: ("Temel düşünce biçiminiz örtüşüyor.\n"
            "Tartışmalarda çoğu zaman aynı yere varıyorsunuz.\n"
            "Arada ince farklar var ama bunlar konuşmayla çözülebilir "
            "türden."),
        3: ("Düşünce biçimleriniz birbirine yakın ve tamamlayıcı.\n"
            "Biri detayı kaçırırken diğeri onu görüyor; bu ortak "
            "kararlarda büyük avantaj.\n"
            "Birbirinizi fazla anladığınız için açık konuşmayı ertelediğiniz "
            "anlar olabilir."),
        4: ("Düşünceleriniz neredeyse iç içe.\n"
            "Tartışmada çoğu zaman aynı sonuca varırsınız ve birbirinizi "
            "tamamlarsınız.\n"
            "Tek dikkat edilecek nokta: aynı fikirde olmak sessiz bir "
            "çatışmayı gizlememelidir."),
        5: ("Düşünce uyumunuz zirvede.\n"
            "Konuşmadan önce birbirinizi anlayabiliyorsunuz; "
            "karşınızdakinin ne demek istediğini neredeyse duyuyorsunuz.\n"
            "Ortak kararlar ve ortak yönelim bu uyumdan doğuyor."),
    },

    # ------------------------------------------------------------ karakter
    "gana": {
        0: ("Karakterleriniz çok farklı.\n"
            "Biri daha temkinli ve yavaş, diğeri daha atılgan ve hızlı.\n"
            "Bu, “acele et” ve “biraz bekle” demenin tekrar tekrar "
            "gündeme gelmesi şeklinde görünür."),
        1: ("Karakterleriniz farklı ama karşılıklı saygı çerçevesinde.\n"
            "Biri daha dışa dönük, diğeri daha içe dönük olabilir.\n"
            "Bu fark günlük hayatı zenginleştirir; sorun ancak “benim gibi "
            "yapmıyor” beklentisi doğduğunda başlar."),
        2: ("Karakter uyumunuz orta düzeyde.\n"
            "Benzer şeylere gülüyorsunuz ama tepki biçimleriniz farklı.\n"
            "Küçük şikayetler genellikle büyümeden çözülür."),
        3: ("Karakterleriniz birbirine yakın ama tamamen aynı değil.\n"
            "Aynı komik durumda ikiniz de gülüyorsunuz; ama biri daha hızlı "
            "harekete geçiyor.\n"
            "Bu, günlük hayatta rahat bir uyum."),
        4: ("Karakterleriniz uyumlu.\n"
            "Tepkileriniz, enerjiniz ve beklentileriniz benzer.\n"
            "Birlikte yapacağınız işlerde verimlisiniz; günlük tempo birinizi "
            "yormuyor."),
        5: ("Karakterleriniz güçlü biçimde örtüşüyor.\n"
            "Tepkileriniz ve beklentileriniz birbirinin aynısı.\n"
            "Karşılığında biriniz değiştiğinde diğerinin de değişmesi "
            "beklenebilir."),
        6: ("Karakterleriniz birbirini tamamlıyor.\n"
            "Sizden birinin enerjisi, diğerinin sakinliğiyle dengeleniyor.\n"
            "Bu, ilişkiyi ayakta tutan en güçlü günlük uyum ve birlikte daha "
            "fazlasını yapma gücü."),
    },

    # ------------------------------------------------------------ ortak yön
    "rasi": {
        0: ("İkinizin doğal olarak aynı alanda çalıştığı görünmüyor.\n"
            "Biri ilişkiyi duygusal, diğeri daha çok eylem üzerinden "
            "tanımlıyor.\n"
            "Farklı harita okumak, birlikte ilerlerken yönü bulanıklaştırır."),
        1: ("Bazı alanlarda aynı yoldasınız, bazılarında değil.\n"
            "Ortak hedeflerinizin olduğu konular işe yarıyor; dağınık "
            "olduğu konular yavaşlıyor.\n"
            "Hangisinin önce çözüleceğini seçmek ilişkinin yönünü "
            "netleştirir."),
        2: ("Doğal yönünüz kısmen örtüşüyor.\n"
            "Bazı konularda aynı hızı yakalıyorsunuz, bazılarında biriniz "
            "öne geçiyor.\n"
            "Birlikte işlerken küçük ama düzenli ayarlamalarla dengeleniyor."),
        3: ("Yönünüz büyük ölçüde aynı.\n"
            "Aynı şeyin neden önemli olduğunu ikiniz de benzer şekilde "
            "görüyorsunuz.\n"
            "Bu, ortak kararların ve uzun vadeli planların sağlam zemini "
            "olur."),
        4: ("Doğal yönünüz örtüşüyor.\n"
            "Ne öncelikli olduğunda kafanız benzer şekilde çalışıyor.\n"
            "Hayatın büyük kararlarında aynı tarafta durmanızı sağlar."),
        5: ("Yön uyumunuz güçlü.\n"
            "İkiniz de aynı şeye aynı şekilde değer veriyorsunuz.\n"
            "Birlikte hareket etmek zorlamaz; aksine enerji verir."),
        6: ("Doğal yönünüz neredeyse birebir aynı.\n"
            "Neyi istediğinizi birbiriniz açıklamadan anlıyorsunuz.\n"
            "Hedefe giden yolda birlikte adımlamak sırtınızı yaslayacak kadar "
            "rahat hissettirir."),
        7: ("Yön uyumunuz tam.\n"
            "Birinizin önceliği diğerinin önceliğidir.\n"
            "Ortak hayat tasarımında eşsiz bir bütünlük demektir; hedefe "
            "giden yolda hep birlikte yürürsünüz."),
    },

    # -------------------------------------------------------- iç çatışma / iç dürtü
    "nadi": {
        0: ("İkinizin doğal iç dürtüsü birbirini tamamlıyor.\n"
            "Biri bir boşluğu doldururken diğeri onu farklı bir yönden "
            "dolduruyor.\n"
            "İlişkinin gücü tam da bu tamamlayıcılıktan geliyor."),
        1: ("İç dürtüleriniz büyük ölçüde örtüşüyor.\n"
            "Aynı şeyleri farklı zamanlarda ama aynı içgüdüyle arzularsınız.\n"
            "Bu, ortak hedeflerde güçlü bir birlik yaratır."),
        2: ("İç dürtüleriniz benzer yönde.\n"
            "İkiniz de aynı eksikliği sezme eğilimindesiniz.\n"
            "Birbirinizi tamamlama ihtimali yüksek bir eşleşme."),
        3: ("İç dürtüleriniz birbirine yakın.\n"
            "Benzer ihtiyaçlara benzer şekilde tepki veriyorsunuz.\n"
            "Paylaşımın kolaylaştığı bir uyum."),
        4: ("İç dürtüleriniz büyük ölçüde örtüşüyor ama nüanslar farklı.\n"
            "Aynı şeyi hedefliyorsunuz, farklı şekillerde.\n"
            "Birlikte hareket ederken küçük çentikler oluşabilir."),
        5: ("İç dürtüleriniz bazı yerlerde çakışıyor.\n"
            "Aynı konuda farklı şeyler arzuluyor olabilirsiniz.\n"
            "Bu, ilişkide en çok konuşulması gereken alan; saklama değil "
            "açık konuşma onu yönetilebilir kılar."),
        6: ("İç dürtüleriniz belirgin biçimde çakışıyor.\n"
            "Benzer ihtiyaçlardan besleniyor ama farklı yerlere "
            "çekiliyorsunuz.\n"
            "Bu, ilişkide enerji kaybı yaratabilir; farkındalık varsa "
            "yönlendirilebilir."),
        7: ("İç dürtüleriniz neredeyse çarpışıyor.\n"
            "Aynı eksiği birbirinizde arıyorsunuz ve ikiniz de aynı yere "
            "koşuyorsunuz.\n"
            "Bu, ilişkinin en zorlu alanıdır; ama burada bir çatışma değil, "
            "iki kişinin aynı şeyi istemesi var."),
        8: ("İç dürtüleriniz birebir aynı.\n"
            "Aynı eksiğe aynı şekilde tepki veriyor, aynı şeyi "
            "arzuluyorsunuz.\n"
            "Bu, iç çatışma yaratır ama ilişkinin sonu demek değildir; aynı "
            "şeyi iki kez arıyorsanız birlikte aramak işe yarar."),
    },
}


def dogal_metin(kod: str, puan: int, aci: int) -> str:
    """`kod` kootası için `puan` değerine karşılık gelen sade metni döndürür.

    `aci`: 0 = vaat, 1 = anlatı, 2 = simge. Çağıran taraf rastgele seçer.
    """
    govde = GOVDE.get(kod, {}).get(puan)
    if govde is None:
        return ""
    return "%s\n%s" % (ACILAR.get(kod, [""] * 3)[aci % 3], govde)


def mevcut(kod: str, puan: int) -> bool:
    """Bu koota için `puan` değerine karşılık gelen metin var mı?"""
    return puan in GOVDE.get(kod, {})


#: Toplam (0-36) için sade dilde bant metinleri. `cok_dusuk` 0-17,
#: `dusuk` 18-24, `orta` 25-32, `yuksek` 33-36 aralıklarına karşılık gelir.
TOPLAM: Dict[str, Dict[str, str]] = {
    "cok_dusuk": {
        "baslik": "Zayıf bir başlangıç",
        "aciklama": ("Birlikte yürünecek çok şey var ve alışkanlık henüz "
                    "oturmamış.\n"
                    "Bu, ilişkinin kapısının kapalı olduğu anlamına "
                    "gelmez; sadece bugünkü uyumun düşük olduğunu gösterir.\n"
                    "En çok işe yarayan şey, karşınızdakini anlamaya "
                    "çalışmaktır."),
        "ipucu": ("Küçük ve düzenli adımlar büyük başlangıçlardan daha "
                  "fazla işe yarar."),
    },
    "dusuk": {
        "baslik": "Bazı alanlarda uyum var",
        "aciklama": ("İlişkinin dayandığı ve iyi gittiği alanlar var, "
                    "ama bazı konularda hâlâ uyum yok.\n"
                    "Güçlü taraflarınız ilişkiyi ayakta tutar; zayıf "
                    "alanlar birlikte çalışılmazsa zamanla ağırlaşır.\n"
                    "Bu, kötü değil ama bilinçli çalışma ister."),
        "ipucu": ("Güçlü olduğunuz alandan başlayın; kalanı zamanla "
                  "gelir."),
    },
    "orta": {
        "baslik": "Sağlam bir uyum",
        "aciklama": ("Bu aralıkta birlikteliklerin çoğu yerleşir.\n"
                    "Günlük hayatta birbirinizi yormuyorsunuz, bazı "
                    "konularda zorlanıyorsunuz ama bu konular sizi "
                    "durdurmuyor.\n"
                    "İlişki sağlam bir zeminde ve gelişmeye açık."),
        "ipucu": ("Sağlam zemin demek süresiz kalacak demek değildir; "
                  "üzerine kurulan şeyleri fark edin."),
    },
    "yuksek": {
        "baslik": "Güçlü bir uyum",
        "aciklama": ("İkinizin birbirine uyum neredeyse tam.\n"
                    "Günlük hayatta aynı dili konuşuyor, birbirinizi "
                    "anlıyorsunuz ve aynı şeyleri önemsiyorsunuz.\n"
                    "Böyle eşleşmeler nadirdir; ancak yüksek uyum "
                    "ilişkinin sonsuza kadar süreceği anlamına gelmez."),
        "ipucu": ("Güçlü uyum, iletişimi akıcı kılar; yine de derin "
                  "konuşmaların yerini tutmaz."),
    },
}


def toplam_metin(seviye: str) -> Dict[str, str]:
    """Toplam bant için sade metni döndürür."""
    return dict(TOPLAM.get(seviye, {}))
