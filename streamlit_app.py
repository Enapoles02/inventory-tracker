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
    padding: 20px 30px; border-radius: 15px; color: white; margin-bottom: 18px;
}

/* Paneles Blancos */
.panel {
    background: #FFFFFF; border-radius: 12px; padding: 18px 20px;
    border: 1px solid #CFD8E3; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
    margin-bottom: 16px;
}

.panel-tight { padding: 14px 16px; }

.hr { height: 1px; background: #E1E8F0; margin: 14px 0; border: none; }

.badge {
    display:inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
    margin: 4px 6px 4px 0;
}

.small-muted { color:#6A7067; font-size:12px; }

.box-title {
    font-size: 16px;
    font-weight: 800;
    color: #002664;
    margin: 0 0 8px 0;
}

/* Sidebar Styling */
[data-testid="stSidebar"] { background-color: #001E4E; }
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] p { color: white !important; }

/* Forzar color azul marino en los tags */
span[data-baseweb="tag"] { background-color: #002664 !important; }
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

# =================================================
# BUILD MASTER DF
# =================================================
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

# Teams sin iniciativas / sin data (fijo, no depende de filtros)
teams_without_ci = [t for t, c in audit_data.items() if len(c) == 0]

# ===== Países con presencia (match por ISO_A3, relleno azul) =====
iso_a3_map = {
    "CANADA": "CAN",
    "USA": "USA",
    "MEXICO": "MEX",
    "CHILE": "CHL",
    "PERU": "PER",
    "PR": "PRI",
}
presence_iso_a3 = sorted({iso_a3_map[c] for c in df_master["Country"].unique() if c in iso_a3_map})
COUNTRIES_GEOJSON_URL = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"

# =================================================
# SIDEBAR - FILTROS
# =================================================
with st.sidebar:
    # Logo DSV arriba del sidebar
    try:
        st.image("assets/dsv_logo.png", use_container_width=True)
    except Exception:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/DSV_logo.svg/512px-DSV_logo.svg.png",
            use_container_width=True
        )

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
# HEADER
# =================================================
st.markdown('<div class="header-bar"><h1>CIQMS | KT Strategic Monitor</h1></div>', unsafe_allow_html=True)

# =================================================
# TOP-LEFT FIXED BOX: Teams without CI initiatives transferred
# =================================================
top_left, _ = st.columns([1, 2.2])
with top_left:
    st.markdown("<div class='panel panel-tight'>", unsafe_allow_html=True)
    st.markdown("<div class='box-title'>Teams without CI initiatives transferred</div>", unsafe_allow_html=True)
    if teams_without_ci:
        for t in teams_without_ci:
            st.markdown(f"<span class='badge' style='background:#FFEBEE; color:#C62828;'>{t}</span>", unsafe_allow_html=True)
    else:
        st.caption("None 🎉")
    st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# MAIN LAYOUT
# =================================================
col_left, col_right = st.columns([1.8, 1])

# =================================================
# LEFT COLUMN
# =================================================
with col_left:
    # --- DONUT ---
    current_data = df_f if sel_focus == "Whole Americas" else df_f[df_f["Country"] == sel_focus]
    avg_progress = int(current_data["Progress"].mean()) if not current_data.empty else 0

    fig = go.Figure(go.Pie(
        values=[avg_progress, 100 - avg_progress],
        hole=0.75,
        marker_colors=["#002664", "#E1E8F0"],
        textinfo="none",
        showlegend=False
    ))
    fig.update_layout(
        annotations=[dict(text=f"{avg_progress}%", x=0.5, y=0.5, font_size=40, showarrow=False, font_color="#002664")],
        margin=dict(t=0, b=0, l=0, r=0),
        height=180,
        paper_bgcolor="rgba(0,0,0,0)"
    )

    st.markdown("<div class='panel' style='text-align:center;'>", unsafe_allow_html=True)
    st.markdown(f"**Readiness Score: {sel_focus}**")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    # --- MAP ---
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    v = view_configs.get(sel_focus, view_configs["Whole Americas"])

    # Países rellenos (sin perímetro azul)
    countries_layer = pdk.Layer(
        "GeoJsonLayer",
        data=COUNTRIES_GEOJSON_URL,
        stroked=False,              # <- QUITAMOS PERÍMETRO
        filled=True,
        extruded=False,
        get_fill_color=[
            "case",
            ["in", ["get", "ISO_A3"], ["literal", presence_iso_a3]],
            0, 38, 100,
            225, 232, 240
        ],
        opacity=0.45,
        pickable=False,
    )

    # Pines por team
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

    # Labels de team
    labels_layer = pdk.Layer(
        "TextLayer",
        data=current_data,
        get_position="[lon, lat]",
        get_text="TeamLabel",
        get_size=14,
        get_color=[0, 30, 80],
        get_text_anchor="'start'",
        get_alignment_baseline="'center'",
        pickable=False,
    )

    st.pydeck_chart(
        pdk.Deck(
            map_style="light",
            initial_view_state=pdk.ViewState(
                latitude=v["lat"],
                longitude=v["lon"],
                zoom=v["zoom"],
                pitch=0,
                transitionDuration=800
            ),
            layers=[countries_layer, pins_layer, labels_layer],
            tooltip={"text": "{Team} in {Country}\nReadiness: {Progress}%\nGaps: {Pending}"}
        ),
        use_container_width=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# RIGHT COLUMN (ADAPTIVE TO FILTERS)
# =================================================
with col_right:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("### 📋 Team Transfer Status")
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    # ✅ Adaptivo a filtros: lista SOLO teams presentes en df_f / current_data
    active_teams = sorted(current_data["Team"].unique()) if current_data is not None and not current_data.empty else []

    # Si focus es "Whole Americas" -> usa df_f
    # Si focus es país -> usa current_data (ya filtrado por país)
    st.markdown("**✅ Active (Filtered View)**")
    if active_teams:
        for team in active_teams:
            st.markdown(
                f"<span class='badge' style='background:#E8F5E9; color:#2E7D32;'>{team}</span>",
                unsafe_allow_html=True
            )
    else:
        st.caption("No teams for selected filters.")

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    # ✅ Critical gaps adaptivo a filtros + focus
    st.markdown("### ⚠️ Critical Gaps (Filtered)")
    if current_data is None or current_data.empty:
        st.caption("No data for selected filters.")
    else:
        tmp = current_data.sort_values("Progress", ascending=True)  # más crítico primero
        any_gap = False
        for _, r in tmp.iterrows():
            if str(r.get("Pending", "")).strip():
                any_gap = True
                st.markdown(f"**{r['Team']} | {r['Country']}**  ·  `{r['Progress']}%`")
                st.caption(f"Gaps: {r['Pending']}")
                st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

        if not any_gap:
            st.caption("No gaps found in this filtered view ✅")

    st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# MATRIX FINAL
# =================================================
st.markdown("<div class='panel'>", unsafe_allow_html=True)
st.markdown("### Strategic Readiness Matrix")
st.dataframe(
    df_f[["Team", "Country", "Progress", "Pending"]].sort_values("Progress", ascending=False),
    use_container_width=True
)
st.markdown("</div>", unsafe_allow_html=True)

st.caption("DSV | CIQMS GBS Mexico – Knowledge Transfer Tracker")
