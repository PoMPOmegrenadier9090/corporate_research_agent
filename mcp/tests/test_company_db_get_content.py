import argparse
import json
import os
import sys


# agentディレクトリをパスに追加してtoolsをインポートできるようにする
agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if agent_dir not in sys.path:
    sys.path.append(agent_dir)

from tools.notion import company_db


DEFAULT_PAGE_ID = "338718ffb6a88166b085d5bba94b43a1"


def run_test(
    page_id: str,
    max_depth: int,
    page_size: int,
    start_cursor: str | None,
    fetch_next: bool,
):
    result = company_db.action_get_content(
        page_id=page_id,
        max_depth=max_depth,
        page_size=page_size,
        start_cursor=start_cursor,
    )

    if "error" in result:
        print(json.dumps({"status": "error", "result": result}, ensure_ascii=False, indent=2))
        return

    output = {
        "status": "ok",
        "page_id": page_id,
        "first_page": result,
    }

    if fetch_next and result.get("has_more") and result.get("next_cursor"):
        next_result = company_db.action_get_content(
            page_id=page_id,
            max_depth=max_depth,
            page_size=page_size,
            start_cursor=result.get("next_cursor"),
        )
        output["next_page"] = next_result

    print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Integration test runner for action_get_content")
    parser.add_argument("--page_id", default=DEFAULT_PAGE_ID, help="Notion page id to read")
    parser.add_argument("--max_depth", type=int, default=3, help="max depth for child traversal")
    parser.add_argument("--page_size", type=int, default=50, help="top-level page size")
    parser.add_argument("--start_cursor", default=None, help="start cursor for pagination")
    parser.add_argument(
        "--fetch_next",
        action="store_true",
        help="if has_more, automatically fetch one additional page",
    )

    args = parser.parse_args()
    run_test(
        page_id=args.page_id,
        max_depth=args.max_depth,
        page_size=args.page_size,
        start_cursor=args.start_cursor,
        fetch_next=args.fetch_next,
    )


if __name__ == "__main__":
    main()