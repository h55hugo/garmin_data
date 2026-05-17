from process_data import fetch_data, process_data, insert_activities
from strength import strength_data
import sqlite3


def main():

    n_activities = int(input("Number of activities to fetch? "))

    # fetch raw data
    raw_data = fetch_data(n_activities)

    # print(raw_data["startTimeLocal"].head())
    # print(raw_data["startTimeLocal"].dtype)
    # print(raw_data["startTimeLocal"].apply(type).unique())

    # transform raw data into clean data
    activities, zones = process_data(raw_data)

    db_path = "./db/garmin.db"

    # get the number of activities before insert
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM activities")
    count_before = cursor.fetchone()[0]
    conn.close()

    # insert clean data into the db making sure there is not replicate
    insert_activities(activities, zones)

    # get the new number of activities after insert
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM activities")
    count_after = cursor.fetchone()[0]
    

    # print the number of activities added
    added = count_after - count_before
    print(f"Number of new activities added: {added}")

    # for each strength activity, fetch and insert strength data
    strength_activities = activities[
        activities["activityType"] == "strength_training"
    ]

    for activity_id in strength_activities["activityId"]:

        cursor.execute(
            "SELECT COUNT(*) FROM strength WHERE activity_id = ?",
            (activity_id,)
        )

        if cursor.fetchone()[0] == 0:
            strength_data(activity_id)
        else:
            print(f"Skipping {activity_id} (already in DB)")
    
    conn.close()


if __name__ == "__main__":
    main()
