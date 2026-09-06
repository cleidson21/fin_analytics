from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta

from backend.api.dependencies.auth import get_current_user
from backend.api.dependencies.database import get_db_session
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.infrastructure.persistence.models.wealth.portfolio_snapshot import PortfolioSnapshotModel

router = APIRouter(prefix="/investments", tags=["Investments"])

@router.get("/evolution/summary", response_model=Dict[str, Any])
async def get_evolution_summary(
    account_id: str = Query(None),
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Retorna o resumo da evolução patrimonial para o Dashboard.
    """
    # 1. Recuperar o último snapshot para os valores correntes e benchmarks acumulados
    stmt_latest = select(PortfolioSnapshotModel)
    if account_id:
        stmt_latest = stmt_latest.where(PortfolioSnapshotModel.account_id == account_id)
    stmt_latest = stmt_latest.order_by(PortfolioSnapshotModel.reference_month.desc()).limit(1)
    
    result_latest = await session.execute(stmt_latest)
    latest_snapshot = result_latest.scalar_one_or_none()

    if not latest_snapshot:
        return {
            "current_wealth": 0,
            "accumulated_return_pct": 0,
            "total_dividends": 0,
            "total_invested": 0,
            "ibov_acumulado": 0,
            "cdi_acumulado": 0
        }

    # 2. Somar proventos totais e calcular "total_invested"
    # SEMÂNTICA DE TOTAL INVESTED:
    # O frontend utiliza "total_invested" como base para calcular o Yield on Cost (YOC) geral da carteira.
    # Somar apenas "compras" ignora as "vendas", distorcendo o custo da carteira.
    # A aproximação mais correta usando a tabela portfolio_snapshots é o Capital Líquido Aportado (Compras - Vendas).
    
    stmt_sums = select(
        func.sum(PortfolioSnapshotModel.proventos).label("total_dividends"),
        func.sum(PortfolioSnapshotModel.compras).label("total_compras"),
        func.sum(PortfolioSnapshotModel.vendas).label("total_vendas")
    )
    if account_id:
        stmt_sums = stmt_sums.where(PortfolioSnapshotModel.account_id == account_id)
        
    result_sums = await session.execute(stmt_sums)
    sums = result_sums.fetchone()
    
    total_dividends = float(sums.total_dividends or 0)
    total_compras = float(sums.total_compras or 0)
    total_vendas = float(sums.total_vendas or 0)
    
    net_capital_invested = total_compras - total_vendas
    # Se o capital líquido ficar negativo (ex: sacou mais do que colocou e o lucro rendeu), travamos em 0 para não quebrar a UI
    total_invested = max(net_capital_invested, 0)

    # O backend salva pct_acumulada como decimal (0.05 para 5%).
    # O front espera um número formatado que ele mesmo não multiplica por 100 na maioria das vezes para exibição direta?
    # No history, o frontend renderiza: `${item.rentabilidade_acumulada_pct.toFixed(2)}%`
    # Então o front já espera que seja 5.0 (para 5%), e não 0.05.
    # Vamos multiplicar os valores pct por 100 para o front.
    
    def to_pct(val):
        return float(val * 100) if val is not None else 0.0

    accumulated_return_pct = to_pct(latest_snapshot.pct_acumulada)
    ibov_acumulado = to_pct(latest_snapshot.ibov_acumulado)
    cdi_acumulado = to_pct(latest_snapshot.cdi_acumulado)

    alpha_vs_ibov = accumulated_return_pct - ibov_acumulado
    alpha_vs_cdi = accumulated_return_pct - cdi_acumulado

    return {
        "current_wealth": float(latest_snapshot.patrimonio or 0),
        "accumulated_return_pct": accumulated_return_pct,
        "total_dividends": total_dividends,
        "total_invested": total_invested,
        "ibov_acumulado": ibov_acumulado,
        "cdi_acumulado": cdi_acumulado,
        "alpha_vs_ibov": alpha_vs_ibov,
        "alpha_vs_cdi": alpha_vs_cdi
    }

@router.get("/evolution/history", response_model=List[Dict[str, Any]])
async def get_evolution_history(
    account_id: str = Query(None),
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Retorna a série histórica da evolução patrimonial e benchmarks.
    O frontend espera um array de pontos mensais ordenados cronologicamente (crescente).
    """
    stmt = select(PortfolioSnapshotModel)
    if account_id:
        stmt = stmt.where(PortfolioSnapshotModel.account_id == account_id)
        
    # Ordenar por mês crescente
    stmt = stmt.order_by(PortfolioSnapshotModel.reference_month.asc())
    
    result = await session.execute(stmt)
    rows = result.scalars().all()
    
    def to_pct(val):
        return float(val * 100) if val is not None else 0.0

    history = []
    for row in rows:
        history.append({
            "month": row.reference_month,
            "patrimonio": str(row.patrimonio or 0),
            "patrimonio_value": float(row.patrimonio or 0),
            "compras": str(row.compras or 0),
            "compras_value": float(row.compras or 0),
            "vendas": str(row.vendas or 0),
            "vendas_value": float(row.vendas or 0),
            "proventos": str(row.proventos or 0),
            "proventos_value": float(row.proventos or 0),
            "rentabilidade_mensal_pct": to_pct(row.pct_mensal),
            "rentabilidade_acumulada_pct": to_pct(row.pct_acumulada),
            "ibov_mensal_pct": to_pct(row.ibov_mensal),
            "ibov_acumulado_pct": to_pct(row.ibov_acumulado),
            "cdi_mensal_pct": to_pct(row.cdi_mensal),
            "cdi_acumulado_pct": to_pct(row.cdi_acumulado),
            "ipca_mensal_pct": to_pct(row.ipca_mensal),
            "ipca_acumulado_pct": to_pct(row.ipca_acumulado),
            "ifix_mensal_pct": to_pct(row.ifix_mensal),
            "ifix_acumulado_pct": to_pct(row.ifix_acumulado),
            "sp500_mensal_pct": to_pct(row.sp_mensal),
            "sp500_acumulado_pct": to_pct(row.sp_acumulado),
            "idiv_mensal_pct": to_pct(row.idiv_mensal),
            "idiv_acumulado_pct": to_pct(row.idiv_acumulado),
        })
        
    return history

from backend.infrastructure.persistence.models.wealth.position_snapshot import PositionSnapshotModel
from backend.infrastructure.persistence.models.wealth.asset import AssetModel
from backend.application.services.market_data_service import market_data_service

@router.get("/dashboard/allocation", response_model=Dict[str, Any])
async def get_dashboard_allocation(
    account_id: str = Query(None),
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Retorna os dados de alocação de carteira (Score de diversificação e insights de risco).
    Filtra as posições pelo mês de referência mais recente que o usuário possui.
    Considera apenas quantity > 0.
    """
    # Descobrir o mês de referência mais recente
    stmt_latest_month = select(func.max(PositionSnapshotModel.reference_date))
    if account_id:
        stmt_latest_month = stmt_latest_month.where(PositionSnapshotModel.account_id == account_id)
        
    result_month = await session.execute(stmt_latest_month)
    latest_month = result_month.scalar_one_or_none()

    if not latest_month:
        return {"by_class": [], "by_asset": []}

    # Buscar as posições vigentes (quantity > 0)
    stmt = select(PositionSnapshotModel, AssetModel).join(
        AssetModel, PositionSnapshotModel.asset_id == AssetModel.id
    ).where(
        PositionSnapshotModel.reference_date == latest_month,
        PositionSnapshotModel.quantity > 0
    )
    
    if account_id:
        stmt = stmt.where(PositionSnapshotModel.account_id == account_id)
        
    result = await session.execute(stmt)
    rows = result.all()
    
    by_asset = []
    class_aggregation = {}
    total_market_value = 0.0
    
    # 1st pass: collect assets and total value
    for pos, asset in rows:
        qty = float(pos.quantity or 0)
        avg_p = float(pos.avg_price or 0)
        invested_value = qty * avg_p
        
        # Current Value da API governada, mantendo nulo se não houver
        market_value = float(pos.current_value) if pos.current_value is not None else None
        
        market_price = None
        price_date = None
        market_data_provider = "GOVERNANCE"
        has_market_value = market_value is not None

        # FASE 6 & 7: Market Data Fallback se Governança não tiver valor
        if market_value is None and asset.asset_class in ["STOCK", "FII", "BDR", "ETF_GLOBAL", "CRYPTO"]:
            quote = market_data_service.get_quote(asset.ticker, asset.asset_class)
            if quote:
                market_price = float(quote.price)
                market_value = market_price * qty
                has_market_value = True
                market_data_provider = quote.provider
                price_date = quote.price_date.isoformat() if quote.price_date else None
        
        # Para fins de agregação de peso da carteira, usamos o valor investido como proxy se market_value for nulo
        val_for_agg = market_value if market_value is not None else invested_value
        total_market_value += val_for_agg
        
        asset_class = asset.asset_class or "Outros"
        if asset_class not in class_aggregation:
            class_aggregation[asset_class] = 0.0
        class_aggregation[asset_class] += val_for_agg
        
        by_asset.append({
            "name": asset.ticker or "Desconhecido",
            "asset_class": asset_class,
            "quantity": qty,
            "avg_price": avg_p,
            "invested_value": invested_value,
            "market_value": market_value,
            "market_price": market_price,
            "market_data_provider": market_data_provider,
            "price_date": price_date,
            "has_market_value": has_market_value
        })

    # 2nd pass: calculate weights and format
    formatted_by_asset = []
    for item in by_asset:
        val_for_weight = item["market_value"] if item["market_value"] is not None else item["invested_value"]
        allocation_pct = (val_for_weight / total_market_value * 100) if total_market_value > 0 else 0.0
        
        profit = None
        if item["market_value"] is not None:
            profit = item["market_value"] - item["invested_value"]
            
        formatted_by_asset.append({
            "name": item["name"],
            "asset_class": item["asset_class"],
            "quantity": item["quantity"],
            "avg_price": item["avg_price"],
            "invested_value": item["invested_value"],
            "market_value": item["market_value"],
            "profit": profit,
            "allocation_percent": allocation_pct,
            "market_price": item["market_price"],
            "market_data_provider": item["market_data_provider"],
            "price_date": item["price_date"],
            "has_market_value": item["has_market_value"]
        })
        
    formatted_by_class = []
    for k, v in class_aggregation.items():
        formatted_by_class.append({
            "name": k,
            "market_value": v
        })
        
    return {
        "by_class": formatted_by_class,
        "by_asset": formatted_by_asset
    }

from backend.infrastructure.persistence.models.wealth.income_event import IncomeEventModel

@router.get("/dividends/history", response_model=List[Dict[str, Any]])
async def get_dividends_history(
    account_id: str = Query(None),
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Retorna todo o histórico de eventos de proventos do usuário.
    O frontend fará o agrupamento mensal e filtragem YTD de acordo com sua necessidade.
    """
    stmt = select(IncomeEventModel)
    if account_id:
        stmt = stmt.where(IncomeEventModel.account_id == account_id)
        
    stmt = stmt.order_by(IncomeEventModel.payment_date.asc())
    
    result = await session.execute(stmt)
    rows = result.scalars().all()
    
    events = []
    for row in rows:
        events.append({
            "data_pagamento": row.payment_date.isoformat() if row.payment_date else None,
            "valor": float(row.gross_amount or 0),
            "tipo_evento": row.event_type if row.event_type else None
        })
        
    return events

@router.get("/dividends/breakdown", response_model=List[Dict[str, Any]])
async def get_dividends_breakdown(
    account_id: str = Query(None),
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Retorna o total recebido agrupado por ativo.
    """
    stmt = select(
        AssetModel.ticker,
        func.sum(IncomeEventModel.gross_amount).label("total_received")
    ).join(
        AssetModel, IncomeEventModel.asset_id == AssetModel.id
    )
    
    if account_id:
        stmt = stmt.where(IncomeEventModel.account_id == account_id)
        
    stmt = stmt.group_by(AssetModel.ticker).order_by(func.sum(IncomeEventModel.gross_amount).desc())
    
    result = await session.execute(stmt)
    rows = result.all()
    
    breakdown = []
    for ticker, total in rows:
        breakdown.append({
            "ticker": ticker or "Desconhecido",
            "total_received": float(total or 0)
        })
        
    return breakdown

@router.get("/asset/{ticker}", response_model=Dict[str, Any])
async def get_asset_detail(
    ticker: str,
    account_id: str = Query(None),
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Retorna os detalhes de um ativo específico, combinando dados governados (posição, custo, proventos)
    com enriquecimento de mercado (MarketDataService) para cotação e histórico, sem persistir mercado.
    """
    # 1. Encontrar o Asset pelo Ticker
    stmt_asset = select(AssetModel).where(AssetModel.ticker == ticker)
    result_asset = await session.execute(stmt_asset.limit(1))
    asset = result_asset.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
        
    # 2. Obter a posição mais recente vinculada a uma conta do usuário
    stmt_pos = select(PositionSnapshotModel).where(
        PositionSnapshotModel.asset_id == asset.id
    ).order_by(PositionSnapshotModel.reference_date.desc()).limit(1)
    
    if account_id:
        stmt_pos = stmt_pos.where(PositionSnapshotModel.account_id == account_id)
        
    result_pos = await session.execute(stmt_pos)
    pos = result_pos.scalar_one_or_none()
    
    if not pos:
        raise HTTPException(status_code=404, detail="Ativo não encontrado na carteira do usuário")
    
    qty = float(pos.quantity or 0) if pos else 0.0
    avg_price = float(pos.avg_price or 0) if pos else 0.0
    invested_value = qty * avg_price
    
    # 3. Market Data (Valuation)
    current_value_governed = float(pos.current_value) if (pos and pos.current_value is not None) else None
    
    market_price = None
    market_value = None
    gain = 0.0
    
    if current_value_governed is not None:
        market_value = current_value_governed
        if qty > 0:
            market_price = market_value / qty
        gain = market_value - invested_value
    else:
        # Market Data Enrichment
        if asset.asset_class in ["STOCK", "FII", "BDR", "ETF_GLOBAL", "CRYPTO"]:
            quote = market_data_service.get_quote(asset.ticker, asset.asset_class)
            if quote:
                market_price = float(quote.price)
                market_value = market_price * qty
                gain = market_value - invested_value

    # 4. Peso no portfólio (Aproximação: buscar patrimônio do último snapshot)
    stmt_port = select(PortfolioSnapshotModel.patrimonio).order_by(
        PortfolioSnapshotModel.reference_month.desc()
    ).limit(1)
    
    if account_id:
        stmt_port = stmt_port.where(PortfolioSnapshotModel.account_id == account_id)
        
    result_port = await session.execute(stmt_port)
    total_wealth = float(result_port.scalar_one_or_none() or 0)
    
    peso = 0.0
    if total_wealth > 0 and market_value is not None:
        peso = (market_value / total_wealth) * 100
    elif total_wealth > 0:
        peso = (invested_value / total_wealth) * 100

    # 5. Proventos (Income Events)
    stmt_income = select(IncomeEventModel).where(IncomeEventModel.asset_id == asset.id)
    result_income = await session.execute(stmt_income)
    income_rows = result_income.scalars().all()
    
    total_dividends = 0.0
    last_12m_dividends = 0.0
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    
    dividend_items = []
    for inc in income_rows:
        val = float(inc.gross_amount or 0)
        total_dividends += val
        
        # Considerar a conversão segura para data
        inc_date = None
        if isinstance(inc.payment_date, datetime):
            inc_date = inc.payment_date
        elif inc.payment_date:
            from datetime import date
            if isinstance(inc.payment_date, date):
                inc_date = datetime.combine(inc.payment_date, datetime.min.time())
                
        if inc_date and inc_date >= one_year_ago:
            last_12m_dividends += val
            
        dividend_items.append({
            "data": inc_date.strftime("%Y-%m-%d") if inc_date else None,
            "valor": val,
            "tipo": inc.event_type
        })
        
    yoc = (total_dividends / invested_value * 100) if invested_value > 0 else 0.0
    
    # Ordenar dividendos decrescente por data para o frontend
    dividend_items.sort(key=lambda x: x["data"] or "", reverse=True)

    # 6. Histórico de Mercado (Read Model apenas)
    history_data = []
    if market_price is not None:
        # Se temos preço atual, tentamos buscar histórico
        hist = market_data_service.get_history(asset.ticker, asset.asset_class, period="1y")
        history_data = hist
        
    market_data_available = len(history_data) > 0

    # 7. Indicadores Fundamentalistas
    indicators_data = {}
    if asset.asset_class in ["STOCK", "FII", "BDR", "ETF_GLOBAL"]:
        indicators_data = market_data_service.get_indicators(asset.ticker, asset.asset_class)
        
    indicators_available = len(indicators_data) > 0

    # 8. Marcos Históricos (Timeline)
    timeline = []
    
    # 8.1 Primeiro Aporte
    stmt_first_pos = select(PositionSnapshotModel).where(
        PositionSnapshotModel.asset_id == asset.id,
        PositionSnapshotModel.quantity > 0
    ).order_by(PositionSnapshotModel.reference_date.asc()).limit(1)
    if account_id:
        stmt_first_pos = stmt_first_pos.where(PositionSnapshotModel.account_id == account_id)
        
    result_first_pos = await session.execute(stmt_first_pos)
    first_pos = result_first_pos.scalar_one_or_none()
    
    if first_pos:
        timeline.append({
            "date": first_pos.reference_date,
            "title": "Primeiro Aporte",
            "description": f"Início da posição em {asset.ticker}",
            "type": "compra"
        })
        
    # 8.2 Primeiro e Maior Provento
    from datetime import date
    def format_date(d):
        if isinstance(d, datetime): return d.strftime("%Y-%m-%d")
        if isinstance(d, date): return d.strftime("%Y-%m-%d")
        return str(d)

    valid_incomes = [inc for inc in income_rows if inc.payment_date]
    if valid_incomes:
        # Sort by date asc
        sorted_incomes = sorted(valid_incomes, key=lambda x: x.payment_date if isinstance(x.payment_date, datetime) else datetime.combine(x.payment_date, datetime.min.time()))
        first_inc = sorted_incomes[0]
        
        timeline.append({
            "date": format_date(first_inc.payment_date),
            "title": "Primeiro Provento",
            "description": f"Recebeu {first_inc.event_type} de R$ {float(first_inc.gross_amount or 0):.2f}",
            "type": "provento"
        })
        
        # Maior provento
        max_inc = max(valid_incomes, key=lambda x: float(x.gross_amount or 0))
        if max_inc != first_inc and float(max_inc.gross_amount or 0) > float(first_inc.gross_amount or 0):
            timeline.append({
                "date": format_date(max_inc.payment_date),
                "title": "Recorde de Provento",
                "description": f"Maior pagamento de {max_inc.event_type} (R$ {float(max_inc.gross_amount or 0):.2f})",
                "type": "provento_recorde"
            })
            
    # 8.3 Marcos de Valorização (se houver lucro)
    if invested_value > 0 and gain > 0:
        gain_pct = (gain / invested_value) * 100
        if gain_pct >= 50:
            timeline.append({
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "title": "Super Valorização",
                "description": f"Ativo atingiu mais de 50% de ganho de capital",
                "type": "gain_50"
            })
        elif gain_pct >= 20:
            timeline.append({
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "title": "Ótima Valorização",
                "description": f"Ativo atingiu mais de 20% de ganho de capital",
                "type": "gain_20"
            })
        elif gain_pct >= 10:
            timeline.append({
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "title": "Boa Valorização",
                "description": f"Ativo rompeu a marca de 10% de ganho",
                "type": "gain_10"
            })

    # Sort timeline by date descending
    timeline.sort(key=lambda x: x["date"], reverse=True)

    return {
        "position": {
            "ticker": asset.ticker,
            "quantidade": qty,
            "preco_medio": avg_price,
            "valor_investido": invested_value,
            "preco_atual": market_price or 0.0,
            "valor_atual": market_value or 0.0,
            "ganho": gain,
            "asset_class": asset.asset_class or "Desconhecido",
            "asset_subclass": "N/A",
            "peso": peso
        },
        "market_data": {
            "available": market_data_available,
            "history": history_data
        },
        "indicators": {
            "available": indicators_available,
            "indicators": indicators_data
        },
        "dividends": {
            "items": dividend_items,
            "kpis": {
                "total": total_dividends,
                "last_12m": last_12m_dividends,
                "yoc": yoc
            }
        },
        "timeline": timeline
    }
