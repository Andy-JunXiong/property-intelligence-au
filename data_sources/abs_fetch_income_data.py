import json
from pathlib import Path
import requests


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DATASET_ID = "ABS_C16_T21_SA"

ABS_DATA_URL = f"https://api.data.abs.gov.au/data/{DATASET_ID}"


def fetch_dataset_data():

    print("Requesting dataset data from ABS...")

    response = requests.get(
        ABS_DATA_URL,
        headers={"Accept": "application/json"},
        timeout=60
    )

    response.raise_for_status()

    return response.json()


def save_json(data):

    path = DATA_DIR / "abs_household_income.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Saved to:", path)


if __name__ == "__main__":

    data = fetch_dataset_data()

    save_json(data)