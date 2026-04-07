---
name: notion-append-research
description: 企業データベース（Notion）の対象企業のページ「本文（ブロック）」の末尾に、調査した結果のノートや参照URL（Markdown）を安全に追記します。
---

# Notion Append Research Tool
Use this tool to add long-form research notes, tech stack details, corporate philosophy summaries, or source URLs to the target company's page. This tool explicitly safe-guards existing data because it strictly *appends* to the bottom of the page and never deletes.

## Usage
Call MCP tool `notion_append_research`.

```json
{
	"tool": "notion_append_research",
	"arguments": {
		"page_id": "{PAGE_ID}",
		"content": "【技術スタック】\n- Python\n- React\n\n【出典】\nhttps://example.com"
	}
}
```

### Options
- `page_id`: The target Notion Page ID retrieved from `notion_search_company` (Required).
- `content`: The long-form text or Markdown notes to append (Required). Newlines (`\n`) will be converted to separate text blocks automatically.

### Output
Returns a JSON object indicating success or error.
