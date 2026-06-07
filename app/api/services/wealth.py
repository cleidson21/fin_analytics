from typing import List

from app.api.schemas.investments import (
    AssetAllocation,
    DividendBreakdown,
    DividendHistory,
    NetWorthEvolution,
    PositionDetail,
    PortfolioEvolutionPoint,
    PortfolioEvolutionSummary,
)
from app.core.formatters import format_money
from database.queries import FinancialQueries


class WealthAnalyticsService:
    def __init__(self):
        self.queries = FinancialQueries()
        # TODO: Future integration point for MarketDataService
        # self.market_data_service = MarketDataService() 
        # This will allow injecting real-time prices, USD conversion, and YFinance fundamental data
        # without modifying the public methods exposed to the controllers.

    def get_dividend_history(self) -> List[DividendHistory]:
        df = self.queries.get_dividend_history()
        if df.empty:
            return []
        
        records = df.to_dict(orient="records")
        return [
            DividendHistory(
                month=r["month"],
                amount_received=format_money(r["amount_received"]),
                amount_received_value=float(r["amount_received"]),
                amount_dividend=format_money(r["amount_dividend"]) if "amount_dividend" in r else None,
                amount_dividend_value=float(r["amount_dividend"]) if "amount_dividend" in r else 0.0,
                amount_jcp=format_money(r["amount_jcp"]) if "amount_jcp" in r else None,
                amount_jcp_value=float(r["amount_jcp"]) if "amount_jcp" in r else 0.0,
                amount_rendimento=format_money(r["amount_rendimento"]) if "amount_rendimento" in r else None,
                amount_rendimento_value=float(r["amount_rendimento"]) if "amount_rendimento" in r else 0.0,
            )
            for r in records
        ]

    def get_portfolio_allocation(self) -> List[AssetAllocation]:
        df = self.queries.get_portfolio_allocation()
        if df.empty:
            return []
        
        records = df.to_dict(orient="records")
        return [
            AssetAllocation(
                asset_class=r["asset_class"],
                current_total=format_money(r["current_total"]),
                current_total_value=float(r["current_total"])
            )
            for r in records
        ]

    def get_net_worth_evolution(self) -> List[NetWorthEvolution]:
        df = self.queries.get_net_worth_history()
        if df.empty:
            return []

        records = df.to_dict(orient="records")
        return [
            NetWorthEvolution(
                month=r["month"],
                net_worth=format_money(r["net_worth"]),
                net_worth_value=float(r["net_worth"])
            )
            for r in records
        ]

    def get_detailed_positions(self) -> List[PositionDetail]:
        df = self.queries.get_detailed_positions()
        if df.empty:
            return []

        records = df.to_dict(orient="records")
        return [
            PositionDetail(
                ticker=r["ticker"],
                asset_class=r.get("asset_class", "Outros"),
                asset_subclass=r.get("asset_subclass", ""),
                quantidade=str(r["quantidade"]),
                preco_medio=format_money(r["preco_medio"]),
                valor_investido=format_money(r["valor_investido"]),
                valor_atual=format_money(r["valor_atual"]),
                ganho=format_money(r["ganho"]),
                peso_percentual=f"{float(r['peso_percentual']):.2f}%",
                quantidade_value=float(r["quantidade"]),
                preco_medio_value=float(r["preco_medio"]),
                valor_investido_value=float(r["valor_investido"]),
                valor_atual_value=float(r["valor_atual"]),
                ganho_value=float(r["ganho"]),
                peso_percentual_value=float(r["peso_percentual"])
            )
            for r in records
        ]

    def get_dividends_by_asset(self) -> List[DividendBreakdown]:
        df = self.queries.get_dividends_by_asset()
        if df.empty:
            return []

        records = df.to_dict(orient="records")
        return [
            DividendBreakdown(
                ticker=r["ticker"],
                total_recebido=format_money(r["total_recebido"]),
                quantidade_eventos=int(r["quantidade_eventos"]),
                primeiro_recebimento=str(r["primeiro_recebimento"]),
                ultimo_recebimento=str(r["ultimo_recebimento"]),
                total_recebido_value=float(r["total_recebido"])
            )
            for r in records
        ]

    def get_portfolio_evolution_history(self) -> List[PortfolioEvolutionPoint]:
        df = self.queries.get_portfolio_evolution_history()
        if df.empty:
            return []

        records = df.to_dict(orient="records")
        return [
            PortfolioEvolutionPoint(
                month=r["month"],
                patrimonio=format_money(r["patrimonio"]),
                patrimonio_value=float(r["patrimonio"]),
                compras=format_money(r["compras"]),
                compras_value=float(r["compras"]),
                vendas=format_money(r["vendas"]),
                vendas_value=float(r["vendas"]),
                proventos=format_money(r["proventos"]),
                proventos_value=float(r["proventos"]),
                rentabilidade_mensal_pct=float(r["rentabilidade_mensal_pct"]),
                rentabilidade_acumulada_pct=float(r["rentabilidade_acumulada_pct"]),
                ibov_mensal_pct=float(r["ibov_mensal_pct"]),
                ibov_acumulado_pct=float(r["ibov_acumulado_pct"]),
                cdi_mensal_pct=float(r["cdi_mensal_pct"]),
                cdi_acumulado_pct=float(r["cdi_acumulado_pct"]),
                ipca_mensal_pct=float(r["ipca_mensal_pct"]),
                ipca_acumulado_pct=float(r["ipca_acumulado_pct"]),
                ifix_mensal_pct=float(r["ifix_mensal_pct"]),
                ifix_acumulado_pct=float(r["ifix_acumulado_pct"]),
                sp500_mensal_pct=float(r["sp500_mensal_pct"]),
                sp500_acumulado_pct=float(r["sp500_acumulado_pct"]),
                idiv_mensal_pct=float(r["idiv_mensal_pct"]),
                idiv_acumulado_pct=float(r["idiv_acumulado_pct"])
            )
            for r in records
        ]

    def get_portfolio_evolution_summary(self) -> PortfolioEvolutionSummary:
        summary_dict = self.queries.get_portfolio_evolution_summary()
        
        rent_acum = summary_dict["rentabilidade_acumulada"]
        ibov_acum = summary_dict["ibov_acumulado_pct"]
        cdi_acum = summary_dict["cdi_acumulado_pct"]
        
        alpha_vs_ibov = rent_acum - ibov_acum
        alpha_vs_cdi = rent_acum - cdi_acum
        
        return PortfolioEvolutionSummary(
            patrimonio_atual=format_money(summary_dict["patrimonio_atual"]),
            patrimonio_atual_value=float(summary_dict["patrimonio_atual"]),
            rentabilidade_acumulada=rent_acum,
            proventos_totais=float(summary_dict["proventos_totais"]),
            compras_totais=float(summary_dict["compras_totais"]),
            vendas_totais=float(summary_dict["vendas_totais"]),
            ibov_acumulado_pct=ibov_acum,
            cdi_acumulado_pct=cdi_acum,
            alpha_vs_ibov=alpha_vs_ibov,
            alpha_vs_cdi=alpha_vs_cdi
        )

    def get_asset_details(self, ticker: str) -> dict:
        """Consolida as informações do ativo (posições, histórico de preços, indicadores, proventos, timeline)."""
        from app.api.services.market_data import get_asset_history, get_asset_indicators
        from fastapi import HTTPException
        
        # 1. Posição
        position = self.queries.get_asset_position(ticker)
        if not position:
            raise HTTPException(status_code=404, detail="Ativo não encontrado na carteira.")
            
        # Para saber o peso, precisamos do valor_atual de todas as posições
        all_positions = self.queries.get_detailed_positions()
        total_wallet = float(all_positions["valor_atual"].sum()) if not all_positions.empty and "valor_atual" in all_positions else 0.0
        peso = (position["valor_atual"] / total_wallet * 100) if total_wallet > 0 else 0
        position["peso"] = peso
        
        # 2. Market Data e Indicadores
        market_history = get_asset_history(ticker)
        indicators = get_asset_indicators(ticker)
        
        # 3. Proventos
        dividends = self.queries.get_asset_dividends(ticker)
        
        # KPI Proventos: Total e 12 Meses
        total_dividends = sum(d["valor"] for d in dividends)
        
        # Soma os últimos 12 proventos recebidos
        dividends_12m = sum(d["valor"] for d in dividends[:12])
        
        yoc = (total_dividends / position["valor_investido"] * 100) if position["valor_investido"] > 0 else 0
        
        # 4. Timeline
        timeline = self.queries.get_asset_timeline(ticker)
        
        return {
            "position": position,
            "market_data": market_history,
            "indicators": indicators,
            "dividends": {
                "items": dividends,
                "kpis": {
                    "total": total_dividends,
                    "last_12m": dividends_12m,
                    "yoc": yoc
                }
            },
            "timeline": timeline
        }
