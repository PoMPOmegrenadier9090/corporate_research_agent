---
name: stock-code-search
description: Search for Japanese stock codes by company name
---

# Stock Code Search

Use this skill to look up the stock code (証券コード) and industry classification of a Japanese listed company.

## When to use

- When you need to find a company's stock code from its name (or part of its name).
- When you need to confirm which industry sector a company belongs to.

## How to use
Call MCP tool `stock_code_search` with one or multiple company names:

```json
{
  "tool": "stock_code_search",
  "arguments": {
    "queries": ["<company1>", "<company2>"]
  }
}
```

### Examples

```json
{
  "tool": "stock_code_search",
  "arguments": {
    "queries": ["トヨタ", "豊田"]
  }
}
```

### Output format

The tool returns `items` as an array containing results for each query:

```json
[
  {
    "query": "トヨタ",
    "count": 1,
    "results": [
      {
        "コード": "7203",
        "銘柄名": "トヨタ自動車",
        "33業種コード": "3700",
        "33業種区分": "輸送用機器"
      }
    ]
  }
]
```

## Notes

- The search is case-insensitive and uses partial matching.
- If no results are found, `count` will be `0` and `results` will be an empty array.
- The data source covers companies listed on the Tokyo Stock Exchange (ETFs and investment trusts are excluded).
