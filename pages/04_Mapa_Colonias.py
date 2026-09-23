"""
04_Mapa_Colonias.py — PIE · Módulo de Colonias (M4)
Traduce el universo priorizado (secciones/manzanas) al lenguaje de colonia,
para que el coordinador pueda instruir a la brigada sin fricción de traducción.
Fuente de colonias: Unidades Territoriales IECM 2022 (cobertura 100% del caso).
Alcance: planeación/referencia/cobertura — sin seguimiento de ejecución en campo.
"""
import streamlit as st
import folium
import branca.colormap as cm
import pandas as pd
import geopandas as gpd
import json
from streamlit_folium import st_folium
from app_utils import (
    verificar_acceso, aplicar_estilos, header, kpi,
    cargar_colonias, cargar_manzanas_colonia, cargar_secciones, PROYECTO,
    COLOR_ALTA, COLOR_ACENTO, COLOR_MEDIA,
    COLOR_TARJETA, COLOR_TEXTO, COLOR_SECUNDARIO,
    CARTO_TILES, CARTO_ATTR, agregar_controles_mapa,
)

st.set_page_config(
    page_title="Mapa de Colonias · PIE",
    page_icon="🏘️",
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
        <p style='color:{COLOR_ACENTO};font-weight:600; font-size:0.78rem; margin:0;'>
            Bernardo Aguilar 2027
    </div>
    <hr style='border:none;border-top:1px solid #3a1010;margin:0.8rem 0;'>
    """, unsafe_allow_html=True)
    st.page_link("Home.py",                      label="🏠  Inicio")
    st.page_link("pages/01_Mapa_Secciones.py",   label="🗺️  Mapa de secciones")
    st.page_link("pages/02_Mapa_Manzanas.py",    label="📍  Mapa de manzanas")
    st.page_link("pages/03_Ranking.py",           label="🔍  Fichas de sección")
    st.page_link("pages/04_Mapa_Colonias.py",     label="🏘️  Mapa de colonias")
    st.markdown("<hr style='border:none;border-top:1px solid #3a1010;margin:1rem 0;'>",
                unsafe_allow_html=True)
    if st.button("Cerrar sesión", use_container_width=True):
        from app_utils import cerrar_sesion
        cerrar_sesion()

# ── Header ────────────────────────────────────────────────────────────────────
header("Mapa de Colonias", "Universo priorizado en el lenguaje que usa la brigada en la calle")

# ── Cargar datos ──────────────────────────────────────────────────────────────
col = cargar_colonias()
col = col.sort_values("COLONIA").reset_index(drop=True)
mz_todas = cargar_manzanas_colonia()
secs_geo = cargar_secciones()

TOTAL_COLONIAS = len(col)
TOTAL_CON_PRIO = int((col["manzanas_prioritarias"] > 0).sum())

# Universo completo de secciones del caso (148/151, según catálogo del pipeline).
# No todas tienen manzana mapeada a colonia — 3072/5654/5655/5656 son brechas
# cartográficas ya documentadas (00b_brechas_cartograficas.md); se muestran en
# el buscador igual, con un mensaje explícito en vez de desaparecer sin avisar.
TODAS_LAS_SECCIONES = sorted(secs_geo[secs_geo["SECCION"] > 0]["SECCION"].tolist())
SECCIONES_CON_COLONIA = set(mz_todas["SECCION"].unique().tolist())

# ── Selector de modo de búsqueda ──────────────────────────────────────────────
modo = st.radio("Buscar por", options=["Colonia", "Sección"], index=0, horizontal=True)

colonia_sel = None
sec_sel = None
resumen_sec = None

if modo == "Colonia":
    # ── Buscador de colonia (punto de entrada principal) ──────────────────────
    opciones = ["— Panorama completo —"] + col["COLONIA"].tolist()
    colonia_sel = st.selectbox("Buscar colonia", options=opciones, index=0)
    colonia_sel = None if colonia_sel == "— Panorama completo —" else colonia_sel

    # ── Filtro narrativo (secundario) ──────────────────────────────────────────
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        universo = st.radio(
            "Colonias a mostrar",
            options=[f"Todas ({TOTAL_COLONIAS})", f"Con manzanas prioritarias ({TOTAL_CON_PRIO})"],
            index=0,
        )
    with col_f2:
        st.markdown(f"""
        <p style='color:{COLOR_SECUNDARIO};font-size:0.76rem;padding-top:1.8rem;'>
            {'Incluye colonias sin universo operativo en este caso (referencia de cobertura).'
             if universo.startswith('Todas')
             else 'Solo colonias con al menos una manzana prioritaria a visitar.'}
        </p>
        """, unsafe_allow_html=True)

    col_filt = col if universo.startswith("Todas") else col[col["manzanas_prioritarias"] > 0]

    # El buscador siempre puede apuntar a cualquier colonia, aunque el filtro la excluya
    if colonia_sel and colonia_sel not in col_filt["COLONIA"].values:
        col_filt = col[col["COLONIA"] == colonia_sel]

else:
    # ── Buscador de sección — traduce en sentido inverso: sección → colonia(s) ──
    sec_sel = st.selectbox(
        "Buscar sección",
        options=TODAS_LAS_SECCIONES,
        format_func=lambda s: f"Sección {int(s)}",
        index=None,
        placeholder="Selecciona una sección...",
    )

    if sec_sel and sec_sel not in SECCIONES_CON_COLONIA:
        # Brecha cartográfica conocida — sin manzanas mapeadas, no hay colonia que mostrar
        st.warning(
            f"La sección {int(sec_sel)} no tiene manzanas asignadas a colonia en este caso "
            "(brecha cartográfica ya documentada — sin detalle de manzana en el pipeline). "
            "Consulta su ficha en 🔍 Fichas de sección para la indicación operativa vigente.",
            icon="⚠️",
        )
        col_filt = col.iloc[0:0]
    elif sec_sel:
        sec_mz = mz_todas[mz_todas["SECCION"] == sec_sel]
        resumen_sec = (
            sec_mz.groupby("COLONIA")
            .agg(manzanas=("COLONIA", "count"),
                 ln=("LN_estimada", "sum"),
                 prioritarias=("es_prioritaria_s1", "sum"))
            .reset_index()
            .sort_values("manzanas", ascending=False)
        )
        resumen_sec["pct_manzanas"] = (
            resumen_sec["manzanas"] / resumen_sec["manzanas"].sum() * 100
        )
        colonias_tocadas = resumen_sec["COLONIA"].tolist()
        col_filt = col[col["COLONIA"].isin(colonias_tocadas)]
    else:
        col_filt = col.iloc[0:0]  # nada que dibujar hasta elegir sección

# ── Mapa folium coroplético ─────────────────────────────────────────────────────
vmax = max(int(col["manzanas_prioritarias"].max()), 1)
colormap = cm.LinearColormap(
    colors=["#cccccc", "#8B4A52", "#6A1B29"],
    vmin=0, vmax=vmax,
    caption="Manzanas prioritarias por colonia",
)

m = folium.Map(
    location=[PROYECTO["lat_centro"], PROYECTO["lon_centro"]],
    zoom_start=PROYECTO["zoom"],
    tiles=CARTO_TILES, attr=CARTO_ATTR,
)

# En modo Sección, las colonias tocadas pasan a solo-contorno — el protagonismo
# visual es de la sección (borde grueso) y sus manzanas, no del relleno de colonia.
solo_contorno = bool(colonia_sel) or (modo == "Sección" and sec_sel is not None)

# Lookup rápido de manzanas/LN por colonia EN ESTA SECCIÓN, para un tooltip
# más relevante que el total de la colonia cuando se busca por sección.
resumen_sec_map = (
    resumen_sec.set_index("COLONIA").to_dict("index")
    if resumen_sec is not None else {}
)

for _, row in col_filt.iterrows():
    if row["COLONIA"] in resumen_sec_map:
        r = resumen_sec_map[row["COLONIA"]]
        frase = (f"{row['COLONIA']}: {int(r['manzanas'])} manzanas de la sección "
                 f"{int(sec_sel)} ({r['pct_manzanas']:.0f}% de la sección) · "
                 f"{int(r['prioritarias'])} prioritarias")
    else:
        frase = (f"{row['COLONIA']}: {int(row['manzanas_prioritarias'])} manzanas "
                 f"prioritarias de {int(row['total_manzanas'])}")
    es_sel = (colonia_sel == row["COLONIA"])
    color = colormap(row["manzanas_prioritarias"])
    fill_opacity = 0.0 if solo_contorno else 0.75
    folium.GeoJson(
        row["geometry"],
        style_function=lambda _, c=color, sel=es_sel, fo=fill_opacity: {
            "fillColor": c, "color": COLOR_ALTA if sel else "#3a1010",
            "weight": 3 if sel else 0.8, "fillOpacity": fo,
        },
        tooltip=frase,
    ).add_to(m)

colormap.add_to(m)

# ── Capa de manzanas — colonia seleccionada, o manzanas de la sección buscada ──
if modo == "Colonia" and colonia_sel:
    mz_scope = mz_todas[mz_todas["COLONIA"] == colonia_sel].copy()
elif modo == "Sección" and sec_sel and sec_sel in SECCIONES_CON_COLONIA:
    mz_scope = mz_todas[mz_todas["SECCION"] == sec_sel].copy()
else:
    mz_scope = None

if mz_scope is not None:
    mz_col = mz_scope

    mz_prio = mz_col[mz_col["es_prioritaria_s1"] == True]
    mz_dest = mz_col[
        (mz_col.get("NIVEL_MZA", pd.Series(dtype=str)) == "MA_ALTA") &
        (mz_col["es_prioritaria_s1"] != True)
    ] if "NIVEL_MZA" in mz_col.columns else pd.DataFrame()
    mz_resto = mz_col[
        (mz_col["es_prioritaria_s1"] != True) &
        (~mz_col.index.isin(mz_dest.index))
    ]

    ln_vals = mz_prio["LN_estimada"].dropna()
    ln_min = float(ln_vals.min()) if len(ln_vals) else 0.0
    ln_max = float(ln_vals.max()) if len(ln_vals) else 1.0

    def _fill_prio(ln):
        if pd.isna(ln):
            return "#8B4A52"
        t = max(0.0, min(1.0, (ln - ln_min) / (ln_max - ln_min + 1e-9)))
        r = int(0xe8 + t * (0x6A - 0xe8))
        g = int(0xd5 + t * (0x1B - 0xd5))
        b = int(0xd5 + t * (0x29 - 0xd5))
        return f"#{r:02x}{g:02x}{b:02x}"

    # Contexto — manzanas no prioritarias de la colonia (gris)
    for _, r in mz_resto.iterrows():
        try:
            geom_json = json.loads(gpd.GeoSeries([r.geometry]).to_json())
            folium.GeoJson(
                geom_json,
                style_function=lambda x: {
                    "fillColor": "#eeeeee", "fillOpacity": 0.5,
                    "color": "#cccccc", "weight": 0.3,
                },
            ).add_to(m)
        except Exception:
            pass

    # Prioritarias — gradiente guinda por LN, mismo criterio que 02_Mapa_Manzanas.py
    for _, r in mz_prio.iterrows():
        ln_val = r.get("LN_estimada", 0)
        rk_val = r.get("ranking_seccion", "?")
        sec_val = int(r.get("SECCION", 0))
        ire_str = f"{r.get('IRE_MZA', 0):.3f}" if "IRE_MZA" in r and pd.notna(r.get("IRE_MZA")) else "—"
        fuente = r.get("fuente_estimacion", "—")
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
            geom_json = json.loads(gpd.GeoSeries([r.geometry]).to_json())
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

    # Destacadas — dorado, mismo criterio que 02_Mapa_Manzanas.py
    for _, r in mz_dest.iterrows():
        ln_val = r.get("LN_estimada", 0)
        sec_val = int(r.get("SECCION", 0))
        rk_val = r.get("ranking_seccion", "?")
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
            geom_json = json.loads(gpd.GeoSeries([r.geometry]).to_json())
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

# ── Contorno de sección — encima de todo, cuando se busca por sección ─────────
if modo == "Sección" and sec_sel:
    sec_geom_rows = secs_geo.loc[secs_geo["SECCION"] == sec_sel, "geometry"]
    if len(sec_geom_rows):
        geom_sec = sec_geom_rows.values[0]
        folium.GeoJson(
            geom_sec,
            style_function=lambda _: {
                "fillOpacity": 0, "color": COLOR_ALTA, "weight": 3.5,
            },
            tooltip=f"Sección {int(sec_sel)}",
        ).add_to(m)
        minx, miny, maxx, maxy = geom_sec.bounds
        m.fit_bounds([[miny, minx], [maxy, maxx]])

if colonia_sel:
    geom_sel = col.loc[col["COLONIA"] == colonia_sel, "geometry"].values[0]
    minx, miny, maxx, maxy = geom_sel.bounds
    m.fit_bounds([[miny, minx], [maxy, maxx]])

# ── Capa satelital alternable + pantalla completa (al final, tras todas las capas) ──
agregar_controles_mapa(m)

st_folium(m, use_container_width=True, height=480, returned_objects=[])

# ── Panel dual ──────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

if modo == "Sección":
    if sec_sel and resumen_sec is not None:
        st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;"
                    f"letter-spacing:0.1em;text-transform:uppercase;margin:0;'>"
                    f"Colonias en esta sección</p>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color:{COLOR_TEXTO};margin:0.1rem 0 0.8rem;"
                    f"font-size:1.6rem;'>Sección {int(sec_sel)}</h2>", unsafe_allow_html=True)

        n_col = len(resumen_sec)
        if n_col == 1:
            st.markdown(f"<p style='color:{COLOR_TEXTO};font-size:0.95rem;margin-bottom:0.8rem;'>"
                        f"La sección {int(sec_sel)} está en "
                        f"<b style='color:{COLOR_ACENTO};'>{resumen_sec.iloc[0]['COLONIA']}</b>.</p>",
                        unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color:{COLOR_TEXTO};font-size:0.95rem;margin-bottom:0.8rem;'>"
                        f"La sección {int(sec_sel)} cruza <b style='color:{COLOR_ACENTO};'>"
                        f"{n_col} colonias</b> — no coincide con un solo límite de colonia.</p>",
                        unsafe_allow_html=True)

        tabla_sec = resumen_sec.copy()
        tabla_sec["ln"] = tabla_sec["ln"].apply(lambda x: f"{x:,.0f}")
        tabla_sec["pct_manzanas"] = tabla_sec["pct_manzanas"].apply(lambda x: f"{x:.0f}%")
        tabla_sec = tabla_sec[["COLONIA", "manzanas", "pct_manzanas", "ln", "prioritarias"]]
        tabla_sec.columns = ["Colonia", "Manzanas en la sección", "% de la sección",
                             "LN en esa colonia", "Manzanas prioritarias"]
        st.dataframe(tabla_sec, use_container_width=True, hide_index=True)

        st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;margin-top:0.6rem;'>"
                    f"El % es sobre el total de manzanas de la sección, no de la colonia. "
                    f"Consulta 🔍 Fichas de sección para el detalle electoral de la sección "
                    f"{int(sec_sel)}.</p>", unsafe_allow_html=True)
    elif sec_sel:
        pass  # ya se mostró el aviso de brecha cartográfica arriba del mapa
    else:
        st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.85rem;'>"
                    f"Selecciona una sección arriba para ver a qué colonia o colonias "
                    f"pertenece.</p>", unsafe_allow_html=True)

elif colonia_sel:
    row = col[col["COLONIA"] == colonia_sel].iloc[0]

    st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;"
                f"letter-spacing:0.1em;text-transform:uppercase;margin:0;'>"
                f"Ficha de colonia</p>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:{COLOR_TEXTO};margin:0.1rem 0 0.8rem;"
                f"font-size:1.6rem;'>{row['COLONIA']}</h2>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Manzanas a visitar", str(int(row["manzanas_prioritarias"])), color=COLOR_ALTA)
    with c2:
        kpi("LN en esas manzanas", f"{int(row['ln_prioritaria']):,}", color=COLOR_ALTA)
    with c3:
        kpi("Total de manzanas", f"{int(row['manzanas_prioritarias'])} de {int(row['total_manzanas'])}",
            f"{row['pct_cobertura']:.1f}% de la colonia", COLOR_ACENTO)
    with c4:
        n_secc = len(str(row["secciones"]).split(",")) if row["secciones"] else 0
        kpi("Secciones que la componen", str(n_secc), color=COLOR_MEDIA)

    st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.78rem;margin-top:0.5rem;'>"
                f"Secciones: {row['secciones'] if row['secciones'] else '—'} · "
                f"consulta la ficha de cada una en 🔍 Fichas de sección.</p>",
                unsafe_allow_html=True)

    st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;margin-top:0.6rem;'>"
                f"En el mapa: <span style='color:#6A1B29;'>■</span> manzanas prioritarias "
                f"(más oscuro = más electores) · "
                f"<span style='color:{COLOR_ACENTO};'>■</span> manzanas destacadas (hallazgo "
                f"del modelo, fuera del corte) · <span style='color:#cccccc;'>■</span> resto "
                f"de manzanas de la colonia.</p>", unsafe_allow_html=True)

else:
    st.markdown(f"<p style='color:{COLOR_TEXTO};font-size:0.9rem;font-weight:600;"
                f"margin-bottom:0.4rem;'>Colonias ordenadas por manzanas prioritarias</p>",
                unsafe_allow_html=True)

    tabla = col_filt.drop(columns="geometry").sort_values(
        "manzanas_prioritarias", ascending=False).copy()
    tabla = tabla[["COLONIA", "manzanas_prioritarias", "total_manzanas",
                   "pct_cobertura", "ln_prioritaria", "ln_total", "secciones"]]
    tabla.columns = ["Colonia", "Manzanas a visitar", "Total manzanas",
                      "% cobertura", "LN en manzanas prio.", "LN total", "Secciones"]
    tabla["% cobertura"] = tabla["% cobertura"].apply(lambda x: f"{x:.1f}%")
    tabla["LN en manzanas prio."] = tabla["LN en manzanas prio."].apply(lambda x: f"{x:,.0f}")
    tabla["LN total"] = tabla["LN total"].apply(lambda x: f"{x:,.0f}")

    st.dataframe(tabla, use_container_width=True, hide_index=True, height=460)
    st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.75rem;'>"
                f"{len(col_filt)} colonias.</p>", unsafe_allow_html=True)