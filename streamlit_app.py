import streamlit as st
import pandas as pd
import pydeck as pdk
import math

# Configuración de alto nivel
st.set_page_config(
    page_title="DSV | Knowledge Transfer Strategic Monitor",
    page_icon="🌍",
    layout="wide"
)

# --- ESTILO CORPORATIVO DSV AVANZADO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #F4F7F9; }
    
    /* Header DSV */
    .header-container {
        background-color: #002664;
        padding: 30px;
        border-radius: 10px;
        color: white;
        margin-bottom: 25px;
    }
    
    /* Tarjetas de Métricas Premium */
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #E1E4E8;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATOS ESTRUCTURADOS ---
tasks = ["Team Huddle", "Operational Calls", "Feedback Tool", "QC", "SharePoint/Catalogue", "Unit Pricing", "MM", "KPIs"]

audit_data = {
    "AP": {
        "CANADA": [1,1,1,1,0,0,1,1], "CHILE": [1,0,1,1,0,0,1,1], 
        "MEXICO": [0,0,1,0,0,0,1,1], "USA": [1,1,1,1,0,0,1,1]
    },
    "VQH": {
        "CANADA": [1,1,0,1,0,0,1,0], "USA": [1,1,0,1,0,0,1,0]
    },
    "Verification": {
        "CANADA": [1,1,1,1,0,1,1,1], "CHILE": [1,1,1,1,0,1,1,1], 
        "PERU": [1,1,1,1,0,1,1,1], "PR": [1,1,1,1,0,1,1,1], "USA": [1,1,1,1,0,1,1,1]
    },
    "Cost Match": { "USA": [1,1,1,1,0,0,1,1] }
}

geo_coords = {
    "CANADA": [56.1, -106.3], "USA": [37.1, -95.7], "MEXICO": [23.6, -102.5],
    "CHILE": [-35.7, -71.5], "PERU": [-9.2, -75.0], "PR": [18.2, -66.6]
}

# Paleta DSV (Azul Profundo a Azul Eléctrico)
dsv_palette = {
    "AP": [0, 38, 100],        
    "VQH": [40, 80, 140],      
    "Verification": [0, 102, 179], 
    "Cost Match": [115, 154, 188]  
}

# --- LÓGICA DE SEPARACIÓN DE PUNTOS (SPREAD) ---
rows = []
for pais, coords in geo_coords.items():
    # Encontrar qué equipos están en este país
    equipos_en_pais = [eq for eq in audit_data if pais in audit_data[eq]]
    n = len(equipos_en_pais)
    
    for i, eq in enumerate(equipos_en_pais):
        val = audit_data[eq][pais]
        prog = int((sum(val)/len(val))*100)
        missing = [tasks[j] for j, v in enumerate(val) if v == 0]
        
        # Algoritmo de dispersión circular (offset) para que no se encimen
        # Radio de dispersión ajustado para visibilidad
        radius = 1.8 
        angle = (2 * math.pi * i) / n if n > 1 else 0
        
        jitter_lat = coords[0] + (radius * math.cos(angle) if n > 1 else 0)
        jitter_lon = coords[1] + (radius * math.sin(angle) if n > 1 else 0)
        
        rows.append({
            "Team": eq, "Country": pais, "Progress": prog,
            "lat": jitter_lat, "lon": jitter_lon,
            "color": dsv_palette[eq],
            "Pending": ", ".join(missing) if missing else "None (100% Ready)"
        })

df = pd.DataFrame(rows)

# --- UI HEADER ---
st.markdown("""
    <div class="header-container">
        <h1 style='margin:0; font-size: 2.5rem;'>Knowledge Transfer Strategic Monitor</h1>
        <p style='margin:0; opacity:0.8; font-size: 1.1rem;'>Operational Readiness | Americas Region | Audit 2026</p>
    </div>
    """, unsafe_allow_html=True)

# Métricas Principales
m1, m2, m3, m4 = st.columns(4)
m1.metric("Average Readiness", f"{int(df['Progress'].mean())}%")
m2.metric("Teams in Deployment", len(df['Team'].unique()))
m3.metric("Critical Pending", "SharePoint")
m4.metric("Status", "On Track")

st.write("")

# --- MAPA Y AUDITORÍA ---
col_map, col_audit = st.columns([1.6, 1])

with col_map:
    # Estilo de mapa 'Dark' o 'Light' de Carto para mayor contraste
    view_state = pdk.ViewState(latitude=15, longitude=-85, zoom=2.8, pitch=0)
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        df,
        get_position='[lon, lat]',
        get_color='color',
        get_radius=180000,
        pickable=True,
        opacity=0.9,
        stroked=True,
        line_width_min_pixels=2,
        get_line_color=[255, 255, 255]
    )

    st.pydeck_chart(pdk.Deck(
        map_style='https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
        initial_view_state=view_state,
        layers=[layer],
        tooltip={"text": "Team: {Team}\nCountry: {Country}\nProgress: {Progress}%\nMissing: {Pending}"}
    ))

with col_audit:
    st.subheader("Regional Deep-Dive")
    selected_c = st.selectbox("Filter by Country:", sorted(df["Country"].unique()))
    
    c_df = df[df["Country"] == selected_c]
    for _, row in c_df.iterrows():
        with st.expander(f"📍 {row['Team']} - {row['Progress']}% Complete"):
            st.progress(row['Progress']/100)
            st.markdown(f"**Gaps:** {row['Pending']}")

# --- TABLA DE CONTROL ---
st.divider()
st.dataframe(
    df[["Team", "Country", "Progress", "Pending"]],
    use_container_width=True,
    column_config={
        "Progress": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)
    }
)
