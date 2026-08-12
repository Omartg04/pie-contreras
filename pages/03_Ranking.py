"""
03_Ranking.py — PIE · Ranking operativo y ficha por sección
"""
import streamlit as st
import pandas as pd
import geopandas as gpd
import io
from app_utils import (
    verificar_acceso, aplicar_estilos, header, kpi,
    cargar_ranking, cargar_unificado,
    badge_nivel, es_nucleo,
    COLOR_ALTA, COLOR_MEDIA, COLOR_BAJA, COLOR_MORENA, COLOR_POSITIVO,
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

    if st.button("Cerrar sesión", use_container_width=True):
        from app_utils import cerrar_sesion
        cerrar_sesion()

# ── Header ────────────────────────────────────────────────────────────────────
header("Ranking Operativo", "Secciones ordenadas por índice de rentabilidad territorial")

# ── Cargar datos ──────────────────────────────────────────────────────────────
rank = cargar_ranking()
gdf  = cargar_unificado()

p3 = rank[(rank["NIVEL_PRIORIDAD_OP"]=="P3_MEDIA") & (rank["SECCION"]>0)].copy()
p3["Prioridad"] = p3["RANK_ESTRATEGICO"].apply(
    lambda r: "★ Núcleo" if r<=25 else "Extensión")

# ── Tabla ranking ─────────────────────────────────────────────────────────────
tab_rank, tab_ficha, tab_descarga = st.tabs(["Ranking completo", "Ficha por sección", "Descargas"])

with tab_rank:
    # Filtros inline
    col_f1, col_f2, _ = st.columns([1, 1, 2])
    with col_f1:
        filtro_prio = st.multiselect(
            "Prioridad",
            options=["★ Núcleo", "Extensión"],
            default=["★ Núcleo", "Extensión"],
        )
    with col_f2:
        min_ire = st.slider("Prob. mínima encuesta", 0.0, 1.0, 0.0, 0.01)

    p3_filt = p3[
        (p3["Prioridad"].isin(filtro_prio)) &
        (p3["IRE_SCORE"] >= min_ire)
    ].copy()

    # Formatear
    p3_disp = p3_filt[[
        "RANK_ESTRATEGICO","SECCION","LN_TOTAL","Prioridad",
        "IRE_SCORE","fuerza_morena","INDICE_RENTABILIDAD",
        "PARTICIPACION_2024","GANADOR_2024","MARGEN_PCT_2024"
    ]].copy()
    p3_disp.columns = [
        "#","Sección","LN","Prioridad",
        "Prob. encuesta","Fuerza Morena","Índice Rentabilidad",
        "Participación 2024","Ganador 2024","Margen 2024"
    ]
    p3_disp["LN"]                  = p3_disp["LN"].apply(lambda x: f"{x:,.0f}")
    p3_disp["Prob. encuesta"]      = p3_disp["Prob. encuesta"].apply(lambda x: f"{x:.3f}")
    p3_disp["Fuerza Morena"]       = p3_disp["Fuerza Morena"].apply(
        lambda x: f"{x*100:.1f}%" if pd.notna(x) else "—")
    p3_disp["Índice Rentabilidad"] = p3_disp["Índice Rentabilidad"].apply(lambda x: f"{x:.3f}")
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
            "#": st.column_config.NumberColumn(width="small"),
            "Sección": st.column_config.NumberColumn(width="small"),
        }
    )
    st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.75rem;'>{len(p3_filt)} secciones mostradas</p>",
                unsafe_allow_html=True)

with tab_ficha:
    sec_lista = p3.sort_values("RANK_ESTRATEGICO")["SECCION"].tolist()
    sec_sel   = st.selectbox(
        "Selecciona una sección",
        options=sec_lista,
        format_func=lambda s: f"Sección {s} — Rank #{int(p3.loc[p3['SECCION']==s,'RANK_ESTRATEGICO'].values[0])}"
    )

    if sec_sel:
        row_sec  = p3[p3["SECCION"]==sec_sel].iloc[0]
        mzas_sec = gdf[gdf["SECCION"]==sec_sel].copy()
        mzas_s1  = mzas_sec[mzas_sec["es_prioritaria_s1"]==True].sort_values("ranking_seccion")
        mzas_hall= mzas_sec[(mzas_sec.get("NIVEL_MZA","") == "MA_ALTA") &
                             (~mzas_sec["es_prioritaria_s1"])] if "NIVEL_MZA" in mzas_sec.columns else pd.DataFrame()

        nucleo   = row_sec["RANK_ESTRATEGICO"] <= 25
        rnk      = int(row_sec["RANK_ESTRATEGICO"])
        etiqueta = "★ NÚCLEO PRIORITARIO" if nucleo else "EXTENSIÓN OPERATIVA"
        col_et   = COLOR_ALTA if nucleo else COLOR_MEDIA

        # Encabezado de ficha
        st.markdown(f"""
        <div style='background:{COLOR_TARJETA};border-left:4px solid {col_et};
                    padding:1rem 1.2rem;border-radius:6px;margin-bottom:1rem;'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                <div>
                    <p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;letter-spacing:0.1em;
                              text-transform:uppercase;margin:0;'>Ficha de sección</p>
                    <h2 style='color:{COLOR_TEXTO};margin:0.2rem 0;font-size:1.6rem;'>
                        Sección {int(sec_sel)}
                    </h2>
                </div>
                <span style='background:{col_et};color:#1a1a1a;padding:4px 12px;
                             border-radius:4px;font-size:0.8rem;font-weight:700;margin-top:4px;'>
                    #{rnk} · {etiqueta}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # KPIs de la sección
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi("Lista Nominal", f"{row_sec.get('LN_TOTAL',0):,.0f}", color=col_et)
        with c2:
            kpi("Prob. encuesta",
                f"{row_sec.get('IRE_SCORE',0):.3f}",
                "En 10 simulaciones aparece este nº de veces", COLOR_MEDIA)
        with c3:
            fm = row_sec.get("fuerza_morena")
            kpi("Fuerza Morena",
                f"{fm*100:.1f}%" if pd.notna(fm) else "—",
                "% del padrón que votó Morena 2024", COLOR_MORENA)
        with c4:
            kpi("Índice Rentabilidad",
                f"{row_sec.get('INDICE_RENTABILIDAD',0):.3f}",
                "Prob. encuesta × Fuerza Morena", col_et)

        st.markdown("<br>", unsafe_allow_html=True)
        col_mzas, col_elect = st.columns([3, 2])

        with col_mzas:
            st.markdown(f"<p style='color:{COLOR_TEXTO};font-size:0.9rem;font-weight:600;margin-bottom:0.4rem;'>Manzanas prioritarias (50% LN)</p>",
                        unsafe_allow_html=True)
            if len(mzas_s1):
                mzas_disp = mzas_s1[["ranking_seccion","LN_estimada",
                                      "fuente_estimacion"]].copy()
                if "IRE_MZA" in mzas_s1.columns:
                    mzas_disp["IRE_MZA"] = mzas_s1["IRE_MZA"]
                mzas_disp.columns = (["Manzana","LN estimada","Fuente","Prob. manzana"]
                                     if "IRE_MZA" in mzas_s1.columns
                                     else ["Manzana","LN estimada","Fuente"])
                mzas_disp["Manzana"]    = mzas_disp["Manzana"].apply(lambda x: f"M{int(x)}")
                mzas_disp["LN estimada"]= mzas_disp["LN estimada"].apply(lambda x: f"{x:,.0f}")
                if "Prob. manzana" in mzas_disp.columns:
                    mzas_disp["Prob. manzana"] = mzas_disp["Prob. manzana"].apply(
                        lambda x: f"{x:.3f}" if pd.notna(x) else "—")
                st.dataframe(mzas_disp, use_container_width=True, hide_index=True, height=280)
                st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;'>LN cubierta total: {mzas_s1['LN_estimada'].sum():,.0f}</p>",
                            unsafe_allow_html=True)
            else:
                st.info("Sin manzanas prioritarias registradas.")

            if len(mzas_hall):
                st.markdown(f"<p style='color:{COLOR_MORENA};font-size:0.82rem;font-weight:600;margin-top:0.8rem;'>★ Manzanas destacadas ({len(mzas_hall)})</p>",
                            unsafe_allow_html=True)
                st.markdown(f"<p style='color:{COLOR_SECUNDARIO};font-size:0.78rem;'>IRE alto fuera del corte de LN — no aparecerían en un ranking estándar.</p>",
                            unsafe_allow_html=True)
                hall_disp = mzas_hall[["ranking_seccion","LN_estimada"]].copy()
                hall_disp.columns = ["Posición en sección","LN estimada"]
                hall_disp["LN estimada"] = hall_disp["LN estimada"].apply(lambda x: f"{x:,.0f}")
                st.dataframe(hall_disp, use_container_width=True, hide_index=True)

        with col_elect:
            st.markdown(f"<p style='color:{COLOR_TEXTO};font-size:0.9rem;font-weight:600;margin-bottom:0.4rem;'>Histórico electoral</p>",
                        unsafe_allow_html=True)

            ganador = row_sec.get("GANADOR_2024","—") or "—"
            margen  = row_sec.get("MARGEN_PCT_2024")
            part    = row_sec.get("PARTICIPACION_2024")

            color_gan = COLOR_MORENA if "MORENA" in str(ganador) else COLOR_MEDIA

            st.markdown(f"""
            <div style='background:{COLOR_TARJETA};border-radius:6px;padding:1.1rem;'>
                <p style='color:{COLOR_SECUNDARIO};font-size:0.78rem;font-weight:600;
                          text-transform:uppercase;letter-spacing:0.08em;margin:0 0 0.8rem;'>
                    Alcaldía 2024
                </p>
                <p style='margin:0 0 0.4rem;'>
                    <span style='color:{COLOR_SECUNDARIO};font-size:0.8rem;'>Ganador: </span>
                    <span style='color:{color_gan};font-weight:600;font-size:0.85rem;'>{ganador}</span>
                </p>
                <p style='margin:0 0 0.4rem;'>
                    <span style='color:{COLOR_SECUNDARIO};font-size:0.8rem;'>Margen: </span>
                    <span style='color:{COLOR_TEXTO};font-size:0.85rem;'>
                        {f"{margen*100:+.1f} pp" if pd.notna(margen) else "—"}
                    </span>
                </p>
                <p style='margin:0 0 1rem;'>
                    <span style='color:{COLOR_SECUNDARIO};font-size:0.8rem;'>Participación: </span>
                    <span style='color:{COLOR_TEXTO};font-size:0.85rem;'>
                        {f"{part*100:.1f}%" if pd.notna(part) else "—"}
                    </span>
                </p>
                <hr style='border:none;border-top:1px solid #3a1010;margin:0.5rem 0;'>
                <p style='color:{COLOR_SECUNDARIO};font-size:0.72rem;margin:0;line-height:1.5;'>
                    La fuerza del bloque en esta sección es del
                    <b style='color:{COLOR_MORENA};'>
                        {f"{fm*100:.1f}%" if pd.notna(fm) else "—"}
                    </b>
                    sobre el padrón total — no sobre los votos emitidos.
                </p>
            </div>
            """, unsafe_allow_html=True)

with tab_descarga:
    st.markdown(f"<h3 style='color:{COLOR_TEXTO};font-size:1.1rem;margin-bottom:1rem;'>Descargas</h3>",
                unsafe_allow_html=True)

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.markdown(f"""
        <div style='background:{COLOR_TARJETA};border-radius:6px;padding:1.2rem;margin-bottom:0.5rem;'>
            <p style='color:{COLOR_TEXTO};font-weight:600;margin:0 0 0.3rem;'>Ranking estratégico</p>
            <p style='color:{COLOR_SECUNDARIO};font-size:0.82rem;margin:0 0 0.8rem;'>
                CSV con las 59 secciones P3_MEDIA ordenadas por índice de rentabilidad.
                Incluye IRE, fuerza Morena, datos electorales 2024.
            </p>
        </div>
        """, unsafe_allow_html=True)

        csv_rank = rank.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇  Descargar ranking CSV",
            data=csv_rank,
            file_name="pie_010_mc_ranking_estrategico.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_d2:
        st.markdown(f"""
        <div style='background:{COLOR_TARJETA};border-radius:6px;padding:1.2rem;margin-bottom:0.5rem;'>
            <p style='color:{COLOR_TEXTO};font-weight:600;margin:0 0 0.3rem;'>Mapas de campo PDF</p>
            <p style='color:{COLOR_SECUNDARIO};font-size:0.82rem;margin:0 0 0.8rem;'>
                59 hojas imprimibles — una por sección. Incluye mapa con calles OSM,
                tabla de manzanas prioritarias y espacio para brigadista.
            </p>
        </div>
        """, unsafe_allow_html=True)

        try:
            with open("assets/pie_010_mc_hojas_campo.pdf", "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="⬇  Descargar mapas PDF",
                data=pdf_bytes,
                file_name="pie_010_mc_hojas_campo.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except FileNotFoundError:
            st.info("El PDF de hojas de campo se agregará próximamente.")

    st.markdown(f"""
    <p style='color:{COLOR_BAJA};font-size:0.72rem;margin-top:1.5rem;'>
        Datos: INE julio 2026 · INEGI Censo 2020 · CONAPO · IECM 2024 ·
        Simulación Monte Carlo 30 diseños × 10,000 iteraciones · Semilla 42
    </p>
    """, unsafe_allow_html=True)