import sqlite3

conn = sqlite3.connect("garmin.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS strength (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER,
    exercise_name TEXT,
    reps INTEGER,
    duration REAL
)
""")

conn.commit()
conn.close()