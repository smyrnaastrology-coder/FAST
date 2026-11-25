-- ============================================================================
--  kullanim_analizi.sql — SADECE OKUMA (SELECT) sorgulari
--
--  Uygulama ekran bazli analitik tutmuyor; bu dosya Supabase'deki kayitlardan
--  "hangi modul gercekten kullaniliyor" sorusuna VEKIL (proxy) cevap uretir.
--  Supabase Dashboard -> SQL Editor -> sorguyu sec -> Run.
--
--  Onemli: buradaki sayilar "ekrani acan kisi" degil, "islem yapan kisi"dir.
--  Ornegin harita ekranini acip kaydetmeyen kullanici gorunmez.
-- ============================================================================

-- ── 1. Tek bakista modul kullanimi ──────────────────────────────────────────
-- Her modul icin: toplam kayit, benzersiz kullanici, son 30 gun kayit.
with moduller as (
  select 'Harita kaydi (user_charts)'            as modul, count(*) as kayit, count(distinct user_id) as kullanici, count(*) filter (where created_at > now() - interval '30 days') as son_30g from public.user_charts
  union all
  select 'Danismanlik sorusu'                    , count(*), count(distinct user_id), count(*) filter (where created_at > now() - interval '30 days') from public.astro_questions
  union all
  select 'Gonderi (posts)'                       , count(*), count(distinct user_id), count(*) filter (where created_at > now() - interval '30 days') from public.posts
  union all
  select 'Hikaye (stories)'                      , count(*), count(distinct user_id), count(*) filter (where created_at > now() - interval '30 days') from public.stories
  union all
  select 'Begeni (likes)'                        , count(*), count(distinct user_id), count(*) filter (where created_at > now() - interval '30 days') from public.likes
  union all
  select 'Yorum (comments)'                      , count(*), count(distinct user_id), count(*) filter (where created_at > now() - interval '30 days') from public.comments
  union all
  select 'Takip (follows)'                       , count(*), count(distinct follower_id), count(*) filter (where created_at > now() - interval '30 days') from public.follows
  union all
  select 'Hikaye goruntuleme'                    , count(*), count(distinct viewer_id), count(*) filter (where viewed_at > now() - interval '30 days') from public.story_views
  union all
  select 'Mesaj (DM)'                            , count(*), count(distinct sender_id), count(*) filter (where created_at > now() - interval '30 days') from public.messages
  union all
  select 'Dogum bilgisi kaydi'                   , count(*), count(distinct user_id), count(*) filter (where created_at > now() - interval '30 days') from public.user_birthdates
  union all
  select 'Gezegen kaydi (user_planets)'          , count(*), count(distinct user_id), count(*) filter (where created_at > now() - interval '30 days') from public.user_planets
)
select modul, kayit, kullanici, son_30g
from moduller
order by son_30g desc nulls last, kayit desc;

-- ── 2. Danismanlik: konu dagilimi ve durum ──────────────────────────────────
select
  topic                                              as konu,
  count(*)                                           as soru,
  count(distinct user_id)                            as kullanici,
  count(*) filter (where status = 'answered')        as cevaplandi,
  count(*) filter (where status = 'pending_payment') as odeme_bekliyor,
  count(*) filter (where status = 'open')            as acik,
  count(*) filter (where status = 'refunded')        as iade,
  round(avg(extract(epoch from (answered_at - created_at)) / 3600.0)::numeric, 1) as ort_saat
from public.astro_questions
group by topic
order by soru desc;

-- ── 3. Danismanlik: dil dagilimi ────────────────────────────────────────────
select lang, count(*) as soru
from public.astro_questions
group by lang
order by soru desc;

-- ── 4. Harita modulu: kisi basina kayit (kaydeden kullanicilar) ─────────────
select
  count(*)                                   as toplam_harita,
  count(distinct user_id)                    as kaydeden_kullanici,
  round(count(*)::numeric / greatest(count(distinct user_id), 1), 2) as kisi_basina,
  min(created_at)::date                      as ilk_kayit,
  max(created_at)::date                      as son_kayit
from public.user_charts;

-- ── 5. Aylik aktif kullanici (herhangi bir modulde islem yapan) ─────────────
with aktivite as (
  select user_id, created_at from public.user_charts
  union all select user_id, created_at from public.astro_questions
  union all select user_id, created_at from public.posts
  union all select user_id, created_at from public.stories
  union all select user_id, created_at from public.comments
  union all select sender_id, created_at from public.messages
  union all select follower_id, created_at from public.follows
)
select
  to_char(date_trunc('month', created_at), 'YYYY-MM') as ay,
  count(distinct user_id)                             as aktif_kullanici,
  count(*)                                            as islem
from aktivite
group by 1
order by 1 desc;

-- ── 6. Gunluk ortalama islem (son 30 gun) ───────────────────────────────────
with aktivite as (
  select user_id, created_at from public.user_charts
  union all select user_id, created_at from public.astro_questions
  union all select user_id, created_at from public.posts
  union all select user_id, created_at from public.stories
  union all select user_id, created_at from public.comments
  union all select sender_id, created_at from public.messages
)
select
  date_trunc('day', created_at)::date as gun,
  count(distinct user_id)             as kullanici,
  count(*)                            as islem
from aktivite
where created_at > now() - interval '30 days'
group by 1
order by 1 desc;

-- ── 7. Bildirim izni / cihaz kaydi (push kullanan kitle) ────────────────────
select
  count(*)                as kayitli_cihaz,
  count(distinct user_id) as kullanici,
  max(updated_at)::date   as son_kayit
from public.device_tokens;

-- ── 8. Sosyal modul sagligi: etkilesim orani ───────────────────────────────
select
  (select count(*) from public.posts)    as gonderi,
  (select count(*) from public.likes)    as begeni,
  (select count(*) from public.comments) as yorum,
  round(
    (select count(*) from public.likes)::numeric
    / greatest((select count(*) from public.posts), 1), 2
  ) as gonderi_basina_begeni;
