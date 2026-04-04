---
name: notion_search_company
description: 企業データベース（Notion）から企業を検索し、対象企業のPage IDと、現在「空（未入力）」のプロパティのリストを取得します。
---

# Notion Search Company Tool
Use this tool to check if a company already exists in the target Notion Database.
It will return the `page_id` which you will need for any further updates, as well as a list of `empty_properties` that explicitly tell you what information needs to be researched and filled in step 2.

## Usage
Execute the tool via uv inside the agent container.

```bash
uv run tools/notion/company_db.py get --name "{Company Name}"
```

### Options
- `--name`: The name of the company to search for in the database (Required).

### Output
Returns a JSON object with the following structure:
- If company exists (`"exists": true`):
  - `page_id`: The Notion Page ID
  - `empty_properties`: List of properties that are empty and need to be filled
  - `filled_properties`: List of properties that already have values
- If company does not exist (`"exists": false`):
  - `exists`: false
  - `message`: Explanation that the company was not found
  
If the company does not exist, proceed to use `notion_add_company` to create a new entry.
