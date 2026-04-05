import json
from pathlib import Path
from typing import Optional, Dict, Any


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "suburb_stats.json"


def load_suburb_stats() -> list[dict]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_suburb_stats(suburb: str, state: str = "NSW") -> Optional[Dict[str, Any]]:
    suburb = suburb.strip().lower()
    state = state.strip().upper()

    records = load_suburb_stats()

    for record in records:
        if (
            record.get("suburb", "").strip().lower() == suburb
            and record.get("state", "").strip().upper() == state
        ):
            return record

    return None


if __name__ == "__main__":
    result = get_suburb_stats("Chatswood", "NSW")
    print(result)