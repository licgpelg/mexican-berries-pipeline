"""Genera el informe (PBIR) de powerbi/Berries.Report: tema, páginas y visuales.

Uso: py scripts/generar_informe.py   (con Power BI Desktop CERRADO: al guardar, Desktop
reescribe el informe con lo que tiene en memoria). PAGINA_ACTIVA=p2produccion elige la página
con la que abre. Borra y reescribe definition/pages: los retoques hechos a mano en Desktop
se pierden. El mapa de México se copia de la instalación de Desktop."""
import json
import os
import shutil
from pathlib import Path

REPORT = Path(__file__).resolve().parents[1] / "powerbi" / "Berries.Report"
PAGES = REPORT / "definition" / "pages"
SCHEMA_V = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.12.0/schema.json"
SCHEMA_P = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
MAPA_DESKTOP = Path(r"C:\Program Files\Microsoft Power BI Desktop\bin\WebView2Resources\minerva"
                    r"\sharedresources\Shapemaps\mexico.states.topo.json")

VERDE = "#1F4D2C"; VERDE_CLARO = "#F5DDE3"; TINTA = "#1F2421"; GRIS = "#5E6660"
FONDO = "#F4F1EA"; BAYA = "#8E1B3A"; BORDE = "#E3DED2"
PALETA = ["#8E1B3A", "#2F7D4A", "#D9822B", "#3F6FA8", "#C9A227", "#6B4E8C", "#3E8E7E", "#A0522D"]
ANIOS_COM = list(range(2006, 2026))  # 2026 va incompleto: fuera de las series anuales
ANIOS_MUNDO = list(range(2000, 2025))
ALTO_BANDA = 100


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def texto_lit(t):
    return lit("'" + t.replace("'", "''") + "'")


def color(c):
    return {"solid": {"color": lit(f"'{c}'")}}


def col(e, p):
    return {"Column": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}}


def med(e, p):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}}


def proj(campo, nombre=None, activo=True):
    k = "Column" if "Column" in campo else "Measure"
    e = campo[k]["Expression"]["SourceRef"]["Entity"]; p = campo[k]["Property"]
    d = {"field": campo, "queryRef": f"{e}.{p}", "nativeQueryRef": p}
    # «active» solo en categorías de gráficos y segmentadores: en una tabla deja fuera
    # las medidas (la tabla salía solo con la columna de texto).
    if k == "Column" and activo:
        d["active"] = True
    if nombre:
        d["displayName"] = nombre
    return d


def literal(v):
    if isinstance(v, int):
        return f"{v}L"
    if v.startswith("datetime'"):  # fecha ya escrita como literal de Power BI
        return v
    return "'" + v.replace("'", "''") + "'"


def condicion(p, valores, excluir=False):
    cond = {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}},
                                               "Property": p}}],
                   "Values": [[{"Literal": {"Value": literal(v)}}] for v in valores]}}
    return {"Not": {"Expression": cond}} if excluir else cond


def filtro(nombre, e, p, valores, excluir=False, como="User"):
    return {"name": nombre, "field": col(e, p), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "d", "Entity": e, "Type": 0}],
                       "Where": [{"Condition": condicion(p, valores, excluir)}]},
            "howCreated": como}


def filtro_slicer(e, p, valores):
    return {"filter": {"Version": 2, "From": [{"Name": "d", "Entity": e, "Type": 0}],
                       "Where": [{"Condition": condicion(p, valores)}]}}


def contenedor(titulo=None, fondo="#FFFFFF", borde=True):
    """Tarjeta blanca con esquinas redondeadas y sombra suave: el estilo de todos los visuales."""
    d = {"background": [{"properties": {"show": lit("true"), "color": color(fondo),
                                         "transparency": lit("0D")}}],
         "border": [{"properties": {"show": lit("true" if borde else "false"),
                                     "color": color(BORDE), "radius": lit("12D")}}],
         "dropShadow": [{"properties": {"show": lit("true" if borde else "false"),
                                         "color": color("#000000"), "transparency": lit("88D"),
                                         "position": lit("'Outer'"), "preset": lit("'BottomRight'")}}],
         "subTitle": [{"properties": {"show": lit("false")}}],
         "padding": [{"properties": {"top": lit("8D"), "bottom": lit("8D"),
                                      "left": lit("12D"), "right": lit("12D")}}]}
    if titulo is None:
        d["title"] = [{"properties": {"show": lit("false")}}]
    else:
        d["title"] = [{"properties": {"show": lit("true"), "text": texto_lit(titulo),
                                       "fontSize": lit("11D"), "bold": lit("true"),
                                       "fontColor": color(TINTA)}}]
    return d


def tema():
    return {
        "name": "Berries de México",
        "dataColors": PALETA,
        "foreground": TINTA, "background": "#FFFFFF", "tableAccent": BAYA,
        # Degradado de los mapas y del formato condicional: de crema a baya.
        "minimum": "#F6E7EA", "center": "#C4566F", "maximum": "#5C0F25",
        "good": "#2F7D4A", "neutral": "#C9A227", "bad": "#B23A48",
        "textClasses": {
            "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 26, "color": BAYA},
            "title": {"fontFace": "Segoe UI Semibold", "fontSize": 11, "color": TINTA},
            "header": {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": TINTA},
            "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": "#3B423D"},
        },
        "visualStyles": {
            "*": {"*": {
                "valueAxis": [{"gridlineColor": {"solid": {"color": "#ECE8DF"}}}],
            }},
            "tableEx": {"*": {
                "columnHeaders": [{"fontColor": {"solid": {"color": "#FFFFFF"}},
                                   "backColor": {"solid": {"color": BAYA}}}],
                "values": [{"backColorSecondary": {"solid": {"color": "#F8F6F1"}}}],
            }},
        },
    }


class Pagina:
    def __init__(self, nombre, visible, titulo, subtitulo, ancho_titulo=1216, filtros=(),
                 ancho=1280, alto=720, vinculo=None, oculta=False, banda=True):
        self.nombre, self.visible, self.visuales = nombre, visible, []
        self.interacciones = []  # (origen, destino, tipo): «NoFilter» corta el filtro cruzado
        self.filtros = list(filtros)
        self.ancho, self.alto, self.vinculo, self.oculta = ancho, alto, vinculo, oculta
        self.z = 0
        if banda:
            self.forma("banda", 0, 0, ancho, ALTO_BANDA, BAYA)
        if titulo is not None:
            if isinstance(titulo, dict):
                self.titulo_medida("titulo", 32, 4, ancho_titulo, 62, titulo, 15, "#FFFFFF")
            else:
                self.texto("titulo", 32, 14, ancho_titulo, 52, [(titulo, 20, True, "#FFFFFF")])
        if subtitulo is not None:
            if isinstance(subtitulo, dict):
                self.titulo_medida("subtitulo", 32, 64, ancho_titulo, 32, subtitulo, 11, VERDE_CLARO,
                                   negrita=False)
            else:
                self.texto("subtitulo", 32, 66, ancho_titulo, 30, [(subtitulo, 11, False, VERDE_CLARO)])

    def _add(self, nombre, x, y, w, h, visual, filtros=None, oculto=False):
        self.z += 1000
        v = {"$schema": SCHEMA_V, "name": nombre,
             "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w,
                          "tabOrder": self.z},
             "visual": visual}
        if filtros:
            v["filterConfig"] = {"filters": filtros}
        if oculto:
            v["isHidden"] = True
        self.visuales.append(v)

    def forma(self, nombre, x, y, w, h, relleno):
        self._add(nombre, x, y, w, h, {
            "visualType": "shape",
            "objects": {"shape": [{"properties": {"tileShape": lit("'rectangle'")}}],
                        "fill": [{"properties": {"show": lit("true"), "fillColor": color(relleno),
                                                  "transparency": lit("0D")},
                                  "selector": {"id": "default"}}],
                        "outline": [{"properties": {"show": lit("false")}}]},
            "visualContainerObjects": {"title": [{"properties": {"show": lit("false")}}],
                                       "background": [{"properties": {"show": lit("false")}}],
                                       "border": [{"properties": {"show": lit("false")}}],
                                       "dropShadow": [{"properties": {"show": lit("false")}}]},
            "drillFilterOtherVisuals": True})

    def titulo_medida(self, nombre, x, y, w, h, medida, size=18, c="#FFFFFF", negrita=True):
        """Un cuadro de texto no admite medidas: el texto dinámico es el título de una forma
        transparente, ligado a la medida (fx)."""
        self._add(nombre, x, y, w, h, {
            "visualType": "shape",
            "objects": {"shape": [{"properties": {"tileShape": lit("'rectangle'")}}],
                        "fill": [{"properties": {"show": lit("false")}}],
                        "outline": [{"properties": {"show": lit("false")}}]},
            "visualContainerObjects": {
                "title": [{"properties": {"show": lit("true"), "text": {"expr": medida},
                                          "fontSize": lit(f"{size}D"),
                                          "bold": lit("true" if negrita else "false"),
                                          "fontColor": color(c), "alignment": lit("'left'"),
                                          "titleWrap": lit("true")}}],
                "background": [{"properties": {"show": lit("false")}}],
                "border": [{"properties": {"show": lit("false")}}],
                "dropShadow": [{"properties": {"show": lit("false")}}]},
            "drillFilterOtherVisuals": True})

    def texto(self, nombre, x, y, w, h, parrafos):
        pars = []
        for t, size, bold, c in parrafos:
            estilo = {"fontSize": f"{size}pt", "color": c}
            if bold:
                estilo["fontWeight"] = "bold"
            pars.append({"textRuns": [{"value": t, "textStyle": estilo}]})
        self._add(nombre, x, y, w, h, {
            "visualType": "textbox",
            "objects": {"general": [{"properties": {"paragraphs": pars}}]},
            "visualContainerObjects": {"background": [{"properties": {"show": lit("false")}}]},
            "drillFilterOtherVisuals": True})

    def tarjeta(self, nombre, x, y, w, h, medida, etiqueta, unidades="0D", filtros=None, size=24):
        self._add(nombre, x, y, w, h, {
            "visualType": "card",
            "query": {"queryState": {"Values": {"projections": [proj(medida)]}}},
            "objects": {
                "labels": [{"properties": {"color": color(BAYA), "fontSize": lit(f"{size}D"),
                                           "labelDisplayUnits": lit(unidades),
                                           "labelPrecision": lit("1L" if unidades not in ("0D", "1D") else "0L")}}],
                "categoryLabels": [{"properties": {"show": lit("false")}}],
                "wordWrap": [{"properties": {"show": lit("true")}}]},
            "visualContainerObjects": contenedor(etiqueta),
            "drillFilterOtherVisuals": True}, filtros)

    def grafico(self, nombre, tipo, x, y, w, h, categoria, medida, titulo, serie=None,
                filtros=None, orden_medida=False, etiquetas=False, leyenda=True,
                unidades_etiqueta="0D", tooltip=None, relleno=None):
        qs = {"Category": {"projections": [proj(categoria)]},
              "Y": {"projections": [proj(medida)]}}
        if serie:
            qs["Series"] = {"projections": [proj(serie)]}
        q = {"queryState": qs}
        if orden_medida:
            q["sortDefinition"] = {"sort": [{"field": medida, "direction": "Descending"}]}
        objetos = {"legend": [{"properties": {"show": lit("true" if (serie and leyenda) else "false"),
                                              "position": lit("'Top'")}}],
                   "labels": [{"properties": {"show": lit("true" if etiquetas else "false"),
                                              "fontSize": lit("8D"),
                                              "labelDisplayUnits": lit(unidades_etiqueta)}}],
                   "valueAxis": [{"properties": {"showAxisTitle": lit("false")}}],
                   "categoryAxis": [{"properties": {"showAxisTitle": lit("false")}}]}
        if relleno:
            objetos["dataPoint"] = [{"properties": {"fill": {"solid": {"color": {"expr": relleno}}}},
                                     "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}]
        elif not serie and tipo in ("clusteredBarChart", "columnChart"):
            objetos["dataPoint"] = [{"properties": {"fill": color(BAYA)}}]
        vco = contenedor(titulo)
        if tooltip:
            vco["visualTooltip"] = [{"properties": {"show": lit("true"), "type": lit("'Canvas'"),
                                                    "section": texto_lit(tooltip)}}]
        self._add(nombre, x, y, w, h, {"visualType": tipo, "query": q, "objects": objetos,
                                         "visualContainerObjects": vco,
                                         "drillFilterOtherVisuals": True}, filtros)

    def mapa(self, nombre, x, y, w, h, ubicacion, medida, titulo, filtros=None, tooltip=None):
        """Mapa de formas con el mapa de estados de México que trae Power BI (claves = nombre
        del estado, por eso el ETL llama «Estado de México» al estado)."""
        vco = contenedor(titulo)
        if tooltip:
            vco["visualTooltip"] = [{"properties": {"show": lit("true"), "type": lit("'Canvas'"),
                                                    "section": texto_lit(tooltip)}}]
        self._add(nombre, x, y, w, h, {
            "visualType": "shapeMap",
            # Roles del mapa de formas: Category (ubicación), Series (leyenda), Value (degradado).
            "query": {"queryState": {"Category": {"projections": [proj(ubicacion)]},
                                     "Value": {"projections": [proj(medida)]}}},
            "objects": {
                "shape": [{"properties": {"map": {"geoJson": {
                    "type": lit("'shared'"), "name": lit("'mexico.states.topo'"),
                    # El contenido apunta al mapa de SharedResources (PackageType 2).
                    "content": {"expr": {"ResourcePackageItem": {
                        "PackageName": "SharedResources", "PackageType": 2,
                        "ItemName": "mexico.states.topo"}}}}},
                    "projectionEnum": lit("'mercator'")}}],
                # Relleno por medida (fx): el degradado automático salía de un solo tono.
                "dataPoint": [{"properties": {"fill": {"solid": {"color": {"expr": COLOR_MAPA}}}},
                               "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}],
                "defaultColors": [{"properties": {"defaultShow": lit("true"),
                                                   "defaultColor": color("#ECE8DF"),
                                                   "borderColor": color("#FFFFFF")}}],
                "legend": [{"properties": {"show": lit("false")}}]},
            "visualContainerObjects": vco,
            "drillFilterOtherVisuals": True}, filtros)

    def tabla(self, nombre, x, y, w, h, campos, titulo, filtros=None, orden=None, totales=True):
        q = {"queryState": {"Values": {"projections": [proj(c, n, activo=False) for c, n in campos]}}}
        if orden:
            q["sortDefinition"] = {"sort": [{"field": orden, "direction": "Descending"}]}
        self._add(nombre, x, y, w, h, {"visualType": "tableEx", "query": q,
                                         "objects": {"total": [{"properties": {
                                             "totals": lit("true" if totales else "false")}}]},
                                         "visualContainerObjects": contenedor(titulo),
                                         "drillFilterOtherVisuals": True}, filtros)

    def segmentador(self, nombre, x, y, w, h, campo, titulo, modo="Basic", horizontal=True,
                    sincro=None, inicial=None, oculto=False, sobre_banda=False, unico=False):
        general = {"orientation": lit("1D" if horizontal else "0D")}
        if inicial:
            e = campo["Column"]["Expression"]["SourceRef"]["Entity"]
            general["filter"] = filtro_slicer(e, campo["Column"]["Property"], inicial)
        vco = contenedor(titulo)
        if sobre_banda:
            vco["title"][0]["properties"]["fontColor"] = color("#FFFFFF")
            vco["background"][0]["properties"]["show"] = lit("false")
            vco["border"][0]["properties"]["show"] = lit("false")
            vco["dropShadow"][0]["properties"]["show"] = lit("false")
        visual = {
            "visualType": "slicer",
            "query": {"queryState": {"Values": {"projections": [proj(campo)]}}},
            "objects": {"data": [{"properties": {"mode": lit(f"'{modo}'")}}],
                        "general": [{"properties": general}],
                        "selection": [{"properties": {"singleSelect": lit("true" if unico else "false")}}],
                        "header": [{"properties": {"show": lit("false")}}]},
            "visualContainerObjects": vco,
            "drillFilterOtherVisuals": True}
        # Mismo grupo en varias páginas = la selección viaja entre ellas.
        if sincro:
            visual["syncGroup"] = {"groupName": sincro, "fieldChanges": True, "filterChanges": True}
        self._add(nombre, x, y, w, h, visual, oculto=oculto)

    def cabecera_cultivo(self, sincro=True):
        """Segmentadores de grupo y cultivo sobre la banda, a la derecha. Sincronizados con
        Inicio, salvo en la página de contraste, que compara todos los cultivos."""
        self.segmentador("s_grupo", 900, 14, 170, 72, GRUPO, "Grupo", modo="Dropdown",
                         sincro="grupo" if sincro else None,
                         inicial=["Berries"] if sincro else None)
        self.segmentador("s_cultivo", 1078, 14, 170, 72, CULTIVO, "Cultivo", modo="Dropdown",
                         sincro="cultivo" if sincro else None)

    def boton(self, nombre, x, y, w, h, texto, destino=None, atras=False, relleno=BAYA):
        enlace = ({"show": lit("true"), "type": lit("'Back'")} if atras else
                  {"show": lit("true"), "type": lit("'PageNavigation'"),
                   "navigationSection": texto_lit(destino)})
        self._add(nombre, x, y, w, h, {
            "visualType": "actionButton",
            "objects": {
                # «show» va sin selector; el contenido, con el estado «default» del botón.
                "icon": [{"properties": {"show": lit("false")}}],
                "text": [{"properties": {"show": lit("true")}},
                         {"properties": {"text": texto_lit(texto), "fontColor": color("#FFFFFF"),
                                         "fontSize": lit("12D"), "bold": lit("true")},
                          "selector": {"id": "default"}}],
                "fill": [{"properties": {"show": lit("true"), "fillColor": color(relleno),
                                          "transparency": lit("0D")}, "selector": {"id": "default"}}],
                "outline": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}]},
            "visualContainerObjects": {"visualLink": [{"properties": enlace}],
                                       "border": [{"properties": {"show": lit("false"),
                                                                   "radius": lit("10D")}}]},
            "drillFilterOtherVisuals": True})

    def navegador(self, nombre, x, y, w, h):
        self._add(nombre, x, y, w, h, {
            "visualType": "pageNavigator",
            "objects": {"pages": [{"properties": {"showHiddenPages": lit("false"),
                                                   "showTooltipPages": lit("false")}}]},
            "drillFilterOtherVisuals": True})

    def escribir(self):
        d = PAGES / self.nombre
        pagina = {"$schema": SCHEMA_P, "name": self.nombre, "displayName": self.visible,
                  "displayOption": "FitToPage", "height": self.alto, "width": self.ancho,
                  "objects": {"background": [{"properties": {"color": color(FONDO),
                                                              "transparency": lit("0D")}}]}}
        if self.vinculo:
            pagina["pageBinding"] = self.vinculo
        if self.oculta:
            pagina["visibility"] = "HiddenInViewMode"
        if self.filtros:
            pagina["filterConfig"] = {"filters": self.filtros}
        if self.interacciones:
            pagina["visualInteractions"] = [{"source": o, "target": d, "type": t}
                                            for o, d, t in self.interacciones]
        (d / "visuals").mkdir(parents=True, exist_ok=True)
        (d / "page.json").write_text(json.dumps(pagina, indent=2, ensure_ascii=False), encoding="utf-8")
        for v in self.visuales:
            vd = d / "visuals" / v["name"]
            vd.mkdir(parents=True, exist_ok=True)
            (vd / "visual.json").write_text(json.dumps(v, indent=2, ensure_ascii=False), encoding="utf-8")


# Campos
ANIO = col("dim_fecha", "anio")
CULTIVO = col("dim_cultivo", "cultivo")
GRUPO = col("dim_cultivo", "grupo")
ESTADO = col("dim_municipio", "estado")
MUNICIPIO = col("dim_municipio", "municipio")
MODALIDAD = col("dim_modalidad", "modalidad")
GRUPO_COM = col("dim_hs6", "grupo_comercio")
PAIS_COM = col("dim_pais_comercio", "pais_en")
P = "fact_produccion"; C = "fact_comercio"; M = "fact_produccion_mundial"
PROD = med(P, "Producción (t)"); VALOR = med(P, "Valor de la producción (MXN)")
HA = med(P, "Superficie cosechada (ha)"); REND = med(P, "Rendimiento (t/ha)")
PRECIO = med(P, "Precio medio rural (MXN/t)"); VXHA = med(P, "Valor por hectárea (MXN/ha)")
PART_EDO = med(P, "Participación del estado %"); LUGAR_EDO = med(P, "Lugar del estado")
MUNI_PRIN = med(P, "Municipio principal"); EDO_NOMBRE = med(P, "Estado: nombre")
COLOR_MAPA = med(P, "Color del mapa")
EXP = med(C, "Exportaciones (USD)"); IMP = med(C, "Importaciones (USD)")
BAL = med(C, "Balanza comercial (USD)"); EUA = med(C, "Exportaciones a EE. UU. %")
PART_MX = med(M, "Participación de México %"); LUGAR = med(M, "Lugar de México")
PROD_MUNDO = med(M, "Producción mundial (t)")
T_RESUMEN = med(P, "Título resumen"); T_PROD = med(P, "Título producción")
T_EXP = med(P, "Título exportación"); T_MUNDO = med(P, "Título mundo")
T_CONTRASTE = med(P, "Título contraste"); T_ESTADO = med(P, "Título estado")
T_ESTADO_VALOR = med(P, "Título estado: valor")
A = "fact_avance"
AV = med(A, "Avance (t)"); AV_ANT = med(A, "Avance mismo corte año anterior (t)")
AV_VAR = med(A, "Var. avance %"); AV_HA = med(A, "Avance sembrada (ha)")
AV_HA_VAR = med(A, "Var. sembrada %"); T_AVANCE = med(A, "Título avance")
CORTE = col(A, "fecha_corte"); ESTADO_AV = col("dim_estado", "estado")
SIN_ARANDANO = filtro("sin_arandano", "dim_cultivo", "cultivo", ["Arándano"], excluir=True)
ANCHO = 850  # el título deja sitio a los segmentadores de la cabecera
TOOLTIP = "ptooltip"; FICHA = "pestado"


def anio(nombre, valores):
    return filtro(nombre, "dim_fecha", "anio", valores)


paginas = []

# 0. Inicio
p = Pagina("p0inicio", "Inicio",
           "Las berries de México frente a la papa, el tomate y el maíz",
           "Datos públicos del SIAP, DataMéxico y la FAO · elige un grupo o uno o varios cultivos: la selección viaja a las demás páginas")
p.segmentador("s_grupo", 32, 120, 560, 84, GRUPO, "Grupo", sincro="grupo", inicial=["Berries"])
p.segmentador("s_cultivo", 32, 216, 560, 314, CULTIVO, "Cultivo (Ctrl + clic para elegir varios)",
              horizontal=False, sincro="cultivo")
p.texto("lbl_sel", 624, 116, 624, 30, [("CON ESTA SELECCIÓN", 10, True, GRIS)])
p.titulo_medida("t_sel", 624, 136, 624, 92, T_RESUMEN, size=15, c=VERDE)
p.tarjeta("k_valor", 624, 232, 304, 112, VALOR, "Valor de la producción 2025 (MXN)", "1000000D", [anio("f", [2025])])
p.tarjeta("k_exp", 944, 232, 304, 112, EXP, "Exportaciones 2025 (USD)", "1000000D", [anio("f", [2025])])
p.tarjeta("k_prod", 624, 354, 304, 112, PROD, "Producción 2025 (t)", "1D", [anio("f", [2025])])
p.tarjeta("k_ha", 944, 354, 304, 112, HA, "Superficie cosechada 2025 (ha)", "1D", [anio("f", [2025])])
p.boton("b_sinaloa", 624, 478, 624, 52, "Ver la ficha de Sinaloa  →", destino=FICHA)
p.navegador("nav", 32, 546, 1216, 52)
p.texto("nota", 32, 612, 1216, 90, [
    ("Sinaloa es el 1.er productor nacional de tomate rojo y tomate verde, y el 2.º de arándano, papa y maíz grano (SIAP, 2025). "
     "En el mapa de la página Producción, clic derecho sobre un estado → Obtener detalles para ver su ficha.", 10, False, TINTA),
    ("Proyecto personal con datos públicos: SIAP/SADER, DataMéxico (Secretaría de Economía) y FAOSTAT (FAO, CC BY 4.0). "
     "Al elegir cultivos distintos (por ejemplo fresa y maíz) sus toneladas se suman tal cual: compara mejor de uno en uno o por grupo.",
     9, False, GRIS)])
paginas.append(p)

# 1. Resumen
p = Pagina("p1portada", "Resumen", T_RESUMEN,
           "Producción 2025 (SIAP) · exportaciones 2025 (DataMéxico) · pesos y dólares corrientes",
           ancho_titulo=ANCHO)
p.cabecera_cultivo()
p.tarjeta("k_valor", 32, 116, 290, 110, VALOR, "Valor de la producción 2025 (MXN)", "1000000D", [anio("f", [2025])])
p.tarjeta("k_prod", 337, 116, 290, 110, PROD, "Producción 2025 (t)", "1D", [anio("f", [2025])])
p.tarjeta("k_ha", 642, 116, 290, 110, HA, "Superficie cosechada 2025 (ha)", "1D", [anio("f", [2025])])
p.tarjeta("k_exp", 947, 116, 301, 110, EXP, "Exportaciones 2025 (USD)", "1000000D", [anio("f", [2025])])
p.grafico("g_valor", "columnChart", 32, 240, 600, 410, ANIO, VALOR,
          "Valor de la producción por año y cultivo (MXN corrientes)", serie=CULTIVO)
p.grafico("g_exp", "columnChart", 648, 240, 600, 410, ANIO, EXP,
          "Exportaciones por año y fracción (USD corrientes)", serie=GRUPO_COM,
          filtros=[anio("f", ANIOS_COM)])
p.texto("nota", 32, 662, 1216, 40, [(
    "Proyecto personal con datos públicos: SIAP/SADER, DataMéxico (Secretaría de Economía) y FAOSTAT (FAO, CC BY 4.0). "
    "Detalle de fuentes y licencias en la página «Fuentes».", 9, False, GRIS)])
paginas.append(p)

# 2. Producción: el mapa
p = Pagina("p2produccion", "Producción", T_PROD,
           "SIAP, cierre 2025 · pasa el cursor por un estado para ver su detalle; clic derecho → Obtener detalles abre su ficha",
           ancho_titulo=ANCHO)
p.cabecera_cultivo()
p.mapa("m_estados", 32, 116, 640, 580, ESTADO, PROD, "Producción 2025 por estado (t)",
       filtros=[anio("f", [2025])], tooltip=TOOLTIP)
p.grafico("g_estado", "clusteredBarChart", 688, 116, 560, 270, ESTADO, PROD,
          "Los estados que más producen, 2025 (t)", filtros=[anio("f", [2025])], orden_medida=True,
          etiquetas=True, unidades_etiqueta="1D", tooltip=TOOLTIP, relleno=COLOR_MAPA)
p.grafico("g_serie", "lineChart", 688, 398, 560, 298, ANIO, PROD, "Producción por año (t)", serie=CULTIVO)
paginas.append(p)

# 2b. Avance 2026: el año en curso, preliminar. Compara cada corte con el mismo día del año
# agrícola anterior, nunca con un año cerrado: medio año contra uno entero parece caída.
p = Pagina("p2avance", "2026 preliminar", T_AVANCE,
           "SIAP, avance mensual de siembras y cosechas · cifras PRELIMINARES, acumuladas al corte · elige la fecha de corte arriba a la derecha",
           ancho_titulo=ANCHO)
p.segmentador("s_corte", 900, 14, 348, 72, CORTE, "Fecha de corte", modo="Dropdown", unico=True,
              inicial=["datetime'2026-06-30T00:00:00'"])
p.tabla("t_avance", 32, 116, 760, 300,
        [(CULTIVO, "Cultivo"), (AV, "Acumulado al corte (t)"),
         (AV_ANT, "Mismo corte, año anterior (t)"), (AV_VAR, "Variación"),
         (AV_HA, "Sembrada (ha)"), (AV_HA_VAR, "Var. sembrada")],
        "Producción al corte contra el mismo corte del año agrícola anterior",
        filtros=[SIN_ARANDANO], orden=AV, totales=False)
p.grafico("g_var", "clusteredBarChart", 808, 116, 440, 300, CULTIVO, AV_VAR,
          "Variación contra el mismo corte del año anterior", filtros=[SIN_ARANDANO],
          orden_medida=True, etiquetas=True)
p.segmentador("s_cultivo_av", 32, 430, 300, 76, CULTIVO, "Cultivo de la gráfica de estados",
              modo="Dropdown", unico=True, inicial=["Fresa"])
p.texto("nota", 32, 518, 300, 178, [
    ("Cómo leerlo", 11, True, VERDE),
    ("Cifras preliminares: con el año agrícola 2025, el cierre del SIAP quedó entre 0 % y 7 % por encima del último avance.", 9, False, TINTA),
    ("El año agrícola va de octubre a marzo del año siguiente: las cifras se acumulan desde octubre (otoño-invierno) o enero (perennes).", 9, False, TINTA),
    ("El arándano no se publica en el avance: solo en el cierre anual.", 9, False, TINTA)])
p.grafico("g_estados", "clusteredBarChart", 348, 430, 900, 266, ESTADO_AV, AV,
          "Producción acumulada al corte por estado (t)", filtros=[SIN_ARANDANO],
          orden_medida=True, etiquetas=True, unidades_etiqueta="1D")
# El cultivo de la gráfica de estados no filtra la tabla ni la gráfica de variación, que
# enseñan los siete; y un clic en ellas no cambia la de estados, que manda el segmentador.
p.interacciones += [("s_cultivo_av", "t_avance", "NoFilter"), ("s_cultivo_av", "g_var", "NoFilter"),
                    ("t_avance", "g_estados", "NoFilter"), ("g_var", "g_estados", "NoFilter")]
paginas.append(p)

# 3. Exportación
p = Pagina("p3exportacion", "Exportación", T_EXP,
           "Dólares corrientes · DataMéxico (SE) · frambuesa y zarzamora comparten la fracción 0810.20 · el tomate verde no tiene fracción propia · 2026 con datos a julio",
           ancho_titulo=ANCHO)
p.cabecera_cultivo()
p.tarjeta("k_exp", 32, 116, 290, 100, EXP, "Exportaciones 2025 (USD)", "1000000D", [anio("f", [2025])])
p.tarjeta("k_eua", 337, 116, 290, 100, EUA, "A EE. UU. en 2025", "0D", [anio("f", [2025])])
p.tarjeta("k_imp", 642, 116, 290, 100, IMP, "Importaciones 2025 (USD)", "1000000D", [anio("f", [2025])])
p.tarjeta("k_bal", 947, 116, 301, 100, BAL, "Saldo comercial 2025 (USD)", "1000000D", [anio("f", [2025])])
p.grafico("g_anual", "columnChart", 32, 230, 760, 466, ANIO, EXP,
          "Exportaciones por año y fracción (USD)", serie=GRUPO_COM, filtros=[anio("f", ANIOS_COM)])
p.grafico("g_destino", "clusteredBarChart", 808, 230, 440, 466, PAIS_COM, EXP,
          "Fuera de EE. UU.: destinos en 2025 (USD)",
          filtros=[anio("f", [2025]), filtro("sin_eua", "dim_pais_comercio", "id_pais_iso3", ["USA"], excluir=True)],
          orden_medida=True, etiquetas=True)
paginas.append(p)

# 4. México en el mundo
p = Pagina("p4mundo", "México en el mundo", T_MUNDO,
           "Producción por país · FAOSTAT 2024 (CC BY 4.0) · la FAO no publica la zarzamora ni el tomate verde por separado",
           ancho_titulo=ANCHO)
p.cabecera_cultivo()
p.tabla("t_lugar", 32, 116, 560, 260,
        [(CULTIVO, "Cultivo"), (LUGAR, "Lugar de México"), (PART_MX, "% de la producción mundial"),
         (PROD_MUNDO, "Producción mundial (t)")],
        "México frente al mundo, 2024", filtros=[anio("f", [2024])], totales=False)
p.grafico("g_part", "lineChart", 608, 116, 640, 260, ANIO, PART_MX,
          "Participación de México en la producción mundial", serie=CULTIVO,
          filtros=[anio("f", ANIOS_MUNDO)])
p.grafico("g_paises", "clusteredBarChart", 32, 390, 1216, 306, col("dim_pais", "pais"), PROD_MUNDO,
          "Mayores productores, 2024 (t) · con varios cultivos elegidos suma sus toneladas",
          filtros=[anio("f", [2024])], orden_medida=True, etiquetas=True)
paginas.append(p)

# 5. Ficha del estado: destino del «Obtener detalles». Abre en Sinaloa; desde el mapa, en el
# estado elegido. No hereda el filtro de cultivo: la ficha muestra siempre los ocho.
F_ESTADO = filtro("f_estado", "dim_municipio", "estado", ["Sinaloa"], como="Drillthrough")
p = Pagina(FICHA, "Ficha del estado", T_ESTADO, T_ESTADO_VALOR, ancho_titulo=1060,
           filtros=[F_ESTADO],
           vinculo={"name": "dt_estado", "type": "Drillthrough",
                    "parameters": [{"name": "p_estado", "boundFilter": "f_estado", "fieldExpr": ESTADO}],
                    "acceptsFilterContext": "None"})
p.boton("b_volver", 1108, 30, 140, 40, "←  Volver", atras=True, relleno="#2F7D4A")
p.tarjeta("k_valor", 32, 116, 290, 104, VALOR, "Valor de la producción 2025 (MXN)", "1000000D", [anio("f", [2025])])
p.tarjeta("k_prod", 337, 116, 290, 104, PROD, "Producción 2025 (t)", "1D", [anio("f", [2025])])
p.tarjeta("k_ha", 642, 116, 290, 104, HA, "Superficie cosechada 2025 (ha)", "1D", [anio("f", [2025])])
p.tarjeta("k_muni", 947, 116, 301, 104, MUNI_PRIN, "Municipio que más produce, 2025", "0D", [anio("f", [2025])], size=16)
p.tabla("t_cultivos", 32, 234, 700, 236,
        [(CULTIVO, "Cultivo"), (PROD, "Producción (t)"), (PART_EDO, "% nacional"),
         (LUGAR_EDO, "Lugar nacional"), (REND, "Rendimiento (t/ha)"), (VALOR, "Valor (MXN)")],
        "Sus cultivos en 2025 frente al resto del país", filtros=[anio("f", [2025])], orden=VALOR,
        totales=False)
p.grafico("g_munis", "clusteredBarChart", 748, 234, 500, 462, MUNICIPIO, VALOR,
          "Municipios por valor de la producción, 2025 (MXN)", filtros=[anio("f", [2025])],
          orden_medida=True, etiquetas=True, unidades_etiqueta="1000000D")
p.grafico("g_serie", "lineChart", 32, 482, 700, 214, ANIO, PART_EDO,
          "Su parte de la producción nacional, por cultivo y año", serie=CULTIVO)
paginas.append(p)

# 6. Contraste: compara todos los cultivos, así que sus segmentadores no se sincronizan.
p = Pagina("p5contraste", "Berries frente a otros cultivos", T_CONTRASTE,
           "Valor de la producción por hectárea cosechada, 2025 (SIAP, pesos corrientes) y saldo comercial 2025 (DataMéxico, USD) · sin filtro se ven los ocho cultivos",
           ancho_titulo=ANCHO)
p.cabecera_cultivo(sincro=False)
p.grafico("g_vxha", "clusteredBarChart", 32, 116, 600, 356, CULTIVO, VXHA,
          "Valor por hectárea, 2025 (MXN/ha)", filtros=[anio("f", [2025])], orden_medida=True, etiquetas=True,
          unidades_etiqueta="1D")
p.grafico("g_bal", "clusteredBarChart", 648, 116, 600, 356, GRUPO_COM, BAL,
          "Saldo comercial 2025 (USD): exporta menos importa", filtros=[anio("f", [2025])],
          orden_medida=True, etiquetas=True)
p.tabla("t_cultivos", 32, 486, 1216, 210,
        [(GRUPO, "Grupo"), (CULTIVO, "Cultivo"), (HA, "Superficie cosechada (ha)"),
         (PROD, "Producción (t)"), (VALOR, "Valor (MXN)"), (VXHA, "Valor por ha (MXN)"),
         (REND, "Rendimiento (t/ha)")],
        "Los ocho cultivos en 2025", filtros=[anio("f", [2025])], orden=VXHA, totales=False)
paginas.append(p)

# 7. Fuentes
p = Pagina("p6fuentes", "Fuentes", "Fuentes, licencias y metodología",
           "Todo el tablero se reconstruye desde cero con «py scripts/run_all.py» en el repositorio público")
p.texto("fuentes", 32, 116, 1216, 580, [
    ("Fuentes", 13, True, VERDE),
    ("SIAP / SADER — Cierre de la producción agrícola, 2003-2025, por municipio. Datos abiertos del Gobierno de México; licencia por confirmar con el SIAP. https://nube.agricultura.gob.mx/datosAbiertos/Agricola.php", 10, False, TINTA),
    ("DataMéxico — Secretaría de Economía. Comercio exterior mensual por fracción arancelaria (HS6) y país, 2006 a julio de 2026, en USD. Licencia por confirmar. https://www.economia.gob.mx/datamexico/", 10, False, TINTA),
    ("FAOSTAT — FAO, Crops and livestock products (QCL), 1961-2024. Licencia CC BY 4.0. https://www.fao.org/faostat/", 10, False, TINTA),
    ("SIAP / SADER — Avance mensual de siembras y cosechas, por estado, de octubre de 2024 al último mes publicado. Preliminar; misma licencia que el cierre. https://nube.agricultura.gob.mx/avance_agricola/", 10, False, TINTA),
    ("Mapa de estados: el mapa de México incluido en el visual Shape map de Power BI.", 10, False, TINTA),
    ("", 6, False, TINTA),
    ("Metodología y advertencias", 13, True, VERDE),
    ("· Cifras en pesos y dólares corrientes, sin deflactar: los crecimientos de valor incluyen inflación.", 10, False, TINTA),
    ("· Rendimiento y precio medio rural se calculan como cocientes (producción/superficie, valor/producción), no como promedios de municipios.", 10, False, TINTA),
    ("· Se excluye la planta de vivero de fresa, que el SIAP publica en plantas bajo el mismo cultivo.", 10, False, TINTA),
    ("· El CSV abierto del SIAP de 2020 y 2021 no incluye el arándano; la FAO sí lo tiene. El hueco se declara, no se rellena.", 10, False, TINTA),
    ("· Comercio: frambuesa y zarzamora comparten la fracción 0810.20; el arándano (0810.40) incluye otros Vaccinium. El tomate verde no tiene fracción propia.", 10, False, TINTA),
    ("· FAO: «Tomatoes» de México suma jitomate y tomate verde; la FAO no separa la zarzamora.", 10, False, TINTA),
    ("· Avance 2026: acumulado al corte y preliminar; se compara con el mismo corte del año agrícola anterior. Contra el cierre 2025, el último avance quedó entre 0.1 % y 6.7 % abajo en producción. No incluye el arándano.", 10, False, TINTA),
    ("· Verificación: el SIAP cuadra con la FAO (diferencias menores al 3 %) y DataMéxico con sus propios totales anuales.", 10, False, TINTA),
    ("", 6, False, TINTA),
    ("Proyecto personal, sin relación con ninguna empresa. Datos públicos.", 10, False, GRIS),
])
paginas.append(p)

# Tooltip del mapa: página oculta de 320 × 240.
p = Pagina(TOOLTIP, "Tooltip estado", None, None, ancho=320, alto=240, oculta=True, banda=False,
           vinculo={"name": "tt_estado", "type": "Tooltip", "parameters": []})
p.forma("banda", 0, 0, 320, 44, BAYA)
p.titulo_medida("t_estado", 10, 2, 300, 40, EDO_NOMBRE, size=14)
p.tarjeta("k_prod", 8, 52, 148, 84, PROD, "Producción (t)", "1D", [anio("f", [2025])], size=16)
p.tarjeta("k_part", 164, 52, 148, 84, PART_EDO, "% del país", "0D", [anio("f", [2025])], size=16)
p.tarjeta("k_lugar", 8, 144, 148, 88, LUGAR_EDO, "Lugar nacional", "0D", [anio("f", [2025])], size=16)
p.tarjeta("k_muni", 164, 144, 148, 88, MUNI_PRIN, "Municipio principal", "0D", [anio("f", [2025])], size=11)
paginas.append(p)


def registrar_recursos():
    """Tema propio en RegisteredResources y el mapa de México en SharedResources."""
    rr = REPORT / "StaticResources" / "RegisteredResources"
    rr.mkdir(parents=True, exist_ok=True)
    (rr / "BerriesMexico.json").write_text(json.dumps(tema(), indent=2, ensure_ascii=False), encoding="utf-8")
    sm = REPORT / "StaticResources" / "SharedResources" / "Shapemaps"
    sm.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MAPA_DESKTOP, sm / "mexico.states.topo.json")

    rj = REPORT / "definition" / "report.json"
    r = json.loads(rj.read_text(encoding="utf-8"))
    base = r["themeCollection"]["baseTheme"]
    r["themeCollection"]["customTheme"] = {"name": "BerriesMexico.json",
                                           "reportVersionAtImport": base["reportVersionAtImport"],
                                           "type": "RegisteredResources"}
    paquetes = {p["name"]: p for p in r["resourcePackages"]}
    compartidos = paquetes["SharedResources"]["items"]
    if not any(i["type"] == "ShapeMap" for i in compartidos):
        compartidos.append({"name": "mexico.states.topo", "path": "Shapemaps/mexico.states.topo.json",
                            "type": "ShapeMap"})
    if "RegisteredResources" not in paquetes:
        r["resourcePackages"].append({"name": "RegisteredResources", "type": "RegisteredResources",
                                      "items": [{"name": "BerriesMexico.json", "path": "BerriesMexico.json",
                                                 "type": "CustomTheme"}]})
    rj.write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")


registrar_recursos()
if PAGES.exists():
    shutil.rmtree(PAGES)
PAGES.mkdir(parents=True)
for p in paginas:
    p.escribir()
(PAGES / "pages.json").write_text(json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
    "pageOrder": [p.nombre for p in paginas],
    "activePageName": os.environ.get("PAGINA_ACTIVA", paginas[0].nombre)}, indent=2),
    encoding="utf-8")
print("páginas:", [p.nombre for p in paginas], "visuales:", sum(len(p.visuales) for p in paginas))
