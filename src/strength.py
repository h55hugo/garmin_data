import pandas as pd
from garminconnect import Garmin
import sqlite3
from config import EMAIL, PASSWORD


# take an activityId in input. Clean and insert the stregth data for that activityId.

def strength_data(activity_id):
    """Fetch strength data for a Garmin activity and insert it into the strength table."""

    # Connect to Garmin
    client = Garmin(EMAIL, PASSWORD)
    client.login()

    # Get exercise sets (usually a list)
    sets = client.get_activity_exercise_sets(activity_id)

    rows = []

    for s in sets["exerciseSets"]:
        if s.get("setType") == "REST":
            continue

        rows.append({
            "activity_id": activity_id,
            "exercise_name": s["exercises"][0]["name"] if s.get("exercises") else None,
            "reps": s.get("repetitionCount"),
            "duration": s.get("duration")
        })

    if not rows:
        print(f"No strength data found for activity {activity_id}")
        return

    df = pd.DataFrame(rows)

    db_path = "./db/garmin.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO strength (activity_id, exercise_name, reps, duration)
            VALUES (?, ?, ?, ?)
        """, (
            row["activity_id"],
            row["exercise_name"],
            row["reps"],
            row["duration"]
        ))

    conn.commit()
    conn.close()

    print(f"{len(df)} rows inserted for activity {activity_id}")

if __name__ == "__main__":
    activity_id = 22903629287
    strength_data(activity_id)