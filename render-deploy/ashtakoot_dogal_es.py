# -*- coding: utf-8 -*-
"""Explicaciones en lenguaje natural, SIN JERGA, para Ashtakoot (ES).

Espejo de `ashtakoot_dogal_tr.py`: mismas 44 claves (koota, puntuación),
mismos tres ángulos (0 promesa / 1 relato / 2 símbolo) y la misma forma de
>=3 líneas.

Aquí no aparece ningún término sánscrito o jyotish; cada texto explica qué
significa la puntuación para la relación en la vida cotidiana.
"""

import random
from typing import Dict, List, Optional

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
        "Esta área señala: cómo reacciona cada uno a lo que ganáis y a lo que perdeis.",
    ],
    "vashya": [
        "Esta área muestra lo que promete: cuán fuerte es de verdad la "
        "atracción entre vosotros.",
        "Esta área explica: de dónde viene esa sensación de «algo se me "
        "movió al verle».",
        "Esta área simboliza: ese primer momento silencioso de atracción.",
        "Esta área señala: tomar la atracción por lo único que sujeta la relación.",
    ],
    "tara": [
        "Esta área muestra lo que promete: cuánto se solapan vuestros "
        "ritmos y cuándo se separan.",
        "Esta área explica: cómo afecta a la relación que uno se acueste "
        "tarde y el otro se levante temprano.",
        "Esta área simboliza: un hogar donde los relojes van a horas "
        "distintas.",
        "Esta área señala: un recuento de horas que se lleva debajo del mismo techo sin que nadie lo decida.",
    ],
    "yoni": [
        "Esta área muestra lo que promete: con qué facilidad vais a leeros "
        "por dentro.",
        "Esta área explica: cuánto aparecerá la pregunta de «¿qué está "
        "sintiendo ahora?».",
        "Esta área simboliza: cuánto de abierta está la puerta de la "
        "intimidad.",
        "Esta área señala: los errores silenciosos que cometeis creyendo que lo entendíais todo.",
    ],
    "graha_maitri": [
        "Esta área muestra lo que promete: cuán bien os leéis la mente el "
        "uno al otro.",
        "Esta área explica: por qué contáis la misma historia de forma "
        "distinta.",
        "Esta área simboliza: la comodidad de dos personas que hablan el "
        "mismo idioma.",
        "Esta área señala: callaros solo porque ya estáis de acuerdo.",
    ],
    "gana": [
        "Esta área muestra lo que promete: vuestra probabilidad de "
        "convivir sin agotaros.",
        "Esta área explica: por qué vuestras reacciones chocan a veces en "
        "el mismo momento.",
        "Esta área simboliza: dos ritmos distintos que se ajustan en un "
        "mismo hogar.",
        "Esta área señala: repetir «eso no lo hago yo» tal cual.",
    ],
    "rasi": [
        "Esta área muestra lo que promete: si podéis caminar hacia una meta "
        "compartida.",
        "Esta área explica: en qué áreas de la vida avanzáis al mismo "
        "ritmo.",
        "Esta área simboliza: dos personas leyendo el mismo mapa.",
        "Esta área señala: caminar hacia un objetivo compartido por motivos distintos.",
    ],
    "nadi": [
        "Esta área muestra lo que promete: la posibilidad de que la misma "
        "falta exista en los dos.",
        "Esta área explica: por qué buscáis siempre lo mismo uno en el "
        "otro.",
        "Esta área simboliza: dos personas en el mismo punto, "
        "completándose o chocando.",
        "Esta área señala: buscar dos veces la misma falta y quedar con las manos vacías.",
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



#: Cada (koota, puan) tiene un segundo cuerpo. `GOVDE` define el nivel y su
#: consecuencia; este texto monta una escena cotidiana concreta. Quien llama
#: elige uno de los dos al azar.
GOVDE_ALT: Dict[str, Dict[int, str]] = {

    # ------------------------------------------------------ valores / mirada social
    "varna": {
        0: ("Manejáis el dinero de forma opuesta.\n"
            "Uno lleva la cuenta y el otro gasta en el momento.\n"
            "Para administrar un mismo presupuesto, seguís reglas distintas."),
        1: ("Los días que os importan coinciden.\n"
            "Los dos tenéis un motivo para celebrar juntos un día cualquiera.\n"
            "Esos pequeños encuentros sostienen la relación sin que se vean."),
    },

    # ------------------------------------------------------------- atracción mutua
    "vashya": {
        0: ("Mostráis el interés de formas distintas.\n"
            "Uno te invita, el otro te llama durante una hora.\n"
            "Uno dice «quiero verte» y el otro «te he echado de menos»; ambos "
            "entran por la misma puerta."),
        1: ("Hay equilibrio entre cercanía y libertad.\n"
            "Cuando uno se acerca, el otro deja un poco de espacio; eso es "
            "respirar, no enfriarse.\n"
            "Cuanto más os acercáis, más fácil es recuperar esa distancia."),
        2: ("Tras separaros, uno de los dos busca al otro primero.\n"
            "Un hueco corto no acaba con el interés: hace el reencuentro más "
            "nítido.\n"
            "Esto es lo que mantiene en pie la relación."),
    },

    # ------------------------------------------------------------ tiempo / ritmo
    "tara": {
        0: ("Teneis los fines de semana montados de otra forma.\n"
            "Uno empieza temprano y el otro se mueve a última hora de la "
            "tarde.\n"
            "Averiguar a qué hora os veis lleva unas dos semanas."),
        1: ("También hay días que sí coinciden.\n"
            "Algunas semanas os levantáis a la misma hora y otras no os "
            "llegáis a ver.\n"
            "Elegir los buenos días vale más que quejarse de los "
            "desajustes."),
        2: ("Vuestros días empiezan a horas parecidas.\n"
            "Salir a trabajar, sentarse a comer, acostarse: todo queda "
            "cerca.\n"
            "Caidar en el mismo ritmo facilita las tareas compartidas."),
        3: ("Os cansáis a la misma hora.\n"
            "Sus horas libres coinciden casi siempre.\n"
            "Esta es la forma más fácil de compartir un día cansado."),
    },

    # ---------------------------------------------------------- mundo interior
    "yoni": {
        0: ("Los dos esperáis entenderos sin hablar.\n"
            "Leéis el estado del otro sin preguntar.\n"
            "Cuando la suposición falla, el otro se calla pensando que no le "
            "estabais escuchando."),
        1: ("Todavía hay temas reservados.\n"
            "A mitad de una conversación, los dos os retiráis.\n"
            "Abrir ese tema sin nombrarlo cansa menos que mantenerlo "
            "cerrado."),
        2: ("Leéis el estado de ánimo antes de que se note.\n"
            "Un buen día se oye; un día malo se ve en la postura.\n"
            "Esa lectura se convierte en una atención que nadie pidió."),
        3: ("Mostráis que habéis escuchado aunque no estéis de acuerdo.\n"
            "El otro se recompone una vez antes de hablar.\n"
            "Esperar aquí vale más que preguntar."),
        4: ("Queda muy poco sin compartir.\n"
            "Saber lo que el otro piensa sin preguntar es raro.\n"
            "Toda esa apertura también facilita las decisiones en común."),
    },

    # ----------------------------------------------------- mente / comunicación
    "graha_maitri": {
        0: ("Nombráis los sentimientos con palabras distintas.\n"
            "Uno dice «estoy triste» donde el otro dice «estoy cansado».\n"
            "Vivir el mismo momento con nombres distintos lleva a "
            "malentendidos."),
        1: ("La mayoría de las discusiones empiezan a destiempo.\n"
            "Uno tiene prisa y el otro está dispuesto a escuchar.\n"
            "La misma idea, dicha en mejor momento, cae de otra forma."),
        2: ("A menudo termináis la frase del otro.\n"
            "A uno le cuesta una palabra y el otro ya la tiene.\n"
            "Eso ahorra tiempo real cuando hay que decidir."),
        3: ("Llegáis a la misma conclusión por caminos distintos.\n"
            "Uno decide primero y el otro un momento después.\n"
            "Con caminos distintos y mismo destino, la discusión se acorta."),
        4: ("Os entendéis sin hablar.\n"
            "Cuando uno se calla, el otro sabe por qué.\n"
            "Lo único que queda sin decir puede ser justo lo importante."),
        5: ("Decidís casi en el mismo instante.\n"
            "Cuando uno dice «este», el otro ya está ahí.\n"
            "Incluso las decisiones difíciles se toman sin debate."),
    },

    # --------------------------------------------------------------- carácter
    "gana": {
        0: ("Decidís en unos dos segundos.\n"
            "Uno contesta sin pensar y el otro enumera tres opciones.\n"
            "La rapidez frente a la prudencia aparece en cada elección "
            "pequeña."),
        1: ("Ninguno espera que el otro sea como tú.\n"
            "No se le debe una explicación por ser distinto.\n"
            "Esa falta de expectativa mantiene la diferencia en algo "
            "inofensivo."),
        2: ("Os resulta gracioso casi lo mismo.\n"
            "El mismo momento divertido os llega a la vez.\n"
            "Las quejas pequeñas se cierran rápido con ese humor compartido."),
        3: ("Aguantáis juntos el ritmo del día a día.\n"
            "Cuando a uno se le acaba la energía, el otro carga con la "
            "mitad.\n"
            "Es apoyo dado sin decir una palabra."),
        4: ("Vuestros gustos y el apetito encajan.\n"
            "Misma comida, mismo programa, misma tarde.\n"
            "Las cosas cotidianas que hacéis juntos se multiplican."),
        5: ("El estado de uno mueve a la otra casi al instante.\n"
            "Cuando os enfadáis, os enfadáis los dos a la vez.\n"
            "Para una relación, enfadarse juntos y calmarse juntos es ideal."),
        6: ("Os turnáis sin llevar la cuenta.\n"
            "Uno da un paso al frente, el otro se retira; luego cambiáis.\n"
            "Así nadie se queda permanentemente en segundo plano."),
    },

    # -------------------------------------------------------- dirección común
    "rasi": {
        0: ("No estáis leyendo el mismo mapa.\n"
            "Uno señala el corto plazo y el otro el plan largo.\n"
            "Cuando cambia la dirección, alguien tiene que volver a "
            "preguntar adónde lleva el camino."),
        1: ("Hay una dirección en la que ya estáis de acuerdo.\n"
            "En eso llegáis a la misma decisión sin discutir.\n"
            "Es un terreno que no hace falta reabrir cada vez."),
        2: ("Uno frena y el otro espera.\n"
            "Uno tiene prisa y el otro va despacio para asegurarse.\n"
            "A veces quien espera acaba teniendo que apresurarse."),
        3: ("Consideráis importantes las mismas cosas por el mismo motivo.\n"
            "Los dos bebéis de experiencias parecidas.\n"
            "Ese motivo compartido mantiene un plan largo sobre el papel."),
        4: ("Vuestras prioridades se respaldan.\n"
            "Cuando uno dice «esto primero», el otro dice «sí».\n"
            "Ese acuerdo es lo que marca la velocidad de la decisión."),
        5: ("Llegáis al mismo sitio por caminos distintos.\n"
            "Mismo destino, carretera diferente.\n"
            "Si uno se sale del camino, el otro tiene que buscar otro."),
        6: ("Entendéis el plan sin explicarlo.\n"
            "No hace falta hablarlo, porque el mañana ya está claro.\n"
            "Un plan así aguantaría también con una tercera persona."),
        7: ("Decidís juntos en lugar de por separado.\n"
            "Dejáis vuestra preferencia en un lado y preguntáis primero la "
            "del otro.\n"
            "Eso facilita la parte más difícil de diseñar una vida común."),
    },

    # ------------------------------------------------ impulso interior / fricción
    "nadi": {
        0: ("Cerráis la misma falta de dos maneras distintas.\n"
            "Uno olvidando y el otro trabajando.\n"
            "El mismo vacío, método distinto."),
        1: ("Queréis lo mismo al mismo tiempo.\n"
            "Cuando a uno le apetece, al otro también.\n"
            "Cualquiera de los dos sabe explicar por qué."),
        2: ("No estáis mirando el mismo punto.\n"
            "Los dos caéis en el mismo error sin verlo.\n"
            "Uno tapa el punto ciego del otro."),
        3: ("La ausencia de esa falta os molesta a los dos a la vez.\n"
            "Os movéis cuando el otro está bien.\n"
            "Eso os evita quedar a solas con ello."),
        4: ("El objetivo es el mismo, el camino no.\n"
            "Uno tiene prisa y el otro espera su turno.\n"
            "Quien espera acaba frenando a quien se precipitó."),
        5: ("Hay dos deseos opuestos sobre lo mismo.\n"
            "Uno quiere más juntos y el otro más espacio.\n"
            "Hablarlo cansa a los dos muy pronto."),
        6: ("Llegáis al mismo sitio dos veces.\n"
            "Uno busca y el otro no lo encuentra; luego os cambiáis.\n"
            "El bucle se ve antes de poder romperlo."),
        7: ("La inquietud de una encuentra su reflejo exacto en la otra.\n"
            "Ninguna se calma hasta que la otra se calma.\n"
            "No podéis empezar la conversación hasta que os calméis juntos."),
        8: ("Dais la misma lección dos veces.\n"
            "Cuando uno se rompe, el otro también.\n"
            "La segunda vuelta dura menos que la primera."),
    },
}


#: Cuatro ángulos: 0 promesa, 1 explica, 2 simboliza, 3 señala.
ACI_SAYISI = 4


def govde_varyantlari(kod: str, puan: int) -> List[str]:
    """Todos los cuerpos disponibles para `kod`/`puan`.

    `GOVDE` es siempre el primero; `GOVDE_ALT` añade el segundo cuando
    existe, de modo que las kootas con un solo cuerpo siguen funcionando.
    """
    ilk = GOVDE.get(kod, {}).get(puan)
    if ilk is None:
        return []
    liste = [ilk]
    ikinci = GOVDE_ALT.get(kod, {}).get(puan)
    if ikinci is not None:
        liste.append(ikinci)
    return liste


def dogal_metin(kod: str, puan: int, aci: int,
                govde_index: Optional[int] = None) -> str:
    """Texto sin jerga para `kod` en `puan` desde el ángulo `aci`.

    `aci`: 0 promesa, 1 explica, 2 simboliza, 3 señala.
    `govde_index`: variante del cuerpo; `None` elige una al azar. Con cuatro
    ángulos y dos cuerpos, un puntaje da ocho textos posibles.
    """
    if GOVDE.get(kod, {}).get(puan) is None:
        return ""
    if govde_index is None:
        govde_index = random.randrange(len(govde_varyantlari(kod, puan)))
    return "%s\n%s" % (ACILAR.get(kod, [""] * ACI_SAYISI)[aci % ACI_SAYISI],
                       govde_varyantlari(kod, puan)[govde_index])


def mevcut(kod: str, puan: int) -> bool:
    return puan in GOVDE.get(kod, {})


#: Lectura general del total, en lenguaje claro.
#: El máximo es 36, pero los totales alcanzables sólo van de 20 a 34, así que
#: las bandas siguen ese rango medido: `cok_dusuk` = 20-23 (Relación débil),
#: `dusuk` = 26-27 (Media), `orta` = 28-29 (Ideal),
#: `yuksek` = 33-34 (Fuerte).
TOPLAM: Dict[str, Dict[str, str]] = {
    "cok_dusuk": {
        "baslik": "Relación débil",
        "aciklama": ("Rango 20-23. Hay mucho que recorrer y el hábito de estar "
                    "juntos aún no está asentado.\n"
                    "Eso no significa que la puerta esté cerrada; solo "
                    "muestra que el encaje actual es bajo.\n"
                    "Lo que más ayuda es el esfuerzo por entender a la otra "
                    "persona."),
        "ipucu": ("Pasos pequeños y constantes llevan más lejos que un "
                  "comienzo espectacular."),
    },
    "dusuk": {
        "baslik": "Relación media",
        "aciklama": ("Rango 26-27. Hay áreas en las que la relación se apoya "
                    "y funciona, y otras que todavía no encajan.\n"
                    "Vuestras fortalezas la sostienen; las débiles pesan "
                    "más si nunca las trabajáis juntos.\n"
                    "No es malo, pero pide un trabajo consciente."),
        "ipucu": ("Empezad por donde sois más fuertes; el resto llega con "
                  "el tiempo."),
    },
    "orta": {
        "baslik": "Relación ideal",
        "aciklama": ("Rango 28-29. El día a día no os desgasta, y la mayoría "
                    "de lo que construís juntos va asentando.\n"
                    "Hay situaciones difíciles, pero no os detienen; además "
                    "ambos sabéis dónde cuesta.\n"
                    "La relación se apoya en un suelo firme y queda abierta "
                    "a crecer."),
        "ipucu": ("Un suelo firme no significa que todo se quede igual; "
                  "fijate en lo que construís encima."),
    },
    "yuksek": {
        "baslik": "Relación fuerte",
        "aciklama": ("Rango 33-34. Vuestro encaje roza la totalidad.\n"
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
