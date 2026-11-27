-- ============================================================================
--  Uzman basliginda "Horary" gorunurlugu
--
--  Amac: iOS danismanlik surumunde "Horary" kelimesi urunun icinde kalsin,
--  ancak App Store adi "Holavon: Uzman Danismanlik" olarak kalsin.
--
--  Etki: "Uzmani tanıyın" ekranindaki baslik satiri (headline) degisir.
--  Build gerektirmez; uygulama bu alani Supabase'den okur.
--
--  Calistirma: Supabase > SQL Editor > New query > yapistir > Run
-- ============================================================================

update public.astrologers
   set headline = 'Astroloji danışmanı · Horary ve matematiksel sinastri'
 where display_name = 'Fatih Asartepe';

-- Dogrulama
select display_name, headline, status
  from public.astrologers
 where display_name = 'Fatih Asartepe';
