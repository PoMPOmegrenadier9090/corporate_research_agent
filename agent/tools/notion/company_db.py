import os
import sys
import json
import argparse
from pathlib import Path
from typing import Any, cast
from notion_client import Client

DEFAULT_TEMPLATE_ID = "336718ffb6a880078681cfc6513ba567"

# ロガーをインポート
sys.path.append(str(Path(__file__).parent.parent))
from logger import log_action

def get_notion_client():
    token = os.environ.get("NOTION_API_TOKEN")
    if not token:
        raise ValueError("NOTION_API_TOKEN is missing in environment.")
    return Client(auth=token)

def get_db_id():
    db_id = os.environ.get("NOTION_DB_ID")
    if not db_id:
        raise ValueError("NOTION_DB_ID is missing in environment.")
    return db_id

def get_template_id():
    template_id = os.environ.get("NOTION_TEMPLATE_ID")
    if not template_id:
        raise ValueError("NOTION_TEMPLATE_ID is missing in environment.")
    return template_id

# プロパティのマッピング設計（DB上の定義に合わせる）
PROPERTY_TYPES = {
    "FCF": "number",
    "営業利益率": "number",
    "売上高": "number",
    "タグ": "multi_select",
    "業種": "multi_select",
    "志望度": "select",
    "業界": "select",
    "応募状況": "status"
}

def format_property_value(prop_name, raw_value):
    """Notionの型に合わせてプロパティを整形する"""
    ptype = PROPERTY_TYPES.get(prop_name)
    if ptype == "title":
        # Usually internal Title is handled separately, but just in case
        return {"title": [{"text": {"content": str(raw_value)}}]}
    elif ptype == "number":
        try:
            return {"number": float(raw_value) if "." in str(raw_value) else int(raw_value)}
        except ValueError:
            return None # 変換できない場合はスキップ
    elif ptype == "select":
        return {"select": {"name": str(raw_value)}}
    elif ptype == "multi_select":
        # カンマ区切りの文字列かリストを受け取る
        items = raw_value if isinstance(raw_value, list) else [x.strip() for x in str(raw_value).split(',')]
        return {"multi_select": [{"name": item} for item in items if item]}
    elif ptype == "status":
        return {"status": {"name": str(raw_value)}}
    else:
        # デフォルトは rich_text とみなす
        return {"rich_text": [{"text": {"content": str(raw_value)}}]}

def action_get(company_name: str):
    """企業名でDBを検索し、ページの存在有無と詳細情報を返す"""
    notion = get_notion_client()
    db_id = get_db_id()
    
    # 最新のNotion APIにおいて，レコードはdatabase/datasourceに存在する
    # データベースのメタデータを取得してデータソースIDを特定
    db_info = cast(dict[str, Any], notion.databases.retrieve(db_id))
    try:
        # 最初のデータソースを使用
        data_source_id = db_info["data_sources"][0]["id"]
        query = {
            "data_source_id": data_source_id,
        }
        # データソースに対してクエリを実行
        datasource_info = cast(dict[str, Any], notion.data_sources.query(**query))
        results = datasource_info.get("results", [])
        log_action("action_get", results)
    except (KeyError, IndexError, Exception) as e:
        return {"error": f"データソースの取得またはクエリに失敗しました: {str(e)}"}

    if not results:
        return {
            "exists": False,
            "company_name": company_name,
            "message": f"データソースからレコードを取得できませんでした"
        }

    # 名前が一致するページを検索 (タイトルプロパティ名は '企業名' 固定)
    target_page = None
    for page in results:
        props = page.get("properties", {})
        title_data = props.get("企業名", {}).get("title", [])
        if title_data:
            plain_text = title_data[0].get("plain_text", "")
            if company_name in plain_text:
                target_page = page
                break
    
    if not target_page:
        return {
            "exists": False,
            "company_name": company_name,
            "message": f"企業 '{company_name}' は存在しません。"
        }
    
    page_id = target_page["id"]
    properties = target_page["properties"]
    
    empty_props = []
    filled_props = []
    
    for pname, pdata in properties.items():
        # タイトルプロパティ自体は除外
        if pdata["id"] == "title":
            continue
            
        ptype = pdata["type"]
        is_empty = False
        
        # 値が入っているかどうかをチェック
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
        "company_name": company_name,
        "title_property": "企業名",
        "empty_properties": empty_props,
        "filled_properties": filled_props
    }

def action_add_company(company_name: str):
    """DBに新しい企業ページを作成する"""
    # まず action_get で存在確認し、重複追加を防ぐ
    existing = action_get(company_name)
    if existing.get("error"):
        return existing

    if existing.get("exists"):
        return {
            "status": "skipped",
            "message": f"企業 '{company_name}' は既に存在するため追加しませんでした。",
            "page_id": existing.get("page_id")
        }

    notion = get_notion_client()
    db_id = get_db_id()
    template_id = get_template_id()
    
    new_page_data = {
        "parent": {"database_id": db_id},
        "properties": {
            "企業名": {
                "title": [{"text": {"content": company_name}}]
            }
        }
    }

    new_page_data["template"] = {
        "type": "template_id",
        "template_id": template_id
    }
    
    try:
        new_page = cast(dict[str, Any], notion.pages.create(**new_page_data))
        return {
            "status": "success",
            "message": f"企業 '{company_name}' を追加しました。",
            "page_id": new_page["id"]
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
            "updated_properties": list(properties_payload.keys())
        }
    except Exception as e:
        return {"error": f"プロパティ更新エラー: {str(e)}"}

def action_append_content(page_id: str, content: str):
    """指定されたPage IDの本文の末尾にMarkdownライクなテキストを追記する"""
    notion = get_notion_client()
    
    # 簡易的にテキストをparagraphブロックに変換。改行で分割する
    paragraphs = content.split('\n')
    blocks = []
    for p in paragraphs:
        if not p.strip():
            continue
        # Notionのテキストブロック制限(2000文字)対応などはここでは簡易実装とする
        text_chunk = p.strip()[:2000]
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": text_chunk}
                    }
                ]
            }
        })
        
    if not blocks:
        return {"error": "追記するコンテンツがありません。"}
        
    try:
        notion.blocks.children.append(block_id=page_id, children=blocks)
        return {
            "status": "success",
            "message": f"ページ本文末尾に {len(blocks)} 個のブロックを追記しました。"
        }
    except Exception as e:
        return {"error": f"本文追記エラー: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description="Domain-specific Notion Company DB Tool")
    subparsers = parser.add_subparsers(dest="action", required=True)
    
    # parser_get
    parser_get = subparsers.add_parser("get", help="Search company by name and return properties status")
    parser_get.add_argument("--name", required=True, help="Company name to search")
    
    # parser_add
    parser_add = subparsers.add_parser("add_company", help="Create a new company entry in the DB")
    parser_add.add_argument("--name", required=True, help="New company name")
    
    # parser_update
    parser_update = subparsers.add_parser("update_properties", help="Update properties of an existing company")
    parser_update.add_argument("--page_id", required=True, help="Notion Page ID to update")
    parser_update.add_argument("--updates", required=True, help="JSON string representing property updates, e.g. '{\"FCF\": 1000}'")

    # parser_append
    parser_append = subparsers.add_parser("append_content", help="Append text blocks to the bottom of the company page")
    parser_append.add_argument("--page_id", required=True, help="Notion Page ID to append to")
    parser_append.add_argument("--content", required=True, help="Text/Markdown to append")

    args = parser.parse_args()
    
    log_action(f"notion_{args.action}", sys.argv[1:])
    
    try:
        if args.action == "get":
            result = action_get(args.name)
        elif args.action == "add_company":
            result = action_add_company(args.name)
        elif args.action == "update_properties":
            result = action_update_properties(args.page_id, args.updates)
        elif args.action == "append_content":
            result = action_append_content(args.page_id, args.content)
            
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        error_result = {"error": f"Fatal error executing {args.action}: {str(e)}"}
        print(json.dumps(error_result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
