from process_data import fetch_data, process_data, insert_activities
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
    conn.close()

    # print the number of activities added
    added = count_after - count_before
    print(f"Number of new activities added: {added}")


if __name__ == "__main__":
    main()
