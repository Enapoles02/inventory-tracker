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
    padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700;
    margin: 3px;
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

view_configs = {
    "Whole Americas": [15, -85, 2.2],
    "CANADA": [56.1, -106.3, 3.5],
    "USA": [37.1, -95.7, 4.0],
    "MEXICO": [23.6, -102.5, 5.0],
    "CHILE": [-35.7, -71.5, 4.2],
    "PERU": [-9.2, -75.0, 5.2],
    "PR": [18.2, -66.6, 7.5],
}

team_colors = {
    "AP": [0, 80, 180], "VQH": [50, 80, 200], "Verification": [18, 99, 56],
    "Cost Match": [0, 38, 100], "Claims": [180, 0, 0], 
    "Intercompany": [180, 0, 0], "Cash Management": [180, 0, 0]
}

# Procesar filas maestras
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
# SIDEBAR - FILTROS DINÁMICOS
# =================================================
with st.sidebar:
    st.markdown("### 🛠 Control Panel")
    all_teams_list = sorted(list(audit_data.keys()))
    selected_teams = st.multiselect("Teams", options=all_teams_list, default=all_teams_list)
    
    # Países válidos según equipos seleccionados
    valid_countries = sorted(df_master[df_master["Team"].isin(selected_teams)]["Country"].unique())
    selected_countries = st.multiselect("Countries", options=valid_countries, default=valid_countries)

    # Lógica de Map Focus Adaptable
    # Si solo hay un país en la selección, forzamos el focus a ese país
    if len(selected_countries) == 1:
        auto_focus = selected_countries[0]
    else:
        auto_focus = "Whole Americas"

    st.markdown("---")
    sel_focus = st.selectbox("🌍 Map Focus", ["Whole Americas"] + selected_countries, index=0 if len(selected_countries) != 1 else 1)

df_f = df_master[df_master["Team"].isin(selected_teams) & df_master["Country"].isin(selected_countries)]

# =================================================
# MAIN VIEW
# =================================================
st.markdown('<div class="header-bar"><h1>CIQMS | KT Strategic Monitor</h1></div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1.7, 1])

with col_left:
    # --- ROSCA DE COMPLETITUD ---
    current_view_data = df_f if sel_focus == "Whole Americas" else df_f[df_f["Country"] == sel_focus]
    avg_progress = int(current_view_data["Progress"].mean()) if not current_view_data.empty else 0
    
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

    # --- MAPA (PINES VISIBLES) ---
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    coords = view_configs.get(sel_focus, view_configs["Whole Americas"])

    st.pydeck_chart(pdk.Deck(
        map_style="light",
        initial_view_state=pdk.ViewState(latitude=coords[0], longitude=coords[1], zoom=coords[2], pitch=0, transitionDuration=1000),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=current_view_data,
                get_position="[lon, lat]",
                get_fill_color="color",
                get_radius=200000 if sel_focus == "Whole Americas" else 60000,
                pickable=True,
                opacity=0.9,
                stroked=True,
                get_line_color=[255, 255, 255],
                line_width_min_pixels=2,
            )
        ],
        tooltip={"text": "{Team} in {Country}\nReadiness: {Progress}%"}
    ), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    # --- EL CUADRO DE LA DERECHA (INTERACTIVO) ---
    st.markdown("<div class='panel' style='height: 825px; overflow-y: auto;'>", unsafe_allow_html=True)
    st.markdown("### 📋 Team Transfer Status")
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    
    # Estatus dinámico basado en filtro de Sidebar
    transferred_in_filter = [t for t in selected_teams if len(audit_data.get(t, {})) > 0]
    pending_in_filter = [t for t in selected_teams if len(audit_data.get(t, {})) == 0]

    st.markdown("**✅ Active in GBS Mexico**")
    if not transferred_in_filter: st.caption("No active teams selected.")
    for t in transferred_teams:
        if t in selected_teams:
            st.markdown(f"<span class='transfer-badge' style='background:#E8F5E9; color:#2E7D32;'>{t}</span>", unsafe_allow_html=True)
    
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown("**⏳ Pending / Outside Scope**")
    for t in pending_teams:
        if t in selected_teams:
            st.markdown(f"<span class='transfer-badge' style='background:#FFEBEE; color:#C62828;'>{t}</span>", unsafe_allow_html=True)
    
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown("### ⚠️ Gap Analysis")
    
    # Gaps específicos de la selección actual
    gaps_display = current_view_data[current_view_data["Pending"] != ""]
    if gaps_display.empty:
        st.success("All selected items are 100% ready.")
    else:
        for _, r in gaps_display.sort_values("Progress", ascending=False).iterrows():
            st.markdown(f"**{r['Team']} | {r['Country']}**")
            st.progress(r["Progress"]/100)
            st.caption(f"⚠️ Missing: {r['Pending']}")
            st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
            
    st.markdown("</div>", unsafe_allow_html=True)

# MATRIX INFERIOR
st.markdown("<div class='panel'>", unsafe_allow_html=True)
st.markdown("### Strategic Readiness Matrix")
st.dataframe(df_f[["Team", "Country", "Progress", "Pending"]].sort_values("Progress", ascending=False), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
st.caption("DSV | CIQMS GBS Mexico – KT Strategic Monitor")
