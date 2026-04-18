import json
import argparse
import sys
from typing import Any, cast

from tools.logger import log_action
from tools.notion import main as notion_main


_COMPANY_PROFILE = notion_main.resolve_profile_settings("company")
DEFAULT_COMPANY_TITLE_PROPERTY_NAME = str(_COMPANY_PROFILE["title_property_name"])
DEFAULT_DB_ID_ENV_KEY = str(_COMPANY_PROFILE["db_id_env_key"])
DEFAULT_TEMPLATE_ID_ENV_KEY = str(_COMPANY_PROFILE["template_id_env_key"])
DEFAULT_PROPERTY_TYPES = dict(_COMPANY_PROFILE["property_types"])


def _ensure_company_profile() -> None:
    notion_main.configure_profile("company")


def _sync_public_constants() -> None:
    global COMPANY_TITLE_PROPERTY_NAME
    global DB_ID_ENV_KEY
    global TEMPLATE_ID_ENV_KEY
    global PROPERTY_TYPES

    COMPANY_TITLE_PROPERTY_NAME = notion_main.COMPANY_TITLE_PROPERTY_NAME
    DB_ID_ENV_KEY = notion_main.DB_ID_ENV_KEY
    TEMPLATE_ID_ENV_KEY = notion_main.TEMPLATE_ID_ENV_KEY
    PROPERTY_TYPES = dict(notion_main.PROPERTY_TYPES)


def _ensure_and_sync() -> None:
    _ensure_company_profile()
    _sync_public_constants()


_ensure_and_sync()


def get_notion_client():
    _ensure_and_sync()
    return notion_main.get_notion_client()


def get_db_id():
    _ensure_and_sync()
    return notion_main.get_db_id()


def get_template_id():
    _ensure_and_sync()
    return notion_main.get_template_id()


def format_property_value(prop_name, raw_value):
    _ensure_and_sync()
    return notion_main.format_property_value(prop_name, raw_value)


def _build_company_query_candidates(company_name: str, aliases: list[str] | None = None) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()

    # クエリ名を正規化しつつ，重複を排除してクエリ候補リストを構築
    for name in [company_name, *(aliases or [])]:
        normalized = str(name).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        candidates.append(normalized)

    return candidates


def action_get(company_name: str, aliases: list[str] | None = None):
    _ensure_and_sync()
    query_candidates = _build_company_query_candidates(company_name, aliases)
    result = notion_main.action_get_many(query_candidates)
    if not isinstance(result, dict):
        return {"error": "検索結果の取得に失敗しました。"}

    if result.get("error"):
        return result

    output = dict(result)
    output["company_name"] = company_name
    return output


def action_add_company(company_name: str):
    _ensure_and_sync()
    return notion_main.action_add_company(company_name)


def action_update_properties(page_id: str, updates_json: str):
    _ensure_and_sync()
    return notion_main.action_update_properties(page_id, updates_json)


def _extract_rich_text_plain_text(rich_text_list):
    return notion_main._extract_rich_text_plain_text(rich_text_list)


def _format_block_plain_text(block):
    return notion_main._format_block_plain_text(block)


def _collect_child_block_texts(notion, block_id: str, depth: int, max_depth: int, page_size: int):
    return notion_main._collect_child_block_texts(
        notion=notion,
        block_id=block_id,
        depth=depth,
        max_depth=max_depth,
        page_size=page_size,
    )


def action_get_content(
    page_id: str,
    max_depth: int = 3,
    page_size: int = 50,
    start_cursor: str | None = None,
):
    _ensure_and_sync()
    return notion_main.action_get_content(
        page_id=page_id,
        max_depth=max_depth,
        page_size=page_size,
        start_cursor=start_cursor,
    )


def action_list_records(
    page_size: int = 50,
    start_cursor: str | None = None,
    title_contains: str | None = None,
):
    _ensure_and_sync()
    return notion_main.action_list_records(
        page_size=page_size,
        start_cursor=start_cursor,
        title_contains=title_contains,
    )


def parse_rich_text(text: str):
    return notion_main.parse_rich_text(text)


def action_append_content(page_id: str, content: str):
    _ensure_and_sync()
    return notion_main.action_append_content(page_id, content)


def main() -> None:
    parser = notion_main._build_parser(default_profile="company", allow_profile_flag=False)
    args = parser.parse_args()

    log_action(f"notion_{args.action}", sys.argv[1:])

    try:
        _ensure_and_sync()
        if args.action == "list_records":
            result = action_list_records(
                page_size=args.page_size,
                start_cursor=args.start_cursor,
                title_contains=args.title_contains,
            )
        elif args.action == "get":
            result = action_get(args.name)
        elif args.action == "add_company":
            result = action_add_company(args.name)
        elif args.action == "update_properties":
            result = action_update_properties(args.page_id, args.updates)
        elif args.action == "append_content":
            result = action_append_content(args.page_id, args.content)
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
