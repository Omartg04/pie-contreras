"""
app_utils.py — PIE · Plataforma de Inteligencia Electoral
Utilidades compartidas: paleta, estilos, autenticación, helpers de datos.
"""
import streamlit as st
import pandas as pd
import geopandas as gpd
from datetime import date

# ── Paleta de color ───────────────────────────────────────────────────────────
COLOR_ALTA      = "#e8a33d"   # ámbar — zona alta prioridad
COLOR_MEDIA     = "#5b7a9e"   # acero — zona media
COLOR_BAJA      = "#2e3a52"   # acero oscuro — zona referencia
COLOR_MORENA    = "#b5451b"   # terracota — fuerza Morena / hallazgo
COLOR_POSITIVO  = "#3f7a52"   # verde — datos positivos
COLOR_FONDO     = "#1a1a2e"   # fondo principal
COLOR_TARJETA   = "#16213e"   # fondo de tarjetas
COLOR_TEXTO     = "#e0e0e0"   # texto principal
COLOR_SECUNDARIO= "#a0a8b8"   # texto secundario

# Colores por nivel operativo (lenguaje cliente)
COLOR_NIVEL = {
    "P1_CERTEZA": COLOR_ALTA,
    "P2_ALTA":    COLOR_ALTA,
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

# ── Identidad del proyecto ────────────────────────────────────────────────────
PROYECTO = {
    "nombre":    "PIE — Plataforma de Inteligencia Electoral",
    "modulo":    "Módulo de Priorización Territorial",
    "subtitulo": "Interna Morena 2026",
    "municipio": "La Magdalena Contreras",
    "vigencia":  date(2027, 2, 12),
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
        <p style='color:{COLOR_SECUNDARIO}; font-size:0.85rem; letter-spacing:0.15em;
                  text-transform:uppercase; margin-bottom:0.5rem;'>
            PLATAFORMA DE INTELIGENCIA ELECTORAL
        </p>
        <h1 style='color:{COLOR_TEXTO}; font-family:Georgia, serif;
                   font-size:2rem; font-weight:400; margin:0 0 0.3rem;'>
            La Magdalena Contreras
        </h1>
        <p style='color:{COLOR_ALTA}; font-size:0.9rem; margin-bottom:2.5rem;'>
            Interna Morena 2026
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
        Plataforma vigente hasta {PROYECTO["vigencia"].strftime("%d de %B de %Y")}
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

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        background-color: {COLOR_FONDO};
        color: {COLOR_TEXTO};
    }}
    h1, h2, h3 {{
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 600;
        letter-spacing: 0.02em;
    }}
    .stButton > button {{
        background-color: {COLOR_ALTA};
        color: #1a1a1a;
        border: none;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }}
    .stButton > button:hover {{
        background-color: #d4923a;
        color: #1a1a1a;
    }}
    .stSelectbox > div, .stMultiSelect > div {{
        background-color: {COLOR_TARJETA};
    }}
    div[data-testid="stSidebar"] {{
        background-color: {COLOR_TARJETA};
        border-right: 1px solid #2a3550;
    }}
    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }}
    footer {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# ── Componente KPI ────────────────────────────────────────────────────────────
def kpi(label, valor, delta="", color=None):
    color = color or COLOR_ALTA
    delta_html = f"<p style='color:{color};font-size:0.75rem;margin:4px 0 0;'>{delta}</p>" if delta else ""
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
                PIE · {PROYECTO["municipio"]} · Interna Morena 2026
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
            <p style='color:{COLOR_ALTA}; font-size:0.72rem; margin:0;'>
                {max(dias,0)} días restantes
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<hr style='border:none;border-top:1px solid #2a3550;margin:0.5rem 0 1rem;'>",
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

# ── Color por IRE continuo (gradiente acero → ámbar) ────────────────────────
def color_ire(valor, vmin=0.0, vmax=1.0):
    """Interpola entre COLOR_MEDIA y COLOR_ALTA según el IRE."""
    if valor is None or pd.isna(valor):
        return "#2e3a52"
    t = max(0.0, min(1.0, (valor - vmin) / (vmax - vmin + 1e-9)))
    # acero (#5b7a9e) → ámbar (#e8a33d)
    r = int(0x5b + t*(0xe8 - 0x5b))
    g = int(0x7a + t*(0xa3 - 0x7a))
    b = int(0x9e + t*(0x3d - 0x9e))
    return f"#{r:02x}{g:02x}{b:02x}"

# ── Badge de nivel ────────────────────────────────────────────────────────────
def badge_nivel(nivel):
    col = COLOR_NIVEL.get(nivel, COLOR_BAJA)
    label = NIVEL_LABEL.get(nivel, nivel)
    return f"<span style='background:{col};color:#1a1a1a;padding:2px 8px;border-radius:3px;font-size:0.75rem;font-weight:600;'>{label}</span>"

# ── Determinar si sección es núcleo ──────────────────────────────────────────
def es_nucleo(rank_estrategico):
    return rank_estrategico is not None and rank_estrategico <= 25
