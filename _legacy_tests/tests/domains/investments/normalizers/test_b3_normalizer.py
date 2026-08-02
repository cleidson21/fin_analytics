import pytest
from datetime import date
from decimal import Decimal
from backend.domains.investments.dto import AssetTypeEnum
from backend.domains.investments.parsers.dto import (
    RawB3StockPosition, RawB3FundPosition, RawB3TreasuryPosition
)
from backend.domains.investments.normalizers.b3_normalizer import B3CustodyNormalizer

class TestB3CustodyNormalizer:
    
    @pytest.fixture
    def normalizer(self):
        return B3CustodyNormalizer()
        
    @pytest.fixture
    def ref_date(self):
        return date(2026, 6, 30)

    def test_normalize_stock_fractional(self, normalizer, ref_date):
        raw = RawB3StockPosition(
            codigo_negociacao="PETR4F",
            instituicao="XP INVESTIMENTOS",
            quantidade=Decimal("55"),
            preco_fechamento=Decimal("35.50"),
            valor_atualizado=Decimal("1952.50")
        )
        
        snapshot = normalizer.normalize_stock(raw, ref_date)
        
        assert snapshot.ticker == "PETR4" # Normalizou o "F"
        assert snapshot.institution == "XP INVESTIMENTOS"
        assert snapshot.asset_type == AssetTypeEnum.STOCK
        assert snapshot.quantity == Decimal("55")
        assert snapshot.snapshot_hash is not None
        assert snapshot.metadata["original_ticker"] == "PETR4F"

    def test_normalize_stock_null_values(self, normalizer, ref_date):
        raw = RawB3StockPosition(
            codigo_negociacao="VALE3",
            instituicao=None, # Testar fallback para UNKNOWN
            quantidade=Decimal("100"),
            tipo="BDR" # Deveria reconhecer BDR
        )
        
        snapshot = normalizer.normalize_stock(raw, ref_date)
        
        assert snapshot.ticker == "VALE3"
        assert snapshot.institution == "UNKNOWN"
        assert snapshot.asset_type == AssetTypeEnum.BDR
        assert snapshot.quantity == Decimal("100")
        assert snapshot.unit_price is None

    def test_normalize_fund(self, normalizer, ref_date):
        raw = RawB3FundPosition(
            codigo_negociacao=" HGLG11 ",
            instituicao=" NUBANK ",
            quantidade=Decimal("10"),
            tipo="FII"
        )
        
        snapshot = normalizer.normalize_fund(raw, ref_date)
        
        assert snapshot.ticker == "HGLG11"
        assert snapshot.institution == "NUBANK"
        assert snapshot.asset_type == AssetTypeEnum.FII
        
    def test_normalize_fund_etf(self, normalizer, ref_date):
        raw = RawB3FundPosition(
            codigo_negociacao="IVVB11F",
            instituicao="CLEAR",
            quantidade=Decimal("5"),
            tipo="ETF BRASIL"
        )
        
        snapshot = normalizer.normalize_fund(raw, ref_date)
        
        assert snapshot.ticker == "IVVB11" # Removeu F
        assert snapshot.asset_type == AssetTypeEnum.ETF

    def test_normalize_treasury(self, normalizer, ref_date):
        raw = RawB3TreasuryPosition(
            produto="Tesouro Selic 2027",
            codigo_isin="BRSTNCLF1RM3",
            instituicao="BTG PACTUAL",
            quantidade=Decimal("1.5"),
            valor_bruto=Decimal("15000.00"),
            valor_atualizado=Decimal("15000.00")
        )
        
        snapshot = normalizer.normalize_treasury(raw, ref_date)
        
        assert snapshot.ticker == "TESOURO SELIC 2027"
        assert snapshot.institution == "BTG PACTUAL"
        assert snapshot.asset_type == AssetTypeEnum.TREASURY
        assert snapshot.quantity == Decimal("1.5")
        # Deve ter calculado preço unitário: valor_bruto / quantidade
        assert snapshot.unit_price == Decimal("10000.00")
        
    def test_normalize_treasury_without_product(self, normalizer, ref_date):
        raw = RawB3TreasuryPosition(
            produto=None,
            codigo_isin="BRSTNCLF1RM3",
            instituicao="BTG PACTUAL",
            quantidade=Decimal("1.5")
        )
        
        snapshot = normalizer.normalize_treasury(raw, ref_date)
        
        # Faz fallback para o ISIN se o produto for None
        assert snapshot.ticker == "BRSTNCLF1RM3"
        assert snapshot.metadata["codigo_isin"] == "BRSTNCLF1RM3"

    def test_hash_idempotency(self, normalizer, ref_date):
        raw1 = RawB3StockPosition(
            codigo_negociacao="WEGE3",
            instituicao="XP",
            quantidade=Decimal("100")
        )
        
        snapshot1 = normalizer.normalize_stock(raw1, ref_date)
        snapshot2 = normalizer.normalize_stock(raw1, ref_date)
        
        assert snapshot1.snapshot_hash == snapshot2.snapshot_hash
        assert isinstance(snapshot1.snapshot_hash, str)
        assert len(snapshot1.snapshot_hash) > 10
