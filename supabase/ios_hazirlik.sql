-- ============================================================================
--  iOS danismanlik surumu icin Supabase hazirligi
--
--  Supabase Dashboard > SQL Editor > bu dosyayi calistir.
--  Idempotenttir: tekrar calistirmak guvenlidir, veri silmez.
--
--  Onceki adim: astro_consult.sql, astro_consult_birth.sql,
--  astro_consult_payments.sql zaten calistirilmis olmali (Android'de
--  danismanlik calistigi icin normalde calistirilmistir). Asagidaki 1. bolum
--  bunu dogrular; eksik cikan olursa ilgili dosyayi once calistirin.
-- ============================================================================

-- ── 1) DURUM KONTROLU ───────────────────────────────────────────────────────
-- Ciktida 6 satir "var" gorunmelidir. "YOK" goren varsa ilgili .sql dosyasini
-- calistirin:
--   tablo yoksa          -> astro_consult.sql
--   kolon/bucket yoksa   -> astro_consult_birth.sql
--   fonksiyon yoksa      -> astro_consult_payments.sql
with kontrol(ad, durum) as (
  select 'tablo: astrologers',
         case when to_regclass('public.astrologers') is not null then 'var' else 'YOK' end
  union all
  select 'tablo: astro_questions',
         case when to_regclass('public.astro_questions') is not null then 'var' else 'YOK' end
  union all
  select 'kolon: birth_date',
         case when exists (
           select 1 from information_schema.columns
           where table_schema = 'public' and table_name = 'astro_questions'
             and column_name = 'birth_date'
         ) then 'var' else 'YOK' end
  union all
  select 'kolon: answer_pdf_url',
         case when exists (
           select 1 from information_schema.columns
           where table_schema = 'public' and table_name = 'astro_questions'
             and column_name = 'answer_pdf_url'
         ) then 'var' else 'YOK' end
  union all
  select 'fonksiyon: confirm_astro_question_payment',
         case when to_regprocedure('public.confirm_astro_question_payment(uuid,uuid,text,text)') is not null
              then 'var' else 'YOK' end
  union all
  select 'storage bucket: astro-pdfs',
         case when exists (select 1 from storage.buckets where id = 'astro-pdfs')
              then 'var' else 'YOK' end
)
select ad, durum from kontrol;

-- ── 2) UZMAN PROFILI ────────────────────────────────────────────────────────
-- iOS ana ekrani ve "Uzmani tanıyın" ekrani bu satiri okur.
-- ONEMLI: bio metnini kendi gercek egitim/deneyim bilginizle degistirin.
-- Sahte istatistik yazilmaz; rating bos (null), answer_count 0 baslar.
insert into public.astrologers
  (display_name, headline, bio, tier, status, langs, topics, max_open, sort_order)
select
  'Fatih Asartepe',
  'Astroloji danışmanı',
  'Astroloji danışmanlığında soru-cevap yöntemiyle çalışır: sorunuzu doğum '
  'verilerinizle birlikte değerlendirir, gerekçeli yazılı cevap ve PDF dosya '
  'hazırlar. Hizmet dili Türkçe, İngilizce ve İspanyolcadır.',
  'mentor',
  'active',
  '{tr,en,es}',
  '{love,career,family,lost,health,other}',
  10,
  0
where not exists (
  select 1 from public.astrologers where display_name = 'Fatih Asartepe'
);

-- Profil zaten varsa dilleri ve durumu iOS icin guncelle:
update public.astrologers
   set status = 'active',
       langs  = '{tr,en,es}'
 where display_name = 'Fatih Asartepe';

-- ── 3) PDF BUCKET (idempotent; zaten varsa dokunmaz) ────────────────────────
insert into storage.buckets (id, name, public)
values ('astro-pdfs', 'astro-pdfs', true)
on conflict (id) do update set public = true;

drop policy if exists astro_pdfs_read on storage.objects;
create policy astro_pdfs_read on storage.objects for select
  using (bucket_id = 'astro-pdfs');

-- ── 4) SON DURUM ────────────────────────────────────────────────────────────
-- Tek satir donmeli: uzman sayisi = 1 (veya daha fazla), aktif.
select
  count(*)                                          as uzman_sayisi,
  count(*) filter (where status = 'active')         as aktif,
  count(*) filter (where 'en' = any(langs))         as ingilizce_hizmet,
  string_agg(display_name, ', ')                    as isimler
from public.astrologers;

-- Istege bagli: mevcut soru sayisi (iOS oncesi durum)
select
  count(*)                                                   as toplam_soru,
  count(*) filter (where status = 'answered')                as cevaplanan,
  count(*) filter (where status = 'pending_payment')         as odeme_bekleyen,
  count(*) filter (where answer_pdf_url is not null)         as pdf_ekli
from public.astro_questions;
