import argparse
import json
import sys
from typing import Any, cast

from tools.logger import log_action
from tools.notion import main as notion_main


def _ensure_episode_profile() -> None:
    notion_main.ensure_profile("episode")


def action_list_records(
    page_size: int = 50,
    start_cursor: str | None = None,
    title_contains: str | None = None,
):
    _ensure_episode_profile()
    return notion_main.action_list_records(
        page_size=page_size,
        start_cursor=start_cursor,
        title_contains=title_contains,
    )


def action_get_content(
    page_id: str,
    max_depth: int = 3,
    page_size: int = 50,
    start_cursor: str | None = None,
):
    _ensure_episode_profile()
    return notion_main.action_get_content(
        page_id=page_id,
        max_depth=max_depth,
        page_size=page_size,
        start_cursor=start_cursor,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only Notion Episode DB Tool")
    subparsers = parser.add_subparsers(dest="action", required=True)

    parser_list = subparsers.add_parser("list_records", help="List records in episode DB")
    parser_list.add_argument("--page_size", type=int, default=50, help="Page size for record listing")
    parser_list.add_argument("--start_cursor", required=False, help="Cursor for record listing pagination")
    parser_list.add_argument("--title_contains", required=False, help="Optional title substring filter")

    parser_get_content = subparsers.add_parser("get_content", help="Get episode page content as plain text")
    parser_get_content.add_argument("--page_id", required=True, help="Notion Page ID to read content from")
    parser_get_content.add_argument("--max_depth", type=int, default=3, help="Max child depth to traverse")
    parser_get_content.add_argument("--page_size", type=int, default=50, help="Top-level page size for block pagination")
    parser_get_content.add_argument("--start_cursor", required=False, help="Cursor for top-level pagination")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    log_action(f"notion_episode_{args.action}", sys.argv[1:])

    try:
        _ensure_episode_profile()
        if args.action == "list_records":
            result = action_list_records(
                page_size=args.page_size,
                start_cursor=args.start_cursor,
                title_contains=args.title_contains,
            )
        elif args.action == "get_content":
            result = action_get_content(
                page_id=args.page_id,
                max_depth=args.max_depth,
                page_size=args.page_size,
                start_cursor=args.start_cursor,
            )
        else:
            result = {"error": f"Unsupported action: {args.action}"}

        print(json.dumps(cast(dict[str, Any], result), ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": f"Fatal error executing {args.action}: {str(e)}"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
