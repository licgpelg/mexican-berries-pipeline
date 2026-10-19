"""dim_cultivo: la tabla que conforma las fuentes (SIAP, HS6 de comercio exterior y FAO)."""
from __future__ import annotations

import pandas as pd

# Idcultivo del SIAP, verificados en los cierres 2003-2025 (2026-10-13).
# HS6 0810.20 junta frambuesa y zarzamora; 0810.40 incluye otros Vaccinium.
# Papa, maíz y tomate entran como cultivos de referencia frente a las berries:
# - Maíz es «Maíz grano». El forrajero (en verde, seco, achicalado) es otro producto,
#   medido en forraje: 16.8 millones de t en 2024.
# - En papa y maíz, la fracción sin semilla (0701.90 y 1005.90); la semilla es otro mercado.
# - El tomate verde (tomatillo) no tiene fracción propia a 6 dígitos ni partida en la FAO:
#   solo entra con datos del SIAP. Y la partida «Tomatoes» de la FAO, para México, es
#   jitomate + tomate verde (coinciden al entero en 2003-2024): en el mundo, «Tomate rojo»
#   de México lleva dentro el tomatillo.
CULTIVOS = [
    # id, cultivo, en inglés, Idcultivo SIAP, HS6, grupo comercio, item FAO, grupo
    (1, "Fresa", "Strawberry", 6820000, "081010", "Fresa", "Strawberries", "Berries"),
    (2, "Frambuesa", "Raspberry", 6810000, "081020", "Frambuesa y zarzamora",
     "Raspberries", "Berries"),
    (3, "Zarzamora", "Blackberry", 9310000, "081020", "Frambuesa y zarzamora", None, "Berries"),
    (4, "Arándano", "Blueberry", 5650000, "081040", "Arándano", "Blueberries", "Berries"),
    (5, "Papa", "Potato", 8100000, "070190", "Papa", "Potatoes", "Hortalizas"),
    (6, "Tomate rojo", "Tomato", 8970000, "070200", "Tomate", "Tomatoes", "Hortalizas"),
    (7, "Tomate verde", "Tomatillo", 8980000, None, None, None, "Hortalizas"),
    (8, "Maíz grano", "Maize", 7490000, "100590", "Maíz", "Maize (corn)", "Granos"),
]

COLUMNAS = ["id_cultivo", "cultivo", "cultivo_en", "id_siap", "hs6", "grupo_comercio",
            "item_fao", "grupo"]


def dim_cultivo() -> pd.DataFrame:
    return pd.DataFrame(CULTIVOS, columns=COLUMNAS)


def por_siap() -> dict[int, int]:
    return {c[3]: c[0] for c in CULTIVOS}


def codigos_hs6() -> list[str]:
    return sorted({c[4] for c in CULTIVOS if c[4]})


def dim_hs6() -> pd.DataFrame:
    """Dimensión de fact_comercio. No puede ser dim_cultivo: 0810.20 es a la vez frambuesa
    y zarzamora, y la relación necesita un lado «uno» sin repetidos."""
    return (pd.DataFrame(CULTIVOS, columns=COLUMNAS)[["hs6", "grupo_comercio", "grupo"]]
              .dropna(subset=["hs6"]).drop_duplicates("hs6").sort_values("hs6"))
