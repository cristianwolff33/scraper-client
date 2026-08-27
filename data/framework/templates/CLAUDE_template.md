# CLAUDE.md — {SOURCE_NAME} Adapter

## Source Overview
- **URL**: {SOURCE_URL}
- **Mode**: {REQUESTS | PLAYWRIGHT | API | XML | CSV}
- **Authentication**: {none | basic | token | cookie}
- **Pagination**: {page param | cursor | next link | infinite scroll}

## Adapter Location
```
adapters/{source_slug}/
  adapter.py       ← extract only
  transformer.py   ← normalize to Product
  validator.py     ← custom rules (optional)
  README.md
```

## ETL Pipeline
This adapter feeds into the shared framework pipeline:
```
adapter.extract() → transformer.transform() → validator.validate() → exporter.export() → downloader
```

## Source-Specific Notes
- {NOTE: any quirks, anti-bot measures, rate limits}
- {NOTE: pagination behavior}
- {NOTE: image URL patterns}

## Known Limitations
- {LIMITATION 1}

## Testing
```bash
uv run pytest tests/test_{source_slug}.py -v
```
