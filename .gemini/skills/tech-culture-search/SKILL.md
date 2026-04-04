---
name: tech-culture-search
description: 企業の技術スタック、エンジニアのカルチャー、開発体制などを「技術系ブログ（Zenn, Qiita, Note）」から厳密に抽出するために使用します。
---

# Tech Culture Search Tool
Use this tool when you specifically need to research a company's tech culture and technology stack. By explicitly restricting the domains to Zenn, Qiita, and Note, it ensures highly relevant, engineer-focused information without noise from corporate marketing pages.

## Usage
Execute the web search tool via uv. You **must** provide the `-d` parameter to restrict domains.

```bash
uv run tools/web_search/main.py -d "zenn.dev,qiita.com,note.com" -q "{Company Name} 技術スタック エンジニア" -l 3
```

### Options
- `--query`, `-q`: The search query text (Required).
- `--domains`, `-d`: Comma-separated list of domains to restrict search to. **Must be provided as "zenn.dev,qiita.com,note.com"**.
- `--limit`, `-l`: Maximum number of search results to retrieve (Integer, defaults to 3).

### Output
Returns a JSON object containing the query, search depth, and results (each with title, URL, and text snippet).
