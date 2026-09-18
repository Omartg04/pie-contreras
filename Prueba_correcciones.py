"""
prueba_correcciones.py — Verifica las tres correcciones del cierre Contreras.

Ejecutar desde la raíz del repo:
    python prueba_correcciones.py

No requiere Streamlit ni geopandas. Solo pypdf y pandas.
"""
import re, io, sys, json
import pandas as pd
from pypdf import PdfReader, PdfWriter

PDF_PATH  = "assets/pie_010_mc_hojas_campo.pdf"
RANK_PATH = "data/pie_010_mc_ranking.csv"       # ajustar si el nombre difiere
UNIF_PATH = "data/pie_010_mc_unificado.geojson"

PASS = "✅"
FAIL = "❌"
resultados = []

def ok(msg):
    resultados.append((PASS, msg))
    print(f"  {PASS}  {msg}")

def fail(msg):
    resultados.append((FAIL, msg))
    print(f"  {FAIL}  {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 1 — Índice PDF por regex (corrige bug de orden incorrecto)
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Bloque 1: índice PDF por regex ──────────────────────────────────────")

reader = PdfReader(PDF_PATH)
patron = re.compile(r"Secci[oó]n[:\s]*(\d{4,5})", re.IGNORECASE)
indice = {}
paginas_sin_match = []

for i, page in enumerate(reader.pages):
    texto = page.extract_text(extraction_mode="layout") or ""
    match = patron.search(texto)
    if match:
        indice[int(match.group(1))] = i
    else:
        paginas_sin_match.append(i)

if paginas_sin_match:
    fail(f"Páginas sin sección identificada: {paginas_sin_match}")
else:
    ok(f"Regex capturó sección en las {len(reader.pages)} páginas del PDF")

# Prueba clave: 3066 y 3099 no deben apuntar al mismo índice
if 3066 in indice and 3099 in indice:
    if indice[3066] != indice[3099]:
        ok(f"3066 → pág {indice[3066]}  |  3099 → pág {indice[3099]}  (distintas ✓)")
    else:
        fail(f"3066 y 3099 apuntan a la misma página {indice[3066]} — bug persiste")
else:
    fail(f"Alguna sección no está en el índice: 3066={3066 in indice}, 3099={3099 in indice}")

# Prueba: 3072 ausente del índice (no tiene manzanas → no tiene hoja)
if 3072 not in indice:
    ok("Sección 3072 correctamente ausente del índice PDF")
else:
    fail(f"Sección 3072 presente en el índice (pág {indice[3072]}) — inesperado")

# Prueba: extracción real de una página
def _extraer(sec_id):
    if sec_id not in indice:
        return None
    r = PdfReader(PDF_PATH)
    w = PdfWriter()
    w.add_page(r.pages[indice[sec_id]])
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()

pdf_3066 = _extraer(3066)
if pdf_3066 and len(pdf_3066) > 1000:
    ok(f"Extracción de sección 3066: {len(pdf_3066):,} bytes — OK")
else:
    fail("Extracción de sección 3066 falló o devolvió bytes vacíos")

pdf_3072 = _extraer(3072)
if pdf_3072 is None:
    ok("_extraer(3072) devuelve None correctamente")
else:
    fail("_extraer(3072) debería devolver None pero devolvió bytes")

# Verificar que la página extraída de 3066 contiene "3066" en su texto
if pdf_3066:
    r_check = PdfReader(io.BytesIO(pdf_3066))
    texto_check = r_check.pages[0].extract_text(extraction_mode="layout") or ""
    if "3066" in texto_check:
        ok("El PDF extraído para 3066 contiene '3066' en el texto — página correcta")
    else:
        fail("El PDF extraído para 3066 NO contiene '3066' — revisar el índice")


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 2 — Sección 3072: en ranking pero sin manzanas
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Bloque 2: sección 3072 en ranking / sin manzanas ────────────────────")

rank = pd.read_csv(RANK_PATH)
p3   = rank[(rank["NIVEL_PRIORIDAD_OP"] == "P3_MEDIA") & (rank["SECCION"] > 0)]

if 3072 in p3["SECCION"].values:
    ok("Sección 3072 presente en p3 del ranking (59 secciones operativas)")
else:
    fail("Sección 3072 NO está en p3 — verificar el CSV de ranking")

# Manzanas de 3072 en el GeoJSON unificado
with open(UNIF_PATH, encoding="utf-8") as f:
    unif = json.load(f)

mzas_3072 = [
    feat for feat in unif["features"]
    if int(feat["properties"].get("SECCION", 0)) == 3072
]
if len(mzas_3072) == 0:
    ok("Sección 3072 tiene 0 manzanas en el GeoJSON unificado — brecha documentada")
else:
    fail(f"Sección 3072 tiene {len(mzas_3072)} manzanas — comportamiento inesperado")

# Congruencia total: p3 debe tener 1 sección más que el PDF
diff = len(p3) - len(reader.pages)
if diff == 1:
    ok(f"p3={len(p3)} secciones · PDF={len(reader.pages)} páginas · diferencia=1 (solo 3072) ✓")
else:
    fail(f"Diferencia inesperada: p3={len(p3)}, PDF={len(reader.pages)}, diff={diff}")


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 3 — Alineación completa del índice contra el ranking
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Bloque 3: alineación índice PDF ↔ ranking ───────────────────────────")

secs_p3  = set(p3["SECCION"].astype(int).tolist())
secs_pdf = set(indice.keys())

en_p3_no_pdf = sorted(secs_p3 - secs_pdf)
en_pdf_no_p3 = sorted(secs_pdf - secs_p3)

if en_p3_no_pdf == [3072]:
    ok(f"Solo sección 3072 en p3 sin hoja PDF — exactamente lo esperado")
else:
    fail(f"Secciones en p3 sin PDF: {en_p3_no_pdf} — se esperaba solo [3072]")

if not en_pdf_no_p3:
    ok("Ninguna página PDF apunta a sección fuera de p3 — índice limpio")
else:
    fail(f"Páginas PDF sin match en p3: secciones {en_pdf_no_p3}")


# ─────────────────────────────────────────────────────────────────────────────
# RESUMEN
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Resumen ─────────────────────────────────────────────────────────────")
aprobadas = sum(1 for r in resultados if r[0] == PASS)
fallidas  = sum(1 for r in resultados if r[0] == FAIL)
print(f"  {aprobadas} pruebas aprobadas · {fallidas} fallidas\n")

if fallidas:
    print("  Pruebas fallidas:")
    for estado, msg in resultados:
        if estado == FAIL:
            print(f"    {FAIL}  {msg}")
    sys.exit(1)
else:
    print("  Todas las pruebas pasaron. Listo para push.\n")