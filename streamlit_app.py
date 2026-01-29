import streamlit as st
import pandas as pd
import pydeck as pdk

# =================================================
# CONFIG
# =================================================
st.set_page_config(
    page_title="CIQMS | GBS Mexico – KT Strategic Monitor",
    page_icon="🌍",
    layout="wide"
)

# =================================================
# CORPORATE CSS (DSV / CIQMS)
# =================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background-color: #F4F6FA; }

/* Header */
.header-bar {
    background: linear-gradient(90deg, #002664 0%, #0B3C91 100%);
    padding: 22px 24px 18px 24px;
    border-radius: 14px;
    color: white;
    margin-bottom: 18px;
    box-shadow: 0 10px 24px rgba(0, 38, 100, 0.18);
}
.header-title { margin:0; font-size: 30px; font-weight: 800; letter-spacing: 0.2px; }
.header-sub { margin:6px 0 0 0; opacity:0.88; font-size: 13px; }

/* Panels */
.panel {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 14px 16px;
    border: 1px solid #E8ECF5;
    box-shadow: 0 8px 20px rgba(16, 24, 40, 0.06);
}
.panel-title {
    display:flex; align-items:center; justify-content:space-between;
    margin: 2px 0 10px 0;
}
.badge {
    display:inline-block;
    padding: 5px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
    border: 1px solid #E6EAF2;
    background: #F6F8FC;
    color: #1f2a44;
}
.metric-inline {
    font-size: 18px;
    font-weight: 800;
    color: #002664;
    background: #E8F0FF;
    padding: 4px 12px;
    border-radius: 8px;
}
.small-muted { color:#5c677d; font-size: 12px; }

/* Metric cards */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 18px 18px 14px 18px;
    border: 1px solid #E8ECF5;
    box-shadow: 0 8px 20px rgba(16, 24, 40, 0.06);
}
[data-testid="stMetricLabel"] { color: #1f2a44; font-weight: 800; }
[data-testid="stMetricValue"] { color: #002664; font-weight: 900; }

.hr { height: 1px; background: #EEF2F9; margin: 12px 0; border: none; }

/* Legend dots */
.legend-item { display:flex; align-items:center; gap:10px; margin: 7px 0; }
.dot { width: 10px; height: 10px; border-radius: 50%; display:inline-block; }
.team-tag {
    display:inline-block;
    padding: 4px 8px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 800;
    background: #F5F7FB;
    border: 1px solid #E8ECF5;
    color: #1f2a44;
}
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
    "Claims": {},
    "Intercompany": {},
    "Cash Management": {},
}

geo_coords = {
    "CANADA": [56.1, -106.3], "USA": [37.1, -95.7], "MEXICO": [23.6, -102.5],
    "CHILE": [-35.7, -71.5], "PERU": [-9.2, -75.0], "PR": [18.2, -66.6],
}

# Configuración de vistas centradas en AMÉRICA
view_configs = {
    "Default": {"lat": 10, "lon": -80, "zoom": 2.0, "pitch": 0}, # Foco en el continente
    "CANADA": {"lat": 56.1, "lon": -106.3, "zoom": 3.2, "pitch": 35},
    "USA": {"lat": 37.1, "lon": -95.7, "zoom": 3.5, "pitch": 35},
    "MEXICO": {"lat": 23.6, "lon": -102.5, "zoom": 4.8, "pitch": 40},
    "CHILE": {"lat": -35.7, "lon": -71.5, "zoom": 4.0, "pitch": 35},
    "PERU": {"lat": -9.2, "lon": -75.0, "zoom": 5.0, "pitch": 35},
    "PR": {"lat": 18.2, "lon": -66.6, "zoom": 7.0, "pitch": 35},
}

# CAMBIO A AZULES MARINOS (Gama DSV)
team_colors = {
    "AP": [0, 102, 204],         # azul brillante
    "VQH": [50, 80, 200],        # azul medio
    "Verification": [0, 153, 102], # verde (mantenido por contraste)
    "Cost Match": [0, 38, 100],  # Azul Marino Core
    "Claims": [0, 25, 70],       # Azul Marino Profundo
    "Intercompany": [10, 45, 110], # Azul Marino Real
    "Cash Management": [5, 30, 85] # Azul Marino Oscuro
}

team_short = {"AP": "AP", "VQH": "VQH", "Verification": "VER", "Cost Match": "CM", "Claims": "CLM", "Intercompany": "IC", "Cash Management": "CASH"}

# =================================================
# BUILD DATASET
# =================================================
rows = []
for team, countries in audit_data.items():
    if not countries: continue
    for country, vals in countries.items():
        prog = int(round((sum(vals) / len(vals)) * 100))
        missing = [tasks[i] for i, v in enumerate(vals) if v == 0]
        rows.append({
            "Team": team, "TeamShort": team_short.get(team, team[:3].upper()),
            "Country": country, "Progress": prog, "Pending": ", ".join(missing),
            "base_lat": geo_coords[country][0], "base_lon": geo_coords[country][1],
            "color": team_colors.get(team, [0,38,100]),
        })

df = pd.DataFrame(rows)
if not df.empty:
    df = df.sort_values(["Country", "Team"]).reset_index(drop=True)
    lat_list, lon_list = [], []
    offset_pattern = [(-2.0, -1.0), (0.0, -1.0), (2.0, -1.0), (-2.0, 1.0), (0.0, 1.0), (2.0, 1.0), (0.0, 0.0)]
    for country, group in df.groupby("Country", sort=False):
        for i in range(len(group)):
            dy, dx = offset_pattern[i % len(offset_pattern)]
            lat_list.append(group["base_lat"].iloc[0] + dy)
            lon_list.append(group["base_lon"].iloc[0] + dx)
    df["lat"], df["lon"] = lat_list, lon_list

# =================================================
# INTERFACE
# =================================================
st.markdown('<div class="header-bar"><div class="header-title">CIQMS | KT Strategic Monitor</div><div class="header-sub">Americas Regional Tracking</div></div>', unsafe_allow_html=True)

# FILTROS SUPERIORES
f1, f2, f3 = st.columns([1, 1, 2])
with f1: team_filter = st.multiselect("Teams", options=sorted(df["Team"].unique()), default=sorted(df["Team"].unique()))
with f2: country_filter = st.multiselect("Countries", options=sorted(df["Country"].unique()), default=sorted(df["Country"].unique()))

df_f = df[df["Team"].isin(team_filter) & df["Country"].isin(country_filter)] if not df.empty else df

# =================================================
# MAP + DRILLDOWN
# =================================================
col_map, col_details = st.columns([1.8, 1.0])

with col_details:
    st.markdown("<div class='panel'><div class='panel-title'><span class='badge'>Country Drilldown</span></div><div class='hr'></div>", unsafe_allow_html=True)
    country_opts = ["Show All"] + sorted(df_f["Country"].unique().tolist())
    selection = st.selectbox("Select Country Focus", country_opts)
    selected_country = selection if selection != "Show All" else "Default"
    
    view_data = df_f if selection == "Show All" else df_f[df_f["Country"] == selection]
    for _, r in view_data.sort_values("Progress", ascending=False).iterrows():
        st.markdown(f"**{r['Team']}** | {r['Country']}")
        st.progress(r["Progress"] / 100)
        st.markdown(f"<span class='small-muted'>Readiness: {r['Progress']}%</span>", unsafe_allow_html=True)
        if r["Pending"]: st.caption(f"⚠️ Gaps: {r['Pending']}")
        st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_map:
    # CÁLCULO DE READINESS QUE REACCIONA AL SELECTOR
    current_readiness = int(view_data["Progress"].mean()) if not view_data.empty else 0
    
    st.markdown(f"""
    <div class='panel'>
        <div class='panel-title'>
            <span class='badge'>Americas Deployment Plan</span>
            <div><span class='small-muted'>Focus Readiness:</span> <span class='metric-inline'>{current_readiness}%</span></div>
        </div>
        <div class='hr'></div>
    """, unsafe_allow_html=True)

    # Configuración de mapa
    map_display_data = df_f if selected_country == "Default" else df_f[df_f["Country"] == selected_country]
    v = view_configs[selected_country]

    deck = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=v["lat"], longitude=v["lon"], zoom=v["zoom"], 
            pitch=v["pitch"], transitionDuration=800
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer", data=map_display_data, get_position="[lon, lat]",
                get_fill_color="color", get_radius=150000, pickable=True, opacity=0.9,
                stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=1,
            ),
            pdk.Layer(
                "TextLayer", data=map_display_data, get_position="[lon, lat]",
                get_text="TeamShort", get_size=12, get_color=[255, 255, 255],
            )
        ],
        tooltip={"text": "{Team}\n{Country}\nReadiness: {Progress}%"}
    )
    st.pydeck_chart(deck, use_container_width=True)

    # Leyenda Compacta
    st.markdown("**Team Palette**")
    lcols = st.columns(4)
    for i, (t, rgb) in enumerate(team_colors.items()):
        lcols[i % 4].markdown(f"<div style='font-size:10px'><span style='height:8px;width:8px;background:rgb({rgb[0]},{rgb[1]},{rgb[2]});display:inline-block;border-radius:50%'></span> {t}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# MATRIX FINAL
st.markdown("<div class='panel'><div class='panel-title'><span class='badge'>Executive Matrix</span></div><div class='hr'></div>", unsafe_allow_html=True)
st.dataframe(df_f[["Team", "Country", "Progress", "Pending"]].sort_values("Progress", ascending=False), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
