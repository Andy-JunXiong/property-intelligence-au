import json
from pathlib import Path
from typing import Any, Dict


INPUT_PATH = Path("data/abs_c16_t21_sa_metadata.json")


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_top_level_keys(data: Dict[str, Any]) -> None:
    print("Top-level keys:")
    for key in data.keys():
        print("-", key)


if __name__ == "__main__":
    data = load_json(INPUT_PATH)
    print_top_level_keys(data)