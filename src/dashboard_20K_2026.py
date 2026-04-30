import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="20K Training Dashboard", layout="wide")

def format_hhmm(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours:02d}:{minutes:02d}"

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("csv/prepa_20_km_Lausanne_2026.csv")

df["activity_date"] = pd.to_datetime(df["activity_date"])
df["duration_h"] = df["duration"] / 3600
df["week"] = df["activity_date"].dt.to_period("W").apply(lambda r: r.start_time)

# =========================
# SPORT GROUPING (NEW FEATURE)
# =========================
st.sidebar.header("Sport settings")

merge_cycling = st.sidebar.checkbox(
    "Merge Indoor + Road Cycling",
    value=True
)

df = df.copy()

if merge_cycling:
    df["sport_group"] = df["activityType"].replace({
        "indoor_cycling": "Cycling",
        "road_biking": "Cycling"
    })
else:
    df["sport_group"] = df["activityType"]

# =========================
# TITLE + PERIOD
# =========================
# =========================
# TITLE + PERIOD
# =========================
start_date = df["activity_date"].min().date()
end_date = df["activity_date"].max().date()

nb_days = (end_date - start_date).days + 1
nb_weeks = nb_days / 7
nb_months = nb_days / 30.44  # average month length

st.title("🏃 20 km Preparation Dashboard")

st.markdown(f"""
📅 **Training period:** {start_date} → {end_date}  

📆 **Total duration:**
- 🗓️ {nb_days} days  
- 📊 {nb_weeks:.1f} weeks  
- 📅 {nb_months:.1f} months  
""")

# =========================
# FILTERS
# =========================
st.sidebar.header("Filters")

sports = st.sidebar.multiselect(
    "Select sport",
    df["sport_group"].unique(),
    default=df["sport_group"].unique()
)

df = df[df["sport_group"].isin(sports)]

# =========================
# WEEKLY METRICS
# =========================
weekly_sessions = df.groupby("week")["activityId"].nunique()
avg_sessions_week = weekly_sessions.mean()
min_sessions_week = weekly_sessions.min()
max_sessions_week = weekly_sessions.max()

weekly_time = df.groupby("week")["duration"].sum()
avg_weekly_time = weekly_time.mean()
min_weekly_time = weekly_time.min()
max_weekly_time = weekly_time.max()

# =========================
# KPI COLUMNS
# =========================
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Distance (km)", round(df["distance_km"].sum(), 1))
col2.metric("Total Time", format_hhmm(df["duration"].sum()))
col3.metric("Sessions", df["activityId"].nunique())
col4.metric("Avg HR", round(df["averageHR"].mean(), 1))
col5.metric("Avg Weekly Time", format_hhmm(avg_weekly_time))
col6.metric("Avg Sessions / Week", f"{avg_sessions_week:.1f}")

# =========================
# WEEKLY RANGE
# =========================
st.markdown("### 📊 Weekly Training Range")

c1, c2 = st.columns(2)

c1.metric(
    "Sessions / Week (min → max)",
    f"{int(min_sessions_week)} → {int(max_sessions_week)}"
)

c2.metric(
    "Weekly Time (min → max)",
    f"{format_hhmm(min_weekly_time)} → {format_hhmm(max_weekly_time)}"
)

# =========================
# TRAINING VOLUME
# =========================
st.header("🏃 Training Volume")

metric = st.selectbox(
    "Choose metric",
    ["distance_km", "duration_h", "Number of Activities"],
    key="volume_metric"
)

if metric == "Number of Activities":
    vol = df.groupby("sport_group")["activityId"].nunique().reset_index()
    value_col = "activityId"
elif metric == "duration_h":
    vol = df.groupby("sport_group")["duration_h"].sum().reset_index()
    value_col = "duration_h"
else:
    vol = df.groupby("sport_group")["distance_km"].sum().reset_index()
    value_col = "distance_km"

vol = vol.sort_values(value_col, ascending=False)

if metric == "duration_h":
    vol["text"] = vol[value_col].apply(lambda x: format_hhmm(x * 3600))
else:
    vol["text"] = vol[value_col].round(2)

fig = px.bar(
    vol,
    x="sport_group",
    y=value_col,
    text="text",
    title=f"Training Volume by Sport ({metric})"
)

fig.update_traces(textposition="outside")
st.plotly_chart(fig, use_container_width=True)

# =========================
# PROGRESSION
# =========================
st.header("📈 Training Progression")

colA, colB = st.columns(2)

with colA:
    progress_metric = st.selectbox(
        "Metric",
        ["distance_km", "duration_h", "Number of Activities"],
        key="progress_metric"
    )

with colB:
    time_agg = st.selectbox(
        "Time aggregation",
        ["Week", "Month"],
        key="progress_time_agg"
    )

df = df.copy()

# -------------------------
# TIME
# -------------------------
if time_agg == "Week":
    df["period"] = df["activity_date"].dt.to_period("W").apply(lambda r: r.start_time)
    df["period_sort"] = df["period"]
else:
    df["period"] = df["activity_date"].dt.strftime("%b")
    df["period_sort"] = df["activity_date"].dt.to_period("M").dt.to_timestamp()

# -------------------------
# METRIC
# -------------------------
if progress_metric == "Number of Activities":
    base = df.groupby(["period", "sport_group"])["activityId"].nunique()
    y_label = "Number of Sessions"
    value_col = "activityId"

elif progress_metric == "duration_h":
    base = df.groupby(["period", "sport_group"])["duration_h"].sum()
    y_label = "Training Time (hours)"
    value_col = "duration_h"

else:
    base = df.groupby(["period", "sport_group"])["distance_km"].sum()
    y_label = "Distance (km)"
    value_col = "distance_km"

# -------------------------
# FULL GRID
# -------------------------
all_periods = df.sort_values("period_sort")["period"].unique()
all_sports = df["sport_group"].unique()

full_index = pd.MultiIndex.from_product(
    [all_periods, all_sports],
    names=["period", "sport_group"]
)

progress = base.reindex(full_index, fill_value=0).reset_index()

progress = progress.merge(
    df[["period", "period_sort"]].drop_duplicates(),
    on="period",
    how="left"
)

progress = progress.sort_values(["sport_group", "period_sort"])

# -------------------------
# DELTA
# -------------------------
progress["prev"] = progress.groupby("sport_group")[value_col].shift(1)

progress["pct_change"] = (
    (progress[value_col] - progress["prev"]) / progress["prev"]
) * 100

progress.loc[progress["prev"] == 0, "pct_change"] = None

progress["pct_change_str"] = progress["pct_change"].apply(
    lambda x: f"{x:.1f}%" if pd.notnull(x) else "N/A"
)

# -------------------------
# DISPLAY
# -------------------------
if progress_metric == "duration_h":
    progress["display_value"] = progress[value_col].apply(lambda x: format_hhmm(x * 3600))
else:
    progress["display_value"] = progress[value_col].round(2)

# -------------------------
# PLOT
# -------------------------
fig = px.line(
    progress,
    x="period",
    y=value_col,
    color="sport_group",
    markers=True,
    labels={
        "period": "Time",
        value_col: y_label,
        "sport_group": "Sport"
    },
    title=f"{y_label} Over Time by Sport",
    hover_data={
        "display_value": True,
        "pct_change_str": True,
        value_col: False
    }
)

fig.update_traces(
    hovertemplate=
    "<b>%{fullData.name}</b><br>" +
    "Period: %{x}<br>" +
    f"{y_label}: %{{customdata[0]}}<br>" +
    "Δ vs previous: %{customdata[1]}<extra></extra>"
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# HEART RATE ZONES
# =========================
st.header("❤️ Heart Rate Zones")

zone_cols = ["zone1", "zone2", "zone3", "zone4", "zone5"]

zone_total = df[zone_cols].sum()
zone_pct = (zone_total / zone_total.sum() * 100).reset_index()
zone_pct.columns = ["zone", "percent"]

fig = px.bar(
    zone_pct,
    x="zone",
    y="percent",
    text="percent",
    title="Training Intensity Distribution"
)

fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# =========================
# RAW DATA
# =========================
st.header("📄 Raw Data")
st.dataframe(df)