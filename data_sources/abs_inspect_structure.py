import json
from pathlib import Path


INPUT_FILE = Path("data/abs_household_income.json")


def load_data():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    data = load_data()

    print("Top-level keys:")
    for key in data.keys():
        print("-", key)

    print("\nStructure keys:")
    structure = data.get("structure", {})
    for key in structure.keys():
        print("-", key)

    print("\nDimensions:")
    dimensions = structure.get("dimensions", {})
    for dim_type, dim_list in dimensions.items():
        print(f"\n[{dim_type}]")
        for idx, dim in enumerate(dim_list):
            print(f"  {idx}: id={dim.get('id')} name={dim.get('name')}")
            values = dim.get("values", [])
            print(f"     number of values: {len(values)}")
            for i, val in enumerate(values[:5]):
                print(f"       {i}: id={val.get('id')} name={val.get('name')}")

    print("\nAttributes:")
    attributes = structure.get("attributes", {})
    for attr_type, attr_list in attributes.items():
        print(f"\n[{attr_type}]")
        for idx, attr in enumerate(attr_list):
            print(f"  {idx}: id={attr.get('id')} name={attr.get('name')}")


if __name__ == "__main__":
    main()