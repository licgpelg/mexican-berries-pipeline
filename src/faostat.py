"""FAOSTAT QCL (Crops and livestock products), producción por país y año desde 1961.

Origen: https://www.fao.org/faostat/en/#data/QCL · Licencia CC BY 4.0.
"""
from __future__ import annotations

import zipfile

import pandas as pd

from .comun import BRONZE, descargar
from .fechas import primero_de_anio
from .cultivos import CULTIVOS

URL = ("https://bulks-faostat.fao.org/production/"
       "Production_Crops_Livestock_E_All_Data_(Normalized).zip")
DATOS = "Production_Crops_Livestock_E_All_Data_(Normalized).csv"
AREAS = "Production_Crops_Livestock_E_AreaCodes.csv"

# Element Code verificados en el ZIP del 2026-10-13: 5312 superficie cosechada (ha),
# 5510 producción (t). El rendimiento no se guarda: se calcula en DAX.
ELEMENTOS = {5312: "superficie_cosechada_ha", 5510: "produccion_t"}
# Los agregados (World, Americas, Least Developed…) llevan Area Code >= 5000; se quitan
# para que sumar países no cuente dos veces.
PRIMER_AGREGADO = 5000
# «China» (351) también va por debajo de 5000 y es la suma de China continental (41),
# Taiwán (214), Hong Kong (96) y Macao (128), que vienen además por separado. Con ella,
# China contaba dos veces: inflaba el total mundial y bajaba un lugar a México en el
# ranking (visto en el informe el 2026-10-13).
AREAS_DUPLICADAS = {351}


def extraer(forzar: bool = False):
    return descargar(URL, BRONZE / "faostat" / "qcl_normalized.zip", forzar=forzar, timeout=900)


def leer(ruta) -> pd.DataFrame:
    items = {c[6]: c[0] for c in CULTIVOS if c[6]}
    z = zipfile.ZipFile(ruta)
    partes = []
    # 545 MB descomprimido: se lee por trozos y se filtra al vuelo.
    # Los CSV del ZIP vienen en UTF-8: leídos como latin1, «Türkiye» salía «TÃ¼rkiye».
    for trozo in pd.read_csv(z.open(DATOS), encoding="utf-8", chunksize=500_000,
                             usecols=["Area Code", "Area Code (M49)", "Item", "Element Code",
                                      "Year", "Unit", "Value", "Flag"]):
        partes.append(trozo[trozo["Item"].isin(items)
                            & trozo["Element Code"].isin(ELEMENTOS)
                            & (trozo["Area Code"] < PRIMER_AGREGADO)
                            & ~trozo["Area Code"].isin(AREAS_DUPLICADAS)])
    df = pd.concat(partes, ignore_index=True)
    df["id_cultivo"] = df["Item"].map(items)
    areas = pd.read_csv(z.open(AREAS), encoding="utf-8")
    return df, areas


def transformar(df: pd.DataFrame, areas: pd.DataFrame) -> dict[str, pd.DataFrame]:
    df = df.assign(m49=df["Area Code (M49)"].str.lstrip("'"),
                   medida=df["Element Code"].map(ELEMENTOS))
    fact = (df.pivot_table(index=["Year", "m49", "id_cultivo"], columns="medida",
                           values="Value", aggfunc="sum")
              .reset_index().rename(columns={"Year": "anio"}))
    # La marca de la producción (A oficial, E estimada, I imputada…) se conserva: en el
    # informe no es lo mismo una cifra oficial que una que la FAO estimó.
    marca = (df[df["Element Code"] == 5510]
             .rename(columns={"Year": "anio", "Flag": "marca_produccion"})
             [["anio", "m49", "id_cultivo", "marca_produccion"]])
    fact = fact.merge(marca, on=["anio", "m49", "id_cultivo"], how="left")
    fact = fact[["anio", "m49", "id_cultivo", "superficie_cosechada_ha", "produccion_t",
                 "marca_produccion"]].sort_values(["anio", "m49", "id_cultivo"])
    fact.insert(1, "fecha", primero_de_anio(fact["anio"]))
    pais = (areas[(areas["Area Code"] < PRIMER_AGREGADO)
                  & ~areas["Area Code"].isin(AREAS_DUPLICADAS)]
            .assign(m49=lambda a: a["M49 Code"].str.lstrip("'"))
            .rename(columns={"Area": "pais"})[["m49", "pais"]]
            .loc[lambda a: a["m49"].isin(fact["m49"])]
            .sort_values("pais"))
    return {"fact_produccion_mundial": fact, "dim_pais": pais}
