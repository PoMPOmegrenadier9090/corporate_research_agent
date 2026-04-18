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
}


def _normalize_task_properties(properties: dict[str, Any] | None) -> dict[str, Any] | None:
    if not properties:
        return properties

    normalized: dict[str, Any] = {}
    for key, value in properties.items():
        canonical = _TASK_PROPERTY_ALIASES.get(str(key).lower(), key)
        normalized[str(canonical)] = value
    return normalized

def _ensure_task_profile() -> None:
    notion_main.ensure_profile("task")

def action_list_records(
    page_size: int = 50,
    start_cursor: str | None = None,
    title_contains: str | None = None,
):
    _ensure_task_profile()
    return notion_main.action_list_records(
        page_size=page_size,
        start_cursor=start_cursor,
        title_contains=title_contains,
    )


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
