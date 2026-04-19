import argparse
import json
import os
import sys
from typing import Any


AGENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if AGENT_DIR not in sys.path:
    sys.path.append(AGENT_DIR)


try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

from tools.notion import task_db


def _parse_json_object(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("JSON must be an object")
    return parsed


def run_list(
    page_size: int,
    title_contains: str | None,
    include_completed: bool,
    area: str | None,
) -> dict[str, Any]:
    return task_db.action_list_records(
        page_size=page_size,
        title_contains=title_contains,
        include_completed=include_completed,
        area=area,
    )


def run_add(title: str, properties_json: str | None) -> dict[str, Any]:
    properties = _parse_json_object(properties_json)
    return task_db.action_add_task(title=title, properties=properties or None)


def run_add_job(title: str, properties_json: str | None) -> dict[str, Any]:
    properties = _parse_json_object(properties_json)
    return task_db.action_add_job_task(title=title, properties=properties or None)


def run_update(page_id: str, properties_json: str) -> dict[str, Any]:
    properties = _parse_json_object(properties_json)
    return task_db.action_update_task(page_id=page_id, properties=properties)


def run_append(page_id: str, content: str) -> dict[str, Any]:
    return task_db.action_append_task_content(page_id=page_id, markdown_content=content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke script for Notion Task DB access")
    subparsers = parser.add_subparsers(dest="action")

    p_list = subparsers.add_parser("list", help="List task records")
    p_list.add_argument("--page_size", type=int, default=20)
    p_list.add_argument("--title_contains", default=None)
    p_list.add_argument("--include_completed", action="store_true", default=False)
    p_list.add_argument("--area", default=None)

    p_add = subparsers.add_parser("add", help="Add a task record")
    p_add.add_argument("--title", required=True)
    p_add.add_argument(
        "--properties",
        default=None,
        help='JSON object, e.g. {"カテゴリ":["就活"],"日付":"2026-04-16"}',
    )

    p_add_job = subparsers.add_parser("add-job", help="Add a job-hunting task record (forces エリア=就活)")
    p_add_job.add_argument("--title", required=True)
    p_add_job.add_argument(
        "--properties",
        default=None,
        help='JSON object, e.g. {"エリア":"研究","カテゴリ":["選考"]}',
    )

    p_update = subparsers.add_parser("update", help="Update task properties")
    p_update.add_argument("--page_id", required=True)
    p_update.add_argument(
        "--properties",
        required=True,
        help='JSON object, e.g. {"ステータス":"進行中"}',
    )

    p_append = subparsers.add_parser("append", help="Append content to task page body")
    p_append.add_argument("--page_id", required=True)
    p_append.add_argument("--content", required=True)

    args = parser.parse_args()

    action = args.action or "list"
    try:
        if action == "list":
            result = run_list(
                page_size=getattr(args, "page_size", 20),
                title_contains=getattr(args, "title_contains", None),
                include_completed=getattr(args, "include_completed", False),
                area=getattr(args, "area", None),
            )
        elif action == "add":
            result = run_add(title=args.title, properties_json=args.properties)
        elif action == "add-job":
            result = run_add_job(title=args.title, properties_json=args.properties)
        elif action == "update":
            result = run_update(page_id=args.page_id, properties_json=args.properties)
        elif action == "append":
            result = run_append(page_id=args.page_id, content=args.content)
        else:
            result = {"error": f"Unsupported action: {action}"}
    except Exception as exc:
        result = {"error": str(exc)}

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if isinstance(result, dict) and result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
