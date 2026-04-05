from collectors.domain_collector import search_listings
from analytics.suburb_analysis import get_suburb_stats
from analytics.valuation_model import evaluate_listing


def main():
    suburb = "Burwood"
    state = "NSW"
    listing_type = "sale"
    max_price = 1500000
    min_bedrooms = 2

    listings = search_listings(
        suburb=suburb,
        state=state,
        listing_type=listing_type,
        max_price=max_price,
        min_bedrooms=min_bedrooms
    )

    if not listings:
        print("No listings found.")
        return

    suburb_stats = get_suburb_stats(suburb, state)
    if not suburb_stats:
        print("No suburb stats found.")
        return

    print(f"Suburb stats for {suburb}:")
    print(suburb_stats)
    print("\nListings with valuation:")
    print("=" * 60)

    for item in listings:
        valuation = evaluate_listing(
            suburb_median_price=suburb_stats["median_sale_price"],
            listing_price=item["price"],
            bedrooms=item["bedrooms"],
            property_type=item["property_type"]
        )

        print(f"Address: {item['address']}")
        print(f"Price: {item['price_text']}")
        print(f"Bedrooms: {item['bedrooms']}")
        print(f"Property Type: {item['property_type']}")
        print(f"Estimated Price: ${valuation['estimated_price']}")
        print(f"Classification: {valuation['classification']}")
        print(f"Difference: ${valuation['difference']}")
        print("-" * 60)


if __name__ == "__main__":
    main()