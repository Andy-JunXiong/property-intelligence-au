from collectors.domain_collector import search_listings


def main():
    results = search_listings(
        suburb="Parramatta",
        state="NSW",
        listing_type="sale",
        max_price=1000000,
        min_bedrooms=2
    )

    print("Listing search results:")
    print(f"Total matched: {len(results)}")

    for item in results:
        print("-" * 50)
        print(f"Address: {item['address']}")
        print(f"Suburb: {item['suburb']}, {item['state']} {item['postcode']}")
        print(f"Type: {item['listing_type']}")
        print(f"Price: {item['price_text']}")
        print(f"Bedrooms: {item['bedrooms']}")
        print(f"Bathrooms: {item['bathrooms']}")
        print(f"Parking: {item['parking']}")
        print(f"Property Type: {item['property_type']}")
        print(f"URL: {item['listing_url']}")


if __name__ == "__main__":
    main()