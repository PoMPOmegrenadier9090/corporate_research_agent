import argparse
import os
import sys
import json
import requests
from pathlib import Path

# agent/tools パスを追加してロガーをインポート
sys.path.append(str(Path(__file__).parent.parent))
from logger import log_action

def fetch_page(target_url: str) -> dict:
    jina_api_key = os.environ.get("JINA_API_KEY")
    api_url = f"https://r.jina.ai/{target_url}"
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {jina_api_key}",
        "X-Md-Bullet-List-Marker": "-",
        "X-Md-Em-Delimiter": "*",
        "X-Md-Hr": "---",
        "X-Retain-Images": "none",
        "X-Timeout": "15",
        "X-Token-Budget": "8000"
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # JINAのJSONレスポンスから必要なタイトルとコンテンツ本文（Markdown）を抽出
        if "data" in data and "content" in data["data"]:
            content = data["data"]["content"]
            title = data["data"].get("title", "No Title")
            
            # ページ内容すべてをログに出すと docker logs が埋まるため、サマリーのみ出力
            log_action("fetch_page", f"Success: {title} (Length: {len(content)} chars)")
            
            return {
                "title": title,
                "url": data["data"].get("url", target_url),
                "content": content
            }
        return {"error": "Unexpected JSON structure", "raw": data}
        
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if response is not None:
            error_msg += f" (Status Code: {response.status_code}, Body: {response.text})"
        return {"error": f"Request failed: {error_msg}"}

def main():
    parser = argparse.ArgumentParser(description="Fetch and parse a webpage using JINA AI reader")
    parser.add_argument("--url", "-u", type=str, required=True, help="URL of the webpage to fetch")
    args = parser.parse_args()

    # 実行ログを残す（docker compose logs 向け）
    log_action("fetch_page", sys.argv[1:])

    result = fetch_page(args.url)
    
    # 標準出力にJSON文字列として吐き出す
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
