import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import os

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SENTINEL | Crime Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING ---
st.markdown("""
<style>
.stApp {
    background: linear-gradient(to bottom right, #0f172a, #1e293b);
    color: #e2e8f0;
}
section[data-testid="stSidebar"] {
    background-color: #0f172a;
    border-right: 1px solid #334155;
}
div[data-testid="stMetric"], div.stPlotlyChart, div.stDeckGlJsonChart, div[data-testid="stMarkdownContainer"] p {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
}
h1, h2, h3 { color: #f8fafc !important; }
.analyst-note {
    font-size: 0.9em;
    color: #94a3b8;
    border-left: 3px solid #38bdf8;
    padding-left: 10px;
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)

# --- OPTIMIZED + SAFE DATA LOADER ---
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file, parse_dates=["OCCURRED_ON_DATE"])

        # Convert columns to category where appropriate
        categorical_cols = [
            "DISTRICT", "OFFENSE_CODE_GROUP", "UCR_PART",
            "DAY_OF_WEEK", "SHOOTING"
        ]
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].astype("category")

        # Normalize SHOOTING
        if "SHOOTING" in df.columns:
            df["SHOOTING"] = df["SHOOTING"].cat.add_categories("N").fillna("N")
        else:
            df["SHOOTING"] = "N"

        # FIX: Make numeric (prevents sum() TypeError)
        df["Is_Shooting"] = (df["SHOOTING"] == "Y").astype(int)

        # Fix HOUR column
        if "HOUR" in df.columns:
            df["HOUR"] = pd.to_numeric(df["HOUR"], errors="coerce").fillna(0).astype(int)
        else:
            df["HOUR"] = df["OCCURRED_ON_DATE"].dt.hour.astype(int)

        # Clean coordinates
        df = df.dropna(subset=["Lat", "Long"])
        df = df[(df["Lat"] != -1) & (df["Lat"] != 0)]

        # Ensure OFFENSE_DESCRIPTION exists
        if "OFFENSE_DESCRIPTION" not in df.columns:
            df["OFFENSE_DESCRIPTION"] = "Unknown"

        return df

    except Exception:
        return None


# --- SIDEBAR ---
st.sidebar.title("🛡️ SENTINEL v2.0")
st.sidebar.caption("Tactical Crime Analysis System")

uploaded_file = st.sidebar.file_uploader("Upload Case Data (CSV)", type=["csv"])

df = None
if uploaded_file:
    df = load_data(uploaded_file)
elif os.path.exists("crime.csv"):
    df = load_data("crime.csv")

if df is None:
    st.info("⚠️ Please upload a CSV file to begin analysis.")
    st.stop()

# --- FILTERS ---
st.sidebar.subheader("📍 Mission Parameters")

min_date = df["OCCURRED_ON_DATE"].min().date()
max_date = df["OCCURRED_ON_DATE"].max().date()
date_range = st.sidebar.slider(
    "Timeline", min_value=min_date, max_value=max_date, value=(min_date, max_date)
)

all_districts = df["DISTRICT"].cat.categories.tolist()
selected_districts = st.sidebar.multiselect("Districts", all_districts, default=all_districts)

mask = (
    (df["OCCURRED_ON_DATE"].dt.date >= date_range[0]) &
    (df["OCCURRED_ON_DATE"].dt.date <= date_range[1]) &
    (df["DISTRICT"].isin(selected_districts))
)
df_filtered = df.loc[mask]

# --- DASHBOARD HEADER ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Operations Dashboard")
    st.markdown(f"**Data Scope:** {date_range[0]} — {date_range[1]} | **Records:** {len(df_filtered):,}")


# --- KPIs ---
st.markdown("### 📊 Key Performance Indicators")
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("Total Incidents", f"{len(df_filtered):,}")
    st.markdown("<p class='analyst-note'>Total incident volume.</p>", unsafe_allow_html=True)

with m2:
    shootings = df_filtered["Is_Shooting"].sum()
    st.metric("Confirmed Shootings", shootings)
    st.markdown("<p class='analyst-note'>Incidents with firearm discharge.</p>", unsafe_allow_html=True)

with m3:
    peak_hour = df_filtered["HOUR"].mode()[0]
    st.metric("Peak Activity Hour", f"{peak_hour}:00")
    st.markdown("<p class='analyst-note'>Time of highest activity.</p>", unsafe_allow_html=True)

with m4:
    top_offense = df_filtered["OFFENSE_CODE_GROUP"].mode()[0]
    st.metric("Top Offense Type", top_offense)
    st.markdown("<p class='analyst-note'>Most frequent crime category.</p>", unsafe_allow_html=True)

with m5:
    serious = len(df_filtered[df_filtered["UCR_PART"] == "Part One"])
    st.metric("Serious Crimes (Part 1)", serious)
    st.markdown("<p class='analyst-note'>Major felonies (UCR Part 1).</p>", unsafe_allow_html=True)

st.markdown("---")


# --- MAP + TEMPORAL TRENDS ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("🗺️ Geospatial Density")

    map_data = df_filtered[["Lat", "Long", "Is_Shooting"]].copy()

    heatmap_layer = pdk.Layer(
        "HexagonLayer",
        data=map_data,
        get_position='[Long, Lat]',
        radius=120,
        elevation_scale=4,
        elevation_range=[0, 1000],
        pickable=True,
        extruded=True,
    )

    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data[map_data["Is_Shooting"] == 1],
        get_position='[Long, Lat]',
        get_color=[255, 0, 0, 200],
        get_radius=80,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=map_data["Lat"].mean(),
        longitude=map_data["Long"].mean(),
        zoom=11,
        pitch=50,
    )

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/dark-v10',
        initial_view_state=view_state,
        layers=[heatmap_layer, scatter_layer],
        tooltip={"text": "Concentration Level"}
    ))


with c2:
    st.subheader("📈 Temporal Trends")

    daily_counts = df_filtered.groupby(df_filtered["OCCURRED_ON_DATE"].dt.date).size()
    daily_counts = daily_counts.reset_index(name="Counts")

    fig_trend = px.area(
        daily_counts,
        x="OCCURRED_ON_DATE",
        y="Counts",
        template="plotly_dark",
        color_discrete_sequence=["#38bdf8"]
    )
    fig_trend.update_layout(height=300, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_trend, use_container_width=True)


# --- PATTERN ANALYSIS ---
st.markdown("### 🔎 Strategic Analysis")

r3c1, r3c2 = st.columns(2)

with r3c1:
    st.subheader("Weekly Rhythm (Radar)")

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_counts = df_filtered.groupby("DAY_OF_WEEK").size().reindex(day_order)
    day_counts = day_counts.reset_index(name="Incidents")

    fig_radar = px.line_polar(
        day_counts,
        r="Incidents",
        theta="DAY_OF_WEEK",
        line_close=True,
        template="plotly_dark",
        color_discrete_sequence=["#ef4444"]
    )
    fig_radar.update_traces(fill="toself")
    fig_radar.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", polar=dict(bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_radar, use_container_width=True)


with r3c2:
    st.subheader("Crime Composition (Sunburst)")

    top_groups = df_filtered["OFFENSE_CODE_GROUP"].value_counts().head(15).index
    df_sun = df_filtered[df_filtered["OFFENSE_CODE_GROUP"].isin(top_groups)]

    fig_sun = px.sunburst(
        df_sun,
        path=["OFFENSE_CODE_GROUP", "OFFENSE_DESCRIPTION"],
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    fig_sun.update_layout(height=350, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_sun, use_container_width=True)

