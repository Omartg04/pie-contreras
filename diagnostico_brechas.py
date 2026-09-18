"""
diagnostico_brechas.py — Diagnóstico completo de brechas cartográficas.

Cruza tres universos:
  A) Lista Nominal   → ranking CSV  (fuente: INE julio 2026)
  B) Shapefile       → secciones GeoJSON (fuente: cartografía INE 2025)
  C) Modelo manzanas → unificado GeoJSON (fuente: pipeline 02)

Ejecutar desde la raíz del repo:
    python diagnostico_brechas.py
"""
import json
import pandas as pd

RANK_PATH  = "data/pie_010_mc_ranking.csv"
SECS_PATH  = "data/pie_010_mc_secciones.geojson"
UNIF_PATH  = "data/pie_010_mc_unificado.geojson"

SEP = "─" * 70

# ─────────────────────────────────────────────────────────────────────────────
# Cargar los tres universos
# ─────────────────────────────────────────────────────────────────────────────
rank = pd.read_csv(RANK_PATH)

with open(SECS_PATH, encoding="utf-8") as f:
    secs_raw = json.load(f)

with open(UNIF_PATH, encoding="utf-8") as f:
    unif_raw = json.load(f)

# Universo A — todas las secciones del ranking (lista nominal INE)
# Excluir proxy negativo si existe
secs_ln = set(
    rank[rank["SECCION"] > 0]["SECCION"].astype(int).tolist()
)

# Universo B — secciones con geometría en el shapefile
secs_shape = set(
    int(f["properties"]["SECCION"])
    for f in secs_raw["features"]
    if f["properties"].get("SECCION") and int(f["properties"]["SECCION"]) > 0
)

# Universo C — secciones con al menos una manzana en el modelo
secs_mzas = set(
    int(f["properties"]["SECCION"])
    for f in unif_raw["features"]
    if f["properties"].get("SECCION") and int(f["properties"]["SECCION"]) > 0
)

# Conteo de manzanas por sección en el modelo
mzas_x_sec = {}
for f in unif_raw["features"]:
    sec = int(f["properties"].get("SECCION", 0))
    if sec > 0:
        mzas_x_sec[sec] = mzas_x_sec.get(sec, 0) + 1

# ─────────────────────────────────────────────────────────────────────────────
# Cruce 1 — En lista nominal pero SIN geometría en shapefile
# (reseccionadas o nuevas — el caso de 5654/5655/5656)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("CRUCE 1 — En lista nominal pero SIN geometría en shapefile")
print(SEP)
ln_sin_shape = sorted(secs_ln - secs_shape)
if ln_sin_shape:
    print(f"  {len(ln_sin_shape)} sección(es) encontrada(s):\n")
    for sec in ln_sin_shape:
        row = rank[rank["SECCION"] == sec]
        ln  = int(row["LN_TOTAL"].values[0]) if not row.empty else "—"
        niv = row["NIVEL_PRIORIDAD_OP"].values[0] if not row.empty else "—"
        rnk = int(row["RANK_ESTRATEGICO"].values[0]) if not row.empty and pd.notna(row["RANK_ESTRATEGICO"].values[0]) else "—"
        print(f"  Sección {sec}  |  LN={ln:,}  |  Nivel={niv}  |  Rank={rnk}")
    print()
    print("  → Sin polígono: no puede generar mapa de campo ni aparecer")
    print("    en el mapa de secciones. Requiere shapefile INE 2026.")
else:
    print("  Ninguna — todas las secciones de la LN tienen geometría.\n")

# ─────────────────────────────────────────────────────────────────────────────
# Cruce 2 — En shapefile pero SIN registro en lista nominal
# (eliminadas o fusionadas — el caso de 3088)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("CRUCE 2 — En shapefile pero SIN registro en lista nominal")
print(SEP)
shape_sin_ln = sorted(secs_shape - secs_ln)
if shape_sin_ln:
    print(f"  {len(shape_sin_ln)} sección(es) encontrada(s):\n")
    for sec in shape_sin_ln:
        print(f"  Sección {sec}  |  Geometría presente, sin electores en LN julio 2026")
    print()
    print("  → Secciones eliminadas o fusionadas. Geometry en el shapefile")
    print("    pero sin padrón activo. Excluir de análisis operativo.")
else:
    print("  Ninguna — todas las geometrías del shapefile tienen LN.\n")

# ─────────────────────────────────────────────────────────────────────────────
# Cruce 3 — En lista nominal + shapefile pero SIN manzanas en el modelo
# (el caso de 3072 — y otros posibles)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("CRUCE 3 — En lista nominal + shapefile pero SIN manzanas en el modelo")
print(SEP)
ln_y_shape_sin_mzas = sorted((secs_ln & secs_shape) - secs_mzas)
if ln_y_shape_sin_mzas:
    print(f"  {len(ln_y_shape_sin_mzas)} sección(es) encontrada(s):\n")
    for sec in ln_y_shape_sin_mzas:
        row = rank[rank["SECCION"] == sec]
        ln  = int(row["LN_TOTAL"].values[0]) if not row.empty else "—"
        niv = row["NIVEL_PRIORIDAD_OP"].values[0] if not row.empty else "—"
        rnk = int(row["RANK_ESTRATEGICO"].values[0]) if not row.empty and pd.notna(row["RANK_ESTRATEGICO"].values[0]) else "—"
        print(f"  Sección {sec}  |  LN={ln:,}  |  Nivel={niv}  |  Rank={rnk}")
    print()
    print("  → Sección en el ranking y con polígono, pero el spatial join")
    print("    de proceso 02 no le asignó manzanas. Sin mapa de campo.")
    print("    El PDF y el mapa de manzanas muestran el aviso documentado.")
else:
    print("  Ninguna más allá de las ya documentadas.\n")

# ─────────────────────────────────────────────────────────────────────────────
# Cruce 4 — Secciones con muy pocas manzanas (posible colapso incompleto)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("CRUCE 4 — Secciones con 1 sola manzana en el modelo (posible anomalía)")
print(SEP)
una_manzana = sorted(sec for sec, n in mzas_x_sec.items() if n == 1 and sec in secs_ln)
if una_manzana:
    print(f"  {len(una_manzana)} sección(es) con exactamente 1 manzana:\n")
    for sec in una_manzana:
        row = rank[rank["SECCION"] == sec]
        ln  = int(row["LN_TOTAL"].values[0]) if not row.empty else "—"
        niv = row["NIVEL_PRIORIDAD_OP"].values[0] if not row.empty else "—"
        print(f"  Sección {sec}  |  LN={ln:,}  |  Nivel={niv}")
    print()
    print("  → Revisar si el colapso de micro-manzanas absorbió todas")
    print("    las manzanas en una sola. Poco probable pero posible.")
else:
    print("  Ninguna — sin anomalías de colapso total.\n")

# ─────────────────────────────────────────────────────────────────────────────
# Resumen ejecutivo
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("RESUMEN EJECUTIVO")
print(SEP)
print(f"  Secciones en lista nominal (LN INE julio 2026) : {len(secs_ln)}")
print(f"  Secciones con geometría en shapefile 2025      : {len(secs_shape)}")
print(f"  Secciones con manzanas en el modelo (proc. 02) : {len(secs_mzas)}")
print()
print(f"  Cruce 1 — LN sin shape   : {len(ln_sin_shape)}  sección(es) → {sorted(ln_sin_shape)}")
print(f"  Cruce 2 — Shape sin LN   : {len(shape_sin_ln)}  sección(es) → {sorted(shape_sin_ln)}")
print(f"  Cruce 3 — LN+shape sin mzas : {len(ln_y_shape_sin_mzas)}  sección(es) → {sorted(ln_y_shape_sin_mzas)}")
print(f"  Cruce 4 — 1 sola manzana : {len(una_manzana)}  sección(es) → {sorted(una_manzana)}")
print()

total_brechas = len(ln_sin_shape) + len(shape_sin_ln) + len(ln_y_shape_sin_mzas)
if total_brechas == 0:
    print("  ✅  Sin brechas críticas detectadas.")
else:
    print(f"  ⚠️   {total_brechas} brecha(s) crítica(s) — ver detalle arriba.")
    print("  Documentar en memoria de método del caso.")
print()
