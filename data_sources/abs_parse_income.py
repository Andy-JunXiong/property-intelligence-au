import json
from pathlib import Path

INPUT_FILE = Path("data/abs_household_income.json")
OUTPUT_FILE = Path("data/suburb_income_raw.json")


def load_data():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_series(data):

    datasets = data["dataSets"][0]
    series = datasets["series"]

    results = []

    for key, value in series.items():

        observations = value.get("observations", {})

        for obs_key, obs_val in observations.items():

            count = obs_val[0]

            results.append({
                "series_key": key,
                "value": count
            })

    return results


def save_output(rows):

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":

    data = load_data()

    rows = extract_series(data)

    save_output(rows)