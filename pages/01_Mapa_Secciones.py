"""
01_Mapa_Secciones.py — PIE · Mapa interactivo de secciones electorales
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import geopandas as gpd
import json
from app_utils import (
    verificar_acceso, aplicar_estilos, header, kpi,
    cargar_ranking, cargar_secciones, cargar_unificado,
    color_ire, badge_nivel, es_nucleo,
    COLOR_ALTA, COLOR_MEDIA, COLOR_BAJA, COLOR_MORENA,
    COLOR_TARJETA, COLOR_TEXTO, COLOR_SECUNDARIO,
    NIVEL_LABEL, PROYECTO,
)

st.set_page_config(
    page_title="Mapa de Secciones · PIE",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)
aplicar_estilos()
if not verificar_acceso():
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='padding:1rem 0 0.5rem;'>
        <p style='color:{COLOR_ALTA};font-size:0.72rem;letter-spacing:0.12em;
                  text-transform:uppercase;margin:0;'>PIE</p>
        <p style='color:{COLOR_TEXTO};font-size:1rem;font-weight:600;margin:0.2rem 0;'>
            La Magdalena Contreras</p>
    </div>
    <hr style='border:none;border-top:1px solid #3a1010;margin:0.8rem 0;'>
    """, unsafe_allow_html=True)
    st.page_link("Home.py",                      label="🏠  Inicio")
    st.page_link("pages/01_Mapa_Secciones.py",   label="🗺️  Mapa de secciones")
    st.page_link("pages/02_Mapa_Manzanas.py",    label="📍  Mapa de manzanas")
    st.page_link("pages/03_Ranking.py",           label="📊  Ranking y ficha")
    st.markdown("<hr style='border:none;border-top:1px solid #3a1010;margin:1rem 0;'>",
                unsafe_allow_html=True)

    st.markdown(f"<p style='color:{COLOR_TEXTO};font-size:0.85rem;font-weight:600;margin-bottom:0.5rem;'>Filtros</p>",
                unsafe_allow_html=True)

    mostrar = st.multiselect(
        "Mostrar secciones",
        options=["Núcleo prioritario (top 25)", "Extensión operativa (26–59)", "Zona de referencia"],
        default=["Núcleo prioritario (top 25)", "Extensión operativa (26–59)"],
    )
    capa_color = st.radio(
        "Colorear por",
        options=["Probabilidad de encuesta", "Fuerza Morena", "Índice Rentabilidad"],
        index=0,
    )

    if st.button("Cerrar sesión", use_container_width=True):
        from app_utils import cerrar_sesion
        cerrar_sesion()

# ── Header ────────────────────────────────────────────────────────────────────
header("Mapa de Secciones", "Distribución territorial de la priorización operativa")

# ── Cargar datos ──────────────────────────────────────────────────────────────
rank = cargar_ranking()
secs = cargar_secciones()

p3   = rank[(rank["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA") & (rank["SECCION"]>0)].copy()
p3["es_nucleo"] = p3["RANK_ESTRATEGICO"] <= 25

# Merge secciones con ranking.
# Del CSV de ranking solo traemos las columnas exclusivas del pipeline MC;
# GANADOR_2024, MARGEN_PCT_2024, PARTICIPACION_2024 y LN_TOTAL ya vienen
# en el GeoJSON de secciones — incluirlas del CSV generaría sufijos _x/_y.
COLS_RANK = ["SECCION", "IRE_SCORE", "NIVEL_PRIORIDAD_OP",
             "INDICE_RENTABILIDAD", "fuerza_morena", "RANK_ESTRATEGICO"]
cols_rank_ok = [c for c in COLS_RANK if c in rank.columns]  # defensivo
secs_m = secs.merge(rank[cols_rank_ok], on="SECCION", how="left")
secs_m = secs_m.to_crs("EPSG:4326")
secs_m["es_nucleo"] = secs_m["RANK_ESTRATEGICO"].apply(
    lambda r: r<=25 if pd.notna(r) else False)

# Aplicar filtro
filtro_niveles = []
if "Núcleo prioritario (top 25)"    in mostrar: filtro_niveles += list(p3[p3["es_nucleo"]]["SECCION"])
if "Extensión operativa (26–59)"    in mostrar: filtro_niveles += list(p3[~p3["es_nucleo"]]["SECCION"])
if "Zona de referencia"             in mostrar:
    filtro_niveles += list(rank[rank["NIVEL_PRIORIDAD_OP"]=="P4_BAJA"]["SECCION"])

secs_vis = secs_m[secs_m["SECCION"].isin(filtro_niveles)]

# ── Mapa folium ───────────────────────────────────────────────────────────────
m = folium.Map(
    location=[PROYECTO["lat_centro"], PROYECTO["lon_centro"]],
    zoom_start=PROYECTO["zoom"],
    tiles="CartoDB positron",
    control_scale=True,
)

# Columna de color según selección
col_map = {
    "Probabilidad de encuesta": "IRE_SCORE",
    "Fuerza Morena":            "fuerza_morena",
    "Índice Rentabilidad":      "INDICE_RENTABILIDAD",
}
col_val = col_map[capa_color]

ire_vals = secs_vis[col_val].dropna()
vmin = float(ire_vals.min()) if len(ire_vals) else 0.0
vmax = float(ire_vals.max()) if len(ire_vals) else 1.0

for _, row in secs_vis.iterrows():
    val    = row.get(col_val)
    nivel  = row.get("NIVEL_PRIORIDAD_OP","")
    rnk    = row.get("RANK_ESTRATEGICO")
    nucleo = row.get("es_nucleo", False)

    fill   = color_ire(val, vmin, vmax) if pd.notna(val) else COLOR_BAJA
    border = COLOR_ALTA if nucleo else (COLOR_MEDIA if nivel=="P3_MEDIA" else COLOR_BAJA)
    weight = 2.5 if nucleo else 1.2

    # Tooltip enriquecido
    ganador = row.get("GANADOR_2024","—") or "—"
    margen  = row.get("MARGEN_PCT_2024")
    margen_str = f"{margen*100:+.1f} pp" if pd.notna(margen) else "—"
    part    = row.get("PARTICIPACION_2024")
    part_str = f"{part*100:.1f}%" if pd.notna(part) else "—"
    ln_str  = f"{row.get('LN_TOTAL',0):,.0f}" if pd.notna(row.get("LN_TOTAL")) else "—"
    ire_str  = f"{row.get('IRE_SCORE',0):.3f}" if pd.notna(row.get("IRE_SCORE")) else "—"
    rent_str = f"{row.get('INDICE_RENTABILIDAD',0):.3f}" if pd.notna(row.get("INDICE_RENTABILIDAD")) else "—"
    fm_str   = f"{row.get('fuerza_morena',0)*100:.1f}%" if pd.notna(row.get("fuerza_morena")) else "—"
    etiqueta = f"{'★ NÚCLEO #'+str(int(rnk)) if nucleo and pd.notna(rnk) else ('Ext. #'+str(int(rnk)) if pd.notna(rnk) else 'Sin ranking')}"

    tooltip = f"""
    <div style='font-family:sans-serif;font-size:12px;min-width:200px;'>
        <b style='font-size:13px;'>Sección {int(row['SECCION'])}</b>
        &nbsp;<span style='color:{"#C1272D" if nucleo else "#8B1A1A"};font-size:11px;'>{etiqueta}</span><br>
        <hr style='margin:4px 0;border:none;border-top:1px solid #ccc;'>
        <b>Lista Nominal:</b> {ln_str}<br>
        <b>Prob. encuesta:</b> {ire_str}<br>
        <b>Índice Rentabilidad:</b> {rent_str}<br>
        <b>Fuerza Morena:</b> {fm_str}<br>
        <hr style='margin:4px 0;border:none;border-top:1px solid #ccc;'>
        <b>Ganador 2024:</b> {ganador}<br>
        <b>Margen 2024:</b> {margen_str}<br>
        <b>Participación 2024:</b> {part_str}
    </div>
    """

    try:
        geom_json = json.loads(gpd.GeoSeries([row.geometry]).to_json())
        folium.GeoJson(
            geom_json,
            style_function=lambda x, f=fill, b=border, w=weight: {
                "fillColor": f, "fillOpacity": 0.65,
                "color": b, "weight": w,
            },
            tooltip=folium.Tooltip(tooltip, sticky=True),
        ).add_to(m)
    except Exception:
        pass

col_mapa, col_panel = st.columns([3, 1])

with col_mapa:
    st_folium(m, width="100%", height=550, returned_objects=[])

with col_panel:
    # KPIs laterales
    secs_p3_vis = secs_vis[secs_vis["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA"]
    nucleo_vis  = secs_p3_vis[secs_p3_vis["es_nucleo"]==True]

    kpi("Secciones visibles", str(len(secs_vis)), color=COLOR_MEDIA)
    kpi("Núcleo visible",     str(len(nucleo_vis)), color=COLOR_ALTA)

    if len(secs_p3_vis):
        ire_med = secs_p3_vis["IRE_SCORE"].mean()
        kpi("Prob. promedio", f"{ire_med:.3f}", color=COLOR_MEDIA)

    st.markdown(f"""
    <div style='background:{COLOR_TARJETA};border-radius:6px;padding:1rem;margin-top:0.5rem;'>
        <p style='color:{COLOR_TEXTO};font-size:0.82rem;font-weight:600;margin:0 0 0.5rem;'>
            Leyenda
        </p>
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>
            <div style='width:14px;height:14px;background:{COLOR_ALTA};border-radius:2px;flex-shrink:0;'></div>
            <span style='color:{COLOR_SECUNDARIO};font-size:0.78rem;'>Alta probabilidad</span>
        </div>
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>
            <div style='width:14px;height:14px;background:{COLOR_MEDIA};border-radius:2px;flex-shrink:0;'></div>
            <span style='color:{COLOR_SECUNDARIO};font-size:0.78rem;'>Probabilidad media</span>
        </div>
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>
            <div style='width:14px;height:14px;background:{COLOR_BAJA};border-radius:2px;flex-shrink:0;'></div>
            <span style='color:{COLOR_SECUNDARIO};font-size:0.78rem;'>Zona de referencia</span>
        </div>
        <p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;margin:0.6rem 0 0;'>
            Borde ámbar = núcleo prioritario (top 25)<br>
            Hover sobre cualquier sección para ver detalle.
        </p>
    </div>
    """, unsafe_allow_html=True)