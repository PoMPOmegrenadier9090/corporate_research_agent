import argparse
import time
import requests
from bs4 import BeautifulSoup
import re
import json
import sys
from pathlib import Path

# __file__ が agent/tools/IR_fetch/main.py なので agent/tools をパスに追加
sys.path.append(str(Path(__file__).parent.parent))
from logger import log_action

from normalize_financials.parser import parse_financial_value

INDICATORS = {
    "c_1": "売上高",
    "c_2": "営業利益",
    "c_3": "当期純利益",
    "c_29": "営業利益率",
    "c_6": "ROE",
    "c_7": "ROA",
    "c_11": "株主資本比率",
    "c_14": "有利子負債比率",
    "c_16": "営業CF",
    "c_19": "フリーCF"
}

def extract_year(dt_text):
    # YYYY/MM 形式を抽出して YYYY-MM に変換
    match = re.search(r'(\d{4})/(\d{2})', dt_text)
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}"

def fetch_data(stock_code):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    })
    
    # 1. Search page
    search_url = f"https://irbank.net/search/{stock_code}"
    res = session.get(search_url)
    if res.status_code != 200:
        return {"error": f"Failed to fetch search page. Status code {res.status_code}"}
        
    soup = BeautifulSoup(res.text, 'lxml')
    # Find the link to EDINET results
    edinet_link = None
    for a in soup.find_all('a'):
        if a.text == '決算' and 'results' in a.get('href', ''):
            edinet_link = a['href']
            break
            
    if not edinet_link:
        return {"error": f"Could not find exact result page link for code {stock_code}"}
        
    time.sleep(1.5)
    
    # 2. Results page
    results_url = f"https://irbank.net{edinet_link}"
    res2 = session.get(results_url)
    if res2.status_code != 200:
        return {"error": f"Failed to fetch results page. Status code {res2.status_code}"}
        
    soup2 = BeautifulSoup(res2.text, 'lxml')
    output_data = {}
    
    for code, name in INDICATORS.items():
        div = soup2.find('div', id=code)
        if not div:
            continue
        dl = div.find('dl', class_='gdl')
        if not dl:
            continue
        
        dts = dl.find_all('dt')
        dds = dl.find_all('dd')
        
        metric_data = {}
        for dt, dd in zip(dts, dds):
            year = extract_year(dt.get_text())
            if not year:
                continue
                
            text_span = dd.find('span', class_='text')
            if text_span:
                val_text = text_span.get_text()
            else:
                val_text = dd.get_text()
                
            val = parse_financial_value(val_text)
            metric_data[year] = val
            
        # 直近5年分を取得（YYYY-MM形式なので文字列ソートで正しく並ぶ）
        sorted_years = sorted(metric_data.keys())
        last_5 = sorted_years[-5:]
        
        output_data[name] = { y: metric_data[y] for y in last_5 }
        
    return output_data

if __name__ == "__main__":
    log_action("IR_fetch", sys.argv[1:])
    parser = argparse.ArgumentParser(description="Fetch and parse 5-year financial data from IRBANK.")
    parser.add_argument("--code", type=str, required=True, help="Stock code (e.g. 7203)")
    args = parser.parse_args()
    
    result = fetch_data(args.code)
    print(json.dumps(result, ensure_ascii=False, indent=2))
