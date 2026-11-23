-- ============================================================================
-- Holavon — Astroloğa Sor: doğum bilgisi + PDF cevap
--
-- Kullanım: Supabase Dashboard > SQL Editor > bu dosyayı çalıştır.
-- Idempotenttir: tekrar çalıştırmak güvenlidir.
--
-- Eklenenler:
--   * astro_questions: soruyu soranın doğum tarihi/saati/yeri ve koordinatları
--   * astro_questions: astrolog cevabına eklenen PDF bağlantısı
--   * storage: 'astro-pdfs' public bucket (yalnızca okuma; yazma service_role)
-- ============================================================================

alter table public.astro_questions
  add column if not exists birth_date      date,
  add column if not exists birth_time      text,
  add column if not exists birth_place     text,
  add column if not exists birth_lat       double precision,
  add column if not exists birth_lon       double precision,
  add column if not exists birth_tz        double precision,
  add column if not exists answer_pdf_url  text,
  add column if not exists answer_pdf_name text;

-- Kullanıcı yalnızca kendi adına ve ÖDENMEMİŞ soru oluşturur; cevap/PDF
-- alanları istemciden yazılamaz (politika yeniden tanımlanıyor).
drop policy if exists astro_questions_insert on public.astro_questions;
create policy astro_questions_insert on public.astro_questions for insert
  to authenticated
  with check (
    auth.uid() = user_id
    and status = 'pending_payment'
    and answer_text is null
    and answered_at is null
    and answer_pdf_url is null
    and answer_pdf_name is null
  );

-- ── Storage: astro-pdfs ─────────────────────────────────────────────────────
insert into storage.buckets (id, name, public)
values ('astro-pdfs', 'astro-pdfs', true)
on conflict (id) do update set public = true;

-- Herkes (giriş yapmış kullanıcı) public bucket'taki PDF'leri okuyabilir.
drop policy if exists astro_pdfs_read on storage.objects;
create policy astro_pdfs_read on storage.objects for select
  using (bucket_id = 'astro-pdfs');

-- Yazma/silme politikası YOK: yalnızca service_role (panel) yükler.
