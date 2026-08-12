"""
01_Mapa_Secciones.py — PIE · Mapa interactivo de secciones electorales
"""
import streamlit as st
import folium
import branca.colormap as cm
from streamlit_folium import st_folium
import pandas as pd
import geopandas as gpd
import json
from app_utils import (
    verificar_acceso, aplicar_estilos, header, kpi,
    cargar_ranking, cargar_secciones, cargar_unificado,
    color_ire, badge_nivel, es_nucleo,
    COLOR_ALTA, COLOR_ACENTO, COLOR_MEDIA, COLOR_BAJA, COLOR_MORENA,
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
        <p style='color:{COLOR_ACENTO};font-size:0.72rem;letter-spacing:0.12em;
                  text-transform:uppercase;margin:0;'>PIE</p>
        <p style='color:{COLOR_TEXTO};font-size:1rem;font-weight:600;margin:0.2rem 0;'>
            La Magdalena Contreras</p>
    </div>
    <hr style='border:none;border-top:1px solid #3a1010;margin:0.8rem 0;'>
    """, unsafe_allow_html=True)
    st.page_link("Home.py",                      label="🏠  Inicio")
    st.page_link("pages/01_Mapa_Secciones.py",   label="🗺️  Mapa de secciones")
    st.page_link("pages/02_Mapa_Manzanas.py",    label="📍  Mapa de manzanas")
    st.page_link("pages/03_Ranking.py",           label="🔍  Fichas de sección")
    st.markdown("<hr style='border:none;border-top:1px solid #3a1010;margin:1rem 0;'>",
                unsafe_allow_html=True)

    st.markdown(f"<p style='color:{COLOR_TEXTO};font-size:0.85rem;font-weight:600;margin-bottom:0.5rem;'>Filtros</p>",
                unsafe_allow_html=True)

    # ── Filtro de secciones — radio con narrativa progresiva ──────────────────
    mostrar = st.radio(
        "Secciones a mostrar",
        options=["Todas (148)", "59 más prioritarias", "25 núcleo operativo"],
        index=0,
    )

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    # ── Colorear por — con descripción dinámica ───────────────────────────────
    capa_color = st.radio(
        "Colorear por",
        options=["Probabilidad de encuesta", "Fuerza Morena", "Índice Rentabilidad"],
        index=0,
    )

    # Descripción dinámica según selección
    descripciones = {
        "Probabilidad de encuesta": "Secciones con mayor probabilidad de ser incluidas en la muestra de cualquier levantamiento externo probabilístico.",
        "Fuerza Morena":            "% del padrón registrado que votó Morena en 2024. No sobre votos emitidos — sobre lista nominal total.",
        "Índice Rentabilidad":      "Combina probabilidad de encuesta y fuerza Morena. El criterio de orden operativo del ranking.",
    }
    st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.76rem;line-height:1.5;margin-top:0.3rem;'>{descripciones[capa_color]}</p>",
                unsafe_allow_html=True)

    st.markdown("<hr style='border:none;border-top:1px solid #3a1010;margin:1rem 0;'>",
                unsafe_allow_html=True)
    if st.button("Cerrar sesión", use_container_width=True):
        from app_utils import cerrar_sesion
        cerrar_sesion()

# ── Header ────────────────────────────────────────────────────────────────────
header("Mapa de Secciones", "Distribución territorial de la priorización operativa")

# ── Cargar datos ──────────────────────────────────────────────────────────────
rank = cargar_ranking()
secs = cargar_secciones()
gdf  = cargar_unificado()   # para manzanas prioritarias por sección

p3 = rank[(rank["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA") & (rank["SECCION"]>0)].copy()
p3["es_nucleo"] = p3["RANK_ESTRATEGICO"].apply(lambda r: r <= 26)  # proxy ocupa #1

# Traer n_manzanas_sec del ranking si existe
cols_rank = ["SECCION", "IRE_SCORE", "NIVEL_PRIORIDAD_OP",
             "INDICE_RENTABILIDAD", "fuerza_morena", "RANK_ESTRATEGICO"]
if "n_manzanas_sec" in rank.columns:
    cols_rank.append("n_manzanas_sec")
cols_rank_ok = [c for c in cols_rank if c in rank.columns]

secs_m = secs.merge(rank[cols_rank_ok], on="SECCION", how="left")
secs_m = secs_m.to_crs("EPSG:4326")
secs_m["es_nucleo"] = secs_m["RANK_ESTRATEGICO"].apply(
    lambda r: r <= 26 if pd.notna(r) else False)

# Manzanas prioritarias por sección (para KPI panel)
mzas_prio_x_sec = (
    gdf[gdf["es_prioritaria_s1"]==True]
    .groupby("SECCION")
    .size()
    .reset_index(name="n_mzas_prio")
)
secs_m = secs_m.merge(mzas_prio_x_sec, on="SECCION", how="left")
secs_m["n_mzas_prio"] = secs_m["n_mzas_prio"].fillna(0).astype(int)

# ── Aplicar filtro de secciones ───────────────────────────────────────────────
if mostrar == "25 núcleo operativo":
    secs_vis = secs_m[secs_m["es_nucleo"]==True].copy()
elif mostrar == "59 más prioritarias":
    secs_vis = secs_m[secs_m["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA"].copy()
else:  # Todas (148) — default
    secs_vis = secs_m[secs_m["SECCION"]>0].copy()

# ── Mapa folium ───────────────────────────────────────────────────────────────
m = folium.Map(
    location=[PROYECTO["lat_centro"], PROYECTO["lon_centro"]],
    zoom_start=PROYECTO["zoom"],
    tiles="CartoDB positron",
    control_scale=True,
)

col_map = {
    "Probabilidad de encuesta": "IRE_SCORE",
    "Fuerza Morena":            "fuerza_morena",
    "Índice Rentabilidad":      "INDICE_RENTABILIDAD",
}
col_val = col_map[capa_color]

vals = secs_vis[col_val].dropna()
vmin = float(vals.min()) if len(vals) else 0.0
vmax = float(vals.max()) if len(vals) else 1.0

# ── Barra de color en el mapa (branca colormap) ───────────────────────────────
colormap = cm.LinearColormap(
    colors=["#cccccc", "#8B4A52", "#6A1B29"],
    vmin=vmin, vmax=vmax,
    caption=capa_color,
)
colormap.add_to(m)

# ── Renderizar secciones ──────────────────────────────────────────────────────
for _, row in secs_vis.iterrows():
    val    = row.get(col_val)
    nivel  = row.get("NIVEL_PRIORIDAD_OP", "")
    rnk    = row.get("RANK_ESTRATEGICO")
    nucleo = row.get("es_nucleo", False)

    fill    = color_ire(val, vmin, vmax) if pd.notna(val) else "#cccccc"
    opacity = 0.75 if nivel == "P3_MEDIA" else 0.45
    border  = COLOR_ALTA if nucleo else ("#8B1A1A" if nivel=="P3_MEDIA" else "#aaaaaa")
    weight  = 2.5 if nucleo else (1.2 if nivel=="P3_MEDIA" else 0.6)

    # Etiqueta de ranking
    if nucleo and pd.notna(rnk):
        etiqueta = f"★ NÚCLEO #{int(rnk)}"
    elif pd.notna(rnk) and nivel == "P3_MEDIA":
        etiqueta = f"Ext. #{int(rnk)}"
    else:
        etiqueta = "Referencia"

    # Datos para tooltip
    ln_str   = f"{row.get('LN_TOTAL', 0):,.0f}"   if pd.notna(row.get("LN_TOTAL"))           else "—"
    ire_str  = f"{row.get('IRE_SCORE', 0):.3f}"   if pd.notna(row.get("IRE_SCORE"))           else "—"
    rent_str = f"{row.get('INDICE_RENTABILIDAD',0):.3f}" if pd.notna(row.get("INDICE_RENTABILIDAD")) else "—"
    fm_str   = f"{row.get('fuerza_morena',0)*100:.1f}%" if pd.notna(row.get("fuerza_morena")) else "—"
    ganador  = row.get("GANADOR_2024", "—") or "—"
    margen   = row.get("MARGEN_PCT_2024")
    margen_str = f"{margen*100:+.1f} pp" if pd.notna(margen) else "—"
    part     = row.get("PARTICIPACION_2024")
    part_str = f"{part*100:.1f}%"         if pd.notna(part)   else "—"
    n_mzas   = int(row.get("n_mzas_prio", 0))
    n_mzas_str = str(n_mzas) if n_mzas > 0 else "—"

    color_etiq = "#6A1B29" if nucleo else ("#8B1A1A" if nivel=="P3_MEDIA" else "#777777")

    tooltip = f"""
    <div style='font-family:sans-serif;font-size:12px;min-width:210px;'>
        <b style='font-size:13px;'>Sección {int(row['SECCION'])}</b>
        &nbsp;<span style='color:{color_etiq};font-size:11px;'>{etiqueta}</span><br>
        <hr style='margin:4px 0;border:none;border-top:1px solid #ddd;'>
        <b>Lista Nominal:</b> {ln_str}<br>
        <b>Manzanas prioritarias:</b> {n_mzas_str}<br>
        <hr style='margin:4px 0;border:none;border-top:1px solid #ddd;'>
        <b>Prob. encuesta:</b> {ire_str}<br>
        <b>Índice Rentabilidad:</b> {rent_str}<br>
        <b>Fuerza Morena:</b> {fm_str}<br>
        <hr style='margin:4px 0;border:none;border-top:1px solid #ddd;'>
        <b>Ganador 2024:</b> {ganador}<br>
        <b>Margen 2024:</b> {margen_str}<br>
        <b>Participación 2024:</b> {part_str}
    </div>
    """

    try:
        geom_json = json.loads(gpd.GeoSeries([row.geometry]).to_json())
        folium.GeoJson(
            geom_json,
            style_function=lambda x, f=fill, b=border, w=weight, o=opacity: {
                "fillColor": f, "fillOpacity": o,
                "color": b, "weight": w,
            },
            tooltip=folium.Tooltip(tooltip, sticky=True),
        ).add_to(m)
    except Exception:
        pass

# ── Layout: mapa + panel ──────────────────────────────────────────────────────
col_mapa, col_panel = st.columns([3, 1])

with col_mapa:
    st_folium(m, width="100%", height=560, returned_objects=[])

with col_panel:
    # KPIs del panel
    secs_p3_vis  = secs_vis[secs_vis["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA"]
    nucleo_vis   = secs_vis[secs_vis["es_nucleo"]==True]
    ln_vis       = secs_vis["LN_TOTAL"].sum() if "LN_TOTAL" in secs_vis.columns else 0
    mzas_vis_tot = secs_vis["n_mzas_prio"].sum()

    kpi("Secciones visibles",    str(len(secs_vis)),          color=COLOR_MEDIA)
    kpi("Núcleo visible",        str(len(nucleo_vis)),         color=COLOR_ALTA)
    kpi("Lista Nominal visible", f"{int(ln_vis):,}",          color=COLOR_MEDIA)
    kpi("Manzanas prioritarias", str(int(mzas_vis_tot)),
        "en secciones visibles", COLOR_ACENTO)

    if len(secs_p3_vis):
        ire_med = secs_p3_vis["IRE_SCORE"].mean()
        kpi("Prob. promedio", f"{ire_med:.3f}",
            "secciones operativas visibles", COLOR_MEDIA)

    # Leyenda del gradiente
    st.markdown(f"""
    <div style='background:{COLOR_TARJETA};border-radius:6px;padding:0.9rem;margin-top:0.6rem;'>
        <p style='color:{COLOR_TEXTO};font-size:0.82rem;font-weight:600;margin:0 0 0.6rem;'>
            Leyenda
        </p>
        <div style='background:linear-gradient(to right,#cccccc,#8B4A52,#6A1B29);
                    height:10px;border-radius:4px;margin-bottom:4px;'></div>
        <div style='display:flex;justify-content:space-between;'>
            <span style='color:{COLOR_SECUNDARIO};font-size:0.70rem;'>Menor</span>
            <span style='color:{COLOR_SECUNDARIO};font-size:0.70rem;'>Mayor</span>
        </div>
        <p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;margin:0.6rem 0 0;line-height:1.5;'>
            Borde guinda grueso = núcleo top 25<br>
            Borde guinda fino = extensión operativa<br>
            Borde gris = sección de referencia<br><br>
            Hover sobre cualquier sección para ver detalle.
        </p>
    </div>
    """, unsafe_allow_html=True)