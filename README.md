# Lead Qualification Engine

A configurable, two-pass lead qualification and scoring engine.

**Pass 1** scores companies from spreadsheet data using configurable ICP criteria:
- Company size scoring (configurable brackets and weights)
- Industry tiering (A/B/C/Out with configurable point values)
- Keyword signal scanning (pattern matching on company descriptions)
- Disqualifiers and flags (configurable rules)

**Pass 2** enriches top-scoring companies with lightweight web search signals and re-scores.

## Quick Start

```bash
pip install openpyxl
```

1. Create a config file defining your ICP (see `examples/config_example.yaml`)
2. Point the engine at your spreadsheet
3. Run scoring

```bash
python -m lead_engine.score --config your_config.yaml --input leads.xlsx --output scored_leads.xlsx
```

## Project Structure

```
lead_engine/           # Core engine (generic, reusable)
  scorer.py            # Pass 1 scoring logic
  enricher.py          # Pass 2 web enrichment (planned)
  config.py            # Configuration loader
  signals.py           # Keyword signal scanner
  writer.py            # Output writer (xlsx)
examples/              # Example configurations
  config_example.yaml  # Sample ICP config
```

## Configuration

The engine is driven by a YAML config file that defines:
- Size brackets and scoring
- Industry tiers and point values
- Keyword signal categories with terms and weights
- Disqualifiers and flag rules
- Tier thresholds

See `examples/config_example.yaml` for the full schema.
