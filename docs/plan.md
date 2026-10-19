# Plan — Berries_portafolio

Objetivo: un tablero de Power BI de inteligencia del sector berries de México,
con datos públicos, que se enseña en LinkedIn (capturas, GIF o video y un
repositorio en GitHub) sin publicarlo en el Service.

Pregunta que responde: **¿cómo se mueve el negocio de las berries mexicanas?**
Dónde se produce, cuánto se exporta, a qué precio se vende en EE. UU. y cómo
le pega el tipo de cambio.

## 1. Modelo y DAX

- Modelo estrella sobre CSV de `data/gold/`; las dimensiones que se comparten
  son `dim_fecha`, `dim_cultivo` y `dim_estado`.
- Hechos candidatos (se confirman con `docs/fuentes.md`):
  - `fact_produccion`: estado × cultivo × año (superficie, producción,
    rendimiento, precio medio rural, valor).
  - `fact_comercio`: mes × cultivo × flujo (valor USD, volumen kg).
  - `fact_precio_eua`: día o semana × cultivo × mercado (precio por caja).
  - `fact_tipo_cambio`: día (FIX).
- Tabla de fechas marcada, fecha/hora automática apagada, medidas base
  reutilizadas en los porcentajes y las variaciones año contra año.
- Cultura `es-MX`; antes de cada captura, una revisión del diseño del modelo
  (estrella, DAX repetido, relaciones).

## 2. Datos: extracción y verificación

- Un extractor por fuente en `src/`, con descarga cruda a `data/bronze/` y
  salida limpia a `data/gold/`.
- Cada extractor verifica contra su origen (totales nacionales publicados por
  la propia fuente), no contra sí mismo.
- Un `scripts/run_all.py` que lo reconstruye todo desde cero.

## 3. Narrativa del tablero

Borrador de páginas (una pregunta por página):

1. **Portada / resumen**: ¿cuánto valen las berries de México? KPI con su periodo.
2. **Producción**: ¿dónde se produce y cómo ha cambiado? (mapa por estado y
   serie por cultivo).
3. **Exportación**: ¿cuánto vendemos fuera y qué crece más?
4. **Precio en EE. UU.**: ¿cuándo se paga mejor? (estacionalidad).
5. **Tipo de cambio**: el mismo dólar en pesos.
6. **Fuentes y metodología**: atribución, licencias y fecha de los datos.

Títulos que dicen la conclusión, no el nombre del gráfico.

## 4. Difusión

- Repositorio público en GitHub: README con captura, cómo reproducirlo y
  fuentes; el PBIP y `data/gold/`.
- Post de LinkedIn: gancho, tres hallazgos con cifra, carrusel en PDF o GIF,
  enlace al repo, atribución de las fuentes.
- Revisar que no salga nada del trabajo (ni datos ni nombres) antes de subir.
