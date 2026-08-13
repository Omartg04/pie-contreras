"""
02_Mapa_Manzanas.py — PIE · Mapa interactivo de manzanas prioritarias
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
    cargar_unificado, cargar_ranking, cargar_secciones,
    COLOR_ALTA, COLOR_ACENTO, COLOR_MEDIA, COLOR_BAJA, COLOR_MORENA,
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

# ── Cargar datos (fuera del sidebar para usarlos en el selector) ──────────────
rank = cargar_ranking()
gdf  = cargar_unificado()
secs = cargar_secciones()

# Clasificar secciones
p3 = rank[(rank["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA") & (rank["SECCION"]>0)].copy()
p3["es_nucleo"] = p3["RANK_ESTRATEGICO"].apply(lambda r: r <= 26)
nucleo_secs    = set(p3[p3["es_nucleo"]]["SECCION"].tolist())
operativas_secs= set(p3["SECCION"].tolist())
todas_secs     = set(rank[rank["SECCION"]>0]["SECCION"].tolist())

# Opciones del selector de sección (148 secciones etiquetadas)
def _label_seccion(sec):
    row = rank[rank["SECCION"]==sec]
    if row.empty or row.iloc[0]["NIVEL_PRIORIDAD_OP"] != "P3_MEDIA":
        return f"Sección {sec} — Referencia"
    rnk = int(row.iloc[0]["RANK_ESTRATEGICO"])
    tag = f"★ Núcleo #{rnk}" if rnk <= 26 else f"Extensión #{rnk}"
    return f"Sección {sec} — {tag}"

secs_ordenadas = sorted(todas_secs)
opciones_sec   = ["— Ver universo completo"] + [_label_seccion(s) for s in secs_ordenadas]
sec_id_map     = {_label_seccion(s): s for s in secs_ordenadas}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='padding:1rem 0 0.5rem;'>
        <p style='color:{COLOR_ACENTO};font-size:0.72rem;letter-spacing:0.12em;
                  text-transform:uppercase;margin:0;'>PIE</p>
        <p style='color:{COLOR_TEXTO};font-size:1rem;font-weight:600;margin:0.2rem 0;'>
            La Magdalena Contreras</p>
        <p style='color:{COLOR_ACENTO};font-weight:600; font-size:0.78rem; margin:0;'>
            Bernardo Aguilar 2027
    </div>
    <hr style='border:none;border-top:1px solid #3a1010;margin:0.8rem 0;'>
    """, unsafe_allow_html=True)
    st.page_link("Home.py",                    label="🏠  Inicio")
    st.page_link("pages/01_Mapa_Secciones.py", label="🗺️  Mapa de secciones")
    st.page_link("pages/02_Mapa_Manzanas.py",  label="📍  Mapa de manzanas")
    st.page_link("pages/03_Ranking.py",        label="🔍  Fichas de sección")
    st.markdown("<hr style='border:none;border-top:1px solid #3a1010;margin:1rem 0;'>",
                unsafe_allow_html=True)

    st.markdown(f"<p style='color:{COLOR_TEXTO};font-size:0.85rem;font-weight:600;margin-bottom:0.5rem;'>Filtros</p>",
                unsafe_allow_html=True)

    # Radio — universo de secciones
    universo = st.radio(
        "Secciones a incluir",
        options=["Todas (148)", "59 operativas", "25 núcleo"],
        index=0,
    )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # Selector de sección — siempre visible, opcional
    sec_sel_label = st.selectbox(
        "Navegar a una sección",
        options=opciones_sec,
        index=0,
    )
    sec_sel = sec_id_map.get(sec_sel_label)  # None si "Ver universo completo"

    st.markdown(f"""
    <p style='color:{COLOR_SECUNDARIO};font-size:0.74rem;line-height:1.5;margin-top:0.2rem;'>
        Al seleccionar una sección el mapa hace zoom automático
        y el panel muestra su ficha.
    </p>""", unsafe_allow_html=True)

    st.markdown("<hr style='border:none;border-top:1px solid #3a1010;margin:1rem 0;'>",
                unsafe_allow_html=True)
    if st.button("Cerrar sesión", use_container_width=True):
        from app_utils import cerrar_sesion
        cerrar_sesion()

# ── Header ────────────────────────────────────────────────────────────────────
header("Mapa de Manzanas", "Priorización a nivel de manzana — corte 50% LN por sección")

# ── Filtrar manzanas según universo seleccionado ──────────────────────────────
if universo == "25 núcleo":
    secs_activas = nucleo_secs
elif universo == "59 operativas":
    secs_activas = operativas_secs
else:
    secs_activas = todas_secs

mzas_universo = gdf[gdf["SECCION"].isin(secs_activas)].copy()
mzas_universo = mzas_universo.to_crs("EPSG:4326")

# Clasificar manzanas
mzas_prio  = mzas_universo[mzas_universo["es_prioritaria_s1"]==True].copy()
mzas_dest  = mzas_universo[
    (mzas_universo.get("NIVEL_MZA", pd.Series(dtype=str)) == "MA_ALTA") &
    (mzas_universo["es_prioritaria_s1"]!=True)
] if "NIVEL_MZA" in mzas_universo.columns else pd.DataFrame()
mzas_resto = mzas_universo[
    (mzas_universo["es_prioritaria_s1"]!=True) &
    (~mzas_universo.index.isin(mzas_dest.index))
].copy()

# Contornos de secciones — siempre todas, para contexto
secs_contorno = secs.to_crs("EPSG:4326")

# ── Centro y zoom del mapa ────────────────────────────────────────────────────
if sec_sel:
    mzas_zoom = mzas_universo[mzas_universo["SECCION"]==sec_sel]
    if len(mzas_zoom):
        bounds = mzas_zoom.total_bounds   # [minx, miny, maxx, maxy]
        lat_c  = (bounds[1] + bounds[3]) / 2
        lon_c  = (bounds[0] + bounds[2]) / 2
        fit_b  = [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]
    else:
        lat_c, lon_c, fit_b = PROYECTO["lat_centro"], PROYECTO["lon_centro"], None
else:
    lat_c, lon_c, fit_b = PROYECTO["lat_centro"], PROYECTO["lon_centro"], None

# ── Mapa folium ───────────────────────────────────────────────────────────────
m = folium.Map(
    location=[lat_c, lon_c],
    zoom_start=15 if sec_sel else PROYECTO["zoom"],
    tiles="CartoDB positron",
)
if fit_b:
    m.fit_bounds(fit_b)

# Barra de color — LN estimada de manzanas prioritarias
ln_vals = mzas_prio["LN_estimada"].dropna()
ln_min  = float(ln_vals.min()) if len(ln_vals) else 0.0
ln_max  = float(ln_vals.max()) if len(ln_vals) else 1.0

colormap_ln = cm.LinearColormap(
    colors=["#e8d5d5", "#8B4A52", "#6A1B29"],
    vmin=ln_min, vmax=ln_max,
    caption="LN estimada por manzana (más oscuro = más electores)",
)
colormap_ln.add_to(m)

def _fill_prio(ln):
    """Interpola LN estimada → color guinda."""
    if pd.isna(ln):
        return "#8B4A52"
    t = max(0.0, min(1.0, (ln - ln_min) / (ln_max - ln_min + 1e-9)))
    r = int(0xe8 + t*(0x6A - 0xe8))
    g = int(0xd5 + t*(0x1B - 0xd5))
    b = int(0xd5 + t*(0x29 - 0xd5))
    return f"#{r:02x}{g:02x}{b:02x}"

# Capa 1 — manzanas de contexto (gris claro)
for _, row in mzas_resto.iterrows():
    try:
        geom_json = json.loads(gpd.GeoSeries([row.geometry]).to_json())
        folium.GeoJson(
            geom_json,
            style_function=lambda x: {
                "fillColor": "#eeeeee", "fillOpacity": 0.5,
                "color": "#cccccc", "weight": 0.3,
            },
        ).add_to(m)
    except Exception:
        pass

# Capa 2 — manzanas prioritarias (gradiente LN)
for _, row in mzas_prio.iterrows():
    ln_val  = row.get("LN_estimada", 0)
    rk_val  = row.get("ranking_seccion", "?")
    sec_val = int(row.get("SECCION", 0))
    ire_str = f"{row.get('IRE_MZA',0):.3f}" if "IRE_MZA" in row and pd.notna(row.get("IRE_MZA")) else "—"
    fuente  = row.get("fuente_estimacion", "—")

    tooltip = f"""
    <div style='font-family:sans-serif;font-size:12px;min-width:190px;'>
        <b>M{int(rk_val) if pd.notna(rk_val) else '?'} — Manzana prioritaria</b><br>
        Sección: {sec_val}<br>
        <hr style='margin:3px 0;border:none;border-top:1px solid #ddd;'>
        <b>LN estimada:</b> {ln_val:,.0f}<br>
        <b>Prob. encuesta:</b> {ire_str}<br>
        <b>Fuente estimación:</b> {fuente}
    </div>
    """
    fill = _fill_prio(ln_val)
    try:
        geom_json = json.loads(gpd.GeoSeries([row.geometry]).to_json())
        folium.GeoJson(
            geom_json,
            style_function=lambda x, f=fill: {
                "fillColor": f, "fillOpacity": 0.85,
                "color": "#3a0a0a", "weight": 1.2,
            },
            tooltip=folium.Tooltip(tooltip, sticky=True),
        ).add_to(m)
    except Exception:
        pass

# Capa 3 — manzanas destacadas (dorado)
for _, row in mzas_dest.iterrows():
    ln_val  = row.get("LN_estimada", 0)
    sec_val = int(row.get("SECCION", 0))
    rk_val  = row.get("ranking_seccion", "?")

    tooltip = f"""
    <div style='font-family:sans-serif;font-size:12px;min-width:190px;'>
        <b>★ Manzana destacada</b><br>
        Sección: {sec_val} · Posición #{int(rk_val) if pd.notna(rk_val) else '?'}<br>
        <hr style='margin:3px 0;border:none;border-top:1px solid #ddd;'>
        <b>LN estimada:</b> {ln_val:,.0f}<br>
        <b>Por qué aparece:</b> Alta probabilidad de encuesta fuera
        del corte de lista nominal — hallazgo del modelo.
    </div>
    """
    try:
        geom_json = json.loads(gpd.GeoSeries([row.geometry]).to_json())
        folium.GeoJson(
            geom_json,
            style_function=lambda x: {
                "fillColor": COLOR_ACENTO, "fillOpacity": 0.85,
                "color": "#7a6010", "weight": 1.5,
            },
            tooltip=folium.Tooltip(tooltip, sticky=True),
        ).add_to(m)
    except Exception:
        pass

# Capa 4 — contornos de secciones (siempre encima)
folium.GeoJson(
    json.loads(secs_contorno.to_json()),
    style_function=lambda x: {
        "fillOpacity": 0,
        "color": "#6A1B29",
        "weight": 1.2,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["SECCION"],
        aliases=["Sección:"],
        style="font-family:sans-serif;font-size:11px;",
    ),
    name="Contornos de sección",
).add_to(m)

# ── Layout ────────────────────────────────────────────────────────────────────
col_mapa, col_panel = st.columns([3, 1])

with col_mapa:
    st_folium(m, width="100%", height=560, returned_objects=[])

with col_panel:
    if sec_sel:
        # ── Modo ficha de sección ─────────────────────────────────────
        row_rank = rank[rank["SECCION"]==sec_sel]
        mzas_sec = mzas_universo[mzas_universo["SECCION"]==sec_sel]
        mzas_s1_sec = mzas_sec[mzas_sec["es_prioritaria_s1"]==True]

        ln_sec     = mzas_sec["LN_real_seccion"].iloc[0] if len(mzas_sec) else 0
        ln_prio    = mzas_s1_sec["LN_estimada"].sum()
        n_prio     = len(mzas_s1_sec)
        pct_cub    = ln_prio / ln_sec * 100 if ln_sec > 0 else 0

        es_op = sec_sel in operativas_secs
        es_nuc= sec_sel in nucleo_secs
        if es_nuc:
            rnk = int(row_rank.iloc[0]["RANK_ESTRATEGICO"]) if not row_rank.empty else "—"
            tag = f"★ Núcleo #{rnk}"
            col_tag = COLOR_ALTA
        elif es_op:
            rnk = int(row_rank.iloc[0]["RANK_ESTRATEGICO"]) if not row_rank.empty else "—"
            tag = f"Extensión #{rnk}"
            col_tag = COLOR_MEDIA
        else:
            tag = "Referencia"
            col_tag = COLOR_BAJA

        st.markdown(f"""
        <div style='background:{COLOR_TARJETA};border-left:3px solid {col_tag};
                    border-radius:6px;padding:0.8rem;margin-bottom:0.6rem;'>
            <p style='color:{COLOR_SECUNDARIO};font-size:0.70rem;margin:0;
                      text-transform:uppercase;letter-spacing:0.08em;'>Ficha de sección</p>
            <p style='color:{COLOR_TEXTO};font-size:1.4rem;font-weight:700;
                      font-family:"Barlow Condensed",sans-serif;margin:0.1rem 0 0;'>
                Sección {sec_sel}
            </p>
            <span style='background:{col_tag};color:#fff;font-size:0.70rem;
                         font-weight:600;padding:2px 7px;border-radius:3px;'>{tag}</span>
        </div>
        """, unsafe_allow_html=True)

        kpi("LN total de la sección", f"{int(ln_sec):,}", color=COLOR_MEDIA)
        kpi("Manzanas prioritarias",  str(n_prio),        color=COLOR_ALTA)
        kpi("LN en manzanas prio.",   f"{int(ln_prio):,}", color=COLOR_ALTA)
        kpi("% LN cubierta",          f"{pct_cub:.1f}%",
            "del padrón de la sección", COLOR_ACENTO)

        if not row_rank.empty and es_op:
            ire = row_rank.iloc[0].get("IRE_SCORE")
            fm  = row_rank.iloc[0].get("fuerza_morena")
            if pd.notna(ire):
                kpi("Prob. encuesta", f"{ire:.3f}", color=COLOR_MEDIA)
            if pd.notna(fm):
                kpi("Fuerza Morena", f"{fm*100:.1f}%", color=COLOR_MORENA)

    else:
        # ── Modo agregado del universo visible ────────────────────────
        n_secs_vis  = len(secs_activas)
        ln_prio_tot = mzas_prio["LN_estimada"].sum()
        ln_tot      = mzas_universo["LN_real_seccion"].drop_duplicates().sum() if len(mzas_universo) else 0
        pct_tot     = ln_prio_tot / ln_tot * 100 if ln_tot > 0 else 0
        n_dest      = len(mzas_dest)

        kpi("Secciones en vista",     str(n_secs_vis),        color=COLOR_MEDIA)
        kpi("Manzanas prioritarias",  f"{len(mzas_prio):,}",  color=COLOR_ALTA)
        kpi("LN en manzanas prio.",   f"{int(ln_prio_tot):,}", color=COLOR_ALTA)
        kpi("Cobertura LN",           f"{pct_tot:.1f}%",
            "del padrón visible", COLOR_ACENTO)
        if n_dest:
            kpi("Manzanas destacadas", str(n_dest),
                "IRE alto fuera del corte de LN", COLOR_ACENTO)

    # ── Leyenda — en llamadas pequeñas para evitar raw HTML ─────────
    st.markdown(f"<p style='color:{COLOR_TEXTO};font-size:0.82rem;font-weight:600;margin:0.8rem 0 0.5rem;'>Leyenda</p>", unsafe_allow_html=True)

    # Gradiente manzanas prioritarias
    st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.75rem;font-weight:600;margin:0 0 2px;'>Manzanas prioritarias</p>", unsafe_allow_html=True)
    st.markdown("<div style='background:linear-gradient(to right,#e8d5d5,#8B4A52,#6A1B29);height:9px;border-radius:4px;margin-bottom:2px;'></div>", unsafe_allow_html=True)

    col_ln1, col_ln2 = st.columns(2)
    with col_ln1:
        st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.68rem;margin:0;'>Menor LN</p>", unsafe_allow_html=True)
    with col_ln2:
        st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.68rem;margin:0;text-align:right;'>Mayor LN</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;margin:4px 0 8px;line-height:1.4;'>Concentran el 50% de la LN de su sección. Destino de las brigadas.</p>", unsafe_allow_html=True)

    # Manzana destacada
    col_ic, col_txt = st.columns([1, 5])
    with col_ic:
        st.markdown(f"<div style='width:14px;height:14px;background:{COLOR_ACENTO};border-radius:2px;margin-top:2px;'></div>", unsafe_allow_html=True)
    with col_txt:
        st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.75rem;font-weight:600;margin:0;'>Manzana destacada ★</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;margin:2px 0 8px;line-height:1.4;'>IRE alto fuera del corte de LN — hallazgo del modelo.</p>", unsafe_allow_html=True)

    # Resto de manzanas
    col_ic2, col_txt2 = st.columns([1, 5])
    with col_ic2:
        st.markdown("<div style='width:14px;height:14px;background:#eeeeee;border:1px solid #ccc;border-radius:2px;margin-top:2px;'></div>", unsafe_allow_html=True)
    with col_txt2:
        st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.75rem;margin:0;'>Resto de manzanas</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;margin:2px 0 8px;line-height:1.4;'>Contexto geográfico.</p>", unsafe_allow_html=True)

    # Contorno sección
    col_ic3, col_txt3 = st.columns([1, 5])
    with col_ic3:
        st.markdown(f"<div style='width:14px;height:3px;background:{COLOR_ALTA};margin-top:6px;'></div>", unsafe_allow_html=True)
    with col_txt3:
        st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;margin:0;'>Contorno de sección</p>", unsafe_allow_html=True)