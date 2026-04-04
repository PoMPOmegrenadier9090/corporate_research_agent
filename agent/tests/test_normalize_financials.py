import json
import os
import sys

# agentディレクトリをパスに追加してtoolsをインポートできるようにする
agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if agent_dir not in sys.path:
    sys.path.append(agent_dir)

from tools.normalize_financials.parser import parse_financial_value


def run_test():
    cases = {
        "1,234": 1234.0,
        "1.2億円": 120000000.0,
        "1兆2,345億6,789万円": 1234567890000.0,
        "1,234百万円": 1234000000.0,
        "12.5%": 0.125,
        "▲3.4%": -0.034,
        "赤字": None,
    }

    for raw, expected in cases.items():
        actual = parse_financial_value(raw)
        if actual != expected:
            raise AssertionError(f"{raw!r}: expected {expected!r}, got {actual!r}")

    print(json.dumps({"status": "ok", "cases": len(cases)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run_test()