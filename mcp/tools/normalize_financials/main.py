import argparse
import json
import sys
from pathlib import Path

# agent/tools パスを追加してロガーと共通パーサーをインポート
sys.path.append(str(Path(__file__).parent.parent))
from logger import log_action

from normalize_financials.parser import parse_financial_value


def main():
    parser = argparse.ArgumentParser(description="Normalize a raw financial value string into a base numeric value.")
    parser.add_argument("--text", type=str, required=True, help="Raw financial text to normalize")
    args = parser.parse_args()

    log_action("normalize_financials", sys.argv[1:])

    result = {
        "input": args.text,
        "normalized_value": parse_financial_value(args.text),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()