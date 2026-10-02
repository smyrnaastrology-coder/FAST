# -*- coding: utf-8 -*-
"""
Standart 36 puanlı Ashtakoot yorum metinleri — Español.

Yapı `ashtakoot_metinleri.py` ile birebir aynıdır; yalnızca metinler İspanyolcadır.
Birliktelik çerçevesi: pareja (es_sevgili) y padre-hijo (ebeveyn_cocuk).
"""

BANTLAR = ["mukemmel", "yuksek", "orta", "dusuk", "yok"]


def bant_bul(puan: int, azami: int) -> str:
    if azami <= 0 or puan <= 0:
        return "yok"
    oran = puan / azami
    if oran >= 1.0:
        return "mukemmel"
    if oran >= 0.70:
        return "yuksek"
    if oran >= 0.45:
        return "orta"
    return "dusuk"


KOOTA_METIN: dict = {

    "varna": {
        "ad": "Varna",
        "baslik": "Varna — Compatibilidad de casta",
        "soru": "¿Se entienden mutuamente sus dos sistemas de valores?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Varna idéntica",
                "aciklama": "Ambas Lunas caen en la misma varna (Brahmin, Kshatriya, Vaishya o "
                            "Shudra), la puntuación máxima de 1/1.",
                "ipucu": "En el Jyotish clásico la varna no es linaje sino una cualidad medida "
                         "según el pada en que estaba la Luna al nacer. No debe leerse como "
                         "clase social actual.",
            },
            "yuksek": {
                "baslik": "Varnas vecinas",
                "aciklama": "Categorías distintas pero contiguas; la diferencia rara vez se nota.",
                "ipucu": "Una historia familiar compartida o prioridades semejantes cierran esta "
                         "brecha.",
            },
            "orta": {
                "baslik": "Distantes pero sin conflicto",
                "aciklama": "Varnas diferentes, sin fricción ni atracción marcada.",
                "ipucu": "La armonía a largo plazo se construye con comunicación consciente.",
            },
            "dusuk": {
                "baslik": "Los dos extremos de la escala",
                "aciklama": "Los extremos opuestos de la escala varna, lo que indica posibles "
                            "diferencias de mirada cultural.",
                "ipucu": "La varna solo aporta 1 de los 36 puntos y nunca debe leerse sola.",
            },
            "yok": {
                "baslik": "Varna incompatible",
                "aciklama": "Las Lunas caen en varnas distintas.",
                "ipucu": "Revise los kootas de mayor peso: Nadi, Rasi y Gana.",
            },
        },
        "mod": {
            "es_sevgili": "Raíces familiares y mundo de valores compartidos dentro del respeto "
                          "mutuo.",
            "ebeveyn_cocuk": "El canal de transmisión de los valores familiares; la distancia "
                             "muestra cómo pasan de una generación a otra.",
        },
    },

    "vashya": {
        "ad": "Vashya",
        "baslik": "Vashya — Estilo de vida depredador / presa",
        "soru": "¿Se alinean su ritmo vital y su dinámica depredador-presa?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Mismo grupo vashya (2/2)",
                "aciklama": "Sus signos lunares pertenecen a la misma categoría vital: ambos "
                            "depredadores, ambos presas, o ambos terrestres.",
                "ipucu": "Vashya procede de una antigua clasificación de hábitos alimentarios: "
                         "Chatura (ave), Chatushpada (cuadrúpedo), Manushya (humano), Khala "
                         "(reptil/insecto).",
            },
            "yuksek": {
                "baslik": "Afinidad mediada (1/2)",
                "aciklama": "Las categorías difieren, pero un signo cae bajo el señor del otro. "
                            "Hay parentesco parcial.",
                "ipucu": "Esta puntuación llega por mediación, no por semejanza directa.",
            },
            "orta": {
                "baslik": "Categorías vecinas",
                "aciklama": "No hay puente entre los grupos; la combinación es neutra.",
                "ipucu": "Los hábitos diarios compartidos cierran esta distancia con facilidad.",
            },
            "dusuk": {
                "baslik": "Vínculo vashya débil",
                "aciklama": "Las categorías vashya están muy alejadas.",
                "ipucu": "Una puntuación baja describe el ritmo del vínculo, no su calidad.",
            },
            "yok": {
                "baslik": "Categorías opuestas",
                "aciklama": "Ni semejanza directa ni solapamiento a través del señor del signo.",
                "ipucu": "Es uno de los indicadores más fuertes de un ritmo vital distinto.",
            },
        },
        "mod": {
            "es_sevgili": "Compatibilidad del ritmo diario y del estilo de vida.",
            "ebeveyn_cocuk": "Cuánto encajan las necesidades evolutivas del hijo con el orden que "
                             "aporta el padre.",
        },
    },

    "tara": {
        "ad": "Tara",
        "baslik": "Tara — Suerte y sincronía temporal",
        "soru": "¿Se sincroniza el ritmo de uno con el del otro?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Mejor tara (3/3)",
                "aciklama": "En el ciclo de nueve nakshatras, la posición del primero cae en la "
                            "tara más afortunada del segundo.",
                "ipucu": "Tara es una medida novena que se repite una vez cada nueve "
                         "nakshatras. Todos tienen una tara; la pregunta es si las dos se solapan.",
            },
            "yuksek": {
                "baslik": "Tara intermedia (1/3)",
                "aciklama": "Posición media del ciclo. El ritmo funciona casi siempre, pero puede "
                            "apretar en periodos difíciles.",
                "ipucu": "Por sí sola, tara representa la porción de suerte asignada.",
            },
            "orta": {
                "baslik": "Tara inferior",
                "aciklama": "La parte baja del ciclo; las decisiones en pareja pueden ir a distinto "
                            "ritmo.",
                "ipucu": "Igualar a propósito el ritmo de decisión es suficiente.",
            },
            "dusuk": {
                "baslik": "Tara débil",
                "aciklama": "Se encuentran en extremos opuestos del ciclo de tara.",
                "ipucu": "Esta área exige paciencia y no debe acelerarse.",
            },
            "yok": {
                "baslik": "Tara más baja (0/3)",
                "aciklama": "El primer nakshatra cae en el rango más bajo del ciclo del segundo.",
                "ipucu": "Tara es direccional: A/B y B/A pueden dar resultados distintos.",
            },
        },
        "mod": {
            "es_sevgili": "Suerte y sincronía, la dimensión temporal del vínculo.",
            "ebeveyn_cocuk": "Cuánto encaja el ritmo del padre con las necesidades del hijo, y en "
                             "qué momentos puede responder a sus distintas etapas.",
        },
    },

    "yoni": {
        "ad": "Yoni",
        "baslik": "Yoni — Atracción física",
        "soru": "¿Qué tan fuerte es la atracción física y emocional?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Mismo animal, mismo género (4/4)",
                "aciklama": "Ambos nakshatras apuntan al mismo animal yoni. Yoni es el indicador "
                            "más claro de atracción física con 4 de 36 puntos.",
                "ipucu": "El género se lee del número de pada: los padas impares masculine y los "
                         "pares femeninos.",
            },
            "yuksek": {
                "baslik": "Mismo animal, género opuesto (3/4)",
                "aciklama": "El animal coincide pero difiere el género del pada. Clásicamente no "
                            "es igual, aunque nunca se rechaza.",
                "ipucu": "Jaimini trata la combinación de género opuesto como desigual pero "
                         "perdonada.",
            },
            "orta": {
                "baslik": "Animales distintos",
                "aciklama": "Los dos nakshatras señalan animales yoni diferentes.",
                "ipucu": "Un yoni distinto es un lenguaje de atracción distinto; el total lo "
                         "llevan Gana, Graha Maitri y Rasi.",
            },
            "dusuk": {
                "baslik": "Animales emparentados pero no emparejados",
                "aciklama": "Los animales son de la misma familia pero no son el mismo.",
                "ipucu": "El yoni por sí solo nunca basta.",
            },
            "yok": {
                "baslik": "Yoni incompatible (0/4)",
                "aciklama": "No hay yoni compartido. Algunos nakshatras (barca, tambor, mano, "
                            "vacío) no tienen pareja yoni y solo coinciden consigo mismos.",
                "ipucu": "El Yastriyotish construye el yoni con apenas quince parejas de animales, "
                         "por eso su cobertura es deliberadamente estrecha.",
            },
        },
        "mod": {
            "es_sevgili": "Atracción física e inclinación romántica.",
            "ebeveyn_cocuk": "La cercanía natural y el instinto protector entre padre e hijo, y "
                             "hacia qué lado se acomoda el niño con más facilidad.",
        },
    },

    "graha_maitri": {
        "ad": "Graha Maitri",
        "baslik": "Graha Maitri — Amistad planetaria",
        "soru": "¿Se acerca su visión de la vida a la del otro?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Mismo signo (5/5)",
                "aciklama": "Ambas Lunas ocupan el mismo signo, de modo que el señor es el mismo "
                            "planeta y la visión básica coincide.",
                "ipucu": "Mismo signo significa mismo planeta. El elemento (fuego/tierra/aire/agua) "
                         "no es aquí el factor decisivo.",
            },
            "yuksek": {
                "baslik": "Señores amigos (4/5)",
                "aciklama": "Signos distintos cuyos señores están en amistad natural.",
                "ipucu": "Es la amistad Naisargika, natural, no un vínculo kármico de vidas "
                         "anteriores.",
            },
            "orta": {
                "baslik": "Señores neutrales (3/5)",
                "aciklama": "Ni afinidad natural ni enemistad entre los señores.",
                "ipucu": "Las relaciones neutrales funcionan sin fricción en la mayoría de las "
                         "uniones largas.",
            },
            "dusuk": {
                "baslik": "Señores enemigos (1/5)",
                "aciklama": "Los señores están en enemistad natural, así que las visiones "
                            "básicas pueden diferir.",
                "ipucu": "El Sol (Leo) y Saturno (Acuario/Capricornio) son la pareja enemiga "
                         "clásica.",
            },
            "yok": {
                "baslik": "Amistad débil",
                "aciklama": "La puntuación más baja de la tabla direccional.",
                "ipucu": "Es el único koota indeciso; equivale a los 2 puntos del Vashya.",
            },
        },
        "mod": {
            "es_sevgili": "Coincidencia de valores, metas y prioridades vitales.",
            "ebeveyn_cocuk": "La capacidad del padre de transmitir una visión del mundo al hijo.",
        },
    },

    "gana": {
        "ad": "Gana",
        "baslik": "Gana — Temperamento básico",
        "soru": "¿Se completan mutuamente los temperamentos?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Mismo gana (6/6)",
                "aciklama": "Ambas Lunas están en la misma clase de temperamento: Deva, Manushya "
                            "o Rakshasa.",
                "ipucu": "Gana es la clasificación triple de Jaimini: Deva (maduro), Manushya "
                         "(equilibrado), Rakshasa (impulsivo).",
            },
            "yuksek": {
                "baslik": "Deva con Manushya (5/6)",
                "aciklama": "Madurez y equilibrio se apoyan mutuamente. Clásicamente es una "
                            "combinación complementaria de respeto recíproco.",
                "ipucu": "Jaimini cuenta esta entre las parejas donde todo está en su lugar.",
            },
            "orta": {
                "baslik": "Combinación débil",
                "aciklama": "El emparejamiento asimétrico Manushya-Rakshasa. Puntuación baja, "
                            "pero no rechazada.",
                "ipucu": "La tabla de gana es direccional; A/B y B/A pueden diferir.",
            },
            "dusuk": {
                "baslik": "Temperamentos opuestos",
                "aciklama": "Deva se encuentra con Rakshasa. Los textos clásicos lo leen como "
                            "señal de enemistad antigua (shatru).",
                "ipucu": "Seis de los 36 puntos dependen de este único ítem, así que mueve con "
                         "fuerza el total.",
            },
            "yok": {
                "baslik": "Gana incompatible (0/6)",
                "aciklama": "La tabla direccional no da puntos para este orden.",
                "ipucu": "Rakshasa con Manushya también es cero en la tabla clásica.",
            },
        },
        "mod": {
            "es_sevgili": "Compatibilidad de carácter y límites de la paciencia de cada uno.",
            "ebeveyn_cocuk": "Cuánto coincide la naturaleza del hijo con la del padre, y dónde "
                             "la crianza choca con el temperamento natural.",
        },
    },

    "rasi": {
        "ad": "Rasi",
        "baslik": "Rashi — Cercanía emocional y mental",
        "soru": "¿Qué tan parecidos son sus mundos interiores?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Mismo signo (7/7)",
                "aciklama": "La puntuación máxima del koota más pesado. Sus lenguajes emocionales "
                            "coinciden exactamente.",
                "ipucu": "Rasi aporta 7 puntos y es el centro de gravedad del Ashtakoot; junto "
                         "con Nadi suma 15 del total.",
            },
            "yuksek": {
                "baslik": "2.º/4.º amigo o 3.º/12.º (5/7)",
                "aciklama": "Signos separados por dos, tres o cuatro lugares. Muchas tradiciones "
                            "los cuentan también como muy compatibles.",
                "ipucu": "Aquí no se usa ni el elemento ni la calidad (cardinal/fixed/mutable); "
                         "solo cuenta la distancia entre signos.",
            },
            "orta": {
                "baslik": "5.º o 9.º (3/7)",
                "aciklama": "Una distancia intermedia. Los sentimientos están, la expresión no.",
                "ipucu": "Esta distancia no dificulta convivir; pide traducción.",
            },
            "dusuk": {
                "baslik": "6.º u 8.º (1/7)",
                "aciklama": "Cerca del eje de signos opuestos. Clásicamente es campo de fricción "
                            "y de transformación.",
                "ipucu": "Encontrarse en un eje transforma más que la mera distancia.",
            },
            "yok": {
                "baslik": "Oposición exacta (0/7)",
                "aciklama": "Los signos están exactamente opuestos (1-7, 2-8, 3-9, 4-10, 5-11, "
                            "6-12). Fuerte espejo emocional, pero sin puntos.",
                "ipucu": "Todos los esquemas kármicos muestran la máxima tensión en este eje.",
            },
        },
        "mod": {
            "es_sevgili": "Cercanía emocional y lenguaje de comunicación.",
            "ebeveyn_cocuk": "El vínculo emocional y la comprensión mutua entre padre e hijo.",
        },
    },

    "nadi": {
        "ad": "Nadi",
        "baslik": "Nadi — Conflicto de destino",
        "soru": "¿Colisionan sus caminos?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Nadi distinto (8/8)",
                "aciklama": "El nadi coincide. Son 8 de 36 y el ítem más alto del Ashtakoot.",
                "ipucu": "El nadi es triple (nadi_1, nadi_2, nadi_3). Caer en el mismo nadi se "
                         "lee como una colisión de destinos.",
            },
            "yok": {
                "baslik": "Mismo nadi, sin puntos (0/8)",
                "aciklama": "Ambos caen en el mismo nadi. Es el único ítem de puntuación cero y "
                            "también el único de ocho puntos del Ashtakoot.",
                "ipucu": "Comparado consigo mismo, uno siempre saca 0 en Nadi y un total de 28/36. "
                         "Como 36 es inalcanzable en la práctica, el techo real es 34 y las "
                         "uniones buenas se sitúan entre 30 y 34.",
            },
        },
        "mod": {
            "es_sevgili": "Dónde se cruzan dos líneas de vida. Clásicamente el mismo nadi se "
                          "lee como una relación tomada de una vida anterior.",
            "ebeveyn_cocuk": "Continuidad del destino entre generaciones; un nadi compartido "
                             "hace la transmisión fuerte pero limitante.",
        },
    },
}

TOPLAM_BANTLARI = {
    "cok_dusuk": {
        "baslik": "0-17 · Bajo",
        "aciklama": "Baja compatibilidad interna. Esto no significa que la relación o el vínculo "
                    "padre-hijo no exista; solo que los nakshatras lunares no coinciden en los "
                    "ocho criterios.",
        "ipucu": "Mire las otras capas: Nadi, Rasi y Gana llevan el peso.",
    },
    "dusuk": {
        "baslik": "18-24 · Por debajo de la media",
        "aciklama": "Compatibilidad parcial. Unos kootas son fuertes y otros débiles.",
        "ipucu": "Los kootas fuertes son aquello sobre lo que el vínculo se apoya de forma natural.",
    },
    "orta": {
        "baslik": "25-32 · Buena",
        "aciklama": "Compatibilidad sana, el rango de los textos clásicos para una buena "
                    "unión.",
        "ipucu": "La mayoría de las relaciones largas cae en esta banda.",
    },
    "yuksek": {
        "baslik": "33-36 · Muy alta",
        "aciklama": "Una combinación fuerte y poco frecuente. Los resultados por encima de 33 son "
                    "raros.",
        "ipucu": "En la práctica 36 no es alcanzable; el mismo nadi limita el total a 34.",
    },
}

KENDISI_NOTU = {
    "baslik": "Comparación consigo mismo",
    "aciklama": "Esta tabla compara a una persona con su propio nakshatra lunar. Es la "
                "referencia de coherencia interna y siempre devuelve 28/36.",
    "ipucu": "Varna, Vashya, Tara, Yoni, Graha Maitri, Gana y Rasi obtienen la máxima puntuación "
             "mientras Nadi obtiene cero, y por eso el resultado es 28 y no 36.",
}


def metin_getir(koota: str, puan: int, azami: int) -> dict:
    k = KOOTA_METIN.get(koota)
    if not k:
        return {"baslik": koota, "aciklama": "", "ipucu": ""}
    bant = bant_bul(puan, azami)
    m = k["bantlar"].get(bant)
    if m is None:
        sira = BANTLAR.index(bant)
        for adim in range(1, len(BANTLAR)):
            for hedef in (sira - adim, sira + adim):
                if 0 <= hedef < len(BANTLAR):
                    m = k["bantlar"].get(BANTLAR[hedef])
                    if m:
                        return dict(m, _bant=bant)
        return {"baslik": koota, "aciklama": "", "ipucu": ""}
    return dict(m, _bant=bant)


def mod_yorumu(koota: str, mod: str) -> str:
    k = KOOTA_METIN.get(koota)
    if not k:
        return ""
    return k.get("mod", {}).get(mod, "")


def toplam_metni(seviye: str) -> dict:
    return TOPLAM_BANTLARI.get(seviye, {"baslik": seviye, "aciklama": "", "ipucu": ""})


def tum_metinler(lang: str = "es") -> dict:
    return KOOTA_METIN


#: Evaluacion del Nadi Dosha. `ashtakoot_motoru.nadi_dosha_analizi` solo
#: produce codos independientes del idioma; este diccionario los traduce.
#:
#: NOTA: este bloque NO modifica la puntuacion del koota nadi. Informa por
#: separado de la presencia, gravedad y factores atenuantes o agravantes.
NADI_DOSHA_METIN = {
    "baslik": "Nadi Dosha",

    "seviye": {
        "yok": {
            "baslik": "Sin nadi dosha",
            "aciklama": "Las Lunas caen en grupos de nadi distintos. El koota "
                        "nadi puntua completo (8/8) y el dosha no llega a "
                        "plantearse.",
            "ipucu": "Este unico koota tiene el mayor peso en la tabla de 36 "
                     "puntos; puntuacion completa es poco habitual pero "
                     "posible.",
        },
        "belirgin": {
            "baslik": "Nadi dosha marcado",
            "aciklama": "Las Lunas comparten grupo de nadi y no se cumple "
                        "ninguna condicion atenuante. Nadi puntua 0/8.",
            "ipucu": "Esto por si solo no es un veredicto. Algunas tradiciones "
                     "lo dejan sin efecto; hacerlo bien exigiria una carta "
                     "natal completa.",
        },
        "hafif": {
            "baslik": "Nadi dosha leve",
            "aciklama": "Las Lunas comparten grupo de nadi, pero se cumple una "
                        "condicion atenuante.",
            "ipucu": "Una condicion atenuante reduce la fuerza del dosha; no "
                     "lo elimina.",
        },
        "hafifletilmis": {
            "baslik": "Nadi dosha atenuado",
            "aciklama": "Las Lunas comparten grupo de nadi, pero se cumplen "
                        "varias condiciones atenuantes.",
            "ipucu": "La puntuacion bruta sigue siendo 0/8; la atenuacion "
                     "enmarca la lectura, no suma puntos.",
        },
    },

    "kosullar": {
        "rasi_kendra": {
            "baslik": "Signos lunares en 2/12, 4/10 u 6/8",
            "detay": "El factor atenuante mas citado. El dosha se equilibra "
                     "cuando los signos lunares ocupan estos pares.",
        },
        "nadi_lord_ayni": {
            "baslik": "Mismo senor del nadi",
            "detay": "Si ambos lados comparten el planeta que rige su nadi, el "
                     "agente del dosha es comun.",
        },
        "ayni_gana": {
            "baslik": "Misma gana",
            "detay": "La misma clase de caracter debilita el dosha en contexto.",
        },
        "ayni_varna": {
            "baslik": "Mismo varna",
            "detay": "El mismo varna implica solapamiento en la capa de casta.",
        },
        "rasi_dusman": {
            "baslik": "Signos lunares en 3/11 o 5/9",
            "detay": "El dosha se considera mas grave en estos pares; una "
                     "condicion atenuante restablece el equilibrio.",
        },
    },

    "etiket": {
        "bhanga": "Atenuante (bhanga)",
        "taraka": "Agravante (taraka)",
    },

    "ozet_etiket": {
        "iliski": "Relacion de signos lunares",
        "pada": "Pada",
        "nadi": "Nadi",
        "lord": "Senor del nadi",
        "bhanga": "Atenuante",
        "taraka": "Agravante",
    },

    "kapsam_disi_baslik": "Subreglas clasicas no evaluadas",
    "kapsam_disi": {
        "nadi_lord_kendra": "Senores del nadi en 2/12, 4/10 u 6/8",
        "rasi_lord_kendra": "Senores de los signos lunares en 2/12, 4/10 u 6/8",
        "nadi_lord_dusthana": "Ambos senores del nadi en 6/8/12",
        "kendra_lagna": "Ascendente en 2/12, 4/10 u 6/8 respecto a ambas Lunas",
    },
    "kapsam_disi_notu": ("Este motor trabaja solo con la Luna; no calcula los "
                         "demas planetas ni el ascendente. Por eso no se "
                         "aplican las subreglas clasicas anteriores."),

    "puan_notu": ("El nadi dosha no cambia la puntuacion. La tabla de 36 puntos "
                  "es la aritmetica de una escuela; este bloque enmarca la "
                  "lectura sin alterarla."),
}
