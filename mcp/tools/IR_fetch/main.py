import argparse
import json
import os
import sys
from pathlib import Path

import requests

sys.path.append(str(Path(__file__).parent.parent))
from logger import log_action

JQUANTS_BASE = "https://api.jquants.com/v2"


def _f(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def fetch_data(stock_code: str) -> dict:
    api_key = os.environ.get("J_QUANTS_API_KEY", "")
    if not api_key:
        return {"error": "J_QUANTS_API_KEY is not set"}

    headers = {"x-api-key": api_key}
    params: dict = {"code": stock_code}
    all_data = []

    while True:
        res = requests.get(
            f"{JQUANTS_BASE}/fins/summary",
            headers=headers,
            params=params,
            timeout=15,
        )
        if res.status_code != 200:
            return {"error": f"J-Quants API error: {res.status_code} {res.text}"}

        d = res.json()
        all_data.extend(d.get("data", []))
        pagination_key = d.get("pagination_key")
        if not pagination_key:
            break
        params["pagination_key"] = pagination_key

    # 通期（FY）のみ
    annual = [s for s in all_data if s.get("CurPerType") == "FY"]

    # 連結があれば連結だけに絞る
    consolidated = [s for s in annual if "Consolidated" in s.get("DocType", "")]
    if consolidated:
        annual = consolidated

    # 会計年度末日でソートして直近5件
    annual_sorted = sorted(annual, key=lambda s: s.get("CurFYEn", ""))
    last_5 = annual_sorted[-5:]

    if not last_5:
        return {"error": f"No annual financial data found for code {stock_code}"}

    output: dict = {}

    for s in last_5:
        fy_end = s.get("CurFYEn", "")[:7]  # YYYY-MM

        net_sales    = _f(s.get("Sales"))
        op_profit    = _f(s.get("OP"))
        profit       = _f(s.get("NP"))
        total_assets = _f(s.get("TA"))
        equity       = _f(s.get("Eq"))
        op_cf        = _f(s.get("CFO"))
        inv_cf       = _f(s.get("CFI"))
        eq_ratio     = _f(s.get("EqAR"))  # 0.0–1.0

        def set_val(key, val):
            if val is not None:
                output.setdefault(key, {})[fy_end] = val

        set_val("売上高", net_sales)
        set_val("営業利益", op_profit)
        set_val("当期純利益", profit)

        if op_profit is not None and net_sales:
            set_val("営業利益率", round(op_profit / net_sales * 100, 2))

        if profit is not None and equity:
            set_val("ROE", round(profit / equity * 100, 2))

        if profit is not None and total_assets:
            set_val("ROA", round(profit / total_assets * 100, 2))

        if eq_ratio is not None:
            set_val("株主資本比率", round(eq_ratio * 100, 2))

        set_val("営業CF", op_cf)

        if op_cf is not None and inv_cf is not None:
            set_val("フリーCF", op_cf + inv_cf)

    return output


if __name__ == "__main__":
    log_action("IR_fetch", sys.argv[1:])
    parser = argparse.ArgumentParser(description="Fetch 5-year financial data via J-Quants API V2.")
    parser.add_argument("--code", type=str, required=True, help="Stock code (e.g. 7203)")
    args = parser.parse_args()

    result = fetch_data(args.code)
    print(json.dumps(result, ensure_ascii=False, indent=2))
