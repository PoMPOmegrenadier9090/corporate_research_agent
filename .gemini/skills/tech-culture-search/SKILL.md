---
name: tech-culture-search
description: 企業の技術スタック、エンジニアのカルチャー、開発体制などを「技術系ブログ（Zenn, Qiita, Note）」から厳密に抽出するために使用します。
---

# Tech Culture Search Tool
Use this tool when you specifically need to research a company's tech culture and technology stack. By explicitly restricting the domains to Zenn, Qiita, and Note, it ensures highly relevant, engineer-focused information without noise from corporate marketing pages.

## Usage
Call MCP tool `web_search`. You **must** provide `domains` to restrict the search.

```json
{
	"tool": "web_search",
	"arguments": {
		"query": "{Company Name} 技術スタック エンジニア",
		"domains": ["zenn.dev", "qiita.com", "note.com"],
		"max_results": 3
	}
}
```

### Options
- `query`: The search query text (Required).
- `domains`: Domain array to restrict search. **Must include `zenn.dev`, `qiita.com`, and `note.com`**.
- `max_results`: Maximum number of search results to retrieve (Integer, defaults to 3).

### Output
Returns a JSON object containing the query, search depth, and results (each with title, URL, and text snippet).
