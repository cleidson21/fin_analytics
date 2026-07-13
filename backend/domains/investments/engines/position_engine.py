from decimal import Decimal
from typing import List, Dict, Optional
from pydantic import BaseModel
from collections import defaultdict
from backend.domains.investments.dto import TradeDTO, PositionSnapshot, TradeType

class PositionResult(BaseModel):
    ticker: str
    institution: str
    quantity: Decimal
    average_price: Decimal
    invested_value: Decimal
    snapshot_quantity: Optional[Decimal] = None
    divergence_quantity: Decimal = Decimal('0')

class PositionEngine:
    """
    Motor de Consolidação Patrimonial Puro.
    Processa um log cronológico de eventos financeiros para derivar
    a posição atual (quantidade, custo médio e valor investido), e
    reconcilia com o último PositionSnapshot da instituição.
    """
    def calculate_position(
        self,
        trades: List[TradeDTO],
        snapshots: List[PositionSnapshot]
    ) -> List[PositionResult]:
        
        # Agrupa trades por (institution, ticker)
        grouped_trades = defaultdict(list)
        for t in trades:
            grouped_trades[(t.broker, t.ticker)].append(t)
            
        # Agrupa snapshots pegando o mais recente por (institution, ticker)
        latest_snapshots = {}
        for s in snapshots:
            key = (s.institution, s.ticker)
            if key not in latest_snapshots or s.reference_date > latest_snapshots[key].reference_date:
                latest_snapshots[key] = s
                
        results = []
        
        # Todas as chaves possíveis
        all_keys = set(grouped_trades.keys()).union(set(latest_snapshots.keys()))
        
        for broker, ticker in all_keys:
            asset_trades = grouped_trades.get((broker, ticker), [])
            # Sort chronologically by trade_date, then created_at to guarantee determinism
            asset_trades.sort(key=lambda t: (t.trade_date, t.created_at))
            
            qty = Decimal('0')
            avg_price = Decimal('0')
            invested = Decimal('0')
            
            for trade in asset_trades:
                if trade.operation_type in (TradeType.BUY, TradeType.INITIAL_POSITION, TradeType.TRANSFER_IN):
                    new_qty = qty + trade.quantity
                    if new_qty > 0:
                        # Para TRANSFER_IN ou BUY o unit_price é assumido ser o custo. 
                        # Se for TRANSFER_IN de corretora x para y, o unit_price carrega o custo de aquisição.
                        new_invested = invested + (trade.quantity * trade.unit_price)
                        avg_price = new_invested / new_qty
                        invested = new_invested
                    qty = new_qty
                    
                elif trade.operation_type in (TradeType.SELL, TradeType.TRANSFER_OUT):
                    new_qty = qty - trade.quantity
                    # O custo médio NÃO muda numa venda/saída.
                    # O valor investido residual diminui na proporção da saída.
                    invested = new_qty * avg_price if new_qty > 0 else Decimal('0')
                    qty = new_qty
                    if qty <= 0:
                        avg_price = Decimal('0')
                        invested = Decimal('0')
                        
                elif trade.operation_type == TradeType.AMORTIZATION:
                    # Amortização reduz o custo médio e devolve capital, sem alterar quantidade
                    invested = invested - (trade.quantity * trade.unit_price)
                    if invested < 0:
                        invested = Decimal('0')
                    if qty > 0:
                        avg_price = invested / qty
                        
                elif trade.operation_type in (TradeType.SPLIT, TradeType.BONUS_SHARE):
                    # Aumenta quantidade sem injetar capital (Custo médio cai proporcionalmente)
                    qty = qty + trade.quantity
                    if qty > 0:
                        avg_price = invested / qty
                        
                elif trade.operation_type == TradeType.REVERSE_SPLIT:
                    # Diminui quantidade, capital se mantém (Custo médio sobe proporcionalmente)
                    qty = qty - trade.quantity
                    if qty > 0:
                        avg_price = invested / qty
                    elif qty <= 0:
                        avg_price = Decimal('0')
                        invested = Decimal('0')
                        
            # Reconciliação
            snapshot = latest_snapshots.get((broker, ticker))
            snap_qty = snapshot.quantity if snapshot else None
            div_qty = (snap_qty - qty) if snap_qty is not None else Decimal('0')
            
            results.append(PositionResult(
                ticker=ticker,
                institution=broker,
                quantity=qty,
                average_price=avg_price,
                invested_value=invested,
                snapshot_quantity=snap_qty,
                divergence_quantity=div_qty
            ))
            
        # Opcional: ordenar os resultados para testes determinísticos
        results.sort(key=lambda x: (x.institution, x.ticker))
        return results
