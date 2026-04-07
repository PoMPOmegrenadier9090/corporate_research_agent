"""
Stock Code Search Tool

企業名で日本の上場銘柄を検索し、証券コード・業種情報を返すCLIツール。
AIエージェントが企業の証券コードを特定する際に使用することを想定。

Usage:
    python main.py <企業名1> [<企業名2> ...]

Examples:
    python main.py トヨタ
    python main.py ソニー 日立 本田
    python main.py "日本ハム"
"""

import sys
import json
import pandas as pd
from pathlib import Path

# __file__ が agent/tools/stock_code_search/main.py なので agent/tools をパスに追加
sys.path.append(str(Path(__file__).parent.parent))
from logger import log_action

DATA_PATH = Path(__file__).parent / "data.csv"

def search(queries: list[str]) -> dict[str, list[dict]]:
    """
    指定された複数のキーワードで銘柄名を検索する（部分一致・大文字小文字無視）。
    
    Args:
        queries: 検索キーワードのリスト（企業名の一部）

    Returns:
        各キーワードをキーとし、マッチしたレコードのリストを値とする辞書。各レコードは以下のキーを持つ辞書:
            - コード: 証券コード
            - 銘柄名: 銘柄名
            - 33業種コード: 業種コード
            - 33業種区分: 業種区分名
    """
    df = pd.read_csv(DATA_PATH)
    
    # 欠損値を空文字に置換し、必要なカラムのみ抽出
    df = df.fillna("")
    cols = ["コード", "銘柄名", "33業種区分"]
    
    results = {}
    for q in set(queries):  # 重複したクエリを除外
        # 大文字小文字を区別せずに部分一致検索
        matched = df[df["銘柄名"].str.contains(q, case=False, na=False)]
        results[q] = matched[cols].to_dict(orient="records")
        
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <企業名1> [<企業名2> ...]", file=sys.stderr)
        sys.exit(1)

    queries = sys.argv[1:]
    results_map = search(queries)

    # 出力用フォーマットに整形
    output = [
        {
            "query": q,
            "count": len(res),
            "results": res
        }
        for q, res in results_map.items()
    ]

    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    log_action("stock_code_search", sys.argv[1:])
    main()
