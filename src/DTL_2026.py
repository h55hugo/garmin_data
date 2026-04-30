import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# =========================
# CONFIG
# =========================
START_DATE = pd.to_datetime("2026-05-11")
RACE_DATE = pd.to_datetime("2026-08-30")

EXPECTED_SESSIONS_PER_WEEK = 6

st.set_page_config(layout="wide")
st.title("🏁 Lausanne Triathlon 2026 Dashboard")

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("csv/Lausanne_Triathlon_2026/main.csv")
df["activity_date"] = pd.to_datetime(df["activity_date"])

# =========================
# SETTINGS
# =========================
st.sidebar.header("⚙️ Settings")

merge_cycling = st.sidebar.checkbox(
    "Merge Indoor Cycling + Road Biking",
    value=True
)

# =========================
# FIXED CYCLING MERGE (ONLY ONCE)
# =========================
df_raw = df.copy()

if merge_cycling:
    df_raw["activityType"] = df_raw["activityType"].replace({
        "indoor_cycling": "cycling",
        "road_biking": "cycling"
    })

df = df_raw

# =========================
# FILTER PLAN
# =========================
plan_df = df[
    (df["activity_date"] >= START_DATE) &
    (df["activity_date"] <= RACE_DATE)
].copy()

plan_df["week"] = ((plan_df["activity_date"] - START_DATE).dt.days // 7) + 1

total_weeks = ((RACE_DATE - START_DATE).days // 7) + 1

# =========================
# UTILS
# =========================
def format_hhmm(hours):
    total_minutes = int(hours * 60)
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h}h {m}m"

# =========================
# GLOBAL COMPLETION
# =========================
expected_total_sessions = total_weeks * EXPECTED_SESSIONS_PER_WEEK
actual_sessions = plan_df["activityId"].nunique()

completion_pct = min(actual_sessions / expected_total_sessions, 1.0) * 100

today = pd.to_datetime("today").normalize()

days_total = (RACE_DATE - START_DATE).days
days_elapsed = (today - START_DATE).days
days_left = (RACE_DATE - today).days

days_elapsed = max(days_elapsed, 0)
days_left = max(days_left, 0)

fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=completion_pct,
    title={
        "text": (
            f"Overall Plan Completion<br>"
            f"{START_DATE.date()} → {RACE_DATE.date()}"
        )
    },
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

st.markdown(
    f"""
📅 **Plan duration:** {days_total} days  
📆 **Elapsed:** {days_elapsed} days  
⏳ **Days left:** {days_left} days  
🏁 **Race day:** {RACE_DATE.date()}
"""
)

# =========================
# WEEK SELECTION
# =========================
st.header("📅 Weekly Overview")

selected_week = st.selectbox("Select week", list(range(1, total_weeks + 1)))

week_df = plan_df[plan_df["week"] == selected_week]
prev_week_df = plan_df[plan_df["week"] == selected_week - 1]

week_start = START_DATE + pd.Timedelta(days=(selected_week - 1) * 7)
week_end = week_start + pd.Timedelta(days=6)

st.markdown(f"📅 Week {selected_week}: {week_start.date()} → {week_end.date()}")

# =========================
# KPI
# =========================
col1, col2 = st.columns(2)

sessions = week_df["activityId"].nunique()
prev_sessions = prev_week_df["activityId"].nunique()

time_h = week_df["duration"].sum() / 3600
prev_time_h = prev_week_df["duration"].sum() / 3600

col1.metric("Sessions", sessions, f"{sessions - prev_sessions:+d}")
col2.metric("Training Time", format_hhmm(time_h), f"{format_hhmm(time_h - prev_time_h)}")

# =========================
# TRAINING VOLUME
# =========================
col_left, col_right = st.columns(2)
with col_left:

    st.subheader("📊 Training Volume")

    metric = st.selectbox("Metric", ["duration", "distance_km"])

    # -------------------------
    # CURRENT WEEK
    # -------------------------
    chart_df = week_df.groupby("activityType").agg(
        duration=("duration", "sum"),
        distance_km=("distance_km", "sum"),
        sessions=("activityId", "nunique")
    ).reset_index()

    # -------------------------
    # PREVIOUS WEEK
    # -------------------------
    prev_df = prev_week_df.groupby("activityType").agg(
        duration_prev=("duration", "sum"),
        distance_km_prev=("distance_km", "sum"),
        sessions_prev=("activityId", "nunique")
    ).reset_index()

    # -------------------------
    # MERGE
    # -------------------------
    chart_df = chart_df.merge(prev_df, on="activityType", how="left").fillna(0)

    # -------------------------
    # FORMAT HELPERS
    # -------------------------
    def format_hhmm(hours):
        total_minutes = int(round(hours * 60))
        h = total_minutes // 60
        m = total_minutes % 60
        return f"{h}h {m:02d}m"

    def safe_pct(curr, prev):
        if prev == 0:
            return None
        return ((curr - prev) / prev) * 100

    # -------------------------
    # METRIC SELECTION
    # -------------------------
    if metric == "duration":

        chart_df["value"] = chart_df["duration"] / 3600
        chart_df["prev_value"] = chart_df["duration_prev"] / 3600
        y_label = "Training Time"

        chart_df["label"] = chart_df["value"].apply(format_hhmm)

        chart_df["delta"] = chart_df["value"] - chart_df["prev_value"]
        chart_df["delta_pct"] = chart_df.apply(
            lambda r: safe_pct(r["value"], r["prev_value"]),
            axis=1
        )

        chart_df["hover"] = chart_df.apply(
            lambda r: (
                f"Current: {format_hhmm(r['value'])}<br>"
                f"Previous: {format_hhmm(r['prev_value'])}<br>"
                f"Δ: {format_hhmm(abs(r['delta'])) if r['delta'] >= 0 else '-' + format_hhmm(abs(r['delta']))}<br>"
                f"Δ%: {r['delta_pct']:+.1f}%<br>"
                f"Sessions: {int(r['sessions'])}"
            ),
            axis=1
        )

    else:

        chart_df["value"] = chart_df["distance_km"]
        chart_df["prev_value"] = chart_df["distance_km_prev"]
        y_label = "Distance (km)"

        chart_df["label"] = chart_df["value"].round(2).astype(str)

        chart_df["delta"] = chart_df["value"] - chart_df["prev_value"]
        chart_df["delta_pct"] = chart_df.apply(
            lambda r: safe_pct(r["value"], r["prev_value"]),
            axis=1
        )

        chart_df["hover"] = chart_df.apply(
            lambda r: (
                f"Current: {r['value']:.2f} km<br>"
                f"Previous: {r['prev_value']:.2f} km<br>"
                f"Δ: {r['delta']:+.2f} km<br>"
                f"Δ%: {r['delta_pct']:+.1f}%<br>"
                f"Sessions: {int(r['sessions'])}"
            ),
            axis=1
        )

    # -------------------------
    # SORT
    # -------------------------
    chart_df = chart_df.sort_values("value", ascending=False)

    # -------------------------
    # PLOT
    # -------------------------
    fig_bar = px.bar(
        chart_df,
        x="activityType",
        y="value",
        text="label",
        hover_data={"hover": True},
        title=f"{y_label} by Sport (Current vs Previous Week)"
    )

    fig_bar.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{customdata[0]}<extra></extra>"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

# =========================
# ❤️ ZONE ANALYSIS (FIXED SAFE VERSION)
# =========================
with col_right:

    st.subheader("❤️ Zone Analysis")

    zone_mode = st.selectbox(
        "View",
        ["Current vs Previous", "Zone Distribution per Sport"]
    )

    zone_cols = ["zone1", "zone2", "zone3", "zone4", "zone5"]

    # =========================
    # MODE 1 — CURRENT VS PREVIOUS (WITH COLORS)
    # =========================
    if zone_mode == "Current vs Previous":

        def zone_percent(df_):
            z = df_[zone_cols].sum()
            total = z.sum()

            if total == 0:
                return pd.DataFrame({
                    "zone": zone_cols,
                    "percent": [0]*5
                })

            return pd.DataFrame({
                "zone": zone_cols,
                "percent": (z / total * 100).values
            })

        week_zone = zone_percent(week_df)
        prev_zone = zone_percent(prev_week_df)

        week_zone["week"] = "Current"
        prev_zone["week"] = "Previous"

        zone_compare = pd.concat([prev_zone, week_zone])

        # -------------------------
        # 🎨 COLOR MAP (Z1 → Z5 gradient)
        # -------------------------
        color_map = {
            "zone1": "#ADD8E6",  # light blue
            "zone2": "#6BAED6",
            "zone3": "#FDAE6B",
            "zone4": "#FB6A4A",
            "zone5": "#FF0000"   # red
        }

        fig_zone = px.bar(
            zone_compare,
            x="week",
            y="percent",
            color="zone",
            color_discrete_map=color_map,
            text=zone_compare["percent"].apply(
                lambda x: f"{int(round(x))}%" if x >= 10 else ""
            )
        )

        fig_zone.update_layout(barmode="stack")

        fig_zone.update_traces(
            textposition="inside",
            insidetextanchor="middle"
        )

        st.plotly_chart(fig_zone, use_container_width=True)

# =========================================================
# MODE 2 — ZONE DISTRIBUTION PER SPORT (FIXED)
# =========================================================
    else:

        melted = week_df.melt(
            id_vars=["activityType"],
            value_vars=zone_cols,
            var_name="zone",
            value_name="time"
        )

        # 🚨 FIX: ensure numeric + no NaN issues
        melted["time"] = pd.to_numeric(melted["time"], errors="coerce").fillna(0)

        # total per zone
        zone_total = melted.groupby("zone")["time"].sum().reset_index()
        zone_total = zone_total.rename(columns={"time": "zone_total"})

        total_time = zone_total["zone_total"].sum()
        zone_total["zone_pct"] = np.where(
            total_time > 0,
            (zone_total["zone_total"] / total_time) * 100,
            0
        )

        # per sport contribution
        zone_sport = melted.groupby(["zone", "activityType"])["time"].sum().reset_index()

        zone_sport = zone_sport.merge(zone_total, on="zone", how="left")

        # 🚨 FIX: safe division (prevents KeyError + NaN issues)
        zone_sport["share"] = np.where(
            zone_sport["zone_total"] > 0,
            zone_sport["time"] / zone_sport["zone_total"],
            0
        )

        zone_sport["value"] = zone_sport["zone_pct"] * zone_sport["share"]
        zone_sport["value"] = zone_sport["value"].fillna(0)

        # labels
        zone_labels = zone_total.copy()
        zone_labels["label"] = zone_labels["zone_pct"].round(0).astype("Int64").astype(str) + "%"

        # plot
        fig_zone = px.bar(
            zone_sport,
            x="zone",
            y="value",
            color="activityType",
            title="Zone Distribution per Sport"
        )

        fig_zone.update_layout(
            barmode="stack",
            yaxis_title="% of Weekly Training"
        )

        fig_zone.add_scatter(
            x=zone_labels["zone"],
            y=zone_labels["zone_pct"],
            text=zone_labels["label"],
            mode="text",
            textposition="top center",
            showlegend=False
        )

        st.plotly_chart(fig_zone, use_container_width=True)

# =========================
# 🌍 GLOBAL OVERVIEW
# =========================
st.header("🌍 Global Overview (Weekly Trends)")

overview_metric = st.selectbox(
    "Metric",
    ["duration", "distance_km"],
    key="global_overview_metric"
)

# -------------------------
# LIMIT WEEKS TO REAL DATA
# -------------------------
max_week = int(plan_df["week"].max())

# -------------------------
# COMPLETE GRID (WEEK × SPORT)
# -------------------------
weeks = pd.DataFrame({"week": range(1, max_week + 1)})
sports = pd.DataFrame({"activityType": plan_df["activityType"].unique()})

grid = weeks.merge(sports, how="cross")

# -------------------------
# AGGREGATION
# -------------------------
agg = plan_df.groupby(["week", "activityType"]).agg(
    duration=("duration", "sum"),
    distance_km=("distance_km", "sum")
).reset_index()

agg = grid.merge(agg, on=["week", "activityType"], how="left").fillna(0)

# -------------------------
# METRIC
# -------------------------
if overview_metric == "duration":
    agg["value"] = agg["duration"] / 3600
    y_label = "Training Time"
else:
    agg["value"] = agg["distance_km"]
    y_label = "Distance (km)"

# -------------------------
# PREVIOUS WEEK (USED INTERNALLY ONLY IF NEEDED LATER)
# -------------------------
agg = agg.sort_values(["activityType", "week"])
agg["prev_value"] = agg.groupby("activityType")["value"].shift(1).fillna(0)

# -------------------------
# PLOT (NO TOOLTIP)
# -------------------------
fig = px.line(
    agg,
    x="week",
    y="value",
    color="activityType",
    markers=True,
    labels={
        "week": "Week",
        "value": y_label,
        "activityType": "Sport"
    },
    title=f"Weekly {y_label} Evolution by Sport"
)

fig.update_traces(hoverinfo="skip")

st.plotly_chart(fig, use_container_width=True)