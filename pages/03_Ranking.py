"""
03_Ranking.py — PIE · Ranking operativo y ficha por sección
"""
import streamlit as st
import pandas as pd
import geopandas as gpd
from app_utils import (
    verificar_acceso, aplicar_estilos, header, kpi,
    cargar_ranking, cargar_unificado, cargar_secciones,
    badge_nivel, es_nucleo,
    COLOR_ALTA, COLOR_ACENTO, COLOR_MEDIA, COLOR_BAJA, COLOR_MORENA, COLOR_POSITIVO,
    COLOR_TARJETA, COLOR_TEXTO, COLOR_SECUNDARIO,
    NIVEL_LABEL,
)

st.set_page_config(
    page_title="Ranking · PIE",
    page_icon="📊",
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
    st.page_link("pages/03_Ranking.py",           label="📊  Ranking y ficha")
    st.markdown("<hr style='border:none;border-top:1px solid #3a1010;margin:1rem 0;'>",
                unsafe_allow_html=True)
    if st.button("Cerrar sesión", use_container_width=True):
        from app_utils import cerrar_sesion
        cerrar_sesion()

# ── Header ────────────────────────────────────────────────────────────────────
header("Ranking Operativo", "Secciones ordenadas por índice de rentabilidad territorial")

# ── Cargar datos ──────────────────────────────────────────────────────────────
rank = cargar_ranking()
gdf  = cargar_unificado()
secs = cargar_secciones()

# GANADOR_2024 y MARGEN_PCT_2024 vienen del GeoJSON de secciones.
# PARTICIPACION_2024 ya está en el ranking CSV — excluirla del merge
# para evitar columnas duplicadas _x/_y.
COLS_ELECT = ["SECCION", "GANADOR_2024", "MARGEN_PCT_2024"]
cols_elect_ok = [c for c in COLS_ELECT if c in secs.columns]
rank = rank.merge(secs[cols_elect_ok], on="SECCION", how="left")

# Limpiar nombres de ganador para presentación
GANADOR_LABEL = {
    "MORENA":          "Morena",
    "VA_POR_MEXICO":   "Va por México",
    "PAN":             "PAN",
    "PRI":             "PRI",
    "PRD":             "PRD",
    "MC":              "Mov. Ciudadano",
}
def _limpiar_ganador(g):
    if pd.isna(g) or g == "":
        return "—"
    return GANADOR_LABEL.get(str(g).strip().upper(), str(g))

rank["GANADOR_LABEL"] = rank["GANADOR_2024"].apply(_limpiar_ganador)

# Secciones operativas
p3 = rank[(rank["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA") & (rank["SECCION"]>0)].copy()
p3["es_nucleo"] = p3["RANK_ESTRATEGICO"].apply(lambda r: r <= 26)
p3["Prioridad"] = p3["es_nucleo"].apply(lambda x: "★ Núcleo" if x else "Extensión")

# Manzanas prioritarias por sección (para tabla y ficha)
mzas_prio_x_sec = (
    gdf[gdf["es_prioritaria_s1"]==True]
    .groupby("SECCION")
    .agg(n_mzas=("LN_estimada","count"), ln_mzas=("LN_estimada","sum"))
    .reset_index()
)
p3 = p3.merge(mzas_prio_x_sec, on="SECCION", how="left")
p3["n_mzas"]  = p3["n_mzas"].fillna(0).astype(int)
p3["ln_mzas"] = p3["ln_mzas"].fillna(0)
p3["pct_cub"] = p3.apply(
    lambda r: r["ln_mzas"] / r["LN_TOTAL"] * 100 if r["LN_TOTAL"] > 0 else 0, axis=1)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_rank, tab_ficha, tab_descarga = st.tabs(
    ["📋  Ranking completo", "🔍  Ficha por sección", "⬇  Descargas"])

# ════════════════════════════════════════════════════════════════════════════
with tab_rank:
    # Filtros
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        filtro_prio = st.radio(
            "Prioridad",
            options=["Todas", "★ Núcleo", "Extensión"],
            index=0, horizontal=True,
        )
    with col_f2:
        min_ire = st.slider("Prob. mínima encuesta", 0.0, 1.0, 0.0, 0.01)

    p3_filt = p3.copy()
    if filtro_prio != "Todas":
        p3_filt = p3_filt[p3_filt["Prioridad"] == filtro_prio]
    p3_filt = p3_filt[p3_filt["IRE_SCORE"] >= min_ire]

    # Tabla formateada
    p3_disp = p3_filt[[
        "RANK_ESTRATEGICO", "SECCION", "LN_TOTAL", "Prioridad",
        "IRE_SCORE", "fuerza_morena", "INDICE_RENTABILIDAD",
        "n_mzas", "pct_cub",
        "PARTICIPACION_2024", "GANADOR_LABEL", "MARGEN_PCT_2024",
    ]].copy()

    p3_disp.columns = [
        "#", "Sección", "LN", "Prioridad",
        "Prob. encuesta", "Fuerza Morena", "Índice Rentabilidad",
        "Manzanas prio.", "% LN cubierta",
        "Participación 2024", "Ganador 2024", "Margen 2024",
    ]
    p3_disp["LN"]                  = p3_disp["LN"].apply(lambda x: f"{x:,.0f}")
    p3_disp["Prob. encuesta"]      = p3_disp["Prob. encuesta"].apply(lambda x: f"{x:.3f}")
    p3_disp["Fuerza Morena"]       = p3_disp["Fuerza Morena"].apply(
        lambda x: f"{x*100:.1f}%" if pd.notna(x) else "—")
    p3_disp["Índice Rentabilidad"] = p3_disp["Índice Rentabilidad"].apply(lambda x: f"{x:.3f}")
    p3_disp["% LN cubierta"]       = p3_disp["% LN cubierta"].apply(lambda x: f"{x:.1f}%")
    p3_disp["Participación 2024"]  = p3_disp["Participación 2024"].apply(
        lambda x: f"{x*100:.1f}%" if pd.notna(x) else "—")
    p3_disp["Margen 2024"]         = p3_disp["Margen 2024"].apply(
        lambda x: f"{x*100:+.1f} pp" if pd.notna(x) else "—")
    p3_disp["Ganador 2024"]        = p3_disp["Ganador 2024"].fillna("—")

    st.dataframe(
        p3_disp,
        use_container_width=True,
        hide_index=True,
        height=480,
        column_config={
            "#":       st.column_config.NumberColumn(width="small"),
            "Sección": st.column_config.NumberColumn(width="small"),
        }
    )
    st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.75rem;'>"
                f"{len(p3_filt)} secciones · "
                f"★ Núcleo = top 25 de mayor rentabilidad territorial</p>",
                unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
with tab_ficha:
    sec_lista = p3.sort_values("RANK_ESTRATEGICO")["SECCION"].tolist()
    sec_sel = st.selectbox(
        "Selecciona una sección",
        options=sec_lista,
        format_func=lambda s: (
            f"Sección {s} — ★ Núcleo #{int(p3.loc[p3['SECCION']==s,'RANK_ESTRATEGICO'].values[0])}"
            if p3.loc[p3['SECCION']==s,'es_nucleo'].values[0]
            else f"Sección {s} — Extensión #{int(p3.loc[p3['SECCION']==s,'RANK_ESTRATEGICO'].values[0])}"
        )
    )

    if sec_sel:
        row_sec  = p3[p3["SECCION"]==sec_sel].iloc[0]
        mzas_sec = gdf[gdf["SECCION"]==sec_sel].copy()
        mzas_s1  = mzas_sec[mzas_sec["es_prioritaria_s1"]==True].sort_values("ranking_seccion")
        mzas_hall= mzas_sec[
            (mzas_sec["NIVEL_MZA"]=="MA_ALTA") & (~mzas_sec["es_prioritaria_s1"])
        ] if "NIVEL_MZA" in mzas_sec.columns else pd.DataFrame()

        nucleo   = bool(row_sec["es_nucleo"])
        rnk      = int(row_sec["RANK_ESTRATEGICO"])
        etiqueta = "★ NÚCLEO PRIORITARIO" if nucleo else "EXTENSIÓN OPERATIVA"
        col_et   = COLOR_ALTA if nucleo else COLOR_MEDIA
        fm       = row_sec.get("fuerza_morena")
        ganador  = row_sec.get("GANADOR_LABEL", "—")
        margen   = row_sec.get("MARGEN_PCT_2024")
        part     = row_sec.get("PARTICIPACION_2024")
        color_gan= COLOR_MORENA if ganador == "Morena" else COLOR_MEDIA

        # ── Encabezado de ficha — llamadas pequeñas ───────────────────
        col_tit, col_badge = st.columns([4, 1])
        with col_tit:
            st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;"
                        f"letter-spacing:0.1em;text-transform:uppercase;margin:0;'>"
                        f"Ficha de sección</p>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color:{COLOR_TEXTO};margin:0.1rem 0;"
                        f"font-size:1.6rem;'>Sección {int(sec_sel)}</h2>",
                        unsafe_allow_html=True)
        with col_badge:
            st.markdown(f"<div style='padding-top:0.8rem;'>"
                        f"<span style='background:{col_et};color:#fff;padding:4px 10px;"
                        f"border-radius:4px;font-size:0.78rem;font-weight:700;'>"
                        f"#{rnk} · {etiqueta}</span></div>",
                        unsafe_allow_html=True)

        st.markdown(f"<hr style='border:none;border-top:1px solid #3a1010;margin:0.5rem 0 1rem;'>",
                    unsafe_allow_html=True)

        # ── KPIs ──────────────────────────────────────────────────────
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            kpi("Lista Nominal", f"{row_sec.get('LN_TOTAL',0):,.0f}", color=col_et)
        with c2:
            kpi("Manzanas prioritarias", str(int(row_sec.get("n_mzas", 0))), color=COLOR_ALTA)
        with c3:
            kpi("LN en manzanas prio.", f"{int(row_sec.get('ln_mzas',0)):,}", color=COLOR_ALTA)
        with c4:
            kpi("% LN cubierta", f"{row_sec.get('pct_cub',0):.1f}%",
                "del padrón de la sección", COLOR_ACENTO)
        with c5:
            kpi("Prob. encuesta",
                f"{row_sec.get('IRE_SCORE',0):.3f}",
                "de cada 10 encuestas incluye esta sección", COLOR_MEDIA)
        with c6:
            kpi("Fuerza Morena",
                f"{fm*100:.1f}%" if pd.notna(fm) else "—",
                "% del padrón que votó Morena 2024", COLOR_MORENA)

        st.markdown("<br>", unsafe_allow_html=True)
        col_mzas, col_elect = st.columns([3, 2])

        with col_mzas:
            st.markdown(f"<p style='color:{COLOR_TEXTO};font-size:0.9rem;"
                        f"font-weight:600;margin-bottom:0.4rem;'>"
                        f"Manzanas prioritarias (50% LN)</p>", unsafe_allow_html=True)
            if len(mzas_s1):
                mzas_disp = mzas_s1[["ranking_seccion", "LN_estimada",
                                      "fuente_estimacion"]].copy()
                if "IRE_MZA" in mzas_s1.columns:
                    mzas_disp["IRE_MZA"] = mzas_s1["IRE_MZA"].values
                    mzas_disp.columns = ["Manzana", "LN estimada", "Fuente", "Prob. manzana"]
                    mzas_disp["Prob. manzana"] = mzas_disp["Prob. manzana"].apply(
                        lambda x: f"{x:.3f}" if pd.notna(x) else "—")
                else:
                    mzas_disp.columns = ["Manzana", "LN estimada", "Fuente"]
                mzas_disp["Manzana"]     = mzas_disp["Manzana"].apply(lambda x: f"M{int(x)}")
                mzas_disp["LN estimada"] = mzas_disp["LN estimada"].apply(lambda x: f"{x:,.0f}")
                st.dataframe(mzas_disp, use_container_width=True, hide_index=True, height=280)
                ln_cub = mzas_s1["LN_estimada"].sum()
                ln_tot = row_sec.get("LN_TOTAL", 1)
                st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;'>"
                            f"LN cubierta: {ln_cub:,.0f} "
                            f"({ln_cub/ln_tot*100:.1f}% del padrón de la sección)</p>",
                            unsafe_allow_html=True)
            else:
                st.info("Sin manzanas prioritarias registradas.")

            if len(mzas_hall):
                st.markdown(f"<p style='color:{COLOR_ACENTO};font-size:0.82rem;"
                            f"font-weight:600;margin-top:0.8rem;'>"
                            f"★ Manzanas destacadas ({len(mzas_hall)})</p>",
                            unsafe_allow_html=True)
                st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.78rem;'>"
                            f"Alta probabilidad de encuesta fuera del corte de LN — "
                            f"hallazgo del modelo, no aparecen en ranking estándar.</p>",
                            unsafe_allow_html=True)
                hall_disp = mzas_hall[["ranking_seccion", "LN_estimada"]].copy()
                hall_disp.columns = ["Posición en sección", "LN estimada"]
                hall_disp["LN estimada"] = hall_disp["LN estimada"].apply(lambda x: f"{x:,.0f}")
                st.dataframe(hall_disp, use_container_width=True, hide_index=True)

        with col_elect:
            st.markdown(f"<p style='color:{COLOR_TEXTO};font-size:0.9rem;"
                        f"font-weight:600;margin-bottom:0.4rem;'>"
                        f"Histórico electoral</p>", unsafe_allow_html=True)

            kpi("Ganador 2024", ganador, color=color_gan)
            kpi("Margen 2024",
                f"{margen*100:+.1f} pp" if pd.notna(margen) else "—",
                "diferencia entre 1° y 2° lugar", COLOR_MEDIA)
            kpi("Participación 2024",
                f"{part*100:.1f}%" if pd.notna(part) else "—",
                "votantes sobre lista nominal", COLOR_MEDIA)

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.74rem;"
                        f"line-height:1.5;'>"
                        f"La fuerza Morena de <b style='color:{COLOR_MORENA};'>"
                        f"{f'{fm*100:.1f}%' if pd.notna(fm) else '—'}</b> "
                        f"se calcula sobre el padrón total, no sobre votos emitidos.</p>",
                        unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
with tab_descarga:
    st.markdown(f"<h3 style='color:{COLOR_TEXTO};font-size:1.1rem;margin-bottom:1rem;'>"
                f"Descargas</h3>", unsafe_allow_html=True)

    # CSV limpio reutilizando la misma lógica que Home
    def _csv_limpio(df_in, incluir_referencia=False):
        df = df_in[df_in["SECCION"] > 0].copy()
        df = df.sort_values("RANK_ESTRATEGICO")
        df["Prioridad"] = df.apply(
            lambda r: (
                "Núcleo top 25"            if r["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA" and r["RANK_ESTRATEGICO"]<=26
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
        available = {k: v for k, v in cols.items() if k in df.columns}
        return df[list(available.keys())].rename(columns=available).to_csv(index=False).encode("utf-8")

    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        st.markdown(f"<p style='color:{COLOR_TEXTO};font-weight:600;margin:0 0 0.2rem;'>"
                    f"59 secciones operativas</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.80rem;margin:0 0 0.6rem;'>"
                    f"Ranking limpio en español, listo para el coordinador.</p>",
                    unsafe_allow_html=True)
        st.download_button(
            label="⬇  Descargar CSV",
            data=_csv_limpio(rank, incluir_referencia=False),
            file_name="pie_010_mc_operativas.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_d2:
        st.markdown(f"<p style='color:{COLOR_TEXTO};font-weight:600;margin:0 0 0.2rem;'>"
                    f"Universo completo (148 secciones)</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.80rem;margin:0 0 0.6rem;'>"
                    f"Incluye secciones de referencia con su rol.</p>",
                    unsafe_allow_html=True)
        st.download_button(
            label="⬇  Descargar CSV",
            data=_csv_limpio(rank, incluir_referencia=True),
            file_name="pie_010_mc_universo_completo.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_d3:
        st.markdown(f"<p style='color:{COLOR_TEXTO};font-weight:600;margin:0 0 0.2rem;'>"
                    f"Mapas de campo PDF</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.80rem;margin:0 0 0.6rem;'>"
                    f"59 hojas imprimibles — una por sección.</p>",
                    unsafe_allow_html=True)
        try:
            with open("assets/pie_010_mc_hojas_campo.pdf", "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="⬇  Descargar PDF",
                data=pdf_bytes,
                file_name="pie_010_mc_hojas_campo.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except FileNotFoundError:
            st.info("El PDF se agregará próximamente.")

    st.markdown(f"<p style='color:{COLOR_BAJA};font-size:0.72rem;margin-top:1.5rem;'>"
                f"Datos: INE julio 2026 · INEGI Censo 2020 · CONAPO · IECM 2024 · "
                f"Monte Carlo 30 diseños × 10,000 iteraciones · Semilla 42</p>",
                unsafe_allow_html=True)