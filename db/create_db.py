import sqlite3
import os


def create_db(db_name="garmin.db"):
    """Create a SQlite database with a table for garmin activities."""

    db_folder = "db"
    db_path = os.path.join(db_folder, db_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS activities (
        activityId TEXT NOT NULL UNIQUE,
        activity_date TEXT,
        activity_time TEXT,
        distance_km REAL,
        duration REAL,
        elevationGain REAL,
        elevationLoss REAL,
        averageSpeed REAL,
        maxSpeed REAL,
        ownerId INTEGER,
        averageHR REAL,
        maxHR REAL,
        activityType TEXT,
        aerobicTrainingEffect REAL,
        anaerobicTrainingEffect REAL,
        deviceId INTEGER,
        locationName TEXT,
        moderateIntensityMinutes REAL,
        vigorousIntensityMinutes REAL
    )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS zones (
        activityId TEXT,
        zone INT,
        time_second INT,
        FOREIGN KEY (activityId) REFERENCES activities(activityId)
    )
    """
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_db()
    print("Database created successfully!")
