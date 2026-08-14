# -*- coding: utf-8 -*-
"""
FBST Meslek Yönlendirme Sistemi — Ebeveyn/Çocuk
Potansiyel ve yetenek alanlarından yola çıkarak çocuğun yatkın olduğu meslekleri önerir.
Her meslek, çocuğun hangi gezegensel enerjiyi kullandığını açıklar.
"""

FBST_MESLEK_EBEVEYN = {
    # ======================================================================
    # SANATSAL YETENEK
    # ======================================================================
    "Sanatsal Yetenek": [
        {
            "meslek": "Müzisyen / Müzik Prodüksiyonu",
            "aciklama": "Duygusal derinlik ve estetik duyarlılık, müziği doğal bir ifade aracı haline getirir. Enstrüman çalmak, beste yapmak veya dijital müzik prodüksiyonu bu potansiyeli besler. Duyguları sese dönüştürme gücü, dinleyicileri derinden etkiler.",
            "gezegenler": "Venüs, Neptün, Ay",
        },
        {
            "meslek": "Görsel Sanatçı (Resim, Dijital Sanat, Fotoğrafçılık)",
            "aciklama": "Form, renk ve kompozisyon algısı güçlüdür. Tuval, dijital ekran veya objektif aracılığıyla iç dünyasını dışa vurabilir. Sanat galerileri, sergi alanları veya dijital platformlarda kendini gösterebilir. Görsel hikaye anlatıcılığında doğal bir yetenek taşır.",
            "gezegenler": "Venüs, Neptün, Uranüs",
        },
        {
            "meslek": "Tasarımcı (Moda, İç Mekan, Grafik, Endüstriyel)",
            "aciklama": "Güzel olanı algılama ve somut ürünlere dönüştürme yeteneği, tasarım dünyasında doğal bir avantaj sağlar. Estetik duyarlılığını fonksiyonel çözümlerle birleştirebilir. Moda, mimari iç mekan, ürün veya grafik tasarımında kendine özgü bir tarz geliştirebilir.",
            "gezegenler": "Venüs, Uranüs, Merkür",
        },
        {
            "meslek": "Yazar / Senarist / Şair / Edebiyatçı",
            "aciklama": "Kelimelerle duygularını ve hayal gücünü ifade etme potansiyeli yüksektir. Roman, senaryo, şiir veya köşe yazarlığı gibi alanlarda derin eserler verebilir. Kelimeleri duygusal bir silah gibi kullanma becerisi, onu edebi dünyada öne çıkarır.",
            "gezegenler": "Merkür, Neptün, Venüs",
        },
        {
            "meslek": "Oyuncu / Sahne Sanatçısı / Dansçı",
            "aciklama": "Tutkulu ve enerjik yapısı, sahne performansında parlamasını sağlar. Tiyatro, sinema, dans veya müzikal gibi canlı ve enerjik alanlarda kendini gösterebilir. Başka birinin hayatına bürünme ve duyguları beden diliyle aktarma konusunda doğal bir yetenek taşır.",
            "gezegenler": "Mars, Venüs, Neptün",
        },
        {
            "meslek": "Film Yönetmeni / Yapımcı",
            "aciklama": "Görsel anlatım ve hikayeleme becerisi, sinema dünyasında güçlü bir temel oluşturur. Farklı sanat disiplinlerini bir araya getirerek bütüncül bir eser yaratma potansiyeli taşır. Teknik bilgi ve sanatsal vizyonun buluştuğu noktada başarılı olabilir.",
            "gezegenler": "Neptün, Uranüs, Güneş",
        },
        {
            "meslek": "Ses Sanatçısı / Ses Tasarımcısı",
            "aciklama": "Seslere ve müzikalitelere karşı doğal bir hassasiyet, ses mühendisliği, podcast production veya sesli kitap seslendirme gibi alanlarda güçlü bir avantaj sağlar. Duyguları ses aracılığıyla aktarma konusunda eşsiz bir yetenek taşır.",
            "gezegenler": "Neptün, Venüs, Merkür",
        },
        {
            "meslek": "Animasyon / VFX / Oyun Tasarımcısı",
            "aciklama": "Hayal gücünü dijital dünyada hayata geçirme potansiyeli, animasyon, görsel efekt veya oyun tasarımında güçlü bir avantaj sağlar. Sanat ve teknolojinin buluştuğu bu alanda orijinal的世界ler yaratabilir.",
            "gezegenler": "Uranüs, Venüs, Neptün",
        },
    ],

    # ======================================================================
    # ZİHİNSEL YETENEK
    # ======================================================================
    "Zihinsel Yetenek": [
        {
            "meslek": "Yazılım Mühendisi / Veri Bilimci / Yapay Zeka Uzmanı",
            "aciklama": "Hızlı ve yenilikçi zihni, kod yazma, algoritma geliştirme ve yapay zeka modelleri oluşturma gibi alanlarda doğal bir avantaj sağlar. Teknoloji dünyasında sıra dışı başarılara imza atabilir. Soyut problemleri somut çözümlere dönüştürme gücü yüksektir.",
            "gezegenler": "Merkür, Uranüs, Satürn",
        },
        {
            "meslek": "Araştırmacı / Bilim İnsanı / Akademisyen",
            "aciklama": "Derinlemesine analiz yapma ve yüzeysel bilgiyle yetinmeme becerisi, bilimsel araştırma dünyasında güçlü bir temel oluşturur. Fizik, biyokimya, nörobilim, genetik gibi alanlarda keşifler yapabilir. Hipotez kurma ve deney tasarlama konusunda doğal bir yetenek taşır.",
            "gezegenler": "Merkür, Plüton, Satürn",
        },
        {
            "meslek": "Mühendis (Bilgisayar, Elektrik, Makine, İnşaat)",
            "aciklama": "Yapılandırılmış düşünce ve problem çözme yeteneği, mühendislik alanlarında somut projelere dönüşebilir. Somut sonuçlar üretme arzusu güçlüdür. Sistemleri anlama, analiz etme ve iyileştirme konusunda doğal bir beceri taşır.",
            "gezegenler": "Merkür, Satürn, Uranüs",
        },
        {
            "meslek": "Matematikçi / İstatistikçi / Aktüer",
            "aciklama": "Soyut düşünme ve mantıksal çıkarım gücü, matematiksel modeller ve istatistiksel analizler konusunda doğal bir yetenek taşır. Risk hesaplama, veri modelleme ve kriptografi gibi alanlarda güçlü bir potansiyel gösterir.",
            "gezegenler": "Merkür, Satürn, Uranüs",
        },
        {
            "meslek": "Hukukçu / Avukat / Hakim",
            "aciklama": "Geniş perspektifli düşünce ve ikna kabiliyeti, hukuk dünyasında güçlü bir avantaj sağlar. Farklı bakış açılarını birleştirme ve karmaşık yasal metinleri analiz etme becerisi öne çıkar. Adalet duygusu ve stratejik düşünme yeteneği onu bu alanda başarılı kılar.",
            "gezegenler": "Merkür, Jüpiter, Satürn",
        },
        {
            "meslek": "Tıp Uzmanı / Cerrah / Tıbbi Araştırmacı",
            "aciklama": "Detaylara dikkat, sabır ve bilimsel merak, tıp alanında güçlü bir temel oluşturur. İnsan vücudunu anlama ve iyileştirme konusunda doğal bir yetenek taşır. Cerrahi hassasiyet, teşhis koyma veya tıbbi araştırma gibi alanlarda başarılı olabilir.",
            "gezegenler": "Merkür, Satürn, Chiron",
        },
        {
            "meslek": "Ekonomist / Finans Analisti / İş Analisti",
            "aciklama": "Sayısal analiz ve sistemleri anlama becerisi, ekonomi ve finans dünyasında güçlü bir avantaj sağlar. Piyasa trendlerini okuma,.modelleme yapma ve stratejik kararlar verme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Merkür, Satürn, Jüpiter",
        },
    ],

    # ======================================================================
    # LİDERLİK
    # ======================================================================
    "Liderlik": [
        {
            "meslek": "Girişimci / İş İnsanı / Kurucu",
            "aciklama": "Doğal liderlik enerjisi ve kararlılığı, kendi işini kurma potansiyelini güçlü kılar. Cesur adımlar atma ve insanları mobilize etme becerisi ön plandadır. Risk alma ve fırsatları değerlendirme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Güneş, Mars, Jüpiter",
        },
        {
            "meslek": "Yönetici / CEO / Genel Müdür",
            "aciklama": "Yapı, disiplin ve sorumluluk duygusu, yönetim pozisyonlarında güçlü bir liderlik potansiyeli taşır. Takımları yönlendirme, stratejik kararlar alma ve kaynakları verimli kullanma konusunda doğal bir yetenek sergiler.",
            "gezegenler": "Güneş, Satürn, Jüpiter",
        },
        {
            "meslek": "Siyasetçi / Devlet Adamı / Sivil Topplum Lideri",
            "aciklama": "Geniş vizyonu ve insanları ikna etme gücü, siyasi arenada veya sivil toplum örgütlerinde etkili bir rol oynamasını sağlar. Toplumsal sorunlara çözüm üretme ve kitleleri harekete geçirme konusunda doğal bir liderlik sergiler.",
            "gezegenler": "Güneş, Jüpiter, Uranüs",
        },
        {
            "meslek": "Askeri Lider / Komutan / Acil Durum Yöneticisi",
            "aciklama": "Sabır, dayanıklılık ve stratejik düşünceyi birleştiren liderlik tarzı, kriz dönemlerinde ve zorlu koşullarda parlamasını sağlar. Baskı altında doğru kararları alma ve insanları yönlendirme konusunda güçlü bir yetenek taşır.",
            "gezegenler": "Mars, Satürn, Güneş",
        },
        {
            "meslek": "Eğitim Lideri / Okul Müdürü / Akademi Başkanı",
            "aciklama": "Bilgiyi taşıma ve gelecek nesilleri yetiştirme vizyonu, eğitim yönetiminde güçlü bir avantaj sağlar. Eğitimcileri destekleme, müfredat geliştirme ve kurumsal strateji oluşturma konusunda doğal bir liderlik sergiler.",
            "gezegenler": "Jüpiter, Satürn, Güneş",
        },
        {
            "meslek": "Spor Kulübü Başkanı / Spor Yöneticisi",
            "aciklama": "Rekabet ruhu ve takım çalışması becerisi, spor yönetiminde güçlü bir avantaj sağlar. Performans analizi, strateji geliştirme ve sporcuları motive etme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Mars, Güneş, Jüpiter",
        },
        {
            "meslek": "STK Başkanı / Sosyal Girişimci",
            "aciklama": "Toplumsal sorunlara duyarlılık ve çözüm üretme arzusu, sivil toplum kuruluşlarında güçlü bir liderlik potansiyeli taşır. Fark yaratma motivasyonu ve insanları bir araya getirme becerisi onu bu alanda öne çıkarır.",
            "gezegenler": "Güneş, Uranüs, Jüpiter",
        },
    ],

    # ======================================================================
    # YARDIMSEVERLİK
    # ======================================================================
    "Yardımseverlik": [
        {
            "meslek": "Doktor / Hemşire / Ebe / Acil Tıp Uzmanı",
            "aciklama": "Başkalarının acısını derinden hissetme ve şifalama potansiyeli, sağlık alanında güçlü bir motivasyon kaynağıdır. Tıp, hemşirelik, ebelik veya acil tıp alanlarında doğal bir yetenek taşır. İnsan hayatına dokunma ve iyileştirme arzusu güçlüdür.",
            "gezegenler": "Neptün, Chiron, Ay",
        },
        {
            "meslek": "Psikolog / Psikoterapist / Psk. Danışman",
            "aciklama": "Duygusal derinlik ve başkalarını anlama becerisi, psikoloji ve terapi alanında güçlü bir temel oluşturur. İnsanların iç dünyasını anlama, travmaları şifalandırma ve duygusal iyileşme süreçlerine eşlik etme konusunda doğal bir yetenek sergiler.",
            "gezegenler": "Chiron, Neptün, Plüton",
        },
        {
            "meslek": "Öğretmen / Eğitimci / Özel Eğitim Uzmanı",
            "aciklama": "Bilgiyi aktarma ve başkalarını besleme arzusu, eğitim alanında güçlü bir motivasyon kaynağıdır. Çocuklarla çalışma, özel eğitim, rehberlik veya akademik danışmanlık gibi alanlarda parlayabilir. Sabırlı ve besleyici yapısı onu doğal bir öğretmen kılar.",
            "gezegenler": "Jüpiter, Ay, Venüs",
        },
        {
            "meslek": "Sosyal Hizmet Uzmanı / Psikososyal Danışman",
            "aciklama": "Toplumsal sorunlara duyarlılık ve yardımseverlik potansiyeli, sosyal hizmetler ve sosyal adalet alanlarında güçlü bir etki yaratabilir. Koruyucu aile danışmanlığı, madde bağımlılığı rehabilitasyonu veya sokak çocukları ile çalışma gibi alanlarda başarılı olabilir.",
            "gezegenler": "Neptün, Ay, Uranüs",
        },
        {
            "meslek": "Diyetisyen / Beslenme Uzmanı / Sağlıklı Yaşam Koçu",
            "aciklama": "Besleyen ve şifalayan enerjisi, beslenme bilimleri ve sağlıklı yaşam danışmanlığında doğal bir yetenek sergiler. Beden-zihin-ruh dengesini koruma, hastalıkları beslenmeyle tedavi etme ve yaşam tarzı danışmanlığı konusunda güçlü bir potansiyel taşır.",
            "gezegenler": "Ceres, Neptün, Ay",
        },
        {
            "meslek": "Fizyoterapist / Rehabilitasyon Uzmanı",
            "aciklama": "İnsanların fiziksel acılarını anlama ve iyileştirme potansiyeli, fizyoterapi alanında güçlü bir avantaj sağlar. Beden mekaniğini anlama, egzersiz programları tasarlama ve rehabilitasyon süreçlerine eşlik etme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Chiron, Mars, Ay",
        },
        {
            "meslek": "Hemşire / Ameliyat Hemşiresi / Yoğun Bakım Hemşiresi",
            "aciklama": "Şefkat ve bakım verme enerjisi, hemşirelik mesleğinde güçlü bir temel oluşturur. Hasta bakımı, acil durum müdahalesi ve yoğun bakım süreçlerinde sabırlı ve dikkatli bir yaklaşım sergiler. İnsan hayatına doğrudan dokunma motivasyonu yüksektir.",
            "gezegenler": "Ay, Neptün, Chiron",
        },
        {
            "meslek": "Ebe / Kadın Doğum Uzmanı",
            "aciklama": "Hayatın başlangıcına eşlik etme ve anne-bebek bağını destekleme potansiyeli, ebelik alanında güçlü bir manevi motivasyon kaynağıdır. Doğal doğum, emzirme danışmanlığı ve anne sağlığı konusunda doğal bir yetenek taşır.",
            "gezegenler": "Ay, Ceres, Neptün",
        },
    ],

    # ======================================================================
    # BİLGELİK
    # ======================================================================
    "Bilgelik": [
        {
            "meslek": "Akademisyen / Profesör / Bilim İnsanı",
            "aciklama": "Geniş perspektifi somut sonuçlara dönüştürme ve bilgiyi derinleştirme yeteneği, akademik dünyada güçlü bir temel oluşturur. Araştırma ve eğitim bir arada yürütebilir. Bilimsel literatürü anlama, eleştirel analiz etme ve yeni bilgi üretme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Jüpiter, Satürn, Merkür",
        },
        {
            "meslek": "Felsefeci / Düşünür / Etik Danışmanı",
            "aciklama": "Hayatin derinliklerini kavrama ve başkalarına aktarma potansiyeli, felsefe alanında güçlü bir bilgelik sergileyebilir. Soyut kavramları somut tartışma konularına dönüştürebilir. Ahlaki ikilemleri analiz etme ve etik çerçeve oluşturma konusunda başarılı olabilir.",
            "gezegenler": "Jüpiter, Plüton, Neptün",
        },
        {
            "meslek": "Strateji Danışmanı / Yönetim Danışmanı / CEO Danışmanı",
            "aciklama": "Geniş bir perspektifi somut planlara dönüştürme becerisi, iş dünyasında strateji danışmanlığı alanında güçlü bir avantaj sağlar. Kurumsal dönüşüm, birleşme ve satın almalar, uzun vadeli strateji geliştirme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Jüpiter, Satürn, Plüton",
        },
        {
            "meslek": "Din Adamı / Manevi Rehber / Ruhani Lider",
            "aciklama": "Manevi bilgelik ve sezgisel anlayış, dini veya manevi rehberlik alanında güçlü bir potansiyel taşır. Farklı inanç sistemlerini anlama ve aktarma konusunda doğal bir yetenek sergiler. Topluma manevi rehberlik etme ve manevi danışmanlık yapma arzusu güçlüdür.",
            "gezegenler": "Neptün, Jüpiter, Satürn",
        },
        {
            "meslek": "Tarihçi / Arkeolog / Kültürel Miras Uzmanı",
            "aciklama": "Geçmişi anlama ve geleceğe aktarma potansiyeli, tarih ve arkeoloji alanında güçlü bir bilgelik sergiler. Kültürel mirası koruma, tarihsel analiz yapma ve medeniyetlerin演变imi konusunda doğal bir yetenek taşır.",
            "gezegenler": "Satürn, Jüpiter, Plüton",
        },
        {
            "meslek": "Yazar / Düşünür / Köşe Yazarı",
            "aciklama": "Derin düşünce ve analiz yeteneği, yazılı medyada güçlü bir avantaj sağlar. Toplumsal olayları derinlemesine analiz etme, eleştirel yazılar yazma ve kamuoyunu yönlendirme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Merkür, Jüpiter, Plüton",
        },
    ],

    # ======================================================================
    # YENİLİKÇİLİK
    # ======================================================================
    "Yenilikçilik": [
        {
            "meslek": "Teknoloji Girişimcisi / İcatçı / Ar-Ge Yöneticisi",
            "aciklama": "Statükoyu sorgulayan ve yeni çözümler üreten zihin yapısı, teknoloji dünyasında çığır açıcı işler yapma potansiyelini taşır. Yazılım, yapay zeka, biyoteknoloji, enerji gibi alanlarda öncü olabilir. Problemleri alışılmadık şekillerde çözme becerisi yüksektir.",
            "gezegenler": "Uranüs, Merkür, Jüpiter",
        },
        {
            "meslek": "Bilim İnsanı / Araştırmacı / Mucit",
            "aciklama": "Beklenmedik bağlantılar kurma ve yeni keşifler yapma potansiyeli, bilimsel araştırma alanında güçlü bir avantaj sağlar. Fizik, kimya, biyoloji, malzeme bilimi gibi temel bilimlerde öncü çalışmalar yapabilir. Patentlenebilir buluşlar üretme potansiyeli taşır.",
            "gezegenler": "Uranüs, Plüton, Merkür",
        },
        {
            "meslek": "Tasarımcı / Endüstriyel Tasarımcı / UX Tasarımcısı",
            "aciklama": "Alışılmadık formlar ve orijinal çözümler üretme yeteneği, tasarım dünyasında kendine özgü bir yol çizmesini sağlar. Kullanıcı deneyimi, ürün tasarımı, mimari tasarım veya dijital tasarım alanlarında parlayabilir. Fonksiyonelliği estetikle birleştirme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Uranüs, Venüs, Mars",
        },
        {
            "meslek": "Dijital Pazarlamacı / Sosyal Medya Stratejisti / Growth Hacker",
            "aciklama": "Yenilikçi iletişim yöntemleri ve dijital dünyaya doğal yatkınlık, pazarlama alanında güçlü bir avantaj sağlar. Sosyal medya, içerik üretimi, dijital reklamcılık ve büyüme hacking konularında başarılı olabilir. Veri odaklı karar alma ve trendleri öngörme becerisi yüksektir.",
            "gezegenler": "Uranüs, Merkür, Venüs",
        },
        {
            "meslek": "Robotik Mühendisi / Otomasyon Uzmanı",
            "aciklama": "Teknolojiyi yeniden şekillendirme ve otomasyon sistemleri tasarlama potansiyeli, robotik alanında güçlü bir avantaj sağlar. Endüstriyel otomasyon, insansı robotlar veya otonom sistemler geliştirme konusunda öncü olabilir.",
            "gezegenler": "Uranüs, Satürn, Merkür",
        },
        {
            "meslek": "Enerji Mühendisi / Yenilenebilir Enerji Uzmanı",
            "aciklama": "Geleceğin enerji çözümlerini tasarlama potansiyeli, yenilenebilir enerji alanında güçlü bir avantaj sağlar. Güneş, rüzgar, hidrojen veya nükleer fusyon teknolojileri geliştirme konusunda öncü çalışmalar yapabilir.",
            "gezegenler": "Uranüs, Jüpiter, Plüton",
        },
    ],

    # ======================================================================
    # GİRİŞİMCİLİK
    # ======================================================================
    "Girişimcilik": [
        {
            "meslek": "Kurucu Girişimci (Startup Kurucusu)",
            "aciklama": "Cesareti, enerjisi ve kararlılığıyla kendi işini kurma potansiyeli güçlüdür. Risk alma ve hızlı karar alma becerisi, girişimcilik dünyasında doğal bir avantaj sağlar. Sıfırdan bir şey inşa etme arzusu ve dayanıklılık onu bu alanda başarılı kılar.",
            "gezegenler": "Mars, Güneş, Jüpiter",
        },
        {
            "meslek": "Satış ve Pazarlama Müdürü / CMO",
            "aciklama": "İkna kabiliyeti ve enerjisi, satış ve pazarlama alanında güçlü bir performans sergilemesini sağlar. İnsanlarla etkili iletişim kurma, müşteri ihtiyaçlarını anlama ve fırsatları değerlendirme konusunda doğal bir yetenek taşır. Hedef odaklı çalışma becerisi yüksektir.",
            "gezegenler": "Merkür, Mars, Güneş",
        },
        {
            "meslek": "E-ticaret Girişimcisi / Dijital İş Modelleri",
            "aciklama": "Teknolojiye yatkınlık ve yenilikçi iş modelleri geliştirme potansiyeli, e-ticaret dünyasında güçlü bir avantaj sağlar. Dijital platformlar, abonelik modelleri veya pazar yeri iş modelleri kurma konusunda başarılı olabilir.",
            "gezegenler": "Uranüs, Mars, Merkür",
        },
        {
            "meslek": "Uluslararası Ticaret Uzmanı / İhracatçı / İthalatçı",
            "aciklama": "Geniş perspektifi ve macera ruhu, uluslararası iş yapma konusunda güçlü bir motivasyon kaynağıdır. Farklı kültürleri anlama, küresel pazarlarda çalışma ve uluslararası tedarik zincirleri yönetme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Jüpiter, Mars, Güneş",
        },
        {
            "meslek": "Gayrimenkul Yatırımcısı / İnşaat Girişimcisi",
            "aciklama": "Somut projeler üretme ve uzun vadeli yatırım yapma becerisi, gayrimenkul alanında güçlü bir avantaj sağlar. Piyasa analizi, risk değerlendirme ve büyük ölçekli projeleri yönetme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Satürn, Mars, Jüpiter",
        },
        {
            "meslek": "Restoran Sahibi / Gastro İşletmeci / Şef",
            "aciklama": "Yaratıcılık ve girişimcilik ruhunun buluştuğu gastronomi alanında güçlü bir potansiyel taşır. Lezzet geliştirme, mekan tasarımı ve müşteri deneyimi konusunda doğal bir yetenek sergiler. Yemeği sanata dönüştürme arzusu güçlüdür.",
            "gezegenler": "Venüs, Mars, Güneş",
        },
        {
            "meslek": "Franchise Sahibi / Zincir İşletmeci",
            "aciklama": "Mevcut iş modellerini anlama ve ölçeklendirme becerisi, franchise alanında güçlü bir avantaj sağlar. Operasyonel verimlilik, marka yönetimi ve sistem kurma konusunda doğal bir yetenek taşır. Büyüme odaklı düşünme tarzı onu bu alanda başarılı kılar.",
            "gezegenler": "Jüpiter, Satürn, Mars",
        },
    ],

    # ======================================================================
    # İLETİŞİM
    # ======================================================================
    "İletişim": [
        {
            "meslek": "Gazeteci / Muhabir / Muhabir",
            "aciklama": "Hızlı ve etkili iletişim kurma becerisi, bilgiyi araştırma ve aktarma konusunda güçlü bir temel oluşturur. Haber peşinde koşma, doğruyu ortaya çıkarma ve toplumu bilgilendirme potansiyeli taşır. Araştırmacı gazetecilik konusunda doğal bir yetenek sergiler.",
            "gezegenler": "Merkür, Mars, Uranüs",
        },
        {
            "meslek": "Sunucu / Spiker / YouTuber / Podcaster",
            "aciklama": "Çekici iletişim tarzı ve kendini ifade etme gücü, kamera veya mikrofon önü performansında doğal bir avantaj sağlar. Dinleyiciyi etkileme, bilgiyi eğlenceli aktarma ve geniş kitlelere ulaşma konusunda başarılı olabilir. Sahne hakimiyeti yüksektir.",
            "gezegenler": "Merkür, Venüs, Güneş",
        },
        {
            "meslek": "Yazar / İçerik Üretici / Blogger / Influencer",
            "aciklama": "Güzel sözler ve derin iletişim yeteneği, yazılı veya dijital içerik üretiminde güçlü bir temel oluşturur. Blog, kitap, senaryo, sosyal medya içeriği veya dijital yayınlar konusunda doğal bir yetenek taşır. Kelimeleri etkili kullanma becerisi onu bu alanda öne çıkarır.",
            "gezegenler": "Merkür, Venüs, Neptün",
        },
        {
            "meslek": "Halkla İlişkiler Uzmanı / Kurumsal İletişimci",
            "aciklama": "Çekici ve ikna edici iletişim tarzı, halkla ilişkiler alanında güçlü bir avantaj sağlar. Kurumların imajını yönetme, kriz iletişimini yürütme ve medya ilişkilerini koordine etme konusunda başarılı olabilir. İmaj yönetimi konusunda doğal bir yetenek taşır.",
            "gezegenler": "Venüs, Merkür, Jüpiter",
        },
        {
            "meslek": "Eğitmen / Konuşmacı / Motivasyon Konuşmacısı",
            "aciklama": "Bilgiyi ilham verici bir şekilde aktarma yeteneği, eğitim ve konuşmacılık alanında güçlü bir avantaj sağlar. Sahne hakimiyeti, ikna edici anlatım ve dinleyicileri harekete geçirme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Jüpiter, Merkür, Güneş",
        },
        {
            "meslek": "Çevirmen / Dilbilimci / Terminoloji Uzmanı",
            "aciklama": "Dillere karşı doğal bir yatkınlık ve kültürel anlayış, çeviri ve dilbilim alanında güçlü bir avantaj sağlar. Eş zamanlı çeviri, teknik çeviri veya dilbilimsel araştırma konusunda başarılı olabilir. Farklı diller arasında köprü kurma becerisi yüksektir.",
            "gezegenler": "Merkür, Neptün, Jüpiter",
        },
    ],

    # ======================================================================
    # MANEVİYAT
    # ======================================================================
    "Maneviyat": [
        {
            "meslek": "Meditasyon Eğitmeni / Yoga Öğretmeni / Mindfulness Uzmanı",
            "aciklama": "Ruhsal ve sezgisel bir rehberlik potansiyeli, meditasyon ve yoga alanında güçlü bir motivasyon kaynağıdır. İç huzuru bulma ve başkalarına aktarma konusunda doğal bir yetenek taşır. Farkındalık temelli yaklaşımlar konusunda derin bir bilgi birikimine sahiptir.",
            "gezegenler": "Neptün, Jüpiter, Satürn",
        },
        {
            "meslek": "Manevi Danışman / Ruhani Rehber / Yaşam Koçu",
            "aciklama": "Sezgisel hassasiyet ve manevi derinlik, manevi danışmanlık alanında güçlü bir temel oluşturur. İnsanların ruhsal yolculuğuna rehberlik etme, yaşam amacı bulma ve içsel dönüşüm süreçlerine eşlik etme konusunda doğal bir yetenek sergiler.",
            "gezegenler": "Neptün, Jüpiter, Plüton",
        },
        {
            "meslek": "Enerji Şifacısı / Reiki Uygulayıcısı / Kristal Terapist",
            "aciklama": "Enerjileri derinden hissetme ve dönüştürme potansiyeli, enerji çalışmaları ve holistic terapi alanında güçlü bir avantaj sağlar. Reiki, kristal terapi, ses terapisi, aromaterapi gibi alternatif tıp alanlarında doğal bir yetenek taşır. İnce enerjileri algılama konusunda hassastır.",
            "gezegenler": "Neptün, Chiron, Uranüs",
        },
        {
            "meslek": "Din Bilimci / İlahiyatçı / Karşılaştırmalı Dinler Uzmanı",
            "aciklama": "Farklı manevi gelenekleri keşfetme ve anlama potansiyeli, din bilimleri alanında güçlü bir temel oluşturur. Karşılaştırmalı din çalışmaları, teoloji ve manevi araştırma konularında başarılı olabilir. Farklı inanç sistemleri arasında köprü kurma becerisi yüksektir.",
            "gezegenler": "Neptün, Jüpiter, Satürn",
        },
        {
            "meslek": "Astrolog / Kadersel Danışman",
            "aciklama": "Kozmik döngüleri anlama ve insanlara rehberlik etme potansiyeli, astroloji alanında güçlü bir avantaj sağlar. Natal harita analizi, transit yorumları ve kadersel danışmanlık konusunda doğal bir yetenek taşır. Evrensel desenleri okuma becerisi yüksektir.",
            "gezegenler": "Neptün, Jüpiter, Uranüs",
        },
        {
            "meslek": "Shaman / Şamanik Uygulayıcı / İçsel Çocuk Terapisti",
            "aciklama": "Ruh dünyasıyla bağlantı kurma ve şifa verme potansiyeli, shamanik uygulamalarda güçlü bir avantaj sağlar. Rüya çalışmaları, içsel çocuk şifası, atalarla çalışma gibi derin ruhsal süreçlerde doğal bir yetenek taşır.",
            "gezegenler": "Neptün, Plüton, Chiron",
        },
    ],

    # ======================================================================
    # STRATEJİK ZEKA
    # ======================================================================
    "Stratejik Zeka": [
        {
            "meslek": "İstihbarat Analisti / Güvenlik Uzmanı / Siber Güvenlik Uzmanı",
            "aciklama": "Karmaşık durumları derinlemesine analiz etme ve stratejik çözümler üretme potansiyeli, istihbarat ve güvenlik alanında güçlü bir avantaj sağlar. Bilgiyi toplama, değerlendirme ve tehditleri öngörme konusunda doğal bir yetenek taşır. Siber güvenlik, siber istihbarat veya fiziksel güvenlik alanında başarılı olabilir.",
            "gezegenler": "Plüton, Merkür, Satürn",
        },
        {
            "meslek": "Finans Analisti / Yatırım Uzmanı / Portföy Yöneticisi",
            "aciklama": "Derinlemesine analiz ve stratejik karar alma yeteneği, finans dünyasında güçlü bir temel oluşturur. Piyasa trendlerini okuma, risk yönetimi yapma ve uzun vadeli yatırım planları oluşturma konusunda başarılı olabilir. Sayısal zeka ve sezgisel piyasa okuma becerisi yüksektir.",
            "gezegenler": "Plüton, Satürn, Jüpiter",
        },
        {
            "meslek": "Avukat / Hakim / Savcı",
            "aciklama": "Güç dinamiklerini anlama ve stratejik bir şekilde kullanma potansiyeli, hukuk alanında güçlü bir avantaj sağlar. Karmaşık davaları analiz etme, stratejik savunma veya kovuşturma yapma ve adaleti tesis etme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Plüton, Mars, Satürn",
        },
        {
            "meslek": "Askeri Stratejist / Politik Analist / Diplomat",
            "aciklama": "Stratejik güç kullanımı ve derin analiz yeteneği, askeri, politik veya diplomatik alanda güçlü bir temel oluşturur. Uzun vadeli planlama, kriz yönetimi ve uluslararası ilişkiler konusunda başarılı olabilir. Güç dengelerini okuma becerisi yüksektir.",
            "gezegenler": "Mars, Plüton, Satürn",
        },
        {
            "meslek": "Siber Güvenlik Mimarı / Veri Güvenliği Uzmanı",
            "aciklama": "Sistemleri anlama ve savunma stratejileri geliştirme potansiyeli, siber güvenlik alanında güçlü bir avantaj sağlar. Hackling önleme, güvenlik protokolleri tasarlama ve siber tehditleri analiz etme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Plüton, Uranüs, Satürn",
        },
        {
            "meslek": "Risk Yöneticisi / Sigorta Uzmanı / Aktüer",
            "aciklama": "Riskleri öngörme ve stratejik çözümler üretme becerisi, risk yönetimi alanında güçlü bir avantaj sağlar. Olasılık hesaplama, senaryo analizi ve kriz hazırlığı konusunda doğal bir yetenek taşır. Belirsizlik altında doğru kararları alma konusunda başarılı olabilir.",
            "gezegenler": "Satürn, Plüton, Merkür",
        },
    ],

    # ======================================================================
    # ZANAATKARLIK / ESNAF / USTA
    # ======================================================================
    "Zanaatkarlık": [
        {
            "meslek": "Kuaför / Berber / Güzellik Uzmanı",
            "aciklama": "Estetik algı ve ellerin becerisi, saç tasarımı, cilt bakımı veya makyaj gibi alanlarda güçlü bir doğal yetenek sağlar. İnsanların görünümünü dönüştürme gücü, hem yaratıcı bir ifade hem de sosyal bir bağ kurma aracıdır. Venüs'ün güzellik enerjisini somut bir sanata dönüştürür.",
            "gezegenler": "Venüs, Mars, Ay",
        },
        {
            "meslek": "Marangoz / Ahşap Ustası / Mobilyacı",
            "aciklama": "Ham malzemeyi işleyerek işlevsel ve güzel nesneler yaratma gücü, marangozluğu güçlü bir zanaatkarlık alanı yapar. Ahşabın doğasını anlama, ölçü hassasiyeti ve estetik compositing bu alanda öne çıkan yeteneklerdir. Somut ve kalıcı eserler bırakma arzusu güçlüdür.",
            "gezegenler": "Satürn, Venüs, Mars",
        },
        {
            "meslek": "Kuyumcu / Saatçi / Değerli Taş Uzmanı",
            "aciklama": "İnce detay algısı, hassasiyet ve estetik duyarlılık, kuyumculuk ve saatçilik gibi ince işçilik gerektiren alanlarda doğal bir avantaj sağlar. Değerli malzemelerle çalışma sabır ve titizlik ister; bu enerjiler Satürn ve Venüs tarafından yönetilir.nadide eserler yaratma potansiyeli yüksektir.",
            "gezegenler": "Venüs, Satürn, Merkür",
        },
        {
            "meslek": "Elektrikçi / Elektronik Teknisyeni",
            "aciklama": "Elektrik devrelerini anlama, arıza tespit etme ve sistemleri çalışır hale getirme becerisi, Uranüs'ün yenilikçi ve teknolojik enerjisiyle güçlü bir uyum sağlar. Görünmeyen enerji akışlarını anlama ve yönlendirme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Uranüs, Merkür, Satürn",
        },
        {
            "meslek": "Tesisatçı / Sıhhi Tesisat Ustası",
            "aciklama": "Sistemleri anlama, boru döşeme, su ve ısıtma tesisatı kurma becerisi, somut ve işlevsel çözümler üretme gücünü yansıtır. Mars'ın eylem odaklı enerjisi ve Satürn'ün yapısal düşüncesi bu alanda güçlü bir sinerji yaratır.",
            "gezegenler": "Mars, Satürn, Merkür",
        },
        {
            "meslek": "Kaynakçı / Metal İşçisi / Kolluk Ustası",
            "aciklama": "Ateş ve metal ile çalışma gücü, kaynakçılık ve metal işleme gibi fiziksel ve teknik beceri gerektiren alanlarda Mars enerjisinin en somut ifadesidir. Güçlü ellere, dayanıklılığa ve ısıya karşı hassasiyet gerektirir.",
            "gezegenler": "Mars, Satürn, Güneş",
        },
        {
            "meslek": "Boyacı / Dekoratör / Duvar Kağıdı Ustası",
            "aciklama": "Renk algısı ve mekan dönüştürme becerisi, boya ve dekorasyon işlerinde estetik ve pratik yeteneğin buluştuğu güçlü bir alan. Venüs'ün renk ve güzellik enerjisini somut mekanlara uygulama potansiyeli taşır.",
            "gezegenler": "Venüs, Neptün, Uranüs",
        },
        {
            "meslek": "Terzi / Dikim Ustası / Moda Konfeksiyon",
            "aciklama": "Kumaş anlayışı, beden ölçümü ve dikim becerisi, Venüs'ün estetik enerjisini somut giysilere dönüştürme gücüdür. El becerisi, detay algısı ve kişinin tarzını anlama konusunda doğal bir yetenek taşır.",
            "gezegenler": "Venüs, Mars, Merkür",
        },
        {
            "meslek": "Fırıncı / Pastacı / Unlu Mamul Ustası",
            "aciklama": "Besinleri dönüştürme sanatı, Ay'ın beslenme ve bakım enerjisinin en lezzetli ifadesidir. Hamur yoğurma, pişirme süreleri ve tat uyumu konusunda doğal bir sezgi taşır. Aromalar ve dokularla yaratıcılık güçlüdür.",
            "gezegenler": "Ay, Venüs, Satürn",
        },
        {
            "meslek": "Kahveci / Lokantacı / Aşçı / Gastro İşletmeci",
            "aciklama": "Tat algısı, yemek pişirme sanatı ve insanları besleme arzusu, Jüpiter'in bereket ve paylaşma enerjisiyle güçlü bir uyum sağlar. Mutfakta yaratıcılık, hız ve organizasyon becerisi bu alanda doğal bir avantaj sağlar.",
            "gezegenler": "Jüpiter, Ay, Venüs",
        },
        {
            "meslek": "Oto Tamircisi / Motor Ustası / Mekanik",
            "aciklama": "Makineleri anlama, arıza bulma ve onarma becerisi, Mars'ın mekanik enerjisi ve Uranüs'ün teknolojik zekasının güçlü bir birleşimidir. Somut meselelere somut çözümler üretme konusunda doğal bir yetenek taşır.",
            "gezegenler": "Mars, Uranüs, Satürn",
        },
        {
            "meslek": "Tamirci / Teknik Servis / Beyaz Eşya Ustası",
            "aciklama": "Bozulan şeyleri onarma ve sistemi tekrar çalışır hale getirme gücü, hem zihinsel analiz hem de pratik el becerisi gerektirir. Merkür'ün teknik zekası ve Uranüs'ün yenilikçi yaklaşımı bu alanda güçlü bir sinerji yaratır.",
            "gezegenler": "Merkür, Uranüs, Mars",
        },
        {
            "meslek": "Bahçıvan / Peyzaj Ustası / Bitki Uzmanı",
            "aciklama": "Doğayla uyum içinde çalışma, bitkileri anlama ve living alanlar yaratma gücü, toprak elementinin en doğal ifadesidir. Ay'ın döngüsel enerjisi ve Venüs'ün estetik algısı, peyzaj tasarımında güçlü bir sinerji oluşturur.",
            "gezegenler": "Ay, Venüs, Satürn",
        },
        {
            "meslek": "Çiftçi / Ziraatçi / Organik Tarım Uzmanı",
            "aciklama": "Toprağı işleme, ürün yetiştirme ve doğanın döngülerini anlama sabır ve kararlılık gerektirir. Satürn'ün disiplini ve Ay'ın döngüsel enerjisi, tarımsal üretimde güçlü bir temel oluşturur. Toprakla güçlü bir bağ kurma potansiyeli taşır.",
            "gezegenler": "Satürn, Ay, Mars",
        },
        {
            "meslek": "Balıkçı / Denizci / Su Ürünleri Ustası",
            "aciklama": "Denizle çalışma, suyun dillerini okuma ve denizden geçim sağlama Neptün'ün en somut ifadesidir. Sabır, sezgi ve doğa olaylarına karşı hassasiyet, balıkçılık ve denizcilikte doğal bir avantaj sağlar.",
            "gezegenler": "Neptün, Jüpiter, Ay",
        },
        {
            "meslek": "İnşaat İşçisi / İnşaat Ustası / Kalfa",
            "aciklama": "Fiziksel güç, dayanıklılık ve yapı inşa etme becerisi, Mars'ın enerji ve dayanıklılık enerjisinin en somut ifadesidir. Somut yapılar ortaya çıkarma arzusu ve ekip çalışmasıyla uyum sağlama bu alanda güçlü bir temel oluşturur.",
            "gezegenler": "Mars, Satürn, Güneş",
        },
        {
            "meslek": "Taksi Şoförü / Otobüs Şoförü / Nakliyeci",
            "aciklama": "Yol bilme, yön duygusu ve insanları bir noktadan diğerine taşıma becerisi, Merkür'ün iletişim ve hareket enerjisiyle güçlü bir uyum sağlar. Sabır, dikkat ve trafik okuma konusunda doğal bir yetenek taşır.",
            "gezegenler": "Merkür, Mars, Satürn",
        },
        {
            "meslek": "Güvenlik Görevlisi / Bekçi / Koruma",
            "aciklama": "Güvenlik sağlama, çevre okuma ve koruma içgüdüsü, Mars'ın koruyucu enerjisi ve Satürn'ün sınırları belirleme gücüyle güçlü bir sinerji yaratır. Fiziksel dayanıklılık ve dikkat bu alanda doğal bir avantaj sağlar.",
            "gezegenler": "Mars, Satürn, Güneş",
        },
        {
            "meslek": "Köpek Eğitmeni / Hayvan Bakıcısı / Veteriner Teknisyeni",
            "aciklama": "Hayvanlarla doğal bağ kurma ve onları anlama becerisi, Ay'ın bakım ve beslenme enerjisi ile Neptün'ün merhamet enerjisinin güçlü bir birleşimidir. Sabır, sezgi ve empati bu alanda temel yeteneklerdir.",
            "gezegenler": "Ay, Neptün, Venüs",
        },
        {
            "meslek": "Fotoğrafçı / Kameraman / Görsel Prodüksiyon",
            "aciklama": "Anı yakalama, ışık ve kompozisyon algısı, Neptün'ün görsel hayal gücü ve Venüs'ün estetik duyarlılığıyla güçlü bir sinerji yaratır. Hem teknik beceri hem de sanatsal vizyon gerektirir. Dijital çağda güçlü bir zanaatkarlık alanıdır.",
            "gezegenler": "Neptün, Venüs, Merkür",
        },
    ],

    # ======================================================================
    # SPOR / FİZİKSEL PERFORMANS
    # ======================================================================
    "Spor": [
        {
            "meslek": "Profesyonel Futbolcu / Sporcu",
            "aciklama": "Mars'ın eylem ve dayanıklılık enerjisi, Venüs'ün estetik beden algısı ve Jüpiter'in genişleme potansiyeliyle güçlü bir sporcu haritası. Rekabet, hız ve fiziksel koordinasyon bu potansiyelin temel taşlarıdır. Sahanın dışında da liderlik ve karizma taşır.",
            "gezegenler": "Mars, Venüs, Jüpiter",
        },
        {
            "meslek": "Olimpik Sporcu / Atlet / Koşucu",
            "aciklama": "Mars'ın yüksek enerjisi ve Satürn'ün disiplini, olimpik düzeyde performans için güçlü bir temel oluşturur. Hız, güç ve dayanıklılık gerektiren bireysel sporlarda doğal bir avantaj taşır. Rekabetçi ruh ve hedef odaklılık öne çıkar.",
            "gezegenler": "Mars, Satürn, Güneş",
        },
        {
            "meslek": "Antrenör / Teknik Direktör / Spor Eğitmeni",
            "aciklama": "Mars'ın liderlik enerjisi ile Merkür'ün stratejik zekasının güçlü birleşimi. Sporcuları yönlendirme, taktik geliştirme ve performans analizi konusunda doğal bir yetenek taşır. Hem fiziksel bilgi hem de iletişim becerisi gerektirir.",
            "gezegenler": "Mars, Merkür, Satürn",
        },
        {
            "meslek": "Boksör / Dövüş Sporları Uzmanı / MMA Dövüşçüsü",
            "aciklama": "Mars'ın savaşçı enerjisinin en yoğun ifadesi. Güç, refleks, stratejik savaş ve fiziksel dayanıklılık bu alanda temel gereksinimlerdir. Mars'ın Koç veya Akrep burcunda güçlü konumlanması bu potansiyeli destekler.",
            "gezegenler": "Mars, Plüton, Satürn",
        },
        {
            "meslek": "Yüzücü / Su Sporları Uzmanı / Dalış Eğitmeni",
            "aciklama": "Neptün'ün su elementi enerjisi ile Mars'ın fiziksel gücünün birleşimi. Suda hareket etme, nefes kontrolü ve su altı keşfi konusunda doğal bir yetenek taşır. Hem estetik hem de dayanıklılık gerektiren bir alan.",
            "gezegenler": "Neptün, Mars, Ay",
        },
        {
            "meslek": "Kayakçı / Dağ Sporları / Tırmanış Uzmanı",
            "aciklama": "Satürn'ün zirve ve yapı enerjisi ile Mars'ın fiziksel dayanıklılık potansiyelinin güçlü birleşimi. Yüksek irtifa, extreme koşullar ve fiziksel zorluklarla mücadele konusunda doğal bir yetenek taşır. Doğayla uyum içinde çalışma becerisi öne çıkar.",
            "gezegenler": "Satürn, Mars, Uranüs",
        },
        {
            "meslek": "Fitness Koçu / Personal Trainer / Vücut Geliştirme",
            "aciklama": "Mars'ın fiziksel güç enerjisi ile Venüs'ün beden estetiği algısının güçlü birleşimi. Vücut şekillendirme, beslenme planlama ve motivasyon verme konusunda doğal bir yetenek taşır. Başkalarını fiziksel olarak dönüştürme gücü taşır.",
            "gezegenler": "Mars, Venüs, Jüpiter",
        },
        {
            "meslek": "Spor Yorumcusu / Spor Gazetecisi / Analist",
            "aciklama": "Merkür'ün iletişim ve analiz enerjisi ile Jüpiter'in geniş perspektifinin birleşimi. Spor olaylarını okuyucuya aktarma, istatistiksel analiz ve stratejik değerlendirme konusunda doğal bir yetenek taşır. Hem sporsever hem de kelimelerin ustası olma potansiyeli taşır.",
            "gezegenler": "Merkür, Jüpiter, Mars",
        },
        {
            "meslek": "Pilot / Yarış Pilotu / Hava Sporları",
            "aciklama": "Uranüs'ün hız ve teknoloji enerjisi ile Mars'ın eylem odaklılığının güçlü birleşimi. Hız, refleks, mekanik anlayış ve risk yönetimi konusunda doğal bir yetenek taşır. Adrenalin arayışı ve teknik beceri bu alanda temel gereksinimlerdir.",
            "gezegenler": "Uranüs, Mars, Merkür",
        },
        {
            "meslek": "Koç / Atlet / Maratoncu",
            "aciklama": "Mars'ın dayanıklılık enerjisi ile Satürn'ün sabır ve uzun vadeli yapı potansiyelinin güçlü birleşimi. Uzun mesafe koşu, maraton ve dayanıklılık sporlarında doğal bir avantaj taşır. Zihinsel direnç ve fiziksel güç bu alanda kritik öneme sahiptir.",
            "gezegenler": "Mars, Satürn, Jüpiter",
        },
    ],

    # ======================================================================
    # ASKERİYE / GÜVENLİK
    # ======================================================================
    "Askeriye": [
        {
            "meslek": "Subay / Askeri Komutan",
            "aciklama": "Mars'ın savaşçı enerjisi ile Satürn'ün disiplin ve otorite yapısının güçlü birleşimi. Komuta yetenekleri, stratejik planlama ve liderlik konusunda doğal bir yetenek taşır. Askeri hiyerarşide yükselme ve ulusal güvenlik hizmetinde başarılı olabilir.",
            "gezegenler": "Mars, Satürn, Kronos",
        },
        {
            "meslek": "İstihbarat Uzmanı / Analist",
            "aciklama": "Plüton'un gizli bilgi arayışı ile Merkür'ün analitik zekasının birleşimi. Gizli operasyonlar, bilgi toplama ve stratejik analiz konusunda güçlü bir potansiyel taşır. Detaylara duyarlılık ve gizlilik prensiplerine bağlılık bu alanda kritiktir.",
            "gezegenler": "Plüton, Merkür, Satürn",
        },
        {
            "meslek": "Polis / Emniyet Mensubu / Jandarma",
            "aciklama": "Mars'ın koruma enerjisi ile Jüpiter'in adalet arayışının birleşimi. Toplum güvenliği, suçla mücadele ve hukuki süreçlerde başarılı olabilir. Fiziksel dayanıklılık ve etik değerler bu alanda temel gereksinimlerdir.",
            "gezegenler": "Mars, Jüpiter, Satürn",
        },
        {
            "meslek": "Siber Güvenlik Uzmanı",
            "aciklama": "Uranüs'ün teknolojik yenilik enerjisi ile Satürn'ün yapısal güvenliğinin birleşimi. Dijital tehditleri analiz etme, sistemleri koruma ve siber operasyonlarda başarılı olabilir. Teknik bilgi ve stratejik düşünce bu alanda kritiktir.",
            "gezegenler": "Uranüs, Satürn, Plüton",
        },
        {
            "meslek": "Acil Durum Yöneticisi / AFAD / UMKE",
            "aciklama": "Mars'ın hızlı tepki enerjisi ile Jüpiter'in geniş organizasyon yeteneğinin birleşimi. Kriz anlarında hızlı karar verme, koordinasyon ve liderlik konusunda doğal bir yetenek taşır. Stres altında çalışma ve ekip yönetimi bu alanda başarı için önemlidir.",
            "gezegenler": "Mars, Jüpiter, Uranüs",
        },
        {
            "meslek": "Özel Güvenlik / Koruma Ekibi",
            "aciklama": "Mars'ın koruma içgüdüsü ile Plüton'un stratejik zekasının birleşimi. Yüksek profilli kişileri koruma, tehdit analizi ve fiziksel müdahale konusunda güçlü bir potansiyel taşır. Dikkat, disiplin ve fiziksel hazırlık bu alanda kritiktir.",
            "gezegenler": "Mars, Plüton, Satürn",
        },
    ],

    # ======================================================================
    # HUKUK / POLİTİKA
    # ======================================================================
    "Hukuk/Politika": [
        {
            "meslek": "Avukat / Hukukçu",
            "aciklama": "Merkür'ün iletişim ve mantıksal düşünce enerjisi ile Jüpiter'in adalet arayışının birleşimi. Hukuki süreçlerde savunma, müzakere ve argüman geliştirme konusunda doğal bir yetenek taşır. Sözlü ve yazılı iletişim becerileri bu alanda kritiktir.",
            "gezegenler": "Merkür, Jüpiter, Satürn",
        },
        {
            "meslek": "Hakim / Savcı",
            "aciklama": "Satürn'ün adalet ve otorite enerjisi ile Jüpiter'in geniş perspektifinin birleşimi. Hukuki karar verme, delil değerlendirme ve toplumsal adalet konusunda güçlü bir potansiyel taşır. Etik değerler ve tarafsızlık bu alanda temel gereksinimlerdir.",
            "gezegenler": "Satürn, Jüpiter, Merkür",
        },
        {
            "meslek": "Politikacı / Milletvekili / Bakan",
            "aciklama": "Güneş'in liderlik enerjisi ile Jüpiter'in vizyoner yapısının birleşimi. Halkı etkileme, politika oluşturma ve toplumsal dönüşüm konusunda güçlü bir potansiyel taşır. İkna kabiliyeti ve stratejik düşünme bu alanda başarı için kritiktir.",
            "gezegenler": "Güneş, Jüpiter, Plüton",
        },
        {
            "meslek": "Diplomat / Büyükelçi",
            "aciklama": "Venüs'ün uyum enerjisi ile Merkür'ün iletişim becerisinin birleşimi. Uluslararası ilişkiler, kültürel anlayış ve müzakere konusunda doğal bir yetenek taşır. Çapraz kültürel iletişim ve stratejik diplomasi bu alanda success için önemlidir.",
            "gezegenler": "Venüs, Merkür, Jüpiter",
        },
        {
            "meslek": "Anayasa Hukukçusu / Akademisyen",
            "aciklama": "Satürn'ün yapısal düşünce enerjisi ile Jüpiter'in bilgelik potansiyelinin birleşimi. Anayasa hukuku, yasal reform ve akademik araştırma konusunda güçlü bir potansiyel taşır. Derinlemesine analiz ve uzun vadeli düşünme bu alanda kritiktir.",
            "gezegenler": "Satürn, Jüpiter, Merkür",
        },
        {
            "meslek": "Siyaset Bilimci / Politik Analist",
            "aciklama": "Plüton'un güç analiz enerjisi ile Merkür'ün araştırma yeteneğinin birleşimi. Politik süreçleri analiz etme, seçim stratejileri geliştirme ve toplumsal analiz konusunda başarılı olabilir. Nesnellik ve derinlemesine araştırma bu alanda temeldir.",
            "gezegenler": "Plüton, Merkür, Jüpiter",
        },
    ],

    # ======================================================================
    # SAĞLIK / TIP
    # ======================================================================
    "Sağlık/Tıp": [
        {
            "meslek": "Doktor / Hekim",
            "aciklama": "Merkür'ün analitik zekası ile Venüs'ün şifa verme enerjisinin birleşimi. Tıbbi tanı, tedavi planlama ve hasta bakımı konusunda güçlü bir potansiyel taşır. Detaylı analiz ve insaniyet bu alanda kritik öneme sahiptir.",
            "gezegenler": "Merkür, Venüs, Jüpiter",
        },
        {
            "meslek": "Cerrah",
            "aciklama": "Mars'ın keskin ve hızlı enerjisi ile Merkür'ün hassas koordinasyonunun birleşimi. Cerrahi müdahalelerde hassasiyet, hız ve kararlılık konusunda doğal bir yetenek taşır. El-göz koordinasyonu ve stres altında çalışma bu alanda temel gereksinimlerdir.",
            "gezegenler": "Mars, Merkür, Satürn",
        },
        {
            "meslek": "Psikolog / Psikiyatr",
            "aciklama": "Plüton'un derinlemesine analiz enerjisi ile Ay'ın duygusal anlayışının birleşimi. İnsan psikolojisini anlama, travma yönetimi ve terapi konusunda güçlü bir potansiyel taşır. Empati ve analitik düşünce bu alanda birlikte çalışır.",
            "gezegenler": "Plüton, Ay, Neptün",
        },
        {
            "meslek": "Ebe / Hemşire",
            "aciklama": "Ay'ın besleyici enerjisi ile Venüs'ün şefkatli yapısının birleşimi. Yeni yaşamın karşılanması, hasta bakımı ve tıbbi destek konusunda doğal bir yetenek taşır. Sabır, merhamet ve fiziksel dayanıklılık bu alanda kritiktir.",
            "gezegenler": "Ay, Venüs, Chiron",
        },
        {
            "meslek": "Diş Hekimi / Ortodontist",
            "aciklama": "Venüs'ün estetik algısı ile Merkür'ün hassas elllerinin birleşimi. Dental estetik, ağız sağlığı ve hassas müdahaleler konusunda güçlü bir potansiyel taşır. Detaylara duyarlılık ve el becerisi bu alanda success için önemlidir.",
            "gezegenler": "Venüs, Merkür, Satürn",
        },
        {
            "meslek": "Eczacı / Farmakolog",
            "aciklama": "Merkür'ün bilimsel araştırma enerjisi ile Başak'ın detaycı yapısının birleşimi. İlaç etkileşimleri, tedavi protokolleri veFarmakolojik araştırma konusunda başarılı olabilir. Bilimsel titizlik ve hassasiyet bu alanda temeldir.",
            "gezegenler": "Merkür, Satürn, Jüpiter",
        },
        {
            "meslek": "Fizyoterapist / Rehabilitasyon Uzmanı",
            "aciklama": "Chiron'un şifa verme enerjisi ile Venüs'ün uyum yapısının birleşimi. Fiziksel rehabilitasyon, hareket terapisi ve uzun vadeli iyileşme süreçlerinde başarılı olabilir. Sabır, empati ve fiziksel anlayış bu alanda kritiktir.",
            "gezegenler": "Chiron, Venüs, Satürn",
        },
    ],

    # ======================================================================
    # AKADEMİK / ARAŞTIRMA
    # ======================================================================
    "Akademik/Araştırma": [
        {
            "meslek": "Profesör / Akademisyen",
            "aciklama": "Jüpiter'in bilgelik enerjisi ile Satürn'ün yapısal disiplininin birleşimi. Üniversite eğitimi, bilimsel araştırma ve akademik yönetim konusunda güçlü bir potansiyel taşır. Uzun vadeli araştırma projeleri ve bilimsel yayın bu alanda başarı için kritiktir.",
            "gezegenler": "Jüpiter, Satürn, Merkür",
        },
        {
            "meslek": "Bilim İnsanı / Araştırmacı",
            "aciklama": "Plüton'un derinlemesine araştırma enerjisi ile Merkür'ün analitik zekasının birleşimi. Bilimsel keşifler, laboratuvar çalışmaları ve akademik yayınlar konusunda güçlü bir potansiyel taşır. Merak, sabır ve titizlik bu alanda temel gereksinimlerdir.",
            "gezegenler": "Plüton, Merkür, Uranüs",
        },
        {
            "meslek": "Doktora Öğrencisi / Araştırma Görevlisi",
            "aciklama": "Satürn'ün disiplin enerjisi ile Jüpiter'in geniş perspektifinin birleşimi. Yüksek lisans ve doktora çalışmaları, akademik kariyer ve araştırma projeleri konusunda başarılı olabilir. Odaklanma, sabır ve bilimselmethodoloji bu alanda kritiktir.",
            "gezegenler": "Satürn, Jüpiter, Merkür",
        },
        {
            "meslek": "Felsefeci / Düşünür",
            "aciklama": "Jüpiter'in felsefi enerjisi ile Plüton'un derinlemesine analizinin birleşimi. Varoluşsal sorular, etik felsefe ve bilgi felsefesi konusunda güçlü bir potansiyel taşır. Soyut düşünce ve mantıksal tutarlılık bu alanda success için önemlidir.",
            "gezegenler": "Jüpiter, Plüton, Satürn",
        },
        {
            "meslek": "Bilim Tarihçisi / Epistemolog",
            "aciklama": "Satürn'ün tarihsel perspektifi ile Jüpiter'in bilgelik arayışının birleşimi. Bilginin gelişimi, bilim felsefesi ve epistemolojik analiz konusunda başarılı olabilir. Tarihsel araştırma ve eleştirel düşünce bu alanda kritiktir.",
            "gezegenler": "Satürn, Jüpiter, Merkür",
        },
        {
            "meslek": "Matematikçi / İstatistikçi",
            "aciklama": "Merkür'ün mantıksal zekası ile Satürn'ün yapısal düşüncesinin birleşimi. Soyut matematik, istatistiksel analiz ve kantitatif araştırma konusunda güçlü bir potansiyel taşır. Mantıksal çıkarım ve hassas hesaplama bu alanda temeldir.",
            "gezegenler": "Merkür, Satürn, Uranüs",
        },
    ],
}
