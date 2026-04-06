---
name: notion-get-content
description: Notionページ本文を取得し、plain_textとして読む必要があるときに使用します。既存メモの重複追記回避や、過去の調査内容の再確認時に使います。
---

# Notion Get Content Tool

Use this tool to fetch the page body content from Notion as plain text.

This skill is useful when:
- You need to inspect existing page notes before appending new content.
- You want to avoid duplicate qualitative summaries.
- You need to continue research based on previously appended notes.

## Usage
Call MCP tool `notion_get_content`.

```json
{
	"tool": "notion_get_content",
	"arguments": {
		"page_id": "{PAGE_ID}",
		"max_depth": 3,
		"page_size": 50
	}
}
```

For pagination (top-level blocks), pass `start_cursor` from the previous response.

```json
{
	"tool": "notion_get_content",
	"arguments": {
		"page_id": "{PAGE_ID}",
		"max_depth": 3,
		"page_size": 50,
		"start_cursor": "{NEXT_CURSOR}"
	}
}
```

### Options
- `page_id`: Target Notion page ID (Required)
- `max_depth`: Max child traversal depth (Optional, default: 3)
- `page_size`: Top-level block page size (Optional, default: 50)
- `start_cursor`: Cursor for top-level pagination (Optional)

### Output
Returns a JSON object including:
- `status`: `success` or `error`
- `plain_text`: Extracted page content as plain text
- `has_more`: Whether more top-level blocks exist
- `next_cursor`: Cursor for the next page (if `has_more` is true)
- `line_count`: Number of extracted lines

If `has_more` is true and more context is required, call the tool again with `next_cursor`.