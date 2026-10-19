"""Reconstruye data/gold/ desde cero y verifica cada fuente contra otra independiente.

    py scripts/run_all.py [--sin-banxico] [--forzar]

Salida: 0 todo bien · 1 una fuente no se pudo bajar · 2 los datos están pero un cuadre
falla.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from src import banxico, datamexico, faostat, siap  # noqa: E402
from src.comun import escribir_gold  # noqa: E402
from src.cultivos import dim_cultivo, dim_hs6  # noqa: E402
from src.fechas import dim_fecha  # noqa: E402

# Tolerancia del cruce SIAP contra FAOSTAT. Medido el 2026-10-13: la FAO toma las cifras
# del SIAP y coinciden al entero salvo revisiones puntuales (fresa 2003: 150 261 contra
# 146 009 t, un 2.9 %). Más del 5 % ya no es una revisión: es un dato mal leído.
TOLERANCIA_FAO = 0.05
# Años que el CSV abierto del SIAP publica con ~80 cultivos en vez de ~300 y sin arándano
# (la FAO sí los tiene como cifra oficial). Hueco del origen: se declara, no se rellena.
HUECOS_SIAP = {(2020, 4), (2021, 4)}
# Diferencias del propio cubo de DataMéxico, comprobadas una a una (2026-10-13): en mayo
# de 2008 hay 78 578 USD de exportación de fresa sin país, que se pierden al desglosar
# por país. Se aceptan solo con esta cifra exacta; cualquier otra diferencia es roja.
DIFERENCIAS_DATAMEXICO = {(2008, "081010", 2): 78_578}


# «Tomatoes» de la FAO, para México, es jitomate + tomate verde del SIAP: coinciden al
# entero en 2003-2024 (comprobado el 2026-10-13). Se cruza la suma contra el id 6.
SIAP_SUMA_FAO = {7: 6}


def cruce_siap_fao(prod: pd.DataFrame, mundial: pd.DataFrame) -> list[str]:
    s = (prod.assign(id_cultivo=prod.id_cultivo.replace(SIAP_SUMA_FAO))
             .groupby(["anio", "id_cultivo"]).produccion_t.sum())
    f = mundial[mundial.m49 == "484"].set_index(["anio", "id_cultivo"]).produccion_t
    c = pd.concat({"siap": s, "fao": f}, axis=1).dropna(subset=["fao"])
    # Solo el periodo que cubren las dos: la FAO empieza en 1961 y el SIAP en 2003.
    anios = c.index.get_level_values("anio")
    c = c[(anios >= prod.anio.min()) & (anios <= prod.anio.max())]
    rojos = []
    for (anio, cultivo), r in c.iterrows():
        if (anio, cultivo) in HUECOS_SIAP:
            continue
        if pd.isna(r.siap):
            rojos.append(f"SIAP sin dato y FAO con {r.fao:,.0f} t: {anio} cultivo {cultivo}")
        elif abs(r.siap / r.fao - 1) > TOLERANCIA_FAO:
            rojos.append(f"SIAP {r.siap:,.0f} t contra FAO {r.fao:,.0f} t: {anio} cultivo {cultivo}")
    return rojos


def cruce_datamexico(fact: pd.DataFrame) -> list[str]:
    """Suma de meses y países de Bronze contra el total anual que da el propio cubo."""
    anios = sorted({m.year for m in fact.mes})
    mia = (fact.assign(anio=[m.year for m in fact.mes])
               .groupby(["anio", "hs6", "id_flujo"]).valor_usd.sum())
    ref = datamexico.totales_anuales(anios).set_index(["anio", "hs6", "id_flujo"]).valor_usd
    c = pd.concat({"bronze": mia, "cubo": ref}, axis=1).fillna(0)
    dif = c.cubo - c.bronze
    conocida = pd.Series(DIFERENCIAS_DATAMEXICO, dtype=float).reindex(c.index).fillna(0)
    malos = c[(dif - conocida).abs() > 1]
    return [f"DataMéxico {k}: Bronze {r.bronze:,.0f} contra cubo {r.cubo:,.0f} USD"
            for k, r in malos.iterrows()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-banxico", action="store_true", help="si aún no hay token")
    ap.add_argument("--forzar", action="store_true", help="vuelve a bajar todo")
    a = ap.parse_args()
    hoy = date.today()
    gold, rojos = {}, []

    try:
        rutas_siap = siap.extraer(hoy.year - 1, forzar_ultimo=a.forzar)
        rutas_dm = datamexico.extraer(hoy.year, forzar=a.forzar)
        ruta_fao = faostat.extraer(forzar=a.forzar)
        ruta_bmx = None if a.sin_banxico else banxico.extraer()
    except Exception as e:  # una fuente caída: los datos no están
        print(f"ERROR al extraer: {e}")
        return 1

    gold.update(siap.transformar(siap.leer(rutas_siap)))
    gold.update(datamexico.transformar(datamexico.leer(rutas_dm)))
    gold.update(faostat.transformar(*faostat.leer(ruta_fao)))
    if ruta_bmx:
        gold.update(banxico.transformar(banxico.leer(ruta_bmx)))
    gold["dim_cultivo"] = dim_cultivo()
    gold["dim_hs6"] = dim_hs6()
    gold["dim_fecha"] = dim_fecha()

    vacias = [n for n, df in gold.items() if df.empty]
    if vacias:
        print(f"ERROR: tablas vacías {vacias}")
        return 1
    for nombre, df in gold.items():
        ruta = escribir_gold(df, nombre)
        print(f"  {ruta.name:<32} {len(df):>7} filas")

    rojos += cruce_siap_fao(gold["fact_produccion"], gold["fact_produccion_mundial"])
    rojos += cruce_datamexico(gold["fact_comercio"])
    print(f"Huecos declarados del SIAP (año, cultivo): {sorted(HUECOS_SIAP)}")
    print(f"Diferencias declaradas de DataMéxico: {DIFERENCIAS_DATAMEXICO}")
    if rojos:
        print(f"{len(rojos)} cuadres en rojo:")
        for r in rojos:
            print("  -", r)
        return 2
    print("Cuadres en verde.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
