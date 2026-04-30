import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# =========================
# CONFIG
# =========================
START_DATE = pd.to_datetime("2026-02-02")  # Monday
RACE_DATE = pd.to_datetime("2026-08-30")   # Sunday

st.set_page_config(layout="wide")
st.title("🏁 Triathlon 2026 Dashboard")

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("csv/Lausanne_Triathlon_2026/main.csv")
df["activity_date"] = pd.to_datetime(df["activity_date"])

# =========================
# TRAINING WEEK (MONDAY-BASED)
# =========================
df = df[df["activity_date"] >= START_DATE].copy()

df["training_week"] = (
    (df["activity_date"] - START_DATE).dt.days // 7
) + 1

# =========================
# FORMAT DURATION AS HH:MM
# =========================
def format_hhmm(hours):
    if pd.isna(hours):
        return "0h 00m"
    total_minutes = int(round(hours * 60))
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h}h {m:02d}m"

# =========================
# FIXED CYCLING MERGE (ONLY ONCE)
# =========================
st.sidebar.header("⚙️ Settings")

merge_cycling = st.sidebar.checkbox(
    "Merge Indoor Cycling + Road Biking",
    value=True
)


df_raw = df.copy()

if merge_cycling:
    df_raw["activityType"] = df_raw["activityType"].replace({
        "indoor_cycling": "cycling",
        "road_biking": "cycling"
    })

df = df_raw

# =========================
# 🌍 GLOBAL COMPLETION
# =========================
st.header("🌍 Global Progress")

today = pd.to_datetime("today").normalize()

total_days = (RACE_DATE - START_DATE).days
elapsed_days = (today - START_DATE).days

completion_pct = max(0, min(elapsed_days / total_days, 1)) * 100

fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=completion_pct,
    title={"text": "Plan Completion (%)"},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": "green"},
        "steps": [
            {"range": [0, 50], "color": "lightgray"},
            {"range": [50, 80], "color": "lightblue"},
            {"range": [80, 100], "color": "lightgreen"},
        ],
    }
))

st.plotly_chart(fig, use_container_width=True)

st.markdown(f"""
📅 Start: {START_DATE.date()}  
🏁 Race: {RACE_DATE.date()}  
📊 Days elapsed: {max(0, elapsed_days)} / {total_days}
""")

# =========================
# 📅 WEEKLY OVERVIEW
# =========================
st.header("📅 Weekly Overview")

max_week = int(df["training_week"].max())

selected_week = st.selectbox(
    "Select Training Week",
    list(range(1, max_week + 1))
)

# =========================
# COMPUTE WEEK DATES
# =========================
week_start = START_DATE + pd.Timedelta(days=(selected_week - 1) * 7)
week_end = week_start + pd.Timedelta(days=6)

st.markdown(
    f"📅 **Week {selected_week}: {week_start.date()} → {week_end.date()}**"
)

# =========================
# FILTER DATA
# =========================
week_df = df[df["training_week"] == selected_week]
prev_week_df = df[df["training_week"] == selected_week - 1]

# =========================
# KPI CALCULATIONS
# =========================
# Sessions
sessions = week_df["activityId"].nunique()
prev_sessions = prev_week_df["activityId"].nunique()

# Training time (hours)
training_time = week_df["duration"].sum() / 3600
prev_training_time = prev_week_df["duration"].sum() / 3600

# =========================
# DELTA CALCULATIONS
# =========================
delta_sessions = sessions - prev_sessions
delta_time = training_time - prev_training_time

# percentage delta (safe)
if prev_training_time > 0:
    delta_pct = (delta_time / prev_training_time) * 100
    delta_pct_str = f"{delta_pct:+.1f}%"
else:
    delta_pct_str = "n/a"

# combined delta string
if prev_training_time > 0:
    delta_time_str = f"{format_hhmm(delta_time)} ({delta_pct_str})"
else:
    delta_time_str = "n/a"

# =========================
# DISPLAY KPIs SIDE BY SIDE
# =========================
col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="Training Sessions",
        value=sessions,
        delta=f"{delta_sessions:+d}"
    )

with col2:
    st.metric(
        label="Training Time",
        value=format_hhmm(training_time),
        delta=delta_time_str
    )


# =========================
# 📊 TRAINING VOLUME (LEFT)
# =========================
col_left, col_right = st.columns(2)

with col_left:

    st.subheader("📊 Training Volume")

    metric = st.selectbox(
        "Metric",
        ["Duration", "Distance"],
        key="training_volume_metric"
    )

    # -------------------------
    # AGGREGATION
    # -------------------------
    current = week_df.groupby("activityType").agg(
        duration=("duration", "sum"),
        distance_km=("distance_km", "sum")
    ).reset_index()

    previous = prev_week_df.groupby("activityType").agg(
        duration_prev=("duration", "sum"),
        distance_km_prev=("distance_km", "sum")
    ).reset_index()

    # merge (keep all sports from current week)
    chart_df = current.merge(previous, on="activityType", how="left").fillna(0)

    # -------------------------
    # METRIC SELECTION
    # -------------------------
    if metric == "Duration":
        chart_df["value"] = chart_df["duration"] / 3600
        chart_df["prev_value"] = chart_df["duration_prev"] / 3600
        y_label = "Training Time"

        chart_df["label"] = chart_df["value"].apply(format_hhmm)

        def format_value(x):
            return format_hhmm(x)

    else:
        chart_df["value"] = chart_df["distance_km"]
        chart_df["prev_value"] = chart_df["distance_km_prev"]
        y_label = "Distance (km)"

        chart_df["label"] = chart_df["value"].round(1).astype(str)

        def format_value(x):
            return f"{x:.1f} km"

    # -------------------------
    # DELTAS
    # -------------------------
    chart_df["delta"] = chart_df["value"] - chart_df["prev_value"]

    def safe_pct(curr, prev):
        if prev == 0:
            return None
        return (curr - prev) / prev * 100

    chart_df["delta_pct"] = chart_df.apply(
        lambda r: safe_pct(r["value"], r["prev_value"]),
        axis=1
    )

    # -------------------------
    # TOOLTIP
    # -------------------------
    def build_tooltip(row):
        delta_pct = row["delta_pct"]

        pct_str = f"{delta_pct:+.1f}%" if delta_pct is not None else "n/a"

        return (
            f"Current: {format_value(row['value'])}<br>"
            f"Previous: {format_value(row['prev_value'])}<br>"
            f"Δ: {format_value(row['delta']) if row['delta'] >= 0 else '-' + format_value(abs(row['delta']))}<br>"
            f"Δ%: {pct_str}"
        )

    chart_df["hover"] = chart_df.apply(build_tooltip, axis=1)

    # -------------------------
    # SORT
    # -------------------------
    chart_df = chart_df.sort_values("value", ascending=False)

    # -------------------------
    # PLOT
    # -------------------------
    import plotly.express as px

    fig = px.bar(
        chart_df,
        x="activityType",
        y="value",
        text="label",
        hover_data={"hover": True},
        title=f"{y_label} by Sport"
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{customdata[0]}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)



# =========================
# ❤️ ZONE ANALYSIS (RIGHT)
# =========================
with col_right:

    st.subheader("❤️ Zone Analysis")

    zone_mode = st.selectbox(
        "View",
        ["Current vs Previous", "Zone Distribution per Sport"],
        key="zone_analysis_mode"
    )

    zone_cols = ["zone1", "zone2", "zone3", "zone4", "zone5"]

    import plotly.express as px
    import numpy as np

    # =========================
    # MODE 1 — CURRENT VS PREVIOUS
    # =========================
    if zone_mode == "Current vs Previous":

        def compute_zone_pct(df_):
            z = df_[zone_cols].sum()
            total = z.sum()

            if total == 0:
                return pd.DataFrame({
                    "zone": zone_cols,
                    "percent": [0]*5
                })

            pct = (z / total * 100).round(0)

            return pd.DataFrame({
                "zone": zone_cols,
                "percent": pct.values
            })

        current_zone = compute_zone_pct(week_df)
        prev_zone = compute_zone_pct(prev_week_df)

        current_zone["week"] = "Current"
        prev_zone["week"] = "Previous"

        zone_df = pd.concat([prev_zone, current_zone])

        # label only if >= 10%
        zone_df["label"] = zone_df["percent"].apply(
            lambda x: f"{int(x)}%" if x >= 10 else ""
        )

        # consistent colors
        color_map = {
            "zone1": "#ADD8E6",
            "zone2": "#6BAED6",
            "zone3": "#FDAE6B",
            "zone4": "#FB6A4A",
            "zone5": "#FF0000"
        }

        fig = px.bar(
            zone_df,
            x="week",
            y="percent",
            color="zone",
            color_discrete_map=color_map,
            text="label"
        )

        fig.update_layout(barmode="stack")

        fig.update_traces(
            textposition="inside",
            insidetextanchor="middle"
        )

        st.plotly_chart(fig, use_container_width=True)

    # =========================
    # MODE 2 — ZONE DISTRIBUTION PER SPORT
    # =========================
    else:

        # reshape data
        melted = week_df.melt(
            id_vars=["activityType"],
            value_vars=zone_cols,
            var_name="zone",
            value_name="time"
        )

        melted["time"] = pd.to_numeric(melted["time"], errors="coerce").fillna(0)

        # total time per zone
        zone_total = melted.groupby("zone")["time"].sum().reset_index()
        zone_total = zone_total.rename(columns={"time": "zone_time"})

        total_time = zone_total["zone_time"].sum()

        # zone % of total training time
        zone_total["zone_pct"] = np.where(
            total_time > 0,
            (zone_total["zone_time"] / total_time) * 100,
            0
        )

        # contribution of each sport inside each zone
        zone_sport = melted.groupby(["zone", "activityType"])["time"].sum().reset_index()

        zone_sport = zone_sport.merge(zone_total, on="zone", how="left")

        # share within zone
        zone_sport["share"] = np.where(
            zone_sport["zone_time"] > 0,
            zone_sport["time"] / zone_sport["zone_time"],
            0
        )

        # final value = contribution to total
        zone_sport["value"] = zone_sport["zone_pct"] * zone_sport["share"]

        # labels for total zone %
        zone_labels = zone_total.copy()
        zone_labels["label"] = zone_labels["zone_pct"].round(0).astype(int).astype(str) + "%"

        # plot
        fig = px.bar(
            zone_sport,
            x="zone",
            y="value",
            color="activityType",
            title="Zone Distribution per Sport"
        )

        fig.update_layout(
            barmode="stack",
            yaxis_title="% of Weekly Training"
        )

        # add total % labels on top
        fig.add_scatter(
            x=zone_labels["zone"],
            y=zone_labels["zone_pct"],
            text=zone_labels["label"],
            mode="text",
            textposition="top center",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)


# =========================
# 🌍 GLOBAL OVERVIEW
# =========================
st.header("🌍 Global Overview")

import plotly.graph_objects as go

# =========================
# CONTROLS (SIDE BY SIDE)
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    metric = st.selectbox(
        "Metric",
        ["Duration", "Distance"],
        key="global_metric"
    )

with col2:
    freq = st.selectbox(
        "Aggregation",
        ["Weekly", "Monthly"],
        key="global_freq"
    )

with col3:
    view_mode = st.selectbox(
        "View mode",
        ["Normal", "Cumulative"],
        key="global_view_mode"
    )
# =========================
# PREP DATA
# =========================
df_global = df.copy()
df_global["activity_date"] = pd.to_datetime(df_global["activity_date"])

# =========================
# PERIOD CREATION
# =========================
if freq == "Weekly":

    # Monday-based training weeks aligned to START_DATE
    df_global["period"] = START_DATE + pd.to_timedelta(
        (df_global["training_week"] - 1) * 7,
        unit="D"
    )
else:
    df_global["period"] = df_global["activity_date"].dt.to_period("M").dt.to_timestamp()

# =========================
# AGGREGATION
# =========================
agg = df_global.groupby(["period", "activityType"]).agg(
    duration=("duration", "sum"),
    distance_km=("distance_km", "sum")
).reset_index()

# =========================
# METRIC SELECTION
# =========================
if metric == "Duration":
    agg["value"] = agg["duration"] / 3600
else:
    agg["value"] = agg["distance_km"]

# =========================
# COMPLETE GRID (NO MISSING SPORTS)
# =========================
all_periods = agg["period"].unique()
all_sports = df["activityType"].unique()

grid = pd.MultiIndex.from_product(
    [all_periods, all_sports],
    names=["period", "activityType"]
).to_frame(index=False)

agg = grid.merge(agg, on=["period", "activityType"], how="left").fillna(0)

# =========================
# SORT (CRITICAL FOR CUMULATIVE)
# =========================
agg = agg.sort_values(["activityType", "period"])

# =========================
# CUMULATIVE MODE
# =========================
if view_mode == "Cumulative":
    agg["value"] = agg.groupby("activityType")["value"].cumsum()

# =========================
# TOOLTIP HELPERS
# =========================
def format_value(x):
    if metric == "Duration":
        return format_hhmm(x)
    return f"{x:.1f} km"

# previous value (ONLY meaningful in Normal mode)
agg["prev_value"] = agg.groupby("activityType")["value"].shift(1).fillna(0)

def safe_pct(curr, prev):
    if prev == 0:
        return None
    return (curr - prev) / prev * 100

def build_tooltip(row):
    delta = row["value"] - row["prev_value"]
    pct = safe_pct(row["value"], row["prev_value"])

    pct_str = f"{pct:+.1f}%" if pct is not None else "n/a"

    return (
        f"Current: {format_value(row['value'])}<br>"
        f"Previous: {format_value(row['prev_value'])}<br>"
        f"Δ: {format_value(delta) if delta >= 0 else '-' + format_value(abs(delta))}<br>"
        f"Δ%: {pct_str}"
    )

agg["hover"] = agg.apply(build_tooltip, axis=1)

# =========================
# PLOT
# =========================
fig = go.Figure()

for sport in agg["activityType"].unique():

    sport_df = agg[agg["activityType"] == sport]

    fig.add_trace(
        go.Scatter(
            x=sport_df["period"],
            y=sport_df["value"],
            mode="lines+markers",
            name=sport,
            customdata=sport_df["hover"],
            hovertemplate="%{customdata}<extra></extra>"
        )
    )

# =========================
# LAYOUT
# =========================
fig.update_layout(
    title=f"{metric} per {freq} by Sport ({view_mode})",
    xaxis_title=freq,
    yaxis_title=metric,
    hovermode="closest"
)

fig.update_xaxes(
    tickformat="%d %b"
)

st.plotly_chart(fig, use_container_width=True)