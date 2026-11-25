-- ============================================================================
--  Uzman profili (iOS "Uzmanı tanıyın" ekranının okuduğu kayıt)
--
--  Supabase Dashboard > SQL Editor > bu dosyayı çalıştırın.
--  Idempotent: satır varsa günceller, yoksa oluşturur. Veri silmez.
--
--  Not: bio üç dillidir (TR / EN / ES). Uygulama tek alan gösterdiği için
--  üç dil aynı metinde verilir; Apple inceleyicisi İngilizce bölümü okur.
--  rating null ve answer_count 0: gerçek değerlendirme gelene kadar sahte
--  istatistik gösterilmez (ekran bu alanları boşsa gizler).
-- ============================================================================

insert into public.astrologers
  (display_name, headline, bio, tier, status, langs, topics, max_open, sort_order)
select
  'Fatih Asartepe',
  'Astroloji danışmanı · Matematiksel sinastri',
  'Altı yıldır ücretli astroloji danışmanlığı yapıyor. Zafer Özyiğit''ten '
  'Temel–Orta Seviye ve İleri Derecede Kehanet, Oğuzhan Ceyhan''dan Astrolojide '
  'Uzmanlaşma, Kubilay Aktaş''tan (Kadim Bilgelik) Temel, Orta ve İleri Seviye '
  'eğitimlerini tamamladı. Matematik lisansı ve iktisat yüksek lisansı vardır. '
  'İlişki, kariyer ve aile sorularında çalışır; kendi geliştirdiği matematiksel '
  'sinastri tekniğini kullanır. Danışmanlık yalnızca yazılıdır; Türkçe, '
  'İngilizce ve İspanyolca hizmet verir.'
  || E'\n\n'
  || 'EN — Has worked as a paid astrological consultant for six years. '
  'Trained with Zafer Özyiğit (Foundation–Intermediate level and Advanced '
  'Divination), Oğuzhan Ceyhan (Specialisation in Astrology) and Kubilay Aktaş '
  '(Kadim Bilgelik: Foundation, Intermediate and Advanced levels). Holds a BSc '
  'in Mathematics and an MSc in Economics. Works on relationship, career and '
  'family questions using his own mathematical synastry technique. '
  'Consultations are written only, in Turkish, English and Spanish.'
  || E'\n\n'
  || 'ES — Ejerce como consultor astrológico remunerado desde hace seis años. '
  'Formado con Zafer Özyiğit (nivel básico–intermedio y adivinación avanzada), '
  'Oğuzhan Ceyhan (especialización en astrología) y Kubilay Aktaş (Kadim '
  'Bilgelik: niveles básico, intermedio y avanzado). Licenciado en Matemáticas '
  'y máster en Economía. Trabaja preguntas de relación, trabajo y familia con '
  'su propia técnica de sinastría matemática. La consulta es solo por escrito, '
  'en turco, inglés y español.',
  'mentor',
  'active',
  '{tr,en,es}',
  '{love,career,family,lost,health,other}',
  10,
  0
where not exists (
  select 1 from public.astrologers where display_name = 'Fatih Asartepe'
);

-- Satır zaten varsa (ör. ios_hazirlik.sql ile eklenmişse) metni güncelle:
update public.astrologers
   set headline = 'Astroloji danışmanı · Matematiksel sinastri',
       bio      = 'Altı yıldır ücretli astroloji danışmanlığı yapıyor. Zafer Özyiğit''ten '
                  'Temel–Orta Seviye ve İleri Derecede Kehanet, Oğuzhan Ceyhan''dan Astrolojide '
                  'Uzmanlaşma, Kubilay Aktaş''tan (Kadim Bilgelik) Temel, Orta ve İleri Seviye '
                  'eğitimlerini tamamladı. Matematik lisansı ve iktisat yüksek lisansı vardır. '
                  'İlişki, kariyer ve aile sorularında çalışır; kendi geliştirdiği matematiksel '
                  'sinastri tekniğini kullanır. Danışmanlık yalnızca yazılıdır; Türkçe, '
                  'İngilizce ve İspanyolca hizmet verir.'
                  || E'\n\n'
                  || 'EN — Has worked as a paid astrological consultant for six years. '
                  'Trained with Zafer Özyiğit (Foundation–Intermediate level and Advanced '
                  'Divination), Oğuzhan Ceyhan (Specialisation in Astrology) and Kubilay Aktaş '
                  '(Kadim Bilgelik: Foundation, Intermediate and Advanced levels). Holds a BSc '
                  'in Mathematics and an MSc in Economics. Works on relationship, career and '
                  'family questions using his own mathematical synastry technique. '
                  'Consultations are written only, in Turkish, English and Spanish.'
                  || E'\n\n'
                  || 'ES — Ejerce como consultor astrológico remunerado desde hace seis años. '
                  'Formado con Zafer Özyiğit (nivel básico–intermedio y adivinación avanzada), '
                  'Oğuzhan Ceyhan (especialización en astrología) y Kubilay Aktaş (Kadim '
                  'Bilgelik: niveles básico, intermedio y avanzado). Licenciado en Matemáticas '
                  'y máster en Economía. Trabaja preguntas de relación, trabajo y familia con '
                  'su propia técnica de sinastría matemática. La consulta es solo por escrito, '
                  'en turco, inglés y español.',
       status   = 'active',
       langs    = '{tr,en,es}',
       topics   = '{love,career,family,lost,health,other}'
 where display_name = 'Fatih Asartepe';

-- Doğrulama
select display_name, headline, status, langs, topics,
       (bio is not null) as bio_var,
       length(bio)       as bio_uzunluk
  from public.astrologers
 where display_name = 'Fatih Asartepe';
