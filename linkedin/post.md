# Borrador del post de LinkedIn

Cifras comprobadas por consulta DAX contra el modelo (2026-10-13 y 2026-10-19).
Carrusel: `linkedin/carrusel.pdf` (7 páginas, 1080 × 1350), generado con
`py scripts/generar_carrusel.py` desde `linkedin/capturas/`. En LinkedIn se sube como
«documento» y se le pone título.

---

¿Sabías que una hectárea de berries en México vale 47 veces lo que una de maíz? 🍓

Armé, de punta a punta y solo con datos públicos, un tablero sobre el mercado de
berries de México: dónde se cultivan, cuánto se exporta y cómo se comparan con el
tomate, la papa y el maíz.

Tres hallazgos:

📍 Michoacán produce el 58 % de las berries del país (SIAP, 2025).
🚚 Las exportaciones crecieron 13.7 veces desde 2006, y el 97 % va a EE. UU.
🌎 México es el 2.º productor mundial de frambuesa, con el 19 % (FAO, 2024).

Y un adelanto: al cierre de junio de 2026, la frambuesa va un 10 % arriba y la
fresa un 6.5 % abajo frente al mismo corte de 2025 (avance preliminar del SIAP).

Lo que hay detrás:
• Pipeline en Python que baja tres fuentes (SIAP, DataMéxico y FAOSTAT), las limpia
  y las convierte en un modelo estrella.
• Cada fuente se cuadra contra otra distinta, no contra sí misma. Así salieron dos
  trampas: la FAO cuenta a China dos veces (como país y por sus partes) y el CSV del
  SIAP mezcla toneladas con plantas de vivero bajo el mismo cultivo.
• Power BI en formato PBIP: el modelo y el informe son texto versionado en Git.
• Cualquiera puede clonarlo y abrirlo, sin base de datos ni credenciales.

Código y datos: https://github.com/licgpelg/mexican-berries-pipeline

Fuentes: SIAP (SADER), DataMéxico (Secretaría de Economía) y FAOSTAT (FAO).
Proyecto personal, sin relación con ninguna empresa.

#PowerBI #Python #DataAnalytics #Agricultura #Berries #DatosAbiertos

---

Notas antes de publicar:
- El enlace en el cuerpo del post reduce el alcance en LinkedIn; alternativa: ponerlo
  en el primer comentario y escribir «enlace en los comentarios».
- Revisar que en ninguna captura salga el nombre de la cuenta de Windows ni de la
  empresa (las capturas se recortan al lienzo del informe).
