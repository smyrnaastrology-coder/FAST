/// Localized, non-predictive reflection themes for natal chart houses.
class EclipsePersonalPrompts {
  static const _tr = [
    'kimlik, kişisel hedefler ve kendini ifade etme',
    'gelir, bütçe, kaynaklar ve özdeğer',
    'iletişim, eğitim, yakın çevre ve kısa yolculuklar',
    'ev, aile, kökler ve yaşam alanı',
    'yaratıcılık, keyif, flört ve çocuklarla ilgili sorumluluklar',
    'günlük düzen, iş akışı ve sürdürülebilir alışkanlıklar',
    'ikili ilişkiler, ortaklıklar ve anlaşmalar',
    'paylaşılan kaynaklar, borçlar ve güven sınırları',
    'eğitim, uzak yolculuklar, inançlar ve dünya görüşü',
    'kariyer, kamusal rol ve uzun vadeli hedefler',
    'arkadaşlıklar, topluluklar ve gelecek planları',
    'dinlenme, kapanışlar, mahremiyet ve içe dönük çalışmalar',
  ];

  static const _en = [
    'identity, personal goals and self-expression',
    'income, budget, resources and self-worth',
    'communication, learning, local connections and short trips',
    'home, family, roots and living space',
    'creativity, enjoyment, dating and responsibilities involving children',
    'daily routines, workflow and sustainable habits',
    'one-to-one relationships, partnerships and agreements',
    'shared resources, debt and boundaries around trust',
    'education, long-distance travel, beliefs and worldview',
    'career, public role and long-term goals',
    'friendships, communities and future plans',
    'rest, closure, privacy and inward-focused work',
  ];

  static const _es = [
    'identidad, metas personales y expresión propia',
    'ingresos, presupuesto, recursos y autoestima',
    'comunicación, aprendizaje, entorno cercano y viajes cortos',
    'hogar, familia, raíces y espacio vital',
    'creatividad, disfrute, citas y responsabilidades relacionadas con hijos',
    'rutinas, flujo de trabajo y hábitos sostenibles',
    'relaciones individuales, asociaciones y acuerdos',
    'recursos compartidos, deudas y límites de confianza',
    'estudios, viajes largos, creencias y visión del mundo',
    'carrera, papel público y metas a largo plazo',
    'amistades, comunidades y planes de futuro',
    'descanso, cierres, privacidad y trabajo interior',
  ];

  static String houseTheme(int house, String languageCode) {
    final themes = switch (languageCode) {
      'tr' => _tr,
      'es' => _es,
      _ => _en,
    };
    return themes[(house - 1).clamp(0, 11)];
  }
}
