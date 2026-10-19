"""dim_fecha: un día por fila, de 1961 (primer año de FAOSTAT) al 31-dic del año en curso."""
from __future__ import annotations

from datetime import date

import pandas as pd

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def dim_fecha(desde: int = 1961, hasta: int | None = None) -> pd.DataFrame:
    hasta = hasta or date.today().year
    f = pd.date_range(f"{desde}-01-01", f"{hasta}-12-31", freq="D")
    return pd.DataFrame({
        "fecha": f.date,
        "anio": f.year,
        "trimestre": f.quarter,
        "mes": f.month,
        "nombre_mes": [MESES[m - 1] for m in f.month],
        "mes_corto": [MESES[m - 1][:3] for m in f.month],
        "inicio_mes": f.to_period("M").to_timestamp().date,
    })


def primero_de_anio(anios: pd.Series) -> pd.Series:
    """Los hechos anuales (SIAP, FAOSTAT) se relacionan con dim_fecha por el 1 de enero."""
    return pd.to_datetime(anios.astype(str) + "-01-01").dt.date
