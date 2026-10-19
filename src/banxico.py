"""Banxico SIE: tipo de cambio FIX (serie SF43718), pesos por dólar, diario hábil.

Origen: https://www.banxico.org.mx/SieAPIRest/ · token gratuito en la cabecera Bmx-Token.
"""
from __future__ import annotations

import json
import os
from datetime import date

import pandas as pd

from .comun import BRONZE, cargar_env, sesion

SERIE = "SF43718"
URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos/{ini}/{fin}"
DESDE = date(2003, 1, 1)  # el primer año del SIAP


def extraer() -> object:
    cargar_env()
    token = os.environ.get("BANXICO_SIE_TOKEN")
    if not token:
        raise RuntimeError("Falta BANXICO_SIE_TOKEN en .env (se pide gratis en el portal "
                           "del SIE de Banxico).")
    r = sesion().get(URL.format(serie=SERIE, ini=DESDE.isoformat(), fin=date.today().isoformat()),
                     headers={"Bmx-Token": token}, timeout=120)
    r.raise_for_status()
    destino = BRONZE / "banxico" / f"{SERIE}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(r.text, encoding="utf-8")
    return destino


def leer(ruta) -> pd.DataFrame:
    datos = json.loads(ruta.read_text(encoding="utf-8"))["bmx"]["series"][0]["datos"]
    return pd.DataFrame(datos)


def transformar(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    # Los días sin publicación vienen como «N/E»: se quitan, no se rellenan; el promedio
    # mensual se calcula en DAX con los días que sí hay.
    fact = pd.DataFrame({
        "fecha": pd.to_datetime(df["fecha"], format="%d/%m/%Y").dt.date,
        "tipo_cambio_fix": pd.to_numeric(df["dato"].str.replace(",", ""), errors="coerce"),
    }).dropna().sort_values("fecha")
    return {"fact_tipo_cambio": fact}
