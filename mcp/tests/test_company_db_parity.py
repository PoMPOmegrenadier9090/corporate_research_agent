import argparse
import json
import os
import sys
from typing import Any


# agentディレクトリをパスに追加してtoolsをインポートできるようにする
agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if agent_dir not in sys.path:
    sys.path.append(agent_dir)

from tools.notion import company_db
from tools.notion import main as notion_main


DEFAULT_PAGE_ID = "338718ffb6a88166b085d5bba94b43a1"


def _dict_diff(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_keys = set(left.keys())
    right_keys = set(right.keys())

    only_left = sorted(left_keys - right_keys)
    only_right = sorted(right_keys - left_keys)

    value_mismatches: dict[str, dict[str, Any]] = {}
    for key in sorted(left_keys & right_keys):
        if left[key] != right[key]:
            value_mismatches[key] = {
                "company_db": left[key],
                "generic": right[key],
            }

    return {
        "only_in_company_db": only_left,
        "only_in_generic": only_right,
        "value_mismatches": value_mismatches,
    }


def run_get_content_parity(
    page_id: str,
    max_depth: int,
    page_size: int,
    start_cursor: str | None,
) -> dict[str, Any]:
    company_result = company_db.action_get_content(
        page_id=page_id,
        max_depth=max_depth,
        page_size=page_size,
        start_cursor=start_cursor,
    )

    notion_main.ensure_profile("company")
    generic_result = notion_main.action_get_content(
        page_id=page_id,
        max_depth=max_depth,
        page_size=page_size,
        start_cursor=start_cursor,
    )

    matched = company_result == generic_result
    return {
        "name": "get_content",
        "matched": matched,
        "diff": {} if matched else _dict_diff(company_result, generic_result),
        "company_db": company_result,
        "generic": generic_result,
    }


def run_get_parity(company_name: str) -> dict[str, Any]:
    company_result = company_db.action_get(company_name)

    notion_main.ensure_profile("company")
    generic_result = notion_main.action_get(company_name)

    normalized_company = dict(company_result)
    normalized_company.pop("company_name", None)

    matched = normalized_company == generic_result
    return {
        "name": "get",
        "matched": matched,
        "diff": {} if matched else _dict_diff(normalized_company, generic_result),
        "company_db": company_result,
        "generic": generic_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Parity test between tools.notion.company_db and tools.notion.main")
    parser.add_argument("--page_id", default=DEFAULT_PAGE_ID, help="Notion page id for get_content parity")
    parser.add_argument("--max_depth", type=int, default=3, help="Max depth for get_content")
    parser.add_argument("--page_size", type=int, default=50, help="Page size for get_content")
    parser.add_argument("--start_cursor", default=None, help="Cursor for get_content pagination")
    parser.add_argument("--name", default=None, help="Optional company name for get parity")

    args = parser.parse_args()

    checks = [
        run_get_content_parity(
            page_id=args.page_id,
            max_depth=args.max_depth,
            page_size=args.page_size,
            start_cursor=args.start_cursor,
        )
    ]

    if args.name:
        checks.append(run_get_parity(args.name))

    all_matched = all(check.get("matched") for check in checks)
    result = {
        "status": "ok" if all_matched else "ng",
        "all_matched": all_matched,
        "checks": checks,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not all_matched:
        sys.exit(1)


if __name__ == "__main__":
    main()
