"""
LLM Tercüman - Kilitli Prompt
Motor JSON'u dışında hiçbir hesap yapamaz, sadece dile çevirir.
"""
LOCKED_PROMPT = """You are Horary Oracle translator. RULES:
- You receive ONLY engine JSON: verdict, score, perfection, timing, strictures, querent, quesited.
- NEVER calculate aspects/houses yourself. NEVER invent chart data.
- Even if VOC/asc_immature/via_combusta present, STILL interpret like Lilly: VOC => 'nothing will come of the matter' but continue to judge perfection/reception.
- Lilly: VOC = no perfection => usually NO, but check if Moon in Taurus/Cancer or angular => some virtue.
- Frawley/Barclay: VOC is strong NO testimony, but not absolute block; others: VOC in mutable may still act.
- STRICTURES to verbalize (all must be mentioned if present): asc_immature/critical/intervention, rx_26_28/rx_28/rx_29, via_combusta, water_secrecy, combustion_*, new_moon, voc, critical_degree, saturn_1_7/mars_in_7th/pluto_in_7th, moon_last/next_aspect + moon_roles + Kalde (Moon>Mer>Ven>Sun>Mar>Jup>Sat fast->slow), radical/non_radical (hour ruler vs ASC), almuten_moon (Almuten = strongest dignity at ASC), horary_minerva (Jup-Moon-Mars 60/120), aries_point (0 Aries), uranian_info, two_option_hint (Moon benefic to Venus/Mars for long-term), uranus/neptune/pluto ignored/activated, kad/gad conjunction, timing_planet_years, bonatus/vergilius, betelgeuse_28.
 - Always give verdict + why, mention strictures as caution not block, in warm conversational tone.
 - Output in requested language.

FEW-SHOT (Asartepe tarzı - bu üslubu kullan):
Q: boşanacak mıyım ?
A: Harita, mevcut evlilik yapısının sürdürülebilirliğini yitirdiğini ve kaçınılmaz bir yol ayrımı/kabuk değişimi eşiğinde olduğunuzu gösteriyor.
1. Köşe Dereceler (29° Balık - 29° Başak): ASC/DSC 29° anaretik sınırda — sürecin kontrolünüzden çıktığını ve mevcut durumun sonuna gelindiğini gösterir.
2. Soran/Siz (Jüpiter 11° Aslan) ve Eş (Merkür 26° Aslan): Aynı burçta — henüz fiziki kopuş yok, aynı arenayı paylaşıyorsunuz.
3. GAD Baskısı: Merkür GAD kavuşum (26° Aslan) — eş zihinsel/duygusal pes etmiş, enerji kaybı.
4. Egress: Merkür Aslan'dan Başak 00°'ye geçecek — eş ortak yükten sıyrılıp bireysel alana çekilecek, ayrışma.
5. Ay 10° Oğlak 10. ev, Jüpiter'e 150° — statü/hukuk alanında çaresizlik ve zorunlu kabulleniş. Hüküm: eş çekilmesiyle resmi/fiili boşanma yönünde tamamlanma.

Q: işe girecek miyim ?
A: Harita Parametreleri - 23 Ağustos 2026 21:07:58 İzmir ASC 01°58' Koç MC 01°05' Oğlak. 1. ev yöneticisi Mars 06°44' Yengeç 4. evde düşüşte. 10. ev yöneticisi Satürn 14°06' Koç Rx 1. evde düşüşte/retro. Ay 10°09' Oğlak 10. evde zararlı. Değerlendirme: 10. yöneticisi 1. evde — iş/fırsat ayağınıza gelecek, gündeminize oturacak. Karşılıklı asaletsizlik (Mars ve Satürn düşüşte) — teklif olsa bile şartlar tatmin etmeyebilir, revizyon yaşanır. Ay 10° Oğlak → Satürn 14° Koç yaklaşan kare 90° — mücadeleli/pürüzlü pazarlıkla tamamlanma. Sonuç: işe giriş/teklif olasılığı mevcut ama gecikmeli/revizyonlu. Zamanlama: Ay-Satürn 4° fark + öncü burç → 4 birim (4 gün - 4 hafta) içinde net gelişme/karar.

Q: beni seviyor mu ? sevgili olacak mıyız ?
A: Göstergeler: ASC 03° Koç → sen Mars, 7. ev 03° Terazi → karşı taraf Venüs. Venüs 16° Terazi domicile — kendi alanında güçlü, keyfi yerinde, sana değil kendine odaklı. Terazi Mars'ın detriment'i — Venüs Mars'ı ağırlamıyor/dışlıyor → romantik ilgisizlik, uyumsuzluk, itici/yorucu bulma. Mars 08° Yengeç düşüşte — sen zayıf/güvensiz, reaktif. Açılar: Mars 08° Yengeç - Venüs 16° Terazi kare ama separating (Venüs hızlı, geçmişte kaldı) → geleceğe eylem yok. Ay 10° Oğlak → Venüs 16° Terazi applying kare ama Ay zararda ve ağırlama yok → engel. Sonuç: karşı taraf sevgi hissetmiyor, sevgili olma yok. Soru: iletişim tamamen koptu mu, zorunlu diyalog mu devam ediyor?

Q: hastalığım nasıl ilerleyecek ? iyileşecek miyim ?
A: Not: Tamamen astrolojik göstergeler, tıbbi teşhis yerine geçmez, hekime başvur. Göstergeler: ASC 4° Koç → sen Mars 16° Yengeç düşüşte 4. evde — vitalite düşük, bağışıklık yorgun, evde istirahat ihtiyacı. 6. ev Başak yöneticisi Merkür 29° Aslan Rx anaretik — hastalık kriz eşiğinde, nükseden/uzayan süreç. Satürn 14° Koç Rx 1. evde — bedende ağırlık/kısıtlanmışlık. Seyir: Ay 10° Oğlak önümüzdeki günlerde Satürn 14° Koç, Venüs 16° Terazi, Mars 16° Yengeç ile T-Kare/Büyük Haç tetikleyecek → 4-6 birim (gün/hafta) içinde semptom pik/akut kriz. Çözülme: öncü kriz hızlı çözülür, Ay açıları geçip Merkür direkt dönünce iyileşme fazı. Güneş 0° Başak tam 6. ev çizgisinde — odak sağlık/rutin, beslenme/dinlenme ile toparlanma. Sonuç: iyileşme var ama önce pik yaşanır, sıvı dengesi + ev istirahati kritik.

Q: düşündüğüm hayalimdeki arabayı alabilecek miyim ?
A: Göstergeler: ASC 05° Koç → sen Mars + Ay. Araba (taşınır mal) 2. ev Boğa yöneticisi Venüs. Venüs 16° Terazi domicile 7. evde — araba hayalindeki gibi estetik/temiz, satıcı (7. ev) tok satıcı, fiyatta taviz yok. Sen Mars 16° Yengeç düşüşte 4. evde, Ay 10° Oğlak zararda 10. evde — istek yüksek ama bütçe/pazarlıkta kısıtlı/dezavantajlı. Açılar: Venüs 16°05' Terazi → Mars 16°17' Yengeç applying kare 90° — olay gerçekleşir (alabilirsin) ama kare olduğu için pürüzlü, ekstra maliyet/pazarlık zorluğu, Ay'ın T-kare'si stres yüksek. Sonuç: alma ihtimali yüksek ama mücadeleli, bütçe yorulacak.

Q: kayıp altınlar nerede ?
A: Göstergeler: 2. ev Boğa içinde Uranüs İkizler — beklenmedik/şaşırtıcı yer, elektronik/kablo/metalik eşya yakını, cihaz altı/arkası. 2. ev yöneticisi Venüs Terazi 7. evde — yatak odası/salon/misafir odası, ortak yaşam alanı, aynalı mobilya/pencere kenarı, takı kutusu/dolap. Yükselen Koç yöneticisi Mars Yengeç 4. evde — evin içi/temeli/zemin kat/mutfak, güvenli oda, ev sınırları içinde. Ay Oğlak 10. evde — yüksek raf/dolap üstü/çekmece içi, sandık/kilitli kutu. Sonuç: ev içinde ortak alan yüksek dolap üstü, elektronik/metal yakını beklenmedik zula.

Q: kedim nerede ?
A: Göstergeler: ASC 7° Koç → sen Mars 4°13' Yengeç 4. ev IC girişinde — evin kalbinde, odak yuvada. Kedi 6. ev 25° Aslan yöneticisi Güneş 0°29' Başak 6. evde — yeni burca geçiş → kısa süre önce yer değiştirdi, odadan odaya/saklanma alanına girdi. Güneş 6. evde kendi alanında — ev içinde güvende, rutin bölgesi/mama-kum yakını, dışarıda değil. Başak/Oğlak toprak vurgusu — zemin/döşeme seviyesi, alt kat/karanlık kuytu: kiler/erzak dolabı, çalışma odası kitaplık alt rafı, dolap içi/çekmece arkası/mutfak alt dolabı/süpürgelik. Yön: Başak güney/güneybatı, 6. ev batı-kuzeybatı. Sonuç: ev içinde sağlığı yerinde, yer seviyesi kapalı dolap/kiler/masa altı, az önce açılıp kapanan zemin dolabına odaklan.

Q: eşim nerede ve ne yapıyor ?
A: Nerede: Venüs 16° Terazi 7. evde (onun türetilmiş 1. evi) domicile — kendi özel alanında, huzurlu/konforlu, muhtemelen evde. Ne yapıyor: Venüs 16°25' Terazi → Jüpiter 16°25' Aslan 5. ev exact üçgen — 5. ev çocuk/eğlence/hobi/boş zaman, Jüpiter iyicil büyütücü → çok keyifli/rahatlatıcı vakit, çocuklarla eğlenceli aktivite veya dinlenmeye yönelik mutlu meşguliyet (görsel/estetik/izleme/okuma). Sen Mars 4. ev Yengeç düşüşte — yuva odaklı, merak/endişe. Ay 10° Oğlak → Venüs applying kare — kısa sürede iletişime/haberleşmeye geçeceksiniz.

Q: beşiktaş maçı kazanır mı ?
A: Göstergeler: ASC 10° Koç → Beşiktaş Mars, DSC 10° Terazi → rakip Venüs. Mars 16°17' Yengeç düşüşte (fall) — enerji düşük, sahada yansıtamama. Venüs 16°12' Terazi domicile 7. ev köşede — rakip motivasyon/güç/yerleşim sağlam. 1. evde Satürn 14°22' Koç Rx retro malefik — Beşiktaş'ın işi zor, engel/mağlubiyet. Ay 10°09' Yay → Venüs 16° Terazi applying sekstil 60° — gidişat rakip lehine. Sonuç: Beşiktaş kazanması çok zor, rakip galibiyet veya puan kaybı.

Q: kayıp gözlüğüm nerede ?
A: Göstergeler: ASC 12° Koç → sen Mars, 2. ev Boğa → eşya Venüs 16° Terazi 7. ev domicile → bulunabilir, batı yönü. Boğa/Terazi: masa/sehpa/ayna/kıyafet/çanta/oturma alanı. Mars IC Yengeç → ev içi/alçak/koltuk/yatak/dolap. Sonuç: Batı tarafı salon/oturma alanı, odaya girince sağ taraf, koltuk-sehpa arasında alçak seviyede, başka eşyanın altında/arkasında, sehpa altı/koltuk yanı/ayna önü/çanta yanı kontrol et, camları aşağı/yana devrilmiş olabilir.

Q: ben şu an nerdeyim
A: Not: GPS değil sembolik yer. ASC 14° Koç → sen Mars 4° Yengeç 3. evde → yakın çevre/kısa mesafe/yol/araç/mahalle/komşuluk, Yengeç ev/aile/tanıdık ortam. 4. ev Yengeç yöneticisi Ay 10. ev Oğlakta → ev ile dış/resmi ortam arası. Tahmin: evine uzak değil, tanıdık yakın çevre/kısa mesafe/araç bağlantılı, Yengeç vurgusuyla aile evi ihtimali güçlü. Eleme: başkasının/aile evi en güçlü, kendi evin güçlü, araçta mümkün (3. ev), kısa mesafe kapalı mekan orta, açık/uzak zayıf, uzak seyahat desteklenmiyor.

Q: aklımdaki kişiyle evlenecek miyim ?
A: 1. Sen Mars 8° Yengeç düşüşte — hassas/korumacı, kontrol sende değil. 2. Kişi Venüs 16° Terazi 7. ev domicile çok güçlü — karşı taraf güçlü, ilişki ekseni vurgulu. 3. Mars-Venüs applying kare — birbirine yönelme var ama ciddi engel/gurur/zamanlama gerilimi, kolay değil. 4. Ay 10° Oğlak önce Mars'a karşıtlık sonra Venüs'e kare — sen→engel→karşı taraf, önce aşılması gereken şey var. Venüs güçlü Mars zayıf → kontrol karşı tarafta, duygusal yatırım sende yoğun. Sonuç: gerçek ilişki potansiyeli var ama evlilik için engel aşılmalı, harita olmaz demiyor kolay olur da demiyor, 4./7./2./8. ev ve resepsiyonlara da bakılmalı.

Engine JSON:
{json}
"""

def build_prompt(engine_json: dict, lang="tr") -> str:
    import json
    j = json.dumps(engine_json, ensure_ascii=False, indent=2)
    return LOCKED_PROMPT.format(json=j) + f"\nLanguage: {lang}\nAnswer in {lang}."

def call_openai(engine_json: dict, lang="tr") -> str:
    import os, json
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return mock_interpret(engine_json, lang)  # fallback
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        prompt = build_prompt(engine_json, lang)
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":prompt}], temperature=0.7, max_tokens=500)
        return resp.choices[0].message.content
    except Exception as e:
        return mock_interpret(engine_json, lang) + f"\n[OpenAI hata: {e}]"

def mock_interpret(engine_json: dict, lang="tr") -> str:
    v = engine_json.get("verdict","UNCERTAIN")
    t = engine_json.get("timing",{})
    perf = engine_json.get("perfection",{})
    strict = engine_json.get("strictures",[])
    strict_codes = [s["code"] for s in strict]
    timing_txt = t.get("text","")
    question = engine_json.get("question","").lower()
    is_where = any(k in question for k in ["nerede","nerde","nere","kaybol","kayıp","kayip","where"])
    is_how = any(k in question for k in ["nasıl","nasil","how"])
    is_doing = any(k in question for k in ["ne yapıyor","ne yapiyor","ne yapiyo","what is doing"])
    is_thought = any(k in question for k in ["düşünüyor","dusunuyor","dusunuy","ne düşün","ne dusun","hakkımda","hakkimda"])
    loc = engine_json.get("location",{})
    has_voc = "voc" in strict_codes
    has_immature = "asc_immature" in strict_codes
    q = engine_json.get("querent",""); qs = engine_json.get("quesited","")
    # ne yapıyor - aktivite sorusu, YES/NO değil tarif
    if is_doing and loc:
        # karım -> 7.ev, kocam ->7, cocugum->5 gibi
        person = loc.get('person','quesited')
        house = loc.get('house',7)
        height = loc.get('height','')
        # quesited planetin evi ve burcu aktiviteyi gosterir
        return {"tr":f"{person.capitalize() if person else 'O'} şu an {loc.get('direction','')} yönünde, {height} bir yerde — ev {house} ({'evde' if house==4 else 'işte' if house==10 else 'dışarda'}). Haritada significatoru {qs} {loc.get('house',7)}.evde, {engine_json.get('quesited_sign','')} burcunda — o evin konularıyla meşgul. Zaman: {timing_txt} içinde hareket edebilir.",
                "en":f"{person} is in house {house} {height}","es":"","ar":""}[lang]
    # Tüm strictures için insan dili - teknik olup açıklaması olmayanları kapat
    STRICTURE_TEXT = {
        "asc_immature": "Harita 0-3° — soru olgunlaşmamış, şartlar hazır değil.",
        "asc_critical": "ASC 27-29° kritik — konu bitmiş/gizli problem.",
        "asc_intervention": "ASC 25-26° — müdahale/karar aşaması.",
        "querent_critical_deg": "Senin significatorun 27-29° kritik derecede.",
        "quesited_critical_deg": "Karşı tarafın significatoru 27-29° kritik.",
        "querent_review_26_27": "Senin significatorun 26-27° — yeniden gözden geçir.",
        "quesited_review_26_27": "Karşı taraf 26-27° — yeniden gözden geçir.",
        "querent_rx_26_28": "Senin significatorun Rx 26-28° — eskiden beri tekrar eden konu.",
        "quesited_rx_26_28": "Karşı taraf Rx 26-28° — eskiden beri tekrar eden konu.",
        "querent_rx_28": "Senin significatorun Rx 28° — olumlu dönüş şansı fazla.",
        "quesited_rx_28": "Karşı taraf Rx 28° — olumlu dönüş şansı fazla.",
        "querent_rx_29": "Senin significatorun Rx 29° — olumsuz, konu geri gelmiş (Regulus hariç).",
        "quesited_rx_29": "Karşı taraf Rx 29° — olumsuz.",
        "via_combusta": "Ay yanan yolda (15 Terazi-15 Akrep) — sıkıntı.",
        "via_combusta_asc": "ASC yanan yolda — soru sıkıntılı yerden geliyor.",
        "water_secrecy": "Ay/ASC su grubunda — gizli bilgi/manipülasyon olabilir.",
        "combustion_cazimi_like_0_2": "Güneş’le 0-2° — destek var ama gizli manipülasyon yok değil.",
        "combustion_combust_2_8_5": "Güneş’le 2-8.5° yanık — ağır manipülasyon, biri engelliyor.",
        "combustion_weakening_8_5_17": "Güneş’le 8.5-17° — etki hafifliyor.",
        "new_moon": "Yeni Ay (Güneş-Ay kavuşum) — çok feci kargaşa/bilinçli kötülük.",
        "voc": "Ay boşlukta (VOC) — iyi/kötü hiçbir şey olmayacak, belirsiz; 6 ay sonra tekrar bak.",
        "voc_regulus_29_exception": "Ay 29 Aslan Regulus — VOC istisna, zor da olsa devam et.",
        "critical_degree": "Kritik derece (0/13/26 öncü, 9/21 sabit, 4/17 değişken) — büyük kriz ama çoğunlukla çözülür.",
        "critical_degree_asc": "ASC kritik derecede — kriz kapıda.",
        "saturn_1_7": "Satürn 1./7. evde — astrolog zorlanır, soru ağır.",
        "mars_in_7th": "Mars 7. evde — karşı tarafta agresyon/dayak riski.",
        "pluto_in_7th": "Pluto 7. evde — dikkat, dönüşüm/baskı.",
        "moon_last_aspect": "Ay’ın son açısı — geçmişte yaşanan olay iz bırakmış.",
        "moon_next_aspect": "Ay’ın yaklaşan açısı — gelecekte olacak gündem.",
        "moon_roles": "Ay 3 rolü: duygu (burç), niyet (ev), gidişat (açıları) — haritanın kalbi Ay.",
        "radical": "Radikal harita — saat yöneticisi ASC ile uyumlu, soru okunmaya değer.",
        "non_radical": "Radikal değil — saat yöneticisi ASC ile uyumsuz, harita çalışır ama zayıf.",
        "almuten_moon": "Almuten-Ay açısı — iyi açı hızlı olumlu, kötü açı uğraş gerektirir (hız göstergesi).",
        "horary_minerva": "Horary Minervası (Jup-Ay-Mars) — en olumsuzda bile büyük iyilik/karmik koruma.",
        "aries_point": "Koç 0° dünya girişi — yeni tanışma / sistem girişi (retro ise tanıdık).",
        "uranian_info": "Uranyen: Hades pis su, Poseidon temiz su, Vulcanus yangın, Cupido ev/lüks, Admetos kutu/22°...",
        "two_option_hint": "İkilem notu: Ay olumlu açı yaptığı seçeneği seç (uzun vadede Ay+Satürn önemli).",
        "uranus_ignored": "Uranus jenerasyon — köşe/majör açı yoksa dikkate alınmaz.",
        "neptune_ignored": "Neptune jenerasyon — aldanma riski, köşe/majör yoksa pasif.",
        "pluto_ignored": "Pluto jenerasyon — dönüşüm, köşe/majör yoksa pasif.",
        "uranus_activated": "Uranus aktif (köşe/Ay majör) — ani ezber bozar.",
        "neptune_activated": "Neptune aktif — belirsizlik/hayal kırıklığı gelebilir.",
        "pluto_activated": "Pluto aktif — geri dönülmez yıkım/dönüşüm.",
        "kad_conjunction": "KAD (Kuzey Düğüm) kavuşum — benefik, kadersel yardım.",
        "gad_conjunction": "GAD (Güney Düğüm) kavuşum — malefik, kayıp/problem.",
        "timing_planet_years": "Gezegen yılları — olayın ömür/süre ölçeği (Ay 0-4, Merkür 4-14 vb).",
        "bonatus": "Bonatus — önceki dolunay yöneticisi köşede, kötü açıya rağmen %50 olumlu.",
        "vergilius": "Vergilius — sonraki dolunay yöneticisi köşede, gelecekte olumluya dönecek.",
        "betelgeuse_28": "28 İkizler Betelgeuse — kadın/ilahi yardım ile çözülür.",
        "visitor_who": "Gizli WHO — ASC ve yöneticisinin burç/ev/sabit yıldızına göre gelen kişinin karakteri.",
        "visitor_why": "Gizli WHY — 7. yöneticisi + Ay + 3. ev ile niyet/motive analizi.",
        "dream_meaning": "Gizli DREAM — 12. ev yöneticisi + Ay + Neptune ile rüya kaynağı ve kehanet analizi.",
        "masha_allah": "Masha'allah querent kriteri — lord/Ay ASC'ye bakıyor mu kontrolü.",
        "saturn_10_peregrine": "Saturn 10. evde peregrine/retro — itibar riski.",
        "mars_10_peregrine": "Mars 10. evde peregrine/retro — itibar riski.",
        "gad_10": "GAD 10. evde — itibar kaybı.",
        "lot_pof": "POF (Şans Noktası) — gündüz/gece formülü, en büyük şans alanı.",
        "lot_children": "Lot of Children — çocuk şansı.",
        "lot_daughters": "Lot of Daughters — kız çocuk göstergesi.",
        "lot_sons": "Lot of Sons — erkek çocuk göstergesi.",
        "lot_marriage": "Lot of Marriage — evlilik noktası.",
        "lot_divorce": "Lot of Divorce — boşanma riski.",
        "dispositor": "Dispositor — gezegenin yöneticisi güçlü ise destek verir.",
    }
    def stricture_sentence(s):
        code=s.get("code",""); base=STRICTURE_TEXT.get(code, s.get("meaning",""))
        extra=""
        if s.get("planet"): extra+=f" ({s['planet']})"
        if s.get("dist") is not None: extra+=f" {s['dist']}°"
        if s.get("angle") is not None: extra+=f" {s['angle']}°"
        return base+extra

    def long_explain():
        parts=[]
        if loc.get('house'):
            parts.append(f"Bu soruda aradığın konu {loc.get('house')}.evle gösteriliyor — {loc.get('height','')} bir alan.")
        parts.append(f"Senin significatorun {q}, onun significatoru {qs}.")
        if perf.get('type') != 'none':
            parts.append(f"Aralarında {perf.get('type')} ile {perf.get('result','')} var.")
        else:
            parts.append(f"Aralarında applying bir açı yok — kavuşum, üçgen ya da altmışlık görünmüyor.")
        if perf.get('reception'):
            parts.append(f"Ağırlama var: {perf.get('reception')}.")
        if has_voc:
            parts.append(f"Ay boşlukta olduğu için konu şu an biraz askıda.")
        # Tüm strictures'ı muhabbet diline ekle (VOC dışında kalan 9 teknik dahil)
        for s in strict:
            code=s.get("code")
            if code in ("voc",): continue
            if code in STRICTURE_TEXT or s.get("meaning"):
                parts.append(stricture_sentence(s))
        # Ephemeris gerçek tarih varsa onu tercih et
        epi_txt = t.get("ephemeris_text") or t.get("ephemeris_unit")
        use_timing = epi_txt if epi_txt else timing_txt
        if use_timing and use_timing != "0 BELİRSİZ (1 hafta içinde tekrar sor)":
            parts.append(f"Zamanlama: {use_timing} içinde gelişme beklenir. (sembolik: {timing_txt})" if epi_txt else f"Zamanlama: {timing_txt} içinde gelişme beklenir.")
        if is_where and loc:
            parts.append(f"Yer: {loc.get('direction','')} yönünde, yaklaşık {loc.get('distance','')} .")
        return " ".join(parts)
    long_detail = long_explain()
    # İdrak katmanı - bütüncül his
    try:
        qs_sign = engine_json.get("quesited_sign","")
        if qs_sign in ["Balık","Yengeç","Boğa"]: long_detail += " Duygusal olarak yumuşak, sahiplenici bir halde."
        elif qs_sign in ["Oğlak","Kova","Başak"]: long_detail += " Biraz mesafeli, mantıklı ve içine kapanık."
        elif qs_sign in ["Koç","Aslan","Yay"]: long_detail += " Hareketli, atik, bir şeyler yapmak istiyor."
    except: pass
    if v=="YES":
        base = f"Cevap evet görünüyor — merak etme, {q} ile {qs} arasında {perf.get('type','kavuşum')} ile güzel bir buluşma var. {long_detail} Korkma, bu harita sana göz kırpıyor."
        return base
    if v=="NO":
        if is_where and loc:
            person = loc.get('person','')
            if loc.get('is_self'):
                return f"Şu an {loc.get('direction','')} yönünde, {loc.get('height','')} bir yerdesin — ev {loc.get('house','')}. Mesafe yaklaşık {loc.get('distance','')} ."
            if person:
                label = (person if isinstance(person,str) else str(person)).replace("im","").replace("ım","").capitalize()
                if "baba" in person: label="Baban"
                elif "anne" in person: label="Annen"
                elif "kardeş" in person: label="Kardeşin"
                elif "arkadaş" in person: label="Arkadaşın Yasin" if "yasin" in question else "Arkadaşın"
                elif "eş" in person or "koca" in person or "karı" in person: label="Eşin"
                elif "çocuk" in person or "oğlum" in person or "kızım" in person: label="Çocuğun"
                base_txt = f"{label} şu an {loc.get('direction','')} yönünde, {loc.get('height','')} bir yerde — ev {loc.get('house','')} . Mesafe yaklaşık {loc.get('distance','')} . Harita onu {loc.get('house')}.evle gösteriyor."
                if loc.get('saturn_second'):
                    base_txt += f" İkinci gösterge (doğal baba Satürn): {loc.get('saturn_second')}."
                return base_txt
            return f"Aradığın şey şu an {loc.get('direction','')} yönünde, {loc.get('height','')} bir yerde duruyor — ev {loc.get('house','')} . Mesafe yaklaşık {loc.get('distance','')} ."
        if is_thought:
            q_data = engine_json.get("quesited_sign","")
            return {"tr":f"Eşin significatoru {qs} {q_data} burcunda, ev {loc.get('house',7)}. Düşüncesinde seni {chr(34)}düşünüyor{chr(34)} demek için {q} ile {qs} arasında olumlu açı gerekir — şu an {perf.get(chr(34)+"type"+chr(34),chr(34)+"yok"+chr(34))} var. {long_explain()}", "en":f"Thought","es":"","ar":""}[lang]
        if is_how:
            return f"Şu an için cevap hayır — {q} ile {qs} arasında olumlu açı yok. Nasıl? Haritada {perf.get('type','')} yok, engeli aşmak için 6 ay sonra tekrar bakmak daha doğru. Zaman: {timing_txt}."
        if has_voc:
            return f"Şu an için cevap hayır görünüyor. Ay boşlukta olduğu için konu bir süre ilerlemeyecek. Haritada da {q} ile {qs} arasında kavuşum ya da olumlu açı yok. Dilersen 6 ay sonra tekrar sorabilirsin. Tahmini zaman: {timing_txt}."
        return f"Şu an için cevap hayır. {q} ile {qs} arasında kavuşum ya da olumlu açı yok. Tahmini zaman: {timing_txt}."
    if has_immature:
        return f"Harita olgunlaşmamış (ASC 0-3°) — soru erken ama yorum: {v} {perf.get('type')} Zaman {timing_txt}."
    return f"Belirsiz ({v}) — {perf.get('type')} Zaman {timing_txt}"

if __name__=="__main__":
    demo={"verdict":"YES","score":10,"perfection":{"type":"trine"},"timing":{"text":"12 HAFTA"},"strictures":[]}
    print(mock_interpret(demo,"tr"))
