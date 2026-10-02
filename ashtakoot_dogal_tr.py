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

import random
from typing import Dict, List, Optional

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
        "Bu alan şuna dikkat çekiyor: kazandığınızı ve kaybettiğinizi kimin "
        "nasıl karşıladığı.",
    ],
    "vashya": [
        "Bu alan şunu vaat ediyor: karşınızdakine çekilme gücünüzün ne "
        "kadar güçlü olduğunu gösterir.",
        "Bu alan şunu anlatıyor: \"gördüğümde içimde bir şey kıpırdadı\" "
        "hissinin nereden geldiğini gösterir.",
        "Bu alan şunu simgeliyor: birbirinize ilk çekildiğiniz o sessiz an.",
        "Bu alan şuna dikkat çekiyor: çekimi ilişkinin tek dayanağı "
        "sanmanın.",
    ],
    "tara": [
        "Bu alan şunu vaat ediyor: günlük ritimlerinizin ne kadar "
        "örtüştüğünü gösterir.",
        "Bu alan şunu anlatıyor: birinizin geç yatıp diğerinin erkenden "
        "kalkmasının ilişkiye etkisini gösterir.",
        "Bu alan şunu simgeliyor: aynı evde farklı saatlerin çalıştığı bir "
        "düzen.",
        "Bu alan şuna dikkat çekiyor: aynı çatı altında sürekli bir saat "
        "hesap defteri açılması.",
    ],
    "yoni": [
        "Bu alan şunu vaat ediyor: birbirinizin iç dünyasını ne kadar kolay "
        "anlayacağınızı gösterir.",
        "Bu alan şunu anlatıyor: \"acaba şu an ne hissediyor?\" sorusunun ne "
        "sıklıkta doğacağını gösterir.",
        "Bu alan şunu simgeliyor: iç dünyanızın kapısının size ne kadar açık "
        "durduğu.",
        "Bu alan şuna dikkat çekiyor: her şeyi anladığınızı sandığınız sessiz "
        "yanlışlar.",
    ],
    "graha_maitri": [
        "Bu alan şunu vaat ediyor: birbirinin aklını ne kadar kolay "
        "okuyabileceğinizi gösterir.",
        "Bu alan şunu anlatıyor: aynı olayı neden farklı anlattığınızı "
        "gösterir.",
        "Bu alan şunu simgeliyor: aynı dili konuşan iki kişinin rahatlığı.",
        "Bu alan şuna dikkat çekiyor: aynı fikirde olduğunuz için susup "
        "kalmak.",
    ],
    "gana": [
        "Bu alan şunu vaat ediyor: günlük hayatta birbirinizi yormadan "
        "yaşama ihtimalinizi gösterir.",
        "Bu alan şunu anlatıyor: tepkilerinizin neden bazen aynı anda "
        "çarpıştığını gösterir.",
        "Bu alan şunu simgeliyor: iki farklı ritmin aynı çatı altında "
        "buluşması.",
        "Bu alan şuna dikkat çekiyor: \"benim gibi yapmıyor\" cümlesinin "
        "aynen tekrarlanması.",
    ],
    "rasi": [
        "Bu alan şunu vaat ediyor: birlikte bir hedefe yürüyüp "
        "yürüyemeyeceğinizi gösterir.",
        "Bu alan şunu anlatıyor: hayatın hangi alanlarında aynı hızda "
        "olduğunuzu gösterir.",
        "Bu alan şunu simgeliyor: iki kişinin aynı haritayı "
        "okuyabilmesi.",
        "Bu alan şuna dikkat çekiyor: aynı hedefe yürümek için farklı "
        "nedenlerle yürümek.",
    ],
    "nadi": [
        "Bu alan şunu vaat ediyor: aynı eksiğin ikinizde de bulunma "
        "ihtimalini gösterir.",
        "Bu alan şunu anlatıyor: aynı şeyi neden hep birbirinizde "
        "aradığınızı gösterir.",
        "Bu alan şunu simgeliyor: aynı noktada duran iki kişinin birbirini "
        "tamamlaması ya da çarpışması.",
        "Bu alan şuna dikkat çekiyor: aynı eksiği iki kez aramanın yalnızca "
        "ikisini de bulmaması.",
    ],
}

#: Her koota için dört açı: 0 vaat, 1 anlatı, 2 simge, 3 dikkat.
ACI_SAYISI = 4

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


#: Her (koota, puan) için İKİNCİ gövde varyantı. `GOVDE` ile aynı anahtar
#: kümesini kullanır ve farklı bir bakış açısı anlatır: `GOVDE` genel
#: düzeyi tanımlayıp sonucu söyler, buradaki metin somut günlük sahneyi
#: kurar. Çağıran taraf iki varyant arasından rastgele seçer; bir puan için
#: olası metin sayısı 4 açı x 2 gövde = 8 olur.
GOVDE_ALT: Dict[str, Dict[int, str]] = {

    # ------------------------------------------------ toplumsal / değer
    "varna": {
        0: ("Harcama alışkanlıklarınız birbirinin tersi.\n"
            "Biri hesabı tutarken diğeri o an için harcar.\n"
            "Aynı bütçeyi yönetirken ikiniz farklı kuralları esas alırsınız."),
        1: ("Önemli saydığınız günler aynı günlere denk geliyor.\n"
            "Sıradan bir günü birlikte kutlamak için ikinizde de aynı sebep "
            "var.\n"
            "Böyle küçük eşleşmeler ilişkiyi görünmeden ayakta tutar."),
    },

    # ------------------------------------------------------- karşılıklı çekim
    "vashya": {
        0: ("İlgiyi gösterme biçimleriniz farklı.\n"
            "Biri davetle, diğeri uzun bir telefonla yaklaşır.\n"
            "Biri \"beni görmek istiyor\", diğeri \"seni özledim\" der; ikisi "
            "de aynı kapıdan geçer."),
        1: ("Yakınlık ile özgürlük arasında bir denge var.\n"
            "Biri yanına geldiğinde diğeri biraz uzaklaşıyor; bu soğukluk "
            "değil, nefes alma biçimi.\n"
            "Yakınlaştıkça eski mesafeyi bulmak kolaylaşır."),
        2: ("Ayrıldıktan sonra ilk yine birbirinizi arıyorsunuz.\n"
            "Kısa bir uzaklık ilgiyi bitirmez, yeniden kavuşmayı daha "
            "belirgin hâle getirir.\n"
            "Bu, ilişkinin neden ayakta kaldığını gösterir."),
    },

    # ------------------------------------------------------------ zaman / ritim
    "tara": {
        0: ("Hafta sonlarınız farklı kurulmuş.\n"
            "Biri sabah erkenden, diğeri akşamüstü hareket ediyor.\n"
            "Hangi saatte bir araya gelebileceğinizi iki hafta sonra "
            "bulursunuz."),
        1: ("Örtüşen günleriniz de var.\n"
            "Ayda bazen aynı saatte uyanıyor, bazen hiç karşılaşmıyorsunuz.\n"
            "İyi günleri seçip planlamak, uyumsuzluktan daha değerli."),
        2: ("Günleriniz benzer saatlerde başlıyor.\n"
            "İşe çıkışınız, yemeğe oturuşunuz ve uyku saatiniz birbirine "
            "yakın.\n"
            "Günün akışına süzülmek birlikte yapılacak işleri kolaylaştırır."),
        3: ("Aynı saatte yoruluyorsunuz.\n"
            "İkinizin de boşta kaldığı anlar birbirine denk geliyor.\n"
            "Yorgunlukları birlikte taşımanın en kolay hâli bu."),
    },

    # ------------------------------------------------------------ iç dünya
    "yoni": {
        0: ("Konuşmadan anlaşmayı bekliyorsunuz.\n"
            "Soru sormadan birbirinizin durumunu tahmin ediyorsunuz.\n"
            "Tahmin yanlış olduğunda karşı taraf \"beni anlamadın\" diye sessiz "
            "kalıyor."),
        1: ("Bazı konular hâlâ korunuyor.\n"
            "Bir sohbet tam ortasında ikiniz de geri çekiliyorsunuz.\n"
            "Bu alanı isim vermeden açmak, kapalı tutmaktan daha az "
            "yıpratıcı."),
        2: ("Birinin hâlini girmeden önce anlıyorsunuz.\n"
            "İyi günde olduğunu sesinden, zor gününü duruşundan "
            "çıkarıyorsunuz.\n"
            "Bu okuma gücü, sorulmadan verilen ilgiye dönüşür."),
        3: ("Sözünü tutmuyorsanız da duyduğunuzu belli ediyorsunuz.\n"
            "Karşı taraf konuşmadan önce bir kez daha kendini topluyor.\n"
            "Beklemek, bu alanda soru sormaktan daha değerli bir tercih."),
        4: ("Paylaşılmayan pek az yeriniz kaldı.\n"
            "Karşı tarafın ne düşündüğünü sormadan bilmek nadir bir durum.\n"
            "Bu kadar açıklık, birlikte karar vermeyi de kolaylaştırır."),
    },

    # ------------------------------------------------------ düşünce / iletişim
    "graha_maitri": {
        0: ("Duygularınızı farklı kelimelerle anlatıyorsunuz.\n"
            "Biri \"üzgünüm\" derken diğeri \"yorgunum\" diyor.\n"
            "Aynı durumu farklı isimlerle yaşamak yanlış anlaşılmaya yol "
            "açabilir."),
        1: ("Tartışmalarınız çoğunlukla yanlış saatte başlıyor.\n"
            "Biri acele içindeyken diğeri dinlenmeye hazır.\n"
            "Aynı fikir, iyi bir zamanda söylendiğinde farklı bir karşılık "
            "bulur."),
        2: ("Cümlenizi çoğu zaman birlikte bitiriyorsunuz.\n"
            "Birinin zor bulduğu kelimeyi diğeri neredeyse aynı anda "
            "buluyor.\n"
            "Bu, karar verme sırasında büyük zaman kazandırır."),
        3: ("Aynı sonuca farklı yollardan varabiliyorsunuz.\n"
            "Biri önce kararına varıyor, diğeri biraz sonra.\n"
            "Yolu farklı olsa da varış noktası aynı olduğunda tartışma "
            "kısalır."),
        4: ("Konuşmadan da anlaşıyorsunuz.\n"
            "Biri susunca diğeri neden susulduğunu biliyor.\n"
            "Anlaşılmadığı tek yer, söylenmeyenler olabilir."),
        5: ("Kararları neredeyse aynı anda veriyorsunuz.\n"
            "Birinin \"burayı seçtim\" demesi diğerininkinin aynısı.\n"
            "Bu, zor kararlarda bile tartışmadan geçmenizi sağlar."),
    },

    # ------------------------------------------------------------ karakter
    "gana": {
        0: ("Bir kararı iki saniyede veriyorsunuz.\n"
            "Biri daha düşünmeden söylüyor, diğeri üç seçenek "
            "sıralıyor.\n"
            "Hız ile temkin arasındaki bu fark günlük seçimlerde görünür."),
        1: ("Birinizden diğerininki olmasını beklemiyorsunuz.\n"
            "Farklı olmak için bir açıklama borçlu değilmiş gibi.\n"
            "Bu beklentisizlik, farkı sorun olmaktan çıkarır."),
        2: ("Güldüğünüz şeyler büyük ölçüde aynı.\n"
            "Aynı komik durum karşısında ikiniz de aynı anda gülüyorsunuz.\n"
            "Küçük şikayetler bu ortak espriyle çabucak kapanır."),
        3: ("Günlük tempoya birlikte yetişiyorsunuz.\n"
            "Biri yorulunca diğeri işi paylaşıyor.\n"
            "Bu, hiçbir şey söylemeden verilmiş bir destek."),
        4: ("Beğenileriniz ve iştahınız uyuşuyor.\n"
            "Aynı yemeği seçiyor, aynı programı izliyorsunuz.\n"
            "Günlük hayatta birlikte yapılacak işler fazlalıkla çıkıyor."),
        5: ("Birinin hâlinden diğeri neredeyse aynı anda etkileniyor.\n"
            "Sinirlendiğinizde ikiniz aynı anda kızıyorsunuz.\n"
            "Birlikte öfkelenip sonra birlikte sakinleşen ilişkiler için idealdir."),
        6: ("Zaman zaman sırayı bırakıyorsunuz.\n"
            "Biri öne çıkarken diğeri çekiliyor; sonra yer değiştiriyorsunuz.\n"
            "Böyle bir paylaşım, hiçbirinin hep ikinci kalmadığı bir denge "
            "kurar."),
    },

    # ------------------------------------------------------------ ortak yön
    "rasi": {
        0: ("Aynı haritayı değil, iki ayrı haritayı okuyorsunuz.\n"
            "Biri kısa vadeli hedefi, diğeri uzun vadeli planı işaret "
            "ediyor.\n"
            "Yön değiştirdiğinizde yolun nereye çıktığını yeniden sormak "
            "gerekir."),
        1: ("Üzerinde anlaştığınız bir yön var.\n"
            "O alanda tartışmadan aynı karara varıyorsunuz.\n"
            "Bu, her seferinde yeniden açılması gerekmeyen bir zemin."),
        2: ("Yavaşlayan tarafı bekliyorsunuz.\n"
            "Biri acele ediyor, diğeri emin olmak için yavaşlıyor.\n"
            "Kimi zaman bekleyen taraf da hızlanmak zorunda kalır."),
        3: ("Aynı şeyin neden önemli olduğunu aynı sebepten anlıyorsunuz.\n"
            "İkiniz de benzer deneyimlerden besleniyorsunuz.\n"
            "Bu ortak sebep, uzun vadeli planı kâğıt üstünde tutar."),
        4: ("Önceliklerinizi karşılıklı destekliyor.\n"
            "Biri \"önce şu\" dediğinde diğeri \"evet\" diyor.\n"
            "Bu, karar hızını belirleyen etken."),
        5: ("Aynı yere farklı yoldan gidiyorsunuz.\n"
            "Sonuçta aynı hedefe varıyorsunuz, aradaki yol farklı.\n"
            "Biri yoldan çekilirse diğeri yeni bir yol bulmak zorunda kalır."),
        6: ("Planı açıklamadan anlaşıyorsunuz.\n"
            "Yarın ne yapılacağı belli olduğu için konuşmaya gerek "
            "kalmıyor.\n"
            "Böyle bir plan, aranızda üçüncü biri olsa da tutardı."),
        7: ("Kararları tek başınıza değil birlikte veriyorsunuz.\n"
            "Kendi isteğinizi bir kenara bırakıp karşınızınkini önce "
            "soruyorsunuz.\n"
            "Bu, ortak hayat tasarımının en zor kısmını kolaylaştırır."),
    },

    # -------------------------------------------------------- iç çatışma / iç dürtü
    "nadi": {
        0: ("Aynı eksikliği iki farklı yoldan kapatıyorsunuz.\n"
            "Biri unutarak, diğeri çalışarak.\n"
            "Aynı boşluğu doldurma biçiminiz farklı."),
        1: ("Aynı şeyi aynı zamanda istiyorsunuz.\n"
            "Birinin canı çektiğinde diğerininki de çekiyor.\n"
            "İkiniz de neden istediğinizi açıklayabiliyorsunuz."),
        2: ("Aynı noktaya bakmıyorsunuz.\n"
            "İkiniz de göremeden aynı hataya düşüyorsunuz.\n"
            "Biri diğerinin gördüğü açığı kapatıyor."),
        3: ("Aynı eksikliğin yokluğu ikinizi aynı anda rahatsız ediyor.\n"
            "Karşı taraf ışıktayken siz de hareketleniyorsunuz.\n"
            "Bu, birbirinizi yalnız kalmaktan kurtarıyor."),
        4: ("Hedefiniz aynı, yolunuz farklı.\n"
            "Biri acele ediyor, diğeri sırasını bekliyor.\n"
            "Bekleyen taraf, acele edeni yavaşlatıyor."),
        5: ("Aynı konuda iki karşıt istek var.\n"
            "Biri daha çok birlikte, diğeri daha çok kendi alanında "
            "kalmak istiyor.\n"
            "Bu alanı konuşmak, ikisini de kısa sürede yoruyor."),
        6: ("Aynı yere iki kez ulaşıyorsunuz.\n"
            "Biri arıyor, diğeri bulamıyor; sonra sıra değişiyor.\n"
            "Bu döngüyü fark etmek, onu durdurmaktan önce gelir."),
        7: ("Birinizdeki huzursuzluk diğerinde tam karşılığını "
            "buluyor.\n"
            "Biri içini rahatlatmadan diğeri de rahatlayamıyor.\n"
            "İkiniz birlikte sakinleşmeden konuşmaya başlayamıyorsunuz."),
        8: ("Aynı şeyi öğrenmek için aynı dersi iki kez alıyorsunuz.\n"
            "Biri kırıldığında diğeri de kırılıyor.\n"
            "Bu ikinci tur, ilkinden daha kısa sürüyor."),
    },
}


def govde_varyantlari(kod: str, puan: int) -> List[str]:
    """`kod`/`puan` için eldeki tüm gövde varyantlarını döndürür.

    `GOVDE` her zaman ilk varyanttır; `GOVDE_ALT` doluysa ikincisi de
    listeye eklenir. Böylece tek gövdesi olan eski kootalar bozulmaz.
    """
    ilk = GOVDE.get(kod, {}).get(puan)
    if ilk is None:
        return []
    liste = [ilk]
    ikinci = GOVDE_ALT.get(kod, {}).get(puan)
    if ikinci is not None:
        liste.append(ikinci)
    return liste


def dogal_metin(kod: str, puan: int, aci: int,
                govde_index: Optional[int] = None) -> str:
    """`kod` kootası için `puan` değerine karşılık gelen sade metni döndürür.

    `aci`: 0 = vaat, 1 = anlatı, 2 = simge, 3 = dikkat.
    `govde_index`: gövde varyantı. `None` ise mevcut varyantlar arasından
    rastgele seçilir. Çağıran taraf açıyı da rastgele seçer; bir puan için
    olası metin sayısı 4 x 2 = 8.
    """
    govde = GOVDE.get(kod, {}).get(puan)
    if govde is None:
        return ""
    if govde_index is None:
        govde_index = random.randrange(len(govde_varyantlari(kod, puan)))
    return "%s\n%s" % (ACILAR.get(kod, [""] * ACI_SAYISI)[aci % ACI_SAYISI],
                       govde_varyantlari(kod, puan)[govde_index])


def mevcut(kod: str, puan: int) -> bool:
    """Bu koota için `puan` değerine karşılık gelen metin var mı?"""
    return puan in GOVDE.get(kod, {})


#: Toplam puan için sade dilde genel ilişki yorumları.
#: Azami 36 olsa da ulaşılabilir toplamlar 7-34 aralığındadır (28 değer,
#: boşluksuz). Bu yüzden bantlar ölçülen aralığa göre kurulur:
#: `cok_dusuk` 7-13 (Zayıf ilişki), `dusuk` 14-20 (Orta ilişki),
#: `orta` 21-27 (İdeal ilişki), `yuksek` 28-34 (Kuvvetli ilişki).
TOPLAM: Dict[str, Dict[str, str]] = {
    "cok_dusuk": {
        "baslik": "Zayıf ilişki",
        "aciklama": ("7–13 puan aralığı. Birlikte yürünecek çok şey var ve "
                    "alışkanlık henüz oturmamış.\n"
                    "Bu, ilişkinin kapısının kapalı olduğu anlamına "
                    "gelmez; sadece bugünkü uyumun düşük olduğunu "
                    "gösterir.\n"
                    "En çok işe yarayan şey, karşınızdakini anlamaya "
                    "çalışmaktır."),
        "ipucu": ("Küçük ve düzenli adımlar büyük başlangıçlardan daha "
                  "fazla işe yarar."),
    },
    "dusuk": {
        "baslik": "Orta ilişki",
        "aciklama": ("14–20 puan aralığı. İlişkinin dayandığı ve iyi "
                    "gittiği alanlar var, ama bazı konularda hâlâ uyum "
                    "yok.\n"
                    "Güçlü taraflarınız ilişkiyi ayakta tutar; zayıf "
                    "alanlar birlikte çalışılmazsa zamanla ağırlaşır.\n"
                    "Bu, kötü değil ama bilinçli çalışma ister."),
        "ipucu": ("Güçlü olduğunuz alandan başlayın; kalanı zamanla "
                  "gelir."),
    },
    "orta": {
        "baslik": "İdeal ilişki",
        "aciklama": ("21–27 puan aralığı. Günlük hayatta birbirinizi "
                    "yormuyorsunuz ve birlikteliklerin çoğu yerleşiyor.\n"
                    "Bazı konularda zorlanıyorsunuz ama bu konular sizi "
                    "durdurmuyor; üstelik nerede zorlandığınızı ikiniz de "
                    "biliyorsunuz.\n"
                    "İlişki sağlam bir zeminde ve gelişmeye açık."),
        "ipucu": ("Sağlam zemin demek süresiz kalacak demek değildir; "
                  "üzerine kurulan şeyleri fark edin."),
    },
    "yuksek": {
        "baslik": "Kuvvetli ilişki",
        "aciklama": ("28–34 puan aralığı. İkinizin birbirine uyum "
                    "neredeyse tam.\n"
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
