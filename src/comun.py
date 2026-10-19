"""Rutas, descarga con reintentos y escritura de Gold, comunes a todas las fuentes."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RAIZ = Path(__file__).resolve().parents[1]
BRONZE = RAIZ / "data" / "bronze"
GOLD = RAIZ / "data" / "gold"


def cargar_env() -> None:
    """Lee `.env` sin depender de python-dotenv: solo líneas CLAVE=valor."""
    ruta = RAIZ / ".env"
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip())


def sesion() -> requests.Session:
    # DataMéxico falla a ratos con 5xx (visto el 2026-10-13): reintentos con espera creciente.
    s = requests.Session()
    reintento = Retry(total=5, backoff_factor=3, status_forcelist=(429, 500, 502, 503, 504),
                      allowed_methods=("GET",))
    s.mount("https://", HTTPAdapter(max_retries=reintento))
    s.headers["User-Agent"] = "berries-portafolio/0.1 (proyecto personal, datos abiertos)"
    return s


def descargar(url: str, destino: Path, *, forzar: bool = False, timeout: int = 300,
              s: requests.Session | None = None, **kwargs) -> Path:
    """Baja `url` a `destino` si no existe ya (o con `forzar`). Escribe a un .part y renombra
    al final, para que una descarga cortada no se confunda con una buena."""
    if destino.exists() and not forzar:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    s = s or sesion()
    r = s.get(url, timeout=timeout, stream=True, **kwargs)
    r.raise_for_status()
    tmp = destino.with_suffix(destino.suffix + ".part")
    with open(tmp, "wb") as f:
        for trozo in r.iter_content(1 << 20):
            f.write(trozo)
    tmp.replace(destino)
    return destino


def escribir_gold(df: pd.DataFrame, nombre: str) -> Path:
    """CSV en UTF-8 con BOM (Excel y Power BI lo abren sin adivinar la codificación),
    punto decimal y fechas ISO. Sin float_format: pandas escribe la forma más corta que
    conserva el valor; con «%.4f» el relleno de ceros llevaba data/gold de 17 MB a más del
    doble de lo necesario (medido el 2026-10-13 al añadir el maíz)."""
    GOLD.mkdir(parents=True, exist_ok=True)
    ruta = GOLD / f"{nombre}.csv"
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta
