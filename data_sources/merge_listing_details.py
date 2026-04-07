import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SEED_FILE = DATA_DIR / "property_listing_details_seed.json"
LISTINGS_FILE = DATA_DIR / "listings.json"
OUTPUT_FILE = DATA_DIR / "property_listing_details.json"


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(value):
    if value is None:
        return None
    return " ".join(str(value).strip().lower().split())


def normalize_suburb(value):
    normalized = normalize_text(value)
    return normalized.upper() if normalized else None


def normalize_address(value):
    text = normalize_text(value)
    if not text:
        return None
    text = text.replace(",", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text.upper()


def make_key(address, suburb):
    normalized_address = normalize_address(address)
    normalized_suburb = normalize_suburb(suburb)
    if not normalized_address or not normalized_suburb:
        return None
    return f"{normalized_address}|{normalized_suburb}"


def convert_listing_row(row):
    return {
        "full_address": row.get("address"),
        "suburb": row.get("suburb"),
        "property_type": row.get("property_type"),
        "bedrooms": row.get("bedrooms"),
        "bathrooms": row.get("bathrooms"),
        "parking_spaces": row.get("parking"),
        "land_size_sqm": None,
        "building_size_sqm": None,
        "listing_url": row.get("listing_url"),
        "listing_date": row.get("timestamp"),
        "listing_title": None,
        "listing_description": None,
        "agency_name": None,
        "source": row.get("source") or "listings_json",
        "notes": None,
    }


def main():
    seed_payload = load_json(SEED_FILE) if SEED_FILE.exists() else {"records": []}
    listings_payload = load_json(LISTINGS_FILE) if LISTINGS_FILE.exists() else []

    merged = {}

    for row in listings_payload:
        key = make_key(row.get("address"), row.get("suburb"))
        if not key:
            continue
        merged[key] = convert_listing_row(row)

    for row in seed_payload.get("records", []):
        key = make_key(row.get("full_address"), row.get("suburb"))
        if not key:
            continue
        merged[key] = dict(row)

    payload = {
        "dataset_name": "property_listing_details",
        "record_count": len(merged),
        "records": list(merged.values()),
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Saved merged listing details to: {OUTPUT_FILE.relative_to(BASE_DIR)}")
    print(f"Record count: {payload['record_count']}")


if __name__ == "__main__":
    main()
