import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
FEATURES_FILE = OUTPUT_DIR / "property_features_dataset.json"
INTELLIGENCE_FILE = OUTPUT_DIR / "suburb_property_intelligence.json"
SUBURB_STATS_FILE = DATA_DIR / "suburb_stats.json"
OUTPUT_FILE = OUTPUT_DIR / "property_prediction_dataset.json"


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_suburb_lookup(rows):
    lookup = {}
    for row in rows:
        suburb = row.get("suburb")
        if suburb:
            lookup[suburb.strip().lower()] = row
    return lookup


def build_suburb_stats_lookup(rows):
    lookup = {}
    for row in rows:
        suburb = row.get("suburb")
        if suburb:
            lookup[suburb.strip().lower()] = row
    return lookup


def derive_model_fields(record):
    sale_price = record.get("sale_price")
    suburb_price = record.get("suburb_median_house_price")

    price_vs_suburb = None
    if sale_price not in (None, 0) and suburb_price not in (None, 0):
        price_vs_suburb = round(sale_price / suburb_price, 4)

    return {
        "sale_year": record.get("sale_date", "")[:4] if record.get("sale_date") else None,
        "price_vs_suburb_median": price_vs_suburb,
        "has_geo": bool(record.get("latitude") is not None and record.get("longitude") is not None),
        "has_size": bool(
            record.get("land_size_sqm") is not None or record.get("building_size_sqm") is not None
        ),
    }


def build_quality_summary(records):
    total = len(records)
    if total == 0:
        return {
            "record_count": 0,
            "rows_with_sale_price": 0,
            "rows_with_bedrooms": 0,
            "rows_with_size": 0,
            "rows_with_suburb_features": 0,
        }

    def count(predicate):
        return sum(1 for row in records if predicate(row))

    return {
        "record_count": total,
        "rows_with_sale_price": count(lambda row: row.get("sale_price") not in (None, "")),
        "rows_with_bedrooms": count(lambda row: row.get("bedrooms") not in (None, "")),
        "rows_with_size": count(
            lambda row: row.get("land_size_sqm") not in (None, "") or row.get("building_size_sqm") not in (None, "")
        ),
        "rows_with_suburb_features": count(
            lambda row: any(
                row.get(field) not in (None, "")
                for field in (
                    "suburb_wealth_score",
                    "suburb_median_house_price",
                    "suburb_median_rent_weekly",
                    "suburb_vacancy_rate",
                )
            )
        ),
    }


def main():
    if not FEATURES_FILE.exists():
        print("Missing enriched property features dataset.")
        print("Run: python data_sources/enrich_property_features.py")
        return

    features_payload = load_json(FEATURES_FILE)
    intelligence_payload = load_json(INTELLIGENCE_FILE) if INTELLIGENCE_FILE.exists() else []
    suburb_stats_payload = load_json(SUBURB_STATS_FILE) if SUBURB_STATS_FILE.exists() else []
    intelligence_lookup = build_suburb_lookup(intelligence_payload if isinstance(intelligence_payload, list) else [])
    suburb_stats_lookup = build_suburb_stats_lookup(suburb_stats_payload if isinstance(suburb_stats_payload, list) else [])

    prediction_rows = []
    for record in features_payload.get("records", []):
        suburb_key = (record.get("suburb") or "").strip().lower()
        suburb_row = intelligence_lookup.get(suburb_key, {})
        suburb_stats = suburb_stats_lookup.get(suburb_key, {})

        merged = dict(record)
        merged["suburb_wealth_score"] = suburb_row.get("wealth_score")
        merged["suburb_median_income"] = suburb_row.get("median_income")
        merged["suburb_price_income_ratio"] = suburb_row.get("price_income_ratio")
        merged["suburb_investment_signal"] = suburb_row.get("investment_signal")
        merged["matched_wealth_suburb"] = suburb_row.get("matched_wealth_suburb")
        merged["suburb_median_house_price"] = (
            merged.get("suburb_median_house_price") or suburb_stats.get("median_sale_price")
        )
        merged["suburb_median_rent_weekly"] = (
            merged.get("suburb_median_rent_weekly") or suburb_stats.get("median_rent_weekly")
        )
        merged["suburb_vacancy_rate"] = (
            merged.get("suburb_vacancy_rate") or suburb_stats.get("vacancy_rate")
        )
        merged.update(derive_model_fields(merged))
        prediction_rows.append(merged)

    payload = {
        "dataset_name": "property_prediction_dataset",
        "record_count": len(prediction_rows),
        "base_source_mode": features_payload.get("base_source_mode"),
        "has_suburb_intelligence": bool(intelligence_lookup),
        "has_suburb_stats": bool(suburb_stats_lookup),
        "quality_summary": build_quality_summary(prediction_rows),
        "records": prediction_rows,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Saved property prediction dataset to: {OUTPUT_FILE.relative_to(BASE_DIR)}")
    print(f"Record count: {payload['record_count']}")
    print(f"Has suburb intelligence: {payload['has_suburb_intelligence']}")
    print(f"Has suburb stats: {payload['has_suburb_stats']}")
    print(f"Quality summary: {payload['quality_summary']}")


if __name__ == "__main__":
    main()
