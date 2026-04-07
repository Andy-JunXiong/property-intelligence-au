# Property Intelligence AU

Property Intelligence AU is a local-first property research workspace for the Australian market, with a current focus on Sydney buyer workflows.

The project now has two practical product tracks:

- `Comparable Sales Explorer`
  Uses official NSW sales data as a historical reference layer.
- `Premium Property Case Workspace`
  Lets you analyze one property in depth with manual inputs, uploaded floor plans/photos, and AI-assisted buyer notes.

The original idea of building a broad property price prediction engine was intentionally narrowed. In practice, reliable property-level prediction depends on fresh listing and sold data that is difficult to obtain without stable commercial APIs. This repo therefore focuses on high-signal workflows that are still useful today.

## Current Product Shape

### 1. Comparable Sales Explorer

This is the official historical reference track.

- Data source: NSW Valuation sales data
- Purpose: suburb and address-level historical sold reference
- Output: `data/output/comparable_sales_dataset.json`
- UI route: `/`

### 2. Premium Property Case Workspace

This is the high-touch analysis track for one property at a time.

- Input: address, sold price, bedrooms, bathrooms, parking, orientation, layout notes, inspection notes, transport/school/shop context, photos, floor plan
- Purpose: produce a structured buyer-side property memo
- Data file: `data/property_cases.json`
- UI route: `/premium`

## Project Structure

```text
app/
  app.py                              # local dashboard server

data/
  property_cases.json                 # premium property case records
  property_listing_details_seed.json  # manual detail seed data
  listings.json                       # fallback listing/demo data
  suburb_stats.json                   # suburb-level fallback stats
  raw/
    nsw_property_sales.csv            # official NSW sales raw extract
  output/
    comparable_sales_dataset.json
    property_transactions.json
    property_features_dataset.json
    property_prediction_dataset.json

data_sources/
  fetch_nsw_property_sales.py
  nsw_sales_api.py
  build_comparable_sales_dataset.py
  run_comparable_sales_pipeline.py
  build_property_transactions.py
  enrich_property_features.py
  run_property_prediction_pipeline.py
```

## What Works Today

- Official NSW sales ingestion for targeted suburbs
- Comparable sales dataset build pipeline
- Local dashboard for historical sold reference
- Premium property case UI
- Draft generation from manual case inputs
- AI analysis endpoint with graceful fallback
  If an OpenAI key is configured, the premium analysis can call OpenAI.
  If not, the app falls back to local rule-based analysis so the workflow still works.

## Local Setup

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd property-intelligence-au
```

### 2. Add environment variables

Create a root `.env` file with any keys you want to use.

Example:

```env
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
```

Only `OPENAI_API_KEY` is currently wired into the premium analysis flow.

### 3. Run the official sales pipeline

```bash
python data_sources/fetch_nsw_property_sales.py --mode=house-only
python data_sources/run_comparable_sales_pipeline.py
```

### 4. Start the app

```bash
python app/app.py
```

Open:

- `http://127.0.0.1:8010/`
- `http://127.0.0.1:8010/premium`

## UI Routes

### `/`

Historical comparable sales reference tool.

Use this route to:

- inspect recent sold records
- review suburb-level reference data
- keep an official baseline separate from premium casework

### `/premium`

Single-property premium workspace.

Use this route to:

- build a structured property case
- upload photos and floor plans
- generate a local draft
- run AI analysis
- prepare a buyer-facing memo for one target property

## Recommended Workflow

### Historical reference

1. Refresh NSW sales data
2. Rebuild comparable sales dataset
3. Use `/` to inspect sold context

### Premium property analysis

1. Open `/premium`
2. Fill in the property facts and manual notes
3. Upload property photos and floor plan
4. Click `Generate Draft`
5. Click `Run AI Analysis`
6. Refine the case into a buyer memo

## Product Positioning

This project is best understood as a property research and decision-support tool, not a fully automated valuation engine.

Best-fit use cases:

- historical comparable sales research
- suburb reference and screening
- one-property premium buyer analysis
- manual plus AI-assisted inspection notes

Not yet a strong fit for:

- broad automated AVM-style property valuation
- real-time sold aggregation from commercial portals
- production-grade listing ingestion without licensed APIs

## Limitations

- Official NSW sales data is useful, but not equivalent to commercial portal data
- Domain-style listing and sold freshness is not available without stable access
- Premium AI analysis is only wired to OpenAI today
- The premium workspace is still evolving toward a stronger memo/report experience

## Roadmap

See [ROADMAP.md](/c:/Users/maki8/OneDrive/桌面/Find%20a%20job/property-intelligence-au/ROADMAP.md).

## License

No license has been added yet. Add one before publishing for broader reuse.
