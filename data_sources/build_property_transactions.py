import csv
import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

RAW_SALES_CANDIDATES = [
    DATA_DIR / "raw" / "nsw_property_sales.csv",
    DATA_DIR / "nsw_property_sales.csv",
    DATA_DIR / "nsw_sales_sample.csv",
]
LISTINGS_FILE = DATA_DIR / "listings.json"
SUBURB_STATS_FILE = DATA_DIR / "suburb_stats.json"
OUTPUT_FILE = OUTPUT_DIR / "property_transactions.json"


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv_rows(path: Path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def first_value(row, candidates):
    for key in candidates:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def to_int(value):
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return int(value)

    cleaned = str(value).strip().replace(",", "").replace("$", "")
    if not cleaned:
        return None
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def to_float(value):
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    cleaned = str(value).strip().replace(",", "").replace("$", "")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def infer_property_type(row):
    explicit = first_value(
        row,
        [
            "property_type",
            "propertyType",
            "dwelling_type",
            "dwellingType",
        ],
    )
    if explicit:
        return str(explicit).strip().lower()

    strata = first_value(row, ["strata", "is_strata"])
    if strata is not None:
        strata_text = str(strata).strip().upper()
        if strata_text in {"1", "Y", "YES", "TRUE"}:
            return "apartment"
        if strata_text in {"0", "N", "NO", "FALSE"}:
            return "house"

    return None


def build_suburb_stats_lookup():
    if not SUBURB_STATS_FILE.exists():
        return {}

    stats = load_json(SUBURB_STATS_FILE)
    lookup = {}
    for row in stats:
        suburb = row.get("suburb")
        if suburb:
            lookup[suburb.strip().lower()] = row
    return lookup


def normalize_sale_rows(rows):
    suburb_lookup = build_suburb_stats_lookup()
    normalized = []

    for row in rows:
        suburb = first_value(row, ["suburb", "locality"])
        sale_price = to_int(first_value(row, ["price", "sale_price", "contract_price"]))

        if not suburb or sale_price is None:
            continue

        source_id = first_value(row, ["propid", "property_id", "OBJECTID", "objectid", "id"])
        address = first_value(
            row,
            ["bp_address", "address", "display_address", "full_address", "property_address"],
        )
        postcode = first_value(row, ["postcode", "post_code"])
        sale_date = first_value(row, ["sale_date", "contract_date", "settlement_date"])
        lat = to_float(first_value(row, ["latitude", "lat", "y"]))
        lon = to_float(first_value(row, ["longitude", "lon", "lng", "x"]))
        suburb_stats = suburb_lookup.get(str(suburb).strip().lower(), {})

        normalized.append(
            {
                "record_type": "sale_transaction",
                "source": "nsw_sales",
                "source_record_id": str(source_id) if source_id is not None else None,
                "listing_url": None,
                "full_address": address,
                "suburb": suburb,
                "postcode": postcode,
                "state": first_value(row, ["state"]) or "NSW",
                "latitude": lat,
                "longitude": lon,
                "property_type": infer_property_type(row),
                "bedrooms": to_int(first_value(row, ["bedrooms", "beds"])),
                "bathrooms": to_int(first_value(row, ["bathrooms", "baths"])),
                "parking_spaces": to_int(first_value(row, ["parking", "parking_spaces", "carspaces"])),
                "land_size_sqm": to_float(first_value(row, ["land_size_sqm", "land_size", "land_area"])),
                "building_size_sqm": to_float(
                    first_value(row, ["building_size_sqm", "building_size", "floor_area"])
                ),
                "sale_price": sale_price,
                "list_price": None,
                "rent_price_weekly": None,
                "sale_date": sale_date,
                "listing_date": None,
                "days_on_market": None,
                "agency_name": first_value(row, ["agency_name", "agency"]),
                "suburb_median_house_price": suburb_stats.get("median_sale_price"),
                "suburb_median_rent_weekly": suburb_stats.get("median_rent_weekly"),
                "suburb_vacancy_rate": suburb_stats.get("vacancy_rate"),
                "raw_record": row,
            }
        )

    return normalized


def normalize_listing_rows(rows):
    suburb_lookup = build_suburb_stats_lookup()
    normalized = []

    for row in rows:
        if row.get("listing_type") != "sale":
            continue

        suburb = row.get("suburb")
        sale_price = to_int(row.get("price"))
        if not suburb or sale_price is None:
            continue

        suburb_stats = suburb_lookup.get(str(suburb).strip().lower(), {})

        normalized.append(
            {
                "record_type": "sale_listing",
                "source": row.get("source") or "listings",
                "source_record_id": row.get("listing_url") or row.get("address"),
                "listing_url": row.get("listing_url"),
                "full_address": row.get("address"),
                "suburb": suburb,
                "postcode": row.get("postcode"),
                "state": row.get("state") or "NSW",
                "latitude": None,
                "longitude": None,
                "property_type": row.get("property_type"),
                "bedrooms": to_int(row.get("bedrooms")),
                "bathrooms": to_int(row.get("bathrooms")),
                "parking_spaces": to_int(row.get("parking")),
                "land_size_sqm": None,
                "building_size_sqm": None,
                "sale_price": sale_price,
                "list_price": sale_price,
                "rent_price_weekly": None,
                "sale_date": None,
                "listing_date": row.get("timestamp"),
                "days_on_market": None,
                "agency_name": None,
                "suburb_median_house_price": suburb_stats.get("median_sale_price"),
                "suburb_median_rent_weekly": suburb_stats.get("median_rent_weekly"),
                "suburb_vacancy_rate": suburb_stats.get("vacancy_rate"),
                "raw_record": row,
            }
        )

    return normalized


def detect_input_path(cli_arg, allow_listing_fallback=False):
    if cli_arg:
        candidate = Path(cli_arg)
        if not candidate.is_absolute():
            candidate = BASE_DIR / candidate
        return candidate if candidate.exists() else None

    for path in RAW_SALES_CANDIDATES:
        if path.exists():
            return path

    if allow_listing_fallback and LISTINGS_FILE.exists():
        return LISTINGS_FILE

    return None


def build_transactions(input_path: Path):
    if input_path.suffix.lower() == ".csv":
        rows = load_csv_rows(input_path)
        normalized = normalize_sale_rows(rows)
        source_mode = "sale_transactions"
    elif input_path.suffix.lower() == ".json":
        rows = load_json(input_path)
        normalized = normalize_listing_rows(rows)
        source_mode = "sale_listings_fallback"
    else:
        raise ValueError(f"Unsupported input format: {input_path.suffix}")

    return {
        "dataset_name": "property_transactions",
        "source_file": str(input_path.relative_to(BASE_DIR)),
        "source_mode": source_mode,
        "record_count": len(normalized),
        "records": normalized,
    }


def main():
    cli_arg = None
    allow_listing_fallback = False

    for arg in sys.argv[1:]:
        if arg == "--allow-listing-fallback":
            allow_listing_fallback = True
        else:
            cli_arg = arg

    input_path = detect_input_path(cli_arg, allow_listing_fallback=allow_listing_fallback)

    if input_path is None:
        print("No real sales input data found.")
        print("Expected one of:")
        for path in RAW_SALES_CANDIDATES:
            print(f"- {path.relative_to(BASE_DIR)}")
        print("You can also pass a custom input path:")
        print("python data_sources/build_property_transactions.py path/to/file.csv")
        print("")
        print("To fetch a real raw file first, run:")
        print("python data_sources/fetch_nsw_property_sales.py")
        print("")
        print("If you really want to use listing fallback, run:")
        print("python data_sources/build_property_transactions.py --allow-listing-fallback")
        return

    payload = build_transactions(input_path)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Saved property transactions to: {OUTPUT_FILE.relative_to(BASE_DIR)}")
    print(f"Source mode: {payload['source_mode']}")
    print(f"Source file: {payload['source_file']}")
    print(f"Record count: {payload['record_count']}")


if __name__ == "__main__":
    main()
