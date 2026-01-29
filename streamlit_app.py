import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.graph_objects as go

# =================================================
# CONFIG
# =================================================
st.set_page_config(
    page_title="DSV | KT Strategic Monitor",
    page_icon="🌍",
    layout="wide"
)

# =================================================
# CORPORATE CSS (DSV)
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

/* Paneles Blancos Estilo Dashboard */
.panel {
    background: #FFFFFF; border-radius: 12px; padding: 20px;
    border: 1px solid #CFD8E3; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
    margin-bottom: 20px;
}

[data-testid="stSidebar"] { background-color: #001E4E; }
[data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label { color: white !important; }
span[data-baseweb="tag"] { background-color: #002664 !important; }

.hr { height: 1px; background: #E1E8F0; margin: 15px 0; border: none; }

.transfer-badge {
    display: inline-block;
    padding: 6px 12px; border-radius: 8px; font-size: 13px; font-weight: 700;
    margin: 4px;
}
</style>
""", unsafe_allow_html=True)

# =================================================
# DATA (Info previa restaurada)
# =================================================
tasks = ["Team Huddle", "Operational Calls", "Feedback Tool", "QC", "SharePoint/Catalogue", "Unit Pricing", "MM", "KPIs"]

audit_data = {
    "AP": {
        "CANADA": [1,1,1,1,0,0,1,1], "CHILE": [1,0,1,1,0,0,1,1],
        "MEXICO": [0,0,1,0,0,0,1,1], "USA": [1,1,1,1,0,0,1,1],
    },
    "VQH": {
        "CANADA": [1,1,0,1,0,0,1,0], "USA": [1,1,0,1,0,0,1,0],
    },
    "Verification": {
        "CANADA": [1,1,1,1,0,1,1,1], "CHILE": [1,1,1,1,0,1,1,1],
        "PERU": [1,1,1,1,0,1,1,1], "PR": [1,1,1,1,0,1,1,1], "USA": [1,1,1,1,0,1,1,1],
    },
    "Cost Match": { "USA": [1,1,1,1,0,0,1,1] },
    "Claims": {}, "Intercompany": {}, "Cash Management": {},
}

geo_coords = {
    "CANADA": [56.1, -106.3], "USA": [37.1, -95.7], "MEXICO": [23.6, -102.5],
    "CHILE": [-35.7, -71.5], "PERU": [-9.2, -75.0], "PR": [18.2, -66.6],
}

team_colors = {
    "AP": [0, 80, 180], "VQH": [50, 80, 200], "Verification": [18, 99, 56],
    "Cost Match": [0, 38, 100], "Claims": [180, 0, 0], 
    "Intercompany": [180, 0, 0], "Cash Management": [180, 0, 0]
}

# Procesar estatus de transferencia
transferred_teams = [t for t, c in audit_data.items() if len(c) > 0]
pending_teams = [t for t, c in audit_data.items() if len(c) == 0]

# Procesar filas para el mapa
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
    all_teams = sorted(df_master["Team"].unique())
    selected_teams = st.multiselect("Teams", options=all_teams, default=all_teams)
    
    # Filtro dinámico: solo muestra países con los equipos seleccionados
    valid_countries = sorted(df_master[df_master["Team"].isin(selected_teams)]["Country"].unique())
    selected_countries = st.multiselect("Countries", options=valid_countries, default=valid_countries)

    st.markdown("---")
    map_focus_opts = ["Whole Americas"] + selected_countries
    sel_focus = st.selectbox("🌍 Map Focus", map_focus_opts)

df_f = df_master[df_master["Team"].isin(selected_teams) & df_master["Country"].isin(selected_countries)]

# =================================================
# MAIN VIEW
# =================================================
st.markdown('<div class="header-bar"><h1>CIQMS | KT Strategic Monitor</h1></div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1.6, 1])

with col_left:
    # --- GRÁFICO DE ROSCA ---
    current_data = df_f if sel_focus == "Whole Americas" else df_f[df_f["Country"] == sel_focus]
    avg_progress = int(current_data["Progress"].mean()) if not current_data.empty else 0
    
    fig = go.Figure(go.Pie(
        values=[avg_progress, 100 - avg_progress], hole=0.75,
        marker_colors=["#002664", "#E1E8F0"], textinfo='none', showlegend=False
    ))
    fig.update_layout(
        annotations=[dict(text=f'{avg_progress}%', x=0.5, y=0.5, font_size=40, showarrow=False, font_color="#002664")],
        margin=dict(t=0, b=0, l=0, r=0), height=180, paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.markdown("<div class='panel' style='text-align: center;'>", unsafe_allow_html=True)
    st.markdown(f"**Readiness Score: {sel_focus}**")
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)

    # --- MAPA (PINES GRANDES Y VISIBLES) ---
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    
    v_map = {"Whole Americas": [15, -85, 2.2], "MEXICO": [23, -102, 5], "CANADA": [56, -106, 3.5], "USA": [37, -95, 4], "CHILE": [-35, -71, 4.5], "PERU": [-9, -75, 5.5], "PR": [18, -66, 8]}
    focus_coords = v_map.get(sel_focus, v_map["Whole Americas"])

    st.pydeck_chart(pdk.Deck(
        map_style="light",
        initial_view_state=pdk.ViewState(latitude=focus_coords[0], longitude=focus_coords[1], zoom=focus_coords[2], pitch=0),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=current_data,
                get_position="[lon, lat]",
                get_fill_color="color",
                get_radius=220000 if sel_focus == "Whole Americas" else 50000,
                pickable=True,
                opacity=0.9,
                stroked=True,
                get_line_color=[255, 255, 255],
                line_width_min_pixels=2,
            )
        ],
        tooltip={"text": "Team: {Team}\nCountry: {Country}\nProgress: {Progress}%"}
    ), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    # --- EL CUADRO DE LA DERECHA: INFO ESTRATÉGICA ---
    st.markdown("<div class='panel' style='height: 820px; overflow-y: auto;'>", unsafe_allow_html=True)
    st.markdown("### 📋 Team Transfer Status")
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    
    st.markdown("**✅ Transferred (Active in GBS)**")
    for t in transferred_teams:
        st.markdown(f"<span class='transfer-badge' style='background:#E8F5E9; color:#2E7D32;'>{t}</span>", unsafe_allow_html=True)
    
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown("**⏳ Pending (NA / Nothing)**")
    for t in pending_teams:
        st.markdown(f"<span class='transfer-badge' style='background:#FFEBEE; color:#C62828;'>{t}</span>", unsafe_allow_html=True)
    
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown("### ⚠️ Country Gaps Analysis")
    st.markdown("<div class='small-muted'>Gaps identified in current focus selection:</div>", unsafe_allow_html=True)
    
    # Mostrar Gaps del país o selección actual
    gaps_found = current_data[current_data["Pending"] != ""]
    if gaps_found.empty:
        st.success("No gaps identified for this selection.")
    else:
        for _, r in gaps_found.sort_values("Progress", ascending=False).iterrows():
            st.markdown(f"**{r['Team']} | {r['Country']}**")
            st.progress(r["Progress"]/100)
            st.caption(f"⚠️ Missing: {r['Pending']}")
            st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
            
    st.markdown("</div>", unsafe_allow_html=True)

# MATRIX INFERIOR
st.markdown("<div class='panel'>", unsafe_allow_html=True)
st.markdown("### Executive Matrix")
st.dataframe(df_f[["Team", "Country", "Progress", "Pending"]].sort_values("Progress", ascending=False), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
st.caption("DSV | CIQMS GBS Mexico – KT Strategic Tracker")
