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
# CORPORATE CSS (DSV) - AZUL MARINO & ELEGANCIA
# =================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #EBF0F5; }

/* Header Azul Marino Profundo */
.header-bar {
    background: linear-gradient(135deg, #001E4E 0%, #002664 100%);
    padding: 20px 30px; border-radius: 15px; color: white; margin-bottom: 25px;
}

/* Paneles Blancos */
.panel {
    background: #FFFFFF; border-radius: 12px; padding: 20px;
    border: 1px solid #CFD8E3; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
    margin-bottom: 20px;
}

/* Sidebar Styling */
[data-testid="stSidebar"] { background-color: #001E4E; }
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] p { color: white !important; }

/* Forzar color azul marino en los tags */
span[data-baseweb="tag"] { background-color: #002664 !important; }

.metric-inline { font-size: 22px; font-weight: 800; color: #002664; }
.hr { height: 1px; background: #E1E8F0; margin: 15px 0; border: none; }

.transfer-badge {
    display:inline-block;
    padding: 6px 10px; border-radius: 999px;
    font-size: 12px; font-weight: 800;
    margin: 4px 6px 4px 0;
}
.small-muted { color:#6A7067; font-size:12px; }
</style>
""", unsafe_allow_html=True)

# =================================================
# DATA
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
    "Whole Americas": {"lat": 12, "lon": -85, "zoom": 2.2},
    "CANADA": {"lat": 56.1, "lon": -106.3, "zoom": 3.5},
    "USA": {"lat": 37.1, "lon": -95.7, "zoom": 3.8},
    "MEXICO": {"lat": 23.6, "lon": -102.5, "zoom": 5.0},
    "CHILE": {"lat": -35.7, "lon": -71.5, "zoom": 4.2},
    "PERU": {"lat": -9.2, "lon": -75.0, "zoom": 5.2},
    "PR": {"lat": 18.2, "lon": -66.6, "zoom": 7.5},
}

team_colors = {
    "AP": [0, 80, 180],
    "VQH": [50, 80, 200],
    "Verification": [18, 99, 56],
    "Cost Match": [0, 38, 100],
    "Claims": [180, 0, 0],
    "Intercompany": [180, 0, 0],
    "Cash Management": [180, 0, 0]
}

# Procesar filas para el mapa y estatus
rows = []
for team, countries in audit_data.items():
    if not countries:
        continue
    for country, vals in countries.items():
        prog = int(round((sum(vals) / len(vals)) * 100))
        pending_list = [tasks[i] for i, v in enumerate(vals) if v == 0]
        rows.append({
            "Team": team,
            "Country": country,
            "Progress": prog,
            "lat": geo_coords[country][0],
            "lon": geo_coords[country][1],
            "color": team_colors.get(team, [0, 38, 100]),
            "Pending": ", ".join(pending_list),
            "TeamLabel": team
        })

df_master = pd.DataFrame(rows)

transferred_teams = [t for t, c in audit_data.items() if len(c) > 0]
pending_teams = [t for t, c in audit_data.items() if len(c) == 0]

# Para relleno de países (GeoJSON usa nombres “humanos”)
geo_name_map = {
    "CANADA": "Canada",
    "USA": "United States of America",
    "MEXICO": "Mexico",
    "CHILE": "Chile",
    "PERU": "Peru",
    # "PR": (Puerto Rico no siempre viene como país independiente en geojson estándar)
}
presence_countries_iso = sorted(df_master["Country"].unique())
presence_countries_geo = [geo_name_map[c] for c in presence_countries_iso if c in geo_name_map]

# Fuente pública GeoJSON países (Natural Earth)
COUNTRIES_GEOJSON_URL = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"

# =================================================
# SIDEBAR - FILTROS
# =================================================
with st.sidebar:
    # Logo DSV arriba del sidebar
    try:
        st.image("assets/dsv_logo.png", use_container_width=True)
    except Exception:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/DSV_logo.svg/512px-DSV_logo.svg.png",
                 use_container_width=True)

    st.markdown("### 🛠 Control Panel")

    all_teams = sorted(df_master["Team"].unique())
    selected_teams = st.multiselect("Teams", options=all_teams, default=all_teams)

    valid_countries = sorted(df_master[df_master["Team"].isin(selected_teams)]["Country"].unique())
    selected_countries = st.multiselect("Countries", options=valid_countries, default=valid_countries)

    st.markdown("---")
    map_focus_opts = ["Whole Americas"] + selected_countries
    sel_focus = st.selectbox("🌍 Map Focus", map_focus_opts)

df_f = df_master[
    df_master["Team"].isin(selected_teams) &
    df_master["Country"].isin(selected_countries)
]

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
        annotations=[dict(text=f'{avg_progress}%', x=0.5, y=0.5, font_size=40, showarrow=False, font_color="#002664")],
        margin=dict(t=0, b=0, l=0, r=0), height=180, paper_bgcolor='rgba(0,0,0,0)'
    )

    st.markdown("<div class='panel' style='text-align:center;'>", unsafe_allow_html=True)
    st.markdown(f"**Readiness Score: {sel_focus}**")
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)

    # --- MAPA: Países rellenos + pines por equipo + label ---
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    v = view_configs.get(sel_focus, view_configs["Whole Americas"])

    # GeoJsonLayer para pintar países donde hay presencia (azul DSV)
    # Nota: esto pinta “toda la presencia” (no solo el filtro actual) para cumplir tu requerimiento.
    countries_layer = pdk.Layer(
        "GeoJsonLayer",
        data=COUNTRIES_GEOJSON_URL,
        opacity=0.20,
        stroked=True,
        filled=True,
        extruded=False,
        get_line_color=[0, 38, 100],
        get_line_width=1,
        line_width_min_pixels=1,
        get_fill_color=[
            "case",
            ["in", ["get", "ADMIN"], ["literal", presence_countries_geo]],
            0, 38, 100,  # azul (relleno)
            225, 232, 240  # gris claro (resto)
        ],
        pickable=False,
    )

    # Pines por team (círculos)
    pins_layer = pdk.Layer(
        "ScatterplotLayer",
        data=current_data,
        get_position="[lon, lat]",
        get_fill_color="color",
        get_radius=180000,
        pickable=True,
        opacity=0.85,
        stroked=True,
        get_line_color=[255, 255, 255],
        line_width_min_pixels=2,
    )

    # Etiqueta del team junto al pin
    labels_layer = pdk.Layer(
        "TextLayer",
        data=current_data,
        get_position="[lon, lat]",
        get_text="TeamLabel",
        get_size=14,
        get_color=[0, 30, 80],
        get_angle=0,
        get_text_anchor="'start'",
        get_alignment_baseline="'center'",
        pickable=False,
    )

    st.pydeck_chart(
        pdk.Deck(
            map_style="light",
            initial_view_state=pdk.ViewState(
                latitude=v["lat"], longitude=v["lon"], zoom=v["zoom"], pitch=0, transitionDuration=800
            ),
            layers=[countries_layer, pins_layer, labels_layer],
            tooltip={"text": "{Team} in {Country}\nReadiness: {Progress}%\nGaps: {Pending}"}
        ),
        use_container_width=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    # =================================================
    # PANEL DERECHO (SIN HTML “abierto” entre componentes)
    # -> construimos TODO el HTML en un string y lo pintamos 1 vez
    # =================================================
    # Transfer badges
    transferred_html = ""
    for team in transferred_teams:
        transferred_html += f"<span class='transfer-badge' style='background:#E8F5E9; color:#2E7D32;'>{team}</span>"

    pending_html = ""
    for team in pending_teams:
        pending_html += f"<span class='transfer-badge' style='background:#FFEBEE; color:#C62828;'>{team}</span>"

    # Critical gaps (orden asc para ver lo crítico primero)
    gaps_html = ""
    if current_data is not None and not current_data.empty:
        tmp = current_data.sort_values("Progress", ascending=True)
        for _, r in tmp.iterrows():
            if str(r.get("Pending", "")).strip():
                gaps_html += f"""
                <div style="margin-bottom:10px;">
                    <div style="font-weight:800; color:#002664;">{r['Team']} | {r['Country']} <span class="small-muted">({r['Progress']}%)</span></div>
                    <div class="small-muted"><b>Gaps:</b> {r['Pending']}</div>
                </div>
                """
    else:
        gaps_html = "<div class='small-muted'>No data for selected filters.</div>"

    right_panel_html = f"""
    <div class="panel" style="height: 835px; overflow-y:auto;">
        <h3 style="margin-top:0;">📋 Team Transfer Status</h3>
        <div class="hr"></div>

        <div style="font-weight:800;">✅ Transferred (In Scope)</div>
        <div style="margin-top:8px;">{transferred_html}</div>

        <div class="hr"></div>
        <div style="font-weight:800;">⏳ Pending (NA/Nothing)</div>
        <div style="margin-top:8px;">{pending_html}</div>

        <div class="hr"></div>
        <h3 style="margin-bottom:6px;">⚠️ Critical Gaps</h3>
        {gaps_html}
    </div>
    """

    st.markdown(right_panel_html, unsafe_allow_html=True)

# MATRIX FINAL
st.markdown("<div class='panel'>", unsafe_allow_html=True)
st.markdown("### Strategic Readiness Matrix")
st.dataframe(
    df_f[["Team", "Country", "Progress", "Pending"]].sort_values("Progress", ascending=False),
    use_container_width=True
)
st.markdown("</div>", unsafe_allow_html=True)
st.caption("DSV | CIQMS GBS Mexico – Knowledge Transfer Tracker")
