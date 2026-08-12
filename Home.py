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
            Interna Morena 2026
        </p>
    </div>
    <hr style='border:none;border-top:1px solid #3a1010;margin:0.8rem 0;'>
    """, unsafe_allow_html=True)

    st.page_link("Home.py",                      label="🏠  Inicio",               )
    st.page_link("pages/01_Mapa_Secciones.py",   label="🗺️  Mapa de secciones"     )
    st.page_link("pages/02_Mapa_Manzanas.py",    label="📍  Mapa de manzanas"      )
    st.page_link("pages/03_Ranking.py",           label="📊  Ranking y ficha"       )

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
st.markdown(f"""
<div style='background:{COLOR_TARJETA}; border:1px solid #3a1010; border-radius:8px;
            padding:1rem 1.5rem; margin-bottom:1.2rem;'>
    <p style='color:{COLOR_SECUNDARIO}; font-size:0.72rem; letter-spacing:0.1em;
              text-transform:uppercase; margin:0 0 0.8rem;'>
        Universo de priorización — La Magdalena Contreras
    </p>
    <div style='display:flex; align-items:center; gap:0; flex-wrap:wrap;'>

        <div style='text-align:center; padding:0 1.2rem;'>
            <p style='color:{COLOR_TEXTO}; font-family:"Barlow Condensed",sans-serif;
                      font-size:2rem; font-weight:700; margin:0; line-height:1;'>
                {total_secs}
            </p>
            <p style='color:{COLOR_SECUNDARIO}; font-size:0.75rem; margin:3px 0 0;'>
                secciones totales
            </p>
        </div>

        <p style='color:#3a1010; font-size:1.8rem; margin:0; padding:0 0.2rem;'>→</p>

        <div style='text-align:center; padding:0 1.2rem;
                    border-left:2px solid #3a1010; border-right:2px solid #3a1010;'>
            <p style='color:{COLOR_ACENTO}; font-family:"Barlow Condensed",sans-serif;
                      font-size:2rem; font-weight:700; margin:0; line-height:1;'>
                {len(p3)}
            </p>
            <p style='color:{COLOR_SECUNDARIO}; font-size:0.75rem; margin:3px 0 0;'>
                secciones operativas
            </p>
            <p style='color:{COLOR_BAJA}; font-size:0.68rem; margin:1px 0 0;'>
                mayor probabilidad de encuesta
            </p>
        </div>

        <p style='color:#3a1010; font-size:1.8rem; margin:0; padding:0 0.2rem;'>→</p>

        <div style='text-align:center; padding:0 1.2rem;'>
            <p style='color:{COLOR_ALTA}; font-family:"Barlow Condensed",sans-serif;
                      font-size:2rem; font-weight:700; margin:0; line-height:1;'>
                {len(nucl)}
            </p>
            <p style='color:{COLOR_SECUNDARIO}; font-size:0.75rem; margin:3px 0 0;'>
                núcleo prioritario
            </p>
            <p style='color:{COLOR_BAJA}; font-size:0.68rem; margin:1px 0 0;'>
                mayor rentabilidad territorial
            </p>
        </div>

        <p style='color:#3a1010; font-size:1.8rem; margin:0; padding:0 0.2rem;'>+</p>

        <div style='text-align:center; padding:0 1.2rem;'>
            <p style='color:{COLOR_MEDIA}; font-family:"Barlow Condensed",sans-serif;
                      font-size:2rem; font-weight:700; margin:0; line-height:1;'>
                {len(extension)}
            </p>
            <p style='color:{COLOR_SECUNDARIO}; font-size:0.75rem; margin:3px 0 0;'>
                extensión operativa
            </p>
            <p style='color:{COLOR_BAJA}; font-size:0.68rem; margin:1px 0 0;'>
                cobertura complementaria
            </p>
        </div>

        <div style='margin-left:auto; text-align:right; padding-left:1rem;
                    border-left:1px solid #3a1010;'>
            <p style='color:{COLOR_BAJA}; font-size:0.75rem; margin:0;'>
                {len(referencia)} secciones de referencia
            </p>
            <p style='color:{COLOR_BAJA}; font-size:0.68rem; margin:2px 0 0;'>
                proyección estadística · sin operación de campo
            </p>
        </div>

    </div>
</div>
""", unsafe_allow_html=True)

# ── Dos columnas: top 10 + contexto ──────────────────────────────────────────
col_tabla, col_info = st.columns([3, 2])

with col_tabla:
    col_h, col_btn = st.columns([3, 1])
    with col_h:
        st.markdown(f"""
        <h3 style='color:{COLOR_TEXTO}; font-size:1.1rem; margin-bottom:0.8rem;'>
            Top 10 secciones — Ranking operativo
        </h3>
        """, unsafe_allow_html=True)
    with col_btn:
        # ── Helper: preparar CSV limpio ────────────────────────────────
        def _csv_limpio(df_in, incluir_referencia=False):
            df = df_in[df_in["SECCION"] > 0].copy()
            df = df.sort_values("RANK_ESTRATEGICO")
            df["Prioridad"] = df.apply(
                lambda r: (
                    "Núcleo top 25"      if r["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA" and r["RANK_ESTRATEGICO"]<=26
                    else "Extensión operativa" if r["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA"
                    else "Referencia"
                ), axis=1
            )
            if not incluir_referencia:
                df = df[df["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA"]
            df["Fuerza Morena (%)"]    = (df["fuerza_morena"] * 100).round(1)
            df["Participación 2024 (%)"] = (df["PARTICIPACION_2024"] * 100).round(1)
            cols = {
                "RANK_ESTRATEGICO":      "# Ranking",
                "SECCION":               "Sección",
                "LN_TOTAL":              "Lista Nominal",
                "Prioridad":             "Prioridad",
                "IRE_SCORE":             "Probabilidad de encuesta",
                "Fuerza Morena (%)":     "Fuerza Morena (%)",
                "INDICE_RENTABILIDAD":   "Índice Rentabilidad",
                "Participación 2024 (%)":"Participación 2024 (%)",
            }
            return df[list(cols.keys())].rename(columns=cols).to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇  59 secciones operativas",
            data=_csv_limpio(rank, incluir_referencia=False),
            file_name="pie_010_mc_operativas.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        st.download_button(
            label="⬇  Universo completo (148 secciones)",
            data=_csv_limpio(rank, incluir_referencia=True),
            file_name="pie_010_mc_universo_completo.csv",
            mime="text/csv",
            use_container_width=True,
        )

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

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<p style='color:{COLOR_BAJA}; font-size:0.72rem; text-align:center;'>
    PIE · Plataforma de Inteligencia Electoral · La Magdalena Contreras · Interna Morena 2026<br>
    Datos: INE julio 2026 · INEGI Censo 2020 · CONAPO · IECM 2024
</p>
""", unsafe_allow_html=True)