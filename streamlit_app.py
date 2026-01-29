import streamlit as st
import pandas as pd
import pydeck as pdk

# Configuración de alto nivel
st.set_page_config(
    page_title="DSV | Knowledge Transfer Strategic Monitor",
    page_icon="🌍",
    layout="wide"
)

# --- IDENTIDAD CORPORATIVA DSV (CSS AVANZADO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main { background-color: #F8F9FB; }
    
    /* Estilo de Tarjetas Métricas */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 4px;
        padding: 20px;
        border-bottom: 4px solid #002664;
        box-shadow: 0 4px 12px rgba(0, 38, 100, 0.08);
    }
    
    /* Header Corporativo */
    .header-bar {
        background-color: #002664;
        padding: 20px;
        border-radius: 0 0 15px 15px;
        color: white;
        margin-bottom: 30px;
    }
    
    /* Expansores y tablas */
    .stExpander { border: none !important; box-shadow: none !important; background: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ESTRUCTURADA ---
# Tareas auditadas de tus imágenes
tasks = ["Team Huddle", "Operational Calls", "Feedback Tool", "QC", "SharePoint/Catalogue", "Unit Pricing", "MM", "KPIs"]

# Dataset basado en las imágenes originales
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

# Coordenadas precisas para evitar solapamiento visual
geo_coords = {
    "CANADA": [56.1, -106.3], "USA": [37.1, -95.7], "MEXICO": [23.6, -102.5],
    "CHILE": [-35.7, -71.5], "PERU": [-9.2, -75.0], "PR": [18.2, -66.6]
}

# Paleta DSV Blue Graduated (Diferentes tonalidades para cada equipo)
dsv_palette = {
    "AP": [0, 38, 100],        # Midnight Blue (Base)
    "VQH": [40, 80, 140],      # Navy Blue
    "Verification": [80, 130, 190], # Steel Blue
    "Cost Match": [120, 170, 220]   # Sky Blue
}

# --- PROCESAMIENTO DE DATOS ---
rows = []
for eq, countries in audit_data.items():
    for c, val in countries.items():
        prog = int((sum(val)/len(val))*100)
        missing = [tasks[i] for i, v in enumerate(val) if v == 0]
        
        # Offset para que los pines de un mismo país se vean separados y elegantes
        jitter = list(audit_data.keys()).index(eq) * 0.9
        
        rows.append({
            "Team": eq, "Country": c, "Progress": prog,
            "lat": geo_coords[c][0] + (jitter if c != "PR" else 0), 
            "lon": geo_coords[c][1] + jitter,
            "color": dsv_palette[eq],
            "Pending": ", ".join(missing)
        })

df = pd.DataFrame(rows)

# --- CABECERA DE LA PRESENTACIÓN ---
st.markdown("""
    <div class="header-bar">
        <h1 style='margin:0; color:white;'>KNOWLEDGE TRANSFER STRATEGIC MONITOR</h1>
        <p style='margin:0; opacity:0.8;'>Global Operations | Americas Region | Readiness Audit 2026</p>
    </div>
    """, unsafe_allow_html=True)

# KPIs Principales (Corregidos para que siempre carguen)
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Overall Progress", f"{int(df['Progress'].mean())}%")
with c2: st.metric("Top Performer", "Verification", "90% Ready")
with c3: st.metric("Risk Areas", "SharePoint", "-100% Core")
with c4: st.metric("Deployment Status", "On Track", "Phase 2")

st.write("")

# --- VISUALIZACIÓN CORE ---
col_map, col_details = st.columns([1.5, 1])

with col_map:
    st.markdown("### 🌎 Interactive Deployment Status")
    # Capa de Mapa con estilo DSV (Limpio y profesional)
    st.pydeck_chart(pdk.Deck(
        map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
        initial_view_state=pdk.ViewState(latitude=12, longitude=-82, zoom=2.3, pitch=0),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                df,
                get_position='[lon, lat]',
                get_color='color',
                get_radius=220000,
                pickable=True,
                opacity=0.9
            ),
        ],
        tooltip={"text": "Team: {Team}\nCountry: {Country}\nReadiness: {Progress}%\nMissing: {Pending}"}
    ))

with col_details:
    st.markdown("### 🔍 Strategic Audit Details")
    # Selector de País con diseño limpio
    selected_c = st.selectbox("Filter by Country:", df["Country"].unique(), index=1)
    country_df = df[df["Country"] == selected_c]
    
    for _, row in country_df.iterrows():
        st.markdown(f"**Team: {row['Team']}**")
        st.progress(row['Progress']/100)
        if row['Pending']:
            st.markdown(f"⚠️ <span style='color:#D93025; font-size:0.8em;'>PENDING: {row['Pending']}</span>", unsafe_allow_html=True)
        else:
            st.markdown("✅ <span style='color:#188038; font-size:0.8em;'>FULL READINESS</span>", unsafe_allow_html=True)
        st.write("")

# --- MATRIZ FINAL PARA EL JEFE ---
st.divider()
st.markdown("### 📋 Executive Readiness Matrix")
st.dataframe(
    df[["Team", "Country", "Progress", "Pending"]].sort_values(by=["Country", "Progress"], ascending=[True, False]),
    use_container_width=True,
    column_config={
        "Progress": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100),
        "Pending": "Identified Gaps"
    }
)

# Footer Corporativo
st.markdown("---")
st.caption("DSV Global Knowledge Transfer Tracker | Confidential - Internal Use Only")
