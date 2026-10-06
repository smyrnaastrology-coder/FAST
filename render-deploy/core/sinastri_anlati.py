# -*- coding: utf-8 -*-
"""
Solar Fire tarzı sinastri anlatı katmanı (özgün metinler, kopya değildir).

Her açı tipi için TR/EN/ES tam paragraf anlatı. Yer tutucular (engine
tarafından formatlanır):
  {p1} {p2}      -> kişi adları
  {g1} {g2}      -> gezegen adları (pdf_label ile lokalize)
  {ev1} {ev2}    -> ev numaraları
  {uygulama}     -> uygulanan/ayrılan kapanış cümlesi (lokalize)
  {baglam}       -> mod cümlesi (aşk/evlilik veya ebeveyn-çocuk, lokalize)

Eksiltme yok: sabit duran bindirilmiş tema metinleri (FBST_SINASTRI_OZEL) ve
şifa reçeteleri aynen korunur; bu modül onların üstüne anlatı katar.
"""

SINASTRI_ANLATI = {
    0: {
        "tr": (
            "{g1} ile {g2} kavuşumu, bu iki alanın aynı odağa kilitlenip tek ses olduğu bir bileşim yaratır. "
            "{p1}'in {g1} enerjisi ile {p2}'nin {g2} enerjisi aynı hizada döner ve ilk tanışma anında bile birbirinizi anlaşılmış hissedersiniz. "
            "{p1}, {p2}'de kendi dilinden konuşan birini bulur; mutabakat ve ortak niyete duyduğu ihtiyaç doğal olarak karşılanır. "
            "{p2} ise bu buluşmada kendini daha canlı ve bütün hisseder. "
            "Bu güç birliği, güç ile nezaketi aynı elde tutmayı gerektirir; aksi halde birinizin sesi diğerini gölgede bırakır. "
            "{g1}'in {ev1}. evde, {g2}'nin {ev2}. evde duruşu bu kaynaşmayı destekler, çünkü ikisi de aynı yönü gösterir. "
            "{uygulama}{baglam} Işıklarınız aynı hedefe odaklandığı sürece, bu kavuşum bağınızın en sadık dostluğu ve en kalıcı ortaklığı olur."
        ),
        "en": (
            "The conjunction of {g1} and {g2} forges a blend of two spheres that locks into a single focus. "
            "{p1}'s {g1} moves in line with {p2}'s {g2}, and from the very first meeting a sense of being understood settles over both of you. "
            "{p1} finds in {p2} someone who speaks his own language; the need for agreement and shared intention is met almost without effort. "
            "{p2}, for their part, feels more vivid and whole in this meeting. "
            "This union of power asks that you keep strength and tenderness in the same hand, or one voice will overshadow the other. "
            "{g1} in house {ev1} and {g2} in house {ev2} point the same way and deepen the fusion. "
            "{uygulama}{baglam} As long as your lights stay aimed at the same goal, this conjunction becomes the loyalty and the most lasting partnership of your bond."
        ),
        "es": (
            "La conjunción de {g1} y {g2} crea una mezcla que se funde en un único foco. "
            "El {g1} de {p1} gira alineado con el {g2} de {p2} y, desde el primer encuentro, la sensación de ser comprendidos se instala en ambos. "
            "{p1} encuentra en {p2} a alguien que habla su propio idioma; la necesidad de acuerdo y de intención compartida se cubre casi sin esfuerzo. "
            "{p2} se siente más vivo y más completo en este encuentro. "
            "Esta unión de poder exige sostener fuerza y ternura en la misma mano, o una voz hará sombra a la otra. "
            "El {g1} en la casa {ev1} y el {g2} en la casa {ev2} señalan la misma dirección y profundizan la fusión. "
            "{uygulama}{baglam} Mientras vuestras luces permanezcan apuntando a la misma meta, esta conjunción se vuelve la lealtad y la sociedad más duradera de vuestro vínculo."
        ),
    },
    45: {
        "tr": (
            "Yarım kare kuran {g1} ile {g2}, sürekli ama büyük olmayan bir sürtünme yaratır. "
            "{p1}, {p2}'nin {g2} alanındaki tavırlarında ince bir pürüz sezer; çoğu zaman neden diye sormadan, için için bir huzursuzluk birikmeye başlar. "
            "{p2} ise {p1}'in {g1} alanındaki beklentilerini küçük gördükçe, cevabını olgunlaşmamış bir sabırsızlığa dönüştürür. "
            "Hiçbiri tek başına büyük değildir; ama biriken ufak kırılmalar ilişkinin dokusunda görünmez çatlaklar açar. "
            "{g1}'in {ev1}. evde ve {g2}'nin {ev2}. evde konumlanması, bu sürtünmenin hayatınızın hangi odasında büyüdüğünü gösterir. "
            "{uygulama}Bu açının çözümü büyük jestlerde değil, küçük alışkanlıkların düzeltilmesindedir; erken konuşulursa, kaşıntı hafifler. "
            "{baglam}"
        ),
        "en": (
            "The semisquare between {g1} and {g2} does not announce itself as an event; it lives as a small but constant itch. "
            "{p1} senses a rough edge in the way {p2} handles {g2} and, without ever asking why, a quiet restlessness slowly accumulates. "
            "{p2}, for their part, meets {p1}'s demands in the sphere of {g1} with an impatient shrug, because each one looks too small to matter. "
            "No single moment is big, but the gathered micro-fractures leave invisible cracks in the fabric of the bond. "
            "{g1} in house {ev1} and {g2} in house {ev2} show in which room of your shared life this friction grows. "
            "{uygulama}The cure is not grand gestures but small corrections of habit; addressed early, the itch fades. "
            "{baglam}"
        ),
        "es": (
            "El semicuadrado entre {g1} y {g2} no se anuncia como un acontecimiento; vive como un picor pequeño y constante. "
            "{p1} percibe un borde áspero en la forma en que {p2} maneja el {g2} y, sin preguntarse nunca el porqué, acumula una inquietud callada. "
            "{p2}, por su parte, responde a las exigencias de {p1} en el ámbito de {g1} con un encogimiento impaciente, porque cada una parece demasiado pequeña para importar. "
            "Ningún momento es grande por sí solo, pero las microfracturas reunidas dejan grietas invisibles en la tela del vínculo. "
            "El {g1} en la casa {ev1} y el {g2} en la casa {ev2} muestran en qué habitación de vuestra vida crece esta fricción. "
            "{uygulama}La cura no está en los grandes gestos sino en pequeñas correcciones de hábito; atendido a tiempo, el picor se desvanece. "
            "{baglam}"
        ),
    },
    60: {
        "tr": (
            "Sekstil kuran {g1} ile {g2} arasında ne mesafe var ne de zorunlu temas; bu açı, kapıyı aralık bırakır ve ikinizin de o kapıdan yürümesini bekler. "
            "{p1}, {p2}'nin {g2} alanında sunduğu zemini doğal bir fırsat olarak görür; adım atarsa, yeni bir alan açılır. "
            "{p2} de aynı şekilde {p1}'in {g1} enerjisinden ilham alır; iki alan birbirini itmeden tamamlar. "
            "Bu uyum kendiliğinden dökülmez; harekete geçilmedikçe fırsat sadece bir imkân olarak kalır. "
            "{g1}'in {ev1}. evde, {g2}'nin {ev2}. evde olması bu imkânın hayatın hangi alanında filizlenebileceğini anlatır. "
            "{uygulama}Ortak bir deneyimin içine girdiğinizde, bu açı en şanslı köprülerinizden biri olur. "
            "{baglam}"
        ),
        "en": (
            "The sextile between {g1} and {g2} keeps an open door rather than demanding a connection; it leaves space and waits for you both to walk through it. "
            "{p1} sees the ground {p2} offers in the sphere of {g2} as a natural chance; if he steps forward, a new area opens. "
            "{p2} is similarly inspired by {p1}'s {g1} energy, and the two spheres complete one another without pushing. "
            "But this harmony does not pour out on its own; unless you act, the chance remains only a possibility. "
            "With {g1} in house {ev1} and {g2} in house {ev2}, you can read in which corner of life this seed may grow. "
            "{uygulama}Once you enter a shared experience, this aspect becomes one of your luckiest bridges. "
            "{baglam}"
        ),
        "es": (
            "El sextil entre {g1} y {g2} mantiene una puerta abierta más que una conexión exigente; deja espacio y espera a que ambos la crucen. "
            "{p1} ve el terreno que {p2} ofrece en el ámbito del {g2} como una oportunidad natural; si da un paso, se abre un área nueva. "
            "{p2} se inspira de igual modo en el {g1} de {p1}, y las dos esferas se completan sin empujarse. "
            "Pero esta armonía no brota sola; sin acción, la oportunidad queda sólo como posibilidad. "
            "Con el {g1} en la casa {ev1} y el {g2} en la casa {ev2} se lee en qué rincón de la vida puede germinar esta semilla. "
            "{uygulama}En cuanto compartís una experiencia, este aspecto se vuelve uno de vuestros puentes más afortunados. "
            "{baglam}"
        ),
    },
    90: {
        "tr": (
            "Kare kuran {g1} ile {g2}, iki alanın neredeyse aynı noktada ama birbirini zorlayan çizgilerde durduğu bir baskı odağı oluşturur. "
            "{p1}, {p2}'nin {g2} alanındaki enerjisini kimi zaman fazla, kimi zaman eksik bulur; ortası yoktur. "
            "{p2} de {p1}'in {g1} tarzına karşılık verirken kendini sık sık savunmada hisseder ve çekişme alışkanlığa dönüşür. "
            "Haftalar içinde aynı konu tekrar tekrar döner; irade ile sevgi dilinin hangisinin öne geçtiği belirsizleşir. "
            "Bu gerilim sizi birbirinizi anlamaya zorlar; konuşulmadığında katılaşır, konuşulduğunda büyütür. "
            "{g1}'in {ev1}. evdeki ve {g2}'nin {ev2}. evdeki karşıtlığı, bu baskının hangi ortak konuda tahta çıktığını gösterir. "
            "{uygulama}Kare, ilişkinin inşası için en zorlu ama en verimli yapı taşıdır; emek verdikçe aranızdaki boşluk boşluk olmaktan çıkar, temel olur. "
            "{baglam}"
        ),
        "en": (
            "The square between {g1} and {g2} creates a point of pressure where two spheres stand almost together while pulling in different directions. "
            "{p1} finds {p2}'s handling of {g2} alternately too much and too little; there is no middle ground. "
            "{p2}, answering {p1}'s way with {g1}, often feels defensive, and the tug-of-war becomes a habit. "
            "Within weeks the same subject keeps returning, and whether will or the language of love is leading grows unclear. "
            "This tension forces you toward understanding: ignored it hardens, spoken about it matures you. "
            "The opposition of {g1} in house {ev1} and {g2} in house {ev2} reveals on which shared theme this pressure climbs the stage. "
            "{uygulama}The square is the hardest but most fruitful building block of a relationship; work on it and the space between you turns from a gap into a foundation. "
            "{baglam}"
        ),
        "es": (
            "La cuadratura entre {g1} y {g2} crea un punto de presión en el que dos esferas casi se tocan mientras tiran en direcciones distintas. "
            "{p1} encuentra la manera de {p2} de manejar el {g2} alternativamente excesiva y escasa; no hay punto medio. "
            "{p2} responde a la forma de {p1} con el {g1} sintiéndose a menudo a la defensiva, y la cuerda se vuelve costumbre. "
            "En pocas semanas vuelve el mismo tema, y no está claro si manda la voluntad o el lenguaje del amor. "
            "Esta tensión os obliga a entenderos: ignorada se endurece, conversada os madura. "
            "La oposición del {g1} en la casa {ev1} y del {g2} en la casa {ev2} revela sobre qué tema compartido sube esta presión al escenario. "
            "{uygulama}La cuadratura es el ladrillo más duro y más fértil de una relación; trabajada, el espacio entre vosotros pasa de vacío a cimiento. "
            "{baglam}"
        ),
    },
    120: {
        "tr": (
            "{g1} ile {g2} arasındaki üçgen, bu iki alanın aynı ritimde nefes aldığı ender bir uyum akışı taşır. "
            "{p1}, {p2}'nin {g2} alanında yaptığı her şeyi sürtünmesiz, takipçi gibi değil eş gibi anlar. "
            "{p2} de {p1}'in {g1} enerjisini desteklerken kendini zorlamaz; yardımı doğal bir refleks gibidir. "
            "Bu kolaylık çoğu zaman fark edilmez, çünkü sürtünme olmayınca emek de görünmez olur. "
            "Üçgenin tuzağı atalettir: uyum fazla doğal olduğunda, tutku solmasa bile rutin ilişkinin üzerine örtüye serilir. "
            "{g1}'in {ev1}. evde ve {g2}'nin {ev2}. evde oluşu bu akışı günlük hayatta destekler. "
            "{uygulama}Bu açı, bilinçli olarak beslemediğinizde sessizce solan ama birlikte attığınız her adımla yeşeren doğal bir dayanaktır. "
            "{baglam}"
        ),
        "en": (
            "The trine between {g1} and {g2} carries a rare flow in which the two spheres breathe on the same rhythm. "
            "{p1} understands everything {p2} does in the sphere of {g2} without friction, not as a follower but as an equal. "
            "{p2} likewise supports {p1}'s {g1} energy without straining; the help comes as a natural reflex. "
            "This ease often goes unnoticed, because without friction the effort also becomes invisible. "
            "The trap of the trine is inertia: when harmony is too natural, passion fades and routine covers the bond. "
            "With {g1} in house {ev1} and {g2} in house {ev2}, the flow is anchored in daily life. "
            "{uygulama}This aspect is a natural foundation that silently fades if not consciously tended, yet greens with every step you take together. "
            "{baglam}"
        ),
        "es": (
            "El trígono entre {g1} y {g2} lleva un raro flujo en el que las dos esferas respiran al mismo ritmo. "
            "{p1} comprende sin fricción todo lo que {p2} hace en el ámbito del {g2}, no como seguidor sino como igual. "
            "{p2} apoya de igual modo el {g1} de {p1} sin esforzarse; la ayuda llega como un reflejo natural. "
            "Esta facilidad suele pasar desapercibida, porque sin fricción también el esfuerzo se vuelve invisible. "
            "La trampa del trígono es la inercia: cuando la armonía es demasiado natural, la pasión se apaga y la rutina cubre el vínculo. "
            "Con el {g1} en la casa {ev1} y el {g2} en la casa {ev2}, el flujo se ancla en la vida diaria. "
            "{uygulama}Este aspecto es un cimiento natural que se desvanece en silencio si no se atiende, y reverdece con cada paso que dais juntos. "
            "{baglam}"
        ),
    },
    135: {
        "tr": (
            "Sekstilin akrabası olan 135 derece, {g1} ile {g2} arasında tek tek küçük ama üst üste biriken uyumsuzluklar kurar. "
            "{p1} başta bunu yok sayar; önemli değilmiş gibi gelir, ama {p2}'nin {g2} alanındaki seçimleri bir süre sonra sinire dokunur. "
            "{p2} de {p1}'in {g1} beklentilerini ölçüsüz bulur ve için için geri çekilir. "
            "Aradaki fark büyük bir kavga çıkarmaz; daha çok, aynı konuşmada iki ayrı monolog döner. "
            "135 derece bir akort sesi gibidir: ritmi kaçırırsınız ve yarım karenin kaşıntısından daha derin bir düzeltme ister. "
            "{g1}'in {ev1}. evde ve {g2}'nin {ev2}. evde konumu, bu ayarın hangi ortak konuda gerekli olduğunu söyler. "
            "{uygulama}Bu açıyı çözmenin yolu büyük bir yüzleşme değil, ritminizi yavaşça birbirinize uydurmaktır. "
            "{baglam}"
        ),
        "en": (
            "The sesquiquadrate (135), a cousin of the sextile, builds between {g1} and {g2} a chain of small mismatches that accumulate rather than explode. "
            "{p1} ignores it at first; it never seems to matter, until {p2}'s choices in the sphere of {g2} begin to grate. "
            "{p2}, for their part, finds {p1}'s expectations in {g1} disproportionate and quietly withdraws. "
            "The difference rarely becomes a quarrel; more often, two separate monologues run inside the same conversation. "
            "135 works like a tuning signal: you lose the rhythm, and it demands a deeper correction than the 45 itch. "
            "The placement of {g1} in house {ev1} and {g2} in house {ev2} tells you on which shared theme this adjustment is needed. "
            "{uygulama}The way out is not a big confrontation but slowly matching your rhythms to one another. "
            "{baglam}"
        ),
        "es": (
            "El sesquicuadrado (135), primo del sextil, construye entre {g1} y {g2} una cadena de pequeños desajustes que se acumulan en vez de estallar. "
            "{p1} al principio lo ignora; nunca parece importar, hasta que las decisiones de {p2} en el ámbito del {g2} empiezan a molestar. "
            "{p2}, por su parte, encuentra desproporcionadas las expectativas de {p1} en el {g1} y se retira en silencio. "
            "La diferencia rara vez se vuelve pelea; más a menudo, dos monólogos distintos corren dentro de la misma conversación. "
            "135 funciona como una señal de afinación: pierdes el ritmo y exige una corrección más profunda que el picor de los 45. "
            "La posición del {g1} en la casa {ev1} y del {g2} en la casa {ev2} indica sobre qué tema compartido hace falta este ajuste. "
            "{uygulama}La salida no es una gran confrontación sino acoplar lentamente vuestros ritmos. "
            "{baglam}"
        ),
    },
    150: {
        "tr": (
            "Quincunx (150 derece), {g1} ile {g2} arasında fark edilmesi en kolay ama adı en zor konan açıdır: hiçbiri yanlış değildir, ikisi birbirine değmez. "
            "{p1}, {p2}'nin {g2} alanındaki dünyasını anlar ama kendine hiç uyduramaz; ilgisiz değildir, sadece ortak ölçü bulamaz. "
            "{p2} de {p1}'in {g1} tarzına saygı duyar, ama kendi yolunun farklı olduğunu görünce hafif bir huzursuzlukla uzaklaşır. "
            "Bu açıda suçlu aramak sonuçsuzdur; mesele, pratik hayattaki farklı ihtiyaçların aynı takvime sığmamasıdır. "
            "Quincunx'ın erdemi uyanık kalmaktır: göz ardı edildiğinde kronik bir yönsüzlük yaratır, bilinçle adapte edildiğinde tamamlayıcı bir ustalık öğretir. "
            "{g1}'in {ev1}. evde ve {g2}'nin {ev2}. evde konumlanışı bu uyumsuzluğun nerede palazlandığını gösterir. "
            "{uygulama}Bu açıyı kayıp bir anahtar gibi aramak yerine ortak bir kullanım alanı açtığınızda, en verimsiz görünen alan en öğretici ortaklığa dönüşür. "
            "{baglam}"
        ),
        "en": (
            "The quincunx (150) between {g1} and {g2} is the aspect that is easiest to notice and hardest to name: neither side is wrong, the two just do not meet. "
            "{p1} understands {p2}'s world in the sphere of {g2} but can never quite fit into it; not indifferent, simply without a shared measure. "
            "{p2} respects {p1}'s way with {g1} but, seeing their own path differ, withdraws with a faint unease. "
            "Looking for a culprit here is useless; the matter is that different practical needs do not fit one calendar. "
            "The virtue of the quincunx is its demand to stay awake: neglected it breeds chronic directionlessness, consciously adapted it teaches a complementary mastery. "
            "The placement of {g1} in house {ev1} and {g2} in house {ev2} shows where this mismatch grows. "
            "{uygulama}Rather than searching for a lost key, open a shared use for this aspect and the most useless-looking area becomes your most instructive partnership. "
            "{baglam}"
        ),
        "es": (
            "El quincuncio (150) entre {g1} y {g2} es el aspecto más fácil de notar y más difícil de nombrar: ninguno está equivocado, simplemente no se tocan. "
            "{p1} comprende el mundo de {p2} en el ámbito del {g2} pero nunca termina de encajar; no es indiferencia, falta una medida común. "
            "{p2} respeta la manera de {p1} con el {g1} pero, al ver distinto su propio camino, se retira con una leve inquietud. "
            "Buscar culpables aquí no sirve; el asunto es que necesidades prácticas diferentes no caben en un mismo calendario. "
            "La virtud del quincuncio es exigir estar despierto: ignorado engendra desorientación crónica; adaptado con conciencia, enseña una maestría complementaria. "
            "La posición del {g1} en la casa {ev1} y del {g2} en la casa {ev2} muestra dónde crece este desajuste. "
            "{uygulama}En vez de buscar una llave perdida, abrid a este aspecto un uso común y el área que parece más inútil se vuelve vuestra asociación más instructiva. "
            "{baglam}"
        ),
    },
    180: {
        "tr": (
            "{g1} ile {g2} arasındaki karşıtlık, iki alanın aynı sahada ama zıt kaleleri kolladığı bir denge çizgisi kurar. "
            "{p1} bu oyunda {g1} tarafını, {p2} ise {g2} tarafını temsil eder; ikiniz de kendi hakkınızın savunucususunuz. "
            "{p1}, {p2}'nin {g2} alanındaki tutumunu farklı buldukça mesafe açılır; çünkü biri yakınlık önce derken, öteki özgürlük korunmalı der. "
            "{p2} da aynı gerilimi kendince yaşar ve konu büyümeden uzlaşmak yerine, sessizce kutuplaşmayı seçebilir. "
            "Karşıtlığın hikmeti eşiktedir: aynı masada zıt talepler bulundurmak yorucudur ama ikinizi birden büyüten tek aynadır. "
            "{g1}'in {ev1}. evde ve {g2}'nin {ev2}. evde duruşu, bu karşıtlığın hangi alanda tamamlayıcı, hangi alanda yıpratıcı olacağını belirler. "
            "{uygulama}Bu bir savaş değil, kutupları birbirine nişan almış bir mıknatıstır; dengeyi bulduğunuzda ilişkinizin en güçlü dayanağı olur. "
            "{baglam}"
        ),
        "en": (
            "The opposition between {g1} and {g2} draws a line of balance where two spheres guard the same field but opposite forts. "
            "{p1} plays the {g1} side and {p2} plays the {g2} side; each of you defends your own claim. "
            "The more {p1} finds {p2}'s stand on {g2} foreign, the wider the distance grows, because one says closeness first while the other says freedom must be kept. "
            "{p2} lives the same tension in their own way and, instead of reconciling, may quietly choose to polarize. "
            "The wisdom of the opposition stands at the door: holding opposite demands at one table is tiring, yet it is the only mirror that grows you both. "
            "The position of {g1} in house {ev1} and {g2} in house {ev2} decides where this polarity completes you and where it wears you out. "
            "{uygulama}This is not a war but a magnet whose poles aim at each other; when balance is found, it becomes the strongest support of your relationship. "
            "{baglam}"
        ),
        "es": (
            "La oposición entre {g1} y {g2} traza una línea de equilibrio donde dos esferas custodian el mismo campo pero fuertes opuestos. "
            "{p1} juega del lado del {g1} y {p2} del lado del {g2}; cada uno defiende su propia demanda. "
            "Cuanto más extranjera le resulta a {p1} la postura de {p2} sobre el {g2}, más crece la distancia, porque uno dice primero la cercanía y el otro que debe conservarse la libertad. "
            "{p2} vive la misma tensión a su manera y, en lugar de reconciliarse, puede polarizarse en silencio. "
            "La sabiduría de la oposición está en la puerta: sostener demandas opuestas en una misma mesa cansa, pero es el único espejo que os hace crecer a ambos. "
            "La posición del {g1} en la casa {ev1} y del {g2} en la casa {ev2} decide dónde esta polaridad os completa y dónde os desgasta. "
            "{uygulama}No es una guerra sino un imán cuyos polos se apuntan; cuando encontráis el equilibrio, se vuelve el apoyo más fuerte de vuestra relación. "
            "{baglam}"
        ),
    },
}

# Mod bağlam cümlesi: anlatının sonuna eklenir.
SINASTRI_ANLATI_BAGLAM = {
    "es_sevgili": {
        "tr": "Bu bağ, sevgiyi hem duygu hem eylem olarak yaşamayı öğreten bir aşk ve evlilik temasıdır.",
        "en": "This bond is a love-and-marriage theme that teaches you to live love as both feeling and action.",
        "es": "Este vínculo es un tema de amor y matrimonio que enseña a vivir el amor como sentimiento y acción a la vez.",
    },
    "ebeveyn_cocuk": {
        "tr": "Bu bağ, nesiller arasında taşınan bir kadersel ders olarak yaşanır.",
        "en": "This bond is lived as a fated lesson carried between generations.",
        "es": "Este vínculo se vive como una lección destinada que se transmite entre generaciones.",
    },
    "bireysel_natal": {
        "tr": "Bu dinamik, içinizdeki iki alanın aynı deneyimde buluştuğu bir bütünleşme temasıdır.",
        "en": "This dynamic is a theme of integration where two inner spheres meet in the same experience.",
        "es": "Esta dinámica es un tema de integración donde dos esferas interiores se encuentran en la misma experiencia.",
    },
}

SINASTRI_ANLATI_UYGULAMA = {
    "tr": {
        "applying": "Bu açı uygulamada olduğundan, bu dinamik şu dönemde ilişkinizin gündemine doğrudan girer; onu birlikte dillendirdiğinizde, kıvılcım derinliğe dönüşür. ",
        "separating": "Bu açı ayrılmakta olduğundan, bu örüntü artık eskidir; üzerinde konuştukça yükü hafifler ve gittikçe şefkatte çözülür. ",
    },
    "en": {
        "applying": "Because the aspect is applying, this dynamic moves directly onto your agenda; once you name it together, the spark turns toward depth. ",
        "separating": "Because the aspect is separating, this pattern is an older one; the more you talk it through, the lighter it grows and the more it softens into affection. ",
    },
    "es": {
        "applying": "Como el aspecto es aplicativo, esta dinámica entra directamente en la agenda de la relación; en cuanto la nombran juntos, la chispa se vuelve profundidad. ",
        "separating": "Como el aspecto es separativo, esta pauta es antigua; cuanto más la conversan, más se aligera y se suaviza en cariño. ",
    },
}