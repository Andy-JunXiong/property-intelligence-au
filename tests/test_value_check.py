from analytics.suburb_analysis import get_suburb_stats
from analytics.valuation_model import evaluate_listing


def main():
    suburb = "Chatswood"
    state = "NSW"
    listing_price = 1750000
    bedrooms = 2
    property_type = "apartment"

    suburb_stats = get_suburb_stats(suburb, state)

    if not suburb_stats:
        print("Suburb stats not found.")
        return

    result = evaluate_listing(
        suburb_median_price=suburb_stats["median_sale_price"],
        listing_price=listing_price,
        bedrooms=bedrooms,
        property_type=property_type
    )

    print("Suburb stats:")
    print(suburb_stats)
    print("\nValuation result:")
    print(result)


if __name__ == "__main__":
    main()