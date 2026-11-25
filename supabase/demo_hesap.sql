-- ============================================================================
--  App Review icin demo danismanlik kaydi
--
--  Sirasi:
--   1) Supabase > Authentication > Users > Add user
--        e-posta: review@holavon.com   (kendi adresiniz de olabilir)
--        sifre:   guclu bir sifre
--        "Auto Confirm User" isaretli olsun
--   2) Storage > astro-pdfs > klasor: demo
--        docs/ornek_danismanlik_dosyasi.pdf dosyasini yukleyin
--        Public URL'i kopyalayin:
--        https://<PROJE-REF>.supabase.co/storage/v1/object/public/astro-pdfs/demo/ornek_danismanlik_dosyasi.pdf
--   3) Asagidaki iki degeri duzenleyip bu dosyayi SQL Editor'da calistirin:
--        v_email  -> 1. adimdaki e-posta
--        v_pdf    -> 2. adimdaki public URL
--
--  Idempotent: ayni kullanici icin ikinci kez eklemez, sadece gunceller.
-- ============================================================================

do $$
declare
  v_email text := 'review@holavon.com';
  v_pdf   text := 'https://PROJE-REF.supabase.co/storage/v1/object/public/astro-pdfs/demo/ornek_danismanlik_dosyasi.pdf';
  v_user  uuid;
  v_astro uuid;
  v_qid   uuid;
begin
  select id into v_user from auth.users where lower(email) = lower(v_email) limit 1;
  if v_user is null then
    raise exception 'Demo kullanici bulunamadi: % (Authentication > Users)', v_email;
  end if;

  select id into v_astro from public.astrologers
   where display_name = 'Fatih Asartepe' limit 1;
  if v_astro is null then
    raise exception 'astrologers tablosunda Fatih Asartepe yok; once ios_hazirlik.sql calistirin';
  end if;

  -- Ayni demo soru varsa onu guncelle, yoksa olustur.
  select id into v_qid from public.astro_questions
   where user_id = v_user and question like 'DEMO:%' limit 1;

  if v_qid is null then
    insert into public.astro_questions (
      user_id, astrologer_id, topic, question, lang, price_try, product_id,
      status, payment_ref, deadline_at, answer_text, answered_at,
      answer_pdf_url, answer_pdf_name, created_at
    ) values (
      v_user, v_astro, 'career',
      'DEMO: I have been offered a new position at a different company. Is this the right time '
      || 'to change my job, and if so, when should I sign the contract?',
      'en', 2399.99, 'sor_tek',
      'answered', 'demo:review', now() - interval '18 hours',
      'Yes to the change of position, no to signing within the next three weeks. '
      || 'The new role genuinely belongs to your professional direction: Venus, ruler of your '
      || 'ascendant, sits in the tenth house, and Saturn, ruler of the tenth, is in its own sign. '
      || 'What the chart does not support is the signature itself. Mercury, the significator of '
      || 'contracts, is in Pisces and turns retrograde within days; documents signed in that '
      || 'window are typically renegotiated in the first quarter. Read the draft now, ask for the '
      || 'clause on responsibilities, probation and review terms to be checked, and sign after '
      || 'Mercury resumes direct motion. Keep your current position until the new contract is '
      || 'signed; the chart gives no sign that the offer will be withdrawn while you wait. '
      || 'The full reasoning, with the chart breakdown, is in the attached PDF.',
      now() - interval '12 hours',
      v_pdf, 'ornek_danismanlik_dosyasi.pdf',
      now() - interval '20 hours'
    )
    returning id into v_qid;
  else
    update public.astro_questions
       set answer_text    = coalesce(answer_text, 'Demo answer'),
           answer_pdf_url = v_pdf,
           answer_pdf_name = 'ornek_danismanlik_dosyasi.pdf',
           status          = 'answered',
           answered_at     = coalesce(answered_at, now() - interval '12 hours')
     where id = v_qid;
  end if;

  raise notice 'Demo soru hazir: % (kullanici %)', v_qid, v_user;
end
$$;

-- Dogrulama: demo hesabin sorulari
select q.id, q.status, q.topic, q.lang,
       left(q.question, 60) as soru,
       (q.answer_text is not null) as cevap_var,
       (q.answer_pdf_url is not null) as pdf_var,
       q.created_at
  from public.astro_questions q
  join auth.users u on u.id = q.user_id
 where lower(u.email) = lower('review@holavon.com')
 order by q.created_at desc;
