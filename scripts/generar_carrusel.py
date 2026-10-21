"""Carrusel de LinkedIn (PDF, 1080 x 1350) a partir de las capturas de linkedin/capturas.

    py scripts/generar_carrusel.py

Las cifras de los textos salen del informe (comprobadas por DAX el 2026-10-13 y el
2026-10-19); si cambian los datos, hay que revisarlas aquí y en linkedin/post.md.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
CAPTURAS = RAIZ / "linkedin" / "capturas"
SALIDA = RAIZ / "linkedin" / "carrusel.pdf"
ANCHO, ALTO, MARGEN = 1080, 1350, 72

# Colores del tema del informe (generar_informe.py).
BAYA, FONDO, TINTA, GRIS, VERDE, BORDE = "#8E1B3A", "#F4F1EA", "#1F2421", "#5E6660", "#1F4D2C", "#E3DED2"
FUENTES = Path("C:/Windows/Fonts")


def fuente(nombre, tam):
    return ImageFont.truetype(str(FUENTES / nombre), tam)


NEGRITA, SEMI, NORMAL = "segoeuib.ttf", "seguisb.ttf", "segoeui.ttf"


def partir(draw, texto, f, ancho):
    """Reparte el texto en líneas que quepan en «ancho» píxeles."""
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if draw.textlength(prueba, font=f) <= ancho:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    lineas.append(actual)
    return lineas


def parrafo(draw, xy, texto, f, color, ancho, interlineado=1.25):
    x, y = xy
    for linea in partir(draw, texto, f, ancho):
        draw.text((x, y), linea, font=f, fill=color)
        y += int(f.size * interlineado)
    return y


def pie(draw, n, total):
    draw.line((MARGEN, ALTO - 96, ANCHO - MARGEN, ALTO - 96), fill=BORDE, width=2)
    draw.text((MARGEN, ALTO - 72), "Berries de México · datos públicos", font=fuente(NORMAL, 24), fill=GRIS)
    t = f"{n} / {total}"
    f = fuente(SEMI, 24)
    draw.text((ANCHO - MARGEN - draw.textlength(t, font=f), ALTO - 72), t, font=f, fill=GRIS)


def captura(lienzo, nombre, y):
    """Pega la captura a todo el ancho útil, con borde y sombra suave."""
    img = Image.open(CAPTURAS / f"{nombre}.png").convert("RGB")
    w = ANCHO - 2 * MARGEN
    img = img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
    d = ImageDraw.Draw(lienzo)
    d.rounded_rectangle((MARGEN - 2 + 6, y - 2 + 8, MARGEN + w + 2 + 6, y + img.height + 2 + 8), 14, fill="#DDD7CA")
    d.rounded_rectangle((MARGEN - 2, y - 2, MARGEN + w + 2, y + img.height + 2), 14, fill=BORDE)
    lienzo.paste(img, (MARGEN, y))
    return y + img.height


def hallazgo(n, total, etiqueta, titulo, cifra, detalle, nombre):
    lienzo = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(lienzo)
    d.rectangle((0, 0, ANCHO, 14), fill=BAYA)
    d.text((MARGEN, 70), etiqueta.upper(), font=fuente(SEMI, 26), fill=VERDE)
    y = parrafo(d, (MARGEN, 112), titulo, fuente(NEGRITA, 52), TINTA, ANCHO - 2 * MARGEN, 1.18)
    d.text((MARGEN, y + 18), cifra, font=fuente(NEGRITA, 96), fill=BAYA)
    y = parrafo(d, (MARGEN, y + 140), detalle, fuente(NORMAL, 30), GRIS, ANCHO - 2 * MARGEN)
    # La captura, centrada en el hueco que queda entre el texto y el pie.
    alto_img = round(715 * (ANCHO - 2 * MARGEN) / 1266)
    captura(lienzo, nombre, y + max(40, (ALTO - 96 - y - alto_img) // 2))
    pie(d, n, total)
    return lienzo


def portada(total):
    lienzo = Image.new("RGB", (ANCHO, ALTO), BAYA)
    d = ImageDraw.Draw(lienzo)
    d.text((MARGEN, 96), "PROYECTO DE DATOS · POWER BI + PYTHON", font=fuente(SEMI, 26), fill="#F5DDE3")
    y = parrafo(d, (MARGEN, 150), "Las berries de México, de la parcela a la frontera",
                fuente(NEGRITA, 74), "#FFFFFF", ANCHO - 2 * MARGEN, 1.12)
    y = parrafo(d, (MARGEN, y + 24), "Dónde se cultivan, cuánto se exporta y cuánto vale una hectárea frente a "
                "la papa, el tomate y el maíz. Solo con datos públicos.",
                fuente(NORMAL, 32), "#F5DDE3", ANCHO - 2 * MARGEN)
    fondo = Image.new("RGB", (ANCHO, ALTO), FONDO)
    lienzo.paste(fondo.crop((0, 0, ANCHO, ALTO - y - 60)), (0, y + 60))
    alto_img = round(715 * (ANCHO - 2 * MARGEN) / 1266)
    captura(lienzo, "portada", y + 60 + (ALTO - 170 - (y + 60) - alto_img) // 2)
    d.text((MARGEN, ALTO - 150), "Desliza →", font=fuente(NEGRITA, 40), fill=BAYA)
    pie(d, 1, total)
    return lienzo


def cierre(n, total):
    lienzo = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(lienzo)
    d.rectangle((0, 0, ANCHO, 14), fill=BAYA)
    d.text((MARGEN, 70), "CÓMO ESTÁ HECHO", font=fuente(SEMI, 26), fill=VERDE)
    y = parrafo(d, (MARGEN, 112), "De tres fuentes públicas a un modelo estrella, de punta a punta",
                fuente(NEGRITA, 52), TINTA, ANCHO - 2 * MARGEN, 1.18)
    # Diagrama del flujo: cuatro cajas en columna.
    pasos = [("Extraer", "SIAP (CSV), DataMéxico (API) y FAOSTAT (ZIP), con reintentos"),
             ("Transformar", "Python y pandas: limpiar, unificar cultivos y armar el modelo estrella"),
             ("Validar", "cada fuente se cuadra contra otra distinta, no contra sí misma"),
             ("Mostrar", "Power BI en PBIP: modelo e informe como texto versionado en Git")]
    y += 40
    for i, (paso, texto) in enumerate(pasos):
        d.rounded_rectangle((MARGEN, y, ANCHO - MARGEN, y + 120), 16, fill="#FFFFFF", outline=BORDE, width=2)
        d.rounded_rectangle((MARGEN, y, MARGEN + 14, y + 120), 7, fill=BAYA)
        d.text((MARGEN + 40, y + 18), paso, font=fuente(NEGRITA, 32), fill=BAYA)
        parrafo(d, (MARGEN + 40, y + 62), texto, fuente(NORMAL, 26), TINTA, ANCHO - 2 * MARGEN - 70)
        y += 120
        if i < len(pasos) - 1:
            d.polygon([(ANCHO // 2 - 14, y + 8), (ANCHO // 2 + 14, y + 8), (ANCHO // 2, y + 26)], fill=GRIS)
            y += 34
    y += 50
    d.text((MARGEN, y), "Código y datos, para clonarlo y abrirlo:", font=fuente(SEMI, 30), fill=TINTA)
    d.text((MARGEN, y + 46), "github.com/licgpelg/mexican-berries-pipeline", font=fuente(NEGRITA, 36), fill=BAYA)
    parrafo(d, (MARGEN, y + 120), "Fuentes: SIAP (SADER), DataMéxico (Secretaría de Economía) y FAOSTAT (FAO, "
            "CC BY 4.0). Proyecto personal, sin relación con ninguna empresa.",
            fuente(NORMAL, 24), GRIS, ANCHO - 2 * MARGEN)
    pie(d, n, total)
    return lienzo


HALLAZGOS = [
    ("Producción", "Michoacán produce más de la mitad de las berries del país", "58 %",
     "de la producción de berries de 2025 (SIAP). Jalisco y Baja California le siguen de lejos.",
     "02_produccion"),
    ("Exportación", "Las exportaciones de berries se multiplicaron desde 2006", "×13.7",
     "hasta 3,228 millones de dólares en 2025; el 97 % va a Estados Unidos (DataMéxico).",
     "04_exportacion"),
    ("México en el mundo", "México es el 2.º productor mundial de frambuesa", "19 %",
     "de la producción mundial en 2024; 4.º en fresa y 5.º en arándano (FAOSTAT).",
     "05_mexico_en_el_mundo"),
    ("2026, cifras preliminares", "Al 30 de junio, la frambuesa sube y la fresa baja", "+10 % / −6.5 %",
     "frente al mismo corte del año agrícola anterior (avance mensual del SIAP, sin arándano).",
     "03_2026_preliminar"),
    ("Contraste", "Una hectárea de berries vale mucho más que una de maíz", "×47",
     "valor de la producción por hectárea cosechada en 2025 (SIAP, pesos corrientes).",
     "07_contraste"),
]


def main():
    total = len(HALLAZGOS) + 2
    paginas = [portada(total)]
    paginas += [hallazgo(i + 2, total, *h) for i, h in enumerate(HALLAZGOS)]
    paginas.append(cierre(total, total))
    vista = RAIZ / "linkedin" / "carrusel"
    vista.mkdir(exist_ok=True)
    pngs = []
    for i, p in enumerate(paginas, 1):
        pngs.append(vista / f"{i:02d}.png")
        p.save(pngs[-1], optimize=True)
    # PDF con PyMuPDF: el Pillow de esta máquina no trae JPEG, que es lo que usa para PDF.
    import pymupdf
    pdf = pymupdf.open()
    for png in pngs:
        pagina = pdf.new_page(width=ANCHO * 0.75, height=ALTO * 0.75)  # 1080 px = 810 pt
        pagina.insert_image(pagina.rect, filename=str(png))
    pdf.save(SALIDA, deflate=True)
    print(f"{SALIDA} ({len(paginas)} páginas)")


if __name__ == "__main__":
    main()
