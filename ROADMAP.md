# Roadmap

## Direction

The roadmap is intentionally centered on two realistic product tracks:

- `Comparable Sales Explorer`
- `Premium Property Case Workspace`

The old broad prediction direction is no longer the primary roadmap. It remains useful as technical research, but not as the main product promise.

## Stage 1: Stabilize The Current Product

Status: `in progress`

Goals:

- polish the premium UI layout and workflow
- make draft generation and AI analysis feel reliable
- keep the historical sales reference route stable

Tasks:

- improve premium page visual hierarchy
- make case queue, intake, detail, and insight sections feel coherent
- improve loading, analyzing, success, and fallback states
- tighten `.env`-based local setup
- document expected data files and routes

## Stage 2: Stronger Premium Case Workflow

Status: `next`

Goals:

- turn one property into a reusable structured case
- move from draft UI to actual case management

Tasks:

- save drafted cases to local JSON
- edit existing cases from the UI
- support uploaded asset persistence to a case folder
- attach floor plan and photo metadata to saved cases
- generate a more report-like AI property memo

## Stage 3: Buyer Memo Output

Status: `planned`

Goals:

- make the premium track exportable and decision-ready

Tasks:

- add a polished memo/report layout
- add summary sections:
  - strengths
  - risks
  - open questions
  - next checks
- export a case as markdown or PDF-ready HTML
- support comparison across 2-3 shortlisted properties

## Stage 4: Enrichment Layer

Status: `planned`

Goals:

- enrich premium cases with structured location context

Tasks:

- station proximity enrichment
- shopping centre proximity enrichment
- school context enrichment
- optional walkability and slope-related context
- nearby sold comparables attached to a case

## Stage 5: LLM Provider Flexibility

Status: `planned`

Goals:

- support multiple AI providers cleanly

Tasks:

- keep OpenAI as the default premium analysis provider
- add Anthropic as an alternative backend
- add provider selection in config or UI
- standardize fallback behavior when keys are missing

## Stage 6: Domain Data Track

Status: `waiting`

Goals:

- evaluate whether licensed Domain access can become a real product input

Tasks:

- wait for access decision
- if approved, design a clean ingestion path
- keep Domain as a premium reference layer, not a fragile scraping dependency

## Stage 7: Historical Sales Track Maturity

Status: `ongoing`

Goals:

- keep the official reference layer useful and lightweight

Tasks:

- improve suburb filters and date windows
- tighten house-only vs all-property-types logic
- add same-street / nearby-street comparable views
- make refresh workflows easier to run

## Backlog: AI 452 Signal Exploration

Status: `backlog`

Goals:

- explore integration of macroeconomic AI insights and automation trends into property intelligence
- research potential to incorporate economic trend indicators and automation-driven market changes into workflows

Tasks:

- monitor developments in AI-driven economic shifts relevant to property markets
- evaluate data sources for economic trend indicators
- prototype integration concepts for automation impact signals in buyer workflows

## Non-Goals For Now

These are intentionally not near-term priorities:

- full AVM-style property valuation engine
- large-scale listing scraping
- production multi-user backend
- complete commercial property portal replacement

## Definition Of Success

The next meaningful success state is:

1. a premium property case can be entered, saved, enriched, and analyzed end-to-end
2. a buyer can use the app to compare a small shortlist of real target homes
3. the historical sales route remains a trustworthy official reference layer