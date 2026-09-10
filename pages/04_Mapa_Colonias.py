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
from streamlit_folium import st_folium
from app_utils import (
    verificar_acceso, aplicar_estilos, header, kpi,
    cargar_colonias, PROYECTO,
    COLOR_ALTA, COLOR_ACENTO, COLOR_MEDIA,
    COLOR_TARJETA, COLOR_TEXTO, COLOR_SECUNDARIO,
    CARTO_TILES, CARTO_ATTR,
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

TOTAL_COLONIAS = len(col)
TOTAL_CON_PRIO = int((col["manzanas_prioritarias"] > 0).sum())

# ── Buscador de colonia (punto de entrada principal) ──────────────────────────
opciones = ["— Panorama completo —"] + col["COLONIA"].tolist()
colonia_sel = st.selectbox("Buscar colonia", options=opciones, index=0)
colonia_sel = None if colonia_sel == "— Panorama completo —" else colonia_sel

# ── Filtro narrativo (secundario) ──────────────────────────────────────────────
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

for _, row in col_filt.iterrows():
    frase = (f"{row['COLONIA']}: {int(row['manzanas_prioritarias'])} manzanas "
             f"prioritarias de {int(row['total_manzanas'])}")
    color = colormap(row["manzanas_prioritarias"])
    es_sel = (colonia_sel == row["COLONIA"])
    folium.GeoJson(
        row["geometry"],
        style_function=lambda _, c=color, sel=es_sel: {
            "fillColor": c, "color": COLOR_ALTA if sel else "#3a1010",
            "weight": 3 if sel else 0.8, "fillOpacity": 0.75,
        },
        tooltip=frase,
    ).add_to(m)

colormap.add_to(m)

if colonia_sel:
    geom_sel = col.loc[col["COLONIA"] == colonia_sel, "geometry"].values[0]
    minx, miny, maxx, maxy = geom_sel.bounds
    m.fit_bounds([[miny, minx], [maxy, maxx]])

st_folium(m, use_container_width=True, height=480, returned_objects=[])

# ── Panel dual ──────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

if colonia_sel:
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
