import json
from pathlib import Path
from typing import Any, Dict

import requests


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# 先用我们 shortlist 里最值得抓的一个
DATASET_ID = "ABS_C16_T21_SA"

# 这个 URL 先做 dataset metadata 测试，不直接抓全部 observation
ABS_DATAFLOW_BASE = "https://api.data.abs.gov.au/dataflow/ABS"


def fetch_dataset_metadata(dataset_id: str) -> Dict[str, Any]:
    url = f"{ABS_DATAFLOW_BASE}/{dataset_id}/latest"
    response = requests.get(
        url,
        headers={"Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def save_json(data: Dict[str, Any], filename: str) -> None:
    output_path = DATA_DIR / filename
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print(f"Fetching metadata for dataset: {DATASET_ID}")
    data = fetch_dataset_metadata(DATASET_ID)
    save_json(data, f"{DATASET_ID.lower()}_metadata.json")
    print(f"Saved to data/{DATASET_ID.lower()}_metadata.json")