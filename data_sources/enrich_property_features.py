import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
TRANSACTIONS_FILE = OUTPUT_DIR / "property_transactions.json"
LISTINGS_FILE = DATA_DIR / "listings.json"
MERGED_LISTING_DETAILS_FILE = DATA_DIR / "property_listing_details.json"
SUBURB_STATS_FILE = DATA_DIR / "suburb_stats.json"
OUTPUT_FILE = OUTPUT_DIR / "property_features_dataset.json"
TARGETS_FILE = OUTPUT_DIR / "property_enrichment_targets.json"


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


def clean_address(value):
    text = normalize_text(value)
    if not text:
        return None
    text = text.replace(",", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def expand_street_tokens(text):
    if not text:
        return None

    replacements = {
        " rd ": " road ",
        " st ": " street ",
        " ave ": " avenue ",
        " dr ": " drive ",
        " pl ": " place ",
        " ct ": " court ",
        " cres ": " crescent ",
        " pde ": " parade ",
        " hwy ": " highway ",
    }
    expanded = f" {text} "
    for short, long_name in replacements.items():
        expanded = expanded.replace(short, long_name)
    return expanded.strip()


def address_variants(address):
    cleaned = clean_address(address)
    if not cleaned:
        return []

    expanded = expand_street_tokens(cleaned)
    variants = {cleaned, expanded}
    return [value for value in variants if value]


def extract_street_key(address):
    cleaned = expand_street_tokens(clean_address(address))
    if not cleaned:
        return None

    text = re.sub(r"\bnsw\b\s+\d{4}\b", "", cleaned).strip()
    parts = text.split()
    if len(parts) < 2:
        return text

    without_unit = re.sub(r"^\d+[a-z]?/?\d*[a-z]?\s+", "", text)
    without_prefix_number = re.sub(r"^\d+[a-z]?\s+", "", without_unit).strip()
    return without_prefix_number or text


def listing_key(address, suburb):
    suburb_key = normalize_suburb(suburb)
    if not suburb_key:
        return None

    address_key = expand_street_tokens(clean_address(address))
    if not address_key:
        return None
    return f"{address_key}|{suburb_key}"


def build_listing_lookups(listings):
    exact_lookup = {}
    street_lookup = {}

    for row in listings:
        address_value = row.get("address") or row.get("full_address")
        suburb_value = row.get("suburb")
        suburb_key = normalize_suburb(suburb_value)
        if not suburb_key:
            continue

        for variant in address_variants(address_value):
            exact_lookup[f"{variant}|{suburb_key}"] = row

        street_key = extract_street_key(address_value)
        if street_key:
            street_lookup.setdefault(f"{street_key}|{suburb_key}", []).append(row)

    return exact_lookup, street_lookup


def build_suburb_stats_lookup():
    if not SUBURB_STATS_FILE.exists():
        return {}

    stats = load_json(SUBURB_STATS_FILE)
    lookup = {}
    for row in stats:
        suburb = row.get("suburb")
        if suburb:
            lookup[normalize_suburb(suburb)] = row
    return lookup


def derive_flags(listing_row):
    text = " ".join(
        filter(
            None,
            [
                str(listing_row.get("property_type") or ""),
                str(listing_row.get("price_text") or ""),
                str(listing_row.get("address") or listing_row.get("full_address") or ""),
                str(listing_row.get("listing_description") or ""),
                str(listing_row.get("listing_title") or ""),
            ],
        )
    ).lower()

    return {
        "parking_flag": bool(listing_row.get("parking") or listing_row.get("parking_spaces")),
        "balcony_flag": "balcony" in text,
        "garden_flag": "garden" in text or "yard" in text,
        "water_view_flag": "water view" in text or "harbour view" in text,
        "luxury_flag": "luxury" in text or "premium" in text,
        "renovated_flag": "renovated" in text or "updated" in text,
    }


def choose_best_street_match(candidates, record):
    if not candidates:
        return None

    target_price = record.get("sale_price")
    if target_price in (None, 0):
        return candidates[0]

    def score(row):
        price = row.get("price")
        if price in (None, 0):
            return float("inf")
        return abs(float(price) - float(target_price))

    return min(candidates, key=score)


def enrich_records(records, exact_lookup, street_lookup, suburb_stats_lookup):
    enriched = []

    for record in records:
        suburb_key = normalize_suburb(record.get("suburb"))
        match_type = "none"
        listing_row = None

        for variant in address_variants(record.get("full_address")):
            listing_row = exact_lookup.get(f"{variant}|{suburb_key}")
            if listing_row:
                match_type = "address_suburb_exact"
                break

        if listing_row is None:
            street_key = extract_street_key(record.get("full_address"))
            if street_key:
                candidates = street_lookup.get(f"{street_key}|{suburb_key}", [])
                listing_row = choose_best_street_match(candidates, record)
                if listing_row:
                    match_type = "street_suburb"

        suburb_stats = suburb_stats_lookup.get(suburb_key, {})

        combined = dict(record)
        combined["property_id_internal"] = record.get("source_record_id") or listing_key(
            record.get("full_address"), record.get("suburb")
        )
        combined["listing_title"] = None
        combined["listing_description"] = None
        combined["year_built"] = None
        combined["lot_number"] = None
        combined["plan_number"] = None
        combined["zoning"] = None
        combined["feature_match_type"] = match_type
        combined["suburb_median_house_price"] = (
            combined.get("suburb_median_house_price") or suburb_stats.get("median_sale_price")
        )
        combined["suburb_median_rent_weekly"] = (
            combined.get("suburb_median_rent_weekly") or suburb_stats.get("median_rent_weekly")
        )
        combined["suburb_vacancy_rate"] = (
            combined.get("suburb_vacancy_rate") or suburb_stats.get("vacancy_rate")
        )

        if listing_row:
            combined["property_type"] = combined.get("property_type") or listing_row.get("property_type")
            combined["bedrooms"] = combined.get("bedrooms") or listing_row.get("bedrooms")
            combined["bathrooms"] = combined.get("bathrooms") or listing_row.get("bathrooms")
            combined["parking_spaces"] = (
                combined.get("parking_spaces")
                or listing_row.get("parking")
                or listing_row.get("parking_spaces")
            )
            combined["land_size_sqm"] = combined.get("land_size_sqm") or listing_row.get("land_size_sqm")
            combined["building_size_sqm"] = (
                combined.get("building_size_sqm") or listing_row.get("building_size_sqm")
            )
            combined["listing_url"] = combined.get("listing_url") or listing_row.get("listing_url")
            combined["listing_date"] = combined.get("listing_date") or listing_row.get("timestamp")
            combined["listing_title"] = listing_row.get("listing_title")
            combined["listing_description"] = listing_row.get("listing_description")
            combined["agency_name"] = combined.get("agency_name") or listing_row.get("agency_name")
            combined.update(derive_flags(listing_row))
        else:
            combined.update(
                {
                    "parking_flag": bool(combined.get("parking_spaces")),
                    "balcony_flag": False,
                    "garden_flag": False,
                    "water_view_flag": False,
                    "luxury_flag": False,
                    "renovated_flag": False,
                }
            )

        enriched.append(combined)

    return enriched


def build_coverage_summary(records):
    total = len(records)
    if total == 0:
        return {
            "record_count": 0,
            "property_type_coverage": 0.0,
            "bedrooms_coverage": 0.0,
            "bathrooms_coverage": 0.0,
            "parking_coverage": 0.0,
            "land_size_coverage": 0.0,
            "building_size_coverage": 0.0,
            "suburb_stats_coverage": 0.0,
            "exact_match_count": 0,
            "street_match_count": 0,
        }

    def coverage(field):
        filled = sum(1 for row in records if row.get(field) not in (None, ""))
        return round(filled / total, 4)

    return {
        "record_count": total,
        "property_type_coverage": coverage("property_type"),
        "bedrooms_coverage": coverage("bedrooms"),
        "bathrooms_coverage": coverage("bathrooms"),
        "parking_coverage": coverage("parking_spaces"),
        "land_size_coverage": coverage("land_size_sqm"),
        "building_size_coverage": coverage("building_size_sqm"),
        "suburb_stats_coverage": coverage("suburb_median_house_price"),
        "exact_match_count": sum(1 for row in records if row.get("feature_match_type") == "address_suburb_exact"),
        "street_match_count": sum(1 for row in records if row.get("feature_match_type") == "street_suburb"),
    }


def build_targets(records):
    targets = []
    seen = set()

    for row in records:
        if row.get("feature_match_type") != "none":
            continue

        key = (row.get("full_address"), row.get("suburb"))
        if key in seen:
            continue
        seen.add(key)

        targets.append(
            {
                "full_address": row.get("full_address"),
                "suburb": row.get("suburb"),
                "postcode": row.get("postcode"),
                "sale_price": row.get("sale_price"),
                "sale_date": row.get("sale_date"),
                "property_type_hint": row.get("property_type"),
                "raw_source_id": row.get("source_record_id"),
            }
        )

    targets.sort(key=lambda row: (row.get("suburb") or "", -(row.get("sale_price") or 0)))
    return targets


def main():
    if not TRANSACTIONS_FILE.exists():
        print("Missing property transaction base table.")
        print("Run: python data_sources/build_property_transactions.py")
        return

    transactions_payload = load_json(TRANSACTIONS_FILE)
    if MERGED_LISTING_DETAILS_FILE.exists():
        merged_payload = load_json(MERGED_LISTING_DETAILS_FILE)
        listings = merged_payload.get("records", []) if isinstance(merged_payload, dict) else []
    else:
        listings = load_json(LISTINGS_FILE) if LISTINGS_FILE.exists() else []
    suburb_stats_lookup = build_suburb_stats_lookup()

    exact_lookup, street_lookup = build_listing_lookups(listings)
    enriched_records = enrich_records(
        transactions_payload.get("records", []),
        exact_lookup,
        street_lookup,
        suburb_stats_lookup,
    )

    payload = {
        "dataset_name": "property_features_dataset",
        "base_source_file": transactions_payload.get("source_file"),
        "base_source_mode": transactions_payload.get("source_mode"),
        "record_count": len(enriched_records),
        "coverage_summary": build_coverage_summary(enriched_records),
        "records": enriched_records,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    targets_payload = {
        "dataset_name": "property_enrichment_targets",
        "record_count": 0,
        "records": [],
    }
    targets_payload["records"] = build_targets(enriched_records)
    targets_payload["record_count"] = len(targets_payload["records"])

    with open(TARGETS_FILE, "w", encoding="utf-8") as f:
        json.dump(targets_payload, f, ensure_ascii=False, indent=2)

    print(f"Saved enriched property features to: {OUTPUT_FILE.relative_to(BASE_DIR)}")
    print(f"Saved enrichment targets to: {TARGETS_FILE.relative_to(BASE_DIR)}")
    print(f"Record count: {payload['record_count']}")
    print(f"Coverage summary: {payload['coverage_summary']}")
    print(f"Unmatched targets: {targets_payload['record_count']}")


if __name__ == "__main__":
    main()
