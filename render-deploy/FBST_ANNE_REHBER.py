# -*- coding: utf-8 -*-
# FBST_ANNE_REHBER.py — Annenin çocuğunu tanıması için doğal dil bölümleri
# Her anahtar çocuğun kendi natal verisinden seçilir.

DUYGUSAL_IHTIYAC_AY = {
    "Koç": "Bu çocuk, annesinden önce güven ve ardından kendi yolunu açabileceği bir özgürlük bekler. Onu dinlediğinizi hissettiğinde dünya en güvenli yerdir; aksi halde bağımsızlık hamlesiyle kendini kanıtlamaya çalışır. Annesini çoğu zaman 'beni anlayan, beni cesaretlendiren kişi' olarak algılar; sabır ve güven onun için sevginin ta kendisidir.",
    "Boğa": "Bu çocuk, annesini sıcak ve tutarlı bir liman gibi algılar. Rutini bozulmadığında, kucağı ve sofrası güvenli olduğunda içi huzurla dolar. Aceleyle yönlendirilmekten değil, sabırla beklenmekten güç alır; ses tonundaki yumuşaklık ona 'her şey yolunda' mesajını verir.",
    "İkizler": "Bu çocuk, annesini konuşacak, sorularına cevap alacak bir yol arkadaşı gibi görür. Merakı doyurulduğunda, fikirleri ciddiye alındığında kendini değerli hisseder. Onun için güven, sohbet eden ve dinleyen bir annedir; sessizlik ise kafasında soru işaretleri büyütür.",
    "Yengeç": "Bu çocuk, annesini hayatının en güçlü koruyucusu olarak algılar. Sevgiyi; dokunmak, sarılmak ve 'seni anlıyorum' duyulan bir seste bulur. Evin kokusu, annenin sesi onun güven duvarıdır; kalbinin kapısı yalnızca gerçek bir şefkatle açılır.",
    "Aslan": "Bu çocuk, annesini kendisini en çok gören ve en çok gurur duyan kişi olarak algılar. Yaptıklarının fark edilmesi, onun için sevginin görünür hali olduğu kadar kimliğinin de aynasıdır. Onaylandığında parlıyor, görmezden gelindiğinde sönüyor; ilgisini ve takdirini esirgemeyen bir anne onun en büyük özgüven kaynağıdır.",
    "Başak": "Bu çocuk, annesini faydalı olmayı ve yardım etmeyi öğreten bir öğretmen gibi görür. Ona bir iş verildiğinde ve yaptığı takdir edildiğinde içi rahatlar. Eleştiriye değil, yol gösterici bir tona ihtiyaç duyar; mükemmeliyetçi kaygısını yalnızca 'yeterince iyisin' cümlesi yumuşatır.",
    "Terazi": "Bu çocuk, annesini adaletin ve zarafetin sembolü olarak algılar. Onunla kurulan dengeli, saygılı bir ilişki iç dengesini korur; kavgayı ve gerginliği evde hissetmek istemez. Annenin 'hem hak verip hem dinleyen' tavrı, onun için hem güven hem de huzur demektir.",
    "Akrep": "Bu çocuk, annesini sırdaşı ve sığınağı olarak algılar, ama güveni kolay kolay vermez. Duygularının yargılanmadan kabul edildiğini hissettiğinde bağı derinleşir; gizli bir yarasına dokunulursa kabuğuna çekilir. Onunla kurulan 'seni koşulsuz anlıyorum' bağı, en sağlam güven köprüsüdür.",
    "Yay": "Bu çocuk, annesini keşfe çıktığı bir macerada yanındaki rehber olarak görür. Serbest alan tanındığında, yanlış yapsa bile düşüp kalkmasına izin verildiğinde kendini güvende hisseder. Annenin 'güveniyorum sana' mesajı onun için hem kanat hem de sığınaktır.",
    "Oğlak": "Bu çocuk, annesini ciddi, güvenilir ve hedefli bir rol model olarak algılar. Takdir edildiğinde ve sorumluluk verildiğinde kendini değerli hisseder; ama övgü beklerken eleştiri alırsa içine kapanır. Annenin 'başardın' sözü, onun için sevginin en somut kanıtıdır.",
    "Kova": "Bu çocuk, annesini fikirlerine saygı duyan bir dost olarak algılar. Bireyselliği onaylandığında, 'sen farklı olabilirsin' dendiğinde kendini güvende hisseder. Onu kalıba sokmaya çalışan her tutum geri tepme yaratır; özgürlük tanıyan anne, onun için en derin güvendir.",
    "Balık": "Bu çocuk, annesini hayal dünyasını anlayan bir melek gibi algılar. Duygularına, sezgilerine ve hayallerine yer açıldığında içi huzurla dolar. Sert bir ses ya da katı bir kural onu incitir; yumuşak, şefkatli ve anlayışlı bir annenin kucağı onun güven limanıdır.",
}

SAKINLESME_AY = {
    "Koç": "Öfke ya da ağlama krizinde onu sakinleştirmenin en etkili yolu, önce duygusunu adlandırmak ve yanında olduğunuzu hissettirmektir: 'Kızgın olduğunu görüyorum, burada seninleyim.' Ardından bir yarışma, hızlı bir oyun ya da koşmasına izin veren bir alan önerin; enerjisi boşaldıkça sakinleşir.",
    "Boğa": "Kriz anında onu aceleye getirmeyin. Kucağınıza alıp sarılmak, sakin bir sesle konuşmak ve tanıdık bir rutine (sıcak bir içecek, battaniye, en sevdiği köşe) dönmek en güçlü yöntemdir. Duygusu geçene kadar sabırla beklemek, onun için sevginin kanıtıdır.",
    "İkizler": "Duygusal bir krizde onu sakinleştirmenin anahtarı, dikkatini bir soruya ya da merakına yöneltmektir. 'Bak, şu bulut neye benziyor?' gibi bir yönlendirme, zihnini sakinleştirir. Konuşmasına izin verin; hissettiklerini dile getirdikçe rahatlar.",
    "Yengeç": "Kriz anında ona sarılmak, 'seni seviyorum' demek ve kendini güvende hissedeceği bir köşe sunmak en etkili yoldur. Duygularını anlattığında yargılamadan dinleyin; ağlamasına izin verin. Kalbi sakinleştiğinde zihni de sakinleşir.",
    "Aslan": "Krizi büyütmeden, onun değerini vurgulayarak yaklaşın: 'Sen benim için çok önemlisin.' Yapıcı bir role geçmesini önerin ('Bize yardım eder misin?') çünkü sahneye çıkma ve faydalı olma duygusu onu sakinleştirir. Eleştiriye kesinlikle kriz anında girmeyin.",
    "Başak": "Kriz anında ona bir sorumluluk ya da düzenlenebilir bir görev verin; düzen duygusu onu topraklar. Nefes egzersizi gibi somut bir yöntem önerin. 'Şu an her şey yolunda, bak sana güveniyorum' cümlesi onu en çok sakinleştiren ifadedir.",
    "Terazi": "Kriz anında önce tartışmayı bırakın, ortamı sakinleştirin. 'Bunu birlikte çözebiliriz' diyerek ona denge ve seçim sunun: 'Hangisini tercih edersin?' Adalet hissi onu rahatlatır; ona hak verildiğini hissettirin.",
    "Akrep": "Kriz anında onu zorlamayın; önce duygusunun yoğunluğunu kabul edin. 'Bunun seni ne kadar etkilediğini anlıyorum' deyin ve yanında sessizce durun. Göz teması ve güven veren bir ses tonu, onun kabuğunu yumuşatır; güven hissettiğinde açılır.",
    "Yay": "Kriz anında dersi bir kenara bırakın, özgürlük alanı tanıyın: 'Hadi bir nefes alalım, sonra devam ederiz.' Açık hava, hareket ve mizah onu sakinleştirir. Ona inandığınızı ve güvendiğinizi hissettirin; coşkusu geri gelir.",
    "Oğlak": "Kriz anında duygusal yaklaşımdan çok, somut bir plan sunun: 'Şimdi ne yapabiliriz?' Sakin bir sesle 'Birlikte halledeceğiz' demek ona güç verir. Yargılanmadığını ve kontrolün elinde olduğunu hissettiğinde hızla toparlanır.",
    "Kova": "Kriz anında ona sakin bir mesafe tanıyın; hemen sarılmaya zorlamayın. Fikrini sorun: 'Sence şimdi ne iyi gelir?' Onu anladığınızı ve fikirlerine değer verdiğinizi gösterin. Bireyselliğine saygı duyulduğunda duygusu yatışır.",
    "Balık": "Kriz anında en etkili şifa, yumuşak bir ses, sakin bir müzik ve onu anladığınızı gösteren bir dokunuştur. Hayal gücünü kullanmasına izin verin: 'Hadi şu bulutu izleyelim.' Onun duygu dünyasına saygı gösterdikçe huzura döner.",
}

GUVEN_ORTAMI_4EV = {
    "Koç": "Evinde kendi alanına ve inisiyatifine saygı duyulduğunda güvende hisseder. Kapısının çalınmadan girilmesi, istediğinde odasında zaman geçirebilmesi onun güven temelidir. Ev, onun için cesaretini test ettiği ama hep geri dönebildiği bir üs olmalıdır.",
    "Boğa": "Evde tutarlı bir düzen, aynı saatlerde yemek ve sıcak bir atmosfer onun güven duvarıdır. Değişiklikler önceden haber verilirse uyum sağlar; ani sarsıntılar onu huzursuz eder. Evin somut ve duyusal konforu (rahat koltuk, sevdiği yemek) onun için güvendir.",
    "İkizler": "Evde serbestçe soru sorabilmek, fikirlerinin ciddiye alınması ve konuşulan bir atmosfer onu güvende tutar. Gazete, kitap, oyun masası gibi zihnini besleyen alanlar onun köşesidir. Ev, sohbetin ve merakın yuvası olduğunda kendini tamamlanmış hisseder.",
    "Yengeç": "Ev, onun için dünyanın en güvenli yeri olmalıdır. Ailece yenen yemekler, fotoğraflar ve geçmişe dair sıcak hatıralar onun kökleridir. Evde huzurlu bir ses tonu ve duygusal şeffaflık, onun güven ihtiyacını doyurur.",
    "Aslan": "Evde yaptıklarının görülmesi ve kutlanması onu güvende hissettirir. Kendi köşesinin (odası, masası) kişisel dokunuşlarla ona ait olması önemlidir. Ev, onun sahnesi ve kalbi olduğunda kendini en değerli hisseder.",
    "Başak": "Evde düzen, temizlik ve her şeyin yerli yerinde olması onun güven temelidir. Kişisel eşyalarının saygı görmesi ve rutinlerin aksatılmaması onu rahatlatır. Ev, işlerin yolunda gittiği sakin bir atölye olduğunda içi huzurla dolar.",
    "Terazi": "Evde adil bir paylaşım ve güzel bir atmosfer onu güvende tutar. Kardeşleriyle ya da anne-babasıyla kurulan dengeli ilişkiler onun ruhunu besler. Ev, kavgaların olmadığı ve herkesin eşit söz hakkına sahip olduğu bir yer olmalıdır.",
    "Akrep": "Evde mahremiyet ve güven onun için hayati önem taşır. Odasının kapısına saygı duyulması, sırlarının korunması onu güvende hissettirir. Ev, derin duyguların yargılanmadan saklandığı bir sığınak olduğunda tamamlanır.",
    "Yay": "Evde katı kurallar yerine esnek bir özgürlük onu güvende tutar. Seyahat hatıraları, kitaplar ve geniş bir ufuk hissi onun evidir. Ev, ona keşfetme alanı tanıyan ama hep dönebileceği bir merkez olduğunda mutludur.",
    "Oğlak": "Evde sorumluluk verilmesi ve güvenilmesi onu güvende hissettirir. Aileye katkı sağlayabileceği roller (masa kurmak, bir işi üstlenmek) ona değer katar. Ev, hedeflerine saygı duyulan ve çabasının görüldüğü bir yer olmalıdır.",
    "Kova": "Evde bireyselliğine saygı duyulması ve fikirlerinin önemsenmesi onu güvende tutar. Kalıplaşmış kurallar yerine mantıklı, açıklanmış düzenlemeler ister. Ev, herkesin kendi gibi olabildiği modern ve özgür bir alan olduğunda tamamlanır.",
    "Balık": "Evde yumuşak, şefkatli ve sezgisel bir atmosfer onu güvende hissettirir. Sanatsal alanlar, müzik ve hayal gücüne açık köşeler onun evidir. Ev, duyguların güvenle yaşandığı ve herkesin anlaşıldığı bir liman olduğunda ruhu dinlenir.",
}

ANNE_ROLU_ZORLUK = {
    "Güneş": "Anne olarak bu dönemde çocuğunuzun varlığını ve çabasını görün; kendini değerli hissettiğinde gerilim doğal olarak azalır.",
    "Ay": "Bu zorlukta çocuğunuzun duygusal ihtiyacına öncelik verin; önce sakinleşmesine yardım edin, sorun çözümünü sonraya bırakın.",
    "Merkür": "Çocuğunuzla bu konuyu sakin ve açık bir dille konuşun; kelimeleri seçerken suçlayıcı değil, merak eden bir ton kullanın.",
    "Venüs": "Sevginizi somut göstermenin yolunu bulun; küçük bir jest, sıcak bir söz bu gerilimi yumuşatır.",
    "Mars": "Bu enerjiyi bastırmayın, yönlendirin; sportif bir aktivite veya hareketli bir oyun, biriken enerjiyi sağlıklı bir kanala akıtır.",
    "Jüpiter": "Çocuğunuza geniş bir perspektif sunun; 'bu da geçecek' diyebilecek bir güven hissi, bu zorluğu büyümesine çevirir.",
    "Satürn": "Bu noktada sınırların net ama sevgi dolu olması gerekir; kuralı açıklayın, tutarlı olun, ceza yerine sorumluluk öğretin.",
    "Uranüs": "Esnek olun ve çözüm için farklı bir yol deneyin; beklenmedik bir yaklaşım, bu gerilimi hızla dağıtabilir.",
    "Neptün": "Hayal gücü ve sanat burada şifadır; müzik, resim ya da bir hikaye, çocuğunuzun duygusunu dönüştürmesine yardım eder.",
    "Plüton": "Bu derin gerilimde güç kavgasına girmeyin; sakin ve güçlü bir duruşla, çocuğunuzun duygusunu anladığınızı hissettirin.",
    "Chiron": "Bu yara hassas bir noktadır; acele şifa beklemeyin, sabırlı bir kabul ve şefkat zamanla en büyük iyileşmeyi getirir.",
    "Ceres": "Besleyici bir tavırla yaklaşın; önce fiziksel ve duygusal ihtiyacını karşılayın, sonra soruna dönün.",
    "Pallas": "Bu zorlukta stratejik olun; çocuğunuza kendi çözümünü bulması için sorular sorun, hazır cevap dayatmayın.",
    "Juno": "Adalet duygusuna hitap edin; 'bunu birlikte adil bir şekilde çözebiliriz' mesajı bu gerilimi yatıştırır.",
    "Vesta": "Çocuğunuzun odaklandığı konuya saygı gösterin; dikkati dağıtılmadan çalışmasına izin vermek, gerilimi azaltır.",
}

OGRENME_MOTIVASYON_MERKUR = {
    "Koç": "Bu çocuk, meydan okuma ve yarışmayla öğrenir; 'bakalım yapabilecek misin' motivasyonu en güçlü itici gücüdür. Kısa ve enerjik dersler, hedef belirleme ve başarıyı kutlama en verimli yöntemdir. Uzun tekrarlar sıkıcı gelir; hareket ve hız onun öğrenme dilidir.",
    "Boğa": "Bu çocuk, tekrar ve somut örneklerle öğrenir; öğrendiklerini uygulayabildiğinde kalıcı hale gelir. Yavaş ama sağlam ilerlemek onu mutlu eder; acele ve baskı öğrenmeyi durdurur. Görsel ve duyusal materyaller, onun için en verimli öğrenme araçlarıdır.",
    "İkizler": "Bu çocuk, konuşarak ve soru sorarak öğrenir; her bilgiyi bir sohbete dönüştürmek onun doğal yöntemidir. Farklı kaynaklar, hikayeler ve tartışma ortamları motivasyonunu yükseltir. Ezberden çok, anlatıp açıklamasına izin verildiğinde zihni açılır.",
    "Yengeç": "Bu çocuk, duygusal bağ kurduğu konuları kolayca öğrenir; sevdiği öğretmen ve sıcak bir ortam en büyük motivasyonudur. Öyküler, görseller ve 'bunun seninle ilgisi ne?' bağlantıları onu besler. Güvende hissetmediği ortamda öğrenme durur.",
    "Aslan": "Bu çocuk, sahne ve takdirle öğrenir; öğrendiklerini sunabildiğinde ve alkış aldığında motivasyonu zirveye çıkar. Başarılarının görülmesi ve kutlanması onun için hayati önem taşır. Eleştiri özel ortamda, takdir herkesin önünde olmalıdır.",
    "Başak": "Bu çocuk, liste ve analizlerle öğrenir; adım adım ilerleyen net bir plan onun en verimli yöntemidir. Kontrol listeleri, düzenli tekrar ve 'nasıl çözdün?' gibi analitik sorular motivasyonunu artırır. Düzen ve netlik onun öğrenme dilidir.",
    "Terazi": "Bu çocuk, işbirliği ve karşılaştırmayla öğrenir; grup çalışması ve tartışma ortamları onun için en verimli yöntemdir. Farklı görüşleri dengeleyerek öğrenir, adil değerlendirilmek ister. Estetik ve düzenli bir çalışma ortamı motivasyonunu yükseltir.",
    "Akrep": "Bu çocuk, derinlemesine ve gizemli konularla öğrenir; yüzeyde kalan bilgi onu sıkar, derine inmesine izin verildiğinde parlar. Araştırma yapmasına ve kendi sorularını sormasına alan tanıyın. Sır gibi görülen bilgi, onun en güçlü motivasyonudur.",
    "Yay": "Bu çocuk, deneyim ve seyahatle öğrenir; kitaplardan çok, deneyerek ve görerek öğrenmeyi sever. Geniş konular, felsefi sorular ve 'neden?' üzerine düşünme onu besler. Serbest bırakıldığında, keşfettikçe öğrenmesi derinleşir.",
    "Oğlak": "Bu çocuk, hedef ve yapıyla öğrenir; 'bu bilgi nereye gidiyor?' sorusunun cevabını görmek ister. Planlı çalışma, somut başarı belgeleri ve adım adım yükselen hedefler motivasyonunu artırır. Sorumluluk verildiğinde en iyi şekilde öğrenir.",
    "Kova": "Bu çocuk, yenilik ve projelerle öğrenir; teknoloji, deney ve farklı bakış açıları onun öğrenme dilidir. Kalıplaşmış müfredat sıkıcı gelir; kendi projesini kurmasına izin verin. Toplumsal bir amaca hizmet eden konular onu en çok motive eder.",
    "Balık": "Bu çocuk, hayal gücü ve müzikle öğrenir; hikayeler, sanat ve görseller en verimli öğrenme araçlarıdır. Sakin bir ortam ve sezgisel bir yaklaşım onu besler. Duygularına hitap eden konular, öğrenmeyi kalıcı hale getirir.",
}

EGITIM_3EV = {
    "Koç": "Sınıfta öne atılmayı ve söz istemeyi seven, rekabetten beslenen bir öğrencidir. Öğretmeniyle sıcak ama net bir ilişki kurduğunda enerjisini derse kanalize eder. Dikkat süresi kısa olabilir; hareketli etkinlikler ve yarışmalar onu derse bağlar.",
    "Boğa": "Sınıfta sakin, sabırlı ve düzenli bir öğrencidir; değişen planlara uyum sağlamakta zorlanır. Öğretmeninden tutarlılık ve adalet bekler. Sevdiği bir konuda inanılmaz bir ısrar gösterir; acele ettirildiğinde kapanır.",
    "İkizler": "Sınıfta çok soru soran, çok konuşan ve hızlı öğrenen bir öğrencidir. Öğretmeninin bilgisine ve esnekliğine güvenir; ezberden çok tartışmayı sever. Dikkati çabuk dağılabilir; çok yönlü etkinlikler onu derse tutar.",
    "Yengeç": "Sınıfta duygusal ve korumacı bir öğrencidir; öğretmenini ikinci bir anne gibi görür. Onaylandığı ve değer verildiği ortamda parlar, eleştirildiğinde içine kapanır. Küçük gruplar ve güvenli bir atmosfer onun öğrenme alanıdır.",
    "Aslan": "Sınıfta dikkat çekmeyi ve liderlik etmeyi seven bir öğrencidir; öğretmeninin takdiri onun yakıtıdır. Sahneye çıkmasına, sunum yapmasına izin verildiğinde harikalar yaratır. Haksızlığa asla sessiz kalmaz; adil bir öğretmenle en iyi uyumu yakalar.",
    "Başak": "Sınıfta titiz, çalışkan ve yardımsever bir öğrencidir; öğretmeninin en güvenilir yardımcısıdır. Detaylara takılıp mükemmeliyetçi kaygı yaşayabilir; 'yeterince iyisin' mesajına ihtiyaç duyar. Düzenli ve planlı bir öğretmenle en verimli çalışır.",
    "Terazi": "Sınıfta uyumlu, nazik ve arkadaş canlısı bir öğrencidir; çatışmadan kaçınır, herkesle iyi geçinmek ister. Öğretmeninin adil olması onun için kritik önem taşır. Grup çalışması ve tartışma ortamlarında en yüksek performansı gösterir.",
    "Akrep": "Sınıfta derin, araştırmacı ve gizemli bir öğrencidir; ilgisini çeken konuyu adeta araştırmacı gibi derinleştirir. Öğretmenine güven duyduğunda bağlılığı tam olur, güveni sarsılırsa kapılarını kapatır. Dürüstlük ve derinlik onun öğretmen beklentisidir.",
    "Yay": "Sınıfta maceracı, felsefi ve özgürlüğüne düşkün bir öğrencidir; katı kurallar onu boğar. Öğretmeninin vizyonu ve geniş bakış açısı onu motive eder. 'Neden?' sorusunun cevabını alabildiği bir ortamda en iyi öğrenir.",
    "Oğlak": "Sınıfta olgun, disiplinli ve hedef odaklı bir öğrencidir; öğretmenine saygı duyar ve ciddiye alır. Başarısının görülmesi ve ödüllendirilmesi onu motive eder. Sorumluluk verildiğinde yaşının ötesinde bir olgunluk gösterir.",
    "Kova": "Sınıfta yenilikçi, bağımsız ve farklı düşünen bir öğrencidir; kalıplaşmış kuralları sorgular. Öğretmeninin fikirlerine saygı duymasını ve esnek olmasını bekler. Teknoloji ve proje temelli öğrenme onun en güçlü motivasyon kaynağıdır.",
    "Balık": "Sınıfta hayal gücü zengin, duyarlı ve sezgisel bir öğrencidir; sert ve katı bir ortam onu korkutur. Sanatsal ve yaratıcı etkinliklerde parlıyor, sezgisiyle konuların özünü yakalar. Yumuşak ve anlayışlı bir öğretmenle en iyi şekilde öğrenir.",
}

BESLENME_RUTIN_AY = {
    "Koç": "Bu çocuğun enerjisi yüksektir; düzenli hareket ve yeterli uyku dengeyi korur. Yemekte aceleci olabilir; masayı oyunlaştırmak iştahını açar. Uykuya geçmeden önce sakin bir ritüel (kısa hikaye, ılık duş) onu derin bir uykuya taşır.",
    "Boğa": "Bu çocuk, düzenli ve aynı saatlerde beslenmeye ihtiyaç duyar; ani değişiklikler onu huzursuz eder. Yemeğe düşkün olabilir, porsiyon dengesini annenin sezgisi belirler. Uykuyu sever; yatış ritüeli sabit olduğunda en rahat uyur.",
    "İkizler": "Bu çocuğun yemekte çabuk sıkılması doğaldır; küçük porsiyonlar ve renkli sunumlar iştahını açar. Zihni aktif olduğundan yatmadan önce sessiz bir ortam ve hikaye gerekir. Rutinlerde esneklik olmalı ama uyku saati korunmalıdır.",
    "Yengeç": "Bu çocuk, yemekte duygusal güven arar; birlikte yenen aile yemekleri onun ruhunu besler. Sıcak ve tanıdık yiyecekler onu rahatlatır. Uykuya gitmeden önce sarılmak ve 'güvendesin' hissi en iyi yatış ritüelidir.",
    "Aslan": "Bu çocuk, yemeğin sunumuna ve 'özel olma' hissine duyarlıdır; masayı onun için özel hale getirmek iştahını artırır. Uykuya gitmeden önce gününün övülmesi onu mutlu eder. Düzenli ama esnek bir uyku saati onun için idealdir.",
    "Başak": "Bu çocuk, beslenmede düzen ve sağlıklı seçimlerle rahatlar; yemek tabağının düzeni iştahını etkiler. Seçim sunmak ('elma mı muz mu?') ona güven verir. Uyku rutini net ve tutarlı olmalı; yatmadan önce sakin bir etkinlik onu dinlendirir.",
    "Terazi": "Bu çocuk, yemekte denge ve uyum arar; sunumun güzelliği iştahını açar. Ailece yenen yemekler ve masadaki sakin atmosfer onu besler. Uykuya geçerken huzurlu bir ortam ve seçenek sunmak onu rahatlatır.",
    "Akrep": "Bu çocuk, yemekte derin bir ilgi ve yoğunluk gösterir; sevdiği yemeklere tutkuyla bağlanır. Uykuya geçmeden önce duygusal bağını kapatması için sakin bir sohbet gerekir. Gizliliğine saygı duyulduğu bir yatış ritüeli en iyisidir.",
    "Yay": "Bu çocuk, yemekte çeşitlilik ve macera ister; yeni tatlar denemek onu mutlu eder. Hareket ihtiyacı yüksektir; uykuya geçmeden önce enerjisini atmasına izin verin. Açık havada oyun ve düzenli uyku dengesi onun için idealdir.",
    "Oğlak": "Bu çocuk, yemekte ölçülü ve disiplinlidir; katı rutinlerden çok, sağlıklı bir düzen onu rahatlatır. Sorumluluk verildiğinde (masayı kurmak) yemekten keyif alır. Uyku, onun için görev gibi değil, kazanılmış bir ödül gibi sunulmalıdır.",
    "Kova": "Bu çocuk, yemekte yeniliklere açıktır; farklı ve ilginç yiyecekler ilgisini çeker. Rutinlere karşı çıkabilir; açıklanmış ve mantıklı kurallara uyar. Uykuya geçmeden önce sakin bir teknoloji molası ve sessiz bir ortam gerekir.",
    "Balık": "Bu çocuk, yemekte sezgisel ve değişken bir iştaha sahiptir; zorlamak ters etki yapar. Yumuşak, sanatsal sunumlar ve sakin bir masa onu besler. Uykuya geçmeden önce sakin müzik, ılık banyo ve şefkatli bir dokunuş en iyi ritüeldir.",
}

OZGURLUK_SINIR_SATURN = {
    "Koç": "Sınırlar net ama aceleci olmayan bir dille konulmalı; bu çocuk kurala değil, saygıya uyar. Özgürlüğü tamamen kısıtlandığında isyan eder; küçük seçimler sunmak ('şimdi mi, birazdan mı?') onu sakinleştirir. Sınırları açıklanmış bir düzen, onun için güvendir.",
    "Boğa": "Bu çocuk, değişmeyen ve tutarlı sınırlarla güvende hisseder; kurallar sürekli değişirse huzursuz olur. Özgürlüğü, rahat hissettiği alanda arar. Sınırlar nazik ama kararlı bir sesle konulmalı; zaman tanındığında en iyi uyum sağlar.",
    "İkizler": "Bu çocuk, kuralların nedenini anlamak ister; açıklanmış bir sınır onu ikna eder, mantıksız yasak isyan ettirir. Özgürlüğü, konuşmak ve soru sormak üzerinden yaşar. Sınırlar esnek ve diyalog içinde konulmalıdır.",
    "Yengeç": "Bu çocuk, sınırları sevgiyle harmanlanmış şekilde algıladığında uyum sağlar; soğuk bir kural onu yaralar. Özgürlüğü, güvende hissettiği ev ortamında arar. Sınırlar 'seni seviyorum, bu yüzden' cümlesiyle konulduğunda en sağlam sonucu verir.",
    "Aslan": "Bu çocuk, sınırları onuruna dokunmadan konulduğunda kabul eder; küçük düşürücü bir yasak isyan ettirir. Özgürlüğü, kendini gösterebildiği sahnesinde arar. Sınırlar, 'sen daha büyük işler için buradayken' ifadesiyle konulmalıdır.",
    "Başak": "Bu çocuk, net ve mantıklı sınırlarla rahatlar; belirsiz kurallar onu kaygılandırır. Özgürlüğü, düzenini kendisinin kurabildiği alanda arar. Sınırlar, açıklanmış ve adım adım konulduğunda en iyi uyumu gösterir.",
    "Terazi": "Bu çocuk, sınırların adil olduğunu hissettiğinde kabul eder; haksız bir kural iç dengesini bozar. Özgürlüğü, uyumlu ilişkiler içinde arar. Sınırlar, 'senin de hakların var, kurallar herkes için' çerçevesiyle konulmalıdır.",
    "Akrep": "Bu çocuk, sınırları derinden hisseder; güven duyduğu bir annenin koyduğu kurala sadakatle uyar. Özgürlüğü, güven içinde gizliliğini koruyabildiği alanda arar. Sınırlar dürüstlükle ve güven temelinde konulmalıdır.",
    "Yay": "Bu çocuk, geniş ve esnek sınırlarla rahatlar; daracık kurallar onu boğar. Özgürlüğü, keşif alanında arar. Sınırlar, 'neden' açıklamasıyla ve özgürlüğün kendisine öğreteceğine güvenilerek konulmalıdır.",
    "Oğlak": "Bu çocuk, yapılandırılmış ve saygılı sınırlarla en iyi uyumu gösterir; kuralların amacını anlamak ister. Özgürlüğü, hedeflerine giden yolda kendi adımlarını atabildiğinde hisseder. Sınırlar, sorumlulukla birlikte gelmelidir.",
    "Kova": "Bu çocuk, mantıksız sınırlara karşı çıkar; açıklanmış, demokratik bir kurala gönülden uyar. Özgürlüğü, birey olarak saygı gördüğü ortamda arar. Sınırlar, onun fikri alınarak ve gerekçesiyle konulmalıdır.",
    "Balık": "Bu çocuk, sert ve soğuk sınırlardan incinir; yumuşak ama kararlı bir çerçeve onu rahatlatır. Özgürlüğü, hayal dünyasında ve şefkatli bir ortamda arar. Sınırlar, 'seni korumak için' duygusuyla ve yumuşak bir sesle konulmalıdır.",
}

YAS_DONEMLERI = {
    "ERKEN": (
        "Erken çocukluk döneminde oyun temelli keşif ön plandadır; bu yaşlarda yetenek seçimi değil, "
        "deneyim zenginliği hedeflenir. Çocuğunuzun eline çok sayıda farklı malzeme ve etkinlik geçmesine "
        "izin verin; hangi oyuncakta, hangi oyunda gözleri parladıysa o alan doğal yatkınlığının ilk ipucudur."
    ),
    "ILK": (
        "İlkokul ve ortaokul döneminde kurs ve atölyelerle yönlendirme önerilir; bu yaş, yeteneğin keşfedilip "
        "sağlamlaştırıldığı dönemdir. Haftada bir-iki saatlik deneme atölyeleri (müzik, robotik, drama, spor) "
        "çocuğunuzun hangi alanda derinleşmek istediğini netleştirir. Başarıdan çok sürece değer verin; "
        "ilginin sürdüğü alan gerçek potansiyeldir."
    ),
    "ERG": (
        "Ergenlik döneminde kulüp ve projelerle derinleşme önerilir; bu yaşta yetenek, kimlik arayışının "
        "bir parçasına dönüşür. Okul kulüpleri, yarışmalar ve proje grupları, çocuğunuzun becerisini hem "
        "test ettiği hem de topluluk içinde deneyimlediği alanlardır. Yönlendirirken kendi seçimine saygı "
        "gösterin; sizin öngördüğünüz alan yerine onun sahiplendiği alan, geleceğin doğru yoludur."
    ),
    "YETISKIN": (
        "Yetişkinlik döneminde sertifika ve uzmanlaşma odaklı gelişim önerilir; bu dönemde potansiyel, "
        "kariyer ve sürdürülebilir beceriye dönüşür. Uzmanlaşma programları, staj ve alanında bir mentor, "
        "çocuğunuzun doğal yatkınlığını profesyonel başarıya taşır. Bu yaşta en doğru rehberlik, "
        "hayallerine saygı duyarak ona kapı açmaktır."
    ),
}

# ═══ ANNE-ÇOCUK UYUM BÖLÜMLERİ (ebeveyn-çocuk PDF'inde kullanılır) ═══

ELEMENT_UYUM_ANNE_COCUK = {
    ("Ateş", "Ateş"): (
        "Annenin ve çocuğun enerjisi aynı ateşli dalgadan beslenir; birbirlerini coşkularıyla canlandırır, "
        "harekete geçirirler. Bu uyumda çocuk, annesini 'benimle koşan, bana inanan' bir yol arkadaşı olarak "
        "algılar. Tek risk, iki ateşin aynı anda alevlenmesiyle çıkan kısa süreli çatışmalardır; birinizin "
        "sakin kalması, ikinizin de hızla toparlanmasını sağlar."
    ),
    ("Ateş", "Toprak"): (
        "Annenin ateşli cesareti ile çocuğun topraksı sağlamlığı birbirini tamamlar; anne hayal verir, "
        "çocuk kök salar. Çocuk, annesini 'beni hızlandıran ama acele ettiren' biri olarak algılayabilir; "
        "annesi sabır gösterdiğinde, çocuk en güçlü ve en istikrarlı halini ortaya koyar. Bu uyum, "
        "yavaş ama sağlam büyüyen bir güven bağıdır."
    ),
    ("Ateş", "Hava"): (
        "Annenin ateşi ile çocuğun havası birbirini sürekli besler; fikirler ateşlenir, hayaller kanatlanır. "
        "Çocuk, annesini 'her fikrime kulak veren' bir ilham kaynağı olarak görür. Bu uyumda konuşmak ve "
        "birlikte plan yapmak, bağınızı her gün tazeler; sohbet, ikinizin de en sevdiği sevgi dilidir."
    ),
    ("Ateş", "Su"): (
        "Annenin ateşli iradesi ile çocuğun su gibi hassas duygu dünyası buluşur; biri ısıtır, diğeri yumuşatır. "
        "Çocuk, annesini 'çok güçlü ama bazen çok hızlı' biri olarak algılayabilir; anne yavaşlayıp duyguya "
        "yer açtığında, çocuk en derin güvenini verir. Bu uyum, hassas bir dikkatle kurulan derin bir köprüdür."
    ),
    ("Toprak", "Ateş"): (
        "Annenin sağlam temeli ile çocuğun ateşli cesareti birbirini tamamlar; anne güven verir, çocuk alev getirir. "
        "Çocuk, annesini 'her zaman arkasında duran' bir kale gibi algılar; annesi de çocuğun enerjisinden güç alır. "
        "Bu uyum, sağlam bir kök üzerinde büyüyen parlak bir yapı gibidir."
    ),
    ("Toprak", "Toprak"): (
        "Annenin ve çocuğun toprağı aynı bereketli tarladan gelir; ikisi de düzeni, güveni ve sadakati doğal olarak "
        "yaşar. Çocuk, annesini 'en güvenilir limanım' olarak algılar; duyguları kolay kolay dile dökülmese de "
        "aralarındaki bağ zamanla en sağlam duvar haline gelir. Birlikte yapılan rutinler, bu bağı her gün güçlendirir."
    ),
    ("Toprak", "Hava"): (
        "Annenin sağlamlığı ile çocuğun zihinsel çevikliği birbirini dengeler; anne pratiklik verir, çocuk fikir üretir. "
        "Çocuk, annesini 'bazen fazla ciddi ama hep güvenilir' biri olarak algılayabilir; anne çocuğun fikirlerine "
        "merakla yaklaştığında, çocuk en yaratıcı halini gösterir. Bu uyum, toprak ve gökyüzü arasında kurulan sağlam bir köprüdür."
    ),
    ("Toprak", "Su"): (
        "Annenin topraksı pratikliği ile çocuğun su gibi sezgisi buluşur; biri güven verir, diğeri derinlik katar. "
        "Çocuk, annesini 'güvenebileceğim ama bazen hislerimi anlamayan' biri olarak görebilir; anne sezgisel olmaya "
        "açıldığında, çocuk iç dünyasının kapılarını ardına kadar açar. Bu uyum, bereketli ve derin bir bağdır."
    ),
    ("Hava", "Ateş"): (
        "Annenin zihinsel dünyası ile çocuğun ateşli coşkusu birbirini alevlendirir; fikirler ve cesaret el ele gider. "
        "Çocuk, annesini 'bana hep yeni kapılar açan' biri olarak algılar; anne de çocuğun enerjisinden tazelenir. "
        "Bu uyumda birlikte konuşmak, plan yapmak ve hayal kurmak, bağınızın anahtarıdır."
    ),
    ("Hava", "Toprak"): (
        "Annenin zihni ile çocuğun topraksı düzeni birbirini tamamlar; biri fikir verir, diğeri hayata geçirir. "
        "Çocuk, annesini 'çok konuşuyor ama beni gerçekten koruyor' biri olarak algılayabilir; anne fikirlerini "
        "çocuğun ritmine uydurduğunda, çocuk en iyi dinleyen ve en sağlam uygulayıcı haline gelir."
    ),
    ("Hava", "Hava"): (
        "Annenin ve çocuğun zihni aynı dalga boyunda çalışır; ikisi de kelimelerle, fikirlerle ve merakla beslenir. "
        "Çocuk, annesini 'her soruma cevap veren' en yakın dostu olarak algılar. Bu uyumda sohbet, ikinizin de "
        "en derin bağ kurma biçimidir; her konuşma, aranızdaki köprüyü güçlendirir."
    ),
    ("Hava", "Su"): (
        "Annenin zihinsel berraklığı ile çocuğun su gibi duygusal dünyası buluşur; biri anlamaya çalışır, diğeri hisseder. "
        "Çocuk, annesini 'çok mantıklı ama bazen hislerimi görmeyen' biri olarak algılayabilir; anne duyguya yer "
        "açtığında, çocuk en zengin hayal gücünü ve sezgisini paylaşır. Bu uyum, zihin ve kalbin birleştiği bir köprüdür."
    ),
    ("Su", "Ateş"): (
        "Annenin su gibi şefkati ile çocuğun ateşli cesareti buluşur; biri yumuşatır, diğeri alevlendirir. "
        "Çocuk, annesini 'beni hep koruyan ama bazen çok duygusal' biri olarak algılayabilir; anne çocuğun "
        "bağımsızlığına güvendiğinde, çocuk en parlak halini gösterir. Bu uyum, derin ve tutkulu bir bağdır."
    ),
    ("Su", "Toprak"): (
        "Annenin sezgisi ile çocuğun topraksı sağlamlığı birbirini güçlendirir; biri hisseder, diğeri ayakta tutar. "
        "Çocuk, annesini 'beni koşulsuz seven' en güvenli sığınağı olarak algılar. Bu uyum, zamanla en derin ve en "
        "sağlam güven bağlarından birine dönüşür; sessizlikler bile sıcacık bir iletişimdir."
    ),
    ("Su", "Hava"): (
        "Annenin su gibi derin duyguları ile çocuğun hava gibi zihinsel dünyası buluşur; biri hisseder, diğeri söyler. "
        "Çocuk, annesini 'beni anlamak için çok çabalayan' biri olarak algılar; anne çocuğun sözcüklerine de "
        "duygularıyla cevap verdiğinde, çocuk kendini tam anlaşılmış hisseder. Bu uyum, kalp ve zihin arasındaki zarif bir köprüdür."
    ),
    ("Su", "Su"): (
        "Annenin ve çocuğun suları aynı okyanustan gelir; ikisi de hisleriyle, sezgileriyle ve derin duygularıyla yaşar. "
        "Çocuk, annesini 'beni hiç konuşmadan anlayan' en derin dostu olarak algılar. Bu uyumda kelimelerden çok "
        "göz teması ve sessiz anlayış konuşur; aranızdaki bağ, en görünmez ama en güçlü bağdır."
    ),
}

OZEL_BAG_ACI_TEMA = {
    "Kavuşum": (
        "Annenizin {gezegen} konumu ile çocuğunuzun {gezegen2} konumu arasındaki kavuşum, ruhlarınızın aynı "
        "dalga boyunda titreştiğini gösterir. Bu noktada birbirinizi kelimelere ihtiyaç duymadan anlarsınız; "
        "çocuğunuz bu konuda annesini adeta bir yansıması gibi hisseder. Bu güçlü yakınlık, kimi zaman "
        "sınırların bulanıklaşmasına da yol açabilir; sağlıklı bir mesafe, bu mührün en değerli hediyesi olan "
        "anlayışı korur."
    ),
    "Üçgen": (
        "Annenizin {gezegen} konumu ile çocuğunuzun {gezegen2} konumu arasındaki üçgen açı, doğal ve akıcı bir "
        "uyum mührüdür. Bu alanda birbirinize zorlanmadan destek olursunuz; çocuğunuz annesini 'beni her zaman "
        "rahatlatan' biri olarak algılar. Bu doğal akış, çocuğunuzun bu konuda kendini güvende hissetmesini "
        "sağlar ve aranızdaki bağı zahmetsizce güçlendirir."
    ),
    "Sekstil": (
        "Annenizin {gezegen} konumu ile çocuğunuzun {gezegen2} konumu arasındaki sekstil açı, büyüme fırsatı "
        "taşıyan faydalı bir köprüdür. Bu alanı birlikte keşfettikçe, ikiniz de birbirinizden yeni şeyler "
        "öğrenirsiniz; annenin deneyimi ile çocuğun merakı birleşir. Bu uyumu beslemek için bu konuda birlikte "
        "etkinlik yapmak, bağınızı çok hızlı derinleştirir."
    ),
    "Kare": (
        "Annenizin {gezegen} konumu ile çocuğunuzun {gezegen2} konumu arasındaki kare açı, ikinizin de bu "
        "konuda farklı ritimlerde olduğunu gösterir. Çocuğunuz kimi zaman annesinin yaklaşımını 'bana ters' "
        "hissedebilir; bu, kötü bir bağ değil, büyüme davetidir. Annesi bu alanda esneklik gösterdiğinde ve "
        "çocuğunun yoluna saygı duyduğunda, bu gerilim ikinizi de güçlendiren bir öğretmene dönüşür."
    ),
    "Karşıt": (
        "Annenizin {gezegen} konumu ile çocuğunuzun {gezegen2} konumu arasındaki karşıt açı, ikinizin bu konuda "
        "iki zıt kutup gibi durduğunu ama aslında birbirini tamamladığını gösterir. Çocuğunuz, annesinin "
        "güçlü yönlerini tamamlayan yönler taşır; bu alanda yaşanan 'karşıtlık' aslında denge arayışıdır. "
        "Birlikte orta yolu bulduğunuzda, bu bağ ikinize de en geniş ufku açar."
    ),
}

GUNES_AY_UYUM_OZET = {
    "Koç": "çocuğunuzun duygusal dünyası cesur ve bağımsızdır; annesinden önce güven, sonra özgür alan bekler",
    "Boğa": "çocuğunuzun duygusal dünyası sakin ve sadıktır; annesinden tutarlılık ve sıcak bir rutin bekler",
    "İkizler": "çocuğunuzun duygusal dünyası meraklı ve konuşkandır; annesinden sohbet ve zihinsel uyarım bekler",
    "Yengeç": "çocuğunuzun duygusal dünyası korumacı ve derindir; annesinden koşulsuz sevgi ve güven bekler",
    "Aslan": "çocuğunuzun duygusal dünyası parlak ve gururludur; annesinden takdir ve görülmek ister",
    "Başak": "çocuğunuzun duygusal dünyası titiz ve yardımseverdir; annesinden kabul ve yumuşak bir dil bekler",
    "Terazi": "çocuğunuzun duygusal dünyası uyumlu ve adildir; annesinden dengeli ve saygılı bir ilişki bekler",
    "Akrep": "çocuğunuzun duygusal dünyası yoğun ve derindir; annesinden sadakat ve güvenilirlik bekler",
    "Yay": "çocuğunuzun duygusal dünyası özgür ve iyimserdir; annesinden güven ve serbest alan bekler",
    "Oğlak": "çocuğunuzun duygusal dünyası olgun ve hedeflidir; annesinden saygı ve sorumluluk bekler",
    "Kova": "çocuğunuzun duygusal dünyası bağımsız ve dostçadır; annesinden fikirlerine saygı bekler",
    "Balık": "çocuğunuzun duygusal dünyası sezgisel ve şefkatlidir; annesinden anlayış ve yumuşaklık bekler",
}
