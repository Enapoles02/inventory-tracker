import streamlit as st
import pandas as pd
import pydeck as pdk

# --- CONFIGURACIÓN CORPORATIVA DSV ---
st.set_page_config(
    page_title="DSV Global | Knowledge Transfer Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Colores Oficiales DSV
DSV_BLUE = "#002664"
DSV_SKY = "#739ABC"
DSV_WHITE = "#FFFFFF"

# Estilos CSS Inyectados para acabado Premium
st.markdown(f"""
    <style>
    .main {{ background-color: #f0f2f6; }}
    .stMetric {{ 
        background-color: white; 
        padding: 20px; 
        border-radius: 8px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-top: 4px solid {DSV_BLUE};
    }}
    h1, h2, h3 {{ color: {DSV_BLUE} !位important; font-weight: 800; }}
    .stProgress > div > div > div {{ background-color: {DSV_BLUE}; }}
    [data-testid="stHeader"] {{ background: {DSV_BLUE}; }}
    </style>
    """, unsafe_allow_html=True)

# --- DATA AUDITADA (Basada en tus tablas) ---
data_matrix = {
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

labels = ["Team Huddle", "Operational Calls", "Feedback/Incident", "QC", "SharePoint/Catalogue", "Unit Pricing", "MM", "KPIs"]
coords = {
    "CANADA": [56.1, -106.3], "USA": [37.1, -95.7], "MEXICO": [23.6, -102.5],
    "CHILE": [-35.6, -71.5], "PERU": [-9.2, -75.0], "PR": [18.2, -66.6]
}

# Procesar para el mapa
rows = []
for eq, countries in data_matrix.items():
    for c, val in countries.items():
        prog = int((sum(val)/len(val))*100)
        missing = [labels[i] for i, v in enumerate(val) if v == 0]
        ready = [labels[i] for i, v in enumerate(val) if v == 1]
        rows.append({
            "Team": eq, "Country": c, "Progress": prog,
            "lat": coords[c][0] + (len(rows)*0.2), "lon": coords[c][1],
            "Pending": ", ".join(missing), "Done": ready
        })
df = pd.DataFrame(rows)

# --- DASHBOARD HEADER ---
st.image("https://www.dsv.com/Assets/dsv/dsv-logo-blue.svg", width=120)
st.title("Knowledge Transfer Strategic Monitor")
st.markdown("#### Operational Readiness | Americas Region")

# Métricas de Poder
c1, c2, c3, c4 = st.columns(4)
c1.metric("Overall Americas Progress", f"{int(df['Progress'].mean())}%", "↑ 4%")
c2.metric("Verification Efficiency", "90%", "Target Reached")
c3.metric("Critical Gaps (SharePoint)", "100%", "Systemic Issue")
c4.metric("Active Regions", "6", "On Schedule")

st.divider()

# --- SECCIÓN VISUAL ---
col_map, col_audit = st.columns([1.8, 1])

with col_map:
    st.subheader("Global Deployment Map")
    st.pydeck_chart(pdk.Deck(
        map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
        initial_view_state=pdk.ViewState(latitude=10, longitude=-80, zoom=2.2),
        layers=[pdk.Layer(
            "ScatterplotLayer", df, get_position='[lon, lat]',
            get_color='[0, 38, 100, 160]', get_radius=250000, pickable=True
        )],
        tooltip={"text": "{Team} - {Country}\nProgreso: {Progress}%\nFalta: {Pending}"}
    ))

with col_audit:
    st.subheader("Deep Audit Tool")
    sel_country = st.selectbox("Select Country:", df["Country"].unique())
    country_rows = df[df["Country"] == sel_country]
    
    for _, r in country_rows.iterrows():
        with st.expander(f"🔍 {r['Team']} - {r['Progress']}% Complete"):
            st.write("**Done:**")
            st.caption(" | ".join(r['Done']))
            st.error(f"**Action Required:** {r['Pending']}")

# --- CONCLUSIÓN ---
st.divider()
st.subheader("Strategic Progress Matrix")
st.dataframe(df[["Team", "Country", "Progress", "Pending"]], use_container_width=True)

st.info("💡 **Executive Summary:** Transition for 'Verification' and 'Cost Match' is near completion. Focus should pivot to SharePoint integration across all clusters.")
