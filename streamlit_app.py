import streamlit as st
import pandas as pd
import pydeck as pdk

# =================================================
# CONFIG
# =================================================
st.set_page_config(
    page_title="DSV | Knowledge Transfer Strategic Monitor",
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
.main { background-color: #F8F9FB; }

/* Metric cards */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border-radius: 8px;
    padding: 18px 18px 14px 18px;
    border-left: 6px solid #002664;
    box-shadow: 0 6px 18px rgba(0, 38, 100, 0.08);
}
[data-testid="stMetricLabel"] { color: #1f2a44; font-weight: 700; }
[data-testid="stMetricValue"] { color: #002664; font-weight: 800; }

/* Header */
.header-bar {
    background: linear-gradient(90deg, #002664 0%, #0B3C91 100%);
    padding: 22px 22px 18px 22px;
    border-radius: 0 0 16px 16px;
    color: white;
    margin-bottom: 22px;
}
.header-title { margin:0; color:white; font-size: 32px; font-weight: 800; letter-spacing: 0.3px;}
.header-sub { margin:0; opacity:0.85; font-size: 14px; }

/* Panels */
.panel {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 14px 16px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.05);
    border: 1px solid #EEF1F6;
}
.small-muted { color:#5c677d; font-size: 12px; }
.badge {
    display:inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    border: 1px solid #E6EAF2;
    background: #F6F8FC;
    color: #1f2a44;
}
.legend-item { display:flex; align-items:center; gap:10px; margin: 6px 0; }
.dot {
    width: 10px; height: 10px; border-radius: 50%;
    display:inline-block;
}
hr { border: none; border-top: 1px solid #EDF1F7; margin: 14px 0; }
</style>
""", unsafe_allow_html=True)

# =================================================
# DATA (from your images / definitions)
# =================================================
tasks = ["Team Huddle", "Operational Calls", "Feedback Tool", "QC", "SharePoint/Catalogue", "Unit Pricing", "MM", "KPIs"]

# 1 = YES (Transferred & executed)
# 0 = NO (In country/GBS visible but not transferred/executed)
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
    # Teams with NOTHING / NA in your tracker (pending transfer to GBS MX scope)
    "Claims": {},
    "Intercompany": {},
    "Cash Management": {},
}

# Country coordinates (centroids)
geo_coords = {
    "CANADA": [56.1, -106.3],
    "USA": [37.1, -95.7],
    "MEXICO": [23.6, -102.5],
    "CHILE": [-35.7, -71.5],
    "PERU": [-9.2, -75.0],
    "PR": [18.2, -66.6],
}

# Distinct pin colors per team (DSV-like)
team_colors = {
    "Verification": [18, 99, 56],     # green-ish (implemented)
    "Cost Match": [0, 38, 100],       # DSV core blue
    "AP": [11, 60, 145],              # deep blue
    "VQH": [60, 110, 180],            # steel blue
    "Claims": [180, 0, 0],            # red (pending transfer)
    "Intercompany": [180, 0, 0],      # red
    "Cash Management": [180, 0, 0],   # red
}

# =================================================
# BUILD ROWS FOR MAP + MATRIX
# =================================================
rows = []
for team, countries in audit_data.items():
    if not countries:
        continue
    for country, vals in countries.items():
        prog = int(round((sum(vals) / len(vals)) * 100))
        missing = [tasks[i] for i, v in enumerate(vals) if v == 0]

        # slight jitter for overlapping pins
        team_idx = list(audit_data.keys()).index(team)
        jitter = (team_idx % 5) * 0.35

        lat, lon = geo_coords[country]
        rows.append({
            "Team": team,
            "Country": country,
            "Progress": prog,
            "Pending": ", ".join(missing) if missing else "",
            "lat": lat + jitter,
            "lon": lon + jitter,
            "color": team_colors.get(team, [0,38,100]),
        })

df = pd.DataFrame(rows)

# =================================================
# TRANSFER STATUS BY TEAM (as you defined)
# YES/NO/NA logic translated to team level
# - "Transferred": teams that have ANY mapped country/activity in the tracker (in scope)
# - "Pending transfer": teams with NOTHING/NA (empty dictionaries)
# =================================================
transferred_teams = [t for t, c in audit_data.items() if isinstance(c, dict) and len(c) > 0]
pending_transfer_teams = [t for t, c in audit_data.items() if isinstance(c, dict) and len(c) == 0]

# =================================================
# HEADER
# =================================================
st.markdown("""
<div class="header-bar">
  <div class="header-title">KNOWLEDGE TRANSFER STRATEGIC MONITOR</div>
  <div class="header-sub">CIQMS | Americas Region | KT / QC / Activities – Executive View</div>
</div>
""", unsafe_allow_html=True)

# =================================================
# KPIs (defendable)
# =================================================
col1, col2, col3, col4 = st.columns(4)

overall_progress = int(df["Progress"].mean()) if not df.empty else 0
top_team = df.groupby("Team")["Progress"].mean().sort_values(ascending=False).index[0] if not df.empty else "-"
top_team_val = int(df.groupby("Team")["Progress"].mean().max()) if not df.empty else 0

# Most common gaps across all entries
most_common_gap = "-"
if not df.empty:
    gaps = (
        df["Pending"].str.split(", ")
        .explode()
        .dropna()
    )
    gaps = gaps[gaps != ""]
    if not gaps.empty:
        most_common_gap = gaps.value_counts().index[0]

with col1:
    st.metric("Overall Readiness (avg)", f"{overall_progress}%")
with col2:
    st.metric("Top Team (avg)", top_team, f"{top_team_val}%")
with col3:
    st.metric("Most common gap", most_common_gap)
with col4:
    st.metric("Teams pending transfer", f"{len(pending_transfer_teams)}")

st.write("")

# =================================================
# FILTERS
# =================================================
left_filters, right_filters = st.columns([1.2, 2.2])
with left_filters:
    st.markdown("<div class='panel'><span class='badge'>Filters</span><hr>", unsafe_allow_html=True)

    team_filter = st.multiselect(
        "Team(s)",
        options=sorted(df["Team"].unique()) if not df.empty else [],
        default=sorted(df["Team"].unique()) if not df.empty else []
    )

    country_filter = st.multiselect(
        "Country(ies)",
        options=sorted(df["Country"].unique()) if not df.empty else [],
        default=sorted(df["Country"].unique()) if not df.empty else []
    )

    st.markdown("</div>", unsafe_allow_html=True)

with right_filters:
    st.markdown("<div class='panel'><span class='badge'>Transfer Status by Team</span><hr>", unsafe_allow_html=True)

    st.markdown("**✅ Transferred (in scope / executing):**")
    if transferred_teams:
        st.write(", ".join(transferred_teams))
    else:
        st.write("—")

    st.markdown("**⏳ Pending transfer (NA / NOTHING):**")
    if pending_transfer_teams:
        st.write(", ".join(pending_transfer_teams))
    else:
        st.write("—")

    st.markdown("<div class='small-muted'>Note: NA/NOTHING = not yet transferred to GBS Mexico scope (not a performance issue).</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Apply filters
if not df.empty:
    df_f = df[df["Team"].isin(team_filter) & df["Country"].isin(country_filter)].copy()
else:
    df_f = df.copy()

# =================================================
# MAP + DETAILS
# =================================================
col_map, col_details = st.columns([1.7, 1])

with col_map:
    st.markdown("<div class='panel'><span class='badge'>Americas Map</span><hr>", unsafe_allow_html=True)

    # Use IconLayer for "pin" look
    icon_data = {
        "url": "https://raw.githubusercontent.com/visgl/deck.gl-data/master/website/icon-atlas.png",
        "width": 128,
        "height": 128,
        "anchorY": 128,
        "mask": True
    }

    df_f["icon_data"] = [icon_data] * len(df_f)

    deck = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(latitude=15, longitude=-85, zoom=2.2, pitch=0),
        layers=[
            pdk.Layer(
                "IconLayer",
                data=df_f,
                get_icon="icon_data",
                get_position="[lon, lat]",
                get_size=4,
                size_scale=12,
                pickable=True,
                get_color="color",
            ),
        ],
        tooltip={
            "text": "Team: {Team}\nCountry: {Country}\nReadiness: {Progress}%\nMissing: {Pending}"
        },
    )

    st.pydeck_chart(deck, use_container_width=True)

    # Legend (pins by team color)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("**Legend (Teams)**")
    for t in sorted(team_colors.keys()):
        rgb = team_colors[t]
        st.markdown(
            f"<div class='legend-item'><span class='dot' style='background: rgb({rgb[0]},{rgb[1]},{rgb[2]});'></span>{t}</div>",
            unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)

with col_details:
    st.markdown("<div class='panel'><span class='badge'>Details</span><hr>", unsafe_allow_html=True)

    if df_f.empty:
        st.info("No data for selected filters.")
    else:
        # Country selector for clean drill-down
        selected_country = st.selectbox("Country view", sorted(df_f["Country"].unique()))
        view = df_f[df_f["Country"] == selected_country].sort_values("Progress", ascending=False)

        for _, r in view.iterrows():
            st.markdown(f"### {r['Team']}")
            st.progress(r["Progress"] / 100)
            st.markdown(f"**Readiness:** {r['Progress']}%")

            if r["Pending"]:
                st.markdown(f"⚠️ **Missing:** {r['Pending']}")
            else:
                st.markdown("✅ **Full readiness**")

            st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# EXEC MATRIX
# =================================================
st.write("")
st.markdown("<div class='panel'><span class='badge'>Executive Readiness Matrix</span><hr>", unsafe_allow_html=True)

if df_f.empty:
    st.info("No matrix to display for selected filters.")
else:
    st.dataframe(
        df_f[["Team", "Country", "Progress", "Pending"]]
        .sort_values(by=["Country", "Progress"], ascending=[True, False]),
        use_container_width=True,
        column_config={
            "Progress": st.column_config.ProgressColumn(
                "Readiness",
                format="%d%%",
                min_value=0,
                max_value=100
            ),
            "Pending": st.column_config.TextColumn("Identified gaps"),
        }
    )

st.markdown("</div>", unsafe_allow_html=True)

st.caption("DSV Global Knowledge Transfer Tracker | Confidential - Internal Use Only")
