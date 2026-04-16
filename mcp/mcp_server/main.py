import json
import os
from typing import Any

from fastmcp import FastMCP

from tools.fetch_page.main import fetch_page as fetch_page_impl
from tools.IR_fetch.main import fetch_data as ir_fetch_impl
from tools.normalize_financials.parser import parse_financial_value
from tools.stock_code_search.main import search as stock_code_search_impl
from tools.web_search.main import search_web
from tools.notion import company_db, episode_db
from tools.memory import actions as memory_actions


mcp = FastMCP(
    name="agent-tools",
    instructions=(
        "Tools for company research workflow. Use read-only tools first and only use "
        "Notion write tools when explicit updates are requested."
    ),
)


def _as_dict(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    return {"result": result}


@mcp.tool(name="fetch_page", description="Fetch full markdown-like content from URL via JINA AI reader")
def fetch_page(url: str) -> dict[str, Any]:
    return _as_dict(fetch_page_impl(url))


@mcp.tool(name="ir_fetch", description="Fetch latest 5-year financial metrics from IRBANK by stock code")
def ir_fetch(stock_code: str) -> dict[str, Any]:
    return _as_dict(ir_fetch_impl(stock_code))


@mcp.tool(name="web_search", description="Search web using Tavily with optional domain filter")
def web_search_tool(query: str, max_results: int = 3, domains: list[str] | None = None) -> dict[str, Any]:
    normalized_domains = domains or []
    return _as_dict(search_web(query=query, max_results=max_results, domains=normalized_domains))


@mcp.tool(name="normalize_financials", description="Normalize mixed-unit Japanese financial text into numeric value")
def normalize_financials(text: str) -> dict[str, Any]:
    return {
        "input": text,
        "normalized_value": parse_financial_value(text),
    }


@mcp.tool(name="stock_code_search", description="Search JP listed company stock code by company name")
def stock_code_search(queries: list[str]) -> dict[str, Any]:
    results_map = stock_code_search_impl(queries)
    output = [
        {
            "query": q,
            "count": len(res),
            "results": res,
        }
        for q, res in results_map.items()
    ]
    return {"items": output}


@mcp.tool(name="notion_search_company", description="Find company page by title in Notion company DB")
def notion_search_company(company_name: str) -> dict[str, Any]:
    return _as_dict(company_db.action_get(company_name))


@mcp.tool(name="notion_add_company", description="Add a company page into Notion company DB if not exists")
def notion_add_company(company_name: str) -> dict[str, Any]:
    return _as_dict(company_db.action_add_company(company_name))


@mcp.tool(name="notion_upsert_company", description="Update Notion company properties by page id")
def notion_upsert_company(page_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(company_db.action_update_properties(page_id=page_id, updates_json=json.dumps(updates, ensure_ascii=False)))


@mcp.tool(name="notion_get_content", description="Read Notion company page content as plain text")
def notion_get_content(
    page_id: str,
    max_depth: int = 3,
    page_size: int = 50,
    start_cursor: str | None = None,
) -> dict[str, Any]:
    return _as_dict(
        company_db.action_get_content(
            page_id=page_id,
            max_depth=max_depth,
            page_size=page_size,
            start_cursor=start_cursor,
        )
    )


@mcp.tool(name="notion_append_research", description="Append markdown-like notes to Notion company page")
def notion_append_research(page_id: str, content: str) -> dict[str, Any]:
    return _as_dict(company_db.action_append_content(page_id=page_id, content=content))


@mcp.tool(name="notion_episode_list_records", description="List records from Notion episode DB")
def notion_episode_list_records(
    page_size: int = 50,
    start_cursor: str | None = None,
    title_contains: str | None = None,
) -> dict[str, Any]:
    return _as_dict(
        episode_db.action_list_records(
            page_size=page_size,
            start_cursor=start_cursor,
            title_contains=title_contains,
        )
    )


@mcp.tool(name="notion_episode_get_content", description="Read Notion episode page content as plain text")
def notion_episode_get_content(
    page_id: str,
    max_depth: int = 3,
    page_size: int = 50,
    start_cursor: str | None = None,
) -> dict[str, Any]:
    return _as_dict(
        episode_db.action_get_content(
            page_id=page_id,
            max_depth=max_depth,
            page_size=page_size,
            start_cursor=start_cursor,
        )
    )


# ── Long-term Memory Tools ──────────────────────────────────────────

@mcp.tool(
    name="memory_store",
    description=(
        "Store a piece of knowledge in long-term memory. "
        "Use this to remember user preferences, important facts, learnings, or task results "
        "that should persist across sessions. "
        "category must be one of: facts, learnings, task results. "
    ),
)
def memory_store(
    content: str,
    category: str,
    source: str | None = None,
) -> dict[str, Any]:
    return _as_dict(memory_actions.action_store(content=content, category=category, source=source))


@mcp.tool(
    name="memory_search",
    description=(
        "Search long-term memory for knowledge relevant to a query. "
        "Use this before answering questions that may require past context, "
        "user preferences, or previously learned information. "
        "Returns the most semantically similar memories ranked by relevance."
    ),
)
def memory_search(
    query: str,
    n_results: int = 5,
    category: str | None = None,
) -> dict[str, Any]:
    return _as_dict(memory_actions.action_search(query=query, n_results=n_results, category=category))


@mcp.tool(
    name="memory_delete",
    description="Delete a specific memory entry by its ID. Use when a memory is outdated or incorrect.",
)
def memory_delete(memory_id: str) -> dict[str, Any]:
    return _as_dict(memory_actions.action_delete(memory_id=memory_id))


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport == "stdio":
        mcp.run()
    else:
        app = mcp.http_app(
            path=os.getenv("MCP_PATH", "/mcp"),
            transport=transport,
        )

        import uvicorn

        uvicorn.run(
            app,
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=int(os.getenv("MCP_PORT", "9001")),
        )
