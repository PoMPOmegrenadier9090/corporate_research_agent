---
name: notion-episode-list-records
description: 就活エピソードDB（Notion）のレコード一覧を取得するときに使用します。
---

# Notion Episode List Records

就活エピソードDBのレコード一覧を取得します。

## Usage

```json
{
	"tool": "notion_episode_list_records",
	"arguments": {
		"page_size": 50
	}
}
```

タイトルで絞り込み:

```json
{
	"tool": "notion_episode_list_records",
	"arguments": {
		"page_size": 50,
		"title_contains": "リーダーシップ"
	}
}
```

## Output
- `record_count`
- `records` (array of `{page_id, title}`)
- `has_more`, `next_cursor`
