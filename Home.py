"""
Home.py — PIE · Plataforma de Inteligencia Electoral
Dashboard principal: KPIs generales y orientación al coordinador.
"""
import streamlit as st
from app_utils import (
    verificar_acceso, aplicar_estilos, header, kpi,
    cargar_ranking, cargar_unificado,
    COLOR_ALTA, COLOR_MEDIA, COLOR_BAJA, COLOR_MORENA,
    COLOR_TARJETA, COLOR_TEXTO, COLOR_SECUNDARIO, COLOR_POSITIVO,
    NIVEL_LABEL, badge_nivel, es_nucleo
)

st.set_page_config(
    page_title="PIE · La Magdalena Contreras",
    page_icon="🗳️",
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
        <p style='color:{COLOR_ALTA}; font-size:0.72rem; letter-spacing:0.12em;
                  text-transform:uppercase; margin:0;'>PIE</p>
        <p style='color:{COLOR_TEXTO}; font-size:1rem; font-weight:600; margin:0.2rem 0;'>
            La Magdalena Contreras
        </p>
        <p style='color:{COLOR_SECUNDARIO}; font-size:0.78rem; margin:0;'>
            Interna Morena 2026
        </p>
    </div>
    <hr style='border:none;border-top:1px solid #2a3550;margin:0.8rem 0;'>
    """, unsafe_allow_html=True)

    st.page_link("Home.py",                      label="🏠  Inicio",               )
    st.page_link("pages/01_Mapa_Secciones.py",   label="🗺️  Mapa de secciones"     )
    st.page_link("pages/02_Mapa_Manzanas.py",    label="📍  Mapa de manzanas"      )
    st.page_link("pages/03_Ranking.py",           label="📊  Ranking y ficha"       )

    st.markdown("<hr style='border:none;border-top:1px solid #2a3550;margin:1rem 0;'>",
                unsafe_allow_html=True)
    if st.button("Cerrar sesión", use_container_width=True):
        from app_utils import cerrar_sesion
        cerrar_sesion()

# ── Header ────────────────────────────────────────────────────────────────────
header("Inicio", "Resumen del módulo de priorización territorial")

# ── Cargar datos ──────────────────────────────────────────────────────────────
rank = cargar_ranking()
gdf  = cargar_unificado()

p3   = rank[(rank["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA") & (rank["SECCION"]>0)]
nucl = p3.head(25)
mzas_s1  = gdf[gdf["es_prioritaria_s1"]==True]
hallazgo = gdf[(gdf["NIVEL_MZA"]=="MA_ALTA") & (gdf["es_prioritaria_s1"]!=True)]

# ── KPIs ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi("Secciones operativas",
        f"{len(p3)}",
        f"Núcleo prioritario: {len(nucl)}",
        COLOR_ALTA)
with c2:
    kpi("Manzanas prioritarias",
        f"{len(mzas_s1):,}",
        f"Corte 50% LN por sección",
        COLOR_ALTA)
with c3:
    kpi("LN en núcleo prioritario",
        f"{nucl['LN_TOTAL'].sum():,.0f}",
        f"{nucl['LN_TOTAL'].sum()/213700*100:.1f}% del padrón total",
        COLOR_MEDIA)
with c4:
    kpi("Manzanas destacadas",
        f"{len(hallazgo)}",
        "IRE alto fuera del corte de LN",
        COLOR_MORENA)

st.markdown("<br>", unsafe_allow_html=True)

# ── Dos columnas: top 10 + contexto ──────────────────────────────────────────
col_tabla, col_info = st.columns([3, 2])

with col_tabla:
    st.markdown(f"""
    <h3 style='color:{COLOR_TEXTO}; font-size:1.1rem; margin-bottom:0.8rem;'>
        Top 10 secciones — Ranking operativo
    </h3>
    """, unsafe_allow_html=True)

    top10 = p3.head(10)[["RANK_ESTRATEGICO","SECCION","LN_TOTAL",
                           "IRE_SCORE","fuerza_morena","INDICE_RENTABILIDAD"]].copy()
    top10["Prioridad"]       = top10["RANK_ESTRATEGICO"].apply(
        lambda r: "★ Núcleo" if r<=25 else "Extensión")
    top10["Prob. encuesta"]  = top10["IRE_SCORE"].apply(lambda x: f"{x:.3f}")
    top10["Fuerza Morena"]   = top10["fuerza_morena"].apply(
        lambda x: f"{x*100:.1f}%" if x==x else "—")
    top10["Índice Rent."]    = top10["INDICE_RENTABILIDAD"].apply(lambda x: f"{x:.3f}")
    top10["LN"]              = top10["LN_TOTAL"].apply(lambda x: f"{x:,.0f}")

    st.dataframe(
        top10[["RANK_ESTRATEGICO","SECCION","LN","Prioridad",
               "Prob. encuesta","Fuerza Morena","Índice Rent."]].rename(columns={
            "RANK_ESTRATEGICO": "#",
            "SECCION": "Sección",
        }),
        use_container_width=True,
        hide_index=True,
        height=370,
    )

with col_info:
    st.markdown(f"""
    <h3 style='color:{COLOR_TEXTO}; font-size:1.1rem; margin-bottom:0.8rem;'>
        Cómo leer la plataforma
    </h3>
    <div style='background:{COLOR_TARJETA}; border-radius:6px; padding:1.2rem;
                font-size:0.85rem; color:{COLOR_SECUNDARIO}; line-height:1.7;'>
        <p style='color:{COLOR_TEXTO}; font-weight:600; margin:0 0 0.5rem;'>
            Tres números en el encabezado de cada sección:
        </p>
        <p><span style='color:{COLOR_ALTA}; font-weight:600;'>Prob. encuesta</span><br>
        En cuántas de cada 10 simulaciones cayó esta sección en la muestra.
        Un valor de 0.72 significa 7 de cada 10.</p>
        <p><span style='color:{COLOR_ALTA}; font-weight:600;'>Fuerza Morena</span><br>
        % de electores del padrón que votaron por el bloque en 2024.
        No sobre quienes votaron — sobre el total registrado.</p>
        <p style='margin-bottom:0;'>
        <span style='color:{COLOR_ALTA}; font-weight:600;'>Índice Rentabilidad</span><br>
        Combina los dos anteriores. Ordena las secciones del PDF de mayor
        a menor impacto operativo.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Contexto electoral
    st.markdown(f"""
    <div style='background:{COLOR_TARJETA}; border-radius:6px; padding:1.2rem;
                font-size:0.85rem; color:{COLOR_SECUNDARIO}; line-height:1.6;'>
        <p style='color:{COLOR_TEXTO}; font-weight:600; margin:0 0 0.5rem;'>
            Contexto electoral — Alcaldía 2024
        </p>
        <p>Morena ganó por <span style='color:{COLOR_ALTA};font-weight:600;'>+1.96 pp</span>
        sobre la oposición. Cuarta alternancia consecutiva.</p>
        <p style='margin-bottom:0;'>
        En las 52 secciones de mayor padrón (S1), Morena tiene
        <span style='color:{COLOR_ALTA};font-weight:600;'>+11.1 pp</span>
        de ventaja. Ahí se concentra el operativo.</p>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<p style='color:{COLOR_BAJA}; font-size:0.72rem; text-align:center;'>
    PIE · Plataforma de Inteligencia Electoral · La Magdalena Contreras · Interna Morena 2026<br>
    Datos: INE julio 2026 · INEGI Censo 2020 · CONAPO · IECM 2024
</p>
""", unsafe_allow_html=True)
