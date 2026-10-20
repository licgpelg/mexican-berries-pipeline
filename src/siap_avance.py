"""SIAP/SADER, Avance mensual de siembras y cosechas (por estado, preliminar).

Origen: https://nube.agricultura.gob.mx/avance_agricola/

El cierre anual (siap.py) solo llega al último año cerrado. El avance da el año en curso
acumulado al último día de cada mes, y por eso es preliminar: el SIAP lo revisa hasta el
cierre. La página no tiene descarga directa: el formulario llama por xajax (POST) a la
función `reporte`, que devuelve la tabla en HTML dentro de un XML.
"""
from __future__ import annotations

import html
import re
import time
import unicodedata
from pathlib import Path

import pandas as pd

from .comun import BRONZE, sesion

URL = "https://nube.agricultura.gob.mx/avance_agricola/"

# Id de cultivo y de unidad «Tonelada» del avance (no son los Idcultivo del cierre),
# leídos de llenaCultivo y llenaUnidMed el 2026-10-19. El avance cubre 65 cultivos y no
# trae el arándano: para él solo hay cierre anual.
CULTIVOS_AVANCE = {
    # id_cultivo del proyecto: (id en el avance, nombre que debe venir en el título)
    1: (150, "Fresa"),
    2: (149, "Frambuesa"),
    3: (420, "Zarzamora"),
    5: (283, "Papa"),
    6: (389, "Tomate rojo (jitomate)"),
    7: (390, "Tomate verde"),
    8: (225, "Maíz grano"),
}
UNIDAD = "Tonelada"
# Parámetros fijos de la consulta: reporte por entidad (tipo 1, opción 2), ciclo 5
# «Cíclicos - Perennes» (el año agrícola completo: OI + PV + perennes) y modalidad 3
# «Riego + Temporal».
TIPO, CICLO, MODALIDAD, POR_ENTIDAD = 1, 5, 3, 2
PAUSA_S = 0.5  # entre llamadas: el servidor es del gobierno y nadie nos paga la carga

# Claves de entidad del INEGI. El avance da el nombre, no la clave.
ESTADOS = {
    "aguascalientes": 1, "baja california": 2, "baja california sur": 3, "campeche": 4,
    "coahuila": 5, "colima": 6, "chiapas": 7, "chihuahua": 8, "ciudad de mexico": 9,
    "durango": 10, "guanajuato": 11, "guerrero": 12, "hidalgo": 13, "jalisco": 14,
    "mexico": 15, "michoacan": 16, "morelos": 17, "nayarit": 18, "nuevo leon": 19,
    "oaxaca": 20, "puebla": 21, "queretaro": 22, "quintana roo": 23,
    "san luis potosi": 24, "sinaloa": 25, "sonora": 26, "tabasco": 27, "tamaulipas": 28,
    "tlaxcala": 29, "veracruz": 30, "yucatan": 31, "zacatecas": 32,
}


def _llave(nombre: str) -> str:
    n = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", n).strip()


class _Cliente:
    def __init__(self):
        self.s = sesion()
        self.s.get(URL, timeout=60)  # abre la sesión PHP que usan las llamadas

    def llamar(self, funcion: str, *args) -> str:
        datos = [("xajax", funcion), ("xajaxr", "1")] + [("xajaxargs[]", str(a)) for a in args]
        for intento in range(4):
            try:
                r = self.s.post(URL, data=datos, timeout=180)
                r.raise_for_status()
                r.encoding = "latin1"
                time.sleep(PAUSA_S)
                return r.text
            except Exception:
                if intento == 3:
                    raise
                time.sleep(10 * (intento + 1))

    def opciones(self, funcion: str, *args) -> dict[str, str]:
        t = self.llamar(funcion, *args)
        return {v: html.unescape(txt).strip()
                for v, txt in re.findall(r'<option value="([^"]*)"[^>]*>([^<]*)', t)}


def extraer(anios_agricolas: list[int], forzar_ultimo: bool = False) -> list[Path]:
    """Baja a Bronze un XML por mes de corte y cultivo. El año agrícola N empieza en
    octubre de N-1, así que se piden también octubre a diciembre del año anterior al
    primero. Solo se vuelve a bajar el último año: es el que el SIAP sigue revisando."""
    c = _Cliente()
    rutas = []
    primero, ultimo = min(anios_agricolas), max(anios_agricolas)
    for anio in range(primero - 1, ultimo + 1):
        meses = sorted(int(m) for m in c.opciones("llenaMes", anio))
        if anio == primero - 1:
            meses = [m for m in meses if m >= 10]
        for mes in meses:
            for id_cultivo, (id_av, _) in CULTIVOS_AVANCE.items():
                destino = BRONZE / "siap_avance" / f"avance_{anio}_{mes:02d}_{id_cultivo}.xml"
                if destino.exists() and not (forzar_ultimo and anio == ultimo):
                    rutas.append(destino)
                    continue
                unidades = {txt: v for v, txt in c.opciones("llenaUnidMed", id_av).items()}
                if UNIDAD not in unidades:
                    raise RuntimeError(f"Avance: el cultivo {id_av} no tiene unidad {UNIDAD}")
                t = c.llamar("reporte", TIPO, anio, CICLO, MODALIDAD, 0, "--", "--", id_av,
                             unidades[UNIDAD], "--", POR_ENTIDAD, 0, 0, 0, mes)
                destino.parent.mkdir(parents=True, exist_ok=True)
                tmp = destino.with_suffix(".part")
                tmp.write_text(t, encoding="utf-8")
                tmp.replace(destino)
                rutas.append(destino)
    return rutas


def _numero(celda: str) -> float:
    return float(celda.replace(",", ""))


MESES = {m: i for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
     "septiembre", "octubre", "noviembre", "diciembre"], start=1)}


def leer(rutas, anios_agricolas: set[int]) -> pd.DataFrame:
    """Una respuesta puede traer DOS tablas, una por año agrícola: el año agrícola N va
    de octubre de N-1 (siembras de otoño-invierno) a marzo de N+1, así que de octubre a
    marzo conviven dos (comprobado el 2026-10-19). Cada tabla dice su año agrícola y su
    fecha de corte; se guardan solo los años pedidos, porque de los otros falta el
    principio de la serie."""
    filas = []
    for ruta in rutas:
        _, _, _, id_cultivo = ruta.stem.split("_")
        id_cultivo = int(id_cultivo)
        _, nombre = CULTIVOS_AVANCE[id_cultivo]
        t = html.unescape(ruta.read_text(encoding="utf-8"))
        # El SIAP deja en comentarios el precio y el valor de la producción: no los publica
        # en su página y aquí tampoco se usan.
        t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
        bloques = re.findall(r'class="titulosTabla">(.*?)</table>', t, flags=re.S)
        if not bloques:
            raise RuntimeError(f"{ruta.name}: la respuesta no trae ninguna tabla")
        for b in bloques:
            anio_agr = int(re.search(r"A.o agr.cola:</strong>\s*(\d{4})", b).group(1))
            titulo = re.search(r"Cultivo:</strong>\s*(.+?)\s*\(", b).group(1).strip()
            # El título corta en el primer paréntesis: «Tomate rojo (jitomate) (ton)».
            if titulo != nombre.split(" (")[0]:
                raise RuntimeError(f"{ruta.name}: se esperaba «{nombre}» y llegó «{titulo}»")
            d, m, a = re.search(r"Situaci.n al (\d+) de (\w+) de (\d{4})", b).groups()
            corte = pd.Timestamp(int(a), MESES[m.lower()], int(d)).date()
            if anio_agr not in anios_agricolas:
                continue
            propias, total = [], None
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", b, flags=re.S):
                celdas = [re.sub(r"<[^>]+>", "", x).strip()
                          for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S)]
                if len(celdas) == 6 and celdas[0] == "Total":
                    total = _numero(celdas[4])
                elif len(celdas) == 7 and celdas[0].isdigit():
                    llave = _llave(celdas[1])
                    if llave not in ESTADOS:
                        raise RuntimeError(f"{ruta.name}: estado desconocido «{celdas[1]}»")
                    propias.append((corte, anio_agr, id_cultivo, ESTADOS[llave],
                                    *[_numero(x) for x in celdas[2:6]]))
            if total is None:
                raise RuntimeError(f"{ruta.name}: tabla {anio_agr} sin fila Total")
            if abs(sum(f[7] for f in propias) - total) > 1:
                raise RuntimeError(f"{ruta.name}: tabla {anio_agr}, la suma de estados "
                                   f"no da el total ({total:,.2f} t)")
            filas += propias
    df = pd.DataFrame(filas, columns=[
        "fecha_corte", "anio_agricola", "id_cultivo", "id_estado", "superficie_sembrada_ha",
        "superficie_cosechada_ha", "superficie_siniestrada_ha", "produccion_t"])
    dup = df.duplicated(["fecha_corte", "anio_agricola", "id_cultivo", "id_estado"])
    if dup.any():
        raise RuntimeError(f"Avance: {dup.sum()} filas repetidas")
    return df


def transformar(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {"fact_avance": df.sort_values(["fecha_corte", "anio_agricola", "id_cultivo",
                                           "id_estado"]).reset_index(drop=True)}
