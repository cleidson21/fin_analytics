from decimal import Decimal
from typing import List, Dict, Optional
from pydantic import BaseModel
from backend.domains.investments.engines.valuation_engine import ValuationResult

class AssetSummary(BaseModel):
    ticker: str
    market_value: Decimal
    cost_basis: Decimal
    unrealized_gain: Decimal
    unrealized_gain_percent: Decimal
    allocation_percent: Decimal

class InstitutionSummary(BaseModel):
    institution: str
    market_value: Decimal
    cost_basis: Decimal
    unrealized_gain: Decimal
    unrealized_gain_percent: Decimal
    allocation_percent: Decimal

class AssetClassSummary(BaseModel):
    asset_class: str
    market_value: Decimal
    cost_basis: Decimal
    unrealized_gain: Decimal
    unrealized_gain_percent: Decimal
    allocation_percent: Decimal

class WealthSummary(BaseModel):
    total_market_value: Decimal
    total_cost_basis: Decimal
    total_unrealized_gain: Decimal
    total_unrealized_gain_percent: Decimal
    asset_count: int
    institution_count: int
    by_asset: List[AssetSummary]
    by_institution: List[InstitutionSummary]
    by_class: List[AssetClassSummary]

class WealthEngine:
    """
    Motor de Consolidação Patrimonial Global (Wealth Engine).
    Agrega posições precificadas (ValuationResult) fornecendo 
    a macro-visão financeira do portfólio, com cálculos de alocação 
    e rentabilidade por agrupamentos.
    """
    def calculate(
        self,
        valuations: List[ValuationResult],
        asset_class_map: Optional[Dict[str, str]] = None
    ) -> WealthSummary:
        
        asset_class_map = asset_class_map or {}
        
        total_market_value = Decimal('0')
        total_cost_basis = Decimal('0')
        
        # Agregadores temporários
        # Key -> {"market_value": Decimal, "cost_basis": Decimal}
        agg_asset: Dict[str, Dict[str, Decimal]] = {}
        agg_inst: Dict[str, Dict[str, Decimal]] = {}
        agg_class: Dict[str, Dict[str, Decimal]] = {}
        
        for val in valuations:
            if val.quantity <= 0:
                continue
                
            mv = val.market_value
            cb = val.cost_basis
            
            total_market_value += mv
            total_cost_basis += cb
            
            ticker = val.ticker
            inst = val.institution
            a_class = asset_class_map.get(ticker, "UNKNOWN")
            
            # Init se não existir
            if ticker not in agg_asset:
                agg_asset[ticker] = {"market_value": Decimal('0'), "cost_basis": Decimal('0')}
            if inst not in agg_inst:
                agg_inst[inst] = {"market_value": Decimal('0'), "cost_basis": Decimal('0')}
            if a_class not in agg_class:
                agg_class[a_class] = {"market_value": Decimal('0'), "cost_basis": Decimal('0')}
                
            agg_asset[ticker]["market_value"] += mv
            agg_asset[ticker]["cost_basis"] += cb
            
            agg_inst[inst]["market_value"] += mv
            agg_inst[inst]["cost_basis"] += cb
            
            agg_class[a_class]["market_value"] += mv
            agg_class[a_class]["cost_basis"] += cb

        # Macro Ganhos
        total_gain = total_market_value - total_cost_basis
        total_gain_pct = Decimal('0')
        if total_cost_basis > 0:
            total_gain_pct = (total_gain / total_cost_basis) * Decimal('100')
        elif total_market_value > 0:
            total_gain_pct = Decimal('100')
            
        def _build_summary_list(agg_dict: Dict[str, Dict[str, Decimal]], DTOClass, key_name: str):
            res_list = []
            for k, v in agg_dict.items():
                g = v["market_value"] - v["cost_basis"]
                g_pct = Decimal('0')
                if v["cost_basis"] > 0:
                    g_pct = (g / v["cost_basis"]) * Decimal('100')
                elif v["market_value"] > 0:
                    g_pct = Decimal('100')
                    
                alloc_pct = Decimal('0')
                if total_market_value > 0:
                    alloc_pct = (v["market_value"] / total_market_value) * Decimal('100')
                    
                res_list.append(DTOClass(**{
                    key_name: k,
                    "market_value": v["market_value"],
                    "cost_basis": v["cost_basis"],
                    "unrealized_gain": g,
                    "unrealized_gain_percent": g_pct,
                    "allocation_percent": alloc_pct
                }))
            # Sort by allocation descending
            res_list.sort(key=lambda x: x.allocation_percent, reverse=True)
            return res_list
            
        return WealthSummary(
            total_market_value=total_market_value,
            total_cost_basis=total_cost_basis,
            total_unrealized_gain=total_gain,
            total_unrealized_gain_percent=total_gain_pct,
            asset_count=len(agg_asset),
            institution_count=len(agg_inst),
            by_asset=_build_summary_list(agg_asset, AssetSummary, "ticker"),
            by_institution=_build_summary_list(agg_inst, InstitutionSummary, "institution"),
            by_class=_build_summary_list(agg_class, AssetClassSummary, "asset_class")
        )
