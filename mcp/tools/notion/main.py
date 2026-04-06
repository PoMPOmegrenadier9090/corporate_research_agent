import os
import sys
import re
import json
import argparse
from typing import Any, cast
from notion_client import Client

from tools.logger import log_action
from tools.notion.profile_loader import load_profile


ACTIVE_PROFILE_NAME = ""
COMPANY_TITLE_PROPERTY_NAME = ""
DB_ID_ENV_KEY = ""
TEMPLATE_ID_ENV_KEY = ""
PROPERTY_TYPES: dict[str, str] = {}


def resolve_profile_settings(
    profile_name: str,
) -> dict[str, Any]:
    """profileを読み込み、実行時に必要な設定値へ正規化する。"""
    if not profile_name:
        raise ValueError("profile_name は必須です。")

    loaded = load_profile(profile_name)

    loaded_types = loaded.get("property_types", {})
    if not isinstance(loaded_types, dict):
        loaded_types = {}

    title_property_name = loaded.get("title_property_name")
    db_id_env_key = loaded.get("db_id_env_key")
    template_id_env_key = loaded.get("template_id_env_key", "")

    if not title_property_name:
        raise ValueError(f"profile '{profile_name}' の title_property_name が不正です。")
    if not db_id_env_key:
        raise ValueError(f"profile '{profile_name}' の db_id_env_key が不正です。")

    return {
        "name": loaded.get("name", profile_name),
        "title_property_name": str(title_property_name),
        "db_id_env_key": str(db_id_env_key),
        "template_id_env_key": str(template_id_env_key or ""),
        "property_types": cast(dict[str, str], dict(loaded_types)),
    }


def configure_profile(
    profile_name: str,
) -> dict[str, Any]:
    """現在の実行プロファイルを切り替える。"""
    global ACTIVE_PROFILE_NAME
    global COMPANY_TITLE_PROPERTY_NAME
    global DB_ID_ENV_KEY
    global TEMPLATE_ID_ENV_KEY
    global PROPERTY_TYPES

    resolved = resolve_profile_settings(profile_name)
    ACTIVE_PROFILE_NAME = str(profile_name)
    COMPANY_TITLE_PROPERTY_NAME = str(resolved["title_property_name"])
    DB_ID_ENV_KEY = str(resolved["db_id_env_key"])
    TEMPLATE_ID_ENV_KEY = str(resolved["template_id_env_key"])
    PROPERTY_TYPES = cast(dict[str, str], resolved["property_types"])
    return resolved


def ensure_profile(profile_name: str) -> dict[str, Any]:
    """指定profileを有効化する。"""
    return configure_profile(profile_name)


def get_notion_client():
    token = os.environ.get("NOTION_API_TOKEN")
    if not token:
        raise ValueError("NOTION_API_TOKEN is missing in environment.")
    return Client(auth=token)


def get_db_id():
    db_id = os.environ.get(DB_ID_ENV_KEY)
    if not db_id:
        raise ValueError(f"{DB_ID_ENV_KEY} is missing in environment.")
    return db_id


def get_template_id():
    if not TEMPLATE_ID_ENV_KEY:
        return None
    template_id = os.environ.get(TEMPLATE_ID_ENV_KEY)
    return template_id  # None が返っても OK、テンプレートなしで作成する


def format_property_value(prop_name, raw_value):
    """Notionの型に合わせてプロパティを整形する"""
    ptype = PROPERTY_TYPES.get(prop_name)
    if ptype == "title":
        return {"title": [{"text": {"content": str(raw_value)}}]}
    if ptype == "number":
        try:
            return {"number": float(raw_value) if "." in str(raw_value) else int(raw_value)}
        except ValueError:
            return None
    if ptype == "select":
        return {"select": {"name": str(raw_value)}}
    if ptype == "multi_select":
        items = raw_value if isinstance(raw_value, list) else [x.strip() for x in str(raw_value).split(",")]
        return {"multi_select": [{"name": item} for item in items if item]}
    if ptype == "status":
        return {"status": {"name": str(raw_value)}}
    return {"rich_text": [{"text": {"content": str(raw_value)}}]}


def action_get(company_name: str):
    """タイトル文字列でDBを検索し、ページの存在有無と詳細情報を返す。"""
    title_query = company_name

    try:
        datasource_info = _query_datasource_pages()
        results = cast(list[dict[str, Any]], datasource_info.get("results", []))
        log_action("action_get", results)
    except Exception as e:
        return {"error": f"データソースの取得またはクエリに失敗しました: {str(e)}"}

    if not results:
        return {
            "exists": False,
            "query": title_query,
            "message": "データソースからレコードを取得できませんでした",
        }

    target_page = _find_page_by_title(results, title_query)

    if not target_page:
        return {
            "exists": False,
            "query": title_query,
            "message": f"'{title_query}' は存在しません。",
        }

    page_id = target_page["id"]
    properties = target_page["properties"]

    empty_props = []
    filled_props = []

    for pname, pdata in properties.items():
        if pdata["id"] == "title":
            continue

        ptype = pdata["type"]
        is_empty = False

        if ptype in ["rich_text", "title"]:
            is_empty = len(pdata.get(ptype, [])) == 0
        elif ptype in ["number", "select", "status", "date"]:
            is_empty = pdata.get(ptype) is None
        elif ptype in ["multi_select", "relation", "people"]:
            is_empty = len(pdata.get(ptype, [])) == 0

        if is_empty:
            empty_props.append(pname)
        else:
            filled_props.append(pname)

    return {
        "exists": True,
        "page_id": page_id,
        "query": title_query,
        "title_property": COMPANY_TITLE_PROPERTY_NAME,
        "empty_properties": empty_props,
        "filled_properties": filled_props,
    }


def _query_datasource_pages(
    page_size: int | None = None,
    start_cursor: str | None = None,
) -> dict[str, Any]:
    """
    データソースに紐づくページをクエリする．ページネーションに対応
    """
    notion = get_notion_client()
    db_id = get_db_id()

    db_info = cast(dict[str, Any], notion.databases.retrieve(db_id))
    data_source_id = db_info["data_sources"][0]["id"]

    query: dict[str, Any] = {
        "data_source_id": data_source_id,
    }
    if page_size is not None:
        query["page_size"] = page_size
    if start_cursor:
        query["start_cursor"] = start_cursor
    # カーソルを指定してクエリ実行
    return cast(dict[str, Any], notion.data_sources.query(**query))


def _find_page_by_title(pages: list[dict[str, Any]], title_query: str) -> dict[str, Any] | None:
    for page in pages:
        title = _extract_page_title(page)
        if title_query in title:
            return page
    return None


def _extract_page_title(page: dict[str, Any]) -> str:
    props = page.get("properties", {})
    if not isinstance(props, dict):
        return ""

    preferred = props.get(COMPANY_TITLE_PROPERTY_NAME, {})
    preferred_title = preferred.get("title", []) if isinstance(preferred, dict) else []
    if isinstance(preferred_title, list) and preferred_title:
        first = preferred_title[0]
        if isinstance(first, dict):
            return str(first.get("plain_text", "") or "")

    for pdata in props.values():
        if not isinstance(pdata, dict):
            continue
        if pdata.get("type") != "title":
            continue
        title_data = pdata.get("title", [])
        if isinstance(title_data, list) and title_data:
            first = title_data[0]
            if isinstance(first, dict):
                return str(first.get("plain_text", "") or "")

    return ""


def action_list_records(
    page_size: int = 50,
    start_cursor: str | None = None,
    title_contains: str | None = None,
):
    """アクティブprofileのDBからレコード一覧を取得する"""
    if page_size <= 0:
        return {"error": "page_size は 1 以上である必要があります。"}

    try:
        datasource_info = _query_datasource_pages(
            page_size=page_size,
            start_cursor=start_cursor,
        )
        results = cast(list[dict[str, Any]], datasource_info.get("results", []))
    except Exception as e:
        return {"error": f"レコード一覧の取得に失敗しました: {str(e)}"}

    records: list[dict[str, Any]] = []
    for page in results:
        title = _extract_page_title(page)
        if title_contains and title_contains not in title:
            continue

        records.append(
            {
                "page_id": str(page.get("id", "")),
                "title": title,
            }
        )

    return {
        "status": "success",
        "title_property": COMPANY_TITLE_PROPERTY_NAME,
        "record_count": len(records),
        "records": records,
        "has_more": bool(datasource_info.get("has_more", False)),
        "next_cursor": cast(str | None, datasource_info.get("next_cursor")),
    }


def action_add_company(company_name: str):
    """DBに新しい企業ページを作成する"""
    existing = action_get(company_name)
    if existing.get("error"):
        return existing

    if existing.get("exists"):
        return {
            "status": "skipped",
            "message": f"企業 '{company_name}' は既に存在するため追加しませんでした。",
            "page_id": existing.get("page_id"),
        }

    notion = get_notion_client()
    db_id = get_db_id()
    template_id = get_template_id()

    new_page_data = {
        "parent": {"database_id": db_id},
        "properties": {
            COMPANY_TITLE_PROPERTY_NAME: {
                "title": [{"text": {"content": company_name}}],
            }
        },
    }

    if template_id:
        new_page_data["template"] = {
            "type": "template_id",
            "template_id": template_id,
        }

    try:
        new_page = cast(dict[str, Any], notion.pages.create(**new_page_data))
        return {
            "status": "success",
            "message": f"企業 '{company_name}' を追加しました。",
            "page_id": new_page["id"],
        }
    except Exception as e:
        return {"error": f"ページの作成に失敗しました: {str(e)}"}


def action_update_properties(page_id: str, updates_json: str):
    """指定されたPage IDに対して、JSONで渡されたプロパティを更新(UPSERT)する"""
    notion = get_notion_client()

    try:
        updates = json.loads(updates_json)
    except json.JSONDecodeError:
        return {"error": "updates_json は正しいJSON形式である必要があります。"}

    properties_payload = {}
    for prop_name, raw_value in updates.items():
        formatted_val = format_property_value(prop_name, raw_value)
        if formatted_val is not None:
            properties_payload[prop_name] = formatted_val

    if not properties_payload:
        return {"error": "更新対象の有効なプロパティがありません。"}

    try:
        notion.pages.update(page_id=page_id, properties=properties_payload)
        return {
            "status": "success",
            "message": "プロパティを更新しました。",
            "updated_properties": list(properties_payload.keys()),
        }
    except Exception as e:
        return {"error": f"プロパティ更新エラー: {str(e)}"}


def _extract_rich_text_plain_text(rich_text_list: list[dict[str, Any]]) -> str:
    texts: list[str] = []
    for item in rich_text_list:
        plain = item.get("plain_text")
        if plain is not None:
            texts.append(str(plain))
            continue

        text_obj = item.get("text", {})
        content = text_obj.get("content") if isinstance(text_obj, dict) else None
        if content is not None:
            texts.append(str(content))

    return "".join(texts)


def _format_block_plain_text(block: dict[str, Any]) -> str:
    block_type = block.get("type", "")
    if not block_type:
        return ""

    payload = block.get(block_type, {})
    if not isinstance(payload, dict):
        payload = {}

    if block_type in {
        "paragraph",
        "heading_1",
        "heading_2",
        "heading_3",
        "heading_4",
        "bulleted_list_item",
        "numbered_list_item",
        "quote",
        "toggle",
        "callout",
        "to_do",
    }:
        rich_text = payload.get("rich_text", [])
        if not isinstance(rich_text, list):
            rich_text = []
        text = _extract_rich_text_plain_text(cast(list[dict[str, Any]], rich_text))

        if block_type == "heading_1":
            return f"# {text}" if text else "#"
        if block_type == "heading_2":
            return f"## {text}" if text else "##"
        if block_type == "heading_3":
            return f"### {text}" if text else "###"
        if block_type == "heading_4":
            return f"#### {text}" if text else "####"
        if block_type == "bulleted_list_item":
            return f"- {text}" if text else "-"
        if block_type == "numbered_list_item":
            return f"1. {text}" if text else "1."
        if block_type == "quote":
            return f"> {text}" if text else ">"
        if block_type == "to_do":
            checked = payload.get("checked", False)
            mark = "x" if checked else " "
            return f"- [{mark}] {text}" if text else f"- [{mark}]"

        return text

    if block_type == "divider":
        return "---"

    if block_type == "child_page":
        title = payload.get("title", "")
        return f"[child_page] {title}" if title else "[child_page]"

    if block_type == "bookmark":
        url = payload.get("url", "")
        return f"[bookmark] {url}" if url else "[bookmark]"

    if block_type == "code":
        rich_text = payload.get("rich_text", [])
        if not isinstance(rich_text, list):
            rich_text = []
        code_text = _extract_rich_text_plain_text(cast(list[dict[str, Any]], rich_text))
        language = payload.get("language", "plain text")
        return f"```{language}\n{code_text}\n```" if code_text else f"```{language}\n```"

    return f"[{block_type}]"


def _collect_child_block_texts(
    notion: Client,
    block_id: str,
    depth: int,
    max_depth: int,
    page_size: int,
) -> list[str]:
    """
    子ブロックのテキストを再帰的に収集する。深さ制限とページネーションに対応。
    """
    lines: list[str] = []
    cursor: str | None = None

    while True:
        query: dict[str, Any] = {"block_id": block_id, "page_size": page_size}
        if cursor:
            query["start_cursor"] = cursor

        response = cast(dict[str, Any], notion.blocks.children.list(**query))
        blocks = cast(list[dict[str, Any]], response.get("results", []))

        for block in blocks:
            line = _format_block_plain_text(block)
            if line:
                lines.append(("  " * depth) + line)

            has_children = block.get("has_children", False)
            child_block_id = block.get("id")
            if has_children and child_block_id and depth < max_depth:
                lines.extend(
                    _collect_child_block_texts(
                        notion=notion,
                        block_id=str(child_block_id),
                        depth=depth + 1,
                        max_depth=max_depth,
                        page_size=page_size,
                    )
                )

        if not response.get("has_more", False):
            break
        cursor = cast(str | None, response.get("next_cursor"))

    return lines


def action_get_content(
    page_id: str,
    max_depth: int = 3,
    page_size: int = 50,
    start_cursor: str | None = None,
):
    """指定ページの本文ブロックを取得し、plain_textとして返す（トップレベルはカーソルページング対応）。"""
    notion = get_notion_client()

    if max_depth < 0:
        return {"error": "max_depth は 0 以上である必要があります。"}
    if page_size <= 0:
        return {"error": "page_size は 1 以上である必要があります。"}

    query: dict[str, Any] = {"block_id": page_id, "page_size": page_size}
    if start_cursor:
        query["start_cursor"] = start_cursor

    try:
        response = cast(dict[str, Any], notion.blocks.children.list(**query))
        top_blocks = cast(list[dict[str, Any]], response.get("results", []))
    except Exception as e:
        return {"error": f"本文ブロックの取得に失敗しました: {str(e)}"}

    lines: list[str] = []
    for block in top_blocks:
        line = _format_block_plain_text(block)
        if line:
            lines.append(line)

        has_children = block.get("has_children", False)
        child_block_id = block.get("id")
        if has_children and child_block_id and max_depth > 0:
            try:
                lines.extend(
                    _collect_child_block_texts(
                        notion=notion,
                        block_id=str(child_block_id),
                        depth=1,
                        max_depth=max_depth,
                        page_size=page_size,
                    )
                )
            except Exception as e:
                return {"error": f"子ブロック取得に失敗しました: {str(e)}"}

    next_cursor = cast(str | None, response.get("next_cursor"))
    return {
        "status": "success",
        "page_id": page_id,
        "max_depth": max_depth,
        "top_level_block_count": len(top_blocks),
        "line_count": len(lines),
        "has_more": bool(response.get("has_more", False)),
        "next_cursor": next_cursor,
        "plain_text": "\n".join(lines),
    }


def parse_rich_text(text: str):
    """簡易的なMarkdownインライン書式（太字、コード）をNotionのrich_textにパースする"""
    pattern = re.compile(r"(\*\*(.*?)\*\*)|(`(.*?)`)")
    rich_texts = []
    last_idx = 0

    for match in pattern.finditer(text):
        if match.start() > last_idx:
            rich_texts.append({
                "type": "text",
                "text": {"content": text[last_idx:match.start()]},
            })

        if match.group(1):
            rich_texts.append({
                "type": "text",
                "text": {"content": match.group(2)},
                "annotations": {"bold": True},
            })
        elif match.group(3):
            rich_texts.append({
                "type": "text",
                "text": {"content": match.group(4)},
                "annotations": {"code": True},
            })
        last_idx = match.end()

    if last_idx < len(text):
        rich_texts.append({
            "type": "text",
            "text": {"content": text[last_idx:]},
        })

    return rich_texts if rich_texts else [{"type": "text", "text": {"content": ""}}]


def _normalize_append_content(content: str) -> str:
    """CLI経由で渡されるエスケープ改行(\\n)を実改行へ戻す。"""
    if "\n" in content:
        return content
    if "\\n" in content or "\\r\\n" in content:
        return content.replace("\\r\\n", "\n").replace("\\n", "\n")
    return content


def action_append_content(page_id: str, content: str):
    """指定されたPage IDの本文の末尾にMarkdownライクなテキストを追記する"""
    notion = get_notion_client()

    normalized_content = _normalize_append_content(content)
    paragraphs = normalized_content.split("\n")
    blocks = []
    for p in paragraphs:
        if not p.strip():
            continue

        text_chunk = p.strip()
        block_type = "paragraph"
        text_content = text_chunk

        if text_chunk.startswith("# "):
            block_type = "heading_1"
            text_content = text_chunk[2:].strip()
        elif text_chunk.startswith("## "):
            block_type = "heading_2"
            text_content = text_chunk[3:].strip()
        elif text_chunk.startswith("### "):
            block_type = "heading_3"
            text_content = text_chunk[4:].strip()
        elif text_chunk.startswith("- ") or text_chunk.startswith("* "):
            block_type = "bulleted_list_item"
            text_content = text_chunk[2:].strip()
        elif text_chunk.startswith("> "):
            block_type = "toggle"
            text_content = text_chunk[2:].strip()
        elif re.match(r"^\d+\.\s", text_chunk):
            block_type = "numbered_list_item"
            text_content = re.sub(r"^\d+\.\s", "", text_chunk)

        text_content = text_content[:2000]

        blocks.append({
            "object": "block",
            "type": block_type,
            block_type: {
                "rich_text": parse_rich_text(text_content)
            },
        })

    if not blocks:
        return {"error": "追記するコンテンツがありません。"}

    try:
        notion.blocks.children.append(block_id=page_id, children=blocks)
        return {
            "status": "success",
            "message": f"ページ本文末尾に {len(blocks)} 個のブロックを追記しました。",
        }
    except Exception as e:
        return {"error": f"本文追記エラー: {str(e)}"}


def _dispatch_action(args: argparse.Namespace) -> dict[str, Any]:
    if args.action == "list_records":
        return cast(
            dict[str, Any],
            action_list_records(
                page_size=args.page_size,
                start_cursor=args.start_cursor,
                title_contains=args.title_contains,
            ),
        )
    if args.action == "get":
        return cast(dict[str, Any], action_get(args.name))
    if args.action == "add_company":
        return cast(dict[str, Any], action_add_company(args.name))
    if args.action == "update_properties":
        return cast(dict[str, Any], action_update_properties(args.page_id, args.updates))
    if args.action == "append_content":
        return cast(dict[str, Any], action_append_content(args.page_id, args.content))
    if args.action == "get_content":
        return cast(
            dict[str, Any],
            action_get_content(
                page_id=args.page_id,
                max_depth=args.max_depth,
                page_size=args.page_size,
                start_cursor=args.start_cursor,
            ),
        )
    return {"error": f"Unsupported action: {args.action}"}


def _build_parser(default_profile: str, allow_profile_flag: bool) -> argparse.ArgumentParser:
    """
    argument parserを構築する
    """
    parser = argparse.ArgumentParser(description="Notion DB Tool")
    if allow_profile_flag:
        parser.add_argument("--profile", default=default_profile, help="Profile name under tools/notion/profiles")

    # subparserを定義することにより，コマンドごとに必要な引数を分けることができる
    subparsers = parser.add_subparsers(dest="action", required=True)

    parser_list = subparsers.add_parser("list_records", help="List records in the current profile DB")
    parser_list.add_argument("--page_size", type=int, default=50, help="Page size for record listing")
    parser_list.add_argument("--start_cursor", required=False, help="Cursor for record listing pagination")
    parser_list.add_argument("--title_contains", required=False, help="Optional title substring filter")

    parser_get = subparsers.add_parser("get", help="Search record by title and return properties status")
    parser_get.add_argument("--name", required=True, help="Record title query to search")

    parser_add = subparsers.add_parser("add_company", help="Create a new company entry in the DB")
    parser_add.add_argument("--name", required=True, help="New company name")

    parser_update = subparsers.add_parser("update_properties", help="Update properties of an existing company")
    parser_update.add_argument("--page_id", required=True, help="Notion Page ID to update")
    parser_update.add_argument("--updates", required=True, help="JSON string representing property updates, e.g. '{\"FCF\": 1000}'")

    parser_append = subparsers.add_parser("append_content", help="Append text blocks to the bottom of the company page")
    parser_append.add_argument("--page_id", required=True, help="Notion Page ID to append to")
    parser_append.add_argument("--content", required=True, help="Text/Markdown to append")

    parser_get_content = subparsers.add_parser("get_content", help="Get page content blocks as plain text")
    parser_get_content.add_argument("--page_id", required=True, help="Notion Page ID to read content from")
    parser_get_content.add_argument("--max_depth", type=int, default=3, help="Max child depth to traverse")
    parser_get_content.add_argument("--page_size", type=int, default=50, help="Top-level page size for block pagination")
    parser_get_content.add_argument("--start_cursor", required=False, help="Cursor for top-level pagination")

    return parser


def run_cli(default_profile: str = "company", allow_profile_flag: bool = True) -> None:
    parser = _build_parser(default_profile=default_profile, allow_profile_flag=allow_profile_flag)
    args = parser.parse_args()

    profile_name = default_profile
    if allow_profile_flag:
        profile_name = cast(str, args.profile)

    try:
        ensure_profile(profile_name)
    except Exception as e:
        print(json.dumps({"error": f"profile解決エラー: {str(e)}", "profile": profile_name}, ensure_ascii=False, indent=2))
        return

    log_action(
        f"notion_{args.action}",
        [f"profile={profile_name}", *sys.argv[1:]],
    )

    try:
        result = _dispatch_action(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        error_result = {"error": f"Fatal error executing {args.action}: {str(e)}"}
        print(json.dumps(error_result, ensure_ascii=False, indent=2))


def main() -> None:
    run_cli(default_profile="company", allow_profile_flag=True)


if __name__ == "__main__":
    main()
