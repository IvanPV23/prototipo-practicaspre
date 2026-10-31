"""Construye la versión 2 del documento de la Parte I a partir del original, sin tocar 01_alcance/.

Aplica las correcciones argumentales que salieron de las fases 1 a 3 de /practicaspre y agrega la sección 12
(diseño del modelo y arquitectura) que pide la plantilla del examen parcial. Edita el XML del .docx original
para conservar sus estilos (títulos, listas, tablas y pie de página).

Uso (desde la raíz del proyecto):
    .venv/Scripts/python.exe 02_documentacion/04_entregable_parcial/generar_figuras.py
    python 02_documentacion/04_entregable_parcial/construir_docx.py <carpeta_trabajo>   (requiere lxml y Pillow)
"""

from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

from lxml import etree
from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
ORIGINAL = RAIZ / "01_alcance" / "Parte_I_Proyecto_SJM.docx"
SALIDA = AQUI / "Parte_I_Proyecto_SJM_v2.docx"
FIGURAS = AQUI / "figuras"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
}
W = "{%s}" % NS["w"]
ANCHO_TEXTO_DXA = 9026
EMU_POR_DXA = 635
DECL = " ".join(f'xmlns:{k}="{v}"' for k, v in NS.items())


# --------------------------------------------------------------------------- construcción de XML
def _xml(fragmento: str) -> etree._Element:
    return etree.fromstring(f"<raiz {DECL}>{fragmento}</raiz>")[0]


def _esc(texto: str) -> str:
    # Espacio de miles no separable, como en el original ("2 592"), para que Word no corte el número
    texto = re.sub(r"(?<=\d) (?=\d{3}(?!\d))", "\u00a0", texto)
    texto = re.sub(r"(?<=\d) %", "\u00a0%", texto)
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _runs(texto: str, tam: int | None = None, cursiva_base: bool = False) -> str:
    """Texto con **negrita** y *cursiva* a runs de Word."""
    salida = []
    for trozo in re.split(r"(\*\*.+?\*\*|\*.+?\*)", texto):
        if not trozo:
            continue
        negrita = trozo.startswith("**")
        cursiva = cursiva_base or (trozo.startswith("*") and not negrita)
        limpio = trozo.strip("*") if (negrita or cursiva and not cursiva_base) else trozo
        rpr = ""
        if negrita:
            rpr += "<w:b/><w:bCs/>"
        if cursiva:
            rpr += "<w:i/><w:iCs/>"
        if tam:
            rpr += f'<w:sz w:val="{tam}"/><w:szCs w:val="{tam}"/>'
        rpr = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
        salida.append(f'<w:r>{rpr}<w:t xml:space="preserve">{_esc(limpio)}</w:t></w:r>')
    return "".join(salida)


def parrafo(texto: str) -> etree._Element:
    return _xml(f'<w:p><w:pPr><w:spacing w:after="120" w:line="360"/><w:jc w:val="both"/></w:pPr>{_runs(texto)}</w:p>')


def vineta(texto: str) -> etree._Element:
    return _xml(
        '<w:p><w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr>'
        f'<w:spacing w:after="60" w:line="336"/><w:jc w:val="both"/></w:pPr>{_runs(texto)}</w:p>'
    )


def titulo(texto: str, nivel: int) -> etree._Element:
    return _xml(f'<w:p><w:pPr><w:pStyle w:val="Heading{nivel}"/></w:pPr>{_runs(texto)}</w:p>')


def leyenda(texto: str) -> etree._Element:
    return _xml(
        '<w:p><w:pPr><w:keepNext/><w:spacing w:after="80" w:before="160"/></w:pPr>'
        f'<w:r><w:rPr><w:b/><w:bCs/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr><w:t xml:space="preserve">{_esc(texto)}</w:t></w:r></w:p>'
    )


def nota(texto: str) -> etree._Element:
    return _xml(f'<w:p><w:pPr><w:spacing w:after="200" w:before="60"/></w:pPr>{_runs(texto, tam=20, cursiva_base=True)}</w:p>')


def referencia(texto: str) -> etree._Element:
    return _xml(
        '<w:p><w:pPr><w:spacing w:after="120" w:line="300"/><w:ind w:left="720" w:hanging="720"/></w:pPr>'
        f"{_runs(texto)}</w:p>"
    )


def _celda(texto: str, ancho: int, alineacion: str, cabecera: bool) -> str:
    borde = "".join(f'<w:{b} w:val="single" w:color="999999" w:sz="4"/>' for b in ("top", "left", "bottom", "right"))
    sombreado = '<w:shd w:fill="D9E2F3" w:color="auto" w:val="clear"/>' if cabecera else ""
    margen = "".join(f'<w:{b} w:type="dxa" w:w="{v}"/>' for b, v in (("top", 60), ("left", 100), ("bottom", 60), ("right", 100)))
    rpr = "<w:b/><w:bCs/>" if cabecera else '<w:b w:val="false"/><w:bCs w:val="false"/>'
    return (
        f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{ancho}"/><w:tcBorders>{borde}</w:tcBorders>{sombreado}'
        f'<w:tcMar>{margen}</w:tcMar></w:tcPr><w:p><w:pPr><w:keepNext/><w:jc w:val="{alineacion}"/></w:pPr>'
        f'<w:r><w:rPr>{rpr}<w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr><w:t xml:space="preserve">{_esc(texto)}</w:t></w:r>'
        "</w:p></w:tc>"
    )


def tabla(cabecera: list[str], filas: list[list[str]], anchos: list[int], alineaciones: list[str]) -> etree._Element:
    assert sum(anchos) == ANCHO_TEXTO_DXA, sum(anchos)
    bordes = "".join(f'<w:{b} w:val="single" w:color="auto" w:sz="4"/>' for b in ("top", "left", "bottom", "right", "insideH", "insideV"))
    grid = "".join(f'<w:gridCol w:w="{a}"/>' for a in anchos)
    cab = "".join(_celda(t, a, al, True) for t, a, al in zip(cabecera, anchos, alineaciones))
    cuerpo = "".join(
        "<w:tr>" + "".join(_celda(t, a, al, False) for t, a, al in zip(fila, anchos, alineaciones)) + "</w:tr>"
        for fila in filas
    )
    return _xml(
        f'<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="{ANCHO_TEXTO_DXA}"/><w:tblBorders>{bordes}</w:tblBorders></w:tblPr>'
        f'<w:tblGrid>{grid}</w:tblGrid><w:tr><w:trPr><w:tblHeader/></w:trPr>{cab}</w:tr>{cuerpo}</w:tbl>'
    )


class Imagenes:
    """Copia las imágenes a word/media y registra sus relaciones."""

    def __init__(self, trabajo: Path) -> None:
        self.trabajo = trabajo
        self.rels_ruta = trabajo / "word" / "_rels" / "document.xml.rels"
        self.rels = etree.parse(str(self.rels_ruta))
        self.siguiente = 100
        (trabajo / "word" / "media").mkdir(exist_ok=True)

    def figura(self, ruta: Path, descripcion: str, fraccion_ancho: float = 1.0) -> etree._Element:
        rid, n = f"rId{self.siguiente}", self.siguiente
        self.siguiente += 1
        destino = f"media/{ruta.name}"
        shutil.copy(ruta, self.trabajo / "word" / destino)
        etree.SubElement(self.rels.getroot(), "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship",
                         Id=rid, Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                         Target=destino)
        with Image.open(ruta) as im:
            ancho_px, alto_px = im.size
        cx = int(ANCHO_TEXTO_DXA * EMU_POR_DXA * fraccion_ancho)
        cy = int(cx * alto_px / ancho_px)
        return _xml(
            '<w:p><w:pPr><w:keepNext/><w:spacing w:after="0" w:before="60"/><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
            f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
            '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
            f'<wp:docPr id="{n}" name="Figura {n}" descr="{_esc(descripcion)}"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
            f'<pic:nvPicPr><pic:cNvPr id="{n}" name="{ruta.name}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            "</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>"
        )

    def guardar(self) -> None:
        self.rels.write(str(self.rels_ruta), xml_declaration=True, encoding="UTF-8", standalone=True)


# --------------------------------------------------------------------------- edición del documento
class Documento:
    def __init__(self, trabajo: Path) -> None:
        self.ruta = trabajo / "word" / "document.xml"
        self.arbol = etree.parse(str(self.ruta))
        self.cuerpo = self.arbol.getroot().find(W + "body")

    @staticmethod
    def texto(el: etree._Element) -> str:
        return "".join(t.text or "" for t in el.iter(W + "t"))

    def buscar(self, prefijo: str) -> etree._Element:
        hallados = [el for el in self.cuerpo if el.tag == W + "p" and self.texto(el).startswith(prefijo)]
        if len(hallados) != 1:
            raise ValueError(f"Se esperaba 1 párrafo que empiece por {prefijo!r}; hay {len(hallados)}")
        return hallados[0]

    def reescribir(self, prefijo: str, nuevo: str) -> etree._Element:
        """Sustituye el texto del párrafo y conserva su formato de párrafo (estilo, lista, sangrías)."""
        p = self.buscar(prefijo)
        for r in p.findall(W + "r"):
            p.remove(r)
        for r in _xml(f"<w:p>{_runs(nuevo)}</w:p>"):
            p.append(r)
        return p

    @staticmethod
    def insertar_despues(ancla: etree._Element, *elementos: etree._Element) -> etree._Element:
        for el in elementos:
            ancla.addnext(el)
            ancla = el
        return ancla

    def guardar(self) -> None:
        self.arbol.write(str(self.ruta), xml_declaration=True, encoding="UTF-8", standalone=True)


def recortar(origen: str, destino: str, caja: tuple[int, int, int, int]) -> Path:
    """Quita el margen vacío superior (y la barra lateral si se pide) de las capturas de la app."""
    with Image.open(FIGURAS / origen) as im:
        x0, y0, x1, y1 = caja
        im.crop((x0, y0, x1 or im.width, y1 or im.height)).save(FIGURAS / destino)
    return FIGURAS / destino


# --------------------------------------------------------------------------- contenido
def aplicar(doc: Documento, img: Imagenes) -> None:
    # 2.1 Situación de los datos
    doc.reescribir(
        "El extracto del CCO disponible",
        "El extracto del CCO disponible para este trabajo contiene **2 592 registros** entre el **16 de mayo y el "
        "10 de junio de 2026** (26 días; fecha de corte: 10 de junio de 2026). Todos los registros tienen latitud y "
        "longitud, y se distribuyen en tres turnos (mañana, tarde y noche) y en cuatro sectores del distrito. En "
        "promedio se registran cerca de 100 incidencias por día. Es la única versión publicada del conjunto: aunque "
        "su ficha anuncia una actualización mensual, al 31 de octubre de 2026 la Plataforma Nacional de Datos "
        "Abiertos solo ofrece el corte del 10 de junio. Se trabaja con el archivo CSV oficial, porque la versión en "
        "hoja de cálculo altera 67 identificadores al guardarlos como números (pierde ceros iniciales o los "
        "convierte en notación científica).",
    )
    p17 = doc.buscar("La mayor parte de los registros no corresponde")
    doc.insertar_despues(p17, parrafo(
        "La revisión de calidad mostró, además, que el periodo no es homogéneo. Del 16 al 21 de mayo se registran "
        "unas 32 incidencias por día y no hay registros en turno noche hasta el 20 de mayo, lo que sugiere la puesta "
        "en marcha del registro. En el otro extremo, el conjunto solo publica incidencias ya cerradas y el cierre "
        "automático tarda alrededor de 24 horas, por lo que el 9 y el 10 de junio están incompletos: el 9 de junio "
        "no tiene ningún registro entre las 22:00 y las 23:59. Por eso, de los 26 días se usan **18 para modelar** "
        "(22 de mayo a 8 de junio), y los días de arranque solo aportan historial (sección 10.2)."
    ))
    doc.reescribir(
        "Como fuente complementaria se identificó",
        "Como fuente complementaria se identificó el conjunto de denuncias policiales del SIDPOL (Ministerio del "
        "Interior, 2026), que reúne conteos por año, mes, distrito y modalidad desde enero de 2018 hasta septiembre "
        "de 2026; para San Juan de Miraflores suma 90 272 denuncias en ese periodo. Al no incluir ubicación fina ni "
        "turno, no permite construir microzonas; se usará únicamente como contexto histórico del distrito.",
    )

    # 2.2 Brechas
    p23 = doc.reescribir(
        "Brecha de evidencia:",
        "**Brecha de evidencia:** el volumen de datos disponible es reducido y cubre pocas semanas (18 días "
        "utilizables), por lo que cualquier modelo debe evaluarse con cautela y de forma temporal, no aleatoria.",
    )
    doc.insertar_despues(p23, vineta(
        "**Brecha de disponibilidad:** en la revisión de la Plataforma Nacional de Datos Abiertos no se encontró "
        "otro distrito de la provincia de Lima que publique incidencias con coordenadas a nivel de punto. San Isidro "
        "publica registros sin latitud ni longitud, San Martín de Porres solo indica la comisaría, Jesús María "
        "publica registros sin coordenadas ni hora y Miraflores, conteos mensuales de 2020 y 2021. Por ahora, el "
        "conjunto del CCO de San Juan de Miraflores es el único de Lima que permite este análisis."
    ))

    # 4.3 Síntesis y 5. Justificación
    p43 = doc.buscar("En la búsqueda realizada no se identificó")
    p43.append(_xml(f"<w:p>{_runs(' Tampoco se encontró otro conjunto municipal abierto de Lima con incidencias georreferenciadas a nivel de punto, lo que refuerza la elección del distrito.')}</w:p>")[0])
    doc.reescribir(
        "Justificación técnica.",
        "**Justificación técnica.** Los datos del CCO son abiertos y están georreferenciados (entre los conjuntos "
        "municipales de Lima revisados, son los únicos con ubicación a nivel de punto), y el problema puede "
        "resolverse con modelos clásicos de aprendizaje automático sobre datos tabulares, sin hardware "
        "especializado, lo que lo hace reproducible en un equipo de cómputo convencional.",
    )

    # 6. Limitaciones
    doc.reescribir(
        "Cobertura temporal reducida.",
        "**Cobertura temporal reducida.** El extracto cubre 26 días (16 de mayo a 10 de junio de 2026), pero solo "
        "18 son utilizables para modelar: los seis primeros corresponden al arranque del registro y los dos últimos "
        "están incompletos. La partición queda en 10 días de entrenamiento, 4 de validación y 4 de prueba. No es "
        "posible observar estacionalidad mensual o anual, cada día de la semana aparece pocas veces y la validación "
        "no incluye fines de semana. Los resultados deben considerarse exploratorios; ampliar el periodo requiere "
        "solicitar a la municipalidad un extracto más reciente.",
    )
    p51 = doc.reescribir(
        "Posible cambio de cobertura entre meses.",
        "**Cambio de cobertura en el periodo.** El promedio diario es de unos 84 registros en la parte de mayo "
        "incluida y de unos 125 en junio. Entre la semana del 22 al 28 de mayo y la del 29 de mayo al 4 de junio el "
        "total sube 32,7 %, y el 88 % de ese aumento proviene de las cámaras, lo que apunta a un cambio en el "
        "esfuerzo de registro más que a un cambio real en las incidencias. Para atenuarlo, el modelo incluye "
        "variables del nivel reciente de todo el distrito.",
    )
    doc.insertar_despues(p51, vineta(
        "**Registro incompleto al final del periodo.** El conjunto solo publica incidencias cerradas, y la mayoría "
        "se cierra de forma automática alrededor de 24 horas después. Por eso el 9 y el 10 de junio están "
        "incompletos y se excluyen del modelado."
    ))
    doc.reescribir(
        "Naturaleza del registro.",
        "**Naturaleza del registro.** Los datos son incidencias atendidas por el CCO, no delitos. Solo el 2,0 % se "
        "clasifica como actividad presuntamente delictiva. Además, lo que se registra depende de dónde hay "
        "patrullaje y cámaras: el 74,5 % de los registros proviene de las cámaras del CECOP, lo que puede sesgar la "
        "distribución espacial.",
    )
    doc.reescribir(
        "Calidad de campos.",
        "**Calidad de campos.** El 20,9 % de los registros (543) no tiene sector asignado, por lo que el sector se "
        "usa solo como referencia y la ubicación se toma de las coordenadas. El código de ubigeo que publica el CCO "
        "(150141) corresponde, en el INEI y en el SIDPOL, al distrito de Surquillo; el de San Juan de Miraflores es "
        "150133. Como las direcciones y el 98,8 % de las coordenadas caen dentro del límite de San Juan de "
        "Miraflores, se trata como un error de codificación de la fuente y se usa 150133. De los 32 puntos fuera del "
        "límite, 20 están a menos de 150 m del borde y se conservan; los 12 restantes, dos de ellos con coordenadas "
        "claramente erróneas, se excluyen.",
    )
    doc.reescribir(
        "Variables posteriores al evento.",
        "**Variables posteriores al evento.** El estado final, la fecha de cierre, el tiempo de respuesta y el nivel "
        "de gravedad que asigna el operador durante la coordinación se conocen después de la incidencia y no se "
        "usan como predictores. El 85,1 % de las incidencias figura como “no atendida” y la mayoría se "
        "cierra después de 23 horas, lo que confirma un cierre automático.",
    )
    doc.reescribir(
        "Sin datos de exposición.",
        "**Sin datos de exposición.** Solo se dispone de la población proyectada del distrito (437 390 habitantes "
        "en 2026; INEI, 2025). No hay población, flujo de personas ni superficie habitada por microzona, de modo "
        "que los conteos no son tasas y las comparaciones entre zonas deben leerse con cuidado.",
    )
    p59 = doc.reescribir(
        "Riesgo de estigmatización.",
        "**Riesgo de estigmatización.** Mostrar zonas con nivel alto puede dar una imagen negativa de un sector. "
        "Los resultados se presentan como apoyo a la decisión y con la aclaración de que reflejan registros, no una "
        "condición permanente del lugar. Para mitigarlo, la interfaz habla de “nivel estimado” e "
        "“incidencias registradas”, usa una escala de color no alarmista, muestra un aviso de uso "
        "responsable en el mapa y el ranking, y el modelo se calibra para no sobreestimar el nivel Alto.",
    )
    doc.insertar_despues(p59, vineta(
        "**Desbalance de clases.** En las microzonas de 500 m, el 72,0 % de las observaciones de entrenamiento no "
        "tiene incidencias y solo el 9,4 % alcanza el nivel Alto. Compensar el desbalance al entrenar hace que el "
        "modelo sobreestime el nivel Alto, por lo que se aplica una calibración posterior con los datos de "
        "validación (sección 12.4)."
    ))

    # 7, 8 y 9
    doc.reescribir(
        "Entrenar y comparar regresión logística",
        "Entrenar, calibrar y comparar regresión logística, Random Forest y Gradient Boosting mediante validación "
        "temporal, usando Macro F1 como métrica principal y una línea base de persistencia como referencia.",
    )
    p71 = doc.buscar("Dado el periodo corto de datos")
    p71.append(_xml(f"<w:p>{_runs(' Su contraste preliminar con el prototipo se resume en la sección 12.7.')}</w:p>")[0])
    doc.reescribir(
        "El diseño es no experimental",
        "El diseño es no experimental, pues no se manipulan las variables ni se interviene en el patrullaje, y "
        "longitudinal retrospectivo, porque se analiza una serie histórica de 26 días consecutivos de incidencias "
        "registradas, de los cuales 18 se usan para modelar, y se evalúa el modelo sobre los últimos cuatro días "
        "completos (5 a 8 de junio de 2026). El alcance es descriptivo y predictivo: primero se describe la "
        "distribución espacial y temporal de las incidencias y luego se estima su nivel por microzona y turno.",
    )

    # 10.2 Muestra
    doc.reescribir(
        "La muestra es el extracto publicado",
        "La muestra es el extracto publicado del CCO: **2 592 registros** del 16 de mayo al 10 de junio de 2026, "
        "todos con coordenadas (WGS84). El muestreo es no probabilístico, por disponibilidad: se utiliza la "
        "totalidad del extracto obtenido. La unidad de análisis es la incidencia, y la unidad de modelado es la "
        "combinación de **microzona, fecha y turno**. Tras la depuración quedan 2 580 incidencias. Las microzonas "
        "son celdas de una grilla de 500 m (unas cinco cuadras por lado); se consideran activas las **86 celdas** "
        "que intersecan el distrito y tienen al menos una incidencia en el periodo de entrenamiento. Con 18 días "
        "utilizables y tres turnos, la tabla de modelado tiene 86 × 18 × 3 = **4 644 observaciones**, incluidas las "
        "combinaciones sin incidencias. También se evaluaron grillas de 300, 750 y 1 000 m: la de 300 m deja muy "
        "pocos casos de nivel Alto (3,6 %) y las de 750 y 1 000 m son demasiado grandes para orientar el patrullaje.",
    )
    doc.reescribir(
        "Como partición temporal inicial",
        "La composición del extracto se resume en las tablas 1 a 3, y la partición temporal, en la Tabla 4 y la "
        "Figura 1.",
    )
    fuente_t3 = [el for el in doc.cuerpo if el.tag == W + "p" and doc.texto(el).startswith("Fuente: elaboración propia")][2]
    doc.insertar_despues(
        fuente_t3,
        parrafo(
            "La partición es temporal: entrenamiento del 22 al 31 de mayo (10 días), validación del 1 al 4 de junio "
            "(4 días) y prueba del 5 al 8 de junio (4 días). Los días del 16 al 21 de mayo solo se usan como "
            "historial para calcular variables, y el 9 y el 10 de junio se excluyen por estar incompletos. El nivel "
            "es Bajo con 0 incidencias en la microzona y el turno, Medio con 1 y Alto con 2 o más (sección 12.3)."
        ),
        leyenda("Tabla 4. Partición temporal y distribución del nivel en la tabla de modelado"),
        tabla(
            ["Partición", "Fechas", "Días", "Observaciones", "Bajo", "Medio", "Alto"],
            [["Entrenamiento", "22–31 may", "10", "2 580", "72,0 %", "18,6 %", "9,4 %"],
             ["Validación", "1–4 jun", "4", "1 032", "73,3 %", "16,7 %", "10,1 %"],
             ["Prueba", "5–8 jun", "4", "1 032", "66,5 %", "19,8 %", "13,8 %"],
             ["Total", "22 may–8 jun", "18", "4 644", "71,1 %", "18,4 %", "10,5 %"]],
            [1800, 1700, 900, 1426, 1066, 1067, 1067],
            ["left", "left", "center", "center", "center", "center", "center"],
        ),
        nota("Fuente: elaboración propia a partir del extracto del CCO (MDSJM, 2026)."),
        leyenda("Figura 1. Incidencias registradas por día y partición temporal"),
        img.figura(FIGURAS / "fig_particion.png", "Barras de incidencias por día coloreadas según la partición"),
        nota("Fuente: elaboración propia a partir del extracto del CCO (MDSJM, 2026). El total diario incluye los "
             "12 registros que la depuración excluye."),
    )
    doc.reescribir(
        "El conjunto de denuncias policiales del SIDPOL",
        "El conjunto de denuncias policiales del SIDPOL (Ministerio del Interior, 2026) cubre de enero de 2018 a "
        "septiembre de 2026 con conteos por año, mes, distrito y modalidad. En San Juan de Miraflores suma 90 272 "
        "denuncias en ese periodo (10 383 en 2025). Se usará para describir la tendencia y la composición histórica "
        "de las denuncias en el distrito y no forma parte del conjunto de entrenamiento.",
    )

    # 11. Instrumentos
    doc.reescribir(
        "Extracto de incidencias atendidas por el CCO",
        "Extracto de incidencias atendidas por el CCO de la MDSJM, en el formato CSV oficial de la Plataforma "
        "Nacional de Datos Abiertos (licencia ODC-By 1.0).",
    )
    p102 = doc.reescribir(
        "Cartografía base de OpenStreetMap",
        "Cartografía base de OpenStreetMap, con la atribución correspondiente (OpenStreetMap Foundation, s. f.), y "
        "límite distrital del INEI (ubigeo 150133), obtenido del servicio de la Autoridad Nacional del Agua (ANA, "
        "s. f.).",
    )
    doc.insertar_despues(p102, vineta(
        "Población proyectada del distrito (INEI, 2025), solo como contexto."
    ))
    doc.reescribir(
        "Python con Pandas y NumPy",
        "Python 3.10 con Pandas y NumPy para limpieza y análisis, y Shapely y pyproj para coordenadas, microzonas y "
        "operaciones espaciales (GeoPandas se descartó para simplificar la instalación en Windows).",
    )
    doc.reescribir(
        "Scikit-learn para regresión logística",
        "Scikit-learn para regresión logística, Random Forest y Gradient Boosting, y para el cálculo de métricas "
        "(Scikit-learn developers, s. f.-a); SciPy para ajustar la calibración, y Joblib para guardar el modelo.",
    )
    doc.reescribir(
        "Streamlit para la aplicación web",
        "Streamlit para la aplicación web, con Folium (streamlit-folium) para el mapa y Plotly para los gráficos.",
    )
    doc.reescribir(
        "SQLite para registrar recursos",
        "SQLite como base de datos local de todo el sistema: incidencias, microzonas, observaciones, modelos, "
        "predicciones, prioridades, recursos y asignaciones.",
    )
    doc.reescribir(
        "Git y GitHub para el control de versiones",
        "Git y GitHub para el control de versiones; pytest y Ruff para pruebas automáticas y estilo de código; "
        "Power BI como herramienta opcional para un tablero histórico a partir de archivos exportados.",
    )
    doc.reescribir(
        "Partición temporal de los datos",
        "Partición temporal de los datos en entrenamiento, validación y prueba (10, 4 y 4 días), evitando mezclar "
        "aleatoriamente observaciones relacionadas en el tiempo (Scikit-learn developers, s. f.-b).",
    )
    p114 = doc.buscar("Macro F1 como métrica principal")
    p114.append(_xml(f"<w:p>{_runs(' Por el periodo corto, se informan también el Macro F1 por día y por turno e intervalos de confianza bootstrap que remuestrean días completos.')}</w:p>")[0])
    p115 = doc.buscar("Comparación contra una línea base")
    doc.insertar_despues(p115, vineta(
        "Calibración posterior con el periodo de validación: escalado de temperatura con un sesgo por clase (Guo et "
        "al., 2017) y ajuste de la regla de decisión, para que la proporción estimada de cada nivel se acerque a la "
        "observada. El Macro F1 de validación se calcula dejando un día fuera, para no favorecer al modelo calibrado."
    ))
    p116 = doc.buscar("Ranking de prioridad P")
    p116.append(_xml(f"<w:p>{_runs(' Los pesos por defecto son 0,5, 0,3 y 0,2.')}</w:p>")[0])

    # 12. Diseño del modelo y arquitectura (nueva)
    detalle = recortar("app_Detalle_de_microzona.png", "app_detalle_doc.png", (470, 170, 0, 1290))
    ranking = recortar("app_Ranking.png", "app_ranking_doc.png", (470, 170, 0, 1290))
    mapa = recortar("app_Mapa.png", "app_mapa_doc.png", (470, 170, 0, 1290))
    doc.insertar_despues(
        p116,
        titulo("12. Diseño del modelo y arquitectura del sistema", 1),
        parrafo(
            "El prototipo se organiza en dos partes que comparten una base de datos SQLite: un **pipeline por "
            "lotes** que prepara los datos, entrena y calibra los modelos y calcula la prioridad, y una "
            "**aplicación web local** que solo consulta los resultados (Figura 2). El código, las pruebas y la "
            "documentación técnica forman parte del repositorio del proyecto."
        ),
        titulo("12.1 Arquitectura general", 2),
        parrafo(
            "El pipeline se ejecuta con un solo comando (python -m seguridad_ciudadana todo) y es reproducible: con "
            "los mismos datos y la misma configuración produce las mismas cifras. La aplicación sigue una "
            "arquitectura por capas: las páginas llaman a una capa de servicios, los servicios usan repositorios y "
            "solo los repositorios contienen SQL. Así, la interfaz nunca entrena ni modifica el modelo, y adaptar el "
            "sistema a otro distrito consiste en cambiar el archivo de configuración y los datos de entrada, no el "
            "código."
        ),
        leyenda("Figura 2. Arquitectura del prototipo"),
        img.figura(FIGURAS / "fig_arquitectura.png", "Diagrama de fuentes, pipeline por lotes, base SQLite y aplicación web"),
        nota("Fuente: elaboración propia."),
        titulo("12.2 Flujo de datos", 2),
        vineta("**Ingesta y limpieza:** se verifica la huella sha256 del archivo, se descartan las columnas "
               "posteriores al evento, se marcan los puntos fuera del límite distrital y se asigna una gravedad de 1 "
               "a 5 a cada tipo de incidencia."),
        vineta("**Microzonas:** grilla de 500 m en coordenadas UTM 18S (EPSG:32718); 121 celdas tocan el distrito y "
               "86 tienen registros en el periodo de entrenamiento."),
        vineta("**Tabla de modelado:** una fila por microzona, fecha y turno, con las combinaciones sin incidencias "
               "incluidas, y 17 variables calculadas solo con información anterior a la fecha que se estima."),
        vineta("**Entrenamiento, calibración y evaluación** con la partición temporal (sección 12.4)."),
        vineta("**Predicción y priorización:** el modelo vigente estima el nivel de cada microzona para las fechas "
               "de prueba y para el día siguiente al último día completo (9 de junio), y se calcula la prioridad P."),
        titulo("12.3 Variable objetivo y variables predictoras", 2),
        parrafo(
            "La variable objetivo es el **nivel de incidencias registradas** en la microzona durante el turno: Bajo "
            "(0 incidencias), Medio (1) o Alto (2 o más). El umbral corresponde a la mediana de los conteos "
            "positivos del periodo de entrenamiento y se mantiene fijo en validación y prueba. Las variables "
            "predictoras se agrupan en cuatro bloques (Tabla 5). Todas usan datos de fechas anteriores a la "
            "estimada, y una prueba automática verifica que no haya fuga de información."
        ),
        leyenda("Tabla 5. Variables predictoras del modelo"),
        tabla(
            ["Grupo", "N.º", "Variables"],
            [["Historial de la microzona", "9", "Incidencias del mismo turno el día anterior y hace una semana; "
              "sumas y promedios de 3 y 7 días; días desde el último registro; gravedad media reciente; nivel del "
              "día anterior"],
             ["Vecindad", "2", "Incidencias en las 8 celdas vecinas el día anterior y en los últimos 7 días"],
             ["Calendario", "3", "Día de la semana, fin de semana y turno"],
             ["Contexto del distrito", "3", "Incidencias de todo el distrito el día anterior (total y del mismo "
              "turno) y promedio de 7 días; absorben los cambios de cobertura"]],
            [2300, 900, 5826],
            ["left", "center", "left"],
        ),
        nota("Fuente: elaboración propia. El indicador de feriado se calculó, pero no entra al modelo porque no "
             "varía en entrenamiento ni en validación."),
        titulo("12.4 Modelos, validación y calibración", 2),
        parrafo(
            "Se comparan la regresión logística multinomial, Random Forest y Gradient Boosting frente a una línea "
            "base de persistencia, que repite el nivel del mismo turno del día anterior. Cada modelo se ajusta solo "
            "con el periodo de entrenamiento, con una búsqueda pequeña de hiperparámetros evaluada en validación. "
            "Para compensar el desbalance (72 % de observaciones en nivel Bajo) se usan pesos de clase balanceados."
        ),
        parrafo(
            "Los pesos balanceados tienen un efecto secundario: el modelo sobreestima el nivel Alto. En la primera "
            "versión, la regresión logística marcaba Alto en el 34,3 % de las observaciones de prueba, frente al "
            "13,8 % observado. Por eso se añadió una **calibración posterior**, ajustada solo con validación, en dos "
            "pasos: (1) un escalado de temperatura con un sesgo por clase (Guo et al., 2017), que hace que la "
            "probabilidad media de cada nivel coincida con su frecuencia observada, y (2) un ajuste de la regla de "
            "decisión que maximiza el Macro F1. El modelo vigente es el de mayor Macro F1 en validación, calculado "
            "dejando un día fuera para que la calibración no lo favorezca."
        ),
        titulo("12.5 Priorización explicable", 2),
        parrafo("La prioridad de cada microzona es **P = w1·R + w2·G + w3·F**, con componentes normalizados entre 0 y 1:"),
        vineta("**R (nivel estimado):** valor esperado del nivel según las probabilidades calibradas: "
               "0·p(Bajo) + 0,5·p(Medio) + 1·p(Alto)."),
        vineta("**G (gravedad histórica):** gravedad media, en escala de 1 a 5, de las incidencias de la microzona "
               "en los siete días previos. La escala ordena los tipos del catálogo del CCO, desde las actividades "
               "presuntamente delictivas (5) hasta los operativos y apoyos (1), y es un supuesto de diseño revisable."),
        vineta("**F (frecuencia reciente):** incidencias de la microzona en los siete días previos, divididas entre "
               "el máximo observado en entrenamiento."),
        parrafo(
            "Los pesos por defecto (0,5, 0,3 y 0,2) dan más peso a la estimación del modelo sin ignorar la gravedad "
            "ni la tendencia reciente. El operador puede cambiarlos y la ficha de detalle muestra el aporte de cada "
            "componente (Figura 3)."
        ),
        leyenda("Figura 3. Ficha de detalle: descomposición de la prioridad de una microzona"),
        img.figura(detalle, "Captura de la ficha de detalle con la tabla de R, G y F y las probabilidades por nivel"),
        nota("Fuente: captura del prototipo (9 de junio de 2026, turno mañana)."),
        titulo("12.6 Aplicación web y base de datos", 2),
        parrafo(
            "La aplicación tiene siete páginas: Inicio, Ranking, Mapa, Detalle de microzona, Tablero, Recursos "
            "(segundo nivel) y Metodología. El Ranking ordena las microzonas por P para la fecha y el turno "
            "elegidos (Figura 4), y el Mapa las colorea por nivel estimado sobre OpenStreetMap (Figura 5). La base "
            "SQLite tiene 12 tablas con claves foráneas, y un disparador impide asignar más recursos de los "
            "declarados. El sistema cuenta con 72 pruebas automáticas."
        ),
        leyenda("Figura 4. Página de ranking de prioridad sugerida"),
        img.figura(ranking, "Captura de la página de ranking con la tabla de microzonas y los controles de pesos"),
        nota("Fuente: captura del prototipo (9 de junio de 2026, turno mañana)."),
        leyenda("Figura 5. Mapa de nivel estimado por microzona"),
        img.figura(mapa, "Captura del mapa con las microzonas coloreadas por nivel estimado"),
        nota("Fuente: captura del prototipo; mapa base © colaboradores de OpenStreetMap."),
        titulo("12.7 Resultados preliminares", 2),
        parrafo(
            "Los resultados son exploratorios: la prueba cubre cuatro días y los intervalos de confianza se solapan "
            "(Tabla 6)."
        ),
        leyenda("Tabla 6. Macro F1 por modelo (versión calibrada)"),
        tabla(
            ["Modelo", "Validación", "Prueba", "IC 95 % (prueba)", "Alto predicho (prueba)"],
            [["Persistencia (línea base)", "0,439", "0,432", "0,416–0,452", "12,5 %"],
             ["Regresión logística (vigente)", "0,480", "0,435", "0,406–0,456", "22,5 %"],
             ["Random Forest", "0,477", "0,448", "0,422–0,466", "11,1 %"],
             ["Gradient Boosting", "0,475", "0,441", "0,416–0,465", "11,2 %"]],
            [2826, 1300, 1300, 1900, 1700],
            ["left", "center", "center", "center", "center"],
        ),
        nota("Fuente: elaboración propia. En los modelos de aprendizaje automático, la validación se calcula "
             "dejando un día fuera. El intervalo se obtiene por bootstrap de días completos. La proporción de nivel "
             "Alto observada en prueba es 13,8 %."),
        vineta("**H1 se sostiene de forma débil:** en prueba, Random Forest (0,448) supera a la regresión logística "
               "(0,435) y a la persistencia (0,432), pero los intervalos se solapan."),
        vineta("**HE1 se sostiene:** al permutar las variables de historial, el Macro F1 de validación cae 0,142, "
               "frente a 0,044 al permutar las de calendario; ocurre lo mismo en los tres modelos."),
        vineta("**HE2 se sostiene:** el 14,0 % de las celdas del distrito concentra la mitad de los registros y el "
               "33,1 %, el 80 % (índice de Gini 0,63; Figura 6). Es concentración del registro del CCO, no del delito."),
        vineta("**Efecto de la calibración:** reduce la proporción de Alto predicha en prueba de 34,3 % a 22,5 % y "
               "eleva el Macro F1 de la regresión logística de 0,418 a 0,435. La prueba ya se había evaluado una vez "
               "con la versión sin calibrar, así que esta mejora debe leerse con cautela."),
        leyenda("Figura 6. Concentración espacial de las incidencias registradas"),
        img.figura(FIGURAS / "fig_concentracion.png", "Curva de concentración de incidencias por celdas", 0.62),
        nota("Fuente: elaboración propia a partir del extracto del CCO (MDSJM, 2026); 121 celdas de 500 m, del 22 "
             "de mayo al 4 de junio."),
    )

    # Referencias
    doc.reescribir(
        "Ministerio del Interior. (2026).",
        "Ministerio del Interior. (2026). *Denuncias policiales registradas a nivel nacional, enero 2018 a "
        "septiembre 2026* [Conjunto de datos]. Plataforma Nacional de Datos Abiertos. "
        "https://www.datosabiertos.gob.pe/dataset/denuncias-policiales-registradas-nivel-nacional-mininter",
    )
    doc.reescribir(
        "Municipalidad Distrital de San Juan de Miraflores. (2026).",
        "Municipalidad Distrital de San Juan de Miraflores. (2026). *Relación de incidencias atendidas por el Centro "
        "de Control de Operaciones (CCO)* (versión 1.0) [Conjunto de datos]. Plataforma Nacional de Datos Abiertos. "
        "https://www.datosabiertos.gob.pe/dataset/relaci%C3%B3n-de-incidencias-atendidas-por-el-centro-de-control-de-operaciones-cco-municipalidad",
    )
    chainey = doc.buscar("Chainey, S., Tompson")
    chainey.addprevious(referencia(
        "Autoridad Nacional del Agua. (s. f.). *Distritos* [Servicio de entidades geográficas, fuente INEI]. "
        "Recuperado el 31 de octubre de 2026, de https://geosnirh.ana.gob.pe/server/rest/services/Hosted/distritos/FeatureServer"
    ))
    escobedo = doc.buscar("Escobedo Neyra, M. C.")
    doc.insertar_despues(
        escobedo,
        referencia(
            "Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration of modern neural networks. "
            "*Proceedings of the 34th International Conference on Machine Learning, 70*, 1321-1330. PMLR."
        ),
        referencia(
            "Instituto Nacional de Estadística e Informática. (2025). *Perú: Población total proyectada al 30 de "
            "junio de cada año, según departamento, provincia y distrito, 2018-2026* [Cuadro estadístico]. "
            "https://www.gob.pe/institucion/inei/informes-publicaciones/6894980-peru-poblacion-total-proyectada-al-30-de-junio-de-cada-ano-segun-departamento-provincia-y-distrito-2018-2026"
        ),
    )


def main() -> int:
    trabajo = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else AQUI / "_trabajo"
    if trabajo.exists():
        shutil.rmtree(trabajo)
    with zipfile.ZipFile(ORIGINAL) as z:
        z.extractall(trabajo)
    doc, img = Documento(trabajo), Imagenes(trabajo)
    aplicar(doc, img)
    doc.guardar()
    img.guardar()
    SALIDA.unlink(missing_ok=True)
    with zipfile.ZipFile(SALIDA, "w", zipfile.ZIP_DEFLATED) as z:
        for ruta in sorted(trabajo.rglob("*")):
            if ruta.is_file():
                z.write(ruta, ruta.relative_to(trabajo).as_posix())
    print("OK", SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
