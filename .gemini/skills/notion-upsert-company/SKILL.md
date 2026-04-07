---
name: notion-upsert-company
description: 企業データベース（Notion）の特定の企業のプロパティ（列データ）を安全に更新します。（上書きを防ぐため、事前に empty_properties に分類されているものだけを更新してください）
---

# Notion Upsert Company Tool
Use this tool to update the database properties of a specific company. You must provide the exact Page ID obtained from `notion_search_company`. 

## Safety Rule
Only update the information that was returned in the `empty_properties` list during your search. Do not pass properties that are already filled.

## Valid Properties
- Number type: `FCF`, `営業利益率`, `売上高`
- Select type: `志望度`, `業界`
- Multi-select type: `タグ`, `業種` (Pass as a comma-separated string, e.g. "IT,通信")
- Status type: `応募状況`

## Usage
Call MCP tool `notion_upsert_company`.

```json
{
	"tool": "notion_upsert_company",
	"arguments": {
		"page_id": "{PAGE_ID}",
		"updates": {
			"売上高": 10000,
			"業種": "IT,ソフトウェア"
		}
	}
}
```

### Options
- `page_id`: The target Notion Page ID (Required).
- `updates`: A JSON object containing key-value pairs of properties to update (Required).

### Output
Returns a JSON object indicating success or error.
