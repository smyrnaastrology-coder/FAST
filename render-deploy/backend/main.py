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
def _es_fix_tire(text):
    if not isinstance(text, str):
        return text
    # Tire: LunaUrano -> Luna-Urano, Luna Mercurio -> Luna-Mercurio, etc.
    # Handle all Luna-planet combos and also fix spacing
    planets = ["Urano","Mercurio","Venus","Marte","Júpiter","Saturno","Neptuno","Plutón","Quirón","Sol","Luna"]
    for pl in planets:
        text = text.replace(f"Luna{pl}", f"Luna-{pl}")
        text = text.replace(f"Luna {pl}", f"Luna-{pl}")
        text = text.replace(f"luna{pl.lower()}", f"luna-{pl.lower()}")
    # Also fix double hyphen
    text = text.replace("Luna--", "Luna-")
    # Place names: Turkish -> Spanish
    text = text.replace("Ekvator Ginesi", "Guinea Ecuatorial")
    text = text.replace("Sao Tome ve Principe", "Santo Tomé y Príncipe")
    text = text.replace("Sao Tome ve Princi", "Santo Tomé y Príncipe")
    text = text.replace("Sao Tome ve", "Santo Tomé y")
    text = text.replace("Ekvator", "Ecuador")
    # Keep other place names as is but ensure correct accent
    return text

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

NATAL_AY_ACISI_YORUMLARI_EN = {
    ("Ay","Güneş","Kavuşum"): [
        "Your emotions and your sense of self are in perfect harmony today. Your inner voice and your logic are saying the same thing. Your self-confidence is growing, and this energy radiates to those around you.",
        "There is a rare unity between your heart and your mind. You see clearly what you want and move forward with certainty in your feelings. Today, feel the power of simply being yourself to the fullest.",
        "A day of inner wholeness: your feelings and your thoughts are vibrating on the same frequency. Thanks to this harmony, you can make even difficult decisions with ease and project a natural authority onto your surroundings."
    ],
    ("Ay","Güneş","Karşıt"): [
        "There is a search for balance within your inner world. Your logic says one thing while your heart pulls in another direction. This tension exists precisely to show you which path to take.",
        "You may feel a conflict between your emotional needs and your ego goals. Today, listen to both voices. The resolution lies not between them but in embracing both.",
        "A day when opposites bring awareness. You may be experiencing inner tension, but it will show you sides of yourself you have not yet discovered. Try to understand both sides to find your balance."
    ],
    ("Ay","Güneş","Kare"): [
        "You may feel caught between your emotions and your goals. Not knowing which way to go is natural. This uncertainty opens space for you to find a new direction.",
        "You are under inner pressure. This tension between your heart and your mind is a sign that you need to make a decision. Do not postpone it; even a small step will relieve you.",
        "Today is a day of confronting yourself. Your inner conflicts offer you an opportunity to grow. Do not resist uncomfortable emotions; try to understand them, they are here to teach you something."
    ],
    ("Ay","Güneş","Trigon"): [
        "There is a natural harmony between your emotional world and your identity. Accepting yourself as you are becomes easier today. Your inner peace reflects onto the outside world.",
        "A day when you are in the flow. There is a smooth connection between your feelings and your actions. Your creativity is high and your intuition strong. Make the most of this energy.",
        "A time when you feel at peace with yourself. Thanks to your inner harmony, you spread tranquility to those around you. Today, make time for the things you enjoy."
    ],
    ("Ay","Güneş","Sekstil"): [
        "A beautiful opportunity to express your feelings is at your door. A situation you encounter today will help you reveal your true inner feelings.",
        "A productive bridge is being built between your inner and outer world. A new hobby, a creative project or a space to express yourself will do you good.",
        "A day when your emotional intelligence rises. Understanding people around you and connecting with them becomes easier. Use this opportunity for an honest, heartfelt conversation."
    ],
    ("Ay","Venüs","Kavuşum"): [
        "Your love energy is very high today. The warmth in your heart reflects onto those around you. Turning to artistic and aesthetic matters and surrounding yourself with beautiful things will do you good.",
        "You feel compassionate and affectionate. You instinctively seek beauty and harmony. Today, do a small favor for yourself; you deserve it.",
        "The balance between giving and receiving is established naturally today. Do not hesitate to express your love. You may draw inspiration for work that requires creativity."
    ],
    ("Ay","Venüs","Karşıt"): [
        "You may need to choose between your emotional needs and the things you enjoy. Ask yourself in which area you want to invest more.",
        "You may feel a sense of inner dissatisfaction. What you want and what you need may not be the same. Today, spend a little time alone and listen to your inner self.",
        "Time to strike a balance between love and money. If there is a mismatch between what you value and where you spend your energy, you can recognize and correct it today."
    ],
    ("Ay","Venüs","Kare"): [
        "You may feel caught between the things you enjoy and your responsibilities. If you struggle to make time for yourself, even a short break makes a big difference.",
        "Your desire to spend may conflict with your need to save. In today's decisions, listen to your logic rather than your heart. Do not let a passing whim mislead you.",
        "You may experience a balance issue in relationships — giving too much and taking too little, or the reverse. Today, review your boundaries and protect yourself."
    ],
    ("Ay","Venüs","Trigon"): [
        "Love and beauty are finding a natural flow in your life. Your inner peace reflects onto the outside world. Artistic activities, music or a nature walk will do you good.",
        "There is a natural harmony between you and your social circle. Today, spending time with loved ones, cooking a nice meal or being in an aesthetic environment will energize you.",
        "A day to pamper yourself. This harmonious aspect between Venus and the Moon offers you the chance to see the beautiful sides of life. Enjoy the small pleasures."
    ],
    ("Ay","Venüs","Sekstil"): [
        "A new discovery of beauty may await you — perhaps a new café, an exhibition or a melody. Your aesthetic sensitivity is high today; pay attention to your surroundings.",
        "A wonderful opportunity to socialize. You may meet new people or come together with old friends. Your communication will be fluent and warm.",
        "You may find a new way to express yourself. An inspiring day to take up a hobby or start a creative project."
    ],
    ("Ay","Mars","Kavuşum"): [
        "Your energy and your emotions are moving at the same time. There is a strong urge to act within you. Channeling this energy into sports or a physical activity will do you good.",
        "Your emotional reactions may be more intense than usual. Recognize your anger but know how to control it. When channeled correctly, this energy is a great driving force.",
        "A day of courage and passion. A perfect time to start something you have been postponing for a long time. Trust your instincts and take action."
    ],
    ("Ay","Mars","Karşıt"): [
        "You may find yourself between your inner desires and the demands of the outside world. You may need to make an effort to balance your wants and your obligations.",
        "You may feel emotionally tense, and your reactions may be harsher than usual. Before entering a conflict, take a deep breath and think.",
        "Other people's energy can affect you. Protect your own boundaries and do not take on others' problems. Physical exercise will help you release this tension."
    ],
    ("Ay","Mars","Kare"): [
        "A volcano may be waiting inside you. A small spark could turn into a big explosion. Today, make a conscious effort to stay calm.",
        "You are stuck between your emotional anger and your logic. You want to break things but also know you must stop. Physical activity can reduce this pressure.",
        "You may feel impatience and restlessness. Everything may seem to bother you. This is a temporary phase; give yourself time and do not force it."
    ],
    ("Ay","Mars","Trigon"): [
        "Your energy and your emotions are in perfect harmony. You have high potential to succeed at anything you want to do. Ideal for sports, creative projects or new beginnings.",
        "Your courage and determination are at their peak. Even a difficult task may seem easy today. You are instinctively making the right moves and surrendering to the flow.",
        "A day when you feel physically and emotionally strong. You trust yourself and do not waste any time before taking action. Use this energy productively."
    ],
    ("Ay","Mars","Sekstil"): [
        "A wonderful opportunity to start a new physical activity. Dance, yoga, running or a team sport may do you well. Your body and soul want to work together.",
        "Your emotional courage is growing. An opportunity you meet today may awaken the warrior within you. Face your fears.",
        "You may discover a new area to channel your energy. A hobby, a project or a sport will provide you with both physical and emotional satisfaction."
    ],
    ("Ay","Jüpiter","Kavuşum"): [
        "Your optimism and joy are peaking today. You look at life from a broader perspective and approach the future with hope. Be open to new experiences.",
        "You feel emotional expansion and liberation. There is a sense of inner abundance and prosperity. Sharing this energy with your loved ones will do you good.",
        "Your desire for adventure and discovery is growing. Seeing a new place, experiencing a different culture, or simply walking down a street you have never seen can do you good."
    ],
    ("Ay","Jüpiter","Karşıt"): [
        "You may find yourself between your desire for inner growth and the limitations of the outside world. You want more, but circumstances may be restricting you. Be patient.",
        "You have a tendency to exaggerate. You may struggle to control your emotions or your spending. Today, try to be moderate.",
        "You may need to balance others' expectations with your own wishes. Listen to your inner voice to find your own path."
    ],
    ("Ay","Jüpiter","Kare"): [
        "Excessive optimism can overshadow your realism. Dreaming big is beautiful, but today your feet should stay on the ground. Step back and evaluate the situation objectively.",
        "You tend to exaggerate emotionally. There may be an imbalance between what you feel and what you do. Today, make an effort to stay measured.",
        "You may feel the need to prove yourself. But do not force yourself to impress others. Being accepted as you are is the greatest freedom."
    ],
    ("Ay","Jüpiter","Trigon"): [
        "Your inner sense of abundance and prosperity is in a natural flow. Life may offer you beautiful surprises. A feeling of gratitude will warm your heart today.",
        "Your desire to learn and explore is growing. A great day to read a book, watch a documentary or learn a new skill. Your mind and heart work together.",
        "Your optimism also affects the people around you. Today, share your positive thoughts and inspire your loved ones. Ideal for socializing."
    ],
    ("Ay","Jüpiter","Sekstil"): [
        "A new learning opportunity may be at your door. An educational program, seminar or workshop might catch your interest. A good time to invest in your personal growth.",
        "A cultural event or a travel plan may do you good. Seeing different perspectives will broaden your horizons. Today, try something new.",
        "Trust your inner wisdom. If you know something to be true, do not hesitate to share it. You can inspire the people around you."
    ],
    ("Ay","Satürn","Kavuşum"): [
        "You may feel more serious and distant emotionally. There is a questioning within your inner world. This is part of your emotional maturation process. Be honest with yourself.",
        "You feel the weight of your responsibilities. Your emotional burden may have increased. Today, show yourself compassion and remember that you are not alone.",
        "A day of discovering your inner boundaries. You are questioning where to stand and where to move forward. This discipline will give you emotional security in the long run."
    ],
    ("Ay","Satürn","Karşıt"): [
        "You are experiencing a conflict between your emotional needs and your responsibilities. Your inner voice says one thing while the outside world expects another. Finding the balance is up to you.",
        "A feeling of loneliness may prevail. You may think others do not understand you. This is a temporary feeling; instead of isolating yourself, reach out to a friend.",
        "An emotional burden from the past may surface today. Forgiving and letting go will lighten this weight. Give yourself time."
    ],
    ("Ay","Satürn","Kare"): [
        "You feel under emotional pressure. You may feel inadequate or unprepared in a matter. See this feeling as a learning opportunity.",
        "Your tendency to criticize yourself is growing. Perfectionism may give you a hard time today. Remember that not everything has to be perfect.",
        "You may encounter an emotional obstacle. Your plans may go wrong or you may experience disappointment in something. This is a test that will strengthen you."
    ],
    ("Ay","Satürn","Trigon"): [
        "Thanks to your emotional discipline and maturity, you overcome difficulties easily. Being aware of your inner strength gives you confidence.",
        "You adopt a structured emotional approach. Instead of suppressing your feelings, you are learning to manage them. This is a sign of growth.",
        "A good day to focus on your long-term goals. Thanks to your emotional stability, you can take solid steps and look to the future with confidence."
    ],
    ("Ay","Satürn","Sekstil"): [
        "An opportunity is before you to become more organized and planned emotionally. A good time to build a habit or establish a routine.",
        "A lesson from the past may prove useful today. On a matter that was difficult for you before, you now feel more mature and ready.",
        "Advice from a mentor or guide will do you good. An experienced person's perspective can guide you on an emotional matter."
    ],
    ("Ay","Merkür","Kavuşum"): [
        "Your power to express your emotions is growing. Putting what is inside you into words becomes easier. A great day for writing, speaking or telling someone your troubles.",
        "Your intuition and your logic work at the same time. You grasp a subject with both your heart and your mind. If there is a contradiction between the two, it will become clear today.",
        "There is a strong connection between your mind and your heart. Your emotional intelligence is high, and your ability to understand people and empathize with them is increasing."
    ],
    ("Ay","Merkür","Karşıt"): [
        "You are experiencing a contradiction between your feelings and your thoughts. Your logic says one thing while your heart feels another. Listen to both.",
        "There may be misunderstandings in communication with others. If there is a gap between what you say and what you feel, try to close it today.",
        "You may overthink an emotional subject and confuse yourself. Sometimes you need to feel rather than analyze. Silence your mind and listen to your heart."
    ],
    ("Ay","Merkür","Kare"): [
        "You may be mentally scattered and find it hard to focus. Your emotions may be clouding your thoughts. Today, avoid making important decisions.",
        "There may be a difference between what you want to say and what you say. If you struggle to express yourself, writing may help you.",
        "You may fall into obsessive thoughts about an emotional subject. To break this cycle, direct your mind toward something else."
    ],
    ("Ay","Merkür","Trigon"): [
        "A perfect day to express your feelings. Your inner voice is clear and your words flow. Telling someone how you feel or writing a letter will do you good.",
        "Your intuition and logic are in harmony. You both feel and understand a subject. Thanks to this holistic perspective, you can make the right decisions.",
        "Your learning and communication abilities are growing. An ideal day to learn a new language, read a book or research a topic."
    ],
    ("Ay","Merkür","Sekstil"): [
        "A new communication opportunity is at your door. You may hear from an old friend or have a meaningful conversation with someone new.",
        "You may encounter a situation where you can use your emotional intelligence. Giving someone advice or understanding them will do you good.",
        "You may feel inspired to write or create something. Keeping a journal, writing poetry or posting on a blog will help you express your emotions."
    ],
    ("Ay","Uranüs","Kavuşum"): [
        "You may feel a sudden need for emotional liberation. Routines are suffocating you, and you want to do something new and different. Trust your instincts.",
        "You may experience an unexpected emotional insight. Suddenly, you may see a matter very clearly. Make the most of this moment of illumination.",
        "A day when you are attached to your freedom. You want to live by your own rules, not by others' expectations. Use this energy creatively."
    ],
    ("Ay","Uranüs","Karşıt"): [
        "You may be caught between your desire for stability and your need for change. On one hand you want to be safe, on the other you want to push your limits. This dilemma offers you a chance to grow.",
        "There is tension between others' expectations and your own need for freedom. You may need to be brave to find your own path.",
        "You may react suddenly and then regret it. Think once more before you say or do something."
    ],
    ("Ay","Uranüs","Kare"): [
        "You may experience an unexpected emotional outburst. A feeling you have been suppressing for a long time may suddenly surface today. Do not be surprised; this is natural.",
        "A disruption of your routine may bother you. Being forced out of your plans, though annoying at first, may open a new door.",
        "You may experience emotional fluctuations. One moment happy, another moment sad. This is a temporary phase; let yourself go with the flow."
    ],
    ("Ay","Uranüs","Trigon"): [
        "A day when you discover your inner freedom. You enjoy living by your own rules. Your creativity and originality influence those around you.",
        "You may experience a sudden burst of inspiration. A perfect idea for a creative project may come to mind. Do not miss it; write it down immediately.",
        "Change and novelty do you good. A different environment, new people or an unusual experience can reveal your inner potential."
    ],
    ("Ay","Uranüs","Sekstil"): [
        "An opportunity for a new and unusual experience is at your door. Trying something you have never done before can energize you.",
        "You may gain a different perspective on a matter. An unconventional thought may help you find a creative solution to a problem.",
        "Getting involved with technology or an innovative field may do you well. A good day to discover a new app or start a digital project."
    ],
    ("Ay","Neptün","Kavuşum"): [
        "Your intuition is very strong today. You sense people and events beyond words. Meditation, music or art will bring you deep peace.",
        "You may feel your boundaries dissolving emotionally and see that you are connected to everything. This sense of unity heals you.",
        "Your imagination and emotions are intertwined. Your dreams may be more vivid and your intuition clearer. Today, listen to your inner voice."
    ],
    ("Ay","Neptün","Karşıt"): [
        "You may drift between reality and your dream world. You may be seeing things differently than they are. Today, avoid making important decisions.",
        "You may experience emotional confusion and struggle to see a matter clearly. Step back for a while and let the situation become clear.",
        "Other people's energy can easily affect you. Your emotional boundaries may be weakened. Create a space where you can be alone to protect yourself."
    ],
    ("Ay","Neptün","Kare"): [
        "You may feel lost in an emotional fog. Distinguishing what is real from what is imagined may become difficult. Today, be honest with yourself.",
        "Your tendency to escape may increase. You may turn to dreams, alcohol or another addiction to get away from reality. Be aware and find healthy alternatives.",
        "Your chances of being deceived or disappointed are high. Do not trust a person or situation too much. Be realistic."
    ],
    ("Ay","Neptün","Trigon"): [
        "There is a natural flow between your intuition and imagination. A perfect day for an artistic project, creative work or a spiritual practice.",
        "You feel inner peace and serenity. Spending time in nature, listening to music or meditating will bring you deep satisfaction.",
        "Your empathy is very high. You have a natural gift for understanding and helping people. Today, use this power."
    ],
    ("Ay","Neptün","Sekstil"): [
        "An opportunity to nourish your creativity is before you. An art workshop, a photography trip or a music event may do you good.",
        "You may have a spiritual experience. A book, a conversation or a memory of nature may bring you deep understanding.",
        "Your intuition will guide you today. If you have a feeling about something, take it seriously. Even if your logic cannot explain it, your heart knows the truth."
    ],
    ("Ay","Plüton","Kavuşum"): [
        "You are in the middle of an emotional transformation. Suppressed feelings may surface today. Though it looks frightening, this confrontation will set you free.",
        "A day when you become aware of your inner power. Letting go of what you cannot control is actually your greatest form of empowerment. Be open to transformation.",
        "You are undergoing a deep emotional purification. Old wounds and past traumas may show themselves today. This is an opportunity to heal them."
    ],
    ("Ay","Plüton","Karşıt"): [
        "You are waging a war between controlling and letting go. The more you try to hold onto a situation, the more you seem to lose. Letting go is the greatest victory.",
        "Others' shadow may affect you. Do not take on the emotions someone projects onto you. Remember your own power.",
        "Time for an emotional reckoning. An event from your past may come up again today. You do not have to react the same way this time."
    ],
    ("Ay","Plüton","Kare"): [
        "Your emotional intensity is at its peak. A small event can turn into a big reaction. Today, take extra care of yourself and recognize your triggers.",
        "You are experiencing an inner power struggle. You may feel caught between your old habits and your new self. Transformation can be painful, but it is necessary.",
        "Obsessive thoughts and feelings may take over. If you struggle to let go of a subject, seeking professional support may be a good idea."
    ],
    ("Ay","Plüton","Trigon"): [
        "Your power of emotional transformation works in a natural flow. You can easily resolve a difficult issue and act with deep understanding.",
        "Your inner healing and recovery energy is high. You are in a powerful period for mending past wounds and breaking old patterns.",
        "Your ability to heal and transform others is growing. Supporting and guiding someone will do you good. In this process, you are healing as well."
    ],
    ("Ay","Plüton","Sekstil"): [
        "You may gain a deep psychological insight. A dream, a therapy session or a deep conversation can teach you something new about yourself.",
        "Researching a matter from the past or exploring your family history may do you good. Understanding your roots can explain your present behavior.",
        "You may learn a hidden truth about a matter. Although shocking at first, in the long run this knowledge will bring you freedom."
    ],
}  # EN mirror

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

AY_BURC_TANIMLARI_ES = {
    "Koç": "Tu Luna está en Aries — tus emociones son ardientes, repentinas y directas. Tus reacciones instintivas son fuertes, valientes y emprendedoras.",
    "Boğa": "Tu Luna está en Tauro — buscas estabilidad emocional y seguridad. La comodidad y el bienestar son importantes para ti.",
    "İkizler": "Tu Luna está en Géminis — sientes la necesidad de poner tus emociones en palabras. Tienes una estructura emocional curiosa y orientada a la comunicación.",
    "Yengeç": "Tu Luna está en Cáncer — la Luna en su propia casa, tus emociones son sumamente profundas y protectoras. La familia y el hogar son muy poderosos en tu interior.",
    "Aslan": "Tu Luna está en Leo — tu expresión emocional es cálida, generosa y brillante. Actúas guiado por el corazón; el honor y el orgullo son importantes para ti.",
    "Başak": "Tu Luna está en Virgo — analizas tus emociones e intentas encajarlas en un marco lógico. El orden y la limpieza te dan paz.",
    "Terazi": "Tu Luna está en Libra — buscas equilibrio y armonía emocional. La estética, la elegancia y la justicia alimentan tus sentimientos.",
    "Akrep": "Tu Luna está en Escorpio — tus emociones son intensas, apasionadas y transformadoras. Tus sentimientos ocultos en lo profundo son poderosos.",
    "Yay": "Tu Luna está en Sagitario — la libertad emocional y la exploración te nutren. Tienes una naturaleza emocional optimista, aventurera e independiente.",
    "Oğlak": "Tu Luna está en Capricornio — tus emociones son controladas, disciplinadas y responsables. Tu seguridad emocional se vincula con el éxito y el estatus.",
    "Kova": "Tu Luna está en Acuario — emocionalmente libre, independiente y poco convencional. Valorizas tu originalidad y mantienes tu distancia emocional.",
    "Balık": "Tu Luna está en Piscis — tus emociones son fluidas, intuitivas y sin límites. Tu capacidad de empatía es alta y tu veta artística y espiritual es fuerte.",
}

AY_EV_TANIMLARI_ES = {
    1: "La Luna en casa 1 — tu expresión emocional es fuerte; tus sentimientos se leen en tu rostro. Tus propias necesidades están en primer plano.",
    2: "La Luna en casa 2 — tu seguridad emocional se conecta con la estabilidad material. Desarrollas vínculos afectivos con lo que posees.",
    3: "La Luna en casa 3 — expresas tus emociones a través de la comunicación. Tu círculo cercano y tus hermanos ocupan un lugar importante en tu mundo emocional.",
    4: "La Luna en casa 4 — la familia y el hogar son tu centro emocional. Tu conexión con tu pasado, tus raíces y tu madre es fuerte.",
    5: "La Luna en casa 5 — expresas tus emociones a través de la creatividad y el juego. El romance y los asuntos de los niños están en primer plano.",
    6: "La Luna en casa 6 — tu salud emocional se relaciona con tu rutina diaria y tu vida laboral. Servir y ayudar te sienta bien.",
    7: "La Luna en casa 7 — tus necesidades emocionales se moldean a través de las relaciones cercanas y las alianzas. Buscas equilibrio y armonía.",
    8: "La Luna en casa 8 — la profundidad emocional, la transformación y los recursos compartidos están en primer plano. La intimidad y la confianza son temas sensibles.",
    9: "La Luna en casa 9 — tu alimento emocional llega a través de los viajes, la filosofía y el aprendizaje superior. La exploración y la búsqueda de sentido son tus necesidades emocionales.",
    10: "La Luna en casa 10 — tu expresión emocional se hace visible a través de tu carrera y tu estatus social. La seguridad emocional se vincula con el logro.",
    11: "La Luna en casa 11 — las amistades y los grupos sociales son importantes en tu mundo emocional. Las metas idealistas te nutren.",
    12: "La Luna en casa 12 — tus emociones fluyen a nivel subconsciente. La soledad, la meditación y el trabajo interior te sientan bien.",
}

NATAL_AY_ACISI_YORUMLARI_ES = {
    ("Ay","Güneş","Kavuşum"): [
        "Tus emociones y tu esencia están hoy en plena sintonía. Tu voz interior y tu lógica dicen lo mismo. Tu confianza aumenta y esa energía se irradia a tu entorno.",
        "Hay una unidad poco frecuente entre tu corazón y tu mente. Ves con claridad lo que quieres y avanzas con pasos seguros, guiado por tus sentimientos. Hoy siente hasta el final el poder de ser tú mismo.",
        "Día de integridad interior: tus sentimientos y tus pensamientos vibran en la misma frecuencia. Gracias a esa armonía puedes tomar incluso decisiones difíciles y proyectar una autoridad natural."
    ],
    ("Ay","Güneş","Karşıt"): [
        "Hay una búsqueda de equilibrio en tu mundo interior. Mientras tu lógica dice una cosa, tu corazón te arrastra hacia otra dirección. Esa tensión existe para mostrarte qué camino seguir.",
        "Puedes sentir un conflicto entre tus necesidades emocionales y tus metas del ego. Hoy escucha las dos voces. La reconciliación no está entre ambas, sino en abrazarlas a las dos.",
        "Un día en que los contrarios traen conciencia. Puede que vivas una tensión interna, pero te mostrará facetas tuyas que aún no has descubierto. Para encontrar tu equilibrio, intenta comprender ambos lados."
    ],
    ("Ay","Güneş","Kare"): [
        "Puedes sentirte atrapado entre tus emociones y tus metas. No saber hacia dónde ir es natural. Esta incertidumbre te abre espacio para encontrar una nueva dirección.",
        "Estás bajo una presión interna. Esta tensión entre tu corazón y tu mente es señal de que debes tomar una decisión. No la postergues; incluso un pequeño paso te aliviará.",
        "Hoy es un día de encuentro contigo mismo. Tus conflictos internos te ofrecen una oportunidad de crecer. No te resistas a las emociones incómodas; intenta comprenderlas: están aquí para enseñarte algo."
    ],
    ("Ay","Güneş","Trigon"): [
        "Hay una armonía natural entre tu mundo emocional y tu identidad. Hoy te resulta más fácil aceptarte tal como eres. Tu paz interior se refleja en el exterior.",
        "Un día de fluidez. Hay una conexión tersa entre tus sentimientos y tus acciones. Tu creatividad es alta y tus intuiciones están fuertes. Aprovecha esta energía.",
        "Un período en el que te sientes en paz contigo mismo. Gracias a tu armonía interna irradias serenidad a quienes te rodean. Hoy dedica tiempo a lo que disfrutas."
    ],
    ("Ay","Güneş","Sekstil"): [
        "Tienes a la puerta una hermosa oportunidad de expresar tus emociones. Una situación que aparezca hoy te ayudará a sacar a la luz tus sentimientos verdaderos.",
        "Se tiende un puente productivo entre tu mundo interior y el exterior. Un pasatiempo nuevo, un proyecto creativo o un espacio donde expresarte te sentará bien.",
        "Un día en que tu inteligencia emocional se eleva. Comprender a quienes te rodean y conectar con ellos se vuelve más fácil. Aprovecha esta oportunidad para una charla sincera."
    ],
    ("Ay","Venüs","Kavuşum"): [
        "Tu energía amorosa está hoy muy elevada. El calor de tu corazón se refleja en tu entorno. Volcarte hacia lo artístico y estético, rodearte de cosas bellas, te sentará bien.",
        "Te sientes emocionalmente lleno de ternura. Buscas instintivamente la belleza y la armonía. Hoy hazte un pequeño gesto; lo mereces.",
        "El equilibrio entre dar y recibir se establece hoy de forma natural. No dudes en expresar tu amor. Puedes inspirarte para trabajos que requieran creatividad."
    ],
    ("Ay","Venüs","Karşıt"): [
        "Puede que tengas que elegir entre tus necesidades emocionales y aquello que disfrutas. Pregúntate en qué ámbito quieres invertir más de ti mismo.",
        "Puedes sentir una insatisfacción interna. Lo que quieres y lo que necesitas puede no ser lo mismo. Hoy quédate un rato a solas y escúchate.",
        "Es momento de equilibrar el amor y el dinero. Si hay una desarmonía entre lo que valoras y la energía que gastas, hoy puedes notarla y corregirla."
    ],
    ("Ay","Venüs","Kare"): [
        "Puedes sentirte atrapado entre lo que disfrutas y tus responsabilidades. Si te cuesta dedicarte tiempo, incluso un pequeño descanso hará una gran diferencia.",
        "Tu deseo de gastar y la necesidad de ahorrar pueden chocar. Hoy, en tus decisiones, escucha tu lógica y no tu impulso. Que un capricho pasajero no te engañe.",
        "Puedes vivir un desequilibrio en las relaciones: dar demasiado y recibir poco, o al revés. Hoy revisa tus límites y protégete."
    ],
    ("Ay","Venüs","Trigon"): [
        "El amor y la belleza fluyen con naturalidad en tu vida. Tu paz interior se refleja en el exterior. Las actividades artísticas, la música o caminar en la naturaleza te sentarán bien.",
        "Hay una armonía natural con tu círculo social. Hoy pasar tiempo con tus seres queridos, cocinar algo rico o estar en un entorno estético te dará energía.",
        "Día para consentirte. Este aspecto armonioso entre Venus y la Luna te ofrece la oportunidad de ver el lado bello de la vida. Disfruta de los pequeños placeres."
    ],
    ("Ay","Venüs","Sekstil"): [
        "Puede que te espere un nuevo descubrimiento estético. Quizá un café nuevo, una exposición o una melodía. Hoy tu sensibilidad estética está alta; fíjate en lo que te rodea.",
        "Una linda oportunidad para socializar. Puedes conocer gente nueva o reencontrarte con viejos amigos. Tu comunicación será fluida y cálida.",
        "Puedes hallar una nueva manera de expresarte. Un día inspirador para tomar un pasatiempo o empezar un proyecto creativo."
    ],
    ("Ay","Mars","Kavuşum"): [
        "Tu energía y tus emociones se ponen en marcha al mismo tiempo. En tu interior hay un fuerte impulso de hacer. Canalizar esta energía hacia el deporte o una actividad física te sentará bien.",
        "Tus reacciones emocionales pueden ser más intensas de lo normal. Reconoce tu ira, pero aprende también a controlarla. Esta energía, bien canalizada, es un gran motor.",
        "Día de coraje y pasión. Un momento perfecto para empezar algo que has estado postergando. Confía en tus instintos y actúa."
    ],
    ("Ay","Mars","Karşıt"): [
        "Puedes verte entre tus deseos internos y las exigencias del mundo exterior. Puede que tengas que esforzarte por equilibrar tus anhelos y tus obligaciones.",
        "Puedes sentirte tenso emocionalmente y reaccionar con más dureza de lo usual. Antes de entrar en un conflicto, respira hondo y piensa.",
        "La energía de los demás puede afectarte. Protege tus propios límites y no cargues con los problemas ajenos. El ejercicio físico te ayudará a liberar esa tensión."
    ],
    ("Ay","Mars","Kare"): [
        "Dentro de ti puede estar a punto un volcán. Una pequeña chispa puede convertirse en una gran explosión. Hoy haz un esfuerzo consciente por mantener la calma.",
        "Estás atrapado entre tu ira emocional y tu lógica. Quieres romper algo, pero sabes que debes detenerte. Una actividad física puede aliviar esa presión.",
        "Puedes sentir impaciencia e inquietud. Como si todo te molestara. Es un período pasajero; date tiempo y no te exijas de más."
    ],
    ("Ay","Mars","Trigon"): [
        "Tu energía y tus emociones están en perfecta sintonía. Tienes un alto potencial de éxito en todo lo que quieras hacer. Ideal para el deporte, proyectos creativos o nuevos comienzos.",
        "Tu coraje y tu determinación están en la cima. Incluso una tarea que parece difícil hoy te resultará fácil. Haces instintivamente los movimientos correctos y te entregas al flujo.",
        "Un día en que te sientes fuerte, tanto física como emocionalmente. Confías en ti y no pierdes tiempo en ponerte en marcha. Aprovecha esta energía de forma productiva."
    ],
    ("Ay","Mars","Sekstil"): [
        "Una buena oportunidad para empezar una nueva actividad física. La danza, el yoga, correr o un deporte de equipo te pueden sentar bien. Tu cuerpo y tu alma quieren trabajar juntos.",
        "Tu valentía emocional aumenta. Una oportunidad que aparezca hoy puede despertar al guerrero que llevas dentro. Enfréntate a tus miedos.",
        "Puedes descubrir un nuevo ámbito donde dirigir tu energía. Un pasatiempo, un proyecto o un deporte te dará satisfacción tanto física como emocional."
    ],
    ("Ay","Jüpiter","Kavuşum"): [
        "Tus sentimientos de optimismo y alegría están hoy por las nubes. Ves la vida desde una perspectiva más amplia y te acercas al futuro con esperanza. Permanece abierto a nuevas experiencias.",
        "Sientes una expansión y liberación emocional. Hay una sensación interior de abundancia y plenitud. Compartir esta energía con tus seres queridos te sentará bien.",
        "Aumenta tu deseo de aventura y descubrimiento. Ver un sitio nuevo, conocer una cultura distinta o simplemente caminar por una calle desconocida puede sentarte de maravilla."
    ],
    ("Ay","Jüpiter","Karşıt"): [
        "Puedes quedar entre tu deseo de crecimiento interior y las limitaciones del mundo exterior. Quieres más, pero las condiciones actuales pueden frenarte. Ten paciencia.",
        "Tienes tendencia a exagerar. Puede costarte controlar tus emociones o tus gastos. Hoy intenta ser moderado.",
        "Puede que necesites equilibrar las expectativas ajenas con tus propios deseos. Escucha tu voz interior para encontrar tu propio camino."
    ],
    ("Ay","Jüpiter","Kare"): [
        "El optimismo excesivo puede ensombrecer tu realismo. Soñar en grande es hermoso, pero hoy debes mantener los pies en la tierra. Da un paso atrás y evalúa la situación objetivamente.",
        "Tiendes a exagerar emocionalmente. Puede haber un desequilibrio entre lo que sientes y lo que haces. Hoy procura ser mesurado.",
        "Puede que sientas la necesidad de demostrar tu valía. Pero no te fuerces para impresionar a los demás. Ser aceptado tal como eres es la mayor libertad."
    ],
    ("Ay","Jüpiter","Trigon"): [
        "Tu sensación interna de abundancia fluye con naturalidad. La vida puede ofrecerte hermosas sorpresas. La gratitud calentará hoy tu corazón.",
        "Aumenta tu deseo de aprender y explorar. Un gran día para leer un libro, ver un documental o aprender una nueva habilidad. Tu mente y tu corazón trabajan juntos.",
        "Tu energía optimista contagia a quienes te rodean. Hoy comparte tus pensamientos positivos e inspira a tus seres queridos. Ideal para socializar."
    ],
    ("Ay","Jüpiter","Sekstil"): [
        "Puede haber a la puerta una nueva oportunidad de aprendizaje. Un programa de formación, un seminario o un taller pueden interesarte. Es un buen momento para invertir en tu crecimiento personal.",
        "Un evento cultural o un plan de viaje puede sentarte bien. Ver perspectivas distintas ampliará tus horizontes. Hoy prueba algo nuevo.",
        "Confía en tu sabiduría interior. Si hay algo que sabes con certeza, no dudes en compartirlo. Puedes inspirar a quienes te rodean."
    ],
    ("Ay","Satürn","Kavuşum"): [
        "Puedes sentirte emocionalmente más serio y distante. Hay un cuestionamiento en tu mundo interior. Es parte de tu proceso de maduración emocional. Sé honesto contigo mismo.",
        "Sientes el peso de tus responsabilidades. Tu carga emocional puede haber aumentado. Hoy muéstrate compasivo contigo y recuerda que no estás solo.",
        "Día de descubrir tus límites internos. Cuestionas dónde detenerte y dónde avanzar. Esta disciplina te dará, a largo plazo, seguridad emocional."
    ],
    ("Ay","Satürn","Karşıt"): [
        "Vives un conflicto entre tus necesidades emocionales y tus responsabilidades. Tu voz interior te dice una cosa, mientras el mundo exterior espera otra. Encontrar el equilibrio está en tus manos.",
        "Puede pesar la sensación de soledad. Puedes creer que los demás no te comprenden. Es un sentimiento pasajero; en lugar de aislarte, acércate a un amigo.",
        "Una carga emocional del pasado puede aflorar hoy. Perdonar y soltar aliviará ese peso. Date tiempo."
    ],
    ("Ay","Satürn","Kare"): [
        "Te sientes bajo presión emocional. Puede que en algún ámbito te consideres insuficiente o poco preparado. Ve esta sensación como una oportunidad de aprendizaje.",
        "Aumenta tu tendencia a autocríticarte. El perfeccionismo puede darte hoy malos momentos. Recuerda que no todo tiene que ser perfecto.",
        "Puedes encontrarte con un obstáculo emocional. Tus planes pueden retrasarse o vivirá una decepción. Es una prueba que te hará más fuerte."
    ],
    ("Ay","Satürn","Trigon"): [
        "Gracias a tu disciplina y madurez emocional superas las dificultades con facilidad. Ser consciente de tu fuerza interior te da confianza.",
        "Adoptas un enfoque emocional estructurado. Aprendes a gestionar tus emociones en lugar de reprimirlas. Es señal de crecimiento.",
        "Un buen día para centrarte en tus metas de largo plazo. Gracias a tu estabilidad emocional puedes dar pasos firmes y mirar el futuro con seguridad."
    ],
    ("Ay","Satürn","Sekstil"): [
        "Se presenta una oportunidad para ser más organizado y planificado emocionalmente. Un buen momento para adquirir un hábito o crear una rutina.",
        "Una lección del pasado puede resultarte útil hoy. En un tema que antes te costaba, ahora te sientes más maduro y preparado.",
        "Un consejo de un mentor o guía te hará bien. La perspectiva de alguien con experiencia puede orientarte en un asunto emocional."
    ],
    ("Ay","Merkür","Kavuşum"): [
        "Aumenta tu capacidad de expresar tus emociones. Poner en palabras lo que llevas dentro se vuelve más fácil. Un gran día para escribir, hablar o contarle a alguien lo que te pasa.",
        "Tus intuiciones y tu lógica trabajan a la vez. Comprendes un tema tanto con el corazón como con la mente. Si hay una contradicción entre ambos, hoy se aclarará.",
        "Hay una conexión fuerte entre tu mente y tu corazón. Tu inteligencia emocional está alta y crece tu capacidad de entender a las personas y empatizar con ellas."
    ],
    ("Ay","Merkür","Karşıt"): [
        "Vives una contradicción entre tus emociones y tus pensamientos. Tu lógica dice una cosa y tu corazón siente otra. Escucha a ambos.",
        "Puede haber malentendidos en la comunicación con los demás. Si hay una diferencia entre lo que dices y lo que sientes, intenta cerrarla hoy.",
        "Puedes darle demasiadas vueltas a un tema emocional y confundirte. A veces hay que sentir en lugar de analizar. Calla tu mente y escucha a tu corazón."
    ],
    ("Ay","Merkür","Kare"): [
        "Puedes sentirte mentalmente disperso y con dificultad para concentrarte. Tus emociones pueden estar nublando tus pensamientos. Hoy evita tomar decisiones importantes.",
        "Puede haber una diferencia entre lo que quieres decir y lo que dices. Si te cuesta expresarte, escribir puede ayudarte.",
        "Puedes caer en pensamientos obsesivos sobre un tema emocional. Para salir de ese bucle, dirige tu mente hacia otra cosa."
    ],
    ("Ay","Merkür","Trigon"): [
        "Un día perfecto para expresar tus emociones. Tu voz interior es clara y tus palabras fluyen. Contarle a alguien lo que sientes o escribir una carta te hará bien.",
        "Tus intuiciones y tu lógica están en armonía. Sientes y comprendes un tema al mismo tiempo. Gracias a esa visión integral puedes tomar decisiones acertadas.",
        "Aumentan tu capacidad de aprendizaje y comunicación. Un día ideal para aprender un idioma nuevo, leer un libro o investigar un tema."
    ],
    ("Ay","Merkür","Sekstil"): [
        "Tienes a la puerta una nueva oportunidad de comunicación. Puedes recibir noticias de un viejo amigo o mantener una conversación profunda con alguien nuevo.",
        "Puedes encontrarte en una situación donde usar tu inteligencia emocional. Dar un consejo a alguien o comprenderlo te hará bien.",
        "Puedes inspirarte para escribir o crear algo. Llevar un diario, escribir poesía o publicar un blog te ayudará a expresar tus emociones."
    ],
    ("Ay","Uranüs","Kavuşum"): [
        "Puedes sentir una necesidad repentina de liberación emocional. Las rutinas te asfixian y quieres hacer algo nuevo y distinto. Confía en tus instintos.",
        "Puedes vivir una toma de conciencia emocional inesperada. De pronto empiezas a ver un tema con gran claridad. Aprovecha ese momento de iluminación.",
        "Un día en que valoras tu libertad. Quieres vivir según tus propias reglas y no según las expectativas ajenas. Usa esta energía de manera creativa."
    ],
    ("Ay","Uranüs","Karşıt"): [
        "Puedes quedar entre tu deseo de estabilidad y tu necesidad de cambio. Por un lado quieres estar seguro y por otro superar tus límites. Esta disyuntiva te ofrece una oportunidad de crecer.",
        "Hay tensión entre las expectativas ajenas y tu necesidad de libertad. Para encontrar tu propio camino puede que debas ser valiente.",
        "Puedes reaccionar emocionalmente de forma impulsiva y luego arrepentirte. Antes de decir o hacer algo, piénsalo una vez más."
    ],
    ("Ay","Uranüs","Kare"): [
        "Puedes vivir una explosión emocional inesperada. Una emoción que has reprimido durante mucho tiempo puede aflorar de repente. No te sorprendas; es natural.",
        "La ruptura de tu rutina puede incomodarte. Tener que salirte de tus planes, aunque al principio sea irritante, puede abrir una nueva puerta.",
        "Puedes vivir altibajos emocionales. Sentirte feliz un momento y triste al siguiente. Es un período pasajero; déjate llevar por el flujo."
    ],
    ("Ay","Uranüs","Trigon"): [
        "Un día en que descubres tu libertad interior. Disfrutas de vivir según tus propias reglas. Tu creatividad y originalidad impactan a tu entorno.",
        "Puedes vivir un estallido de inspiración repentino. Puede venirte a la mente una idea perfecta para un proyecto creativo. No la dejes escapar; anótala de inmediato.",
        "El cambio y la novedad te sientan bien. Un entorno distinto, gente nueva o una experiencia poco habitual pueden sacar a la luz tu potencial interior."
    ],
    ("Ay","Uranüs","Sekstil"): [
        "Tienes a la puerta la oportunidad de vivir una experiencia nueva y poco habitual. Probar algo que nunca has hecho puede darte energía.",
        "Puedes adquirir una perspectiva distinta sobre un tema. Un pensamiento fuera de lo común puede ayudarte a encontrar una solución creativa a un problema.",
        "Interesarte por la tecnología o un campo innovador puede sentarte bien. Un buen día para descubrir una aplicación nueva o empezar un proyecto digital."
    ],
    ("Ay","Neptün","Kavuşum"): [
        "Tus intuiciones están hoy muy fuertes. Sientes a las personas y los acontecimientos más allá de las palabras. La meditación, la música o el arte te darán una paz profunda.",
        "Puedes sentir que tus límites emocionales se disuelven, que estás conectado con todo. Esa sensación de fusión te está sanando.",
        "Tu imaginación y tus emociones se entrelazan. Tus sueños pueden ser más vívidos y tus intuiciones más claras. Hoy presta atención a tu voz interior."
    ],
    ("Ay","Neptün","Karşıt"): [
        "Puedes oscilar entre la realidad y tu mundo imaginario. Puede que veas las cosas distinto de como son. Hoy evita tomar decisiones importantes.",
        "Puedes vivir una confusión emocional y tener dificultad para ver con claridad un tema. Retírate un momento y aclara la situación.",
        "La energía de los demás puede afectarte con facilidad. Tus límites emocionales pueden estar debilitados. Crea un espacio donde puedas estar a solas para protegerte."
    ],
    ("Ay","Neptün","Kare"): [
        "Puedes sentirte perdido en una niebla emocional. Distinguir lo real de lo imaginario puede volverse difícil. Hoy sé honesto contigo mismo.",
        "Puede aumentar tu tendencia a la evasión. Para alejarte de la realidad puedes recurrir a los sueños, al alcohol o a otro tipo de dependencia. Sé consciente y busca alternativas sanas.",
        "Es alta la probabilidad de una decepción o un engaño. No confíes de más en alguien o en una situación. Sé realista."
    ],
    ("Ay","Neptün","Trigon"): [
        "Hay un flujo natural entre tus intuiciones y tu imaginación. Un día perfecto para un proyecto artístico, un trabajo creativo o una práctica espiritual.",
        "Sientes paz interior y serenidad. Pasar tiempo en la naturaleza, escuchar música o meditar te dará una profunda satisfacción.",
        "Tu capacidad de empatía es muy alta. Tienes un talento natural para comprender a las personas y ayudarlas. Hoy usa ese poder."
    ],
    ("Ay","Neptün","Sekstil"): [
        "Se presenta una oportunidad que alimentará tu creatividad. Un taller de arte, una salida fotográfica o un evento musical pueden sentarte bien.",
        "Puedes vivir una experiencia espiritual. Un libro, una conversación o un recuerdo de la naturaleza puede darte una comprensión profunda.",
        "Tus intuiciones te guiarán hoy. Si sientes algo sobre un tema, tómalo en serio. Aunque tu lógica no lo explique, tu corazón sabe qué es lo correcto."
    ],
    ("Ay","Plüton","Kavuşum"): [
        "Estás justo en medio de una transformación emocional. Las emociones reprimidas pueden aflorar hoy. Aunque parezca aterrador, ese enfrentamiento te liberará.",
        "Un día en que tomas conciencia de tu fuerza interior. Soltar lo que no puedes controlar es, en realidad, tu mayor forma de empoderamiento. Permanece abierto a la transformación.",
        "Vives una profunda purificación emocional. Heridas antiguas y traumas pasados pueden mostrarse hoy. Es una oportunidad para sanarlos."
    ],
    ("Ay","Plüton","Karşıt"): [
        "Libras una batalla entre controlar y soltar. Cuanto más intentas retener una situación, más sientes que la pierdes. Soltar es la mayor victoria.",
        "La sombra de los demás puede influir en ti. No cargues con las emociones que otra persona proyecta sobre ti. Recuerda tu propio poder.",
        "Es momento de un ajuste de cuentas emocional. Un acontecimiento del pasado puede volver a hoy. Pero esta vez no tienes que reaccionar del mismo modo."
    ],
    ("Ay","Plüton","Kare"): [
        "Tu intensidad emocional está en su punto máximo. Un pequeño acontecimiento puede convertirse en una gran reacción. Hoy cuídate de más y reconoce tus desencadenantes.",
        "Vives una lucha de poder interna. Puedes sentirte atrapado entre tus viejos hábitos y tu nuevo yo. La transformación puede ser dolorosa, pero es necesaria.",
        "Los pensamientos y emociones obsesivos pueden apoderarse de ti. Si te cuesta soltar un tema, buscar apoyo profesional puede ser una buena idea."
    ],
    ("Ay","Plüton","Trigon"): [
        "Tu poder de transformación emocional fluye con naturalidad. Puedes resolver con facilidad un tema difícil y actuar con comprensión profunda.",
        "Tu energía de sanación interior está alta. Estás en un período poderoso para cerrar viejas heridas y romper patrones antiguos.",
        "Aumenta tu capacidad de sanar y transformar a los demás. Apoyar a alguien, guiarlo, te hará bien. En ese proceso también te sanas a ti."
    ],
    ("Ay","Plüton","Sekstil"): [
        "Puedes ganar una profunda visión psicológica. Un sueño, una sesión de terapia o una conversación profunda pueden enseñarte algo nuevo sobre ti.",
        "Investigarte un tema del pasado o explorar tu historia familiar puede sentarte bien. Comprender tus raíces puede explicar tu comportamiento actual.",
        "Puedes conocer una verdad oculta sobre un tema. Aunque al principio sea conmovedor, a largo plazo ese conocimiento te traerá libertad."
    ],
}

def _ay_ortami_yorumu(ay_burc, ay_ev):
    """Ay'ın bulunduğu burç ve eve göre ortam tanımı döndürür."""
    _ES = _i18n_get_lang() == "es"
    if _ES:
        burc_tanim = AY_BURC_TANIMLARI_ES.get(ay_burc, "Tu Luna está dando forma a tu mundo emocional.")
        ev_tanim = AY_EV_TANIMLARI_ES.get(ay_ev, "")
    else:
        _EN = _i18n_get_lang() == "en"
        burc_tanim = AY_BURC_TANIMLARI.get(ay_burc, ("Your Moon is shaping your emotional world." if _EN else "Ay duygusal dünyanızı şekillendiriyor."))
        ev_tanim = AY_EV_TANIMLARI.get(ay_ev, "")
    return f"{burc_tanim} {ev_tanim}"

def _aspekt_yorumu_sec(gezegen1, gezegen2, aci_turu, index=0):
    """NATAL_AY_ACISI_YORUMLARI'ndan bir yorum seçer."""
    _ES = _i18n_get_lang() == "es"
    if _ES:
        sozluk = NATAL_AY_ACISI_YORUMLARI_ES
    else:
        _EN = _i18n_get_lang() == "en"
        sozluk = NATAL_AY_ACISI_YORUMLARI_EN if _EN else NATAL_AY_ACISI_YORUMLARI
    key = (gezegen1, gezegen2, aci_turu)
    if key in sozluk:
        return sozluk[key][index % 3]
    # Try reverse order
    rev_key = (gezegen2, gezegen1, aci_turu)
    if rev_key in sozluk:
        return sozluk[rev_key][index % 3]
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
    FALLBACK_ES = {
        "Kavuşum": "Esta energía de conjunción está fortaleciendo tu mundo emocional.",
        "Karşıt": "Esta oposición pone a prueba tu equilibrio emocional y trae conciencia.",
        "Kare": "Este aspecto desafiante ofrece una prueba para tu crecimiento emocional.",
        "Trigon": "Este aspecto armonioso favorece tu flujo emocional.",
        "Sekstil": "Este aspecto de oportunidad abre una puerta para tu desarrollo emocional.",
    }
    if _ES:
        return FALLBACK_ES.get(aci_turu, "Este aspecto está afectando tu mundo emocional.")
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
                    if _i18n_get_lang() == "en":
                        aciklamalar.append(f"{pdf_label(aci_turu)} ∟ {pdf_label(gez)} (orb {orb:.1f}°): {yorum}")
                    else:
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
        _ES = _i18n_get_lang() == "es"
        GUN_AD = (["Mon","Tue","Wed","Thu","Fri","Sat","Sun"] if _EN else (["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"] if _ES else ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"]))
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
        minor_oran = 27.32166 / 365.2422
        for kaydir in range(baslangic_gunu, baslangic_gunu + gun_sayisi):
            # Progressed JD = birth JD + current age (secondary) + N * minor_oran (27.3 days = 1 year)
            jd_prog = jd_natal + yas + kaydir * minor_oran
            
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
                    if _i18n_get_lang() != "tr":
                        aspekt_yorumlari.append(f"{pdf_label(hedef)} {pdf_label(aci_turu)}: {yorum}")
                    else:
                        aspekt_yorumlari.append(f"{hedef} {aci_turu}: {yorum}")
            
            if not aspekt_yorumlari:
                aspekt_yorumlari.append(("No prominent Moon aspect was found for this period." if _EN else ("No se encontró ningún aspecto prominente de la Luna para este período." if _ES else "Bu dönem için belirgin bir Ay açısı bulunamadı.")))
            
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

_TR_BLOCK_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc", "/api/debug_ephe"}

# ─── Rate limit (basit, in-memory) ───
import time as _rl_time
_RL_BUCKET = {}
_RL_LIMIT = int(os.getenv("RL_LIMIT", "30"))  # 30 req / 60s / IP
_RL_WINDOW = 60

@app_fast.middleware("http")
async def _rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.url.path not in _TR_BLOCK_PATHS:
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.client.host if request.client else "unknown"
        now = _rl_time.time()
        bucket = _RL_BUCKET.get(ip)
        if bucket:
            count, start = bucket
            if now - start > _RL_WINDOW:
                _RL_BUCKET[ip] = [1, now]
            else:
                if count >= _RL_LIMIT:
                    return JSONResponse(status_code=429, content={"error": "Rate limit, try later"})
                bucket[0] += 1
        else:
            _RL_BUCKET[ip] = [1, now]
        # temizlik (1000+ IP birikmesin)
        if len(_RL_BUCKET) > 2000:
            for k in list(_RL_BUCKET.keys())[:1000]:
                del _RL_BUCKET[k]
    return await call_next(request)

# ─── IP ülke gate (TR hariç global) ───
# Aktif etmek için env: GLOBAL_EXCLUDE_TR=1 (Render dashboard'da ayarla)

@app_fast.middleware("http")
async def _tr_ip_gate(request: Request, call_next):
    if os.getenv("GLOBAL_EXCLUDE_TR") == "1" and request.url.path not in _TR_BLOCK_PATHS:
        country = (request.headers.get("CF-IPCountry") or request.headers.get("cf-ipcountry") or "").upper()
        # Fallback: X-Country custom header (test için)
        if not country:
            country = (request.headers.get("X-Country") or "").upper()
        if country == "TR":
            return JSONResponse(status_code=403, content={"error": "TR region excluded — please use the TR app", "code": "TR_BLOCKED"})
    return await call_next(request)

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

# ─── ES veri alanı lokalizasyonu ───
# API'nin ürettiği bazı teknik alanlar (meslek, potansiyel, Arap noktaları,
# asteroid konumları) burç/gezegen/kategori adlarını Türkçe üretir. Bu harita
# sayesinde ES modunda bu alanlar İspanyolca görünür.
_ES_VERI_KELIMELER = {
    # Gezegenler
    "Güneş": "Sol", "Ay": "Luna", "Merkür": "Mercurio", "Venüs": "Venus",
    "Mars": "Marte", "Jüpiter": "Júpiter", "Satürn": "Saturno",
    "Uranüs": "Urano", "Neptün": "Neptuno", "Plüton": "Plutón",
    "Chiron": "Quirón", "Ceres": "Ceres", "Pallas": "Palas",
    "Juno": "Juno", "Vesta": "Vesta", "KAD": "Nodo Norte", "GD": "Nodo Sur",
    # Burçlar
    "Koç": "Aries", "Boğa": "Tauro", "İkizler": "Géminis", "Yengeç": "Cáncer",
    "Aslan": "Leo", "Başak": "Virgo", "Terazi": "Libra", "Akrep": "Escorpio",
    "Yay": "Sagitario", "Oğlak": "Capricornio", "Kova": "Acuario", "Balık": "Piscis",
    # Açılar
    "Kavuşum": "Conjunción", "Karşıt": "Oposición", "Kare": "Cuadratura",
    "Zıtlık": "Oposición", "Trine": "Trino", "Trigon": "Trino", "Sextil": "Sextil",
    # Gün adları
    "Pazartesi": "Lunes", "Salı": "Martes", "Çarşamba": "Miércoles",
    "Perşembe": "Jueves", "Cuma": "Viernes", "Cumartesi": "Sábado",
    "Pazar": "Domingo",
    # Ay adları
    "Ocak": "Enero", "Şubat": "Febrero", "Mart": "Marzo", "Nisan": "Abril",
    "Mayıs": "Mayo", "Haziran": "Junio", "Temmuz": "Julio", "Ağustos": "Agosto",
    "Eylül": "Septiembre", "Ekim": "Octubre", "Kasım": "Noviembre",
    "Aralık": "Diciembre",
    # Kategoriler
    "Sağlık/Tıp": "Salud/Medicina", "İletişim": "Comunicación", "Spor": "Deportes",
    "Maneviyat": "Espiritualidad", "Sanatsal Yetenek": "Talento Artístico",
    "Liderlik": "Liderazgo", "Stratejik Zeka": "Inteligencia Estratégica",
    "Yardımseverlik": "Solidaridad", "Girişimcilik": "Emprendimiento",
    "Akademik/Araştırma": "Académico/Investigación", "Zanaatkarlık": "Artesanía",
    "Askeriye": "Militar", "Bilgelik": "Sabiduría", "Hukuk/Politika": "Derecho/Política",
    "Zihinsel Yetenek": "Talento Mental", "Yenilikçilik": "Innovación",
    # Açı türleri (alternatif yazımlar)
    "Sekstil": "Sextil",
    # Arap noktaları (ebeveyn-çocuk)
    "Baba Noktası": "Punto del Padre", "Anne Noktası": "Punto de la Madre",
    "Çocuk Ruhu": "Alma del Niño", "Koruma Noktası": "Punto de Protección",
    "Eğitim Noktası": "Punto de Educación", "Sınır Noktası": "Punto del Límite",
    "Bağlanma Noktası": "Punto de Vínculo", "Sorumluluk": "Responsabilidad",
    # Arap noktaları (ilişki)
    "Şans Noktası": "Parte de la Fortuna", "Ruh Noktası": "Punto del Espíritu",
    "Evlilik Noktası": "Punto del Matrimonio", "Aşk Noktası": "Punto del Amor",
    "Tutku Noktası": "Punto de la Pasión", "Para Noktası": "Punto del Dinero",
    # Ev
    "Ev": "Casa",
}

def _es_cv_text(metin):
    """Bilinen Türkçe gezegen/burç/açı/ev adlarını İspanyolcaya çevirir."""
    if not isinstance(metin, str):
        return metin
    for _tr, _es in _ES_VERI_KELIMELER.items():
        metin = re.sub(r"(?<![A-Za-zÀ-ÖØ-öø-ÿ])" + re.escape(_tr) + r"(?![A-Za-zÀ-ÖØ-öø-ÿ])", _es, metin)
    return metin

def _es_localize(data):
    """ES modunda API yanıtındaki Türkçe veri alanlarını İspanyolcaya çevirir."""
    if not isinstance(data, dict):
        return data
    # potansiyel_alanlar
    for p in data.get("potansiyel_alanlar") or []:
        if isinstance(p, dict):
            p["alan"] = _es_cv_text(p.get("alan", ""))
            p["aci"] = _es_cv_text(p.get("aci", ""))
    # meslek_onerileri
    for m in data.get("meslek_onerileri") or []:
        if not isinstance(m, dict):
            continue
        m["alan"] = _es_cv_text(m.get("alan", ""))
        if isinstance(m.get("gezegenler"), list):
            m["gezegenler"] = [_es_cv_text(g) for g in m["gezegenler"]]
        m["mc_burc"] = _es_cv_text(m.get("mc_burc", ""))
        m["mc_yonetici"] = _es_cv_text(m.get("mc_yonetici", ""))
        m["mc_yonetici_konum"] = _es_cv_text(m.get("mc_yonetici_konum", ""))
        m["aci_detaylari"] = _es_cv_text(m.get("aci_detaylari", ""))
        if isinstance(m.get("sabit_yildizlar"), list):
            m["sabit_yildizlar"] = [_es_cv_text(s) for s in m["sabit_yildizlar"]]
    # arap_sinastri (ebeveyn-çocuk ve sevgili modları)
    for b in data.get("arap_sinastri") or []:
        if not isinstance(b, dict):
            continue
        for _k in ("nokta_a", "nokta_b", "kaynak", "hedef", "nokta", "gezegen"):
            if b.get(_k):
                b[_k] = _es_cv_text(b[_k])
    # arap_noktalari (nokta adı anahtarları - hem dış hem iç anahtarlar)
    arap_noktalari = data.get("arap_noktalari")
    if isinstance(arap_noktalari, dict):
        def _arap_nokta_cevir(d):
            if not isinstance(d, dict):
                return d
            return {_es_cv_text(k): _arap_nokta_cevir(v) if isinstance(v, dict) else v for k, v in d.items()}
        data["arap_noktalari"] = _arap_nokta_cevir(arap_noktalari)
    # asteroit_konumlar
    for a in data.get("asteroit_konumlar") or []:
        if isinstance(a, dict):
            a["burc"] = _es_cv_text(a.get("burc", ""))
    # progression açı türleri
    for pr in data.get("progression") or []:
        if isinstance(pr, dict) and isinstance(pr.get("ay_aci_yorumlari"), list):
            for a in pr["ay_aci_yorumlari"]:
                if isinstance(a, dict) and a.get("aci_turu"):
                    a["aci_turu"] = _es_cv_text(a["aci_turu"])
    # hava_durumu (gün adı + yorum + açı içi gezegen/açı adları)
    for h in data.get("hava_durumu") or []:
        if not isinstance(h, dict):
            continue
        if h.get("gun_ad"):
            h["gun_ad"] = _es_cv_text(h["gun_ad"])
        if h.get("ay_burc"):
            h["ay_burc"] = _es_cv_text(h["ay_burc"])
        if h.get("yorum"):
            h["yorum"] = _es_cv_text(h["yorum"])
        if isinstance(h.get("acilar"), list):
            for a in h["acilar"]:
                if isinstance(a, dict) and a.get("yorum"):
                    a["yorum"] = _es_cv_text(a["yorum"])
                elif isinstance(a, str):
                    h["acilar"] = [_es_cv_text(x) if isinstance(x, str) else x for x in h["acilar"]]
    # sabianlar
    for s in data.get("sabianlar") or []:
        if not isinstance(s, dict):
            continue
        if s.get("gezegen"):
            s["gezegen"] = _es_cv_text(s["gezegen"])
        if s.get("derece_str"):
            s["derece_str"] = _es_cv_text(s["derece_str"])
    # asteroitler
    for a in data.get("asteroitler") or []:
        if isinstance(a, dict) and a.get("gezegen"):
            a["gezegen"] = _es_cv_text(a["gezegen"])
    # minor_progress
    for mp in data.get("minor_progress") or []:
        if not isinstance(mp, dict):
            continue
        if mp.get("gun_ad"):
            mp["gun_ad"] = _es_cv_text(mp["gun_ad"])
        if mp.get("ay_burc"):
            mp["ay_burc"] = _es_cv_text(mp["ay_burc"])
        if mp.get("gunes_burc"):
            mp["gunes_burc"] = _es_cv_text(mp["gunes_burc"])
    # hayat_alanlari onerileri
    for hl in data.get("hayat_alanlari") or []:
        if not isinstance(hl, dict):
            continue
        if isinstance(hl.get("oneriler"), list):
            for o in hl["oneriler"]:
                if isinstance(o, dict) and o.get("metin"):
                    o["metin"] = _es_cv_text(o["metin"])
    # chart_yorumu_gezegenler ve chart_yorumu_acilar
    for g in data.get("chart_yorumu_gezegenler") or []:
        if isinstance(g, dict) and g.get("gezegen"):
            g["gezegen"] = _es_cv_text(g["gezegen"])
    for a in data.get("chart_yorumu_acilar") or []:
        if isinstance(a, dict) and a.get("baslik"):
            a["baslik"] = _es_cv_text(a["baslik"])
    # minor_progress_6month
    if data.get("minor_progress_6month"):
        data["minor_progress_6month"] = _es_cv_text(data["minor_progress_6month"])
    # astrokartografi etkileri
    _skor = (data.get("astrokartografi") or {}).get("skor")
    if isinstance(_skor, dict) and isinstance(_skor.get("etkiler"), list):
        _skor["etkiler"] = [_es_cv_text(e) for e in _skor["etkiler"]]
    # yildiz_muhurleri
    for y in data.get("yildiz_muhurleri") or []:
        if not isinstance(y, dict):
            continue
        if y.get("baslik"):
            y["baslik"] = _es_cv_text(y["baslik"])
        if y.get("icerik"):
            y["icerik"] = _es_cv_text(y["icerik"])
    # karmik_ev raporlari
    _ke = data.get("karmik_ev")
    if isinstance(_ke, dict):
        for _rk in ("rapor_a", "rapor_b"):
            if isinstance(_ke.get(_rk), list):
                _ke[_rk] = [_es_cv_text(x) if isinstance(x, str) else x for x in _ke[_rk]]
    return data

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
    try:
        _isim = getattr(girdi, "lang", "tr")
    except Exception:
        _isim = "tr"
    def _dondur(r_):
        if _isim == "es":
            return _es_localize(r_), None
        return r_, None
    r = _ANALIZ_CACHE.get(h)
    if r is not None:
        return _dondur(r)
    ev = _ANALIZ_RUNNING.get(h)
    if ev is not None:
        ev.wait()
        r = _ANALIZ_CACHE.get(h)
        if r is not None:
            return _dondur(r)
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
            return _dondur(r)
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
        e = e.replace("↑ Yükselen", "↑ Ascendant").replace("↓ Alçalan", "↓ Descendant").replace("⌃ MC", "MC Axis").replace("⌄ IC", "IC Axis")
    elif _i18n_get_lang() == "es":
        e = e.replace("↑ Ascendente", "eje Ascendente").replace("↑ Yükselen", "eje Ascendente").replace("↓ Descendente", "eje Descendente").replace("↓ Alçalan", "eje Descendente").replace("⌃ MC", "eje MC").replace("⌄ IC", "eje IC")
    else:
        e = e.replace("↑ Yükselen", "Yükselen ekseni").replace("↓ Alçalan", "Alçalan ekseni").replace("⌃ MC", "MC ekseni").replace("⌄ IC", "IC ekseni")
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
    _ES = _i18n_get_lang() == "es"
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
            y -= boyut + 5
        return y

    def yazi_olcul(metin, font="DejaVu", boyut=8.5, max_genislik=90):
        """Calculate how tall the text block will be."""
        satirlar = _wrap_text(metin, max_genislik)
        return len(satirlar) * (boyut + 5)

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
    c.drawCentredString(w / 2, 130, "FAST — Synastry Technique  |  v4.0" if _EN else ("FAST — Técnica de Sinastría  |  v4.0" if _ES else "FAST — Sinastri Tekniği  |  v4.0"))
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
        y = sayfa_basligi("Natal Chart Interpretation" if _EN else ("Interpretación de la Carta Natal" if _ES else "Doğum Haritası Yorumu"), numara=str(bolum_no[0]))
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
                    g1d, g2d = pdf_label(g1), pdf_label(g2)
                    c.drawString(SOL + 6, y - 2, f"✦ {GEZEGEN_GLIF.get(g1, '')} {g1d} – {GEZEGEN_GLIF.get(g2, '')} {g2d}")
                    if aci_adi:
                        c.setFillColor(altin)
                        c.drawString(SOL + 8 + c.stringWidth(f"✦ {GEZEGEN_GLIF.get(g1, '')} {g1d} – {GEZEGEN_GLIF.get(g2, '')} {g2d}", "DejaVu-Bold", 9.5), y - 2, f"{ACI_GLIF.get(aci_adi, '')} {pdf_label(aci_adi)}")
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
            ust_bilgi = (f"{pdf_label(burc)}, House {ev_no} ({derece}°)" if _EN else (f"{pdf_label(burc)}, Casa {ev_no} ({derece}°)" if _ES else f"{burc} burcu, {ev_no}. Ev ({derece}°)")) if burc else (f"House {ev_no} ({derece}°)" if _EN else (f"Casa {ev_no} ({derece}°)" if _ES else f"{ev_no}. Ev ({derece}°)"))
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
            c.drawString(SOL + 12, y - 16, f"✦ {pdf_label(_nokta_adi)}")
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
                    _gez_es2 = pdf_label(gez_ad) if _ES else gez_ad
                    parag = (f"{asto_ad} is in conjunction with your {gez_ad} energy." if _EN else (f"{asto_ad} está en conjunción con tu energía de {_gez_es2}." if _ES else f"{asto_ad} asteroidi {gez_ad} enerjinizle kavuşumda."))
                _gez_es = pdf_label(gez_ad) if _ES else gez_ad
                baslik = (f"✦ {asto_ad} — {gez_ad} ({fark}° conjunction)" if _EN else (f"✦ {asto_ad} — {_gez_es} ({fark}° conjunción)" if _ES else f"✦ {asto_ad} — {gez_ad} ({fark}° kavuşum)"))
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
                ak_burc_ad = pdf_label(ak_burc)
                ak_line = f"✦ {ak_ad} — {ak_burc_ad} ({ak_deg}°)  ·  {ak_etki}" if ak_etki else f"✦ {ak_ad} — {ak_burc_ad} ({ak_deg}°)"
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
            sembol = _strip_html(str(s.get('sembol','')))[:600]
            sembol = re.sub(r'^[\U0001F000-\U0001FAFF\uFE0F\u200D\s]*(?:Sabian Şifresi|Sabian Cipher) \(\d+°\):\s*', '', sembol)
            sembol = re.sub(r'[\U0001F000-\U0001FAFF\uFE0F\u20E3\u200D]', '', sembol)
            muhur = ""
            _muhur_etiketi = "Seal:" if _EN else ("Sello:" if _ES else "Mühür:")
            if "Mühür:" in sembol or "Seal:" in sembol:
                _ayrac = "Mühür:" if "Mühür:" in sembol else "Seal:"
                sembol, muhur = sembol.split(_ayrac, 1)
                muhur = (_muhur_etiketi + " " + muhur.strip())[:400]
            gez_isim = s.get('gezegen','')
            sembol_h = 30
            sembol_h += yazi_olcul(sembol.strip(), "DejaVu", 8, 86) + 16
            if muhur:
                sembol_h += yazi_olcul(muhur, "DejaVu-Oblique", 8, 86) + 10
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
            c.drawString(SOL + 14, y - 17, f"✦ {GEZEGEN_GLIF.get(gez_isim, '')} {pdf_label(gez_isim)}  —  {re.sub(r'(?<=\d°)\s*\S+$', lambda m: ' ' + pdf_label(m.group(0).strip()), (s.get('derece_str','') or str(s.get('derece',''))+'°'))}")
            c.setFillColor(altin)
            c.setFont("DejaVu-Bold", 7)
            c.drawRightString(SAG - 14, y - 16, "✦ Sabian Cipher" if _EN else ("✦ Símbolo Sabiano" if _ES else "✦ Sabian Şifresi"))
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
        y = metin_yaz(SOL, y, pdf_label("İlerleyen Ay'ınızın önümüzdeki 6 ay boyunca oluşturacağı açılar, aylık takvim düzeninde aşağıda gösterilmiştir."), "DejaVu", 8.5, acik, 95) - 14
        _leg_x = SOL
        for _renk, _leg_metin in (
            (HexColor('#8FC0E8'), pdf_label("■ Uyumlu açı (Trigon · Sekstil) · ")),
            (HexColor('#D08A96'), pdf_label("■ Zorlayıcı açı (Kare · Karşıt) · ")),
            (acik, pdf_label("□ Açı yoğunluğu düşük")),
        ):
            _leg_w = c.stringWidth(_leg_metin, "DejaVu", 8.5)
            if _leg_x + _leg_w > SAG - 6:
                y -= 12
                _leg_x = SOL
            c.setFillColor(_renk)
            c.drawString(_leg_x, y, _leg_metin)
            _leg_x += _leg_w + 12
        y -= 16

        import datetime as _dt_mod
        AY_ADLARI = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"] if _ES else (["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"] if not _EN else ["January","February","March","April","May","June","July","August","September","October","November","December"])
        HAFTALAR = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"] if _ES else (["Pzt","Sal","Çar","Per","Cum","Cmt","Paz"] if not _EN else ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])
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
                grid_h = 48 + satir_sayisi * HUCRE_H + 10
                onemli = [gd for gd in ay_gunleri if (gun_verileri[gd].get("aspekt_adet") or 0) >= 2]
                _onemli_bilgi = []
                _gruplar = []
                for _gd2 in onemli:
                    _pe2 = gun_verileri[_gd2]
                    _i0b = ((_pe2.get("yorumlar") or [pdf_label("Açı bulunamadı")])[0])
                    _i0b = _es_fix_tire(_i0b) if _ES else _i0b
                    if len(_i0b) > 800:
                        _i0b = _i0b[:800].rsplit('. ', 1)[0] + '.'
                    _h2 = max(16, yazi_olcul(_i0b, "DejaVu", 8.5, 72) + 22)
                    _onemli_bilgi.append((_gd2, _i0b, _h2))
                if _onemli_bilgi:
                    _P = 8.5 + 5
                    _tum_h = sum(_h for _, _, _h in _onemli_bilgi) + (len(_onemli_bilgi) - 1) * _P + 18
                    if y - (40 + satir_sayisi * HUCRE_H + _tum_h) - 6 < SAYFA_ALT:
                        yeni_sayfa(); y = SAYFA_UST
                    _avail_h = (y - 40 - satir_sayisi * HUCRE_H) - SAYFA_ALT - 6
                    _gr = []
                    for _it in _onemli_bilgi:
                        _trial = _gr + [_it]
                        _gh_guess = sum(h for _, _, h in _trial) + (len(_trial) - 1) * _P + 18
                        if _gr and _gh_guess > _avail_h:
                            _gruplar.append(_gr); _gr = [_it]
                        else:
                            _gr.append(_it)
                    if _gr:
                        _gruplar.append(_gr)
                    _onk = sum(h for _, _, h in _gruplar[0])
                    grid_h = 40 + satir_sayisi * HUCRE_H + _onk + (len(_gruplar[0]) - 1) * _P + 18
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
                c.drawString(SOL + 12, y - 17, f"{AY_ADLARI[mm-1]} {yy}")
                c.setStrokeColor(sari_cizgi)
                c.setLineWidth(0.4)
                c.line(SOL + 12, y - 23, SAG - 12, y - 23)
                # Weekday headers
                c.setFillColor(acik)
                c.setFont("DejaVu-Bold", 8)
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
                    cy = y - 48 - row * HUCRE_H
                    renk = gd_renk.get(gd)
                    if renk:
                        c.setFillColor(renk)
                        c.roundRect(cx, cy + 2, HUCRE_W - 4, HUCRE_H - 4, 3, fill=1, stroke=0)
                        c.setFillColor(HexColor('#12121A'))
                        c.setFont("DejaVu-Bold", 9)
                    else:
                        c.setStrokeColor(HexColor('#3A3A42'))
                        c.setLineWidth(0.5)
                        c.roundRect(cx, cy + 2, HUCRE_W - 4, HUCRE_H - 4, 3, fill=0, stroke=1)
                        c.setFillColor(acik)
                        c.setFont("DejaVu", 9)
                    c.drawCentredString(cx + (HUCRE_W - 4) / 2, cy + 13, str(gd.day))
                    col += 1
                    if col == 7:
                        col = 0; row += 1
                # Featured days (tümü görünür; sayfa dolunca devam kartı)
                if _onemli_bilgi:
                    ly = y - 40 - satir_sayisi * HUCRE_H
                    c.setFillColor(bordo)
                    c.setFont("DejaVu-Bold", 9)
                    c.drawString(SOL + 12, ly, f"✦ {pdf_label('Bu Ayın Öne Çıkan Günleri')}")
                    for gd, _iy, _satir_h in _gruplar[0]:
                        p_entry = gun_verileri[gd]
                        ly -= _satir_h
                        _label = f"{gd.day:02d} {AY_ADLARI[mm-1]} · {pdf_label(p_entry.get('ay_burc',''))} {pdf_label('Ay')}"
                        c.setFillColor(koyu)
                        c.setFont("DejaVu-Bold", 8.5)
                        c.drawString(SOL + 16, ly, _label)
                        _x_desc = SOL + 118
                        if SOL + 16 + c.stringWidth(_label, "DejaVu-Bold", 8.5) + 8 > _x_desc:
                            _x_desc = SOL + 16 + c.stringWidth(_label, "DejaVu-Bold", 8.5) + 8
                        c.setFillColor(acik)
                        c.setFont("DejaVu", 8.5)
                        # Yazıya göre sarılıp çiz (taşma önlenir, tam cümle)
                        metin_yaz(_x_desc, ly, _iy, "DejaVu", 8.5, acik, 72)
                    _devam = 1
                    for _grp in _gruplar[1:]:
                        _gh = 48 + sum(_h for _, _, _h in _grp) + (len(_grp) - 1) * _P + 18
                        yeni_sayfa(); y = SAYFA_UST
                        if y - _gh - 6 < SAYFA_ALT:
                            yeni_sayfa(); y = SAYFA_UST
                        c.setFillColor(kart_bg)
                        c.roundRect(SOL, y - _gh, SAG - SOL, _gh, 5, fill=1, stroke=0)
                        c.setStrokeColor(gri)
                        c.setLineWidth(0.4)
                        c.roundRect(SOL, y - _gh, SAG - SOL, _gh, 5, fill=0, stroke=1)
                        c.setFillColor(altin)
                        c.setFont("DejaVu-Bold", 11)
                        c.drawString(SOL + 12, y - 17, f"{AY_ADLARI[mm-1]} {yy}")
                        c.setStrokeColor(sari_cizgi)
                        c.setLineWidth(0.4)
                        c.line(SOL + 12, y - 23, SAG - 12, y - 23)
                        c.setFillColor(bordo)
                        c.setFont("DejaVu-Bold", 9)
                        c.drawString(SOL + 12, y - 38, f"✦ {pdf_label('Bu Ayın Öne Çıkan Günleri')} · {pdf_label('devam')} {_devam}")
                        ly = y - 48
                        for gd, _iy, _satir_h in _grp:
                            p_entry = gun_verileri[gd]
                            ly -= _satir_h
                            _label = f"{gd.day:02d} {AY_ADLARI[mm-1]} · {pdf_label(p_entry.get('ay_burc',''))} {pdf_label('Ay')}"
                            c.setFillColor(koyu)
                            c.setFont("DejaVu-Bold", 8.5)
                            c.drawString(SOL + 16, ly, _label)
                            _x_desc = SOL + 118
                            if SOL + 16 + c.stringWidth(_label, "DejaVu-Bold", 8.5) + 8 > _x_desc:
                                _x_desc = SOL + 16 + c.stringWidth(_label, "DejaVu-Bold", 8.5) + 8
                            c.setFillColor(acik)
                            c.setFont("DejaVu", 8.5)
                            metin_yaz(_x_desc, ly, _iy, "DejaVu", 8.5, acik, 72)
                        _devam += 1
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
        c.drawString(SOL, y, (("The cities on Earth where your planets exert their strongest influence — 15,000+ locations scanned.") if _EN else
                              (("Las ciudades de la Tierra donde tus planetas ejercen su influencia más potente — se han analizado más de 15.000 ubicaciones.") if _ES else pdf_label("Gezegenlerinizin dünya üzerinde en güçlü etki gösterdiği şehirler — 15.000+ konum taranmıştır."))))
        y -= 22
        # ── Calculation technique explanation ──
        teknik = ((("Calculation Method: Your planets' natal positions are compared against the coordinates of "
                    "more than 15,000 cities worldwide. ") if _EN else (("Método de cálculo: Las posiciones natales de tus planetas se comparan con las coordenadas de "
                    "más de 15.000 ciudades de todo el mundo. ") if _ES else pdf_label("Hesaplama Tekniği: Doğum haritanızdaki gezegen konumları, dünya üzerindeki 15.000'den fazla şehir koordinatıyla karşılaştırılır. "))) +
                  (("For each city, the day's sky axes — the Ascendant (AC), Midheaven (MC), Descendant (DC) and "
                    "Imum Coeli (IC) — are computed; ") if _EN else (("Para cada ciudad se calculan los ejes celestes del momento — el Ascendente (AC), el Medio Cielo (MC), el Descendente (DC) y el "
                    "Imum Coeli (IC); ") if _ES else pdf_label("Her şehir için o günkü gökyüzünde Yükselen (AC), Zirve (MC), Alçalan (DC) ve Taban (IC) eksenleri hesaplanır; "))) +
                  (("Your planets' closeness (orb) to these axes up to 5° is scored together with the planet's nature — "
                    "the sharper the angle, the stronger the influence. ") if _EN else (("La cercanía (orb) de tus planetas a estos ejes, hasta 5°, se puntúa junto con la naturaleza del planeta — "
                    "cuanto más agudo es el ángulo, más fuerte es la influencia. ") if _ES else pdf_label("gezegenlerinizin bu eksenlere 5°'ye kadar olan yakınlığı (orb) ile gezegenin doğası puanlanır — açı ne kadar keskinse etki o kadar güçlüdür. "))) +
                  (("Each city is assessed with 4 core scores: Wealth & Abundance, Peace & Inner Calm, "
                    "Passion & Adventure, Crisis & Transformation. ") if _EN else (("Cada ciudad se evalúa con 4 puntuaciones esenciales: Riqueza y Abundancia, Paz y Calma Interior, "
                    "Pasión y Aventura, Crisis y Transformación. ") if _ES else pdf_label("Her şehir 4 temel skorla değerlendirilir: Para & Bolluk, Huzur & İç Sakinlik, Tutku & Macera, Kriz & Dönüşüm. "))) +
                  (("The top 10 cities in each category by score represent the points where your energies resonate most powerfully on Earth." if _EN else
                    ("Las 10 ciudades con mayor puntuación en cada categoría representan los puntos donde tus energías resuenan con mayor fuerza sobre la Tierra." if _ES else "Her kategoride en yüksek skorlu ilk 10 şehir, enerjilerinizin dünya üzerinde en güçlü rezonans kurduğu noktaları temsil eder."))))
        teknik_h = 27 + yazi_olcul(teknik, "DejaVu", 7.5, 90) + 14
        if y - teknik_h < SAYFA_ALT:
            yeni_sayfa()
            y = sayfa_basligi(pdf_label("Global Kader Pusulası") + (" (devam)" if not _EN and not _ES else (" (continuación)" if _ES else " (continued)")), numara=str(bolum_no[0]))
        kart_ciz(SOL, y - teknik_h, SAG - SOL, teknik_h, pdf_label("Hesaplama Tekniği"), "🔮")
        _tek_son = metin_yaz(SOL + 14, y - 27, teknik, "DejaVu", 7.5, acik, 90)
        if _tek_son < y - teknik_h:
            y = _tek_son - 12
        else:
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
                y = sayfa_basligi(pdf_label("Global Kader Pusulası") + (" (devam)" if not _EN and not _ES else (" (continuación)" if _ES else " (continued)")), numara=str(bolum_no[0]))
            kart_ciz(SOL, y - kat_h, SAG - SOL, kat_h, label, icon)
            # Category color stripe on the left edge
            c.setFillColor(KAT_RENK.get(kat_key, altin))
            c.rect(SOL + 2, y - kat_h + 6, 3, kat_h - 12, fill=1, stroke=0)
            inner_y = y - 28
            for i, city in enumerate(cities):
                sehir_adi = _es_fix_tire(city.get("sehir", "")[:42]) if _ES else city.get("sehir", "")[:42]
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
                    _etkiler_list = [_etki_temizle(e) for e in etkiler[:2]]
                    if _EN or _ES:
                        import re as _re_mod
                        if _ES:
                            _pname_map = {"Güneş":"Sol","Ay":"Luna","Merkür":"Mercurio","Venüs":"Venus","Mars":"Marte","Jüpiter":"Júpiter","Satürn":"Saturno","Uranüs":"Urano","Neptün":"Neptuno","Plüton":"Plutón","Chiron":"Quirón"}
                        else:
                            _pname_map = {"Güneş":"Sun","Ay":"Moon","Merkür":"Mercury","Venüs":"Venus","Mars":"Mars","Jüpiter":"Jupiter","Satürn":"Saturn","Uranüs":"Uranus","Neptün":"Neptune","Plüton":"Pluto","Chiron":"Chiron"}
                        _pname_pat = _re_mod.compile("|".join(_pname_map.keys()))
                        _etkiler_list = [_pname_pat.sub(lambda m: _pname_map[m.group(0)], e) for e in _etkiler_list]
                    etki_list = "; ".join(_etkiler_list)
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
    _ES = _i18n_get_lang() == "es"

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

    _ES_OZ = {
        "Güneş": "la identidad, el propósito vital, la voluntad y la creatividad",
        "Ay": "las emociones, el mundo interior, la madre, la nutrición, los hábitos, la intuición, la necesidad de seguridad",
        "Merkür": "la mente, la comunicación, la lógica, el aprendizaje, el análisis, la escritura, los viajes cortos",
        "Venüs": "el amor, la belleza, los valores, la armonía, la estética, la atracción, el dinero, el confort",
        "Mars": "la acción, la pasión, el coraje, la ira, la competencia, la voluntad, la energía de lucha",
        "Jüpiter": "la abundancia, la suerte, la expansión, la filosofía, la fe, el aprendizaje, el optimismo",
        "Satürn": "la disciplina, los límites, la responsabilidad, la madurez, la estructura, el miedo, la paciencia, las lecciones",
        "Uranüs": "la libertad, la revolución, el cambio repentino, la invención, el espíritu rebelde, la independencia, el genio",
        "Neptün": "los sueños, la inspiración, la intuición, la bruma, la espiritualidad, el idealismo, la confusión",
        "Plüton": "la transformación, el poder, la muerte y renacimiento, la obsesión, la profundidad, el poder oculto",
        "Chiron": "la herida, la vulnerabilidad, la curación, la sabiduría, la herida del sanador, la aceptación",
        "Juno": "el compromiso, el matrimonio, la lealtad, la sociedad, la justicia, los votos de relación",
        "Ceres": "la nutrición, la maternidad, la pérdida, la aceptación, la compasión, la alimentación, la naturaleza",
        "Pallas": "la sabiduría, la estrategia, la inteligencia creativa, el talento artístico, el espíritu guerrero, la previsión",
        "Vesta": "la devoción, el foco, el fuego sagrado, la disciplina interior, el servicio, el Templo",
        "Eros": "el amor apasionado, el deseo, la sexualidad, la lujuria, la pasión creativa, el gusto por la vida",
        "Psyche": "el alma, la psicología, el vínculo profundo, la vulnerabilidad, la intuición, el amor espiritual",
        "Ruh Noktası": "el propósito de vida, la dirección espiritual, el camino profesional, el destino, la fuente de inspiración",
        "Evlilik Noktası": "el potencial de relación, el tema del matrimonio, la pareja a largo plazo, la búsqueda de armonía",
        "Aşk Noktası": "el potencial amoroso, la atracción romántica, el vínculo emocional, la armonía sexual",
        "Tutku Noktası": "la pasión intensa, el deseo, la ambición, la obsesión, la atracción profunda, la energía sexual",
        "Para Noktası": "el potencial material, la suerte financiera, la creación de valor, la abundancia",
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

    CIFT_TEMA_ES = {
        ("Güneş","Ay"): "el puente entre la esencia propia y el mundo emocional",
        ("Güneş","Merkür"): "la conexión directa entre la identidad y la mente",
        ("Güneş","Venüs"): "la armonía entre la esencia propia y el amor y los valores",
        ("Güneş","Mars"): "el vínculo fuerte entre la identidad y la acción y la pasión",
        ("Güneş","Jüpiter"): "el apoyo entre la esencia y la abundancia y la expansión",
        ("Güneş","Satürn"): "el equilibrio entre la esencia y la responsabilidad y los límites",
        ("Güneş","Uranüs"): "la ruptura entre la identidad y la libertad y la revolución",
        ("Güneş","Neptün"): "la nebulosidad entre la esencia y los sueños y las intuiciones",
        ("Güneş","Plüton"): "el vínculo profundo entre la esencia y el poder y la transformación",
        ("Güneş","Chiron"): "la herida de la esencia y la lucha por la aceptación",
        ("Ay","Merkür"): "el puente entre la emoción y la mente",
        ("Ay","Venüs"): "la armonía profunda entre el mundo emocional y el amor",
        ("Ay","Mars"): "el conflicto y la pasión entre las emociones y la acción",
        ("Ay","Jüpiter"): "la expansión entre la seguridad emocional y la abundancia",
        ("Ay","Satürn"): "el equilibrio exigente entre las emociones y los límites",
        ("Ay","Uranüs"): "las rupturas súbitas entre el mundo interior y la libertad",
        ("Ay","Neptün"): "la intuición profunda entre las emociones y los sueños",
        ("Ay","Plüton"): "la transformación intensa entre el mundo emocional y el poder",
        ("Ay","Chiron"): "la herida emocional y la necesidad de nutrición",
        ("Ay","KAD"): "el vínculo entre las raíces familiares y los hábitos emocionales",
        ("Ay","Lilith"): "el secretismo emocional y el deseo reprimido",
        ("Merkür","Venüs"): "la armonía entre la mente y el atractivo",
        ("Merkür","Mars"): "la rapidez entre el pensamiento y la acción",
        ("Merkür","Jüpiter"): "la abundancia entre la mente y la expansión",
        ("Merkür","Satürn"): "la seriedad entre el pensamiento y los límites",
        ("Merkür","Uranüs"): "el genio entre la mente y la revolución",
        ("Merkür","Neptün"): "la inteligencia nebulosa entre el pensamiento y el sueño",
        ("Merkür","Plüton"): "el análisis profundo entre la mente y el poder",
        ("Merkür","Chiron"): "la herida de la comunicación y la dificultad de expresión",
        ("Merkür","KAD"): "los patrones de comunicación en las raíces familiares",
        ("Merkür","Lilith"): "el secretismo mental y el pensamiento reprimido",
        ("Venüs","Mars"): "la fuerte atracción entre el atractivo y la pasión",
        ("Venüs","Jüpiter"): "la expansión entre el amor y la abundancia",
        ("Venüs","Satürn"): "la maduración entre el amor y los límites",
        ("Venüs","Uranüs"): "el cambio súbito entre los valores y la revolución",
        ("Venüs","Neptün"): "el idealismo entre el amor y el sueño",
        ("Venüs","Plüton"): "la transformación intensa entre el amor y el poder",
        ("Venüs","Chiron"): "la herida del amor y la búsqueda de aceptación",
        ("Venüs","KAD"): "los patrones de amor y valores en las raíces familiares",
        ("Venüs","Lilith"): "el secretismo en el amor y el deseo reprimido",
        ("Mars","Jüpiter"): "la expansión entre la pasión y la abundancia",
        ("Mars","Satürn"): "la disciplina entre la acción y los límites",
        ("Mars","Uranüs"): "las explosiones súbitas entre la pasión y la revolución",
        ("Mars","Neptün"): "la lucha nebulosa entre la acción y el sueño",
        ("Mars","Plüton"): "la guerra intensa entre la pasión y el poder",
        ("Mars","Chiron"): "la herida de la guerra y el coraje frágil",
        ("Mars","KAD"): "la guerra y la protección en las raíces familiares",
        ("Mars","Lilith"): "el secretismo apasionado y la ira reprimida",
        ("Jüpiter","Satürn"): "el equilibrio entre la abundancia y los límites",
        ("Jüpiter","Uranüs"): "la suerte súbita entre la expansión y la revolución",
        ("Jüpiter","Neptün"): "la expansión espiritual entre la fe y el sueño",
        ("Jüpiter","Plüton"): "la expansión profunda entre la abundancia y el poder",
        ("Jüpiter","Chiron"): "la herida de la fe y la curación espiritual",
        ("Jüpiter","KAD"): "la abundancia y la fe en las raíces familiares",
        ("Jüpiter","Lilith"): "el secretismo y la expansión en la fe",
        ("Satürn","Uranüs"): "el equilibrio exigente entre el límite y la revolución",
        ("Satürn","Neptün"): "la estructura nebulosa entre la disciplina y el sueño",
        ("Satürn","Plüton"): "la estructura intensa entre el límite y el poder",
        ("Satürn","Chiron"): "la herida del miedo y la maduración",
        ("Satürn","KAD"): "la responsabilidad y los límites en las raíces familiares",
        ("Satürn","Lilith"): "el secretismo en el límite y el miedo reprimido",
        ("Uranüs","Neptün"): "el cambio espiritual entre la revolución y el sueño",
        ("Uranüs","Plüton"): "la revolución profunda entre la libertad y el poder",
        ("Uranüs","Chiron"): "la herida de la libertad y la aceptación",
        ("Uranüs","KAD"): "la revolución y el cambio súbito en las raíces familiares",
        ("Uranüs","Lilith"): "el secretismo en la libertad y el espíritu rebelde",
        ("Neptün","Plüton"): "la transformación espiritual entre el sueño y el poder",
        ("Neptün","Chiron"): "la herida del sueño y la curación espiritual",
        ("Neptün","KAD"): "los sueños y la nebulosidad en las raíces familiares",
        ("Neptün","Lilith"): "el secretismo en el sueño y la intuición reprimida",
        ("Plüton","Chiron"): "la herida de la transformación y la curación profunda",
        ("Plüton","KAD"): "el poder y la transformación profunda en las raíces familiares",
        ("Plüton","Lilith"): "el secretismo del poder y la pasión reprimida",
        ("Juno","Güneş"): "el vínculo fuerte entre el compromiso y la identidad",
        ("Juno","Ay"): "la armonía profunda entre el compromiso y las emociones",
        ("Juno","Venüs"): "el tema matrimonial entre el compromiso y el atractivo",
        ("Juno","Mars"): "el equilibrio exigente entre el compromiso y la pasión",
        ("Ceres","Güneş"): "la energía materna entre el cuidado y la identidad",
        ("Ceres","Ay"): "la compasión profunda entre el cuidado y las emociones",
        ("Ceres","Venüs"): "el amor incondicional entre el cuidado y el atractivo",
        ("Ceres","Merkür"): "el cuidado comunicativo entre el cuidado y la mente",
        ("Pallas","Güneş"): "la sabiduría entre la estrategia y la identidad",
        ("Pallas","Merkür"): "el poder analítico entre la estrategia y la mente",
        ("Pallas","Satürn"): "la sabiduría estructural entre la estrategia y los límites",
        ("Pallas","Plüton"): "la previsión profunda entre la estrategia y el poder",
        ("Vesta","Güneş"): "el fuego sagrado entre la devoción y la identidad",
        ("Vesta","Ay"): "la disciplina interna entre la devoción y las emociones",
        ("Vesta","Venüs"): "el amor sagrado entre la devoción y el atractivo",
        ("Vesta","Plüton"): "el enfoque profundo entre la devoción y el poder",
        ("Eros","Venüs"): "el amor sensual entre la pasión y el atractivo",
        ("Eros","Mars"): "el deseo intenso entre la pasión y la acción",
        ("Eros","Plüton"): "la transformación profunda entre la pasión y el poder",
        ("Eros","Güneş"): "el entusiasmo vital entre la pasión y la identidad",
        ("Psyche","Ay"): "el vínculo profundo entre el alma y las emociones",
        ("Psyche","Venüs"): "el amor espiritual entre el alma y el atractivo",
        ("Psyche","Plüton"): "la transformación psicológica entre el alma y el poder",
        ("Psyche","Neptün"): "la intuición espiritual entre el alma y el sueño",
        ("Ruh Noktası","Güneş"): "el vínculo profundo entre el propósito de vida y la identidad",
        ("Ruh Noktası","Ay"): "la dirección intuitiva entre el propósito de vida y las emociones",
        ("Ruh Noktası","Venüs"): "la dirección estética entre el propósito de vida y el atractivo",
        ("Ruh Noktası","Mars"): "la dirección orientada a la acción entre el propósito de vida y la pasión",
        ("Evlilik Noktası","Venüs"): "la fuerte armonía entre el potencial de relación y el atractivo",
        ("Evlilik Noktası","Jüpiter"): "la expansión entre el potencial de relación y la abundancia",
        ("Evlilik Noktası","Satürn"): "el compromiso serio entre el potencial de relación y los límites",
        ("Evlilik Noktası","Neptün"): "la relación idealista entre el potencial de relación y el sueño",
        ("Aşk Noktası","Venüs"): "el fuerte romanticismo entre el potencial de amor y el atractivo",
        ("Aşk Noktası","Mars"): "el amor apasionado entre el potencial de amor y la pasión",
        ("Aşk Noktası","Plüton"): "la transformación intensa entre el potencial de amor y el poder",
        ("Aşk Noktası","Güneş"): "el amor propio entre el potencial de amor y la identidad",
        ("Tutku Noktası","Mars"): "la ambición fuerte entre la pasión intensa y la acción",
        ("Tutku Noktası","Plüton"): "la obsesión profunda entre la pasión intensa y el poder",
        ("Tutku Noktası","Venüs"): "la energía sensual entre la pasión intensa y el atractivo",
        ("Tutku Noktası","Ay"): "el deseo profundo entre la pasión intensa y las emociones",
        ("Para Noktası","Jüpiter"): "la fuerte suerte entre el potencial material y la abundancia",
        ("Para Noktası","Satürn"): "la estructura entre el potencial material y los límites",
        ("Para Noktası","Venüs"): "el valor estético entre el potencial material y el atractivo",
        ("Para Noktası","Plüton"): "la transformación profunda entre el potencial material y el poder",
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

    OZEL_YORUMLAR_ES = {}

    tum = list(GEZEGENLER.keys()) + list(ASTEROITLER.keys()) + list(ARAP_NOKTALARI.keys())

    def _urun(p1, p2, aci, en=False, es=False):
        key = (p1, p2, aci)
        key_t = (p2, p1, aci)
        if en:
            if key in OZEL_YORUMLAR_EN: return OZEL_YORUMLAR_EN[key]
            if key_t in OZEL_YORUMLAR_EN: return OZEL_YORUMLAR_EN[key_t]
            p1n = pdf_label(p1); p2n = pdf_label(p2)
            pair = (p1, p2) if (p1, p2) in CIFT_TEMA_EN else ((p2, p1) if (p2, p1) in CIFT_TEMA_EN else None)
            tema = CIFT_TEMA_EN.get(pair, f"the connection between the energies of {p1n} and {p2n}") if pair else f"the connection between the energies of {p1n} and {p2n}"
            p1o = _EN_OZ.get(p1) or f"{p1n} energy"; p2o = _EN_OZ.get(p2) or f"{p2n} energy"
            if aci == "Kavuşum":
                return f"{p1n} and {p2n} energies merge at the same point. {tema}. The {p1o} of {p1n} and the {p2o} of {p2n} form a unified whole. This conjunction allows you to experience both energies with great intensity."
            elif aci == "Karşıt":
                return f"{p1n} and {p2n} stand at opposite poles. {tema}. There is constant search for balance between the {p1o} of {p1n} and the {p2o} of {p2n}. This opposition requires you to fully understand both sides."
            elif aci == "Kare":
                return f"The square between {p1n} and {p2n} creates tension around {tema}. This demanding energy pushes you beyond your comfort zone and forces growth. The struggle between the {p1o} of {p1n} and the {p2o} of {p2n} is one of your most powerful transformation opportunities."
            elif aci == "Trigon":
                return f"The trine between {p1n} and {p2n} creates a natural harmony around {tema}. Used consciously, this energy can create flow in your life. The {p1o} of {p1n} and the {p2o} of {p2n} naturally build a bridge."
            elif aci == "Sekstil":
                return f"The sextile between {p1n} and {p2n} offers opportunities around {tema}. To activate this energy, you need to take a conscious step. There is a supportive bond between the {p1o} of {p1n} and the {p2o} of {p2n}."
            return ""
        if es:
            if key in OZEL_YORUMLAR_ES: return OZEL_YORUMLAR_ES[key]
            if key_t in OZEL_YORUMLAR_ES: return OZEL_YORUMLAR_ES[key_t]
            p1n = pdf_label(p1); p2n = pdf_label(p2)
            pair = (p1, p2) if (p1, p2) in CIFT_TEMA_ES else ((p2, p1) if (p2, p1) in CIFT_TEMA_ES else None)
            tema = CIFT_TEMA_ES.get(pair, f"la conexión entre las energías de {p1n} y {p2n}") if pair else f"la conexión entre las energías de {p1n} y {p2n}"
            # Limpieza de artículos: de el -> del, a el -> al
            tema = tema.replace(" de el ", " del ").replace(" De el ", " Del ").replace(" a el ", " al ").replace(" A el ", " Al ")
            p1o = _ES_OZ.get(p1) or f"la energía de {p1n}"; p2o = _ES_OZ.get(p2) or f"la energía de {p2n}"
            if aci == "Kavuşum":
                return f"Las energías de {p1n} y {p2n} se unen en el mismo punto. {tema}. {p1o[0].upper()+p1o[1:]} de {p1n} y {p2o} de {p2n} forman un todo unificado. Esta conjunción te permite experimentar ambas energías con gran intensidad."
            elif aci == "Karşıt":
                return f"{p1n} y {p2n} se sitúan en polos opuestos. {tema}. Hay una búsqueda constante de equilibrio entre la {p1o} de {p1n} y la {p2o} de {p2n}. Esta oposición te exige comprender por completo ambos lados."
            elif aci == "Kare":
                return f"El cuadrado entre {p1n} y {p2n} genera tensión alrededor de {tema}. Esta energía exigente te empuja fuera de tu zona de confort y obliga al crecimiento. La lucha entre {p1o} de {p1n} y {p2o} de {p2n} es una de tus oportunidades de transformación más poderosas."
            elif aci == "Trigon":
                return f"El trígono entre {p1n} y {p2n} crea una armonía natural alrededor de {tema}. Usada con conciencia, esta energía puede fluir en tu vida. {p1o[0].upper()+p1o[1:]} de {p1n} y {p2o} de {p2n} construyen naturalmente un puente."
            elif aci == "Sekstil":
                return f"El sextil entre {p1n} y {p2n} ofrece oportunidades alrededor de {tema}. Para activar esta energía, debes dar un paso consciente. Existe un vínculo de apoyo entre {p1o} de {p1n} y {p2o} de {p2n}."
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
    _sozluk_es = None
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
            if _ES:
                if _sozluk_es is None: _sozluk_es = {}
                _sozluk_es[f"{pk[0]}-{pk[1]}"] = {}
            for aci in ["Kavuşum","Karşıt","Kare","Trigon","Sekstil"]:
                _sozluk_tr[f"{pk[0]}-{pk[1]}"][aci] = _urun(pk[0], pk[1], aci, es=_ES)
                if _sozluk_en is not None:
                    _sozluk_en[f"{pk[0]}-{pk[1]}"][aci] = _urun(pk[0], pk[1], aci, en=True)
                if _sozluk_es is not None:
                    _sozluk_es[f"{pk[0]}-{pk[1]}"][aci] = _urun(pk[0], pk[1], aci, es=True)
    if _sozluk_en is not None:
        return _sozluk_en
    if _sozluk_es is not None:
        return _sozluk_es
    return _sozluk_tr

def _collect_solar_lunar_data(motor):
    """Solar return and lunar return predictions for the natal chart. Individual-focused."""
    data = {}
    try:
        jd = motor.get_natal_julian_day("p1")
        import datetime
        simdi = datetime.datetime.now()
        # Solar: 2 yıl arka arkaya (baba correccion #3)
        sr_list = []
        sr_html_list = []
        for y in [simdi.year, simdi.year + 1]:
            sr = motor.calculate_solar_return_tema(jd, y)
            if sr and isinstance(sr, str) and len(sr) > 20:
                sr_list.append(_bireysellestir(_strip_html(sr)))
                try:
                    sr_html_list.append(_bireysellestir(sr))
                except:
                    pass
        if sr_list:
            data["solar_return"] = "\n\n".join(sr_list)
            data["solar_return_html"] = "<hr/>".join(sr_html_list)
    except:
        pass
    try:
        jd = motor.get_natal_julian_day("p1")
        import datetime
        simdi = datetime.datetime.now()
        # Lunar: 6 ay (baba correccion #4) + tarih başlığı
        lr_list = []
        lr_html_list = []
        y, m = simdi.year, simdi.month
        for i in range(6):
            yy = y + (m + i - 1) // 12
            mm = (m + i - 1) % 12 + 1
            lr = motor.calculate_lunar_return_tema(jd, yy, mm)
            if lr and isinstance(lr, str) and len(lr) > 20:
                # Tarih ekle
                lr_with_date = f"<b>{mm:02d}/{yy} — {lr[0:30]}</b><br/>" + lr if len(lr) < 200 else f"<b>{mm:02d}/{yy}</b> — " + lr
                _lr_date_html = f"<b>{mm:02d}/{yy}</b> — " + lr
                lr_list.append(_bireysellestir(_strip_html(_lr_date_html)))
                try:
                    lr_html_list.append(_bireysellestir(_lr_date_html))
                except:
                    pass
        if lr_list:
            data["lunar_return"] = "\n\n".join(lr_list)
            data["lunar_return_html"] = "<hr/>".join(lr_html_list)
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
        _EN = _i18n_get_lang() == "en"
        _ES = _i18n_get_lang() == "es"
        jd = motor.get_natal_julian_day("p1")

        BURCLAR = ["Koç","Boğa","İkizler","Yengeç","Aslan","Başak","Terazi","Akrep","Yay","Oğlak","Kova","Balık"]
        BURCLAR_EN = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
        BURCLAR_ES = ["Aries","Tauro","Géminis","Cáncer","Leo","Virgo","Libra","Escorpio","Sagitario","Capricornio","Acuario","Piscis"]

        def _hburc(burc_no):
            return BURCLAR_EN[burc_no % 12] if _EN else (BURCLAR_ES[burc_no % 12] if _ES else BURCLAR[burc_no % 12])

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

        # ── EN variants (selected when _EN) ──
        if _EN:
            BURC_SPOR = {
                "Koç": "running, boxing, martial arts, cross-country, mountain climbing, sprint",
                "Boğa": "walking, pilates, weight training, gardening sports, horse riding",
                "İkizler": "cycling, badminton, table tennis, trying multiple sports, archery",
                "Yengeç": "swimming, water sports, tai-chi, evening walks, rhythmic movement",
                "Aslan": "tennis, bodybuilding, gymnastics, fitness, show sports",
                "Başak": "yoga, pilates, regular walking, fresh-air exercise, stretching",
                "Terazi": "dance, pilates, ice skating, rhythmic gymnastics, partner sports",
                "Akrep": "boxing, martial arts, crossfit, swimming, diving, high-intensity interval training",
                "Yay": "horse riding, outdoor sports, camping, archery, adventure sports",
                "Oğlak": "long-distance running, cycling, mountain climbing, disciplined training, weights",
                "Kova": "extreme sports, skateboarding, snowboarding, free diving, innovative workouts",
                "Balık": "swimming, diving, yoga, tai-chi, meditative movement, water sports",
            }
            SPOR_MAP = {
                ("Mars",1): "Running, boxing, martial arts and solo combat sports",
                ("Mars",6): "CrossFit, interval training, high-tempo workouts",
                ("Mars",5): "Competitive sports, tennis, squash, sports competitions",
                ("Venüs",1): "Dance, pilates, swimming, aesthetic and fluid sports",
                ("Venüs",6): "Yoga, stretching exercises, nature walking",
                ("Venüs",5): "Dance, ice skating, rhythmic gymnastics",
                ("Jüpiter",1): "Outdoor sports, team games, nature sports",
                ("Jüpiter",6): "Long walks, trekking, nature camping",
                ("Jüpiter",9): "Horse riding, archery, outdoor adventure sports",
                ("Satürn",1): "Long-distance running, cycling, endurance sports",
                ("Satürn",6): "Regular walking, disciplined training, weight training",
                ("Satürn",10): "Marathons, triathlons, long-term endurance goals",
                ("Ay",1): "Swimming, tai-chi, evening walks, rhythmic movement",
                ("Ay",6): "Yoga, meditative exercises, light-tempo sports",
                ("Ay",4): "Garden walks, home workouts, family sports activities",
                ("Uranüs",1): "Extreme sports, skateboarding, snowboarding, innovative workouts",
                ("Uranüs",11): "Group extreme sports, parkour, free diving",
                ("Neptün",1): "Yoga, swimming, dance, water sports, tai-chi",
                ("Neptün",12): "Meditative movements, qigong, spiritual body exercises",
                ("Güneş",1): "Tennis, athletics, sports requiring leadership",
                ("Güneş",5): "Show sports, gymnastics, artistic performance",
                ("Plüton",8): "Transformative fitness, deep bodywork, detox sports",
                ("Plüton",6): "Healing yoga, meditation, body-spirit cleansing",
                ("Merkür",3): "Brisk walking, cycling, multi-station gym exercises",
                ("Merkür",6): "Coordination work, mind-body exercises",
            }
            BURC_SANAT = {
                "Koç": "sculpture, performance art, bold experimental works, street art",
                "Boğa": "ceramics, art with natural materials, photography, playing an instrument",
                "İkizler": "writing, literature, theater, podcasts, linguistic art, journalism",
                "Yengeç": "culinary art, crafts, photography, emotional music, storytelling",
                "Aslan": "stage arts, theater, dance, showmanship, costume design, artistic performance",
                "Başak": "detailed crafts, digital design, the art of organization, fine workmanship",
                "Terazi": "fashion design, interior architecture, aesthetic arts, jewelry design, photography",
                "Akrep": "photography, cinema, transformative art, sculpture, deeply themed works",
                "Yay": "travel photography, documentaries, murals, street art, cross-cultural art",
                "Oğlak": "architecture, sculpture, structural arts, restoration, traditional techniques",
                "Kova": "digital art, installation, video art, technology-art, graphic design",
                "Balık": "watercolor, music, dance, meditative art, cinema, spiritual symbolism",
            }
            SANAT_MAP = {
                ("Venüs",5): "Painting, sculpture, ceramics, visual arts",
                ("Venüs",3): "Poetry, literature, creative writing, writing song lyrics",
                ("Venüs",10): "Fashion design, interior architecture, aesthetic consulting",
                ("Neptün",5): "Music, dance, photography, cinema and stage arts",
                ("Neptün",12): "Meditative art, mandala, spiritual painting, poetry",
                ("Neptün",3): "Playing an instrument, singing, composing",
                ("Merkür",3): "Writing, journalism, blogging, theater acting",
                ("Merkür",5): "Theater, screenwriting, creative writing workshops",
                ("Ay",4): "Handicrafts, knitting, embroidery, ceramics, culinary art",
                ("Ay",5): "Writing children's books, toy design, storytelling",
                ("Güneş",5): "Stage arts, theater acting, performance",
                ("Uranüs",5): "Digital art, graphic design, installation, experimental art",
                ("Jüpiter",5): "Performance arts, show business, stage management",
                ("Satürn",5): "Architecture, sculpture, structural arts, restoration",
                ("Plüton",5): "Photography, transformative art, deeply themed works",
            }
            BURC_HOBI = {
                "Koç": "adventure sports, travel, exploration, motor sports, camping",
                "Boğa": "gardening, collecting, cooking, antique research, nature walks",
                "İkizler": "chess, software, reading, podcasts, learning languages, solving puzzles",
                "Yengeç": "kitchen hobbies, photography, keeping a journal, family conversations",
                "Aslan": "theater, stage arts, volunteering with children, show hobbies",
                "Başak": "organizing, detail-oriented crafts, coding, data analysis",
                "Terazi": "music, art collecting, social events, decoration, fashion",
                "Akrep": "mystery novels, detective games, diving, research, psychology",
                "Yay": "travel planning, philosophy, archery, nature exploration, cross-cultural interaction",
                "Oğlak": "woodworking, strategy games, hiking, planning, traditional crafts",
                "Kova": "technology, science fiction, robotics, space research, digital projects",
                "Balık": "music, photography, nature observation, meditation, imagination activities",
            }
            BURC_SAGLIK = {
                "Koç": "mind head-region health; dynamic exercise but avoid head injuries",
                "Boğa": "throat and thyroid health; regular eating and metabolism control",
                "İkizler": "nervous system and respiratory health; breathing exercises are important",
                "Yengeç": "stomach and digestive system; regular sleep and emotional balance",
                "Aslan": "heart and spine health; cardio exercises and posture correction",
                "Başak": "gut health and food sensitivity; clean eating is a priority",
                "Terazi": "kidney and skin health; water intake and hormonal balance matter",
                "Akrep": "reproductive system and immunity; detox and cleansing nutrition",
                "Yay": "liver and hip health; active living and regular exercise",
                "Oğlak": "joint, bone and skin health; mineral supplementation and moisturizing",
                "Kova": "circulatory system and ankles; blood-circulation exercises",
                "Balık": "immune system and sleep routine; meditation and a steady rhythm",
            }
            BURC_BESLENME = {
                "Koç": "spicy, energizing foods; iron- and protein-heavy, red meat and leafy greens",
                "Boğa": "quality, tasty, filling meals; natural and additive-free eating, dairy products",
                "İkizler": "light, varied and colorful foods; nuts, fruit, rich snacks",
                "Yengeç": "homemade, natural, organic foods; dairy, soups and warm dishes",
                "Aslan": "heart-friendly foods, antioxidant-rich foods, red berries, fish",
                "Başak": "pure, clean, organic eating; fibrous foods, whole grains, detox teas",
                "Terazi": "balanced, light, colorful eating; salads, social meals, chocolate",
                "Akrep": "intensely flavorful foods, detox foods, probiotics, garlic and ginger",
                "Yay": "exploring different cuisines; spicy and exotic flavors, protein-heavy",
                "Oğlak": "mineral-rich, regular and measured eating; bone-friendly calcium foods",
                "Kova": "innovative and different foods; smoothie bowls, superfoods, vegetarian alternatives",
                "Balık": "seafood, omega-3 sources; light and liquid-heavy, herbal teas",
            }
            BESLENME_MAP = {
                "Ay_Yengeç": "Homemade, natural, organic foods; dairy products and home cooking serve you well",
                "Ay_Boğa": "Quality, tasty, filling meals; natural and additive-free eating",
                "Ay_Balık": "Seafood, omega-3 sources; light and liquid-heavy eating",
                "Ay_Oğlak": "Regular, disciplined, scheduled eating; mineral- and calcium-heavy",
                "Ay_Başak": "Pure, clean, organic eating; watch food sensitivities",
                "Venüs_Boğa": "Flavor-focused, quality foods; deli items and natural tastes",
                "Venüs_Terazi": "Balanced, light, colorful and varied eating; social meals",
                "Jüpiter_Yay": "Exploring different cuisines; spicy and exotic flavors",
                "Jüpiter_Balık": "Seafood, plant-heavy, plenty of fluids",
                "Mars_Koç": "Spicy, energizing, iron- and protein-heavy eating",
                "Mars_Aslan": "Heart-friendly foods, magnesium, antioxidant-rich foods",
                "Satürn_Oğlak": "Mineral-rich, bone-friendly calcium eating",
                "Neptün_Balık": "Vegetable-heavy, light, liquid and plant-based eating",
            }
            BURC_ASK = {
                "Koç": "a passionate and enthusiastic bond; strong physical attraction, bold romantic gestures",
                "Boğa": "loyalty, trust and long-term commitment; sensual pleasures and comfort come first",
                "İkizler": "intellectual harmony and social sharing; communication, humor and a mental bond matter",
                "Yengeç": "a deep emotional bond and a sense of home; affection, protection and family values are fundamental",
                "Aslan": "dazzling romance; attention, appreciation and lavish expressions of love",
                "Başak": "service and practical love; small regular gestures, thoughtfulness and loyalty",
                "Terazi": "an elegant and balanced union; aesthetic sharing, art and a sense of justice",
                "Akrep": "passion, mystery and deep transformation; a powerful spiritual and sexual bond",
                "Yay": "free and adventurous love; shared discovery, philosophy and broad horizons",
                "Oğlak": "serious, long-term and goal-oriented union; discipline and respect",
                "Kova": "an original and independent bond; intellectual harmony, innovation and social idealism",
                "Balık": "spiritual and unconditional love; empathy, sacrifice and imagination-filled romance",
            }
            BURC_KARIYER = {
                "Koç": "entrepreneurship, leadership, emergency management, sports, military, start-ups",
                "Boğa": "banking, real estate, food, music, design, art, value management",
                "İkizler": "communication, media, software, marketing, sales, journalism, teaching",
                "Yengeç": "education, consulting, tourism, gastronomy, real estate, family business",
                "Aslan": "stage arts, management, education, entertainment, PR, luxury brand management",
                "Başak": "accounting, health services, editing, quality control, analysis, IT",
                "Terazi": "law, diplomacy, art, fashion, interior architecture, mediation, consulting",
                "Akrep": "research, psychology, finance, detective work, transformation consulting, medicine",
                "Yay": "academia, international relations, travel, publishing, philosophy",
                "Oğlak": "management, architecture, engineering, public service, long-term projects",
                "Kova": "technology, science, social movements, aviation, innovative start-ups",
                "Balık": "art, psychology, health, consulting, spiritual guidance, charitable organizations",
            }
            BURC_AILE = {
                "Koç": "a leader and protector role in the family; passes on courage and independence values",
                "Boğa": "a trustworthy bond that keeps family traditions; comfort and stability focused",
                "İkizler": "intellectual sharing and open communication with family; versatile interaction",
                "Yengeç": "family ties woven with emotional depth and affection; protective and nurturing",
                "Aslan": "creativity and generosity in the family; being a source of inspiration to children",
                "Başak": "order and service in the family; practical support and attentive care",
                "Terazi": "balance and harmony in the family; artistic sharing and aesthetic values",
                "Akrep": "deep transformation and loyalty in the family; strong emotional bonds and protection",
                "Yay": "adventure and the passing of wisdom in the family; open-minded and broad perspective",
                "Oğlak": "discipline and responsibility in the family; traditional values and long-term structure",
                "Kova": "innovation and independence in the family; respect for individuality and celebrating difference",
                "Balık": "compassion and a spiritual bond in the family; intuitive understanding and unconditional acceptance",
            }
            BURC_MADDI = {
                "Koç": "entrepreneurial investments and high risk-taking potential; hasty decisions",
                "Boğa": "savings and long-term investments; a preference for real estate and precious metals",
                "İkizler": "diverse income sources; communication and media investments, short-term",
                "Yengeç": "real estate and family investments; seeking a safe harbor, controlling emotional spending",
                "Aslan": "showy investments and art; luxury brands and the entertainment sector",
                "Başak": "detailed budget planning; small savings and practical thrift",
                "Terazi": "joint financial decisions with a partner; aesthetic investments and a search for balance",
                "Akrep": "transformative investments; shared resources, inheritance and tax planning",
                "Yay": "income sources from different cultures; international investments and education",
                "Oğlak": "long-term and disciplined investments; retirement planning and real estate",
                "Kova": "technology and innovative investments; crypto, start-ups and social projects",
                "Balık": "investments with artistic and spiritual value; philanthropy and creative projects",
            }
            BURC_SOSYAL = {
                "Koç": "a natural leader and source of inspiration in your circle; bold and open",
                "Boğa": "a loyal and trustworthy friend; solid and lasting bonds around you",
                "İkizler": "a wide circle and intellectual conversations; communication-focused sociability",
                "Yengeç": "sincere and emotional bonds; a small but deep circle of friends",
                "Aslan": "the star of the social circle; generosity and inspiring leadership",
                "Başak": "service-oriented sociability; volunteering and practical help circles",
                "Terazi": "elegant and balanced social relationships; artistic sharing and an aesthetic circle",
                "Akrep": "deep and selective social bonds; strong alliances built on trust",
                "Yay": "a wide and diverse social circle; friendships from different cultures",
                "Oğlak": "professional and purposeful social circles; career-focused networking",
                "Kova": "original and innovative circles; social groups and digital communities",
                "Balık": "empathetic and spiritual circles; aid associations and spiritual communities",
            }
            BURC_EGITIM = {
                "Koç": "you take quick interest in new topics and dive in boldly; practical and applied learning",
                "Boğa": "in-depth study and gaining practical skills; patient and methodical",
                "İkizler": "you are inclined toward abstract concepts and theoretical knowledge; using multiple sources",
                "Yengeç": "intuitive learning and interest in family/emotional topics; the storytelling method",
                "Aslan": "visual and performance-focused learning; creative projects and presentations",
                "Başak": "systematic and detail-oriented study; research, analysis and practical application",
                "Terazi": "balanced and multi-perspective learning; negotiation and aesthetic studies",
                "Akrep": "research and diving deep; psychology, mystery and transformation topics",
                "Yay": "philosophical and broad-perspective learning; international education and travel",
                "Oğlak": "disciplined and goal-oriented study; certification and career focused",
                "Kova": "innovative and technological learning; online education, digital resources",
                "Balık": "intuitive and creative learning; through art, music and meditation",
            }
            BURC_MANEVİ = {
                "Koç": "active meditation and spiritual connection in nature; bold inner exploration",
                "Boğa": "connection with the earth, nature rituals and physical spiritual practices",
                "İkizler": "philosophical inquiry and mental awareness; writing and meditation",
                "Yengeç": "rituals tied to lunar cycles, family-roots meditation, water meditation",
                "Aslan": "heart-centered meditation, creative visualization, inspiring rituals",
                "Başak": "daily spiritual practices, service meditation, a regular spiritual routine",
                "Terazi": "balance-and-harmony meditation, spiritual expression through art, uniting opposites",
                "Akrep": "transformative meditation, shadow work, deep inner cleansing",
                "Yay": "philosophical meditation, exploring different spiritual traditions, mountain meditation",
                "Oğlak": "disciplined meditation practice, the guru-student relationship, structured spirituality",
                "Kova": "technology-supported meditation, group meditation, innovative spiritual practices",
                "Balık": "deep meditation, spiritual guidance, sea meditation, ego dissolution",
            }
            BURC_SEYAHAT = {
                "Koç": "adventure-filled discoveries, adrenaline-packed routes, solo travel",
                "Boğa": "natural beauty, luxury accommodation, gastronomy tours, slow travel",
                "İkizler": "city-by-city trips, museum and culture tours, short trips",
                "Yengeç": "the lands where you were born and raised, historic sites, comfortable and peaceful holidays",
                "Aslan": "luxury resorts, performing-arts festivals, lavish destinations",
                "Başak": "health tours, wellness centers, clean nature walks, detox camps",
                "Terazi": "cultural capitals, art galleries, romantic getaways, aesthetic destinations",
                "Akrep": "mysterious and historic sites, archaeological sites, deep cultural experiences",
                "Yay": "different continents, far-off cultures, philosophical and historic routes, open-air camps",
                "Oğlak": "mountaineering tours, historic castles, traditional and structural architecture discoveries",
                "Kova": "innovative destinations, science museums, diverse communities, space centers",
                "Balık": "coastal towns, mystical temples, meditation camps, spiritual journeys",
            }
            HASTALIK_MAP = {
                ("Mars",6,"Koç"): "Headaches, migraines, sinusitis, face and head-region ailments",
                ("Mars",6,"Boğa"): "Throat infections, vocal-cord issues, thyroid imbalance",
                ("Mars",6,"Aslan"): "Palpitations, back pain, spine issues",
                ("Mars",6,"Akrep"): "Inflammation, reproductive health, intestinal inflammation",
                ("Mars",6,"Yay"): "Liver, hip region, sciatic nerve",
                ("Satürn",6,"Oğlak"): "Arthritis, joint pain, knee problems, osteoporosis",
                ("Satürn",6,"Kova"): "Circulatory issues, varicose veins, ankle injuries",
                ("Satürn",6,"Balık"): "Foot health, lymphatic system, a tendency to retain water",
                ("Ay",6,"Yengeç"): "Stomach sensitivity, digestive problems, chest health",
                ("Ay",6,"Balık"): "Psychological sensitivity, addictive tendencies, sleep routine",
                ("Ay",6,"Boğa"): "Throat sensitivity, eating disorders, metabolism",
                ("Venüs",6,"Boğa"): "Throat and tonsil issues, skin allergies, kidney balance",
                ("Venüs",6,"Terazi"): "Kidney function, skin sensitivity, hormonal balance",
                ("Neptün",6,"Balık"): "Weakened immunity, chronic fatigue, sleep apnea",
                ("Neptün",6,"Yay"): "Liver sensitivity, allergic reactions",
                ("Güneş",6,"Aslan"): "Heart health, vitality decline, blood-pressure fluctuations",
                ("Plüton",6,"Akrep"): "Immune system, cellular issues, a need for detox",
            }
            BURC_SAGLIK_UYARISI = {
                "Koç": "head region, migraines and injury risk; watch hot conflicts",
                "Boğa": "throat, thyroid and neck muscle tension; a slow-metabolism tendency",
                "İkizler": "nervous system, respiratory tract and communication-related tension",
                "Yengeç": "stomach, digestion, chest region; emotional eating and water retention",
                "Aslan": "heart, back and spine; tension from overexertion",
                "Başak": "intestines, skin and nervous system; stress from being overly meticulous",
                "Terazi": "kidneys, skin and hormonal balance; indecision stress",
                "Akrep": "reproductive system, immunity and intense emotional stress",
                "Yay": "liver, hips and sciatica; overdoing it and pushing limits",
                "Oğlak": "joints, bones, skin and joints; chronic stress and dystonia",
                "Kova": "circulation, ankles and nervous system; unexpected accidents",
                "Balık": "immunity, feet and lymphatic system; medication/allergy sensitivity",
            }

        elif _ES:
            HASTALIK_MAP = {
                ("Mars",6,"Koç"): "Dolores de cabeza, migrañas, sinusitis, afecciones de rostro y cabeza",
                ("Mars",6,"Boğa"): "Infecciones de garganta, cuerdas vocales, desequilibrio tiroideo",
                ("Mars",6,"Aslan"): "Palpitaciones, dolor de espalda, problemas de columna",
                ("Mars",6,"Akrep"): "Inflamación, salud reproductiva, inflamación intestinal",
                ("Mars",6,"Yay"): "Hígado, zona de la cadera, nervio ciático",
                ("Satürn",6,"Oğlak"): "Artrosis, dolor articular, problemas de rodilla, osteoporosis",
                ("Satürn",6,"Kova"): "Problemas circulatorios, varices, torceduras de tobillo",
                ("Satürn",6,"Balık"): "Salud de los pies, sistema linfático, tendencia a retener líquidos",
                ("Ay",6,"Yengeç"): "Sensibilidad estomacal, problemas digestivos, salud torácica",
                ("Ay",6,"Balık"): "Sensibilidad psicológica, tendencias adictivas, rutina de sueño",
                ("Ay",6,"Boğa"): "Sensibilidad de garganta, trastornos alimentarios, metabolismo",
                ("Venüs",6,"Boğa"): "Problemas de garganta y amígdalas, alergias cutáneas, equilibrio renal",
                ("Venüs",6,"Terazi"): "Función renal, sensibilidad cutánea, equilibrio hormonal",
                ("Neptün",6,"Balık"): "Inmunidad debilitada, fatiga crónica, apnea del sueño",
                ("Neptün",6,"Yay"): "Sensibilidad hepática, reacciones alérgicas",
                ("Güneş",6,"Aslan"): "Salud del corazón, caída de vitalidad, fluctuaciones de tensión",
                ("Plüton",6,"Akrep"): "Sistema inmunitario, problemas celulares, necesidad de depuración",
            }
            BURC_SAGLIK_UYARISI = {
                "Koç": "zona de la cabeza, migrañas y riesgo de lesiones; cuidado con los conflictos",
                "Boğa": "garganta, tiroides y tensión muscular en el cuello; tendencia al metabolismo lento",
                "İkizler": "sistema nervioso, vías respiratorias y tensión ligada a la comunicación",
                "Yengeç": "estómago, digestión, zona torácica; alimentación emocional y retención de líquidos",
                "Aslan": "corazón, espalda y columna; tensión por sobreesfuerzo",
                "Başak": "intestinos, piel y sistema nervioso; estrés por exceso de perfeccionismo",
                "Terazi": "riñones, piel y equilibrio hormonal; estrés por indecisión",
                "Akrep": "sistema reproductivo, inmunidad y estrés emocional intenso",
                "Yay": "hígado, caderas y ciática; excesos y sobrepasar límites",
                "Oğlak": "articulaciones, huesos y piel; estrés crónico y distonía",
                "Kova": "circulación, tobillos y sistema nervioso; accidentes inesperados",
                "Balık": "inmunidad, pies y sistema linfático; sensibilidad a medicamentos/alergias",
            }
            BURC_SPOR = {
                "Koç": "correr, boxeo, deportes de combate, campo a través, escalada, sprint",
                "Boğa": "caminata, pilates, entrenamiento de fuerza, deportes de jardín, equitación",
                "İkizler": "ciclismo, bádminton, tenis de mesa, probar varios deportes, tiro con arco",
                "Yengeç": "natación, deportes acuáticos, tai-chi, paseos al atardecer, movimiento rítmico",
                "Aslan": "tenis, culturismo, gimnasia, fitness, deportes de exhibición",
                "Başak": "yoga, pilates, caminata regular, ejercicio al aire libre, estiramientos",
                "Terazi": "baile, pilates, patinaje sobre hielo, gimnasia rítmica, deportes en pareja",
                "Akrep": "boxeo, artes marciales, crossfit, natación, buceo, intervalos de alta intensidad",
                "Yay": "equitación, deportes al aire libre, campamento, tiro con arco, deportes de aventura",
                "Oğlak": "carreras de fondo, ciclismo, escalada, entrenamiento disciplinado, pesas",
                "Kova": "deportes extremos, skate, snowboard, buceo libre, rutinas innovadoras",
                "Balık": "natación, buceo, yoga, tai-chi, movimientos meditativos, deportes acuáticos",
            }
            SPOR_MAP = {
                ("Mars",1): "Correr, boxeo, artes marciales y deportes de combate individual",
                ("Mars",6): "CrossFit, entrenamiento por intervalos, ejercicios de alta intensidad",
                ("Mars",5): "Deportes competitivos, tenis, squash, competiciones deportivas",
                ("Venüs",1): "Baile, pilates, natación, deportes estéticos y fluidos",
                ("Venüs",6): "Yoga, ejercicios de estiramiento, caminatas por la naturaleza",
                ("Venüs",5): "Baile, patinaje sobre hielo, gimnasia rítmica",
                ("Jüpiter",1): "Deportes al aire libre, juegos de equipo, deportes de naturaleza",
                ("Jüpiter",6): "Caminatas largas, trekking, campamentos en la naturaleza",
                ("Jüpiter",9): "Equitación, tiro con arco, deportes de aventura al aire libre",
                ("Satürn",1): "Carreras de fondo, ciclismo, deportes de resistencia",
                ("Satürn",6): "Caminata regular, entrenamiento disciplinado, trabajo con pesas",
                ("Satürn",10): "Maratones, triatlones, objetivos de resistencia a largo plazo",
                ("Ay",1): "Natación, tai-chi, paseos al atardecer, movimiento rítmico",
                ("Ay",6): "Yoga, ejercicios meditativos, deportes de ritmo suave",
                ("Ay",4): "Paseos por el jardín, ejercicio en casa, actividades deportivas en familia",
                ("Uranüs",1): "Deportes extremos, skate, snowboard, rutinas innovadoras",
                ("Uranüs",11): "Deportes extremos en grupo, parkour, buceo libre",
                ("Neptün",1): "Yoga, natación, baile, deportes acuáticos, tai-chi",
                ("Neptün",12): "Movimientos meditativos, qigong, ejercicios corporales espirituales",
                ("Güneş",1): "Tenis, atletismo, deportes que requieren liderazgo",
                ("Güneş",5): "Deportes de exhibición, gimnasia, actuación artística",
                ("Plüton",8): "Fitness transformador, trabajo corporal profundo, deportes de depuración",
                ("Plüton",6): "Yoga terapéutico, meditación, limpieza cuerpo-mente",
                ("Merkür",3): "Marcha rápida, ciclismo, ejercicios multipuesto en el gimnasio",
                ("Merkür",6): "Trabajo de coordinación, ejercicios mente-cuerpo",
            }
            BURC_SANAT = {
                "Koç": "escultura, arte de performance, obras experimentales atrevidas, arte callejero",
                "Boğa": "cerámica, arte con materiales naturales, fotografía, tocar un instrumento",
                "İkizler": "escritura, literatura, teatro, pódcast, arte lingüístico, periodismo",
                "Yengeç": "arte culinario, artesanía, fotografía, música emotiva, narración de historias",
                "Aslan": "artes escénicas, teatro, danza, espectáculo, diseño de vestuario, actuación artística",
                "Başak": "artesanía detallada, diseño digital, el arte de la organización, trabajo fino",
                "Terazi": "diseño de moda, decoración de interiores, artes estéticas, diseño de joyas, fotografía",
                "Akrep": "fotografía, cine, arte transformador, escultura, obras de temática profunda",
                "Yay": "fotografía de viajes, documental, mural, arte callejero, arte intercultural",
                "Oğlak": "arquitectura, escultura, artes estructurales, restauración, técnicas tradicionales",
                "Kova": "arte digital, instalación, videoarte, tecnología-arte, diseño gráfico",
                "Balık": "acuarela, música, danza, arte meditativo, cine, simbolismo espiritual",
            }
            SANAT_MAP = {
                ("Venüs",5): "Pintura, escultura, cerámica, artes visuales",
                ("Venüs",3): "Poesía, literatura, escritura creativa, escribir letras de canciones",
                ("Venüs",10): "Diseño de moda, decoración de interiores, asesoría estética",
                ("Neptün",5): "Música, danza, fotografía, cine y artes escénicas",
                ("Neptün",12): "Arte meditativo, mandala, pintura espiritual, poesía",
                ("Neptün",3): "Tocar un instrumento, cantar, componer",
                ("Merkür",3): "Escritura, periodismo, blog, actuación teatral",
                ("Merkür",5): "Teatro, guion cinematográfico, talleres de escritura creativa",
                ("Ay",4): "Artesanías, tejido, bordado, cerámica, arte culinario",
                ("Ay",5): "Escribir libros infantiles, diseño de juguetes, narración de historias",
                ("Güneş",5): "Artes escénicas, actuación teatral, performance",
                ("Uranüs",5): "Arte digital, diseño gráfico, instalación, arte experimental",
                ("Jüpiter",5): "Artes de performance, mundo del espectáculo, dirección de escena",
                ("Satürn",5): "Arquitectura, escultura, artes estructurales, restauración",
                ("Plüton",5): "Fotografía, arte transformador, obras de temática profunda",
            }
            BURC_HOBI = {
                "Koç": "deportes de aventura, viajes, exploración, deportes de motor, campamento",
                "Boğa": "jardinería, coleccionismo, cocina, investigación de antigüedades, caminatas por la naturaleza",
                "İkizler": "ajedrez, programación, lectura, escuchar pódcast, aprender idiomas, resolver acertijos",
                "Yengeç": "pasatiempos de cocina, fotografía, llevar un diario, conversaciones familiares",
                "Aslan": "teatro, artes escénicas, voluntariado con niños, pasatiempos de espectáculo",
                "Başak": "organizar, artesanía detallada, programación, análisis de datos",
                "Terazi": "música, coleccionismo de arte, eventos sociales, decoración, moda",
                "Akrep": "novelas de misterio, juegos de detectives, buceo, investigación, psicología",
                "Yay": "planificar viajes, filosofía, tiro con arco, exploración de la naturaleza, interacción intercultural",
                "Oğlak": "carpintería, juegos de estrategia, senderismo, planificación, artesanía tradicional",
                "Kova": "tecnología, ciencia ficción, robótica, exploración espacial, proyectos digitales",
                "Balık": "música, fotografía, observación de la naturaleza, meditación, actividades de imaginación",
            }
            BURC_SAGLIK = {
                "Koç": "cuidado de la zona de la cabeza; ejercicio dinámico, pero evita los traumatismos craneales",
                "Boğa": "salud de la garganta y la tiroides; alimentación regular y control del metabolismo",
                "İkizler": "sistema nervioso y vías respiratorias; los ejercicios de respiración son importantes",
                "Yengeç": "estómago y sistema digestivo; sueño regular y equilibrio emocional",
                "Aslan": "salud del corazón y la columna; ejercicios cardiovasculares y corrección de la postura",
                "Başak": "salud intestinal y sensibilidad alimentaria; la alimentación limpia es prioridad",
                "Terazi": "salud de los riñones y la piel; consumo de agua y equilibrio hormonal",
                "Akrep": "sistema reproductivo e inmunidad; depuración y alimentación limpiadora",
                "Yay": "salud del hígado y las caderas; vida activa y ejercicio regular",
                "Oğlak": "salud de articulaciones, huesos y piel; suplementación mineral e hidratación",
                "Kova": "sistema circulatorio y tobillos; ejercicios de circulación sanguínea",
                "Balık": "sistema inmunitario y rutina de sueño; meditación y ritmo regular",
            }
            BURC_BESLENME = {
                "Koç": "alimentos picantes y energéticos; ricos en hierro y proteína, carne roja y verduras de hoja verde",
                "Boğa": "comidas de calidad, sabrosas y saciantes; alimentación natural sin aditivos, lácteos",
                "İkizler": "alimentos ligeros, variados y coloridos; frutos secos, fruta, tentempiés nutritivos",
                "Yengeç": "comidas caseras, naturales y orgánicas; lácteos, sopas y platos calientes",
                "Aslan": "alimentos cardioprotectores, ricos en antioxidantes, frutos rojos, pescado",
                "Başak": "alimentación pura, limpia y orgánica; alimentos ricos en fibra, cereales integrales, tés depurativos",
                "Terazi": "alimentación equilibrada, ligera y colorida; ensaladas, comidas sociales, chocolate",
                "Akrep": "alimentos de sabor intenso, alimentos depurativos, probióticos, ajo y jengibre",
                "Yay": "descubrir distintas cocinas; sabores picantes y exóticos, rica en proteínas",
                "Oğlak": "alimentación rica en minerales, regular y medida; alimentos con calcio para los huesos",
                "Kova": "alimentos innovadores y diferentes; bowls de batido, superalimentos, alternativas vegetarianas",
                "Balık": "mariscos, fuentes de omega-3; alimentos ligeros y ricos en líquidos, infusiones",
            }
            BESLENME_MAP = {
                "Ay_Yengeç": "Comidas caseras, naturales y orgánicas; los lácteos y la comida casera te sientan bien",
                "Ay_Boğa": "Comidas de calidad, sabrosas y saciantes; alimentación natural sin aditivos",
                "Ay_Balık": "Mariscos, fuentes de omega-3; alimentación ligera y rica en líquidos",
                "Ay_Oğlak": "Alimentación regular, disciplinada y a horas; rica en minerales y calcio",
                "Ay_Başak": "Alimentación pura, limpia y orgánica; cuidado con las sensibilidades alimentarias",
                "Venüs_Boğa": "Alimentos de calidad orientados al sabor; embutidos y sabores naturales",
                "Venüs_Terazi": "Alimentación equilibrada, ligera, colorida y variada; comidas sociales",
                "Jüpiter_Yay": "Descubrir distintas cocinas; sabores picantes y exóticos",
                "Jüpiter_Balık": "Mariscos, alimentos de origen vegetal y abundante líquido",
                "Mars_Koç": "Alimentación picante, energética, rica en hierro y proteínas",
                "Mars_Aslan": "Alimentos cardioprotectores, magnesio, alimentos ricos en antioxidantes",
                "Satürn_Oğlak": "Alimentación rica en minerales, con calcio para los huesos",
                "Neptün_Balık": "Alimentación rica en verduras, ligera, líquida y de origen vegetal",
            }
            BURC_ASK = {
                "Koç": "un vínculo apasionado y entusiasta; fuerte atracción física, gestos románticos valientes",
                "Boğa": "lealtad, confianza y compromiso a largo plazo; los placeres sensoriales y la comodidad importan",
                "İkizler": "armonía intelectual y compartir social; la comunicación, el humor y el vínculo mental importan",
                "Yengeç": "un vínculo emocional profundo y sensación de hogar; el afecto, la protección y los valores familiares son fundamentales",
                "Aslan": "romance deslumbrante; atención, aprecio y muestras de amor exuberantes",
                "Başak": "servicio y amor práctico; pequeños gestos regulares, consideración y lealtad",
                "Terazi": "una unión elegante y equilibrada; compartir estético, arte y sentido de la justicia",
                "Akrep": "pasión, misterio y transformación profunda; un vínculo espiritual y sexual intenso",
                "Yay": "amor libre y aventurero; descubrimiento compartido, filosofía y horizontes amplios",
                "Oğlak": "una unión seria, a largo plazo y orientada a objetivos; disciplina y respeto",
                "Kova": "un vínculo original e independiente; armonía intelectual, innovación e idealismo social",
                "Balık": "amor espiritual e incondicional; empatía, entrega y un romance lleno de imaginación",
            }
            BURC_KARIYER = {
                "Koç": "emprendimiento, liderazgo, gestión de emergencias, deportes, carrera militar, empresas emergentes",
                "Boğa": "banca, inmobiliario, alimentación, música, diseño, arte, gestión de valores",
                "İkizler": "comunicación, medios, software, marketing, ventas, periodismo, docencia",
                "Yengeç": "educación, consultoría, turismo, gastronomía, inmobiliario, empresa familiar",
                "Aslan": "artes escénicas, gestión, educación, entretenimiento, relaciones públicas, gestión de marcas de lujo",
                "Başak": "contabilidad, servicios de salud, edición, control de calidad, análisis, TI",
                "Terazi": "derecho, diplomacia, arte, moda, decoración de interiores, mediación, consultoría",
                "Akrep": "investigación, psicología, finanzas, detective, consultoría de transformación, medicina",
                "Yay": "mundo académico, relaciones internacionales, viajes, edición, filosofía",
                "Oğlak": "gestión, arquitectura, ingeniería, servicio público, proyectos a largo plazo",
                "Kova": "tecnología, ciencia, movimientos sociales, aviación, empresas emergentes innovadoras",
                "Balık": "arte, psicología, salud, consultoría, guía espiritual, organizaciones benéficas",
            }
            BURC_AILE = {
                "Koç": "un papel de líder y protector en la familia; transmite valores de valentía e independencia",
                "Boğa": "un vínculo confiable que mantiene las tradiciones familiares; centrado en la comodidad y la estabilidad",
                "İkizler": "compartir intelectual y comunicación abierta con la familia; interacción versátil",
                "Yengeç": "lazos familiares tejidos con profundidad emocional y afecto; protector y nutriente",
                "Aslan": "creatividad y generosidad en la familia; ser una inspiración para los hijos",
                "Başak": "orden y servicio en la familia; apoyo práctico y cuidado atento",
                "Terazi": "equilibrio y armonía en la familia; compartir artístico y valores estéticos",
                "Akrep": "transformación profunda y lealtad en la familia; vínculos emocionales fuertes y protección",
                "Yay": "aventura y transmisión de sabiduría en la familia; mente abierta y perspectiva amplia",
                "Oğlak": "disciplina y responsabilidad en la familia; valores tradicionales y estructura a largo plazo",
                "Kova": "innovación e independencia en la familia; respeto por la individualidad y celebración de las diferencias",
                "Balık": "compasión y vínculo espiritual en la familia; comprensión intuitiva y aceptación incondicional",
            }
            BURC_MADDI = {
                "Koç": "inversiones emprendedoras y alto potencial de asumir riesgos; decisiones impulsivas",
                "Boğa": "ahorro e inversiones a largo plazo; preferencia por inmuebles y metales preciosos",
                "İkizler": "distintas fuentes de ingresos; inversiones en comunicación y medios, a corto plazo",
                "Yengeç": "inversiones inmobiliarias y familiares; búsqueda de puerto seguro y control del gasto emocional",
                "Aslan": "inversiones llamativas y arte; marcas de lujo y sector del entretenimiento",
                "Başak": "planificación presupuestaria detallada; pequeños ahorros y ahorro práctico",
                "Terazi": "decisiones financieras compartidas con la pareja; inversiones estéticas y búsqueda de equilibrio",
                "Akrep": "inversiones transformadoras; recursos compartidos, herencia y planificación fiscal",
                "Yay": "fuentes de ingresos de distintas culturas; inversiones internacionales y educación",
                "Oğlak": "inversiones a largo plazo y disciplinadas; planificación de jubilación e inmuebles",
                "Kova": "inversiones tecnológicas e innovadoras; criptomonedas, empresas emergentes y proyectos sociales",
                "Balık": "inversiones con valor artístico y espiritual; filantropía y proyectos creativos",
            }
            BURC_SOSYAL = {
                "Koç": "un líder natural y fuente de inspiración en tu círculo; valiente y abierto",
                "Boğa": "un amigo leal y confiable; vínculos sólidos y duraderos a tu alrededor",
                "İkizler": "un círculo amplio y conversaciones intelectuales; sociabilidad centrada en la comunicación",
                "Yengeç": "vínculos sinceros y emocionales; un círculo de amigos pequeño pero profundo",
                "Aslan": "la estrella del círculo social; generosidad y liderazgo inspirador",
                "Başak": "sociabilidad orientada al servicio; voluntariado y círculos de ayuda práctica",
                "Terazi": "relaciones sociales elegantes y equilibradas; compartir artístico y un círculo estético",
                "Akrep": "vínculos sociales profundos y selectos; fuertes alianzas basadas en la confianza",
                "Yay": "un círculo social amplio y diverso; amistades de distintas culturas",
                "Oğlak": "círculos sociales profesionales y con propósito; networking orientado a la carrera",
                "Kova": "círculos originales e innovadores; grupos sociales y comunidades digitales",
                "Balık": "círculos empáticos y espirituales; asociaciones solidarias y comunidades espirituales",
            }
            BURC_EGITIM = {
                "Koç": "te interesas rápidamente por temas nuevos y te sumerges con valentía; aprendizaje práctico y aplicado",
                "Boğa": "estudio en profundidad y adquisición de habilidades prácticas; paciente y metódico",
                "İkizler": "te inclinas por conceptos abstractos y conocimiento teórico; uso de múltiples fuentes",
                "Yengeç": "aprendizaje intuitivo e interés por temas familiares y emocionales; el método de la narración",
                "Aslan": "aprendizaje visual y centrado en la actuación; proyectos creativos y presentaciones",
                "Başak": "estudio sistemático y detallista; investigación, análisis y aplicación práctica",
                "Terazi": "aprendizaje equilibrado y con múltiples perspectivas; negociación y estudios estéticos",
                "Akrep": "investigación y profundización; psicología, misterio y temas de transformación",
                "Yay": "aprendizaje filosófico y de perspectiva amplia; educación internacional y viajes",
                "Oğlak": "estudio disciplinado y orientado a objetivos; certificaciones y enfoque profesional",
                "Kova": "aprendizaje innovador y tecnológico; educación online, recursos digitales",
                "Balık": "aprendizaje intuitivo y creativo; a través del arte, la música y la meditación",
            }
            BURC_MANEVİ = {
                "Koç": "meditación activa y conexión espiritual en la naturaleza; exploración interior valiente",
                "Boğa": "conexión con la tierra, rituales de la naturaleza y prácticas espirituales físicas",
                "İkizler": "indagación filosófica y conciencia mental; escritura y meditación",
                "Yengeç": "rituales ligados a los ciclos lunares, meditación de raíces familiares, meditación del agua",
                "Aslan": "meditación centrada en el corazón, visualización creativa, rituales inspiradores",
                "Başak": "prácticas espirituales diarias, meditación de servicio, rutina espiritual regular",
                "Terazi": "meditación de equilibrio y armonía, expresión espiritual a través del arte, unión de opuestos",
                "Akrep": "meditación transformadora, trabajo con la sombra, limpieza interior profunda",
                "Yay": "meditación filosófica, exploración de distintas tradiciones espirituales, meditación de montaña",
                "Oğlak": "práctica disciplinada de meditación, relación gurú-discípulo, espiritualidad estructurada",
                "Kova": "meditación asistida por tecnología, meditación en grupo, prácticas espirituales innovadoras",
                "Balık": "meditación profunda, guía espiritual, meditación marina, disolución del ego",
            }
            BURC_SEYAHAT = {
                "Koç": "descubrimientos llenos de aventura, rutas cargadas de adrenalina, viajes en solitario",
                "Boğa": "bellezas naturales, alojamiento de lujo, tours gastronómicos, viaje lento",
                "İkizler": "recorridos ciudad por ciudad, tours de museos y cultura, viajes cortos",
                "Yengeç": "las tierras donde naciste y creciste, sitios históricos, vacaciones cómodas y tranquilas",
                "Aslan": "complejos turísticos de lujo, festivales de artes escénicas, destinos ostentosos",
                "Başak": "tours de salud, centros de bienestar, caminatas por naturaleza limpia, campamentos de depuración",
                "Terazi": "capitales culturales, galerías de arte, escapadas románticas, destinos estéticos",
                "Akrep": "lugares misteriosos e históricos, sitios arqueológicos, experiencias culturales profundas",
                "Yay": "distintos continentes, culturas lejanas, rutas filosóficas e históricas, campamentos al aire libre",
                "Oğlak": "tours de montañismo, castillos históricos, descubrimientos de arquitectura tradicional y estructural",
                "Kova": "destinos innovadores, museos de ciencia, comunidades diversas, centros espaciales",
                "Balık": "pueblos costeros, templos místicos, campamentos de meditación, viajes espirituales",
            }

        # ── Yardımcı fonksiyonlar ──
        def _gad(g_ad):
            return pdf_label(g_ad)

        def _spor_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            key = (g_ad, ev_no)
            if key in SPOR_MAP:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {SPOR_MAP[key]}"
            burc_spor = BURC_SPOR.get(burc)
            if burc_spor:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {burc_spor}"
            return None

        def _sanat_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            key = (g_ad, ev_no)
            if key in SANAT_MAP:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {SANAT_MAP[key]}"
            burc_sanat = BURC_SANAT.get(burc)
            if burc_sanat:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {burc_sanat}"
            return None

        def _hobi_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_hobi = BURC_HOBI.get(burc)
            if burc_hobi:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {burc_hobi}"
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
                if _ES:
                    return f"Influencia de {_gad(g_ad)} en {_hburc(burc_no)}: {uyari}"
                return f"{_gad(g_ad)} influence on {_hburc(burc_no)}: {uyari}"
            return None

        def _saglik_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            saglik = BURC_SAGLIK.get(burc)
            if saglik:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {saglik}"
            return None

        def _beslenme_onerisi(g_ad, burc_no):
            burc = BURCLAR[burc_no % 12]
            key = f"{g_ad}_{burc}"
            if key in BESLENME_MAP:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {BESLENME_MAP[key]}"
            burc_besl = BURC_BESLENME.get(burc)
            if burc_besl:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {burc_besl}"
            return None

        def _ask_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_ask = BURC_ASK.get(burc)
            if burc_ask:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {burc_ask}"
            return None

        def _kariyer_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_kar = BURC_KARIYER.get(burc)
            if burc_kar:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {burc_kar}"
            return None

        def _aile_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_ail = BURC_AILE.get(burc)
            if burc_ail:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {burc_ail}"
            return None

        def _maddi_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_mad = BURC_MADDI.get(burc)
            if burc_mad:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {burc_mad}"
            return None

        def _sosyal_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_sos = BURC_SOSYAL.get(burc)
            if burc_sos:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {burc_sos}"
            return None

        def _egitim_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_egi = BURC_EGITIM.get(burc)
            if burc_egi:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {burc_egi}"
            return None

        def _manevi_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_man = BURC_MANEVİ.get(burc)
            if burc_man:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {burc_man}"
            return None

        def _seyahat_onerisi(g_ad, ev_no, burc_no):
            burc = BURCLAR[burc_no % 12]
            burc_sey = BURC_SEYAHAT.get(burc)
            if burc_sey:
                return f"{_gad(g_ad)} • {_hburc(burc_no)}: {burc_sey}"
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

        if _EN:
            ALAN_EN = {
                "spor": {"etiket":"Sports & Fitness","giris":"Physical activity holds an important place in your life; your body carries a natural call to move.","kapanis":"Movement is life — listen to your body."},
                "sanat": {"etiket":"Art & Creativity","giris":"Creativity and aesthetic sensitivity form the colorful side of life for you.","kapanis":"Art is the food of the soul — nourish the creativity within you."},
                "hobi": {"etiket":"Hobbies & Interests","giris":"How you spend your free time is directly linked to the variety of your interests.","kapanis":"Every moment of joy is a gift that feeds your soul."},
                "saglik": {"etiket":"Health & Vitality","giris":"The balance between body and mind is a reflection of your daily habits.","kapanis":"A healthy life is built through the big effect of small habits."},
                "beslenme": {"etiket":"Nutrition & Diet","giris":"What you eat affects not only your body but also your emotional world directly.","kapanis":"What you eat feeds not only your body but also your soul."},
                "ask": {"etiket":"Love & Romance","giris":"Your love life is shaped by the emotional codes hidden deep within your heart.","kapanis":"True love begins with the love you hold for yourself."},
                "kariyer": {"etiket":"Career & Work Life","giris":"Your career journey takes shape where discipline and vision meet.","kapanis":"Success comes through bold steps taken at the right time."},
                "aile": {"etiket":"Family & Roots","giris":"Your family bonds and roots are the key to understanding who you are.","kapanis":"Your family bonds are your greatest spiritual inheritance."},
                "maddi": {"etiket":"Financial Situation","giris":"When your financial flow aligns with your values, abundance arrives naturally.","kapanis":"Financial balance begins by clarifying your values."},
                "sosyal": {"etiket":"Social Life","giris":"Your social circle, communication style and interaction enrich your life.","kapanis":"Your circle is your greatest mirror and teacher."},
                "egitim": {"etiket":"Education & Mind","giris":"Your desire to learn and your mental curiosity continually push you toward growth.","kapanis":"Learning is a journey that never ends."},
                "manevi": {"etiket":"Spirituality & Inner Journey","giris":"Your inner journey reaches into the depths of unseen connections and intuitive awareness.","kapanis":"Inner peace is the essence of everything you seek in the outer world."},
                "seyahat": {"etiket":"Travel & Discovery","giris":"Your urge to explore is a reflection of your longing for new horizons.","kapanis":"Every journey is an opportunity to discover yourself."},
            }
            for _a in ALANLAR:
                _en_info = ALAN_EN.get(_a["anahtar"])
                if _en_info:
                    _a["etiket"] = _en_info["etiket"]
                    _a["giris"] = _en_info["giris"]
                    _a["kapanis"] = _en_info["kapanis"]

        elif _ES:
            ALAN_ES_ETIKET = {
                "spor": "Deporte y Forma Física",
                "sanat": "Arte y Creatividad",
                "hobi": "Pasatiempos e Intereses",
                "saglik": "Salud y Vitalidad",
                "beslenme": "Nutrición y Dieta",
                "ask": "Amor y Romance",
                "kariyer": "Carrera y Vida Laboral",
                "aile": "Familia y Raíces",
                "maddi": "Situación Financiera",
                "sosyal": "Vida Social",
                "egitim": "Educación y Mente",
                "manevi": "Espiritualidad y Viaje Interior",
                "seyahat": "Viajes y Descubrimiento",
            }
            ALAN_ES_GIRIS = {
                "spor": "La actividad física ocupa un lugar importante en tu vida; El movimiento es parte esencial de tu vida; tu cuerpo anhela expresarse y ponerse en acción de forma natural.",
                "sanat": "La creatividad y la sensibilidad estética dan color y sentido a tu vida.",
                "hobi": "Tu tiempo libre revela la riqueza de tus intereses y la forma en que disfrutas la vida.",
                "saglik": "El equilibrio entre cuerpo y mente se refleja en tus hábitos cotidianos.",
                "beslenme": "Lo que comes afecta no solo a tu cuerpo, sino también directamente a tu mundo emocional.",
                "ask": "Tu vida amorosa nace de los códigos emocionales más profundos de tu corazón.",
                "kariyer": "Tu camino profesional se forja en el encuentro entre disciplina y visión.",
                "aile": "Tus raíces y lazos familiares son la base que te define.",
                "maddi": "Cuando tu flujo económico vibra en sintonía con tus valores, la abundancia fluye con naturalidad.",
                "sosyal": "Tu círculo social y tu forma de comunicar enriquecen cada aspecto de tu vida.",
                "egitim": "Tu curiosidad y deseo de aprender te impulsan a crecer sin pausa.",
                "manevi": "Tu viaje interior te lleva a lo invisible, a tu intuición más profunda.",
                "seyahat": "Tu anhelo de explorar nace del deseo de abrir nuevos horizontes.",
            }
            ALAN_ES_KAPANIS = {
                "spor": "Moverse es vivir; escucha con atención lo que tu cuerpo te pide.",
                "sanat": "El arte alimenta el alma; cultiva sin miedo la creatividad que habita en ti.",
                "hobi": "Cada instante de disfrute es un regalo que nutre tu esencia.",
                "saglik": "Una vida saludable nace de pequeños hábitos sostenidos con amor.",
                "beslenme": "Alimentar tu cuerpo es también alimentar tu alma.",
                "ask": "El amor verdadero comienza por el amor que te das a ti mismo.",
                "kariyer": "El éxito florece cuando das pasos valientes en el momento justo.",
                "aile": "Tus lazos familiares son tu herencia espiritual más valiosa.",
                "maddi": "La claridad en tus valores es la base de tu equilibrio material.",
                "sosyal": "Tu entorno refleja con honestidad quién eres y te enseña a crecer.",
                "egitim": "Aprender es un viaje infinito que te expande.",
                "manevi": "La paz interior es el verdadero destino de toda búsqueda externa.",
                "seyahat": "Cada viaje es un reencuentro contigo mismo.",
            }
            # Fix page 10-12 systematic translations
            def _fix_es_alan(s):
                if not isinstance(s, str):
                    return s
                s = s.replace("Alimentos como alimentos ligeros,", "Alimentos ligeros,")
                s = s.replace("Alimentos como alimentos ligeros", "Alimentos ligeros")
                s = s.replace("sabores picantes y exóticos, rica en proteínas", "sabores picantes y exóticos, ricos en proteínas")
                s = s.replace("En tus relaciones, la búsqueda de un vínculo apasionado y entusiasta, una fuerte atracción física.", "En tus relaciones, buscas un vínculo apasionado y entusiasta, así como una fuerte atracción física.")
                s = s.replace("directamente a tu mundo emocional", "a tu mundo emocional")
                return s
            for _a in ALANLAR:
                if _a["anahtar"] in ALAN_ES_ETIKET:
                    _a["etiket"] = _fix_es_alan(ALAN_ES_ETIKET[_a["anahtar"]])
                if _a["anahtar"] in ALAN_ES_GIRIS:
                    _a["giris"] = _fix_es_alan(ALAN_ES_GIRIS[_a["anahtar"]])
                if _a["anahtar"] in ALAN_ES_KAPANIS:
                    _a["kapanis"] = _fix_es_alan(ALAN_ES_KAPANIS[_a["anahtar"]])

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
            ELEMENT_AD_EN = {"Ateş":"Fire","Toprak":"Earth","Hava":"Air","Su":"Water"}
            dominan_en = ELEMENT_AD_EN.get(dominan, dominan)
            ELEMENT_AD_ES = {"Ateş":"Fuego","Toprak":"Tierra","Hava":"Aire","Su":"Agua"}
            dominan_es = ELEMENT_AD_ES.get(dominan, dominan)

            # ── Natural language yorum generation (no planet names) ──
            havuz = [alan["giris"]]

            ELEMENT_ACIKLAMA = {
                "Ateş": "içinizdeki dinamik ve tutkulu enerji, harekete geçme cesaretiniz",
                "Toprak": "sabit ve güvenilir yapınız, sağlam temeller kurma beceriniz",
                "Hava": "zihinsel berraklığınız ve iletişim kurma yeteneğiniz",
                "Su": "derin duygusal sezgileriniz ve empatik anlayışınız",
            }
            ELEMENT_ACIKLAMA_EN = {
                "Ateş": "your dynamic and passionate energy, your courage to take action",
                "Toprak": "your steady and reliable nature, your ability to build solid foundations",
                "Hava": "your mental clarity and your ability to communicate",
                "Su": "your deep emotional intuition and empathic understanding",
            }
            ELEMENT_ACIKLAMA_ES = {
                "Ateş": "tu energía dinámica y apasionada, tu valentía para actuar",
                "Toprak": "tu naturaleza firme y confiable, tu capacidad para construir bases sólidas",
                "Hava": "tu claridad mental y tu capacidad de comunicación",
                "Su": "tus intuiciones emocionales profundas y tu comprensión empática",
            }
            eac = element_acik = ELEMENT_ACIKLAMA.get(dominan, "enerjiniz")
            eac_baslik = eac[0].upper() + eac[1:] if eac else eac
            if _EN:
                eac = element_acik = ELEMENT_ACIKLAMA_EN.get(dominan, "your energy")
                eac_baslik = eac[0].upper() + eac[1:] if eac else eac
            if _ES:
                eac = element_acik = ELEMENT_ACIKLAMA_ES.get(dominan, "tu energía")
                eac_baslik = eac[0].upper() + eac[1:] if eac else eac

            if _EN:
                ALAN_DOMINAN = {
                    "spor": f"You have a body constitution in which the {dominan_en} element especially comes to the fore. Rather than forcing your body, you get the most efficient results when you align with its natural rhythm.",
                    "sanat": f"The traces of the {dominan_en} element are clear in your artistic expression — {eac} is the main source feeding your creativity.",
                    "hobi": f"Activities guided by the {dominan_en} element appeal to you more in your free time. {eac_baslik} forms the foundation of your interests.",
                    "saglik": f"Your health is sensitive to the balance of the {dominan_en} element — {eac} helps you read your body's signals correctly.",
                    "beslenme": f"The influence of the {dominan_en} element is visible in your eating habits. {eac_baslik} plays an important role in determining which foods suit you.",
                    "ask": f"The energy of the {dominan_en} element stands out in your love life. {eac_baslik} deeply affects how you form emotional bonds.",
                    "kariyer": f"The qualities of the {dominan_en} element are decisive in your career journey. {eac_baslik} is your greatest strength in your work life.",
                    "aile": f"Your family bonds are woven with the texture of the {dominan_en} element. {eac_baslik} determines the quality of the bond you build with your roots.",
                    "maddi": f"The approach of the {dominan_en} element guides you in financial matters. {eac_baslik} shapes your financial decisions.",
                    "sosyal": f"You move with the energy of the {dominan_en} element in your social circle. {eac_baslik} strengthens the bonds you build with your surroundings.",
                    "egitim": f"Your learning style suits the nature of the {dominan_en} element. {eac_baslik} determines how you internalize knowledge.",
                    "manevi": f"Your spiritual journey advances under the guidance of the {dominan_en} element. {eac_baslik} is the core dynamic of your spiritual search.",
                    "seyahat": f"Your urge to explore is nourished by the energy of the {dominan_en} element. {eac_baslik} gives you the courage to open up to new horizons.",
                }
                ELEMENT_ONERI = {
                    "spor": {"Ateş":"high-tempo cardio, combat sports and team games","Toprak":"weight training, pilates and nature walks","Hava":"dance, stretching and group fitness classes","Su":"swimming, yoga and water exercises"},
                    "sanat": {"Ateş":"sculpture, performance art and experimental works","Toprak":"ceramics, weaving and art with natural materials","Hava":"digital art, literature and photography","Su":"watercolor, music and emotionally expressive arts"},
                    "hobi": {"Ateş":"adventure sports, travel and exploration","Toprak":"gardening, collecting and crafts","Hava":"chess, software and reading","Su":"music, photography and nature observation"},
                    "saglik": {"Ateş":"dynamic exercise and high-energy activities","Toprak":"regular sleep, a solid daily routine and natural eating","Hava":"breathing practices and the mind-body connection","Su":"meditation, water therapy and emotional balance"},
                    "beslenme": {"Ateş":"light, fresh and revitalizing foods; be careful with spicy meals","Toprak":"regular meals, root vegetables and natural grains","Hava":"varied and colorful foods; the joy of social meals","Su":"water-rich foods, seafood and herbal teas"},
                    "ask": {"Ateş":"a search for a passionate and enthusiastic bond, strong physical attraction","Toprak":"loyalty, trust and long-term commitment come first","Hava":"intellectual harmony and social sharing matter","Su":"you seek a deep emotional bond and spiritual harmony"},
                    "kariyer": {"Ateş":"pioneering and entrepreneurial roles, leadership positions","Toprak":"constructive and managerial positions, financial stability","Hava":"communication, software, media and consulting","Su":"art, psychology, health and consulting fields"},
                    "aile": {"Ateş":"you take on a leader and protector role in the family","Toprak":"you build a trustworthy bond that keeps family traditions","Hava":"intellectual sharing and open communication with family","Su":"family bonds woven with emotional depth and affection"},
                    "maddi": {"Ateş":"high entrepreneurial investment and risk-taking potential","Toprak":"savings and long-term investments suit you","Hava":"gain through intellectual capital and networking","Su":"investments with artistic and emotional value suit you"},
                    "sosyal": {"Ateş":"you are a natural leader and source of inspiration in your circle","Toprak":"a loyal and trustworthy friend, solid bonds around you","Hava":"a wide circle and intellectual conversations nourish you","Su":"you build deep friendships and empathic bonds"},
                    "egitim": {"Ateş":"you take quick interest in new topics and dive in boldly","Toprak":"in-depth study and gaining practical skills","Hava":"you are inclined toward abstract concepts and theoretical knowledge","Su":"intuitive learning and psychological topics draw your interest"},
                    "manevi": {"Ateş":"active meditation and spiritual connection in nature","Toprak":"rituals and daily spiritual practices","Hava":"philosophical inquiry and mental awareness","Su":"deep meditation, yoga and spiritual guidance"},
                    "seyahat": {"Ateş":"adventure-filled discoveries and adrenaline-packed routes","Toprak":"natural beauty and cultural tours","Hava":"intellectual travel and learning new cultures","Su":"seaside, mystical and spiritual journeys"},
                }
                oneri_metni = ELEMENT_ONERI.get(anahtar, {}).get(dominan, "activities suited to your natural constitution")
                ALAN_OZEL_CUMLER = {
                    "spor": f"The most suitable sports for you are activities like {oneri_metni}. Rather than forcing your body, you get the most efficient results when you align with its natural rhythm.",
                    "sanat": f"Your creative side is shaped most under the influence of the {dominan_en} element. Artistic expression forms like {oneri_metni} come naturally to you. When you allow your intuition to guide you, truly original work emerges.",
                    "hobi": f"Your interests reflect the qualities of the {dominan_en} element. Hobbies like {oneri_metni} appeal to you more. Your curiosity in this area constantly pushes you to try new things.",
                    "saglik": f"Understanding the needs of the {dominan_en} element in health gives you a big advantage. The activities that suit you best can be listed as {oneri_metni}. When you heed your body's signals, you make the right choices.",
                    "beslenme": f"Arranging your eating habits according to the balance of the {dominan_en} element will serve you well. Foods like {oneri_metni} nourish your body both physically and spiritually.",
                    "ask": f"In your relationships, {oneri_metni}. Your search for depth and sincerity in your emotional world keeps you away from superficial bonds. When you listen to your heart, you find the right path.",
                    "kariyer": f"You use the strong qualities of the {dominan_en} element in your professional life. {oneri_metni} help you reach success in your career. Taking disciplined steps brings you stability.",
                    "aile": f"Your family bonds take shape in keeping with the nature of the {dominan_en} element. {oneri_metni}. When you recognize the strength you draw from your roots, you make peace with your past and move toward the future with firm steps.",
                    "maddi": f"In financial matters, {oneri_metni}. When you clarify your values and trust the flow, you manage your resources more consciously.",
                    "sosyal": f"In your social circle, {oneri_metni}. Your search for sincerity and depth in the bonds you build earns you meaningful friendships.",
                    "egitim": f"Your learning process carries the qualities of the {dominan_en} element. {oneri_metni}. The deeper you go into the subjects you are curious about, the more you feel the power knowledge gives you.",
                    "manevi": f"{oneri_metni} guides you on your inner journey. When you set aside time for silence and introspection in your spiritual search, you gain new awareness about yourself.",
                    "seyahat": f"Your spirit of discovery comes alive with the energy of the {dominan_en} element. {oneri_metni} give you not only pleasure but also a deep perspective.",
                }
            elif _ES:
                ALAN_DOMINAN = {
                    "spor": f"Tienes una constitución física en la que destaca especialmente el elemento {dominan_es}. En lugar de forzar tu cuerpo, obtienes los resultados más eficientes cuando te alineas con su ritmo natural.",
                    "sanat": f"Las huellas del elemento {dominan_es} son evidentes en tu expresión artística — {eac} son la fuente principal que alimenta tu creatividad.",
                    "hobi": f"En tu tiempo libre te atraen más las actividades guiadas por el elemento {dominan_es}. {eac_baslik} forma parte de la base de tus intereses.",
                    "saglik": f"Tu salud es sensible al equilibrio del elemento {dominan_es} — {eac} te ayuda a leer correctamente las señales de tu cuerpo.",
                    "beslenme": f"La influencia del elemento {dominan_es} se aprecia en tus hábitos alimentarios. {eac_baslik} juega un papel importante a la hora de determinar qué alimentos te sientan bien.",
                    "ask": f"En tu vida amorosa destaca la energía del elemento {dominan_es}. {eac_baslik} afecta profundamente a cómo formas vínculos emocionales.",
                    "kariyer": f"Las cualidades del elemento {dominan_es} son decisivas en tu camino profesional. {eac_baslik} es tu mayor fortaleza en tu vida laboral.",
                    "aile": f"Tus lazos familiares están tejidos con la textura del elemento {dominan_es}. {eac_baslik} determina la calidad del vínculo que estableces con tus raíces.",
                    "maddi": f"En asuntos económicos te guía el enfoque del elemento {dominan_es}. {eac_baslik} da forma a tus decisiones financieras.",
                    "sosyal": f"Te mueves con la energía del elemento {dominan_es} en tu círculo social. {eac_baslik} fortalece los lazos que construyes con tu entorno.",
                    "egitim": f"Tu estilo de aprendizaje se adapta a la naturaleza del elemento {dominan_es}. {eac_baslik} determina cómo interiorizas el conocimiento.",
                    "manevi": f"Tu viaje espiritual avanza guiado por el elemento {dominan_es}. {eac_baslik} es la dinámica central de tu búsqueda espiritual.",
                    "seyahat": f"Tu ansia de explorar se nutre de la energía del elemento {dominan_es}. {eac_baslik} te da el coraje para abrirte a nuevos horizontes.",
                }
                ELEMENT_ONERI = {
                    "spor": {"Ateş":"cardio de alto ritmo, deportes de combate y juegos de equipo","Toprak":"entrenamiento de fuerza, pilates y caminatas por la naturaleza","Hava":"baile, estiramientos y clases de fitness en grupo","Su":"natación, yoga y ejercicios acuáticos"},
                    "sanat": {"Ateş":"escultura, arte de performance y obras experimentales","Toprak":"cerámica, tejido y arte con materiales naturales","Hava":"arte digital, literatura y fotografía","Su":"acuarela, música y artes de expresión emocional"},
                    "hobi": {"Ateş":"deportes de aventura, viajes y exploración","Toprak":"jardinería, coleccionismo y artesanías","Hava":"ajedrez, programación y lectura","Su":"música, fotografía y observación de la naturaleza"},
                    "saglik": {"Ateş":"ejercicio dinámico y actividades de alta energía","Toprak":"sueño regular, una rutina diaria sólida y alimentación natural","Hava":"prácticas de respiración y la conexión mente-cuerpo","Su":"meditación, hidroterapia y equilibrio emocional"},
                    "beslenme": {"Ateş":"alimentos ligeros, frescos y revitalizantes; cuidado con las comidas picantes","Toprak":"comidas regulares, vegetales de raíz y cereales naturales","Hava":"alimentos variados y coloridos; el placer de las comidas sociales","Su":"alimentos ricos en agua, mariscos e infusiones"},
                    "ask": {"Ateş":"buscas un vínculo apasionado y entusiasta, así como una fuerte atracción física","Toprak":"la lealtad, la confianza y el compromiso a largo plazo importan primero","Hava":"importan la armonía intelectual y el compartir social","Su":"buscas un vínculo emocional profundo y armonía espiritual"},
                    "kariyer": {"Ateş":"Los roles pioneros y emprendedores, posiciones de liderazgo","Toprak":"posiciones constructivas y de gestión, estabilidad financiera","Hava":"comunicación, software, medios y consultoría","Su":"ámbitos del arte, la psicología, la salud y la consultoría"},
                    "aile": {"Ateş":"Asumes un papel de líder y protector en la familia","Toprak":"construyes un vínculo confiable que mantiene las tradiciones familiares","Hava":"compartir intelectual y comunicación abierta con la familia","Su":"lazos familiares tejidos con profundidad emocional y afecto"},
                    "maddi": {"Ateş":"tienes un alto potencial para la inversión emprendedora y para asumir riesgos","Toprak":"te convienen el ahorro y las inversiones a largo plazo","Hava":"ganancias mediante el capital intelectual y las redes de contactos","Su":"te convienen las inversiones con valor artístico y emocional"},
                    "sosyal": {"Ateş":"eres un líder natural y fuente de inspiración en tu círculo","Toprak":"un amigo leal y confiable, vínculos sólidos a tu alrededor","Hava":"un círculo amplio y conversaciones intelectuales te nutren","Su":"construyes amistades profundas y vínculos empáticos"},
                    "egitim": {"Ateş":"Te interesas rápidamente por temas nuevos y te sumerges con valentía","Toprak":"estudio en profundidad y adquisición de habilidades prácticas","Hava":"te inclinas por conceptos abstractos y conocimiento teórico","Su":"el aprendizaje intuitivo y los temas psicológicos despiertan tu interés"},
                    "manevi": {"Ateş":"La meditación activa y la conexión espiritual con la naturaleza","Toprak":"rituales y prácticas espirituales diarias","Hava":"indagación filosófica y conciencia mental","Su":"meditación profunda, yoga y guía espiritual"},
                    "seyahat": {"Ateş":"Los descubrimientos llenos de aventura y las rutas cargadas de adrenalina","Toprak":"bellezas naturales y tours culturales","Hava":"viajes intelectuales y aprendizaje de nuevas culturas","Su":"viajes junto al mar, místicos y espirituales"},
                }
                oneri_metni = ELEMENT_ONERI.get(anahtar, {}).get(dominan, "actividades acordes con tu constitución natural")
                ALAN_OZEL_CUMLER = {
                    "spor": f"Los deportes más adecuados para ti son actividades como {oneri_metni}. En lugar de forzar tu cuerpo, obtienes los resultados más eficientes cuando te alineas con su ritmo natural.",
                    "sanat": f"Tu lado creativo se forma sobre todo bajo la influencia del elemento {dominan_es}. Formas de expresión artística como {oneri_metni} te resultan naturales. Cuando permites que tu intuición te guíe, surge un trabajo realmente original.",
                    "hobi": f"Tus intereses reflejan las cualidades del elemento {dominan_es}. Los pasatiempos como {oneri_metni} te atraen más. Tu curiosidad en este campo te empuja constantemente a probar cosas nuevas.",
                    "saglik": f"Entender las necesidades del elemento {dominan_es} en la salud te da una gran ventaja. Las actividades que mejor te sientan pueden enumerarse como {oneri_metni}. Cuando atiendes las señales de tu cuerpo, tomas las decisiones correctas.",
                    "beslenme": f"Organizar tus hábitos alimentarios según el equilibrio del elemento {dominan_es} te vendrá bien. Alimentos como {oneri_metni} nutren tu cuerpo tanto física como espiritualmente.",
                    "ask": f"En tus relaciones, {oneri_metni}. Tu búsqueda de profundidad y sinceridad en tu mundo emocional te aleja de los vínculos superficiales. Cuando escuchas a tu corazón, encuentras el camino correcto.",
                    "kariyer": f"Utilizas las fuertes cualidades del elemento {dominan_es} en tu vida profesional. {oneri_metni} te ayudan a alcanzar el éxito en tu carrera. Dar pasos disciplinados te aporta estabilidad.",
                    "aile": f"Tus lazos familiares se forman en sintonía con la naturaleza del elemento {dominan_es}. {oneri_metni}. Cuando reconoces la fuerza que recibes de tus raíces, haces las paces con tu pasado y avanzas con paso firme hacia el futuro.",
                    "maddi": f"En asuntos económicos, {oneri_metni}. Cuando aclaras tus valores y confías en el flujo, gestionas tus recursos de forma más consciente.",
                    "sosyal": f"En tu círculo social, {oneri_metni}. Tu búsqueda de sinceridad y profundidad en los vínculos que construyes te granjea amistades significativas.",
                    "egitim": f"Tu proceso de aprendizaje lleva las cualidades del elemento {dominan_es}. {oneri_metni}. Cuanto más profundizas en los temas que te interesan, más sientes el poder que te da el conocimiento.",
                    "manevi": f"{oneri_metni} te guían en tu viaje interior. Cuando reservas tiempo para el silencio y la introspección en tu búsqueda espiritual, adquieres una mayor conciencia de ti mismo.",
                    "seyahat": f"Tu espíritu de descubrimiento cobra vida con la energía del elemento {dominan_es}. {oneri_metni} te aportan no solo placer, sino también una perspectiva profunda.",
                }
            else:
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
                "Ateş": "Haftada en az 3 gün yüksek tempolu egzersiz; dinamik ve rekabetçi sporlar enerjinizi besler." if not _EN else "At least 3 days a week of high-tempo exercise; dynamic and competitive sports feed your energy.",
                "Toprak": "Düzenli ve sabit bir antrenman programı; doğa yürüyüşleri ve ağırlık çalışmaları ideal." if not _EN else "A regular and steady training program; nature walks and weight training are ideal.",
                "Hava": "Grup dersleri ve dans temelli egzersizler; zihinsel bağlantı kuran sporlar sizi besler." if not _EN else "Group classes and dance-based workouts; sports that create a mental connection feed you.",
                "Su": "Ritmik ve akıcı sporlar; yüzme, yoga, tai-chi gibi su ve meditasyon odaklı aktiviteler." if not _EN else "Rhythmic and fluid sports; water- and meditation-focused activities like swimming, yoga and tai-chi."
            }
            ELEMENT_SANAT_IPUCU = {
                "Ateş": "Cesur ve deneysel sanat dallarına dalın; performans ve sahne sanatları size enerji katar." if not _EN else "Dive into bold and experimental art forms; performance and stage arts add energy to you.",
                "Toprak": "Somut ve elle yapılan sanatlara odaklanın; seramik, ahşap, dokuma gibi doğal malzemeler." if not _EN else "Focus on tangible, handmade arts; natural materials like ceramics, wood and weaving.",
                "Hava": "Yazı, edebiyat ve dijital sanatlar zihinsel yaratıcılığınızı besler; iletişim temelli sanatlar." if not _EN else "Writing, literature and digital arts feed your mental creativity; communication-based arts.",
                "Su": "Müzik, suluboya ve duygusal ifade sanatları; sezgilerinizin rehberliğine bırakın kendinizi." if not _EN else "Music, watercolor and emotionally expressive arts; let yourself be guided by your intuition."
            }
            ELEMENT_BESLENME_IPUCU = {
                "Ateş": "Enerji veren ve baharatlı besinler; yeşil yapraklılar ve protein ağırlıklı beslenme." if not _EN else "Energizing and spicy foods; leafy greens and protein-heavy eating.",
                "Toprak": "Toprak ürünleri ve köklü sebzeler; düzenli öğünler ve doğal gıdalar." if not _EN else "Root crops and root vegetables; regular meals and natural foods.",
                "Hava": "Çeşitli ve renkli besinler; hafif atıştırmalıklar ve sosyal yemek deneyimleri." if not _EN else "Varied and colorful foods; light snacks and social dining experiences.",
                "Su": "Sıvı tüketimi ve deniz ürünleri; çorbalar, çaylar ve bitki bazlı beslenme." if not _EN else "Fluid intake and seafood; soups, teas and plant-based eating."
            }
            ELEMENT_GENEL_IPUCU = {
                "spor": ELEMENT_SPOR_IPUCU,
                "sanat": ELEMENT_SANAT_IPUCU,
                "beslenme": ELEMENT_BESLENME_IPUCU,
            }
            if _ES:
                ELEMENT_SPOR_IPUCU = {
                    "Ateş": "Ejercicio de alto ritmo al menos 3 días a la semana; los deportes dinámicos y competitivos alimentan tu energía.",
                    "Toprak": "Un programa de entrenamiento regular y constante; son ideales las caminatas por la naturaleza y el trabajo con pesas.",
                    "Hava": "Clases en grupo y ejercicios basados en el baile; los deportes que crean una conexión mental te nutren.",
                    "Su": "Deportes rítmicos y fluidos; actividades centradas en el agua y la meditación, como natación, yoga y tai-chi."
                }
                ELEMENT_SANAT_IPUCU = {
                    "Ateş": "Sumérgete en disciplinas artísticas atrevidas y experimentales; el performance y las artes escénicas te aportan energía.",
                    "Toprak": "Céntrate en artes concretas y hechas a mano; materiales naturales como la cerámica, la madera y el tejido.",
                    "Hava": "La escritura, la literatura y las artes digitales alimentan tu creatividad mental; artes basadas en la comunicación.",
                    "Su": "La música, la acuarela y las artes de expresión emocional; déjate guiar por tu intuición."
                }
                ELEMENT_BESLENME_IPUCU = {
                    "Ateş": "Alimentos energéticos y picantes; verduras de hoja verde y una dieta rica en proteínas.",
                    "Toprak": "Cultivos de la tierra y vegetales de raíz; comidas regulares y alimentos naturales.",
                    "Hava": "Alimentos variados y coloridos; tentempiés ligeros y experiencias de comida social.",
                    "Su": "Consumo de líquidos y mariscos; sopas, infusiones y una alimentación de origen vegetal."
                }
            if _EN:
                kat_oneriler = {
                    "spor": [ELEMENT_SPOR_IPUCU.get(dominan, "Regular exercise and sports suited to your element are ideal.")],
                    "sanat": [ELEMENT_SANAT_IPUCU.get(dominan, "Try different art forms to discover your artistic expression.")],
                    "hobi": ["Try returning to the activities you enjoyed in childhood; curiosity is always a good guide."],
                    "saglik": ["Do not skip a comprehensive health check-up once a year; regular sleep and natural eating are your priorities."],
                    "beslenme": [ELEMENT_BESLENME_IPUCU.get(dominan, "Seasonal and natural eating balances your digestive system.")],
                    "ask": ["Deep and honest communication with your partner; openly share your emotional needs."],
                    "kariyer": ["Writing down your career goals and reviewing them regularly increases your chances of success."],
                    "aile": ["Spending regular time with family members and sharing past stories strengthens bonds."],
                    "maddi": ["Budget planning and a habit of regular saving bring you financial freedom."],
                    "sosyal": ["Practice active listening and empathy for deep, meaningful relationships."],
                    "egitim": ["You can turn a new subject into a habit by studying it regularly for 21 days."],
                    "manevi": ["Even 10 minutes of silent meditation daily creates big differences in the long run."],
                    "seyahat": ["Plan your travels in advance but stay flexible; the best moments often come unplanned."],
                }
            elif _ES:
                kat_oneriler = {
                    "spor": [ELEMENT_SPOR_IPUCU.get(dominan, "Son ideales el ejercicio regular y los deportes acordes con tu elemento.")],
                    "sanat": [ELEMENT_SANAT_IPUCU.get(dominan, "Prueba distintas disciplinas para descubrir tu expresión artística.")],
                    "hobi": ["Intenta volver a las actividades que disfrutabas en la infancia; la curiosidad siempre es una buena guía."],
                    "saglik": ["No descuides un chequeo de salud integral una vez al año; el sueño regular y la alimentación natural son tu prioridad."],
                    "beslenme": [ELEMENT_BESLENME_IPUCU.get(dominan, "La alimentación de temporada y natural equilibra tu sistema digestivo.")],
                    "ask": ["Comunicación profunda y honesta con tu pareja; comparte abiertamente tus necesidades emocionales."],
                    "kariyer": ["Escribir tus metas profesionales y revisarlas con regularidad aumenta tus probabilidades de éxito."],
                    "aile": ["Pasar tiempo regular con los miembros de tu familia y compartir historias del pasado fortalece los vínculos."],
                    "maddi": ["La planificación presupuestaria y el hábito del ahorro regular te aportan libertad financiera."],
                    "sosyal": ["Practica la escucha activa y la empatía para relaciones profundas y significativas."],
                    "egitim": ["Puedes convertir un tema nuevo en hábito estudiándolo 21 días de forma regular."],
                    "manevi": ["Incluso 10 minutos diarios de meditación en silencio generan grandes diferencias a largo plazo."],
                    "seyahat": ["Planifica tus viajes con antelación pero mantente flexible; los mejores momentos suelen llegar sin planearlos."],
                }
            else:
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
        _ES = _i18n_get_lang() == "es"
        BURCLAR = ["Koç","Boğa","İkizler","Yengeç","Aslan","Başak","Terazi","Akrep","Yay","Oğlak","Kova","Balık"]
        EN_EV = {1:"1st",2:"2nd",3:"3rd",4:"4th",5:"5th",6:"6th",7:"7th",8:"8th",9:"9th",10:"10th",11:"11th",12:"12th"}
        ES_EV = {1:"1ª",2:"2ª",3:"3ª",4:"4ª",5:"5ª",6:"6ª",7:"7ª",8:"8ª",9:"9ª",10:"10ª",11:"11ª",12:"12ª"}
        BURCLAR_ES = ["Aries","Tauro","Géminis","Cáncer","Leo","Virgo","Libra","Escorpio","Sagitario","Capricornio","Acuario","Piscis"]

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
        EV_ANLAM_ES = {
            1:"personalidad y apariencia exterior", 2:"valores y seguridad material", 3:"comunicación y entorno cercano",
            4:"raíces y familia", 5:"creatividad y amor", 6:"salud y rutina diaria",
            7:"relaciones y alianzas", 8:"transformación y recursos compartidos", 9:"creencias y educación superior",
            10:"carrera y estatus social", 11:"círculo social e ideales", 12:"el subconsciente y el viaje espiritual"
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
        element_acik_es = {
            "Ateş": "El elemento Fuego prevalece — eres un pionero natural y una fuente de inspiración. Das pasos valientes en la vida y proyectas tu pasión interior hacia el exterior.",
            "Toprak": "El elemento Tierra prevalece — tienes una naturaleza sólida, confiable y productiva, construida sobre cimientos firmes. Conviertes tus sueños en realidad mediante pasos concretos.",
            "Hava": "El elemento Aire prevalece — tu mente está en constante actividad, generando ideas y tejiendo conexiones. La comunicación y tu círculo social ocupan el centro de tu vida.",
            "Su": "El elemento Agua prevalece — posees una profunda inteligencia intuitiva y una gran empatía. Tu mundo emocional moldea tus decisiones y tus relaciones.",
        }
        eksik_element = [e for e, s in eleman_say.items() if s == 0]
        eksik_not = ""
        if eksik_element:
            if _ES:
                _eks = {"Ateş":"Fuego","Toprak":"Tierra","Hava":"Aire","Su":"Agua"}
                eksik_not = f" Asimismo, tu carta no contiene planetas en el elemento { ' y '.join(_eks.get(e, e) for e in eksik_element) }; quizá te aguarde un camino de crecimiento consciente para equilibrar estas áreas."
            elif _EN:
                _eks = {"Ateş":"Fire","Toprak":"Earth","Hava":"Air","Su":"Water"}
                eksik_not = f" Meanwhile, your chart holds no planets in the { ' and '.join(_eks.get(e, e) for e in eksik_element) } element; a conscious journey of growth may await you to bring these areas into balance."
            else:
                eksik_not = f" Öte yandan haritanızda { ' ve '.join(eksik_element) } elementinde gezegen bulunmuyor; bu alanları dengelemek için bilinçli bir gelişim yolculuğu sizi bekliyor olabilir."

        if _EN:
            par1 = f"With your Ascendant in {pdf_label(asc_burc)} and your MC in {pdf_label(mc_burc)}, your approach to life and your social goals take shape. {element_acik_en.get(bask_element, 'Your elemental distribution is balanced and harmonious.')}{eksik_not}"
        elif _ES:
            par1 = f"Con tu Ascendente en {pdf_label(asc_burc)} y tu MC en {pdf_label(mc_burc)}, tu manera de llegar a la vida y tus metas sociales van tomando forma. {element_acik_es.get(bask_element, 'Tu distribución elemental es equilibrada y armoniosa.')}{eksik_not}"
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
            g_ad = pdf_label(g)
            burc_ad = pdf_label(burc)
            e_anlam = EV_ANLAM.get(ev, "hayat")
            e_anlam_en = EV_ANLAM_EN.get(ev, "life")
            e_anlam_es = EV_ANLAM_ES.get(ev, "vida")
            DUSUK_ZARAR = {
                "Güneş": ("Terazi","Kova"), "Ay": ("Akrep","Oğlak"), "Merkür": ("Balık","Yay"),
                "Venüs": ("Başak","Akrep"), "Mars": ("Boğa","Terazi"), "Jüpiter": ("Oğlak","Başak"),
                "Satürn": ("Yengeç","Koç"), "Uranüs": ("Boğa","Aslan"), "Neptün": ("Başak","Kova"),
                "Plüton": ("Başak","Boğa"), "Chiron": ("",""),
            }
            dusuk, zarar = DUSUK_ZARAR.get(g, ("",""))
            notu = ""
            if burc == zarar:
                notu = (" Here its energy is challenged — an area that requires conscious effort." if _EN else (" Aquí su energía se ve desafiada — un área que exige esfuerzo consciente." if _ES else " Burada enerjisi sınanıyor — bilinçli çaba gerektiren bir alan."))
            elif burc == dusuk:
                notu = (" Here its expression is weakened but can be restored — it can be strengthened with awareness." if _EN else (" Aquí su expresión se debilita, aunque puede recuperarse — puede fortalecerse con conciencia." if _ES else " Burada ifadesi zayıflıyor ama telafisi mümkün — farkındalıkla güçlenebilir."))

            giris = {
                "Güneş": (f"{g_ad} is in {burc_ad}, in the {EN_EV.get(ev, str(ev))} House ({e_anlam_en}). Your core self is curious and adaptable through {burc_ad}, but in this house that light turns inward: your purpose clarifies when you find quiet to listen before shining outward." if _EN else (f"{g_ad} está en {burc_ad}, en la Casa {ES_EV.get(ev, str(ev))} ({e_anlam_es}). Tu identidad es curiosa y adaptable por {burc_ad}, pero en esta casa esa luz pide interioridad: tu propósito se aclara cuando encuentras silencio para escucharte antes de brillar hacia afuera." if _ES else f"{g} {burc} burcunda, {ev}. evde ({e_anlam}) konumlanmış. {burc_ad} burcunun meraklı ve esnek enerjisi öz benliğinizi besler; {ev}. evin yaşam alanında bu ışık içe döner ve amacınız sessizlikte netleşir. Kendinize kulak verdiğinizde yaratıcılığınız akışa geçer.")),
                "Ay": (f"{g_ad} is in {burc_ad}, in the {EN_EV.get(ev, str(ev))} House ({e_anlam_en}). Your emotional world is {burc_ad.lower()} — sensitive and shifting — and in this house your instincts ask for {e_anlam_en.lower()}. Honour that need with small rituals of care and your inner security grows." if _EN else (f"{g_ad} está en {burc_ad}, en la Casa {ES_EV.get(ev, str(ev))} ({e_anlam_es}). Tu mundo emocional es {burc_ad.lower()} — sensible y cambiante — y en esta casa tus instintos piden {e_anlam_es.lower()}. Si honras esa necesidad con pequeños rituales de cuidado, tu seguridad interna se fortalece." if _ES else f"{g} {burc} burcunda, {ev}. evde ({e_anlam}) yer alıyor. {burc_ad} burcunun duygusal tonu {e_anlam} ile buluşur; içgüdüsel tepkileriniz bu alanda filizlenir. Kendinize şefkatle yaklaştığınızda duygusal güveniniz artar.")),
                "Merkür": (f"{g_ad} in {burc_ad}, {EN_EV.get(ev, str(ev))} House ({e_anlam_en}). Your mind is {burc_ad.lower()} — curious and articulate — and in this house your words seek {e_anlam_en.lower()}. Speak clearly and listen with equal care; your ideas gain power when shared." if _EN else (f"{g_ad} en {burc_ad}, Casa {ES_EV.get(ev, str(ev))} ({e_anlam_es}). Tu mente es {burc_ad.lower()} — curiosa y articulada — y en esta casa tus palabras buscan {e_anlam_es.lower()}. Habla con claridad y escucha con la misma atención; tus ideas cobran fuerza al compartirlas." if _ES else f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). {burc_ad} burcunun meraklı zihni {e_anlam} ile buluşur; iletişim tarzınız bu alanda filizlenir. Net konuşup aynı özenle dinlediğinizde düşünceleriniz güç kazanır.")),
                "Venüs": (f"{g_ad} in {burc_ad}, {EN_EV.get(ev, str(ev))} House ({e_anlam_en}). Your love language is {burc_ad.lower()} — warm and value-driven — and in this house your heart seeks {e_anlam_en.lower()}. Offer affection in small, consistent gestures; your values become your compass." if _EN else (f"{g_ad} en {burc_ad}, Casa {ES_EV.get(ev, str(ev))} ({e_anlam_es}). Tu lenguaje del amor es {burc_ad.lower()} — cálido y orientado a valores — y en esta casa tu corazón busca {e_anlam_es.lower()}. Ofrece afecto en gestos pequeños y constantes; tus valores se vuelven tu brújula." if _ES else f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). {burc_ad} burcunun sıcak ve değer odaklı sevgisi {e_anlam} ile buluşur; sevgi diliniz bu alanda filizlenir. Küçük ve tutarlı jestlerle sevgiyi sunduğunuzda değerleriniz pusulanız olur.")),
                "Mars": (f"{g_ad} in {burc_ad}, {EN_EV.get(ev, str(ev))} House ({e_anlam_en}). Your will is {burc_ad.lower()} — direct and courageous — and in this house your drive seeks {e_anlam_en.lower()}. Channel that fire into one clear action at a time; your courage grows when you act with purpose." if _EN else (f"{g_ad} en {burc_ad}, Casa {ES_EV.get(ev, str(ev))} ({e_anlam_es}). Tu voluntad es {burc_ad.lower()} — directa y valiente — y en esta casa tu impulso busca {e_anlam_es.lower()}. Canaliza ese fuego en una acción clara a la vez; tu valentía crece cuando actúas con propósito." if _ES else f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). {burc_ad} burcunun cesur ve doğrudan iradesi {e_anlam} ile buluşur; mücadele enerjiniz bu alanda filizlenir. Enerjinizi tek bir net eyleme yönlendirdiğinizde cesaretiniz artar.")),
                "Jüpiter": (f"{g_ad} in {burc_ad}, {EN_EV.get(ev, str(ev))} House ({e_anlam_en}). Your luck is {burc_ad.lower()} — expansive and optimistic — and in this house abundance seeks {e_anlam_en.lower()}. Share what you learn; generosity returns as opportunity." if _EN else (f"{g_ad} en {burc_ad}, Casa {ES_EV.get(ev, str(ev))} ({e_anlam_es}). Tu suerte es {burc_ad.lower()} — expansiva y optimista — y en esta casa la abundancia busca {e_anlam_es.lower()}. Comparte lo que aprendes; la generosidad vuelve como oportunidad." if _ES else f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). {burc_ad} burcunun iyimser ve genişleyen şansı {e_anlam} ile buluşur; bolluk bu alanda filizlenir. Öğrendiklerinizi paylaştığınızda cömertlik fırsata dönüşür.")),
                "Satürn": (f"{g_ad} in {burc_ad}, {EN_EV.get(ev, str(ev))} House ({e_anlam_en}). Your discipline is {burc_ad.lower()} — steady and structured — and in this house lessons ask for {e_anlam_en.lower()}. Build one small boundary at a time; consistency becomes your strength." if _EN else (f"{g_ad} en {burc_ad}, Casa {ES_EV.get(ev, str(ev))} ({e_anlam_es}). Tu disciplina es {burc_ad.lower()} — constante y estructurada — y en esta casa las lecciones piden {e_anlam_es.lower()}. Construye un pequeño límite a la vez; la constancia se vuelve tu fortaleza." if _ES else f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). {burc_ad} burcunun istikrarlı disiplini {e_anlam} ile buluşur; sorumluluklarınız bu alanda filizlenir. Her seferinde küçük bir sınır inşa ettiğinizde tutarlılık gücünüz olur.")),
                "Uranüs": (f"{g_ad} in {burc_ad}, {EN_EV.get(ev, str(ev))} House ({e_anlam_en}). Your originality is {burc_ad.lower()} — inventive and independent — and in this house change seeks {e_anlam_en.lower()}. Try one small experiment; your freedom grows when you test new paths." if _EN else (f"{g_ad} en {burc_ad}, Casa {ES_EV.get(ev, str(ev))} ({e_anlam_es}). Tu originalidad es {burc_ad.lower()} — inventiva e independiente — y en esta casa el cambio busca {e_anlam_es.lower()}. Prueba un pequeño experimento; tu libertad crece al explorar caminos nuevos." if _ES else f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). {burc_ad} burcunun özgün ve bağımsız yeniliği {e_anlam} ile buluşur; değişim bu alanda filizlenir. Küçük bir deney yaptığınızda özgürlüğünüz artar.")),
                "Neptün": (f"{g_ad} in {burc_ad}, {EN_EV.get(ev, str(ev))} House ({e_anlam_en}). Your dreams are {burc_ad.lower()} — intuitive and boundless — and in this house inspiration seeks {e_anlam_en.lower()}. Keep a small dream note; your intuition speaks in quiet images." if _EN else (f"{g_ad} en {burc_ad}, Casa {ES_EV.get(ev, str(ev))} ({e_anlam_es}). Tus sueños son {burc_ad.lower()} — intuitivos y sin límites — y en esta casa la inspiración busca {e_anlam_es.lower()}. Guarda una pequeña nota de sueños; tu intuición habla en imágenes silenciosas." if _ES else f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). {burc_ad} burcunun sezgisel ve sınırsız hayalleri {e_anlam} ile buluşur; sezgileriniz bu alanda filizlenir. Küçük bir rüya notu tuttuğunuzda sezgileriniz sessiz imgelerle konuşur.")),
                "Plüton": (f"{g_ad} in {burc_ad}, {EN_EV.get(ev, str(ev))} House ({e_anlam_en}). Your transformation is {burc_ad.lower()} — deep and irreversible — and in this house power asks for {e_anlam_en.lower()}. Name one pattern to release; your rebirth begins with honest choice." if _EN else (f"{g_ad} en {burc_ad}, Casa {ES_EV.get(ev, str(ev))} ({e_anlam_es}). Tu transformación es {burc_ad.lower()} — profunda e irreversible — y en esta casa el poder pide {e_anlam_es.lower()}. Nombra un patrón que soltar; tu renacimiento comienza con una elección honesta." if _ES else f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). {burc_ad} burcunun derin ve geri dönüşsüz dönüşümü {e_anlam} ile buluşur; güç bu alanda filizlenir. Bırakacağınız bir kalıbı adlandırdığınızda yeniden doğuşunuz dürüst bir seçimle başlar.")),
                "Chiron": (f"{g_ad} in {burc_ad}, {EN_EV.get(ev, str(ev))} House ({e_anlam_en}). Your wound is {burc_ad.lower()} — tender and instructive — and in this house healing asks for {e_anlam_en.lower()}. Speak kindly to that tender part; your healing becomes a gift to others." if _EN else (f"{g_ad} en {burc_ad}, Casa {ES_EV.get(ev, str(ev))} ({e_anlam_es}). Tu herida es {burc_ad.lower()} — tierna e instructiva — y en esta casa la sanación pide {e_anlam_es.lower()}. Háblale con amabilidad a esa parte tierna; tu sanación se vuelve un regalo para otros." if _ES else f"{g} {burc} burcunda, {ev}. evde ({e_anlam}). {burc_ad} burcunun hassas ve öğretici yarası {e_anlam} ile buluşur; iyileşme bu alanda filizlenir. O hassas parçaya şefkatle konuştuğunuzda iyileşmeniz başkalarına hediye olur.")),
            }.get(g, "")
            giris_en = {
                "Güneş": f"{g_ad} is placed in {burc_ad}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your core self and your life's fundamental purpose take shape at this intersection.",
                "Ay": f"{g_ad} sits in {burc_ad}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your emotional world and instinctive reactions are nourished by this placement.",
                "Merkür": f"{g_ad} in {burc_ad}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your mental structure and communication style draw strength from this placement.",
                "Venüs": f"{g_ad} in {burc_ad}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your love language, aesthetic sense and what you value bear the imprint of this position.",
                "Mars": f"{g_ad} in {burc_ad}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your will, passions and fighting energy are governed from here.",
                "Jüpiter": f"{g_ad} in {burc_ad}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your domain of luck, abundance and personal expansion reveals itself in this position.",
                "Satürn": f"{g_ad} in {burc_ad}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your responsibilities, limits and most important life lessons lie hidden in this placement.",
                "Uranüs": f"{g_ad} in {burc_ad}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your originality, sudden changes and the areas you rebel against are linked to this position.",
                "Neptün": f"{g_ad} in {burc_ad}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your dreams, intuitions and spiritual connections draw inspiration from here.",
                "Plüton": f"{g_ad} in {burc_ad}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Deep transformation, power dynamics and your potential for rebirth are stored in this position.",
                "Chiron": f"{g_ad} in {burc_ad}, in the {EN_EV.get(ev, str(ev))} house ({e_anlam_en}). Your deepest wound and, at the same time, your greatest healing power reside here.",
            }.get(g, "")
            if giris:
                tam_metin = f"{giris}{notu}"
                if _EN:
                    tam_metin = f"{giris_en}{notu}"
                gez_parcalar.append(tam_metin)
                gez_bolumler.append({"gezegen": g, "baslik": (f"{g_ad} — {burc_ad}, {EN_EV.get(ev, str(ev))} House" if _EN else (f"{g_ad} — {burc_ad}, Casa {ES_EV.get(ev, str(ev))}" if _ES else f"{g} — {burc}, {ev}. Ev")), "metin": tam_metin})

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
                    yorum = f"{pdf_label(aci)} aspect between {pdf_label(a['g1'])} and {pdf_label(a['g2'])} brings you {etiket.get(aci, 'some tension')}."
                elif _ES:
                    etiket = {"Kavuşum":"una unión y fortalecimiento","Trigon":"flujo natural y armonía","Sekstil":"oportunidad y apoyo","Kare":"un desafío","Karşıt":"una llamada al equilibrio"}
                    yorum = f"El aspecto de {pdf_label(aci)} entre {pdf_label(a['g1'])} y {pdf_label(a['g2'])} te trae {etiket.get(aci, 'alguna tensión')}."
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
                    diger_not += f"Your Part of Spirit is in {pdf_label(mp['ruh_burc'])} (the {EN_EV.get(mp['ruh_ev'], str(mp['ruh_ev']))} house) — it serves as a compass on your career and life-purpose journey. "
                elif _ES:
                    diger_not += f"Tu Parte del Espíritu está en {pdf_label(mp['ruh_burc'])} (la casa {ES_EV.get(mp['ruh_ev'], str(mp['ruh_ev']))}) — te sirve de brújula en tu camino de carrera y propósito vital. "
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
                                eklenen.append(f"{pdf_label(nokta_ad)} in {pdf_label(nokta_data['burc'])} (the {EN_EV.get(nokta_data.get('ev'), str(nokta_data.get('ev','?')))} house)")
                            elif _ES:
                                eklenen.append(f"{pdf_label(nokta_ad)} en {pdf_label(nokta_data['burc'])} (la casa {ES_EV.get(nokta_data.get('ev'), str(nokta_data.get('ev','?')))})")
                            else:
                                eklenen.append(f"{nokta_ad} {nokta_data['burc']} burcunda ({nokta_data.get('ev','?')}. ev)")
                    if eklenen:
                        diger_not += (f"Among the Arabic parts, {', '.join(eklenen)} stand out. " if _EN else (f"Entre las partes arábigas, destacan {', '.join(eklenen)}. " if _ES else f"Arap noktalarından {', '.join(eklenen)} öne çıkıyor. "))
        except: pass
        try:
            ast_anahtar = {"Juno":"commitment","Ceres":"nurturing","Pallas":"wisdom","Vesta":"devotion","Eros":"passion","Psyche":"spiritual bond"} if _EN else ({"Juno":"compromiso","Ceres":"nutrición","Pallas":"sabiduría","Vesta":"devoción","Eros":"pasión","Psyche":"vínculo espiritual"} if _ES else {"Juno":"bağlılık","Ceres":"beslenme","Pallas":"bilgelik","Vesta":"adanma","Eros":"tutku","Psyche":"ruhsal bağ"})
            ast_list = []
            for ast_isim, ast_tema in ast_anahtar.items():
                ast_id = GEZEGENLER.get(ast_isim)
                if ast_id:
                    deg = swe.calc_ut(jd, ast_id)[0][0]
                    ast_burc = BURCLAR[int(deg // 30)]
                    ast_list.append(f"{ast_isim} ({pdf_label(ast_burc)} — {ast_tema})")
            if ast_list:
                diger_not += (f"Among the asteroids, {', '.join(ast_list[:4])} carry prominent themes in your chart." if _EN else (f"Entre los asteroides, {', '.join(ast_list[:4])} portan temas destacados en tu carta." if _ES else f"Asteroitlerden {', '.join(ast_list[:4])} haritanızda belirgin temalar taşıyor."))
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
    _ES = _i18n_get_lang() == "es"
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

    SIFA_DICT_ES = {
        ("Güneş","Satürn"): "Te sientes atrapado entre tu autoconfianza y tus responsabilidades. Detecta la voz interior que te dice que 'no eres suficiente' y desafíala. Celebrar tus pequeños logros aliviará esta tensión.",
        ("Güneş","Plüton"): "Las luchas de poder y las dinámicas de control están en tu agenda. En lugar de intentar cambiar a los demás, enfréntate a tus propias sombras. Cuando descubras tu propio poder, las disputas externas perderán su sentido.",
        ("Güneş","Neptün"): "Una niebla se disipa en torno a tu identidad. Deja de moldear tu vida según las expectativas ajenas. La meditación y el tiempo a solas te recordarán tu verdadero ser.",
        ("Güneş","Uranüs"): "Tu necesidad de libertad choca con tus responsabilidades. En lugar de rebelarte por rebelarte, cuestiona qué patrones realmente te quedan estrechos. Encontrar tu propio camino no exige rechazar a los demás.",
        ("Güneş","Merkür"): "Hay una desarmonía entre tus pensamientos y tu yo esencial. Lo que dices y lo que sientes puede no coincidir. Sé honesto contigo mismo y no compartas ideas que no hayas hecho plenamente tuyas.",
        ("Güneş","Venüs"): "Tu manera de expresarte y tu lenguaje del amor pueden contradecirse. Para complacer a los demás, dejas de lado tus propios deseos. Primero, reconoce tus propias necesidades.",
        ("Güneş","Mars"): "Estás atrapado entre la voluntad y el deseo. Puede que quieras algo con intensidad y, sin embargo, temas actuar. Da el primer paso; el resto vendrá solo.",
        ("Güneş","Jüpiter"): "Tu necesidad de demostrar tu valía puede llevarte al extremo. En lugar de intentar probar algo a todos, permítete simplemente existir. Ya eres suficiente; no hace falta nada más.",
        ("Güneş","KAD"): "Los patrones familiares del pasado y los hábitos heredados de tus ancestros dificultan que construyas tu propia identidad. Para trazar tu camino, aprende a liberarte de los lazos familiares sin rechazarlos. Hacer las paces con tus raíces te fortalecerá.",
        ("Güneş","Lilith"): "Te cuesta aceptar tu ira y tus lados reprimidos. Reivindicar las partes de ti que la sociedad considera 'inapropiadas' te liberará. Enfrentar tu sombra es el único camino para encontrar tu luz.",
        ("Ay","Satürn"): "Emocionalmente te sientes limitado. Puede que tu niño interior haya sido silenciado. Permítete: llorar, abrazar, beber algo caliente. Baja tus muros protectores, poco a poco.",
        ("Ay","Plüton"): "Tus emociones son profundas como un océano y a veces asfixiantes. Observa tus tendencias posesivas y celosas. Recuérdate que puedes sentirte seguro sin depender de alguien.",
        ("Ay","Neptün"): "Absorbes la energía ajena como una esponja y no distingues dónde terminas tú y dónde comienzan los demás. Diez minutos de silencio cada día te ayudarán a trazar límites emocionales.",
        ("Ay","Uranüs"): "Tus vaivenes emocionales pueden ser impredecibles: feliz un instante, inquieto al siguiente. Esta volatilidad es la fuente de tu creatividad, pero también puede generar inestabilidad. Las rutinas diarias serán tu ancla.",
        ("Ay","Mars"): "Tus reacciones son repentinas e intensas. Tu ira y tu sensibilidad están entrelazadas. Cuando algo te moleste, respira hondo antes de responder. Mover tu cuerpo transformará esta energía.",
        ("Ay","Venüs"): "Hay una contradicción entre tus necesidades emocionales y lo que te complace. Puede que te esfuerces por ser amado y aprobado. Muéstrate amor incondicional en primer lugar.",
        ("Ay","Merkür"): "Te cuesta poner en palabras tus sentimientos. Algo se agita en tu interior, pero no puedes expresarlo. Llevar un diario y la escritura creativa te ayudarán a romper ese bloqueo.",
        ("Ay","Jüpiter"): "Tus emociones tienden a exagerarse. Puedes magnificar un pequeño acontecimiento o arrastrar la tristeza de un instante durante días. Consulta a alguien de confianza para ganar perspectiva realista.",
        ("Ay","KAD"): "Llevas el peso emocional de tu historia familiar. Tu madre o tus mayores te legaron hábitos emocionales. Es hora de detectar esos patrones y tomar decisiones conscientes. No dejes que el pasado te defina.",
        ("Ay","Lilith"): "Hay tensión entre tu feminidad, tu sensibilidad y los lados tuyos que no se aceptan. Tus respuestas emocionales reprimidas pueden aflorar en los momentos más inesperados. Crea espacios seguros donde expresarte sin miedo al juicio.",
        ("Merkür","Neptün"): "Tu mente habita en una nube de niebla. Distinguir el sueño de la realidad se vuelve difícil. Plasmar tus pensamientos en el papel —escribir y dibujar— te dará claridad. Confía en tu intuición, pero no sueltes la comprobación de la realidad.",
        ("Merkür","Plüton"): "Tu mente es profunda e investigadora, pero también puede caer en bucles de pensamiento obsesivos. Te cuesta soltar un tema y repites la misma idea. Prueba la meditación y la actividad física para vaciar la mente.",
        ("Merkür","Uranüs"): "Tus ideas son poco convencionales y pioneras, pero puedes dejar atrás a los demás al expresarlas. Tus arrebatos repentinos y comentarios inesperados pueden tensar las relaciones. Haz una pausa de un segundo antes de compartir tus pensamientos.",
        ("Merkür","Satürn"): "Tu mente es crítica y disciplinada, pero puede volverse excesivamente pesimista. Cuestionas incluso tus propios pensamientos y te cuesta decidir. Compartir una idea imperfecta es mejor que quedarse inmóvil.",
        ("Merkür","Mars"): "Tus pensamientos pueden ser rápidos y agresivos. En una discusión, las palabras pueden volverse armas. Defender tu punto de vista no significa rebajar a otra persona. Puedes comunicarte sin pelear.",
        ("Merkür","KAD"): "Viejos patrones mentales —sistemas de creencias heredados de tu familia— moldean tu mente. Es hora de preguntarte qué creencias no son realmente tuyas. Declara tu libertad mental.",
        ("Merkür","Lilith"): "Las palabras no dichas, las ideas reprimidas y los temas tabú ocupan tu mente. Encuentra el valor de decir lo que no se dice. Apropia de los pensamientos que creías prohibidos.",
        ("Venüs","Satürn"): "Te sientes distante e inseguro en las relaciones. El miedo a 'no ser amado lo suficiente' te detiene. Empieza a expresar tu amor con pequeños gestos e intenta aprender el lenguaje del otro.",
        ("Venüs","Plüton"): "Tus relaciones son intensas y apasionadas, pero pueden arrastrar posesividad y control. El miedo a perder a alguien te hace aferrarte con demasiada fuerza. Aprender a confiar es tu mayor lección.",
        ("Venüs","Neptün"): "Tus límites en el amor son difusos. Los sueños románticos pueden imponerse a la realidad. En lugar de ver a alguien tal como es, lo idealizas. Abre los ojos: el amor verdadero también incluye la decepción.",
        ("Venüs","Uranüs"): "Oscilas entre la libertad y el apego. Cuanto más te acercas a alguien, más sientes la necesidad de alejarte. Acepta que necesitas espacio en tus relaciones — y aprende a decirlo.",
        ("Venüs","Mars"): "Buscas un equilibrio entre el amor y la pasión. Uno llama a tu corazón, el otro a tu cuerpo. Una salida creativa —la danza, la pintura, la música— puede armonizar estas dos energías.",
        ("Venüs","KAD"): "Los hábitos de amor de tus raíces familiares afectan tus relaciones adultas. El lenguaje del amor que aprendiste en la infancia puede que ya no satisfaga tus necesidades. Nunca es tarde para aprender uno nuevo.",
        ("Venüs","Lilith"): "Vives un conflicto interno en torno a la sexualidad, la atracción y el deseo prohibido. Puede que te sientas atrapado entre los guiones sociales sobre la mujer y el sexo y tu propia verdad. Reivindicar tu cuerpo y tus deseos te liberará.",
        ("Mars","Satürn"): "Te cuesta expresar la ira, o sufres arrebatos descontrolados — dos caras del mismo problema: un ciclo de represión y explosión. El ejercicio físico regular canaliza esta energía de forma sana.",
        ("Mars","Plüton"): "Tu ira es volcánica: silenciosa durante mucho tiempo, y luego una erupción destructiva. Te ves arrastrado a luchas de poder y puedes tratar todo como un campo de batalla. Recuerda que el verdadero poder no está en controlar, sino en soltar.",
        ("Mars","Neptün"): "Tu energía está dispersa; te cuesta encontrar motivación. Sientes que no sabes hacia dónde vas. Fija metas pequeñas y claras. Avanzar paso a paso es más eficaz que intentar lograrlo todo de una vez.",
        ("Mars","Uranüs"): "Los arrebatos de ira repentinos y las acciones impulsivas son el rasgo más destacado de este aspecto. Actuar sin pensar puede traer arrepentimiento. Reconoce tus detonantes y cuenta hasta tres antes de reaccionar.",
        ("Mars","Jüpiter"): "El optimismo excesivo y los movimientos exagerados pueden llevarte a asumir riesgos. Lo quieres todo a la vez y luego te agotas. Reduce la velocidad, concéntrate en una sola meta y no la sueltes hasta alcanzarla.",
        ("Mars","KAD"): "Las raíces de tu ira pueden estar en tu historia familiar. Existe un patrón de ira heredado de tu padre o tus mayores. No tienes que repetir las batallas de tus ancestros en tu propia vida. Reconocer este ciclo ya es sanador.",
        ("Mars","Lilith"): "La ira reprimida y los deseos prohibidos se acumulan en tu cuerpo. Encontrar formas sanas de expresar la ira importa tanto para tu salud física como emocional. Las artes marciales, el ejercicio intenso y la terapia de voz pueden ayudar.",
        ("Jüpiter","Satürn"): "Oscilas entre la expansión y la restricción. Construyes grandes sueños y luego te detienes. No esperes el momento perfecto; empieza con lo que tienes. Los sueños que se alzan sobre cimientos sólidos se cumplen.",
        ("Jüpiter","Plüton"): "El poder, la abundancia y el control están entrelazados. El deseo de tener más puede consumirte. La abundancia verdadera viene de apreciar lo que tienes. Recuerda que lo que compartes se multiplica.",
        ("Jüpiter","Neptün"): "El optimismo sin límites puede alejarte de ser realista. Crees tan firmemente que todo irá bien que pasas por alto las señales de peligro. Equilibrio: busca un punto medio entre soñar y ser realista.",
        ("Jüpiter","Uranüs"): "Tu deseo de libertad y aventura es tan fuerte que puedes ignorar por completo la estabilidad. Las decisiones repentinas y los movimientos sin plan pueden traer arrepentimiento. Libertad no es irresponsabilidad; no las confundas.",
        ("Jüpiter","KAD"): "Puede que te sientas atrapado entre los sistemas de creencias heredados de tu familia y tus propios sueños. Cuestiona los patrones de 'así se hacen las cosas'. Los límites de tus ancestros no son tus límites.",
        ("Jüpiter","Lilith"): "El conocimiento prohibido, los temas tabú y las verdades reprimidas te atraen. Te sientes atraído por lo que la sociedad considera 'excesivo' o 'inapropiado'. Canaliza esa curiosidad hacia campos creativos y constructivos.",
        ("Satürn","Uranüs"): "Estás atrapado entre la tradición y la revolución. Por un lado quieres seguridad y por el otro libertad. Antes de un cambio radical, prueba pequeñas innovaciones. Transforma los viejos patrones en lugar de derribarlos de golpe.",
        ("Satürn","Neptün"): "Hay un conflicto entre tus responsabilidades y tus sueños. Cuanto más te acercas a uno, más se aleja el otro. Encuentra un modo de perseguir tus sueños sin descuidar tus deberes.",
        ("Satürn","Plüton"): "Enfrentas las lecciones más pesadas de la vida: pérdida, control, poder. Este aspecto te enseña resistencia, pero también puede endurecerte. Ablandarse no es debilidad; es señal de madurez.",
        ("Satürn","KAD"): "Cargas la responsabilidad de tu historia familiar. Los asuntos no resueltos de tus ancestros pueden pesar sobre tus hombros. Soltar esta carga puede sentirse como una traición, pero la verdadera traición es no vivir tu propia vida.",
        ("Satürn","Lilith"): "Las emociones reprimidas y los lados tuyos considerados prohibidos quedan atrapados tras tus muros de responsabilidad. Como no puedes mostrarte por completo, te sientes constreñido por dentro. Abrazar tu sombra te liberará.",
        ("Chiron","Satürn"): "Tu herida más profunda está ligada a la responsabilidad y a la sensación de insuficiencia. La creencia de 'nunca soy suficiente' bloquea tu sanación. Acepta que tus imperfecciones son lo que te hace humano. No tienes que ser perfecto.",
        ("Chiron","Plüton"): "Estás sobre un puente entre el trauma pasado y la transformación. El lugar que más duele guarda tu mayor potencial de sanación. No tienes que hacerlo solo — busca apoyo profesional.",
        ("Chiron","Neptün"): "Anhelas sanar pero no sabes cómo. Buscas rutas de escape y puedes volcarte hacia dependencias. La sanación real viene de enfrentar tu dolor, no de huir de él.",
        ("Chiron","KAD"): "Puede que una herida no sanada haya sido heredada de tu historia familiar. Puede que la sientas como propia, aunque provenga de tus ancestros. Romper este ciclo está en tus manos; es parte de tu viaje de destino.",
        ("Chiron","Lilith"): "El miedo al rechazo, a la exclusión y a no ser aceptado es tu punto más sensible. Sientes que 'sobras'. Sin embargo, lo que te hace distinto es precisamente tu poder sanador. Allí donde te sientas excluido, puedes ser fuente de sanación para otros.",
        ("KAD","Lilith"): "Cuando la sombra del pasado se une a los lados reprimidos del presente, emerge un poderoso peso kármico. Hay historias silenciadas heredadas de tus ancestros. Romper ese silencio liberará tanto a ti como a tu linaje.",
        ("KAD","Plüton"): "En tu historia familiar puede haber luchas de poder, disputas hereditarias o pérdidas traumáticas. Esta energía intensa circula en tu subconsciente. Sacar a la luz los secretos familiares puede dar miedo, pero es la clave de tu liberación.",
        ("KAD","Neptün"): "En tu historia familiar puede haber una historia no resuelta de victimismo, sacrificio o decepción. Tu tendencia a sacrificarte por los demás proviene de aquí. El sacrificio no es amor. Cuídate a ti mismo primero.",
        ("KAD","Uranüs"): "Librabas una batalla entre los patrones familiares y tu independencia. Rechazas los roles tradicionales que te imponen, pero no logras desprenderte del todo. Liberarse no es rechazar; es hacer tu propia elección.",
        ("Lilith","Plüton"): "La sexualidad reprimida, los deseos prohibidos y los impulsos sombríos piden una transformación profunda. Los lados tuyos que más te avergüenzan guardan tu mayor poder. Hacer las paces con tu lado oscuro te hará completo.",
        ("Lilith","Neptün"): "Puedes estar perdido en un ciclo de víctima-redentora. Mientras intentas salvar a otros, te pierdes a ti — o esperas a un salvador. Reconoce que la salvación verdadera no está en otra persona, sino dentro de ti.",
        ("Uranüs","Lilith"): "La rebeldía y los deseos reprimidos están entrelazados. Quebrantar las reglas no te libera; solo te constriñe más. La libertad real está en fijar tus propios límites. En lugar de combatir la autoridad externa, cuestiona la autoridad interna.",
        ("Uranüs","KAD"): "Te sientes apretado entre el impulso de desprenderte de tu pasado familiar y la necesidad de pertenecer. En lugar de cortar tus lazos con las raíces, redefínelos según tus propias necesidades. Pertenecer no es rendirse.",
        ("Lilith","Mars"): "Hay un vínculo entre tu ira y tus lados reprimidos. Temes actuar en un ámbito donde crees que la autoexpresión está 'prohibida'. Mover tu cuerpo y alzar la voz romperá esas cadenas.",
        ("Venüs","Jüpiter"): "El exceso de indulgencia y las expectativas exageradas pueden crear desequilibrio en tus relaciones. Intentas llegar a todos y complacer a todos. Aprender a decir no equilibrará esta energía.",
        ("Merkür","Venüs"): "Hay una desarmonía entre lo que dices y lo que sientes. Puedes ser poco sincero al halagar o demasiado duro al criticar. Alinea lo que hay en tu corazón con lo que sale de tu boca.",
        ("Ay","Jüpiter"): "Tus reacciones emocionales son grandes y arrolladoras. Una alegría pequeña te entusiasma, mientras que una pequeña decepción puede derribarte. Prueba ejercicios de respiración y técnicas de conexión a tierra para equilibrar tus altibajos.",
        ("Mars","Jüpiter"): "Te encanta asumir riesgos, pero a veces te pasas de la raya. Tu enfoque de 'todo o nada' puede quemarte. Ver el panorama general es bueno, pero avanzar paso a paso trae resultados más duraderos.",
        ("Güneş","Ay"): "Tu identidad y tu mundo emocional chocan. Uno quiere una cosa mientras el otro quiere otra. Debes reconciliar estas dos partes para lograr tu plenitud interior. Escucha a ambas; no favorezcas a una.",
    }
    key = (g1, g2)
    rev_key = (g2, g1)
    if _EN:
        sifa_dict = SIFA_DICT_EN
    elif _ES:
        sifa_dict = SIFA_DICT_ES
    else:
        sifa_dict = SIFA_DICT
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
    g1n = pdf_label(g1); g2n = pdf_label(g2)
    generic_kare_en = [
        f"The square between {g1n} and {g2n} creates tension between the two. Instead of suppressing this energy, listen to what each is telling you. One does not have to destroy the other.",
        f"This demanding aspect between {g1n} and {g2n} asks you to question a habit. Where the two conflict actually lies your growth opportunity. Look closely at what disturbs you.",
        f"This square is a test for harmonizing the energies of {g1n} and {g2n}. You do not have to choose one; you can embrace both. What matters is finding the balance between them.",
        f"The tension between {g1n} and {g2n} says something inside you must change. Listen to this discomfort. It may be time to release old habits.",
        f"The square between {g1n} and {g2n} pushes you beyond your comfort zone. This is a demanding yet deeply instructive cycle. Try channeling this tension into a creative project.",
    ]
    generic_karsit_en = [
        f"The opposition between {g1n} and {g2n} makes you swing between two separate poles. To find a point of balance, learn to stand at equal distance from both sides.",
        f"This opposition between {g1n} and {g2n} points to a mechanism of projection. What you see in front of you may be a part of yourself you do not accept.",
        f"This opposing aspect can make you feel forced to choose a side in the realms of {g1n} and {g2n}. Yet the real matter is finding a way to keep both areas in your life.",
        f"There is an attraction-repulsion dynamic between {g1n} and {g2n}. The closer you get, the further you drift; the further you drift, the more you long. To break this cycle, find a middle path that embraces both energies.",
        f"The opposition between {g1n} and {g2n} symbolizes your search for balance in a relationship or situation. Instead of black-and-white thinking, explore the gray areas. The real solution lies beyond both.",
    ]
    generic_kare_es = [
        f"La cuadratura entre {g1n} y {g2n} genera tensión entre ambos. En lugar de reprimir esta energía, escucha lo que cada uno te dice. Ninguno tiene que destruir al otro.",
        f"Este aspecto exigente entre {g1n} y {g2n} te pide que cuestiones un hábito. En el punto donde ambos chocan se encuentra tu oportunidad de crecimiento. Mira de cerca lo que te inquieta.",
        f"Esta cuadratura es una prueba para armonizar las energías de {g1n} y {g2n}. No tienes que elegir uno; puedes abrazar los dos. Lo importante es encontrar el equilibrio entre ellos.",
        f"La tensión entre {g1n} y {g2n} te dice que algo en tu interior debe cambiar. Presta atención a esa incomodidad. Puede que haya llegado el momento de soltar viejos hábitos.",
        f"La cuadratura entre {g1n} y {g2n} te empuja fuera de tu zona de confort. Es un ciclo exigente pero profundamente instructivo. Intenta canalizar esa tensión hacia un proyecto creativo.",
    ]
    generic_karsit_es = [
        f"La oposición entre {g1n} y {g2n} te hace oscilar entre dos polos distintos. Para hallar un punto de equilibrio, aprende a mantener la misma distancia de ambos lados.",
        f"Esta oposición entre {g1n} y {g2n} señala un mecanismo de proyección. Lo que ves frente a ti puede ser una parte tuya que no aceptas.",
        f"Este aspecto de oposición puede hacerte sentir obligado a elegir un bando en los ámbitos de {g1n} y {g2n}. Sin embargo, la verdadera cuestión es encontrar un modo de mantener ambas áreas en tu vida.",
        f"Hay una dinámica de atracción y rechazo entre {g1n} y {g2n}. Cuanto más te acercas, más te alejas; cuanto más te alejas, más lo extrañas. Para romper este ciclo, busca un camino intermedio que abrace ambas energías.",
        f"La oposición entre {g1n} y {g2n} simboliza tu búsqueda de equilibrio en una relación o situación. En lugar de pensar en blanco y negro, explora las zonas grises. La solución real está más allá de ambos.",
    ]
    if _ES:
        generic_kare = generic_kare_es
        generic_karsit = generic_karsit_es
    elif _EN:
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
    _ES = _i18n_get_lang() == "es"
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
        SAGALTIM_TEKNIKLERI_ES = {
            "Güneş": {"Terazi": "Aprende a valorarte a ti mismo. Observa tu necesidad de aprobación y deja que tu luz interior brille sin esperar validación externa. Saludos al sol (Surya Namaskar) y afirmaciones de autoconfianza.", "Kova": "Abdica tu singularidad, pero no te cortes completamente de la comunidad. Encuentra formas de compartir tus dones únicos con los demás. Meditación y trabajo comunitario."},
            "Ay": {"Akrep": "Dirige tu intensidad emocional a campos creativos. Escribir un diario, plasmar tus sentimientos y expresarte por el arte te harán bien. Pasas tiempo junto al agua.", "Oğlak": "Te cuesta expresar tus emociones. Reserva diez minutos al día para volverte hacia adentro y muéstrate compasión. Los tés herbales y los baños calientes son reconfortantes."},
            "Merkür": {"Balık": "Tu mente puede sentirse dispersa. La escritura diaria y los mapas mentales te ayudarán a concentrarte. Intenta trabajar en un entorno tranquilo.", "Yay": " investiga más antes de compartir tus ideas. Prestar atención a los detalles y escuchar con paciencia te hará un comunicador más eficaz."},
            "Venüs": {"Başak": "Deja de buscar el amor perfecto. Aceptar pequeñas imperfecciones y desarrollar expectativas realistas mejorará tus relaciones. Regálate una flor o crea un entorno hermoso.", "Akrep": "Detecta tus tendencias posesivas y celosas en las relaciones. Realiza ejercicios de confianza y da espacio a tu pareja. Bailar disuelve bloqueos emocionales."},
            "Mars": {"Boğa": "En lugar de reprimir tu ira, exprésala de forma sana a través de la actividad física. Ejercicios de conexión a tierra y caminatas por la naturaleza equilibrarán tu energía.", "Terazi": "Evita comportamientos pasivo-agresivos. Aprende a expresar tus necesidades de forma clara y amable. El yoga y el trabajo respiratorio te ayudan a gestionar la ira."},
            "Jüpiter": {"Oğlak": "Crea un plan disciplinado para materializar tus grandes sueños. Haz afirmaciones de abundancia y lleva un diario de gratitud.", "Başak": "No dejes que el perfeccionismo te oculte la visión general. Aprende a tolerar riesgos y celebra cada pequeño éxito."},
            "Satürn": {"Yengeç": "Tu necesidad de seguridad emocional puede chocar con tus responsabilidades. Enfrenta tu historia familiar y fortalecécete emocionalmente te dará libertad.", "Koç": "La paciencia es tu mayor lección. En lugar de exigir resultados rápidos, confía en el proceso. El caldo de huesos, suplementos de calcio y rutinas regulares te harán bien."},
            "Uranüs": {"Boğa": "En lugar de resistirte al cambio, abrígate a la innovación en pequeños pasos. Hacer pequeños cambios en tu rutina abrirá la puerta a grandes transformaciones.", "Aslan": "No temas expresar tu singularidad. Sigue la inspiración repentina en proyectos creativos. El azul eléctrico y el púrpura elevan tu vibración."},
            "Neptün": {"Başak": "Arrela tu espiritualidad en una base práctica. Añade meditación a tu rutina diaria. Cruces (ametista, lapislázuli) y incienso te ayudan a concentrarte.", "Kova": "Busca una comunidad para materializar tus sueños. Convertir tu energía idealista en proyectos prácticos te arraigará."},
            "Plüton": {"Başak": "Dejar ir tu necesidad de control será tu mayor transformación. En lugar de quedarte en los detalles, enfócate en la visión general. La respiración profunda facilita la transformación.", "Boğa": "Detecta tus impulsos posesivos y dominantes. Enfrenta tu miedo a soltar y perder. La práctica del perdón y la gratitud acelera la transformación."},
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
                            elif _ES:
                                aci_label = "Oposición" if aci_ad == "Karşıt" else "Cuadratura"
                            else:
                                aci_label = aci_ad
                            if _EN:
                                _pname_map = {"Güneş":"Sun","Ay":"Moon","Merkür":"Mercury","Venüs":"Venus","Mars":"Mars","Jüpiter":"Jupiter","Satürn":"Saturn","Uranüs":"Uranus","Neptün":"Neptune","Plüton":"Pluto","Chiron":"Chiron"}
                                for _tk, _tv in _pname_map.items():
                                    sifa = sifa.replace(_tk, _tv)
                                receteler.append(f"🔴 {_pname_map.get(g1, g1)} {aci_label} {_pname_map.get(g2, g2)}: {sifa}")
                            elif _ES:
                                _pname_map = {"Güneş":"Sol","Ay":"Luna","Merkür":"Mercurio","Venüs":"Venus","Mars":"Marte","Jüpiter":"Júpiter","Satürn":"Saturno","Uranüs":"Urano","Neptün":"Neptuno","Plüton":"Plutón","Chiron":"Chirón"}
                                for _tk, _tv in _pname_map.items():
                                    sifa = sifa.replace(_tk, _tv)
                                receteler.append(f"🔴 {_pname_map.get(g1, g1)} {aci_label} {_pname_map.get(g2, g2)}: {sifa}")
                            else:
                                receteler.append(f"🔴 {g1} {aci_label} {g2}: {sifa}")
                        break

        # Fall / detriment remedies
        if _ES:
            diki = SAGALTIM_TEKNIKLERI_ES
        elif _EN:
            diki = SAGALTIM_TEKNIKLERI_EN
        else:
            diki = SAGALTIM_TEKNIKLERI
        if _ES:
            fark_tr = "Se necesita conciencia y trabajo consciente."
        elif _EN:
            fark_tr = "Awareness and conscious work are needed."
        else:
            fark_tr = "Farkındalık ve bilinçli çalışma gerekiyor."
        BURCLAR_ES = ["Aries","Tauro","Géminis","Cáncer","Leo","Virgo","Libra","Escorpio","Sagitario","Capricornio","Acuario","Piscis"]
        for gez, burc in gez_poz.items():
            if gez in DUSUK_ZARAR:
                dusuk, zarar = DUSUK_ZARAR[gez]
                if burc["burc"] == zarar:
                    teknik = diki.get(gez, {}).get(zarar, fark_tr)
                    if _EN:
                        zarar_label = BURCLAR_EN[BURCLAR.index(zarar)]
                        receteler.append(f"🟠 {pdf_label(gez)} Detriment ({zarar_label}): {teknik}")
                    elif _ES:
                        zarar_label = BURCLAR_ES[BURCLAR.index(zarar)]
                        receteler.append(f"🟠 {pdf_label(gez)} en disminución ({zarar_label}): {teknik}")
                    else:
                        receteler.append(f"🟠 {gez} Zarar ({zarar}): {teknik}")
                elif burc["burc"] == dusuk:
                    teknik = diki.get(gez, {}).get(dusuk, fark_tr)
                    if _EN:
                        dusuk_label = BURCLAR_EN[BURCLAR.index(dusuk)]
                        receteler.append(f"🟡 {pdf_label(gez)} Fall ({dusuk_label}): {teknik}")
                    elif _ES:
                        dusuk_label = BURCLAR_ES[BURCLAR.index(dusuk)]
                        receteler.append(f"🟡 {pdf_label(gez)} Debilidad ({dusuk_label}): {teknik}")
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

# ─── Billing & Entitlement ───
try:
    from backend.billing import is_subscribed, has_free_used, mark_free_used, upsert_subscription, get_status
except Exception:
    from billing import is_subscribed, has_free_used, mark_free_used, upsert_subscription, get_status

class FreeClaim(BaseModel):
    uid: str
    device_token: Optional[str] = None

class BillingWebhook(BaseModel):
    uid: str
    product_id: str
    expiry: Optional[float] = None
    status: Optional[str] = "active"

@app_fast.get("/api/billing/status")
def billing_status(uid: str = "", device_token: str = ""):
    return get_status(uid) | {"device_has_free": has_free_used("", device_token) if device_token else False}

@app_fast.post("/api/billing/claim-free")
def claim_free(body: FreeClaim):
    if has_free_used(body.uid, body.device_token or ""):
        raise HTTPException(status_code=402, detail={"code": "FREE_ALREADY_USED", "msg": "Free PDF already claimed"})
    mark_free_used(body.uid, body.device_token or "")
    return {"ok": True, "msg": "Free PDF claimed"}

@app_fast.post("/api/billing/webhook")
def billing_webhook(body: BillingWebhook, request: Request):
    # RevenueCat webhook doğrulaması (opsiyonel)
    rc_sig = request.headers.get("X-RevenueCat-Signature") or request.headers.get("Authorization")
    rc_secret = os.getenv("REVENUECAT_WEBHOOK_SECRET", "")
    if rc_secret and rc_sig:
        # HMAC SHA256 kontrolü (RevenueCat docs: header = HMAC)
        import hmac as _hmac
        body_raw = body.model_dump_json() if hasattr(body, "model_dump_json") else json.dumps(body.__dict__)
        expected = _hmac.new(rc_secret.encode(), body_raw.encode(), hashlib.sha256).hexdigest()
        if not _hmac.compare_digest(expected, rc_sig.replace("Bearer ", "")):
            # logla ama bloklama — test webhook'ları için esnek
            print(f"[billing] webhook sig mismatch uid={body.uid}")
    # Play Integrity iskeleti: header X-Play-Integrity-Token varsa doğrula (gerçek doğrulama Google API ile)
    play_token = request.headers.get("X-Play-Integrity-Token") or request.headers.get("x-play-integrity-token")
    if play_token and os.getenv("PLAY_INTEGRITY_ENFORCE") == "1":
        # TODO: Google PlayIntegrity API çağrısı -> device/emulator/root kontrolü
        # Şu an iskelet: token yoksa bile geçiş, enforce=1 ise logla
        print(f"[billing] play integrity token present uid={body.uid} len={len(play_token)}")
    upsert_subscription(body.uid, body.product_id, body.expiry or 0, body.status or "active")
    return {"ok": True}

@app_fast.post("/api/billing/verify-play-integrity")
def verify_play_integrity(request: Request):
    """Play Integrity token doğrulama iskeleti — APK'dan X-Play-Integrity-Token ile çağırılır."""
    token = request.headers.get("X-Play-Integrity-Token") or ""
    if not token:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "token missing"})
    # Gerçek doğrulama: https://playintegrity.googleapis.com/v1/... (service account gerekir)
    # İskelet: token varsa ok dön, logla
    print(f"[integrity] verify token len={len(token)} ip={request.client.host if request.client else ''}")
    return {"ok": True, "mock": True, "msg": "Play Integrity iskelet — Google API bağlanınca gerçek doğrulama aktif olacak"}

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
def astrokartografi_analiz(input: AstroInput, request: Request):
    """Verilen koordinat için composite chart'a göre astrokartografi skoru hesaplar. Tarayıcı interaktif harita -> sadece aboneler."""
    # Browser interactive gate: sadece abone olan kullanabilir (PDF alan PDF'te görür)
    uid = request.headers.get("X-UID") or request.headers.get("x-uid") or getattr(input, "uid", "") or ""
    # uid yoksa da deneyip preview dön — frontend blur gösterecek
    try:
        from backend.billing import is_subscribed as _is_sub
    except Exception:
        try:
            from billing import is_subscribed as _is_sub
        except Exception:
            _is_sub = lambda x: True  # fallback açık
    if uid and not _is_sub(uid):
        # limitli preview: sadece ilk skor, detay yok
        raise HTTPException(status_code=402, detail={"code": "SUB_REQUIRED", "msg": "Astrokartografi için abonelik gerekli", "locked": True})
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
        aci_simge = {"AC": "↑ Ascendant", "DC": "↓ Descendant", "MC": "⌃ MC", "IC": "⌄ IC"}
        if _i18n_get_lang() == "tr":
            aci_simge = {"AC": "↑ Yükselen", "DC": "↓ Alçalan", "MC": "⌃ MC", "IC": "⌄ IC"}
        elif _i18n_get_lang() == "es":
            aci_simge = {"AC": "↑ Ascendente", "DC": "↓ Descendente", "MC": "⌃ MC", "IC": "⌄ IC"}
        etkiler.append(f"[K] {gezegen_adi} {aci_simge.get(aci, aci)} ({fark:.1f}°) → {deger.get('parlaklik', '')}")
    if "Satürn" in comp and "Plüton" in comp:
        sp_f = aci_farki_safe(comp["Satürn"], comp["Plüton"])
        if sp_f < 10:
            kriz += 20 * (1 - sp_f / 10)
            etkiler.append(f"⚠️ [K] Satürn-Plüto kavuşumu ({sp_f:.1f}°)" if _i18n_get_lang() == "tr" else (f"⚠️ [K] Saturn-Pluto conjunction ({sp_f:.1f}°)" if _i18n_get_lang() == "en" else f"⚠️ [K] Conjunción Saturno-Plutón ({sp_f:.1f}°)"))
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
    _ULKE_EN = {"Türkiye":"Turkey","İngiltere":"United Kingdom","İrlanda":"Ireland","İsviçre":"Switzerland","Çin":"China","Kamboçya":"Cambodia","Çad":"Chad","Norveç":"Norway","Rusya":"Russia","Yunanistan":"Greece","Almanya":"Germany","Fransa":"France","İtalya":"Italy","İspanya":"Spain","Portekiz":"Portugal","Avusturya":"Austria","Hollanda":"Netherlands","Belçika":"Belgium","İsveç":"Sweden","Danimarka":"Denmark","Finlandiya":"Finland","İzlanda":"Iceland","Polonya":"Poland","Ukrayna":"Ukraine","Romanya":"Romania","Bulgaristan":"Bulgaria","Sırbistan":"Serbia","Hırvatistan":"Croatia","Arnavutluk":"Albania","Makedonya":"North Macedonia","Bosna-Hersek":"Bosnia and Herzegovina","Karadağ":"Montenegro","Kosova":"Kosovo","Gürcistan":"Georgia","Ermenistan":"Armenia","Azerbaycan":"Azerbaijan","Kazakistan":"Kazakhstan","Özbekistan":"Uzbekistan","Kırgızistan":"Kyrgyzstan","Türkmenistan":"Turkmenistan","Tacikistan":"Tajikistan","Afganistan":"Afghanistan","İran":"Iran","Irak":"Iraq","Suriye":"Syria","Lübnan":"Lebanon","İsrail":"Israel","Ürdün":"Jordan","Suudi Arabistan":"Saudi Arabia","Birleşik Arap Emirlikleri":"United Arab Emirates","Katar":"Qatar","Kuveyt":"Kuwait","Umman":"Oman","Yemen":"Yemen","Bahreyn":"Bahrain","Mısır":"Egypt","Libya":"Libya","Tunus":"Tunisia","Cezayir":"Algeria","Fas":"Morocco","ABD":"United States","ABD, Kaliforniya":"United States","Kanada":"Canada","Meksika":"Mexico","Brezilya":"Brazil","Arjantin":"Argentina","Şili":"Chile","Kolombiya":"Colombia","Peru":"Peru","Venezuela":"Venezuela","Ekvador":"Ecuador","Bolivya":"Bolivia","Paraguay":"Paraguay","Uruguay":"Uruguay","Küba":"Cuba","Japonya":"Japan","Güney Kore":"South Korea","Kuzey Kore":"North Korea","Hindistan":"India","Endonezya":"Indonesia","Malezya":"Malaysia","Singapur":"Singapore","Tayland":"Thailand","Vietnam":"Vietnam","Filipinler":"Philippines","Avustralya":"Australia","Yeni Zelanda":"New Zealand","Güney Afrika":"South Africa","Nijerya":"Nigeria","Kenya":"Kenya","Etiyopya":"Ethiopia","Tanzanya":"Tanzania","Cezayir":"Algeria","Fildişi Sahili":"Ivory Coast","Gana":"Ghana","Senegal":"Senegal","Kamerun":"Cameroon","Uganda":"Uganda","Moritanya":"Mauritania","Mali":"Mali","Nijer":"Niger","Çek Cumhuriyeti":"Czech Republic","Çekya":"Czechia","Slovakya":"Slovakia","Macaristan":"Hungary","Slovenya":"Slovenia","Estonya":"Estonia","Letonya":"Latvia","Litvanya":"Lithuania","Belarus":"Belarus","Moldova":"Moldova","Lüksemburg":"Luxembourg","Monako":"Monaco","Vatikan":"Vatican City","San Marino":"San Marino","Malta":"Malta","Kıbrıs":"Cyprus","Andorra":"Andorra","Lihtenştayn":"Liechtenstein","Grönland":"Greenland","Yeni Kaledonya":"New Caledonia","Fransız Polinezyası":"French Polynesia","Madagaskar":"Madagascar","Mozambik":"Mozambique","Zimbabve":"Zimbabwe","Zambiya":"Zambia","Angola":"Angola","Namibya":"Namibia","Botsvana":"Botswana","Svaziland":"Eswatini","Lesotho":"Lesotho","Malavi":"Malawi","Kongo Cumhuriyeti":"Republic of the Congo","Gine":"Guinea","Gine-Bissau":"Guinea-Bissau","Sierra Leone":"Sierra Leone","Liberya":"Liberia","Togo":"Togo","Benin":"Benin","Burkina Faso":"Burkina Faso","Orta Afrika Cumhuriyeti":"Central African Republic","Güney Sudan":"South Sudan","Eritre":"Eritrea","Cibuti":"Djibouti","Somali":"Somalia","Surinam":"Suriname","Guyana":"Guyana","Panama":"Panama","Kosta Rika":"Costa Rica","Nikaragua":"Nicaragua","Honduras":"Honduras","Guatemala":"Guatemala","El Salvador":"El Salvador","Belize":"Belize","Jamaika":"Jamaica","Dominik Cumhuriyeti":"Dominican Republic","Haiti":"Haiti","Porto Riko":"Puerto Rico","Trinidad ve Tobago":"Trinidad and Tobago","Bahamalar":"Bahamas","Barbados":"Barbados","Kırgızistan":"Kyrgyzstan","Moğolistan":"Mongolia","Nepal":"Nepal","Bhutan":"Bhutan","Bangladeş":"Bangladesh","Myanmar":"Myanmar","Sri Lanka":"Sri Lanka","Maldivler":"Maldives","Brunei":"Brunei","Doğu Timor":"East Timor","Papua Yeni Gine":"Papua New Guinea","Fiji":"Fiji","Samoa":"Samoa","Tonga":"Tonga","Vanuatu":"Vanuatu","Solomon Adaları":"Solomon Islands","Marshall Adaları":"Marshall Islands","Mikronezya":"Micronesia","Palau":"Palau","Kiribati":"Kiribati","Nauru":"Nauru","Tuvalu":"Tuvalu"}
    _ULKE_ES = {"Türkiye":"Turquía","İngiltere":"Reino Unido","İrlanda":"Irlanda","İsviçre":"Suiza","Çin":"China","Kamboçya":"Camboya","Çad":"Chad","Norveç":"Noruega","Rusya":"Rusia","Yunanistan":"Grecia","Almanya":"Alemania","Fransa":"Francia","İtalya":"Italia","İspanya":"España","Portekiz":"Portugal","Avusturya":"Austria","Hollanda":"Países Bajos","Belçika":"Bélgica","İsveç":"Suecia","Danimarka":"Dinamarca","Finlandiya":"Finlandia","İzlanda":"Islandia","Polonya":"Polonia","Ukrayna":"Ucrania","Romanya":"Rumania","Bulgaristan":"Bulgaria","Sırbistan":"Serbia","Hırvatistan":"Croacia","Arnavutluk":"Albania","Makedonya":"Macedonia del Norte","Bosna-Hersek":"Bosnia y Herzegovina","Karadağ":"Montenegro","Kosova":"Kosovo","Gürcistan":"Georgia","Ermenistan":"Armenia","Azerbaycan":"Azerbaiyán","Kazakistan":"Kazajistán","Özbekistan":"Uzbekistán","Kırgızistan":"Kirguistán","Türkmenistan":"Turkmenistán","Tacikistan":"Tayikistán","Afganistan":"Afganistán","İran":"Irán","Irak":"Irak","Suriye":"Siria","Lübnan":"Líbano","İsrail":"Israel","Ürdün":"Jordania","Suudi Arabistan":"Arabia Saudita","Birleşik Arap Emirlikleri":"Emiratos Árabes Unidos","Katar":"Catar","Kuveyt":"Kuwait","Umman":"Omán","Yemen":"Yemen","Bahreyn":"Baréin","Mısır":"Egipto","Libya":"Libia","Tunus":"Túnez","Cezayir":"Argelia","Fas":"Marruecos","ABD":"Estados Unidos","ABD, Kaliforniya":"Estados Unidos","Kanada":"Canadá","Meksika":"México","Brezilya":"Brasil","Arjantin":"Argentina","Şili":"Chile","Kolombiya":"Colombia","Perú":"Perú","Venezuela":"Venezuela","Ekvador":"Ecuador","Bolivya":"Bolivia","Paraguay":"Paraguay","Uruguay":"Uruguay","Küba":"Cuba","Japonya":"Japón","Güney Kore":"Corea del Sur","Kuzey Kore":"Corea del Norte","Hindistan":"India","Endonezya":"Indonesia","Malezya":"Malasia","Singapur":"Singapur","Tayland":"Tailandia","Vietnam":"Vietnam","Filipinler":"Filipinas","Avustralya":"Australia","Yeni Zelanda":"Nueva Zelanda","Güney Afrika":"Sudáfrica","Nijerya":"Nigeria","Kenya":"Kenia","Etiyopya":"Etiopía","Tanzanya":"Tanzania","Fildişi Sahili":"Costa de Marfil","Gana":"Ghana","Senegal":"Senegal","Kamerun":"Camerún","Uganda":"Uganda","Moritanya":"Mauritania","Mali":"Malí","Nijer":"Níger","Çek Cumhuriyeti":"República Checa","Çekya":"Chequia","Slovakya":"Eslovaquia","Macaristan":"Hungría","Slovenya":"Eslovenia","Estonya":"Estonia","Letonya":"Letonia","Litvanya":"Lituania","Belarus":"Bielorrusia","Moldova":"Moldavia","Lüksemburg":"Luxemburgo","Monako":"Mónaco","Vatikan":"Ciudad del Vaticano","San Marino":"San Marino","Malta":"Malta","Kıbrıs":"Chipre","Andorra":"Andorra","Lihtenştayn":"Liechtenstein","Grönland":"Groenlandia","Yeni Kaledonya":"Nueva Caledonia","Fransız Polinezyası":"Polinesia Francesa","Madagaskar":"Madagascar","Mozambik":"Mozambique","Zimbabve":"Zimbabue","Zambiya":"Zambia","Angola":"Angola","Namibya":"Namibia","Botsvana":"Botsuana","Svaziland":"Suazilandia","Lesotho":"Lesoto","Malavi":"Malaui","Kongo Cumhuriyeti":"República del Congo","Gine":"Guinea","Gine-Bissau":"Guinea-Bisáu","Sierra Leone":"Sierra Leona","Liberya":"Liberia","Togo":"Togo","Benin":"Benín","Burkina Faso":"Burkina Faso","Orta Afrika Cumhuriyeti":"República Centroafricana","Güney Sudan":"Sudán del Sur","Eritre":"Eritrea","Cibuti":"Yibuti","Somali":"Somalia","Surinam":"Surinam","Guyana":"Guyana","Panama":"Panamá","Kosta Rika":"Costa Rica","Nikaragua":"Nicaragua","Honduras":"Honduras","Guatemala":"Guatemala","El Salvador":"El Salvador","Belize":"Belice","Jamaika":"Jamaica","Dominik Cumhuriyeti":"República Dominicana","Haiti":"Haití","Porto Riko":"Puerto Rico","Trinidad ve Tobago":"Trinidad y Tobago","Bahamalar":"Bahamas","Barbados":"Barbados","Moğolistan":"Mongolia","Nepal":"Nepal","Bhutan":"Bután","Bangladeş":"Bangladés","Myanmar":"Birmania","Sri Lanka":"Sri Lanka","Maldivler":"Maldivas","Brunei":"Brunéi","Doğu Timor":"Timor Oriental","Papua Yeni Gine":"Papúa Nueva Guinea","Fiji":"Fiyi","Samoa":"Samoa","Tonga":"Tonga","Vanuatu":"Vanuatu","Solomon Adaları":"Islas Salomón","Marshall Adaları":"Islas Marshall","Mikronezya":"Micronesia","Palau":"Palaos","Kiribati":"Kiribati","Nauru":"Nauru","Tuvalu":"Tuvalu"}
    if _i18n_get_lang() == "en":
        for _k, _v in _ULKE_EN.items():
            if _k in EXCLUDED or _v in EXCLUDED:
                continue
            EXCLUDED.discard(_k); EXCLUDED.discard(_v)
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
                if _i18n_get_lang() == "en":
                    ulke = _ULKE_EN.get(ulke, ulke)
                elif _i18n_get_lang() == "es":
                    ulke = _ULKE_ES.get(ulke, ulke)
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
        lang=motor._lang,
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
