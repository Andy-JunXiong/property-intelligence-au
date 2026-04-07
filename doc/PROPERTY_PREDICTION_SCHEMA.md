# Property Prediction Schema

## Goal

Build a property-level prediction dataset for NSW / Sydney north suburbs.

This is different from the current suburb intelligence layer.

- Current layer: suburb-level signals
- Target layer: individual property-level features for price prediction

## Prediction Targets

Recommended primary target:

- `sale_price`

Recommended secondary targets:

- `estimated_market_value`
- `days_on_market`
- `rent_price_weekly`

## Dataset Grain

One row should represent one property transaction or one listing snapshot.

Preferred row types:

1. `sale_transaction`
2. `sale_listing`
3. `rental_listing`

For the first model, prefer:

- `sale_transaction` rows for training price prediction

## Feature Groups

### 1. Identity

These fields help dedupe and join records.

- `property_id_internal`
- `source`
- `source_record_id`
- `listing_url`
- `full_address`
- `suburb`
- `postcode`
- `state`
- `latitude`
- `longitude`

### 2. Property Core

These are the highest-value prediction features.

- `property_type`
- `bedrooms`
- `bathrooms`
- `parking_spaces`
- `land_size_sqm`
- `building_size_sqm`
- `year_built`
- `lot_number`
- `plan_number`
- `zoning`

### 3. Transaction / Listing

- `record_type`
- `listing_type`
- `sale_price`
- `list_price`
- `rent_price_weekly`
- `sale_date`
- `listing_date`
- `days_on_market`
- `vendor_bid`
- `auction_result`
- `agency_name`

### 4. Temporal Features

These should be derived during feature engineering.

- `sale_year`
- `sale_month`
- `sale_quarter`
- `days_since_last_sale`
- `previous_sale_price`
- `price_growth_since_last_sale`

### 5. Location / Accessibility

- `sa2_name`
- `distance_to_cbd_km`
- `distance_to_station_km`
- `distance_to_metro_km`
- `distance_to_major_road_km`
- `distance_to_nearest_school_km`
- `school_catchment`
- `lga_name`

### 6. Neighborhood / Market

These can come from your current suburb layer.

- `suburb_median_house_price`
- `suburb_median_unit_price`
- `suburb_median_rent_weekly`
- `suburb_vacancy_rate`
- `suburb_sales_count_12m`
- `suburb_wealth_score`
- `suburb_median_income`
- `suburb_price_income_ratio`

### 7. Text / Quality Signals

Optional for later versions.

- `listing_title`
- `listing_description`
- `renovated_flag`
- `water_view_flag`
- `parking_flag`
- `balcony_flag`
- `garden_flag`
- `luxury_flag`

## Minimum Viable Schema

This is the minimum useful feature set for a first prediction model.

- `full_address`
- `suburb`
- `postcode`
- `property_type`
- `bedrooms`
- `bathrooms`
- `parking_spaces`
- `land_size_sqm`
- `building_size_sqm`
- `sale_price`
- `sale_date`
- `latitude`
- `longitude`
- `suburb_median_house_price`
- `suburb_median_rent_weekly`
- `suburb_vacancy_rate`
- `suburb_wealth_score`

## Nice-to-Have Schema

These improve model quality but are not required for v1.

- `year_built`
- `days_on_market`
- `previous_sale_price`
- `price_growth_since_last_sale`
- `distance_to_station_km`
- `distance_to_nearest_school_km`
- `school_catchment`
- `listing_description`

## Current Project Coverage

### Already Available

- `suburb`
- `sale_price` at suburb aggregate level
- `rent_price_weekly` at suburb aggregate level
- `vacancy_rate`
- `suburb_wealth_score`
- `suburb_median_income`

### Partially Available

- `sale_price` at transaction level from NSW sales source
- `sale_date`
- some address-like fields
- some transaction metadata

### Missing or Weak

- `bedrooms`
- `bathrooms`
- `parking_spaces`
- `land_size_sqm`
- `building_size_sqm`
- `latitude`
- `longitude`
- `year_built`
- `days_on_market`
- reliable property-level `property_type`

## Data Source Strategy

### Source A: NSW Sales / Government Transaction Data

Best for:

- `sale_price`
- `sale_date`
- historical transactions
- address / parcel linkage

Weak for:

- room counts
- floor area
- listing quality

### Source B: Listing Detail Pages

Best for:

- `bedrooms`
- `bathrooms`
- `parking_spaces`
- `property_type`
- description text
- marketing attributes

Weak for:

- long historical coverage
- stable IDs

### Source C: Geospatial / School / Transport Enrichment

Best for:

- `distance_to_station_km`
- `distance_to_school_km`
- catchments
- coordinates

## Recommended Build Order

### Phase 1

Build a property transaction base table.

Required outputs:

- `data/output/property_transactions.json`

Fields:

- `full_address`
- `suburb`
- `sale_price`
- `sale_date`
- `property_type` if available

### Phase 2

Enrich with listing detail features.

Required outputs:

- `data/output/property_features_dataset.json`

New fields:

- `bedrooms`
- `bathrooms`
- `parking_spaces`
- `land_size_sqm`
- `building_size_sqm`

### Phase 3

Join suburb intelligence features.

New fields:

- `suburb_wealth_score`
- `suburb_median_income`
- `suburb_vacancy_rate`
- `suburb_median_house_price`

### Phase 4

Train baseline models.

Suggested baselines:

- linear regression
- random forest
- xgboost or lightgbm

## Recommended V1 Priority Fields

If we need to prioritize aggressively, collect these first:

1. `full_address`
2. `suburb`
3. `sale_price`
4. `sale_date`
5. `property_type`
6. `bedrooms`
7. `bathrooms`
8. `parking_spaces`
9. `land_size_sqm`
10. `building_size_sqm`

## Next Implementation Tasks

1. Create `data/property_features_schema.json`
2. Create `data_sources/build_property_transactions.py`
3. Create `data_sources/enrich_property_features.py`
4. Create `data_sources/build_property_prediction_dataset.py`
5. Create `models/train_price_model.py`
