import osmnx as ox
import json

G = ox.graph_from_place(
    "La Magdalena Contreras, Ciudad de México, México",
    network_type="all"
)

# Exportar como GeoJSON sin usar geopandas ni to_file
geojson_data = ox.graph_to_gdfs(G, nodes=False).__geo_interface__

with open("data/calles_contreras.geojson", "w", encoding="utf-8") as f:
    json.dump(geojson_data, f, ensure_ascii=False)

print("Guardado: data/calles_contreras.geojson")