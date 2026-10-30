import 'lunar_mansions.dart';

typedef _MansionText = ({String meaning, String doText, String avoidText});

// The names are traditional proper names; their descriptions are localized.
const _english = <_MansionText>[
  (meaning: 'Little belly', doText: 'Short journeys, communication, new beginnings', avoidText: 'Major investments, marriage'),
  (meaning: 'The Pleiades', doText: 'Community affairs, commerce, art', avoidText: 'Tasks requiring solitude'),
  (meaning: 'The follower', doText: 'Research, pursuit, secret matters', avoidText: 'Open agreements'),
  (meaning: 'White spot', doText: 'Cleaning, purification, worship', avoidText: 'Messy or complicated matters'),
  (meaning: 'The sign', doText: 'Travel, education, learning', avoidText: 'Inactive pursuits'),
  (meaning: 'The seed', doText: 'Planting, beginnings, planning', avoidText: 'Harvesting, finishing'),
  (meaning: 'The eagle', doText: 'High ambitions, leadership', avoidText: 'Tasks requiring humility'),
  (meaning: 'Corner of the eye', doText: 'Observation, analysis, strategy', avoidText: 'Hasty decisions'),
  (meaning: 'The forehead', doText: 'Honor, recognition, official matters', avoidText: 'Secrecy'),
  (meaning: "The lion's mane", doText: 'Strength, courage, defense', avoidText: 'Retreat'),
  (meaning: 'The turn', doText: 'Transformation, renewal', avoidText: 'Remaining unchanged'),
  (meaning: 'The caller', doText: 'Communication, invitations, meetings', avoidText: 'Working alone'),
  (meaning: 'The high one', doText: 'Rising, progress', avoidText: 'Decline, retreat'),
  (meaning: 'The covering', doText: 'Protection, concealment, security', avoidText: 'Disclosure, exposure'),
  (meaning: 'The scales', doText: 'Balance, agreement, law', avoidText: 'One-sided decisions'),
  (meaning: 'The crown', doText: 'Coronation, honoring others', avoidText: 'Humiliation'),
  (meaning: 'The heart', doText: 'Love, bonds, family', avoidText: 'Coldness, separation'),
  (meaning: 'The tail', doText: 'Finishing, completion', avoidText: 'Beginnings'),
  (meaning: 'The ostrich', doText: 'Speed, movement, travel', avoidText: 'Waiting'),
  (meaning: 'The city', doText: 'Settlement, construction, home', avoidText: 'Destruction'),
  (meaning: 'The sacrificer', doText: 'Sacrifice, helping others, charity', avoidText: 'Selfishness'),
  (meaning: 'The swallower', doText: 'Cleaning, purification', avoidText: 'Accumulation'),
  (meaning: 'Happiness', doText: 'Joy, celebration, marriage', avoidText: 'Mourning, sadness'),
  (meaning: 'The tents', doText: 'Community, family, hospitality', avoidText: 'Solitude'),
  (meaning: 'The opening', doText: 'Emptying, cleaning, purification', avoidText: 'Filling, beginnings'),
  (meaning: 'The second opening', doText: 'Finishing, closure', avoidText: 'Opening'),
  (meaning: 'The belly of the fish', doText: 'Depth, introspection, meditation', avoidText: 'Superficial matters'),
  (meaning: 'The rope', doText: 'Binding, bringing together, contracts', avoidText: 'Breaking ties, separation'),
];

const _spanish = <_MansionText>[
  (meaning: 'El pequeño vientre', doText: 'Viajes cortos, comunicación, nuevos comienzos', avoidText: 'Grandes inversiones, matrimonio'),
  (meaning: 'Las Pléyades', doText: 'Asuntos comunitarios, comercio, arte', avoidText: 'Tareas que requieren soledad'),
  (meaning: 'El que sigue', doText: 'Investigación, seguimiento, asuntos secretos', avoidText: 'Acuerdos abiertos'),
  (meaning: 'La mancha blanca', doText: 'Limpieza, purificación, culto', avoidText: 'Asuntos sucios o complicados'),
  (meaning: 'La señal', doText: 'Viajes, educación, aprendizaje', avoidText: 'Actividades sin movimiento'),
  (meaning: 'La semilla', doText: 'Siembra, comienzos, planificación', avoidText: 'Cosecha, finalización'),
  (meaning: 'El águila', doText: 'Grandes objetivos, liderazgo', avoidText: 'Tareas que requieren humildad'),
  (meaning: 'El rabillo del ojo', doText: 'Observación, análisis, estrategia', avoidText: 'Decisiones apresuradas'),
  (meaning: 'La frente', doText: 'Honor, reconocimiento, asuntos oficiales', avoidText: 'Secretismo'),
  (meaning: 'La melena del león', doText: 'Fuerza, valentía, defensa', avoidText: 'Retirada'),
  (meaning: 'El giro', doText: 'Transformación, renovación', avoidText: 'Permanecer sin cambios'),
  (meaning: 'El que llama', doText: 'Comunicación, invitaciones, reuniones', avoidText: 'Trabajar a solas'),
  (meaning: 'El elevado', doText: 'Ascenso, progreso', avoidText: 'Descenso, retirada'),
  (meaning: 'La cubierta', doText: 'Protección, ocultación, seguridad', avoidText: 'Revelación, exposición'),
  (meaning: 'Los brazos de la balanza', doText: 'Equilibrio, acuerdos, derecho', avoidText: 'Decisiones unilaterales'),
  (meaning: 'La corona', doText: 'Coronación, honrar a otros', avoidText: 'Humillación'),
  (meaning: 'El corazón', doText: 'Amor, vínculos, familia', avoidText: 'Frialdad, ruptura'),
  (meaning: 'La cola', doText: 'Finalizar, completar', avoidText: 'Comienzos'),
  (meaning: 'El avestruz', doText: 'Rapidez, movimiento, viajes', avoidText: 'Esperar'),
  (meaning: 'La ciudad', doText: 'Asentamiento, construcción, hogar', avoidText: 'Destrucción'),
  (meaning: 'El sacrificador', doText: 'Sacrificio, ayuda, caridad', avoidText: 'Egoísmo'),
  (meaning: 'El que traga', doText: 'Limpieza, purificación', avoidText: 'Acumulación'),
  (meaning: 'Felicidad', doText: 'Alegría, celebración, matrimonio', avoidText: 'Duelo, tristeza'),
  (meaning: 'Las tiendas', doText: 'Comunidad, familia, hospitalidad', avoidText: 'Soledad'),
  (meaning: 'La abertura', doText: 'Vaciar, limpiar, purificar', avoidText: 'Llenar, comenzar'),
  (meaning: 'La segunda abertura', doText: 'Finalización, cierre', avoidText: 'Apertura'),
  (meaning: 'El vientre del pez', doText: 'Profundidad, introspección, meditación', avoidText: 'Asuntos superficiales'),
  (meaning: 'La cuerda', doText: 'Unir, vincular, contratos', avoidText: 'Romper vínculos, separarse'),
];

LunarMansion localizedLunarMansion(LunarMansion mansion, String languageCode) {
  final texts = switch (languageCode) {
    'en' => _english,
    'es' => _spanish,
    _ => null,
  };
  if (texts == null) return mansion;
  final text = texts[mansion.index];
  return LunarMansion(
    index: mansion.index,
    name: mansion.name,
    meaning: text.meaning,
    doText: text.doText,
    avoidText: text.avoidText,
  );
}
