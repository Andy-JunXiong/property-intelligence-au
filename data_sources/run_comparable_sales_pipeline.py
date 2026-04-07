from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from data_sources.build_comparable_sales_dataset import main as build_comparable_sales_main


def main():
    print("Step 1/1: Building comparable sales dataset...")
    build_comparable_sales_main()
    print("Done.")


if __name__ == "__main__":
    main()
