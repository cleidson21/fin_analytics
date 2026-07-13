import os
import csv
from typing import Dict, List, Tuple
from datetime import date
from decimal import Decimal
import threading

class HistoricalPriceRepository:
    def __init__(self, data_dir: str = "database/prices"):
        self.data_dir = data_dir
        self._cache: Dict[str, List[Tuple[date, Decimal]]] = {}
        self._lock = threading.Lock()
        self._load_all_csvs()

    def _load_all_csvs(self):
        with self._lock:
            if not os.path.exists(self.data_dir):
                return
            for filename in os.listdir(self.data_dir):
                if filename.endswith(".csv"):
                    ticker = filename.replace(".csv", "")
                    file_path = os.path.join(self.data_dir, filename)
                    prices = []
                    with open(file_path, mode='r', encoding='utf-8') as file:
                        reader = csv.DictReader(file)
                        for row in reader:
                            try:
                                dt_str = row['date']
                                y, m, d = map(int, dt_str.split('-'))
                                dt = date(y, m, d)
                                close_val = Decimal(row['close'])
                                prices.append((dt, close_val))
                            except Exception:
                                continue
                    prices.sort(key=lambda x: x[0])
                    self._cache[ticker] = prices

    def get_price_series(self, ticker: str) -> List[Tuple[date, Decimal]]:
        return self._cache.get(ticker, [])
