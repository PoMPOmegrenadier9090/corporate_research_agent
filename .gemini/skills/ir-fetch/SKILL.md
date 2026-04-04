---
name: ir-fetch
description: Fetches key financial metrics for the last 5 years from IRBANK based on a company's stock code. Includes sales, operating profit, net profit, margins, ROE, ROA, shareholders' equity ratio (株主資本比率), debt ratio, and cash flows (operating and free). Useful for evaluating financial health, growth, and scale. Returns data in JSON format.
---

# IR Data Scraping Tool

This tool fetches and parses the recent 5 years of financial metrics for a given company from IRBANK.net.

## Context
When you need to analyze a company's financial health, scale, or growth potential, use this tool with the appropriate `stock_code` (which you can get using the `stock_code_search` tool). The parsed data includes exact numbers (float) that you can use to perform comparisons or deep financial analyses.

## Usage

Use the `run_command` tool to execute the script inside the agent container.

```bash
uv run tools/IR_fetch/main.py --code {stock_code}
```

### Example
To fetch the financial data for Toyota (7203):

```bash
uv run tools/IR_fetch/main.py --code 7203
```

### JSON Output
The command returns a JSON object where keys are metric names (e.g., "売上高", "営業利益", "フリーCF", "株主資本比率") and values are dictionaries mapping years (e.g. "2024-03" or "2025-03") to exact numeric floating-point values (e.g., sales in pure yen amount `45095300000000.0` or percentages as decimals `0.1186`).
