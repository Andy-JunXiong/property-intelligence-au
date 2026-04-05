import json
from pathlib import Path


INPUT_FILE = Path("data/abs_household_income.json")
OUTPUT_FILE = Path("data/suburb_income_decoded.json")


def load_data():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_dimension_maps(data):
    structure = data["structure"]
    dimensions = structure["dimensions"]

    series_dims = dimensions.get("series", [])
    obs_dims = dimensions.get("observation", [])

    series_dim_maps = []
    for dim in series_dims:
        values = dim.get("values", [])
        mapped_values = [
            {
                "id": v.get("id"),
                "name": v.get("name")
            }
            for v in values
        ]
        series_dim_maps.append(
            {
                "id": dim.get("id"),
                "name": dim.get("name"),
                "values": mapped_values
            }
        )

    obs_dim_maps = []
    for dim in obs_dims:
        values = dim.get("values", [])
        mapped_values = [
            {
                "id": v.get("id"),
                "name": v.get("name")
            }
            for v in values
        ]
        obs_dim_maps.append(
            {
                "id": dim.get("id"),
                "name": dim.get("name"),
                "values": mapped_values
            }
        )

    return series_dim_maps, obs_dim_maps


def decode_series_key(series_key, series_dim_maps):
    index_parts = series_key.split(":")
    decoded = {}

    for idx, raw_index in enumerate(index_parts):
        dim_meta = series_dim_maps[idx]
        value_index = int(raw_index)

        if value_index < len(dim_meta["values"]):
            decoded[dim_meta["id"]] = dim_meta["values"][value_index]
        else:
            decoded[dim_meta["id"]] = {"id": None, "name": None}

    return decoded


def decode_observation_key(obs_key, obs_dim_maps):
    index_parts = obs_key.split(":")
    decoded = {}

    for idx, raw_index in enumerate(index_parts):
        dim_meta = obs_dim_maps[idx]
        value_index = int(raw_index)

        if value_index < len(dim_meta["values"]):
            decoded[dim_meta["id"]] = dim_meta["values"][value_index]
        else:
            decoded[dim_meta["id"]] = {"id": None, "name": None}

    return decoded


def main():
    data = load_data()
    series_dim_maps, obs_dim_maps = get_dimension_maps(data)

    dataset = data["dataSets"][0]
    series_data = dataset["series"]

    decoded_rows = []

    for series_key, series_value in series_data.items():
        decoded_series = decode_series_key(series_key, series_dim_maps)
        observations = series_value.get("observations", {})

        for obs_key, obs_value in observations.items():
            decoded_obs = decode_observation_key(obs_key, obs_dim_maps)

            row = {
                "series_key": series_key,
                "observation_key": obs_key,
                "value": obs_value[0] if obs_value else None,
                "decoded_series": decoded_series,
                "decoded_observation": decoded_obs,
            }
            decoded_rows.append(row)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(decoded_rows[:1000], f, ensure_ascii=False, indent=2)

    print(f"Saved first 1000 decoded rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()