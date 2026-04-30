import os
import sqlite3
import pandas as pd


def export_dashboard_csv(db_path,
                         start_date="2026-05-11",
                         end_date="2050-12-31",
                         output_folder="./csv/Lausanne_Triathlon_2026"):

    # =========================
    # SQL QUERY
    # =========================
    query = """
    SELECT
        a.*,

        z.zone1,
        z.zone2,
        z.zone3,
        z.zone4,
        z.zone5

    FROM (
        SELECT *
        FROM activities
        WHERE activity_date >= ?
          AND activity_date <  ?
    ) a

    LEFT JOIN (
        SELECT
            CAST(activityId AS INTEGER) AS activityId,

            SUM(CASE WHEN zone = 1 THEN time_second ELSE 0 END) AS zone1,
            SUM(CASE WHEN zone = 2 THEN time_second ELSE 0 END) AS zone2,
            SUM(CASE WHEN zone = 3 THEN time_second ELSE 0 END) AS zone3,
            SUM(CASE WHEN zone = 4 THEN time_second ELSE 0 END) AS zone4,
            SUM(CASE WHEN zone = 5 THEN time_second ELSE 0 END) AS zone5

        FROM zones
        GROUP BY CAST(activityId AS INTEGER)
    ) z
    ON a.activityId = z.activityId
    ORDER BY a.activity_date ASC;
    """

    # =========================
    # LOAD DATA FROM SQLITE
    # =========================
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    conn.close()

    # =========================
    # CREATE OUTPUT FOLDER
    # =========================
    os.makedirs(output_folder, exist_ok=True)

    # =========================
    # WRITE MAIN CSV (OVERWRITE)
    # =========================
    output_path = os.path.join(output_folder, "main.csv")
    df.to_csv(output_path, index=False)

    print(f"✅ Dashboard updated: {output_path}")

    return df


# =========================
# RUN SCRIPT
# =========================
if __name__ == "__main__":

    df = export_dashboard_csv(
        db_path="./db/garmin.db",
        start_date="2026-01-01",
        end_date="2026-04-01"
    )

    print(f"Rows exported: {len(df)}")