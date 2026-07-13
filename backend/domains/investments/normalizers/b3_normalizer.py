import hashlib
from datetime import date
from decimal import Decimal
from typing import List, Union
from backend.domains.investments.dto import PositionSnapshot, AssetTypeEnum
from backend.domains.investments.parsers.dto import (
    RawB3StockPosition, RawB3FundPosition, RawB3TreasuryPosition
)

class B3CustodyNormalizer:
    """
    Normalizer responsável por converter DTOs brutos da B3 (gerados pelo Parser)
    em instâncias maduras de PositionSnapshot.
    
    Responsabilidades:
    - Normalizar campos essenciais (ticker, institution, numéricos).
    - Mapear AssetTypeEnum corretamente.
    - Gerar o snapshot_hash (identity).
    
    Limitações Arquiteturais Intencionais (Fase 1D):
    - NÃO acessa banco (Zero ORM).
    - NÃO cruza dados com fontes externas (Ex: MyProfit).
    - NÃO faz merge ou dedup.
    """
    
    def normalize_stock(self, raw: RawB3StockPosition, reference_date: date) -> PositionSnapshot:
        ticker = self._normalize_ticker(raw.codigo_negociacao)
        institution = self._normalize_institution(raw.instituicao)
        
        # B3 separa "Ações" de "Fundos", porém ETFs e BDRs muitas vezes vêm na aba "Ações"
        # Sem consulta a API externa, consideramos tudo STOCK, ou FII se for óbvio (B3 já manda em aba separada).
        asset_type = AssetTypeEnum.STOCK
        if raw.tipo and "BDR" in raw.tipo.upper():
            asset_type = AssetTypeEnum.BDR
        elif raw.tipo and "ETF" in raw.tipo.upper():
            asset_type = AssetTypeEnum.ETF
            
        return PositionSnapshot(
            source_system="B3_AREA_INVESTIDOR",
            reference_date=reference_date,
            ticker=ticker,
            asset_type=asset_type,
            institution=institution,
            quantity=raw.quantidade,
            unit_price=raw.preco_fechamento,
            total_value=raw.valor_atualizado,
            snapshot_hash=self._generate_hash(reference_date, ticker, institution),
            metadata={
                "original_ticker": raw.codigo_negociacao,
                "cnpj_empresa": raw.cnpj_empresa,
                "codigo_isin": raw.codigo_isin,
                "tipo": raw.tipo,
                "motivo": raw.motivo
            }
        )

    def normalize_fund(self, raw: RawB3FundPosition, reference_date: date) -> PositionSnapshot:
        ticker = self._normalize_ticker(raw.codigo_negociacao)
        institution = self._normalize_institution(raw.instituicao)
        
        # Na aba de "Posição - Fundos", a imensa maioria é FII ou fundo fechado.
        asset_type = AssetTypeEnum.FII
        if raw.tipo and "ETF" in raw.tipo.upper():
            asset_type = AssetTypeEnum.ETF
            
        return PositionSnapshot(
            source_system="B3_AREA_INVESTIDOR",
            reference_date=reference_date,
            ticker=ticker,
            asset_type=asset_type,
            institution=institution,
            quantity=raw.quantidade,
            unit_price=raw.preco_fechamento,
            total_value=raw.valor_atualizado,
            snapshot_hash=self._generate_hash(reference_date, ticker, institution),
            metadata={
                "original_ticker": raw.codigo_negociacao,
                "cnpj_fundo": raw.cnpj_fundo,
                "codigo_isin": raw.codigo_isin,
                "tipo": raw.tipo,
                "motivo": raw.motivo
            }
        )

    def normalize_treasury(self, raw: RawB3TreasuryPosition, reference_date: date) -> PositionSnapshot:
        # No tesouro o "Ticker" geralmente é nome do ativo em 'produto' ou ISIN. 
        # A convenção do projeto é usar Produto ou ISIN como Ticker.
        # Vamos usar o ISIN como chave hard e o Produto nos metadados/formatado.
        
        raw_ticker = raw.produto if raw.produto else raw.codigo_isin
        ticker = self._normalize_ticker(raw_ticker)
        institution = self._normalize_institution(raw.instituicao)
        
        return PositionSnapshot(
            source_system="B3_AREA_INVESTIDOR",
            reference_date=reference_date,
            ticker=ticker,
            asset_type=AssetTypeEnum.TREASURY,
            institution=institution,
            quantity=raw.quantidade,
            unit_price=raw.valor_bruto / raw.quantidade if (raw.valor_bruto and raw.quantidade) else None,
            total_value=raw.valor_atualizado,
            snapshot_hash=self._generate_hash(reference_date, ticker, institution),
            metadata={
                "original_ticker": raw_ticker,
                "codigo_isin": raw.codigo_isin,
                "indexador": raw.indexador,
                "vencimento": raw.vencimento,
                "motivo": raw.motivo
            }
        )

    def _normalize_ticker(self, ticker: Union[str, None]) -> str:
        if not ticker:
            return "UNKNOWN"
        t = ticker.strip().upper()
        # Tratamento do lote fracionário (Ex: PETR4F -> PETR4)
        if len(t) >= 5 and t.endswith("F") and t[-2].isdigit():
            # A heurística de terminar em F após um número (ex TICK3F) é muito segura
            t = t[:-1]
        elif len(t) == 7 and t.endswith("11F"):
            # Para BOVA11F, SMAL11F
            t = t[:-1]
        return t
        
    def _normalize_institution(self, inst: Union[str, None]) -> str:
        if not inst:
            return "UNKNOWN"
        # Pode haver mais complexidade no futuro, mas no momento é caixa alta sem espaço
        return inst.strip().upper()
        
    def _generate_hash(self, ref_date: date, ticker: str, institution: str) -> str:
        # hash(reference_date + ticker + institution)
        raw_str = f"{ref_date.isoformat()}|{ticker}|{institution}"
        return hashlib.md5(raw_str.encode("utf-8")).hexdigest()
