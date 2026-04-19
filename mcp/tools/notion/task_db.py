import argparse
import json
import sys
from typing import Any, cast, Optional

from tools.logger import log_action
from tools.notion import main as notion_main

_TASK_PROPERTY_ALIASES: dict[str, str] = {
    "status": "ステータス",
    "category": "カテゴリ",
    "date": "日付",
    "company": "企業",
    "episode": "エピソード",
    "file": "file",
    "area": "エリア",
}

_TASK_STATUS_PROPERTY_NAME = "ステータス"
_TASK_AREA_PROPERTY_NAME = "エリア"
_TASK_COMPLETED_STATUS_NAME = "完了"


def _normalize_task_properties(properties: dict[str, Any] | None) -> dict[str, Any] | None:
    if not properties:
        return properties

    normalized: dict[str, Any] = {}
    for key, value in properties.items():
        canonical = _TASK_PROPERTY_ALIASES.get(str(key).lower(), key)
        normalized[str(canonical)] = value
    return normalized


def _extract_property_option_name(page: dict[str, Any], property_name: str) -> str | None:
    """Notion APIのクエリ結果から，特定のプロパティのオプション名を抽出する。例えば，セレクトやステータスプロパティの選択肢名を取得する際に使用する。"""
    properties = page.get("properties", {})
    if not isinstance(properties, dict):
        return None

    prop = properties.get(property_name)
    if not isinstance(prop, dict):
        return None

    prop_type = str(prop.get("type", ""))
    payload = prop.get(prop_type)
    if not isinstance(payload, dict):
        return None

    name = payload.get("name")
    if name is None:
        return None
    return str(name)


def _build_task_list_filter(
    include_completed: bool,
    area: str | None,
) -> dict[str, Any] | None:
    """Build a Notion API filter for listing tasks based on completion status and area. 
    The conditions are combined with AND."""
    conditions: list[dict[str, Any]] = []

    if not include_completed:
        conditions.append(
            {
                "property": _TASK_STATUS_PROPERTY_NAME,
                "status": {"does_not_equal": _TASK_COMPLETED_STATUS_NAME},
            }
        )

    normalized_area = str(area).strip() if area is not None else ""
    if normalized_area:
        conditions.append(
            {
                "property": _TASK_AREA_PROPERTY_NAME,
                "select": {"equals": normalized_area},
            }
        )

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"and": conditions}

def _ensure_task_profile() -> None:
    notion_main.ensure_profile("task")

def action_list_records(
    page_size: int = 50,
    start_cursor: str | None = None,
    title_contains: str | None = None,
    include_completed: bool = False,
    area: str | None = None,
):
    _ensure_task_profile()
    if page_size <= 0:
        return {"error": "page_size は 1 以上である必要があります。"}

    normalized_area = str(area).strip() if area is not None else ""
    query_filter = _build_task_list_filter(include_completed=include_completed, area=normalized_area or None)

    try:
        datasource_info = notion_main._query_datasource_pages(  # type: ignore[attr-defined]
            page_size=page_size,
            start_cursor=start_cursor,
            filter=query_filter,
        )
    # Notion APIのフィルタの構造が変化した場合に備えた互換処理
    except Exception:
        datasource_info = notion_main._query_datasource_pages(  # type: ignore[attr-defined]
            page_size=page_size,
            start_cursor=start_cursor,
        )

    results = cast(list[dict[str, Any]], datasource_info.get("results", []))
    records: list[dict[str, Any]] = []

    for page in results:
        title = notion_main._extract_page_title(page)  # type: ignore[attr-defined]

        if title_contains and title_contains not in title:
            continue

        status_name = _extract_property_option_name(page, _TASK_STATUS_PROPERTY_NAME)
        if not include_completed and status_name == _TASK_COMPLETED_STATUS_NAME:
            continue

        area_name = _extract_property_option_name(page, _TASK_AREA_PROPERTY_NAME)
        if normalized_area and area_name != normalized_area:
            continue

        records.append(
            {
                "page_id": str(page.get("id", "")),
                "title": title,
            }
        )

    return {
        "status": "success",
        "title_property": notion_main.COMPANY_TITLE_PROPERTY_NAME,
        "record_count": len(records),
        "records": records,
        "has_more": bool(datasource_info.get("has_more", False)),
        "next_cursor": cast(str | None, datasource_info.get("next_cursor")),
    }


def action_get_schema():
    """Get Notion Task DB schema from Notion API."""
    _ensure_task_profile()
    return notion_main.action_get_schema()

def action_add_task(
    title: str,
    properties: dict[str, Any] | None = None,
):
    """Add a new task via notion.main.action_add_record"""
    _ensure_task_profile()
    normalized_properties = _normalize_task_properties(properties)
    return notion_main.action_add_record(
        title=title,
        properties=normalized_properties,
    )


def action_add_job_task(
    title: str,
    properties: dict[str, Any] | None = None,
):
    """Add a new job-hunting task and force エリア=就活."""
    _ensure_task_profile()
    normalized_properties = _normalize_task_properties(properties) or {}
    normalized_properties["エリア"] = "就活"
    return notion_main.action_add_record(
        title=title,
        properties=normalized_properties,
    )

def action_update_task(
    page_id: str,
    properties: dict[str, Any],
):
    """Update an existing task's properties via notion.main.action_update_properties"""
    _ensure_task_profile()
    normalized_properties = _normalize_task_properties(properties)
    return notion_main.action_update_properties(
        page_id=page_id,
        updates_json=json.dumps(normalized_properties),
    )

def action_append_task_content(
    page_id: str,
    markdown_content: str,
):
    """Append content to an existing task via notion.main.action_append_content"""
    _ensure_task_profile()
    return notion_main.action_append_content(
        page_id=page_id,
        content=markdown_content,
    )
