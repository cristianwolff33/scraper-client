# {SOURCE_NAME} Adapter

Adapter for [{SOURCE_URL}]({SOURCE_URL}) — part of the scraper-framework ETL platform.

## What it does

Extracts product data from {SOURCE_NAME} and normalizes it into the canonical `Product` model.

## Quick start

```bash
# From scraper-framework root
uv run python main.py --adapter {source_slug} --export json
```

## Output

| Format | Path |
|--------|------|
| JSON | `output/json/` |
| CSV | `output/csv/` |
| Excel | `output/excel/` |
| Images | `output/images/` |

## Source fields mapped

| Source field | Product field |
|-------------|--------------|
| `id` | `sku` |
| `title` | `name` |
| ... | ... |

## Notes

- {NOTE}
