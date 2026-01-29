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

/* Divider line */
.hr {
    height: 1px;
    background: #EEF2F9;
    margin: 12px 0;
    border: none;
}

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
# DATA (from your images / definitions)
# =================================================
tasks = ["Team Huddle", "Operational Calls", "Feedback Tool", "QC", "SharePoint/Catalogue", "Unit Pricing", "MM", "KPIs"]

# 1 = YES (Transferred & executed)
# 0 = NO (In country visible, not yet transferred/executed)
audit_data = {
    "AP": {
        "CANADA": [1,1,1,1,0,0,1,1],
        "CHILE":  [1,0,1,1,0,0,1,1],
        "MEXICO": [0,0,1,0,0,0,1,1],
        "USA":    [1,1,1,1,0,0,1,1],
    },
    "VQH": {
        "CANADA": [1,1,0,1,0,0,1,0],
        "USA":    [1,1,0,1,0,0,1,0],
    },
    "Verification": {
        "CANADA": [1,1,1,1,0,1,1,1],
        "CHILE":  [1,1,1,1,0,1,1,1],
        "PERU":   [1,1,1,1,0,1,1,1],
        "PR":     [1,1,1,1,0,1,1,1],
        "USA":    [1,1,1,1,0,1,1,1],
    },
    "Cost Match": {
        "USA": [1,1,1,1,0,0,1,1],
    },
    # Pending transfer (NA / NOTHING in your tracker)
    "Claims": {},
    "Intercompany": {},
    "Cash Management": {},
}

# Country centroids (good enough; we place pins INSIDE each country using offsets)
geo_coords = {
    "CANADA": [56.1, -106.3],
    "USA": [37.1, -95.7],
    "MEXICO": [23.6, -102.5],
    "CHILE": [-35.7, -71.5],
    "PERU": [-9.2, -75.0],
    "PR": [18.2, -66.6],
}

# Corporate-distinct palette (easy to separate)
team_colors = {
    "AP": [0, 102, 204],             # blue
    "VQH": [102, 90, 255],           # indigo
    "Verification": [0, 153, 102],   # green
    "Cost Match": [0, 38, 100],      # DSV core navy
    "Claims": [220, 53, 69],         # red
    "Intercompany": [220, 53, 69],   # red
    "Cash Management": [220, 53, 69] # red
}

# Short labels for pins
team_short = {
    "AP": "AP",
    "VQH": "VQH",
    "Verification": "VER",
    "Cost Match": "CM",
    "Claims": "CLM",
    "Intercompany": "IC",
    "Cash Management": "CASH"
}

# =================================================
# BUILD PIN POSITIONS (NO OVERLAP)
# We place multiple team pins inside each country using a fixed offset pattern.
# =================================================
# Offset patterns in degrees (small, stable, doesn’t “move around”)
# pattern supports up to 6+ teams per country if needed
offset_pattern = [
    (-2.2, -1.2),
    ( 0.0, -1.2),
    ( 2.2, -1.2),
    (-2.2,  1.2),
    ( 0.0,  1.2),
    ( 2.2,  1.2),
    ( 0.0,  0.0),
]

rows = []
for team, countries in audit_data.items():
    if not countries:
        continue
    for country, vals in countries.items():
        prog = int(round((sum(vals) / len(vals)) * 100))
        missing = [tasks[i] for i, v in enumerate(vals) if v == 0]
        rows.append({
            "Team": team,
            "TeamShort": team_short.get(team, team[:3].upper()),
            "Country": country,
            "Progress": prog,
            "Pending": ", ".join(missing) if missing else "",
            "base_lat": geo_coords[country][0],
            "base_lon": geo_coords[country][1],
            "color": team_colors.get(team, [0,38,100]),
        })

df = pd.DataFrame(rows)

# Assign stable positions per country: sort teams so always same placement
if not df.empty:
    df = df.sort_values(["Country", "Team"]).reset_index(drop=True)

    lat_list, lon_list = [], []
    for country, group in df.groupby("Country", sort=False):
        base_lat = group["base_lat"].iloc[0]
        base_lon = group["base_lon"].iloc[0]

        # Use pattern per team in that country
        for i in range(len(group)):
            dy, dx = offset_pattern[i % len(offset_pattern)]  # dy on lat, dx on lon
            lat_list.append(base_lat + dy)
            lon_list.append(base_lon + dx)

    df["lat"] = lat_list
    df["lon"] = lon_list

# =================================================
# TRANSFER STATUS BY TEAM
# =================================================
transferred_teams = [t for t, c in audit_data.items() if isinstance(c, dict) and len(c) > 0]
pending_transfer_teams = [t for t, c in audit_data.items() if isinstance(c, dict) and len(c) == 0]

# =================================================
# HEADER
# =================================================
st.markdown("""
<div class="header-bar">
  <div class="header-title">CIQMS | GBS Mexico – Knowledge Transfer Monitor</div>
  <div class="header-sub">Americas Region | KT / QC / Activities – Executive Tracking</div>
</div>
""", unsafe_allow_html=True)

# =================================================
# KPIs (defendable)
# =================================================
c1, c2, c3, c4 = st.columns(4)

overall_progress = int(df["Progress"].mean()) if not df.empty else 0
top_team = df.groupby("Team")["Progress"].mean().sort_values(ascending=False).index[0] if not df.empty else "-"
top_team_val = int(df.groupby("Team")["Progress"].mean().max()) if not df.empty else 0

most_common_gap = "-"
if not df.empty:
    gaps = df["Pending"].str.split(", ").explode().dropna()
    gaps = gaps[gaps != ""]
    if not gaps.empty:
        most_common_gap = gaps.value_counts().index[0]

with c1: st.metric("Overall Readiness (avg)", f"{overall_progress}%")
with c2: st.metric("Top Performer", top_team, f"{top_team_val}%")
with c3: st.metric("Main Gap (mode)", most_common_gap)
with c4: st.metric("Teams Pending Transfer", f"{len(pending_transfer_teams)}")

st.write("")

# =================================================
# FILTERS + TRANSFER STATUS PANEL
# =================================================
left, right = st.columns([1.15, 2.35])

with left:
    st.markdown("<div class='panel'><div class='panel-title'><span class='badge'>Filters</span></div><div class='hr'></div>", unsafe_allow_html=True)

    team_filter = st.multiselect(
        "Teams",
        options=sorted(df["Team"].unique()) if not df.empty else [],
        default=sorted(df["Team"].unique()) if not df.empty else []
    )
    country_filter = st.multiselect(
        "Countries",
        options=sorted(df["Country"].unique()) if not df.empty else [],
        default=sorted(df["Country"].unique()) if not df.empty else []
    )

    st.markdown("<div class='small-muted'>Tip: Select a country to review team readiness and gaps.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='panel'><div class='panel-title'><span class='badge'>Transfer Status</span></div><div class='hr'></div>", unsafe_allow_html=True)

    st.markdown("**✅ Transferred (in scope / executing):**")
    st.write(", ".join(transferred_teams) if transferred_teams else "—")

    st.markdown("**⏳ Pending transfer (NA / NOTHING):**")
    st.write(", ".join(pending_transfer_teams) if pending_transfer_teams else "—")

    st.markdown("<div class='small-muted'>NA / NOTHING = not transferred to GBS Mexico scope yet (not a performance issue).</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Apply filters
if not df.empty:
    df_f = df[df["Team"].isin(team_filter) & df["Country"].isin(country_filter)].copy()
else:
    df_f = df.copy()

# =================================================
# MAP + DETAILS (TRUE INTERACTIVE + NO OVERLAP)
# =================================================
col_map, col_details = st.columns([1.7, 1.0])

with col_map:
    st.markdown("<div class='panel'><div class='panel-title'><span class='badge'>Americas Deployment Map</span><span class='small-muted'>Pins are placed inside each country (no overlap)</span></div><div class='hr'></div>", unsafe_allow_html=True)

    # Scatter pins with outline (more corporate than icon atlas)
    map_layers = [
        pdk.Layer(
            "ScatterplotLayer",
            data=df_f,
            get_position="[lon, lat]",
            get_fill_color="color",
            get_radius=180000,
            radius_min_pixels=8,
            radius_max_pixels=22,
            pickable=True,
            opacity=0.92,
            stroked=True,
            get_line_color=[255, 255, 255],
            line_width_min_pixels=2,
        ),
        # Team label on top of pin (clean and professional)
        pdk.Layer(
            "TextLayer",
            data=df_f,
            get_position="[lon, lat]",
            get_text="TeamShort",
            get_size=14,
            size_units="pixels",
            get_color=[255, 255, 255],
            get_angle=0,
            pickable=False,
        )
    ]

    deck = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(latitude=15, longitude=-85, zoom=2.25, pitch=0),
        layers=map_layers,
        tooltip={
            "text": "Team: {Team}\nCountry: {Country}\nReadiness: {Progress}%\nMissing: {Pending}"
        },
        controller=True  # ✅ makes it properly interactive
    )

    st.pydeck_chart(deck, use_container_width=True)

    # Legend
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown("**Legend (Teams)**")
    for t in sorted(team_colors.keys()):
        rgb = team_colors[t]
        st.markdown(
            f"<div class='legend-item'><span class='dot' style='background: rgb({rgb[0]},{rgb[1]},{rgb[2]});'></span><span class='team-tag'>{t}</span></div>",
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

with col_details:
    st.markdown("<div class='panel'><div class='panel-title'><span class='badge'>Country Drilldown</span></div><div class='hr'></div>", unsafe_allow_html=True)

    if df_f.empty:
        st.info("No data for selected filters.")
    else:
        selected_country = st.selectbox("Select Country", sorted(df_f["Country"].unique()))
        view = df_f[df_f["Country"] == selected_country].sort_values("Progress", ascending=False)

        for _, r in view.iterrows():
            st.markdown(f"### {r['Team']}")
            st.progress(r["Progress"] / 100)
            st.markdown(f"**Readiness:** {r['Progress']}%")
            if r["Pending"]:
                st.markdown(f"⚠️ **Missing:** {r['Pending']}")
            else:
                st.markdown("✅ **Full readiness**")
            st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# EXEC MATRIX
# =================================================
st.write("")
st.markdown("<div class='panel'><div class='panel-title'><span class='badge'>Executive Readiness Matrix</span></div><div class='hr'></div>", unsafe_allow_html=True)

if df_f.empty:
    st.info("No matrix to display for selected filters.")
else:
    st.dataframe(
        df_f[["Team", "Country", "Progress", "Pending"]]
        .sort_values(by=["Country", "Progress"], ascending=[True, False]),
        use_container_width=True,
        column_config={
            "Progress": st.column_config.ProgressColumn("Readiness", format="%d%%", min_value=0, max_value=100),
            "Pending": st.column_config.TextColumn("Identified gaps"),
        }
    )

st.markdown("</div>", unsafe_allow_html=True)
st.caption("CIQMS | DSV GBS Mexico – Knowledge Transfer Tracker | Confidential - Internal Use Only")
