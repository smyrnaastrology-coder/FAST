-- ============================================================================
-- Holavon — Astroloğa Sor: one-time Play purchase verification
--
-- Run in Supabase Dashboard > SQL Editor after astro_consult_birth.sql.
-- Idempotent. RevenueCat API verification remains server-side; this function
-- is executable only by the service_role backend.
-- ============================================================================

-- Tighten the client insert policy now that the single Play product is fixed.
drop policy if exists astro_questions_insert on public.astro_questions;
create policy astro_questions_insert on public.astro_questions for insert
  to authenticated
  with check (
    auth.uid() = user_id
    and status = 'pending_payment'
    and price_try = 1999.99
    and (product_id is null or product_id = 'sor_tek')
    and payment_ref is null
    and answer_text is null
    and answered_at is null
    and answer_pdf_url is null
    and answer_pdf_name is null
  );

-- One RevenueCat/Play transaction can pay for at most one question.
create unique index if not exists astro_questions_payment_ref_uidx
  on public.astro_questions (payment_ref)
  where payment_ref is not null;

create or replace function public.astro_question_payment_ready()
returns boolean
language sql
security definer
set search_path = public
as $$
  select true;
$$;

create or replace function public.reserve_astro_question_payment(
  p_question_id    uuid,
  p_user_id        uuid,
  p_transaction_id text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_question public.astro_questions%rowtype;
  v_payment_ref text;
begin
  if nullif(trim(coalesce(p_transaction_id, '')), '') is null then
    raise exception 'transaction_required';
  end if;
  v_payment_ref := 'pending_store:' || trim(p_transaction_id);

  select * into v_question
    from public.astro_questions
   where id = p_question_id
   for update;
  if not found then
    raise exception 'question_not_found';
  end if;
  if v_question.user_id <> p_user_id then
    raise exception 'question_user_mismatch';
  end if;
  if v_question.status = 'open'
     and v_question.payment_ref = 'store:' || trim(p_transaction_id) then
    return jsonb_build_object('ok', true, 'paid', true, 'status', 'open');
  end if;
  if v_question.status <> 'pending_payment' then
    raise exception 'question_not_pending_payment';
  end if;
  if v_question.payment_ref = v_payment_ref then
    return jsonb_build_object('ok', true, 'reserved', true);
  end if;
  if v_question.payment_ref is not null
     and v_question.payment_ref <> ('pending_lookup:' || p_question_id::text) then
    raise exception 'another_payment_attempt_reserved';
  end if;

  update public.astro_questions
     set payment_ref = v_payment_ref,
         product_id  = 'sor_tek',
         price_try   = 1999.99
   where id = p_question_id;
  return jsonb_build_object('ok', true, 'reserved', true);
end;
$$;

create or replace function public.reserve_astro_question_payment_lookup(
  p_question_id uuid,
  p_user_id     uuid
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_question public.astro_questions%rowtype;
  v_payment_ref text := 'pending_lookup:' || p_question_id::text;
begin
  select * into v_question
    from public.astro_questions
   where id = p_question_id
   for update;
  if not found then
    raise exception 'question_not_found';
  end if;
  if v_question.user_id <> p_user_id then
    raise exception 'question_user_mismatch';
  end if;
  if v_question.status = 'open'
     and v_question.payment_ref like 'store:%' then
    return jsonb_build_object('ok', true, 'paid', true, 'status', 'open');
  end if;
  if v_question.status <> 'pending_payment' then
    raise exception 'question_not_pending_payment';
  end if;
  if v_question.payment_ref = v_payment_ref
     or (v_question.payment_ref is not null
         and v_question.payment_ref like 'pending_store:%') then
    return jsonb_build_object('ok', true, 'reserved', true);
  end if;
  if v_question.payment_ref is not null then
    raise exception 'another_payment_attempt_reserved';
  end if;

  update public.astro_questions
     set payment_ref = v_payment_ref,
         product_id  = 'sor_tek',
         price_try   = 1999.99
   where id = p_question_id;
  return jsonb_build_object('ok', true, 'reserved', true);
end;
$$;

create or replace function public.confirm_astro_question_payment(
  p_question_id    uuid,
  p_user_id        uuid,
  p_transaction_id text,
  p_product_id     text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_question public.astro_questions%rowtype;
  v_payment_ref text;
  v_deadline timestamptz;
begin
  if p_product_id <> 'sor_tek' then
    raise exception 'invalid_product';
  end if;
  if nullif(trim(coalesce(p_transaction_id, '')), '') is null then
    raise exception 'transaction_required';
  end if;

  v_payment_ref := 'store:' || trim(p_transaction_id);

  select * into v_question
    from public.astro_questions
   where id = p_question_id
   for update;

  if not found then
    raise exception 'question_not_found';
  end if;
  if v_question.user_id <> p_user_id then
    raise exception 'question_user_mismatch';
  end if;

  -- Idempotent retry after the store purchase was already applied.
  if v_question.status = 'open' and v_question.payment_ref = v_payment_ref then
    return jsonb_build_object(
      'ok', true,
      'paid', true,
      'status', v_question.status,
      'deadline_at', v_question.deadline_at
    );
  end if;
  if v_question.status <> 'pending_payment' then
    raise exception 'question_not_pending_payment';
  end if;
  if v_question.payment_ref is not null
     and v_question.payment_ref <> ('pending_store:' || trim(p_transaction_id))
     and v_question.payment_ref <> ('pending_lookup:' || p_question_id::text) then
    raise exception 'another_payment_attempt_reserved';
  end if;

  update public.astro_questions
     set product_id   = 'sor_tek',
         price_try    = 1999.99,
         payment_ref  = v_payment_ref,
         status       = 'open',
         deadline_at  = now() + interval '24 hours'
   where id = p_question_id;

  select deadline_at into v_deadline
    from public.astro_questions
   where id = p_question_id;

  return jsonb_build_object(
    'ok', true,
    'paid', true,
    'status', 'open',
    'deadline_at', v_deadline
  );
end;
$$;

revoke all on function public.confirm_astro_question_payment(uuid, uuid, text, text)
  from public, anon, authenticated;
grant execute on function public.confirm_astro_question_payment(uuid, uuid, text, text)
  to service_role;
revoke all on function public.reserve_astro_question_payment(uuid, uuid, text)
  from public, anon, authenticated;
grant execute on function public.reserve_astro_question_payment(uuid, uuid, text)
  to service_role;
revoke all on function public.reserve_astro_question_payment_lookup(uuid, uuid)
  from public, anon, authenticated;
grant execute on function public.reserve_astro_question_payment_lookup(uuid, uuid)
  to service_role;
revoke all on function public.astro_question_payment_ready()
  from public, anon, authenticated;
grant execute on function public.astro_question_payment_ready()
  to service_role;

-- A paid question moves from pending_payment to open, so notify the astrologer
-- at payment confirmation time (the ordinary INSERT trigger correctly ignores
-- pending_payment rows).
create or replace function public.notify_astro_paid_question_open()
returns trigger
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
  v_astrologer uuid;
begin
  if old.status = 'pending_payment' and new.status = 'open' then
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
      'new_question', v_astrologer, new.id, new.lang, new.topic, new.question
    );
  end if;
  return new;
exception
  when others then
    raise warning '[astro-payment-push] %', sqlerrm;
    return new;
end;
$$;

revoke all on function public.notify_astro_paid_question_open() from public;
revoke all on function public.notify_astro_paid_question_open() from anon;
revoke all on function public.notify_astro_paid_question_open() from authenticated;

drop trigger if exists trg_astro_paid_question_open_push
  on public.astro_questions;
create trigger trg_astro_paid_question_open_push
  after update of status on public.astro_questions
  for each row
  when (old.status = 'pending_payment' and new.status = 'open')
  execute function public.notify_astro_paid_question_open();

notify pgrst, 'reload schema';
