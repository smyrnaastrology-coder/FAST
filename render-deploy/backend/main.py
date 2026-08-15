import os, sys, logging, base64, stripe, json, hmac, hashlib, re
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

logging.disable(logging.CRITICAL)
os.environ.setdefault("STREAMLIT_RUN", "0")
os.environ.setdefault("STREAMLIT_SUPPRESS_WARNINGS", "1")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_PROJECT_ROOT)

import swisseph as swe
from core import FBST_Engine
from core.i18n import pdf_label, get_lang as _i18n_get_lang
from core.data import ARAP_ILISKI
from core.utils import (
    GEZEGENLER, get_planetary_position, kadersel_yildiz_taramasi,
    aci_farki_safe, sehir_veritabani_yukle, sehir_bul,
    get_safe_flags, dereceyi_burca_cevir, sehir_ara,
    ULKE_SEHIR_DB as ULKE_SEHIR_DB,
)

# GEZEGENLER'de eksik olan asteroid ID'leri (swe.AST_OFFSET tabanlı)
ASTEROID_ID_MAP = {
    "Juno": swe.AST_OFFSET + 3, "Ceres": swe.AST_OFFSET + 1,
    "Pallas": swe.AST_OFFSET + 2, "Vesta": swe.AST_OFFSET + 4,
    "Eros": swe.AST_OFFSET + 433, "Psyche": swe.AST_OFFSET + 16,
    "Sappho": swe.AST_OFFSET + 80, "Amor": swe.AST_OFFSET + 1221,
}

# GEZEGEN_ACG - ACG hesaplamalari icin gezegen ID'leri
GEZEGEN_ACG = {
    "Güneş": 0, "Ay": 1, "Merkür": 2, "Venüs": 3, "Mars": 4,
    "Jüpiter": 5, "Satürn": 6, "Uranüs": 7, "Neptün": 8, "Plüton": 9,
}

# GEZEGEN_ANLAMLARI - ACG icin gezegen anlamlari
GEZEGEN_ANLAMLARI = {
    "Güneş": {"para": 8, "huzur": 5, "tutku": 6},
    "Ay": {"para": 4, "huzur": 9, "tutku": 3},
    "Merkür": {"para": 6, "huzur": 5, "tutku": 4},
    "Venüs": {"para": 7, "huzur": 9, "tutku": 7},
    "Mars": {"para": 6, "huzur": 3, "tutku": 9},
    "Jüpiter": {"para": 9, "huzur": 7, "tutku": 5},
    "Satürn": {"para": 7, "huzur": 4, "tutku": 3},
    "Uranüs": {"para": 8, "huzur": 5, "tutku": 7},
    "Neptün": {"para": 5, "huzur": 8, "tutku": 6},
    "Plüton": {"para": 9, "huzur": 3, "tutku": 8},
}

def _strip_html(text):
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text).strip()

def _bireysellestir(text):
    """Replace relationship-focused language with individual life language."""
    if not text or not isinstance(text, str): return text
    if _i18n_get_lang() == "en": return text
    subs = [
        ("İlişkinin", "Hayatın"), ("ilişkinin", "hayatın"),
        ("ilişkinizde", "hayatınızda"), ("ilişkinizden", "hayatınızdan"),
        ("ilişkinize", "hayatınıza"), ("ilişkiniz", "hayatınız"),
        ("ilişkide", "hayatta"), ("ilişkiyi", "hayatı"),
        ("ilişkinizi", "hayatınızı"), ("ilişkiye", "hayata"),
        ("ilişkideki", "hayattaki"), ("ilişkinin", "hayatın"),
        ("ilişkinizle", "hayatınızla"),
        ("Partnerinizin", "Kendinizin"), ("partnerinizin", "kendinizin"),
        ("Partneriniz", "Kendiniz"), ("partneriniz", "kendiniz"),
        ("partnerinize", "kendinize"), ("partnerinizden", "kendinizden"),
        ("partnerinizle", "kendinizle"),
        ("Partnerine", "Kendine"), ("partnerine", "kendine"),
        ("Partnerinin", "Kendinin"), ("partnerinin", "kendinin"),
        ("partneriyle", "kendisiyle"), ("partneri", "kendisi"),
        ("Partner", "Kendi"), ("partner", "kendi"),
        ("çift olarak", "birey olarak"), ("Çift olarak", "Birey olarak"),
        ("çiftin", "kişinin"), ("Çiftin", "Kişinin"),
        ("aranızda", "içinizde"), ("Aranızda", "İçinizde"),
        ("birbirinize", "kendinize"), ("birbirinizi", "kendinizi"),
        ("birbirinizle", "kendinizle"), ("birbirinizin", "kendinizin"),
        ("Birbirinize", "Kendinize"), ("Birbirinizi", "Kendinizi"),
        ("birbirinin", "kendinin"), ("Birbirinin", "Kendinin"),
        ("ikili ilişki", "hayat"), ("İkili ilişki", "Hayat"),
        ("ikili bir", ""), ("İkili bir", ""), ("ikili", ""), ("İkili", ""),
        ("ortak", "kişisel"), ("Ortak", "Kişisel"),
        ("birlikte", ""), ("Birlikte", ""),
        ("bu ilişkinin", "hayatınızın"), ("Bu ilişkinin", "Hayatınızın"),
        ("bu ilişki", "hayat"), ("Bu ilişki", "Hayat"),
        ("ilişkinizin", "hayatınızın"), ("İlişkinizin", "Hayatınızın"),
    ]
    for old, new in subs:
        text = text.replace(old, new)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ── Natal Moon Aspect Library: 3 interpretations per aspect ──
NATAL_AY_ACISI_YORUMLARI = {
    # ─────────── Ay + Güneş ───────────
    ("Ay","Güneş","Kavuşum"): [
        "Duygularınızla benliğiniz bugün tam bir uyum içinde. İç sesinizle mantığınız aynı şeyi söylüyor. Kendinize olan güveniniz artıyor ve bu enerji çevrenize de yansıyor.",
        "Kalbinizle aklınız arasında nadir bir birlik var. Ne istediğinizi net görüyor, hislerinizden emin adımlarla ilerliyorsunuz. Bugün kendiniz olmanın gücünü sonuna kadar hissedin.",
        "İçsel bütünlük günü: Hisleriniz ve düşünceleriniz aynı frekansta titreşiyor. Bu uyum sayesinde zor kararları bile kolaylıkla verebilir, çevrenize doğal bir otorite yayabilirsiniz."
    ],
    ("Ay","Güneş","Karşıt"): [
        "İç dünyanızda bir denge arayışı var. Mantığınız bir şey söylerken kalbiniz başka bir yöne çekiyor. Bu gerilim aslında size hangi yolda ilerlemeniz gerektiğini göstermek için var.",
        "Duygusal ihtiyaçlarınızla ego hedefleriniz arasında bir çatışma hissedebilirsiniz. Bugün iki sesi de dinleyin. Uzlaşma, ikisinin arasında değil, ikisini de kucaklamakta.",
        "Zıtlıkların farkındalık getirdiği bir gün. İçsel bir gerilim yaşıyor olabilirsiniz, ancak bu size kendinizin henüz keşfetmediğiniz yönlerini gösterecek. Dengenizi bulmak için her iki tarafı da anlamaya çalışın."
    ],
    ("Ay","Güneş","Kare"): [
        "Duygularınızla hedefleriniz arasında sıkışmış hissedebilirsiniz. Ne tarafa gideceğinizi bilememek doğal. Bu belirsizlik, yeni bir yön bulmanız için size alan açıyor.",
        "İçsel bir baskı altındasınız. Kalbinizle aklınız arasındaki bu gerilim, bir karar vermeniz gerektiğinin işareti. Ertelemeyin, küçük bir adım bile sizi rahatlatacak.",
        "Bugün kendinizle yüzleşme günü. İçsel çatışmalarınız size büyüme fırsatı sunuyor. Rahatsız edici duygulara direnmeyin; onları anlamaya çalışın, size bir şey öğretmek için buradalar."
    ],
    ("Ay","Güneş","Trigon"): [
        "Duygusal dünyanız ve kimliğiniz arasında doğal bir uyum var. Bugün kendinizi olduğunuz gibi kabul etmek kolaylaşıyor. İç huzurunuz dış dünyaya yansıyor.",
        "Akışta olduğunuz bir gün. Hislerinizle eylemleriniz arasında pürüzsüz bir bağlantı var. Yaratıcılığınız yüksek, sezgileriniz güçlü. Bu enerjiyi değerlendirin.",
        "Kendinizle barışık hissettiğiniz bir zaman dilimi. İçsel uyumunuz sayesinde çevrenizdeki insanlara da huzur yayıyorsunuz. Bugün keyif aldığınız şeylere zaman ayırın."
    ],
    ("Ay","Güneş","Sekstil"): [
        "Duygularınızı ifade etmek için güzel bir fırsat kapınızda. Bugün karşınıza çıkacak bir durum, içinizdeki gerçek hisleri açığa çıkarmanıza yardımcı olacak.",
        "İç dünyanızla dış dünyanız arasında verimli bir köprü kuruluyor. Yeni bir hobi, yaratıcı bir proje veya kendinizi ifade edeceğiniz bir alan size iyi gelecek.",
        "Duygusal zekanızın yükseldiği bir gün. Çevrenizdeki insanları anlamak ve onlarla bağ kurmak kolaylaşıyor. Bu fırsatı samimi bir sohbet için değerlendirin."
    ],
    # ─────────── Ay + Venüs ───────────
    ("Ay","Venüs","Kavuşum"): [
        "Sevgi enerjiniz bugün çok yüksek. Kalbinizdeki sıcaklık çevrenize de yansıyor. Sanatsal ve estetik konulara yönelmek, kendinizi güzel şeylerle çevrelemek size iyi gelecek.",
        "Duygusal olarak şefkat dolu hissediyorsunuz. İçgüdüsel olarak güzellik ve uyum arayışındasınız. Bugün kendinize küçük bir jest yapın, bunu hak ediyorsunuz.",
        "Vermek ve almak arasındaki denge bugün doğal olarak kuruluyor. Sevginizi ifade etmekten çekinmeyin. Yaratıcılık gerektiren işler için ilham alabilirsiniz."
    ],
    ("Ay","Venüs","Karşıt"): [
        "Duygusal ihtiyaçlarınızla keyif aldığınız şeyler arasında bir seçim yapmanız gerekebilir. Kendinize hangi alanda daha fazla yatırım yapmak istediğinizi sorun.",
        "İçsel bir tatminsizlik hissedebilirsiniz. İstediğiniz şeyle ihtiyacınız olan şey aynı olmayabilir. Bugün biraz yalnız kalıp içinizi dinleyin.",
        "Sevgi ve para arasında bir denge kurma zamanı. Değer verdiğiniz şeylerle harcadığınız enerji arasında bir uyumsuzluk varsa, bugün bunu fark edip düzeltebilirsiniz."
    ],
    ("Ay","Venüs","Kare"): [
        "Keyif aldığınız şeylerle sorumluluklarınız arasında sıkışmış hissedebilirsiniz. Kendinize zaman ayırmakta zorlanıyorsanız, küçük bir mola bile büyük fark yaratır.",
        "Harcama isteğinizle tasarruf etme gerekliliğiniz çatışabilir. Bugün alacağınız kararlarda kalbinizi değil, mantığınızı dinleyin. Geçici bir heves sizi yanıltmasın.",
        "İlişkilerde bir denge sorunu yaşayabilirsiniz. Fazla verip az almak veya tam tersi. Bugün sınırlarınızı gözden geçirin ve kendinizi koruyun."
    ],
    ("Ay","Venüs","Trigon"): [
        "Sevgi ve güzellik hayatınızda doğal bir akış yakalıyor. İç huzurunuz dış dünyaya yansıyor. Sanatsal faaliyetler, müzik veya doğa yürüyüşü size iyi gelecek.",
        "Sosyal çevrenizle aranızda doğal bir uyum var. Bugün sevdiklerinizle vakit geçirmek, güzel bir yemek yapmak veya estetik bir ortamda bulunmak size enerji verecek.",
        "Kendinizi şımartma günü. Venüs ve Ay arasındaki bu uyumlu açı, size hayatın güzel yanlarını görme fırsatı sunuyor. Küçük zevklerin tadını çıkarın."
    ],
    ("Ay","Venüs","Sekstil"): [
        "Yeni bir güzellik keşfi sizi bekliyor olabilir. Belki yeni bir kafe, belki bir sergi, belki de bir melodi. Bugün estetik duyarlılığınız yüksek, çevrenize dikkat edin.",
        "Sosyalleşmek için güzel bir fırsat. Yeni insanlarla tanışabilir veya eski dostlarla bir araya gelebilirsiniz. İletişiminiz akıcı ve sıcak olacak.",
        "Kendinizi ifade etmenin yeni bir yolunu bulabilirsiniz. Bir hobi edinmek veya yaratıcı bir projeye başlamak için ilham verici bir gün."
    ],
    # ─────────── Ay + Mars ───────────
    ("Ay","Mars","Kavuşum"): [
        "Enerjiniz ve duygularınız aynı anda harekete geçiyor. İçinizde güçlü bir yapma arzusu var. Bu enerjiyi spor veya fiziksel bir aktiviteye yönlendirmek size iyi gelecek.",
        "Duygusal tepkileriniz normalden daha yoğun olabilir. Öfkenizi tanıyın ama kontrol etmesini de bilin. Bu enerji, doğru kanalize edildiğinde büyük bir itici güç.",
        "Cesaret ve tutku günü. Uzun zamandır ertelediğiniz bir şeye başlamak için mükemmel bir zaman. İçgüdülerinize güvenin ve harekete geçin."
    ],
    ("Ay","Mars","Karşıt"): [
        "İçsel arzularınızla dış dünyanın talepleri arasında kalabilirsiniz. İsteklerinizle zorunluluklarınız arasında bir denge kurmak için çaba göstermeniz gerekebilir.",
        "Duygusal olarak gergin hissedebilir, tepkileriniz normalden daha sert olabilir. Bir çatışmaya girmeden önce derin bir nefes alın ve düşünün.",
        "Başkalarının enerjisi sizi etkileyebilir. Kendi sınırlarınızı koruyun ve başkalarının sorunlarını üstlenmeyin. Fiziksel egzersiz bu gerilimi atmanıza yardımcı olacak."
    ],
    ("Ay","Mars","Kare"): [
        "İçinizde bir volkan hazırda bekliyor olabilir. Küçük bir kıvılcım büyük bir patlamaya dönüşebilir. Bugün sakin kalmak için bilinçli çaba gösterin.",
        "Duygusal öfkenizle mantığınız arasında sıkıştınız. Bir şeyleri kırıp dökmek istiyor ama durmanız gerektiğini de biliyorsunuz. Fiziksel bir aktivite bu baskıyı azaltabilir.",
        "Sabırsızlık ve huzursuzluk hissedebilirsiniz. Her şey sizi rahatsız ediyor gibi gelebilir. Bu geçici bir dönem, kendinize zaman tanıyın ve zorlamayın."
    ],
    ("Ay","Mars","Trigon"): [
        "Enerjiniz ve duygularınız mükemmel bir uyum içinde. Yapmak istediğiniz her şeyde başarılı olma potansiyeliniz yüksek. Spor, yaratıcı projeler veya yeni başlangıçlar için ideal.",
        "Cesaretiniz ve azminiz zirvede. Zor görünen bir iş bile bugün size kolay gelebilir. İçgüdüsel olarak doğru hamleleri yapıyor, akışa teslim oluyorsunuz.",
        "Fiziksel ve duygusal olarak güçlü hissettiğiniz bir gün. Kendinize güveniyor ve harekete geçmek için hiç vakit kaybetmiyorsunuz. Bu enerjiyi verimli kullanın."
    ],
    ("Ay","Mars","Sekstil"): [
        "Yeni bir fiziksel aktiviteye başlamak için güzel bir fırsat. Dans, yoga, koşu veya takım sporu size iyi gelebilir. Bedeniniz ve ruhunuz birlikte çalışmak istiyor.",
        "Duygusal cesaretiniz artıyor. Bugün karşınıza çıkacak bir fırsat, içinizdeki savaşçıyı uyandırabilir. Korkularınızın üzerine gidin.",
        "Enerjinizi yönlendirebileceğiniz yeni bir alan keşfedebilirsiniz. Bir hobi, bir proje veya bir spor dalı size hem fiziksel hem duygusal tatmin sağlayacak."
    ],
    # ─────────── Ay + Jüpiter ───────────
    ("Ay","Jüpiter","Kavuşum"): [
        "İyimserlik ve neşe duygularınız bugün tavan yapıyor. Hayata daha geniş bir perspektiften bakıyor, geleceğe umutla yaklaşıyorsunuz. Yeni deneyimlere açık olun.",
        "Duygusal olarak genişleme ve özgürleşme hissediyorsunuz. İçsel bir bolluk ve bereket duygusu var. Bu enerjiyi sevdiklerinizle paylaşmak size iyi gelecek.",
        "Macera ve keşif arzunuz artıyor. Yeni bir yer görmek, farklı bir kültür tanımak veya sadece bilmediğiniz bir sokakta yürümek bile size iyi gelebilir."
    ],
    ("Ay","Jüpiter","Karşıt"): [
        "İçsel büyüme arzunuzla dış dünyanın sınırlamaları arasında kalabilirsiniz. Daha fazlasını istiyor ama mevcut koşullar sizi kısıtlıyor olabilir. Sabırlı olun.",
        "Abartma eğilimindesiniz. Duygularınızı veya harcamalarınızı kontrol etmekte zorlanabilirsiniz. Bugün ölçülü olmaya çalışın.",
        "Başkalarının beklentileriyle kendi istekleriniz arasında bir denge kurmanız gerekebilir. Kendi yolunuzu bulmak için iç sesinizi dinleyin."
    ],
    ("Ay","Jüpiter","Kare"): [
        "Aşırı iyimserlik gerçekçiliğinizi gölgeleyebilir. Büyük hayaller kurmak güzel ama bugün ayaklarınız yere basmalı. Bir adım geri çekilip durumu objektif değerlendirin.",
        "Duygusal olarak abartıya kaçma eğilimindesiniz. Ne hissettiğinizle ne yaptığınız arasında bir dengesizlik olabilir. Bugün ölçülü olmaya özen gösterin.",
        "Kendinizi kanıtlama ihtiyacı duyabilirsiniz. Ancak başkalarını etkilemek için kendinizi zorlamayın. Olduğunuz gibi kabul edilmek en büyük özgürlük."
    ],
    ("Ay","Jüpiter","Trigon"): [
        "İçsel bolluk ve bereket duygunuz doğal bir akış içinde. Hayat size güzel sürprizler sunabilir. Minnettarlık duygusu bugün kalbinizi ısıtacak.",
        "Öğrenme ve keşfetme arzunuz artıyor. Bir kitap okumak, belgesel izlemek veya yeni bir beceri öğrenmek için harika bir gün. Zihniniz ve kalbiniz birlikte çalışıyor.",
        "İyimserlik enerjiniz çevrenizdeki insanları da etkiliyor. Bugün pozitif düşüncelerinizi paylaşın, sevdiklerinize ilham verin. Sosyalleşmek için ideal."
    ],
    ("Ay","Jüpiter","Sekstil"): [
        "Yeni bir öğrenme fırsatı kapınızda olabilir. Bir eğitim programı, seminer veya atölye ilginizi çekebilir. Kişisel gelişiminize yatırım yapmak için güzel bir zaman.",
        "Kültürel bir etkinlik veya seyahat planı size iyi gelebilir. Farklı perspektifler görmek, ufkunuzu genişletecek. Bugün yeni bir şey deneyin.",
        "İçsel bilgeliğinize güvenin. Bir konuda doğru bildiğiniz bir şey varsa, bunu paylaşmaktan çekinmeyin. Çevrenizdeki insanlara ilham verebilirsiniz."
    ],
    # ─────────── Ay + Satürn ───────────
    ("Ay","Satürn","Kavuşum"): [
        "Duygusal olarak daha ciddi ve mesafeli hissedebilirsiniz. İç dünyanızda bir sorgulama var. Bu, duygusal olgunlaşma sürecinizin bir parçası. Kendinize karşı dürüst olun.",
        "Sorumluluklarınızın ağırlığını hissediyorsunuz. Duygusal yükünüz artmış olabilir. Bugün kendinize şefkat gösterin ve yalnız olmadığınızı hatırlayın.",
        "İçsel sınırlarınızı keşfetme günü. Nerede durmanız, nerede ilerlemeniz gerektiğini sorguluyorsunuz. Bu disiplin, uzun vadede size duygusal güvenlik sağlayacak."
    ],
    ("Ay","Satürn","Karşıt"): [
        "Duygusal ihtiyaçlarınızla sorumluluklarınız arasında bir çatışma yaşıyorsunuz. İç sesiniz size bir şey söylerken, dış dünya başka bir şey bekliyor. Dengeyi bulmak sizin elinizde.",
        "Yalnızlık hissi ağır basabilir. Başkaları tarafından anlaşılmadığınızı düşünebilirsiniz. Bu geçici bir duygu, kendinizi izole etmek yerine bir arkadaşınıza ulaşın.",
        "Geçmişten gelen bir duygusal yük bugün yüzeye çıkabilir. Affetmek ve bırakmak, üzerinizdeki bu yükü hafifletecek. Kendinize zaman tanıyın."
    ],
    ("Ay","Satürn","Kare"): [
        "Duygusal olarak baskı altında hissediyorsunuz. Bir konuda yetersiz veya hazırlıksız olabilirsiniz. Bu duyguyu bir öğrenme fırsatı olarak görün.",
        "Kendinizi eleştirme eğiliminiz artıyor. Mükemmeliyetçilik bugün size zor anlar yaşatabilir. Her şeyin mükemmel olması gerekmediğini hatırlayın.",
        "Duygusal bir engelle karşılaşabilirsiniz. Planlarınız aksayabilir veya bir konuda hayal kırıklığı yaşayabilirsiniz. Bu sizi güçlendirecek bir test."
    ],
    ("Ay","Satürn","Trigon"): [
        "Duygusal disiplininiz ve olgunluğunuz sayesinde zorlukları kolaylıkla aşıyorsunuz. İçsel gücünüzün farkında olmak size güven veriyor.",
        "Yapılandırılmış bir duygusal yaklaşım benimsiyorsunuz. Duygularınızı kontrol altında tutmak yerine onları yönetmeyi öğreniyorsunuz. Bu büyümenin işareti.",
        "Uzun vadeli hedeflerinize odaklanmak için güzel bir gün. Duygusal istikrarınız sayesinde sağlam adımlar atabiliyor, geleceğe güvenle bakabiliyorsunuz."
    ],
    ("Ay","Satürn","Sekstil"): [
        "Duygusal olarak daha organize ve planlı olmanızı sağlayacak bir fırsat karşınızda. Bir alışkanlık edinmek veya bir rutin oluşturmak için güzel bir zaman.",
        "Geçmişten gelen bir ders bugün işinize yarayabilir. Daha önce zorlandığınız bir konuda şimdi daha olgun ve hazır hissediyorsunuz.",
        "Bir mentor veya rehberden gelebilecek bir tavsiye size iyi gelecek. Deneyimli birinin perspektifi, duygusal bir konuda size yol gösterebilir."
    ],
    # ─────────── Ay + Merkür ───────────
    ("Ay","Merkür","Kavuşum"): [
        "Duygularınızı ifade etme gücünüz artıyor. İçinizdekileri kelimelere dökmek kolaylaşıyor. Yazmak, konuşmak veya birine derdinizi anlatmak için harika bir gün.",
        "Sezgileriniz ve mantığınız aynı anda çalışıyor. Bir konuyu hem kalbinizle hem aklınızla kavrıyorsunuz. İkisi arasında bir çelişki varsa, bugün netleşecek.",
        "Zihniniz ve kalbiniz arasında güçlü bir bağlantı var. Duygusal zekanız yüksek, insanları anlama ve onlarla empati kurma yeteneğiniz artıyor."
    ],
    ("Ay","Merkür","Karşıt"): [
        "Duygularınızla düşünceleriniz arasında bir çelişki yaşıyorsunuz. Mantığınız bir şey söylerken kalbiniz başka bir şey hissediyor. İkisini de dinleyin.",
        "Başkalarıyla iletişimde yanlış anlaşılmalar olabilir. Söylediklerinizle hissettikleriniz arasında bir fark varsa, bugün bu farkı kapatmaya çalışın.",
        "Duygusal bir konuyu fazla düşünüp kafanızı karıştırabilirsiniz. Bazen analiz etmek yerine hissetmek gerekir. Zihninizi susturup kalbinizi dinleyin."
    ],
    ("Ay","Merkür","Kare"): [
        "Zihinsel olarak dağınık ve odaklanmakta zorlanabilirsiniz. Duygularınız düşüncelerinizi bulandırıyor olabilir. Bugün önemli kararlar vermekten kaçının.",
        "Söylemek istediklerinizle söyledikleriniz arasında fark olabilir. Kendinizi ifade etmekte zorlanıyorsanız, yazmak size yardımcı olabilir.",
        "Duygusal bir konu hakkında takıntılı düşüncelere kapılabilirsiniz. Bu döngüden çıkmak için zihninizi başka bir şeye yönlendirin."
    ],
    ("Ay","Merkür","Trigon"): [
        "Duygularınızı ifade etmek için mükemmel bir gün. İç sesiniz net, kelimeleriniz akıcı. Birine duygularınızı anlatmak veya bir mektup yazmak size iyi gelecek.",
        "Sezgileriniz ve mantığınız uyum içinde. Bir konuyu hem hissediyor hem anlıyorsunuz. Bu bütünsel bakış açısı sayesinde doğru kararlar verebilirsiniz.",
        "Öğrenme ve iletişim yeteneğiniz artıyor. Yeni bir dil öğrenmek, bir kitap okumak veya bir konuda araştırma yapmak için ideal bir gün."
    ],
    ("Ay","Merkür","Sekstil"): [
        "Yeni bir iletişim fırsatı kapınızda. Eski bir arkadaşınızdan haber alabilir veya yeni biriyle anlamlı bir sohbet edebilirsiniz.",
        "Duygusal zekanızı kullanabileceğiniz bir durumla karşılaşabilirsiniz. Birine tavsiye vermek veya onu anlamak size iyi gelecek.",
        "Yazmak veya yaratıcı bir şey üretmek için ilham alabilirsiniz. Bir günlük tutmak, şiir yazmak veya blog paylaşımı yapmak duygularınızı ifade etmenize yardımcı olacak."
    ],
    # ─────────── Ay + Uranüs ───────────
    ("Ay","Uranüs","Kavuşum"): [
        "Duygusal olarak ani bir özgürleşme ihtiyacı hissedebilirsiniz. Rutinler sizi boğuyor, yeni ve farklı bir şey yapmak istiyorsunuz. İçgüdülerinize güvenin.",
        "Beklenmedik bir duygusal farkındalık yaşayabilirsiniz. Birdenbire bir konuyu çok net görmeye başlayabilirsiniz. Bu aydınlanma anını değerlendirin.",
        "Özgürlüğünüze düşkün olduğunuz bir gün. Başkalarının beklentilerine göre değil, kendi kurallarınıza göre yaşamak istiyorsunuz. Bu enerjiyi yaratıcı bir şekilde kullanın."
    ],
    ("Ay","Uranüs","Karşıt"): [
        "İstikrar arzunuzla değişim ihtiyacınız arasında kalabilirsiniz. Bir yandan güvende olmak istiyor, bir yandan da sınırlarınızı zorlamak. Bu ikilem size büyüme fırsatı sunuyor.",
        "Başkalarının beklentileriyle kendi özgürlük ihtiyacınız arasında bir gerilim var. Kendi yolunuzu bulmak için cesur olmanız gerekebilir.",
        "Duygusal olarak ani tepkiler verebilir, sonra pişman olabilirsiniz. Bir şey söylemeden veya yapmadan önce bir kez daha düşünün."
    ],
    ("Ay","Uranüs","Kare"): [
        "Beklenmedik bir duygusal patlama yaşayabilirsiniz. Uzun zamandır bastırdığınız bir duygu bugün aniden yüzeye çıkabilir. Şaşırmayın, bu doğal.",
        "Rutininizin bozulması sizi rahatsız edebilir. Planlarınızın dışına çıkmak zorunda kalmak, başta sinir bozucu olsa da yeni bir kapı aralayabilir.",
        "Duygusal dalgalanmalar yaşayabilirsiniz. Bir an mutlu, bir an hüzünlü hissedebilirsiniz. Bu geçici bir dönem, kendinizi akışa bırakın."
    ],
    ("Ay","Uranüs","Trigon"): [
        "İçsel özgürlüğünüzü keşfettiğiniz bir gün. Kendi kurallarınızla yaşamanın tadını çıkarıyorsunuz. Yaratıcılığınız ve özgünlüğünüz çevrenizi etkiliyor.",
        "Ani bir ilham patlaması yaşayabilirsiniz. Yaratıcı bir proje için mükemmel bir fikir aklınıza gelebilir. Bu ilhamı kaçırmayın, hemen not alın.",
        "Değişim ve yenilik size iyi geliyor. Farklı bir ortam, yeni insanlar veya alışılmadık bir deneyim, içinizdeki potansiyeli ortaya çıkarabilir."
    ],
    ("Ay","Uranüs","Sekstil"): [
        "Yeni ve sıra dışı bir deneyim için fırsat kapınızda. Daha önce hiç yapmadığınız bir şeyi denemek, size enerji verebilir.",
        "Bir konuda farklı bir perspektif kazanabilirsiniz. Alışılmışın dışında bir düşünce, bir soruna yaratıcı bir çözüm bulmanızı sağlayabilir.",
        "Teknoloji veya yenilikçi bir alanla ilgilenmek size iyi gelebilir. Yeni bir uygulama keşfetmek veya dijital bir projeye başlamak için güzel bir gün."
    ],
    # ─────────── Ay + Neptün ───────────
    ("Ay","Neptün","Kavuşum"): [
        "Sezgileriniz bugün çok güçlü. İnsanları ve olayları kelimelerin ötesinde hissediyorsunuz. Meditasyon, müzik veya sanat size derin bir huzur verecek.",
        "Duygusal olarak sınırlarınızın eridiğini hissedebilir, her şeyle bir bağlantı içinde olduğunuzu görebilirsiniz. Bu birleşme duygusu size şifa veriyor.",
        "Hayal gücünüz ve duygularınız iç içe geçiyor. Rüyalarınız daha canlı, sezgileriniz daha net olabilir. Bugün iç sesinize kulak verin."
    ],
    ("Ay","Neptün","Karşıt"): [
        "Gerçeklikle hayal dünyanız arasında gidip gelebilirsiniz. Bir şeyleri olduğundan farklı görüyor olabilirsiniz. Bugün önemli kararlar vermekten kaçının.",
        "Duygusal olarak kafa karışıklığı yaşayabilir, bir konuda net görmekte zorlanabilirsiniz. Bir süre geri çekilip durumu berraklaştırın.",
        "Başkalarının enerjisi sizi kolayca etkileyebilir. Duygusal sınırlarınız zayıflamış olabilir. Kendinizi korumak için yalnız kalabileceğiniz bir alan yaratın."
    ],
    ("Ay","Neptün","Kare"): [
        "Duygusal bir sisin içinde kaybolmuş hissedebilirsiniz. Neyin gerçek neyin hayal olduğunu ayırt etmek zorlaşabilir. Bugün kendinize karşı dürüst olun.",
        "Kaçış eğiliminiz artabilir. Gerçeklikten uzaklaşmak için hayallere, alkole veya başka bir bağımlılığa yönelebilirsiniz. Farkında olun ve sağlıklı alternatifler bulun.",
        "Aldatılma veya hayal kırıklığı yaşama olasılığınız yüksek. Birine veya bir duruma fazla güvenmeyin. Gerçekçi olun."
    ],
    ("Ay","Neptün","Trigon"): [
        "Sezgileriniz ve hayal gücünüz arasında doğal bir akış var. Sanatsal bir proje, yaratıcı bir çalışma veya manevi bir uygulama için mükemmel bir gün.",
        "İçsel huzur ve dinginlik hissediyorsunuz. Doğada vakit geçirmek, müzik dinlemek veya meditasyon yapmak size derin bir tatmin verecek.",
        "Empati yeteneğiniz çok yüksek. İnsanları anlamak ve onlara yardım etmek için doğal bir yeteneğiniz var. Bugün bu gücünüzü kullanın."
    ],
    ("Ay","Neptün","Sekstil"): [
        "Yaratıcılığınızı besleyecek bir fırsat karşınızda. Bir sanat atölyesi, fotoğraf gezisi veya müzik etkinliği size iyi gelebilir.",
        "Manevi bir deneyim yaşayabilirsiniz. Bir kitap, bir konuşma veya bir doğa anısı size derin bir anlayış kazandırabilir.",
        "Sezgileriniz bugün size yol gösterecek. Bir konuda içinizde bir his varsa, onu ciddiye alın. Mantığınız açıklayamasa da kalbiniz doğruyu biliyor."
    ],
    # ─────────── Ay + Plüton ───────────
    ("Ay","Plüton","Kavuşum"): [
        "Duygusal bir dönüşümün tam ortasındasınız. Bastırılmış duygular bugün yüzeye çıkabilir. Korkutucu görünse de bu yüzleşme sizi özgürleştirecek.",
        "İçsel gücünüzün farkına vardığınız bir gün. Kontrol edemediğiniz şeyleri bırakmak, aslında en büyük güçlenme biçiminiz. Dönüşüme açık olun.",
        "Derin bir duygusal arınma yaşıyorsunuz. Eski yaralar, geçmiş travmalar bugün kendini gösterebilir. Bu, onları iyileştirmek için bir fırsat."
    ],
    ("Ay","Plüton","Karşıt"): [
        "Kontrol etmekle bırakmak arasında bir savaş veriyorsunuz. Bir durumu tutmaya çalıştıkça daha çok kaybediyor gibi hissedebilirsiniz. Bırakmak en büyük zafer.",
        "Başkalarının gölgesi sizi etkileyebilir. Birinin size yansıttığı duyguları kendinize almayın. Kendi gücünüzü hatırlayın.",
        "Duygusal bir hesaplaşma zamanı. Geçmişte yaşadığınız bir olay bugün tekrar gündeme gelebilir. Bu sefer aynı şekilde tepki vermek zorunda değilsiniz."
    ],
    ("Ay","Plüton","Kare"): [
        "Duygusal yoğunluğunuz tavan yapmış durumda. Küçük bir olay büyük bir tepkiye dönüşebilir. Bugün kendinize ekstra özen gösterin ve tetikleyicilerinizi tanıyın.",
        "İçsel bir güç mücadelesi yaşıyorsunuz. Eski alışkanlıklarınızla yeni benliğiniz arasında sıkışmış hissedebilirsiniz. Dönüşüm acı verici olabilir ama gerekli.",
        "Takıntılı düşünceler ve duygular sizi ele geçirebilir. Bir konuyu bırakmakta zorlanıyorsanız, profesyonel destek almak iyi bir fikir olabilir."
    ],
    ("Ay","Plüton","Trigon"): [
        "Duygusal dönüşüm gücünüz doğal bir akış içinde çalışıyor. Zor bir konuyu kolaylıkla çözebilir, derin bir anlayışla hareket edebilirsiniz.",
        "İçsel iyileşme ve şifa enerjiniz yüksek. Geçmiş yaralarınızı sarmak, eski kalıplarınızı kırmak için güçlü bir dönemdesiniz.",
        "Başkalarını iyileştirme ve dönüştürme yeteneğiniz artıyor. Birine destek olmak, rehberlik etmek size iyi gelecek. Bu süreçte siz de iyileşiyorsunuz."
    ],
    ("Ay","Plüton","Sekstil"): [
        "Derin bir psikolojik içgörü kazanabilirsiniz. Bir rüya, bir terapi seansı veya derin bir sohbet, size kendinizle ilgili yeni bir şey öğretebilir.",
        "Geçmişten gelen bir konuyu araştırmak veya aile geçmişinizi keşfetmek size iyi gelebilir. Köklerinizi anlamak, bugünkü davranışlarınızı açıklayabilir.",
        "Bir konuda gizli kalmış bir gerçeği öğrenebilirsiniz. Bu bilgi başta sarsıcı olsa da, uzun vadede size özgürlük getirecek."
    ],
}  # 45 keys × 3 = 135 interpretations

# ── Natal Moon Sign & House descriptors ──
AY_BURC_TANIMLARI = {
    "Koç": "Ay'ınız Koç burcunda — duygularınız ateşli, ani ve doğrudan. İçgüdüsel tepkileriniz güçlü, cesur ve atılgan.",
    "Boğa": "Ay'ınız Boğa burcunda — duygusal istikrar ve güvenlik arayışındasınız. Konfor ve rahatlık sizin için önemli.",
    "İkizler": "Ay'ınız İkizler burcunda — duygularınızı kelimelere dökme ihtiyacı hissediyorsunuz. Meraklı ve iletişim odaklı bir duygusal yapınız var.",
    "Yengeç": "Ay'ınız Yengeç burcunda — Ay kendi evinde, duygularınız son derece derin ve korumacı. Aile ve yuva kavramı içinizde güçlü.",
    "Aslan": "Ay'ınız Aslan burcunda — duygusal ifadeniz sıcak, cömert ve gösterişli. Kalbinizle hareket eder, onur ve gurur sizin için önemlidir.",
    "Başak": "Ay'ınız Başak burcunda — duygularınızı analiz eder, mantıklı çerçeveye oturtmaya çalışırsınız. Düzen ve temizlik size huzur verir.",
    "Terazi": "Ay'ınız Terazi burcunda — duygusal denge ve uyum arayışı içindesiniz. Estetik, zarafet ve adalet duygularınızı besler.",
    "Akrep": "Ay'ınız Akrep burcunda — duygularınız yoğun, tutkulu ve dönüştürücü. Derinlerde gizlenen hisleriniz güçlüdür.",
    "Yay": "Ay'ınız Yay burcunda — duygusal özgürlük ve keşif sizi besler. İyimser, maceracı ve bağımsız bir duygusal yapınız var.",
    "Oğlak": "Ay'ınız Oğlak burcunda — duygularınız kontrollü, disiplinli ve sorumlu. Duygusal güvenlik başarı ve statü ile bağlantılı.",
    "Kova": "Ay'ınız Kova burcunda — duygusal olarak özgür, bağımsız ve alışılmadık. Özgünlüğünüze değer verir, duygusal mesafenizi korursunuz.",
    "Balık": "Ay'ınız Balık burcunda — duygularınız akışkan, sezgisel ve sınırsız. Empati yeteneğiniz yüksek, sanatsal ve manevi yönünüz güçlü.",
}

AY_EV_TANIMLARI = {
    1: "Ay 1. evde — duygusal dışavurumunuz güçlü, hisleriniz yüzünüzde okunur. Kendi ihtiyaçlarınız ön planda.",
    2: "Ay 2. evde — duygusal güvenliğiniz maddi istikrarla bağlantılı. Sahip olduklarınıza duygusal bağ geliştirirsiniz.",
    3: "Ay 3. evde — duygularınızı iletişim yoluyla ifade edersiniz. Yakın çevreniz ve kardeşleriniz duygusal dünyanızda önemli yer tutar.",
    4: "Ay 4. evde — aile ve yuva duygusal merkeziniz. Geçmişiniz, kökleriniz ve annenizle bağlantınız güçlü.",
    5: "Ay 5. evde — duygularınızı yaratıcılık ve eğlence yoluyla ifade edersiniz. Romantizm ve çocuklarla ilgili konular ön planda.",
    6: "Ay 6. evde — duygusal sağlığınız günlük rutin ve iş hayatınızla bağlantılı. Hizmet etmek ve yardım etmek size iyi gelir.",
    7: "Ay 7. evde — duygusal ihtiyaçlarınız yakın ilişkiler ve ortaklıklar üzerinden şekillenir. Denge ve uyum arayışındasınız.",
    8: "Ay 8. evde — duygusal derinlik, dönüşüm ve paylaşılan kaynaklar ön planda. Mahremiyet ve güven konuları hassastır.",
    9: "Ay 9. evde — duygusal beslenmeniz seyahat, felsefe ve yüksek öğrenim yoluyla gelir. Keşif ve anlam arayışı duygusal ihtiyacınız.",
    10: "Ay 10. evde — duygusal ifadeniz kariyer ve toplumsal statü üzerinden görünür. Duygusal güvenlik başarı ile bağlantılı.",
    11: "Ay 11. evde — arkadaşlıklar ve toplumsal gruplar duygusal dünyanızda önemli. İdealist hedefler sizi besler.",
    12: "Ay 12. evde — duygularınız bilinçaltı düzeyde akar. Yalnızlık, meditasyon ve içsel çalışma size iyi gelir.",
}

def _ay_ortami_yorumu(ay_burc, ay_ev):
    """Ay'ın bulunduğu burç ve eve göre ortam tanımı döndürür."""
    _EN = _i18n_get_lang() == "en"
    burc_tanim = AY_BURC_TANIMLARI.get(ay_burc, ("Your Moon is shaping your emotional world." if _EN else "Ay duygusal dünyanızı şekillendiriyor."))
    ev_tanim = AY_EV_TANIMLARI.get(ay_ev, "")
    return f"{burc_tanim} {ev_tanim}"

def _aspekt_yorumu_sec(gezegen1, gezegen2, aci_turu, index=0):
    """NATAL_AY_ACISI_YORUMLARI'ndan bir yorum seçer."""
    _EN = _i18n_get_lang() == "en"
    key = (gezegen1, gezegen2, aci_turu)
    if key in NATAL_AY_ACISI_YORUMLARI:
        return NATAL_AY_ACISI_YORUMLARI[key][index % 3]
    # Try reverse order
    rev_key = (gezegen2, gezegen1, aci_turu)
    if rev_key in NATAL_AY_ACISI_YORUMLARI:
        return NATAL_AY_ACISI_YORUMLARI[rev_key][index % 3]
    # Fallback by aspect type
    FALLBACK = {
        "Kavuşum": "Bu birleşme enerjisi duygusal dünyanızı güçlendiriyor.",
        "Karşıt": "Bu karşıtlık duygusal dengenizi test ediyor, farkındalık getiriyor.",
        "Kare": "Bu zorlu açı duygusal büyüme için bir sınav sunuyor.",
        "Trigon": "Bu uyumlu açı duygusal akışınızı destekliyor.",
        "Sekstil": "Bu fırsat açısı duygusal gelişim için bir kapı aralıyor.",
    }
    FALLBACK_EN = {
        "Kavuşum": "This conjunction energy is strengthening your emotional world.",
        "Karşıt": "This opposition is testing your emotional balance, bringing awareness.",
        "Kare": "This challenging aspect offers a test for emotional growth.",
        "Trigon": "This harmonious aspect supports your emotional flow.",
        "Sekstil": "This opportunity aspect opens a door for emotional development.",
    }
    if _EN:
        return FALLBACK_EN.get(aci_turu, "This aspect is affecting your emotional world.")
    return FALLBACK.get(aci_turu, "Bu açı duygusal dünyanızı etkiliyor.")

def _natal_gunluk_hava_durumu(motor):
    """Daily Moon transit weather: transit Ay → natal gezegenler, 3 gün."""
    import datetime, random
    from datetime import timedelta
    try:

        BURCLAR = ["Koç","Boğa","İkizler","Yengeç","Aslan","Başak","Terazi","Akrep","Yay","Oğlak","Kova","Balık"]
        jd_natal = motor.get_natal_julian_day("p1")
        bugun = datetime.datetime.now()
        sonuclar = []
        for gun_kaydir in range(3):  # today + 2 more days
            gun = bugun + timedelta(days=gun_kaydir)
            jd_transit = swe.julday(gun.year, gun.month, gun.day, 12.0)
            # Transit Ay pozisyonu
            ay_id = GEZEGENLER.get("Ay")
            if ay_id is None: continue
            ay_deg = swe.calc_ut(jd_transit, ay_id)[0][0]
            ay_burc = BURCLAR[int(ay_deg // 30)]
            ay_burc_no = int(ay_deg // 30)
            # Transit Ay evi (house cusps)
            cusps, ascmc = swe.houses(jd_natal, motor.enlem, motor.boylam, b'P')
            def _house_of(deg):
                for i in range(12):
                    bas = cusps[i]; bit = cusps[(i+1)%12]
                    if bas <= bit:
                        if bas <= deg < bit: return i+1
                    else:
                        if deg >= bas or deg < bit: return i+1
                return 1
            ay_ev = _house_of(ay_deg)
            ortam = _ay_ortami_yorumu(ay_burc, ay_ev)
            # Aspects transit Ay → natal planets
            aciklamalar = []
            gorusler = []
            hedef_list = ["Güneş","Merkür","Venüs","Mars","Jüpiter","Satürn","Uranüs","Neptün","Plüton","Chiron"]
            for gez in hedef_list:
                g_id = GEZEGENLER.get(gez)
                if g_id is None: continue
                try:
                    g_deg = swe.calc_ut(jd_natal, g_id)[0][0]
                except: continue
                fark = abs(ay_deg - g_deg)
                if fark > 180: fark = 360 - fark
                # Aspect type detection
                aci_turu = None
                orb = 0
                for (aci_dk, aci_adi, orb_max) in [(0,"Kavuşum",8),(180,"Karşıt",8),(90,"Kare",6),(120,"Trigon",6),(60,"Sekstil",4)]:
                    if abs(fark - aci_dk) <= orb_max:
                        aci_turu = aci_adi
                        orb = abs(fark - aci_dk)
                        break
                if aci_turu and fark >= 1:
                    index = (gun_kaydir + len(aciklamalar)) % 3
                    yorum = _aspekt_yorumu_sec("Ay", gez, aci_turu, index)
                    aciklamalar.append(f"{aci_turu} ∟ {gez} (orb {orb:.1f}°): {yorum}")
            if not aciklamalar:
                aciklamalar.append(f"Sakin bir geçiş — Ay bugün belirgin bir açı yapmıyor.")
            # Pick 2-3 aspect highlights
            rng = random.Random(str(jd_transit))
            rng.shuffle(aciklamalar)
            highlight = aciklamalar[:3]
            hava = {
                "tarih": gun.strftime("%Y-%m-%d"),
                "gun_ad": ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"][gun.weekday()],
                "ay_burc": ay_burc,
                "ay_ev": ay_ev,
                "ay_derece": round(ay_deg, 1),
                "ortam": ortam,
                "yorum": "\n".join(highlight),
                "acilar": aciklamalar,
            }
            sonuclar.append(hava)
        return sonuclar
    except Exception as e:
        import traceback; traceback.print_exc()
        return [{"tarih":"","gun_ad":"Hata","ay_burc":"","ay_ev":0,"ortam":"","yorum":f"Hava durumu alınamadı: {e}","acilar":[]}]

def _natal_minor_progress_yorumlari(motor, gun_sayisi=3, baslangic_gunu=0):
    """Daily minor progress (secondary progression) for next N days.
    Each "day" = 1 symbolic progression year (1 after birth = 1 year of life).
    Returns entries for the next progression years."""
    import datetime
    from datetime import timedelta
    try:
        _EN = _i18n_get_lang() == "en"
        GUN_AD = (["Mon","Tue","Wed","Thu","Fri","Sat","Sun"] if _EN else ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"])
        BURCLAR = ["Koç","Boğa","İkizler","Yengeç","Aslan","Başak","Terazi","Akrep","Yay","Oğlak","Kova","Balık"]

        jd_natal = motor.get_natal_julian_day("p1")
        cusps, ascmc = swe.houses(jd_natal, motor.enlem, motor.boylam, b'P')
        def _house_of(deg):
            for i in range(12):
                bas = cusps[i]; bit = cusps[(i+1)%12]
                if bas <= bit:
                    if bas <= deg < bit: return i+1
                else:
                    if deg >= bas or deg < bit: return i+1
            return 1
        
        bugun = datetime.datetime.now()
        jd_now = swe.julday(bugun.year, bugun.month, bugun.day, 12.0)
        # Current age in years (for secondary progression: 1 day = 1 year)
        yas = (jd_now - jd_natal) / 365.25
        
        sonuclar = []
        for kaydir in range(baslangic_gunu, baslangic_gunu + gun_sayisi):
            # Progressed JD = birth JD + (current age + N) as days
            jd_prog = jd_natal + yas + kaydir
            
            # Planet positions at progressed JD
            gez_poz = {}
            for g_ad, g_id in list(GEZEGENLER.items())[:14]:
                try:
                    gez_poz[g_ad] = swe.calc_ut(jd_prog, g_id)[0][0]
                except:
                    pass
            
            ay_derece = gez_poz.get("Ay", 0)
            gunes_derece = gez_poz.get("Güneş", 0)
            ay_burc = BURCLAR[int(ay_derece // 30)]
            gunes_burc = BURCLAR[int(gunes_derece // 30)]
            ay_ev = _house_of(float(ay_derece))
            
            ortam = _ay_ortami_yorumu(ay_burc, ay_ev)
            
            # Ay aspects to other progressed planets
            aci_tipleri = [(0,"Kavuşum",8),(180,"Karşıt",8),(90,"Kare",6),(120,"Trigon",6),(60,"Sekstil",4)]
            hedefler = ["Güneş","Merkür","Venüs","Mars","Jüpiter","Satürn","Uranüs","Neptün","Plüton","Chiron"]
            aspekt_yorumlari = []
            for hedef in hedefler:
                if hedef not in gez_poz: continue
                fark = abs(ay_derece - gez_poz[hedef])
                if fark > 180: fark = 360 - fark
                aci_turu = None
                for (aci_dk, aci_adi, orb_max) in aci_tipleri:
                    if abs(fark - aci_dk) <= orb_max:
                        aci_turu = aci_adi; break
                if aci_turu and fark >= 1:
                    index = (kaydir + len(aspekt_yorumlari)) % 3
                    yorum = _aspekt_yorumu_sec("Ay", hedef, aci_turu, index)
                    aspekt_yorumlari.append(f"{hedef} {aci_turu}: {yorum}")
            
            if not aspekt_yorumlari:
                aspekt_yorumlari.append(("No prominent Moon aspect was found for this period." if _EN else "Bu dönem için belirgin bir Ay açısı bulunamadı."))
            
            # Pick 2-3 aspects max
            if len(aspekt_yorumlari) > 3:
                import random
                rng = random.Random(str(jd_prog))
                rng.shuffle(aspekt_yorumlari)
                aspekt_yorumlari = aspekt_yorumlari[:3]
            
            prog_yili = int(bugun.year + kaydir)
            gun_tarih = bugun + timedelta(days=kaydir)
            
            entry = {
                "tarih": gun_tarih.strftime("%Y-%m-%d"),
                "gun_ad": GUN_AD[gun_tarih.weekday()],
                "yil": prog_yili,
                "ay_burc": ay_burc,
                "gunes_burc": gunes_burc,
                "ay_ev": ay_ev,
                "ortam": ortam,
                "aspekt_adet": len(aspekt_yorumlari),
                "yorumlar": aspekt_yorumlari,
            }
            sonuclar.append(entry)
        return sonuclar
    except Exception as e:
        import traceback, sys
        traceback.print_exc(file=sys.stdout)
        _EN_err = _i18n_get_lang() == "en"
        return [{"tarih":"","gun_ad":("Error" if _EN_err else "Hata"),"yil":0,"ay_burc":"","gunes_burc":"","ay_ev":0,"ortam":"","aspekt_adet":0,"yorumlar":[("Progress interpretation could not be retrieved: " if _EN_err else "İlerleme yorumu alınamadı: ") + str(e)]}]

def _natal_minor_progress_6month(motor):
    """6-month daily minor progress for PDF — returns a pre-formatted HTML string."""
    import datetime
    from datetime import timedelta
    try:
        entries = _natal_minor_progress_yorumlari(motor, gun_sayisi=180)
        if not entries:
            return "Önümüzdeki 6 ay boyunca minör bir tetiklenme bulunmuyor. Stabil bir akıştasınız."
        
        # Group by month
        aylar_tr = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
        lines = []
        for e in entries:
            t = e.get("tarih","")
            if not t:
                continue
            try:
                dt = datetime.datetime.strptime(t, "%Y-%m-%d")
                ay_ad = aylar_tr[dt.month - 1]
                lines.append(
                    f"<b>{dt.day} {ay_ad} {dt.year}</b> — "
                    f"Ay {e['ay_burc']} ({e['ay_ev']}. Ev) | "
                    f"{' | '.join(e['yorumlar'][:2])}"
                )
            except:
                continue
        
        if not lines:
            return "Önümüzdeki 6 ay boyunca minör bir tetiklenme bulunmuyor. Stabil bir akıştasınız."
        return "<br/>".join(lines)
    except Exception as e:
        return f"6 aylık minör progress raporu alınamadı: {e}"

app_fast = FastAPI(title="FAST — Asartepe Sinastri Tekniği API", version="4.0")

app_fast.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from starlette.middleware.gzip import GZipMiddleware
    app_fast.add_middleware(GZipMiddleware, minimum_size=1024)
except Exception:
    pass

# ─── In-memory engine cache ───
_ENGINE_CACHE = {}
_ENGINE_CACHE_MAX = 12

def _cache_engine(motor):
    sid = motor._session_id
    _ENGINE_CACHE[sid] = motor
    if len(_ENGINE_CACHE) > _ENGINE_CACHE_MAX:
        for k in list(_ENGINE_CACHE)[:-_ENGINE_CACHE_MAX]:
            del _ENGINE_CACHE[k]

def _get_engine(sid: str):
    return _ENGINE_CACHE.get(sid)

# ─── Analiz sonuc cache + tek-kilitleme + 429 ───
import hashlib as _hashlib
import threading as _threading
_ANALIZ_CACHE = {}
_ANALIZ_CACHE_MAX = 40
_ANALIZ_RUNNING = {}
_ANALIZ_GLOBAL_LOCK = _threading.Lock()

def _analiz_hash(tag, girdi):
    try:
        _g = girdi.dict()
    except Exception:
        _g = girdi
    _s = tag + "::" + str(sorted(_g.items()))
    return _hashlib.md5(_s.encode("utf-8", "ignore")).hexdigest()

def _analiz_sonuc(tag, girdi, calistir):
    """Cache + single-flight + 429:
    - Ayni girdi hesaplanmissa cache'ten aninda doner.
    - Ayni girdi su an hesaplaniyorsa bekler ve sonucu alir (kuyruk yok).
    - Farkli bir girdi hesaplanirken farkli istek gelirse 429 doner.
    """
    h = _analiz_hash(tag, girdi)
    r = _ANALIZ_CACHE.get(h)
    if r is not None:
        return r, None
    ev = _ANALIZ_RUNNING.get(h)
    if ev is not None:
        ev.wait()
        r = _ANALIZ_CACHE.get(h)
        if r is not None:
            return r, None
    if not _ANALIZ_GLOBAL_LOCK.acquire(blocking=False):
        return None, HTTPException(429, "Sunucu su anda mesgul, kisa sure sonra tekrar deneyin.")
    try:
        ev = _threading.Event()
        _ANALIZ_RUNNING[h] = ev
        try:
            r = calistir()
            _ANALIZ_CACHE[h] = r
            if len(_ANALIZ_CACHE) > _ANALIZ_CACHE_MAX:
                for _k in list(_ANALIZ_CACHE)[:-_ANALIZ_CACHE_MAX]:
                    del _ANALIZ_CACHE[_k]
            return r, None
        finally:
            _ANALIZ_RUNNING.pop(h, None)
            ev.set()
    finally:
        _ANALIZ_GLOBAL_LOCK.release()

# ─── Request Models ───

class EsSevgiliInput(BaseModel):
    p1_isim: str = ""
    p1_tarih: str
    p2_isim: str = ""
    p2_tarih: str
    event_tarih: str
    event_saat: str = "12:00"
    sehir: str = "İstanbul"
    ulke: str = "Türkiye"
    enlem: float = 41.0082
    boylam: float = 28.9784
    utc_offset: Optional[float] = None
    lang: str = "tr"

class EbeveynCocukInput(BaseModel):
    ebeveyn_isim: str = ""
    ebeveyn_tarih: str
    ebeveyn_rolu: str = "anne"
    cocuk_isim: str = ""
    cocuk_tarih: str
    cocuk_saat: str = "12:00"
    sehir: str = "İstanbul"
    ulke: str = "Türkiye"
    enlem: float = 41.0082
    boylam: float = 28.9784
    utc_offset: Optional[float] = None
    lang: str = "tr"

class PotansiyelYetenekInput(BaseModel):
    isim: str = ""
    tarih: str
    saat: str = "12:00"
    sehir: str = "İstanbul"
    ulke: str = "Türkiye"
    enlem: float = 41.0082
    boylam: float = 28.9784
    utc_offset: Optional[float] = None
    lang: str = "tr"

class BireyselNatalInput(BaseModel):
    isim: str = ""
    tarih: str
    saat: str = "12:00"
    sehir: str = "İstanbul"
    ulke: str = "Türkiye"
    enlem: float = 41.0082
    boylam: float = 28.9784
    utc_offset: Optional[float] = None
    lang: str = "tr"

class SehirInput(BaseModel):
    arama: str

class AlternatifInput(BaseModel):
    session_id: str
    sehir: str
    enlem: float
    boylam: float
    utc_offset: Optional[float] = None

class AstroInput(BaseModel):
    session_id: str = ""
    sehir: str = ""
    enlem: float = 41.0082
    boylam: float = 28.9784
    tarih: str = ""
    saat: str = "12:00"

# ─── Helpers ───

_TR_AYLAR = {"ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "mayis": 5, "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8, "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12, "aralik": 12}

def _parse_date(d: str) -> str:
    d = (d or "").strip()
    if not d:
        return datetime.now().strftime("%Y-%m-%d")
    d = d.replace("/", "-").replace(".", "-")
    parts = d.split("-")
    if len(parts) == 3:
        if len(parts[0]) == 4:
            return d
        else:
            return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
    for ay_tr, ay_num in _TR_AYLAR.items():
        if f" {ay_tr} " in f" {d.lower()} ":
            par = d.lower().split(" ")
            if len(par) == 3 and par[1] == ay_tr and par[0].isdigit() and par[2].isdigit():
                return f"{int(par[2])}-{ay_num:02d}-{int(par[0]):02d}"
    return d

def _generate_ek_charts(motor):
    sid = motor._session_id
    motor.ciz_titresim_grafigi(dosya_adi=f"{sid}_Frekans.png")
    motor.ciz_composite_harita(dosya_adi=f"{sid}_Composite.png")
    motor.ciz_aci_gridi(dosya_adi=f"{sid}_Aci_Gridi.png")
    motor.ciz_arap_noktalari_radar(dosya_adi=f"{sid}_Arap_Noktalari.png")

def _generate_pdf(motor, tip="rapor"):
    try:
        from core.i18n import set_lang as _pdflang
        _pdflang(motor._lang)
    except Exception:
        pass
    if tip == "natal":
        _generate_natal_pdf(motor)
    elif tip == "potansiyel":
        motor.pdf_potansiyel_rapor_uret(dosya_adi=f"{motor._session_id}_Potansiyel_Yetenek.pdf")
    else:
        motor.pdf_rapor_uret(dosya_adi=f"{motor._session_id}_Cift_Tarafli_Kontrat.pdf")

def _html_bolumleri_ayir(html):
    """Split '<b>Baslik:</b> icerik' HTML into (baslik, icerik) pairs.
    Kurallar:
    - '📅' ile baslayan ilk kalin etiket (sayfa basligi) atlanir.
    - Iki nokta icermeyen TAMAMI BUYUK kalin etiket = ust baslik (parent).
    - ':' ile biten kalin etiket = bolum basligi.
    - Diger kalinlar (orn. burc adi) icerige karistirilir.
    Icerigi olmayan basliklar bir sonraki dolan bolume baglanir."""
    bolumler = []
    if not html or not isinstance(html, str):
        return bolumler

    def _tag_ayikla(s):
        return re.sub(r"<[^>]+>", "", s or "")

    parcalar = re.split(r"<b>(.*?)</b>", html)
    metin = ""
    son_heading = None
    parent = None
    for i in range(0, len(parcalar), 2):
        metin += _tag_ayikla(parcalar[i])
        if i + 1 >= len(parcalar):
            break
        bold = _tag_ayikla(parcalar[i + 1]).strip()
        if not bold:
            continue
        if bold.startswith("📅") and parent is None:
            metin = ""
            continue
        if ":" not in bold and bold.upper() == bold:
            parent = bold
            metin = ""
            continue
        if bold.endswith(":"):
            icerik = " ".join(metin.split())
            if icerik.strip("• "):
                bolumler.append(((parent or son_heading) or "", icerik))
                parent = None
            son_heading = bold
            metin = ""
        else:
            metin += bold + " "
    icerik = " ".join(metin.split())
    if icerik.strip("• "):
        bolumler.append(((parent or son_heading) or "", icerik))
    return bolumler

def _etki_temizle(etki):
    """Clean a raw city-effect line for the PDF."""
    e = str(etki).replace("[K]", "").replace("[S]", "").replace("⚠️", "").strip()
    if _i18n_get_lang() == "en":
        e = e.replace("↑ Yükselen", "↑ Ascendant").replace("↓ Alçalan", "↓ Descendant")
    else:
        e = e.replace("↑ Yükselen", "Yükselen ekseni").replace("↓ Alçalan", "Alçalan ekseni")
    e = e.replace("⌃ MC", "MC ekseni").replace("⌄ IC", "IC ekseni")
    if "→" in e:
        oncesi, sonrasi = e.split("→", 1)
        e = oncesi.strip() + (f": {sonrasi.strip()}" if sonrasi.strip() else "")
    else:
        e = e.strip()
    return e

def _generate_natal_pdf(motor):
    """Generate a professional Bireysel Natal PDF — clean cards, proper spacing."""
    try:
        from core.i18n import set_lang as _pdflang2
        _pdflang2(motor._lang)
    except Exception:
        pass
    _EN = _i18n_get_lang() == "en"
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_dir = os.path.join(_PROJECT_ROOT, "dejavu-sans")
    pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(font_dir, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(font_dir, "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Oblique", os.path.join(font_dir, "DejaVuSans-Oblique.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-BoldOblique", os.path.join(font_dir, "DejaVuSans-BoldOblique.ttf")))

    dosya = f"{motor._session_id}_Bireysel_Natal.pdf"
    yol = os.path.join(_PROJECT_ROOT, dosya)
    w, h = A4
    c = canvas.Canvas(yol, pagesize=A4)

    # ── Colors — black & polished-gold theme ──
    altin = HexColor('#E6C14F')
    koyu = HexColor('#F0E6D2')
    acik = HexColor('#B8A87F')
    gri = HexColor('#D4AF37')
    bg = HexColor('#0B0B0F')
    kart_bg = HexColor('#16161C')
    bordo = HexColor('#E6C14F')
    yesil = HexColor('#8FBF8F')
    sari_cizgi = HexColor('#8A6D2B')
    bar_zemin = HexColor('#2A2A30')

    # ── Element pastel palette (color-coded life areas) ──
    ELEMENT_RENK = {
        "Ateş": HexColor('#F2A65A'),
        "Toprak": HexColor('#A9C97E'),
        "Hava": HexColor('#8FC0E8'),
        "Su": HexColor('#9FB2E8'),
    }
    ELEMENT_DEGER = {
        "Ateş": ("#F2A65A", "#4A2C10"),
        "Toprak": ("#A9C97E", "#24381A"),
        "Hava": ("#8FC0E8", "#1C2E40"),
        "Su": ("#9FB2E8", "#232B4A"),
    }
    # ── Astrological glyphs (all verified in DejaVuSans) ──
    GEZEGEN_GLIF = {
        "Güneş": "☉", "Ay": "☽", "Merkür": "☿", "Venüs": "♀", "Mars": "♂",
        "Jüpiter": "♃", "Satürn": "♄", "Uranüs": "♅", "Neptün": "♆", "Plüton": "♇",
        "Chiron": "✕", "Lilith": "⚸",
    }
    ACI_GLIF = {"Kavuşum": "☌", "Karşıt": "☍", "Kare": "□", "Trigon": "△", "Sekstil": "⚹"}
    # ── Global Kader Pusulası category colors ──
    KAT_RENK = {
        "para": HexColor('#A9C97E'),
        "huzur": HexColor('#8FC0E8'),
        "tutku": HexColor('#F2A65A'),
        "kriz": HexColor('#C78F9E'),
    }

    toc_cizildi = [False]  # mutable flag: back-to-TOC links drawn once TOC page exists

    SAYFA_UST = h - 60
    SAYFA_ALT = 55
    SOL = 55
    SAG = w - 55

    def yeni_sayfa():
        c.showPage()
        c.setFillColor(bg)
        c.rect(0, 0, w, h, fill=1)
        c.setStrokeColor(altin)
        c.setLineWidth(1.5)
        c.line(50, h - 40, w - 50, h - 40)
        c.setStrokeColor(altin)
        c.setLineWidth(0.5)
        c.line(50, 45, w - 50, 45)
        # Page number bottom-right
        c.setFillColor(HexColor('#8A8A8A'))
        c.setFont("DejaVu", 7)
        c.drawRightString(w - 55, 22, f"{pdf_label('Sayfa')} {c.getPageNumber()}")
        # "Back to contents" link — bottom-left
        if toc_cizildi[0]:
            c.linkAbsolute("", "icindekiler", (SOL, 26, SOL + 130, 42))
            c.setFillColor(acik)
            c.setFont("DejaVu", 7)
            c.drawString(SOL + 2, 29, pdf_label("↑ İçindekilere Dön"))
        c.setFillColor(HexColor('#5A5348'))
        c.setFont("DejaVu", 7)
        c.drawString(SOL + 2, 22, pdf_label("FAST · Asartepe Sinastri Tekniği"))

    def sayfa_basligi(baslik, y=SAYFA_UST, numara=""):
        c.setFont("DejaVu-Bold", 18)
        c.setFillColor(koyu)
        # Draw section number in gold box if provided
        if numara:
            c.setFillColor(altin)
            c.roundRect(SOL - 4, y - 2, 24, 22, 3, fill=1, stroke=0)
            c.setFillColor(HexColor('#FFFFFF'))
            c.setFont("DejaVu-Bold", 11)
            c.drawCentredString(SOL + 8, y + 2, numara)
            c.setFont("DejaVu-Bold", 18)
            c.setFillColor(koyu)
            c.drawString(SOL + 30, y, baslik)
        else:
            c.drawString(SOL, y, baslik)
        c.setStrokeColor(altin)
        c.setLineWidth(1)
        cx = SOL + (30 if numara else 0)
        c.line(cx, y - 6, cx + len(baslik) * 9.5, y - 6)
        return y - 28

    def kart_ciz(x, y, genislik, yukseklik, baslik="", baslik_icon=""):
        """Draw a card with background, border, and optional header."""
        c.setFillColor(kart_bg)
        c.roundRect(x, y, genislik, yukseklik, 6, fill=1, stroke=0)
        c.setStrokeColor(gri)
        c.setLineWidth(0.6)
        c.roundRect(x, y, genislik, yukseklik, 6, fill=0, stroke=1)
        if baslik:
            icon_temiz = re.sub(r'[\U0001F000-\U0001FAFF\uFE0F\u20E3]', '', str(baslik_icon))
            c.setFillColor(bordo)
            c.setFont("DejaVu-Bold", 10)
            c.drawString(x + 12, y + yukseklik - 18, f"{icon_temiz} {baslik}" if icon_temiz else baslik)
            c.setStrokeColor(sari_cizgi)
            c.setLineWidth(0.4)
            c.line(x + 12, y + yukseklik - 24, x + genislik - 12, y + yukseklik - 24)
        return y + yukseklik

    def metin_yaz(x, y, metin, font="DejaVu", boyut=8.5, renk=acik, max_genislik=90):
        """Write wrapped text, return new y position."""
        c.setFont(font, boyut)
        c.setFillColor(renk)
        for satir in _wrap_text(metin, max_genislik):
            if y < SAYFA_ALT:
                yeni_sayfa()
                y = SAYFA_UST
                c.setFont(font, boyut)
                c.setFillColor(renk)
            c.drawString(x, y, satir)
            y -= boyut + 3.5
        return y

    def yazi_olcul(metin, font="DejaVu", boyut=8.5, max_genislik=90):
        """Calculate how tall the text block will be."""
        satirlar = _wrap_text(metin, max_genislik)
        return len(satirlar) * (boyut + 3.5)

    def bolum_ayraci(y):
        """Draw a decorative gold section separator."""
        if y < SAYFA_ALT + 30: return y
        y -= 10
        c.setStrokeColor(altin)
        c.setLineWidth(0.8)
        mid = (SOL + SAG) / 2
        c.line(mid - 100, y, mid + 100, y)
        c.setFillColor(altin)
        c.setFont("DejaVu", 8)
        c.drawCentredString(mid, y - 10, "✦  ✦  ✦")
        return y - 18

    # Collect data
    try:
        data = _collect_natal_data(motor)
    except:
        data = {}

    # ── Simulation radar data ──
    sim_data = {}
    try:
        p1_dt = motor.p1 if hasattr(motor, 'p1') else None
        if p1_dt:
            e_date = getattr(motor, 'event_date_str', '')
            e_time = getattr(motor, 'event_time_str', '12:00')
            radar_raw = _natal_radar(p1_dt, e_date, e_time)
            if radar_raw:
                kat, _ = _result_kategorize(radar_raw)
                sim_data = kat
    except Exception as e:
        print(f"[PDF] Simülasyon verisi alınamadı: {e}")
    data["simulasyon"] = sim_data

    # ═══════════════════════════════════════════
    # COVER PAGE — big logo
    # ═══════════════════════════════════════════
    c.setFillColor(bg)
    c.rect(0, 0, w, h, fill=1)
    c.setFillColor(altin)
    c.rect(0, h - 14, w, 14, fill=1)
    c.setFillColor(altin)
    c.rect(0, 0, w, 10, fill=1)
    try:
        logo_yol = os.path.join(_PROJECT_ROOT, "kapak1.png")
        if os.path.exists(logo_yol):
            logo_boyut = 520
            lx = (w - logo_boyut) / 2
            ly = h - logo_boyut - 56
            c.drawImage(logo_yol, lx, ly, width=logo_boyut, height=logo_boyut, mask=None)
        else:
            c.setFont("DejaVu-Bold", 34)
            c.setFillColor(HexColor('#FDFAF5'))
            c.drawCentredString(w / 2, h - 150, pdf_label("Bireysel Natal"))
            c.drawCentredString(w / 2, h - 190, pdf_label("Analiz Raporu"))
            c.setStrokeColor(altin)
            c.setLineWidth(1)
            c.line(w / 2 - 110, h - 212, w / 2 + 110, h - 212)
    except Exception as e:
        print(f"[PDF] Logo çizilemedi: {e}")
    # Name + version + birth info at bottom of cover
    c.setFont("DejaVu-Bold", 16)
    c.setFillColor(altin)
    c.drawCentredString(w / 2, 152, motor.p1_isim or pdf_label("Kişisel Analiz"))
    c.setFont("DejaVu", 9)
    c.setFillColor(HexColor('#999999'))
    c.drawCentredString(w / 2, 130, "FAST — Synastry Technique  |  v4.0" if _EN else "FAST — Sinastri Tekniği  |  v4.0")
    try:
        dogum_bilgi = f"{pdf_label('Doğum:')} {motor.p1_str or ''}  |  {getattr(motor, 'event_time_str', '')}"
        yer_bilgi = f"{pdf_label('Konum:')} {getattr(motor, 'sehir', '')}, {getattr(motor, 'ulke', '')} ({motor.enlem:.2f}°, {motor.boylam:.2f}°)" if hasattr(motor, 'enlem') else ""
        c.setFont("DejaVu", 8)
        c.setFillColor(HexColor('#999999'))
        if dogum_bilgi:
            c.drawCentredString(w / 2, 112, dogum_bilgi)
        if yer_bilgi:
            c.drawCentredString(w / 2, 96, yer_bilgi)
    except: pass

    bolum_no = [0]  # mutable counter for closures

    # ═══════════════════════════════════════════
    # PRE-COMPUTE sections availability (for clickable TOC)
    # ═══════════════════════════════════════════
    try:
        mp6_entries = _natal_minor_progress_yorumlari(motor, gun_sayisi=180)
    except:
        mp6_entries = []
    chart_png = ""
    try:
        motor.haritalari_ciz()
        chart_png = os.path.join(_PROJECT_ROOT, f"{motor._session_id}_Situa_A.png")
    except Exception as e:
        print(f"[PDF] Harita üretilemedi: {e}")
    sim = data.get("simulasyon", {})
    toc_bolumler = []
    if chart_png and os.path.exists(chart_png):
        toc_bolumler.append((pdf_label("Doğum Haritası"), "bolum_harita"))
    if len(str(data.get("chart_yorumu", ""))) > 30:
        toc_bolumler.append((pdf_label("Doğum Haritası Yorumu"), "bolum_yorum"))
    if data.get("arap_noktalari"):
        toc_bolumler.append((pdf_label("Arap Noktaları"), "bolum_arap"))
    if data.get("asteroitler") or data.get("asteroit_konumlar"):
        toc_bolumler.append((pdf_label("Asteroit Bulguları"), "bolum_asteroit"))
    if data.get("hayat_alanlari"):
        toc_bolumler.append((pdf_label("Hayat Alanları Detayı"), "bolum_hayat"))
    if data.get("sifa_receteleri") or data.get("sifa_receteleri_detay"):
        toc_bolumler.append((pdf_label("Şifa Reçeteleri"), "bolum_sifa"))
    if data.get("sabianlar"):
        toc_bolumler.append((pdf_label("Sabian Sembolleri"), "bolum_sabian"))
    if len(str(data.get("solar_return", ""))) > 20:
        toc_bolumler.append((pdf_label("Solar Return — Yıllık Döngü"), "bolum_solar"))
    if len(str(data.get("lunar_return", ""))) > 20:
        toc_bolumler.append((pdf_label("Lunar Return — Aylık Döngü"), "bolum_lunar"))
    if isinstance(mp6_entries, list) and mp6_entries:
        toc_bolumler.append((pdf_label("6 Aylık Minor Progress — Gün Gün"), "bolum_minor"))
    if sim and any(v for v in sim.values()):
        toc_bolumler.append((pdf_label("Global Kader Pusulası"), "bolum_kader"))

    # ═══════════════════════════════════════════
    # TABLE OF CONTENTS — clickable page
    # ═══════════════════════════════════════════
    if toc_bolumler:
        yeni_sayfa()
        toc_cizildi[0] = True
        c.bookmarkPage("icindekiler")
        y = sayfa_basligi(pdf_label("İçindekiler"), numara="☰")
        c.setFont("DejaVu", 8.5)
        c.setFillColor(acik)
        c.drawString(SOL, y, pdf_label("Raporunuzun bölümlerine gitmek için başlıklara tıklayın."))
        y -= 22
        for i, (toc_baslik, toc_hedef) in enumerate(toc_bolumler, 1):
            satir_h = 30
            if y - satir_h < SAYFA_ALT:
                yeni_sayfa(); y = SAYFA_UST
            c.setFillColor(altin)
            c.roundRect(SOL, y - satir_h + 4, 22, 20, 3, fill=1, stroke=0)
            c.setFillColor(HexColor('#FFFFFF'))
            c.setFont("DejaVu-Bold", 10)
            c.drawCentredString(SOL + 11, y - satir_h + 10, str(i))
            c.setFillColor(koyu)
            c.setFont("DejaVu-Bold", 10.5)
            c.drawString(SOL + 32, y - satir_h + 8, toc_baslik)
            c.linkAbsolute("", toc_hedef, (SOL - 6, y - satir_h - 4, SAG, y + 4))
            c.setStrokeColor(sari_cizgi)
            c.setLineWidth(0.3)
            c.line(SOL + 32, y - satir_h - 6, SAG - 6, y - satir_h - 6)
            y -= satir_h + 6
        y -= 16

    # ═══════════════════════════════════════════
    # CHART WHEEL PAGE
    # ═══════════════════════════════════════════
    try:
        if chart_png and os.path.exists(chart_png):
            yeni_sayfa()
            c.bookmarkPage("bolum_harita")
            y = SAYFA_UST - 10
            c.setFont("DejaVu-Bold", 18)
            c.setFillColor(koyu)
            c.drawCentredString(w / 2, y, pdf_label("Doğum Haritası"))
            c.setStrokeColor(altin)
            c.setLineWidth(1)
            c.line(w / 2 - 100, y - 8, w / 2 + 100, y - 8)
            c.drawImage(chart_png, SOL + 20, SAYFA_ALT + 20, width=(SAG - SOL - 40), height=(y - SAYFA_ALT - 40), preserveAspectRatio=True)
    except Exception as e:
        print(f"[PDF] Harita eklenemedi: {e}")

    # ═══════════════════════════════════════════
    # CHART INTERPRETATION — sub-sections per planet
    # ═══════════════════════════════════════════
    chart_yorum = data.get("chart_yorumu", "")
    gez_bolumler = data.get("chart_yorumu_gezegenler", []) or []
    aci_bolumler = data.get("chart_yorumu_acilar", []) or []
    if chart_yorum and len(chart_yorum) > 30:
        bolum_no[0] += 1
        yeni_sayfa()
        c.bookmarkPage("bolum_yorum")
        y = sayfa_basligi("Natal Chart Interpretation" if _EN else "Doğum Haritası Yorumu", numara=str(bolum_no[0]))
        gez_parag_metin = " ".join(b.get("metin", "") for b in gez_bolumler if b.get("metin"))
        aci_parag_metin = " ".join(b.get("metin", "") for b in aci_bolumler if b.get("metin"))
        paragraflar = chart_yorum.split("\n\n")
        for para in paragraflar:
            if not para.strip():
                y -= 8
                continue
            # Planet paragraph → one sub-section per planet
            if gez_bolumler and gez_parag_metin and para.strip() == gez_parag_metin.strip():
                for zb in gez_bolumler:
                    alt_h = 16 + yazi_olcul(zb.get("metin", ""), "DejaVu", 8, 90) + 6
                    if y - alt_h < SAYFA_ALT:
                        yeni_sayfa(); y = SAYFA_UST
                    c.setFont("DejaVu-Bold", 9.5)
                    c.setFillColor(bordo)
                    gez_isim = zb.get('gezegen', '')
                    gez_glif = GEZEGEN_GLIF.get(gez_isim, '✦')
                    c.drawString(SOL + 6, y - 2, f"✦ {gez_glif} {zb.get('baslik') or pdf_label(gez_isim)}")
                    c.setStrokeColor(sari_cizgi)
                    c.setLineWidth(0.4)
                    c.line(SOL + 6, y - 7, SAG - 6, y - 7)
                    y -= 16
                    y = metin_yaz(SOL + 10, y, zb.get("metin", ""), "DejaVu", 8, koyu, 90)
                    y -= 8
                continue
            # Aspects paragraph → one sub-section per aspect
            if aci_bolumler and aci_parag_metin and para.strip() == aci_parag_metin.strip():
                for zb in aci_bolumler:
                    alt_h = 16 + yazi_olcul(zb.get("metin", ""), "DejaVu", 8, 90) + 6
                    if y - alt_h < SAYFA_ALT:
                        yeni_sayfa(); y = SAYFA_UST
                    c.setFont("DejaVu-Bold", 9.5)
                    c.setFillColor(bordo)
                    baslik_metni = zb.get('baslik', '')
                    g1 = baslik_metni.split('–')[0].strip() if '–' in baslik_metni else ''
                    g2 = baslik_metni.split('–')[1].split('(')[0].strip() if '–' in baslik_metni and '(' in baslik_metni else ''
                    aci_adi = ''
                    if '(' in baslik_metni and ')' in baslik_metni:
                        aci_adi = baslik_metni.split('(')[1].split(')')[0].strip()
                    c.drawString(SOL + 6, y - 2, f"✦ {GEZEGEN_GLIF.get(g1, '')} {g1} – {GEZEGEN_GLIF.get(g2, '')} {g2}")
                    if aci_adi:
                        c.setFillColor(altin)
                        c.drawString(SOL + 8 + c.stringWidth(f"✦ {GEZEGEN_GLIF.get(g1, '')} {g1} – {GEZEGEN_GLIF.get(g2, '')} {g2}", "DejaVu-Bold", 9.5), y - 2, f"{ACI_GLIF.get(aci_adi, '')} {aci_adi}")
                    c.setStrokeColor(sari_cizgi)
                    c.setLineWidth(0.4)
                    c.line(SOL + 6, y - 7, SAG - 6, y - 7)
                    y -= 16
                    y = metin_yaz(SOL + 10, y, zb.get("metin", ""), "DejaVu", 8, koyu, 90)
                    y -= 8
                continue
            if y < 80:
                yeni_sayfa(); y = SAYFA_UST
            y = metin_yaz(SOL, y, para.strip(), "DejaVu", 8.5, acik, 92)
            y -= 6

    # ═══════════════════════════════════════════
    # ARABIC POINTS (Arap Noktaları)
    # ═══════════════════════════════════════════
    arap_noktalari = data.get("arap_noktalari", {}) or {}
    arap_listesi = []
    if isinstance(arap_noktalari, dict):
        for _kisi, _noktalar in arap_noktalari.items():
            if isinstance(_noktalar, dict):
                arap_listesi.extend(list(_noktalar.items()))
    if arap_listesi:
        bolum_no[0] += 1
        yeni_sayfa()
        c.bookmarkPage("bolum_arap")
        y = sayfa_basligi(pdf_label("Arap Noktaları — Sembolik Hassas Noktalar"), numara=str(bolum_no[0]))
        y = metin_yaz(SOL, y, pdf_label("Arap noktaları, doğum haritanızdaki Yükselen ve gezegenlerin özel kombinasyonlarından türetilen sembolik hassas noktalardır; hayatınızın hangi alanında şans, ruh, aşk, bağlılık, tutku ve bolluk temalarının öne çıktığını gösterir."), "DejaVu", 8, acik, 92)
        y -= 10
        for _nokta_adi, _bilgi in arap_listesi:
            if not isinstance(_bilgi, dict):
                continue
            burc = _bilgi.get("burc", "")
            ev_no = _bilgi.get("ev", 0)
            derece = _bilgi.get("derece", 0)
            burc_yorum = _bilgi.get("burc_yorum", "") or ""
            ev_yorumu = _bilgi.get("ev_yorumu", "") or ""
            ust_bilgi = (f"{pdf_label(burc)}, House {ev_no} ({derece}°)" if _i18n_get_lang() == "en" else f"{burc} burcu, {ev_no}. Ev ({derece}°)") if burc else (f"House {ev_no} ({derece}°)" if _i18n_get_lang() == "en" else f"{ev_no}. Ev ({derece}°)")
            parag = " ".join(p for p in [burc_yorum, ev_yorumu] if p)
            nokta_h = 16 + 12 + yazi_olcul(parag, "DejaVu", 8, 90) + 8
            if y - nokta_h < SAYFA_ALT:
                yeni_sayfa(); y = SAYFA_UST
            c.setFillColor(kart_bg)
            c.roundRect(SOL, y - nokta_h, SAG - SOL, nokta_h, 5, fill=1, stroke=0)
            c.setStrokeColor(gri)
            c.setLineWidth(0.4)
            c.roundRect(SOL, y - nokta_h, SAG - SOL, nokta_h, 5, fill=0, stroke=1)
            c.setFont("DejaVu-Bold", 9.5)
            c.setFillColor(bordo)
            c.drawString(SOL + 12, y - 16, f"✦ {_nokta_adi}")
            c.setFont("DejaVu", 7.5)
            c.setFillColor(acik)
            c.drawString(SAG - 130, y - 16, ust_bilgi[:52])
            c.setStrokeColor(sari_cizgi)
            c.setLineWidth(0.3)
            c.line(SOL + 12, y - 21, SAG - 12, y - 21)
            if parag:
                y = metin_yaz(SOL + 14, y - 34, parag, "DejaVu", 8, koyu, 88)
            y -= nokta_h - 34 + 10
        y -= 8

    # ═══════════════════════════════════════════
    # ASTEROID FINDINGS (Asteroit Bulguları)
    # ═══════════════════════════════════════════
    asteroitler = data.get("asteroitler", []) or []
    asteroit_konumlar = data.get("asteroit_konumlar", []) or []
    if isinstance(asteroitler, list) and (asteroitler or asteroit_konumlar):
        bolum_no[0] += 1
        yeni_sayfa()
        c.bookmarkPage("bolum_asteroit")
        y = sayfa_basligi(pdf_label("Asteroit Bulguları — Ruhsal Mühürler"), numara=str(bolum_no[0]))
        y = metin_yaz(SOL, y, pdf_label("Asteroitler, doğum haritanızdaki gezegenlerle 5°'lik kavuşum orbunun içine girdiğinde ruhsal bir mühür oluşturur; Juno (evlilik), Ceres (beslenme), Pallas (bilgelik) ve Vesta (adanmışlık) temalarını açığa çıkarır."), "DejaVu", 8, acik, 92)
        y -= 10
        if asteroitler:
            for _ab in asteroitler[:16]:
                if not isinstance(_ab, dict):
                    continue
                asto_ad = _ab.get("asteroit", "")
                gez_ad = _ab.get("gezegen", "")
                fark = _ab.get("fark", 0)
                etki = _ab.get("etki", "") or ""
                yorum = _ab.get("yorum", "") or ""
                parag = " ".join(p for p in [yorum, etki] if p)
                if not parag:
                    parag = (f"{asto_ad} is in conjunction with your {gez_ad} energy." if _EN else f"{asto_ad} asteroidi {gez_ad} enerjinizle kavuşumda.")
                baslik = (f"✦ {asto_ad} — {gez_ad} ({fark}° conjunction)" if _EN else f"✦ {asto_ad} — {gez_ad} ({fark}° kavuşum)")
                ast_h = 16 + yazi_olcul(parag, "DejaVu", 8, 90) + 8
                if y - ast_h < SAYFA_ALT:
                    yeni_sayfa(); y = SAYFA_UST
                c.setFillColor(kart_bg)
                c.roundRect(SOL, y - ast_h, SAG - SOL, ast_h, 5, fill=1, stroke=0)
                c.setStrokeColor(gri)
                c.setLineWidth(0.4)
                c.roundRect(SOL, y - ast_h, SAG - SOL, ast_h, 5, fill=0, stroke=1)
                c.setFont("DejaVu-Bold", 9.5)
                c.setFillColor(bordo)
                c.drawString(SOL + 12, y - 16, baslik[:80])
                c.setStrokeColor(sari_cizgi)
                c.setLineWidth(0.3)
                c.line(SOL + 12, y - 21, SAG - 12, y - 21)
                y = metin_yaz(SOL + 14, y - 34, parag, "DejaVu", 8, koyu, 88)
                y -= ast_h - 34 + 10
            y -= 8
        if asteroit_konumlar:
            y = metin_yaz(SOL, y, pdf_label("Doğum haritanızdaki asteroit konumları:"), "DejaVu-Bold", 8.5, koyu, 92)
            y -= 6
            for _ak in asteroit_konumlar:
                if not isinstance(_ak, dict):
                    continue
                ak_ad = _ak.get("asteroit", "")
                ak_burc = _ak.get("burc", "")
                ak_deg = _ak.get("derece", 0)
                ak_etki = _ak.get("etki", "") or ""
                ak_line = f"✦ {ak_ad} — {ak_burc} ({ak_deg}°)  ·  {ak_etki}" if ak_etki else f"✦ {ak_ad} — {ak_burc} ({ak_deg}°)"
                if y - 14 < SAYFA_ALT:
                    yeni_sayfa(); y = SAYFA_UST
                y = metin_yaz(SOL + 6, y, ak_line, "DejaVu", 8, koyu, 92)
                y -= 6
        y -= 8

    # ═══════════════════════════════════════════
    # LIFE AREAS DETAIL — cards
    # ═══════════════════════════════════════════
    ha_list = data.get("hayat_alanlari", [])
    if ha_list:
        bolum_no[0] += 1
        yeni_sayfa()
        c.bookmarkPage("bolum_hayat")
        y = sayfa_basligi(pdf_label("Hayat Alanları Detayı"), numara=str(bolum_no[0]))
        for ha in ha_list:
            yorum_text = ha.get("yorum", "")
            oneriler = ha.get("oneriler", [])[:3]
            # Calculate card height
            card_h = 28  # header
            card_h += yazi_olcul(yorum_text, "DejaVu", 8.5, 86) + 4
            card_h += len(oneriler) * 14 + 6
            card_h += 10  # padding

            if y - card_h < SAYFA_ALT:
                yeni_sayfa(); y = SAYFA_UST

            kart_ciz(SOL, y - card_h, SAG - SOL, card_h, ha.get('etiket',''), ha.get('icon',''))
            # Element badge — color-coded pastel badge next to title
            element_adi = ha.get("element", "")
            if element_adi in ELEMENT_RENK:
                e_rengi = ELEMENT_RENK[element_adi]
                e_bx = SOL + 12 + c.stringWidth(ha.get('etiket',''), "DejaVu-Bold", 10) + 16
                c.setFillColor(e_rengi)
                c.circle(e_bx + 4, y - card_h + card_h - 13, 4, fill=1, stroke=0)
                c.setFillColor(e_rengi)
                c.setFont("DejaVu-Bold", 7.5)
                c.drawString(e_bx + 12, y - card_h + card_h - 16, pdf_label(element_adi))
            inner_y = y - 30
            # Score bar — wide, element-colored progress bar
            bar_w = 115
            skor = ha.get("skor", 50)
            dolu = int(bar_w * min(skor, 100) / 100)
            bar_x = SAG - bar_w - 45
            c.setFillColor(bar_zemin)
            c.rect(bar_x, y - 22, bar_w, 11, fill=1)
            c.setFillColor(ELEMENT_RENK.get(ha.get("element",""), altin))
            c.rect(bar_x, y - 22, dolu, 11, fill=1)
            c.setFont("DejaVu-Bold", 8)
            c.setFillColor(koyu)
            c.drawString(SAG - 38, y - 21, f"%{skor}")
            # Yorum
            inner_y = metin_yaz(SOL + 12, inner_y - 4, yorum_text, "DejaVu", 8.5, koyu, 86)
            # Öneriler
            for oneri in oneriler:
                metin_oneri = oneri.get("metin", "")
                if len(metin_oneri) > 127:
                    metin_oneri = metin_oneri[:127].rsplit(" ", 1)[0] + "…"
                if inner_y < SAYFA_ALT:
                    break
                c.setFont("DejaVu-Oblique", 7.5)
                c.setFillColor(acik)
                c.drawString(SOL + 18, inner_y, f"\u2022 {metin_oneri}")
                inner_y -= 12
            y -= card_h + 12

    # ═══════════════════════════════════════════
    # HEALING PRESCRIPTIONS
    # ═══════════════════════════════════════════
    sifa = data.get("sifa_receteleri", "")
    sifa_detay = data.get("sifa_receteleri_detay", [])
    if sifa or sifa_detay:
        bolum_no[0] += 1
        yeni_sayfa()
        c.bookmarkPage("bolum_sifa")
        y = sayfa_basligi(pdf_label("Şifa Reçeteleri"), numara=str(bolum_no[0]))
        if sifa:
            sifa_metin = str(sifa)
            sifa_metin = re.sub(r'[\U0001F000-\U0001FAFF\uFE0F\u20E3]', '', sifa_metin)
            sifa_metin = sifa_metin.replace("<br/>", " ").replace("<br>", " ").replace("<b>", "").replace("</b>", "")
            # Call-out box for phase-title (Ustalık Aşaması / Kalfalık / Çıraklık)
            if any(k in sifa_metin for k in ("Aşama", "Faz", "Phase", "Stage")):
                if ":" in sifa_metin:
                    sifa_baslik, sifa_acik = sifa_metin.split(":", 1)
                else:
                    sifa_baslik, sifa_acik = sifa_metin, ""
                call_h = 24 + yazi_olcul(sifa_acik.strip(), "DejaVu", 8.5, 88) + 10
                if y - call_h < SAYFA_ALT:
                    yeni_sayfa(); y = SAYFA_UST
                c.setFillColor(HexColor('#1E1C14'))
                c.roundRect(SOL, y - call_h, SAG - SOL, call_h, 5, fill=1, stroke=0)
                c.setStrokeColor(altin)
                c.setLineWidth(1.2)
                c.roundRect(SOL, y - call_h, SAG - SOL, call_h, 5, fill=0, stroke=1)
                c.setFillColor(altin)
                c.rect(SOL + 2, y - call_h + 6, 3, call_h - 12, fill=1, stroke=0)
                c.setFont("DejaVu-Bold", 10)
                c.setFillColor(altin)
                c.drawString(SOL + 14, y - 18, f"✦ {sifa_baslik.strip()}")
                c.setStrokeColor(sari_cizgi)
                c.setLineWidth(0.4)
                c.line(SOL + 14, y - 24, SAG - 14, y - 24)
                y = metin_yaz(SOL + 16, y - 36, sifa_acik.strip(), "DejaVu", 8.5, koyu, 88)
                y -= 10
            else:
                y = metin_yaz(SOL, y, sifa_metin[:600], "DejaVu", 8.5, acik, 92)
                y -= 10
        if sifa_detay:
            for rec in sifa_detay:
                rec_h = yazi_olcul(rec, "DejaVu", 8, 88) + 16
                if y - rec_h < SAYFA_ALT:
                    yeni_sayfa(); y = SAYFA_UST
                # card
                c.setFillColor(kart_bg)
                c.roundRect(SOL, y - rec_h, SAG - SOL, rec_h, 4, fill=1, stroke=0)
                c.setStrokeColor(altin)
                c.setLineWidth(2)
                c.line(SOL + 4, y - 6, SOL + 4, y - rec_h + 6)
                c.setStrokeColor(gri)
                c.setLineWidth(0.3)
                c.roundRect(SOL, y - rec_h, SAG - SOL, rec_h, 4, fill=0, stroke=1)
                inner_y = y - 10
                inner_y = metin_yaz(SOL + 14, inner_y, rec, "DejaVu", 8, koyu, 86)
                y -= rec_h + 8

    # ═══════════════════════════════════════════
    # SABIAN SYMBOLS
    # ═══════════════════════════════════════════
    sabianlar = data.get("sabianlar", [])
    if sabianlar:
        bolum_no[0] += 1
        yeni_sayfa()
        c.bookmarkPage("bolum_sabian")
        y = sayfa_basligi(pdf_label("Sabian Sembolleri"), numara=str(bolum_no[0]))
        for s in sabianlar:
            sembol = _strip_html(str(s.get('sembol','')))[:250]
            sembol = re.sub(r'^[\U0001F000-\U0001FAFF\uFE0F\u200D\s]*(?:Sabian Şifresi|Sabian Cipher) \(\d+°\):\s*', '', sembol)
            sembol = re.sub(r'[\U0001F000-\U0001FAFF\uFE0F\u20E3\u200D]', '', sembol)
            muhur = ""
            _muhur_etiketi = "Seal:" if _EN else "Mühür:"
            if "Mühür:" in sembol or "Seal:" in sembol:
                _ayrac = "Mühür:" if "Mühür:" in sembol else "Seal:"
                sembol, muhur = sembol.split(_ayrac, 1)
                muhur = (_muhur_etiketi + " " + muhur.strip())[:170]
            gez_isim = s.get('gezegen','')
            sembol_h = 30
            sembol_h += yazi_olcul(sembol.strip(), "DejaVu", 8, 86)
            if muhur:
                sembol_h += yazi_olcul(muhur, "DejaVu-Oblique", 8, 86) + 6
            if y - sembol_h < SAYFA_ALT:
                yeni_sayfa(); y = SAYFA_UST
            # Call-out card — gold accent
            c.setFillColor(HexColor('#1A1812'))
            c.roundRect(SOL, y - sembol_h, SAG - SOL, sembol_h, 5, fill=1, stroke=0)
            c.setStrokeColor(altin)
            c.setLineWidth(1.1)
            c.roundRect(SOL, y - sembol_h, SAG - SOL, sembol_h, 5, fill=0, stroke=1)
            c.setFillColor(altin)
            c.rect(SOL + 2, y - sembol_h + 6, 3, sembol_h - 12, fill=1, stroke=0)
            c.setFont("DejaVu-Bold", 9.5)
            c.setFillColor(bordo)
            c.drawString(SOL + 14, y - 17, f"✦ {GEZEGEN_GLIF.get(gez_isim, '')} {pdf_label(gez_isim)}  —  {s.get('derece_str','') or str(s.get('derece',''))+'°'}")
            c.setFillColor(altin)
            c.setFont("DejaVu-Bold", 7)
            c.drawRightString(SAG - 14, y - 16, "✦ Sabian Cipher" if _EN else "✦ Sabian Şifresi")
            c.setStrokeColor(sari_cizgi)
            c.setLineWidth(0.4)
            c.line(SOL + 14, y - 23, SAG - 14, y - 23)
            inner_y = y - 30
            inner_y = metin_yaz(SOL + 16, inner_y, sembol.strip(), "DejaVu", 8, acik, 86)
            if muhur:
                inner_y -= 4
                inner_y = metin_yaz(SOL + 16, inner_y, muhur, "DejaVu-Oblique", 8, koyu, 86)
            y -= sembol_h + 10

    # ═══════════════════════════════════════════
    # SOLAR / LUNAR RETURN — sub-sections
    # ═══════════════════════════════════════════
    for baslik, anahtar, html_anahtar in [(pdf_label("Solar Return — Yıllık Döngü"), "solar_return", "solar_return_html"),
                                          (pdf_label("Lunar Return — Aylık Döngü"), "lunar_return", "lunar_return_html")]:
        icerik = data.get(anahtar, "")
        if icerik and len(str(icerik)) > 20:
            bolum_no[0] += 1
            yeni_sayfa()
            c.bookmarkPage("bolum_solar" if anahtar == "solar_return" else "bolum_lunar")
            y = sayfa_basligi(baslik, numara=str(bolum_no[0]))
            bolumler = _html_bolumleri_ayir(data.get(html_anahtar, ""))
            if bolumler:
                for b_baslik, b_metin in bolumler:
                    if not b_metin.strip():
                        continue
                    alt_h = 16 + yazi_olcul(b_metin, "DejaVu", 8, 90) + 6
                    if y - alt_h < SAYFA_ALT:
                        yeni_sayfa(); y = SAYFA_UST
                    c.setFont("DejaVu-Bold", 9.5)
                    c.setFillColor(bordo)
                    c.drawString(SOL + 6, y - 2, f"✦ {b_baslik}")
                    c.setStrokeColor(sari_cizgi)
                    c.setLineWidth(0.4)
                    c.line(SOL + 6, y - 7, SAG - 6, y - 7)
                    y -= 16
                    y = metin_yaz(SOL + 10, y, b_metin, "DejaVu", 8, koyu, 90)
                    y -= 8
            else:
                y = metin_yaz(SOL, y, str(icerik)[:3000], "DejaVu", 8.5, acik, 92)

    # ═══════════════════════════════════════════
    # 6-MONTH MINOR PROGRESS — calendar grid
    # ═══════════════════════════════════════════
    if isinstance(mp6_entries, list) and mp6_entries:
        bolum_no[0] += 1
        yeni_sayfa()
        c.bookmarkPage("bolum_minor")
        y = sayfa_basligi(pdf_label("6 Aylık Minor Progress — Gün Gün"), numara=str(bolum_no[0]))
        c.setFont("DejaVu", 7.5)
        c.setFillColor(acik)
        c.drawString(SOL, y, pdf_label("İlerleyen Ay'ınızın önümüzdeki 6 ay boyunca oluşturacağı açılar, aylık takvim düzeninde aşağıda gösterilmiştir."))
        y -= 4
        c.setFillColor(HexColor('#8FC0E8'))
        c.drawString(SOL, y, pdf_label("■ Uyumlu açı (Trigon · Sekstil) · "))
        c.setFillColor(HexColor('#D08A96'))
        c.drawString(SOL + 150, y, pdf_label("■ Zorlayıcı açı (Kare · Karşıt) · "))
        c.setFillColor(acik)
        c.drawString(SOL + 330, y, pdf_label("□ Açı yoğunluğu düşük"))
        y -= 16

        import datetime as _dt_mod
        AY_ADLARI_TR = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"] if _i18n_get_lang() != "en" else ["January","February","March","April","May","June","July","August","September","October","November","December"]
        HAFTALAR = ["Pzt","Sal","Çar","Per","Cum","Cmt","Paz"] if _i18n_get_lang() != "en" else ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        HUCRE_W = (SAG - SOL - 14) / 7.0
        HUCRE_H = 24.0

        gun_verileri = {}
        for p in mp6_entries:
            t = p.get("tarih", "")
            if not t:
                continue
            try:
                gd = _dt_mod.datetime.strptime(t, "%Y-%m-%d").date()
                gun_verileri[gd] = p
            except:
                pass

        if gun_verileri:
            ay_listesi = []
            for gd in sorted(gun_verileri.keys()):
                ay_anahtar = (gd.year, gd.month)
                if ay_listesi and ay_listesi[-1]["anahtar"] == ay_anahtar:
                    ay_listesi[-1]["gunler"].append(gd)
                else:
                    ay_listesi.append({"anahtar": ay_anahtar, "gunler": [gd]})

            for ay_kayit in ay_listesi:
                yy, mm = ay_kayit["anahtar"]
                ay_gunleri = ay_kayit["gunler"]
                ilk_hafta_gun = _dt_mod.date(yy, mm, 1).weekday()
                satir_sayisi = -(-(ilk_hafta_gun + len(ay_gunleri)) // 7)
                grid_h = 18 + 14 + satir_sayisi * HUCRE_H + 12
                onemli = [gd for gd in ay_gunleri if (gun_verileri[gd].get("aspekt_adet") or 0) >= 2]
                if onemli:
                    grid_h += 18 + len(onemli[:4]) * 13 + 8

                if y - grid_h - 6 < SAYFA_ALT:
                    yeni_sayfa(); y = SAYFA_UST
                # Month card
                c.setFillColor(kart_bg)
                c.roundRect(SOL, y - grid_h, SAG - SOL, grid_h, 5, fill=1, stroke=0)
                c.setStrokeColor(gri)
                c.setLineWidth(0.4)
                c.roundRect(SOL, y - grid_h, SAG - SOL, grid_h, 5, fill=0, stroke=1)
                c.setFillColor(altin)
                c.setFont("DejaVu-Bold", 11)
                c.drawString(SOL + 12, y - 17, f"{AY_ADLARI_TR[mm-1]} {yy}")
                c.setStrokeColor(sari_cizgi)
                c.setLineWidth(0.4)
                c.line(SOL + 12, y - 23, SAG - 12, y - 23)
                # Weekday headers
                c.setFillColor(acik)
                c.setFont("DejaVu-Bold", 7)
                for hafta_i in range(7):
                    c.drawCentredString(SOL + 8 + hafta_i * HUCRE_W, y - 33, HAFTALAR[hafta_i])
                # Cells
                gd_renk = {}
                for gd in ay_gunleri:
                    yrm_metin = " ".join(gun_verileri[gd].get("yorumlar") or [])
                    if any(k in yrm_metin for k in ("Kare", "Karşıt")):
                        gd_renk[gd] = HexColor('#D08A96')
                    elif any(k in yrm_metin for k in ("Trigon", "Sekstil", "Kavuşum")):
                        gd_renk[gd] = HexColor('#8FC0E8')
                    else:
                        gd_renk[gd] = None
                col = ilk_hafta_gun
                row = 0
                for gd in ay_gunleri:
                    cx = SOL + 6 + col * HUCRE_W
                    cy = y - 42 - row * HUCRE_H
                    renk = gd_renk.get(gd)
                    if renk:
                        c.setFillColor(renk)
                        c.roundRect(cx, cy + 2, HUCRE_W - 4, HUCRE_H - 4, 3, fill=1, stroke=0)
                        c.setFillColor(HexColor('#12121A'))
                        c.setFont("DejaVu-Bold", 8)
                    else:
                        c.setStrokeColor(HexColor('#3A3A42'))
                        c.setLineWidth(0.5)
                        c.roundRect(cx, cy + 2, HUCRE_W - 4, HUCRE_H - 4, 3, fill=0, stroke=1)
                        c.setFillColor(acik)
                        c.setFont("DejaVu", 8)
                    c.drawCentredString(cx + (HUCRE_W - 4) / 2, cy + 8.5, str(gd.day))
                    col += 1
                    if col == 7:
                        col = 0; row += 1
                # Featured days
                if onemli:
                    ly = y - 46 - satir_sayisi * HUCRE_H - 2
                    c.setFillColor(bordo)
                    c.setFont("DejaVu-Bold", 8)
                    c.drawString(SOL + 12, ly, f"✦ {pdf_label('Bu Ayın Öne Çıkan Günleri')} ({len(onemli)})" if _i18n_get_lang() == "en" else f"✦ Bu Ayın Öne Çıkan Günleri ({len(onemli)})")
                    for gd in onemli[:4]:
                        ly -= 13
                        p_entry = gun_verileri[gd]
                        ilk_yorum = (p_entry.get("yorumlar") or [pdf_label("Açı bulunamadı")])[0]
                        c.setFillColor(koyu)
                        c.setFont("DejaVu-Bold", 7.5)
                        c.drawString(SOL + 16, ly, f"{gd.day:02d} {AY_ADLARI_TR[mm-1]} · {p_entry.get('ay_burc','')} {pdf_label('Ay')}")
                        c.setFillColor(acik)
                        c.setFont("DejaVu", 7)
                        c.drawString(SOL + 118, ly, ilk_yorum[:135])
                y -= grid_h + 12

    # ═══════════════════════════════════════════
    # SIMULATION — Global Kader Pusulası
    # ═══════════════════════════════════════════
    sim = data.get("simulasyon", {})
    if sim and any(v for v in sim.values()):
        bolum_no[0] += 1
        yeni_sayfa()
        c.bookmarkPage("bolum_kader")
        y = sayfa_basligi(pdf_label("Global Kader Pusulası"), numara=str(bolum_no[0]))
        c.setFont("DejaVu", 8)
        c.setFillColor(acik)
        c.drawString(SOL, y, pdf_label("Gezegenlerinizin dünya üzerinde en güçlü etki gösterdiği şehirler — 15.000+ konum taranmıştır."))
        y -= 22
        # ── Calculation technique explanation ──
        teknik = ((("Calculation Method: Your planets' natal positions are compared against the coordinates of "
                    "more than 15,000 cities worldwide. ") if _EN else pdf_label("Hesaplama Tekniği: Doğum haritanızdaki gezegen konumları, dünya üzerindeki 15.000'den fazla şehir koordinatıyla karşılaştırılır. ")) +
                  (("For each city, the day's sky axes — the Ascendant (AC), Midheaven (MC), Descendant (DC) and "
                    "Imum Coeli (IC) — are computed; ") if _EN else pdf_label("Her şehir için o günkü gökyüzünde Yükselen (AC), Zirve (MC), Alçalan (DC) ve Taban (IC) eksenleri hesaplanır; ")) +
                  (("Your planets' closeness (orb) to these axes up to 5° is scored together with the planet's nature — "
                    "the sharper the angle, the stronger the influence. ") if _EN else pdf_label("gezegenlerinizin bu eksenlere 5°'ye kadar olan yakınlığı (orb) ile gezegenin doğası puanlanır — açı ne kadar keskinse etki o kadar güçlüdür. ")) +
                  (("Each city is assessed with 4 core scores: Wealth & Abundance, Peace & Inner Calm, "
                    "Passion & Adventure, Crisis & Transformation. ") if _EN else pdf_label("Her şehir 4 temel skorla değerlendirilir: Para & Bolluk, Huzur & İç Sakinlik, Tutku & Macera, Kriz & Dönüşüm. ")) +
                  pdf_label("Her kategoride en yüksek skorlu ilk 10 şehir, enerjilerinizin dünya üzerinde en güçlü rezonans kurduğu noktaları temsil eder."))
        teknik_h = 24 + yazi_olcul(teknik, "DejaVu", 7.5, 90) + 12
        kart_ciz(SOL, y - teknik_h, SAG - SOL, teknik_h, pdf_label("Hesaplama Tekniği"), "🔮")
        metin_yaz(SOL + 14, y - teknik_h + 22, teknik, "DejaVu", 7.5, acik, 90)
        y -= teknik_h + 12
        SIM_KAT_PDF = [
            ("para", "⚖", pdf_label("Para & Bolluk")),
            ("huzur", "✦", pdf_label("Huzur & İç Sakinlik")),
            ("tutku", "★", pdf_label("Tutku & Macera")),
            ("kriz", "✕", pdf_label("Kriz & Dönüşüm")),
        ]
        KAT_ACIKLAMA = {
            "para": pdf_label("Maddi kazanç, bolluk ve fırsat enerjilerinin en güçlü olduğu şehir."),
            "huzur": pdf_label("İç sakinlik, duygusal denge ve huzurlu bir yaşam enerjisinin en güçlü olduğu şehir."),
            "tutku": pdf_label("Tutku, macera ve girişimcilik enerjisinin en yüksek olduğu şehir."),
            "kriz": pdf_label("Dönüşüm, kriz ve güçlü değişim rüzgârlarının estiği şehir."),
        }
        for kat_key, icon, label in SIM_KAT_PDF:
            cities = sim.get(kat_key, [])
            if not cities:
                continue
            kat_h = 28 + len(cities) * 26 + 8
            if y - kat_h < SAYFA_ALT:
                yeni_sayfa()
                y = sayfa_basligi(pdf_label("Global Kader Pusulası") + " (devam)" if _i18n_get_lang() != "en" else "Global Destiny Compass (continued)")
            kart_ciz(SOL, y - kat_h, SAG - SOL, kat_h, label, icon)
            # Category color stripe on the left edge
            c.setFillColor(KAT_RENK.get(kat_key, altin))
            c.rect(SOL + 2, y - kat_h + 6, 3, kat_h - 12, fill=1, stroke=0)
            inner_y = y - 28
            for i, city in enumerate(cities):
                sehir_adi = city.get("sehir", "")[:42]
                skor_val = city.get("skor", 0)
                c.setFont("DejaVu-Bold", 8)
                c.setFillColor(koyu)
                c.drawString(SOL + 16, inner_y, f"{i+1}. {sehir_adi}")
                bar_w = 90
                bar_x = SAG - bar_w - 55
                dolu = int(bar_w * min(skor_val, 99) / 99)
                c.setFillColor(bar_zemin)
                c.rect(bar_x, inner_y - 2, bar_w, 10, fill=1)
                c.setFillColor(KAT_RENK.get(kat_key, altin))
                c.rect(bar_x, inner_y - 2, dolu, 10, fill=1)
                c.setFont("DejaVu-Bold", 7)
                c.setFillColor(koyu)
                c.drawString(bar_x + bar_w + 5, inner_y - 1, f"%{skor_val}")
                inner_y -= 13
                etkiler = city.get("etkiler") or []
                if etkiler:
                    etki_list = "; ".join(_etki_temizle(e) for e in etkiler[:2])
                    acik_yazi = f"{pdf_label('Etkiler:')} {etki_list}."
                else:
                    acik_yazi = KAT_ACIKLAMA.get(kat_key, "")
                c.setFont("DejaVu", 7)
                c.setFillColor(acik)
                c.drawString(SOL + 16, inner_y, acik_yazi[:150])
                inner_y -= 13
            y -= kat_h + 10

    c.save()
    print(f"[PDF] Natal PDF saved: {yol}")

def _wrap_text(text, maxlen):
    """Wrap text into lines of maxlen characters."""
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        if len(cur) + len(w) + 1 > maxlen:
            if cur: lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur: lines.append(cur)
    return lines or [text]

def _collect_extra_data(motor):
    data = {}
    try:
        mod = getattr(motor, 'mod', '')
        ev = motor.karmik_ev_aktarimlari(pdf_icin=False)
        if isinstance(ev, tuple):
            data["karmik_ev"] = {"rapor_a": ev[0], "rapor_b": [] if mod == 'bireysel_natal' else ev[1]}
        else:
            data["karmik_ev"] = {"rapor_a": [], "rapor_b": []}
    except: data["karmik_ev"] = {"rapor_a": [], "rapor_b": []}
    try:
        if getattr(motor, 'mod', '') == 'bireysel_natal':
            data["bagil_iklim"] = ""
        else:
            data["bagil_iklim"] = motor.kadersel_bsp_iklimi()
    except: data["bagil_iklim"] = ""
    try:
        mod = getattr(motor, 'mod', '')
        if mod == 'bireysel_natal':
            data["progression"] = []
        else:
            prog = motor.secondary_progression_yorumla()
            data["progression"] = prog if isinstance(prog, list) else []
    except: data["progression"] = []
    try:
        if getattr(motor, 'mod', '') == 'bireysel_natal':
            data["hava_durumu"] = []
        else:
            alarms = motor.gunluk_bsp_taramasi(gun_sayisi=30)
            data["hava_durumu"] = alarms[:3] if isinstance(alarms, list) else []
    except: data["hava_durumu"] = []
    try:
        if getattr(motor, 'mod', '') == 'bireysel_natal':
            data["zaman_makinesi"] = []
        else:
            nav = motor.calculate_gelecek_navigasyonu(pdf_icin=False)
            data["zaman_makinesi"] = nav[:3] if isinstance(nav, list) else []
    except: data["zaman_makinesi"] = []
    try:

        yildiz_liste = []
        mod = getattr(motor, 'mod', '')
        # For bireysel_natal, only use p1 (no duplicate data from p2)
        ekran_haritalari = [
            {"jd": motor.get_natal_julian_day("p1"), "isim": motor.p1_isim},
        ]
        if mod != 'bireysel_natal':
            isim2 = motor.p2_isim or "Situa B"
            ekran_haritalari.append({"jd": motor.get_natal_julian_day("p2"), "isim": isim2})
        for harita in ekran_haritalari:
            for g_ad, g_id in list(GEZEGENLER.items())[:10]:
                if len(yildiz_liste) >= 3: break
                try:
                    deg = get_planetary_position(harita["jd"], g_id)
                    sonuc = kadersel_yildiz_taramasi(g_ad, deg, orb_siniri=2.0)
                    if sonuc:
                        for s in sonuc:
                            if len(yildiz_liste) >= 3: break
                            satirlar = s.split("\n")
                            yildiz_liste.append({"baslik": satirlar[0].replace("Kavuşumu", f"Kavuşumu ({harita['isim']})").replace("Conjunction", f"Conjunction ({harita['isim']})"), "icerik": "\n".join(satirlar[1:])})
                except: continue
            if len(yildiz_liste) >= 3: break
        data["yildiz_muhurleri"] = yildiz_liste
    except: data["yildiz_muhurleri"] = []
    try:
        arap = motor.arap_noktasi_hesapla()
        if isinstance(arap, dict):
            if getattr(motor, 'mod', '') == 'bireysel_natal':
                # Keep only p1's data (same person, skip duplicate from p2)
                p1_isim = motor.p1_isim
                data["arap_noktalari"] = {k: v for k, v in arap.items() if k == p1_isim}
            else:
                data["arap_noktalari"] = arap
        else:
            data["arap_noktalari"] = {}
    except: data["arap_noktalari"] = {}
    try:
        if mod == 'bireysel_natal':
            data["arap_sinastri"] = []
        else:
            arap_sin = motor.arap_noktasi_sinastri_analizi()
            data["arap_sinastri"] = arap_sin if isinstance(arap_sin, list) else []
    except: data["arap_sinastri"] = []
    try:
        # Gerçek natal doğum tarihlerini kullan (göreli/Milat tarihleri seas_*.se1 gerektirir ve sunucuda eksik)
        j_ileri = motor.get_natal_julian_day("p1")
        j_geri = motor.get_natal_julian_day("p2")
        ephe_yolu = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ephe')
        swe.set_ephe_path(ephe_yolu)
        # MOSEPH (analitik) sadece bu 4 asteroidi dosyasız hesaplar; ephe dosyaları eksik olduğundan diğerleri atlanır
        ASTEROIDLER = ["Juno", "Ceres", "Pallas", "Vesta"]
        HEDEFLER = ["Güneş", "Ay", "Merkür", "Venüs", "Mars", "Jüpiter", "Satürn", "Uranüs", "Neptün", "Plüton", "Chiron"]

        asteroit_bulgular = []
        asteroit_konumlar = []
        asteroit_hata = []
        mod = getattr(motor, 'mod', '')
        for asto in ASTEROIDLER:
            try:
                asto_id = ASTEROID_ID_MAP.get(asto) or GEZEGENLER.get(asto)
                if asto_id is None: continue
                a_deg = swe.calc_ut(j_ileri, asto_id, swe.FLG_MOSEPH | swe.FLG_SPEED)[0][0]
                a_burc = dereceyi_burca_cevir(a_deg)
                asteroit_konumlar.append({
                    "asteroit": asto, "derece": round(a_deg, 2), "burc": a_burc,
                    "etki": ARAP_ILISKI.get("ASTEROID_ISIMLERI", {}).get(asto, {}).get("etki", ""),
                })
            except Exception as _e:
                asteroit_hata.append(f"konum {asto}: {_e}")
                continue
        if mod == 'bireysel_natal':
            # Natal mod: asteroids conjunct natal planets in same chart
            for asto in ASTEROIDLER:
                try:
                    asto_id = ASTEROID_ID_MAP.get(asto) or GEZEGENLER.get(asto)
                    if asto_id is None: continue
                    a_deg = swe.calc_ut(j_ileri, asto_id, swe.FLG_MOSEPH | swe.FLG_SPEED)[0][0]
                    for gez in HEDEFLER:
                        g_id = GEZEGENLER.get(gez)
                        if g_id is None: continue
                        try:
                            g_flags = swe.FLG_MOSEPH | swe.FLG_SPEED if g_id >= 10 else get_safe_flags(g_id)
                            g_deg = swe.calc_ut(j_ileri, g_id, g_flags)[0][0]
                        except Exception as _e:
                            asteroit_hata.append(f"gezegen {gez}: {_e}")
                            continue
                        fark = abs(a_deg - g_deg)
                        if fark > 180: fark = 360 - fark
                        if fark <= 5.0:
                            ainfo = ARAP_ILISKI.get("ASTEROID_ISIMLERI", {}).get(asto, {})
                            yorum_dict = ARAP_ILISKI.get("ASTEROID_SINASTRI_YORUMLARI", {})
                            yorum = yorum_dict.get((asto, gez), "") or yorum_dict.get((gez, asto), "")
                            asteroit_bulgular.append({
                                "kaynak": motor.p1_isim, "asteroit": asto,
                                "hedef": motor.p1_isim, "gezegen": gez,
                                "fark": round(fark, 1),
                                "etki": ainfo.get("etki", ""),
                                "yorum": yorum,
                            })
                except: continue
                if len(asteroit_bulgular) >= 20: break
        else:
            for (kaynak_jd, kaynak_ad, hedef_jd, hedef_ad) in [
                (j_ileri, motor.p1_isim, j_geri, motor.p2_isim),
                (j_geri, motor.p2_isim, j_ileri, motor.p1_isim),
            ]:
                for asto in ASTEROIDLER:
                    try:
                        asto_id = ASTEROID_ID_MAP.get(asto) or GEZEGENLER.get(asto)
                        if asto_id is None: continue
                        a_deg = swe.calc_ut(kaynak_jd, asto_id, swe.FLG_MOSEPH | swe.FLG_SPEED)[0][0]
                        for gez in HEDEFLER:
                            g_id = GEZEGENLER.get(gez)
                            if g_id is None: continue
                            try:
                                g_flags = swe.FLG_MOSEPH | swe.FLG_SPEED if g_id >= 10 else get_safe_flags(g_id)
                                g_deg = swe.calc_ut(hedef_jd, g_id, g_flags)[0][0]
                            except: continue
                            fark = abs(a_deg - g_deg)
                            if fark > 180: fark = 360 - fark
                            if fark <= 5.0:
                                ainfo = ARAP_ILISKI.get("ASTEROID_ISIMLERI", {}).get(asto, {})
                                yorum_dict = ARAP_ILISKI.get("ASTEROID_SINASTRI_YORUMLARI", {})
                                yorum = yorum_dict.get((asto, gez), "") or yorum_dict.get((gez, asto), "")
                                asteroit_bulgular.append({
                                    "kaynak": kaynak_ad, "asteroit": asto,
                                    "hedef": hedef_ad, "gezegen": gez,
                                    "fark": round(fark, 1),
                                    "etki": ainfo.get("etki", ""),
                                    "yorum": yorum,
                                })
                    except: continue
                if len(asteroit_bulgular) >= 20: break
        data["asteroitler"] = asteroit_bulgular
        data["asteroit_konumlar"] = asteroit_konumlar
        if asteroit_hata:
            data["asteroit_hata"] = "; ".join(asteroit_hata[:8])
    except Exception as _e:
        data["asteroitler"] = []
        data["asteroit_konumlar"] = []
        data["asteroit_hata"] = f"DIS: {_e}"
    return data

def _collect_astro_data(motor):
    """Event koordinatları için composite-based astrokartografi verisi toplar."""
    try:
        comp = _composite_midpoints(motor.p1, motor.p2)
        jd_ev = swe.julday(motor.event_date.year, motor.event_date.month, motor.event_date.day,
                               motor.event_date.hour + motor.event_date.minute / 60.0)
        skor = _composite_sehir_skor(comp, jd_ev, motor.enlem, motor.boylam)
        return {"gezegenler": comp, "skor": {k: skor[k] for k in ["huzur","para","tutku","kriz","etkiler"]}}
    except:
        return None

def _parse_time(t: str) -> str:
    t = (t or "").strip()
    try:
        datetime.strptime(t, "%H:%M")
        return t
    except Exception:
        return "12:00"

def _engine_es(p: EsSevgiliInput, ek_charts=False):
    _ephe_yolu = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ephe')
    if os.path.isdir(_ephe_yolu):
        swe.set_ephe_path(_ephe_yolu)
    motor = FBST_Engine(
        p1=_parse_date(p.p1_tarih), p2=_parse_date(p.p2_tarih),
        event_date=_parse_date(p.event_tarih), event_time=_parse_time(p.event_saat),
        city=p.sehir, country=p.ulke,
        lat=p.enlem, lon=p.boylam,
        p1_isim=p.p1_isim, p2_isim=p.p2_isim,
        mod="es_sevgili", utc_offset=p.utc_offset,
        lang=p.lang,
    )
    motor.fbst_analizi_yap(sessiz=True)
    _cache_engine(motor)
    return motor

def _engine_eb(p: EbeveynCocukInput, ek_charts=False):
    _ephe_yolu = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ephe')
    if os.path.isdir(_ephe_yolu):
        swe.set_ephe_path(_ephe_yolu)
    motor = FBST_Engine(
        p1=_parse_date(p.cocuk_tarih), p2=_parse_date(p.ebeveyn_tarih),
        event_date=_parse_date(p.cocuk_tarih), event_time=_parse_time(p.cocuk_saat),
        city=p.sehir, country=p.ulke,
        lat=p.enlem, lon=p.boylam,
        p1_isim=p.cocuk_isim, p2_isim=p.ebeveyn_isim,
        mod="ebeveyn_cocuk", ebeveyn_rolu=p.ebeveyn_rolu,
        utc_offset=p.utc_offset,
        lang=p.lang,
    )
    motor.fbst_analizi_yap(sessiz=True)
    _cache_engine(motor)
    return motor

def _engine_py(p: PotansiyelYetenekInput, ek_charts=False):
    tarih = _parse_date(p.tarih)
    _ephe_yolu = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ephe')
    if os.path.isdir(_ephe_yolu):
        swe.set_ephe_path(_ephe_yolu)
    motor = FBST_Engine(
        p1=tarih, p2=tarih,
        event_date=tarih, event_time=_parse_time(p.saat),
        city=p.sehir, country=p.ulke,
        lat=p.enlem, lon=p.boylam,
        p1_isim=p.isim, p2_isim="",
        mod="potansiyel_yetenek", utc_offset=p.utc_offset,
        lang=p.lang,
    )
    motor.fbst_analizi_yap(sessiz=True)
    _cache_engine(motor)
    return motor

def _engine_natal(p: BireyselNatalInput, ek_charts=False):
    tarih = _parse_date(p.tarih)
    _ephe_yolu = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ephe')
    if os.path.isdir(_ephe_yolu):
        swe.set_ephe_path(_ephe_yolu)
    motor = FBST_Engine(
        p1=tarih, p2=tarih,
        event_date=tarih, event_time=_parse_time(p.saat),
        city=p.sehir, country=p.ulke,
        lat=p.enlem, lon=p.boylam,
        p1_isim=p.isim, p2_isim="",
        mod="bireysel_natal", utc_offset=p.utc_offset,
        lang=p.lang,
    )
    motor.fbst_analizi_yap(sessiz=True)
    _cache_engine(motor)
    return motor

def _collect_sabian_data(motor):
    """Collect Sabian symbols for all planets in the natal chart."""
    try:

        BURCLAR = ["Koç","Boğa","İkizler","Yengeç","Aslan","Başak","Terazi","Akrep","Yay","Oğlak","Kova","Balık"]
        jd = motor.get_natal_julian_day("p1")
        sabianlar = []
        for g_ad, g_id in list(GEZEGENLER.items())[:12]:
            try:
                deg = get_planetary_position(jd, g_id)
                sonuc = motor.sabian_okuyucu(g_ad, deg)
                if sonuc:
                    burc = BURCLAR[int(deg // 30)]
                    derece = deg % 30
                    sabianlar.append({
                        "gezegen": g_ad,
                        "derece": round(deg, 1),
                        "derece_str": f"{derece:.1f}° {burc}",
                        "sembol": _strip_html(sonuc)
                    })
            except:
                continue
        return sabianlar
    except:
        return []

def _aspect_interpretasyon_kutuphanesi():
    """Dev interpretasyon kütüphanesi: gezegen profilleri × açı türleri × ev bağlamı.
    Her çift için 5 açı tipinde doğrudan yorum + üretici ile eksikleri tamamlama."""

    _EN = _i18n_get_lang() == "en"

    _EN_OZ = {
        "Güneş": "core self, identity, life purpose, creative power, authority, leadership",
        "Ay": "emotions, inner world, mother, nurturing, habits, intuition, need for security",
        "Merkür": "mind, communication, logic, learning, analysis, writing, short journeys",
        "Venüs": "love, beauty, values, harmony, aesthetics, attraction, money, comfort",
        "Mars": "action, passion, courage, anger, competition, will, fighting energy",
        "Jüpiter": "abundance, luck, expansion, philosophy, faith, learning, optimism",
        "Satürn": "discipline, limits, responsibility, maturity, structure, fear, patience, lessons",
        "Uranüs": "freedom, revolution, sudden change, invention, rebellious spirit, independence, genius",
        "Neptün": "dreams, inspiration, intuition, haze, spirituality, idealism, confusion",
        "Plüton": "transformation, power, death and rebirth, obsession, depth, hidden power",
        "Chiron": "wound, vulnerability, healing, wisdom, healer's wound, acceptance",
        "Juno": "commitment, marriage, loyalty, partnership, justice, relationship vows",
        "Ceres": "nurturing, motherhood, loss, acceptance, compassion, nourishment, nature",
        "Pallas": "wisdom, strategy, creative intelligence, artistic talent, warrior spirit, foresight",
        "Vesta": "devotion, focus, sacred fire, inner discipline, service, the Temple",
        "Eros": "passionate love, desire, sexuality, lust, creative passion, zest for life",
        "Psyche": "soul, psychology, deep bond, vulnerability, intuition, spiritual love",
        "Ruh Noktası": "life purpose, spiritual direction, career path, destiny, source of inspiration",
        "Evlilik Noktası": "relationship potential, marriage theme, long-term partnership, search for harmony",
        "Aşk Noktası": "love potential, romantic attraction, emotional bonding, sexual harmony",
        "Tutku Noktası": "intense passion, desire, ambition, obsession, deep attraction, sexual energy",
        "Para Noktası": "material potential, financial luck, value creation, abundance",
    }

    GEZEGENLER = {
        "Güneş": {"oz": "öz benlik, kimlik, hayati amaç, yaratıcı güç, otorite, liderlik",
                  "ev": {1:"dış görünüş ve kişilik",2:"değerler ve maddi güvenlik",3:"iletişim ve yakın çevre",4:"kökler ve aile",5:"yaratıcılık ve aşk",6:"sağlık ve günlük rutin",7:"ilişkiler ve ortaklıklar",8:"dönüşüm ve ortak kaynaklar",9:"inançlar ve yüksek öğrenim",10:"kariyer ve toplumsal statü",11:"sosyal çevre ve idealler",12:"bilinçaltı ve ruhsal yolculuk"}},
        "Ay": {"oz": "duygular, iç dünya, anne, besleme, alışkanlıklar, sezgi, güven ihtiyacı",
               "ev": {1:"duygusal dışavurum",2:"güvenlik arayışı",3:"kısa vadeli duygusal paylaşımlar",4:"aile bağı ve yuva hissi",5:"yaratıcı duygusal ifade",6:"günlük bakım alışkanlıkları",7:"duygusal partner",8:"derin duygusal dönüşüm",9:"duygusal inanç",10:"toplumsal roller duygusu",11:"arkadaşlık duyguları",12:"bilinçaltı duygular ve gizli korkular"}},
        "Merkür": {"oz": "zihin, iletişim, mantık, öğrenme, analiz, yazma, kısa yolculuklar",
                   "ev": {1:"iletişim tarzı",2:"parasal düşünce",3:"kardeşler ve yakın çevre iletişimi",4:"aile içi iletişim",5:"yaratıcı zihin",6:"çalışma ortamı iletişimi",7:"partnerle diyalog",8:"derin araştırma",9:"felsefi düşünce",10:"kariyer iletişimi",11:"grup çalışmaları",12:"bilinçaltı düşünce kalıpları"}},
        "Venüs": {"oz": "aşk, güzellik, değerler, harmoni, estetik, çekim, para, rahatlık",
                  "ev": {1:"fiziksel çekicilik",2:"para ve maddi değerler",3:"iletişimde çekicilik",4:"aile içi sevgi",5:"romantik aşk",6:"güzel alışkanlıklar",7:"ilişkiler ve evlilik",8:"cinsellik ve duygusal paylaşımlar",9:"güzellik felsefesi",10:"kariyerde estetik",11:"arkadaşlık ve sosyal zevkler",12:"gizli aşklar"}},
        "Mars": {"oz": "eylem, tutku, cesaret, öfke, rekabet, irade, savaş enerjisi",
                 "ev": {1:"dışa vurulan cesaret",2:"parasal mücadele",3:"sözlü tartışma",4:"aile içi mücadele",5:"tutkulu yaratıcılık",6:"iş hayatı ve sağlık mücadelesi",7:"ilişkilerde çatışma",8:"derin dönüşüm ve kriz yönetimi",9:"felsefi mücadele",10:"kariyer hırsı",11:"grup çalışmaları",12:"bilinçaltı öfke"}},
        "Jüpiter": {"oz": "bolluk, şans, genişleme, felsefe, inanç, öğrenme, iyimserlik",
                    "ev": {1:"geniş kişilik",2:"maddi bolluk",3:"iletişimde cömertlik",4:"aile içi bolluk",5:"yaratıcı bolluk",6:"sağlıkta şans",7:"ilişkilerde bolluk",8:"ortak kaynaklarda bolluk",9:"felsefi genişleme",10:"kariyerde bolluk",11:"sosyal çevre bolluğu",12:"ruhsal genişleme"}},
        "Satürn": {"oz": "disiplin, sınırlar, sorumluluk, olgunluk, yapı, korku, sabır, dersler",
                   "ev": {1:"kişisel sorumluluklar",2:"maddi sınırlar",3:"iletişimde kısıtlamalar",4:"aile köklerinde sorumluluklar",5:"yaratıcı kısıtlamalar",6:"sağlık disiplini",7:"ilişkilerde sınırlar",8:"derin korkular",9:"felsefi kısıtlamalar",10:"kariyer sorumlulukları",11:"sosyal sınırlamalar",12:"bilinçaltı korkular"}},
        "Uranüs": {"oz": "özgürlük, devrim, ani değişim, icat, asi ruh, bağımsızlık, deha",
                   "ev": {1:"kişisel özgürlük",2:"para ve değerlerde değişimler",3:"iletişimde yenilikçilik",4:"aile köklerinde değişimler",5:"yaratıcı devrim",6:"iş hayatında değişiklikler",7:"ilişkilerde ani başlangıçlar",8:"ani dönüşüm",9:"felsefi devrim",10:"kariyerde yön değişimi",11:"sosyal çevre değişimi",12:"bilinçaltı devrim"}},
        "Neptün": {"oz": "hayal, ilham, sezgi, puslu, maneviyat, idealizm, kafa karışıklığı",
                   "ev": {1:"kişisel hayaller",2:"para ve değerlerde hayal kırıklıkları",3:"iletişimde belirsizlik",4:"aile içi hayaller",5:"yaratıcı ilham",6:"sağlıkta belirsizlik",7:"ilişkilerde idealizm",8:"derin sezgisel dönüşüm",9:"ruhsal ilham",10:"kariyerde hayaller",11:"sosyal hayaller",12:"bilinçaltı sezgiler"}},
        "Plüton": {"oz": "dönüşüm, güç, ölüm-yeniden doğum, obsesyon, derinlik, gizli güç",
                   "ev": {1:"kişisel güç",2:"para ve değerlerde güç mücadeleleri",3:"iletişimde güç oyunları",4:"aile köklerinde güç dinamikleri",5:"yaratıcı güç",6:"iş hayatında güç mücadelesi",7:"ilişkilerde güç dengeleri",8:"derin cinsel ve ruhsal dönüşüm",9:"felsefi dönüşüm",10:"kariyerde güç",11:"sosyal güç",12:"bilinçaltı güç"}},
        "Chiron": {"oz": "yara, kırılganlık, iyileşme, bilgelik, şifacı yara, kabul",
                   "ev": {1:"kişisel yara",2:"değer yarası",3:"iletişim yarası",4:"aile yarası",5:"yaratıcı yara",6:"sağlık yarası",7:"ilişki yarası",8:"derin yara",9:"felsefi yara",10:"kariyer yarası",11:"sosyal yara",12:"bilinçaltı yara"}},
    }

    ASTEROITLER = {
        "Juno": {"oz": "bağlılık, evlilik, sadakat, ortaklık, adalet, ilişki taahhüdü",
                 "ev": {1:"kişisel bağlılık",2:"değer bağlılığı",3:"iletişimde sadakat",4:"aile bağlılığı",5:"yaratıcı bağlılık",6:"iş hayatı bağlılığı",7:"evlilik ve uzun vadeli ortaklıklar",8:"cinsel bağlılık",9:"felsefi bağlılık",10:"kariyer bağlılığı",11:"arkadaşlık bağlılığı",12:"ruhsal bağlılık"}},
        "Ceres": {"oz": "besleme, annelik, kayıp, kabul, şefkat, beslenme, doğa",
                  "ev": {1:"kişisel besleme",2:"değer beslemesi",3:"iletişimde besleme",4:"aile beslemesi",5:"yaratıcı besleme",6:"iş hayatı beslemesi",7:"partner beslemesi",8:"derin besleme ve kayıp",9:"felsefi besleme",10:"kariyer beslemesi",11:"arkadaşlık beslemesi",12:"ruhsal besleme"}},
        "Pallas": {"oz": "bilgelik, strateji, yaratıcı zekâ, sanatsal yetenek, savaşçılık, öngörü",
                   "ev": {1:"kişisel strateji",2:"maddi strateji",3:"iletişim stratejisi",4:"aile stratejisi",5:"yaratıcı strateji",6:"iş hayatı stratejisi",7:"ilişki stratejisi",8:"derin strateji",9:"felsefi strateji",10:"kariyer stratejisi",11:"grup stratejisi",12:"ruhsal strateji"}},
        "Vesta": {"oz": "adanma, odak, kutsal ateş, iç disiplin, hizmet, Tapınak",
                  "ev": {1:"kişisel adanma",2:"değer adanması",3:"iletişim adanması",4:"aile adanması",5:"yaratıcı adanma",6:"iş hayatı adanması",7:"ilişki adanması",8:"derin adanma",9:"felsefi adanma",10:"kariyer adanması",11:"arkadaşlık adanması",12:"ruhsal adanma"}},
        "Eros": {"oz": "tutkulu aşk, arzu, cinsellik, şehvet, yaratıcı tutku, yaşam coşkusu",
                 "ev": {1:"kişisel tutku",2:"maddi tutku",3:"iletişim tutkusu",4:"aile tutkusu",5:"romantik tutku",6:"iş hayatı tutkusu",7:"ilişki tutkusu",8:"derin tutku",9:"felsefi tutku",10:"kariyer tutkusu",11:"arkadaşlık tutkusu",12:"ruhsal tutku"}},
        "Psyche": {"oz": "ruh, psikoloji, derin bağ, kırılganlık, sezgi, ruhsal aşk",
                   "ev": {1:"kişisel ruh",2:"değer psikolojisi",3:"iletişim psikolojisi",4:"aile psikolojisi",5:"yaratıcı ruh",6:"iş hayatı psikolojisi",7:"ilişki psikolojisi",8:"derin psikoloji",9:"felsefi psikoloji",10:"kariyer psikolojisi",11:"arkadaşlık psikolojisi",12:"bilinçaltı psikoloji"}},
    }

    ARAP_NOKTALARI = {
        "Ruh Noktası": {"oz": "yaşam amacı, ruhsal yön, kariyer yönü, kader, ilham kaynağı",
                        "ev": {1:"yaşam amacı benlik üzerinden",2:"değer ve güvenlik amacı",3:"iletişim ve çevre amacı",4:"aile ve kökler amacı",5:"yaratıcılık ve aşk amacı",6:"hizmet ve sağlık amacı",7:"ilişki ve ortaklık amacı",8:"dönüşüm ve derinlik amacı",9:"öğrenim ve felsefe amacı",10:"kariyer ve toplumsal amaç",11:"sosyal çevre ve idealler amacı",12:"ruhsal arınma amacı"}},
        "Evlilik Noktası": {"oz": "ilişki potansiyeli, evlilik teması, uzun vadeli ortaklık, uyum arayışı",
                           "ev": {1:"benlik ile ilişki dengesi",2:"değer ve güvenlik ilişkisi",3:"iletişim ve çevre ilişkisi",4:"aile ve kökler ilişkisi",5:"yaratıcılık ve aşk ilişkisi",6:"hizmet ve sağlık ilişkisi",7:"doğrudan evlilik ve ortaklık",8:"derin dönüşüm ilişkisi",9:"felsefi ve uzak kültür ilişkisi",10:"kariyer ve toplumsal ilişki",11:"arkadaşlık ve grup ilişkisi",12:"ruhsal ve gizli ilişki"}},
        "Aşk Noktası": {"oz": "aşk potansiyeli, romantik çekim, duygusal bağlılık, cinsel uyum",
                       "ev": {1:"fiziksel çekim",2:"değer aşkı",3:"iletişim aşkı",4:"aile aşkı",5:"doymuş romantik aşk",6:"iş hayatı aşkı",7:"ilişki aşkı",8:"derin aşk",9:"felsefi aşk",10:"kariyer aşkı",11:"arkadaşlık aşkı",12:"ruhsal aşk"}},
        "Tutku Noktası": {"oz": "yoğun tutku, arzu, hırs, obsesyon, derin çekim, cinsel enerji",
                         "ev": {1:"kişisel tutku",2:"değer tutkusu",3:"iletişim tutkusu",4:"aile tutkusu",5:"yaratıcı tutku",6:"iş hayatı tutkusu",7:"ilişki tutkusu",8:"derin tutku",9:"felsefi tutku",10:"kariyer tutkusu",11:"arkadaşlık tutkusu",12:"ruhsal tutku"}},
        "Para Noktası": {"oz": "maddi potansiyel, finansal şans, değer üretimi, bolluk",
                        "ev": {1:"kişisel para potansiyeli",2:"doğrudan para üretimi",3:"iletişim ve çevre para potansiyeli",4:"aile mirası",5:"yaratıcı para",6:"iş hayatı para üretimi",7:"ilişki ve ortaklık para potansiyeli",8:"ortak kaynaklar",9:"uzak ülkeler ve bolluk",10:"kariyer para potansiyeli",11:"sosyal çevre para",12:"ruhsal bolluk"}},
    }

    CIFT_TEMA = {
        ("Güneş","Ay"): "öz benlik ile duygusal dünya arasında köprü",
        ("Güneş","Merkür"): "kimlik ile zihin arasında doğrudan bağlantı",
        ("Güneş","Venüs"): "öz benlik ile sevgi ve değerler arasında uyum",
        ("Güneş","Mars"): "kimlik ile eylem ve tutku arasında güçlü bağ",
        ("Güneş","Jüpiter"): "benlik ile bolluk ve genişleme arasında destek",
        ("Güneş","Satürn"): "öz ile sorumluluk ve sınırlar arasında denge",
        ("Güneş","Uranüs"): "kimlik ile özgürlük ve devrim arasında kopuş",
        ("Güneş","Neptün"): "benlik ile hayaller ve sezgiler arasında pusluluk",
        ("Güneş","Plüton"): "öz ile güç ve dönüşüm arasında derin bağ",
        ("Güneş","Chiron"): "benlik yarası ve kabul mücadelesi",
        ("Ay","Merkür"): "duygu ile zihin arasında köprü",
        ("Ay","Venüs"): "duygusal dünya ile sevgi arasında derin uyum",
        ("Ay","Mars"): "duygular ile eylem arasında çatışma ve tutku",
        ("Ay","Jüpiter"): "duygusal güvenlik ile bolluk arasında genişleme",
        ("Ay","Satürn"): "duygular ile sınırlar arasında zorlu denge",
        ("Ay","Uranüs"): "iç dünya ile özgürlük arasında ani kopuşlar",
        ("Ay","Neptün"): "duygular ile hayaller arasında derin sezgisellik",
        ("Ay","Plüton"): "duygusal dünya ile güç arasında yoğun dönüşüm",
        ("Ay","Chiron"): "duygusal yara ve beslenme ihtiyacı",
        ("Ay","KAD"): "aile kökleri ile duygusal alışkanlıklar arasında bağ",
        ("Ay","Lilith"): "duygusal gizlilik ve bastırılmış arzu",
        ("Merkür","Venüs"): "zihin ile çekicilik arasında uyum",
        ("Merkür","Mars"): "düşünce ile eylem arasında hız",
        ("Merkür","Jüpiter"): "zihin ile genişleme arasında bolluk",
        ("Merkür","Satürn"): "düşünce ile sınırlar arasında ciddiyet",
        ("Merkür","Uranüs"): "zihin ile devrim arasında deha",
        ("Merkür","Neptün"): "düşünce ile hayal arasında puslu zekâ",
        ("Merkür","Plüton"): "zihin ile güç arasında derin analiz",
        ("Merkür","Chiron"): "iletişim yarası ve ifade zorluğu",
        ("Merkür","KAD"): "aile köklerinde iletişim kalıpları",
        ("Merkür","Lilith"): "zihinsel gizlilik ve bastırılmış düşünce",
        ("Venüs","Mars"): "çekicilik ile tutku arasında güçlü çekim",
        ("Venüs","Jüpiter"): "sevgi ile bolluk arasında genişleme",
        ("Venüs","Satürn"): "aşk ile sınırlar arasında olgunlaşma",
        ("Venüs","Uranüs"): "değerler ile devrim arasında ani değişim",
        ("Venüs","Neptün"): "sevgi ile hayal arasında idealizm",
        ("Venüs","Plüton"): "aşk ile güç arasında yoğun dönüşüm",
        ("Venüs","Chiron"): "sevgi yarası ve kabul arayışı",
        ("Venüs","KAD"): "aile köklerinde sevgi ve değer kalıpları",
        ("Venüs","Lilith"): "aşkta gizlilik ve bastırılmış arzu",
        ("Mars","Jüpiter"): "tutku ile bolluk arasında genişleme",
        ("Mars","Satürn"): "eylem ile sınırlar arasında disiplin",
        ("Mars","Uranüs"): "tutku ile devrim arasında ani patlamalar",
        ("Mars","Neptün"): "eylem ile hayal arasında puslu mücadele",
        ("Mars","Plüton"): "tutku ile güç arasında yoğun savaş",
        ("Mars","Chiron"): "savaş yarası ve kırılgan cesaret",
        ("Mars","KAD"): "aile köklerinde savaş ve koruma",
        ("Mars","Lilith"): "tutkulu gizlilik ve bastırılmış öfke",
        ("Jüpiter","Satürn"): "bolluk ile sınırlar arasında denge",
        ("Jüpiter","Uranüs"): "genişleme ile devrim arasında ani şans",
        ("Jüpiter","Neptün"): "inanç ile hayal arasında manevi genişleme",
        ("Jüpiter","Plüton"): "bolluk ile güç arasında derin genişleme",
        ("Jüpiter","Chiron"): "inanç yarası ve manevi iyileşme",
        ("Jüpiter","KAD"): "aile köklerinde bolluk ve inanç",
        ("Jüpiter","Lilith"): "inançta gizlilik ve genişleme",
        ("Satürn","Uranüs"): "sınır ile devrim arasında zorlu denge",
        ("Satürn","Neptün"): "disiplin ile hayal arasında puslu yapı",
        ("Satürn","Plüton"): "sınır ile güç arasında yoğun yapı",
        ("Satürn","Chiron"): "korku yarası ve olgunlaşma",
        ("Satürn","KAD"): "aile köklerinde sorumluluk ve sınırlar",
        ("Satürn","Lilith"): "sınırda gizlilik ve bastırılmış korku",
        ("Uranüs","Neptün"): "devrim ile hayal arasında manevi değişim",
        ("Uranüs","Plüton"): "özgürlük ile güç arasında derin devrim",
        ("Uranüs","Chiron"): "özgürlük yarası ve kabul",
        ("Uranüs","KAD"): "aile köklerinde devrim ve ani değişim",
        ("Uranüs","Lilith"): "özgürlükte gizlilik ve asi ruh",
        ("Neptün","Plüton"): "hayal ile güç arasında manevi dönüşüm",
        ("Neptün","Chiron"): "hayal yarası ve ruhsal iyileşme",
        ("Neptün","KAD"): "aile köklerinde hayaller ve pus",
        ("Neptün","Lilith"): "hayalde gizlilik ve bastırılmış sezgi",
        ("Plüton","Chiron"): "dönüşüm yarası ve derin iyileşme",
        ("Plüton","KAD"): "aile köklerinde güç ve derin dönüşüm",
        ("Plüton","Lilith"): "güçte gizlilik ve bastırılmış tutku",
        ("Juno","Güneş"): "bağlılık ile kimlik arasında güçlü bağ",
        ("Juno","Ay"): "bağlılık ile duygular arasında derin uyum",
        ("Juno","Venüs"): "bağlılık ile çekicilik arasında evlilik teması",
        ("Juno","Mars"): "bağlılık ile tutku arasında zorlu denge",
        ("Ceres","Güneş"): "besleme ile kimlik arasında anne enerjisi",
        ("Ceres","Ay"): "besleme ile duygular arasında derin şefkat",
        ("Ceres","Venüs"): "besleme ile çekicilik arasında koşulsuz sevgi",
        ("Ceres","Merkür"): "besleme ile zihin arasında iletişim bakımı",
        ("Pallas","Güneş"): "strateji ile kimlik arasında bilgelik",
        ("Pallas","Merkür"): "strateji ile zihin arasında analitik güç",
        ("Pallas","Satürn"): "strateji ile sınırlar arasında yapısal bilgelik",
        ("Pallas","Plüton"): "strateji ile güç arasında derin öngörü",
        ("Vesta","Güneş"): "adanma ile kimlik arasında kutsal ateş",
        ("Vesta","Ay"): "adanma ile duygular arasında iç disiplin",
        ("Vesta","Venüs"): "adanma ile çekicilik arasında kutsal sevgi",
        ("Vesta","Plüton"): "adanma ile güç arasında derin odak",
        ("Eros","Venüs"): "tutku ile çekicilik arasında şehvetli aşk",
        ("Eros","Mars"): "tutku ile eylem arasında yoğun arzu",
        ("Eros","Plüton"): "tutku ile güç arasında derin dönüşüm",
        ("Eros","Güneş"): "tutku ile kimlik arasında yaşam coşkusu",
        ("Psyche","Ay"): "ruh ile duygular arasında derin bağ",
        ("Psyche","Venüs"): "ruh ile çekicilik arasında ruhsal aşk",
        ("Psyche","Plüton"): "ruh ile güç arasında psikolojik dönüşüm",
        ("Psyche","Neptün"): "ruh ile hayal arasında manevi sezgi",
        ("Ruh Noktası","Güneş"): "yaşam amacı ile kimlik arasında derin bağ",
        ("Ruh Noktası","Ay"): "yaşam amacı ile duygular arasında sezgisel yön",
        ("Ruh Noktası","Venüs"): "yaşam amacı ile çekicilik arasında estetik yön",
        ("Ruh Noktası","Mars"): "yaşam amacı ile tutku arasında eylem odaklı yön",
        ("Evlilik Noktası","Venüs"): "ilişki potansiyeli ile çekicilik arasında güçlü uyum",
        ("Evlilik Noktası","Jüpiter"): "ilişki potansiyeli ile bolluk arasında genişleme",
        ("Evlilik Noktası","Satürn"): "ilişki potansiyeli ile sınırlar arasında ciddi taahhüt",
        ("Evlilik Noktası","Neptün"): "ilişki potansiyeli ile hayal arasında idealist ilişki",
        ("Aşk Noktası","Venüs"): "aşk potansiyeli ile çekicilik arasında güçlü romantizm",
        ("Aşk Noktası","Mars"): "aşk potansiyeli ile tutku arasında tutkulu aşk",
        ("Aşk Noktası","Plüton"): "aşk potansiyeli ile güç arasında yoğun dönüşüm",
        ("Aşk Noktası","Güneş"): "aşk potansiyeli ile kimlik arasında benlik aşkı",
        ("Tutku Noktası","Mars"): "yoğun tutku ile eylem arasında güçlü hırs",
        ("Tutku Noktası","Plüton"): "yoğun tutku ile güç arasında derin obsesyon",
        ("Tutku Noktası","Venüs"): "yoğun tutku ile çekicilik arasında şehvetli enerji",
        ("Tutku Noktası","Ay"): "yoğun tutku ile duygular arasında derin arzu",
        ("Para Noktası","Jüpiter"): "maddi potansiyel ile bolluk arasında güçlü şans",
        ("Para Noktası","Satürn"): "maddi potansiyel ile sınırlar arasında yapı",
        ("Para Noktası","Venüs"): "maddi potansiyel ile çekicilik arasında estetik değer",
        ("Para Noktası","Plüton"): "maddi potansiyel ile güç arasında derin dönüşüm",
    }

    CIFT_TEMA_EN = {
        ("Güneş","Ay"): "the bridge between the core self and the emotional world",
        ("Güneş","Merkür"): "the direct link between identity and the mind",
        ("Güneş","Venüs"): "the harmony between the core self and love and values",
        ("Güneş","Mars"): "the powerful bond between identity and action and passion",
        ("Güneş","Jüpiter"): "the support between the self and abundance and expansion",
        ("Güneş","Satürn"): "the balance between the self and responsibility and limits",
        ("Güneş","Uranüs"): "the break between identity and freedom and revolution",
        ("Güneş","Neptün"): "the haziness between the self and dreams and intuitions",
        ("Güneş","Plüton"): "the deep bond between the self and power and transformation",
        ("Güneş","Chiron"): "the wound of the self and the struggle for acceptance",
        ("Ay","Merkür"): "the bridge between emotion and the mind",
        ("Ay","Venüs"): "the deep harmony between the emotional world and love",
        ("Ay","Mars"): "the conflict and passion between emotions and action",
        ("Ay","Jüpiter"): "the expansion between emotional security and abundance",
        ("Ay","Satürn"): "the demanding balance between feelings and limits",
        ("Ay","Uranüs"): "the sudden ruptures between the inner world and freedom",
        ("Ay","Neptün"): "the deep intuition between feelings and dreams",
        ("Ay","Plüton"): "the intense transformation between the emotional world and power",
        ("Ay","Chiron"): "the emotional wound and the need for nurturing",
        ("Ay","KAD"): "the bond between family roots and emotional habits",
        ("Ay","Lilith"): "emotional secrecy and repressed desire",
        ("Merkür","Venüs"): "the harmony between mind and charm",
        ("Merkür","Mars"): "speed between thought and action",
        ("Merkür","Jüpiter"): "the abundance between mind and expansion",
        ("Merkür","Satürn"): "the seriousness between thought and limits",
        ("Merkür","Uranüs"): "the genius between mind and revolution",
        ("Merkür","Neptün"): "the misty intellect between thought and dream",
        ("Merkür","Plüton"): "the deep analysis between mind and power",
        ("Merkür","Chiron"): "the wound of communication and the difficulty of expression",
        ("Merkür","KAD"): "communication patterns in family roots",
        ("Merkür","Lilith"): "mental secrecy and repressed thought",
        ("Venüs","Mars"): "the powerful attraction between charm and passion",
        ("Venüs","Jüpiter"): "the expansion between love and abundance",
        ("Venüs","Satürn"): "maturation between love and limits",
        ("Venüs","Uranüs"): "the sudden change between values and revolution",
        ("Venüs","Neptün"): "idealism between love and dream",
        ("Venüs","Plüton"): "the intense transformation between love and power",
        ("Venüs","Chiron"): "the wound of love and the search for acceptance",
        ("Venüs","KAD"): "patterns of love and values in family roots",
        ("Venüs","Lilith"): "secrecy in love and repressed desire",
        ("Mars","Jüpiter"): "the expansion between passion and abundance",
        ("Mars","Satürn"): "discipline between action and limits",
        ("Mars","Uranüs"): "the sudden explosions between passion and revolution",
        ("Mars","Neptün"): "the misty struggle between action and dream",
        ("Mars","Plüton"): "the intense war between passion and power",
        ("Mars","Chiron"): "the wound of battle and fragile courage",
        ("Mars","KAD"): "war and protection in family roots",
        ("Mars","Lilith"): "passionate secrecy and repressed anger",
        ("Jüpiter","Satürn"): "the balance between abundance and limits",
        ("Jüpiter","Uranüs"): "the sudden luck between expansion and revolution",
        ("Jüpiter","Neptün"): "the spiritual expansion between faith and dream",
        ("Jüpiter","Plüton"): "the deep expansion between abundance and power",
        ("Jüpiter","Chiron"): "the wound of faith and spiritual healing",
        ("Jüpiter","KAD"): "abundance and faith in family roots",
        ("Jüpiter","Lilith"): "secrecy and expansion in faith",
        ("Satürn","Uranüs"): "the demanding balance between limit and revolution",
        ("Satürn","Neptün"): "the misty structure between discipline and dream",
        ("Satürn","Plüton"): "the intense structure between limit and power",
        ("Satürn","Chiron"): "the wound of fear and maturation",
        ("Satürn","KAD"): "responsibility and limits in family roots",
        ("Satürn","Lilith"): "secrecy at the limit and repressed fear",
        ("Uranüs","Neptün"): "the spiritual change between revolution and dream",
        ("Uranüs","Plüton"): "the deep revolution between freedom and power",
        ("Uranüs","Chiron"): "the wound of freedom and acceptance",
        ("Uranüs","KAD"): "revolution and sudden change in family roots",
        ("Uranüs","Lilith"): "secrecy in freedom and the rebellious spirit",
        ("Neptün","Plüton"): "the spiritual transformation between dream and power",
        ("Neptün","Chiron"): "the wound of dreams and spiritual healing",
        ("Neptün","KAD"): "dreams and fog in family roots",
        ("Neptün","Lilith"): "secrecy in dreams and repressed intuition",
        ("Plüton","Chiron"): "the wound of transformation and deep healing",
        ("Plüton","KAD"): "power and deep transformation in family roots",
        ("Plüton","Lilith"): "secrecy in power and repressed passion",
        ("Juno","Güneş"): "the powerful bond between commitment and identity",
        ("Juno","Ay"): "the deep harmony between commitment and feelings",
        ("Juno","Venüs"): "the marriage theme between commitment and charm",
        ("Juno","Mars"): "the demanding balance between commitment and passion",
        ("Ceres","Güneş"): "the mother energy between nurturing and identity",
        ("Ceres","Ay"): "the deep compassion between nurturing and feelings",
        ("Ceres","Venüs"): "unconditional love between nurturing and charm",
        ("Ceres","Merkür"): "caring communication between nurturing and mind",
        ("Pallas","Güneş"): "wisdom between strategy and identity",
        ("Pallas","Merkür"): "analytical power between strategy and mind",
        ("Pallas","Satürn"): "structural wisdom between strategy and limits",
        ("Pallas","Plüton"): "deep foresight between strategy and power",
        ("Vesta","Güneş"): "the sacred fire between devotion and identity",
        ("Vesta","Ay"): "inner discipline between devotion and feelings",
        ("Vesta","Venüs"): "sacred love between devotion and charm",
        ("Vesta","Plüton"): "deep focus between devotion and power",
        ("Eros","Venüs"): "lustful love between passion and charm",
        ("Eros","Mars"): "intense desire between passion and action",
        ("Eros","Plüton"): "the deep transformation between passion and power",
        ("Eros","Güneş"): "zest for life between passion and identity",
        ("Psyche","Ay"): "the deep bond between soul and feelings",
        ("Psyche","Venüs"): "spiritual love between soul and charm",
        ("Psyche","Plüton"): "psychological transformation between soul and power",
        ("Psyche","Neptün"): "spiritual intuition between soul and dream",
        ("Ruh Noktası","Güneş"): "the deep bond between life purpose and identity",
        ("Ruh Noktası","Ay"): "the intuitive direction between life purpose and feelings",
        ("Ruh Noktası","Venüs"): "the aesthetic direction between life purpose and charm",
        ("Ruh Noktası","Mars"): "the action-oriented direction between life purpose and passion",
        ("Evlilik Noktası","Venüs"): "the strong harmony between relationship potential and charm",
        ("Evlilik Noktası","Jüpiter"): "the expansion between relationship potential and abundance",
        ("Evlilik Noktası","Satürn"): "the serious commitment between relationship potential and limits",
        ("Evlilik Noktası","Neptün"): "the idealist relationship between relationship potential and dream",
        ("Aşk Noktası","Venüs"): "the strong romance between love potential and charm",
        ("Aşk Noktası","Mars"): "passionate love between love potential and passion",
        ("Aşk Noktası","Plüton"): "the intense transformation between love potential and power",
        ("Aşk Noktası","Güneş"): "self-love between love potential and identity",
        ("Tutku Noktası","Mars"): "the strong ambition between intense passion and action",
        ("Tutku Noktası","Plüton"): "deep obsession between intense passion and power",
        ("Tutku Noktası","Venüs"): "lustful energy between intense passion and charm",
        ("Tutku Noktası","Ay"): "deep desire between intense passion and feelings",
        ("Para Noktası","Jüpiter"): "the strong luck between material potential and abundance",
        ("Para Noktası","Satürn"): "structure between material potential and limits",
        ("Para Noktası","Venüs"): "the aesthetic value between material potential and charm",
        ("Para Noktası","Plüton"): "the deep transformation between material potential and power",
    }

    OZEL_YORUMLAR = {
        ("Güneş","Ay","Kavuşum"): "Güneş ve Ay'ınız aynı burçta birleşmiş. Öz benliğiniz ile duygusal dünyanız tam uyum içinde — ne istediğiniz ve neye ihtiyacınız olduğu konusunda doğal bir berraklığınız var. Bu kavuşum, hayatınızda güçlü bir iç tutarlılık sağlar.",
        ("Güneş","Ay","Karşıt"): "Güneş ve Ay'ınız zıt burçlarda. Öz benliğiniz ile duygusal ihtiyaçlarınız sürekli denge arayışında — ne istediğiniz ile neye ihtiyacınız olduğu arasında gidip gelirsiniz. Bu karşıtlık, her iki tarafı da tam olarak anlamanızı gerektirir.",
        ("Güneş","Ay","Kare"): "Güneş ve Ay'ınız kare açıda. Kimliğiniz ile duygusal dünyanız arasındaki gerilim, iç çatışmalara yol açabilir. Ancak bu mücadele, kendinizi daha derin tanımanız için güçlü bir fırsat sunar.",
        ("Güneş","Ay","Trigon"): "Güneş ve Ay'ınız trigon açıda. Öz benliğiniz ile duygularınız doğal uyum içinde — ne istediğiniz konusunda içsel bir berraklığınız var. Bu enerjiyi yaratıcı projelerinizde kullanabilirsiniz.",
        ("Güneş","Ay","Sekstil"): "Güneş ve Ay'ınız sekstil açıda. Öz benlik ile duygusal dünya arasında destekleyici bir bağ var. Bu fırsatı değerlendirerek, duygusal zekanızı ve kişisel powerınızı birleştirebilirsiniz.",
        ("Güneş","Merkür","Kavuşum"): "Güneş ve Merkür'ünüz kavuşumda. Kimliğiniz ile zihinsel gücünüz aynı noktada — düşünce tarzınız ve iletişim şekliniz benliğinizi yansıtıyor. Zihniniz hızlı çalışır ve fikirlerinizi cesurca ifade edersiniz.",
        ("Güneş","Merkür","Karşıt"): "Güneş ve Merkür'ünüz karşıt burçlarda. Öz benliğiniz ile düşünce tarzınız arasında bir denge arayışı var — ne istediğinizi söylerken aslında ne düşündüğünüz ile çelişebilirsiniz.",
        ("Güneş","Merkür","Kare"): "Güneş ve Merkür'ünüz kare açıda. Kimliğiniz ile zihinsel analiz arasında gerilim var — cesurca konuşurken bazen düşüncelerinizi tam ifade edemeyebilirsiniz. Bu iletişim becerilerinizi geliştirmeniz için bir fırsat.",
        ("Güneş","Merkür","Trigon"): "Güneş ve Merkür'ünüz trigon açıda. Düşünce ile kimlik doğal uyum içinde — zihniniz berrak, iletişiminiz akıcı ve fikirlerinizi kolayca hayata geçirirsiniz.",
        ("Güneş","Merkür","Sekstil"): "Güneş ve Merkür'ünüz sekstil açıda. Zihinsel yetenekleriniz ile kimliğiniz arasında destekleyici bir bağ var. Yaratıcı fikirlerinizi güçlü bir şekilde ifade edebilirsiniz.",
        ("Güneş","Venüs","Kavuşum"): "Güneş ve Venüs'ünüz kavuşumda. Öz benliğiniz ile sevgi diliniz aynı noktada — kendinizi sevme ve değer verme kapasiteniz güçlü. Çekiciliğiniz ve kişisel charminiz doğal olarak parlıyor.",
        ("Güneş","Venüs","Karşıt"): "Güneş ve Venüs'ünüz karşıt burçlarda. Benlik ile sevgi arasında denge arayışı var — kendinizi ifade ederken sevdiklerinizin ihtiyaçlarını da göz önünde bulundurmanız gerekiyor.",
        ("Güneş","Venüs","Kare"): "Güneş ve Venüs'ünüz kare açıda. Kimliğiniz ile sevgi diliniz arasındaki gerilim, ilişkilerinizde zorluklara yol açabilir. Ancak bu mücadele, sevgiyi daha derin anlamanız için bir fırsat.",
        ("Güneş","Venüs","Trigon"): "Güneş ve Venüs'ünüz trigon açıda. Öz benliğiniz ile çekicilik enerjiniz doğal uyum içinde — sevgi ve değerler konusunda içsel bir berraklığınız var.",
        ("Güneş","Venüs","Sekstil"): "Güneş ve Venüs'ünüz sekstil açıda. Kimlik ile sevgi arasında destekleyici bir bağ var. İlişkilerinizde ve yaratıcılığınızda güçlü bir denge kurabilirsiniz.",
        ("Güneş","Mars","Kavuşum"): "Güneş ve Mars'ınız kavuşumda. Kimliğiniz ile savaşçı ruhunuz aynı noktada — cesaret, tutku ve eylem enerjiniz güçlü. Doğal bir lider ve mücadeleci yapıdasınız.",
        ("Güneş","Mars","Karşıt"): "Güneş ve Mars'ınız karşıt burçlarda. Öz benlik ile eylem arasında denge arayışı var — ne istediğiniz konusunda tutkulu ama bazen sabırsız olabilirsiniz.",
        ("Güneş","Mars","Kare"): "Güneş ve Mars'ınız kare açıda. Kimlik ile tutku arasındaki gerilim, öfke ve sabırsızlık yaratabilir. Ancak bu güçlü enerjiyi yaratıcı projelere kanalize etmek, büyük başarılara yol açar.",
        ("Güneş","Mars","Trigon"): "Güneş ve Mars'ınız trigon açıda. Benlik ile eylem doğal uyum içinde — cesur, enerjik ve tutkulu bir yapınız var. Bu enerjiyi hedeflerinize ulaşmak için kullanabilirsiniz.",
        ("Güneş","Mars","Sekstil"): "Güneş ve Mars'ınız sekstil açıda. Kimlik ile tutku arasında destekleyici bir bağ var. Cesur adımlar atarak hayallerinizi hayata geçirebilirsiniz.",
        ("Güneş","Jüpiter","Kavuşum"): "Güneş ve Jüpiteriniz kavuşumda. Öz benliğiniz ile bolluk enerjisi aynı noktada — iyimserlik, cömertlik ve genişleme potansiyeliniz güçlü. Hayatınızda doğal bir şans ve bereket akışı var.",
        ("Güneş","Jüpiter","Karşıt"): "Güneş ve Jüpiteriniz karşıt burçlarda. Benlik ile bolluk arasında denge arayışı var — aşırı iyimserlik ile gerçekçilik arasında gidip gelebilirsiniz.",
        ("Güneş","Jüpiter","Kare"): "Güneş ve Jüpiteriniz kare açıda. Kimlik ile genişleme arasındaki gerilim, aşırıya kaçma eğilimini güçlendirebilir. Ancak bu enerjiyi dengelemek, büyük fırsatlar yaratır.",
        ("Güneş","Jüpiter","Trigon"): "Güneş ve Jüpiteriniz trigon açıda. Benlik ile bolluk doğal uyum içinde — iyimser, cömert ve geniş düşünebilen bir yapınız var.",
        ("Güneş","Jüpiter","Sekstil"): "Güneş ve Jüpiteriniz sekstil açıda. Kimlik ile genişleme arasında destekleyici bir bağ var. Kişisel gelişiminize ve başkalarına fayda sağlayabilirsiniz.",
        ("Güneş","Satürn","Kavuşum"): "Güneş ve Satürn'ünüz kavuşumda. Öz benliğiniz ile sorumluluklarınız aynı noktada — disiplinli, ciddi ve yapısal bir yapınız var. Hayatınızda güçlü bir olgunluk enerjisi hakim.",
        ("Güneş","Satürn","Karşıt"): "Güneş ve Satürn'ünüz karşıt burçlarda. Benlik ile sınırlar arasında denge arayışı — özgürlük ile sorumluluk arasındaki gerilim hayatınızın temel derslerinden biri.",
        ("Güneş","Satürn","Kare"): "Güneş ve Satürn'ünüz kare açıda. Kimlik ile sınırlar arasındaki gerilim, kendinize karşı aşırı katı olmanıza yol açabilir. Bu dersi öğrenmek, gerçek olgunluğun anahtarı.",
        ("Güneş","Satürn","Trigon"): "Güneş ve Satürn'ünüz trigon açıda. Benlik ile yapı doğal uyum içinde — disiplinli, kararlı ve sorumluluk sahibi bir yapınız var.",
        ("Güneş","Satürn","Sekstil"): "Güneş ve Satürn'ünüz sekstil açıda. Kimlik ile sınırlar arasında destekleyici bir bağ var. Disiplinli adımlarla büyük projeler hayata geçirebilirsiniz.",
        ("Güneş","Uranüs","Kavuşum"): "Güneş ve Uranüs'ünüz kavuşumda. Kimliğiniz ile devrimci ruhunuz aynı noktada — özgürlüğünüz, bağımsızlığınız ve yaratıcı dehanız güçlü. Ani değişimler hayatınızda belirgin.",
        ("Güneş","Uranüs","Karşıt"): "Güneş ve Uranüs'ünüz karşıt burçlarda. Özgürlük ile gelenek arasında denge arayışı — asi ruhunuz ile toplumsal beklentiler arasında sürekli bir gerilim.",
        ("Güneş","Uranüs","Kare"): "Güneş ve Uranüs'ünüz kare açıda. Kimlik ile devrim arasındaki gerilim, ani kopuşlara yol açabilir. Bu enerjiyi yapıcı kullanmak, hayatınızı dönüştürür.",
        ("Güneş","Uranüs","Trigon"): "Güneş ve Uranüs'ünüz trigon açıda. Benlik ile özgürlük doğal uyum içinde — yenilikçi, yaratıcı ve bağımsız bir yapınız var.",
        ("Güneş","Uranüs","Sekstil"): "Güneş ve Uranüs'ünüz sekstil açıda. Kimlik ile devrim arasında destekleyici bir bağ var. Yenilikçi değişimler başlatabilirsiniz.",
        ("Güneş","Neptün","Kavuşum"): "Güneş ve Neptün'ünüz kavuşumda. Benliğiniz ile hayalleriniz aynı noktada — sezgisel, yaratıcı ve manevi bir yapınız var. Sanatsal yetenekleriniz güçlü.",
        ("Güneş","Neptün","Karşıt"): "Güneş ve Neptün'ünüz karşıt burçlarda. Gerçekçilik ile hayal arasında denge arayışı — gerçek dünya ile hayal dünyası arasında gidip gelebilirsiniz.",
        ("Güneş","Neptün","Kare"): "Güneş ve Neptün'ünüz kare açıda. Kimlik ile pusluluk arasındaki gerilim, kafa karışıklığı yaratabilir. Ancak bu enerjiyi sanatsal yaratıcılığa kanalize etmek güçlü sonuçlar verir.",
        ("Güneş","Neptün","Trigon"): "Güneş ve Neptün'ünüz trigon açıda. Benlik ile sezgi doğal uyum içinde — manevi dünyanız güçlü ve yaratıcı ilhamınız bereketli.",
        ("Güneş","Neptün","Sekstil"): "Güneş ve Neptün'ünüz sekstil açıda. Kimlik ile hayal arasında destekleyici bir bağ var. Sanatsal ve manevi projelerinizi hayata geçirebilirsiniz.",
        ("Güneş","Plüton","Kavuşum"): "Güneş ve Plüton'uz kavuşumda. Kimliğiniz ile güç enerjiniz aynı noktada — derin bir dönüşüm, kararlılık ve iç güç taşıyorsunuz. Hayatınızda güçlü yeniden doğum döngüleri var.",
        ("Güneş","Plüton","Karşıt"): "Güneş ve Plüton'uz karşıt burçlarda. Benlik ile güç arasında denge arayışı — başkalarının güç dinamikleri ile kendi powerınız arasında gerilim.",
        ("Güneş","Plüton","Kare"): "Güneş ve Plüton'uz kare açıda. Kimlik ile güç arasındaki gerilim, kontrol ve güç mücadelelerini hayatınıza çekebilir. Bırakmayı öğrenmek, derin bir dönüşüm getirir.",
        ("Güneş","Plüton","Trigon"): "Güneş ve Plüton'uz trigon açıda. Benlik ile güç doğal uyum içinde — derin kararlılık, iç güç ve dönüştürücü enerji taşıyorsunuz.",
        ("Güneş","Plüton","Sekstil"): "Güneş ve Plüton'uz sekstil açıda. Kimlik ile güç arasında destekleyici bir bağ var. Kişisel dönüşümünüzü hızlandırabilirsiniz.",
        ("Ay","Merkür","Kavuşum"): "Ay ve Merkür'ünüz kavuşumda. Duygularınız ile zihinsel gücünüz aynı noktada — duygusal zekanız yüksek, sezgileriniz ve analiz yeteneğiniz güçlü bir şekilde iç içe.",
        ("Ay","Merkür","Karşıt"): "Ay ve Merkür'ünüz karşıt burçlarda. Duygular ile mantık arasında denge arayışı — hisleriniz ile düşünceleriniz zaman zaman çelişebilir.",
        ("Ay","Merkür","Kare"): "Ay ve Merkür'ünüz kare açıda. Duygu ile zihin arasındaki gerilim, karar verme süreçlerinizi zorlaştırabilir. Ancak bu dengeyi öğrenmek, duygusal zekanızı güçlendirir.",
        ("Ay","Merkür","Trigon"): "Ay ve Merkür'ünüz trigon açıda. Duygular ile düşünce doğal uyum içinde — sezgisel analiz yeteneğiniz güçlü, iletişim tarzınız akıcı ve empatik.",
        ("Ay","Merkür","Sekstil"): "Ay ve Merkür'ünüz sekstil açıda. Duygusal dünya ile zihin arasında destekleyici bir bağ var. Duygusal berraklığınızı artırabilirsiniz.",
        ("Ay","Venüs","Kavuşum"): "Ay ve Venüs'ünüz kavuşumda. Duygusal dünyanız ile sevgi diliniz aynı noktada — kendinizi ve başkalarını sevme kapasiteniz güçlü, içsel huzur ve estetik anlayışınız doğal.",
        ("Ay","Venüs","Karşıt"): "Ay ve Venüs'ünüz karşıt burçlarda. Duygusal ihtiyaçlar ile sevgi dili arasında denge arayışı — sevilme ihtiyacınız ile sevme biçiminiz zaman zaman çelişebilir.",
        ("Ay","Venüs","Kare"): "Ay ve Venüs'ünüz kare açıda. Duygu ile çekicilik arasındaki gerilim, ilişkilerinizde duygusal dalgalanmalara yol açabilir. Sevgi dilinizi güçlendirmek için bir fırsat.",
        ("Ay","Venüs","Trigon"): "Ay ve Venüs'ünüz trigon açıda. Duygular ile sevgi doğal uyum içinde — empatik, şefkatli ve estetik anlayışı güçlü bir yapınız var.",
        ("Ay","Venüs","Sekstil"): "Ay ve Venüs'ünüz sekstil açıda. Duygusal dünya ile sevgi arasında destekleyici bir bağ var. İlişkilerinizde derin bir uyum kurabilirsiniz.",
        ("Ay","Mars","Kavuşum"): "Ay ve Mars'ınız kavuşumda. Duygularınız ile savaşçı ruhunuz aynı noktada — duygusal tepkileriniz hızlı ve güçlü, koruma içgüdünüz yüksek.",
        ("Ay","Mars","Karşıt"): "Ay ve Mars'ınız karşıt burçlarda. Duygusal world ile eylem arasında denge arayışı — hisleriniz ile aksiyonunuz zaman zaman çelişebilir.",
        ("Ay","Mars","Kare"): "Ay ve Mars'ınız kare açıda. Duygu ile tutku arasındaki gerilim, öfke ve duygusal tepkilere yol açabilir. Bu enerjiyi yapıcı kanalize etmek, büyük bir güç kaynağı.",
        ("Ay","Mars","Trigon"): "Ay ve Mars'ınız trigon açıda. Duygular ile eylem doğal uyum içinde — cesur, enerjik ve duygusal olarak dengeli bir yapınız var.",
        ("Ay","Mars","Sekstil"): "Ay ve Mars'ınız sekstil açıda. Duygusal dünya ile tutku arasında destekleyici bir bağ var. Duygusal cesaretinizi güçlendirebilirsiniz.",
        ("Ay","Jüpiter","Kavuşum"): "Ay ve Jüpiteriniz kavuşumda. Duygularınız ile bolluk enerjiniz aynı noktada — duygusal genişleme, cömertlik ve iyimserlik içsel doğanız.",
        ("Ay","Jüpiter","Karşıt"): "Ay ve Jüpiteriniz karşıt burçlarda. Duygusal güvenlik ile genişleme arasında denge arayışı — duygusal ihtiyaçlarınız ile büyüme arzunuz çelişebilir.",
        ("Ay","Jüpiter","Kare"): "Ay ve Jüpiteriniz kare açıda. Duygu ile genişleme arasındaki gerilim, aşırıya kaçma eğilimini güçlendirebilir. Duygusal bolluk yaratmak için bir denge bulmalısınız.",
        ("Ay","Jüpiter","Trigon"): "Ay ve Jüpiteriniz trigon açıda. Duygular ile bolluk doğal uyum içinde — duygusal olarak geniş, cömert ve iyimser bir yapınız var.",
        ("Ay","Jüpiter","Sekstil"): "Ay ve Jüpiteriniz sekstil açıda. Duygusal dünya ile genişleme arasında destekleyici bir bağ var. Duygusal bolluğunuzu artırabilirsiniz.",
        ("Ay","Satürn","Kavuşum"): "Ay ve Satürn'ünüz kavuşumda. Duygularınız ile sınırlarınız aynı noktada — duygusal olarak disiplinli, ciddi ve yapısal bir yapınız var. Güvenlik ihtiyacınız güçlü.",
        ("Ay","Satürn","Karşıt"): "Ay ve Satürn'ünüz karşıt burçlarda. Duygusal world ile sınırlar arasında denge arayışı — duygusal ihtiyaçlarınız ile sorumluluklarınız çelişebilir.",
        ("Ay","Satürn","Kare"): "Ay ve Satürn'ünüz kare açıda. Duygu ile sınır arasındaki gerilim, duygusal kısıtlamalara ve korkulara yol açabilir. Bu dersi öğrenmek, duygusal olgunluğun anahtarı.",
        ("Ay","Satürn","Trigon"): "Ay ve Satürn'ünüz trigon açıda. Duygular ile yapı doğal uyum içinde — duygusal olarak olgun, disiplinli ve güvenilir bir yapınız var.",
        ("Ay","Satürn","Sekstil"): "Ay ve Satürn'ünüz sekstil açıda. Duygusal dünya ile sınırlar arasında destekleyici bir bağ var. Duygusal güvenliğinizi güçlendirebilirsiniz.",
        ("Merkür","Venüs","Kavuşum"): "Merkür ve Venüs'ünüz kavuşumda. Zihniniz ile çekiciliğiniz aynı noktada — iletişim tarzınız doğal olarak çekici, sosyal zekanız ve estetik anlayışınız güçlü.",
        ("Merkür","Venüs","Karşıt"): "Merkür ve Venüs'ünüz karşıt burçlarda. Mantık ile çekicilik arasında denge arayışı — düşünceleriniz ile sevgi diliniz zaman zaman çelişebilir.",
        ("Merkür","Venüs","Kare"): "Merkür ve Venüs'ünüz kare açıda. Zihin ile çekicilik arasındaki gerilim, iletişimde zorluklara yol açabilir. Sosyal becerilerinizi geliştirmek için bir fırsat.",
        ("Merkür","Venüs","Trigon"): "Merkür ve Venüs'ünüz trigon açıda. Zihin ile çekicilik doğal uyum içinde — iletişim tarzınız akıcı, sosyal zekanız güçlü.",
        ("Merkür","Venüs","Sekstil"): "Merkür ve Venüs'ünüz sekstil açıda. Düşünce ile çekicilik arasında destekleyici bir bağ var. İletişim becerilerinizi ve sosyal zekanızı artırabilirsiniz.",
        ("Mars","Jüpiter","Kavuşum"): "Mars ve Jüpiteriniz kavuşumda. Tutku ile bolluk aynı noktada — cesur, enerjik ve geniş düşünebilen bir yapınız var. Aksiyon alırken doğal bir şans ve bereket akışı.",
        ("Mars","Jüpiter","Karşıt"): "Mars ve Jüpiteriniz karşıt burçlarda. Eylem ile genişleme arasında denge arayışı — tutkunuz ile iyimserliğiniz zaman zaman çelişebilir.",
        ("Mars","Jüpiter","Kare"): "Mars ve Jüpiteriniz kare açıda. Tutku ile genişleme arasındaki gerilim, aşırıya kaçma eğilimini güçlendirebilir. Ancak bu enerjiyi dengelemek, büyük başarılara yol açar.",
        ("Mars","Jüpiter","Trigon"): "Mars ve Jüpiteriniz trigon açıda. Tutku ile bolluk doğal uyum içinde — cesur, enerjik ve bereketli bir yapınız var.",
        ("Mars","Jüpiter","Sekstil"): "Mars ve Jüpiteriniz sekstil açıda. Eylem ile genişleme arasında destekleyici bir bağ var. Cesur adımlar atarak büyük fırsatlar yakalayabilirsiniz.",
        ("Mars","Satürn","Kavuşum"): "Mars ve Satürn'ünüz kavuşumda. Tutku ile disiplin aynı noktada — güçlü bir irade, kararlılık ve yapısal mücadele enerjisi taşıyorsunuz.",
        ("Mars","Satürn","Karşıt"): "Mars ve Satürn'ünüz karşıt burçlarda. Eylem ile sınırlar arasında denge arayışı — tutkunuz ile kısıtlamalarınız zaman zaman çelişebilir.",
        ("Mars","Satürn","Kare"): "Mars ve Satürn'ünüz kare açıda. Tutku ile sınır arasındaki gerilim, güçlü bir iç mücadeleye yol açabilir. Bu dersi öğrenmek, irade gücünüzü dönüştürür.",
        ("Mars","Satürn","Trigon"): "Mars ve Satürn'ünüz trigon açıda. Eylem ile yapı doğal uyum içinde — disiplinli, kararlı ve güçlü bir yapınız var.",
        ("Mars","Satürn","Sekstil"): "Mars ve Satürn'ünüz sekstil açıda. Tutku ile sınırlar arasında destekleyici bir bağ var. Disiplinli adımlarla büyük projeler hayata geçirebilirsiniz.",
        ("Venüs","Mars","Kavuşum"): "Venüs ve Mars'ınız kavuşumda. Çekicilik ile tutku aynı noktada — romantik ve cinsel enerjiniz güçlü, fiziksel ve duygusal çekim potansiyeliniz yüksek.",
        ("Venüs","Mars","Karşıt"): "Venüs ve Mars'ınız karşıt burçlarda. Sevgi ile tutku arasında denge arayışı — çekim ile itiş dinamiği ilişkinizin temelini oluşturur.",
        ("Venüs","Mars","Kare"): "Venüs ve Mars'ınız kare açıda. Çekicilik ile tutku arasındaki gerilim, ilişkilerinizde tutkulu ama zorlayıcı bir dinamik yaratabilir.",
        ("Venüs","Mars","Trigon"): "Venüs ve Mars'ınız trigon açıda. Sevgi ile tutku doğal uyum içinde — romantik, tutkulu ve uyumlu bir ilişki enerjisi taşıyorsunuz.",
        ("Venüs","Mars","Sekstil"): "Venüs ve Mars'ınız sekstil açıda. Çekicilik ile tutku arasında destekleyici bir bağ var. Romantik ve tutkulu bir denge kurabilirsiniz.",
        ("Venüs","Satürn","Kavuşum"): "Venüs ve Satürn'ünüz kavuşumda. Sevgi ile sınırlar aynı noktada — ilişkilerinize ciddiyet ve yapı kazandırırsınız. Uzun vadeli taahhütler konusunda güçlü potansiyel.",
        ("Venüs","Satürn","Karşıt"): "Venüs ve Satürn'ünüz karşıt burçlarda. Sevgi ile sınırlar arasında denge arayışı — aşk life'ınızda ciddiyet ve kısıtlama dinamikleri.",
        ("Venüs","Satürn","Kare"): "Venüs ve Satürn'ünüz kare açıda. Çekicilik ile sınır arasındaki gerilim, ilişkilerinizde zorluklara yol açabilir. Ancak bu dersi olgunlaştırır.",
        ("Venüs","Satürn","Trigon"): "Venüs ve Satürn'ünüz trigon açıda. Sevgi ile yapı doğal uyum içinde — olgun, kararlı ve yapısal ilişkiler kurarsınız.",
        ("Venüs","Satürn","Sekstil"): "Venüs ve Satürn'ünüz sekstil açıda. Aşk ile sınırlar arasında destekleyici bir bağ var. Uzun vadeli ve değerli ilişkiler kurabilirsiniz.",
        ("Jüpiter","Satürn","Kavuşum"): "Jüpiter ve Satürn'ünüz kavuşumda. Bolluk ile sınırlar aynı noktada — genişleme ve yapı arasında güçlü bir denge kurarsınız. Uzun vadeli projelerde doğal strateji yeteneği.",
        ("Jüpiter","Satürn","Karşıt"): "Jüpiter ve Satürn'ünüz karşıt burçlarda. Genişleme ile yapı arasında denge arayışı — iyimserlik ile realite arasındaki gerilim hayatınızın temel derslerinden biri.",
        ("Jüpiter","Satürn","Kare"): "Jüpiter ve Satürn'ünüz kare açıda. Bolluk ile sınır arasındaki gerilim, fırsatları ve kısıtlamaları aynı anda deneyimlemenize yol açar.",
        ("Jüpiter","Satürn","Trigon"): "Jüpiter ve Satürn'ünüz trigon açıda. Genişleme ile yapı doğal uyum içinde — stratejik, kararlı ve geniş düşünebilen bir yapınız var.",
        ("Jüpiter","Satürn","Sekstil"): "Jüpiter ve Satürn'ünüz sekstil açıda. Bolluk ile sınırlar arasında destekleyici bir bağ var. Büyük projeleri yapısal bir şekilde hayata geçirebilirsiniz.",
        ("Jüpiter","Neptün","Kavuşum"): "Jüpiter ve Neptün'ünüz kavuşumda. İnanç ile hayal aynı noktada — manevi genişleme, ilham ve sezgisel berraklık içsel doğanız.",
        ("Jüpiter","Neptün","Karşıt"): "Jüpiter ve Neptün'ünüz karşıt burçlarda. Gerçekçi genişleme ile idealist hayal arasında denge arayışı — iyimserlik ile pusluluk zaman zaman çelişebilir.",
        ("Jüpiter","Neptün","Kare"): "Jüpiter ve Neptün'ünüz kare açıda. İnanç ile hayal arasındaki gerilim, kafa karışıklığı ve hayal kırıklıkları yaratabilir. Ancak bu enerjiyi manevi geliştirmek güçlü sonuçlar verir.",
        ("Jüpiter","Neptün","Trigon"): "Jüpiter ve Neptün'ünüz trigon açıda. İnanç ile hayal doğal uyum içinde — manevi dünyanız geniş, ilhamınız bereketli ve sezgileriniz güçlü.",
        ("Jüpiter","Neptün","Sekstil"): "Jüpiter ve Neptün'ünüz sekstil açıda. İnanç ile hayal arasında destekleyici bir bağ var. Manevi projelerinizi ve hayallerinizi hayata geçirebilirsiniz.",
        ("Jüpiter","Plüton","Kavuşum"): "Jüpiter ve Plüton'uz kavuşumda. Bolluk ile güç aynı noktada — derin genişleme, dönüşüm ve güç potansiyeliniz güçlü. Hayatınızda büyük dönüşüm döngüleri var.",
        ("Jüpiter","Plüton","Karşıt"): "Jüpiter ve Plüton'uz karşıt burçlarda. Genişleme ile güç arasında denge arayışı — bolluk ile güç arasındaki gerilim, büyük dengesizliklere yol açabilir.",
        ("Jüpiter","Plüton","Kare"): "Jüpiter ve Plüton'uz kare açıda. Bolluk ile güç arasındaki gerilim, kontrol ve güç mücadelelerini hayatınıza çekebilir. Ancak bu enerjiyi dengelemek, büyük dönüşümler yaratır.",
        ("Jüpiter","Plüton","Trigon"): "Jüpiter ve Plüton'uz trigon açıda. Bolluk ile güç doğal uyum içinde — derin genişleme, kararlılık ve dönüştürücü enerji taşıyorsunuz.",
        ("Jüpiter","Plüton","Sekstil"): "Jüpiter ve Plüton'uz sekstil açıda. Bolluk ile güç arasında destekleyici bir bağ var. Derin dönüşümleri yapıcı bir şekilde hayata geçirebilirsiniz.",
        ("Satürn","Plüton","Kavuşum"): "Satürn ve Plüton'uz kavuşumda. Sınır ile güç aynı noktada — yapısal dönüşüm, derin sorumluluk ve güçlü bir kararlılık enerjisi taşıyorsunuz.",
        ("Satürn","Plüton","Karşıt"): "Satürn ve Plüton'uz karşıt burçlarda. Yapı ile güç arasında denge arayışı — sınırlar ile güç arasındaki gerilim, büyük yapısal dönüşümlere yol açabilir.",
        ("Satürn","Plüton","Kare"): "Satürn ve Plüton'uz kare açıda. Sınır ile güç arasındaki gerilim, yapısal krizlere ve derin dönüşümlere yol açabilir. Bu dersi öğrenmek, güçlü bir olgunluk getirir.",
        ("Satürn","Plüton","Trigon"): "Satürn ve Plüton'uz trigon açıda. Yapı ile güç doğal uyum içinde — disiplinli, kararlı ve dönüştürücü bir yapınız var.",
        ("Satürn","Plüton","Sekstil"): "Satürn ve Plüton'uz sekstil açıda. Sınır ile güç arasında destekleyici bir bağ var. Yapısal dönüşümleri stratejik bir şekilde hayata geçirebilirsiniz.",
        ("Uranüs","Plüton","Kavuşum"): "Uranüs ve Plüton'uz kavuşumda. Özgürlük ile güç aynı noktada — derin devrim, ani değişim ve güçlü bir dönüşüm enerjisi taşıyorsunuz. Hayatınızda köklü yenilikler var.",
        ("Uranüs","Plüton","Karşıt"): "Uranüs ve Plüton'uz karşıt burçlarda. Özgürlük ile güç arasında denge arayışı — asi ruh ile güç arasındaki gerilim, büyük çatışmalara yol açabilir.",
        ("Uranüs","Plüton","Kare"): "Uranüs ve Plüton'uz kare açıda. Özgürlük ile güç arasındaki gerilim, ani kopuşlara ve derin dönüşümlere yol açabilir. Bu enerjiyi yapıcı kullanmak, hayatınızı dönüştürür.",
        ("Uranüs","Plüton","Trigon"): "Uranüs ve Plüton'uz trigon açıda. Özgürlük ile güç doğal uyum içinde — yenilikçi, kararlı ve dönüştürücü bir yapınız var.",
        ("Uranüs","Plüton","Sekstil"): "Uranüs ve Plüton'uz sekstil açıda. Özgürlük ile güç arasında destekleyici bir bağ var. Derin devrimleri yapıcı bir şekilde hayata geçirebilirsiniz.",
        ("Neptün","Plüton","Kavuşum"): "Neptün ve Plüton'uz kavuşumda. Hayal ile güç aynı noktada — manevi dönüşüm, derin sezgi ve güçlü bir ruhsal enerji taşıyorsunuz.",
        ("Neptün","Plüton","Karşıt"): "Neptün ve Plüton'uz karşıt burçlarda. Hayal ile güç arasında denge arayışı — manevi dünyam ile güç arasındaki gerilim, büyük ruhsal dönüşümlere yol açabilir.",
        ("Neptün","Plüton","Kare"): "Neptün ve Plüton'uz kare açıda. Hayal ile güç arasındaki gerilim, manevi krizlere ve derin dönüşümlere yol açabilir. Bu enerjiyi manevi geliştirmek, güçlü sonuçlar verir.",
        ("Neptün","Plüton","Trigon"): "Neptün ve Plüton'uz trigon açıda. Hayal ile güç doğal uyum içinde — manevi dünyanız derin, sezgileriniz güçlü ve dönüştürücü enerji taşıyorsunuz.",
        ("Neptün","Plüton","Sekstil"): "Neptün ve Plüton'uz sekstil açıda. Hayal ile güç arasında destekleyici bir bağ var. Manevi dönüşümlerinizi yapıcı bir şekilde hayata geçirebilirsiniz.",
    }

    OZEL_YORUMLAR_EN = {
        ("Güneş","Ay","Kavuşum"): "Your Sun and Moon are united in the same sign. Your core self and emotional world are in perfect harmony — you have a natural clarity about what you want and what you need. This conjunction provides a strong inner coherence throughout your life.",
        ("Güneş","Ay","Karşıt"): "Your Sun and Moon are in opposing signs. Your core self and emotional needs are constantly seeking balance — you move between what you want and what you need. This opposition requires you to fully understand both sides.",
        ("Güneş","Ay","Kare"): "Your Sun and Moon are in a square. The tension between your identity and your emotional world can lead to inner conflict. Yet this struggle offers a powerful opportunity to know yourself more deeply.",
        ("Güneş","Ay","Trigon"): "Your Sun and Moon are in a trine. Your core self and your feelings are in natural harmony — you have an inner clarity about what you want. You can channel this energy into your creative projects.",
        ("Güneş","Ay","Sekstil"): "Your Sun and Moon are in a sextile. There is a supportive bond between the core self and the emotional world. By making use of this opportunity, you can combine your emotional intelligence and personal power.",
        ("Güneş","Merkür","Kavuşum"): "Your Sun and Mercury are conjunct. Your identity and mental power meet at the same point — your way of thinking and communicating reflects your self. Your mind works quickly, and you express your ideas boldly.",
        ("Güneş","Merkür","Karşıt"): "Your Sun and Mercury are in opposing signs. There is a search for balance between your core self and your way of thinking — what you say you want may contradict what you actually think.",
        ("Güneş","Merkür","Kare"): "Your Sun and Mercury are in a square. There is tension between your identity and mental analysis — while speaking boldly, you may not fully express your thoughts. This is an opportunity to develop your communication skills.",
        ("Güneş","Merkür","Trigon"): "Your Sun and Mercury are in a trine. Thought and identity are in natural harmony — your mind is clear, your communication is fluid, and you easily bring your ideas into being.",
        ("Güneş","Merkür","Sekstil"): "Your Sun and Mercury are in a sextile. There is a supportive bond between your mental abilities and your identity. You can express your creative ideas with strength.",
        ("Güneş","Venüs","Kavuşum"): "Your Sun and Venus are conjunct. Your core self and your love language meet at the same point — your capacity to love and value yourself is strong. Your charm and personal magnetism shine naturally.",
        ("Güneş","Venüs","Karşıt"): "Your Sun and Venus are in opposing signs. There is a search for balance between self and love — while expressing yourself, you also need to consider the needs of your loved ones.",
        ("Güneş","Venüs","Kare"): "Your Sun and Venus are in a square. Tension between your identity and your love language can create challenges in your relationships. Yet this struggle is an opportunity to understand love more deeply.",
        ("Güneş","Venüs","Trigon"): "Your Sun and Venus are in a trine. Your core self and your charm energy are in natural harmony — you have an inner clarity when it comes to love and values.",
        ("Güneş","Venüs","Sekstil"): "Your Sun and Venus are in a sextile. There is a supportive bond between identity and love. You can build a strong balance in your relationships and creativity.",
        ("Güneş","Mars","Kavuşum"): "Your Sun and Mars are conjunct. Your identity and warrior spirit meet at the same point — your courage, passion and drive are powerful. You have the nature of a natural leader and fighter.",
        ("Güneş","Mars","Karşıt"): "Your Sun and Mars are in opposing signs. There is a search for balance between the self and action — you are passionate about what you want but can sometimes be impatient.",
        ("Güneş","Mars","Kare"): "Your Sun and Mars are in a square. Tension between identity and passion can create anger and impatience. Yet channeling this powerful energy into creative projects can lead to great achievements.",
        ("Güneş","Mars","Trigon"): "Your Sun and Mars are in a trine. Self and action are in natural harmony — you have a courageous, energetic and passionate nature. You can use this energy to reach your goals.",
        ("Güneş","Mars","Sekstil"): "Your Sun and Mars are in a sextile. There is a supportive bond between identity and passion. You can make bold moves to bring your dreams to life.",
        ("Güneş","Jüpiter","Kavuşum"): "Your Sun and Jupiter are conjunct. Your core self and abundance energy meet at the same point — your optimism, generosity and capacity for expansion are strong. There is a natural flow of luck and blessing in your life.",
        ("Güneş","Jüpiter","Karşıt"): "Your Sun and Jupiter are in opposing signs. There is a search for balance between self and abundance — you may swing between excessive optimism and realism.",
        ("Güneş","Jüpiter","Kare"): "Your Sun and Jupiter are in a square. Tension between identity and expansion can strengthen the tendency to go to extremes. Yet balancing this energy creates great opportunities.",
        ("Güneş","Jüpiter","Trigon"): "Your Sun and Jupiter are in a trine. Self and abundance are in natural harmony — you are an optimistic, generous and broad-minded person.",
        ("Güneş","Jüpiter","Sekstil"): "Your Sun and Jupiter are in a sextile. There is a supportive bond between identity and expansion. You can contribute to your personal growth and to others.",
        ("Güneş","Satürn","Kavuşum"): "Your Sun and Saturn are conjunct. Your core self and responsibilities meet at the same point — you have a disciplined, serious and structured nature. A strong energy of maturity presides over your life.",
        ("Güneş","Satürn","Karşıt"): "Your Sun and Saturn are in opposing signs. There is a search for balance between self and limits — the tension between freedom and responsibility is one of your fundamental life lessons.",
        ("Güneş","Satürn","Kare"): "Your Sun and Saturn are in a square. Tension between identity and limits can make you overly harsh with yourself. Learning this lesson is the key to true maturity.",
        ("Güneş","Satürn","Trigon"): "Your Sun and Saturn are in a trine. Self and structure are in natural harmony — you are a disciplined, determined and responsible person.",
        ("Güneş","Satürn","Sekstil"): "Your Sun and Saturn are in a sextile. There is a supportive bond between identity and limits. With disciplined steps you can bring large projects to life.",
        ("Güneş","Uranüs","Kavuşum"): "Your Sun and Uranus are conjunct. Your identity and revolutionary spirit meet at the same point — your freedom, independence and creative genius are powerful. Sudden changes are prominent in your life.",
        ("Güneş","Uranüs","Karşıt"): "Your Sun and Uranus are in opposing signs. There is a search for balance between freedom and tradition — a constant tension between your rebellious spirit and social expectations.",
        ("Güneş","Uranüs","Kare"): "Your Sun and Uranus are in a square. Tension between identity and revolution can lead to sudden breaks. Used constructively, this energy can transform your life.",
        ("Güneş","Uranüs","Trigon"): "Your Sun and Uranus are in a trine. Self and freedom are in natural harmony — you are an innovative, creative and independent person.",
        ("Güneş","Uranüs","Sekstil"): "Your Sun and Uranus are in a sextile. There is a supportive bond between identity and revolution. You can initiate innovative changes.",
        ("Güneş","Neptün","Kavuşum"): "Your Sun and Neptune are conjunct. Your self and your dreams meet at the same point — you are an intuitive, creative and spiritual person. Your artistic abilities are strong.",
        ("Güneş","Neptün","Karşıt"): "Your Sun and Neptune are in opposing signs. There is a search for balance between realism and dream — you may drift between the real world and the world of imagination.",
        ("Güneş","Neptün","Kare"): "Your Sun and Neptune are in a square. Tension between identity and haze can create confusion. Yet channeling this energy into artistic creativity produces powerful results.",
        ("Güneş","Neptün","Trigon"): "Your Sun and Neptune are in a trine. Self and intuition are in natural harmony — your spiritual world is rich and your creative inspiration is abundant.",
        ("Güneş","Neptün","Sekstil"): "Your Sun and Neptune are in a sextile. There is a supportive bond between identity and dream. You can bring your artistic and spiritual projects to life.",
        ("Güneş","Plüton","Kavuşum"): "Your Sun and Pluto are conjunct. Your identity and power energy meet at the same point — you carry deep transformation, determination and inner strength. Powerful cycles of rebirth shape your life.",
        ("Güneş","Plüton","Karşıt"): "Your Sun and Pluto are in opposing signs. There is a search for balance between self and power — a tension between others' power dynamics and your own authority.",
        ("Güneş","Plüton","Kare"): "Your Sun and Pluto are in a square. Tension between identity and power can draw control struggles and power games into your life. Learning to let go brings deep transformation.",
        ("Güneş","Plüton","Trigon"): "Your Sun and Pluto are in a trine. Self and power are in natural harmony — you carry deep determination, inner strength and transformative energy.",
        ("Güneş","Plüton","Sekstil"): "Your Sun and Pluto are in a sextile. There is a supportive bond between identity and power. You can accelerate your personal transformation.",
        ("Ay","Merkür","Kavuşum"): "Your Moon and Mercury are conjunct. Your feelings and mental power meet at the same point — your emotional intelligence is high, and your intuition and analytical ability are powerfully interwoven.",
        ("Ay","Merkür","Karşıt"): "Your Moon and Mercury are in opposing signs. There is a search for balance between feelings and logic — your emotions and your thoughts may occasionally contradict each other.",
        ("Ay","Merkür","Kare"): "Your Moon and Mercury are in a square. Tension between emotion and mind can complicate your decision-making. Yet learning this balance strengthens your emotional intelligence.",
        ("Ay","Merkür","Trigon"): "Your Moon and Mercury are in a trine. Feelings and thought are in natural harmony — your intuitive analysis is strong, and your communication is fluid and empathetic.",
        ("Ay","Merkür","Sekstil"): "Your Moon and Mercury are in a sextile. There is a supportive bond between the emotional world and the mind. You can increase your emotional clarity.",
        ("Ay","Venüs","Kavuşum"): "Your Moon and Venus are conjunct. Your emotional world and love language meet at the same point — your capacity to love yourself and others is strong, and your inner peace and aesthetic sense come naturally.",
        ("Ay","Venüs","Karşıt"): "Your Moon and Venus are in opposing signs. There is a search for balance between emotional needs and love language — your need to be loved and the way you love may occasionally conflict.",
        ("Ay","Venüs","Kare"): "Your Moon and Venus are in a square. Tension between feeling and charm can cause emotional fluctuations in your relationships. An opportunity to strengthen your love language.",
        ("Ay","Venüs","Trigon"): "Your Moon and Venus are in a trine. Feelings and love are in natural harmony — you are an empathetic, compassionate person with a strong aesthetic sense.",
        ("Ay","Venüs","Sekstil"): "Your Moon and Venus are in a sextile. There is a supportive bond between the emotional world and love. You can build deep harmony in your relationships.",
        ("Ay","Mars","Kavuşum"): "Your Moon and Mars are conjunct. Your feelings and warrior spirit meet at the same point — your emotional reactions are quick and strong, and your protective instinct is high.",
        ("Ay","Mars","Karşıt"): "Your Moon and Mars are in opposing signs. There is a search for balance between the emotional world and action — your feelings and your actions may occasionally conflict.",
        ("Ay","Mars","Kare"): "Your Moon and Mars are in a square. Tension between feeling and passion can lead to anger and emotional reactions. Channeling this energy constructively is a great source of power.",
        ("Ay","Mars","Trigon"): "Your Moon and Mars are in a trine. Feelings and action are in natural harmony — you are a courageous, energetic and emotionally balanced person.",
        ("Ay","Mars","Sekstil"): "Your Moon and Mars are in a sextile. There is a supportive bond between the emotional world and passion. You can strengthen your emotional courage.",
        ("Ay","Jüpiter","Kavuşum"): "Your Moon and Jupiter are conjunct. Your feelings and abundance energy meet at the same point — emotional expansion, generosity and optimism are your inner nature.",
        ("Ay","Jüpiter","Karşıt"): "Your Moon and Jupiter are in opposing signs. There is a search for balance between emotional security and expansion — your emotional needs and your desire to grow may conflict.",
        ("Ay","Jüpiter","Kare"): "Your Moon and Jupiter are in a square. Tension between feeling and expansion can strengthen the tendency to go to extremes. You must find a balance to create emotional abundance.",
        ("Ay","Jüpiter","Trigon"): "Your Moon and Jupiter are in a trine. Feelings and abundance are in natural harmony — you are emotionally expansive, generous and optimistic.",
        ("Ay","Jüpiter","Sekstil"): "Your Moon and Jupiter are in a sextile. There is a supportive bond between the emotional world and expansion. You can increase your emotional abundance.",
        ("Ay","Satürn","Kavuşum"): "Your Moon and Saturn are conjunct. Your feelings and limits meet at the same point — you are emotionally disciplined, serious and structured. Your need for security is strong.",
        ("Ay","Satürn","Karşıt"): "Your Moon and Saturn are in opposing signs. There is a search for balance between the emotional world and limits — your emotional needs and your responsibilities may conflict.",
        ("Ay","Satürn","Kare"): "Your Moon and Saturn are in a square. Tension between feeling and limit can lead to emotional restriction and fear. Learning this lesson is the key to emotional maturity.",
        ("Ay","Satürn","Trigon"): "Your Moon and Saturn are in a trine. Feelings and structure are in natural harmony — you are emotionally mature, disciplined and reliable.",
        ("Ay","Satürn","Sekstil"): "Your Moon and Saturn are in a sextile. There is a supportive bond between the emotional world and limits. You can strengthen your emotional security.",
        ("Merkür","Venüs","Kavuşum"): "Your Mercury and Venus are conjunct. Your mind and your charm meet at the same point — your communication style is naturally attractive, and your social intelligence and aesthetic sense are strong.",
        ("Merkür","Venüs","Karşıt"): "Your Mercury and Venus are in opposing signs. There is a search for balance between logic and charm — your thoughts and your love language may occasionally conflict.",
        ("Merkür","Venüs","Kare"): "Your Mercury and Venus are in a square. Tension between mind and charm can create difficulties in communication. An opportunity to develop your social skills.",
        ("Merkür","Venüs","Trigon"): "Your Mercury and Venus are in a trine. Mind and charm are in natural harmony — your communication is fluid and your social intelligence is strong.",
        ("Merkür","Venüs","Sekstil"): "Your Mercury and Venus are in a sextile. There is a supportive bond between thought and charm. You can enhance your communication skills and social intelligence.",
        ("Mars","Jüpiter","Kavuşum"): "Your Mars and Jupiter are conjunct. Passion and abundance meet at the same point — you are a courageous, energetic and broad-minded person. There is a natural flow of luck and blessing when you take action.",
        ("Mars","Jüpiter","Karşıt"): "Your Mars and Jupiter are in opposing signs. There is a search for balance between action and expansion — your passion and your optimism may occasionally conflict.",
        ("Mars","Jüpiter","Kare"): "Your Mars and Jupiter are in a square. Tension between passion and expansion can strengthen the tendency to go to extremes. Yet balancing this energy leads to great achievements.",
        ("Mars","Jüpiter","Trigon"): "Your Mars and Jupiter are in a trine. Passion and abundance are in natural harmony — you are courageous, energetic and resourceful.",
        ("Mars","Jüpiter","Sekstil"): "Your Mars and Jupiter are in a sextile. There is a supportive bond between action and expansion. You can seize great opportunities with bold steps.",
        ("Mars","Satürn","Kavuşum"): "Your Mars and Saturn are conjunct. Passion and discipline meet at the same point — you carry strong will, determination and structured fighting energy.",
        ("Mars","Satürn","Karşıt"): "Your Mars and Saturn are in opposing signs. There is a search for balance between action and limits — your passion and your constraints may occasionally conflict.",
        ("Mars","Satürn","Kare"): "Your Mars and Saturn are in a square. Tension between passion and limit can lead to a powerful inner struggle. Learning this lesson transforms your willpower.",
        ("Mars","Satürn","Trigon"): "Your Mars and Saturn are in a trine. Action and structure are in natural harmony — you are disciplined, determined and strong.",
        ("Mars","Satürn","Sekstil"): "Your Mars and Saturn are in a sextile. There is a supportive bond between passion and limits. With disciplined steps you can bring large projects to life.",
        ("Venüs","Mars","Kavuşum"): "Your Venus and Mars are conjunct. Charm and passion meet at the same point — your romantic and sexual energy is strong, and your physical and emotional attraction potential is high.",
        ("Venüs","Mars","Karşıt"): "Your Venus and Mars are in opposing signs. There is a search for balance between love and passion — the dynamics of attraction and repulsion form the foundation of your relationships.",
        ("Venüs","Mars","Kare"): "Your Venus and Mars are in a square. Tension between charm and passion can create a passionate but demanding dynamic in your relationships.",
        ("Venüs","Mars","Trigon"): "Your Venus and Mars are in a trine. Love and passion are in natural harmony — you carry a romantic, passionate and harmonious relationship energy.",
        ("Venüs","Mars","Sekstil"): "Your Venus and Mars are in a sextile. There is a supportive bond between charm and passion. You can build a romantic and passionate balance.",
        ("Venüs","Satürn","Kavuşum"): "Your Venus and Saturn are conjunct. Love and limits meet at the same point — you bring seriousness and structure to your relationships. You have strong potential for long-term commitment.",
        ("Venüs","Satürn","Karşıt"): "Your Venus and Saturn are in opposing signs. There is a search for balance between love and limits — dynamics of seriousness and restriction run through your love life.",
        ("Venüs","Satürn","Kare"): "Your Venus and Saturn are in a square. Tension between charm and limit can create challenges in your relationships. Yet this lesson will mature you.",
        ("Venüs","Satürn","Trigon"): "Your Venus and Saturn are in a trine. Love and structure are in natural harmony — you build mature, determined and structured relationships.",
        ("Venüs","Satürn","Sekstil"): "Your Venus and Saturn are in a sextile. There is a supportive bond between love and limits. You can build long-term and valuable relationships.",
        ("Jüpiter","Satürn","Kavuşum"): "Your Jupiter and Saturn are conjunct. Abundance and limits meet at the same point — you build a strong balance between expansion and structure. A natural strategic ability in long-term projects.",
        ("Jüpiter","Satürn","Karşıt"): "Your Jupiter and Saturn are in opposing signs. There is a search for balance between expansion and structure — the tension between optimism and reality is one of your fundamental life lessons.",
        ("Jüpiter","Satürn","Kare"): "Your Jupiter and Saturn are in a square. Tension between abundance and limit causes you to experience opportunities and constraints at the same time.",
        ("Jüpiter","Satürn","Trigon"): "Your Jupiter and Saturn are in a trine. Expansion and structure are in natural harmony — you are strategic, determined and broad-minded.",
        ("Jüpiter","Satürn","Sekstil"): "Your Jupiter and Saturn are in a sextile. There is a supportive bond between abundance and limits. You can bring large projects into being in a structured way.",
        ("Jüpiter","Neptün","Kavuşum"): "Your Jupiter and Neptune are conjunct. Faith and dream meet at the same point — spiritual expansion, inspiration and intuitive clarity are your inner nature.",
        ("Jüpiter","Neptün","Karşıt"): "Your Jupiter and Neptune are in opposing signs. There is a search for balance between realistic expansion and idealist dream — optimism and haze may occasionally conflict.",
        ("Jüpiter","Neptün","Kare"): "Your Jupiter and Neptune are in a square. Tension between faith and dream can create confusion and disillusionment. Yet pursuing spiritual development brings powerful results.",
        ("Jüpiter","Neptün","Trigon"): "Your Jupiter and Neptune are in a trine. Faith and dream are in natural harmony — your spiritual world is expansive, your inspiration abundant and your intuition strong.",
        ("Jüpiter","Neptün","Sekstil"): "Your Jupiter and Neptune are in a sextile. There is a supportive bond between faith and dream. You can bring your spiritual projects and dreams to life.",
        ("Jüpiter","Plüton","Kavuşum"): "Your Jupiter and Pluto are conjunct. Abundance and power meet at the same point — your potential for deep expansion, transformation and power is strong. Great transformation cycles shape your life.",
        ("Jüpiter","Plüton","Karşıt"): "Your Jupiter and Pluto are in opposing signs. There is a search for balance between expansion and power — the tension between abundance and power can lead to great imbalances.",
        ("Jüpiter","Plüton","Kare"): "Your Jupiter and Pluto are in a square. Tension between abundance and power can draw control struggles and power games into your life. Yet balancing this energy creates great transformations.",
        ("Jüpiter","Plüton","Trigon"): "Your Jupiter and Pluto are in a trine. Abundance and power are in natural harmony — you carry deep expansion, determination and transformative energy.",
        ("Jüpiter","Plüton","Sekstil"): "Your Jupiter and Pluto are in a sextile. There is a supportive bond between abundance and power. You can bring deep transformations to life constructively.",
        ("Satürn","Plüton","Kavuşum"): "Your Saturn and Pluto are conjunct. Limit and power meet at the same point — you carry structural transformation, deep responsibility and powerful determination.",
        ("Satürn","Plüton","Karşıt"): "Your Saturn and Pluto are in opposing signs. There is a search for balance between structure and power — the tension between limits and power can lead to great structural transformations.",
        ("Satürn","Plüton","Kare"): "Your Saturn and Pluto are in a square. Tension between limit and power can lead to structural crises and deep transformations. Learning this lesson brings strong maturity.",
        ("Satürn","Plüton","Trigon"): "Your Saturn and Pluto are in a trine. Structure and power are in natural harmony — you are disciplined, determined and transformative.",
        ("Satürn","Plüton","Sekstil"): "Your Saturn and Pluto are in a sextile. There is a supportive bond between limit and power. You can bring structural transformations to life strategically.",
        ("Uranüs","Plüton","Kavuşum"): "Your Uranus and Pluto are conjunct. Freedom and power meet at the same point — you carry deep revolution, sudden change and powerful transformative energy. Radical innovations shape your life.",
        ("Uranüs","Plüton","Karşıt"): "Your Uranus and Pluto are in opposing signs. There is a search for balance between freedom and power — the tension between the rebellious spirit and power can lead to great conflicts.",
        ("Uranüs","Plüton","Kare"): "Your Uranus and Pluto are in a square. Tension between freedom and power can lead to sudden breaks and deep transformations. Used constructively, this energy can transform your life.",
        ("Uranüs","Plüton","Trigon"): "Your Uranus and Pluto are in a trine. Freedom and power are in natural harmony — you are innovative, determined and transformative.",
        ("Uranüs","Plüton","Sekstil"): "Your Uranus and Pluto are in a sextile. There is a supportive bond between freedom and power. You can bring deep revolutions to life constructively.",
        ("Neptün","Plüton","Kavuşum"): "Your Neptune and Pluto are conjunct. Dream and power meet at the same point — you carry spiritual transformation, deep intuition and powerful psychic energy.",
        ("Neptün","Plüton","Karşıt"): "Your Neptune and Pluto are in opposing signs. There is a search for balance between dream and power — the tension between the spiritual world and power can lead to deep spiritual transformations.",
        ("Neptün","Plüton","Kare"): "Your Neptune and Pluto are in a square. Tension between dream and power can lead to spiritual crises and deep transformations. Pursuing spiritual development brings powerful results.",
        ("Neptün","Plüton","Trigon"): "Your Neptune and Pluto are in a trine. Dream and power are in natural harmony — your spiritual world is deep, your intuition strong, and you carry transformative energy.",
        ("Neptün","Plüton","Sekstil"): "Your Neptune and Pluto are in a sextile. There is a supportive bond between dream and power. You can bring your spiritual transformations to life constructively.",
    }

    tum = list(GEZEGENLER.keys()) + list(ASTEROITLER.keys()) + list(ARAP_NOKTALARI.keys())

    def _urun(p1, p2, aci, en=False):
        key = (p1, p2, aci)
        key_t = (p2, p1, aci)
        if en:
            if key in OZEL_YORUMLAR_EN: return OZEL_YORUMLAR_EN[key]
            if key_t in OZEL_YORUMLAR_EN: return OZEL_YORUMLAR_EN[key_t]
            pair = (p1, p2) if (p1, p2) in CIFT_TEMA_EN else ((p2, p1) if (p2, p1) in CIFT_TEMA_EN else None)
            tema = CIFT_TEMA_EN.get(pair, f"the connection between the energies of {p1} and {p2}") if pair else f"the connection between the energies of {p1} and {p2}"
            p1o = _EN_OZ.get(p1) or f"{p1} energy"; p2o = _EN_OZ.get(p2) or f"{p2} energy"
            if aci == "Kavuşum":
                return f"{p1} and {p2} energies merge at the same point. {tema}. The {p1o} of {p1} and the {p2o} of {p2} form a unified whole. This conjunction allows you to experience both energies with great intensity."
            elif aci == "Karşıt":
                return f"{p1} and {p2} stand at opposite poles. {tema}. There is constant search for balance between the {p1o} of {p1} and the {p2o} of {p2}. This opposition requires you to fully understand both sides."
            elif aci == "Kare":
                return f"The square between {p1} and {p2} creates tension around {tema}. This demanding energy pushes you beyond your comfort zone and forces growth. The struggle between the {p1o} of {p1} and the {p2o} of {p2} is one of your most powerful transformation opportunities."
            elif aci == "Trigon":
                return f"The trine between {p1} and {p2} creates a natural harmony around {tema}. Used consciously, this energy can create flow in your life. The {p1o} of {p1} and the {p2o} of {p2} naturally build a bridge."
            elif aci == "Sekstil":
                return f"The sextile between {p1} and {p2} offers opportunities around {tema}. To activate this energy, you need to take a conscious step. There is a supportive bond between the {p1o} of {p1} and the {p2o} of {p2}."
            return ""
        if key in OZEL_YORUMLAR: return OZEL_YORUMLAR[key]
        if key_t in OZEL_YORUMLAR: return OZEL_YORUMLAR[key_t]
        pair = (p1, p2) if (p1, p2) in CIFT_TEMA else ((p2, p1) if (p2, p1) in CIFT_TEMA else None)
        tema = CIFT_TEMA.get(pair, f"{p1} ve {p2} enerjileri arasında bir ilişki") if pair else f"{p1} ve {p2} enerjileri arasında bir ilişki"
        p1p = GEZEGENLER.get(p1) or ASTEROITLER.get(p1) or ARAP_NOKTALARI.get(p1, {})
        p2p = GEZEGENLER.get(p2) or ASTEROITLER.get(p2) or ARAP_NOKTALARI.get(p2, {})
        p1o = p1p.get("oz", f"{p1} enerjisi"); p2o = p2p.get("oz", f"{p2} enerjisi")
        if aci == "Kavuşum":
            return f"{p1} ve {p2} enerjileri aynı noktada birleşmiş durumda. {tema}. {p1}in {p1o} yönü ile {p2}nin {p2o} yönü bir bütün oluşturuyor. Bu kavuşum, her iki enerjiyi de güçlü bir şekilde deneyimlemenizi sağlıyor."
        elif aci == "Karşıt":
            return f"{p1} ve {p2} zıt kutuplarda duruyor. {tema}. {p1}in {p1o} yönü ile {p2}nin {p2o} yönü arasında sürekli bir denge arayışı var. Bu karşıtlık, her iki tarafı da tam olarak anlamanızı gerektiriyor."
        elif aci == "Kare":
            return f"{p1} ile {p2} arasındaki kare açısı, {tema} konusunda bir gerilim yaratıyor. Bu zorlayıcı enerji, sizi konfor alanınızın dışına itiyor ve büyümeye zorluyor. {p1}in {p1o} yönü ile {p2}nin {p2o} yönü arasındaki mücadele, en güçlü dönüşüm fırsatlarınızdan biri."
        elif aci == "Trigon":
            return f"{p1} ile {p2} arasındaki trigon açısı, {tema} konusunda doğal bir uyum sağlıyor. Bu enerjiyi bilinçli kullanarak hayatınızda akış yaratabilirsiniz. {p1}in {p1o} yönü ile {p2}nin {p2o} yönü doğal bir köprü kuruyor."
        elif aci == "Sekstil":
            return f"{p1} ile {p2} arasındaki sekstil açısı, {tema} konusunda fırsatlar sunuyor. Bu enerjiyi harekete geçirmek için bilinçli bir adım atmanız gerekiyor. {p1}in {p1o} yönü ile {p2}nin {p2o} yönü arasında destekleyici bir bağ var."
        return ""

    _sozluk_tr = {}
    _sozluk_en = None
    islenen = set()
    for p1 in tum:
        for p2 in tum:
            if p1 == p2: continue
            pk = tuple(sorted([p1, p2]))
            if pk in islenen: continue
            islenen.add(pk)
            _sozluk_tr[f"{pk[0]}-{pk[1]}"] = {}
            if _EN:
                if _sozluk_en is None: _sozluk_en = {}
                _sozluk_en[f"{pk[0]}-{pk[1]}"] = {}
            for aci in ["Kavuşum","Karşıt","Kare","Trigon","Sekstil"]:
                _sozluk_tr[f"{pk[0]}-{pk[1]}"][aci] = _urun(pk[0], pk[1], aci, en=False)
                if _sozluk_en is not None:
                    _sozluk_en[f"{pk[0]}-{pk[1]}"][aci] = _urun(pk[0], pk[1], aci, en=True)
    if _sozluk_en is not None:
        return _sozluk_en
    return _sozluk_tr

def _collect_solar_lunar_data(motor):
    """Solar return and lunar return predictions for the natal chart. Individual-focused."""
    data = {}
    try:
        jd = motor.get_natal_julian_day("p1")
        import datetime
        simdi = datetime.datetime.now()
        sr = motor.calculate_solar_return_tema(jd, simdi.year)
        if sr and isinstance(sr, str) and len(sr) > 20:
            sr_clean = _bireysellestir(_strip_html(sr))
            if len(sr_clean) > 20:
                data["solar_return"] = sr_clean
            try:
                data["solar_return_html"] = _bireysellestir(sr)
            except:
                data["solar_return_html"] = ""
    except:
        pass
    try:
        jd = motor.get_natal_julian_day("p1")
        import datetime
        simdi = datetime.datetime.now()
        lr = motor.calculate_lunar_return_tema(jd, simdi.year, simdi.month)
        if lr and isinstance(lr, str) and len(lr) > 20:
            lr_clean = _bireysellestir(_strip_html(lr))
            if len(lr_clean) > 20:
                data["lunar_return"] = lr_clean
            try:
                data["lunar_return_html"] = _bireysellestir(lr)
            except:
                data["lunar_return_html"] = ""
    except:
        pass
    try:
        data["minor_progress"] = _natal_minor_progress_yorumlari(motor)
    except:
        data["minor_progress"] = []
    try:
        data["minor_progress_6month"] = _natal_minor_progress_6month(motor)
    except:
        data["minor_progress_6month"] = ""
    return data

def _natal_hayat_alani_analizi(motor):
    """Bireysel natal için kapsamlı hayat alanı analizi.
    Her alan için: skor, doğal dil yorum, spor/sanat/beslenme/hastalık/öneri."""
    try:
        jd = motor.get_natal_julian_day("p1")

        BURCLAR = ["Koç","Boğa","İkizler","Yengeç","Aslan","Başak","Terazi","Akrep","Yay","Oğlak","Kova","Balık"]

        gez_poz = {}
        for g_ad, g_id in list(GEZEGENLER.items())[:14]:
            try:
                deg = swe.calc_ut(jd, g_id)[0][0]
                gez_poz[g_ad] = {"derece": deg, "burc": BURCLAR[int(deg//30)], "burc_no": int(deg//30)}
            except: pass

        cusps, ascmc = swe.houses(jd, motor.enlem, motor.boylam, b'P')
        ev_kapsamlari = []
        for i in range(12):
            bas = cusps[i]; bit = cusps[(i+1)%12]
            ev_kapsamlari.append({"ev": i+1, "bas": bas, "bit": bit, "bas_burc": BURCLAR[int(bas//30)]})

        def gezegenin_evi(deg):
            for ek in ev_kapsamlari:
                if ek["bas"] <= ek["bit"]:
                    if ek["bas"] <= deg < ek["bit"]: return ek["ev"]
                else:
                    if deg >= ek["bas"] or deg < ek["bit"]: return ek["ev"]
            return 1

        gez_ev = {}
        for g_ad, info in gez_poz.items():
            gez_ev[g_ad] = gezegenin_evi(info["derece"])

        BURC_YONETICI = {"Koç":"Mars","Boğa":"Venüs","İkizler":"Merkür","Yengeç":"Ay",
            "Aslan":"Güneş","Başak":"Merkür","Terazi":"Venüs","Akrep":"Plüton",
            "Yay":"Jüpiter","Oğlak":"Satürn","Kova":"Uranüs","Balık":"Neptün"}

        def ev_konusu(ev_no):
            return {1:"Benlik algısı",2:"Maddi kaynaklar",3:"İletişim",4:"Aile",5:"Yaratıcılık",
                6:"Sağlık ve rutin",7:"Ortaklıklar",8:"Dönüşüm",9:"Seyahat ve inanç",
                10:"Kariyer",11:"Sosyal çevre",12:"Bilinçaltı"}.get(ev_no,"Genel")

        # ── Burç bazlı spor önerileri ──
        BURC_SPOR = {
            "Koç": "koşu, boks, dövüş sporları, kros, dağcılık, sprint",
            "Boğa": "yürüyüş, pilates, ağırlık çalışması, bahçe sporları, ata binme",
            "İkizler": "bisiklet, badminton, masa tenisi, çoklu spor denemeleri, okçuluk",
            "Yengeç": "yüzme, su sporları, tai-chi, akşam yürüyüşleri, ritmik hareket",
            "Aslan": "tenis, vücut geliştirme, jimnastik, Fitness, gösteri sporları",
            "Başak": "yoga, pilates, düzenli yürüyüş, temiz hava egzersizleri, stretching",
            "Terazi": "dans, pilates, buz pateni, ritmik jimnastik, partner sporları",
            "Akrep": "boks, dövüş sanatları, crossfit, yüzme, dalış, yüksek yoğunluklu interval",
            "Yay": "at biniciliği, açık hava sporları, kampçılık, okçuluk, macera sporları",
            "Oğlak": "uzun mesafe koşusu, bisiklet, dağcılık, disiplinli antrenman, ağırlık",
            "Kova": "ekstrem sporlar, kaykay, snowboard, serbest dalış, yenilikçi egzersizler",
            "Balık": "yüzme, dalış, yoga, tai-chi, meditasyon hareketleri, su sporları",
        }

        # ── Planet+ev özel spor haritası ──
        SPOR_MAP = {
            ("Mars",1): "Koşu, boks, dövüş sanatları ve bireysel mücadele sporları",
            ("Mars",6): "CrossFit, interval antrenman, yüksek tempolu egzersizler",
            ("Mars",5): "Rekabetçi sporlar, tenis, squash, spor müsabakaları",
            ("Venüs",1): "Dans, pilates, yüzme, estetik ve akıcı sporlar",
            ("Venüs",6): "Yoga, esneme egzersizleri, doğa yürüyüşü",
            ("Venüs",5): "Dans, buz pateni, ritmik jimnastik",
            ("Jüpiter",1): "Açık hava sporları, takım oyunları, doğa sporları",
            ("Jüpiter",6): "Uzun yürüyüşler, trekking, doğa kampçılığı",
            ("Jüpiter",9): "At biniciliği, okçuluk, açık hava macera sporları",
            ("Satürn",1): "Uzun mesafe koşusu, bisiklet, dayanıklılık sporları",
            ("Satürn",6): "Düzenli yürüyüş, disiplinli antrenman, ağırlık çalışması",
            ("Satürn",10): "Maraton, triatlon, uzun vadeli dayanıklılık hedefleri",
            ("Ay",1): "Yüzme, tai-chi, akşam yürüyüşleri, ritmik hareket",
            ("Ay",6): "Yoga, meditasyon egzersizleri, hafif tempolu sporlar",
            ("Ay",4): "Bahçe yürüyüşleri, evde egzersiz, aile spor aktiviteleri",
            ("Uranüs",1): "Ekstrem sporlar, kaykay, snowboard, yenilikçi egzersizler",
            ("Uranüs",11): "Grup extreme sporları, parkour, serbest dalış",
            ("Neptün",1): "Yoga, yüzme, dans, su sporları, tai-chi",
            ("Neptün",12): "Meditasyon hareketleri, qigong, ruhsal beden egzersizleri",
            ("Güneş",1): "Tenis, atletizm, liderlik gerektiren spor branşları",
            ("Güneş",5): "Gösteri sporları, jimnastik, artistik performans",
            ("Plüton",8): "Dönüşümsel fitness, derin vücut çalışmaları,detoks sporları",
            ("Plüton",6): "Şifa odaklı yoga, meditasyon, beden-ruh arındırması",
            ("Merkür",3): "Hızlı yürüyüş, bisiklet, çoklu spor salonu egzersizleri",
            ("Merkür",6): "Koordinasyon çalışmaları, beyin-beden egzersizleri",
        }

        # ── Burç bazlı sanat önerileri ──
        BURC_SANAT = {
            "Koç": "heykel, performans sanatı, cesur deneysel çalışmalar, sokak sanatı",
            "Boğa": "seramik, doğal malzemelerle sanat, fotoğrafçılık, müzik aleti çalma",
            "İkizler": "yazma, edebiyat, tiyatro, podcast, dilbilimsel sanat, gazetecilik",
            "Yengeç": "mutfak sanatı, el işi, fotoğrafçılık, duygusal müzik, hikaye anlatıcılığı",
            "Aslan": "sahne sanatları, tiyatro, dans, gösteri, kostüm tasarımı, artistik performans",
            "Başak": "detaylı el işleri, dijital tasarım, organizasyon sanatı, ince işçilik",
            "Terazi": "moda tasarımı, iç mimari, estetik sanatlar, mücevher tasarımı, fotoğrafçılık",
            "Akrep": "fotoğrafçılık, sinema, dönüşümsel sanat, heykel, derin temalı eserler",
            "Yay": "seyahat fotoğrafçılığı, belgesel, mural, sokak sanatı, kültürler arası sanat",
            "Oğlak": "mimari, heykel, yapısal sanatlar, restorasyon, geleneksel teknikler",
            "Kova": "dijital sanat, enstalasyon, video art, teknoloji-sanat, grafik tasarım",
            "Balık": "suluboya, müzik, dans, meditasyon sanatı, sinema, ruhsal sembolizm",
        }

        # ── Planet+ev özel sanat haritası ──
        SANAT_MAP = {
            ("Venüs",5): "Resim, heykel, seramik, görsel sanatlar",
            ("Venüs",3): "Şiir, edebiyat, yaratıcı yazarlık, şarkı sözü yazma",
            ("Venüs",10): "Moda tasarımı, iç mimari, estetik danışmanlık",
            ("Neptün",5): "Müzik, dans, fotoğrafçılık, sinema ve sahne sanatları",
            ("Neptün",12): "Meditasyon sanatı, mandala, spiritüel resim, şiir",
            ("Neptün",3): "Müzik aleti çalma, şarkı söyleme, beste yapma",
            ("Merkür",3): "Yazma, gazetecilik, blog, tiyatro oyunculuğu",
            ("Merkür",5): "Tiyatro, senaryo yazımı, yaratıcı yazma atölyeleri",
            ("Ay",4): "El sanatları, örgü, nakış, seramik, mutfak sanatı",
            ("Ay",5): "Çocuk kitabı yazarlığı, oyuncak tasarımı, hikaye anlatıcılığı",
            ("Güneş",5): "Sahne sanatları, tiyatro oyunculuğu, performans",
            ("Uranüs",5): "Dijital sanat, grafik tasarım, enstalasyon, deneysel sanat",
            ("Jüpiter",5): "Performans sanatları, gösteri dünyası, sahne yönetimi",
            ("Satürn",5): "Mimari, heykel, yapısal sanatlar, restorasyon",
            ("Plüton",5): "Fotoğrafçılık, dönüşümsel sanat, derin temalı eserler",
        }

        # ── Burç bazlı hobi önerileri ──
        BURC_HOBI = {
            "Koç": "macera sporları, seyahat, keşif, motor sporları, kampçılık",
            "Boğa": "bahçecilik, koleksiyonculuk, yemek yapımı, antika araştırması, doğa yürüyüşü",
            "İkizler": "satranç, yazılım, okuma, podcast dinleme, dil öğrenme, bulmaca çözme",
            "Yengeç": "mutfak hobileri, fotoğrafçılık, hatıra defteri tutma, aile sohbetleri",
            "Aslan": "tiyatro, sahne sanatları, çocuklara gönüllülük, gösteri hobileri",
            "Başak": " Düzenleme, organizasyon, detaylı el işleri, kod yazma, veri analizi",
            "Terazi": "müzik, sanat koleksiyonculuğu, sosyal etkinlikler, dekorasyon, modа",
            "Akrep": "gizem romanları, dedektiflik oyunları, dalış, araştırma, psikoloji",
            "Yay": "seyahat planlama, felsefe, okçuluk, doğa keşfi, kültürler arası etkileşim",
            "Oğlak": "ahşap işçiliği, strateji oyunları, yürüyüş, plan yapma, geleneksel zanaat",
            "Kova": "teknoloji, bilim kurgu, robotik, uzay araştırmaları, dijital projeler",
            "Balık": "müzik, fotoğrafçılık, doğa gözleme, meditasyon, hayal güç aktiviteleri",
        }

        # ── Burç bazlı sağlık önerileri ──
        BURC_SAGLIK = {
            "Koç": "baş bölgesi sağlığına dikkat; dinamik egzersiz ama kafa travmalarından kaçınma",
            "Boğa": "boğaz ve tiroid sağlığı; düzenli beslenme ve metabolizma kontrolü",
            "İkizler": "sinir sistemi ve solunum yolu sağlığı; nefes çalışmaları önemli",
            "Yengeç": "mide ve sindirim sistemi; düzenli uyku ve duygusal denge",
            "Aslan": "kalp ve omurga sağlığı; kardiyo egzersizleri ve duruş düzeltilmesi",
            "Başak": "bağırsak sağlığı ve gıda hassasiyeti; temiz beslenme öncelik",
            "Terazi": "böbrek ve cilt sağlığı; su tüketimi ve hormonal denge önemli",
            "Akrep": "üreme sistemi ve bağışıklık; detoks ve arındırıcı beslenme",
            "Yay": "karaciğer ve kalça sağlığı; aktif yaşam ve düzenli egzersiz",
            "Oğlak": "eklem, kemik ve cilt sağlığı; mineral takviyesi ve nemlendirme",
            "Kova": "dolaşım sistemi ve ayak bilekleri; kan dolaşımı egzersizleri",
            "Balık": "bağışıklık sistemi ve uyku düzeni; meditasyon ve düzenli ritim",
        }

        # ── Burç bazlı beslenme önerileri ──
        BURC_BESLENME = {
            "Koç": "baharatlı, enerji veren besinler; demir ve protein ağırlıklı, kırmızı et ve yeşil yapraklı",
            "Boğa": "kaliteli, lezzetli, doyurucu yemekler; doğal ve katkısız beslenme, süt ürünleri",
            "İkizler": "hafif, çeşitli ve renkli besinler; kuruyemiş, meyve, zengin atıştırmalıklar",
            "Yengeç": "ev yapımı, doğal, organik gıdalar; süt ürünleri, çorbalar ve sıcak yemekler",
            "Aslan": "kalp dostu besinler, antioksidan zengini gıdalar, kırmızı meyveler, balık",
            "Başak": "saf, temiz, organik beslenme; lifli gıdalar, tam tahıllar, detoks çayları",
            "Terazi": "dengeli, hafif, renkli beslenme; salatalar, sosyal yemekler, çikolata",
            "Akrep": "yoğun lezzetli besinler, detoks gıdalar, probiyotikler, sarımsak ve zencefil",
            "Yay": "farklı mutfakları keşfetme; baharatlı ve egzotik tatlar, protein ağırlıklı",
            "Oğlak": "mineral zengini, düzenli ve ölçülü beslenme; kemik dostu kalsiyumlu gıdalar",
            "Kova": "yenilikçi ve farklı besinler; smoothie bowl, süper gıdalar, vejetaryen alternatifler",
            "Balık": "deniz ürünleri, omega-3 kaynakları; hafif ve sıvı ağırlıklı, bitki çayları",
        }

        # ── Burç bazlı aşk önerileri ──
        BURC_ASK = {
            "Koç": "tutkulu ve coşkulu bir bağ; fiziksel çekim güçlü, cesur romantik girişimler",
            "Boğa": "sadakat, güven ve uzun vadeli bağlılık; duyusal zevkler ve konfor ön planda",
            "İkizler": "entelektüel uyum ve sosyal paylaşım; iletişim, mizah ve zihinsel bağ önemli",
            "Yengeç": "derin duygusal bağ ve ev hissi; şefkat, koruma ve aile değerleri temel",
            "Aslan": "göz kamaştırıcı romantizm; ilgi, takdir ve gösterişli sevgi ifadeleri",
            "Başak": "hizmet ve pratik sevgi; düzenli küçük jestler, düşüncelilik ve sadakat",
            "Terazi": "zarif ve dengeli birliktelik; estetik paylaşım, sanat ve adalet duygusu",
            "Akrep": "tutku, gizem ve derin dönüşüm; güçlü ruhsal ve cinsel bağ arayışı",
            "Yay": "özgür ve maceracı aşk; birlikte keşif, felsefe ve geniş ufuklar",
            "Oğlak": "ciddi, uzun vadeli ve hedefe yönelik birliktelik; disiplin ve saygı",
            "Kova": "özgün ve bağımsız bağ; entelektüel uyum, yenilik ve sosyal idealizm",
            "Balık": "ruhani ve koşulsuz aşk; empati, fedakarlık ve hayal gücü dolu romantizm",
        }

        # ── Burç bazlı kariyer önerileri ──
        BURC_KARIYER = {
            "Koç": "girişimcilik, liderlik, acil durum yönetimi, spor, askeriye, start-up",
            "Boğa": "bankacılık, gayrimenkul, gıda, müzik, tasarım, sanat, değer yönetimi",
            "İkizler": "iletişim, medya, yazılım, pazarlama, satış, gazetecilik, pedagoji",
            "Yengeç": "eğitim, danışmanlık, turizm, gastronomi, emlak, aile işletmeciliği",
            "Aslan": "sahne sanatları, yönetim, eğitim, eğlence, PR, lüks marka yönetimi",
            "Başak": "muhasebe, sağlık hizmetleri, editörlük, kalite kontrol, analiz, IT",
            "Terazi": "hukuk, diplomasi, sanat, moda, iç mimari, arabuluculuk, danışmanlık",
            "Akrep": "araştırma, psikoloji, finans, dedektiflik, dönüşüm danışmanlığı, tıp",
            "Yay": "akademisyenlik, uluslararası ilişkiler, seyahat, yayıncılık, felsefe",
            "Oğlak": "yöneticilik, mimari, mühendislik, devlet hizmeti, uzun vadeli projeler",
            "Kova": "teknoloji, bilim, sosyal hareketler, havacılık, yenilikçi start-up'lar",
            "Balık": "sanat, psikoloji, sağlık, danışmanlık, manevi rehberlik, hayır kurumları",
        }

        # ── Burç bazlı aile önerileri ──
        BURC_AILE = {
            "Koç": "aile içinde lider ve koruyucu rol; cesaret ve bağımsızlık değerleri aktarır",
            "Boğa": "aile geleneklerini sürdüren güvenilir bağ; konfor ve istikrar odaklı",
            "İkizler": "aile ile entelektüel paylaşım ve açık iletişim; çok yönlü etkileşim",
            "Yengeç": "aile bağlarınız duygusal derinlik ve şefkatle örülü; koruyucu ve besleyici",
            "Aslan": "ailede yaratıcılık ve cömertlik; çocuklara ilham kaynağı olma",
            "Başak": "aile içinde düzen ve hizmet; pratik destek ve detaycı bakım",
            "Terazi": "ailede denge ve uyum; sanatsal paylaşım ve estetik değerler",
            "Akrep": "ailede derin dönüşüm ve sadakat; güçlü duygusal bağlar ve korunma",
            "Yay": "ailede macera ve bilgelik aktarımı; açık fikirli ve geniş perspektif",
            "Oğlak": "ailede disiplin ve sorumluluk; geleneksel değer ve uzun vadeli yapı",
            "Kova": "ailede yenilik ve bağımsızlık; bireyselliğe saygı ve farklılık kutlaması",
            "Balık": "ailede merhamet ve ruhsal bağ; sezgisel anlayış ve koşulsuz kabul",
        }

        # ── Burç bazlı maddi öneriler ──
        BURC_MADDI = {
            "Koç": "girişimci yatırımlar ve risk alma potansiyeliniz yüksek; ani kararlar",
            "Boğa": "birikim ve uzun vadeli yatırımlar; gayrimenkul ve değerli metal tercihi",
            "İkizler": "çeşitli gelir kaynakları; iletişim ve medya yatırımları, kısa vadeli",
            "Yengeç": "emlak ve aile yatırımları; güvenli liman arayışı, duygusal harcama kontrolü",
            "Aslan": "gösterişli yatırımlar ve sanat; lüks markalar ve eğlence sektörü",
            "Başak": "detaylı bütçe planlaması; küçük birikimler ve pratik tasarruf",
            "Terazi": "partnerle ortak finansal kararlar; estetik yatırımlar ve denge arayışı",
            "Akrep": "dönüşümsel yatırımlar; ortak kaynaklar, miras ve vergi planlaması",
            "Yay": "farklı kültürlerden gelir kaynakları; uluslararası yatırımlar ve eğitim",
            "Oğlak": "uzun vadeli ve disiplinli yatırımlar; emeklilik planlaması ve gayrimenkul",
            "Kova": "teknoloji ve yenilikçi yatırımlar; kripto, start-up ve sosyal projeler",
            "Balık": "sanat ve manevi değeri olan yatırımlar; hayırseverlik ve yaratıcı projeler",
        }

        # ── Burç bazlı sosyal öneriler ──
        BURC_SOSYAL = {
            "Koç": "sosyal çevrenizde doğal bir lider ve ilham kaynağısınız; cesur ve açık",
            "Boğa": "sadık ve güvenilir bir dost; çevrenizde sağlam ve uzun süreli bağlar",
            "İkizler": "geniş bir çevre ve entelektüel sohbetler; iletişim odaklı sosyallik",
            "Yengeç": "samimi ve duygusal bağlar; küçük ama derin dostluk çevresi",
            "Aslan": "sosyal çevrenin yıldızı; cömertlik ve ilham veren liderlik",
            "Başak": "hizmet odaklı sosyallik; gönüllülük ve pratik yardımlaşma çevreleri",
            "Terazi": "zarif ve dengeli sosyal ilişkiler; sanatsal paylaşım ve estetik çevre",
            "Akrep": "derin ve seçici sosyal bağlar; güvene dayalı güçlü ittifaklar",
            "Yay": "geniş ve çeşitli sosyal çevre; farklı kültürlerden dostluklar",
            "Oğlak": "profesyonel ve amaçlı sosyal çevreler; kariyer odaklı networking",
            "Kova": "özgün ve yenilikçi çevreler; sosyal gruplar ve dijital topluluklar",
            "Balık": "empatik ve ruhsal çevreler; yardım dernekleri ve spiritüel topluluklar",
        }

        # ── Burç bazlı eğitim önerileri ──
        BURC_EGITIM = {
            "Koç": "yeni konulara hızlı ilgi duyar ve cesurca dalarsınız; pratik ve uygulamalı öğrenme",
            "Boğa": "derinlemesine çalışma ve pratik beceriler kazanma; sabırlı ve metodik",
            "İkizler": "soyut kavramlar ve teorik bilgiye yatkınsınız; çoklu kaynak kullanımı",
            "Yengeç": "sezgisel öğrenme ve aile/duygusal konulara ilgi; hikaye anlatımı yöntemi",
            "Aslan": "görsel ve performans odaklı öğrenme; yaratıcı projeler ve sunumlar",
            "Başak": "sistemli ve detaycı çalışma; araştırma, analiz ve pratik uygulama",
            "Terazi": "dengeli ve çok perspektifli öğrenme; müzakere ve estetik eğitimleri",
            "Akrep": "araştırma ve derinlemesine dalma; psikoloji, gizem ve dönüşüm konuları",
            "Yay": "felsefi ve geniş perspektifli öğrenme; uluslararası eğitim ve seyahat",
            "Oğlak": "disiplinli ve hedefe yönelik çalışma; sertifika ve kariyer odaklı",
            "Kova": "yenilikçi ve teknolojik öğrenme; online eğitim, dijital kaynaklar",
            "Balık": "sezgisel ve yaratıcı öğrenme; sanat, müzik ve meditasyon yoluyla",
        }

        # ── Burç bazlı manevi öneriler ──
        BURC_MANEVİ = {
            "Koç": "aktif meditasyon ve doğada ruhsal bağlantı; cesur içsel keşif",
            "Boğa": "toprakla bağlantı, doğa ritüelleri ve fiziksel manevi pratikler",
            "İkizler": "felsefi sorgulama ve zihinsel farkındalık; yazı ve meditasyon",
            "Yengeç": "ay döngülerine bağlı ritüeller, aile kökleri meditasyonu, su meditasyonu",
            "Aslan": "kalp merkezli meditasyon, yaratıcı görselleştirme, ilham veren ritüeller",
            "Başak": "günlük manevi pratikler, hizmet meditasyonu, düzenli ruhsal rutin",
            "Terazi": "denge ve uyum meditasyonu, sanat yoluyla ruhsal ifade, ikiliklerin birleşmesi",
            "Akrep": "dönüşüm meditasyonu, gölge çalışmaları, derin içsel arınma",
            "Yay": "felsefi meditasyon, farklı spiritüel gelenekleri keşif, dağ meditasyonu",
            "Oğlak": "disiplinli meditasyon pratiği, guru-öğrenci ilişkisi, yapılandırılmış ruhsallık",
            "Kova": "teknoloji destekli meditasyon, grup meditasyonu, yenilikçi ruhsal pratikler",
            "Balık": "derin meditasyon,瑜伽, ruhsal rehberlik, deniz meditasyonu, ego erimesi",
        }

        # ── Burç bazlı seyahat önerileri ──
        BURC_SEYAHAT = {
            "Koç": "macera dolu keşifler, adrenalin yüklü rotalar, solo seyahatler",
            "Boğa": "doğa güzellikleri, lüks konaklama, gastronomi turları, yavaş seyahat",
            "İkizler": "şehir şehir gezmeler, müze ve kültür turları, kısa süreli seyahatler",
            "Yengeç": "doğup büyüdüğünüz topraklar, tarihi mekanlar, rahat ve huzurlu tatiller",
            "Aslan": "lüks tatil köyleri, sahne sanatları festivalleri, gösterişli destinasyonlar",
            "Başak": "sağlık turları, wellness merkezleri, temiz doğa yürüyüşleri, detoks kampları",
            "Terazi": "kültürel başkentler, sanat galerileri, romantik kaçamaklar, estetik destinasyonlar",
            "Akrep": "gizemli ve tarihi mekanlar, arkeolojik sitler, derin kültürel deneyimler",
            "Yay": "farklı kıtalar, uzak kültürler, felsefi ve tarihi rotalar, açık hava kampları",
            "Oğlak": "dağcılık turları, tarihi kaleler, geleneksel ve yapısal mimari keşifleri",
            "Kova": "yenilikçi destinasyonlar, bilim müzeleri, farklı topluluklar, uzay merkezleri",
            "Balık": "sahil kasabaları, mistik tapınaklar, meditasyon kampları, ruhsal yolculuklar",
        }

        # ── Planet+burç bazlı hastalık haritası ──
        HASTALIK_MAP = {
            ("Mars",6,"Koç"): "Baş ağrısı, migren, sinüzit, yüz ve kafa bölgesi rahatsızlıkları",
            ("Mars",6,"Boğa"): "Boğaz enfeksiyonları, ses teli sorunları, tiroid dengesizliği",
            ("Mars",6,"Aslan"): "Kalp çarpıntısı, sırt ağrıları, omurga sorunları",
            ("Mars",6,"Akrep"): "Enflamasyon, üreme sağlığı, bağırsak iltihabı",
            ("Mars",6,"Yay"): "Karaciğer, kalça bölgesi, siyatik sinir",
            ("Mars",6,"Koç"): "Diş sağlığı, kafa travmaları, kemik yapısı",
            ("Satürn",6,"Oğlak"): "Kireçlenme, eklem ağrıları, diz sorunları, kemik erimesi",
            ("Satürn",6,"Kova"): "Dolaşım sorunları, varis, ayak bileği incinmeleri",
            ("Satürn",6,"Balık"): "Ayak sağlığı, lenf sistemi, ödem tutma eğilimi",
            ("Ay",6,"Yengeç"): "Mide hassasiyeti, sindirim sorunları, göğüs sağlığı",
            ("Ay",6,"Balık"): "Psikolojik hassasiyet, bağımlılık eğilimi, uyku düzeni",
            ("Ay",6,"Boğa"): "Boğaz hassasiyeti, yeme bozuklukları, metabolizma",
            ("Venüs",6,"Boğa"): "Boğaz ve bademcik sorunları, cilt alerjileri, böbrek dengesi",
            ("Venüs",6,"Terazi"): "Böbrek fonksiyonları, cilt hassasiyeti, hormonal denge",
            ("Neptün",6,"Balık"): "Bağışıklık zayıflığı, kronik yorgunluk, uyku apnesi",
            ("Neptün",6,"Yay"): "Karaciğer hassasiyeti, alerjik reaksiyonlar",
            ("Güneş",6,"Aslan"): "Kalp sağlığı, canlılık düşüşü, tansiyon dalgalanmaları",
            ("Plüton",6,"Akrep"): "Bağışıklık sistemi, hücresel sorunlar, detoks ihtiyacı",
        }

        # ── Planet+burç bazlı beslenme haritası (özel durumlar) ──
        BESLENME_MAP = {
            "Ay_Yengeç": "Ev yapımı, doğal, organik gıdalar; süt ürünleri ve ev yemekleri iyi gelir",
            "Ay_Boğa": "Kaliteli, lezzetli, doyurucu yemekler; doğal ve katkısız beslenme",
            "Ay_Balık": "Deniz ürünleri, omega-3 kaynakları; hafif ve sıvı ağırlıklı beslenme",
            "Ay_Oğlak": "Düzenli, disiplinli, saatli beslenme; mineral ve kalsiyum ağırlıklı",
            "Ay_Başak": "Saf, temiz, organik beslenme; gıda hassasiyetlerine dikkat",
            "Venüs_Boğa": "Lezzet odaklı, kaliteli gıdalar; şarküteri ve doğal tatlar",
            "Venüs_Terazi": "Dengeli, hafif, renkli ve çeşitli beslenme; sosyal yemekler",
            "Jüpiter_Yay": "Farklı mutfakları keşfetme; baharatlı ve egzotik tatlar",
            "Jüpiter_Balık": "Deniz ürünleri, bitkisel ağırlıklı, bol sıvı tüketimi",
            "Mars_Koç": "Baharatlı, enerji veren, demir ve protein ağırlıklı beslenme",
            "Mars_Aslan": "Kalp dostu besinler, magnezyum, antioksidan zengini gıdalar",
            "Satürn_Oğlak": "Mineral zengini, kemik dostu kalsiyumlu beslenme",
            "Neptün_Balık": "Sebze ağırlıklı, hafif, sıvı ve bitki bazlı beslenme",
        }

        # ── Burç bazlı sağlık uyarı haritası ──
        BURC_SAGLIK_UYARISI = {
            "Koç": "baş bölgesi, migren ve yaralanma riski; sıcak çatışmalara dikkat",
            "Boğa": "boğaz, tiroid ve boyun kas gerginliği; yavaş metabolizma eğilimi",
            "İkizler": "sinir sistemi, solunum yolu ve iletişim kaynaklı gerginlik",
            "Yengeç": "mide, sindirim, göğüs bölgesi; duygusal yeme ve su tutma",
            "Aslan": "kalp, sırt ve omurga; aşırı efordan kaynaklanan gerilim",
            "Başak": "bağırsak, deri ve sinir sistemi; aşırı titizlik kaynaklı stres",
            "Terazi": "böbrek, cilt ve hormonal denge; kararsızlık stresi",
            "Akrep": "üreme sistemi, bağışıklık ve yoğun duygusal stres",
            "Yay": "karaciğer, kalça ve siyatik; aşırıya kaçma ve sınırları zorlama",
            "Oğlak": "eklem, kemik, cilt ve eklemler; kronik stres ve distoni",
            "Kova": "dolaşım, ayak bilekleri ve sinir sistemi; beklenmedik kazalar",
            "Balık": "bağışıklık, ayak ve lenf sistemi; ilaç/alergi duyarlılığı",
        }

        # ── Yardımcı fonksiyonlar ──
        def _spor_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            key = (g_ad, ev_no)
            if key in SPOR_MAP:
                return f"{g_ad} • {burc}: {SPOR_MAP[key]}"
            burc_spor = BURC_SPOR.get(burc)
            if burc_spor:
                return f"{g_ad} • {burc}: {burc_spor}"
            return None

        def _sanat_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            key = (g_ad, ev_no)
            if key in SANAT_MAP:
                return f"{g_ad} • {burc}: {SANAT_MAP[key]}"
            burc_sanat = BURC_SANAT.get(burc)
            if burc_sanat:
                return f"{g_ad} • {burc}: {burc_sanat}"
            return None

        def _hobi_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_hobi = BURC_HOBI.get(burc)
            if burc_hobi:
                return f"{g_ad} • {burc}: {burc_hobi}"
            return None

        def _hastalik_uyarisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            key = (g_ad, ev_no, burc)
            if key in HASTALIK_MAP:
                return HASTALIK_MAP[key]
            for (g, e, b), v in HASTALIK_MAP.items():
                if g == g_ad and e == ev_no: return v
            uyari = BURC_SAGLIK_UYARISI.get(burc)
            if uyari:
                return f"{g_ad} etkisiyle {burc}: {uyari}"
            return None

        def _saglik_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            saglik = BURC_SAGLIK.get(burc)
            if saglik:
                return f"{g_ad} • {burc}: {saglik}"
            return None

        def _beslenme_onerisi(g_ad, burc_no):
            burc = BURCLAR[burc_no % 12]
            key = f"{g_ad}_{burc}"
            if key in BESLENME_MAP:
                return f"{g_ad} • {burc}: {BESLENME_MAP[key]}"
            burc_besl = BURC_BESLENME.get(burc)
            if burc_besl:
                return f"{g_ad} • {burc}: {burc_besl}"
            return None

        def _ask_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_ask = BURC_ASK.get(burc)
            if burc_ask:
                return f"{g_ad} • {burc}: {burc_ask}"
            return None

        def _kariyer_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_kar = BURC_KARIYER.get(burc)
            if burc_kar:
                return f"{g_ad} • {burc}: {burc_kar}"
            return None

        def _aile_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_ail = BURC_AILE.get(burc)
            if burc_ail:
                return f"{g_ad} • {burc}: {burc_ail}"
            return None

        def _maddi_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_mad = BURC_MADDI.get(burc)
            if burc_mad:
                return f"{g_ad} • {burc}: {burc_mad}"
            return None

        def _sosyal_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_sos = BURC_SOSYAL.get(burc)
            if burc_sos:
                return f"{g_ad} • {burc}: {burc_sos}"
            return None

        def _egitim_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_egi = BURC_EGITIM.get(burc)
            if burc_egi:
                return f"{g_ad} • {burc}: {burc_egi}"
            return None

        def _manevi_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_man = BURC_MANEVİ.get(burc)
            if burc_man:
                return f"{g_ad} • {burc}: {burc_man}"
            return None

        def _seyahat_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_sey = BURC_SEYAHAT.get(burc)
            if burc_sey:
                return f"{g_ad} • {burc}: {burc_sey}"
            return None

        # ── Kategori tanımları ──
        ALANLAR = [
            {"anahtar":"spor","etiket":"Spor & Fitness","icon":"🏃","image":"https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=400&fit=crop",
             "evler":[1,6,9],"gezegenler":["Mars","Satürn","Jüpiter","Venüs","Uranüs","Neptün","Ay","Güneş"],
             "giris":"Fiziksel aktivite hayatınızda önemli bir yere sahip; bedeniniz harekete geçmek için doğal bir çağrı taşıyor.",
             "kapanis":"Hareket hayattır, bedeninizi dinleyin."},
            {"anahtar":"sanat","etiket":"Sanat & Yaratıcılık","icon":"🎨","image":"https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=400&h=400&fit=crop",
             "evler":[5,3,12,9],"gezegenler":["Venüs","Neptün","Merkür","Ay","Uranüs","Jüpiter","Satürn","Plüton"],
             "giris":"Yaratıcılık ve estetik duyarlılık sizin için hayatın renkli tarafını oluşturuyor.",
             "kapanis":"Sanat ruhun gıdasıdır, içinizdeki yaratıcılığı besleyin."},
            {"anahtar":"hobi","etiket":"Hobi & İlgi Alanları","icon":"🎮","image":"https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=400&h=400&fit=crop",
             "evler":[3,5,9,12],"gezegenler":["Ay","Venüs","Merkür","Neptün","Uranüs","Jüpiter","Mars","Güneş"],
             "giris":"Boş zamanlarınızı nasıl değerlendirdiğiniz, ilgi alanlarınızın çeşitliliğiyle doğrudan bağlantılı.",
             "kapanis":"Keyif aldığınız her an ruhunuzu besleyen bir hediyedir."},
            {"anahtar":"saglik","etiket":"Sağlık & Zindelik","icon":"💪","image":"https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=400&fit=crop",
             "evler":[6,12,1],"gezegenler":["Ay","Mars","Satürn","Neptün","Güneş"],
             "giris":"Beden ve ruh arasındaki denge, günlük yaşam alışkanlıklarınızın bir yansımasıdır.",
             "kapanis":"Sağlıklı bir yaşam küçük alışkanlıkların büyük etkisiyle inşa edilir."},
            {"anahtar":"beslenme","etiket":"Beslenme & Diyet","icon":"🥗","image":"https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=400&h=400&fit=crop",
             "evler":[2,6,12],"gezegenler":["Ay","Venüs","Mars","Jüpiter","Satürn","Neptün","Plüton","Güneş"],
             "giris":"Yedikleriniz yalnızca bedeninizi değil, duygusal dünyanızı da doğrudan etkiler.",
             "kapanis":"Yedikleriniz sadece bedeninizi değil ruhunuzu da besler."},
            {"anahtar":"ask","etiket":"Aşk & Romantizm","icon":"❤️","image":"https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=400&h=400&fit=crop",
             "evler":[5,7],"gezegenler":["Venüs","Mars","Ay","Güneş"],
             "giris":"Aşk hayatınız, kalbinizin derinliklerinde saklı olan duygusal kodlarla şekilleniyor.",
             "kapanis":"Gerçek aşk önce kendinize duyduğunuz sevgiyle başlar."},
            {"anahtar":"kariyer","etiket":"Kariyer & İş Hayatı","icon":"💼","image":"https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop",
             "evler":[6,10,2],"gezegenler":["Satürn","Jüpiter","Mars","Güneş","Merkür"],
             "giris":"Kariyer yolculuğunuz, disiplin ve vizyonun birleştiği noktada şekilleniyor.",
             "kapanis":"Başarı doğru zamanda atılan cesur adımlarla gelir."},
            {"anahtar":"aile","etiket":"Aile & Kökler","icon":"🏠","image":"https://images.unsplash.com/photo-1511895426328-dc8714191300?w=400&h=400&fit=crop",
             "evler":[4,7,12],"gezegenler":["Ay","Satürn","Venüs","Güneş","Mars"],
             "giris":"Aile bağlarınız ve kökleriniz, kim olduğunuzu anlamanın anahtarıdır.",
             "kapanis":"Aile bağlarınız en büyük manevi mirasınızdır."},
            {"anahtar":"maddi","etiket":"Maddi Durum","icon":"💰","image":"https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=400&h=400&fit=crop",
             "evler":[2,8,11],"gezegenler":["Jüpiter","Venüs","Satürn","Plüton","Mars"],
             "giris":"Parasal akışınız, değerlerinizle uyumlu olduğunda bereket doğal olarak gelir.",
             "kapanis":"Maddi denge önce değerlerinizi netleştirmekten geçer."},
            {"anahtar":"sosyal","etiket":"Sosyal Hayat","icon":"👥","image":"https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=400&h=400&fit=crop",
             "evler":[11,3,7],"gezegenler":["Merkür","Uranüs","Jüpiter","Venüs","Güneş"],
             "giris":"Sosyal çevreniz, iletişim şekliniz ve çevrenizle etkileşiminiz hayatınızı zenginleştiriyor.",
             "kapanis":"Çevreniz size en büyük aynanız ve öğretmeninizdir."},
            {"anahtar":"egitim","etiket":"Eğitim & Zihin","icon":"📚","image":"https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=400&h=400&fit=crop",
             "evler":[3,9,1],"gezegenler":["Merkür","Jüpiter","Satürn","Uranüs","Ay"],
             "giris":"Öğrenme arzunuz ve zihinsel merakınız sizi sürekli gelişmeye yönlendiriyor.",
             "kapanis":"Öğrenmek asla bitmeyen bir yolculuktur."},
            {"anahtar":"manevi","etiket":"Maneviyat & İçsel Yolculuk","icon":"🧘","image":"https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=400&h=400&fit=crop",
             "evler":[9,12,4],"gezegenler":["Neptün","Jüpiter","Ay","Plüton","Satürn"],
             "giris":"İçsel yolculuğunuz, görünmeyen bağlantıların ve sezgisel farkındalığınızın derinliklerine uzanıyor.",
             "kapanis":"İçsel huzur dış dünyada aradığınız her şeyin özüdür."},
            {"anahtar":"seyahat","etiket":"Seyahat & Keşif","icon":"✈️","image":"https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400&h=400&fit=crop",
             "evler":[9,3,12],"gezegenler":["Jüpiter","Uranüs","Merkür","Neptün","Ay"],
             "giris":"Keşfetme arzunuz, yeni ufuklara duyduğunuz özlemin bir yansımasıdır.",
             "kapanis":"Her yolculuk kendinizi keşfetme fırsatıdır."},
        ]

        import random
        sonuclar = []
        for alan in ALANLAR:
            anahtar = alan["anahtar"]
            ilgili_gezegenler = [g for g, e in gez_ev.items() if e in alan["evler"] and g in alan["gezegenler"]]
            ilgili_gezegenler += [g for g in alan["gezegenler"] if g not in ilgili_gezegenler and g in gez_poz]
            ilgili_gezegenler = ilgili_gezegenler[:5]

            skor = 50
            rng = random.Random(str(gez_poz) + anahtar)
            oneriler = []

            # Collect element counts and key planet data (silently, for yorum generation)
            element_sayac = {"Ateş":0,"Toprak":0,"Hava":0,"Su":0}
            for g_ad in ilgili_gezegenler:
                if g_ad not in gez_poz: continue
                info = gez_poz[g_ad]
                ev_no = gez_ev.get(g_ad,1)
                burc_no = info["burc_no"]
                burc_adi = info["burc"]
                element = ["Ateş","Toprak","Hava","Su"][burc_no % 4]
                element_sayac[element] = element_sayac.get(element,0) + 1

                yonetici = BURC_YONETICI.get(burc_adi,"")
                if yonetici == g_ad:
                    skor += 8
                elif ev_no in alan["evler"]:
                    skor += 5
                else:
                    skor += 2

                # Öneriler (tüm kategoriler için gezegen-burç bazlı)
                if anahtar == "spor":
                    spor = _spor_onerisi(g_ad, ev_no, burc_no)
                    if spor: oneriler.append({"tur":"spor","metin":spor})
                elif anahtar == "sanat":
                    sanat = _sanat_onerisi(g_ad, ev_no, burc_no)
                    if sanat: oneriler.append({"tur":"sanat","metin":sanat})
                elif anahtar == "hobi":
                    hobi = _hobi_onerisi(g_ad, ev_no, burc_no)
                    if hobi: oneriler.append({"tur":"hobi","metin":hobi})
                elif anahtar == "saglik":
                    hasta = _hastalik_uyarisi(g_ad, ev_no, burc_no)
                    if hasta: oneriler.append({"tur":"saglik","metin":f"🔴 {hasta}"})
                    saglik = _saglik_onerisi(g_ad, ev_no, burc_no)
                    if saglik: oneriler.append({"tur":"saglik","metin":saglik})
                elif anahtar == "beslenme":
                    besln = _beslenme_onerisi(g_ad, burc_no)
                    if besln: oneriler.append({"tur":"beslenme","metin":besln})
                elif anahtar == "ask":
                    ask = _ask_onerisi(g_ad, ev_no, burc_no)
                    if ask: oneriler.append({"tur":"ask","metin":ask})
                elif anahtar == "kariyer":
                    kar = _kariyer_onerisi(g_ad, ev_no, burc_no)
                    if kar: oneriler.append({"tur":"kariyer","metin":kar})
                elif anahtar == "aile":
                    ail = _aile_onerisi(g_ad, ev_no, burc_no)
                    if ail: oneriler.append({"tur":"aile","metin":ail})
                elif anahtar == "maddi":
                    mad = _maddi_onerisi(g_ad, ev_no, burc_no)
                    if mad: oneriler.append({"tur":"maddi","metin":mad})
                elif anahtar == "sosyal":
                    sos = _sosyal_onerisi(g_ad, ev_no, burc_no)
                    if sos: oneriler.append({"tur":"sosyal","metin":sos})
                elif anahtar == "egitim":
                    egi = _egitim_onerisi(g_ad, ev_no, burc_no)
                    if egi: oneriler.append({"tur":"egitim","metin":egi})
                elif anahtar == "manevi":
                    man = _manevi_onerisi(g_ad, ev_no, burc_no)
                    if man: oneriler.append({"tur":"manevi","metin":man})
                elif anahtar == "seyahat":
                    sey = _seyahat_onerisi(g_ad, ev_no, burc_no)
                    if sey: oneriler.append({"tur":"seyahat","metin":sey})

            dominan = sorted(element_sayac.items(), key=lambda x: -x[1])[0][0] if max(element_sayac.values()) > 0 else "Ateş"

            # ── Natural language yorum generation (no planet names) ──
            havuz = [alan["giris"]]

            ELEMENT_ACIKLAMA = {
                "Ateş": "içinizdeki dinamik ve tutkulu enerji, harekete geçme cesaretiniz",
                "Toprak": "sabit ve güvenilir yapınız, sağlam temeller kurma beceriniz",
                "Hava": "zihinsel berraklığınız ve iletişim kurma yeteneğiniz",
                "Su": "derin duygusal sezgileriniz ve empatik anlayışınız",
            }
            eac = element_acik = ELEMENT_ACIKLAMA.get(dominan, "enerjiniz")
            eac_baslik = eac[0].upper() + eac[1:] if eac else eac

            ALAN_DOMINAN = {
                "spor": f"Özellikle {dominan} elementinin ön planda olduğu bir vücut yapısına sahipsiniz. Bedeninizi zorlamaktan çok, onun doğal ritmine uyum sağladığınızda en verimli sonuçları alıyorsunuz.",
                "sanat": f"Sanatsal ifadenizde {dominan} elementinin izleri belirgin — {eac} yaratıcılığınızı besleyen ana kaynak.",
                "hobi": f"Boş zamanlarınızda {dominan} elementinin yönlendirdiği aktiviteler size daha çok hitap ediyor. {eac_baslik}, ilgi alanlarınızın temelini oluşturuyor.",
                "saglik": f"Sağlığınız {dominan} elementinin dengesine duyarlı — {eac} beden sinyallerinizi doğru okumanızı sağlıyor.",
                "beslenme": f"Beslenme alışkanlıklarınızda {dominan} elementinin etkisi görülüyor. {eac_baslik}, hangi besinlerin size iyi geldiğini belirlemede önemli rol oynuyor.",
                "ask": f"Aşk hayatınızda {dominan} elementinin enerjisi öne çıkıyor. {eac_baslik}, duygusal bağ kurma biçiminizi derinden etkiliyor.",
                "kariyer": f"Kariyer yolculuğunuzda {dominan} elementinin özellikleri belirleyici. {eac_baslik}, iş hayatınızdaki en büyük gücünüz.",
                "aile": f"Aile bağlarınız {dominan} elementinin dokusuyla örülü. {eac_baslik}, köklerinizle kurduğunuz bağın kalitesini belirliyor.",
                "maddi": f"Maddi konularda {dominan} elementinin yaklaşımı size rehberlik ediyor. {eac_baslik}, finansal kararlarınızı şekillendiriyor.",
                "sosyal": f"Sosyal çevrenizde {dominan} elementinin enerjisiyle hareket ediyorsunuz. {eac_baslik}, çevrenizle kurduğunuz bağları güçlendiriyor.",
                "egitim": f"Öğrenme tarzınız {dominan} elementinin doğasına uygun. {eac_baslik}, bilgiyi içselleştirme biçiminizi belirliyor.",
                "manevi": f"Manevi yolculuğunuz {dominan} elementinin rehberliğinde ilerliyor. {eac_baslik}, ruhsal arayışınızın temel dinamiği.",
                "seyahat": f"Keşfetme arzunuz {dominan} elementinin enerjisiyle besleniyor. {eac_baslik}, size yeni ufuklara açılma cesareti veriyor.",
            }

            # Element-based specific suggestions for each area
            ELEMENT_ONERI = {
                "spor": {"Ateş":"yüksek tempolu kardiyo, dövüş sporları ve takım oyunları","Toprak":"ağırlık çalışmaları, pilates ve doğa yürüyüşleri","Hava":"dans, esneme ve grup fitness dersleri","Su":"yüzme, yoga ve su egzersizleri"},
                "sanat": {"Ateş":"heykel, performans sanatı ve deneysel çalışmalar","Toprak":"seramik, dokuma ve doğal malzemelerle sanat","Hava":"dijital sanat, edebiyat ve fotoğrafçılık","Su":"suluboya, müzik ve duygusal ifade sanatları"},
                "hobi": {"Ateş":"macera sporları, seyahat ve keşif","Toprak":"bahçecilik, koleksiyon ve el işleri","Hava":"satranç, yazılım ve okuma","Su":"müzik, fotoğrafçılık ve doğa gözlemi"},
                "saglik": {"Ateş":"dinamik egzersiz ve yüksek enerjili aktiviteler","Toprak":"düzenli uyku, sağlam bir günlük rutin ve doğal beslenme","Hava":"nefes çalışmaları ve zihin-beden bağlantısı","Su":"meditasyon, su terapisi ve duygusal denge"},
                "beslenme": {"Ateş":"hafif, taze ve canlandırıcı besinler; baharatlı yemeklere dikkat","Toprak":"düzenli öğünler, köklü sebzeler ve doğal tahıllar","Hava":"çeşitli ve renkli besinler; sosyal yemek keyfi","Su":"sulu gıdalar, deniz ürünleri ve bitki çayları"},
                "ask": {"Ateş":"tutkulu ve coşkulu bir bağ arayışı, fiziksel çekim güçlü","Toprak":"sadakat, güven ve uzun vadeli bağlılık ön planda","Hava":"entelektüel uyum ve sosyal paylaşım önemli","Su":"derin duygusal bağ ve ruhsal uyum arıyorsunuz"},
                "kariyer": {"Ateş":"öncü ve girişimci roller, liderlik pozisyonları","Toprak":"yapıcı ve yönetici pozisyonlar, finansal istikrar","Hava":"iletişim, yazılım, medya ve danışmanlık","Su":"sanat, psikoloji, sağlık ve danışmanlık alanları"},
                "aile": {"Ateş":"aile içinde lider ve koruyucu rol üstleniyorsunuz","Toprak":"aile geleneklerini sürdüren güvenilir bir bağ kuruyorsunuz","Hava":"aile ile entelektüel paylaşım ve açık iletişim","Su":"aile bağlarınız duygusal derinlik ve şefkatle örülü"},
                "maddi": {"Ateş":"girişimci yatırımlar ve risk alma potansiyeliniz yüksek","Toprak":"birikim ve uzun vadeli yatırımlar size uygun","Hava":"entelektüel sermaye ve network ile kazanç","Su":"sanat ve duygusal değeri olan yatırımlar size uygun"},
                "sosyal": {"Ateş":"sosyal çevrenizde doğal bir lider ve ilham kaynağısınız","Toprak":"sadık ve güvenilir bir dost, çevrenizde sağlam bağlar","Hava":"geniş bir çevre ve entelektüel sohbetler sizi besliyor","Su":"derin dostluklar ve empatik bağlar kuruyorsunuz"},
                "egitim": {"Ateş":"yeni konulara hızlı ilgi duyar ve cesurca dalarsınız","Toprak":"derinlemesine çalışma ve pratik beceriler kazanma","Hava":"soyut kavramlar ve teorik bilgiye yatkınsınız","Su":"sezgisel öğrenme ve psikolojik konular ilginizi çeker"},
                "manevi": {"Ateş":"aktif meditasyon ve doğada ruhsal bağlantı","Toprak":"ritüeller ve günlük manevi pratikler","Hava":"felsefi sorgulama ve zihinsel farkındalık","Su":"derin meditasyon, yoga ve ruhsal rehberlik"},
                "seyahat": {"Ateş":"macera dolu keşifler ve adrenalin yüklü rotalar","Toprak":"doğal güzellikler ve kültürel turlar","Hava":"entelektüel seyahatler ve yeni kültürler öğrenme","Su":"deniz kenarı, mistik ve ruhsal yolculuklar"},
            }
            oneri_metni = ELEMENT_ONERI.get(anahtar, {}).get(dominan, "doğal yapınıza uygun aktiviteler")

            ALAN_OZEL_CUMLER = {
                "spor": f"Sizin için en uygun sporlar {oneri_metni} gibi aktivitelerdir. Vücudunuzu zorlamaktan çok, onun doğal ritmine uyum sağladığınızda en verimli sonuçları alıyorsunuz.",
                "sanat": f"Yaratıcı yönünüz en çok {dominan} elementinin etkisi altında şekilleniyor. {oneri_metni} gibi sanatsal ifade biçimleri size doğal geliyor. Sezgilerinizin rehberliğine izin verdiğinizde ortaya gerçekten özgün işler çıkıyor.",
                "hobi": f"İlgi alanlarınız {dominan} elementinin özelliklerini yansıtıyor. {oneri_metni} gibi hobiler size daha çok hitap ediyor. Bu alandaki merakınız sizi sürekli yeni şeyler denemeye itiyor.",
                "saglik": f"Sağlık konusunda {dominan} elementinin ihtiyaçlarını anlamak size büyük avantaj sağlıyor. Size en iyi gelen aktiviteler {oneri_metni} şeklinde sıralanabilir. Vücudunuzun sinyallerine kulak verdiğinizde doğru seçimleri yapıyorsunuz.",
                "beslenme": f"Beslenme alışkanlıklarınızı {dominan} elementinin dengesine göre düzenlemek size iyi gelecek. {oneri_metni} gibi besinler vücudunuzu hem fiziksel hem de ruhsal olarak besliyor.",
                "ask": f"İlişkilerinizde {oneri_metni}. Duygusal dünyanızda derinlik ve samimiyet arayışınız, sizi yüzeysel bağlardan uzaklaştırıyor. Kalbinizin sesini dinlediğinizde doğru yolu buluyorsunuz.",
                "kariyer": f"Profesyonel hayatınızda {dominan} elementinin güçlü yönlerini kullanıyorsunuz. {oneri_metni} kariyerinizde başarıya ulaşmanızda size yardımcı oluyor. Disiplinli adımlar atmak size istikrar getiriyor.",
                "aile": f"Aile bağlarınız {dominan} elementinin doğasına uygun bir şekilde şekilleniyor. {oneri_metni}. Köklerinizden aldığınız gücü fark ettiğinizde, hem geçmişinizle barışıyor hem de geleceğe sağlam adımlarla ilerliyorsunuz.",
                "maddi": f"Parasal konularda {oneri_metni}. Değerlerinizi netleştirdiğinizde ve akışa güvendiğinizde, maddi kaynaklarınızı daha bilinçli yönetiyorsunuz.",
                "sosyal": f"Sosyal çevrenizde {oneri_metni}. İnsanlarla kurduğunuz bağlarda içtenlik ve derinlik aramanız, size anlamlı dostluklar kazandırıyor.",
                "egitim": f"Öğrenme süreciniz {dominan} elementinin özelliklerini taşıyor. {oneri_metni}. Merak ettiğiniz konuların derinliklerine indikçe, bilginin size kattığı gücü daha çok hissediyorsunuz.",
                "manevi": f"İçsel yolculuğunuzda {oneri_metni} size rehberlik ediyor. Ruhsal arayışınızda sessizliğe ve iç gözleme zaman ayırdığınızda, kendinizle ilgili yeni farkındalıklar kazanıyorsunuz.",
                "seyahat": f"Keşif ruhunuz {dominan} elementinin enerjisiyle canlanıyor. {oneri_metni} size sadece keyif değil, aynı zamanda derin bir perspektif kazandırıyor.",
            }

            yorum_parcalari = [alan["giris"]]
            yorum_parcalari.append(ALAN_DOMINAN[anahtar])
            yorum_parcalari.append(ALAN_OZEL_CUMLER[anahtar])
            yorum_parcalari.append(alan["kapanis"])

            # Kategoriye özel genel öneriler (element-bilinçli)
            ELEMENT_SPOR_IPUCU = {
                "Ateş": "Haftada en az 3 gün yüksek tempolu egzersiz; dinamik ve rekabetçi sporlar enerjinizi besler.",
                "Toprak": "Düzenli ve sabit bir antrenman programı; doğa yürüyüşleri ve ağırlık çalışmaları ideal.",
                "Hava": "Grup dersleri ve dans temelli egzersizler; zihinsel bağlantı kuran sporlar sizi besler.",
                "Su": "Ritmik ve akıcı sporlar; yüzme, yoga, tai-chi gibi su ve meditasyon odaklı aktiviteler."
            }
            ELEMENT_SANAT_IPUCU = {
                "Ateş": "Cesur ve deneysel sanat dallarına dalın; performans ve sahne sanatları size enerji katar.",
                "Toprak": "Somut ve elle yapılan sanatlara odaklanın; seramik, ahşap, dokuma gibi doğal malzemeler.",
                "Hava": "Yazı, edebiyat ve dijital sanatlar zihinsel yaratıcılığınızı besler; iletişim temelli sanatlar.",
                "Su": "Müzik, suluboya ve duygusal ifade sanatları; sezgilerinizin rehberliğine bırakın kendinizi."
            }
            ELEMENT_BESLENME_IPUCU = {
                "Ateş": "Enerji veren ve baharatlı besinler; yeşil yapraklılar ve protein ağırlıklı beslenme.",
                "Toprak": "Toprak ürünleri ve köklü sebzeler; düzenli öğünler ve doğal gıdalar.",
                "Hava": "Çeşitli ve renkli besinler; hafif atıştırmalıklar ve sosyal yemek deneyimleri.",
                "Su": "Sıvı tüketimi ve deniz ürünleri; çorbalar, çaylar ve bitki bazlı beslenme."
            }
            ELEMENT_GENEL_IPUCU = {
                "spor": ELEMENT_SPOR_IPUCU,
                "sanat": ELEMENT_SANAT_IPUCU,
                "beslenme": ELEMENT_BESLENME_IPUCU,
            }
            kat_oneriler = {
                "spor": [ELEMENT_SPOR_IPUCU.get(dominan, "Düzenli egzersiz ve elementinize uygun sporlar ideal.")],
                "sanat": [ELEMENT_SANAT_IPUCU.get(dominan, "Sanatsal ifadenizi keşfetmek için farklı dalları deneyin.")],
                "hobi": ["Çocukluğunuzda keyif aldığınız aktivitelere geri dönmeyi deneyin; merak her zaman iyi bir rehberdir."],
                "saglik": ["Yılda bir kez kapsamlı sağlık kontrolünden geçmeyi ihmal etmeyin; düzenli uyku ve doğal beslenme önceliğiniz."],
                "beslenme": [ELEMENT_BESLENME_IPUCU.get(dominan, "Mevsimsel ve doğal beslenme sindirim sisteminizi dengeler.")],
                "ask": ["Partnerinizle derin ve dürüst iletişim; duygusal ihtiyaçlarınızı açıkça paylaşın."],
                "kariyer": ["Kariyer hedeflerinizi yazılı hale getirmek ve düzenli gözden geçirmek başarı şansınızı artırır."],
                "aile": ["Aile bireyleriyle düzenli zaman geçirmek ve geçmiş hikayelerini paylaşmak bağları güçlendirir."],
                "maddi": ["Bütçe planlaması ve düzenli tasarruf alışkanlığı size finansal özgürlük getirir."],
                "sosyal": ["Derin ve anlamlı ilişkiler için aktif dinleme ve empati pratiği yapın."],
                "egitim": ["Yeni bir konuyu 21 gün düzenli çalışarak alışkanlık haline getirebilirsiniz."],
                "manevi": ["Günlük 10 dakikalık sessiz meditasyon bile uzun vadede büyük farklar yaratır."],
                "seyahat": ["Seyahatlerinizi önceden planlamak ama esnek kalmak; en güzel anlar çoğu zaman plansız gelir."],
            }
            for o in kat_oneriler.get(anahtar, []):
                oneriler.append({"tur":"genel","metin":o})

            skor = max(10, min(100, skor))
            yorum = " ".join(yorum_parcalari)

            sonuclar.append({
                "anahtar": anahtar,
                "etiket": alan["etiket"],
                "icon": alan["icon"],
                "image": alan["image"],
                "skor": skor,
                "element": dominan,
                "yorum": yorum.strip(),
                "oneriler": oneriler[:8],
            })

        return sonuclar
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[HAYAT_ALANI_HATASI] {e}\n{tb}")
        return [{"anahtar":"genel","etiket":"Genel Değerlendirme","icon":"📊","skor":50,"yorum":f"Sistem şu anda analiz yapamıyor: {e}","oneriler":[]}]

def _natal_chart_yorumu(motor):
    """Natal chart interpretation as flowing narrative — like a human astrologer."""
    try:
        _EN = _i18n_get_lang() == "en"
        BURCLAR = ["Koç","Boğa","İkizler","Yengeç","Aslan","Başak","Terazi","Akrep","Yay","Oğlak","Kova","Balık"]
        EN_EV = {1:"1st",2:"2nd",3:"3rd",4:"4th",5:"5th",6:"6th",7:"7th",8:"8th",9:"9th",10:"10th",11:"11th",12:"12th"}

        jd = motor.get_natal_julian_day("p1")
        cusps, ascmc = swe.houses(jd, motor.enlem, motor.boylam, b'P')
        asc_burc = BURCLAR[int(ascmc[0] // 30)]
        mc_burc = BURCLAR[int(ascmc[1] // 30)]

        EV_ANLAM = {
            1:"kişilik ve dış görünüş", 2:"değerler ve maddi güvenlik", 3:"iletişim ve yakın çevre",
            4:"kökler ve aile", 5:"yaratıcılık ve aşk", 6:"sağlık ve günlük rutin",
            7:"ilişkiler ve ortaklıklar", 8:"dönüşüm ve ortak kaynaklar", 9:"inançlar ve yüksek öğrenim",
            10:"kariyer ve toplumsal statü", 11:"sosyal çevre ve idealler", 12:"bilinçaltı ve ruhsal yolculuk"
        }
        EV_ANLAM_EN = {
            1:"personality and outward appearance", 2:"values and material security", 3:"communication and close environment",
            4:"roots and family", 5:"creativity and love", 6:"health and daily routine",
            7:"relationships and partnerships", 8:"transformation and shared resources", 9:"beliefs and higher learning",
            10:"career and social standing", 11:"social circle and ideals", 12:"the subconscious and the spiritual journey"
        }

        gez_poz = {}
        for g_ad, g_id in list(GEZEGENLER.items())[:14]:
            try:
                deg = swe.calc_ut(jd, g_id)[0][0]
                burc_i = int(deg // 30)
                burc = BURCLAR[burc_i]
                ev = 1
                for i in range(12):
                    bas = cusps[i]; bit = cusps[(i+1)%12]
                    if bas <= bit:
                        if bas <= deg < bit: ev = i+1; break
                    else:
                        if deg >= bas or deg < bit: ev = i+1; break
                element = ["Ateş","Ateş","Toprak","Toprak","Hava","Hava","Su","Su","Ateş","Ateş","Toprak","Toprak","Hava","Hava","Su","Su"][burc_i % 6]
                gez_poz[g_ad] = {"burc": burc, "ev": ev, "derece": deg, "element": element}
            except:
                pass

        # Elements
        eleman_say = {"Ateş":0,"Toprak":0,"Hava":0,"Su":0}
        for g, p in gez_poz.items():
            e = p["element"]
            if e in eleman_say: eleman_say[e] += 1
        bask_element = max(eleman_say, key=eleman_say.get)

        # Aspects
        acilar = []
        gez_list = list(gez_poz.keys())[:12]
        for i, g1 in enumerate(gez_list):
            for j, g2 in enumerate(gez_list):
                if j <= i: continue
                if g1 not in gez_poz or g2 not in gez_poz: continue
                fark = abs(gez_poz[g1]["derece"] - gez_poz[g2]["derece"])
                if fark > 180: fark = 360 - fark
                for aci_dk, aci_ad, orb_max in [(0,"Kavuşum",7),(180,"Karşıt",7),(90,"Kare",6),(120,"Trigon",6),(60,"Sekstil",4)]:
                    if abs(fark - aci_dk) <= orb_max and fark >= 1:
                        acilar.append({"g1": g1, "g2": g2, "aci": aci_ad, "fark": round(fark, 1)})
                        break

        def _derece_str(d):
            return f"{int(d%30)}°{BURCLAR[int(d//30)]}"

        # ── PARAGRAPH 1: Overview + element + asc/mc ──
        element_acik = {
            "Ateş": "Ateş elementi ağır basıyor — doğal bir öncü ve ilham kaynağısınız. Hayatta cesur adımlar atar, içinizdeki tutkuyu dışarıya yansıtırsınız.",
            "Toprak": "Toprak elementi ağır basıyor — sağlam temeller üzerinde yükselen, güvenilir ve üretken bir yapınız var. Hayallerinizi somut adımlarla gerçeğe dönüştürüyorsunuz.",
            "Hava": "Hava elementi ağır basıyor — zihniniz sürekli aktif, fikirler üretiyor ve bağlantılar kuruyorsunuz. İletişim ve sosyal çevre hayatınızın merkezinde.",
            "Su": "Su elementi ağır basıyor — derin bir sezgisel zekaya ve empati yeteneğine sahipsiniz. Duygusal dünyanız, aldığınız kararları ve ilişkilerinizi şekillendiriyor.",
        }
        element_acik_en = {
            "Ateş": "The Fire element prevails — you are a natural pioneer and source of inspiration. You take bold steps in life and channel your inner passion outward.",
            "Toprak": "The Earth element prevails — you have a grounded, reliable and productive nature built on solid foundations. You turn your dreams into reality through concrete steps.",
            "Hava": "The Air element prevails — your mind is constantly active, generating ideas and building connections. Communication and your social circle stand at the center of your life.",
            "Su": "The Water element prevails — you possess deep intuitive intelligence and empathy. Your emotional world shapes your decisions and relationships.",
        }
        eksik_element = [e for e, s in eleman_say.items() if s == 0]
        eksik_not = ""
        if eksik_element:
            if _EN:
                _eks = {"Ateş":"Fire","Toprak":"Earth","Hava":"Air","Su":"Water"}
                eksik_not = f" Meanwhile, your chart holds no planets in the { ' and '.join(_eks.get(e, e) for e in eksik_element) } element; a conscious journey of growth may await you to bring these areas into balance."
            else:
                eksik_not = f" Öte yandan haritanızda { ' ve '.join(eksik_element) } elementinde gezegen bulunmuyor; bu alanları dengelemek için bilinçli bir gelişim yolculuğu sizi bekliyor olabilir."

        if _EN:
            par1 = f"With your Ascendant in {asc_burc} and your MC in {mc_burc}, your approach to life and your social goals take shape. {element_acik_en.get(bask_element, 'Your elemental distribution is balanced and harmonious.')}{eksik_not}"
        else:
            par1 = f"Yükselen burcunuz {asc_burc} ve MC'niz {mc_burc} ile hayata geliş tarzınız ve toplumsal hedefleriniz şekilleniyor. {element_acik.get(bask_element, 'Element dağılımınız dengeli ve uyumlu.')}{eksik_not}"

        # ── PARAGRAPH 2: Planet story ──
        ozne_gezegenler = ["Güneş","Ay","Merkür","Venüs","Mars","Jüpiter","Satürn","Uranüs","Neptün","Plüton","Chiron"]
        gez_parcalar = []
        gez_bolumler = []
        for g in ozne_gezegenler:
            if g not in gez_poz: continue
            p = gez_poz[g]
            burc = p["burc"]; ev = p["ev"]
            e_anlam = EV_ANLAM.get(ev, "hayat")
            e_anlam_en = EV_ANLAM_EN.get(ev, "life")
            DUSUK_ZARAR = {
                "Güneş": ("Terazi","Kova"), "Ay": ("Akrep","Oğlak"), "Merkür": ("Balık","Yay"),
                "Venüs": ("Başak","Akrep"), "Mars": ("Boğa","Terazi"), "Jüpiter": ("Oğlak","Başak"),
                "Satürn": ("Yengeç","Koç"), "Uranüs": ("Boğa","Aslan"), "Neptün": ("Başak","Kova"),
                "Plüton": ("Başak","Boğa"), "Chiron": ("",""),
            }
            dusuk, zarar = DUSUK_ZARAR.get(g, ("",""))
            notu = ""
            if burc == zarar: notu = (" Here its energy is challenged — an area that requires conscious effort." if _EN else " Burada enerjisi sınanıyor — bilinçli çaba gerektiren bir alan.")
            elif burc == dusuk: notu = (" Here its expression is weakened but can be restored — it can be strengthened with awareness." if _EN else " Burada ifadesi zayıflıyor ama telafisi mümkün — farkındalıkla güçlenebilir.")

            giris = {
                "Güneş": f"{g} {burc} burcunda, {ev}. evde ({e_anlam}) konumlanmış. Öz benliğiniz ve hayattaki temel amacınız bu kesişimde şekilleniyor.",
                "Ay": f"{g} {burc} burcunda, {ev}. evde ({e_anlam}) yer alıyor. Duygusal dünyanız ve içgüdüsel tepkileriniz bu konumdan besleniyor.",
                "Merkür": f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). Zihinsel yapınız ve iletişim tarzınız bu yerleşimden güç alıyor.",
                "Venüs": f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). Sevgi diliniz, estetik anlayışınız ve değer verdikleriniz bu konumun izlerini taşıyor.",
                "Mars": f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). İradeniz, tutkularınız ve mücadele enerjiniz buradan yönetiliyor.",
                "Jüpiter": f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). Şans, bolluk ve kişisel genişleme alanınız bu konumda kendini gösteriyor.",
                "Satürn": f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). Sorumluluklarınız, sınırlarınız ve en önemli hayat dersleriniz bu yerleşimde gizli.",
                "Uranüs": f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). Özgünlüğünüz, ani değişimleriniz ve isyan ettiğiniz alanlar bu konumla bağlantılı.",
                "Neptün": f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). Hayalleriniz, sezgileriniz ve manevi bağlantılarınız buradan ilham alıyor.",
                "Plüton": f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). Derin dönüşüm, güç dinamikleri ve yeniden doğuş potansiyeliniz bu konumda saklı.",
                "Chiron": f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). En derin yaranız ve aynı zamanda en büyük iyileşme gücünüz burada.",
            }.get(g, "")
            giris_en = {
                "Güneş": f"{g} is placed in {burc}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your core self and your life's fundamental purpose take shape at this intersection.",
                "Ay": f"{g} sits in {burc}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your emotional world and instinctive reactions are nourished by this placement.",
                "Merkür": f"{g} in {burc}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your mental structure and communication style draw strength from this placement.",
                "Venüs": f"{g} in {burc}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your love language, aesthetic sense and what you value bear the imprint of this position.",
                "Mars": f"{g} in {burc}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your will, passions and fighting energy are governed from here.",
                "Jüpiter": f"{g} in {burc}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your domain of luck, abundance and personal expansion reveals itself in this position.",
                "Satürn": f"{g} in {burc}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your responsibilities, limits and most important life lessons lie hidden in this placement.",
                "Uranüs": f"{g} in {burc}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your originality, sudden changes and the areas you rebel against are linked to this position.",
                "Neptün": f"{g} in {burc}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your dreams, intuitions and spiritual connections draw inspiration from here.",
                "Plüton": f"{g} in {burc}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Deep transformation, power dynamics and your potential for rebirth are stored in this position.",
                "Chiron": f"{g} in {burc}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your deepest wound and, at the same time, your greatest healing power reside here.",
            }.get(g, "")
            if giris:
                tam_metin = f"{giris}{notu}"
                if _EN:
                    tam_metin = f"{giris_en}{notu}"
                gez_parcalar.append(tam_metin)
                gez_bolumler.append({"gezegen": g, "baslik": (f"{g} — {burc}, {EN_EV.get(ev, str(ev))} House" if _EN else f"{g} — {burc}, {ev}. Ev"), "metin": tam_metin})

        # Connect first 3-4 planets with transitions, rest as separate sentences
        if len(gez_parcalar) <= 4:
            gez_parag = " ".join(gez_parcalar)
        else:
            gez_parag = " ".join(gez_parcalar[:3]) + " " + " ".join(gez_parcalar[3:])

        # ── PARAGRAPH 3: Aspects — kütüphane ile spesifik yorumlar ──
        try:
            kutuphane = _aspect_interpretasyon_kutuphanesi()
        except:
            kutuphane = {}

        aspekt_cumleleri = []
        aci_bolumler = []
        for a in acilar[:12]:
            pk = tuple(sorted([a["g1"], a["g2"]]))
            pair_key = f"{pk[0]}-{pk[1]}"
            aci = a["aci"]
            yorum = ""
            if pair_key in kutuphane and aci in kutuphane[pair_key]:
                yorum = kutuphane[pair_key][aci]
            if not yorum:
                sifa = _olumsuz_aci_sifasi(a["g1"], a["g2"], aci) if aci in ("Kare","Karşıt") else ""
                if _EN:
                    etiket = {"Kavuşum":"a union and strengthening","Trigon":"natural flow and harmony","Sekstil":"opportunity and support","Kare":"a challenge","Karşıt":"a call for balance"}
                    yorum = f"The {aci} aspect between {a['g1']} and {a['g2']} brings you {etiket.get(aci, 'some tension')}."
                else:
                    etiket = {"Kavuşum":"birleşme ve güçlenme","Trigon":"doğal akış ve uyum","Sekstil":"fırsat ve destek","Kare":"meydan okuyor","Karşıt":"denge çağrısı yapıyor"}
                    yorum = f"{a['g1']} ve {a['g2']} arasındaki {aci} açısı size {etiket.get(aci,'bir gerilim getiriyor')}."
                if sifa: yorum += f" {sifa}"
            aspekt_cumleleri.append(yorum)
            aci_bolumler.append({"baslik": f"{a['g1']} – {a['g2']} ({aci})", "metin": yorum})

        aspekt_parag = " ".join(aspekt_cumleleri) if aspekt_cumleleri else ""

        # ── PARAGRAPH 4: Arabic Parts + Asteroids ──
        diger_not = ""
        try:
            mp = motor.meslek_arap_noktasi_hesapla()
            if mp and mp.get("ruh_burc"):
                if _EN:
                    diger_not += f"Your Part of Spirit is in {mp['ruh_burc']} (the {EN_EV.get(mp['ruh_ev'], str(mp['ruh_ev']))} house) — it serves as a compass on your career and life-purpose journey. "
                else:
                    diger_not += f"Ruh noktanız {mp['ruh_burc']} burcunda ({mp['ruh_ev']}. ev) — kariyer ve yaşam amacı yolculuğunuzda size pusula görevi görüyor. "
        except: pass
        try:
            ap = motor.arap_noktasi_hesapla()
            if ap and isinstance(ap, dict):
                ilk_kisi = list(ap.keys())[0]
                if ilk_kisi and isinstance(ap.get(ilk_kisi), dict):
                    ap_list = list(ap[ilk_kisi].items())[:3]
                    eklenen = []
                    for nokta_ad, nokta_data in ap_list:
                        if isinstance(nokta_data, dict) and nokta_data.get("burc"):
                            if _EN:
                                eklenen.append(f"{nokta_ad} in {nokta_data['burc']} (the {EN_EV.get(nokta_data.get('ev'), str(nokta_data.get('ev','?')))} house)")
                            else:
                                eklenen.append(f"{nokta_ad} {nokta_data['burc']} burcunda ({nokta_data.get('ev','?')}. ev)")
                    if eklenen:
                        diger_not += (f"Among the Arabic parts, {', '.join(eklenen)} stand out. " if _EN else f"Arap noktalarından {', '.join(eklenen)} öne çıkıyor. ")
        except: pass
        try:
            ast_anahtar = {"Juno":"commitment","Ceres":"nurturing","Pallas":"wisdom","Vesta":"devotion","Eros":"passion","Psyche":"spiritual bond"} if _EN else {"Juno":"bağlılık","Ceres":"beslenme","Pallas":"bilgelik","Vesta":"adanma","Eros":"tutku","Psyche":"ruhsal bağ"}
            ast_list = []
            for ast_isim, ast_tema in ast_anahtar.items():
                ast_id = GEZEGENLER.get(ast_isim)
                if ast_id:
                    deg = swe.calc_ut(jd, ast_id)[0][0]
                    ast_burc = BURCLAR[int(deg // 30)]
                    ast_list.append(f"{ast_isim} ({ast_burc} — {ast_tema})")
            if ast_list:
                diger_not += (f"Among the asteroids, {', '.join(ast_list[:4])} carry prominent themes in your chart." if _EN else f"Asteroitlerden {', '.join(ast_list[:4])} haritanızda belirgin temalar taşıyor.")
        except: pass

        # ── Assemble ──
        paragraf = []
        paragraf.append(par1)
        paragraf.append(gez_parag)
        if aspekt_parag:
            paragraf.append(aspekt_parag)
        if diger_not:
            paragraf.append(diger_not)

        return "\n\n".join(paragraf), gez_bolumler, aci_bolumler
    except Exception as e:
        import traceback; traceback.print_exc()
        _EN_err = _i18n_get_lang() == "en"
        return (f"Chart interpretation could not be prepared: {e}" if _EN_err else f"Harita yorumu hazırlanamadı: {e}"), [], []

def _olumsuz_aci_sifasi(g1, g2, aci_turu):
    """Returns a healing suggestion for a challenging aspect — natural, varied, specific."""
    _EN = _i18n_get_lang() == "en"
    SIFA_DICT = {
        # ── Güneş ──
        ("Güneş","Satürn"): "Özgüveninizle sorumluluklarınız arasında sıkışmış hissediyorsunuz. Kendinize 'yeterli olmadığınızı' söyleyen iç sesi fark edin ve ona meydan okuyun. Küçük başarılarınızı kutlamak bu gerilimi azaltacak.",
        ("Güneş","Plüton"): "Güç mücadeleleri ve kontrol dinamikleri gündemde. Başkalarını değiştirmeye çalışmak yerine kendi gölge yönlerinizle yüzleşin. Kendi gücünüzü keşfettiğinizde dışarıdaki mücadeleler anlamını yitirecek.",
        ("Güneş","Neptün"): "Kimliğinizle ilgili bir sis perdesi aralanıyor. Kendinizi başkalarının beklentilerine göre şekillendirmekten vazgeçin. Meditasyon ve yalnız zaman geçirmek size gerçek benliğinizi hatırlatacak.",
        ("Güneş","Uranüs"): "Özgürlük ihtiyacınız sorumluluklarınızla çatışıyor. Başkaldırmak için başkaldırmak yerine, hangi kalıpların size gerçekten dar geldiğini sorgulayın. Kendi yolunuzu bulmak başkalarını reddetmekten geçmez.",
        ("Güneş","Merkür"): "Düşüncelerinizle öz benliğiniz arasında bir uyumsuzluk var. Söylediklerinizle hissettikleriniz aynı olmayabilir. Kendinize karşı dürüst olun, fikirlerinizi içinize sindirmeden paylaşmayın.",
        ("Güneş","Venüs"): "Kendinizi ifade etme biçiminizle sevgi diliniz çelişiyor olabilir. Başkalarını memnun etmek için kendi isteklerinizi geri plana atıyorsunuz. Önce kendi ihtiyaçlarınızı fark edin.",
        ("Güneş","Mars"): "İrade ile arzu arasında kalmış durumdasınız. Bir şeyi çok istiyor ama harekete geçmekten korkuyor olabilirsiniz. İlk adımı atın, gerisi kendiliğinden gelecek.",
        ("Güneş","Jüpiter"): "Kendinizi kanıtlama ihtiyacınız abartıya kaçabilir. Herkese bir şey kanıtlamaya çalışmak yerine, sadece var olmanıza izin verin. Yeterlisiniz, fazlasına gerek yok.",
        ("Güneş","KAD"): "Geçmişten gelen aile kalıpları ve atalardan miras kalan alışkanlıklar, kendi kimliğinizi kurmanızı zorlaştırıyor. Kendi yolunuzu çizmek için aile bağlarınızı reddetmeden onlardan özgürleşmeyi öğrenin. Köklerinizle barışmak sizi güçlendirecek.",
        ("Güneş","Lilith"): "Öfkenizi ve bastırılmış yönlerinizi kabul etmekte zorlanıyorsunuz. Toplumun 'uygun' bulmadığı taraflarınızı sahiplenmek sizi özgürleştirecek. Gölgenizle yüzleşmek, ışığınızı bulmanın tek yolu.",
        # ── Ay ──
        ("Ay","Satürn"): "Duygusal olarak kendinizi kısıtlanmış hissediyorsunuz. İç çocuğunuz susturulmuş olabilir. Kendinize izin verin: ağlamak, sarılmak, sıcak bir şeyler içmek. Koruyucu duvarlarınızı yavaşça indirin.",
        ("Ay","Plüton"): "Duygularınız okyanus kadar derin ve zaman zaman boğucu olabilir. Sahiplenme ve kıskançlık eğilimlerinizi fark edin. Birine bağımlı olmadan da güvende hissedebileceğinizi kendinize hatırlatın.",
        ("Ay","Neptün"): "Başkalarının enerjisini sünger gibi çekiyor, nerede siz başlayıp nerede başkaları bittiğini ayırt edemiyorsunuz. Duygusal sınırlar çizmek için her gün 10 dakika sessizlik size iyi gelecek.",
        ("Ay","Uranüs"): "Duygusal dalgalanmalarınız tahmin edilemez olabilir. Bir an mutlu, bir an huzursuz. Bu değişkenlik yaratıcılığınızın kaynağı ama aynı zamanda istikrarsızlığa da yol açabilir. Günlük rutinler size çapa olacak.",
        ("Ay","Mars"): "Tepkileriniz ani ve güçlü. Öfkenizle duygusallığınız iç içe geçmiş durumda. Bir şey sizi kızdırdığında önce derin bir nefes alın, sonra yanıt verin. Bedeninizi hareket ettirmek bu enerjiyi dönüştürecek.",
        ("Ay","Venüs"): "Duygusal ihtiyaçlarınızla keyif aldığınız şeyler arasında bir çelişki var. Sevilmek ve onaylanmak için kendinizi zorluyor olabilirsiniz. Koşulsuz sevgiyi önce kendinize gösterin.",
        ("Ay","Merkür"): "Duygularınızı kelimelere dökmekte zorlanıyorsunuz. İçinizde bir şeyler oluyor ama ifade edemiyorsunuz. Günlük yazmak ve yaratıcı yazarlık bu blokajı aşmanıza yardımcı olacak.",
        ("Ay","Jüpiter"): "Duygularınız abartıya meyilli. Küçük bir olayı büyütebilir, bir anlık üzüntüyü günlerce taşıyabilirsiniz. Gerçekçi bir perspektif geliştirmek için güvendiğiniz bir arkadaşınıza danışın.",
        ("Ay","KAD"): "Aile geçmişinizin duygusal yükünü taşıyorsunuz. Annenizden veya büyüklerinizden size miras kalan duygusal alışkanlıklar var. Bu kalıpları fark edip bilinçli seçimler yapma zamanı. Geçmişin sizi tanımlamasına izin vermeyin.",
        ("Ay","Lilith"): "Kadınlık, duygusallık ve kabul edilmeyen yönleriniz arasında bir gerilim var. Bastırdığınız duygusal tepkileriniz en beklenmedik anda yüzeye çıkabilir. Yargılanma korkusu olmadan kendinizi ifade edebileceğiniz güvenli alanlar yaratın.",
        # ── Merkür ──
        ("Merkür","Neptün"): "Zihniniz bir sis bulutunun içinde. Hayal ile gerçeği ayırt etmek zorlaşabiliyor. Düşüncelerinizi kağıda dökmek, yazmak ve çizmek size netlik kazandıracak. Sezgilerinize güvenin ama gerçeklik kontrolünü de elden bırakmayın.",
        ("Merkür","Plüton"): "Zihniniz derin ve araştırmacı ama takıntılı düşünce döngülerine de kapılabiliyor. Bir konuyu bırakmakta zorlanıyor, sürekli aynı şeyi düşünüyorsunuz. Zihninizi boşaltmak için meditasyon ve fiziksel aktivite deneyin.",
        ("Merkür","Uranüs"): "Fikirleriniz sıra dışı ve öncü ama bunları ifade ederken başkalarını geride bırakabiliyorsunuz. Ani çıkışlarınız ve beklenmedik sözleriniz ilişkilerinizi zorlayabilir. Düşüncelerinizi paylaşmadan önce bir saniye bekleyin.",
        ("Merkür","Satürn"): "Zihniniz eleştirel ve disiplinli ama aşırı karamsar da olabiliyor. Kendi düşüncelerinizi bile fazla sorguluyor, karar vermekte zorlanıyorsunuz. Mükemmel olmayan bir fikri paylaşmak, hareketsiz kalmaktan iyidir.",
        ("Merkür","Mars"): "Düşünceleriniz hızlı ve saldırgan olabilir. Tartışma sırasında kelimeler silaha dönüşebiliyor. Fikrinizi savunmak başkasını küçük düşürmek anlamına gelmez. Savaşmadan da iletişim kurabilirsiniz.",
        ("Merkür","KAD"): "Eski düşünce kalıplarınız, ailenizden devraldığınız inanç sistemleri zihninizi şekillendiriyor. Hangi inançların size ait olmadığını sorgulama zamanı. Kendi zihinsel özgürlüğünüzü ilan edin.",
        ("Merkür","Lilith"): "Söylenmemiş sözler, bastırılmış fikirler ve tabu konular zihninizi meşgul ediyor. Konuşulmayanı konuşma cesareti gösterin. Yasak olduğunu düşündüğünüz düşüncelerinizi sahiplenin.",
        # ── Venüs ──
        ("Venüs","Satürn"): "İlişkilerde mesafeli ve güvensiz hissediyorsunuz. 'Yeterince sevilmiyorum' korkusu sizi geri çekiyor. Küçük jestlerle sevginizi ifade etmeye başlayın ve karşınızdakinin dilini öğrenmeye çalışın.",
        ("Venüs","Plüton"): "İlişkileriniz yoğun ve tutkulu ama aynı zamanda sahiplenme ve kontrol içerebiliyor. Birini kaybetme korkusu, ona fazla sıkı sarılmanıza neden oluyor. Güvenmeyi öğrenmek en büyük dersiniz.",
        ("Venüs","Neptün"): "Aşkta sınırlarınız bulanık. Romantik hayalleriniz gerçekliğin önüne geçebiliyor. Birini olduğu gibi görmek yerine idealize ediyorsunuz. Gözlerinizi açın: gerçek aşk, hayal kırıklığını da içerir.",
        ("Venüs","Uranüs"): "Özgürlük ve bağlanma arasında gidip geliyorsunuz. Birine yaklaştıkça uzaklaşma ihtiyacı duyuyorsunuz. İlişkilerinizde alana ihtiyacınız olduğunu kabul edin ama bunu ifade etmeyi öğrenin.",
        ("Venüs","Mars"): "Sevgiyle tutku arasında bir denge arayışı içindesiniz. Biri kalbinizi, diğeri bedeninizi çağırıyor. Yaratıcı bir çıkış yolu — dans, resim, müzik — bu iki enerjiyi uyumlu hale getirebilir.",
        ("Venüs","KAD"): "Aile kökenlerinizdeki sevgi alışkanlıkları yetişkin ilişkilerinizi etkiliyor. Çocuklukta öğrendiğiniz sevgi dili ihtiyaçlarınızı karşılamıyor olabilir. Yeni bir sevgi dili öğrenmek için geç değil.",
        ("Venüs","Lilith"): "Cinsellik, çekim ve yasak arzu konularında içsel bir çatışma yaşıyorsunuz. Toplumun kadına veya cinselliğe dair dayattığı kalıplarla kendi gerçeğiniz arasında sıkışmış olabilirsiniz. Bedeninizi ve arzularınızı sahiplenmek sizi özgürleştirecek.",
        # ── Mars ──
        ("Mars","Satürn"): "Öfkenizi ifade etmekte zorlanıyor veya tam tersi, kontrolsüz patlamalar yaşıyorsunuz. İkisi de aynı sorunun iki yüzü: bastırma ve patlama döngüsü. Düzenli fiziksel egzersiz bu enerjiyi sağlıklı kanala yönlendirir.",
        ("Mars","Plüton"): "Öfkeniz volkanik: uzun süre sessiz, sonra yıkıcı bir patlama. Güç mücadelelerine çekiliyor, her şeyi bir savaş alanı gibi görebiliyorsunuz. Gerçek gücün kontrol etmekte değil, bırakmakta olduğunu hatırlayın.",
        ("Mars","Neptün"): "Enerjiniz dağınık, motivasyon bulmakta zorlanıyorsunuz. Nereye gitmek istediğinizi bilmiyor gibi hissediyorsunuz. Küçük ve net hedefler koyun. Adım adım ilerlemek, bir anda her şeyi başarmaya çalışmaktan daha etkili.",
        ("Mars","Uranüs"): "Ani öfke patlamaları ve dürtüsel hareketler bu açının en belirgin özelliği. Düşünmeden hareket etmek sonra pişmanlık getirebilir. Sizi tetikleyen durumları tanıyın ve tepki vermeden önce 3'e kadar sayın.",
        ("Mars","Jüpiter"): "Aşırı iyimserlik ve abartılı hareketler risk almanıza neden olabilir. Her şeyi birden istiyor, sonra tükeniyorsunuz. Hızınızı kesin, bir hedefe odaklanın ve oraya varana kadar bırakmayın.",
        ("Mars","KAD"): "Öfkenizin kökeni aile geçmişinizde olabilir. Babanız veya büyüklerinizden miras kalan bir öfke kalıbı var. Atalarınızın savaşlarını kendi hayatınızda tekrarlamak zorunda değilsiniz. Bu döngüyü fark etmek bile iyileştirici.",
        ("Mars","Lilith"): "Bastırılmış öfke ve yasak arzular vücudunuzda birikiyor. Öfkenizi ifade etmenin sağlıklı yollarını bulmak hem fiziksel hem duygusal sağlığınız için önemli. Dövüş sporları, yoğun egzersiz ve ses terapi işe yarayabilir.",
        # ── Jüpiter ──
        ("Jüpiter","Satürn"): "Genişleme ve sınırlama arasında bir salınım yaşıyorsunuz. Büyük hayaller kuruyor ama sonra kendinizi durduruyorsunuz. Mükemmel anı beklemeyin, elinizdeki imkanlarla başlayın. Sağlam temeller üzerinde yükselen hayaller gerçek olur.",
        ("Jüpiter","Plüton"): "Güç, bolluk ve kontrol iç içe geçmiş durumda. Daha fazlasına sahip olma arzusu sizi tüketebilir. Gerçek bolluk, sahip olduklarınızın kıymetini bilmekten geçer. Paylaştıkça çoğalacağınızı hatırlayın.",
        ("Jüpiter","Neptün"): "Sınır tanımayan iyimserlik sizi gerçekçi olmaktan uzaklaştırabilir. Her şeyin güzel olacağına o kadar inanıyorsunuz ki, tehlike işaretlerini görmüyorsunuz. Denge: hayal etmek ve gerçekçi olmak arasında bir orta yol bulun.",
        ("Jüpiter","Uranüs"): "Özgürlük ve macera arzunuz o kadar güçlü ki istikrarı tamamen göz ardı edebiliyorsunuz. Ani kararlar, plansız atılımlar sonra pişmanlık getirebilir. Özgürlük sorumsuzluk demek değildir, ikisini birbirine karıştırmayın.",
        ("Jüpiter","KAD"): "Ailenizden size miras kalan inanç sistemleriyle kendi hayalleriniz arasında sıkışmış olabilirsiniz. 'Biz böyle yapmayız' kalıplarını sorgulayın. Atalarınızın sınırlamaları sizin sınırlarınız değil.",
        ("Jüpiter","Lilith"): "Yasak bilgi, tabu konular ve bastırılmış gerçekler size çekici geliyor. Toplumun 'aşırı' veya 'uygunsuz' bulduğu şeylere ilgi duyuyorsunuz. Bu merakınızı yaratıcı ve yapıcı alanlara yönlendirin.",
        # ── Satürn ──
        ("Satürn","Uranüs"): "Gelenekle devrim arasında sıkışmış durumdasınız. Bir yandan güvende olmak istiyor, diğer yandan özgür. Köklü bir değişim yapmadan önce küçük yenilikler deneyin. Eski kalıpları birden yıkmak yerine dönüştürün.",
        ("Satürn","Neptün"): "Sorumluluklarınızla hayalleriniz arasında bir çatışma var. Birine ne kadar yaklaşırsanız diğeri o kadar uzaklaşıyor. Sorumluluklarınızı ihmal etmeden hayallerinizin peşinden gitmenin bir yolunu bulun.",
        ("Satürn","Plüton"): "Hayatın en ağır dersleriyle yüzleşiyorsunuz: kayıp, kontrol, güç. Bu açı size dayanıklılık öğretiyor ama aynı zamanda katılaştırabiliyor. Yumuşamak güçsüzlük değil, olgunluğun işaretidir.",
        ("Satürn","KAD"): "Aile geçmişinizden gelen sorumluluk yükünü taşıyorsunuz. Atalarınızın çözülmemiş sorunları sizin omuzlarınızda olabilir. Bu yükü bırakmak size ihanet gibi geliyor, ama asıl ihanet kendi hayatınızı yaşamamak.",
        ("Satürn","Lilith"): "Bastırılmış duygular, yasak kabul edilen yönleriniz sorumluluk duvarlarınızın ardında sıkışmış durumda. Kim olduğunuzu tam olarak gösteremediğiniz için içinizde bir sıkışma hissediyorsunuz. Gölgenizi kucaklamak sizi özgürleştirecek.",
        # ── Chiron ──
        ("Chiron","Satürn"): "En derin yaranız sorumluluk ve yetersizlik hissiyle bağlantılı. 'Asla yeterli değilim' inancı iyileşmenizi engelliyor. Kusurlarınızın sizi insan yaptığını kabul edin. Mükemmel olmak zorunda değilsiniz.",
        ("Chiron","Plüton"): "Geçmiş travmalar ve dönüşüm arasında bir köprüdesiniz. En çok acıdığınız yerde en büyük iyileşme potansiyeli yatıyor. Bunun için yalnız başınıza yapmak zorunda değilsiniz, profesyonel destek alın.",
        ("Chiron","Neptün"): "İyileşme arzunuz var ama bunu nasıl yapacağınızı bilmiyorsunuz. Kaçış yolları arıyor, bağımlılıklara yönelebiliyorsunuz. Gerçek iyileşme, acınızla yüzleşmekten geçer, ondan kaçmaktan değil.",
        ("Chiron","KAD"): "Aile geçmişinizde iyileşmemiş bir yara size miras kalmış olabilir. Bu, sizin kendi yaranız gibi hissettirse de aslında atalarınızdan geliyor olabilir. Bu döngüyü kırmak sizin elinizde, bu sizin kader yolculuğunuzun bir parçası.",
        ("Chiron","Lilith"): "Reddedilme, dışlanma ve kabul görmeme korkusu en hassas noktanız. 'Fazla' olduğunuzu hissediyorsunuz. Oysa sizi farklı kılan şey tam da iyileşme gücünüz. Dışlanmış hissettiğiniz her alanda başkalarına şifa olabilirsiniz.",
        # ── KAD + Lilith ──
        ("KAD","Lilith"): "Geçmişin gölgesiyle bugünün bastırılmış yönleri birleşince güçlü bir karmik yük ortaya çıkıyor. Atalarınızdan miras kalan susturulmuş hikayeler var. Bu suskunluğu bozmak, hem kendinizi hem soyunuzu özgürleştirecek.",
        ("KAD","Plüton"): "Aile geçmişinizde güç mücadeleleri, miras kavgaları veya travmatik kayıplar olabilir. Bu yoğun enerji bilinçaltınızda dolaşıyor. Aile sırlarını gün yüzüne çıkarmak korkutucu gelebilir ama bu, özgürleşmenizin anahtarı.",
        ("KAD","Neptün"): "Aile geçmişinizde çözülmemiş bir kurbanlık hikayesi, fedakarlık veya hayal kırıklığı olabilir. Kendinizi başkaları için feda etme eğiliminiz buradan geliyor. Fedakarlık sevgi değildir. Önce kendinize iyi bakın.",
        ("KAD","Uranüs"): "Aile kalıplarıyla bağımsızlığınız arasında bir savaş veriyorsunuz. Size dayatılan geleneksel rolleri reddediyor ama tamamen de kopamıyorsunuz. Özgürleşmek reddetmek değil, kendi seçiminizi yapmaktır.",
        ("Lilith","Plüton"): "Bastırılmış cinsellik, yasak arzular ve gölge dürtüler derin bir dönüşüm çağrısı yapıyor. En çok utandığınız yönleriniz, en büyük gücünüzü barındırıyor. Karanlık yanınızla barışmak sizi bütünleyecek.",
        ("Lilith","Neptün"): "Kurban-kurtarıcı döngüsü içinde kaybolmuş olabilirsiniz. Başkalarını kurtarmaya çalışırken kendinizi kaybediyorsunuz. Ya da bir kurtarıcı bekliyorsunuz. Gerçek kurtuluşun başkasında değil, kendi içinizde olduğunu fark edin.",
        ("Uranüs","Lilith"): "İsyan ve bastırılmış arzular iç içe geçmiş durumda. Kurallara karşı gelmek sizi özgürleştirmiyor, sadece daha çok sıkıştırıyor. Asıl özgürlük, kendi sınırlarınızı kendinizin belirlemesinde. Dışarıdaki otoriteyle savaşmak yerine içinizdeki otoriteyi sorgulayın.",
        ("Uranüs","KAD"): "Aile geçmişinizden kopma isteğiyle aidiyet ihtiyacınız arasında sıkışmış hissediyorsunuz. Köklerinizle bağlarınızı tamamen koparmak yerine, onları kendi ihtiyaçlarınıza göre yeniden tanımlayın. Aidiyet teslimiyet değildir.",
        ("Lilith","Mars"): "Öfkeniz ve bastırılmış yönleriniz arasında bir bağ var. Kendinizi ifade etmenin 'yasak' olduğuna inandığınız bir alanda harekete geçmekten korkuyorsunuz. Bedeninizi hareket ettirmek ve sesinizi yükseltmek bu zincirleri kıracak.",
        # ── Ek yaygın çiftler ──
        ("Venüs","Jüpiter"): "Aşırı hoşgörü ve abartılı beklentiler ilişkilerinizde dengesizlik yaratabilir. Herkese yetişmeye, herkesi memnun etmeye çalışıyorsunuz. Hayır demeyi öğrenmek bu enerjiyi dengeleyecek.",
        ("Merkür","Venüs"): "Ne söyleyeceğinizle ne hissettiğiniz arasında bir uyumsuzluk var. İltifat ederken samimiyetsiz ya da eleştirirken fazla sert olabilirsiniz. Kalbinizden geçenle dilinizden çıkanı aynı hizaya getirin.",
        ("Ay","Jüpiter"): "Duygusal tepkileriniz büyük ve geniş kapsamlı. Küçük bir mutluluk sizi coştururken, küçük bir hayal kırıklığı yerle bir edebiliyor. Duygusal iniş çıkışlarınızı dengelemek için nefes egzersizleri ve topraklama teknikleri deneyin.",
        ("Mars","Jüpiter"): "Risk almayı seviyorsunuz ama bazen aşırıya kaçabiliyor. 'Ya hep ya hiç' yaklaşımınız sizi yakabilir. Büyük resmi görmek güzel ama adım adım ilerlemek daha kalıcı sonuçlar getirecek.",
        ("Güneş","Ay"): "Kimliğinizle duygusal dünyanız çatışıyor. Biri bir şey isterken diğeri başka bir şey istiyor. İçsel bütünlük için bu iki parçayı uzlaştırmalısınız. İkisini de dinleyin, birini tercih etmeyin.",
    }

    SIFA_DICT_EN = {
        ("Güneş","Satürn"): "You feel trapped between your self-confidence and your responsibilities. Notice the inner voice telling you that you are 'not enough' and challenge it. Celebrating your small wins will ease this tension.",
        ("Güneş","Plüton"): "Power struggles and control dynamics are on your agenda. Instead of trying to change others, face your own shadow sides. Once you discover your own power, the struggles outside will lose their meaning.",
        ("Güneş","Neptün"): "A veil of fog is lifting around your identity. Stop shaping yourself to others' expectations. Meditation and time alone will remind you of your true self.",
        ("Güneş","Uranüs"): "Your need for freedom clashes with your responsibilities. Instead of rebelling for its own sake, question which patterns truly feel too tight for you. Finding your own path does not require rejecting others.",
        ("Güneş","Merkür"): "There is a mismatch between your thoughts and your core self. What you say and what you feel may not align. Be honest with yourself, and do not share ideas you have not fully made your own.",
        ("Güneş","Venüs"): "Your way of expressing yourself and your love language may contradict. To please others, you push your own desires aside. First, recognize your own needs.",
        ("Güneş","Mars"): "You are caught between will and desire. You may want something intensely yet fear taking action. Take the first step; the rest will follow.",
        ("Güneş","Jüpiter"): "Your need to prove yourself can go to extremes. Instead of trying to prove something to everyone, allow yourself simply to exist. You are enough; nothing more is needed.",
        ("Güneş","KAD"): "Family patterns from the past and habits inherited from your ancestors make it difficult to build your own identity. To chart your own path, learn to free yourself from family ties without rejecting them. Making peace with your roots will strengthen you.",
        ("Güneş","Lilith"): "You struggle to accept your anger and your repressed sides. Claiming the parts of you that society deems 'inappropriate' will set you free. Facing your shadow is the only way to find your light.",
        ("Ay","Satürn"): "Emotionally, you feel restricted. Your inner child may have been silenced. Allow yourself: cry, hug, drink something warm. Lower your protective walls, slowly.",
        ("Ay","Plüton"): "Your emotions are as deep as an ocean and sometimes suffocating. Notice your possessive and jealous tendencies. Remind yourself that you can feel safe without depending on someone.",
        ("Ay","Neptün"): "You absorb others' energy like a sponge and cannot tell where you end and others begin. Ten minutes of silence each day will help you draw emotional boundaries.",
        ("Ay","Uranüs"): "Your emotional swings can be unpredictable — happy one moment, restless the next. This volatility is the source of your creativity but can also lead to instability. Daily routines will anchor you.",
        ("Ay","Mars"): "Your reactions are sudden and strong. Your anger and your sensitivity are intertwined. When something upsets you, take a deep breath before responding. Moving your body will transform this energy.",
        ("Ay","Venüs"): "There is a contradiction between your emotional needs and what pleases you. You may be forcing yourself to be loved and approved. Show yourself unconditional love first.",
        ("Ay","Merkür"): "You struggle to put your feelings into words. Something stirs inside you, yet you cannot express it. Keeping a journal and creative writing will help you break through this block.",
        ("Ay","Jüpiter"): "Your emotions tend toward exaggeration. You may magnify a small event or carry a moment's sadness for days. Consult someone you trust to develop a realistic perspective.",
        ("Ay","KAD"): "You carry the emotional weight of your family history. Emotional habits were bequeathed to you by your mother or your elders. It is time to notice these patterns and make conscious choices. Do not let the past define you.",
        ("Ay","Lilith"): "There is tension between your femininity, your sensitivity and the sides of you that go unaccepted. Your repressed emotional responses may surface at the most unexpected moments. Create safe spaces where you can express yourself without fear of judgment.",
        ("Merkür","Neptün"): "Your mind dwells in a cloud of fog. Distinguishing dream from reality grows difficult. Putting your thoughts on paper — writing and drawing — will bring you clarity. Trust your intuition, but never let go of reality checks.",
        ("Merkür","Plüton"): "Your mind is deep and investigative, but it can also fall into obsessive thought loops. You struggle to let a subject go and keep replaying the same idea. Try meditation and physical activity to empty your mind.",
        ("Merkür","Uranüs"): "Your ideas are unconventional and pioneering, but you can leave others behind when expressing them. Your sudden outbursts and unexpected remarks may strain relationships. Pause for a second before sharing your thoughts.",
        ("Merkür","Satürn"): "Your mind is critical and disciplined but can turn excessively pessimistic. You over-question even your own thoughts and struggle to decide. Sharing an imperfect idea is better than staying still.",
        ("Merkür","Mars"): "Your thoughts can be quick and aggressive. In argument, words can become weapons. Defending your view does not mean belittling someone else. You can communicate without fighting.",
        ("Merkür","KAD"): "Old thought patterns — belief systems inherited from your family — shape your mind. It is time to question which beliefs are not truly yours. Declare your mental freedom.",
        ("Merkür","Lilith"): "Unspoken words, repressed ideas and taboo subjects occupy your mind. Find the courage to speak the unspoken. Own the thoughts you believed were forbidden.",
        ("Venüs","Satürn"): "You feel distant and insecure in relationships. The fear of 'not being loved enough' pulls you back. Start expressing your love through small gestures and try to learn the other person's language.",
        ("Venüs","Plüton"): "Your relationships are intense and passionate, yet they can carry possessiveness and control. The fear of losing someone makes you cling too tightly. Learning to trust is your greatest lesson.",
        ("Venüs","Neptün"): "Your boundaries in love are blurred. Romantic dreams can override reality. Instead of seeing someone as they are, you idealize them. Open your eyes: true love also includes disappointment.",
        ("Venüs","Uranüs"): "You oscillate between freedom and attachment. The closer you get to someone, the more you feel the need to pull away. Accept that you need space in your relationships — and learn to say so.",
        ("Venüs","Mars"): "You are searching for a balance between love and passion. One calls to your heart, the other to your body. A creative outlet — dance, painting, music — can bring these two energies into harmony.",
        ("Venüs","KAD"): "The habits of love in your family roots affect your adult relationships. The love language you learned in childhood may no longer meet your needs. It is never too late to learn a new love language.",
        ("Venüs","Lilith"): "You experience inner conflict around sexuality, attraction and forbidden desire. You may feel trapped between society's scripts about women and sex and your own truth. Owning your body and desires will set you free.",
        ("Mars","Satürn"): "You struggle to express anger, or you experience uncontrolled outbursts — two faces of the same problem: a cycle of suppression and explosion. Regular physical exercise channels this energy healthily.",
        ("Mars","Plüton"): "Your anger is volcanic: silent for a long time, then a destructive eruption. You get drawn into power struggles and can treat everything as a battlefield. Remember that real power lies not in control but in letting go.",
        ("Mars","Neptün"): "Your energy is scattered; you struggle to find motivation. You feel you do not know where you are heading. Set small, clear goals. Moving step by step is more effective than trying to achieve everything at once.",
        ("Mars","Uranüs"): "Sudden outbursts of anger and impulsive actions are the most prominent feature of this aspect. Acting without thinking can bring regret. Recognize your triggers and count to three before reacting.",
        ("Mars","Jüpiter"): "Excessive optimism and exaggerated moves can lead you to take risks. You want everything at once, then burn out. Slow down, focus on a single goal, and do not let go until you reach it.",
        ("Mars","KAD"): "The roots of your anger may lie in your family history. There is a pattern of anger inherited from your father or elders. You do not have to repeat your ancestors' battles in your own life. Simply recognizing this cycle is healing.",
        ("Mars","Lilith"): "Repressed anger and forbidden desires accumulate in your body. Finding healthy ways to express anger matters for both your physical and emotional health. Martial arts, intense exercise and voice therapy can help.",
        ("Jüpiter","Satürn"): "You swing between expansion and restriction. You build grand dreams, then stop yourself. Do not wait for the perfect moment; start with what you have. Dreams that rise on solid foundations come true.",
        ("Jüpiter","Plüton"): "Power, abundance and control are intertwined. The desire to have more can consume you. True abundance comes from appreciating what you have. Remember that what you share multiplies.",
        ("Jüpiter","Neptün"): "Boundless optimism can pull you away from being realistic. You believe so strongly that everything will be fine that you miss the warning signs. Balance: find a middle ground between dreaming and being realistic.",
        ("Jüpiter","Uranüs"): "Your desire for freedom and adventure is so strong that you can overlook stability entirely. Sudden decisions and unplanned moves can bring regret. Freedom is not irresponsibility; do not confuse the two.",
        ("Jüpiter","KAD"): "You may feel trapped between the belief systems inherited from your family and your own dreams. Question the 'this is how we do things' patterns. Your ancestors' limits are not your limits.",
        ("Jüpiter","Lilith"): "Forbidden knowledge, taboo subjects and repressed truths attract you. You are drawn to what society deems 'excessive' or 'inappropriate'. Channel this curiosity into creative and constructive fields.",
        ("Satürn","Uranüs"): "You are stuck between tradition and revolution. You want security on one hand and freedom on the other. Before making a radical change, try small innovations. Transform old patterns instead of tearing them down overnight.",
        ("Satürn","Neptün"): "There is a conflict between your responsibilities and your dreams. The closer you get to one, the further the other drifts. Find a way to pursue your dreams without neglecting your duties.",
        ("Satürn","Plüton"): "You are confronting life's heaviest lessons: loss, control, power. This aspect teaches you endurance but can also harden you. Softening is not weakness; it is a sign of maturity.",
        ("Satürn","KAD"): "You carry the burden of responsibility from your family history. Your ancestors' unresolved issues may rest on your shoulders. Putting this burden down may feel like betrayal, but the real betrayal is not living your own life.",
        ("Satürn","Lilith"): "Repressed emotions and the sides of you deemed forbidden are trapped behind your walls of responsibility. Because you cannot fully show who you are, you feel constricted inside. Embracing your shadow will set you free.",
        ("Chiron","Satürn"): "Your deepest wound is tied to responsibility and a sense of inadequacy. The belief 'I am never enough' blocks your healing. Accept that your flaws are what make you human. You do not have to be perfect.",
        ("Chiron","Plüton"): "You stand on a bridge between past trauma and transformation. The place that hurts most holds your greatest healing potential. You do not have to do this alone — seek professional support.",
        ("Chiron","Neptün"): "You long to heal but do not know how. You search for escape routes and may turn toward dependencies. True healing comes from facing your pain, not fleeing it.",
        ("Chiron","KAD"): "An unhealed wound may have been inherited from your family history. It may feel like your own, yet it could come from your ancestors. Breaking this cycle is in your hands; it is part of your destiny journey.",
        ("Chiron","Lilith"): "The fear of rejection, exclusion and not being accepted is your most tender point. You feel 'too much'. Yet what makes you different is precisely your healing power. Wherever you feel excluded, you can be a healer to others.",
        ("KAD","Lilith"): "When the shadow of the past meets today's repressed sides, a powerful karmic weight emerges. There are silenced stories inherited from your ancestors. Breaking this silence will liberate both you and your lineage.",
        ("KAD","Plüton"): "There may have been power struggles, inheritance feuds or traumatic losses in your family history. This intense energy circulates in your subconscious. Unearthing family secrets can be frightening, but it is the key to your liberation.",
        ("KAD","Neptün"): "There may be an unresolved story of victimhood, sacrifice or disappointment in your family history. Your tendency to sacrifice yourself for others originates here. Sacrifice is not love. Take care of yourself first.",
        ("KAD","Uranüs"): "You are fighting a battle between family patterns and your independence. You reject the traditional roles imposed on you yet cannot fully break away. Liberation is not rejection; it is making your own choice.",
        ("Lilith","Plüton"): "Repressed sexuality, forbidden desires and shadow impulses call for deep transformation. The sides of you you most shame hold your greatest power. Making peace with your dark side will make you whole.",
        ("Lilith","Neptün"): "You may be lost in a victim-redeemer cycle. While trying to save others, you lose yourself — or you wait for a savior. Recognize that true salvation lies not in someone else but within you.",
        ("Uranüs","Lilith"): "Rebellion and repressed desires are intertwined. Breaking the rules does not free you; it only constricts you more. True freedom lies in setting your own boundaries. Instead of fighting external authority, question the authority within you.",
        ("Uranüs","KAD"): "You feel squeezed between the urge to break away from your family past and the need to belong. Rather than severing your ties to your roots, redefine them according to your own needs. Belonging is not surrender.",
        ("Lilith","Mars"): "There is a bond between your anger and your repressed sides. You fear acting in an area where you believe self-expression is 'forbidden'. Moving your body and raising your voice will break these chains.",
        ("Venüs","Jüpiter"): "Excess indulgence and exaggerated expectations can create imbalance in your relationships. You try to keep up with everyone and please everyone. Learning to say no will balance this energy.",
        ("Merkür","Venüs"): "There is a mismatch between what you say and what you feel. You can be insincere when complimenting or too harsh when criticizing. Bring what is in your heart and what comes from your tongue into alignment.",
        ("Ay","Jüpiter"): "Your emotional reactions are big and sweeping. A small joy excites you, while a small disappointment can flatten you. Try breathing exercises and grounding techniques to balance your emotional ups and downs.",
        ("Mars","Jüpiter"): "You love taking risks, but sometimes you go overboard. Your 'all or nothing' approach can burn you. Seeing the big picture is good, but moving step by step brings more lasting results.",
        ("Güneş","Ay"): "Your identity and emotional world conflict. One wants one thing while the other wants another. You must reconcile these two parts for inner wholeness. Listen to both; do not favor one.",
    }
    key = (g1, g2)
    rev_key = (g2, g1)
    sifa_dict = SIFA_DICT_EN if _EN else SIFA_DICT
    if key in sifa_dict: return sifa_dict[key]
    if rev_key in sifa_dict: return sifa_dict[rev_key]
    # Varied generic fallbacks
    import random
    rng = random.Random(g1 + g2 + aci_turu)
    generic_kare = [
        f"{g1} ile {g2} arasındaki kare açısı ikisi arasında bir gerilim yaratıyor. Bu enerjiyi bastırmak yerine, ikisinin de size ne söylediğini dinleyin. Biri diğerini yok etmek zorunda değil.",
        f"{g1} ve {g2} arasındaki bu zorlayıcı açı, bir alışkanlığınızı sorgulamanızı istiyor. İkisinin çatıştığı noktada aslında büyüme fırsatınız yatıyor. Sizi neyin rahatsız ettiğine yakından bakın.",
        f"Bu kare açı, {g1} ve {g2} enerjilerini uyumlu hale getirmeniz için bir sınav. Birini seçmek zorunda değilsiniz, ikisini de kucaklayabilirsiniz. Önemli olan aralarındaki dengeyi bulmak.",
        f"{g1} ile {g2} arasındaki gerilim, içinizde bir şeylerin değişmesi gerektiğini söylüyor. Bu rahatsızlık hissine kulak verin. Eski alışkanlıklarınızı bırakma zamanı gelmiş olabilir.",
        f"{g1} ve {g2} arasındaki kare, sizi konfor alanınızın dışına itiyor. Zorlayıcı ama bir o kadar da öğretici bir döngüdesiniz. Bu gerilimi yaratıcı bir projeye kanalize etmeyi deneyin.",
    ]
    generic_karsit = [
        f"{g1} ve {g2} arasındaki karşıt açı, iki ayrı kutup arasında gidip gelmenize neden oluyor. Bir denge noktası bulmak için her iki tarafa da eşit mesafede durmayı öğrenin.",
        f"{g1} ile {g2} arasındaki bu karşıtlık, aslında bir yansıtma mekanizmasını işaret ediyor. Karşınızda gördüğünüz şey, kendi içinizde kabul etmediğiniz bir parçanız olabilir.",
        f"Bu karşıt açı, {g1} ve {g2} alanlarında bir taraf seçmeye zorlanıyormuş gibi hissettirebilir. Oysa asıl mesele, her iki alanı da hayatınızda tutabilmenin bir yolunu bulmak.",
        f"{g1} ile {g2} arasında bir çekim-itiş dinamiği var. Yaklaştıkça uzaklaşıyor, uzaklaştıkça özlüyorsunuz. Bu döngüyü kırmak için her iki enerjiyi de kucaklayacak bir orta yol bulun.",
        f"{g1} ve {g2} arasındaki karşıtlık, bir ilişkide veya durumda denge arayışınızı simgeliyor. Siyah-beyaz düşünmek yerine gri alanları keşfedin. Gerçek çözüm, ikisinin de ötesinde.",
    ]
    generic_kare_en = [
        f"The square between {g1} and {g2} creates tension between the two. Instead of suppressing this energy, listen to what each is telling you. One does not have to destroy the other.",
        f"This demanding aspect between {g1} and {g2} asks you to question a habit. Where the two conflict actually lies your growth opportunity. Look closely at what disturbs you.",
        f"This square is a test for harmonizing the energies of {g1} and {g2}. You do not have to choose one; you can embrace both. What matters is finding the balance between them.",
        f"The tension between {g1} and {g2} says something inside you must change. Listen to this discomfort. It may be time to release old habits.",
        f"The square between {g1} and {g2} pushes you beyond your comfort zone. This is a demanding yet deeply instructive cycle. Try channeling this tension into a creative project.",
    ]
    generic_karsit_en = [
        f"The opposition between {g1} and {g2} makes you swing between two separate poles. To find a point of balance, learn to stand at equal distance from both sides.",
        f"This opposition between {g1} and {g2} points to a mechanism of projection. What you see in front of you may be a part of yourself you do not accept.",
        f"This opposing aspect can make you feel forced to choose a side in the realms of {g1} and {g2}. Yet the real matter is finding a way to keep both areas in your life.",
        f"There is an attraction-repulsion dynamic between {g1} and {g2}. The closer you get, the further you drift; the further you drift, the more you long. To break this cycle, find a middle path that embraces both energies.",
        f"The opposition between {g1} and {g2} symbolizes your search for balance in a relationship or situation. Instead of black-and-white thinking, explore the gray areas. The real solution lies beyond both.",
    ]
    if _EN:
        generic_kare = generic_kare_en
        generic_karsit = generic_karsit_en
    if aci_turu == "Kare":
        return rng.choice(generic_kare)
    elif aci_turu == "Karşıt":
        return rng.choice(generic_karsit)
    return ""

def _natal_sifa_receteleri(motor):
    """Expanded healing prescriptions for negative aspects + fallen/detriment planets."""
    _EN = _i18n_get_lang() == "en"
    try:
        BURCLAR = ["Koç","Boğa","İkizler","Yengeç","Aslan","Başak","Terazi","Akrep","Yay","Oğlak","Kova","Balık"]
        BURCLAR_EN = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

        jd = motor.get_natal_julian_day("p1")
        cusps, ascmc = swe.houses(jd, motor.enlem, motor.boylam, b'P')

        gez_poz = {}
        for g_ad, g_id in list(GEZEGENLER.items())[:14]:
            try:
                deg = swe.calc_ut(jd, g_id)[0][0]
                burc = BURCLAR[int(deg // 30)]
                gez_poz[g_ad] = {"burc": burc, "derece": deg}
            except: pass

        # Fall & detriment positions
        DUSUK_ZARAR = {
            "Güneş": ("Terazi","Kova"), "Ay": ("Akrep","Oğlak"), "Merkür": ("Balık","Yay"),
            "Venüs": ("Başak","Akrep"), "Mars": ("Boğa","Terazi"), "Jüpiter": ("Oğlak","Başak"),
            "Satürn": ("Yengeç","Koç"), "Uranüs": ("Boğa","Aslan"), "Neptün": ("Başak","Kova"),
            "Plüton": ("Başak","Boğa"),
        }
        SAGALTIM_TEKNIKLERI = {
            "Güneş": {"Terazi": "Kendinize değer vermeyi öğrenin. Onaylanma ihtiyacınızı fark edin ve içinizdeki ışığı dışarıdan onay beklemeden parlatın. Güneşe selam (Surya Namaskar) ve özgüven afirmasyonları.", "Kova": "Özgünlüğünüzü kucaklayın ama topluluktan tamamen kopmayın. Benzersiz yeteneklerinizi başkalarıyla paylaşmanın yollarını bulun. Meditasyon ve topluluk çalışmaları."},
            "Ay": {"Akrep": "Duygusal yoğunluğunuzu yaratıcı alanlara yönlendirin. Günlük tutmak, duygularınızı yazmak ve sanatla ifade etmek size iyi gelecek. Su kenarında vakit geçirin.", "Oğlak": "Duygularınızı ifade etmekte zorlanıyorsunuz. İç dünyanıza dönmek ve kendinize şefkat göstermek için her gün 10 dakika ayırın. Bitki çayları ve sıcak banyo rahatlatıcı."},
            "Merkür": {"Balık": "Düşünceleriniz dağınık hissedebilir. Günlük yazma pratiği ve zihin haritaları size odaklanma konusunda yardımcı olacak. Sessiz ortamda çalışmayı deneyin.", "Yay": "Fikirlerinizi paylaşmadan önce daha fazla araştırma yapın. Detaylara dikkat etmek ve sabırla dinlemek sizi daha etkili bir iletişimci yapacak."},
            "Venüs": {"Başak": "Mükemmel aşkı aramaktan vazgeçin. Küçük kusurları kabul etmek ve gerçekçi beklentiler geliştirmek ilişkilerinizi iyileştirecek. Kendinize bir çiçek alın veya güzel bir ortam yaratın.", "Akrep": "İlişkilerde sahiplenme ve kıskançlık eğilimlerinizi fark edin. Güven egzersizleri yapın ve partnerinize alan tanıyın. Dans etmek duygusal blokajları çözer."},
            "Mars": {"Boğa": "Öfkenizi bastırmak yerine fiziksel aktiviteyle sağlıklı şekilde ifade edin. Topraklama egzersizleri ve doğa yürüyüşleri enerjinizi dengeleyecek.", "Terazi": "Pasif-agresif davranışlardan kaçının. İhtiyaçlarınızı net ve nazikçe ifade etmeyi öğrenin. Yoga ve nefes çalışmaları öfke yönetimine yardımcı."},
            "Jüpiter": {"Oğlak": "Büyük hayallerinizi gerçekleştirmek için disiplinli bir plan oluşturun. Bolluk bilinci affirmasyonları yapın ve minnettarlık günlüğü tutun.", "Başak": "Mükemmeliyetçiliğinizin sizi büyük resimden alıkoymasına izin vermeyin. Riski tolere etmeyi öğrenin ve her küçük başarıyı kutlayın."},
            "Satürn": {"Yengeç": "Duygusal güvenlik ihtiyacınız sorumluluklarınızla çatışabilir. Aile geçmişinizle yüzleşmek ve duygusal olarak güçlenmek size özgürlük getirecek.", "Koç": "Sabır en büyük dersiniz. Hızlı sonuç beklemek yerine sürece güvenin. Kemik suyu, kalsiyum takviyeleri ve düzenli rutin size iyi gelir."},
            "Uranüs": {"Boğa": "Değişime direnmek yerine küçük adımlarla yeniliklere açılın. Rutininizde küçük değişiklikler yapmak büyük dönüşümün kapısını aralayacak.", "Aslan": "Özgünlüğünüzü ifade etmekten korkmayın. Yaratıcı projelerde ani ilhamları takip edin. Elektrik mavisi ve mor renkler titreşiminizi yükseltir."},
            "Neptün": {"Başak": "Maneviyatınızı pratik bir temele oturtun. Meditasyonu günlük rutininize ekleyin. Kristaller (ametist, lapis lazuli) ve tütsü odaklanmanıza yardımcı olur.", "Kova": "Hayallerinizi gerçekleştirmek için bir topluluk bulun. İdealist enerjinizi pratik projelere dönüştürmek sizi topraklayacak."},
            "Plüton": {"Başak": "Kontrol ihtiyacınızı bırakmak en büyük dönüşümünüz olacak. Detaylara takılmak yerine büyük resme odaklanın. Derin nefes çalışmaları dönüşümü kolaylaştırır.", "Boğa": "Sahiplenme ve kontrol dürtülerinizi fark edin. Bir şeyleri bırakmak, kaybetmek korkunuzla yüzleşin. Bağışlama ve şükür pratikleri dönüşümü hızlandırır."},
        }
        SAGALTIM_TEKNIKLERI_EN = {
            "Güneş": {"Terazi": "Learn to value yourself. Notice your need for approval and let your inner light shine without waiting for external validation. Sun salutations (Surya Namaskar) and self-confidence affirmations.", "Kova": "Embrace your uniqueness, but do not completely cut off from community. Find ways to share your unique gifts with others. Meditation and community work."},
            "Ay": {"Akrep": "Channel your emotional intensity into creative fields. Journaling, writing your feelings and expressing through art will do you good. Spend time near water.", "Oğlak": "You struggle to express your emotions. Set aside ten minutes each day to turn inward and show yourself compassion. Herbal teas and warm baths are soothing."},
            "Merkür": {"Balık": "Your thoughts may feel scattered. Daily writing practice and mind maps will help you focus. Try working in a quiet environment.", "Yay": "Do more research before sharing your ideas. Paying attention to details and listening patiently will make you a more effective communicator."},
            "Venüs": {"Başak": "Stop searching for perfect love. Accepting small flaws and developing realistic expectations will improve your relationships. Buy yourself a flower or create a beautiful environment.", "Akrep": "Notice your possessive and jealous tendencies in relationships. Do trust exercises and give your partner space. Dancing dissolves emotional blockages."},
            "Mars": {"Boğa": "Instead of suppressing your anger, express it healthily through physical activity. Grounding exercises and nature walks will balance your energy.", "Terazi": "Avoid passive-aggressive behavior. Learn to express your needs clearly and kindly. Yoga and breathing work help with anger management."},
            "Jüpiter": {"Oğlak": "Create a disciplined plan to realize your big dreams. Do abundance affirmations and keep a gratitude journal.", "Başak": "Do not let perfectionism keep you from the big picture. Learn to tolerate risk and celebrate every small success."},
            "Satürn": {"Yengeç": "Your need for emotional security can conflict with your responsibilities. Facing your family history and becoming emotionally stronger will bring you freedom.", "Koç": "Patience is your greatest lesson. Instead of expecting quick results, trust the process. Bone broth, calcium supplements and a regular routine do you good."},
            "Uranüs": {"Boğa": "Instead of resisting change, open up to innovation in small steps. Making small changes in your routine will open the door to great transformation.", "Aslan": "Do not fear expressing your uniqueness. Follow sudden inspiration in creative projects. Electric blue and purple raise your vibration."},
            "Neptün": {"Başak": "Ground your spirituality in a practical foundation. Add meditation to your daily routine. Crystals (amethyst, lapis lazuli) and incense help you focus.", "Kova": "Find a community to realize your dreams. Turning your idealistic energy into practical projects will ground you."},
            "Plüton": {"Başak": "Letting go of your need for control will be your greatest transformation. Instead of getting stuck on details, focus on the big picture. Deep breathing exercises ease transformation.", "Boğa": "Notice your possessive and controlling impulses. Face your fear of letting go and losing. Forgiveness and gratitude practices accelerate transformation."},
        }

        receteler = []
        # Hard aspects
        gez_list = list(gez_poz.keys())[:12]
        for i, g1 in enumerate(gez_list):
            for j, g2 in enumerate(gez_list):
                if j <= i: continue
                if g1 not in gez_poz or g2 not in gez_poz: continue
                fark = abs(gez_poz[g1]["derece"] - gez_poz[g2]["derece"])
                if fark > 180: fark = 360 - fark
                for aci_dk, aci_ad, orb_max in [(90,"Kare",6),(180,"Karşıt",7)]:
                    if abs(fark - aci_dk) <= orb_max and fark >= 1:
                        sifa = _olumsuz_aci_sifasi(g1, g2, aci_ad)
                        if sifa:
                            if _EN:
                                aci_label = "Opposition" if aci_ad == "Karşıt" else "Square"
                            else:
                                aci_label = aci_ad
                            receteler.append(f"🔴 {g1} {aci_label} {g2}: {sifa}")
                        break

        # Fall / detriment remedies
        diki = SAGALTIM_TEKNIKLERI_EN if _EN else SAGALTIM_TEKNIKLERI
        fark_tr = "Awareness and conscious work are needed." if _EN else "Farkındalık ve bilinçli çalışma gerekiyor."
        for gez, burc in gez_poz.items():
            if gez in DUSUK_ZARAR:
                dusuk, zarar = DUSUK_ZARAR[gez]
                if burc["burc"] == zarar:
                    teknik = diki.get(gez, {}).get(zarar, fark_tr)
                    if _EN:
                        zarar_label = BURCLAR_EN[BURCLAR.index(zarar)]
                        receteler.append(f"🟠 {gez} Detriment ({zarar_label}): {teknik}")
                    else:
                        receteler.append(f"🟠 {gez} Zarar ({zarar}): {teknik}")
                elif burc["burc"] == dusuk:
                    teknik = diki.get(gez, {}).get(dusuk, fark_tr)
                    if _EN:
                        dusuk_label = BURCLAR_EN[BURCLAR.index(dusuk)]
                        receteler.append(f"🟡 {gez} Fall ({dusuk_label}): {teknik}")
                    else:
                        receteler.append(f"🟡 {gez} Düşük ({dusuk}): {teknik}")

        if not receteler:
            if _EN:
                receteler.append("Your chart does not feature a prominent hard aspect or fall/detriment placement. Your energy is flowing naturally.")
            else:
                receteler.append("Haritanızda belirgin bir zorlu açı veya zarar/düşük pozisyonu bulunmuyor. Enerjiniz doğal akışında.")
        return receteler
    except Exception as e:
        import traceback; traceback.print_exc()
        if _EN:
            return [f"Healing prescriptions could not be prepared: {e}"]
        return [f"Şifa reçeteleri hazırlanamadı: {e}"]

def _collect_natal_data(motor):
    """Full natal analysis data combining all collectors."""
    data = _collect_extra_data(motor)
    data["sabianlar"] = _collect_sabian_data(motor)
    data["hayat_alanlari"] = _natal_hayat_alani_analizi(motor)
    # Apply _bireysellestir to each hayat_alanlari yorum for bireysel natal
    if getattr(motor, 'mod', '') == 'bireysel_natal':
        for h in data["hayat_alanlari"]:
            if "yorum" in h:
                h["yorum"] = _bireysellestir(h["yorum"])
        for s in data["sabianlar"]:
            if "sembol" in s:
                s["sembol"] = _bireysellestir(s["sembol"])
    sr_lr = _collect_solar_lunar_data(motor)
    data.update(sr_lr)
    # Daily Moon transit weather (overrides empty from _collect_extra_data)
    data["hava_durumu"] = _natal_gunluk_hava_durumu(motor)
    # Individual potential + career
    try:
        pot = motor.potansiyel_hesapla()
        data["potansiyel_alanlar"] = pot[:10] if isinstance(pot, list) else []
    except:
        data["potansiyel_alanlar"] = []
    try:
        mes = motor.meslek_onerileri()
        data["meslek_onerileri"] = mes[:7] if isinstance(mes, list) else []
    except:
        data["meslek_onerileri"] = []
    # Healing prescriptions (şifa reçeteleri)
    try:
        data["sifa_receteleri"] = motor.get_kadersel_durak()
    except:
        data["sifa_receteleri"] = ""
    # Comprehensive chart interpretation
    try:
        cy = _natal_chart_yorumu(motor)
        if isinstance(cy, tuple) and len(cy) >= 3:
            data["chart_yorumu"] = cy[0]
            data["chart_yorumu_gezegenler"] = cy[1]
            data["chart_yorumu_acilar"] = cy[2]
        elif isinstance(cy, tuple):
            data["chart_yorumu"] = cy[0]
            data["chart_yorumu_gezegenler"] = cy[1]
            data["chart_yorumu_acilar"] = []
        else:
            data["chart_yorumu"] = cy
            data["chart_yorumu_gezegenler"] = []
            data["chart_yorumu_acilar"] = []
    except:
        data["chart_yorumu"] = ""
        data["chart_yorumu_gezegenler"] = []
        data["chart_yorumu_acilar"] = []
    # Expanded healing prescriptions (negative aspects + fall/detriment)
    try:
        data["sifa_receteleri_detay"] = _natal_sifa_receteleri(motor)
    except:
        data["sifa_receteleri_detay"] = []
    return data

# ─── API Endpoints ───

@app_fast.get("/api/health")
def health():
    return {"status": "ok", "version": "4.0"}

@app_fast.get("/api/debug_ephe")
def debug_ephe():
    """Sunucudaki efemeris/star yeteneklerini raporlar (teşhis amaçlı)."""
    import os as _os
    sonuc = {}
    try:
        sonuc["swe_version"] = swe.version
    except Exception as e:
        sonuc["swe_version"] = f"HATA: {e}"
    try:
        sonuc["swe_ephe_path"] = swe.get_ephe_path()
    except Exception as e:
        sonuc["swe_ephe_path"] = f"HATA: {e}"
    try:
        sonuc["ephe_dizin_var"] = _os.path.isdir(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'ephe'))
    except Exception as e:
        sonuc["ephe_dizin_var"] = f"HATA: {e}"
    for alt in ["", "ast0", "ast1", "ast2"]:
        try:
            d = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'ephe', alt)
            if alt == "":
                sonuc["ephe_icerik"] = sorted(_os.listdir(d)) if _os.path.isdir(d) else "YOK"
            else:
                icerik = sorted(_os.listdir(d)) if _os.path.isdir(d) else "YOK"
                sonuc[f"ephe_{alt}_dosya_sayisi"] = len(icerik) if isinstance(icerik, list) else icerik
        except Exception as e:
            sonuc[f"ephe_{alt}_dosya_sayisi"] = f"HATA: {e}"

    from datetime import datetime as _dt
    jd = swe.julday(2026, 8, 3, 12.0)
    cisimler = {
        "Gunes": 0, "Ay": 1, "Merkur": 2, "Venus": 3, "Mars": 4,
        "Jupiter": 5, "Saturne": 6, "Uranus": 7, "Neptun": 8, "Pluto": 9,
        "Lilith_apog": 10, "Chiron": 15, "Juno": swe.AST_OFFSET + 3,
        "Ceres": swe.AST_OFFSET + 1, "Pallas": swe.AST_OFFSET + 2,
        "Vesta": swe.AST_OFFSET + 4, "Eros": swe.AST_OFFSET + 433,
        "Psyche": swe.AST_OFFSET + 16, "Sappho": swe.AST_OFFSET + 80,
        "Amor": swe.AST_OFFSET + 1221,
    }
    cisim_durum = {}
    for ad, gid in cisimler.items():
        try:
            flaglar = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_NOABERR if gid >= 10 else swe.FLG_SWIEPH | swe.FLG_SPEED
            arr, _iflag = swe.calc_ut(jd, gid, flaglar)
            derece = float(arr[0])
            cisim_durum[ad] = {"ok": True, "derece": round(derece, 4)}
        except Exception as e:
            cisim_durum[ad] = {"ok": False, "hata": str(e)[:150]}
    sonuc["cisim_hesap"] = cisim_durum

    yildiz_durum = {}
    for yad in ["Regulus", "Sirius", "Revati", "Pushya", "Antares"]:
        try:
            r = swe.fixstar_ut(yad, jd, swe.FLG_SWIEPH)
            arr = r[0]
            derece = arr[0] if hasattr(arr, "__getitem__") else arr
            yildiz_durum[yad] = {"ok": True, "derece": round(float(derece), 4)}
        except Exception as e:
            yildiz_durum[yad] = {"ok": False, "hata": str(e)[:150]}
    sonuc["yildiz_hesap"] = yildiz_durum
    try:
        from core.utils import fixstar_ut_lon, ephe_klasoru as utils_ephe_klasoru
        sonuc["utils_ephe_klasoru"] = utils_ephe_klasoru
        # set_ephe_path'in gerçekten etki edip etmediğini test et
        swe.set_ephe_path(utils_ephe_klasoru)
        try:
            arr, _iflag = swe.calc_ut(jd, 15, swe.FLG_SWIEPH | swe.FLG_SPEED)
            sonuc["set_sonrasi_chiron"] = {"ok": True, "derece": round(float(arr[0]), 4)}
        except Exception as e:
            sonuc["set_sonrasi_chiron"] = {"ok": False, "hata": str(e)[:150]}
        try:
            r = swe.fixstar_ut("Regulus", jd, swe.FLG_SWIEPH)
            arr = r[0]
            derece = arr[0] if hasattr(arr, "__getitem__") else arr
            sonuc["set_sonrasi_fixstar"] = {"ok": True, "derece": round(float(derece), 4)}
        except Exception as e:
            sonuc["set_sonrasi_fixstar"] = {"ok": False, "hata": str(e)[:150]}
        try:
            arr, _iflag = swe.calc_ut(jd, swe.AST_OFFSET + 3, swe.FLG_MOSEPH | swe.FLG_SPEED)
            sonuc["moseph_juno"] = {"ok": True, "derece": round(float(arr[0]), 4)}
        except Exception as e:
            sonuc["moseph_juno"] = {"ok": False, "hata": str(e)[:150]}
        fs_durum = {}
        for yad in ["Regulus", "Sirius", "Revati", "Pushya", "Antares", "Decrux", "Alchiba"]:
            try:
                fs_durum[yad] = fixstar_ut_lon(yad, jd)
            except Exception as e:
                fs_durum[yad] = f"HATA: {str(e)[:120]}"
        sonuc["fixstar_ut_lon_motor"] = fs_durum
    except Exception as e:
        sonuc["fixstar_ut_lon_motor"] = f"içe aktarılamadı: {str(e)[:120]}"
    try:
        from core.utils import tum_sabit_yildizlar_listesi
        liste = tum_sabit_yildizlar_listesi()
        sonuc["sefstars_yildiz_sayisi"] = len(liste) if isinstance(liste, list) else str(type(liste))
    except Exception as e:
        sonuc["sefstars_yildiz_sayisi"] = f"HATA: {e}"
    return sonuc

@app_fast.get("/api/ulkeler")
def ulkeler_listesi():
    """Tüm ülkeler ve her ülkenin şehir listesi (cities_db.json'dan, 223 ülke)."""
    try:
        db = sehir_veritabani_yukle()
    except Exception:
        db = ULKE_SEHIR_DB
    ulkeler = sorted(db.keys())
    sehirler = {}
    for u in ulkeler:
        seh_liste = db[u]
        if isinstance(seh_liste, dict):
            sehirler[u] = sorted(seh_liste.keys())
        elif isinstance(seh_liste, list):
            sehirler[u] = seh_liste
    return {"ulkeler": ulkeler, "sehirler": sehirler}

@app_fast.get("/api/sehir_ara")
def sehir_ara_endpoint(q: str = "", limit: int = 15):
    """Aksan duyarsız şehir/ülke araması — otomatik tanıma için."""
    q = (q or "").strip()
    if len(q) < 2:
        return {"sonuc": []}
    sonuc = sehir_ara(q, limit=max(1, min(limit, 50)))
    return {"sonuc": sonuc}

@app_fast.post("/api/astrokartografi")
def astrokartografi_analiz(input: AstroInput):
    """Verilen koordinat için composite chart'a göre astrokartografi skoru hesaplar."""
    try:
        motor = _get_engine(input.session_id)
        if not motor:
            raise HTTPException(404, "Oturum bulunamadı")
        comp = _composite_midpoints(motor.p1, motor.p2)
        dt = datetime.strptime(f"{input.tarih} {input.saat}", "%Y-%m-%d %H:%M")
        jd_ev = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)
        skor = _composite_sehir_skor(comp, jd_ev, input.enlem, input.boylam)
        return {
            "sehir": input.sehir,
            "enlem": input.enlem,
            "boylam": input.boylam,
            "tarih": input.tarih,
            "saat": input.saat,
            "gezegenler": comp,
            "skor": {k: skor[k] for k in ["huzur","para","tutku","kriz","etkiler"]},
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Hesaplama hatası: {str(e)}")

@app_fast.post("/api/geocode")
def geocode(input: SehirInput):
    try:
        result = sehir_bul(input.arama)
        if result:
            return {
                "lat": result["lat"],
                "lon": result["lon"],
                "city": result.get("sehir", input.arama),
                "country": result.get("ulke", ""),
                "tam_ad": result.get("tam_ad", ""),
            }
    except Exception as e:
        raise HTTPException(404, f"Şehir bulunamadı: {str(e)}")
    raise HTTPException(404, f"Şehir bulunamadı: {input.arama}")

@app_fast.post("/api/harita/es_sevgili")
def harita_es(input: EsSevgiliInput):
    motor = _engine_es(input)
    dosya = f"{motor._session_id}_Situa_A.png"
    yol = os.path.join(_PROJECT_ROOT, dosya)
    if os.path.exists(yol):
        with open(yol, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        return JSONResponse({"session_id": motor._session_id, "harita_base64": img_b64})
    raise HTTPException(404, "Harita oluşturulamadı")

@app_fast.post("/api/analiz/es_sevgili")
def analiz_es(input: EsSevgiliInput):
    global TOTAL_ANALYSIS; TOTAL_ANALYSIS += 1
    def calistir():
        motor = _engine_es(input, ek_charts=True)
        uyum = motor.calculate_altin_oran_muhru()
        tork = round(motor.calculate_tork_skoru(), 1)
        fraktal = round(motor.calculate_fraktal_uyum(), 1)
        base = {
            "session_id": motor._session_id,
            "p1_isim": motor.p1_isim,
            "p2_isim": motor.p2_isim,
            "uyum_orani": uyum,
            "tork": tork,
            "fraktal": fraktal,
            "mod": "es_sevgili",
            "chartlar": ["situa_a", "situa_b", "frekans", "composite", "aci_gridi", "arap_noktalari"],
        }
        base.update(_collect_extra_data(motor))
        base["event_tarih"] = motor.event_date_str
        base["event_saat"] = motor.event_time_str
        try:
            astro = _collect_astro_data(motor)
            if astro: base["astrokartografi"] = astro
        except: pass
        return base
    sonuc, hata = _analiz_sonuc("es_sevgili", input, calistir)
    if hata: raise hata
    return sonuc

@app_fast.post("/api/analiz/ebeveyn_cocuk")
def analiz_eb(input: EbeveynCocukInput):
    global TOTAL_ANALYSIS; TOTAL_ANALYSIS += 1
    def calistir():
        motor = _engine_eb(input, ek_charts=True)
        uyum = motor.calculate_altin_oran_muhru()
        tork = round(motor.calculate_tork_skoru(), 1)
        fraktal = round(motor.calculate_fraktal_uyum(), 1)
        base = {
            "session_id": motor._session_id,
            "ebeveyn": motor.p2_isim,
            "cocuk": motor.p1_isim,
            "uyum_orani": uyum,
            "tork": tork,
            "fraktal": fraktal,
            "mod": "ebeveyn_cocuk",
            "chartlar": ["situa_a", "situa_b", "frekans", "composite", "aci_gridi", "arap_noktalari"],
        }
        base.update(_collect_extra_data(motor))
        base["event_tarih"] = motor.event_date_str
        base["event_saat"] = motor.event_time_str
        try:
            pot = motor.potansiyel_hesapla()
            base["potansiyel_alanlar"] = pot[:5] if isinstance(pot, list) else []
        except: base["potansiyel_alanlar"] = []
        try:
            mes = motor.meslek_onerileri()
            base["meslek_onerileri"] = mes[:7] if isinstance(mes, list) else []
        except: base["meslek_onerileri"] = []
        try:
            astro = _collect_astro_data(motor)
            if astro: base["astrokartografi"] = astro
        except: pass
        return base
    sonuc, hata = _analiz_sonuc("ebeveyn_cocuk", input, calistir)
    if hata: raise hata
    return sonuc

@app_fast.post("/api/analiz/ebeveyn_cocuk/detayli")
def analiz_eb_detayli(input: EbeveynCocukInput):
    global TOTAL_ANALYSIS; TOTAL_ANALYSIS += 1
    def calistir():
        motor = _engine_eb(input, ek_charts=True)
        uyum = motor.calculate_altin_oran_muhru()
        tork = round(motor.calculate_tork_skoru(), 1)
        fraktal = round(motor.calculate_fraktal_uyum(), 1)
        extra = _collect_extra_data(motor)
        base = {
            "session_id": motor._session_id,
            "ebeveyn": motor.p2_isim,
            "cocuk": motor.p1_isim,
            "uyum_orani": uyum,
            "tork": tork,
            "fraktal": fraktal,
            "mod": "ebeveyn_cocuk",
            "chartlar": ["situa_a", "situa_b", "frekans", "composite", "aci_gridi", "arap_noktalari"],
        }
        base.update(extra)
        base["event_tarih"] = motor.event_date_str
        base["event_saat"] = motor.event_time_str
        try:
            pot = motor.potansiyel_hesapla()
            base["potansiyel_alanlar"] = pot[:5] if isinstance(pot, list) else []
        except: base["potansiyel_alanlar"] = []
        try:
            mes = motor.meslek_onerileri()
            base["meslek_onerileri"] = mes[:7] if isinstance(mes, list) else []
        except: base["meslek_onerileri"] = []
        try:
            astro = _collect_astro_data(motor)
            if astro: base["astrokartografi"] = astro
        except: pass
        return base
    sonuc, hata = _analiz_sonuc("ebeveyn_cocuk_detayli", input, calistir)
    if hata: raise hata
    return sonuc

@app_fast.post("/api/analiz/potansiyel_yetenek")
def analiz_py(input: PotansiyelYetenekInput):
    global TOTAL_ANALYSIS; TOTAL_ANALYSIS += 1
    def calistir():
        motor = _engine_py(input)
        uyum = motor.calculate_altin_oran_muhru()
        potansiyel = motor.potansiyel_hesapla()
        base = {
            "session_id": motor._session_id,
            "isim": motor.p1_isim,
            "uyum_orani": uyum,
            "potansiyel_alan_sayisi": len(potansiyel) if potansiyel else 0,
            "potansiyel_alanlar": potansiyel[:5] if isinstance(potansiyel, list) else [],
            "mod": "potansiyel_yetenek",
        }
        base["event_tarih"] = motor.event_date_str
        base["event_saat"] = motor.event_time_str
        try:
            mes = motor.meslek_onerileri()
            base["meslek_onerileri"] = mes[:7] if isinstance(mes, list) else []
        except: base["meslek_onerileri"] = []
        try:
            astro = _collect_astro_data(motor)
            if astro: base["astrokartografi"] = astro
        except: pass
        return base
    sonuc, hata = _analiz_sonuc("potansiyel_yetenek", input, calistir)
    if hata: raise hata
    return sonuc

@app_fast.post("/api/analiz/bireysel_natal")
def analiz_bireysel_natal(input: BireyselNatalInput):
    global TOTAL_ANALYSIS; TOTAL_ANALYSIS += 1
    def calistir():
        motor = _engine_natal(input, ek_charts=True)
        uyum = motor.calculate_altin_oran_muhru()
        tork = round(motor.calculate_tork_skoru(), 1)
        fraktal = round(motor.calculate_fraktal_uyum(), 1)
        data = _collect_natal_data(motor)
        base = {
            "session_id": motor._session_id,
            "isim": motor.p1_isim,
            "uyum_orani": uyum,
            "tork": tork,
            "fraktal": fraktal,
            "mod": "bireysel_natal",
            "chartlar": ["situa_a", "frekans", "aci_gridi", "arap_noktalari"],
        }
        base["event_tarih"] = motor.event_date_str
        base["event_saat"] = motor.event_time_str
        base.update(data)
        try:
            astro = _collect_astro_data(motor)
            if astro: base["astrokartografi"] = astro
        except: pass
        return base
    sonuc, hata = _analiz_sonuc("bireysel_natal", input, calistir)
    if hata: raise hata
    return sonuc

@app_fast.get("/api/pdf/{session_id}/{tip}")
def pdf_indir(session_id: str, tip: str):
    if tip == "natal":
        dosya_adi = f"{session_id}_Bireysel_Natal.pdf"
    elif tip == "potansiyel":
        dosya_adi = f"{session_id}_Potansiyel_Yetenek.pdf"
    else:
        dosya_adi = f"{session_id}_Cift_Tarafli_Kontrat.pdf"
    yol = os.path.join(_PROJECT_ROOT, dosya_adi)
    if not os.path.exists(yol):
        m = _get_engine(session_id)
        if m is not None:
            try:
                _generate_pdf(m, tip)
            except Exception:
                pass
    if os.path.exists(yol):
        return FileResponse(yol, media_type="application/pdf", filename=dosya_adi)
    raise HTTPException(404, "PDF bulunamadı. Önce analiz çalıştırılmalı.")

# ─── Specific chart routes (SVG with PNG fallback) ───

def _svgy(resim):
    return FileResponse(resim, media_type="image/svg+xml")

def _resim_once(svg, png):
    if os.path.exists(png): return FileResponse(png, media_type="image/png")
    if os.path.exists(svg): return _svgy(svg)
    return None

@app_fast.get("/api/gorsel/{session_id}/situa_a")
def gorsel_situa_a(session_id: str):
    svg = os.path.join(_PROJECT_ROOT, f"{session_id}_Situa_A.svg")
    png = os.path.join(_PROJECT_ROOT, f"{session_id}_Situa_A.png")
    r = _resim_once(svg, png)
    if r: return r
    m = _get_engine(session_id)
    if m: m.haritalari_ciz()
    r = _resim_once(svg, png)
    if r: return r
    raise HTTPException(404)

@app_fast.get("/api/gorsel/{session_id}/situa_b")
def gorsel_situa_b(session_id: str):
    svg = os.path.join(_PROJECT_ROOT, f"{session_id}_Situa_B.svg")
    png = os.path.join(_PROJECT_ROOT, f"{session_id}_Situa_B.png")
    r = _resim_once(svg, png)
    if r: return r
    m = _get_engine(session_id)
    if m: m.haritalari_ciz()
    r = _resim_once(svg, png)
    if r: return r
    raise HTTPException(404)

@app_fast.get("/api/gorsel/{session_id}/frekans")
def gorsel_frekans(session_id: str):
    svg = os.path.join(_PROJECT_ROOT, f"{session_id}_Frekans.svg")
    png = os.path.join(_PROJECT_ROOT, f"{session_id}_Frekans.png")
    r = _resim_once(svg, png)
    if r: return r
    m = _get_engine(session_id)
    if m: m.ciz_titresim_grafigi(dosya_adi=png)
    r = _resim_once(svg, png)
    if r: return r
    raise HTTPException(404)

@app_fast.get("/api/gorsel/{session_id}/composite")
def gorsel_composite(session_id: str):
    svg = os.path.join(_PROJECT_ROOT, f"{session_id}_Composite.svg")
    png = os.path.join(_PROJECT_ROOT, f"{session_id}_Composite.png")
    r = _resim_once(svg, png)
    if r: return r
    m = _get_engine(session_id)
    if m: m.ciz_composite_harita(dosya_adi=png)
    r = _resim_once(svg, png)
    if r: return r
    raise HTTPException(404)

@app_fast.get("/api/gorsel/{session_id}/aci_gridi")
def gorsel_aci_gridi(session_id: str):
    svg = os.path.join(_PROJECT_ROOT, f"{session_id}_Aci_Gridi.svg")
    png = os.path.join(_PROJECT_ROOT, f"{session_id}_Aci_Gridi.png")
    r = _resim_once(svg, png)
    if r: return r
    m = _get_engine(session_id)
    if m: m.ciz_aci_gridi(dosya_adi=png)
    r = _resim_once(svg, png)
    if r: return r
    raise HTTPException(404)

@app_fast.get("/api/gorsel/{session_id}/arap_noktalari")
def gorsel_arap(session_id: str):
    svg = os.path.join(_PROJECT_ROOT, f"{session_id}_Arap_Noktalari.svg")
    png = os.path.join(_PROJECT_ROOT, f"{session_id}_Arap_Noktalari.png")
    r = _resim_once(svg, png)
    if r: return r
    m = _get_engine(session_id)
    if m: m.ciz_arap_noktalari_radar(dosya_adi=png)
    r = _resim_once(svg, png)
    if r: return r
    raise HTTPException(404)

@app_fast.get("/api/gorsel/{session_id}/{dosya}")
def gorsel_getir(session_id: str, dosya: str):
    yol = os.path.join(_PROJECT_ROOT, dosya)
    if os.path.exists(yol):
        return FileResponse(yol, headers={"X-Handler": "generic"})
    raise HTTPException(404, "Görsel bulunamadı")

@app_fast.post("/api/analiz/es_sevgili/detayli")
def analiz_es_detayli(input: EsSevgiliInput):
    global TOTAL_ANALYSIS; TOTAL_ANALYSIS += 1
    def calistir():
        motor = _engine_es(input, ek_charts=True)
        uyum = motor.calculate_altin_oran_muhru()
        tork = round(motor.calculate_tork_skoru(), 1)
        fraktal = round(motor.calculate_fraktal_uyum(), 1)
        extra = _collect_extra_data(motor)
        base = {
            "session_id": motor._session_id,
            "p1_isim": motor.p1_isim,
            "p2_isim": motor.p2_isim,
            "uyum_orani": uyum,
            "tork": tork,
            "fraktal": fraktal,
            "mod": "es_sevgili",
            "chartlar": ["situa_a", "situa_b", "frekans", "composite", "aci_gridi", "arap_noktalari"],
        }
        base.update(extra)
        base["event_tarih"] = motor.event_date_str
        base["event_saat"] = motor.event_time_str
        try:
            astro = _collect_astro_data(motor)
            if astro: base["astrokartografi"] = astro
        except: pass
        return base
    sonuc, hata = _analiz_sonuc("es_sevgili_detayli", input, calistir)
    if hata: raise hata
    return sonuc

# ─── Composite chart astrocartography ───

def _composite_midpoints(p1_dt, p2_dt):
    """Compute composite midpoints for all planets from two birth datetimes."""
    jd1 = swe.julday(p1_dt.year, p1_dt.month, p1_dt.day, 12.0)
    jd2 = swe.julday(p2_dt.year, p2_dt.month, p2_dt.day, 12.0)
    comp = {}
    for gezegen_adi, gezegen_id in GEZEGEN_ACG.items():
        try:
            d1 = swe.calc_ut(jd1, gezegen_id)[0][0]
            d2 = swe.calc_ut(jd2, gezegen_id)[0][0]
            fark = abs(d1 - d2)
            if fark > 180:
                ort = (d1 + (d2 + 360)) / 2 if d1 > d2 else ((d1 + 360) + d2) / 2
            else:
                ort = (d1 + d2) / 2
            comp[gezegen_adi] = ort % 360
        except Exception:
            continue
    return comp

def _composite_sehir_skor(comp, jd_event, lat, lon):
    """Score a city using composite planet midpoints vs local AC/MC/DC/IC."""
    try:
        evre, ascs = swe.houses(jd_event, lat, lon, b'P')
        mc_derece = ascs[1]
        ac_derece = ascs[0]
    except Exception:
        return {"huzur": 50, "para": 50, "tutku": 50, "kriz": 50, "etkiler": []}
    huzur, para, tutku, kriz = 50.0, 50.0, 50.0, 50.0
    etkiler = []
    ORB = 5.0
    for gezegen_adi, gezegen_lon in comp.items():
        ac_f = aci_farki_safe(gezegen_lon, ac_derece)
        mc_f = aci_farki_safe(gezegen_lon, mc_derece)
        dc_f = aci_farki_safe(gezegen_lon, (ac_derece + 180) % 360)
        ic_f = aci_farki_safe(gezegen_lon, (mc_derece + 180) % 360)
        en_yakin = min([("AC", ac_f), ("MC", mc_f), ("DC", dc_f), ("IC", ic_f)], key=lambda x: x[1])
        aci, fark = en_yakin
        if fark > ORB:
            continue
        deger = GEZEGEN_ANLAMLARI.get(gezegen_adi, {})
        carpan = max(0, 1.0 - (fark / ORB))
        if aci == "AC":        carpan *= 1.2
        elif aci == "MC":       carpan *= 1.0
        elif aci == "DC":       carpan *= 0.8
        elif aci == "IC":       carpan *= 0.6
        para += deger.get("para", 0) * carpan
        tutku += deger.get("tutku", 0) * carpan
        huzur += deger.get("huzur", 0) * carpan
        kriz -= deger.get("huzur", 0) * carpan * 0.5
        aci_simge = {"AC": "↑ Yükselen", "DC": "↓ Alçalan", "MC": "⌃ MC", "IC": "⌄ IC"}
        etkiler.append(f"[K] {gezegen_adi} {aci_simge.get(aci, aci)} ({fark:.1f}°) → {deger.get('parlaklik', '')}")
    if "Satürn" in comp and "Plüton" in comp:
        sp_f = aci_farki_safe(comp["Satürn"], comp["Plüton"])
        if sp_f < 10:
            kriz += 20 * (1 - sp_f / 10)
            etkiler.append(f"⚠️ [K] Satürn-Plüto kavuşumu ({sp_f:.1f}°)")
    huzur = min(99, max(5, huzur))
    para = min(99, max(5, para))
    tutku = min(99, max(5, tutku))
    kriz = min(99, max(5, kriz))
    return {"huzur": round(huzur, 1), "para": round(para, 1), "tutku": round(tutku, 1), "kriz": round(kriz, 1), "etkiler": etkiler}

def _composite_radar(p1_dt, p2_dt, event_date_str, event_time):
    """Global city scan using composite chart midpoints + event-date houses."""
    comp = _composite_midpoints(p1_dt, p2_dt)
    if not comp:
        return []
    dt = datetime.strptime(f"{event_date_str} {event_time}", "%Y-%m-%d %H:%M")
    jd_ev = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)
    db = sehir_veritabani_yukle()
    is_list = []
    for ulke, sehirler in db.items():
        for sehir, koordinat in sehirler.items():
            if isinstance(koordinat, dict):
                lat, lon = koordinat["lat"], koordinat["lon"]
            else:
                lat, lon = koordinat
            is_list.append((ulke, sehir, lat, lon))
    from concurrent.futures import ThreadPoolExecutor, as_completed
    def _hesapla(u, s, la, lo):
        skor = _composite_sehir_skor(comp, jd_ev, la, lo)
        return {"sehir": f"{s}, {u}", "lat": la, "lon": lo,
                "huzur": skor["huzur"], "para": skor["para"],
                "tutku": skor["tutku"], "kriz": skor["kriz"],
                "etkiler": skor["etkiler"]}
    sonuc = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_hesapla, u, s, la, lo): (u, s) for u, s, la, lo in is_list}
        for f in as_completed(futs):
            sonuc.append(f.result())
    return sonuc

def _natal_radar(p1_dt, event_date_str, event_time):
    """Global city scan using natal planet positions (single chart)."""
    jd1 = swe.julday(p1_dt.year, p1_dt.month, p1_dt.day, 12.0)
    natal = {}
    for gezegen_adi, gezegen_id in GEZEGEN_ACG.items():
        try:
            natal[gezegen_adi] = swe.calc_ut(jd1, gezegen_id)[0][0]
        except Exception:
            continue
    if not natal:
        return []
    dt = datetime.strptime(f"{event_date_str} {event_time}", "%Y-%m-%d %H:%M")
    jd_ev = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)
    db = sehir_veritabani_yukle()
    is_list = []
    for ulke, sehirler in db.items():
        for sehir, koordinat in sehirler.items():
            if isinstance(koordinat, dict):
                lat, lon = koordinat["lat"], koordinat["lon"]
            else:
                lat, lon = koordinat
            is_list.append((ulke, sehir, lat, lon))
    from concurrent.futures import ThreadPoolExecutor, as_completed
    def _hesapla(u, s, la, lo):
        skor = _composite_sehir_skor(natal, jd_ev, la, lo)
        return {"sehir": f"{s}, {u}", "lat": la, "lon": lo,
                "huzur": skor["huzur"], "para": skor["para"],
                "tutku": skor["tutku"], "kriz": skor["kriz"],
                "etkiler": skor["etkiler"]}
    sonuc = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_hesapla, u, s, la, lo): (u, s) for u, s, la, lo in is_list}
        for f in as_completed(futs):
            sonuc.append(f.result())
    return sonuc

def _result_kategorize(radar):
    """Sort radar results into 4 categories, one per country, exclude 3rd world."""
    EXCLUDED = {"Afghanistan","Afganistan","Pakistan","Bangladesh","Sri Lanka","Myanmar","Cambodia","Laos","Nepal","Bhutan","Maldives","Maldivler","Yemen","Syria","Suriye","Iraq","Irak","Libya","Sudan","Somali","Somalia","Ethiopia","Eritre","Chad","Nijer","Niger","Mali","Burkina Faso","Moritanya","Mauritania","Orta Afrika Cumhuriyeti","Central African Republic","Kongo","Demokratik Kongo Cumhuriyeti","DRC","Zimbabwe","Mozambik","Mozambique","Madagaskar","Madagascar","Haiti","Kuzey Kore","North Korea","Küba","Cuba"}
    excluded_any = {e.lower() for e in EXCLUDED}
    sirali = {"para": [], "huzur": [], "tutku": [], "kriz": []}
    for c in radar:
        raw = c["sehir"]
        sehir_ad, ulke = raw.rsplit(", ", 1) if ", " in raw else (raw, "")
        if (ulke in EXCLUDED) or (ulke and any(e in raw.lower() for e in excluded_any)): continue
        for kat in sirali:
            sirali[kat].append((sehir_ad, ulke, c[kat], c.get("lat"), c.get("lon"), c.get("etkiler", [])))
    for kat in sirali:
        sirali[kat].sort(key=lambda x: x[2], reverse=True)
        gorulen = set()
        tekil = []
        for sehir_ad, ulke, skor, lat, lon, etkiler in sirali[kat]:
            if ulke not in gorulen:
                gorulen.add(ulke)
                tekil.append({"sehir": f"{sehir_ad}, {ulke}", "skor": round(skor, 2), "lat": lat, "lon": lon, "etkiler": list(etkiler or [])[:2]})
                if len(tekil) == 10: break
        sirali[kat] = tekil
    return sirali, len(radar)

@app_fast.post("/api/simulasyon/radar")
def simulasyon_radar(input: EsSevgiliInput):
    motor = _engine_es(input)
    radar = _composite_radar(
        p1_dt=motor.p1,
        p2_dt=motor.p2,
        event_date_str=_parse_date(input.event_tarih),
        event_time=input.event_saat,
    )
    sirali, toplam = _result_kategorize(radar)
    return {"session_id": motor._session_id, "top_sehirler": sirali, "toplam_sehir": toplam}

@app_fast.post("/api/simulasyon/natal_radar")
def simulasyon_natal_radar(input: BireyselNatalInput):
    motor = _engine_natal(input)
    radar = _natal_radar(
        p1_dt=motor.p1,
        event_date_str=_parse_date(input.tarih),
        event_time=input.saat,
    )
    sirali, toplam = _result_kategorize(radar)
    return {"session_id": motor._session_id, "top_sehirler": sirali, "toplam_sehir": toplam}

@app_fast.post("/api/simulasyon/alternatif")
def simulasyon_alternatif(input: AlternatifInput):
    # Re-run analysis with different coordinates
    motor = _get_engine(input.session_id)
    if not motor:
        raise HTTPException(404, "Oturum bulunamadı. Önce analiz çalıştırın.")
    # Create new engine with alternative location
    motor2 = FBST_Engine(
        p1=motor.p1_str, p2=motor.p2_str,
        event_date=motor.event_date_str, event_time=motor.event_time_str,
        city=input.sehir, country="",
        lat=input.enlem, lon=input.boylam,
        p1_isim=motor.p1_isim, p2_isim=motor.p2_isim,
        mod=motor.mod, utc_offset=input.utc_offset,
    )
    motor2.fbst_analizi_yap(sessiz=True)
    _cache_engine(motor2)
    uyum = motor2.calculate_altin_oran_muhru()
    tork = round(motor2.calculate_tork_skoru(), 1) if motor2.mod != "potansiyel_yetenek" else None
    fraktal = round(motor2.calculate_fraktal_uyum(), 1) if motor2.mod != "potansiyel_yetenek" else None
    return {
        "session_id": motor2._session_id,
        "sehir": input.sehir,
        "enlem": input.enlem,
        "boylam": input.boylam,
        "uyum_orani": uyum,
        "tork": tork,
        "fraktal": fraktal,
    }

# ─── City image cache ───
import urllib.request, urllib.parse, json as pyjson
_CITY_IMG_CACHE = {}  # {norm: {"img": str|None, "page": str|None}}

def _sehir_wikipedia_bul(ad: str):
    """Wikipedia'da şehri ara, (img_url, page_url) döndür."""
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(ad)}&format=json&srlimit=3&srprop="
        req = urllib.request.Request(search_url, headers={"User-Agent": "FAST/4.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            results = pyjson.loads(resp.read()).get("query", {}).get("search", [])
        for r in results:
            title = r.get("title", "")
            if not title: continue
            try:
                page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
                req2 = urllib.request.Request(summary_url, headers={"User-Agent": "FAST/4.0"})
                with urllib.request.urlopen(req2, timeout=4) as resp2:
                    data = pyjson.loads(resp2.read())
                img = data.get("thumbnail", {}).get("source") or data.get("originalimage", {}).get("source")
                return img, page_url
            except: continue
    except: pass
    return None, None

@app_fast.get("/api/sehir_gorsel/{sehir:path}")
def sehir_gorsel(sehir: str):
    norm = sehir.strip().lower()
    if norm in _CITY_IMG_CACHE:
        img_url = _CITY_IMG_CACHE[norm]["img"]
        if img_url:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(img_url)
        raise HTTPException(404)
    ad = sehir.split(',')[0].strip()
    img, page = _sehir_wikipedia_bul(ad)
    _CITY_IMG_CACHE[norm] = {"img": img, "page": page}
    if img:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(img)
    raise HTTPException(404)

@app_fast.get("/api/sehir_bilgi/{sehir:path}")
def sehir_bilgi(sehir: str):
    norm = sehir.strip().lower()
    if norm not in _CITY_IMG_CACHE:
        ad = sehir.split(',')[0].strip()
        img, page = _sehir_wikipedia_bul(ad)
        _CITY_IMG_CACHE[norm] = {"img": img, "page": page}
    return _CITY_IMG_CACHE[norm]

@app_fast.get("/api/astrocartography/harita/{session_id}")
def astrocartography_harita(session_id: str):
    """Astrocartography dünya haritasını SVG olarak döndürür."""
    motor = _get_engine(session_id)
    if not motor:
        raise HTTPException(404, "Oturum bulunamadı")
    try:
        abs_svg = os.path.join(_PROJECT_ROOT, f"acg_{session_id}.svg")
        abs_png = os.path.join(_PROJECT_ROOT, f"acg_{session_id}.png")
        if not os.path.isfile(abs_svg) and not os.path.isfile(abs_png):
            motor.ciz_astrocartography(abs_png)
        if os.path.isfile(abs_svg):
            return FileResponse(abs_svg, media_type="image/svg+xml")
        if os.path.isfile(abs_png):
            return FileResponse(abs_png, media_type="image/png")
        raise HTTPException(500, "Harita oluşturulamadı")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Harita hatası: {str(e)}")

# ─── Stripe / Ödeme ───
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
PAID_SESSIONS = {}

class PaymentRequest(BaseModel):
    plan: str  # "premium" | "pro"
    session_id: str

PRICE_IDS = {
    "premium": os.getenv("STRIPE_PRICE_PREMIUM", "price_premium_placeholder"),
    "pro": os.getenv("STRIPE_PRICE_PRO", "price_pro_placeholder"),
}
PRICES_TL = {"premium": 12900, "pro": 24900}

@app_fast.post("/api/payment/create-checkout")
def create_checkout(req: PaymentRequest):
    if stripe.api_key == "sk_test_placeholder":
        # Demo mode — simulate success
        PAID_SESSIONS[req.session_id] = True
        return {"url": "", "demo": True}
    try:
        checkout = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": PRICE_IDS[req.plan], "quantity": 1}],
            metadata={"session_id": req.session_id, "plan": req.plan},
            success_url=f"/?session_id={req.session_id}&paid=true",
            cancel_url="/",
        )
        return {"url": checkout.url}
    except Exception as e:
        raise HTTPException(400, f"Stripe hatası: {str(e)}")

@app_fast.post("/api/payment/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    whsec = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if whsec:
        try:
            event = stripe.Webhook.construct_event(payload, sig, whsec)
        except (ValueError, hmac.HMACError):
            raise HTTPException(400, "Geçersiz imza")
    else:
        event = json.loads(payload)
    if event.get("type") == "checkout.session.completed":
        sess = event["data"]["object"]
        sid = sess.get("metadata", {}).get("session_id")
        if sid:
            PAID_SESSIONS[sid] = True
    return {"ok": True}

@app_fast.get("/api/payment/verify/{session_id}")
def verify_payment(session_id: str):
    return {"paid": PAID_SESSIONS.get(session_id, False)}

# ─── Email (placeholder) ───
class EmailRequest(BaseModel):
    session_id: str
    email: str

@app_fast.post("/api/email/send-pdf")
def send_pdf_email(req: EmailRequest):
    if not PAID_SESSIONS.get(req.session_id):
        raise HTTPException(402, "Ödeme yapılmamış")
    # TODO: integrate SendGrid / SMTP
    # For now, log and return success
    print(f"[EMAIL] PDF for session {req.session_id} would be sent to {req.email}")
    return {"sent": True}

# ─── Stats / Social Proof ───
TOTAL_ANALYSIS = 0  # incremented in handle_submit

@app_fast.get("/api/stats")
def get_stats():
    return {"total_analysis": TOTAL_ANALYSIS, "total_cities": 15000}

# ─── Frontend serving ───
_FRONTEND_HTML = os.path.join(_PROJECT_ROOT, "frontend", "dist", "index.html")
_FRONTEND_DIR = os.path.dirname(_FRONTEND_HTML)

@app_fast.get("/")
def frontend_index():
    if os.path.isfile(_FRONTEND_HTML):
        return FileResponse(_FRONTEND_HTML)
    raise HTTPException(404)

@app_fast.get("/{path:path}")
def frontend_catchall(path: str):
    """Serve frontend static files for non-API paths."""
    if path.startswith("api/"):
        raise HTTPException(404)
    file_path = os.path.join(_FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    if os.path.isfile(_FRONTEND_HTML):
        return FileResponse(_FRONTEND_HTML)
    raise HTTPException(404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app_fast, host="127.0.0.1", port=8000, log_level="error")
