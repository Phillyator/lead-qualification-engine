# Lead Qualification Engine

A configurable, two-pass lead qualification and scoring engine.

**Pass 1** scores companies from spreadsheet data using configurable ICP criteria:
- Company size scoring (configurable brackets and weights)
- Industry tiering (A/B/C/Out with configurable point values)
- Keyword signal scanning (pattern matching on company descriptions)
- Disqualifiers and flags (configurable rules)

**Pass 2** enriches top-scoring companies with lightweight web search + LLM signal extraction and re-scores:
- DuckDuckGo search per company (no API key needed)
- Claude LLM extracts structured signals (locations, sentiment, HR initiatives, competitor tools)
- Configurable bonus/penalty rules applied to enrichment signals
- Results written to a new tab with full transparency (snippets, signals, summaries)

## Quick Start

```bash
pip install -r requirements.txt
```

1. Create a config file defining your ICP (see `examples/config_example.yaml`)
2. Point the engine at your spreadsheet

**Pass 1 — Score companies from spreadsheet data:**
```bash
python -m lead_engine --config your_config.yaml --input leads.xlsx
```

**Pass 2 — Enrich top leads with web signals** (requires `ANTHROPIC_API_KEY`):
```bash
python -m lead_engine --mode pass2 --config your_config.yaml --input leads.xlsx
```

## Project Structure

```
lead_engine/           # Core engine (generic, reusable)
  __main__.py          # CLI entry point (--mode pass1/pass2)
  scorer.py            # Pass 1 scoring logic + Pass 1 result reader
  enricher.py          # Pass 2 web enrichment pipeline
  config.py            # Configuration loader and validator
  signals.py           # Keyword signal scanner
  writer.py            # Output writer (xlsx) for both passes
examples/              # Example configurations
  config_example.yaml  # Sample ICP config (Pass 1 + Pass 2)
```

## Configuration

The engine is driven by a YAML config file that defines:
- Size brackets and scoring
- Industry tiers and point values
- Keyword signal categories with terms and weights
- Disqualifiers and flag rules
- Tier thresholds
- **Enrichment** (optional): search query template, LLM model, bonus/penalty rules

See `examples/config_example.yaml` for the full schema.

## Pass 2 Enrichment

The enrichment pipeline runs per company:

```
Company name → DuckDuckGo search → top snippets → Claude extracts signals → bonus/penalty points
```

Extracted signals:
- `num_locations` — number of offices/sites
- `employee_sentiment` — positive/negative/neutral/unknown
- `hr_initiatives` — evidence of HR transformation or people programs
- `competitor_tools` — any employee engagement tools mentioned
- `decentralized` — distributed/multi-region organization

Each signal maps to configurable bonus or penalty points (capped at `bonus_cap`). The enrichment section in the config controls everything — search query, LLM model, delay between searches, and the scoring rules.
