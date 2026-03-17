# Kelp Target Engine

Strategic partnership target management CLI for Kelp Blue's Stimblue+ commercialisation.

## Setup

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Import existing workbook
python cli.py import-xlsx --file "Strategic_Decision_Matrix.xlsx"

# View summary dashboard
python cli.py summary

# List Tier 1 companies
python cli.py list --tier 1

# Export board-ready workbook
python cli.py export --output "Target_List_Board.xlsx"
```

## Commands

| Command | Description |
|---------|-------------|
| `add` | Add a new company interactively |
| `edit` | Edit an existing company |
| `remove` | Soft-delete a company |
| `list` | List companies with filters |
| `view` | View a single company in detail |
| `search` | Search by name, crop, country, tag |
| `summary` | Dashboard with counts by tier, region, stage |
| `rescore` | Recalculate all scores and tiers |
| `what-if` | Simulate weight changes |
| `audit` | Flag data quality issues |
| `advance` | Move company to next pipeline stage |
| `pipeline` | Pipeline funnel view |
| `history` | Pipeline history for a company |
| `revenue` | Revenue projections with filters |
| `scenario` | Revenue scenario modelling |
| `export` | Export multi-tab Excel workbook |
| `tag` | Add/remove tags |
| `tags` | List all tags with counts |
| `config` | View/update configuration |
| `import-xlsx` | Import from Excel workbook |
| `import-csv` | Bulk import from CSV |
