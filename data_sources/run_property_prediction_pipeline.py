from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from data_sources.build_property_transactions import main as build_transactions_main
from data_sources.merge_listing_details import main as merge_listing_details_main
from data_sources.enrich_property_features import main as enrich_features_main
from data_sources.build_property_prediction_dataset import main as build_prediction_main


RAW_SALES_FILE = BASE_DIR / "data" / "raw" / "nsw_property_sales.csv"


def main():
    if not RAW_SALES_FILE.exists():
        print("Missing real NSW sales raw file:")
        print(f"- {RAW_SALES_FILE.relative_to(BASE_DIR)}")
        print("Fetch it first with:")
        print("python data_sources/fetch_nsw_property_sales.py")
        return

    print("Step 1/3: Building property transaction base table...")
    build_transactions_main()

    print("Step 2/4: Merging listing detail sources...")
    merge_listing_details_main()

    print("Step 3/4: Enriching property features...")
    enrich_features_main()

    print("Step 4/4: Building property prediction dataset...")
    build_prediction_main()

    print("Done.")


if __name__ == "__main__":
    main()
