import csv
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
import bisect

class MarketDataRepository:
    """
    Repositório de dados de mercado para carregar e consultar 
    séries históricas de benchmarks (IBOV, CDI, etc.) em memória.
    Acesso O(log N) usando busca binária (bisect).
    """
    
    _cache: Dict[str, List[tuple[date, Decimal]]] = {}
    _loaded: bool = False

    def __init__(self, data_dir: str = "database/benchmarks"):
        self.data_dir = data_dir
        if not self.__class__._loaded:
            self._load_all_csvs()
            self.__class__._loaded = True

    def _load_all_csvs(self):
        benchmarks = ["ibov", "ifix", "cdi", "ipca", "idiv", "sp500"]
        for b in benchmarks:
            file_path = os.path.join(self.data_dir, f"{b}.csv")
            self.__class__._cache[b] = []
            if os.path.exists(file_path):
                with open(file_path, mode='r', encoding='utf-8') as csv_file:
                    reader = csv.DictReader(csv_file)
                    # Exemplo: date,value
                    data_points = []
                    for row in reader:
                        d_str = row.get("date")
                        v_str = row.get("value", "0")
                        if d_str:
                            d = datetime.strptime(d_str, "%Y-%m-%d").date()
                            v = Decimal(v_str)
                            data_points.append((d, v))
                    # Ordenar por data cronologicamente
                    data_points.sort(key=lambda x: x[0])
                    self.__class__._cache[b] = data_points

    def get_by_date(self, benchmark: str, target_date: date) -> Decimal:
        """
        Retorna o valor exato ou o mais próximo anterior à data especificada.
        Complexidade O(log N).
        """
        series = self.__class__._cache.get(benchmark, [])
        if not series:
            return Decimal("0.0")

        # Busca binária
        keys = [pt[0] for pt in series]
        idx = bisect.bisect_right(keys, target_date)
        
        if idx == 0:
            # target_date é antes do primeiro registro
            return Decimal("0.0")
            
        return series[idx - 1][1]

    def get_interval(self, benchmark: str, start_date: date, end_date: date) -> List[tuple[date, Decimal]]:
        """
        Busca por intervalo O(log N).
        """
        series = self.__class__._cache.get(benchmark, [])
        if not series:
            return []
            
        keys = [pt[0] for pt in series]
        idx_start = bisect.bisect_left(keys, start_date)
        idx_end = bisect.bisect_right(keys, end_date)
        
        return series[idx_start:idx_end]
