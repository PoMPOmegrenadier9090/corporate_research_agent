---
name: notion-episode-get-content
description: 就活エピソードDB（Notion）の個別ページ本文を取得するときに使用します。
---

# Notion Episode Get Content

就活エピソードDBの個別ページ本文を取得します。

## Usage

```bash
uv run -m tools.notion.episode_db get_content --page_id "{PAGE_ID}" --max_depth 3 --page_size 50
```

ページネーションが必要な場合:

```bash
uv run -m tools.notion.episode_db get_content --page_id "{PAGE_ID}" --max_depth 3 --page_size 50 --start_cursor "{NEXT_CURSOR}"
```

## Output
- `plain_text`
- `line_count`
- `has_more`, `next_cursor`
