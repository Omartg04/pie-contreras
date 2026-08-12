import pandas as pd
import json

# CSV de ranking
rank = pd.read_csv("data/pie_010_mc_ranking.csv")
print("=== RANKING CSV ===")
print(rank.columns.tolist())

# GeoJSON de secciones — como JSON puro
with open("data/pie_010_mc_secciones.geojson", encoding="utf-8") as f:
    secs_raw = json.load(f)
props_sec = list(secs_raw["features"][0]["properties"].keys())
print("\n=== SECCIONES GEOJSON — propiedades ===")
print(props_sec)

# GeoJSON unificado (manzanas)
with open("data/pie_010_mc_unificado.geojson", encoding="utf-8") as f:
    uni_raw = json.load(f)
props_uni = list(uni_raw["features"][0]["properties"].keys())
print("\n=== UNIFICADO GEOJSON — propiedades ===")
print(props_uni)