"""SIAP/SADER, Cierre de la producción agrícola (municipal, anual desde 2003).

Origen: https://nube.agricultura.gob.mx/datosAbiertos/Agricola.php
"""
from __future__ import annotations

import pandas as pd

from .comun import BRONZE, descargar, sesion
from .fechas import primero_de_anio
from .cultivos import por_siap

# La ruta va colgando de la raíz del sitio; con /datosAbiertos/ en medio devuelve una
# página HTML en vez del CSV (comprobado el 2026-10-13).
URL = "https://nube.agricultura.gob.mx/index.php?view=10AE434F-A2158368-A120BC5A-EDF4AFAA&ANIO={anio}"
PRIMER_ANIO = 2003

COLUMNAS = ["Anio", "Idestado", "Nomestado", "Idddr", "Nomddr", "Idcader", "Nomcader",
            "Idmunicipio", "Nommunicipio", "Idciclo", "Nomcicloproductivo", "Idmodalidad",
            "Nommodalidad", "Idunidadmedida", "Nomunidad", "Idcultivo", "Nomcultivo",
            "Sembrada", "Cosechada", "Siniestrada", "Volumenproduccion", "Rendimiento",
            "Preciomediorural", "Valorproduccion"]

# Encabezados de los años viejos (revisados el 2026-10-13): 2003-2020 llaman «Precio» al
# precio medio rural y 2015-2020 llaman «Nomcultivo Sin Um» al cultivo.
RENOMBRES = {"Precio": "Preciomediorural", "Nomcultivo Sin Um": "Nomcultivo"}
NUMERICAS = ["Sembrada", "Cosechada", "Siniestrada", "Volumenproduccion",
             "Preciomediorural", "Valorproduccion"]
# 2019-2025 traen la planta de vivero de fresa bajo el mismo Idcultivo, medida en
# plantas y no en toneladas (antes tenía su propio id, 6830000). Sumarla con la fruta
# pone la fresa de 2025 en 61.6 millones «de producción» en vez de 641 897 t.
UNIDAD = "Tonelada"


def extraer(ultimo_anio: int, forzar_ultimo: bool = False) -> list:
    """Baja los CSV anuales a Bronze. Solo se vuelve a bajar el último año, que es el que
    el SIAP puede corregir; los cerrados no cambian."""
    s = sesion()
    rutas = []
    for anio in range(PRIMER_ANIO, ultimo_anio + 1):
        destino = BRONZE / "siap" / f"siap_cierre_{anio}.csv"
        descargar(URL.format(anio=anio), destino, s=s,
                  forzar=forzar_ultimo and anio == ultimo_anio)
        with open(destino, "rb") as f:
            if f.read(15).lstrip().lower().startswith(b"<!doctype"):
                raise RuntimeError(f"SIAP {anio}: llegó HTML en vez de CSV ({destino})")
        rutas.append(destino)
    return rutas


def leer(rutas) -> pd.DataFrame:
    mapa = por_siap()
    partes = []
    for ruta in rutas:
        df = pd.read_csv(ruta, encoding="latin1", dtype=str).rename(columns=RENOMBRES)
        faltan = set(COLUMNAS) - set(df.columns)
        if faltan:
            raise RuntimeError(f"{ruta.name}: faltan columnas {sorted(faltan)}")
        partes.append(df.loc[df["Idcultivo"].astype(int).isin(mapa), COLUMNAS])
    df = pd.concat(partes, ignore_index=True)
    # Se lee todo como texto: 2021 y 2022 traen separador de miles en algunas cifras.
    for c in NUMERICAS:
        df[c] = pd.to_numeric(df[c].str.replace(",", "", regex=False))
    for c in ["Anio", "Idestado", "Idmunicipio", "Idciclo", "Idmodalidad", "Idcultivo"]:
        df[c] = df[c].astype(int)
    otra_unidad = df["Nomunidad"] != UNIDAD
    if otra_unidad.any():
        print(f"SIAP: se excluyen {otra_unidad.sum()} filas en "
              f"{sorted(df.loc[otra_unidad, 'Nomunidad'].unique())} (vivero, no fruta)")
    df = df.loc[~otra_unidad].copy()
    df["id_cultivo"] = df["Idcultivo"].map(mapa)
    return df


def transformar(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    # Clave de municipio como la del INEGI (2 dígitos de estado + 3 de municipio),
    # para poder pintar el mapa con cualquier capa estándar.
    df = df.assign(cve_mun=df["Idestado"].astype(str).str.zfill(2)
                   + df["Idmunicipio"].astype(str).str.zfill(3))
    fact = df.rename(columns={
        "Anio": "anio", "Idestado": "id_estado", "Idciclo": "id_ciclo",
        "Idmodalidad": "id_modalidad", "Volumenproduccion": "produccion_t",
        "Sembrada": "superficie_sembrada_ha", "Cosechada": "superficie_cosechada_ha",
        "Siniestrada": "superficie_siniestrada_ha",
        "Preciomediorural": "precio_medio_rural_mxn", "Valorproduccion": "valor_produccion_mxn",
    })[["anio", "cve_mun", "id_estado", "id_cultivo", "id_ciclo", "id_modalidad",
        "superficie_sembrada_ha", "superficie_cosechada_ha", "superficie_siniestrada_ha",
        "produccion_t", "precio_medio_rural_mxn", "valor_produccion_mxn"]]
    fact.insert(1, "fecha", primero_de_anio(fact["anio"]))
    # El rendimiento no se guarda: es producción / cosechada y se calcula en DAX, porque un
    # promedio de rendimientos municipales no es el rendimiento del estado.

    # Los nombres pueden cambiar de un año a otro (acentos, fusiones): manda el más reciente.
    geo = (df.sort_values("Anio")
             .drop_duplicates("cve_mun", keep="last")
             [["cve_mun", "Idestado", "Nomestado", "Nommunicipio", "Nomddr"]]
             .rename(columns={"Idestado": "id_estado", "Nomestado": "estado",
                              "Nommunicipio": "municipio", "Nomddr": "ddr"})
             .sort_values("cve_mun"))
    # El SIAP llama «México» al estado; el mapa de formas de Power BI lo reconoce como «Estado
    # de México» (los otros 31 nombres coinciden, comprobado el 2026-10-13), y así no se
    # confunde con el país.
    geo["estado"] = geo["estado"].replace({"México": "Estado de México"})
    ciclo = (df[["Idciclo", "Nomcicloproductivo"]].drop_duplicates("Idciclo")
               .rename(columns={"Idciclo": "id_ciclo", "Nomcicloproductivo": "ciclo"}))
    modalidad = (df[["Idmodalidad", "Nommodalidad"]].drop_duplicates("Idmodalidad")
                   .rename(columns={"Idmodalidad": "id_modalidad", "Nommodalidad": "modalidad"}))
    return {"fact_produccion": fact, "dim_municipio": geo,
            "dim_ciclo": ciclo.sort_values("id_ciclo"),
            "dim_modalidad": modalidad.sort_values("id_modalidad")}
