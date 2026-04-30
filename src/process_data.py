import pandas as pd
from garminconnect import Garmin
import sqlite3
from config import EMAIL, PASSWORD


def fetch_data(n_activities=50):
    """Fetch the last raw n_activites available on garmin connect. Return raw data."""

    # Connect to garmin
    client = Garmin(EMAIL, PASSWORD)
    client.login()

    # Download the last activities
    activities = client.get_activities(0, n_activities)

    # Convert to pandas df
    df = pd.DataFrame(activities)

    return df


def process_data(raw_data):
    """Transform raw Garmin data obtained from fetch_data into a DataFrame
    ready to be inserted into garmin.db
    """
    cols_to_keep = [
        "activityId",
        "startTimeLocal",
        "distance",
        "duration",
        "elevationGain",
        "elevationLoss",
        "averageSpeed",
        "maxSpeed",
        "ownerId",
        "averageHR",
        "maxHR",
        "activityType",
        "aerobicTrainingEffect",
        "anaerobicTrainingEffect",
        "deviceId",
        "locationName",
        "moderateIntensityMinutes",
        "vigorousIntensityMinutes",
        "hrTimeInZone_1",
        "hrTimeInZone_2",
        "hrTimeInZone_3",
        "hrTimeInZone_4",
        "hrTimeInZone_5"
    ]

    # Keep only relevant columns and make a copy to avoid warnings
    df = raw_data[cols_to_keep].copy()

    # Add a time and date column
    df["startTimeLocal"] = pd.to_datetime(
        df["startTimeLocal"], errors="coerce")

    df["activity_date"] = df["startTimeLocal"].dt.date.astype(str)
    df["activity_time"] = df["startTimeLocal"].dt.time.astype(str)

    # Drop the original datetime column
    df = df.drop("startTimeLocal", axis=1)

    # Convert units and round
    df.loc[:, "distance_km"] = round(df["distance"] / 1000, 2)
    df.loc[:, "averageSpeed"] = round(df["averageSpeed"] * 3.6, 2)
    df.loc[:, "duration"] = round(df["duration"], 2)
    df.loc[:, "maxSpeed"] = round(df["maxSpeed"], 2)
    df.loc[:, "maxSpeed"] = round(df["maxSpeed"], 2)
    df.loc[:, "aerobicTrainingEffect"] = round(df["aerobicTrainingEffect"], 2)
    df.loc[:, "anaerobicTrainingEffect"] = round(
        df["anaerobicTrainingEffect"], 2)

    # Remove activities with 0 duration
    df = df[df.duration > 0]

    # Drop the original distance column
    df = df.drop("distance", axis=1)

    # Parse the activityType column
    df["activityType"] = df["activityType"].apply(lambda x: x.get("typeKey"))

    # Drop duplicates
    df = df.drop_duplicates()

    # Reorder columns to match database schema
    col_order = [
        "activityId", "activity_date", "activity_time", "distance_km", "duration",
        "elevationGain", "elevationLoss", "averageSpeed", "maxSpeed", "ownerId",
        "averageHR", "maxHR", "activityType", "aerobicTrainingEffect",
        "anaerobicTrainingEffect", "deviceId", "locationName",
        "moderateIntensityMinutes", "vigorousIntensityMinutes"
    ]
    activities = df[col_order]

    zones = df[["activityId", "hrTimeInZone_1", "hrTimeInZone_2", "hrTimeInZone_3",
               "hrTimeInZone_4", "hrTimeInZone_5"]]

    # Pivot from wide to long format
    zones_long = zones.melt(
        id_vars=["activityId"],               # columns to keep as identifiers
        value_vars=["hrTimeInZone_1", "hrTimeInZone_2", "hrTimeInZone_3",
                    "hrTimeInZone_4", "hrTimeInZone_5"],  # columns to unpivot
        var_name="zone",                      # name for the new 'zone' column
        value_name="time_second"              # name for the values
    )

    # Convert zone names from 'hrTimeInZone_1' → 1
    zones_long["zone"] = zones_long["zone"].str.extract("(\d+)").astype(int)

    zones_long["time_second"] = zones_long["time_second"].fillna(0)

    return activities, zones_long


def insert_activities(activities, zones, db_path="./db/garmin.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Insert activities
    for _, row in activities.iterrows():
        cursor.execute(
            """
            INSERT OR IGNORE INTO activities (
                activityId, activity_date, activity_time, distance_km, duration,
                elevationGain, elevationLoss, averageSpeed, maxSpeed, ownerId,
                averageHR, maxHR, activityType, aerobicTrainingEffect,
                anaerobicTrainingEffect, deviceId, locationName,
                moderateIntensityMinutes, vigorousIntensityMinutes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            # tuple(row.values)
            (str(row["activityId"]), *row.values[1:])  # The activityId as TEXT
        )

    # Insert zones
    for _, row in zones.iterrows():
        cursor.execute(
            """
            INSERT OR IGNORE INTO zones (
                activityId, zone, time_second
            )
            VALUES (?, ?, ?)
            """,
            # tuple(row.values)
            (str(row["activityId"]), *row.values[1:])  # The activityId as TEXT
        )

    conn.commit()
    conn.close()
