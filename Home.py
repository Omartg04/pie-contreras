"""
Home.py — PIE · Plataforma de Inteligencia Electoral
Dashboard principal: KPIs generales y orientación al coordinador.
"""
import streamlit as st
from app_utils import (
    verificar_acceso, aplicar_estilos, header, kpi,
    cargar_ranking, cargar_unificado,
    COLOR_ALTA, COLOR_ACENTO, COLOR_MEDIA, COLOR_BAJA, COLOR_MORENA,
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
        <p style='color:{COLOR_ACENTO}; font-size:0.72rem; letter-spacing:0.12em;
                  text-transform:uppercase; margin:0;'>PIE</p>
        <p style='color:{COLOR_TEXTO}; font-size:1rem; font-weight:600; margin:0.2rem 0;'>
            La Magdalena Contreras
        </p>
        <p style='color:{COLOR_ACENTO};font-weight:600; font-size:0.78rem; margin:0;'>
            Bernardo Aguilar 2027
        </p>
    </div>
    <hr style='border:none;border-top:1px solid #3a1010;margin:0.8rem 0;'>
    """, unsafe_allow_html=True)

    st.page_link("Home.py",                      label="🏠  Inicio",               )
    st.page_link("pages/01_Mapa_Secciones.py",   label="🗺️  Mapa de secciones"     )
    st.page_link("pages/02_Mapa_Manzanas.py",    label="📍  Mapa de manzanas"      )
    st.page_link("pages/03_Ranking.py",           label="🔍  Fichas de sección"       )

    st.markdown("<hr style='border:none;border-top:1px solid #3a1010;margin:1rem 0;'>",
                unsafe_allow_html=True)
    if st.button("Cerrar sesión", use_container_width=True):
        from app_utils import cerrar_sesion
        cerrar_sesion()

# ── Header ────────────────────────────────────────────────────────────────────
header("Inicio", "Resumen del módulo de priorización territorial")

# ── Cargar datos ──────────────────────────────────────────────────────────────
rank = cargar_ranking()
gdf  = cargar_unificado()

p3   = rank[(rank["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA") & (rank["SECCION"]>0)].sort_values("RANK_ESTRATEGICO")
nucl      = p3.head(25)
extension = p3.tail(len(p3)-25)
referencia= rank[(rank["NIVEL_PRIORIDAD_OP"]!="P3_MEDIA") & (rank["SECCION"]>0)]
total_secs = len(rank[rank["SECCION"]>0])

mzas_s1      = gdf[gdf["es_prioritaria_s1"]==True]
ln_mzas_s1   = mzas_s1["LN_estimada"].sum()
ln_total_mun = gdf["LN_estimada"].sum()
pct_cobertura = ln_mzas_s1 / ln_total_mun * 100 if ln_total_mun > 0 else 0

# ── KPIs ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi("Secciones operativas",
        f"{len(p3)}",
        f"Núcleo prioritario: {len(nucl)}",
        COLOR_ALTA)
    st.markdown(f"""
    <p style='color:{COLOR_SECUNDARIO};font-size:0.78rem;line-height:1.5;
              margin:-0.2rem 0 1rem;padding:0 0.2rem;'>
        Secciones con mayor probabilidad de ser incluidas en la muestra.
        Las primeras 25 concentran la mayor rentabilidad territorial.
    </p>""", unsafe_allow_html=True)
with c2:
    kpi("Manzanas prioritarias",
        f"{len(mzas_s1):,}",
        f"Corte 50% LN por sección",
        COLOR_ALTA)
    st.markdown(f"""
    <p style='color:{COLOR_SECUNDARIO};font-size:0.78rem;line-height:1.5;
              margin:-0.2rem 0 1rem;padding:0 0.2rem;'>
        Manzanas que concentran el 50% de la lista nominal de cada sección.
        El destino de las brigadas de campo.
    </p>""", unsafe_allow_html=True)
with c3:
    kpi("Electores en secciones prioritarias",
        f"{nucl['LN_TOTAL'].sum():,.0f}",
        f"{nucl['LN_TOTAL'].sum()/213700*100:.1f}% del padrón total",
        COLOR_MEDIA)
    st.markdown(f"""
    <p style='color:{COLOR_SECUNDARIO};font-size:0.78rem;line-height:1.5;
              margin:-0.2rem 0 1rem;padding:0 0.2rem;'>
        Electores que viven en las secciones prioritarias. Concentrar
        la operación aquí maximiza la incidencia en cualquier encuesta externa.
    </p>""", unsafe_allow_html=True)
with c4:
    kpi("Cobertura del operativo",
        f"{pct_cobertura:.1f}%",
        f"{ln_mzas_s1:,.0f} electores en manzanas prioritarias",
        COLOR_ALTA)
    st.markdown(f"""
    <p style='color:{COLOR_SECUNDARIO};font-size:0.78rem;line-height:1.5;
              margin:-0.2rem 0 1rem;padding:0 0.2rem;'>
        Fracción del padrón municipal que vive en las manzanas donde
        operan las brigadas. A mayor cobertura, mayor impacto.
    </p>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Franja de contexto — universo de priorización ────────────────────────────
# Usar columnas nativas de Streamlit para evitar problemas de rendering HTML complejo

def _celda(numero, label, sublabel="", color="#FFFFFF"):
    return f"""<div style='text-align:center; padding:0.6rem 0.2rem;'>
        <p style='color:{color}; font-family:"Barlow Condensed",sans-serif;
                  font-size:2rem; font-weight:700; margin:0; line-height:1;'>{numero}</p>
        <p style='color:#C8C0C0; font-size:0.74rem; margin:3px 0 0;'>{label}</p>
        <p style='color:#555555; font-size:0.68rem; margin:1px 0 0;'>{sublabel}</p>
    </div>"""

def _flecha(simbolo="→"):
    return f"""<div style='text-align:center; padding:0.6rem 0; color:#8a4a52;
                font-size:1.4rem; font-weight:300;'>{simbolo}</div>"""

st.markdown(f"<p style='color:{COLOR_SECUNDARIO}; font-size:0.72rem; letter-spacing:0.1em; text-transform:uppercase; margin:0 0 0.4rem;'>Universo de priorización — La Magdalena Contreras</p>", unsafe_allow_html=True)

_BG = f"background:{COLOR_TARJETA}; border:1px solid #3a1010; border-radius:6px; padding:0.3rem 0.5rem;"

c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2, 0.6, 2, 0.6, 2, 0.6, 2, 2])

with c1:
    st.markdown(f"<div style='{_BG}'>" + _celda(total_secs, "secciones totales", "", COLOR_TEXTO) + "</div>", unsafe_allow_html=True)
with c2:
    st.markdown(_flecha("→"), unsafe_allow_html=True)
with c3:
    st.markdown(f"<div style='{_BG}'>" + _celda(len(p3), "secciones operativas", "mayor prob. de encuesta", COLOR_ACENTO) + "</div>", unsafe_allow_html=True)
with c4:
    st.markdown(_flecha("→"), unsafe_allow_html=True)
with c5:
    st.markdown(f"<div style='{_BG}'>" + _celda(len(nucl), "núcleo prioritario", "mayor rentabilidad", COLOR_ALTA) + "</div>", unsafe_allow_html=True)
with c6:
    st.markdown(_flecha("+"), unsafe_allow_html=True)
with c7:
    st.markdown(f"<div style='{_BG}'>" + _celda(len(extension), "extensión operativa", "cobertura complementaria", COLOR_MEDIA) + "</div>", unsafe_allow_html=True)
with c8:
    st.markdown(f"""<div style='border-left:1px solid #3a1010; padding:0.6rem 0 0.6rem 0.8rem;'>
        <p style='color:#555555; font-size:0.75rem; margin:0;'>{len(referencia)} de referencia</p>
        <p style='color:#555555; font-size:0.68rem; margin:3px 0 0; line-height:1.4;'>
            proyección estadística<br>sin operación de campo</p>
    </div>""", unsafe_allow_html=True)

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
        lambda r: "★ Top 25" if r<=25 else "Extensión")
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
    st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.73rem;margin-top:0.2rem;'>★ Top 25 = secciones con mayor rentabilidad territorial (núcleo del operativo)</p>",
                unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Helper CSV limpio ─────────────────────────────────────────────
    def _csv_limpio(df_in, incluir_referencia=False):
        df = df_in[df_in["SECCION"] > 0].copy()
        df = df.sort_values("RANK_ESTRATEGICO")
        df["Prioridad"] = df.apply(
            lambda r: (
                "Núcleo top 25"           if r["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA" and r["RANK_ESTRATEGICO"]<=26
                else "Extensión operativa" if r["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA"
                else "Referencia"
            ), axis=1
        )
        if not incluir_referencia:
            df = df[df["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA"]
        df["Fuerza Morena (%)"]      = (df["fuerza_morena"] * 100).round(1)
        df["Participación 2024 (%)"] = (df["PARTICIPACION_2024"] * 100).round(1)
        cols = {
            "RANK_ESTRATEGICO":       "# Ranking",
            "SECCION":                "Sección",
            "LN_TOTAL":               "Lista Nominal",
            "Prioridad":              "Prioridad",
            "IRE_SCORE":              "Probabilidad de encuesta",
            "Fuerza Morena (%)":      "Fuerza Morena (%)",
            "INDICE_RENTABILIDAD":    "Índice Rentabilidad",
            "Participación 2024 (%)": "Participación 2024 (%)",
        }
        return df[list(cols.keys())].rename(columns=cols).to_csv(index=False).encode("utf-8")

    bd1, bd2 = st.columns(2)
    with bd1:
        st.download_button(
            label="⬇  59 secciones operativas",
            data=_csv_limpio(rank, incluir_referencia=False),
            file_name="pie_010_mc_operativas.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with bd2:
        st.download_button(
            label="⬇  Universo completo (148 secciones)",
            data=_csv_limpio(rank, incluir_referencia=True),
            file_name="pie_010_mc_universo_completo.csv",
            mime="text/csv",
            use_container_width=True,
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
        <p><span style='color:{COLOR_ACENTO}; font-weight:600;'>Prob. encuesta</span><br>
        En cuántas de cada 10 simulaciones cayó esta sección en la muestra.
        Un valor de 0.72 significa 7 de cada 10.</p>
        <p><span style='color:{COLOR_ACENTO}; font-weight:600;'>Fuerza Morena</span><br>
        % de electores del padrón que votaron por el bloque en 2024.
        No sobre quienes votaron — sobre el total registrado.</p>
        <p style='margin-bottom:0;'>
        <span style='color:{COLOR_ACENTO}; font-weight:600;'>Índice Rentabilidad</span><br>
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
        <p>Morena ganó por <span style='color:{COLOR_ACENTO};font-weight:600;'>+1.96 pp</span>
        sobre la oposición. Cuarta alternancia consecutiva.</p>
        <p style='margin-bottom:0;'>
        En las 52 secciones de mayor padrón (S1), Morena tiene
        <span style='color:{COLOR_ACENTO};font-weight:600;'>+11.1 pp</span>
        de ventaja. Ahí se concentra el operativo.</p>
    </div>
    """, unsafe_allow_html=True)

# ── Nota metodológica ────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📋  Notas sobre los datos y alcance del modelo", expanded=False):
    st.markdown(f"""
    <div style='font-size:0.82rem; color:{COLOR_SECUNDARIO}; line-height:1.7;'>
        <p style='color:{COLOR_TEXTO}; font-weight:600; margin:0 0 0.5rem;'>
            Fuentes y fecha de corte
        </p>
        <p>Lista Nominal INE · julio 2026 &nbsp;·&nbsp;
           INEGI Censo 2020 &nbsp;·&nbsp;
           CONAPO proyecciones 2026 &nbsp;·&nbsp;
           IECM resultados 2024 &nbsp;·&nbsp;
           Monte Carlo 30 diseños × 10,000 iteraciones · Semilla 42</p>
        <p style='color:{COLOR_TEXTO}; font-weight:600; margin:0.8rem 0 0.5rem;'>
            Alcance del modelo
        </p>
        <p>La probabilidad de encuesta identifica unidades con certeza o alta robustez de
           inclusión bajo la familia de diseños muestrales probabilísticos estándar del
           mercado (PPT sobre lista nominal, muestreo en vivienda, dos o tres etapas).
           No cubre diseños atípicos: cuotas en puntos de afluencia, muestras
           telefónicas o paneles en línea.</p>
        <p style='color:{COLOR_TEXTO}; font-weight:600; margin:0.8rem 0 0.5rem;'>
            Brecha cartográfica conocida — Sección 3072
        </p>
        <p>La sección <strong style='color:{COLOR_ACENTO};'>3072</strong>
           (ranking #14 · 1,773 electores) está presente en el ranking operativo
           con todos sus indicadores correctos — probabilidad de encuesta, fuerza
           Morena e índice de rentabilidad — porque estos se calculan a nivel de
           sección desde la lista nominal.</p>
        <p>Lo que no está disponible es la <strong>guía de manzanas</strong>:
           el modelo cartográfico no le asignó manzanas del marco geoestadístico
           INEGI 2020, por lo que no existe mapa de campo imprimible ni
           priorización por bloque para esta sección. No es un error de la
           plataforma — es una brecha en los datos de origen.</p>
        <p><strong style='color:{COLOR_ACENTO};'>Indicación para el coordinador de
           sección 3072:</strong> cubrir la sección completa usando el polígono
           visible en el Mapa de Secciones como referencia geográfica. Con
           1,773 electores en el contexto de una interna, la cobertura total
           de la sección es operativamente viable sin priorización por manzana.</p>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<p style='color:{COLOR_BAJA}; font-size:0.72rem; text-align:center;'>
    PIE · Plataforma de Inteligencia Electoral · La Magdalena Contreras · Bernardo Aguilar 2027<br>
    Data & AI Inclusion Technologies
</p>
""", unsafe_allow_html=True)