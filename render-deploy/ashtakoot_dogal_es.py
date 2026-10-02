# -*- coding: utf-8 -*-
"""Explicaciones en lenguaje natural, SIN JERGA, para Ashtakoot (ES).

Espejo de `ashtakoot_dogal_tr.py`: mismas 44 claves (koota, puntuación),
mismos tres ángulos (0 promesa / 1 relato / 2 símbolo) y la misma forma de
>=3 líneas.

Aquí no aparece ningún término sánscrito o jyotish; cada texto explica qué
significa la puntuación para la relación en la vida cotidiana.
"""

from typing import Dict, List

KOOTA_BASLIK: Dict[str, str] = {
    "varna": "Valores y mirada social",
    "vashya": "Atracción mutua",
    "tara": "Momentos y ritmo",
    "yoni": "Mundo interior e intimidad",
    "graha_maitri": "Pensamiento y comunicación",
    "gana": "Carácter y vida diaria",
    "rasi": "Dirección compartida",
    "nadi": "Impulso interior y fricción",
}

ACILAR: Dict[str, List[str]] = {
    "varna": [
        "Esta área muestra lo que promete: si vais a chocar por valores "
        "mientras construís una vida juntos.",
        "Esta área explica: si surgirán en el día a día las "
        "discusiones sobre «quién tiene razón».",
        "Esta área simboliza: si coinciden de verdad las cosas que ambos "
        "consideráis importantes.",
    ],
    "vashya": [
        "Esta área muestra lo que promete: cuán fuerte es de verdad la "
        "atracción entre vosotros.",
        "Esta área explica: de dónde viene esa sensación de «algo se me "
        "movió al verle».",
        "Esta área simboliza: ese primer momento silencioso de atracción.",
    ],
    "tara": [
        "Esta área muestra lo que promete: cuánto se solapan vuestros "
        "ritmos y cuándo se separan.",
        "Esta área explica: cómo afecta a la relación que uno se acueste "
        "tarde y el otro se levante temprano.",
        "Esta área simboliza: un hogar donde los relojes van a horas "
        "distintas.",
    ],
    "yoni": [
        "Esta área muestra lo que promete: con qué facilidad vais a leeros "
        "por dentro.",
        "Esta área explica: cuánto aparecerá la pregunta de «¿qué está "
        "sintiendo ahora?».",
        "Esta área simboliza: cuánto de abierta está la puerta de la "
        "intimidad.",
    ],
    "graha_maitri": [
        "Esta área muestra lo que promete: cuán bien os leéis la mente el "
        "uno al otro.",
        "Esta área explica: por qué contáis la misma historia de forma "
        "distinta.",
        "Esta área simboliza: la comodidad de dos personas que hablan el "
        "mismo idioma.",
    ],
    "gana": [
        "Esta área muestra lo que promete: vuestra probabilidad de "
        "convivir sin agotaros.",
        "Esta área explica: por qué vuestras reacciones chocan a veces en "
        "el mismo momento.",
        "Esta área simboliza: dos ritmos distintos que se ajustan en un "
        "mismo hogar.",
    ],
    "rasi": [
        "Esta área muestra lo que promete: si podéis caminar hacia una meta "
        "compartida.",
        "Esta área explica: en qué áreas de la vida avanzáis al mismo "
        "ritmo.",
        "Esta área simboliza: dos personas leyendo el mismo mapa.",
    ],
    "nadi": [
        "Esta área muestra lo que promete: la posibilidad de que la misma "
        "falta exista en los dos.",
        "Esta área explica: por qué buscáis siempre lo mismo uno en el "
        "otro.",
        "Esta área simboliza: dos personas en el mismo punto, "
        "completándose o chocando.",
    ],
}

GOVDE: Dict[str, Dict[int, str]] = {

    # ------------------------------------------------------ valores / mirada social
    "varna": {
        0: ("Vuestros mundos de valores se diferencian claramente.\n"
            "La familia, el dinero y la autoridad pueden generar "
            "expectativas distintas.\n"
            "No implica conflicto, pero puede repetir la misma discusión por "
            "cosas pequeñas."),
        1: ("Vuestros mundos de valores son muy próximos.\n"
            "En familia, dinero y responsabilidad os cuesta poco coincidir.\n"
            "Ese acuerdo es el suelo tranquilo y cómodo de vuestra vida "
            "diaria."),
    },

    # ------------------------------------------------------------ atracción
    "vashya": {
        0: ("Lo que tenéis es más costumbre que atracción.\n"
            "Os conocéis, pero la sensación de «algo se me movió al "
            "verte» es débil.\n"
            "No es un defecto: la confianza que se construye viviendo "
            "puede convertirse en chispa."),
        1: ("La atracción es equilibrada.\n"
            "El interés tiene respuesta; ni demasiado ni demasiado poco.\n"
            "Ese equilibrio es lo que hace que la relación sea sostenible."),
        2: ("La atracción es fuerte y mutua.\n"
            "En el momento en que os percebéis, ambos decís sí.\n"
            "Alimenta directamente la relación; aunque haya dificultades, "
            "volver el uno hacia el otro es fácil."),
    },

    # ---------------------------------------------------------- momentos / ritmo
    "tara": {
        0: ("Vuestros ritmos diarios van en direcciones opuestas.\n"
            "Uno es de mañana y planificado; el otro vive más cerca de la "
            "noche y la sorpresa.\n"
            "Vivir a horas distintas bajo el mismo techo puede importar más "
            "que las diferencias culturales."),
        1: ("Vuestros ritmos diarios coinciden en parte.\n"
            "Hay etapas casi idénticas y otras que se separan por "
            "completo.\n"
            "Esto no debilita la relación; solo crea un desajuste por "
            "temporadas."),
        2: ("Vuestros ritmos diarios coinciden en gran medida.\n"
            "Las horas que compartís se parecen.\n"
            "Eso da un suelo firme para las tareas comunes y el ocio "
            "conjunto."),
        3: ("Vuestros ritmos diarios son casi idénticos.\n"
            "Si uno se levanta tarde, el otro también; si uno está "
            "ocupado, el otro también.\n"
            "Es una de las áreas más difíciles de romper y también la que "
            "más tiempo os ahorra."),
    },

    # ------------------------------------------------------------ mundo interior
    "yoni": {
        0: ("Vuestros mundos interiores están cerrados entre sí.\n"
            "Cuesta adivinar qué siente el otro, y al otro le cuesta lo "
            "mismo contigo.\n"
            "Nombrar lo que se siente, en vez de adivinarlo, es lo que "
            "acorta esta distancia."),
        1: ("Vuestros mundos interiores están parcialmente abiertos.\n"
            "Entendéis muchas cosas, pero algunos sentimientos siguen "
            "ocultos.\n"
            "Significa que las capas más profundas aún no se han abierto, "
            "no que la intimidad sea cero."),
        2: ("Vuestros mundos interiores están moderadamente abiertos.\n"
            "Casi siempre leéis la alegría y la tristeza del otro.\n"
            "Lo que queda en la sombra suele venir del pasado no dicho, no "
            "del presente."),
        3: ("Os leéis con facilidad por dentro.\n"
            "Mucho se entiende sin palabras; la tristeza suele notarse "
            "de un vistazo.\n"
            "La otra cara es la expectativa: si lees tan bien al otro, debes "
            "ofrecer la misma apertura."),
        4: ("Vuestros mundos interiores son casi transparentes.\n"
            "Casi todo se entiende sin decirlo, y una necesidad de uno "
            "encuentra respuesta en el otro.\n"
            "Este nivel de intimidad es raro y es la mayor fuente de "
            "confianza de la relación."),
    },

    # ------------------------------------------------- pensamiento / diálogo
    "graha_maitri": {
        0: ("Vuestras formas de pensar son casi opuestas.\n"
            "Vosotros sois más fríos y analíticos; el otro, más emocional e "
            "intuitivo.\n"
            "A primera vista parece un conflicto, pero en realidad habláis "
            "idiomas distintos."),
        1: ("Pensáis casi igual, pero os separáis en algunos puntos "
            "básicos.\n"
            "La conversación diaria fluye; en las discusiones profundas "
            "aparecen límites claros.\n"
            "Leer esa diferencia como algo complementario, y no como un "
            "obstáculo, refuerza esta área."),
        2: ("Vuestra forma básica de pensar coincide.\n"
            "En la mayoría de las discusiones llegáis a la misma "
            "conclusión.\n"
            "Quedan diferencias finas, pero de las que se resolvieron "
            "hablando."),
        3: ("Vuestro pensamiento es cercano y complementario.\n"
            "Uno se pierde el detalle que el otro capta, y eso rinde en las "
            "decisiones comunes.\n"
            "Entenderos demasiado bien también puede aplazar la conversación "
            "honesta."),
        4: ("Vuestro pensamiento está casi entrelazado.\n"
            "Llegáis a la misma conclusión y completáis las ideas del "
            "otro.\n"
            "Una advertencia: coincidir no debe convertirse en un sitio "
            "donde esconder el desacuerdo."),
        5: ("Vuestro pensamiento está en su punto máximo.\n"
            "Os entendéis antes de hablar; casi oís lo que el otro quiere "
            "decir.\n"
            "Las decisiones compartidas y la dirección común crecen de "
            "esta comunión."),
    },

    # ---------------------------------------------------------------- carácter
    "gana": {
        0: ("Vuestros caracteres son muy distintos.\n"
            "Uno es prudente y lento; el otro, audaz y rápido.\n"
            "Aparece como un «date prisa» y un «espera un momento» que se "
            "repite una y otra vez."),
        1: ("Diferís en carácter, pero dentro del respeto mutuo.\n"
            "Uno puede ser más extrovertido y el otro más "
            "introvertido.\n"
            "Esa diferencia enriquece el día a día; el problema aparece "
            "cuando surge «tú no lo haces a mi manera»."),
        2: ("Vuestro ajuste de carácter es moderado.\n"
            "Os reís de lo mismo, pero reaccionáis de forma distinta.\n"
            "Las pequeñas quejas suelen resolverse antes de crecer."),
        3: ("Vuestros caracteres son próximos sin ser idénticos.\n"
            "Os reís del mismo momento divertido, aunque uno se mueva más "
            "rápido.\n"
            "Ese es un ajuste relajado y cómodo."),
        4: ("Vuestros caracteres encajan bien.\n"
            "Las reacciones, la energía y las expectativas coinciden.\n"
            "Soiséficientes juntos y el ritmo diario no desgasta a ninguno."),
        5: ("Vuestros caracteres se solapan con fuerza.\n"
            "Las reacciones y las expectativas son casi idénticas.\n"
            "La otra cara es que si uno cambia, se espera que el otro "
            "cambie también."),
        6: ("Vuestros caracteres os completáis.\n"
            "La energía de uno la equilibra la calma del otro.\n"
            "Ese es el mejor ajuste diario y también os da la fuerza para "
            "hacer más juntos."),
    },

    # --------------------------------------------------------- dirección común
    "rasi": {
        0: ("No trabajáis de forma natural en la misma área.\n"
            "Uno define la relación desde lo emocional y el otro desde la "
            "acción.\n"
            "Leer mapas distintos difumina la dirección cuando avanzáis "
            "juntos."),
        1: ("Coincidís en unas áreas y en otras no.\n"
            "Los temas con objetivo común funcionan; los dispersos ralentizan.\n"
            "Elegir cuál resolver primero da a la relación una dirección "
            "clara."),
        2: ("Vuestra dirección se solapa en parte.\n"
            "En unos temas cogéis el mismo ritmo y en otros uno va por "
            "delante.\n"
            "Pequeños ajustes regulares lo mantienen equilibrado cuando "
            "trabajáis juntos."),
        3: ("Vuestra dirección coincide en gran medida.\n"
            "Los dos veis las mismas razones para que algo importe.\n"
            "Eso es un suelo firme para las decisiones comunes y los "
            "planes a largo plazo."),
        4: ("Vuestra dirección está alineada.\n"
            "Las prioridades os pasan por la mente en el mismo orden.\n"
            "Os acabóis en el mismo lado de las decisiones importantes de "
            "la vida."),
        5: ("Vuestra dirección encaja con fuerza.\n"
            "Valoráis lo mismo de la misma manera.\n"
            "Moveros juntos no cuesta nada; de hecho, aporta energía."),
        6: ("Vuestra dirección es casi idéntica.\n"
            "Entendéis lo que el otro quiere sin que os lo diga.\n"
            "Caminar hacia una meta juntos se siente fácil, como apoyarse "
            "el uno en el otro."),
        7: ("Vuestra dirección coincide por completo.\n"
            "Lo que uno prioriza, el otro también.\n"
            "Es una unidad poco común al diseñar una vida en común; "
            "camináis siempre por el mismo camino."),
    },

    # -------------------------------------------- impulso interior / fricción
    "nadi": {
        0: ("Vuestros impulsos interiores se completan.\n"
            "Uno cubre un vacío mientras el otro lo cubre desde otro "
            "ángulo.\n"
            "La fuerza de la relación viene exactamente de esa "
            "complementariedad."),
        1: ("Vuestros impulsos interiores se solapan mucho.\n"
            "Deseáis lo mismo en momentos distintos, pero con el mismo "
            "instinto.\n"
            "Eso crea una unión fuerte en torno a objetivos "
            "compartidos."),
        2: ("Vuestros impulsos interiores apuntan al mismo lado.\n"
            "Los dos intuís la misma carencia.\n"
            "Es una combinación con alta probabilidad de completarse."),
        3: ("Vuestros impulsos interiores son próximos.\n"
            "Necesidades similares producen reacciones similares en "
            "vosotros.\n"
            "Es un ajuste que hace fácil compartir."),
        4: ("Vuestros impulsos interiores coinciden en gran medida, aunque "
            "cambian los matices.\n"
            "PersLigáis lo mismo de formas distintas.\n"
            "Avanzar juntos puede producir pequeños roces."),
        5: ("Vuestros impulsos interiores chocan en algunos puntos.\n"
            "Podéis querer cosas distintas de la misma situación.\n"
            "Es el área que más merece hablar; decirlo en vez de "
            "esconderlo la mantiene manejable."),
        6: ("Vuestros impulsos interiores chocan con claridad.\n"
            "Os alimentáis de necesidades similares, pero tiráis hacia "
            "lugares distintos.\n"
            "Puede drenar la relación, aunque la conciencia lo hace "
            "orientable."),
        7: ("Vuestros impulsos interiores casi colisionan.\n"
            "Buscáis la misma carencia en el otro y los dos vais al mismo "
            "sitio.\n"
            "Es el área más difícil, pero no es un choque: son dos "
            "personas que quieren lo mismo."),
        8: ("Vuestros impulsos interiores son idénticos.\n"
            "Reaccionáis igual ante la misma carencia y deseáis lo "
            "mismo.\n"
            "Genera fricción interna, pero no significa el final: si "
            "queréis lo mismo dos veces, buscarlo juntos funciona."),
    },
}


def dogal_metin(kod: str, puan: int, aci: int) -> str:
    """Devuelve el texto sin jerga para `kod`, `puan` y ángulo `aci`."""
    govde = GOVDE.get(kod, {}).get(puan)
    if govde is None:
        return ""
    return "%s\n%s" % (ACILAR.get(kod, [""] * 3)[aci % 3], govde)


def mevcut(kod: str, puan: int) -> bool:
    return puan in GOVDE.get(kod, {})


#: Total (0-36) en lenguaje claro. `cok_dusuk` = 0-17, `dusuk` = 18-24,
#: `orta` = 25-32, `yuksek` = 33-36.
TOPLAM: Dict[str, Dict[str, str]] = {
    "cok_dusuk": {
        "baslik": "Un comienzo débil",
        "aciklama": ("Hay mucho que recorrer y el hábito de estar juntos "
                    "aún no está asentado.\n"
                    "Eso no significa que la puerta esté cerrada; solo "
                    "muestra que el encaje actual es bajo.\n"
                    "Lo que más ayuda es el esfuerzo por entender a la otra "
                    "persona."),
        "ipucu": ("Pasos pequeños y constantes llevan más lejos que un "
                  "comienzo espectacular."),
    },
    "dusuk": {
        "baslik": "Algunas áreas encajan bien",
        "aciklama": ("Hay áreas en las que la relación se apoya y funciona, "
                    "y otras que todavía no encajan.\n"
                    "Vuestras fortalezas la sostienen; las débiles pesan "
                    "más si nunca las trabajáis juntos.\n"
                    "No es malo, pero pide un trabajo consciente."),
        "ipucu": ("Empezad por donde sois más fuertes; el resto llega con "
                  "el tiempo."),
    },
    "orta": {
        "baslik": "Un encaje sólido",
        "aciklama": ("La mayoría de las relaciones largas cae en este "
                    "intervalo.\n"
                    "El día a día no os desgasta; hay situaciones difíciles, "
                    "pero no os detienen.\n"
                    "La relación se apoya en un suelo firme y queda abierta "
                    "a crecer."),
        "ipucu": ("Un suelo firme no significa que todo se quede igual; "
                  "fijate en lo que construís encima."),
    },
    "yuksek": {
        "baslik": "Un encaje fuerte",
        "aciklama": ("Vuestro encaje roza la totalidad.\n"
                    "Habláis el mismo idioma a diario, os entendéis y os "
                    "importan las mismas cosas.\n"
                    "Estas combinaciones son raras, pero una puntuación alta "
                    "no significa que la relación dure para siempre."),
        "ipucu": ("Un encaje fuerte facilita la comunicación; aun así no "
                  "sustituye la conversación sincera y profunda."),
    },
}


def toplam_metin(seviye: str) -> Dict[str, str]:
    return dict(TOPLAM.get(seviye, {}))
