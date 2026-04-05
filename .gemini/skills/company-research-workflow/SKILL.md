---
name: company-research-workflow
description: "Use when asked to investigate a specific company and update Notion (e.g., 企業調査, financials, culture, tech stack, empty_properties filling). Executes the full company-research workflow end-to-end."
---

# Company Research Workflow

Use this skill when the user requests concrete company research for a named company and expects structured updates in Notion.

## Workflow

### Step 1: Notion State Check & Initialization

1. Run `notion-search-company` first.
2. If the company does not exist, run `notion-add-company`.
3. Collect:
   - `page_id`
   - `empty_properties`
   - `filled_properties`

### Step 2: Information Gathering by Property Type

Collect only what is needed to fill `empty_properties`.

- Financials & Stability (Revenue, FCF, Operating Margin):
  - `ir-fetch`
  - `stock-code-search`
- Corporate Philosophy (Vision, Mission, Values):
  - `corporate-search`
- Culture & Environment (Tech Stack, Engineering Culture, Work-Life Balance):
  - `tech-culture-search` (required for tech-related properties)
- Supplemental extraction from discovered URLs:
  - `fetch-page`

### Step 3: Data Extraction & Normalization

1. Extract objective facts only.
2. Ensure values match the destination property types.
3. For financial indicators, always run `normalize-financials` and store only normalized numeric values.

### Step 4: Notion Update (UPSERT + Append)

1. Use `notion-upsert-company` to update only `empty_properties`.
2. Never modify `filled_properties`.
3. Before append, it's better to compare planned notes with existing body content from `notion-get-content`.
4. Append only new qualitative/quantitative findings with `notion-append-research` in Markdown format.

## Mandatory Rules

1. Data protection:
   - Never overwrite existing Notion values.
2. Financial normalization:
   - Never write raw mixed-unit strings (e.g., 億/兆表記) to numeric fields.
3. Markdown append format:
   - Use `- ` for bullets.
   - Use `1. ` format for ordered lists.
   - Use `**bold**` for key metrics and concepts.
   - Use headings (`#`, `##`, `###`) for structure where needed.
   - Use `> ` for quotes.
4. Secure CLI quoting for append content:
   - When passing Markdown to `--content`, wrap the full string in single quotes (`'...'`) to avoid shell substitution side effects.

## Final Output Contract

Summarize quantitative and qualitative insights to make a comprehensive summary of the company from a job seeker's perspective, including:

1. Updated properties
2. qualitative and quantitative findings in Markdown format