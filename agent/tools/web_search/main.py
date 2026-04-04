import os
import sys
import json
import argparse
from pathlib import Path
from tavily import TavilyClient

# agent/tools パスを追加してロガーをインポート
sys.path.append(str(Path(__file__).parent.parent))
from logger import log_action

def search_web(query: str, max_results: int = 3, domains: list[str] = []):
    """
    Tavily APIを使用してウェブ検索を行う関数。
    """
    api_key = os.environ.get("TAVILY_API_TOKEN")
    if not api_key:
        return {"error": "TAVILY_API_KEY is not set in the environment variables."}
        
    try:
        tavily_client = TavilyClient(api_key=api_key)
        response = tavily_client.search(
            query=query,
            topic="general",
            search_depth="basic",
            max_results=max_results,
            include_domains=domains,
            country="japan"
            )
        
        # 検索結果の各コンテンツを500文字に切り詰める
        if "results" in response:
            for result in response["results"]:
                if "content" in result and len(result["content"]) > 500:
                    result["content"] = result["content"][:500] + "..."
                    
        return response
    except Exception as e:
        return {"error": f"Tavily API error: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description="Web search tool using Tavily API")
    parser.add_argument("--query", "-q", type=str, required=True, help="The search query text")
    parser.add_argument("--limit", "-l", type=int, default=3, help="Max number of results to return")
    parser.add_argument("--domains", "-d", type=str, help="Comma-separated list of domains to restrict search to (e.g. zenn.dev,qiita.com,note.com)")
    args = parser.parse_args()

    # 実行ログを残す（docker compose logs 向け）
    log_action("web_search", sys.argv[1:])

    # 検索実行
    domains_list = None
    if args.domains:
        domains_list = [d.strip() for d in args.domains.split(",") if d.strip()]
        
    result = search_web(args.query, args.limit, domains_list)
    
    # 最終出力をJSONとして標準出力にスロー
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
