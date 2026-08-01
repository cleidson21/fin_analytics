import os
import sys
import json
import time
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import requests

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        k, v = line.strip().split('=', 1)
                        os.environ[k] = v.strip('"\'')

def ensure_dirs():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports', 'pierre')
    raw_dir = os.path.join(base_dir, 'raw')
    structured_dir = os.path.join(base_dir, 'structured')
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(structured_dir, exist_ok=True)
    return base_dir, raw_dir, structured_dir

def fetch_data(api_key, start_date, end_date, fmt):
    url = 'https://www.pierre.finance/tools/api/get-transactions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    params = {
        'startDate': start_date.strftime('%Y-%m-%d'),
        'endDate': end_date.strftime('%Y-%m-%d'),
        'format': fmt
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def main():
    load_env()
    api_key = os.environ.get('PIERRE_API_KEY')
    if not api_key:
        print("PIERRE_API_KEY not found in .env")
        sys.exit(1)
        
    base_dir, raw_dir, structured_dir = ensure_dirs()
    
    today = date.today()
    periods = {
        '3m': today - relativedelta(months=3),
        '6m': today - relativedelta(months=6),
        '12m': today - relativedelta(months=12)
    }
    
    total_start_time = time.time()
    
    # Store the 12m raw payload for analysis
    payload_12m_raw = None
    
    for label, start_date in periods.items():
        print(f"Fetching data for {label} (from {start_date} to {today})...")
        
        # Raw
        start_req = time.time()
        raw_data = fetch_data(api_key, start_date, today, 'raw')
        raw_path = os.path.join(raw_dir, f'transactions_raw_{label}.json')
        with open(raw_path, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
            
        if label == '12m':
            payload_12m_raw = raw_data
            
        # Structured
        structured_data = fetch_data(api_key, start_date, today, 'structured')
        structured_path = os.path.join(structured_dir, f'transactions_structured_{label}.json')
        with open(structured_path, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
            
    total_duration = time.time() - total_start_time
    print(f"Export completed in {total_duration:.2f} seconds.")
    
    # Generate Report
    if payload_12m_raw:
        transactions = payload_12m_raw.get('data', [])
        
        accounts = set()
        categories = set()
        types = set()
        statuses = set()
        currencies = set()
        
        for t in transactions:
            accounts.add(t.get('account_name', 'Unknown'))
            categories.add(t.get('category') or 'None')
            types.add(t.get('type', 'Unknown'))
            statuses.add(t.get('status', 'Unknown'))
            currencies.add(t.get('currency_code', 'Unknown'))
            
        raw_12m_path = os.path.join(raw_dir, 'transactions_raw_12m.json')
        json_size_bytes = os.path.getsize(raw_12m_path)
        
        report = {
            "period": "12m",
            "start_date": periods['12m'].strftime('%Y-%m-%d'),
            "end_date": today.strftime('%Y-%m-%d'),
            "export_date": datetime.now().isoformat(),
            "execution_time_seconds": round(total_duration, 2),
            "json_size_bytes": json_size_bytes,
            "json_size_mb": round(json_size_bytes / (1024 * 1024), 2),
            "metrics": {
                "total_transactions": len(transactions),
                "distinct_accounts_count": len(accounts),
                "distinct_accounts": list(accounts),
                "distinct_categories_count": len(categories),
                "distinct_categories": list(categories),
                "distinct_types_count": len(types),
                "distinct_types": list(types),
                "distinct_statuses_count": len(statuses),
                "distinct_statuses": list(statuses),
                "distinct_currencies_count": len(currencies),
                "distinct_currencies": list(currencies)
            }
        }
        
        report_path = os.path.join(base_dir, 'report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"Report generated at {report_path}")

if __name__ == '__main__':
    main()
