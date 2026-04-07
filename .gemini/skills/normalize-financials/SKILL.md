---
name: normalize-financials
description: "Use when normalizing Japanese financial values into consistent base units for Notion updates, IRBANK parsing, or any workflow that needs 兆/億/万/円 and percentage strings converted into numeric values."
---

# Normalize Financials

Use this skill when a raw financial string must be converted into a consistent numeric value before storing or comparing it.

## What it normalizes

- Amounts such as `1兆2,345億6,789万円` into yen-based floats.
- Values such as `1,234百万円` or `1.2億円` into yen-based floats.
- Percentages such as `12.3%` into decimal ratios like `0.123`.
- Empty or unavailable markers such as `-`, `赤字`, or `N/A` into `null`.

## How to use
Call MCP tool `normalize_financials`.

```json
{
  "tool": "normalize_financials",
  "arguments": {
    "text": "1兆2,345億6,789万円"
  }
}
```

### Example output

```json
{
  "input": "1兆2,345億6,789万円",
  "normalized_value": 1234567890000.0
}
```

## When to apply

- Before writing financial numbers to Notion.
- When combining data from different sources that use different unit conventions.
- When comparing revenue, operating profit, cash flow, or margin values across companies.

## Notes

- The shared parser is implemented in `agent/tools/normalize_financials/parser.py` and reused by IRBANK fetching.
- Keep the normalized value in base units; do not store the original unit string as the canonical field value.