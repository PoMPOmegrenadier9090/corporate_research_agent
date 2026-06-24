---
name: ir-fetch
description: Fetches key financial metrics for up to the last 2 years from J-Quants API (JPX official) based on a company's stock code. Includes sales, operating profit, net profit, margins, ROE, ROA, shareholders' equity ratio (株主資本比率), and cash flows (operating and free). Useful for evaluating financial health, growth, and scale. Returns data in JSON format.
---

# IR Data Fetch Tool

This tool fetches recent annual financial metrics for a given company via the J-Quants API (JPX official data). Data covers up to the last 2 fiscal years. Consolidated figures are preferred over non-consolidated when available.

## Context
When you need to analyze a company's financial health, scale, or growth potential, use this tool with the appropriate `stock_code` (which you can get using the `stock_code_search` tool). The parsed data includes exact numbers (float) that you can use to perform comparisons or deep financial analyses.

## Usage
Call MCP tool `ir_fetch` with `stock_code`.

```json
{
	"tool": "ir_fetch",
	"arguments": {
		"stock_code": "7203"
	}
}
```

### Example output (Toyota 7203)
```json
{
  "売上高":     {"2024-03": 45095325000000, "2025-03": 48036704000000},
  "営業利益":   {"2024-03":  5352934000000, "2025-03":  4795586000000},
  "当期純利益": {"2024-03":  4944933000000, "2025-03":  4765086000000},
  "営業利益率": {"2024-03": 11.87,          "2025-03":  9.98},
  "ROE":        {"2024-03": 14.03,          "2025-03": 12.92},
  "ROA":        {"2024-03":  5.49,          "2025-03":  5.09},
  "株主資本比率":{"2024-03": 38.0,           "2025-03": 38.4},
  "営業CF":     {"2024-03":  4206373000000, "2025-03":  3696934000000},
  "フリーCF":   {"2024-03":  -792378000000, "2025-03":  -492802000000}
}
```

売上高・営業利益・当期純利益・営業CF・フリーCF の単位は円。営業利益率・ROE・ROA・株主資本比率はパーセント（例: `11.87` = 11.87%）。
