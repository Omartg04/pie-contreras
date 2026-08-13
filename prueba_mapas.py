import json

with open("data/pie_010_mc_secciones.geojson", encoding="utf-8") as f:
    secs = json.load(f)

with open("data/pie_010_mc_unificado.geojson", encoding="utf-8") as f:
    mzas = json.load(f)

# Secciones disponibles en el shapefile
secs_disponibles = {
    int(f["properties"]["SECCION"])
    for f in secs["features"]
    if f["properties"].get("SECCION")
}

# Manzanas de la sección 3072
mzas_3072 = [
    f for f in mzas["features"]
    if int(f["properties"].get("SECCION", 0)) == 3072
]

print(f"3072 en shapefile de secciones : {3072 in secs_disponibles}")
print(f"Manzanas de 3072 en unificado  : {len(mzas_3072)}")

if mzas_3072:
    p = mzas_3072[0]["properties"]
    print(f"  LN real sección    : {p.get('LN_real_seccion')}")
    print(f"  Prioritarias       : {sum(1 for m in mzas_3072 if m['properties'].get('es_prioritaria'))}")
    geom_nulas = sum(1 for m in mzas_3072 if m.get('geometry') is None)
    print(f"  Geometrías nulas   : {geom_nulas}")