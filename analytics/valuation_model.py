from typing import Dict, Optional


BEDROOM_FACTORS = {
    1: 0.70,
    2: 1.00,
    3: 1.35,
    4: 1.70,
    5: 2.00,
}

PROPERTY_TYPE_FACTORS = {
    "studio": 0.65,
    "apartment": 1.00,
    "unit": 0.95,
    "townhouse": 1.15,
    "house": 1.30,
}


def get_bedroom_factor(bedrooms: int) -> float:
    """
    Return a rough multiplier based on bedroom count.
    """
    if bedrooms in BEDROOM_FACTORS:
        return BEDROOM_FACTORS[bedrooms]

    if bedrooms <= 1:
        return 0.70

    return 2.20


def get_property_type_factor(property_type: str) -> float:
    """
    Return a rough multiplier based on property type.
    """
    if not property_type:
        return 1.00

    return PROPERTY_TYPE_FACTORS.get(property_type.lower(), 1.00)


def estimate_property_price(
    suburb_median_price: float,
    bedrooms: int,
    property_type: str
) -> float:
    """
    Estimate a rough property price using suburb median price
    and simple adjustment factors.
    """
    bedroom_factor = get_bedroom_factor(bedrooms)
    property_type_factor = get_property_type_factor(property_type)

    estimated_price = suburb_median_price * bedroom_factor * property_type_factor
    return round(estimated_price, 2)


def classify_price(
    listing_price: float,
    estimated_price: float
) -> str:
    """
    Classify listing price relative to estimated fair price.
    """
    if estimated_price <= 0:
        return "unknown"

    ratio = listing_price / estimated_price

    if ratio < 0.90:
        return "underpriced"
    elif ratio > 1.10:
        return "overpriced"
    return "fair"


def evaluate_listing(
    suburb_median_price: float,
    listing_price: float,
    bedrooms: int,
    property_type: str
) -> Dict[str, Optional[float]]:
    """
    Return valuation result for a single listing.
    """
    estimated_price = estimate_property_price(
        suburb_median_price=suburb_median_price,
        bedrooms=bedrooms,
        property_type=property_type
    )

    classification = classify_price(
        listing_price=listing_price,
        estimated_price=estimated_price
    )

    difference = round(listing_price - estimated_price, 2)

    return {
        "estimated_price": estimated_price,
        "listing_price": listing_price,
        "difference": difference,
        "classification": classification,
    }


if __name__ == "__main__":
    sample_result = evaluate_listing(
        suburb_median_price=1200000,
        listing_price=1150000,
        bedrooms=2,
        property_type="apartment"
    )

    print("Valuation result:")
    print(sample_result)