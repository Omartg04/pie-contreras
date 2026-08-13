"""
app_utils.py — PIE · Plataforma de Inteligencia Electoral
Utilidades compartidas: paleta, estilos, autenticación, helpers de datos.
"""
import streamlit as st
import pandas as pd
import geopandas as gpd
from datetime import date

# ── Paleta de color — Identidad oficial Morena ────────────────────────────────
COLOR_ALTA      = "#6A1B29"   # guinda Morena — prioridad alta, bordes card
COLOR_ACENTO    = "#E6D194"   # dorado claro — labels de acento sobre fondo oscuro
COLOR_MEDIA     = "#A57F2C"   # dorado oscuro — prioridad media
COLOR_BAJA      = "#555555"   # gris neutro — zona referencia
COLOR_MORENA    = "#6A1B29"   # alias de COLOR_ALTA
COLOR_POSITIVO  = "#3f7a52"   # verde — datos positivos
COLOR_FONDO     = "#0f0608"   # negro-vino — fondo principal
COLOR_TARJETA   = "#1a0a0d"   # vino muy oscuro — fondo de tarjetas
COLOR_TEXTO     = "#FFFFFF"   # blanco puro — máximo contraste
COLOR_SECUNDARIO= "#C8C0C0"   # gris claro — texto secundario

# Colores por nivel operativo (lenguaje cliente)
COLOR_NIVEL = {
    "P1_CERTEZA": COLOR_ACENTO,
    "P2_ALTA":    COLOR_ACENTO,
    "P3_MEDIA":   COLOR_MEDIA,
    "P4_BAJA":    COLOR_BAJA,
}

# Traducción de niveles a lenguaje cliente
NIVEL_LABEL = {
    "P1_CERTEZA": "Certeza de encuesta",
    "P2_ALTA":    "Alta probabilidad",
    "P3_MEDIA":   "Probabilidad media",
    "P4_BAJA":    "Zona de referencia",
}

# ── Meses en español ─────────────────────────────────────────────────────────
MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

def fecha_es(d):
    """Devuelve fecha en español: '12 de noviembre de 2026'."""
    return f"{d.day} de {MESES_ES[d.month]} de {d.year}"

# ── Identidad del proyecto ────────────────────────────────────────────────────
PROYECTO = {
    "nombre":    "PIE — Plataforma de Inteligencia Electoral",
    "modulo":    "Módulo de Priorización Territorial",
    "subtitulo": "Bernardo Aguilar 2027",
    "municipio": "La Magdalena Contreras",
    "vigencia":  date(2026, 11, 12),
    "lat_centro": 19.298,
    "lon_centro": -99.268,
    "zoom":      13,
}

# ── Autenticación ─────────────────────────────────────────────────────────────
def verificar_acceso():
    """
    Muestra pantalla de login y bloquea el acceso si no se autentifica.
    Devuelve True si el usuario está autenticado.
    """
    if st.session_state.get("autenticado"):
        return True

    st.markdown(f"""
    <div style='text-align:center; padding: 3rem 1rem 1rem;'>
        <p style='color:{COLOR_ACENTO}; font-size:0.82rem; letter-spacing:0.2em;
                  text-transform:uppercase; margin-bottom:0.5rem; font-weight:600;'>
            PLATAFORMA DE INTELIGENCIA ELECTORAL
        </p>
        <h1 style='color:#FFFFFF !important; font-family:Georgia, serif;
                   font-size:2.2rem; font-weight:700; margin:0 0 0.3rem;
                   text-shadow: 0 1px 4px rgba(0,0,0,0.5);'>
            La Magdalena Contreras
        </h1>
        <p style='color:{COLOR_ACENTO}; font-size:1rem; margin-bottom:2.5rem;
                  font-weight:600; letter-spacing:0.05em;'>
            Bernardo Aguilar 2027
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        usuario = st.text_input("Usuario", placeholder="usuario")
        clave   = st.text_input("Contraseña", type="password", placeholder="••••••••")
        entrar  = st.button("Entrar", use_container_width=True, type="primary")

        if entrar:
            usuarios = st.secrets.get("auth", {})
            if usuario in usuarios and usuarios[usuario] == clave:
                st.session_state["autenticado"] = True
                st.session_state["usuario"]     = usuario
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

    dias_restantes = (PROYECTO["vigencia"] - date.today()).days
    st.markdown(f"""
    <p style='text-align:center; color:{COLOR_SECUNDARIO}; font-size:0.75rem; margin-top:2rem;'>
        Plataforma vigente hasta {fecha_es(PROYECTO["vigencia"])}
        · {max(dias_restantes,0)} días restantes
    </p>
    """, unsafe_allow_html=True)

    return False

def cerrar_sesion():
    st.session_state["autenticado"] = False
    st.session_state["usuario"]     = ""
    st.rerun()

# ── Estilos globales ──────────────────────────────────────────────────────────
def aplicar_estilos():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Barlow+Condensed:wght@400;600;700&display=swap');

    /* ── Fondo global — capturar todos los niveles de Streamlit ── */
    .stApp, .stApp > div, .stApp > div > div,
    html, body,
    .main, .main > div,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > div,
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {{
        background-color: {COLOR_FONDO} !important;
    }}

    /* ── Tipografía global ── */
    html, body, [class*="css"], p, span, label, div {{
        font-family: 'Inter', sans-serif !important;
        color: {COLOR_TEXTO};
    }}

    /* ── Headings ── */
    h1, h2, h3, h4, h5, h6,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {{
        font-family: 'Barlow Condensed', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        color: {COLOR_TEXTO} !important;
    }}

    /* ── Botones ── */
    .stButton > button {{
        background-color: {COLOR_ALTA} !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }}
    .stButton > button:hover {{
        background-color: #531521 !important;
        color: #FFFFFF !important;
    }}

    /* ── Inputs ── */
    .stTextInput > div > div > input {{
        background-color: #2a0a0d !important;
        color: {COLOR_TEXTO} !important;
        border: 1px solid #3a1010 !important;
    }}

    /* ── Selectbox / multiselect ── */
    .stSelectbox > div, .stMultiSelect > div {{
        background-color: {COLOR_TARJETA} !important;
    }}

    /* ── Sidebar ── */
    div[data-testid="stSidebar"],
    div[data-testid="stSidebar"] > div {{
        background-color: {COLOR_TARJETA} !important;
        border-right: 1px solid #3a1010 !important;
    }}

    /* ── Tablas ── */
    [data-testid="stDataFrame"] {{
        background-color: {COLOR_TARJETA} !important;
    }}

    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }}
    footer {{ visibility: hidden; }}
    /* Ocultar navegación automática de Streamlit (visible en login) */
    [data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# ── Componente KPI ────────────────────────────────────────────────────────────
def kpi(label, valor, delta="", color=None):
    color = color or COLOR_ACENTO
    # Delta siempre en dorado — garantiza contraste sobre fondo oscuro
    delta_html = f"<p style='color:{COLOR_ACENTO};font-size:0.75rem;margin:4px 0 0;'>{delta}</p>" if delta else ""
    st.markdown(f"""
    <div style='background:{COLOR_TARJETA}; border-left:4px solid {color};
                padding:1rem 1.2rem; border-radius:6px; margin-bottom:0.5rem;'>
        <p style='color:{COLOR_SECUNDARIO}; font-size:0.78rem; margin:0 0 4px;
                  text-transform:uppercase; letter-spacing:0.08em;'>
            {label}
        </p>
        <p style='color:{COLOR_TEXTO}; font-family:"Barlow Condensed",sans-serif;
                  font-size:2rem; margin:0; font-weight:700; line-height:1.1;'>
            {valor}
        </p>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

# ── Header de página ──────────────────────────────────────────────────────────
def header(titulo, subtitulo=""):
    dias = (PROYECTO["vigencia"] - date.today()).days
    usuario = st.session_state.get("usuario","")

    col_t, col_u = st.columns([5,1])
    with col_t:
        st.markdown(f"""
        <div style='margin-bottom:0.5rem;'>
            <p style='color:{COLOR_SECUNDARIO}; font-size:0.72rem; letter-spacing:0.12em;
                      text-transform:uppercase; margin:0;'>
                PIE · {PROYECTO["municipio"]} · Bernardo Aguilar 2027
            </p>
            <h1 style='color:{COLOR_TEXTO}; margin:0.1rem 0 0; font-size:1.7rem;'>
                {titulo}
            </h1>
            {'<p style="color:'+COLOR_SECUNDARIO+'; font-size:0.85rem; margin:0.2rem 0 0;">'+subtitulo+'</p>' if subtitulo else ""}
        </div>
        """, unsafe_allow_html=True)
    with col_u:
        st.markdown(f"""
        <div style='text-align:right; padding-top:0.5rem;'>
            <p style='color:{COLOR_SECUNDARIO}; font-size:0.72rem; margin:0;'>{usuario}</p>
            <p style='color:{COLOR_ACENTO}; font-size:0.72rem; margin:0;'>
                {max(dias,0)} días restantes
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<hr style='border:none;border-top:1px solid #3a1010;margin:0.5rem 0 1rem;'>",
                unsafe_allow_html=True)

# ── Carga de datos con caché ───────────────────────────────────────────────────
@st.cache_data
def cargar_unificado():
    gdf = gpd.read_file("data/pie_010_mc_unificado.geojson")
    return gdf

@st.cache_data
def cargar_secciones():
    gdf = gpd.read_file("data/pie_010_mc_secciones.geojson")
    return gdf

@st.cache_data
def cargar_ranking():
    df = pd.read_csv("data/pie_010_mc_ranking.csv",
                     dtype={"CVE_MUN": str} if "CVE_MUN" in pd.read_csv(
                         "data/pie_010_mc_ranking.csv", nrows=0).columns else {})
    return df

# ── Color por IRE continuo (gradiente gris claro → guinda Morena) ────────────
def color_ire(valor, vmin=0.0, vmax=1.0):
    """Interpola entre gris claro y guinda Morena según el IRE.
    Diseñado para mapas con fondo CartoDB positron (claro).
    """
    if valor is None or pd.isna(valor):
        return "#cccccc"
    t = max(0.0, min(1.0, (valor - vmin) / (vmax - vmin + 1e-9)))
    # gris claro (#cccccc) → guinda Morena (#6A1B29)
    r = int(0xcc + t*(0x6A - 0xcc))
    g = int(0xcc + t*(0x1B - 0xcc))
    b = int(0xcc + t*(0x29 - 0xcc))
    return f"#{r:02x}{g:02x}{b:02x}"

# ── Badge de nivel ────────────────────────────────────────────────────────────
def badge_nivel(nivel):
    col = COLOR_NIVEL.get(nivel, COLOR_BAJA)
    label = NIVEL_LABEL.get(nivel, nivel)
    return f"<span style='background:{col};color:#1a0a0d;padding:2px 8px;border-radius:3px;font-size:0.75rem;font-weight:600;'>{label}</span>"

# ── Determinar si sección es núcleo ──────────────────────────────────────────
def es_nucleo(rank_estrategico):
    return rank_estrategico is not None and rank_estrategico <= 25