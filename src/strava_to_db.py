import requests
import pandas as pd
from datetime import datetime, timedelta

# ------------------------------
# Configuration
# ------------------------------
ACCESS_TOKEN = "1a06ab047f77db53e4f5a72a1afffaf0e79c4739"  # replace with your token
NUM_ACTIVITIES = 100  # number of recent activities to fetch

# Column order
col_order = [
    "activityId", "activity_date", "activity_time", "distance_km", "duration",
    "elevationGain", "elevationLoss", "averageSpeed", "maxSpeed", "ownerId",
    "averageHR", "maxHR", "sportTypeId", "aerobicTrainingEffect",
    "anaerobicTrainingEffect", "deviceId", "locationName",
    "moderateIntensityMinutes", "vigorousIntensityMinutes",
    "hrTimeInZone_1", "hrTimeInZone_2", "hrTimeInZone_3",
    "hrTimeInZone_4", "hrTimeInZone_5"
]

# ------------------------------
# Fetch activities from Strava
# ------------------------------
url = "https://www.strava.com/api/v3/athlete/activities"
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
params = {"per_page": NUM_ACTIVITIES}

response = requests.get(url, headers=headers, params=params)
activities = response.json()

print(activities)
