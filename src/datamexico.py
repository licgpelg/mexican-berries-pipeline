"""DataMéxico (Secretaría de Economía): comercio exterior mensual de México por HS6 y país.

Origen: https://www.economia.gob.mx/datamexico/ · API tesseract, sin clave.
Solo trae valor en USD, sin volumen.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date

import pandas as pd

from .comun import BRONZE, sesion
from .cultivos import codigos_hs6

BASE = "https://www.economia.gob.mx/apidatamexico/tesseract/data.jsonrecords"
CUBO = "economy_foreign_trade_nat"
PRIMER_ANIO = 2006  # primer año del cubo (consultado el 2026-10-13)
# El cubo antepone un dígito al código del SA: 0810.10 es 2081010 y 1005.90 es 2100590.
HS6 = ["2" + c for c in codigos_hs6()]
# La caché de cada año lleva la firma de las fracciones pedidas: al añadir un cultivo,
# los años cerrados se vuelven a pedir en vez de quedarse con las fracciones viejas.
FIRMA = hashlib.sha1(",".join(HS6).encode()).hexdigest()[:8]
FLUJOS = {1: "Importación", 2: "Exportación"}


def _datos(r) -> list:
    """Una fracción inexistente no da error HTTP: responde 200 con el texto «Cut member not
    found» en lugar del JSON (visto el 2026-10-13)."""
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or "data" not in j:
        raise RuntimeError(f"DataMéxico respondió sin datos: {str(j)[:200]}")
    return j["data"]


def extraer(ultimo_anio: int | None = None, forzar: bool = False) -> list:
    """Un JSON por año en Bronze. Se vuelven a pedir los dos últimos años: la SE revisa
    las cifras recientes y el año en curso crece cada mes."""
    ultimo_anio = ultimo_anio or date.today().year
    s = sesion()
    rutas = []
    for anio in range(PRIMER_ANIO, ultimo_anio + 1):
        destino = BRONZE / "datamexico" / f"comercio_{anio}_{FIRMA}.json"
        if forzar or not destino.exists() or anio >= ultimo_anio - 1:
            # El servidor tarda 20-60 s por consulta y a ratos da 5xx (2026-10-13).
            r = s.get(BASE, timeout=600, params={
                "cube": CUBO, "drilldowns": "Month,HS6,Flow,Continent,Country",
                "measures": "Trade Value", "HS6": ",".join(HS6), "Year": str(anio)})
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(json.dumps(_datos(r), ensure_ascii=False), encoding="utf-8")
        rutas.append(destino)
    return rutas


def leer(rutas) -> pd.DataFrame:
    filas = []
    for ruta in rutas:
        filas += json.loads(ruta.read_text(encoding="utf-8"))
    return pd.DataFrame(filas)


def transformar(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    fact = pd.DataFrame({
        "mes": pd.to_datetime(df["Month"] + "-01").dt.date,
        "hs6": df["HS6 ID"].astype(str).str[1:],
        "id_flujo": df["Flow ID"],
        "id_pais_iso3": df["Country ID"].str.upper(),
        "valor_usd": df["Trade Value"],
    }).sort_values(["mes", "hs6", "id_flujo", "id_pais_iso3"])
    pais = (df[["Country ID", "Country", "Continent"]].drop_duplicates("Country ID")
              .assign(id_pais_iso3=lambda d: d["Country ID"].str.upper())
              .rename(columns={"Country": "pais_en", "Continent": "continente_en"})
              [["id_pais_iso3", "pais_en", "continente_en"]].sort_values("id_pais_iso3"))
    flujo = pd.DataFrame(list(FLUJOS.items()), columns=["id_flujo", "flujo"])
    return {"fact_comercio": fact, "dim_pais_comercio": pais, "dim_flujo": flujo}


def totales_anuales(anios) -> pd.DataFrame:
    """Total por año, HS6 y flujo pedido al cubo sin desglose por país ni mes: sirve para
    comprobar que la suma de los meses y países de Bronze no pierde ni duplica nada."""
    r = sesion().get(BASE, timeout=600, params={
        "cube": CUBO, "drilldowns": "Year,HS6,Flow", "measures": "Trade Value",
        "HS6": ",".join(HS6), "Year": ",".join(str(a) for a in anios)})
    d = pd.DataFrame(_datos(r))
    return pd.DataFrame({"anio": d["Year"], "hs6": d["HS6 ID"].astype(str).str[1:],
                         "id_flujo": d["Flow ID"], "valor_usd": d["Trade Value"]})
