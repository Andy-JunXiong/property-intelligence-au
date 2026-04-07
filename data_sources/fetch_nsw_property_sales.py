import csv
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from data_sources.nsw_sales_api import DEFAULT_TARGET_SUBURBS, RAW_DIR, fetch_sales_rows


OUTPUT_FILE = RAW_DIR / "nsw_property_sales.csv"


def write_csv(rows, output_path: Path):
    if not rows:
        raise ValueError("No sales rows fetched. Nothing to write.")

    fieldnames = sorted({key for row in rows for key in row.keys()})
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_cli():
    args = sys.argv[1:]
    years_back = 8
    mode = "all-property-types"
    suburbs = []

    for arg in args:
        if arg.startswith("--years-back="):
            years_back = int(arg.split("=", 1)[1])
        elif arg.startswith("--mode="):
            mode = arg.split("=", 1)[1]
        else:
            suburbs.append(arg)

    return years_back, mode, suburbs or DEFAULT_TARGET_SUBURBS


def main():
    years_back, mode, suburbs = parse_cli()
    rows = fetch_sales_rows(suburbs=suburbs, years_back=years_back, mode=mode)
    write_csv(rows, OUTPUT_FILE)

    print(f"Saved NSW property sales raw file to: {OUTPUT_FILE.relative_to(BASE_DIR)}")
    print(f"Mode: {mode}")
    print(f"Suburbs covered: {len(suburbs)}")
    print(f"Rows written: {len(rows)}")


if __name__ == "__main__":
    main()
