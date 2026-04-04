---
name: corporate-search
description: 企業の基本的な情報、事業内容、企業理念（PurposeやMission）、求める人物像などを対象企業から広く検索するために使用します。
---

# Corporate Info Search Tool
Use this tool to gather general information about a company, such as their philosophy, business domains, and recruiting information, using the Tavily search engine.

## Usage
Execute the web search tool via uv. No need to restrict domains because corporate information is spread across various official sites and news domains.

```bash
uv run tools/web_search/main.py -q "{Company Name} 企業理念 OR 求める人物像" -l 3
```

### Options
- `--query`, `-q`: The search query text (Required).
- `--limit`, `-l`: Maximum number of search results to retrieve (Integer, defaults to 3).

### Output
Returns a JSON object containing the query, search depth, and results (each with title, URL, and text snippet).
