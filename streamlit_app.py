import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="KT Progress Dashboard", layout="wide")

# --- BASE DE DATOS MAESTRA (EXTRAÍDA DE TUS TABLAS) ---
# Representamos los "YES" como 1 y los "NO" como 0 para calcular el % real
kt_data = {
    "AP": {
        "CANADA": {"Team Huddle": 1, "Ops Calls": 1, "Feedback": 1, "QC": 1, "SharePoint": 0, "Pricing": 0, "MM": 1, "KPIs": 1},
        "CHILE":  {"Team Huddle": 1, "Ops Calls": 0, "Feedback": 1, "QC": 1, "SharePoint": 0, "Pricing": 0, "MM": 1, "KPIs": 1},
        "MEXICO": {"Team Huddle": 0, "Ops Calls": 0, "Feedback": 1, "QC": 0, "SharePoint": 0, "Pricing": 0, "MM": 1, "KPIs": 1},
        "USA":    {"Team Huddle": 1, "Ops Calls": 1, "Feedback": 1, "QC": 1, "SharePoint": 0, "Pricing": 0, "MM": 1, "KPIs": 1},
    },
    "VQH": {
        "CANADA": {"Team Huddle": 1, "Ops Calls": 1, "Incident": 0, "QC": 1, "SharePoint": 0, "Pricing": 0, "MM": 1, "KPIs": 0},
        "USA":    {"Team Huddle": 1, "Ops Calls": 1, "Incident": 0, "QC": 1, "SharePoint": 0, "Pricing": 0, "MM": 1, "KPIs": 0},
    },
    "Verification": {
        "CANADA": {"Team Huddle": 1, "Ops Calls": 1, "Feedback": 1, "QC": 1, "SharePoint": 0, "Pricing": 1, "MM": 1, "KPIs": 1},
        "CHILE":  {"Team Huddle": 1, "Ops Calls": 1, "Feedback": 1, "QC": 1, "SharePoint": 0, "Pricing": 1, "MM": 1, "KPIs": 1},
        "PERU":   {"Team Huddle": 1, "Ops Calls": 1, "Feedback": 1, "QC": 1, "SharePoint": 0, "Pricing": 1, "MM": 1, "KPIs": 1},
        "PR":     {"Team Huddle": 1, "Ops Calls": 1, "Feedback": 1, "QC": 1, "SharePoint": 0, "Pricing": 1, "MM": 1, "KPIs": 1},
        "USA":    {"Team Huddle": 1, "Ops Calls": 1, "Feedback": 1, "QC": 1, "SharePoint": 0, "Pricing": 1, "MM": 1, "KPIs": 1},
    },
    "Cost Match": {
        "USA":    {"Team Huddle": 1, "Ops Calls": 1, "Feedback": 1, "QC": 1, "SharePoint": 0, "Pricing": 0, "MM": 1, "KPIs": 1},
    }
}

# Coordenadas para el mapa
coords = {
    "CANADA": [56.13, -106.34], "USA": [37.09, -95.71], "MEXICO": [23.63, -102.55],
    "CHILE": [-35.67, -71.54], "PERU": [-9.19, -75.01], "PR": [18.22, -66.59]
}

colors = {
    "AP": [0, 0, 255], "VQH": [0, 255, 255], "Verification": [0, 255, 0], "Cost Match": [255, 165, 0]
}

# --- PROCESAMIENTO ---
map_list = []
for equipo, paises in kt_data.items():
    for pais, tareas in paises.items():
        total_tareas = len(tareas)
        completadas = sum(tareas.values())
        progreso = int((completadas / total_tareas) * 100)
        faltantes = [t for t, v in tareas.items() if v == 0]
        
        map_list.append({
            "País": pais, "Equipo": equipo, "Progreso": progreso,
            "lat": coords[pais][0] + (len(map_list) * 0.1), # Offset para que no se encimen
            "lon": coords[pais][1], "color": colors[equipo],
            "Faltante": ", ".join(faltantes)
        })

df = pd.DataFrame(map_list)

# --- UI ---
st.title("📊 KT Progress Interactive Dashboard")

# Filtros
equipo_sel = st.multiselect("Filtrar por Equipo:", options=df["Equipo"].unique(), default=df["Equipo"].unique())
df_filtered = df[df["Equipo"].isin(equipo_sel)]

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Mapa de Implementación")
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(latitude=15, longitude=-80, zoom=2),
        layers=[pdk.Layer(
            "ScatterplotLayer", df_filtered, get_position='[lon, lat]',
            get_color='color', get_radius=250000, pickable=True, opacity=0.7
        )],
        tooltip={"text": "{Equipo} en {País}\nProgreso: {Progreso}%\nFalta: {Faltante}"}
    ))

with col2:
    st.subheader("Análisis de Brechas")
    for _, row in df_filtered.iterrows():
        with st.expander(f"{row['Equipo']} - {row['País']} ({row['Progreso']}%)"):
            st.write(f"⚠️ **Pendiente:** {row['Faltante']}")
            st.progress(row['Progreso'] / 100)

st.divider()
st.subheader("Tabla Maestra de Control")
st.table(df[["Equipo", "País", "Progreso", "Faltante"]])

# Equipos en gris
st.info("Equipos sin actividad (Gris): Intercompany, Claims, Cash Management.")
