"""FBST Veri Katmani - Tum yorum ve sembol sozlukleri"""
import os
import importlib.util as _iu

_FAST_RENKLER = {
    "birincil": "#B8A9C9",    # lavender
    "ikincil": "#8FB8CA",     # sage
    "vurgu": "#C9A96E",       # gold
    "rose": "#D4878F",        # rose
    "text": "#4A4A4A",        # dark gray
    "text_light": "#6B5B7B",  # muted purple
    "bg": "#FBF7F4",          # cream
    "border": "#E8E0D8",      # light border
}

fbst_yukselenler = {
    "Koc": "Dış dünyaya inisiyatif alan, cesur ve öncü bir vitrinle çıkarsınız. Aşkın tutkusunu ve eylemsel guccunu dünyada fetihler yaparak somutlaştırırsınız.",
    "Boga": "Dış dünyaya sarsılmaz, huzur veren ve güven kokan bir vitrinle çıkarsınız. İlişkinin köklerini dünyada kalıcı bir maddi güvence ve sadakatle inşa edersiniz.",
    "Ikizler": "Dış dünyaya zihinsel olarak uyumlu, hareketli ve neşeli bir vitrinle çıkarsınız. Birbirinizin ufkunu açan o tatlı merakı, dünyada bilgi transferi ve iletişim ağı kurarak maddileştirirsiniz.",
    "Yengec": "Dış dünyaya korumacı, şefkatli ve birbirini saran bir vitrinle çıkarsınız. Aşkınızın o derin aidiyetini, dünyada sarsılmaz bir ruhsal yuva ve sıcak bir sığınak inşa ederek sergilersiniz.",
    "Aslan": "Dış dünyaya parlayan, cömert ve asil bir vitrinle çıkarsınız. Aşkınızın o ihtişamlı görkemini, dünyada yaratıcılık ve yönetme gücüyle taçlandırarak gösterirsiniz.",
    "Basak": "Dış dünyaya kusursuz işleyen, naif ve analitik bir vitrinle çıkarsınız. Birbirinize adadığınız iyileştirici şefkati, dünyada pratik bir düzen ve sıfır hatalı bir hizmetle maddileştirirsiniz.",
    "Terazi": "Dış dünyaya zarafetin ve uyumun vitriniyle çıkarsınız. Aşkın o masalsı dengesini, dünyada mutlak adalet, diplomasi ve kusursuz bir estetikle maddileştirirsiniz.",
    "Akrep": "Dış dünyaya son derece ketum, derin ve gizemli bir vitrinle çıkarsınız. Aşkınızın o hipnotik tutkusunu, dünyada yüzeysellikten uzak, dönüştürücü ve sarsılmaz bir güç merkezi kurarak yansıtırsınız.",
    "Yay": "Dış dünyaya maceracı, sınır tanımayan ve iyimser bir vitrinle çıkarsınız. Aşkın o coşkulu özgürlüğünü, dünyada uzak ufuklar keşfederek ve ortak bir vizyon inşa ederek maddileştirirsiniz.",
    "Oglak": "Dış dünyaya saygın, otoriter ve zamanın ötesinde bir vitrinle çıkarsınız. Fırtınaların sarsamayacağı o ebedi güveni, dünyada toplumsal statü ve yıkılmaz bir kale kurarak gösterirsiniz.",
    "Kova": "Dış dünyaya kuralları yıkan, ezber bozan ve elektrikli bir vitrinle çıkarsınız. Aşkınızın o isyankar doğasını, dünyada fütüristik idealler ve kolektif projeler üzerinden maddileştirirsiniz.",
    "Balik": "Dış dünyaya mistik, şefkatli ve adeta bu boyuta ait değilmiş gibi bir vitrinle çıkarsınız. Aşkınızın o koşulsuz teslimiyetini, dünyada ilahi bir şifa ve sanatsal bir üretimle maddileştirirsiniz."
}

fbst_retrolar = {
    "Merkür": "📝 <b>[Karmik Retro Mührü]:</b> <i>Zihinsel içe dönüş! Geçmiş kadersel yaşamlardan kalma söylenmemiş sözleriniz var. Bu ilişkide iletişim dışa dönük olmaktan ziyade, telepatik ve derin bir içsel anlayışla çözülecektir.</i>",
    "Venüs": "📝 <b>[Karmik Retro Mührü]:</b> <i>Özdeğer sınavı! Sevgi enerjisi dış dünyadaki gösterişten çekilip, ruhun en derinlerine gizlenmiştir. Partnerinizle geçmişten gelen yarım kalmış bir aşk kontratınız var; şimdi onu şifalandırmaya geldiniz.</i>",
    "Mars": "📝 <b>[Karmik Retro Mührü]:</b> <i>Eylemin içselleştirilmesi! Öfke ve tutku dışarıya patlamak yerine içsel bir guca dönüşmüştür. Geçmişte yanlış kullanılmış güç veya pasif-agresif enerjileri bu ilişkide sevgiyle dönüştürme sınavındasınız.</i>",
    "Jüpiter": "📝 <b>[Karmik Retro Mührü]:</b> <i>İçsel bilgelik! Dış dünyanın ahlak ve inanç kurallarını reddedip, kendi ruhsal felsefenizi yaratma vaktidir. Bu ilişki, şansı dışarıda aramak yerine, bereketi kendi içinizde bulmanızı sağlayacaktır.</i>",
    "Satürn": "📝 <b>[Karmik Retro Mührü]:</b> <i>Ağır Karmik Borç! Otorite figürleriyle ve geçmiş yaşamlardaki sorumluluklarla ilgili bitmemiş bir sınavınız var. İlişkinin kurallarını dış dünyanın dayatmalarına göre değil, kendi sarsılmaz iç otoritenizle kurmalısınız.</i>",
    "Uranüs": "📝 <b>[Karmik Retro Mührü]:</b> <i>İçsel devrim! İsyankar enerjiniz topluma karşı değil, kendi iç dünyanızdaki prangalara karşı çalışacak. İkiniz de bu bağın içinde birbirinizin ruhunu özgürleştirecek gizli birer anarşistsiniz.</i>",
    "Neptün": "📝 <b>[Karmik Retro Mührü]:</b> <i>Gizli illüzyonlar! Spiritüel algılarınız çok açık ancak kurban psikolojisine düşme tehlikeniz var. Rüyalarınız ve sezgileriniz size yol gösterecek; dış dünyanın gürültüsüne değil, içinizdeki ilahi sese güvenin.</i>",
    "Plüton": "📝 <b>[Karmik Retro Mührü]:</b> <i>Yeraltı simyası! Güç savaşları ve manipülasyon arzusu, en derine gömülmüş korkulardan beslenir. Bu ilişki sizi en büyük psikolojik zaaflarınızla yüzleştirip, kendi küllerinizden sessizce yeniden doğuracak.</i>",
    "Chiron": "📝 <b>[Karmik Retro Mührü]:</b> <i>Kadim yara! Şifa enerjisi dışarıdan önce kendi içinize yönelmelidir. Kendinizi iyileştirmeden partnerinizi iyileştiremezsiniz. Bu bağ, ruhun en saklı kalmış dehlizlerindeki acılara ayna tutarak merhem olacaktır.</i>",
    "Juno": "📝 <b>[Karmik Retro Mührü]:</b> <i>Karmik eş kontratı! Geçmiş yaşamlardan kalan tamamlanmamış bir evlilik veya sadakat sözleşmesi tekrar masada. Bağlılığın yüzeysel kurallarını yıkıp, ruhsal sadakati en derinden test edeceksiniz.</i>",
    "Ceres": "📝 <b>[Karmik Retro Mührü]:</b> <i>İçsel beslenme! Partnerinizden şefkat beklerken, aslında kendi kendinize yetmeyi ve kendi ruhunuzu beslemeyi öğrenmeniz gereken özel bir kadersel döngü.</i>",
    "Lilith": "📝 <b>[Karmik Retro Mührü]:</b> <i>Gölgenin inzivası! Bastırılmış tabular, cinsellik ve boyun eğmeyen vahşi enerji, yüzeysel olarak yaşanmak yerine ilişkideki en karanlık ve büyüleyici gizem olarak içselleşmiştir.</i>"
}


fbst_yukselenler_ebeveyn = {
    "Koc": "Dış dünyaya cesur ve koruyucu bir ebeveyn vitriniyle çıkarsınız. Ebeveynlikte inisiyatif alan, çocuğunu korumak için dünyaya meydan okuyan bir enerji sergilersiniz.",
    "Boga": "Dış dünyaya sarsılmaz, huzur veren ve güvenli bir ebeveyn vitriniyle çıkarsınız. Çocuğunuza maddi ve manevi güvence sağlayan, köklü bir yuva inşa edersiniz.",
    "Ikizler": "Dış dünyaya iletişim odaklı, neşeli ve meraklı bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzla bilgi paylaşan, her şeyi onunla birlikte keşfeden bir ebeveyn olursunuz.",
    "Yengec": "Dış dünyaya korumacı, şefkatli ve kucaklayıcı bir ebeveyn vitriniyle çıkarsınız. Çocuğunuz için sarsılmaz bir duygusal sığınak inşa edersiniz.",
    "Aslan": "Dış dünyaya parlayan, cömert ve gurur verici bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzun yeteneklerini sahneye koyan, onunla gurur duyan bir ebeveyn olursunuz.",
    "Basak": "Dış dünyaya kusursuz organize eden, pratik ve detaycı bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzun her ihtiyacını milimetrik karşılayan bir sistem kurarsınız.",
    "Terazi": "Dış dünyaya zarif, dengeli ve adaletli bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzla adil bir ilişki kuran, her zaman dengeyi arayan bir ebeveyn olursunuz.",
    "Akrep": "Dış dünyaya derin, gizemli ve koruyucu bir ebeveyn vitriniyle çıkarsınız. Çocuğunuz için her türlü tehlikeye karşı tetikte olan, okült bir ebeveynlik sergilersiniz.",
    "Yay": "Dış dünyaya maceracı, iyimser ve özgürlükçü bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzla birlikte hayatı keşfeden, ona geniş bir vizyon aşılayan bir ebeveyn olursunuz.",
    "Oglak": "Dış dünyaya saygın, disiplinli ve sorumluluk sahibi bir ebeveyn vitriniyle çıkarsınız. Çocuğunuza yapı ve disiplin veren, hayata hazırlayan bir ebeveyn olursunuz.",
    "Kova": "Dış dünyaya yenilikçi, özgürlükçü ve sıra dışı bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzu kalıplara sokmayan, bireyselliğine saygı duyan bir ebeveyn olursunuz.",
    "Balik": "Dış dünyaya mistik, şefkatli ve sezgisel bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzla ruhsal bir bağ kuran, onun manevi gelişimine odaklanan bir ebeveyn olursunuz."
}

fbst_retrolar_ebeveyn = {
    "Merkür": "📝 <b>[Karmik Retro Mührü]:</b> <i>Ebeveynlikte iletişim içe yönelir! Çocuğunuzla aranızdaki bağ sözcüklerin ötesindedir; sezgisel ve telepatik bir anlayışla connected olmanız beklenir.</i>",
    "Venüs": "📝 <b>[Karmik Retro Mührü]:</b> <i>Özdeğer ve sevgi dilini yeniden öğrenme! Çocuğunuza sevginizi gösterme şekliniz, kendi çocukluk deneyimlerinizden derinden etkilenmiştir.</i>",
    "Mars": "📝 <b>[Karmik Retro Mührü]:</b> <i>Koruma içgüdüsünün içselleştirilmesi! Öfke ve sabır dengeniz test edilir; çocuğunuzla aranızdaki güç dinamiğinde içsel bir denge bulmanız gereken döngü.</i>",
    "Jüpiter": "📝 <b>[Karmik Retro Mührü]:</b> <i>Öğretme felsefesinin yeniden yapılması! Çocuğunuza aktardığınız değerler ve inançlar, kendi içinizde derin bir sorgulamadan geçmelidir.</i>",
    "Satürn": "📝 <b>[Karmik Retro Mührü]:</b> <i>Ebeveynlik disiplinindeki karmik borç! Sınır koyma ve otorite kurma konularında, kendi ebeveynlerinizden aldığınız mirası yeniden yapılandırmanız gereken sınav.</i>",
    "Uranüs": "📝 <b>[Karmik Retro Mührü]:</b> <i>İçsel ebeveynlik devrimi! Çocuğunuzun özgürlüğünü desteklerken, kendi içinizdeki bağımlılıkları ve korkuları yenmeniz gereken kadersel döngü.</i>",
    "Neptün": "📝 <b>[Karmik Retro Mührü]:</b> <i>İllüzyon ve ideal ebeveynlik! Mükemmel anne/baba olma hayaliniz, gerçekçi sınırlarla dengelenmelidir. Sezgileriniz güçlü ama netlik gerekli.</i>",
    "Plüton": "📝 <b>[Karmik Retro Mührü]:</b> <i>Ebeveynlik güç dönüşümü! Çocuğunuzun büyümesiyle birlikte kendi kimliğiniz de derinden değişir; kontrol bırakma ve yeniden doğuş sınavı.</i>",
    "Chiron": "📝 <b>[Karmik Retro Mührü]:</b> <i>Nesnel yara mirası! Kendi ebeveynlerinizden aldığınız yaraları şifalandırmadan, çocuğunuza tam anlamıyla şifa veremezsiniz. Nesnel şifa zincirinin bilinci.</i>",
    "Juno": "📝 <b>[Karmik Retro Mührü]:</b> <i>Ebeveynlik sadakat kontratı! Çocuğunuza verdiğiniz koşulsuz sadakat sözü, kendi iç çatışmalarınızla test edilir.</i>",
    "Ceres": "📝 <b>[Karmik Retro Mührü]:</b> <i>Besleme ve bırakma dengesi! Çocuğunuzu beslerken onu aynı anda bağımsız bırakmayı da öğrenmeniz gereken kadersel döngü.</i>",
    "Lilith": "📝 <b>[Karmik Retro Mührü]:</b> <i>Ebeveynlikte bastırılmış vahşilik! Toplumsal beklentilerin dışında, çocuğunuza en otantik ve sınırsız sevginizi gösterme korkunuzla yüzleşme zamanı.</i>"
}



KRIZ_KUTUPHANESI_EBEVEYN = [
    {
        "baslik": "İlk Uyanış: Vücudun Sırrı (0-6 Ay)",
        "yorum": "Doğumla birlikte hem siz hem de bebeğiniz devasa bir değişime uğradınız. Uykusuz geceler, beslenme düzeni ve ebeveyn kimliğinin ilk adımları bu dönemin temel sınavlarıdır. Bu kriz, sizi birey olmaktan anne/babaya dönüştüren ilk kapıdır."
    },
    {
        "baslik": "Kök Bağı: Ayrışmanın Tohumları (6 Ay - 2 Yıl)",
        "yorum": "Bebeğiniz yürümeye, konuşmaya ve mundo keşfetmeye başladıkça, onunla aranızdaki fiziksel bağın ötesinde güvenli bir bağlanma inşa etmenin zamanıdır. İlk 'hayır'ların ve ilk ayrılıkların evidir."
    },
    {
        "baslik": "Ben Merkezcilik Sınavı (2-4 Yaş)",
        "yorum": "'Hayır!' diyen, sınır denemeleri yapan, tuvalet eğitimiyle yüzleşen bir çocukla başa çıkmak, ebeveynlik sabrının ilk büyük testidir. Sınır koyma sanatı burada öğrenilir."
    },
    {
        "baslik": "Sosyal Aynada Yansıma (4-7 Yaş)",
        "yorum": "Çocuğunuz okula başlar, arkadaş edinir ve sizin dışınızdaki dünyanın kurallarını keşfeder. Onun sosyal yeteneklerini desteklerken kendi ebeveynlik kaygılarınızla yüzleşmenin zamanıdır."
    },
    {
        "baslik": "Bilgi Tapınağının Kapıları (7-12 Yaş)",
        "yorum": "Akademik baskı, yetenek keşfi ve karşılaştırma tuzağı bu dönemin sınavlarıdır. Çocuğunuzun kendi yolunu bulmasına izin verirken, toplumsal beklentilerle denge kurmanız gereken kritik dönem."
    },
    {
        "baslik": "Ergenlik Fırtınası: Kimlik Bunalımı (12-16 Yaş)",
        "yorum": "Hormonal değişiklikler, bağımsızlık savaşları ve kimlik arayışı bu dönemin temel yapiylaridir. Çocuğunuz artık bir birey olmak istiyor; siz ise hala korumak istiyorsunuz. Bu çatışma, ebeveyn-çocuk ilişkisinin en kritik sınavıdır."
    },
    {
        "baslik": "Ayrışma Protokolü (16-18 Yaş)",
        "yorum": "Üniversite, evden ayrılma ve bağımsız hayatın ilk adımları bu dönemde atılır. Yıllardır inşa ettiğiniz bağı gevşetip, bırakmanın zamanı gelmiştir."
    },
    {
        "baslik": "Yansıma: Kendini Görmek (18-21 Yaş)",
        "yorum": "Artık yetişkin olan çocuğunuz, sizi bir birey olarak görmeye başlar. Ebeveyn hatalarını fark etme, affetme ve ilişkide yeniden denge kurma sürecidir."
    },
    {
        "baslik": "Eşitlik Kapısı: Yetişkin Dostluğu (21+ Yaş)",
        "yorum": "Ebeveyn-çocuk ilişkisi artık hiyerarşik olmaktan çıkıp, iki yetişkin arasındaki saygı ve dostluğa dönüşür. Bu, ebeveynliğin en tatlı ödülünü toplama zamanıdır."
    }
]



fbst_sabian = {
    "Koc": {
        1: ("Denizden yeni çıkmış, fok balığına sarılan bir kadın", "Yeni başlangıçlar, geçmişin sularından çıkarak bu ilişkide yepyeni bir formda doğma cesareti."),
        2: ("Gözlerden uzak bir vadide, yeteneklerini sergileyen bir komedyen", "Dış dünyanın onayına ihtiyaç duymadan, ilişkinin kendi içindeki neşeyi ve potansiyeli keşfetmesi."),
        3: ("Ülkesinin haritasını çıkaran bir adam", "İlişkinin kendi sınırlarını, potansiyelini ve gelecekteki ortak yaşam alanını belirleme çabası."),
        4: ("Gözlerden uzak, tenha bir yolda yürüyen iki aşık", "Dış dünyanın kalabalığından izole olup, ilişkinin kendi iç mahremiyetini ve kutsal yalnızlığını inşa etme gücü."),
        5: ("Kanatlı bir üçgen", "Ruh, beden ve zihin bütünlüğünün sağlanarak ilişkinin dünyevi sınırları aşıp ilahi bir boyuta (guce) yükselişi."),
        6: ("Bir kenarı parlak şekilde aydınlatılmış bir kare", "İlişkideki sağlam ve yapısal temellerin üzerine düşen evrensel ışık; odaklanılması gereken kadersel yönü gösteriyor."),
        7: ("Aynı anda iki farklı dünyada kendini ifade edebilen bir adam", "Hem maddi hem de manevi alemlerde denge kurarak, ilişkinin dualiteyi aşan kusursuz bir uyum yakalaması."),
        8: ("Doğu rüzgarında dalgalanan kurdeleli büyük bir kadın şapkası", "Evrensel değişim rüzgarlarına karşı sezgisel bir kalkan oluşturma ve ruhsal fırtınalara direnmeden uyumlanma."),
        9: ("Kristal küreye odaklanmış bir medyum", "Görünenin ötesine geçme, partnerin içsel dünyasındaki sessiz çağrıları ve yaraları telepatik olarak okuma yeteneği."),
        10: ("Geleneksel imgelere yeni formlar veren bir öğretmen", "Eski alışkanlıkları ve kalıplaşmış toksik ilişki yapiylarini yıkarak, bağınızı yepyeni bir vizyonla baştan yaratma."),
        11: ("Bir ülkenin yöneticisi", "İlişkinin kendi krallığını ilan etmesi, sorumluluk alma ve bu kadersel birliğin sarsılmaz otoritesini kurma vakti."),
        12: ("Üçgen şeklinde uçan yaban kazları sürüsü", "Ortak hedeflere doğru kusursuz bir kadersel senkronizasyon ve ilahi bir içgüdüyle, çabasızca yol alma gücü."),
        13: ("Patlamamış bir bomba; başarısız bir sosyal isyan", "İçinizde biriken öfke ve krizlerin, yıkıcı bir şekilde patlamak yerine sönümlenerek ruhsal bir bilgeliğe dönüşmesi ihtimali."),
        14: ("Bir adam ve kadının yakınında kıvrılan bir yılan", "Karmik bilgelik, köklü cinsel enerji (Kundalini) ve ilişkinin en derinlerinden uyanan gizemli, dönüştürücü çekim gücü."),
        15: ("Törensel bir battaniye dokuyan bir Kızılderili", "İlişkinin her bir anını, ince bir sabır ve emekle dokuyarak dışarıya karşı kutsal bir ruhsal zırh veya yuva haline getirme çabası."),
        16: ("Gün batımında çalışan doğa ruhları (periler)", "Günlük çabaların ötesinde, görünmez evrensel güçlerin (kadersel amortisörlerin) ilişkinizi onarmak ve desteklemek için devrede olması."),
        17: ("Sessizlik içinde onurlu bir şekilde oturan iki bekar kadın", "Yalnızlık korkusunu aşarak, sessizliğin ve ruhsal dinginliğin içinde birbirinize muazzam bir huzurla eşlik etme erdemi."),
        18: ("İki ağaç arasına gerilmiş boş bir hamak", "Aksiyon ve çabayı bırakıp, ilişkinin dinlenmeye, eylemsizliğe ve doğal akışa (rölantiye) teslim olmaya ihtiyaç duyduğu o kutsal an."),
        19: ("Sihirli bir halı", "Dünyevi kısıtlamaları ve mantığı reddeden, hayal gücü ve inançla sınırları aşarak ilişkinizi masalsı bir boyuta taşıma potansiyeli."),
        20: ("Kışın kuşları besleyen genç bir kız", "En zor, soğuk ve krizli anlarda bile; şefkat, merhamet ve koşulsuz sevgiyle birbirinizin ruhunu besleyebilme mucizesi."),
        21: ("Ringe giren bir boksör", "İlişkinin dışsal engellere, zorluklara veya içsel gölgelere karşı savaşmak üzere cesaretle ve eylemsel guce donanması."),
        22: ("Tüm arzuların gerçekleştiği bahçeye açılan kapı", "Ruhsal ve dünyevi tatminin zirvesine ulaşma vaadi; engellerin aşılıp kadersel ödüllerin, bolluğun kapısında durma hali."),
        23: ("Hafif bir yazlık elbise içinde hamile bir kadın", "İlişkinin kendi içinde büyüttüğü yeni bir vizyonun, yaratıcılığın, bereketin veya ruhsal bir meyvenin doğuma hazırlanması."),
        24: ("Açık bir pencereden içeri savrulan perdelerin bereket boynuzu şeklini alması", "Evrensel akışa tam teslim olunduğunda, kozmik şansın ve ruhsal bereketin beklenmedik bir şekilde ilişkinize dolması."),
        25: ("İnsanın iki farklı varlık seviyesinde deneyim kazanma ihtimali", "Aşkı hem en tutkulu fiziksel boyutta hem de en yüce ilahi boyutta aynı anda, ustalıkla yaşayabilme lütfu."),
        26: ("Taşıyabileceğinden daha fazla yeteneğe sahip olan bir adam", "İlişkinin potansiyelinin taşması; bu çok yoğun kadersel enerjiyi dağıtmadan odaklayıp doğru şekilde yönetme sınavı."),
        27: ("Hayal gücü sayesinde kaybedilmiş bir fırsatın yeniden kazanılması", "Geçmişte yapılmış hataların veya kaçırılan şansların, güçlü bir sevgi ve inançla onarılıp kadersel rotanın yeniden çizilmesi."),
        28: ("Hayal kırıklığına uğramış büyük bir izleyici kitlesiyle yüzleşen performans sanatçısı", "İlişkideki aşırı beklentilerin gerçeklikle çarpışması; maskelerin düşerek çıplak gerçeğin sevgiyle, olduğu gibi kabul edilmesi sınavı."),
        29: ("Göksel kürelerin (gezegenlerin) müziği", "Ruhlarınızın evrensel titreşimle tam bir uyuma girdiği, kelimelere ihtiyaç duyulmayan o ilahi ve kozmik senkronizasyon noktası."),
        30: ("Bir ördek göleti ve yavruları", "Kadersel yolculuğun bu fazında sükunete erme; ait olma, huzurlu bir yuva kurma ve mutlak bir korunma alanının tamamlanması.")
    },
    "Boga": {
        1: ("Berrak bir dağ deresinin taşıdığı altın tozları", "İlişkinin doğal akışında saklı olan muazzam maddi ve manevi zenginliği fark etme ve bu bereketi sevgiyle kabul etme zamanı."),
        2: ("Elektrik fırtınası; doğanın karanlık gökyüzündeki muazzam gücü", "Krizlerin ve ani patlamaların aslında aranızdaki durgun enerjiyi temizleyen kozmik bir şifa ve uyanış olması."),
        3: ("Yoncalarla açan bir çimenliğe çıkan doğal basamaklar", "İlişkinin huzura, berekete ve köklenmeye giden yolda acele etmeden, adım adım ve organik bir şekilde büyümesi."),
        4: ("Gökkuşağının sonundaki altın küpü", "Fırtınalı süreçlerin ve sınavların ardından gelen o büyük kadersel ödül; birlikte ulaşılan ruhsal ve maddi tatmin."),
        5: ("Açık bir mezarın başında bekleyen dul bir kadın", "Geçmişin acılarına ve bitmiş karmik bağlara veda ederek, ruhsal bir arınmayla bu yeni ilişkiye tamamen yer açma sınavı."),
        6: ("Derin bir uçurumun üzerine kurulan asma köprü", "Aranızdaki en aşılmaz gibi görünen farklılıkları, sağlam ve güvenilir bir iletişim/sadakat köprüsüyle aşma gücü."),
        7: ("Kuyunun başındaki Samiriyeli kadın", "Eski önyargıları ve dünyevi tabuları yıkarak, partnerinizin ruhundaki en derin susuzluğu koşulsuz sevgiyle giderme erdemi."),
        8: ("Karsız bir zeminde duran kızak", "Gelecek için yapılan planlarda zamanlamanın önemini anlama; doğru kadersel şartlar oluşana kadar sabırla bekleme iradesi."),
        9: ("Tamamen süslenmiş bir Noel ağacı", "İlişkinin en karanlık veya soğuk günlerinde bile umudu canlı tutması ve birbirinize sunduğunuz içsel değerlerin kutlanması."),
        10: ("Bir Kızılhaç hemşiresi", "Koşulsuz şefkat, fedakarlık ve partnerin en zayıf, yaralı anında onun en büyük ruhsal şifacısı olma kontratı."),
        11: ("Bahçesindeki çiçekleri sulayan bir kadın", "Sevginin ancak günlük, istikrarlı ve pratik bir emekle beslendiğinde yıkılmaz ve kalıcı bir yuvaya dönüşeceği bilgeliği."),
        12: ("Vitrinlere bakan genç bir çift", "Ortak hayaller kurma, geleceği birlikte inşa etme ve ilişkinin dünyevi/maddi hedeflerini neşeyle belirleme fazı."),
        13: ("Ağır yükler taşıyan bir hamal", "İlişkinin maddi veya kadersel yüklerini cesaretle omuzlama; sadakatin ve sorumluluğun ağır bir sabır testine dönüşmesi."),
        14: ("Sahilde oynayan çocuklar ve suyun kenarındaki deniz kabukluları", "Doğal sınırlar içinde güvenle neşeyi yaşama; huzurlu bir yuva alanında çocuksu, korunaklı ve saf duygulara teslimiyet."),
        15: ("Kafasını kalın bir atkıyla sarmış adam", "Dış dünyanın gürültüsüne ve toksik müdahalelerine karşı ilişkinin mahremiyetini koruma; sadece birbirinizin iç sesini dinleme ihtiyacı."),
        16: ("Öğrencilerinin ilgisini çekemeyen yaşlı bir öğretmen", "İlişkide eski, işe yaramayan kalıpları bırakma vakti; inatlaşılan kurallar yerine yeni ve ilham verici bir ortak dil bulma zorunluluğu."),
        17: ("Kılıçlar ve meşaleler arasındaki sembolik savaş", "İlişkide zihinsel aydınlanma (meşale) ile yıkıcı eleştiri (kılıç) arasında seçim yapma; haklı olmayı değil şifayı seçme sınavı."),
        18: ("Eski bir çantayı açık pencereden havalandıran kadın", "Bilinçaltında birikmiş eski zehirleri, şüpheleri ve yükleri sevginin o taze ve şifalı rüzgarıyla temizleme arınması."),
        19: ("Okyanusun içinden yükselen yeni bir kıta", "Büyük krizlerin ve duygusal çalkantıların ardından ilişkinin yepyeni, sarsılmaz ve somut bir temel (kıta) yaratma mucizesi."),
        20: ("Gökyüzünde uçuşan kanat benzeri bulutlar", "Manevi bir ilhamın, evrensel korumanın ve hafifliğin ilişkiye sızması; aşırı maddiyatçılıktan sıyrılıp ilahi akışa güvenme."),
        21: ("Açık bir kitaptaki satırı gösteren parmak", "Kadersel kontratın size sunduğu çok net bir işareti, mesajı veya senkronizasyonu fark edip ona göre hizalanma anı."),
        22: ("Fırtınalı suların üzerinde uçan beyaz güvercin", "En büyük krizlerin, kavgaların ve korkuların ortasında bile; evrensel bir barışın, güvenin ve ilahi korumanın ilişkinin üzerinde süzülmesi."),
        23: ("Değerli taşlarla dolu bir mücevher dükkanı", "İlişkinin sahip olduğu o yüksek özdeğeri, nadir bulunan yetenekleri ve parlayan ortak zenginliği idrak etme zirvesi."),
        24: ("Belinde düşman kafa derileriyle at süren Kızılderili savaşçı", "Koruma içgüdüsünün veya sahiplenmenin yıkıcı bir kıskançlığa/kontrolcülüğe dönüşmesi riski; ilkel egoyu ehlileştirme sınavı."),
        25: ("Geniş ve muazzam bir halk parkı", "Kişisel sevginin sınırlarını aşıp, ilişkinin dış dünyaya da ilham veren kolektif bir huzur, bereket ve hoşgörü alanına dönüşmesi."),
        26: ("Sevgilisine serenat yapan İspanyol aşık", "Romantizmin, kur yapmanın ve sevgi dilini estetik bir şekilde, cesurca ifade etmenin ilişkinin manyetik guccunu yeniden alevlendirmesi."),
        27: ("Kabilesinin el sanatlarını satan yaşlı bir kadın", "Geleneklerin, köklerin ve geçmişin kadim bilgeliğini; ilişkinizin bugünkü maddi ve manevi inşasına faydalı olacak şekilde uyarlama."),
        28: ("Aşka yeniden uyanan olgun bir kadın", "Geçmişin tüm hayal kırıklıklarına rağmen kalbi cesurca yeniden açma; aşkın zamansız olduğunu ve ilişkinin her an yeniden filizlenebileceğini idrak etme."),
        29: ("Bir masada çalışan iki ayakkabı tamircisi", "Ortak bir amaç için omuz omuza, sıfır ego ile çalışma; vizyonları gerçeğe dönüştürmek için pratik, dengeli ve kusursuz bir işbirliği mühürü."),
        30: ("Eski bir kalenin terasında gösteriş yapan tavus kuşu", "Zamanın testlerinden geçmiş başarıların, asaletin ve ebedi güvenin haklı gururu; ilişkinin köklü bir imparatorluk üzerinde ihtişamla taçlanması.")
    },
    "Ikizler": {
        1: ("Cam tabanlı bir teknede okyanusun dibini izleyen insanlar", "Yüzeysel olanın ötesine geçip, zihinsel merakla birbirinizin en derin ruhsal sularını keşfetme arzusu."),
        2: ("Noel Baba'nın gizlice çorapları doldurması", "Beklenmedik anda gelen kadersel hediyeler ve aranızdaki saf, çocuksu masumiyetin görünmez bir el tarafından ödüllendirilmesi."),
        3: ("Paris'teki Tuileries Bahçeleri", "İletişimde zarafetin, zihinsel düzenin ve entelektüel uyumun kusursuz bir mimariyle (ortak bir dille) inşa edilmesi."),
        4: ("Çobanpüskülü ve ökse otu", "Nostaljinin, eski anıların ve köklü geleneklerin aranızdaki zihinsel bağı romantik bir köprüyle canlı tutması."),
        5: ("Eyleme çağıran radikal bir dergi", "Zihinsel isyan! İlişkideki sıradanlığı ve rutini kırarak, birbirinizin zihnini ateşleyecek yeni ve devrimsel fikirler üretme ihtiyacı."),
        6: ("Petrol sondajı yapan işçiler", "Günlük sohbetlerin ve yüzeysel iletişimin çok ötesine geçip, ilişkinin en derinindeki o zengin, gizli güç kaynağına (petrole) ulaşma çabası."),
        7: ("Eski moda bir su kuyusu", "Birbirinizin zihninden, tükenmeyen kadim bir bilgelik ve ilham kaynağı gibi faydalanma; ruhsal susuzluğu kelimelerle giderme."),
        8: ("Fabrikanın etrafında toplanmış öfkeli grevciler", "Fikir ayrılıklarının krize dönüşmesi; zihinsel adalet arayışı ve ilişkide eşit söz hakkı talep eden sarsıcı bir yüzleşme."),
        9: ("Oklarla dolu bir sadak", "Zihinsel keskinlik! Hedefe kilitlenmiş sözler; kelimeleri birbirinizi yaralamak için değil, ortak engelleri vurmak için kullanma sınavı."),
        10: ("Burun dalışı yapan bir uçak", "İletişimde tehlikeli manevralar; büyük zihinsel riskler alarak ilişkide korkulan o büyük yüzleşmeyi cesaretle gerçekleştirme."),
        11: ("Yeni açılmış topraklarda sunulan bakir deneyim alanları", "Zihnin sınırlarını genişletme; ilişkinin yepyeni ufuklara, ortak eğitimlere veya daha önce hiç konuşulmamış konulara yelken açması."),
        12: ("Siyahi bir köle kızın, hanımından haklarını talep etmesi", "İletişimdeki gizli dengesizliklerin patlaması; bir tarafın zihinsel tahakkümüne karşı diğerinin özgürlük ve saygı talebiyle ayaklanması."),
        13: ("Piyano konseri veren ünlü bir müzisyen", "Entelektüel yeteneklerin kusursuz sergilenişi; fikirlerinizle, vizyonunuzla ve iletişiminizle birbirinize ilham verip hayran bırakma hali."),
        14: ("Uzaklarda yaşayan iki insanın telepatik iletişimi", "Mekansal mesafelere veya sessizliklere rağmen, zihinlerin kuantum seviyesinde birbirine bağlanarak muazzam bir telepatik aktarım yapması."),
        15: ("Kendi aralarında konuşan iki Hollandalı çocuk", "Karmaşık felsefeleri bir kenara bırakıp, ilişkinin en saf, en neşeli ve sadece ikinizin anladığı o basit ortak dili kurabilme mucizesi."),
        16: ("Duygusal bir konuşma yapan kadın aktivist", "İnançlar ve ortak hedefler uğruna tutkulu bir savunma; ilişkinin zihinsel enerjisinin dış dünyaya karşı bir kalkana dönüşmesi."),
        17: ("Gürbüz bir gencin kafasının olgun bir düşünürün kafasına dönüşmesi", "İlişkinin zihinsel olarak seviye atlaması; çocuksu merakın ve fevriliğin, deneyimle harmanlanarak derin bir kadersel bilgeliğe evrilmesi."),
        18: ("Amerikan kalabalığı içinde kendi anadillerinde konuşan iki Çinli", "Dış dünyanın kalabalığı ve gürültüsü içinde, sadece ikinizin çözebildiği o gizli zihinsel titreşim ve özel şifrelerle iletişim kurma."),
        19: ("Geleneksel bilgeliği ortaya çıkaran büyük arkaik bir cilt (kitap)", "İlişkinin köklerini, geçmişten veya kadim öğretilerden alınan büyük bir dersle, felsefi bir aydınlanmayla besleme anı."),
        20: ("Çok sayıda seçeneğin bulunduğu bir kafeterya", "Zihinsel dağınıklık veya kararsızlık sınavı; birçok fikir veya seçenek arasından ilişkinin kadersel rotasını ortak bir akılla seçebilme gücü."),
        21: ("Gürültülü bir işçi gösterisi", "Mantık ve duyguların, haklılık ve haksızlığın sert çatışması; ilişkide birikmiş zihinsel basıncın tahliye edilmesi gereken darboğaz."),
        22: ("Hasat festivalinde dans eden çiftler", "Zihinsel uyumun, üretken fikirlerin ve başarılı iletişimin meyvelerini toplama; ilişkinin neşeli ve coşkulu bir kutlamaya dönüşmesi."),
        23: ("Ağacın tepesindeki bir yuvada bulunan üç yavru kuş", "Zihinsel tohumların büyümesi; ortak fikirlerin, planların veya projelerin henüz kuluçka aşamasında olup şefkatle korunmaya ihtiyaç duyması."),
        24: ("Donmuş köy göletinde buz pateni yapan çocuklar", "Soğuk, krizli veya mesafeli dönemlerin üstesinden, iletişimdeki kıvrak bir zeka, neşe ve esneklikle gelebilme yeteneği."),
        25: ("Büyük palmiye ağaçlarını budayan bir bahçıvan", "İlişkinin zihinsel dallarını temizleme; gereksiz detayları, toksik düşünceleri ve geçmiş takıntıları budayarak ana hedefe (gövdeye) odaklanma."),
        26: ("Kış gökyüzüne karşı duran kırağı kaplı ağaçlar", "Duygusal mesafenin veya sessizliğin olduğu dönemlerde bile, aradaki o sağlam zihinsel bağın kristalize olmuş o eşsiz, asil güzelliği."),
        27: ("Kabilesinin kamp kurduğu ormandan çıkan bir çingene", "Zihinsel özgürlük arayışı; alışılmış düşünce kalıplarından ve ilişkinin konfor alanından çıkarak dışarıda yeni bir felsefe deneme cesareti."),
        28: ("İflas yoluyla toplumun yeniden başlama fırsatı vermesi", "Eski iletişim dilinin veya zihinsel yapıların tamamen çökmesi; bu yıkımın ardından sıfırdan, çok daha dürüst ve güçlü bir zihin inşası şansı."),
        29: ("İlkbaharın ilk bülbülü", "Yeniden doğuş, neşeli haberler ve taze fikirler; aradaki iletişimin kıştan çıkarak bahar coşkusuyla ve tatlı bir melodiyle canlanması."),
        30: ("Denize giren güzellerin geçit töreni", "Zihinsel ve estetik uyumun dışarıya cesurca sergilenmesi; ilişkinin sosyal vitrininde özgüvenle, parıldayarak boy gösterme enerjisi.")
    },
    "Yengec": {
        1: ("Aboard a ship sailors lower an old flag and raise a new one (Yelkenlide eski bayrağın inip yenisinin çekilmesi)", "Eski aidiyetlerin, ailevi bağların veya geçmişin sona erip, bu ilişkiyle yepyeni bir 'ortak yuva' kimliğine doğma cesareti."),
        2: ("Sihirli bir halı üzerinde geniş bir araziyi izleyen adam", "İlişkinin, günlük dünyevi dertlerden soyutlanıp, birbirinizin ruhuna üst bir perspektiften ve objektif bir şefkatle bakabilme yeteneği."),
        3: ("Kürklere bürünmüş bir adamın tüylü bir geyiği yönlendirmesi", "En soğuk, zor ve krizli zamanlarda bile, partnerinin o hassas ruhuna (geyiğe) sarsılmaz bir koruyucu kalkan (kürk) olma içgüdüsü."),
        4: ("Fareyle tartışan bir kedi", "Ortak yaşam alanında (yuvada) yaşanan ufak tefek güç savaşları; duygusal sınırların sevgiyle mi yoksa manipülasyonla mı test edileceğinin sınavı."),
        5: ("Tren yolunda trenin çarpıp parçaladığı bir otomobil", "Kaderin o durdurulamaz akışına (tren) karşı kişisel egoyla inatlaşmanın yıkıcılığı; bu ilişkide sisteme ve ilahi plana mutlak teslimiyetin şart olması."),
        6: ("Yuvalarını tüylendiren oyun kuşları", "Evliliğe, ortak yaşama ve yuvaya duygusal/maddi yatırım yapma vakti; birbirinizin kalbinde o en güvenli ve sıcak köşeyi inşa etme erdemi."),
        7: ("Ay ışığında dans eden iki doğa ruhu (peri)", "Mantığın bittiği yerde başlayan masalsı, çocuksu ve sihirli duygusal uyum; ilişkinin rasyonel dünyadan çıkıp rüya aleminde şifalanması."),
        8: ("İnsan kıyafetleri giymiş bir grup tavşanın geçit töreni", "Dış dünyanın, ailelerin veya toplumun ilişkiye dayattığı sahte formlara (kıyafetlere) bürünme tehlikesi; yapaylıktan kaçıp öze dönme uyarısı."),
        9: ("Gölette balık yakalamaya çalışan küçük, çıplak bir kız çocuğu", "İlişkinin en saf, en masum, en savunmasız anlarına geri dönerek o ilk günkü heyecanı (balığı) telaşsızca yakalama ve koruma çabası."),
        10: ("İlk kesim aşamasındaki büyük ve işlenmemiş bir elmas", "Ham ve ilkel sevginin zamanla, krizlerle ve sabırla işlenerek paha biçilmez, ebedi bir sadakat pırlantasına dönüşme süreci."),
        11: ("Ünlüleri taklit eden bir palyaço", "İlişkideki egoları, gerginlikleri ve çatışmaları muazzam bir mizahla, şefkatli bir alayla yumuşatarak yuvaya neşe katma yeteneği."),
        12: ("Aurasından reenkarne bir bilge olduğu anlaşılan bebeği emziren kadın", "Birbirinizin o naif, çocuksu yaralarını sararken aslında çok kadim ve kadersel bir ruhu beslediğinizin o büyük, kutsal farkındalığı."),
        13: ("İncelenmek üzere uzatılan, belirgin başparmaklı bir el", "İlişkide iradenin, karakterin ve somut eylemlerin (el) maskesiz bir şekilde dürüstçe masaya yatırılması ve yüzleşilmesi."),
        14: ("Kuzeydoğudaki karanlık ve dipsiz boşluğa bakan çok yaşlı bir adam", "Bilinmeyene, geleceğe ve yaşlılığa karşı birlikte geliştirilen sarsılmaz bir ruhsal bilgelik; ebediyete el ele yürüme cesareti."),
        15: ("Büyük bir ziyafet sonrası lüks bir yemek salonunda dinlenen konuklar", "İlişkinin zor günlerini atlatıp maddi/manevi tatminin, doygunluğun ve yuva huzurunun doruğuna ulaşma; o büyük ruhsal hasat anı."),
        16: ("Kadim bir kitap yardımıyla önündeki mandalayı inceleyen bir adam", "Aranızdaki bu derin ve karmaşık kadersel yapıyı (mandala), yüzeysel akılla değil, evrensel yasalar ve ruhsal bilgelikle çözme arzusu."),
        17: ("Bilgiye ve hayata dönüşen tohum", "Atılan ufacık bir sevgi ve şefkat tohumunun, köklenerek muazzam bir yaşam alanına (koca bir aileye) dönüşmesinin ilahi müjdesi."),
        18: ("Yavrularını beslemek için toprağı eşeleyen bir tavuk", "Aileyi, çocukları veya ilişkinin ortak geleceğini korumak için gösterilen o bitmek bilmeyen, fedakar ve kutsal anaç/ataç emek."),
        19: ("Evlilik töreni yöneten bir rahip", "İlişkinin kadersel bir akitle mühürlenmesi; sadakatin sadece dünyevi bir imza değil, ilahi bir onayla ve evrensel bir sözleşmeyle taçlanması."),
        20: ("Serenat yapan Venedik gondolcuları", "Duygusal dalgalanmaların, krizlerin ve suların üzerinde (gondol) muazzam bir zarafetle, romantizmle durarak aşkı kutlama gücü."),
        21: ("Operada hünerini sergileyen ünlü bir şarkıcı", "Birbirinize olan o derin sevginizin, fedakarlığınızın ve aidiyetinizin doruk noktasını yaşama ve bunu dünyada saygın bir duruşla sunma."),
        22: ("Yelkenliyi bekleyen genç kadın", "Kadersel partneri, beklenen ruhsal kurtarıcıyı veya ilişkinin gelecekteki o huzurlu günlerini sarsılmaz bir inanç, sadakat ve sabırla bekleme."),
        23: ("Bir edebiyat kulübünün toplantısı", "Sadece duygusal değil, ortak entelektüel değerlerin, kültürel köklerin ve paylaşılan ideallerin ilişkinin yatağını ve çatısını güçlendirmesi."),
        24: ("Güney denizlerinde küçük bir adada mahsur kalan kadın ve iki erkek", "İlişkide kadersel bir izolasyon, kıskançlık testleri veya aidiyetin, sadakatin sınırlarının en uç noktalarda, krizlerle sınanması."),
        25: ("İrade sahibi bir adamın üzerine inen üstün bir gücün gölgesi", "Kişisel egoların ve inatlaşmaların, ilişkinin ilahi kaderi (üstün güç) karşısında ezilmesi; evrene ve bu aşka tam teslimiyete zorlanma."),
        26: ("Lüks bir evin kütüphanesinde okuyan misafirler", "Zengin bir ruhsal ve zihinsel yuvada muazzam bir huzur bulma; tartışmaların yerini ortak bilgeliğin ve sessiz bir ahengin alması."),
        27: ("Lüks evlerin olduğu kanyonda şiddetli fırtına", "Konfor alanını ve yuvayı vuran kadersel kriz! İlişkinin sarsılmaz köklerinin, maddi ve manevi olarak dayaniklilik testinden geçmesi."),
        28: ("Beyaz sevgilisini kabilesiyle tanıştıran Kızılderili kız", "İki farklı kökün, ailenin, geleneğin veya geçmişin tek bir sevgi köprüsüyle birleştirilmesi; köklenmenin getirdiği o büyük uyum sınavı."),
        29: ("Yenidoğan ikizleri altın terazide tartan Yunan ilham perisi", "İçsel dualitenin (mantık ve duygu, sen ve ben) ilişki içinde kusursuz, ilahi ve yorulmaz bir dengeye oturtulduğu o altın mühür."),
        30: ("Amerikan Devrimi'nin kızı", "Köklere, geçmişe ve birbirinize duyulan o derin onur; ilişkinin dünyadaki gücünü ve devrimsel guccunu bu sarsılmaz aidiyetten alması.")
    },
    "Aslan": {
        1: ("Hırslarının dürtüsüyle hayati enerjisi harekete geçen bir adamın başına kan sıçraması", "İlişkide egonun ve tutkunun aniden alevlenmesi; ortak bir hedefe kilitlenip durdurulamaz bir güçle (guce) eyleme geçme uyanışı."),
        2: ("Bir kabakulak salgını", "İlişki içindeki bir krizin veya bulaşıcı bir karamsarlığın hızla yayılması tehlikesi; toksik enerjileri başkalarına bulaştırmadan izole etme sınavı."),
        3: ("Saçlarını omuzlarına dökmüş, gençlik kıyafetleri içindeki orta yaşlı bir kadın", "İlişkinin zamana ve yaşa meydan okuması; rutinin sıkıcılığından sıyrılıp, ilk günkü o taze, isyankar ve özgür ruhu yeniden kuşanma."),
        4: ("Av seferinden getirdiği ganimetlerin yanında duran resmi giyimli yaşlı adam", "Ego ve gurur sınavı! Geçmiş başarılarla veya ilişkinin sosyal statüsüyle övünme; partneri bir ganimet gibi değil, bir eş gibi görme uyarısı."),
        5: ("Derin bir kanyonun üzerinde yükselen heybetli kaya oluşumları", "Sarsılmazlık mühürü! İlişkinizin, etrafındaki tüm zamanın yıpratıcılığına ve derin krizlere rağmen dimdik, asil ve yıkılmaz bir kule gibi durması."),
        6: ("Eski moda, muhafazakar bir kadının, günümüzün modern bir kızıyla yüzleşmesi", "Geçmişin köklü değerleri ile geleceğin özgürleşme arzusunun çarpışması; ilişkide eski tabuları sevgiyle yıkarak modern bir ortak dil bulma."),
        7: ("Gece gökyüzünde ışıl ışıl parlayan takımyıldızlar", "Ruhlarınızın en karanlık zamanlarda bile evrensel bir rehberlikle (kadersel pusula) korunduğunu ve ilişkinizin ilahi bir plana hizmet ettiğini idrak etme."),
        8: ("Devrimci ideallerini yayan bir aktivist", "İlişkide bir şeyleri kökünden değiştirme ve yeniden inşa etme tutkusu; ancak bu isyanın partneri yıkmak için değil, bağı özgürleştirmek için yapılması gerekliliği."),
        9: ("Nefesleriyle parlayan cama şekil veren cam üfleyicileri", "Karmik simya! Birbirinizin ruhuna (nefes) dokunarak, başlangıçta ham olan bu bağı muazzam bir estetiğe ve kalıcı bir esere dönüştürme ustalığı."),
        10: ("Güneş ışığı tarlayı doldururken parlayan sabah çiy damlaları", "Karanlık bir dönemin ardından gelen taptaze bir ruhsal uyanış; ilişkinin her sabah yeniden, umutla ve ilahi bir iyimserlikle yıkanması."),
        11: ("Devasa bir meşe ağacının dallarından sarkan salıncakta sallanan çocuklar", "Çok köklü, korunaklı ve sarsılmaz bir güvenin (meşe ağacı) gölgesinde; ilişkinin en masum, eğlenceli ve çocuksu tarafını korkusuzca yaşama lütfu."),
        12: ("Süslü fenerlerle aydınlatılmış bir çimenlikte yetişkinlerin akşam partisi", "İlişkinin sosyal vitrininde parlama zamanı; gururla, estetikle ve dış dünyanın da onaylayıp hayran kalacağı bir uyumla sahneye çıkma."),
        13: ("Kulübesinin verandasında sallanan yaşlı bir deniz kaptanı", "Büyük fırtınaları, krizleri ve sabır testlerini atlatmış bir ilişkinin, artık deneyim ve bilgelikle geçmişe gülümseyerek baktığı o huzurlu demlenme anı."),
        14: ("Dışavurum fırsatları arayan bir insan ruhu", "Sadece kalplerde gizli kalan sevginin artık somut dünyada bir esere, bir evliliğe veya kalıcı bir ortak yaratıma dönüşme ihtiyacının patlaması."),
        15: ("Tezahürat yapan kalabalık bir caddede ilerleyen görkemli bir geçit töreni", "İlişkinin kendi krallığını ilan etmesi; gösterişli, cesur ve çevreden yüksek onay (alkış) alan asil bir kadersel zirve noktası."),
        16: ("Fırtına dindiğinde, doğanın parlak güneş ışığı altında sevinci", "Çok ağır bir krizin veya güç savaşının ardından gelen o muazzam rahatlama; gözyaşlarının yerini yıkanmış, tertemiz bir aşka bırakması."),
        17: ("Dini ilahiler söyleyen gönüllü bir kilise korosu", "Farklı seslerin (egoların) tek bir yüce amaç uğruna uyumlanması; ilişkinin dünyevi boyuttan çıkıp ruhsal bir adanmışlıkla bütünleşmesi."),
        18: ("Öğrencileri için deney yapan bir kimyager", "İlişkinin matematiğini ve kimyasını çözme zamanı! Formüllerin, elementlerin ve duyguların nasıl reaksiyon verdiğini deneyimleyerek ustalaşma."),
        19: ("Bir tekne partisi (yüzen ev)", "Bağlılığı bir pranga olarak değil, birlikte seyredilen eğlenceli ve özgür bir yolculuk olarak görme; ilişkinin sınırlarını esnetip neşeye odaklanma."),
        20: ("Güneş ritüeli yapan Zuni Kızılderilileri", "Varlığınızın ve bu muazzam aşkın kaynağına (Güneş'e/Yaradan'a) derin bir şükran duyma; egoyu sıfırlayıp ilahi güce saygıyla bağlanma."),
        21: ("Uçmaya çalışırken başları dönen ve kanat çırpan sarhoş tavuklar", "İlişkide kapasitenin ötesinde, gerçek dışı beklentilere veya abartılı egolara kapılma uyarısı; uçmaya çalışırken komik veya krizli durumlara düşme riski."),
        22: ("Görevini yerine getiren bir posta güvercini", "Sadakatin mührü! En zor şartlarda bile birbirinize verdiğiniz kadersel sözü tutma ve sevginin o kutsal mesajını hedefine ulaştırma erdemi."),
        23: ("Sirkte eyersiz ata binen bir binicinin heyecanlı kalabalığı büyülemesi", "İlişkinin tehlikeli, riskli ama bir o kadar da hipnotik durus gucu; engelleri ve kuralları hiçe sayarak cesaretle şov yapma ve başarma."),
        24: ("Fiziksel görünümünü tamamen ihmal edip ruhsal aydınlanmaya odaklanmış bir adam", "Dış dünyadaki gösterişin, egonun ve estetiğin anlamını yitirip; ilişkinin tamamen bilinçaltı, mistik ve yeraltı simyasına odaklanması."),
        25: ("Uçsuz bucaksız ve acımasız bir çölü geçen büyük bir deve", "Muazzam bir Dayaniklilik testi! İlişkinin kurak ve krizli süreçlerinde, içsel su (sevgi) rezervlerinizi kullanarak sabırla ve inatla hedefe yürüme."),
        26: ("Ağır bir fırtınanın ardından beliren gökkuşağı", "Kadersel bir söz! Çekilen acıların ve dökülen gözyaşlarının ardından evrenin ilişkinize sunduğu o ilahi umut, onarım ve şifa köprüsü."),
        27: ("Doğu gökyüzünde şafağın parıltısı", "Karanlık bir döngünün sonsuza dek kapanması; bu aşkla birlikte ruhun yeni bir bilince, umuda ve güneşe (uyanışa) gözlerini açması."),
        28: ("Büyük bir ağacın dalında cıvıldayan birçok küçük kuş", "Ortak çevrenin, dostlukların ve ufak neşelerin ilişkiyi beslemesi; ağır dramalardan uzaklaşıp basit, eğlenceli ve hareketli bir iletişime geçiş."),
        29: ("İnsan formunda yeniden doğmak üzere okyanus dalgalarından çıkan deniz kızı", "Büyük Simyasal Evrim! Bilinçsiz duyguların, kıskançlıkların (su) geride bırakılıp, ilişkinin tam idrak sahibi, olgun ve somut bir yapıya (insana) dönüşmesi."),
        30: ("Mührü açılmış (mühürsüz) bir mektup", "Mutlak şeffaflık! Sırların, maskelerin ve gizli ajandaların tamamen ortadan kalktığı; kalplerin birbirine dürüstçe, sansürsüzce okunmaya açıldığı son derece özgür bir faz.")
    },
    "Basak": {
        1: ("Bir adamın başındaki hayvan postu", "Kendi ilkel, hayvansal dürtülerini veya ham enerjini; disiplin, çalışma ve pratik zeka ile ehlileştirip üst bir formda kullanma yeteneği."),
        2: ("Geniş bir düzlükte yer alan, beyaz bir haç", "İlişkideki fedakarlığın ve hizmetin bir 'yük' değil, ilişkinin kalıcı huzurunu (kutsal yönünü) ayakta tutan temel sütun olduğunu fark etme."),
        3: ("İki melek yardıma hazır", "Birlikte en çok tıkandığınız, kusursuzlaştırmaya çalıştığınız kriz anlarında; evrenin size pratik bir çözümle, sezgisel bir yardımla kapı açması."),
        4: ("Genç bir adamın hayal gücü, gerçek bir boyuta dönüşüyor", "İlişkideki hayallerin ve uçuşan fikirlerin; çalışma, detaylara odaklanma ve pratik adımlarla somut bir esere (yuvaya/başarıya) dönüşmesi."),
        5: ("Bir adamın elinde rüya dolu bir peri masalı kitabı", "Gündelik hayatın pratikliğinde (Başak) kaybolurken, aşkın o masalsı ve ilahi kökenini (Peri masalı) unutmadan yaşama sanatı."),
        6: ("Süslemelerle dolu bir dans salonu", "Detaylarda estetik; ilişkinin gündelik düzenini kurarken, bu düzeni adeta bir sanat eseri veya bir dans gibi özenle, kusursuzca yönetme başarısı."),
        7: ("İki kadeh şarapla dolu bir masa", "Gündelik hayatın pratik koşturmacasında, durup birbirinize ayırdığınız o küçük ama nitelikli paylaşım anlarının kadersel değeri."),
        8: ("Bir kız, evcil kuşları besliyor", "İlişkideki küçük, savunmasız ve ilgiye muhtaç olan (çocuksu tarafınız, zayıf yanlarınız) parçaların şefkatle ve düzenle beslenip korunması."),
        9: ("Kendi kendini boyayan bir ressam", "İlişkiyi ve kendinizi dışarıdan bir gözle, adeta bir sanatçı titizliğiyle gözlemleyip; hataları anında revize ederek kusursuzluğa ulaşma çabası."),
        10: ("İki başlı bir adam, hayata bakıyor", "Mantık ve sezgiyi aynı anda kullanma; hem pratik işlere hem de ilişkinin gelecekteki ruhsal ihtiyaçlarına aynı anda odaklanabilme yetisi."),
        11: ("Yeni bir günün doğuşuyla parlayan, el değmemiş bir vadi", "İlişkideki eski krizlerin ve hataların, Başak'ın analitik temizliğiyle yok olması; her sabah taptaze bir başlangıç yapma temizliği."),
        12: ("Hazinesini arayan bir adam", "İlişkinin gündelik işleri (ev, iş, rutin) içinde, aslında aradığınız o büyük kadersel hazinenin (ruhsal olgunluk) saklı olduğunu fark etme."),
        13: ("Halkın önünde konuşan devlet adamı", "İlişkinin düzenini, kurallarını veya vizyonunu dış dünyaya karşı temsil etme; bir sistem/ekol gibi disiplinli ve saygın bir birliktelik."),
        14: ("Fotoğrafı çekilen bir aile albümü", "Zamanın akışına karşı duruş; ilişkinin her evresini, hatırasını ve dersini bir disiplinle kayda alıp geleceğe bir 'yaşanmışlık mirası' olarak taşıma."),
        15: ("Oyuncak bebeklerle oynayan bir kız çocuğu", "İlişkideki sorumlulukları, rolleri ve krizleri, bir oyun ciddiyetiyle; yargılamadan, suçlamadan, adeta bir simülasyon gibi deneyimleyerek çözme."),
        16: ("Volkanik patlamanın ardından oluşan verimli topraklar", "En büyük krizlerin (patlama), aslında Başak'ın analiz gücüyle işlendiğinde ilişkinizi gelecekte besleyecek en bereketli toprakları (tecrübe) oluşturması."),
        17: ("Halkı için dua eden bir din adamı", "İlişkideki gündelik hizmetin bir ibadete dönüşmesi; birbirinizin eksiklerini kapatmanın veya düzeni kurmanın, aslında birbirinizin ruhunu kutsamak olduğu bilinci."),
        18: ("Büyük bir kütüphanede çalışan araştırmacı", "İlişkinin kadersel kodlarını çözme arzusu; birbirinizin geçmişini, psikolojisini ve bu ilişkinin 'neden' var olduğunu bilimsel/analitik bir titizlikle araştırma."),
        19: ("Çiçek açmış bir nar ağacı", "Pratik ve sade görünümün altında, çok sayıda bereketli tohumun ve hayat enerjisinin saklı olduğu; ilişkinin potansiyelinin taşması."),
        20: ("Tarlasında hasat yapan bir köylü", "Emek verilen, planlanan ve ilmek ilmek işlenen her türlü kadersel çalışmanın, tam vaktinde ve bollukla karşılığını alma günü."),
        21: ("Kızlar basketbol takımı", "Ortak bir hedef uğruna koordineli çalışma; herkesin kendi rolünü kusursuz yaptığı, ego çatışması olmayan, tıkır tıkır işleyen bir ekip olma hali."),
        22: ("Kraliyet armasını taşıyan bir kraliyet muhafızı", "Sarsılmaz sadakat ve sistem koruyuculuğu; ilişkinin değerlerini, düzenini ve özel dünyasını dış tehlikelere karşı çelik bir disiplinle muhafaza etme."),
        23: ("Bir hayvanat bahçesinde kafes temizleyen bir adam", "İlişkideki vahşi, kontrolsüz veya hayvansal içgüdülerin; titiz bir temizlik ve disiplinle, sisteme zarar vermeyecek şekilde evcilleştirilmesi."),
        24: ("Büyük bir sarayın kapısında bekleyen gardiyan", "İlişkinin 'Kutsal Yuvaya' giriş ve çıkışlarını kontrol etme; kimlerin (veya hangi enerjilerin) bu alana dahil olup olmayacağına dair katı ve güvenli sınırlar."),
        25: ("Bahçesindeki otları temizleyen bir adam", "İlişkinin ruhsal topraklarını 'yabani otlardan' (toksik düşünceler, vesveseler) arındırma; bağı sadece saf ve işlevsel olanla besleme."),
        26: ("Bir ağaca asılı, henüz olgunlaşmamış meyveler", "İlişkinin planlarının veya hayallerinin henüz zamanının gelmediği; acele etmeden, sabırla ve düzenle olgunlaşmasını (hasadını) bekleme disiplini."),
        27: ("Güneş ışığıyla parlayan bir çaydanlık", "İlişkinin gündelik rutinini (çay/ritüel) kutsallaştırma; sıradan bir çay anını bile muazzam bir huzur ve şifa anına dönüştürme ustalığı."),
        28: ("Kel başını öne eğmiş bir keşiş", "İlişkide egonun tamamen geri çekilmesi; zihinsel kibrin yerini, sessiz bir hizmetin ve derin bir tevazunun alması."),
        29: ("Gizli bir kapıdan çıkan bir insan", "İlişkideki sorunları, krizleri ve tıkanıklıkları, kimsenin fark etmediği pratik, dahice ve gizli bir çıkış yoluyla (yöntemle) aşabilme."),
        30: ("Gökyüzünü süpüren bir yıldız süpürgesi", "İlişkinin kadersel arınması! Artık Başak'ın detaycı disiplini, gökyüzündeki kadersel tozları ve karmik tortuları bile temizleyerek, bağı kristal kadar berrak bir hale getirmiştir.")
    },
    "Terazi": {
        1: ("Bir kelebek kanadının üzerinde, üzerinde bir ok olan bir ok işareti", "İlişkideki duygusal veya zihinsel yönelimin (ok) belirlenmesi; aranızdaki etkileşimin hangi kadersel hedefe doğru uçtuğunu idrak etme."),
        2: ("Bir adamın elinde bulunan altı parıltılı ışık küresi", "İlişkinin yaşamın temel güçlerini (ışık kürelerini) dengede tutma ve bu güçleri ortak bir estetikle yönetebilme yetisi."),
        3: ("Şafak vakti ormanda yeni doğan bir gün", "Geçmişin tüm ağırlıklarını silen taze bir başlangıç; ilişkinin her yeni güne, temiz bir sayfayla ve umutla başlama disiplini."),
        4: ("Bir gruptan ayrılarak kendi yoluna giden bir adam", "İlişkide 'biz' olurken bireysel özgürlüğünü ve özgün karakterini koruyabilme; bağımlı değil, bağlı olma sanatı."),
        5: ("İçinde bir içki kadehi olan parlak bir halka", "Birlikteliğin getirdiği o kutsal, içsel bütünlük; birbirinizi 'tamamlanmış bir halka' gibi sarıp sarmalama ve bu bağın tadını çıkarma."),
        6: ("İçinde bir adamın figürü olan küçük bir heykel", "Birbirinizin hayatında kalıcı, asil ve estetik bir iz bırakma; ilişkinin dünyada somut bir sanat eseri gibi hatırlanması."),
        7: ("Fırtına öncesi sessizce duran bir gökyüzü", "Krizlerden önceki o kritik, sessiz ve dingin gözlem anı; yaklaşan kadersel değişimi, tartışmadan, sadece sezgisel olarak hissedip önlem alma."),
        8: ("Bir şöminenin başında ısınan bir grup insan", "En soğuk krizlerde bile ilişkinin iç sıcaklığını, güvenini ve yuva olma özelliğini, birbirinizin varlığıyla diri tutma yeteneği."),
        9: ("Üç usta sanatçı kendi atölyelerinde çalışıyor", "İlişkinin ortak vizyonu için her iki tarafın da kendi yeteneklerini, zekasını ve emeğini bağımsızca ama uyum içinde üretmesi."),
        10: ("Kano yapan bir grup insan", "İlişkinin akışında, herkesin aynı ritimle kürek çekmesi; çatışmaları dindirip, tek bir kadersel yöne doğru (hedefe) senkronize hareket etme."),
        11: ("Gözlerinde bir ışık olan bir adam", "İçsel aydınlanma! İlişkideki sorunları, karşıdakinin niyetini ve evrensel mesajı, görünür olandan çok daha derin bir vizyonla görme."),
        12: ("Madenden yeni çıkarılmış bir elmas", "İlişkinin ham ve işlenmemiş potansiyelinin, zorluklarla parlatılarak gerçek, paha biçilemez ve dayanıklı bir değer haline gelmesi."),
        13: ("Şapkasını çıkarmış, güneşin altında duran bir adam", "Egoların tamamen aradan çekilmesi; birbirinize ve kadersel rotanıza karşı o derin, maskesiz ve tevazulu teslimiyet."),
        14: ("Gökyüzünde birbirine doğru koşan iki melek", "İlişkinin ilahi bir el tarafından desteklendiği o anlar; krizlerin, tesadüf gibi görünen mucizevi yardımlarla çözüme kavuşması."),
        15: ("Bir yuvada toplanmış olan kuş yavruları", "İlişkinin en savunmasız, en çocuksu ve en korunmaya muhtaç olduğu o evre; birbirinizin içindeki 'çocuğu' sarmalayıp güvenle büyütme."),
        16: ("Bir adamın elinde tuttuğu bir pusula", "İlişkinin kadersel rotasını sapmadan, evrensel pusulaya (vicdan ve hakikat) uygun şekilde çizme becerisi."),
        17: ("Sık ağaçlıklı bir ormanda kaybolmuş bir adam", "İlişkide karmaşa ve belirsizlik dönemi! Dış dünyadan (başkalarının fikirleri) etkilenip kendi kadersel merkezinden sapma riski."),
        18: ("Eski bir kalenin surlarına asılı boş bir zırh", "Geçmişin savunma mekanizmalarının artık gereksizleşmesi; birbirinize karşı savunmasız (maskesiz) kalabilme cesareti."),
        19: ("Bir grup insan bir sanat eserini inceliyor", "İlişkinin dışarıya nasıl göründüğüne dair farkındalık; ilişkinin değerini, estetiğini ve başarısını objektif bir şekilde değerlendirme."),
        20: ("Tüm çiçeklerin açtığı bir mevsim", "İlişkide yaratıcılığın, aşkın ve paylaşımın zirvesi; her şeyin tıkır tıkır işlediği, güzelliklerin ve bereketin taşma noktası."),
        21: ("Bir fırtınanın ortasında dimdik duran bir çam ağacı", "En sarsıcı dış etkilerde bile, birbirinize olan bağınızın esnemesi ama asla kırılmaması; köklerinizin sarsılmaz gücü."),
        22: ("Bir tepenin zirvesinde yanan kutsal bir ateş", "İlişkinin kadersel amacının, herkesin görebileceği kadar net ve yüksek olması; ortak bir inançla dünyayı ısıtma gücü."),
        23: ("Bir aynada kendini izleyen bir kedi", "İlişkideki 'ben' ve 'sen' ayrımının netleşmesi; partnerinizin gözlerinde kendi kusurlarınızı ve güzelliklerinizi görebilme farkındalığı."),
        24: ("Bir adamın elinde bulunan eski bir anahtar", "İlişkinin kilitli olan tüm kadersel kapılarını açacak o çok özel, kadim bilgeliğe veya yönteme erişme (FBST'nin kendi anahtarı)."),
        25: ("Gökyüzünde süzülen bir kartal", "İlişkinin dünyevi dertlerin çok üzerine çıkması; perspektif, uzak görüşlülük ve kadersel bütünlüğü yukarıdan bir tanrısal bakışla görme."),
        26: ("Bir kartalın pençelerinde bir yılan", "Krizin, manipülasyonun veya korkunun (yılan), ilişkinin en yüksek vizyonu (kartal) tarafından etkisiz hale getirilip şifaya dönüştürülmesi."),
        27: ("Bir bahçede oynayan çocukların kahkahaları", "Ciddiyetin ve sorumlulukların arasında, ilişkinin o en saf, en neşeli ve çocuksu neşesini koruma zorunluluğu; mutluluk bir seçimdir."),
        28: ("Bir adamın büyük bir titizlikle kütüphane raflarını düzenlemesi", "İlişkinin geçmişini, anılarını ve öğrendiği dersleri zihinsel bir düzene oturtma; hatıraların birikim (bilgelik) olarak tutulması."),
        29: ("Güneşin batışında yanan ufuk çizgisi", "Bir devrin kapanışı! Artık ilişkinin bir aşamasının bitip, yeni ve bambaşka bir seviyeye geçmeden önceki o büyüleyici geçiş aralığı."),
        30: ("Dünya sahnesinde rolünü oynayan bir oyuncu", "İlişkinin evrensel tiyatrodaki kadersel görevi; herkesin bir rolü olduğu gibi, sizin ilişkinizin de dünyada 'temsil ettiği' o ilahi mesajı dürüstçe oynama.")
    },
    "Akrep": {
        1: ("Gece yarısı gökyüzünde parlayan, gözetleyen bir göz", "İlişkinin her anının evrensel bir gözlem altında olduğu; sadakatin ve niyetin en derin katmanlarda test edildiği o uyanık duruş."),
        2: ("Kırık bir şişeden sızan esansın kokusu", "Geçmişten gelen bir acının veya bastırılmış bir duygunun serbest kalarak ilişkinin havasını tamamen değiştirmesi; şifalanma sürecinin başlangıcı."),
        3: ("Evcilleştirilmeye çalışılan vahşi bir ev kedisi", "İlişkideki asi, kontrol edilemez ve özgür ruhlu yanların; şefkatle ve sabırla yuvaya/sisteme dahil edilme sınavı."),
        4: ("Bir mum ışığında elindeki kağıtları okuyan genç bir adam", "İlişkinin kadersel kontratlarını, gizli niyetlerini ve birbirinizin ruhsal haritasını, o karanlıkta bile net bir şekilde okuma/anlama yeteneği."),
        5: ("Kendi kendine yeten, izole bir kaya üzerindeki denizanası", "Kriz anlarında bile dışarıdan destek almadan, ilişkinin kendi içsel dayanıklılığıyla ve kendi kendine yetebilme gücüyle ayakta kalması."),
        6: ("Altın bir madeninde çalışan işçiler", "İlişkinin zorluklarını (toprağı) kazarak, birbirinizin karakterindeki o saklı, paha biçilemez ve asil hazineleri (altınları) gün yüzüne çıkarma çabası."),
        7: ("Derin gölün üzerindeki bir dalgıç", "Duyguların o karanlık ve tekinsiz derinliklerine korkusuzca dalıp, orada saklanan kadersel gizemleri (veya yaraları) birbiriniz için gün yüzüne çıkarma."),
        8: ("Ay'ın ışığını yansıtan bir göl", "İlişkinin, doğrudan güneşin parlaklığıyla değil, geceye özgü o yumuşak, mistik ve sezgisel bir bilgelikle aydınlanması; ruhların gece konuşması."),
        9: ("Kendi yansımasını hayranlıkla izleyen bir zürafa", "İlişkideki 'ben' ve 'biz' arasındaki o ince çizgi; partnerinizin gözlerinde kendi ruhunuzun güzelliğini değil, kendi eksikliklerinizi de görebilme cesareti."),
        10: ("Büyük bir kaza sonrasında kurtarılan bir grup insan", "Büyük kadersel krizlerden sağ çıkma mucizesi; ilişkinin yıkılacak gibi olduğu en karanlık anlarda bile ilahi bir elle kurtarılma."),
        11: ("Bir fırtına sonrasında ağacın dalında bekleyen bir kuş", "Krizli ve fırtınalı süreçlerden sonra gelen o mutlak sessizlik; korkunun yerini alan, artık güvende olduğunuz o huzurlu bekleme anı."),
        12: ("Büyük bir kütüphanede yasaklı kitapları arayan bir öğrenci", "İlişkinin tabu olan, konuşulmayan veya derinlerde saklanan o 'yasak' duygularını cesaretle ortaya çıkarıp yüzleşme arzusu."),
        13: ("Fırtınada limana sığınan dev bir gemi", "Dış dünyanın krizleri ve toplumsal baskılar karşısında, ilişkinin kendi içindeki o sarsılmaz ve güvenli limana (birbirinize) sığınıp korunma gücü."),
        14: ("Bir insanın içindeki derin tutku ormanları", "İlişkinin o tarif edilemez, kontrol edilemez ve vahşi tutku enerjisi; bu ateşi birbirinizi yakmak yerine birlikte dünyayı fethetmek için kullanma."),
        15: ("Yeniden doğuşu kutlayan bir kabile", "Büyük bir yıkımın veya ayrılık korkusunun ardından, ilişkinin küllerinden çok daha güçlü, bilge ve mühürlü bir şekilde yeniden doğması."),
        16: ("Bir çayırda kendi başına dans eden bir kız", "İlişkide, partnerinizin dünyasından bağımsız olarak kendi ruhsal neşenizi koruyabilme; aşkta bağımsız ama birleşik kalabilme becerisi."),
        17: ("Kendi kendini arayan bir sanatçı", "İlişkide partneri bir ayna olarak kullanıp, aslında kendi ruhunuzdaki eksik parçaları tamamlayarak 'bütünleşme' (individuasyon) yolculuğu."),
        18: ("Sessizce akan bir nehrin üzerindeki köprü", "Duygusal geçişler! Krizli sulardan, sarsılmaz bir mantık ve diplomasi köprüsü kurarak birbirinize ulaşabilme."),
        19: ("Kendi gölgesiyle konuşan bir adam", "İlişkide partnerinizin size yansıttığı 'karanlık' yanları yargılamadan, onları kendi gölgenizle barışmanın bir aracı olarak kullanma."),
        20: ("Törenle yakılan eski bir tapınak", "Eski inançların, bitmiş bir yaşantının veya geçmiş bir kadersel döngünün, ilişkinin selameti için büyük bir ritüelle ateşe verilip küle dönüştürülmesi."),
        21: ("Kendi iç dünyasında dev bir şehir kuran bir mimar", "İlişkinin dışarıya değil, birbirinizin ruhunun o uçsuz bucaksız, devasa ve zengin dünyasına kurduğunuz o görkemli ortak yuva."),
        22: ("Alevlerin içinden çıkan anka kuşu", "Mutlak yıkım ve diriliş! İlişkinin tamamen bitti denilen noktasında, bir mucizeyle tüm acıların şifaya dönüşüp çok daha yüce bir formda canlanması."),
        23: ("Bir tarlada yatan ölü bir karga", "Artık işlevi bitmiş olan korkuların, şüphelerin veya eski 'kara' düşüncelerin (karga) ilişkinizden sonsuza dek uzaklaşması, arınma."),
        24: ("Bir adamın elinde tuttuğu, parıldayan kutsal bir kadeh", "İlişkinin o en zorlu krizlerinden süzülüp elde edilen ruhsal iksir; mutlak sadakat ve aşkla içilen o kadersel yaşam şifası."),
        25: ("İki kutup arasında gidip gelen bir el feneri", "Duygusal uç noktalarda (sevgi ve öfke) gidip gelme; ancak her ne olursa olsun, bir el feneri gibi birbirinizin yolunu aydınlatma gayesi."),
        26: ("Bir uçurumun kenarında dimdik duran bir dağcı", "İlişkinin en uç, en tehlikeli ve en krizli noktasında bile, düşmeden, sapmadan, o asil ve sarsılmaz dengede durabilme ustalığı."),
        27: ("Gecenin karanlığını yırtan bir şimşek", "İlişkideki o çok gizli, çok saklı kalmış kadersel bir gerçeğin; beklenmedik, sarsıcı ve aydınlatıcı bir olayla tüm berraklığıyla ortaya çıkması."),
        28: ("Bir nehirde kendi kendine kaynayan sular", "İlişkinin derinlerinde biriken öfkenin veya tutkunun, dışarıdan fark edilmeden içeride fokur fokur kaynaması; patlamadan önce şifalandırma ihtiyacı."),
        29: ("Güneşin doğuşunu bekleyen bir grup insan", "En karanlık kadersel döngünün sonuna gelindiği; birbirinize olan inançla, yeni ve aydınlık bir dönemin başlamasını sabırla bekleme."),
        30: ("Mükemmel bir şekilde dengelenmiş bir terazinin iki kefesi", "Akrep'in o uçsuz bucaksız krizli derinliğinden, artık mutlak bir ruhsal dengeye ve hakikate ulaşıldığı o son kadersel durak.")
    },
    "Yay": {
        1: ("Gece gökyüzünde parlayan sönük bir yıldızın aniden patlayarak nova'ya dönüşmesi", "İlişkide uzun süredir durgun olan bir potansiyelin veya vizyonun, aniden patlayarak tüm hayatınızı aydınlatan kadersel bir rehbere dönüşmesi."),
        2: ("Sıcak bir ocağın başında, elleriyle yüzünü ısıtan bir beyaz rahibe", "İlişkinin en krizli, soğuk ve belirsiz anlarında bile; sarsılmaz bir inançla, kendi ruhsal ısınızı birbirinizin varlığında bulma mucizesi."),
        3: ("İki insan, yeni bir ülkeye ilk adımı atıyor", "İlişkide keşfedilmemiş yepyeni bir boyuta geçiş; ezberlerin bozulup, sınırların aşıldığı o ilk, cesur kadersel keşif adımı."),
        4: ("Uzak bir ülkede, kendi geleneklerini sürdüren bir göçmen", "İlişkinin dış çevreye, topluma veya standartlara uyum sağlamaya çalışırken, aslında kendi köklerine ve özgün felsefesine tutunma çabası."),
        5: ("Kendi içsel ışığını takip eden bir bilge", "Dış dünyanın ne dediğine bakmadan, ilişkinin kadersel rotasını sadece aranızdaki o ortak, ilahi rehberliğe (inanca) güvenerek çizme."),
        6: ("Eski bir kilisenin kapısında dilenen bir adam", "İlişkideki inanç ve şükür sınavı; elinizde olanın değerini bilmeyip sürekli eksikliklere odaklanma tuzağından kurtulma ihtiyacı."),
        7: ("Deniz kıyısında, devasa okyanusa bakan bir adam", "İlişkinin sahip olduğu o devasa, uçsuz bucaksız kadersel potansiyeli idrak etme; küçük sorunları, okyanusun büyüklüğü içinde eritme."),
        8: ("Bir taşın üzerine oyulmuş, silinmeye yüz tutmuş bir yazı", "Geçmişten gelen bir kadersel uyarının veya kadim bir öğretinin, ilişkinizin rotasını değiştirecek bir mesajla tekrar hatırlanması."),
        9: ("Dünyayı gezen bir grup öğrenci", "İlişkinin hayatı bir 'öğrenim alanı' olarak görmesi; birlikte dünyayı gezmek, kitaplar okumak veya felsefi bir yolculuğa çıkmak en büyük ortak bağınızdır."),
        10: ("Eski bir tiyatro sahnesinde prova yapan oyuncular", "İlişkinin yaşam sahnesinde sürekli bir gelişim ve prova halinde olması; hataları dert etmeden, hayatı bir neşe ve ustalıkla sahneleme."),
        11: ("Işıklı bir fenerin, denizde yol gösterdiği bir gemi", "Karanlık, belirsiz ve fırtınalı kadersel süreçlerde, birbirinizin vizyonuyla yolunuzu bulma; aşkın bir pusula gibi netleşmesi."),
        12: ("Bayrağın üzerinde parlayan altın bir güneş", "İlişkinin başarısının ve gücünün, tamamen o ortak inanca ve ilahi vizyona adanmışlıktan gelmesi; ışıkla mühürlenmiş zafer."),
        13: ("Huzur içinde uyuyan bir aslanın başını okşayan bir çocuk", "İlişkideki en güçlü, vahşi ve kontrolsüz tarafların (Aslan), şefkatle (çocuk) ehlileştirilip sevgiyle terbiye edilmesi."),
        14: ("Gökyüzünde asılı kalmış, devasa bir piramit", "İlişkinin ilahi bir düzene, kadim bir geometriye sahip olması; tesadüflerin ötesinde, planlı ve kadersel bir yapı üzerine kurulu oluşu."),
        15: ("Toprağa tohum eken bir çiftçi", "Şu an ilişkinin gördüğü zorlukların aslında gelecekteki büyük hasadın (huzurun/başarının) hazırlığı olduğu bilinci; sabırla ekmek."),
        16: ("Denizlerin üzerinde yükselen, ışık saçan bir şehir", "İlişkinin gerçeklikten kopuk, hayali ve idealist bir ütopya kurma çabası; bu hayalleri yere indirip nasıl yaşanabilir kılacağınızın sınavı."),
        17: ("Kendi içinde dönüp duran bir derviş", "İlişkinin dış dünyadaki kargaşadan sıyrılıp, sadece kendi iç ritmi ve ortak meditasyonları ile huzur bulma; aşkın bir ibadete dönüşmesi."),
        18: ("Savaş meydanında, kılıcını bırakıp dua eden bir şövalye", "Haklı olma savaşını bırakma! İlişkinin en şiddetli krizlerinde bile, silahları (egoyu/eleştiriyi) yere bırakıp birliğe dönme bilgeliği."),
        19: ("Yüksek bir dağın zirvesinden dünyayı izlemek", "İlişkinin günlük sorunlara, basit tartışmalara ve kıskançlıklara, sanki bir dağ zirvesinden bakıyormuş gibi mesafeli, bilge ve huzurlu bir bakış atması."),
        20: ("Gökyüzüne yükselen bir füze", "İlişkinin dünyevi kısıtlamalardan tamamen kurtulup, hızla ve buyuk bir ivmeyle, hayalleri gerçekleştirmek üzere yüksek bir kadersel boyuta sıçraması."),
        21: ("Kendi kendine yeten bir keşiş", "İlişkide bağımlılıktan kurtulup, herkesin kendi manevi merkezini koruduğu; ancak birbirinin ruhunu zenginleştirdiği o asil beraberlik."),
        22: ("Bir çayırda oynayan bebekler", "İlişkinin en saf, en çıkarsız, en neşeli ve sadece 'var olmanın' tadını çıkaran o ilk kadersel evresi; sevginin en yalın hali."),
        23: ("Bir gölün üzerinde süzülen bir kuğu", "Zarafetin, asaletin ve sevginin duru güzelliği; krizli anlarda bile, ilişkinin kendi asil duruşunu ve estetiğini asla bozmaması."),
        24: ("Büyük bir kütüphanede tozlu rafları karıştıran bir adam", "İlişkinin eksik kalan kadersel bilgilerini, geçmişin tozlu hatıralarında veya kadim bir öğretide arayıp bulma zorunluluğu."),
        25: ("Yükseklerden düşen bir yıldız", "Beklenmedik bir ilahi müdahale; ilişkinin gidişatını tek bir anda değiştiren, mucizevi ve kaderi yeniden yazan o göksel işaret."),
        26: ("Bir fırtınada bayrağını dik tutan bir asker", "Kriz ne kadar büyük olursa olsun, ilişkinin ana hedefine, değerlerine ve birbirinize olan bağlılığa sadık kalma yemini."),
        27: ("Bir sanatçının kendi eserini beğenmeyip parçalaması", "Mükemmeliyetçilik sınavı! İlişkideki bazı şeyleri veya bazı yönlerinizi, daha iyisini kurmak için tamamen yıkıp sıfırdan yapma cesareti."),
        28: ("Bir bahçede açan, kışın bile solmayan kırmızı güller", "İlişkinin en imkansız şartlarda, en krizli mevsimlerde bile o 'kırmızı' (tutku ve aşk) rengini koruyup yaşamaya devam etmesi."),
        29: ("Ufukta batarken denizi yutan güneş", "Bir kadersel evrenin kapanışı; ilişkinin bildiğiniz tüm formlarının, yeni ve çok daha parlak bir şafak öncesi karanlığa gömülmesi."),
        30: ("Gökyüzünde el ele tutuşan, melek gibi iki insan", "Kadersel Mühür! İki ruhun, dünyevi rollerini bitirip, artık tamamen ilahi bir kontratla, zamansız ve mekan dışı bir aşkla ebediyen birleşmesi.")
    },
    "Oglak": {
        1: ("Hintli bir şef, kendi kabilesini yönetiyor", "İlişkinin kendi içinde hiyerarşik bir düzen kurması; ortak yaşamın sorumluluklarını, rollerini ve sınırlarını asil bir otoriteyle yönetme becerisi."),
        2: ("Üç gül penceresi, biri parçalanmış", "İlişkinin mükemmeliyetçi yapısında bir çatlak veya noksanlık! Bu kusurun, ilişkinin daha fazla 'dışarıya ışık sızdırmasına' (yeni bakış açılarına) izin vermesi."),
        3: ("İnsan ruhunun, yeni deneyimler için fiziksel bedenini terk etmesi", "İlişkinin dünyevi kısıtlamalardan, maddi yüklerden ve katı sorumluluklardan sıyrılıp, sadece ruhun yüce amaçları için birleştiği o yükselmiş faz."),
        4: ("Grup kutlaması içinde, kendi dünyasında dans eden bir adam", "İlişkide sosyal sorumlulukları (toplum/aile) yerine getirirken, aslında ruhsal olarak kendi kadersel merkezine ve partnerine sadık kalabilme."),
        5: ("Kano yapan yerliler", "Hayatın o sert ve hızlı akan krizli sularında, ilişkinin ritmini kaybetmeden, birbirinize olan güvenle (aynı ritim) hedefe doğru ilerleme."),
        6: ("Kara bir kuş, beyaz bir kuşa dönüşüyor", "Kadersel simya! İlişkideki karanlık, şüpheci veya korku dolu enerjilerin; sarsılmaz bir sadakat ve disiplinle arınıp saf, beyaz bir şifaya dönüşmesi."),
        7: ("Bir kütüphanede çalışan, çok yaşlı bir adam", "İlişkinin geçmişteki tüm tecrübeleri, yaşanmışlıkları ve kadersel dersleri; geleceğin 'imparatorluğunu' kurmak için birer bilgelik kaynağı olarak kullanma."),
        8: ("Evinde, güneşin doğuşunu izleyen bir kadın", "Her gün, her krizden sonra ilişkinin potansiyeline ve yeni bir şafağın getirdiği o temiz, düzenli, disiplinli huzura olan inancı diri tutma."),
        9: ("Cirit atan bir Kızılderili savaşçı", "İlişkideki hedeflerin, hayallerin ve ortak projelerin; keskin bir odaklanma, tam bir kararlilik ve disiplinli bir çabayla (cirit) hedefe fırlatılması."),
        10: ("Eskimiş bir elmas, yeni bir yüzeye yerleştiriliyor", "İlişkinin yıllanmış, tecrübeli ve köklü değerinin; bugünün dünyasında yeni bir statüyle, yeni bir formla tekrar parlatılarak sunulması."),
        11: ("Büyük bir sarayda, hükümdarı bekleyen bir grup insan", "İlişkinin kendi içinde kurduğu o yüksek standartlar ve otorite; dış dünyanın (veya krizlerin) bu sarsılmaz otoriteye saygı duyması."),
        12: ("Bir kuş, kendi yuvasını inşa ediyor", "En temel sorumluluk! İlişkinin her bir çöpünü, her bir detayını; sarsılmaz bir güven, emek ve uzun vadeli bir planla (yuva) örme."),
        13: ("Şarkı söyleyen bir grup insan", "İlişkinin kurallarının ve sorumluluklarının sadece bir görev değil, bir neşe ve uyum içinde (şarkı) yerine getirilmesi; disiplinin sanata dönüşmesi."),
        14: ("Büyük bir kayanın üzerinde duran bir balık", "İlişkinin, duygusal (balık) doğasını; toprağın ve disiplinin o sarsılmaz (kaya) gücüyle birleştirip, duyguları somut bir başarıya dökme."),
        15: ("Yeniden doğuşunu bekleyen bir tohum", "İlişkide kış (kriz) dönemi; her şeyin donduğu, sessizleştiği bu dönemde aslında köklerin o gizli, güçlü ve derin hazırlığı."),
        16: ("Masa başında çalışan bir muhasebeci", "İlişkinin gerçekçi muhasebesi; kim ne veriyor, kim ne alıyor, kadersel borçlar neler? Dürüst bir yüzleşme ve rasyonel düzenleme."),
        17: ("Uzak bir tepede yanan bir fener", "İlişkinin çevresine, diğer insanlara veya birbirinize; kriz anlarında sarsılmaz bir yön, güven ve istikrar (fener) olma görevi."),
        18: ("Eski bir kalenin içinden dışarıyı izleyen bir nöbetçi", "İlişkinin değerlerini ve mahremiyetini; dışarıdan gelebilecek (dedikodu, müdahale) her türlü tehlikeye karşı 7/24 koruma disiplini."),
        19: ("Kendi kendine yeten, asil bir duruş", "Partnerinize muhtaç olduğunuz için değil, birbirinizi seçtiğiniz için birliktesiniz. Ego bağımlılığından özgür, asil bir beraberlik."),
        20: ("Tüm kış boyunca yetecek erzakın depolandığı bir ambar", "İlişkinin gelecek (kriz) planlaması; birbirinize olan güvenin ve kaynakların, zor günlerde birbirinizi ayakta tutacak kadar sağlam olması."),
        21: ("Tırmanılan devasa, karlı bir dağ", "İlişkinin o en zirve, en görkemli, en zorlu kadersel hedefi; o tepeye çıkarken birbirinizin elini bırakmadan, zorluklara göğüs germe."),
        22: ("Bir fırtınada bayrağını dik tutan bir asker", "Sadakat mühürü! Kriz ne kadar büyük olursa olsun, ilişkinin ana hedefine, değerlerine ve birbirinize olan bağlılığa sadık kalma yemini."),
        23: ("Bir kütüphanede tozlu rafları karıştıran bir adam", "İlişkinin eksik kalan kadersel bilgilerini, geçmişin tozlu hatıralarında veya kadim bir öğretide arayıp bulma zorunluluğu."),
        24: ("Kutsal bir sunakta yanan sürekli ateş", "İlişkideki emeğin sürekliliği; bir günlük aşk değil, bir ömür boyu yanan o kutsal hizmet ve adanmışlık ateşi."),
        25: ("Gökyüzünde el ele tutuşan, melek gibi iki insan", "Kadersel Mühür! İki ruhun, dünyevi rollerini bitirip, artık tamamen ilahi bir kontratla, zamansız ve mekan dışı bir aşkla ebediyen birleşmesi."),
        26: ("Kendi eliyle inşa ettiği bir kulübede huzur bulan adam", "İlişkinin dış dünyadan, karmaşadan ve statü hırsından uzaklaşıp, sadece birbirinizin inşa ettiği o basit ve dürüst yuvada bulduğu huzur."),
        27: ("Bir dağın zirvesinde, elindeki meşaleyle dünyayı aydınlatan bir adam", "İlişkinin ulaştığı o bilgelik seviyesi; kendi huzurunu bulup, aynı zamanda diğer çiftlere de kadersel bir rehber/örnek olma."),
        28: ("Bir nehirde kendi kendine kaynayan sular", "Dışarıdan durgun, içeriden derin; ilişkinin o en derin kadersel tortularının, sessizce ama çok güçlü bir şekilde arınma ve dönüşüm süreci."),
        29: ("Güneşin batışında yanan ufuk çizgisi", "Bir devrin kapanışı! Artık ilişkinin bir aşamasının bitip, yeni ve bambaşka bir statüye (imparatorluğa) geçmeden önceki o geçiş aralığı."),
        30: ("Mükemmel bir şekilde dengelenmiş bir terazinin iki kefesi", "Oğlak'ın o katı, disiplinli ve dünyevi yapısından; artık mutlak bir ruhsal dengeye ve ilahi adalete ulaşıldığı son durak.")
    },
    "Kova": {
        1: ("Eski bir misyon şefinin, kabile halkına yeni vizyonlar anlatması", "İlişkide rutinin dışına çıkma; partnerinle birlikte geleceğe dair radikal, özgürlükçü ve sınırları zorlayan yeni bir ortak yaşam vizyonu oluşturma."),
        2: ("Fırtınadan sığınmış bir şemsiye; altındaki iki kişi", "Dünyanın kaosu (fırtına) dışarıdayken, ilişkinin o kendine has, bağımsız ve entelektüel sığınağında birbirinize duyduğunuz o sarsılmaz zihinsel güven."),
        3: ("Taze bir şelalenin, vadideki göle dökülmesi", "Duyguların durgunlaşmasına izin vermeyen, sürekli yenilenen, tazeleyen ve zihni diri tutan o elektrikli tutku akışı."),
        4: ("Bir rahibin, kutsal ritüel için ateş yakması", "İlişkinin günlük sıradanlığını, bir ritüele dönüştürme; aşkı sadece fiziksel değil, evrensel bir bilgi ve hizmet aracı olarak kullanma."),
        5: ("Kendi içsel sesini takip eden bir adam", "İlişkide başkalarının ne dediğine, toplumsal kalıplara değil; sadece aranızdaki o benzersiz, sıra dışı kadersel sese (içgüdüye) güvenme."),
        6: ("Beyaz bir maske takmış, sahnede rol yapan bir oyuncu", "İlişkinin sosyal maskelerle değil, tamamen dürüst bir 'benlik' ile yaşanması; rollerin bitip hakikatin konuşulmaya başlandığı faz."),
        7: ("Deniz kıyısındaki kayalıklarda güneşlenen çocuk", "Zorlukların (kayalık) içinde bile neşeyi, özgürlüğü ve o çocuksu yaratıcılığı koruyabilme; krizlerin içinde huzuru bulma yetisi."),
        8: ("Güzelce düzenlenmiş bir bahçede oturan, kıyafetleri tozlu bir adam", "İçsel zenginliğin dış görünüme veya statüye ihtiyaç duymaması; ilişkinin özünün, dışarıdan nasıl göründüğünden çok daha kıymetli olduğunun farkına varma."),
        9: ("Kuş sürüsünün, fırtınaya karşı uçması", "Engeller ne kadar büyük olursa olsun; ilişkinin o bağımsız, grup bilinciyle hareket eden ve sınırları reddeden özgür ruhuyla fırtınaya meydan okuması."),
        10: ("Gözleri bağlı bir şekilde, denge üzerinde yürüyen adam", "İlişkideki sarsılmaz güven! Partnerinizin yönettiği bir dünyada, gözleriniz kapalı bile olsa (tam teslimiyetle) o denge üzerinde yürüme kararlılığı."),
        11: ("İlham perilerinin dans ettiği bir stüdyo", "İlişkinin sadece bir birliktelik değil, ortak bir 'yaratım merkezi' olması; birlikte üreterek, yazarak veya çizerek dünyayı güzelleştirme."),
        12: ("Tüm kitapların yandığı bir kütüphaneden kurtulan tek bir sayfa", "Eski öğretilerin, geleneksel aşk kalıplarının veya yaşanmışlıkların çöküşü; arta kalan o tek, saf ve gerçek 'aşk hakikati' ile yola devam."),
        13: ("Teleskopla yıldızları izleyen bir bilim insanı", "İlişkinin dünyevi dertlerin ötesine geçip, birbirinizin hayat amacını ve kadersel rotanızı en uzak galaksilere kadar (makro vizyon) okuma arzusu."),
        14: ("Gökyüzünde süzülen renkli bir uçurtma", "İlişkinin her türlü zorlukta bile yükselme, hafifleme ve esnek kalma gücü; bağlarınızın, sizi dünyaya çivilemek yerine özgürleştirmesi."),
        15: ("Yüksek bir dağın tepesinde dikilen fener", "İlişkinin hem kendi yolunu aydınlatması hem de çevresindeki diğer çiftlere (topluma) bir özgürlük/sevgi rehberi olması."),
        16: ("İki farklı dilden şarkı söyleyen bir koro", "İlişkinin uyumu! Farklılıklardan gelen o eşsiz sesin, tek bir kadersel melodide buluşarak ortaya çıkardığı o sıra dışı zenginlik."),
        17: ("Kendi kendini eğiten bir köpek yavrusu", "İlişkide hatalardan ders çıkarma disiplini; kimsenin dışarıdan müdahalesine gerek kalmadan, kendi krizlerini kendi kendine çözen o bağımsız yapı."),
        18: ("Eski bir saatin iç çarklarını temizleyen saatçi", "Zamanın ve kadersel döngülerin kusursuz işlemesi için, ilişkinin mekanik/zihinsel aksaklıklarını büyük bir titizlikle onarma."),
        19: ("Kendi içindeki okyanusu keşfeden bir kaşif", "İlişkinin sadece fiziksel bir birliktelik değil; birbirinizin bilinçaltındaki o uçsuz bucaksız, bilinmez ve gizemli okyanusları keşfetme yolculuğu."),
        20: ("Tüm sınırları yıkan bir vizyoner", "İlişkinin, toplumun size dayattığı 'oğlan-kız', 'eş-karı' veya 'aşk' kalıplarını tamamen reddedip, kendinize has kadersel bir 'birlikte var olma' modeli kurma."),
        21: ("Kendi kendine yeten ve konuşan bir heykel", "Dış dünyanın onayına muhtaç olmayan; kendi güzelliğini, kendi değerini ve kendi sessizliğini yaratabilen asil, bireysel birliktelik."),
        22: ("Işık saçan dev bir bulut", "İlişkinin bir formdan başka bir forma geçişi; artık somut ve katı sorumluluklardan sıyrılıp, sadece saf bir enerji ve ilham alanına dönüşme."),
        23: ("Bir göletin üzerinde yansıyan dolunay", "İlişkinin dünyadaki yansımasının, gökyüzündeki kadersel planla (ay) kusursuz bir uyum içinde olması; niyet ve eylemin birleşmesi."),
        24: ("Kendi elleriyle yaptığı bir müzik aletiyle çalan müzisyen", "İlişkinin müziğinin (uyumunun) başka kimseden değil, tamamen kendi el emeğinizle, kendi kurallarınızla ve kendi enstrümanlarınızla üretilmesi."),
        25: ("Eski bir tapınağın kalıntıları arasında açan orkideler", "İlişkideki eski krizlerin ve yıkılmışlıkların, artık hayatın neşesiyle ve nadide bir güzellikle (orkide) kaplanıp iyileştirilmesi."),
        26: ("Bir adamın gözlerinde parlayan merak", "Sorgulamanın ve keşfetmenin hiç bitmemesi; ilişkinin her gün, sanki partnerinizi ilk kez görüyormuş gibi bir heyecanla keşfedilme zorunluluğu."),
        27: ("Yağmurun altında ıslanan bir çiçek", "Duygusal arınma; ilişkinin o en yoğun ve bazen sert (yağmurlu) süreçlerinde, aslında birbirinizi temizleyip ruhsal olarak daha da canlı kıldığınız gerçeği."),
        28: ("Uçsuz bucaksız bir karda, sadece kendi ayak izleri olan bir adam", "İlişkide açılan o yepyeni, kimsenin yürümediği kadersel bir yol; tamamen size ait, tamamen özgün, tamamen keşfedilmemiş bir gelecek."),
        29: ("Gökyüzünde dans eden renkli ışıklar (Kuzey ışıkları)", "İlişkinin spiritüel bir olgunluğa ermesi; aradaki bağın artık dünyevi kelimelerin ötesine geçip, adeta bir enerji şölenine dönüşmesi."),
        30: ("Dünya sahnesinde, kendine has bir yöntemle yürüyen bir adam", "İlişkinin bir 'ekol' olması; hiçbir kurala, hiçbir modaya veya hiçbir toplumsal baskıya uymadan, kendi kadersel ritminizle dünyada var olma."),
    },
    "Balik": {
        1: ("Halka açık bir pazarda sergilenen kamuya ait ticaret alanı", "İlişkinin bireysel sırlar yerine, birbirinize karşı tam bir şeffaflık ve 'ortak yaşam' alanında dürüstçe var olma sınavı."),
        2: ("Sincapların bir ağaçta birbiriyle oyun oynaması", "İlişkideki o ilk, saf ve masum neşeyi; hiçbir kadersel yük altına girmeden, sadece birbirinizin varlığından keyif alarak yaşama erdemi."),
        3: ("Taşlaşmış bir ağaç gövdesi", "İlişkinin zamanın yıkıcılığına karşı gösterdiği sarsılmaz direniş; birbirinize olan bağlılığınızın artık tarihe kazınmış kadar kalıcı bir form alması."),
        4: ("Küçük bir adada, güneşli bir gün", "İlişkinin dış dünyadan, karmaşadan ve krizlerden yalıtılmış; sadece ikinizin huzur ve ışıkla dolu o kadersel sığınağı."),
        5: ("Kendi içsel dünyasında yaşayan, gizemli bir rahip", "Partnerinizi asla tamamen 'çözemeyeceğinizi' kabul etme; birbirinizin ruhundaki o gizemli ve dokunulmaz kutsal alanlara saygı duyma."),
        6: ("Sihirli bir değneğe sahip bir büyücü", "İlişkideki krizleri veya tıkanıklıkları, rasyonel yollarla değil; ancak birbirinize olan o büyük, ilahi 'aşk büyüsüyle' (şefkatle) çözme ustalığı."),
        7: ("Deniz kıyısında, ağlarını onaran balıkçılar", "İlişkinin duygusal yorgunluklarını (ağları) dürüstçe tamir etme; birbirinizi hırpalamak yerine, yara alan kısımları sevgiyle dikip onarma."),
        8: ("İki aşığın, gün batımında sessizce oturduğu bir bank", "Hiçbir kelimeye, hiçbir eyleme ihtiyaç duymadan; sadece yan yana var olmanın verdiği o mutlak huzur ve ruhsal bütünlük."),
        9: ("Kendi ışığıyla parlayan bir denizanası", "Karanlık ve krizli kadersel süreçlerde bile; ilişkinin kendi içindeki o saf, mistik ışığı yakarak birbirinize yol gösterme yetisi."),
        10: ("Yıldızların altında dua eden bir çocuk", "İlişkinin tüm kaderini, geleceğini ve birbirinizi evrenin o sonsuz şefkatine (Yaradan'a) bırakıp, ilahi akışa mutlak güven."),
        11: ("Işık saçan, mistik bir tapınağın kapısı", "İlişkinin artık bir çift olmanın ötesinde, ilahi bir hizmete veya ortak bir ruhsal amaca hizmet eden bir mabede dönüşmesi."),
        12: ("Denizlerin üzerinde süzülen bir martı", "En büyük krizlerde bile özgürlüğü koruma; ilişkiyi bir hapishane değil, birbirinizin ruhunu gökyüzüne taşıyan bir kanat yapma."),
        13: ("Eski bir tablonun temizlenmesi", "Geçmişin (ilişkinin önceki evrelerinin) üzerine birikmiş tozları ve hayal kırıklıklarını, şefkatle temizleyip o ilk günkü canlılığına döndürme."),
        14: ("Yıldızları gözlemleyen bir astronom", "İlişkinin kadersel rotasını, gündelik dertlere değil; yıldızların (evrensel yasaların) o muazzam ve değişmez rehberliğine göre çizme."),
        15: ("Bir grup insan, bir nehirde yıkanıyor", "Duygusal arınma! İlişkinin tüm ağırlığını, öfkesini ve geçmiş tortusunu, birbirinizin şefkatli sularında (sevgi) tamamen yıkıp arındırma."),
        16: ("Bir çayırda kendi başına dans eden bir kız", "İlişkinin içinde bile, kendi ruhsal neşenizi ve bağımsızlığınızı koruyarak, aşkı bir zorunluluk değil, bir neşe kaynağı yapma."),
        17: ("Kendi gölgesiyle konuşan bilge", "İlişkide partnerinizde gördüğünüz her şeyi, aslında kendi gölgenizin bir yansıması olarak kabul edip, bu aynalıkla bütünleşme."),
        18: ("Sessizce akan nehrin üzerindeki köprü", "Duygusal geçişler; krizli sulardan, sarsılmaz bir mantık ve şefkat köprüsü kurarak birbirinize ulaşabilme."),
        19: ("Kendi iç dünyasında dev bir şehir kuran mimar", "İlişkinin dış dünyadan çok, birbirinizin ruhunun o uçsuz bucaksız, zengin ve huzurlu dünyasında var olması."),
        20: ("Alevlerin içinden çıkan anka kuşu", "Mutlak yıkım ve diriliş! İlişkinin bittiği denilen noktasında, bir mucizeyle tüm acıların şifaya dönüşüp çok daha yüce bir formda canlanması."),
        21: ("Kendi eliyle yaptığı müzik aletiyle çalan müzisyen", "İlişkinin uyumunun başka kimseden değil, tamamen kendi içinizden gelen o özel titreşimle, özgün bir şekilde üretilmesi."),
        22: ("Eski bir tapınağın kalıntıları arasında açan orkideler", "İlişkideki eski krizlerin ve yıkılmışlıkların, artık nadide bir güzellikle iyileştirilmesi."),
        23: ("Bir adamın gözlerinde parlayan merak", "Sorgulamanın ve keşfetmenin hiç bitmemesi; partnerinizi her gün yeniden keşfetme arzusu."),
        24: ("Yağmurun altında ıslanan bir çiçek", "İlişkinin o en yoğun ve bazen sert (yağmurlu) süreçlerinde, aslında birbirinizi temizleyip ruhsal olarak daha da canlı kıldığınız gerçeği."),
        25: ("Uçsuz bucaksız karda kendi ayak izleri", "İlişkide kimsenin yürümediği o özgün kadersel yol; tamamen size ait, tamamen keşfedilmemiş bir gelecek."),
        26: ("Gökyüzünde dans eden renkli ışıklar", "İlişkinin artık dünyevi kelimelerin ötesine geçip, bir enerji ve ışık şölenine dönüşmesi."),
        27: ("Dünya sahnesinde kendine has bir yöntemle yürüyen adam", "İlişkinin bir 'ekol' olması; hiçbir kurala uymadan, kendi kadersel ritminizle dünyada var olma."),
        28: ("Bir nehirde kendi kendine kaynayan sular", "Derinlerdeki duygusal fokurdama; öfkenin veya tutkunun sessiz ama güçlü bir şekilde şifaya dönüşümü."),
        29: ("Güneşin batışında yanan ufuk çizgisi", "Bir devrin kapanışı! Artık ilişkinin bildiğiniz tüm formlarının, çok daha parlak bir şafak öncesi karanlığa gömülmesi."),
        30: ("Gökyüzünde el ele tutuşan, melek gibi iki insan", "Kadersel Mühür! İki ruhun, dünyevi rollerini bitirip, artık tamamen ilahi bir kontratla, zamansız ve mekan dışı bir aşkla ebediyen birleşmesi.")
    },
}



import importlib.util as _iu

def _load_ext_dict(filename):
    """Dış Python dosyasından tek bir dict değişkeni yükler."""
    _dir = os.path.dirname(os.path.abspath(__file__))
    _path = os.path.join(_dir, filename)
    if not os.path.exists(_path):
        _path = os.path.join(os.path.dirname(_dir), filename)
    if not os.path.exists(_path):
        return {}
    _spec = _iu.spec_from_file_location("_mod_" + filename, _path)
    _mod = _iu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    for _k, _v in vars(_mod).items():
        if isinstance(_v, dict) and not _k.startswith("_"):
            return _v
    return {}

fbst_sabian_ebeveyn = _load_ext_dict("fbst_sabian_ebeveyn.py")
fbst_sabit_yildizlar_ebeveyn = _load_ext_dict("fbst_sabit_yildizlar_ebeveyn.py")
ASTEROID_SINASTRI_YORUMLARI_EBEVEYN = _load_ext_dict("ASTEROID_SINASTRI_YORUMLARI_EBEVEYN.py")
FBST_GEZEGEN_EV_COCUK = _load_ext_dict("FBST_GEZEGEN_EV_COCUK.py")
FBST_GEZEGEN_EV_EBEVEYN = _load_ext_dict("FBST_GEZEGEN_EV_EBEVEYN.py")
FBST_YORUMLAR_EBEVEYN = _load_ext_dict("FBST_YORUMLAR_EBEVEYN.py")
FBST_GELISIM_DONEMleri_EBEVEYN = _load_ext_dict("FBST_GELISIM_DONEMleri_EBEVEYN.py")
FBST_POTANSIYEL_EBEVEYN = _load_ext_dict("FBST_POTANSIYEL_EBEVEYN.py")
FBST_MESLEK_EBEVEYN = _load_ext_dict("FBST_MESLEK_EBEVEYN.py")
FBST_YORUMLAR_BURC = _load_ext_dict("FBST_YORUMLAR_BURC.py")
FBST_YORUMLAR_EV = _load_ext_dict("FBST_YORUMLAR_EV.py")
FBST_SINASTRI_OZEL = _load_ext_dict("FBST_SINASTRI_OZEL.py")

def _load_all_ext_dicts(filename):
    """Dış Python dosyasındaki TÜM dict değişkenlerini tek bir dict olarak yükler."""
    _dir = os.path.dirname(os.path.abspath(__file__))
    _path = os.path.join(_dir, filename)
    if not os.path.exists(_path):
        _path = os.path.join(os.path.dirname(_dir), filename)
    if not os.path.exists(_path):
        return {}
    _spec = _iu.spec_from_file_location("_mod_" + filename, _path)
    _mod = _iu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    result = {}
    for _k, _v in vars(_mod).items():
        if isinstance(_v, dict) and not _k.startswith("_"):
            result[_k] = _v
    return result

ARAP_EBEVEYN = _load_all_ext_dicts("ARAP_EBEVEYN_DICTS.py")
ARAP_ILISKI = _load_all_ext_dicts("ARAP_ILISKI_DICTS.py")


fbst_sabit_yildizlar = {
    "ACRAB": {
        "derece": 242.48,  # 2°29' Yay
        "yargi": "Kadersel mimarinizde 'Yıkılan Kule' etkisini taşıyan bu sarsıcı mühür, büyük maddi kazançlar ve derin ezoterik sırlar vaat ederken, ihtirasın getirebileceği krizlere karşı kesin bir uyarıdır. Elde edilen dünyevi statü ve servet, kibre dönüştüğü an kadersel bir sarsıntıyla yıkılabilir; ancak krizleri sabırla yöneten bir irade, bu enkazdan muazzam bir ruhsal ve maddi zenginlik inşa edecektir.",

        "etkiler": {
            "evlilik": {
                "Satürn": "Evlilik yoluyla elde edilen kazanç.",
                "Uranüs": "Evlilik yoluyla gelen kazanç, ancak içsel zorlukları ve yasal sorunları aşmak gerekir."
            },
            "maddi": {
                "Mars": "Para konularında olumlu ancak abartılı borçlanma riski.",
                "Merkür": "Maddi hediyeler ve sürpriz destekler.",
                "Ay": "Materyalist eğilimler, servet edinme ancak terfiler nedeniyle gelebilecek krizler."
            },
            "saglik": {
                "Genel": "Bulaşıcı hastalıklara yatkınlık veya bağışıklık testleri.",
                "Güneş": "Kötü sağlık, canlılıkta dönemsel düşüşler."
            },
            "kaza": {
                "Neptün": "Orta yaş döneminde kazalara açıklık.",
                "Uranüs": "Elektrik ve yangın risklerine karşı görünmez kadersel sorumluluk."
            },
            "zihinsel": {
                "Mars": "Son derece aktif, stratejik ve delici bir zihin.",
                "Merkür": "Donuk zihin veya iletişim/ifade kusurlarında kadersel zorlanma."
            },
            "gizlilikler": {
                "Genel": "Özellikle gizemli doğa araştırma yeteneği, derin sörf yapabilme kapasitesi."
            }
        }
    },
    
    "ALDEBARAN": {
        "derece": 69.08,  # 9°05' İkizler

        "yargi":"Zihinsel ve ahlaki dürüstlüğün kozmik mührüdür. İlişkinizde dürüstlükten ve ilkelerinizden taviz vermediğiniz sürece size eşsiz bir kadersel sağlamlık ve uyum bahşeder.",

        "etkiler": {
            "ask": {
                "Venüs": "Aşk hayatında sıra dışı anormallikler, sürprizli ve tutkulu durumlar."
            },
            "evlilik": {
                "Ay": "Son derece uyumlu, kadersel koruma kalkanına sahip evlilik.",
                "Neptün": "İçsel mutluluğun önünde görünmez engeller.",
                "Satürn": "Evlilik içinde kalıcı içsel başarı, sarsılmaz taahhüt."
            },
            "is_hayati": {
                "Ay": "İş ve ticaret konularına yüksek elverişlilik.",
                "Neptün": "Büyük şirket yöneticiliği, gizli finansal kaynaklar ve danışmanlıkta zirve.",
                "Uranüs": "İş hayatında ani ve beklenmedik değişimler, kadersel yeniden yapılanmalar."
            },
            "saglik": {
                "Genel": "Bedensel olarak enfeksiyonlara ve hastalıklara genel bir hassasiyet.",
                "Mars": "Ateşli hastalıklar ve ani iltihaplar."
            },
            "kaza": {
                "Mars": "Kesici aletler veya ateşle ilgili kaza riskleri."
            },
            "zihinsel": {
                "Genel": "Akıllı, keskin ve pratik bir bilinç.",
                "Satürn": "Geçmişi asla unutmayan, son derece güçlü bir bellek."
            }
        }
    },
    
    "ALCYONE": {
        "derece": 59.76,  # 29° Boğa
        "yargi":"Alcyone, kolektif bilincin ve ruhsal arayışın mührüdür. Eğer bu mühür aktifse, ilişkinizdeki bireysel egoların çatışması yerini, daha yüksek bir vizyona hizmet eden 'ortak bir hayale' bırakmalıdır. Yargısı şudur: Alcyone size, kişisel hırslarınızın ilişkinizi zayıflattığını, ancak bir bütünün parçası olarak hareket ettiğinizde durdurulamaz bir güç haline geleceğinizi hatırlatır. Bu mühür, 'biz' olabilmenin, bireysel ışığın kolektif bir güce dönüşmesinin mührüdür; bu süreçte yaşadığınız krizler, sizi birbirinize değil, ortak bir hakikate bağlamak içindir.",

        "etkiler": {

            "ask": {
                "Genel": "Karşı cins ile genel olarak olumsuz, yıpratıcı kadersel sınavlar."
            },
            "evlilik": {
                "Neptün": "Eşin sağlığı ile ilgili kadersel hassasiyetler ve endişeler.",
                "Uranüs": "Evlilik ortağının beklenmedik şekilde farklı bir boyut keşfetmesi."
            },
            "cinsellik": {
                "Yükselen": "Şiddetli şehvet ve bastırılması zor, tehlikeli cinsel eğilimler.",
                "Venüs": "Cinsel konularda yoğun tutku ve dönüştürücü enerjiler."
            },
            "is_hayati": {
                "Genel": "Denizaşırı bağlantılar veya büyük ticaret vasıtasıyla başarılar.",
                "Merkür": "Ticari yazışmalarda veya anlaşmalarda başarısızlık riski."
            },
            "saglik": {
                "Satürn": "Kronik rahatsızlıklar veya tümörel oluşumlara karşı risk.",
                "Güneş": "Katarakt, kafa ve boğaz bölgesi rahatsızlıkları."
            },
            "kaza": {
                "Mars": "Kafa bölgesinde kazalar.",
                "Neptün": "Sinsi ve ciddi kaza potansiyelleri."
            },
            "arkadaslar": {
                "Neptün": "Arkadaşlardan ve kolektiften gelen gizli/kadersel yardımlar."
            },
            "zihinsel": {
                "Uranüs": "Son derece aktif, isyankar ve elektrikli bir zihin yapısı."
            }
        }
    },
    
    "ALFARD": {
        "derece": 147.17,  # 27° Aslan
        "yargi":"Alfard, arzunun karanlık derinliklerini ve bu derinliklerde kaybolma riskini temsil eden bir mühürdür. Eğer bu mühür aktifse, ilişkinizdeki tutkular birer kurtarıcı değil, zaman zaman sizi kendinize yabancılaştıran birer 'duygusal bataklık' gibi hissettirebilir. Yargısı şudur: Alfard size, sevginin sadece 'sahip olmak' olmadığını, gerçek sevginin bağımlılıklardan arınmış bir özgürlük olduğunu öğretmek için gelir. İlişkinizdeki acılar birer ceza değil, ruhunuzun o tutkulu ama dar kalıbından çıkması için gereken birer 'duygusal temizlik' evresidir; bu süreci şuurla geçtiğinizde, sevginin en saf haline ulaşırsınız." ,

        "etkiler": {
            "ask": {
                "Jüpiter": "İlişkilerde geç kalmışlık, dulluk veya derin bir yalnızlık teması.",
                "Merkür": "Kişinin hayatının seyrini tamamen değiştirecek acılı ve tehlikeli tutkular.",
                "Venüs": "Yakın çevreyle uyumsuz olan, gizli ve sıra dışı ilişkilere çekilme."
            },
            "evlilik": {
                "Merkür": "İletişim kopukluğuna dayalı uyumsuz evlilik.",
                "Ay": "Eşin veya annenin sağlığıyla ilgili kadersel krizler ve sınavlar."
            },
            "cinsellik": {
                "Genel": "Cinsellikte aşırı duygusallık ve sınır deneme potansiyeli."
            },
            "saglik": {
                "Mars": "Kadersel kayıplar (Düşük, ani ve ölümcül sağlık krizleri)."
            },
            "kaza": {
                "Mars": "Çok ciddi ve geri dönülemez kaza ihtimalleri."
            },
            "gizlilikler": {
                "Satürn": "Kısa süreli, gizli ve sonunda keder getiren yasak aşklar."
            }
        }
    },

    "AGENA": {
        "derece": 233.80,  # 23° Akrep
        "yargi":"Agena, kadersel bir 'hizmet' sınavının mührüdür. Eğer bu mühür aktifse, ilişkinizdeki veya yaşamınızdaki başarılarınız sadece kişisel tatmin için değil, çevrenize yayacağınız şifa ve bilgelik için tasarlanmıştır. Yargısı şudur: Otoriteyi bir baskı aracı olarak değil, bir sorumluluk bilinciyle kullandığınızda, kadersel rotanızdaki engeller kendiliğinden açılacaktır. Kendinizi kolektif bir iyiliğin parçası olarak gördüğünüzde, Agena size fiziksel güçle ruhsal derinliği birleştiren sarsılmaz bir başarı vadeder." ,

        "etkiler": {
            "evlilik": {
                "Satürn": "Kıskançlık yüzünden iç uyumun tamamen bozulması riski.",
                "Uranüs": "İç uyumsuzluk ve ani kopuş titreşimleri."
            },
            "ask": {
                "Genel": "Tutkuların yönlendirdiği, kadersel derinliği olan etkileşimler."
            },
            "cinsellik": {
                "Genel": "Cinsellikte yoğun enerji ve deneyim arayışı.",
                "Venüs": "Duygusallığın cinsellikte sesle ve yoğun bir tutkuyla ifadesi."
            },
            "maddi": {
                "Merkür": "Maddi kazanç ve zihinsel projelerden gelen kadersel ödüller.",
                "Güneş": "Toplumsal başarı ve parlama."
            },
            "is_hayati": {
                "Neptün": "Yetersiz yöneticilik veya başarıda görünmez engellerle karşılaşma."
            },
            "saglik": {
                "Genel": "Zehirlenmelere karşı hassasiyet.",
                "Mars": "Büyük fiziksel güç ve dayanıklılık potansiyeli."
            },
            "kaza": {
                "Neptün": "Dikkatsizlik veya dalgınlık sonucu gelen kazalar."
            },
            "zihinsel": {
                "Jüpiter": "Aydın, vizyoner ve bilge bir zihin.",
                "Mars": "Büyük zihinsel güçler, stratejik düşünme."
            },
            "arkadaslar": {
                "Genel": "Geniş ve etkili bir çevre, arkadaşlardan gelen dönemsel faydalar."
            }
        }
    },
    "SPICA": {
        "derece": 204.00,  # 24°00' Terazi
        "yargi":"Zodyak'ın en şanslı dokunuşlarından biridir. Bu mühür, ilahi bilginin, zarafetin ve sanatsal yeteneğin size sınırsız bir kadersel bereket ve ruhsal bütünleşme getireceğini simgeler." ,

        "etkiler": {
            "maddi": {
                "Genel": "Zenginlik, başarı ve çok konforlu bir çevrede yaşama lütfu.",
                "Neptün": "Her zaman tatmin edici ve akışı kesilmeyen kazanç."
            },
            "evlilik": {
                "Neptün": "Uyumlu, ruh eşi hissi veren kadersel evlilik.",
                "Uranüs": "Evlilik yoluyla aniden elde edilen kazanç ve sınıf atlama."
            },
            "zihinsel": {
                "Merkür": "Müthiş zeki, yetenekli ve sanatsal olarak marifetli bir akıl."
            },
            "saglik": {
                "Satürn": "İyi, kalıcı ve sağlam bir fiziksel temel."
            }
        }
    },

    "VEGA": {
        "derece": 285.26,  # 15° Oğlak
        "yargi":"Vega, kadersel rotanızda 'sanatsal deha'nın ve ruhsal zarafetin mührüdür. Eğer bu mühür aktifse, ilişkinizdeki her türlü zorluğun üstesinden sadece mantıkla değil, estetik bir zekayla ve ruhsal bir incelikle gelebilirsiniz. Yargısı şudur: Vega, size dünyevi olanın ötesine geçme yeteneği sunar. Maddi kazanımlarınızın kalıcı olması, ilişkinizdeki sanatın ve estetiğin korunmasına bağlıdır. Bu mühür, 'saf ışığın' temsilcisidir; bu nedenle ruhunuzdaki ışığı karartacak her türlü hesaplı ve kirli oyun, ilişkinizdeki kadersel korumayı anında geri çeker." ,

        "etkiler": {
            "evlilik": {
                "Neptün": "Evliliğin veya evin ikiye bölünmesi tehlikesi.",
                "Satürn": "Gecikmiş içsel sorunlar ve soğukluk.",
                "Uranüs": "Beklenmedik içsel kederler ve kopuşlar."
            },
            "maddi": {
                "Jüpiter": "Maddi kazanca elverişlilik, ancak kibrin getirebileceği servet kaybı.",
                "Ay": "Rant, gayrimenkul veya emeklilik yoluyla düzenli kazanç.",
                "Uranüs": "Çok hızlı para kazanıp aynı hızda kaybetme (Materyalist aşırılık)."
            },
            "cinsellik": {
                "Genel": "Genellikle gizli ve yoğun şehvetlilik."
            }
        }
    },

"ANTARES": {
        "derece": 249.76,  # 9°46' Yay
        "yargi":"İlişkinizde ve hayatınızda büyük güç savaşlarını, stratejik dönemeçleri temsil eder. Yıkıcı rekabeti bırakıp gücünüzü inşaya yönlendirirseniz, kadersel bir zafer kazanırsınız." ,

        "etkiler": {
            "maddi": {
                "Genel": "Stratejik davranıldığında büyük servet, komutanlık ve ticari onur.",
                "Uranüs": "Beklenmedik finansal krizler ve spekülasyon zararları."
            },
            "ask": {
                "Ay": "İlişki dinamiğinde nüfuzlu, güçlü ve kadersel arkadaşların desteği."
            },
            "evlilik": {
                "Genel": "İlişkide kibir ve güç savaşları dengelenmezse, en yüksekten ani düşüş ve yıkım riski."
            },
            "is_hayati": {
                "Ay": "İş konularında elverişlilik ve dayanıklılık."
            },
            "arkadaslar": {
                "Ay": "Çok güçlü ve etkin çevrenin koruyucu kalkanı."
            }
        }
    },

    "REGULUS": {
        "derece": 149.83,  # 29°50' Aslan
        "yargi":"Kadersel mimaride kraliyet tacını temsil eder. Bu mühür size büyük bir itibar ve koruma vadeder; ancak intikamdan ve kibirden uzak durduğunuz sürece bu tahtta kalabilirsiniz." ,

        "etkiler": {
            "maddi": {
                "Genel": "KRALİYET YILDIZI; muazzam bir servet, yüksek itibar ve görünürlük.",
                "Satürn": "Sorumluluk bilinciyle korunduğu takdirde kalıcı, köklü zenginlik."
            },
            "ask": {
                "Venüs": "Şiddet içeren, yoğun tutkulu bağlılıklar veya krizli, büyük aşk maceraları."
            },
            "evlilik": {
                "Genel": "Güçlü, nüfuzlu çevrelerin ve kadersel dostların koruması altında, adeta 'kraliyet' tarzı bir birliktelik."
            },
            "arkadaslar": {
                "Güneş": "Arkadaşlar üzerinde büyük bir etki, liderlik ve komutanlık gücü.",
                "Uranüs": "İleri zamanda aniden düşman olan, rekabete giren eski arkadaşlar."
            }
        }
    },

    "SIRIUS": {
        "derece": 104.08,  # 14°05' Yengeç
        "yargi":"Evrensel şansın ve ilahi lütufların mührüdür. Bu hizalanma, attığınız adımların ardında büyük bir kadersel koruma ve bereket olduğunu, ruhsal bir sıçrama yaşayacağınızı müjdeler." ,

        "etkiler": {
            "maddi": {
                "Genel": "Kolektiften gelen devasa zenginlik, itibar ve kadersel lütuflar.",
                "Jüpiter": "Finansal genişleme, her zaman talihli ve bereketli bir akar hattı."
            },
            "cinsellik": {
                "Genel": "Çok güçlü bir cinsel şevk, bitmek bilmeyen yüksek yaşam enerjisi ve manyetik karizma."
            },
            "evlilik": {
                "Genel": "Toplumsal mevkisi yüksek, saygın ve koruyucu ortaklıklar kurma meyli."
            },
            "saglik": {
                "Ay": "Çok dayanıklı ve iyi bir sağlık genetiği."
            },
            "is_hayati": {
                "Neptün": "Kurumlarda, bankalarda ve büyük organizasyonlarda müthiş iş takibi ve başarı."
            }
        }
    },

    "ALGOL": {
        "derece": 56.17,  # 26°10' Boğa
        "yargi":"Kadersel navigasyonda en keskin virajlardan biridir. Kendi karanlığınızla veya dış dünyanın yıkıcı tutkularıyla yüzleştiğiniz bu evrede, öfkeyi bilgeliğe dönüştürmek en büyük sınavınızdır." ,

        "etkiler": {
            "ask": {
                "Genel": "Tutkuların kontrolden çıkmasıyla gelen ağır kadersel hayal kırıklıkları.",
                "Mars": "Karşı cinsle olan ilişkilerde yıkıcı krizler ve ani yol ayrımları."
            },
            "evlilik": {
                "Genel": "İlişki içinde ego krizlerinin, öfkenin ve inatçılığın evliliğin dengesini sarsma riski."
            },
            "maddi": {
                "Genel": "Büyük kazançlar elde etme hırsı ve gücü; ancak etik kurallar aşılırsa ani finansal kayıplar riski."
            }
        }
    },

    "SCHEAT": {
        "derece": 359.36,  # 29° Balık (yaklaşık)
        "yargi": "Scheat, kadersel rotanızda 'beklenmedik olanın' mührüdür. Eğer bu mühür aktifse, hayatınızda veya ilişkinizde kontrolünüz dışında gelişen ani olaylar, sizi konfor alanınızdan çıkarmak için tasarlanmış birer 'uyanış sarsıntısı'dır. Yargısı şudur: Scheat, sizi belirsizliğe hazırlar. Planlarınızın altüst olması bir başarısızlık değil, kadersel bir revizyondur. Bu türbülanslarda dik durmayı ve esnemeyi başardığınızda, normal bir rotada asla ulaşamayacağınız o derin bilgelik zirvesine ulaşacaksınız.",
        "etkiler": {
            "ask": {
                "Jüpiter": "Kadersel kayıplar ve hayal kırıklıklarıyla gelen ruhsal arınma.",
                "Ay": "Duygusal eleştiri krizleri ve partnerin beklentileriyle yüzleşme."
            },
            "evlilik": {
                "Genel": "Geçmişten gelen travmaların evliliğe yansıması, kadersel sınavlar."
            },
            "kaza": {
                "Mars": "Beklenmedik kazalar, dikkatsizlik kaynaklı olaylar.",
                "Merkür": "Özellikle su ve seyahatle ilgili, başta olmak üzere kadersel aksilikler."
            },
            "zihinsel": {
                "Uranüs": "Konsantrasyon düşüklüğü ancak anlık, parlak sezgiler."
            }
        }
    },

    "DENEB_ALGEDI": {
        "derece": 323.53,  # 23° Kova (yaklaşık)
        "yargi": "Deneb Algedi, gökyüzünün kadersel terazisinin kefesidir. Eğer bu mühür aktifse, ilişkinizdeki her eylem, söz ve niyet, evrensel bir kayıt sistemine işleniyor demektir. Yargısı şudur: Bu mühür size ne ceza ne de ödül verir; sadece 'adalet' getirir. İlişkinizde dürüstlük ve sadakat temelini inşa ettiyseniz, bu mühür size sarsılmaz bir yuva ve uzun ömürlü bir huzur bahşeder. Ancak sömürü, yalan veya haksızlık üzerine bir yapı kurduysanız, bu kadersel durak, ilişkinizdeki o yapının doğal bir sonuçla (hasatla) çözülmesini sağlar. Burada sınav, sorumluluk almanın onurudur.",
        "etkiler": {
            "ask": {
                "Jüpiter": "Beklentilerin gerçekle çarpışması, yüzeysel duygulardan arınma sınavı.",
                "Genel": "İlişkide ahlaki sorumluluk ve kadersel ciddiyet arayışı."
            },
            "evlilik": {
                "Genel": "Sadakat temelli köklü bir yuva inşası, karşılıklı sözleşmelere dayalı güven."
            },
            "maddi": {
                "Genel": "Hak edilenin (ne eksik ne fazla) alınacağı kadersel bir finansal döngü."
            }
        }
    },

    "UNUKALHAI": {
        "derece": 232.07,  # 22° Akrep (yaklaşık)
        "yargi": "Unukalhai, yılanın deri değiştirmesi gibi, kadersel bir arınmanın ve gölgelerle yüzleşmenin mührüdür. Eğer bu mühür aktifse, ilişkinizdeki mevcut krizler veya zorlanmalar, eski ve artık işlevini yitirmiş kalıplarınızdan kurtulmanız için birer 'kabuk değiştirme' davetidir. Yargısı şudur: Gölgenizden kaçtığınız sürece krizler sizi kovalar; ancak gölgenizi (ilişkinizdeki bastırılmış korkuları) kabul edip şifalandırdığınızda, aradığınız o derin güç ve kozmik bütünleşmeye ulaşırsınız. Buradaki sınav, 'görünür olan' ile 'gölgede kalan' arasındaki dengedir.",
        "etkiler": {
            "evlilik": {
                "Uranüs": "Yıpratıcı ve ani değişimler getiren evlilikler.", 
                "Venüs": "İlişkide mülkiyetçilik, kıskançlık ve yoğun manipülasyon krizleri."
            },
            "ask": {
                "Neptün": "Kadersel karmaşalar, bulanık sınırlarla gelen ruhsal sınavlar.",
                "Genel": "İlişkide derin bir tutku arayışı, ancak bu tutkunun karanlık tarafıyla (tutku-takıntı dengesi) yüzleşme."
            },
            "cinsellik": {
                "Genel": "Sınırları zorlama, alışılmışın dışında, dönüşümsel cinsel enerjiler."
            },
            "maddi": {
                "Uranüs": "Lüks ortamlara çekilme ve bu ortamların getirdiği kadersel sorumluluklar."
            }
        }
    },


    "PROCYON": {
        "derece": 115.82,  # 25°49' Yengeç
        "yargi": "İlişkinizde bastırılamaz tutku ve iletişim krizleri arasında gidip gelen bir enerji hattı oluşuyor. Bu kadersel mühür, fevri kararlar yerine zihinsel bir diplomasi geliştirmeniz gerektiğinin kesin bir uyarısıdır." ,

        "etkiler": {
            "ask": {
                "Merkür": "Karşı cinsle zihinsel boyutta ve fikirsel anlamda yaşanan kadersel uyum sorunları."
            },
            "cinsellik": {
                "Yükselen": "Yoğun çekim gücü ve karşı tarafı derinden etkileyen manyetik bir enerji."
            },
            "saglik": {
                "Genel": "Sıvılardan, zehirlerden veya ani gelişen enfeksiyonlardan gelebilecek kadersel hassasiyetler."
            },
            "kaza": {
                "Genel": "Ani ve beklenmedik tehlikelere karşı fevri hareket etmekten doğan riskler."
            }
        }
    },

    "SABIK": {
        "derece": 257.97,  # 17°58' Yay
        "yargi":"Kadersel rotanızda aşk, gizli rekabetler ve geç gelen başarılarla sınanacağınız bir kavşaktasınız. Bu mühür, kalıcı zaferlerin ancak sabır ve ahlaki disiplinle kazanılabileceğini gösterir." ,

        "etkiler": {
            "ask": {
                "Mars": "Karşı cinsle olan ilişkilerde bitmek bilmeyen rekabet, sorunlar ve geçimsizlik.",
                "Neptün": "Karşı cinsle kadersel olarak çok olumlu, derin ve favori ilişkiler içine çekilme.",
                "Satürn": "Aşk hayatında kalıcı sorumluluklar, soğukluk, sorun ve hayal kırıklığı."
            },
            "cinsellik": {
                "Genel": "Tutkulu ve yoğun cinsel enerjiler, farklı deneyimlere açıklık."
            },
            "maddi": {
                "Jüpiter": "Yüksek ve kalıcı maddi başarı.",
                "Ay": "Mesleki olarak başarılı olmak ancak bunun zenginliğe dönüşmemesi.",
                "Neptün": "Maddi konularda sezgisel ve kadersel başarı.",
                "Satürn": "Başarı, itibar ve onurun ancak orta yaştan sonraki dönemlerde gelmesi."
            },
            "is_hayati": {
                "Merkür": "İş hayatında iletişim veya ticari hatalardan kaynaklanan zorlanmalar."
            },
            "arkadaslar": {
                "Merkür": "Arkadaşlardan gelecek küçük ama kritik yardımlar.",
                "Neptün": "Kolektif ve ruhsal idealleri paylaşan arkadaş çevreleri.",
                "Uranüs": "Arkadaş ve akrabalarla aniden gelişen, beklenmedik ayrılıklar."
            },
            "gizlilikler": {
                "Ay": "Bilinçaltında yatan veya çevreden gelen gizli rekabet enerjisi.",
                "Satürn": "Gizli yardımlar ve bunun yarattığı kadersel sorumluluklar."
            }
        }
    },

    "SADALSUUD": {
        "derece": 323.40,  # 23°24' Kova
        "yargi":"İlişkinizdeki enerji, klasik ilişki formüllerine sığmayacak kadar geniştir. Satürn'ün disiplini ile Uranüs'ün özgürlüğünü dengelediğiniz an, kadersel talih kapılarınız sonuna kadar açılacaktır." ,

        "etkiler": {
            "ask": {
                "Satürn": "Karşı cins üzerinde adeta hipnotik, büyüleyici ve otoriter bir etki kurabilme gücü.",
                "Uranüs": "Karşı cinsle ilişkilerde beklenmedik istikrarsızlık ve aniden kopan bağlar.",
                "Genel": "İlişkide sıra dışı, teknolojik veya entelektüel derinliği olan bir çekim alanı."
            },
            "cinsellik": {
                "Satürn": "Dürtüsel konularda aşırıya kaçma eğilimi ve gizli tutkular.",
                "Genel": "Fiziksel zevkten ziyade zihinsel ve ruhsal bir bütünleşmeyi arzulayan bir yapı."
            },
            "maddi": {
                "Jüpiter": "Çok güçlü kadersel maddi talih, spekülatif kazançlar ve şans odaklı zenginlik.",
                "Genel": "Kolektiften ve toplumsal projelerden gelen finansal bereket."
            },
            "evlilik": {
                "Uranüs": "Evlilikte özgürlükçü, geleneksel olmayan ve sıra dışı bir bağ kurma isteği.",
                "Genel": "Kadersel şansın yüksek olduğu, ancak bireysel alanın korunması gereken bir birliktelik."
            },
            "zihinsel": {
                "Genel": "Zamanının ötesinde, vizyoner, uzak görüşlü ve orijinal bir zeka yapısı."
            },
            "arkadaslar": {
                "Ay": "Sıradan olmayan, entelektüel açıdan besleyici ve saygılı arkadaşlıklar."
            }
        }
    },

"ARCTURUS": {
        "derece": 204.0,  # 24° Terazi (Konum verilerine göre hassas ayar gerektirebilir)
        "yargi":"İlişkinizdeki sırlar, dış dünyanın gürültüsünden uzakta ve 'sessiz bir koruma' altındadır. Bu mühür, dışarıdan gelen müdahalelere karşı ilişkinize doğal bir kalkan ve mahremiyet zırhı kazandırır." ,

        "etkiler": {
            "gizlilikler": {
                "Yükselen": "Sadık arkadaşlar ve kişisel yaşamdaki gizliliklerin sessizce korunması, özel hayatın mahremiyeti.",
                "Genel": "Sırları saklama konusunda mükemmel bir disiplin ve kadersel koruma."
            },
            "maddi": {
                "Genel": "Çalışarak elde edilen zenginlik, başarı ve toplum içinde saygınlık.",
                "Jüpiter": "Finansal konularda sürpriz fırsatlar ve şanslı girişimler."
            },
            "is_hayati": {
                "Genel": "Liderlik kapasitesi, iş hayatında güvenilir bir otorite figürü olma."
            },
            "ask": {
                "Genel": "Kişinin sadakati ile sınandığı, ancak sağlam temelli kadersel birliktelikler."
            }
        }
    },

"MERGA": {
        "derece": 204.0,  # 24° Terazi (Yaklaşık)
        "yargi": "Merga, dağınık enerjilerin tek bir kadersel hedefe odaklanması gerektiğinin mührüdür. Eğer bu mühür aktifse, ilişkinizdeki veya yaşamınızdaki dağınıklık bir 'yol kaybı' değil, bir 'hasat hazırlığı'dır. Yargısı şudur: Enerjinizi sağa sola saçmayı bıraktığınızda, kadersel hasadınızın ne kadar bereketli olduğunu fark edeceksiniz. Merga, size zayıf taraflarınızı birleştirip bir 'kadersel değnek' gibi kullanarak, kendi kaderinizin efendisi olabileceğinizi fısıldar; bu, sorumluluk almanın en saf ve en ödüllendirici biçimidir.",
        "etkiler": {
            "maddi": {
                "Genel": "Odaklanmış çaba ile gelen hasat; uzun vadeli, sabırlı emeklerin meyve vermesi.",
                "Satürn": "Zamanın olgunlaştırdığı maddi kazanımlar."
            },
            "zihinsel": {
                "Genel": "Bilinçli odaklanma, dikkat dağınıklığının giderilmesi, hedefe kilitlenme yetisi.",
                "Merkür": "Düşünceleri eyleme dönüştürme konusunda yüksek stratejik yetenek."
            },
            "evlilik": {
                "Genel": "İlişkide ortak hedeflere yönelme, dağılmış bir bağı disiplinle yeniden inşa etme gücü."
            }
        }
    },

"FOMALHAUT": {
        "derece": 353.0,  # 3° 23' Balık
        "yargi":"Kadersel rotanızdaki yüksek idealleri temsil eder. Hayatınıza giren sırlar sizin sınavınızdır. Gizli düşmanlıklara karşı stratejik bir zırh kuşanmanız ve hayalperestlikten uzak durmanız gereken bir dönemdesiniz." ,

        "etkiler": {
            "gizlilikler": {
                "Jüpiter": "Gizli topluluklar veya ezoterik çevrelerle kadersel bağlar.",
                "Mars": "Arka planda yürütülen kadersel çatışmalar ve gizli gündemler.",
                "Merkür": "Sırlar içeren yazışmalar veya gizli bilgilerin açığa çıkması.",
                "Ay": "Büyük zorluklara ve karmaşık sorunlara yol açan gizli süreçler; ancak sabırla ulaşılan nihai kazançlar.",
                "Neptün": "Gizli operationalar veya görünmeyen güçlerle ilişkili kadersel süreçler.",
                "Venüs": "Gizli ve toplumdan saklanan aşk ilişkileri."
            },
            "maddi": {
                "Genel": "Uzun vadeli çabalarla elde edilen, çok zorlukla kazanılan ancak kalıcı olan kadersel servet.",
                "Uranüs": "İş hayatında ani ve sıra dışı değişimler, beklenmedik finansal kırılmalar."
            },
            "ask": {
                "Genel": "İlişkide idealist beklentiler ve gerçeklikten kopuş riski.",
                "Venüs": "Aşk hayatında kadersel sırlar ve ulaşılmaz olanın peşinde koşma."
            },
            "is_hayati": {
                "Genel": "Yaratıcı zeka gerektiren işlerde başarı, ancak gizli engellere karşı tetikte olma zorunluluğu."
            }
        }
    },
"RIGEL": {
        "derece": 76.5,  # 16°30' İkizler
        "yargi":"Bu mühür, zekanızın ve potansiyelinizin hızını artırır ancak duygusal rotanızda sarsıcı etkiler yaratabilir. Zekanızı dengeleyecek sabrı inşa etmezseniz, ani yükselişler aynı hızla sarsıntıya dönüşebilir." ,
        
        "etkiler": {
            "ask": {
                "Uranüs": "Aşk hayatında beklenmedik, şok edici ve erken yaşta gelen hayal kırıklıkları.",
                "Venüs": "Tutkulu ama sınırları zorlayan, gelenek dışı romantik deneyimler."
            },
            "zihinsel": {
                "Mars": "Dahi seviyesinde bir zeka, ancak bu zekanın getirdiği aşırı huzursuzluk ve sabırsızlık.",
                "Neptün": "Bilimsel keşiflere açık, aktif ve ilham dolu bir zihin yapısı."
            },
            "maddi": {
                "Genel": "Zeka ve yetenekle gelen hızlı yükseliş, ancak bu statüyü koruma sınavı.",
                "Jüpiter": "Sürpriz finansal kapıların açılması ve sosyal statü artışı."
            },
            "is_hayati": {
                "Genel": "İş hayatında üstün başarı, buluş yeteneği ve çevreyi yönetme becerisi."
            },
            "saglik": {
                "Genel": "Yüksek sinirsel enerji, zaman zaman gelen zihinsel tükenmişlik."
            }
        }
    },

"ZUBEN_EL_SCHEMALI": {
        "derece": 219.0,  # 19° Akrep
        "yargi":"Sistemin kadersel terazisinde dengeyi temsil eder. Eğer bu mühür aktifse, ilişkinizdeki stratejik hamleleriniz size 'akılcı bir yükseliş' olarak geri dönecektir." ,
        "etkiler": {
            "maddi": {
                "Genel": "Büyük zenginlik, onur ve entelektüel başarı. Başkalarından gelen kazançlar.",
                "Satürn": "Maddi konularda yavaş ama kalıcı ve sağlam bir yükseliş."
            },
            "ask": {
                "Genel": "İlişkilerde nezaket, diplomatik beceri ve uyum arayışı.",
                "Venüs": "Aşk hayatında entelektüel ve uyumlu bir atmosfer."
            },
            "evlilik": {
                "Genel": "Kadersel olarak dengeli, sosyal statüsü yüksek bir birliktelik."
            },
            "zihinsel": {
                "Merkür": "Bilimsel, felsefi ve yüksek düzeyde zihinsel yetenekler."
            }
        }
    },

    "ZUBEN_EL_GENUBI": {
        "derece": 215.0,  # 15° Akrep
        "yargi":"Terazinin bu kefesi, geçmiş karmik borçların ödendiği yerdir. İlişkinizdeki krizler bir 'ceza' değil, terazinin dengelenmesi için gereken bir kadersel hesaplaşmadır." ,

        
        "etkiler": {
            "maddi": {
                "Genel": "Zenginlik ancak bu zenginliğin getirdiği toplumsal bedeller ve kadersel riskler.",
                "Mars": "Dürtüsel harcamalar sonucu gelen kayıplar."
            },
            "ask": {
                "Genel": "Karşı cinsle ilişkilerde dikkatli olunması gereken, bazen manipülatif etkiler.",
                "Venüs": "Aşkta kadersel zorluklar ve yanlış anlaşılmalar."
            },
            "kaza": {
                "Genel": "İhmalkarlık ve dikkatsizlik sonucu oluşan fiziksel aksilikler."
            },
            "evlilik": {
                "Satürn": "Evlilikte zorlu imtihanlar, kadersel bir 'terazi' sınanması.",
                "Genel": "Evlilik ortaklığında güç ve denge unsurlarının çatışması."
            }
        }
    },
"THUBAN": {
        "derece": 167.0,  # Yaklaşık 17° Başak (FBST hassasiyetine göre ayarlanabilir)
        "yargi": "Zihniniz şu an kadim bir arşiv gibi çalışıyor. Çözemediğiniz krizlerin kökleri bugünde değil, geçmişin dosyalarında saklı. Stratejik dehanızı kullanarak bu karmik veriyi büyük bir kazanca dönüştürme vaktidir.",
        
        "etkiler": {
            "zihinsel": {
                "Genel": "Son derece delici, analizci ve gizli kalmış bilgileri ortaya çıkaran bir zihin yapısı.",
                "Satürn": "Zihinsel disiplin, tarihsel ve kadim konulara eğilim."
            },
            "is_hayati": {
                "Genel": "Borsa ve spekülatif piyasalarda kadersel başarı, gizli yatırımlarda öngörü.",
                "Uranüs": "Finansal piyasalarda ani stratejik hamleler."
            },
            "saglik": {
                "Genel": "Zehirlenme tehlikeleri ve kimyasal hassasiyetlere karşı kadersel uyarı."
            },
            "arkadaslar": {
                "Genel": "Bilgi paylaşımına dayalı, entelektüel derinliği olan arkadaşlıklar."
            },
            "gizlilikler": {
                "Genel": "Kökleri geçmişe dayanan sırlar, ailevi veya kadim bir mirasın korunması."
            }
        }
    },
"ALTAIR": {
        "derece": 300.9,  # 0° 54' Kova (FBST hassasiyetine göre ayarlanabilir)
        "yargi":"Yükselişiniz, bir kartalın kanat çırpışı kadar hızlı ve sarsıcı olacak. Ancak bu hız kıskançlık enerjilerini de çeker. Hızlı yükselmenin bedeli, rotada sabit kalabilme iradesidir." ,

        "etkiler": {
            "maddi": {
                "Genel": "Büyük, ani ancak kısa ömürlü zenginlik ve onur; şanslı girişimler.",
                "Mars": "Sosyal toplum ve iş ortaklıklarından gelen kadersel sınavlar sonrası büyük kazançlar."
            },
            "is_hayati": {
                "Merkür": "Ortaklıklar için kadersel olarak zorlu, dikkat gerektiren bir konum.",
                "Ay": "Şirket ve kamu işlerinde dönemsel sorunlar ve krizler."
            },
            "kaza": {
                "Satürn": "Çalışma hayatında veya genel yaşamda ömür boyu sürebilecek kaza tehlikesi veya yetersizlik hissi.",
                "Genel": "Ani ve büyük değişimlerin getirdiği kadersel sarsıntılar."
            },
            "arkadaslar": {
                "Güneş": "Çok sayıda arkadaş, ancak bunların bir kısmının kıskançlık ve yazışmalar yoluyla yarattığı problemler.",
                "Uranüs": "İkizler doğasında, entelektüel, edebiyatçı veya zeki arkadaş grupları."
            },
            "zihinsel": {
                "Genel": "Keskin, hızlı ve yönetici bir zeka; hızlı kavrayış."
            }
        }
    },

"MIRFAK": {
        "derece": 61.0,  # 1° İkizler
        "yargi": "Mirfak, kadersel bir yükselişin ve stratejik otoritenin mührüdür. Eğer bu mühür aktifse, ilişkinizdeki veya yaşamınızdaki zorluklar, karakterinizi çelikleştirmek için tasarlanmış birer 'kadersel antrenman'dır. Yargısı şudur: Otoritenizi ve onurunuzu korumak için attığınız her akılcı adım, kadersel rotanızda sizi bir lider konumuna taşır. Ancak bu mühür, sadece kişisel hırsla değil, kolektife hizmet eden bir vizyonla yönetildiğinde gerçek gücünü ortaya çıkarır; aksi takdirde elde edilen statü, beraberinde yalnızlığı getirebilir.",
        "etkiler": {
            "maddi": {
                "Genel": "Liderlik becerisiyle gelen onur, prestij ve yüksek statü.",
                "Satürn": "Zamanla gelen kalıcı otorite."
            },
            "saglik": {
                "Genel": "Yüksek fiziksel dayanıklılık, ancak aşırı çalışmaya bağlı sinirsel yorgunluk."
            },
            "is_hayati": {
                "Genel": "Yönetici pozisyonları, kitleleri yönlendirme yetisi ve stratejik planlama başarısı."
            }
        }
    },
    
   "MARFIK": {
        "derece": 255.0,  # 15° Yay (yaklaşık)
        "yargi": "Marfik, gökyüzünün şifacı elini temsil eden, zehri panzehire dönüştürme kapasitesinin mührüdür. Eğer bu mühür aktifse, ilişkinizdeki çatışmalar ve zorlu süreçler aslında ruhsal tekamülünüz için gereken birer 'arınma töreni'dir. Yargısı şudur: Kendi hakikatinizi dışarıda değil, ilişkinizin derinliklerinde saklı olan 'gölge'lerde bulacaksınız. Zehri şifaya dönüştürmek, ancak kendi içsel karanlığınızla yüzleşip onu sevgiyle kucakladığınızda mümkündür; aksi takdirde krizler kısır bir döngü olarak tekrarlanacaktır.",
        "etkiler": {
            "zihinsel": {
                "Genel": "Kendi doğrularını savunma, felsefi ve ruhsal arayışlarda keskin bir zihin.",
                "Satürn": "Kadim bilgilere duyulan ilgi, ciddi ve disiplinli ruhsal araştırmalar."
            },
            "maddi": {
                "Genel": "Ruhsal veya ilahi olanın peşinden giderek elde edilen dünyevi bilgi ve manevi kazanç."
            },
            "evlilik": {
                "Genel": "Partnerle paylaşılan ortak inanç sistemleri, ruhsal hedefler ve kadersel bir yol arkadaşlığı."
            }
        }
    },
    
    "ANKA": { # Ankaa / Alpha Phoenicis
        "derece": 15.0,  # 15° Balık
        "yargi":"Bu mühür bir krizin veya yıkımın son olmadığını fısıldar. Yaşananlar ilişkinizin bitişi değil, geçmişin küllerinden çok daha güçlü ve asil bir şekilde yeniden doğuşunun habercisidir." ,

        "etkiler": {
            "maddi": {"Genel": "Küllerinden yeniden doğma gücü; büyük krizlerden finansal yükselişle çıkma."},
            "ask": {"Genel": "Derin bir duygusal dönüşüm ve bağ kurma arzusu."},
            "evlilik": {"Genel": "İlişkide yaşanan büyük değişim ve yenilenme süreçleri."}
        }
    },
    
    "ACRUX": {
        "derece": 221.0,  # 11° Akrep
        "yargi":"İlişkiniz kadersel bir ihtişam evresine giriyor. Bu mühür aktifken yaşananlar sadece dünyevi bir başarı değil, büyük bir prestij ve ruhsal otorite transferidir." ,

        "etkiler": {
            "maddi": {"Genel": "İhtişam, lüks, gösteriş ve sosyal prestij."},
            "is_hayati": {"Genel": "Yüksek onur, büyük başarı, kadersel bir yükseliş süreci."},
            "gizlilikler": {"Genel": "Ezoterik güçler ve saklı kalmış derin bilgilerin kullanımı."}
        }
    },

"RANA": {
        "derece": 58.0,  # 28° Boğa
        "yargi": "Rana, kadersel bir akışta belirsizliğin ve dalgalanmanın mührüdür. Bu yıldız aktifleştiğinde, hayatınızdaki en güvenli limanların bile sarsılabileceğini unutmamalısınız. Yargısı şudur: Kontrol etmeye çalıştığınız her şeyin akışa bırakılması gerektiğini öğretir; aksi takdirde 'boğulma' hissi veren duygusal veya fiziksel türbülanslarla yüzleşmek zorunda kalırsınız. Bu krizler, aslında sizi sahte güvenli alanlarınızdan çıkarıp gerçek kadersel rotanıza yönlendiren birer 'akıntı'dır.",
        "etkiler": {
            "kaza": {
                "Genel": "Sıvılarla, denizle veya seyahatlerde yaşanabilecek kadersel aksilikler/kazalar."
            },
            "saglik": {
                "Genel": "Solunum yolları hassasiyeti, sıvı dengesizliği veya ödem eğilimi."
            },
            "zihinsel": {
                "Genel": "Sezgisel derinlik ancak bu derinlikte kaybolma riski."
            }
        }
    },
    

    "CAPULUS": {
        "derece": 63.0,  # 3° İkizler
        "yargi": "Şu an haritanızda 'Dönüşüm Tutkusu' mühürleri aktif. Bu dönem, duygusal enerjilerinizin bir yıkım mı yoksa simyasal bir dönüşüm mü yaratacağını belirleyeceğiniz çok kritik bir kadersel kavşaktır." ,
        "etkiler": {
            "ask": {
                "Genel": "İlişkilerde yoğun duygusal dalgalanmalar ve tutku krizleri.",
                "Mars": "İlişkide yoğun tartışmalar ve kadersel olarak zorlu süreçler."
            },
            "maddi": {
                "Genel": "Riskli yatırımlardan gelen ani dalgalanmalar, dikkatli olunması gereken dönem."
            }
        }
    },

    "CASTOR": {
        "derece": 110.0,  # 20° Yengeç
        "yargi":"Castor, zihinsel dehanın ve edebi başarının ışığını taşırken, aynı zamanda bu parlaklığın getirdiği kadersel ağırlığı temsil eder. Bu mühür aktifse, ilişkiniz ani ve göz kamaştırıcı başarıların eşiğindedir; ancak elde edilen her zafer, beraberinde sürdürülebilirlik sınavını getirir. Zekayı manipülasyon için değil, ortak hakikati inşa etmek için kullanmadığınız takdirde, zirveden gelen hızlı düşüşler kaçınılmaz bir kadersel döngü haline gelir." ,

        "etkiler": {
            "maddi": {
                "Genel": "Ani ve büyük başarılar, ancak sonrasında gelen hızlı düşüş veya kayıplar.",
                "Jüpiter": "Finansal konularda şanslılık, ancak sürdürülebilirlik sınavı."
            },
            "zihinsel": {
                "Genel": "Zekayı yönetme gücü, edebi başarılar, ancak sinirsel aşırılıklar."
            },
            "kaza": {
                "Genel": "Göz rahatsızlıkları ve kaza potansiyeli."
            }
        }
    },

    "POLLUX": {
        "derece": 113.0,  # 23° Yengeç
        "yargi":"Şu an haritanızda 'Yıkıcı Tutku' mühürleri aktif. Bu dönem, duygusal tepkilerinizin bir yıkım mı yoksa simyasal bir dönüşüm mü yaratacağını belirleyeceğiniz çok kritik bir kadersel kavşaktır." ,

        "etkiler": {
            "cinsellik": {
                "Güneş": "Yoğun ve dönüştürücü cinsel enerjiler, tutkunun sınandığı derin deneyimler.",
                "Venüs": "Aşırı çekim gücü ve duygusal derinlikle şekillenen, sıra dışı cinsel deneyimler."
            },
            "ask": {
                "Genel": "Yıkıcı duygular, kadersel krizler ve ilişkideki manipülasyonlar."
            },
            "maddi": {
                "Genel": "Mücadeleyle gelen kazançlar, ancak güvenilmez çevre yüzünden riskler."
            }
        }
    },

    "ALGIEBA": {
        "derece": 149.99,  # 29°59' Aslan (γ Leo)
        "yargi": "Algieba, Aslan'ın alnındaki cesaret ve şeref mührüdür. Eğer bu mühür aktifse, ilişkinizdeki liderlik, koruyuculuk ve cömertlik duyguları güçlenir; ancak gurur kontrolden çıkarsa itibar kazanımları ani sarsıntılara açık hale gelir. Yargısı şudur: Sahip olduğunuz taht, ancak kibirden ve sertlikten arındığında korunabilir; cesareti sevgiyle, otoriteyi şefkatle harmanladığınızda bu mühür sizi kalıcı bir onura taşır.",
        "etkiler": {
            "ask": {
                "Genel": "Koruyucu ve onurlu bir sevgi; partnerinizi güçlü bir şekilde sahiplenme ve gözetme."
            },
            "evlilik": {
                "Genel": "Saygın, korumacı ve lider ruhlu bir birliktelik; ancak egonun sınırlanması şarttır."
            },
            "maddi": {
                "Genel": "Onur ve çabayla gelen kazançlar; itibar kaynaklı fırsatlar."
            },
            "kaza": {
                "Mars": "Gurur kaynaklı ani çatışma ve sarsıntılara açıklık; dikkatli olunmalı."
            },
            "zihinsel": {
                "Genel": "Keskin, kararlı ve cesur bir zihin yapısı."
            }
        }
    },

    "ALMACH": {
        "derece": 44.59,  # 14°35' Boğa (γ And) — Almaak/Almak/Almac varyantlarıyla aynı yıldız
        "yargi": "Almach, sanatın ve zarafetin kozmik mührüdür. Bu mühür aktifse, ilişkinizde estetik duyarlılık, müzik ve kültürel paylaşımlar öne çıkar; sevginizi ifade etme biçiminiz incelik kazanır. Yargısı şudur: Güzelliği yüzeysel bir süs olarak değil, birleştirici bir dil olarak kullandığınızda bu mühür size hem sanatsal başarı hem de derin bir romantik çekim bahşeder; ancak aşırılıklardan kaçınmazsanız tutkular dengeden sapabilir.",
        "etkiler": {
            "ask": {
                "Genel": "Zarif, sanatsal ve çekici bir aşk enerjisi; estetik zevkler ortak payda olur."
            },
            "evlilik": {
                "Venüs": "Kültürel ve estetik uyum üzerine kurulu, incelikli bir birliktelik."
            },
            "cinsellik": {
                "Genel": "Sanat ve sevgiyi birleştiren, zarif ama tutkulu bir cinsel enerji."
            },
            "is_hayati": {
                "Genel": "Sanat, müzik ve kültür alanlarında başarı fırsatları."
            },
            "kaza": {
                "Genel": "Hızlı hareketler ve yüksek yerlerle ilgili dikkat gerektiren durumlar."
            }
        }
    },

    "ALCHIBA": {
        "derece": 192.24,  # 12°14' Terazi (α Crv) — Alchita varyantıyla aynı yıldız
        "yargi": "Alchiba, kuzgunun taşıdığı kehanet mührüdür; mesajların ve sezgilerin diliyle örülü bir yoldur. Bu mühür aktifse, ilişkinizde söylenmemiş olanı sezme ve doğru zamanda doğru sözü söyleme yeteneği belirir; birbirinizin zihnini okur gibi anlarsınız. Yargısı şudur: Gelen haberin ve sezginin dilini çözdüğünüzde bu mühür size keskin bir anlayış kazandırır; ancak zekâ, oyunlara ve gizli hesaplara dönüşmemelidir. Kuzgun gerçeği yüksekten görür; sevgi ise onu yumuşak bir yere kondurur.",
        "etkiler": {
            "ask": {
                "Genel": "Sezgisel ve zeki bir iletişimle örülen, anlam derinliği yüksek bir sevgi."
            },
            "evlilik": {
                "Genel": "Akıl ve sezginin ortak dil kurduğu; mesajlaşmanın kaderi bağladığı bir birliktelik."
            },
            "zihinsel": {
                "Genel": "Keskin, sezgisel ve sembolleri hızla çözen bir zihin."
            },
            "gizlilikler": {
                "Genel": "Saklı mesajlar ve gizli anlamlar; doğru çözüldüğünde büyük bir avantaj."
            },
            "arkadaslar": {
                "Genel": "Zekâ oyunlarıyla kurulan, entelektüel derinliği olan dostluklar."
            }
        }
    },

    "DECRUX": {
        "derece": 215.66,  # 5°40' Akrep (δ Cru) — Güney Haçı'nın işareti
        "yargi": "Decrux, Güney Haçı'nın işaretidir; kaderin en karanlık yönünde bile yön bulmayı öğreten bir mühürdür. Bu mühür aktifse, ilişkinizde birlikte katlanılan fedakârlıklar derin bir anlam kazanır; güçlü bir amaç uğruna sevmek, sıradan bir bağı aşar. Yargısı şudur: Haçın ağırlığını birlikte taşımayı seçtiğinizde bu mühür size kalıcı bir ruhsal derinlik kazandırır; ancak yük tek tarafa kalırsa kırılma yaşanır. Birlikte katlanılan karanlık, en parlak ışığı doğurur.",
        "etkiler": {
            "ask": {
                "Genel": "Fedakârlık ve derin sadakatle yoğrulmuş, kaderin sınadığı bir sevgi."
            },
            "evlilik": {
                "Genel": "Zorlukları birlikte aşan, kutsal bir amaç etrafında kenetlenen bir birliktelik."
            },
            "cinsellik": {
                "Genel": "Tutkuyu ruhsallıkla harmanlayan, birleşmeyi kutsal kılan bir enerji."
            },
            "gizlilikler": {
                "Genel": "Aileye ve geçmişe dair kadersel sırlar; ortak yüzleşmeyle aydınlanır."
            },
            "saglik": {
                "Genel": "Aşırı yüklenme ve tükenmişliğe karşı dikkat; dinlenme, fedakârlıkla çelişmemeli."
            }
        }
    },

    "SHIR": {
        "derece": 156.39,  # 6°23' Başak (ρ Leo) — Aslan'ın şarkısı
        "yargi": "Shir, aslanın gururla söylediği şarkıdır; içteki sese güvenip kendini ifade etme mührüdür. Bu mühür aktifse, ilişkinizde açık sözlülük ve içten ifade öne çıkar; duygularınız saklanmadan, gururla ve net biçimde dışa akar. Yargısı şudur: Sesinizi yükseltmekten korkmadığınızda bu mühür size hem özgüven hem hayranlık kazandırır; ancak sözler yara açacak kadar keskinleşmemelidir. Doğru zamanda söylenen şarkı, yalnızlığı bile onarır.",
        "etkiler": {
            "ask": {
                "Genel": "Kendini net ve gururla ifade eden, cesur ve içten bir sevgi."
            },
            "evlilik": {
                "Genel": "Açık sözlülük üzerine kurulu; gurur ve saygının dengelendiği bir birliktelik."
            },
            "maddi": {
                "Genel": "Kendini değerli görme ve görünür olma; yetenekleri duyurmanın getirdiği kazanç."
            },
            "zihinsel": {
                "Genel": "Yaratıcı, ifade gücü yüksek ve cesur bir zihin."
            }
        }
    },

    "RASALAS": {
        "derece": 141.43,  # 21°26' Aslan (μ Leo) — Ras Elased Borealis varyantıyla aynı yıldız
        "yargi": "Rasalas, aslanın kuzey başıdır; cesareti taşıyan ama gurura karşı uyaran bir mühürdür. Bu mühür aktifse, ilişkinizde koruyuculuk ve atılganlık öne çıkar; sevdiğinizi savunmak için gösterdiğiniz cesaret, bağınızın görünür bir kanıtı olur. Yargısı şudur: Cesaretinizi sevginin emrine verdiğinizde bu mühür size onur ve sadakat kazandırır; ancak gurur savaşçıyı yalnızlaştırır. Gücünüzü koruyucu değil, yıkıcı kullandığınızda tahtınız sarsılır; aslanın asaleti, yumuşaklıkla dengelenen güçtedir.",
        "etkiler": {
            "ask": {
                "Genel": "Koruyucu, cesur ve sahiplenici bir sevgi; sevdiğini savunmak için risk alır."
            },
            "evlilik": {
                "Genel": "Güçlü bir koruma içgüdüsü üzerine kurulu; gururun saygıyla dengelendiği birliktelik."
            },
            "cinsellik": {
                "Genel": "Atılgan, tutkulu ve sahiplenici bir cinsel enerji."
            },
            "kaza": {
                "Genel": "Ani gurur kırılmaları ve öfke patlamalarına bağlı çatışma riski."
            },
            "zihinsel": {
                "Genel": "Cesur, kararlı ve savunmacı bir zihin yapısı."
            }
        }
    },

    "MENKAR": {
        "derece": 44.69,  # 14°41' Boğa (α Cet)
        "yargi": "Menkar, balinanın burun deliğindeki sınav ve bilgelik mührüdür. Bu mühür aktifse, ilişkinizde sağlık ve dayanıklılık konuları öne çıkar; birbirinizin zayıf anlarında hekim gibi davranma görevi yüklenirsiniz. Yargısı şudur: Karşılaştığınız güçlükler, çözüm ve şifa yeteneğinizi geliştirmek için yazılmıştır; krize değil çareye odaklandığınızda bu mühür size hem bilgi hem iyileşme gücü kazandırır.",
        "etkiler": {
            "ask": {
                "Genel": "Şefkatli ve iyileştirici bir sevgi; partneri zorlukta koruma dürtüsü."
            },
            "saglik": {
                "Genel": "Hastalıklara ve yorgunluğa karşı hassasiyet; düzenli bakım gerekir."
            },
            "evlilik": {
                "Genel": "Birlikte zorlukları aşan, dayanıklı ve bakım odaklı bir bağ."
            },
            "zihinsel": {
                "Genel": "Tıp, bilim ve araştırma konularına yatkın, keskin bir zihin."
            }
        }
    },

    "RASALHAGUE": {
        "derece": 262.83,  # 22°50' Yay (α Oph)
        "yargi": "Rasalhague, yılan taşıyıcısının başındaki şifa ve bilgelik mührüdür. Bu mühür aktifse, ilişkinizde iyileştirici bir güç ve hakikat arayışı belirir; birbirinizin duygusal yaralarını sarmada doğal bir yeteneğiniz vardır. Yargısı şudur: Bilgeliğinizi güç aracı olarak değil, şifa aracı olarak kullandığınızda bu mühür size sarsılmaz bir bütünlük ve derin bir bağ kazandırır; ancak gizli çekişmeler ve zehirli sözler bağınızı yıpratmamalıdır.",
        "etkiler": {
            "ask": {
                "Genel": "Şifacı ruhlu, bilge ve derin bir sevgi bağı."
            },
            "evlilik": {
                "Genel": "Karşılıklı anlayış, dürüstlük ve manevi destek üzerine kurulu bir birliktelik."
            },
            "saglik": {
                "Genel": "İyileşme kapasitesi yüksek; hem kendi hem partnerin sağlığına şifa verir."
            },
            "zihinsel": {
                "Genel": "Tıp, felsefe ve derin araştırma konularına yatkın, analitik bir zihin."
            },
            "gizlilikler": {
                "Genel": "Gizli düşmanlıklara ve imalara karşı dikkatli olunmalıdır."
            }
        }
    },

    "WASAT": {
        "derece": 108.89,  # 18°53' Yengeç (δ Gem)
        "yargi": "Wasat, ikizlerin ortasındaki denge ve şeref mührüdür. Bu mühür aktifse, ilişkinizde edebi ve bilimsel paylaşımlar, ortak okumalar ve fikir alışverişleri öne çıkar; adalet duygunuz güçlenir. Yargısı şudur: Dürüstlük ve ölçüden ayrılmadığınızda bu mühür size hem maddi hem manevi itibar kazandırır; ancak kötü niyetli çevrelerden gelebilecek yönlendirmelere karşı seçici olmanız gerekir.",
        "etkiler": {
            "ask": {
                "Genel": "Dengeli, dürüst ve entelektüel bir sevgi dili."
            },
            "evlilik": {
                "Genel": "Ortak fikirler ve adalet anlayışı üzerine kurulu sağlam bir bağ."
            },
            "maddi": {
                "Genel": "İtibar ve emek yoluyla gelen istikrarlı kazançlar."
            },
            "arkadaslar": {
                "Genel": "Çevrenin etkisine açık olma; güvenilir dostluklar seçilmelidir."
            }
        }
    },

    "TEJAT": {
        "derece": 95.67,  # 5°40' Yengeç (μ Gem)
        "yargi": "Tejat, yaratıcılığın ve anlatım gücünün mührüdür. Bu mühür aktifse, ilişkinizde sanatsal üretim, el becerisi ve sözel yetenek öne çıkar; duygularınızı ifade etmekte usta olursunuz. Yargısı şudur: Yaratıcı enerjinizi ortak bir projeye dönüştürdüğünüzde bu mühür size hem ilham hem bereket getirir; ancak dürtüsellik ve dikkatsizlik kazalara ve sözlerin kırıcılığına açık kapı bırakabilir.",
        "etkiler": {
            "ask": {
                "Genel": "Yaratıcı, esprili ve canlı bir sevgi enerjisi."
            },
            "cinsellik": {
                "Genel": "İfadesi güçlü, sanatsal ve coşkulu bir cinsel enerji."
            },
            "is_hayati": {
                "Genel": "Sanat, yazı ve iletişim alanlarında başarı fırsatları."
            },
            "kaza": {
                "Genel": "Su, yol ve ani hareketlerle ilgili dikkat gerektiren durumlar."
            }
        }
    },

    "DABIH": {
        "derece": 304.43,  # 4°26' Kova (β Cap)
        "yargi": "Dabih, oğlak kesicisinin emek ve kader mührüdür. Bu mühür aktifse, ilişkinizde kazançlar emek ve mücadeleyle gelir; kolay para vaadi sizi yanıltabilir. Yargısı şudur: Ticari konularda şeffaflıktan ve dürüstlükten ayrılmadığınızda bu mühür size kalıcı servet getirir; ancak kısa yoldan kazanç ve belirsiz ortaklıklar kadersel kayıplara yol açabilir. Bu yüzleşme, ahlaki sağlamlığınızın sınavıdır.",
        "etkiler": {
            "ask": {
                "Genel": "Emekle büyüyen, istikrarlı ve ciddi bir sevgi bağı."
            },
            "evlilik": {
                "Genel": "Ortak çaba ve mücadeleyle güçlenen, kalıcı bir birliktelik."
            },
            "maddi": {
                "Genel": "Mücadeleyle gelen kazançlar; riskli ortaklıklardan kaçınılmalıdır."
            },
            "is_hayati": {
                "Genel": "Ticaret ve iş dünyasında sabırlı çalışmayla yükselme."
            }
        }
    },

    "ARNEB": {
        "derece": 81.75,  # 21°45' İkizler (α Lep)
        "yargi": "Arneb, tavşanın çeviklik ve teyakkuz mührüdür. Bu mühür aktifse, ilişkinizde hızlı düşünme ve pratik çözümler öne çıkar; ani fırsatları yakalamakta usta olursunuz. Yargısı şudur: Çevikliğinizi yön ve amaçla birleştirdiğinizde bu mühür size avantaj sağlar; ancak acelecilik ve plansızlık sizi gereksiz risklere sürükleyebilir. Dengeli bir tempo, bu mührün en büyük anahtarıdır.",
        "etkiler": {
            "ask": {
                "Genel": "Canlı, atılgan ve sürprizlerle dolu bir sevgi enerjisi."
            },
            "evlilik": {
                "Genel": "Hareketli ve esnek bir birliktelik; sabitliğe ihtiyaç duyar."
            },
            "maddi": {
                "Genel": "Hızlı fırsatlar ve kısa vadeli kazançlar; risk yönetimi şart."
            },
            "zihinsel": {
                "Genel": "Çevik, hızlı ve fırsatları sezen bir zihin."
            }
        }
    },

    "CHARA": {
        "derece": 168.07,  # 18°04' Başak (β CVn) — Asterion varyantıyla aynı yıldız
        "yargi": "Chara, sadık köpeğin dostluk ve vefâ mührüdür. Bu mühür aktifse, ilişkinizde sadakat, koruma ve karşılıklı güven öne çıkar; birlikteliğiniz sevgi dolu bir sığınağa dönüşür. Yargısı şudur: Sadakatiniz koşulsuz olduğunda bu mühür size ömür boyu süren güvenilir bir bağ bahşeder; ancak aşırı korumacılık özgürlüğü kısıtlamamalıdır. Sevgi, güvenle özgürlüğün dansıdır.",
        "etkiler": {
            "ask": {
                "Genel": "Sadık, koruyucu ve içten bir sevgi; gerçek dostluğun aşkı."
            },
            "evlilik": {
                "Genel": "Güven, vefâ ve sadakat üzerine kurulu çok sağlam bir birliktelik."
            },
            "arkadaslar": {
                "Genel": "Güvenilir, sadık ve kalıcı dostluklar kurma yeteneği."
            },
            "zihinsel": {
                "Genel": "Sadakat ve sezgiyi birleştiren, içten ve anlayışlı bir zihin."
            }
        }
    },

    "ANSER": {
        "derece": 299.88,  # 29°53' Oğlak (α Vul)
        "yargi": "Anser, tilki ve kazın kurnazlık mührüdür. Bu mühür aktifse, ilişkinizde stratejik düşünme ve kıvrak zekâ öne çıkar; zorlu meseleleri zarafetle çözersiniz. Yargısı şudur: Zekânızı dürüstlükle birleştirdiğinizde bu mühür size üstünlük sağlar; ancak aldatma ve gizli oyunlar güveni zedeler. Şeffaflık, bu mührün karanlık yüzünü dengeleyen tek anahtardır.",
        "etkiler": {
            "ask": {
                "Genel": "Zeki, oyuncu ve stratejik bir sevgi dili; gizlilikten kaçınılmalıdır."
            },
            "evlilik": {
                "Genel": "Kurnazlık yerine dürüstlük üzerine kurulması gereken bir birliktelik."
            },
            "maddi": {
                "Genel": "Zekâ ve stratejiyle gelen kazançlar; etik sınırlar korunmalıdır."
            },
            "zihinsel": {
                "Genel": "Kıvrak, stratejik ve olayları önceden sezen bir zihin."
            }
        }
    },

    "ELECTRA": {
        "derece": 59.78,  # 29°47' Boğa (17 Tau)
        "yargi": "Electra, Ülker'in hüznü ve hırsıyla yoğrulmuş bir mührüdür. Bu mühür aktifse, ilişkinizde büyük hedefler ve tutkulu bir ilerleme arzusu belirir; ancak geçmişten gelen kayıp ve özlem temaları zaman zaman yüzeye çıkabilir. Yargısı şudur: Hırsınızı sevgiyle dengeleyip geçmişin yüklerini bıraktığınızda bu mühür size görkemli bir başarı kazandırır; kayıplar, sizi birbirinize daha sıkı bağlayan derslere dönüşür.",
        "etkiler": {
            "ask": {
                "Genel": "Tutkulu, hırslı ve derin bir sevgi; kayıp korkusuyla sınanır."
            },
            "evlilik": {
                "Genel": "Büyük hedeflere ortak olan, özlem ve hırsın dengelenmesi gereken bir bağ."
            },
            "maddi": {
                "Genel": "Hırs ve çabayla gelen büyük kazançlar; itibar odaklı ilerleme."
            },
            "arkadaslar": {
                "Genel": "Etkili çevreler; ancak geçmiş bağlar zaman zaman gündeme gelir."
            }
        }
    },

    "CELAENO": {
        "derece": 59.80,  # 29°48' Boğa (16 Tau) — Celeano varyantıyla aynı yıldız
        "yargi": "Celaeno, Ülker'in karanlıkta kalan kız kardeşidir; kayıp ve kederle sınanan bir mührüdür. Bu mühür aktifse, ilişkinizde zaman zaman hüzün ve geçmiş yaralar belirir; ancak bu derinlik, bağınıza şefkat ve olgunluk katar. Yargısı şudur: Kederi inkâr etmek yerine birlikte dönüştürdüğünüzde bu mühür size güçlü bir dayanıklılık kazandırır; ortak acılarınız, en derin bağlarınızın temeli olur.",
        "etkiler": {
            "ask": {
                "Genel": "Derin, şefkatli ve zaman zaman hüzünlü bir sevgi; iyileşme gerektirir."
            },
            "evlilik": {
                "Genel": "Ortak yaraları saran, sabır ve şefkatle güçlenen bir birliktelik."
            },
            "saglik": {
                "Genel": "Duygusal yorgunluk ve kederin bedensel yansımalarına dikkat."
            },
            "gizlilikler": {
                "Genel": "Geçmişin saklı yaraları; birlikte yüzleşildiğinde şifaya dönüşür."
            }
        }
    },

    "BEID": {
        "derece": 59.80,  # 29°48' Boğa (ο1 Eri)
        "yargi": "Beid, nehrin sularındaki bilgelik ve sınav mührüdür. Bu mühür aktifse, ilişkinizde araştırmacı bir ruh ve gizli bilgilere merak belirir; derin konularda birlikte çalışmaktan keyif alırsınız. Yargısı şudur: Zorlukları bilgiye dönüştürdüğünüzde bu mühür size sezgisel bir derinlik kazandırır; ancak belirsizlik ve kararsızlık, net sınırlar koymadığınızda ilişkiyi zayıflatabilir.",
        "etkiler": {
            "ask": {
                "Genel": "Meraklı, araştırmacı ve derin bir sevgi; netlik gerektirir."
            },
            "maddi": {
                "Genel": "Dalgalanmalara açık kazançlar; planlı ilerleme şarttır."
            },
            "zihinsel": {
                "Genel": "Ezoterik ve bilimsel konulara yatkın, sezgisel bir zihin."
            },
            "gizlilikler": {
                "Genel": "Saklı gerçekleri görme yeteneği; gizlilikte dikkatli olunmalıdır."
            }
        }
    },

    "ZIBAL": {
        "derece": 44.20,  # 14°12' Boğa (ζ Eri)
        "yargi": "Zibal, ırmaktaki yıldızın güç ve dikkat mührüdür. Bu mühür aktifse, ilişkinizde enerji, atılganlık ve mücadele ruhu öne çıkar; birlikte zorlu engelleri aşacak güce sahipsinizdir. Yargısı şudur: Gücünüzü öfkeye değil yapıcı hedeflere yönelttiğinizde bu mühür size sarsılmaz bir dayanıklılık kazandırır; ancak dürtüsellik ve ani tepkiler ilişkide gereksiz yaralar açabilir.",
        "etkiler": {
            "ask": {
                "Genel": "Tutkulu, atılgan ve korumacı bir sevgi; öfke kontrolü gerekir."
            },
            "evlilik": {
                "Genel": "Ortak mücadele ve dayanıklılık üzerine kurulu güçlü bir bağ."
            },
            "kaza": {
                "Genel": "Acelecilik ve ani hareketlerle ilgili dikkat gerektiren durumlar."
            },
            "zihinsel": {
                "Genel": "Güçlü, kararlı ve mücadeleden yılmayan bir zihin."
            }
        }
    },

    "ZHANG": {
        "derece": 156.06,  # 6°04' Başak (υ1 Hya)
        "yargi": "Zhang, Çin takvimindeki tören ve düzen mührüdür. Bu mühür aktifse, ilişkinizde protokol, saygı ve ortak kurallara bağlılık öne çıkar; birlikteliğiniz görgülü ve onurlu bir çerçeveye kavuşur. Yargısı şudur: Düzen ve zerafeti sevgiyle buluşturduğunuzda bu mühür size toplumsal saygınlık kazandırır; ancak aşırı kuralcılık samimiyeti soğutabilir. Denge, bu mührün en büyük erdemidir.",
        "etkiler": {
            "ask": {
                "Genel": "Zarif, saygılı ve ölçülü bir sevgi dili."
            },
            "evlilik": {
                "Genel": "Düzen, görgü ve karşılıklı saygı üzerine kurulu onurlu bir birliktelik."
            },
            "is_hayati": {
                "Genel": "Kamu, sanat ve törensel işlerde başarı fırsatları."
            },
            "arkadaslar": {
                "Genel": "Saygın ve güvenilir çevreler; itibarı koruyan dostluklar."
            }
        }
    },

    "GIEDI_SECUNDA": {
        "derece": 304.24,  # 4°14' Kova (α² Cap)
        "yargi": "Giedi Secunda, keçinin fedakârlık ve sorumluluk mührüdür. Bu mühür aktifse, ilişkinizde özveri, dürüstlük ve toplumsal yarar öne çıkar; birlikteliğiniz çevrenize örnek olur. Yargısı şudur: Sorumluluklarınızı sevgiyle üstlendiğinizde bu mühür size kalıcı bir saygınlık kazandırır; ancak kendinizi tüketen bir fedakârlık, ilişkinin dengesini bozabilir. Özveri, karşılıklı olduğunda kutsaldır.",
        "etkiler": {
            "ask": {
                "Genel": "Dürüst, özverili ve sorumluluk sahibi bir sevgi."
            },
            "evlilik": {
                "Genel": "Sadakat, görev bilinci ve ortak yarar üzerine kurulu sağlam bir bağ."
            },
            "maddi": {
                "Genel": "Dürüst çalışmayla gelen istikrarlı kazançlar."
            },
            "kaza": {
                "Genel": "Yüksek yerler ve düşme riskiyle ilgili dikkat gerektiren durumlar."
            }
        }
    },

    "ADHAFERA": {
        "derece": 147.93,  # 27°56' Aslan (ζ Leo)
        "yargi": "Adhafera, Aslan'ın orağının keskin hırs mührüdür. Bu mühür aktifse, ilişkinizde yükselme arzusu ve güçlü bir hedef odaklılık belirir; birlikte büyük hedeflere yürürken birbirinizi motive edersiniz. Yargısı şudur: Hırsınızı ittifaka dönüştürdüğünüzde bu mühür size zirveyi gösterir; ancak gurur ve tahakküm eğilimi, kazandıklarınızı kaybettirebilir. Başarı, tevazuyla taçlandığında kalıcıdır.",
        "etkiler": {
            "ask": {
                "Genel": "Tutkulu, hırslı ve hedef odaklı bir sevgi; egonun kontrolü gerekir."
            },
            "evlilik": {
                "Genel": "Ortak hedefler ve yükselme arzusuyla şekillenen dinamik bir birliktelik."
            },
            "maddi": {
                "Genel": "Hırs ve çabayla gelen kazançlar; itibar kaynaklı fırsatlar."
            },
            "kaza": {
                "Genel": "Gurur kaynaklı ani düşüşlere karşı dikkatli olunmalıdır."
            }
        }
    },

    "ALAGEMIN": {
        "derece": 5.06,  # 5°04' Koç (η Cep)
        "yargi": "Alagemin, Kral'ın yalnız ama asil mührüdür. Bu mühür aktifse, ilişkinizde derin bir içe dönüklük ve manevi olgunluk öne çıkar; birlikte sessiz anların değerini bilirsiniz. Yargısı şudur: Yalnızlığı yalnızlık olarak değil, içsel güç olarak gördüğünüzde bu mühür size sarsılmaz bir karakter kazandırır; ancak duygusal mesafe, bağınızın sıcaklığını azaltmamalıdır.",
        "etkiler": {
            "ask": {
                "Genel": "Derin, olgun ve sessiz güven üzerine kurulu bir sevgi."
            },
            "evlilik": {
                "Genel": "İstikrarlı, manevi ve duygusal açıklık gerektiren bir birliktelik."
            },
            "zihinsel": {
                "Genel": "Manevi ve felsefi konulara yatkın, derin düşünen bir zihin."
            },
            "arkadaslar": {
                "Genel": "Az ama öz, güvenilir dostluklar; kalabalık içinde yalnızlık eğilimi."
            }
        }
    },

    "KAHT": {
        "derece": 17.90,  # 17°54' Koç (ε Psc)
        "yargi": "Kaht, balıkların ağındaki sanat ve hayal mührüdür. Bu mühür aktifse, ilişkinizde şiirsel ifade, yaratıcılık ve zengin bir hayal dünyası öne çıkar; sevginizi sembollerle ve sözlerle zarafetle anlatırsınız. Yargısı şudur: Hayal gücünüzü gerçekliğe bağladığınızda bu mühür size sanatsal başarı ve romantik derinlik kazandırır; ancak hayallere fazla kapılmak, somut adımları geciktirebilir.",
        "etkiler": {
            "ask": {
                "Genel": "Şiirsel, hayalperest ve romantik bir sevgi dili."
            },
            "cinsellik": {
                "Genel": "Hayal gücüyle zenginleşen, incelikli ve romantik bir enerji."
            },
            "is_hayati": {
                "Genel": "Sanat, yazı ve yaratıcı işlerde başarı fırsatları."
            },
            "zihinsel": {
                "Genel": "Sezgisel, sanatsal ve sembolleri okuyan bir zihin."
            }
        }
    },

    "HECATEBOLUS": {
        "derece": 285.21,  # 15°13' Oğlak (τ Sgr)
        "yargi": "Hecatebolus, okçunun isabet ve dikkat mührüdür. Bu mühür aktifse, ilişkinizde hassas zamanlama ve doğru hedef seçimi öne çıkar; kritik anlarda isabetli kararlar alırsınız. Yargısı şudur: Odağınızı sevgiyle birleştirdiğinizde bu mühür size keskin bir sezgi kazandırır; ancak ani ve keskin tepkiler, ilişkide gereksiz yaralar açabilir. Nişan almadan ok atmamak, bu mührün temel kuralıdır.",
        "etkiler": {
            "ask": {
                "Genel": "Tutkulu, keskin ve hedef odaklı bir sevgi; sözler dikkatle seçilmelidir."
            },
            "evlilik": {
                "Genel": "Ortak hedeflere isabet eden, planlı ve kararlı bir birliktelik."
            },
            "kaza": {
                "Genel": "Ani kazalara ve keskin aletlere karşı dikkat gerektiren durumlar."
            },
            "zihinsel": {
                "Genel": "Keskin, isabetli ve stratejik düşünen bir zihin."
            }
        }
    },

    "KEBASH": {
        "derece": 109.15,  # 19°09' Yengeç (λ Gem)
        "yargi": "Kebash, ikizlerin kıvrak zekâ mührüdür. Bu mühür aktifse, ilişkinizde hızlı iletişim, espri ve zihinsel uyum öne çıkar; birbirinizi kelimelerin ötesinde yakalarsınız. Yargısı şudur: Zihinsel enerjinizi istikrarla birleştirdiğinizde bu mühür size hem iletişim hem anlayış gücü kazandırır; ancak kararsızlık ve dağınıklık, söz verdiğiniz konularda güveni zedeleyebilir.",
        "etkiler": {
            "ask": {
                "Genel": "Zeki, esprili ve iletişimi güçlü bir sevgi dili."
            },
            "evlilik": {
                "Genel": "Sohbet, zihinsel uyum ve espri üzerine kurulu canlı bir bağ."
            },
            "is_hayati": {
                "Genel": "Yazı, ticaret ve iletişim alanlarında başarı fırsatları."
            },
            "zihinsel": {
                "Genel": "Hızlı, kıvrak ve çok yönlü bir zihin; odaklanma gerektirir."
            }
        }
    },

    "QIN": {
        "derece": 228.72,  # 18°43' Akrep (δ Ser)
        "yargi": "Qin, yılanın süzülüşündeki strateji ve iç çatışma mührüdür. Bu mühür aktifse, ilişkinizde gizli gündemler yerine dürüst müzakere öne çıkmalıdır; aklınız ve kalbiniz arasında denge kurmanız gerekir. Yargısı şudur: Stratejik zekânızı şeffaflıkla kullandığınızda bu mühür size üstünlük kazandırır; ancak manipülasyon ve gizlilik, güveni en hızlı yıpratan zehirdir. Açıklık, bu mührün şifasıdır.",
        "etkiler": {
            "ask": {
                "Genel": "Derin, stratejik ama şeffaflık gerektiren bir sevgi; gizlilikten kaçınılmalıdır."
            },
            "evlilik": {
                "Genel": "Dürüst müzakere ve açık iletişim üzerine kurulması gereken bir bağ."
            },
            "zihinsel": {
                "Genel": "Stratejik, derin ve olayların ötesini gören bir zihin."
            },
            "gizlilikler": {
                "Genel": "Gizli sırlara ve imalara karşı dikkatli olunmalıdır."
            }
        }
    },

    "COPERNICUS": {
        "derece": 128.10,  # 8°06' Aslan (55 Cnc)
        "yargi": "Copernicus, gözlemin ve bilimsel merakın mührüdür. Bu mühür aktifse, ilişkinizde analitik bakış, öğrenme aşkı ve detaylara dikkat öne çıkar; birlikte dünyayı keşfetmekten keyif alırsınız. Yargısı şudur: Merakınızı paylaşım olarak yaşadığınızda bu mühür size hem anlayış hem başarı kazandırır; ancak aşırı eleştirellik ve duygusal mesafe, sıcaklığı azaltabilir. Kalbinizi de gözlemleyin, sadece yıldızları değil.",
        "etkiler": {
            "ask": {
                "Genel": "Meraklı, öğrenmeye açık ve analitik bir sevgi dili."
            },
            "evlilik": {
                "Genel": "Ortak keşifler ve öğrenme üzerine kurulu, gelişen bir birliktelik."
            },
            "zihinsel": {
                "Genel": "Bilim ve araştırmaya yatkın, keskin gözlem gücüne sahip bir zihin."
            },
            "is_hayati": {
                "Genel": "Bilim, teknoloji ve eğitim alanlarında başarı fırsatları."
            }
        }
    },

    "DRUS": {
        "derece": 151.08,  # 1°05' Başak (χ Car) — Drys varyantıyla aynı yıldız
        "yargi": "Drus, güney göğünün sabır ve dayanıklılık mührüdür. Bu mühür aktifse, ilişkinizde zorluklar karşısında yılmadan ilerleme gücü belirir; birlikte uzun vadeli hedeflere sadık kalırsınız. Yargısı şudur: Engelleri aşma kararlılığınızı şefkatle birleştirdiğinizde bu mühür size kalıcı bir güç kazandırır; ancak katılık ve inatçılık, esnek olmanız gereken anlarda sizi zorlayabilir. Sabır, akılla birleştiğinde zaferdir.",
        "etkiler": {
            "ask": {
                "Genel": "Sabırlı, dayanıklı ve uzun vadeli bir sevgi; esneklik gerektirir."
            },
            "evlilik": {
                "Genel": "Zorlukları birlikte aşan, istikrarlı ve kararlı bir birliktelik."
            },
            "maddi": {
                "Genel": "Sabır ve uzun vadeli planlamayla gelen kazançlar."
            },
            "zihinsel": {
                "Genel": "Disiplinli, kararlı ve engelleri gören bir zihin."
            }
        }
    },

    "ALVASHAK": {
        "derece": 132.21,  # 12°13' Aslan (α Lyn) — Al Fahd varyantıyla aynı yıldız
        "yargi": "Alvashak, vaşağın keskin gözleriyle görme mührüdür. Bu mühür aktifse, ilişkinizde incelikleri fark etme ve gizli anlamları okuma yeteneği öne çıkar; birbirinizin söylenmeyen ihtiyaçlarını sezersiniz. Yargısı şudur: Keskin gözlem gücünüzü yargıya değil şefkate dönüştürdüğünüzde bu mühür size derin bir anlayış kazandırır; ancak sürekli tetikte olmak huzursuzluk yaratabilir. Görülen gerçek, sevgiyle karşılanmalıdır.",
        "etkiler": {
            "ask": {
                "Genel": "Sezgisel, ince ayrıntıları fark eden ve şefkatli bir sevgi."
            },
            "evlilik": {
                "Genel": "Karşılıklı sezgi ve anlayış üzerine kurulu, derin bir birliktelik."
            },
            "zihinsel": {
                "Genel": "Keskin gözlem gücüne sahip, gizli anlamları okuyan bir zihin."
            },
            "gizlilikler": {
                "Genel": "Saklı gerçekleri görme yeteneği; tetikte olma eğilimi dengelenmelidir."
            }
        }
    },
}


