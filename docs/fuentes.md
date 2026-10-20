# Fuentes — Berries_portafolio

Investigación del 2026-10-13. Marcas: **[V]** verificado con descarga o
llamada real · **[D]** según documentación oficial · **[NC]** no confirmado.

Regla del proyecto (`AGENTS.md`): una fuente entra solo con licencia que
permita republicar. Las que quedan en [NC] de licencia están **pendientes de
decisión**, no aprobadas.

## Resumen

| Fuente | Nivel | Periodo / último dato | Acceso | Clave | Licencia | Dificultad | Estado |
|---|---|---|---|---|---|---|---|
| SIAP Cierre agrícola | municipio, las 4 berries separadas | anual 2003-2025 [V] | CSV por GET | no | ambigua [NC] | baja | MVP, pendiente licencia |
| DataMéxico (SE) | nación/estado/municipio × HS6 × país, solo USD | mensual, a jul-2026 [V] | REST | no | [NC] | baja-media | MVP, pendiente licencia |
| FAOSTAT QCL | país, anual | 1961-2024 [V] | ZIP | no | **CC BY 4.0** [V] | baja | MVP |
| Banxico SIE (FIX) | diario | al día | REST | token gratis | [NC] | baja | MVP, pendiente licencia |
| US Census Intl Trade | país × HS, valor y cantidad | mensual 2010 a ~ago-2026 [NC] | REST | clave gratis | pública, con aviso [D] | baja | fase 2 |
| USDA AMS MARS | mercados terminales, cruces desde México | diario-semanal [NC] | REST | clave gratis | dominio público EE. UU. [NC] | media | fase 2 |
| SIAP Avance mensual | estado (también municipio), 65 cultivos, **sin arándano** [V] | corte mensual, a sep-2026 [V] | xajax (POST) | no | la misma del cierre [NC] | media | **en uso desde el 2026-10-19**, preliminar; pendiente licencia |
| FAS GATS | igual que Census | mensual | REST / web | sí | dominio público [NC] | media | redundante con Census |
| UN Comtrade | mundial | — | REST | sí | **prohíbe redistribuir** [V] | — | **descartada** |

## Detalle

### SIAP / SADER — Cierre de la producción agrícola

- Página: https://nube.agricultura.gob.mx/datosAbiertos/Agricola.php
- CSV municipal por año (2003-2025) [V]:
  `https://nube.agricultura.gob.mx/index.php?view=10AE434F-A2158368-A120BC5A-EDF4AFAA&ANIO=2025`.
  La ruta cuelga de la raíz del sitio: con `/datosAbiertos/` en medio devuelve
  una página HTML en vez del CSV.
- 2025: 5.8 MB, 35 903 filas, codificación **latin1**. Columnas: `Anio,
  Idestado, Nomestado, Idddr, Nomddr, Idcader, Nomcader, Idmunicipio,
  Nommunicipio, Idciclo, Nomcicloproductivo, Idmodalidad, Nommodalidad,
  Idunidadmedida, Nomunidad, Idcultivo, Nomcultivo, Sembrada, Cosechada,
  Siniestrada, Volumenproduccion, Rendimiento, Preciomediorural,
  Valorproduccion`.
- Filas de berries en 2025: Fresa 101, Zarzamora 77, Arándano 74, Frambuesa 62.
- **Licencia [NC]:** la página no declara ninguna. Su pie enlaza a
  https://www.gob.mx/terminos, que limita el contenido a uso personal y prohíbe
  transferirlo a terceros. Los «Términos de Libre Uso MX» del Gobierno federal
  sí permiten redistribuir citando la fuente, pero no se confirmó que se
  apliquen a este conjunto (datos.gob.mx devolvió 403).

### SIAP / SADER — Avance mensual de siembras y cosechas (desde el 2026-10-19)

- Página: https://nube.agricultura.gob.mx/avance_agricola/ [V]. No tiene descarga
  directa: el formulario llama por **xajax** (POST a la misma URL, `xajax=<función>` y
  `xajaxargs[]`) y la respuesta es un XML con la tabla en HTML. `src/siap_avance.py`
  abre la sesión con un GET y llama a `reporte` con: tipo 1 (por ubicación), ciclo 5
  «Cíclicos - Perennes», modalidad 3 «Riego + Temporal», opción 2 «por entidad», el
  cultivo, la unidad «Tonelada» y el mes. El botón «Excel» (`Clases/reporte.php`)
  depende de la sesión y no hace falta.
- **Cultivos**: 65 en el catálogo; están 7 de los 8 del proyecto. **El arándano no
  está**: para él solo hay cierre anual. Los ids del avance no son los del cierre
  (fresa 150, frambuesa 149, zarzamora 420, papa 283, jitomate 389, tomate verde 390,
  maíz grano 225).
- **Año agrícola** [V]: el año N va de octubre de N-1 (siembras de otoño-invierno) a
  marzo de N+1. Entre octubre y marzo una consulta trae dos tablas, una por año
  agrícola; cada una dice su año y su fecha de corte («Situación al 30 de junio de
  2026»). Las cifras son **acumuladas** al corte.
- Precio medio rural y valor de la producción vienen en el HTML **comentados**: el
  SIAP no los publica en el avance, y aquí tampoco se usan.
- Datos al 2026-10-19: año agrícola 2026 con cortes de oct-2025 a sep-2026; 2025,
  de ene-2025 a mar-2026 (de oct a dic-2024 no se bajó: el corte de enero ya acumula).
- **Contra el cierre** (año agrícola 2025, corte del 31-03-2026): superficie sembrada
  igual o casi (0 a -0.7 %); producción **por debajo** entre 0.1 % (papa) y 6.7 %
  (frambuesa). El avance es provisional y se queda corto. Tolerancia del cruce: 10 %
  en producción y 2 % en superficie.
- Licencia: la misma situación que el cierre (pendiente, pendiente 6).

### DataMéxico (Secretaría de Economía) — comercio exterior

- API [V], sin clave: `https://www.economia.gob.mx/apidatamexico/tesseract/`.
  El dominio antiguo `api.datamexico.org` ya no responde.
- Cubos disponibles: `economy_foreign_trade_nat`, `_ent` (por estado), `_mun`
  (por municipio) y `_movement`.
- Ejemplo [V]:
  `data.jsonrecords?cube=economy_foreign_trade_nat&drilldowns=Month,HS6,Flow&measures=Trade+Value&HS6=2081010,2081020,2081040&Year=2026`
  → fresa, exportación de enero de 2026: 197 394 220 USD.
- **Solo trae valor en USD, sin volumen.** El HS6 0810.20 junta frambuesa con
  zarzamora, y el 0810.40 incluye otros *Vaccinium* además del arándano.
- Servidor lento e inestable: hacen falta reintentos y esperas largas.
- **Licencia [NC]:** la página de términos (`/datamexico/es/about/legal`) se
  arma con JavaScript y no se pudo leer.

### FAOSTAT — producción mundial (QCL)

- ZIP de 33 MB, sin clave [V]:
  https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip
- Última actualización: 2025-12-31 (catálogo `datasets_E.json`) [V].
- México [V]: Strawberries y Raspberries 1961-2024, Blueberries 1991-2024; cada
  una con superficie, producción y rendimiento. La zarzamora no tiene partida
  propia [NC].
- Se quita el área «China» (351), que suma China continental, Taiwán, Hong Kong y
  Macao, que también vienen por separado; si no, China cuenta dos veces.
- **Licencia [V]: CC BY 4.0.** Se atribuye a la FAO con base, conjunto, fecha
  y URL: https://www.fao.org/contact-us/terms/db-terms-of-use/en/

### Banxico SIE — tipo de cambio FIX

- `https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos/...`
- El token gratuito va en la cabecera `Bmx-Token` [D]. Sin token, la API
  responde 400 «Token inválido» [V].
- **Licencia [NC]:** el enlace a la «Salvedad de uso» da 404.

### US Census — International Trade API (fase 2)

- Endpoint: `https://api.census.gov/data/timeseries/intltrade/imports/hs`.
  Su lista de variables [V] incluye `GEN_VAL_MO`, `CON_VAL_MO` y `GEN_QY1_MO`.
  Clave gratuita.
- El filtro previsto es México, `CTY_CODE=2010`; los parámetros de producto no
  se probaron [NC].
- Términos [D]: hay que mostrar «This product uses the Census Bureau Data API
  but is not endorsed or certified by the Census Bureau».

### USDA AMS Market News — API MARS (fase 2)

- `https://marsapi.ams.usda.gov/services/v1.2/reports`. Sin clave devuelve
  403 [V]. La clave es gratuita: con registro en eAuth y MyMarketNews, se usa
  como usuario de autenticación básica con la contraseña vacía [D].
- Informes candidatos (ids no verificados): 1662, National Shipping Point
  Trends, con cruces desde México; 3284, movimiento por origen.

### UN Comtrade — descartada

- Su acuerdo de licencia (sección 5) prohíbe redistribuir o publicar sin
  permiso escrito de la ONU [V].

## Conformación entre fuentes (`dim_cultivo`)

| Cultivo | SIAP `Nomcultivo` | HS6 | FAO |
|---|---|---|---|
| Fresa | Fresa | 0810.10 | Strawberries |
| Frambuesa | Frambuesa | 0810.20 (agrupada con zarzamora) | Raspberries |
| Zarzamora | Zarzamora | 0810.20 (agrupada con frambuesa) | sin partida [NC] |
| Arándano | Arándano | 0810.40 (incluye otros *Vaccinium*) | Blueberries |
| Papa | Papa (8100000) | 0701.90 (sin semilla) | Potatoes |
| Tomate rojo | Tomate rojo (jitomate) (8970000) | 0702.00 | Tomatoes (**para México, jitomate + tomate verde**) |
| Tomate verde | Tomate verde (8980000) | sin fracción propia a 6 dígitos | sin partida (va dentro de Tomatoes) |
| Maíz grano | Maíz grano (7490000) | 1005.90 (sin semilla) | Maize (corn) |

Cultivos de referencia añadidos el 2026-10-13. El maíz forrajero (en verde, seco,
achicalado) queda fuera: es otro producto, medido como forraje (16.8 millones de t
en 2024). Cuadres contra la FAO, 2003-2024: papa, diferencia máxima del 0.05 %;
maíz, del 0.37 %; jitomate + tomate verde del SIAP contra Tomatoes de la FAO,
iguales al entero los 22 años.

## Verificación al extraer (2026-10-13)

`scripts/run_all.py` cruza cada fuente con otra independiente:

- **SIAP contra FAOSTAT** (México, producción por cultivo y año, 2003-2024):
  coinciden al entero salvo revisiones puntuales (fresa 2003: 146 009 t en el
  SIAP y 150 261 t en la FAO). Tolerancia: 5 %. La zarzamora no entra en el
  cruce porque la FAO no la separa.
- **Hueco declarado del SIAP:** el CSV abierto de 2020 y 2021 trae ~80 cultivos
  (contra ~300 en los demás años) y no incluye el arándano. La FAO tiene esos
  años como cifra oficial (50 293 t y 66 482 t). No se rellena.
- **Vivero excluido del SIAP:** 13 filas de fresa en unidad «Planta»
  (2019-2025, bajo el mismo Idcultivo de la fruta).
- **DataMéxico contra su propio total anual:** cuadra en 118 de 119
  combinaciones (año × HS6 × flujo). En la que falta, exportación de fresa de 2008,
  hay 78 578 USD de mayo sin país asignado en el cubo, que se pierden al
  desglosar por país.

### Mapa de estados (página Producción)

- Es el mapa de México por estados que trae el visual *Shape map* de Power BI Desktop
  (`mexico.states.topo.json`, 20 KB, 32 estados, claves por nombre, ISO e id) [V]. Desktop
  lo copia dentro del PBIP (`StaticResources/SharedResources/Shapemaps/`) al usarlo, y
  `scripts/generar_informe.py` hace lo mismo desde la instalación.
- No es un dato publicado, sino una geometría que acompaña al producto. Las condiciones de
  republicarlo fuera de un informe de Power BI no están confirmadas [NC]. Si hiciera falta
  quitarlo del repo, la alternativa es Natural Earth (dominio público).
- Para que los nombres coincidan, el ETL llama «Estado de México» al estado que el SIAP
  publica como «México». Los otros 31 nombres coinciden tal cual (comprobado el 2026-10-13).
