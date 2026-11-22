-- ============================================================================
-- Holavon — "Astroloğa Sor" push bildirimleri + 24 saat iade cron'u
--
-- Kullanım: Supabase Dashboard > SQL Editor > bu dosyayı çalıştır.
-- Idempotenttir; tekrar çalıştırmak güvenlidir.
--
-- Akış:
--   astro_questions INSERT                  -> astroloğa  "Yeni soru"
--   astro_questions UPDATE (answered)       -> kullanıcıya "Cevabınız hazır"
--   astro_questions UPDATE (expired/refund) -> kullanıcıya bilgi
--   pg_cron (15 dk)                          -> süresi geçen 'open' soruları
--                                              'expired' yapar (push tetiklenir)
--
-- Ön koşul: public.push_config tablosu ve HOLAVON_PUSH_SECRET
-- (supabase/push_notifications.sql). Aynı secret kullanılır.
-- ============================================================================

create extension if not exists pg_net with schema extensions;

-- ----------------------------------------------------------------------------
-- 1) Push uç noktası: aynı push_config satırına astro endpoint'i ekle
-- ----------------------------------------------------------------------------
alter table public.push_config
  add column if not exists astro_endpoint text;

update public.push_config
   set astro_endpoint = 'https://fbst-api-mzum.onrender.com/api/push/astro'
 where id = 1
   and (astro_endpoint is null or astro_endpoint = '');

-- ----------------------------------------------------------------------------
-- 2) Bildirim gönderen ortak yardımcı
-- ----------------------------------------------------------------------------
create or replace function public._astro_push_send(
  p_kind        text,
  p_user        uuid,
  p_question_id uuid,
  p_lang        text,
  p_topic       text,
  p_preview     text
)
returns void
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
  v_endpoint text;
  v_secret   text;
begin
  if p_user is null then
    return;
  end if;

  select coalesce(astro_endpoint, endpoint), secret
    into v_endpoint, v_secret
    from public.push_config
   where id = 1 and enabled = true;

  if v_endpoint is null or v_secret is null or v_secret = 'CHANGE_ME' then
    return;
  end if;

  perform net.http_post(
    url := v_endpoint,
    body := jsonb_build_object(
      'kind',        p_kind,
      'user_id',     p_user,
      'question_id', p_question_id,
      'lang',        coalesce(nullif(p_lang, ''), 'tr'),
      'topic',       coalesce(p_topic, ''),
      'preview',     left(coalesce(p_preview, ''), 160)
    ),
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'X-Holavon-Push-Secret', v_secret
    ),
    timeout_milliseconds := 5000
  );
end;
$$;

revoke all on function public._astro_push_send(text, uuid, uuid, text, text, text) from public;
revoke all on function public._astro_push_send(text, uuid, uuid, text, text, text) from anon;
revoke all on function public._astro_push_send(text, uuid, uuid, text, text, text) from authenticated;

-- ----------------------------------------------------------------------------
-- 3) Trigger fonksiyonu (INSERT + UPDATE)
-- ----------------------------------------------------------------------------
create or replace function public.notify_astro_push()
returns trigger
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
  v_astrologer uuid;
begin
  -- Yeni soru -> astroLOĞA
  if tg_op = 'INSERT' then
    if new.status in ('open', 'answered') then
      -- Ödeme anında açılan soruda INSERT bildirimi gönderme; UPDATE
      -- tarafında ele alınır. Yalnızca yeni gelen (bekleyen) sorular için
      -- astroloğa haber ver.
      return new;
    end if;

    if new.astrologer_id is not null then
      select a.user_id into v_astrologer
        from public.astrologers a
       where a.id = new.astrologer_id;
    end if;

    if v_astrologer is null then
      select a.user_id into v_astrologer
        from public.astrologers a
       where a.status = 'active' and a.user_id is not null
       order by a.sort_order
       limit 1;
    end if;

    perform public._astro_push_send(
      'new_question', v_astrologer, new.id, new.lang, new.topic,
      new.question
    );
    return new;
  end if;

  -- Durum değişiklikleri -> kullanıcıYA
  if tg_op = 'UPDATE' and old.status is distinct from new.status then
    if new.status = 'answered' then
      perform public._astro_push_send(
        'answered', new.user_id, new.id, new.lang, new.topic,
        left(coalesce(new.answer_text, ''), 140)
      );
    elsif new.status = 'expired' then
      perform public._astro_push_send(
        'expired', new.user_id, new.id, new.lang, new.topic, ''
      );
    elsif new.status = 'refunded' then
      perform public._astro_push_send(
        'refunded', new.user_id, new.id, new.lang, new.topic, ''
      );
    end if;
  end if;

  return new;
exception
  when others then
    raise warning '[push] notify_astro_push failed: %', sqlerrm;
    return new;
end;
$$;

revoke all on function public.notify_astro_push() from public;
revoke all on function public.notify_astro_push() from anon;
revoke all on function public.notify_astro_push() from authenticated;

drop trigger if exists trg_push_astro on public.astro_questions;
create trigger trg_push_astro
  after insert or update on public.astro_questions
  for each row execute function public.notify_astro_push();

-- ----------------------------------------------------------------------------
-- 4) 24 saatlik süre dolumu
-- ----------------------------------------------------------------------------
create or replace function public.expire_astro_questions()
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  v_count integer;
begin
  with expired as (
    update public.astro_questions
       set status = 'expired'
     where status = 'open'
       and deadline_at is not null
       and deadline_at < now()
    returning id
  )
  select count(*) into v_count from expired;
  return v_count;
end;
$$;

revoke all on function public.expire_astro_questions() from public;
revoke all on function public.expire_astro_questions() from anon;
revoke all on function public.expire_astro_questions() from authenticated;

-- pg_cron her Supabase projesinde açık olmayabilir. Varsa 15 dakikada bir
-- çalıştır; yoksa aşağıdaki "manuel" sorguyu Dashboard'dan zamanlayın
-- (Database > Cron Jobs > yeni job: select public.expire_astro_questions();).
do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    if exists (select 1 from cron.job where jobname = 'astro-expire-questions') then
      perform cron.unschedule('astro-expire-questions');
    end if;
    perform cron.schedule(
      'astro-expire-questions',
      '*/15 * * * *',
      'select public.expire_astro_questions();'
    );
    raise notice 'pg_cron: astro-expire-questions zamanlandi (15 dk).';
  else
    raise notice 'pg_cron yok: Dashboard > Database > Cron Jobs ile 15 dk job ekleyin.';
  end if;
exception
  when others then
    raise warning '[cron] astro-expire-questions kurulamadi: %', sqlerrm;
end $$;

-- ----------------------------------------------------------------------------
-- 5) Elle test
-- ----------------------------------------------------------------------------
-- Süresi geçmiş soruları hemen kapat:   select public.expire_astro_questions();
-- Push uç noktasını doğrula:             select endpoint, astro_endpoint,
--                                               (secret <> 'CHANGE_ME') as secret_ok
--                                          from public.push_config where id = 1;
