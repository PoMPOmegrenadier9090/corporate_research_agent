---
name: notion-search-company
description: 企業データベース（Notion）から企業を検索し、対象企業のPage ID、候補一致結果、未入力プロパティを取得します。
---

# Notion Search Company Tool
Use this tool to check if a company already exists in the target Notion Database.
It returns the matched page information, including `page_id`, `matches`, `match_count`, `empty_properties`, and `filled_properties`.
If multiple matches are returned, inspect `matches` and choose the intended page before writing.

## Usage
Call MCP tool `notion_search_company`.

```json
{
  "tool": "notion_search_company",
  "arguments": {
    "company_name": "{Company Name}",
    "aliases": ["{Alternative Name 1}", "{Alternative Name 2}"]
  }
}
```

### Options
- `company_name`: The name of the company to search for in the database (Required).
- `aliases`: Optional alternative names, abbreviations, or local-language variants to search in one pass.

### Output
Returns a JSON object with the following structure:
- If company exists (`"exists": true`):
  - `page_id`: The first matched Notion Page ID
  - `query`: The primary query string
  - `query_candidates`: The deduplicated list of query candidates actually searched
  - `match_count`: Number of matched pages
  - `matches`: List of matched pages, each with `page_id` and `title`
  - `empty_properties`: List of properties that are empty and need to be filled
  - `filled_properties`: List of properties that already have values
  - `title_property`: The title property name for the active profile
- If company does not exist (`"exists": false`):
  - `exists`: false
  - `query`: The primary query string
  - `query_candidates`: The deduplicated list of query candidates actually searched
  - `message`: Explanation that the company was not found
  
If the company does not exist, proceed to use `notion_add_company` to create a new entry.
