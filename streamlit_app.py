import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.graph_objects as go

# =================================================
# CONFIG
# =================================================
st.set_page_config(
    page_title="CIQMS | GBS Mexico – KT Strategic Monitor",
    page_icon="🌍",
    layout="wide"
)

# =================================================
# CORPORATE CSS
# =================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #EBF0F5; }
.header-bar {
    background: linear-gradient(135deg, #001E4E 0%, #002664 100%);
    padding: 20px 30px; border-radius: 15px; color: white; margin-bottom: 25px;
}
.panel {
    background: #FFFFFF; border-radius: 12px; padding: 20px;
    border: 1px solid #CFD8E3; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
    margin-bottom: 20px;
}
[data-testid="stSidebar"] { background-color: #001E4E; }
[data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label { color: white !important; }
span[data-baseweb="tag"] { background-color: #002664 !important; }
.hr { height: 1px; background: #E1E8F0; margin: 15px 0; border: none; }
</style>
""", unsafe_allow_html=True)

# =================================================
# DATA
# =================================================
tasks = ["Team Huddle", "Operational Calls", "Feedback Tool", "QC", "SharePoint/Catalogue", "Unit Pricing", "MM", "KPIs"]

audit_data = {
    "AP": {"CANADA": [1,1,1,1,0,0,1,1], "CHILE": [1,0,1,1,0,0,1,1], "MEXICO": [0,0,1,0,0,0,1,1], "USA": [1,1,1,1,0,0,1,1]},
    "VQH": {"CANADA": [1,1,0,1,0,0,1,0], "USA": [1,1,0,1,0,0,1,0]},
    "Verification": {"CANADA": [1,1,1,1,0,1,1,1], "CHILE": [1,1,1,1,0,1,1,1], "PERU": [1,1,1,1,0,1,1,1], "PR": [1,1,1,1,0,1,1,1], "USA": [1,1,1,1,0,1,1,1]},
    "Cost Match": {"USA": [1,1,1,1,0,0,1,1]},
    "Claims": {}, "Intercompany": {}, "Cash Management": {},
}

geo_coords = {
    "CANADA": [56.1, -106.3], "USA": [37.1, -95.7], "MEXICO": [23.6, -102.5],
    "CHILE": [-35.7, -71.5], "PERU": [-9.2, -75.0], "PR": [18.2, -66.6],
}

team_colors = {
    "AP": [0, 80, 180], "VQH": [0, 50, 140], "Verification": [0, 110, 220],
    "Cost Match": [0, 30, 90], "Claims": [10, 40, 100], 
    "Intercompany": [20, 60, 120], "Cash Management": [0, 20, 60]
}

# Consolidar DataFrame base
rows = []
for team, countries in audit_data.items():
    if not countries: continue
    for country, vals in countries.items():
        prog = int(round((sum(vals) / len(vals)) * 100))
        rows.append({
            "Team": team, "Country": country, "Progress": prog,
            "lat": geo_coords[country][0], "lon": geo_coords[country][1],
            "color": team_colors.get(team, [0, 38, 100]),
            "Pending": ", ".join([tasks[i] for i, v in enumerate(vals) if v == 0])
        })
df_master = pd.DataFrame(rows)

# =================================================
# SIDEBAR - FILTROS CONDICIONALES
# =================================================
with st.sidebar:
    st.markdown("### 🛠 Control Panel")
    
    # Lógica de Filtros Cruzados
    all_teams = sorted(df_master["Team"].unique())
    all_countries = sorted(df_master["Country"].unique())

    # Inicializar selectores en session_state si no existen
    if 'f_teams' not in st.session_state: st.session_state.f_teams = all_teams
    if 'f_countries' not in st.session_state: st.session_state.f_countries = all_countries

    # 1. Filtro de Equipos
    selected_teams = st.multiselect("Teams", options=all_teams, default=all_teams)
    
    # 2. Determinar países válidos para esos equipos
    valid_countries = sorted(df_master[df_master["Team"].isin(selected_teams)]["Country"].unique())
    
    # 3. Filtro de Países (solo muestra los válidos)
    selected_countries = st.multiselect("Countries", options=valid_countries, default=valid_countries)

    st.markdown("---")
    # 4. Map Focus (condicionado a los países seleccionados)
    map_focus_opts = ["Whole Americas"] + selected_countries
    sel_focus = st.selectbox("🌍 Map Focus", map_focus_opts)

# Filtrado Final del Dataframe
df_f = df_master[df_master["Team"].isin(selected_teams) & df_master["Country"].isin(selected_countries)]

# =================================================
# MAIN VIEW
# =================================================
st.markdown('<div class="header-bar"><h1>CIQMS | KT Strategic Monitor</h1></div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1.8, 1])

with col_left:
    # --- GRÁFICO DE ROSCA ---
    current_data = df_f if sel_focus == "Whole Americas" else df_f[df_f["Country"] == sel_focus]
    avg_progress = int(current_data["Progress"].mean()) if not current_data.empty else 0
    
    fig = go.Figure(go.Pie(
        values=[avg_progress, 100 - avg_progress], hole=0.75,
        marker_colors=["#002664", "#E1E8F0"], textinfo='none', showlegend=False
    ))
    fig.update_layout(
        annotations=[dict(text=f'{avg_progress}%', x=0.5, y=0.5, font_size=45, showarrow=False, font_color="#002664")],
        margin=dict(t=0, b=0, l=0, r=0), height=180, paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.markdown("<div class='panel' style='text-align: center;'>", unsafe_allow_html=True)
    st.markdown(f"**Readiness Score: {sel_focus}**")
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)

    # --- MAPA ---
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    
    # View State dinámico
    view_states = {
        "Whole Americas": {"lat": 10, "lon": -85, "zoom": 2.2},
        "MEXICO": {"lat": 23.6, "lon": -102.5, "zoom": 5},
        "CANADA": {"lat": 56.1, "lon": -106.3, "zoom": 3.5},
        "USA": {"lat": 37.1, "lon": -95.7, "zoom": 4},
        "CHILE": {"lat": -35.7, "lon": -71.5, "zoom": 4.5},
        "PERU": {"lat": -9.2, "lon": -75.0, "zoom": 5.5},
        "PR": {"lat": 18.2, "lon": -66.6, "zoom": 8}
    }
    v = view_states.get(sel_focus, view_states["Whole Americas"])

    # Capa de etiquetas (TextLayer mejorada)
    text_layer = pdk.Layer(
        "TextLayer",
        data=current_data,
        get_position="[lon, lat]",
        get_text="Team",
        get_color="color",
        get_size=20,
        size_units="pixels",
        get_alignment_baseline="'center'",
        background_color=[255, 255, 255, 200],
        padding=[6, 6]
    )

    # Usar un estilo que no requiera Mapbox Token
    st.pydeck_chart(pdk.Deck(
        map_style="light", # Estilo nativo de Pydeck (no falla)
        initial_view_state=pdk.ViewState(
            latitude=v["lat"], longitude=v["lon"], 
            zoom=v["zoom"], pitch=30, transitionDuration=1000
        ),
        layers=[text_layer],
        tooltip={"text": "{Team} in {Country}\nProgress: {Progress}%"}
    ), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown("<div class='panel' style='height: 830px; overflow-y: auto;'>", unsafe_allow_html=True)
    st.markdown("### Country Analysis")
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    
    for _, r in current_data.sort_values("Progress", ascending=False).iterrows():
        st.markdown(f"**{r['Team']}** | {r['Country']}")
        st.progress(r["Progress"]/100)
        st.caption(f"Progress: {r['Progress']}%")
        if r['Pending']: st.caption(f"Gaps: {r['Pending']}")
        st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# MATRIX
st.markdown("<div class='panel'>", unsafe_allow_html=True)
st.markdown("### Strategic Readiness Matrix")
st.dataframe(df_f[["Team", "Country", "Progress", "Pending"]].sort_values("Progress", ascending=False), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
