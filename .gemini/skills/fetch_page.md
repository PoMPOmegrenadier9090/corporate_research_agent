---
name: fetch_page
description: 指定されたURLのウェブページにアクセスし、JINA AI リーダー APIを経由して不要な要素を省いた綺麗なマークダウンテキスト（コンテンツ本文）を取得します。
---

# Fetch Page Tool (JINA AI Reader)
Use this tool to read the deep contents of a specific web page. 
When `corporate_search` or `tech_culture_search` returns interesting links but the short snippet is not enough, use this tool with the URL to extract the full readable text of that specific page in an LLM-friendly markdown format.

## Usage
Execute the fetch tool via uv. 

```bash
uv run tools/fetch_page/main.py -u "{URL}"
```

### Options
- `--url`, `-u`: The URL of the web page you want to read (Required).

### Output
Returns a JSON object containing the `title`, `url`, and main `content` (in markdown format).
