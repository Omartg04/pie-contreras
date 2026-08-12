"""
02_Mapa_Manzanas.py — PIE · Mapa interactivo de manzanas prioritarias
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import geopandas as gpd
import json
from app_utils import (
    verificar_acceso, aplicar_estilos, header, kpi,
    cargar_unificado, cargar_ranking,
    color_ire,
    COLOR_ALTA, COLOR_MEDIA, COLOR_BAJA, COLOR_MORENA,
    COLOR_TARJETA, COLOR_TEXTO, COLOR_SECUNDARIO,
    PROYECTO,
)

st.set_page_config(
    page_title="Mapa de Manzanas · PIE",
    page_icon="📍",
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
    <hr style='border:none;border-top:1px solid #2a3550;margin:0.8rem 0;'>
    """, unsafe_allow_html=True)
    st.page_link("Home.py",                      label="🏠  Inicio")
    st.page_link("pages/01_Mapa_Secciones.py",   label="🗺️  Mapa de secciones")
    st.page_link("pages/02_Mapa_Manzanas.py",    label="📍  Mapa de manzanas")
    st.page_link("pages/03_Ranking.py",           label="📊  Ranking y ficha")
    st.markdown("<hr style='border:none;border-top:1px solid #2a3550;margin:1rem 0;'>",
                unsafe_allow_html=True)

    st.markdown(f"<p style='color:{COLOR_TEXTO};font-size:0.85rem;font-weight:600;margin-bottom:0.5rem;'>Filtros</p>",
                unsafe_allow_html=True)

    rank = cargar_ranking()
    p3_secs = sorted(
        rank[(rank["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA") & (rank["SECCION"]>0)]
        .sort_values("RANK_ESTRATEGICO")["SECCION"].tolist()
    )
    sec_opts = ["Todas las secciones P3"] + [str(s) for s in p3_secs]
    sec_sel  = st.selectbox("Sección", options=sec_opts)

    solo_prioritarias = st.checkbox("Solo manzanas prioritarias S1", value=True)
    mostrar_hallazgo  = st.checkbox("Mostrar manzanas destacadas (IRE alto)", value=True)

    if st.button("Cerrar sesión", use_container_width=True):
        from app_utils import cerrar_sesion
        cerrar_sesion()

# ── Header ────────────────────────────────────────────────────────────────────
header("Mapa de Manzanas", "Priorización a nivel de manzana — corte 50% LN por sección")

# ── Cargar datos ──────────────────────────────────────────────────────────────
gdf  = cargar_unificado()

# Filtrar por sección seleccionada
if sec_sel == "Todas las secciones P3":
    mzas = gdf[gdf["SECCION"].isin(p3_secs)].copy()
else:
    sec_id = int(sec_sel)
    mzas   = gdf[gdf["SECCION"] == sec_id].copy()

# Aplicar filtros adicionales
if solo_prioritarias:
    mzas_vis = mzas[mzas["es_prioritaria_s1"] == True].copy()
else:
    mzas_vis = mzas.copy()

mzas_vis = mzas_vis.to_crs("EPSG:4326")

# ── KPIs ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi("Manzanas visibles", f"{len(mzas_vis):,}", color=COLOR_MEDIA)
with c2:
    ln_vis = mzas_vis["LN_estimada"].sum()
    kpi("LN cubierta", f"{ln_vis:,.0f}", color=COLOR_MEDIA)
with c3:
    hall_vis = mzas_vis[
        (mzas_vis.get("NIVEL_MZA","") == "MA_ALTA") &
        (mzas_vis["es_prioritaria_s1"] != True)
    ] if "NIVEL_MZA" in mzas_vis.columns else pd.DataFrame()
    kpi("Manzanas destacadas", str(len(hall_vis)), "IRE alto fuera del corte", COLOR_MORENA)
with c4:
    if "IRE_MZA" in mzas_vis.columns and mzas_vis["IRE_MZA"].notna().any():
        ire_med = mzas_vis["IRE_MZA"].mean()
        kpi("Prob. media manzana", f"{ire_med:.3f}", color=COLOR_ALTA)
    else:
        kpi("Sección", sec_sel, color=COLOR_ALTA)

# ── Mapa folium ───────────────────────────────────────────────────────────────
# Centro del mapa
if len(mzas_vis):
    bounds = mzas_vis.total_bounds
    lat_c  = (bounds[1] + bounds[3]) / 2
    lon_c  = (bounds[0] + bounds[2]) / 2
    zoom   = 15 if sec_sel != "Todas las secciones P3" else PROYECTO["zoom"]
else:
    lat_c, lon_c, zoom = PROYECTO["lat_centro"], PROYECTO["lon_centro"], PROYECTO["zoom"]

m = folium.Map(
    location=[lat_c, lon_c],
    zoom_start=zoom,
    tiles="CartoDB dark_matter",
)

ire_vals = mzas_vis["IRE_MZA"].dropna() if "IRE_MZA" in mzas_vis.columns else pd.Series([0.1, 0.6])
vmin = float(ire_vals.min()) if len(ire_vals) else 0.0
vmax = float(ire_vals.max()) if len(ire_vals) else 1.0

# Manzanas no prioritarias como fondo (gris, sin tooltip)
if not solo_prioritarias:
    mzas_bg = mzas[mzas["es_prioritaria_s1"] != True].to_crs("EPSG:4326")
    for _, row in mzas_bg.iterrows():
        try:
            geom_json = json.loads(gpd.GeoSeries([row.geometry]).to_json())
            folium.GeoJson(
                geom_json,
                style_function=lambda x: {
                    "fillColor": "#2e3a52", "fillOpacity": 0.4,
                    "color": "#3a4d6e", "weight": 0.4,
                },
            ).add_to(m)
        except Exception:
            pass

# Manzanas prioritarias con color por IRE
for _, row in mzas_vis.iterrows():
    ire_mza  = row.get("IRE_MZA")
    es_hall  = (row.get("NIVEL_MZA")=="MA_ALTA") and (not row.get("es_prioritaria_s1", True))
    es_prio  = row.get("es_prioritaria_s1", False)

    if es_hall and mostrar_hallazgo:
        fill   = COLOR_MORENA
        border = COLOR_MORENA
        weight = 2.0
        opacity = 0.75
    elif es_prio:
        fill   = color_ire(ire_mza, vmin, vmax) if pd.notna(ire_mza) else COLOR_MEDIA
        border = "white"
        weight = 1.2
        opacity = 0.80
    else:
        continue

    ln_val  = row.get("LN_estimada", 0)
    rk_val  = row.get("ranking_seccion", "—")
    sec_val = row.get("SECCION", "—")
    ire_str = f"{ire_mza:.3f}" if pd.notna(ire_mza) else "—"
    tipo    = "★ Manzana destacada" if es_hall else f"Manzana M{int(rk_val) if pd.notna(rk_val) else '?'}"

    tooltip = f"""
    <div style='font-family:sans-serif;font-size:12px;min-width:180px;'>
        <b>{tipo}</b><br>
        Sección: {int(sec_val) if pd.notna(sec_val) else '—'}<br>
        <hr style='margin:3px 0;border:none;border-top:1px solid #ccc;'>
        <b>LN estimada:</b> {ln_val:,.0f}<br>
        <b>Prob. encuesta manzana:</b> {ire_str}<br>
        <b>Tipo INEGI:</b> {row.get("TIPOMZA","—")}
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

col_mapa, col_panel = st.columns([3, 1])

with col_mapa:
    st_folium(m, width="100%", height=530, returned_objects=[])

with col_panel:
    st.markdown(f"""
    <div style='background:{COLOR_TARJETA};border-radius:6px;padding:1rem;margin-bottom:0.8rem;'>
        <p style='color:{COLOR_TEXTO};font-size:0.82rem;font-weight:600;margin:0 0 0.7rem;'>
            Leyenda
        </p>
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>
            <div style='width:14px;height:14px;background:{COLOR_ALTA};border-radius:2px;flex-shrink:0;'></div>
            <span style='color:{COLOR_SECUNDARIO};font-size:0.78rem;'>Alta prob. encuesta</span>
        </div>
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>
            <div style='width:14px;height:14px;background:{COLOR_MEDIA};border-radius:2px;flex-shrink:0;'></div>
            <span style='color:{COLOR_SECUNDARIO};font-size:0.78rem;'>Media prob. encuesta</span>
        </div>
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>
            <div style='width:14px;height:14px;background:{COLOR_MORENA};border-radius:2px;flex-shrink:0;'></div>
            <span style='color:{COLOR_SECUNDARIO};font-size:0.78rem;'>Manzana destacada ★</span>
        </div>
        <div style='display:flex;align-items:center;gap:8px;'>
            <div style='width:14px;height:14px;background:#2e3a52;border-radius:2px;flex-shrink:0;'></div>
            <span style='color:{COLOR_SECUNDARIO};font-size:0.78rem;'>Sin prioridad</span>
        </div>
        <p style='color:{COLOR_SECUNDARIO};font-size:0.70rem;margin:0.8rem 0 0;line-height:1.5;'>
            <b style='color:{COLOR_MORENA};'>Manzana destacada:</b> IRE alto fuera del corte de LN —
            no habría aparecido en un ranking estándar por tamaño de padrón.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Top manzanas de la vista actual
    if len(mzas_vis) > 0 and "IRE_MZA" in mzas_vis.columns:
        top_mzas = mzas_vis[mzas_vis["IRE_MZA"].notna()].nlargest(8, "IRE_MZA")[
            ["SECCION","ranking_seccion","LN_estimada","IRE_MZA"]
        ].copy()
        top_mzas.columns = ["Sección","Rk","LN","IRE"]
        top_mzas["LN"]  = top_mzas["LN"].apply(lambda x: f"{x:,.0f}")
        top_mzas["IRE"] = top_mzas["IRE"].apply(lambda x: f"{x:.3f}")
        top_mzas["Rk"]  = top_mzas["Rk"].apply(lambda x: f"M{int(x)}" if pd.notna(x) else "—")

        st.markdown(f"<p style='color:{COLOR_TEXTO};font-size:0.82rem;font-weight:600;margin-bottom:0.3rem;'>Top manzanas visibles</p>",
                    unsafe_allow_html=True)
        st.dataframe(top_mzas, use_container_width=True, hide_index=True, height=240)
