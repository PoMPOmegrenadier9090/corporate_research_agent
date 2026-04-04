---
name: notion-add-company
description: 企業データベース（Notion）を検索して、対象企業が存在しなかった場合に、新しい企業の空ページを作成します。
---

# Notion Add Company Tool
Use this tool only when `notion_search_company` returns `"exists": false`, indicating the company does not exist in the database. This tool will initialize a new blank company record in the database, allowing you to proceed with updating its properties and appending content.
## Usage
Execute the tool via uv inside the agent container.

```bash
uv run tools/notion/company_db.py add_company --name "{Company Name}"
```

### Options
- `--name`: The name of the new company to add to the DB (Required).

### Output
Returns a JSON object containing:
- `status`: Either `"success"` (newly created) or `"skipped"` (company already exists)
- `message`: Description of the action taken
- `page_id`: The Notion Page ID for the company, which you can then use with the upsert and append tools
