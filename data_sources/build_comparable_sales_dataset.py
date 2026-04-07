import csv
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_FILE = DATA_DIR / "raw" / "nsw_property_sales.csv"
OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "comparable_sales_dataset.json"


def parse_sale_date(value):
    if value in (None, ""):
        return None

    text = str(value).strip()
    for fmt in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def to_int(value):
    if value in (None, ""):
        return None
    cleaned = str(value).replace(",", "").replace("$", "").strip()
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def median(values):
    if not values:
        return None
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return ordered[mid]
    return int((ordered[mid - 1] + ordered[mid]) / 2)


def load_rows():
    with open(RAW_FILE, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_dataset(rows):
    comparable_rows = []
    suburb_prices = defaultdict(list)
    suburb_rows = defaultdict(list)
    all_dates = []

    for row in rows:
        sale_price = to_int(row.get("price"))
        sale_dt = parse_sale_date(row.get("sale_date"))
        suburb = (row.get("suburb") or "").strip().title()
        address = (row.get("bp_address") or "").strip().title()
        land_size = row.get("area")

        if not suburb or not address or sale_price is None or sale_dt is None:
            continue

        strata_value = str(row.get("strata", "")).strip()
        property_type = "house" if strata_value == "0" else "strata_or_attached"

        comparable = {
            "suburb": suburb,
            "full_address": address,
            "street": (row.get("street") or "").strip().title() or None,
            "postcode": row.get("postcode"),
            "sale_price": sale_price,
            "sale_date": sale_dt.isoformat(),
            "land_size_sqm": float(land_size) if land_size not in (None, "") else None,
            "property_type": property_type,
            "strata": strata_value,
            "deal_props": row.get("deal_props"),
            "source_record_id": row.get("propid"),
            "dealing": row.get("dealing"),
        }

        comparable_rows.append(comparable)
        suburb_prices[suburb].append(sale_price)
        suburb_rows[suburb].append(comparable)
        all_dates.append(sale_dt)

    comparable_rows.sort(key=lambda row: (row["sale_date"], row["sale_price"]), reverse=True)

    suburb_summary = []
    for suburb, prices in suburb_prices.items():
        rows_for_suburb = suburb_rows[suburb]
        rows_for_suburb.sort(key=lambda row: row["sale_date"], reverse=True)
        suburb_summary.append(
            {
                "suburb": suburb,
                "sales_count": len(prices),
                "median_sale_price": median(prices),
                "max_sale_price": max(prices),
                "min_sale_price": min(prices),
                "latest_sale_date": rows_for_suburb[0]["sale_date"],
                "top_sales": rows_for_suburb[:5],
            }
        )

    suburb_summary.sort(key=lambda row: row["median_sale_price"] or 0, reverse=True)

    coverage = {
        "total_sales": len(comparable_rows),
        "suburb_count": len(suburb_summary),
        "date_from": min(all_dates).isoformat() if all_dates else None,
        "date_to": max(all_dates).isoformat() if all_dates else None,
    }

    return {
        "dataset_name": "comparable_sales_dataset",
        "coverage": coverage,
        "suburb_summary": suburb_summary,
        "sales": comparable_rows,
    }


def main():
    if not RAW_FILE.exists():
        print("Missing NSW sales raw file.")
        print("Run: python data_sources/fetch_nsw_property_sales.py")
        return

    rows = load_rows()
    payload = build_dataset(rows)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Saved comparable sales dataset to: {OUTPUT_FILE.relative_to(BASE_DIR)}")
    print(f"Total sales: {payload['coverage']['total_sales']}")
    print(f"Suburbs: {payload['coverage']['suburb_count']}")
    print(f"Date range: {payload['coverage']['date_from']} to {payload['coverage']['date_to']}")


if __name__ == "__main__":
    main()
