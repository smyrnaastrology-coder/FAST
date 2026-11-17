/* Holavon — dil, menü ve küçük etkileşimler */
(function () {
  var STORE_KEY = "holavon.lang";
  var SUPPORTED = ["tr", "en", "es"];
  var HTML_LANG = { tr: "tr", en: "en", es: "es" };

  var META = {
    home: {
      tr: ["Holavon — Horary Oracle | Sorunu sor, gökyüzü cevaplasın", "Holavon, sorunun sorulduğu anın haritasını çıkarır ve klasik horary kurallarıyla yorumlar. Kayıp eşya, ilişki, iş ve para sorularına net cevaplar."],
      en: ["Holavon — Horary Oracle | Ask your question, let the sky answer", "Holavon maps the sky at the moment you ask and reads it with classical horary rules. Clear answers about lost objects, relationships, work and money."],
      es: ["Holavon — Horary Oracle | Haz tu pregunta, que responda el cielo", "Holavon cartografía el cielo del momento en que preguntas y lo interpreta con las reglas clásicas de la horaria. Respuestas claras sobre objetos perdidos, relaciones, trabajo y dinero."]
    },
    horary: {
      tr: ["Horary nedir? — Holavon", "Horary astrolojisi nedir, nasıl okunur, neye iyi gelir ve sınırları neler? Klasik yöntemin sade anlatımı."],
      en: ["What is horary? — Holavon", "What horary astrology is, how a chart is read, what it is good for, and its limits. A plain-language guide to the classical method."],
      es: ["¿Qué es la horaria? — Holavon", "Qué es la astrología horaria, cómo se lee una carta, para qué sirve y cuáles son sus límites."]
    },
    features: {
      tr: ["Özellikler — Holavon", "Tek soruya odaklı yorum, kayıp eşya modu, sesli soru, natal çapraz kontrol, üç dil ve PDF raporlar."],
      en: ["Features — Holavon", "Question-focused readings, lost-object mode, voice input, natal cross-check, three languages and PDF reports."],
      es: ["Funciones — Holavon", "Lecturas centradas en la pregunta, modo objetos perdidos, voz, cruce natal, tres idiomas e informes PDF."]
    },
    pricing: {
      tr: ["Fiyatlar — Holavon", "5, 15 ve 40 kredi paketleri ile aylık Pro. Satın alınan krediler süresiz geçerlidir."],
      en: ["Pricing — Holavon", "5, 15 and 40 credit packs plus monthly Pro. Purchased credits never expire."],
      es: ["Precios — Holavon", "Paquetes de 5, 15 y 40 créditos y Pro mensual. Los créditos comprados no caducan."]
    },
    faq: {
      tr: ["Sık sorulan sorular — Holavon", "Horary, krediler, abonelik ve teknik konularda sık sorulan soruların cevapları."],
      en: ["FAQ — Holavon", "Answers about horary, credits, subscriptions and technical questions."],
      es: ["Preguntas frecuentes — Holavon", "Respuestas sobre horaria, créditos, suscripciones y cuestiones técnicas."]
    },
    blog: {
      tr: ["Astroloji günlüğü — Holavon", "Horary'yi öğrenmek için kısa yazılar: temel kavramlar, kayıp eşya soruları ve Ay'ın rolü."],
      en: ["Astrology journal — Holavon", "Short reads to learn horary: core concepts, lost-object questions and the role of the Moon."],
      es: ["Diario de astrología — Holavon", "Lecturas breves para aprender horaria: conceptos básicos, objetos perdidos y el papel de la Luna."]
    },
    "blog-horary-nedir": {
      tr: ["Horary nedir, ne değildir? — Holavon", "Horary ile doğum haritası arasındaki fark, haritanın nasıl çizildiği ve aynı sorunun neden tekrar sorulmadığı."],
      en: ["What horary is — and isn't — Holavon", "The difference between horary and a birth chart, how the chart is cast, and why a question is never asked twice."],
      es: ["Qué es la horaria y qué no es — Holavon", "La diferencia entre horaria y carta natal, cómo se levanta la carta y por qué no se repite una pregunta."]
    },
    "blog-kayip-esya": {
      tr: ["Kayıp eşya sorusu nasıl sorulur? — Holavon", "Doğru cümle, doğru zaman ve kayıp eşya sorusunda haritanın hangi göstergelerine bakıldığı."],
      en: ["How to ask a lost-object question — Holavon", "The right sentence, the right moment, and which chart indicators a lost-object reading uses."],
      es: ["Cómo preguntar por un objeto perdido — Holavon", "La frase correcta, el momento correcto y los indicadores de la carta que se usan."]
    },
    "blog-ay": {
      tr: ["Horary'de Ay neden bu kadar önemli? — Holavon", "Ay'ın evi, burcu, son açısı ve boş yolda olması horary yorumunda zamanlamayı nasıl belirler?"],
      en: ["Why the Moon matters in horary — Holavon", "How the Moon's house, sign, final aspect and void-of-course state determine timing in a horary reading."],
      es: ["Por qué la Luna importa en horaria — Holavon", "Cómo la casa, el signo, el último aspecto y la Luna vacía de curso determinan el tiempo en una lectura horaria."]
    }
  };

  function getLang() {
    try {
      var saved = localStorage.getItem(STORE_KEY);
      if (saved && SUPPORTED.indexOf(saved) !== -1) return saved;
    } catch (e) {}
    var nav = (navigator.language || "tr").slice(0, 2).toLowerCase();
    return SUPPORTED.indexOf(nav) !== -1 ? nav : "tr";
  }

  function apply(lang) {
    var dict = (window.HOLAVON_I18N || {})[lang] || window.HOLAVON_I18N.tr;
    document.documentElement.lang = HTML_LANG[lang] || lang;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      if (dict[key] != null) el.textContent = dict[key];
    });
    document.querySelectorAll("[data-i18n-attr]").forEach(function (el) {
      el.getAttribute("data-i18n-attr").split(",").forEach(function (pair) {
        var bits = pair.split(":");
        if (bits.length !== 2) return;
        var attr = bits[0].trim();
        var key = bits[1].trim();
        if (dict[key] != null) el.setAttribute(attr, dict[key]);
      });
    });
    document.querySelectorAll(".lang button").forEach(function (b) {
      var on = b.getAttribute("data-lang") === lang;
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
    var page = document.body.getAttribute("data-page");
    var m = META[page];
    if (m && m[lang]) {
      document.title = m[lang][0];
      var desc = document.querySelector('meta[name="description"]');
      if (desc) desc.setAttribute("content", m[lang][1]);
      var ogT = document.querySelector('meta[property="og:title"]');
      if (ogT) ogT.setAttribute("content", m[lang][0]);
      var ogD = document.querySelector('meta[property="og:description"]');
      if (ogD) ogD.setAttribute("content", m[lang][1]);
    }
    if (document.body) document.body.classList.add("lang-ready");
  }

  function setLang(lang) {
    if (SUPPORTED.indexOf(lang) === -1) return;
    try { localStorage.setItem(STORE_KEY, lang); } catch (e) {}
    apply(lang);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var lang = getLang();
    apply(lang);

    document.querySelectorAll(".lang button").forEach(function (b) {
      b.addEventListener("click", function () { setLang(b.getAttribute("data-lang")); });
    });

    var toggle = document.querySelector(".nav-toggle");
    var nav = document.querySelector(".nav");
    if (toggle && nav) {
      toggle.addEventListener("click", function () {
        var open = nav.classList.toggle("open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      nav.querySelectorAll("a").forEach(function (a) {
        a.addEventListener("click", function () { nav.classList.remove("open"); });
      });
    }

    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
        });
      }, { threshold: 0.12 });
      document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
    } else {
      document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("in"); });
    }
  });
})();
