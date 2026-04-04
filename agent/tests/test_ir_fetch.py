import sys
import os
import json

# agentディレクトリをパスに追加してtoolsをインポートできるようにする
agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if agent_dir not in sys.path:
    sys.path.append(agent_dir)

from tools.IR_fetch.main import fetch_data

def run_test():
    print("=== トヨタ自動車(7203)のデータ取得テストを開始 ===")
    stock_code = "7203"
    result = fetch_data(stock_code)
    
    if "error" in result:
        print(f"❌ エラーが発生しました: {result['error']}")
        return
        
    if not isinstance(result, dict):
        print("❌ 結果が辞書型配列ではありません")
        return
        
    expected_keys = [
        "売上高", "営業利益", "当期純利益", "営業利益率", 
        "ROE", "ROA", "株主資本比率", "有利子負債比率", "営業CF", "フリーCF"
    ]
    
    success = True
    for key in expected_keys:
        if key not in result:
            print(f"❌ 期待されるキーが見つかりません: {key}")
            success = False
        elif not isinstance(result[key], dict):
            print(f"❌ キー {key} のデータが辞書ではありません")
            success = False
            
    if not success:
        return
        
    # 売上高にデータがあるかの簡単なチェック
    if len(result.get("売上高", {})) == 0:
        print("❌ 売上高のデータが1件も取得できていません")
        return
        
    # 値が正しく数値としてパースされているかチェック
    for key, data_dict in result.items():
        for year, val in data_dict.items():
            if not (isinstance(val, float) or isinstance(val, int)):
                print(f"❌ {key} の {year} の値が数値（float/int）ではありません: {type(val)} (値: {val})")
                success = False
                
    if not success:
        return
        
    print("✅ 全ての項目が正しく取得・パースされました！\n")
    print("=== 取得データサンプル ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    run_test()
