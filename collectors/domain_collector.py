import json
from pathlib import Path
from typing import List, Dict, Any, Optional


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "listings.json"


def load_listings() -> List[Dict[str, Any]]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def search_listings(
    suburb: Optional[str] = None,
    state: str = "NSW",
    listing_type: Optional[str] = None,
    max_price: Optional[float] = None,
    min_bedrooms: Optional[int] = None
) -> List[Dict[str, Any]]:
    listings = load_listings()
    results = []

    for listing in listings:
        if suburb and listing.get("suburb", "").strip().lower() != suburb.strip().lower():
            continue

        if state and listing.get("state", "").strip().upper() != state.strip().upper():
            continue

        if listing_type and listing.get("listing_type", "").strip().lower() != listing_type.strip().lower():
            continue

        if max_price is not None and float(listing.get("price", 0)) > max_price:
            continue

        if min_bedrooms is not None and int(listing.get("bedrooms", 0)) < min_bedrooms:
            continue

        results.append(listing)

    return results


if __name__ == "__main__":
    sample_results = search_listings(
        suburb="Chatswood",
        state="NSW",
        listing_type="rent",
        max_price=1000,
        min_bedrooms=2
    )

    print("Search results:")
    for item in sample_results:
        print(item)