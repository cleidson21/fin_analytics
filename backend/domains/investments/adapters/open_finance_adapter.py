from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import hashlib

from backend.domains.investments.dto import (
    PositionSnapshot,
    TradeDTO,
    AssetTypeEnum,
    TradeType
)

class OpenFinanceAdapter:
    """
    Camada pura (Pure Layer) responsável por atuar como Anti-Corruption Layer (ACL).
    Traduz os payloads JSON brutos recebidos das APIs de Open Finance (B3, Bancos, etc)
    diretamente para os DTOs canônicos do sistema (PositionSnapshot e TradeDTO).
    
    Esta classe NÃO possui conhecimento sobre banco de dados, repositórios ou ORMs.
    """

    def parse_positions(self, payload: List[Dict[str, Any]]) -> List[PositionSnapshot]:
        """
        Recebe uma lista de dicionários representando posições de custódia
        do Open Finance e converte em uma lista de PositionSnapshot.
        """
        self._validate_payload_is_list(payload)
        
        snapshots = []
        for item in payload:
            self._validate_required_keys(item, ["reference_date", "ticker", "institution", "quantity"])
            
            ref_date = self._parse_date(item["reference_date"])
            ticker = self._normalize_ticker(item["ticker"])
            inst = self._normalize_institution(item["institution"])
            qty = self._parse_quantity(item["quantity"])
            
            unit_price = self._parse_money(item.get("unit_price"))
            total_value = self._parse_money(item.get("total_value"))
            asset_type = self._parse_asset_type(item.get("asset_type"))
            
            metadata = item.get("metadata", {})
            if not isinstance(metadata, dict):
                raise ValueError(f"Metadata must be a dictionary, got: {type(metadata)}")

            snapshot_hash = self._generate_position_hash(ref_date, ticker, inst)
            
            snapshot = PositionSnapshot(
                source_system="OPEN_FINANCE",
                reference_date=ref_date,
                ticker=ticker,
                asset_type=asset_type,
                institution=inst,
                quantity=qty,
                unit_price=unit_price,
                total_value=total_value,
                snapshot_hash=snapshot_hash,
                metadata=metadata
            )
            snapshots.append(snapshot)
            
        return snapshots

    def parse_trades(self, payload: List[Dict[str, Any]]) -> List[TradeDTO]:
        """
        Recebe uma lista de dicionários representando movimentações/operações
        do Open Finance e converte em uma lista de TradeDTO.
        """
        self._validate_payload_is_list(payload)
        
        trades = []
        for item in payload:
            self._validate_required_keys(item, ["trade_date", "ticker", "broker", "operation_type", "quantity", "unit_price", "total_value"])
            
            t_date = self._parse_date(item["trade_date"])
            ticker = self._normalize_ticker(item["ticker"])
            broker = self._normalize_institution(item["broker"])
            op_type = self._parse_trade_type(item["operation_type"])
            qty = self._parse_quantity(item["quantity"])
            unit_price = self._parse_money(item["unit_price"])
            total_value = self._parse_money(item["total_value"])
            
            # total_value must be provided by the payload in TradeDTO for exact financial matching,
            # but unit_price might also be required.
            if unit_price is None or total_value is None:
                raise ValueError("Trades require strictly non-null unit_price and total_value")
                
            metadata = item.get("metadata", {})
            if not isinstance(metadata, dict):
                raise ValueError(f"Metadata must be a dictionary, got: {type(metadata)}")
                
            exp_date_raw = item.get("expiration_date")
            exp_date = self._parse_date(exp_date_raw) if exp_date_raw else None
            
            market_type = str(item.get("market_type", "")).strip() or None

            idempotency_hash = self._generate_trade_hash(t_date, broker, ticker, op_type, qty, unit_price)
            
            trade = TradeDTO(
                ticker=ticker,
                broker=broker,
                operation_type=op_type,
                market_type=market_type,
                expiration_date=exp_date,
                trade_date=t_date,
                quantity=qty,
                unit_price=unit_price,
                total_value=total_value,
                source="OPEN_FINANCE",
                idempotency_hash=idempotency_hash,
                metadata=metadata
            )
            trades.append(trade)
            
        return trades

    # --- PRIVATE METHODS ---

    def _validate_payload_is_list(self, payload: Any) -> None:
        if not isinstance(payload, list):
            raise ValueError(f"Expected payload to be a list, got {type(payload)}")
            
    def _validate_required_keys(self, item: Dict[str, Any], keys: List[str]) -> None:
        if not isinstance(item, dict):
            raise ValueError(f"Expected item to be a dictionary, got {type(item)}")
        for key in keys:
            if key not in item:
                raise ValueError(f"Missing required key in payload: {key}")

    def _parse_date(self, date_val: Any) -> date:
        if isinstance(date_val, date):
            return date_val
        if isinstance(date_val, str):
            try:
                # ISO Format expected: YYYY-MM-DD
                return datetime.strptime(date_val.strip()[:10], "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid date format: {date_val}. Expected YYYY-MM-DD.")
        raise ValueError(f"Invalid date type: {type(date_val)}")

    def _parse_money(self, money_val: Any) -> Optional[Decimal]:
        if money_val is None:
            return None
        try:
            val = Decimal(str(money_val))
            if val < 0:
                raise ValueError(f"Monetary value cannot be negative: {val}")
            return val
        except InvalidOperation:
            raise ValueError(f"Invalid monetary value: {money_val}")

    def _parse_quantity(self, qty_val: Any) -> Decimal:
        if qty_val is None:
            raise ValueError("Quantity cannot be None")
        try:
            val = Decimal(str(qty_val))
            if val <= 0:
                raise ValueError(f"Quantity must be strictly positive: {val}")
            return val
        except InvalidOperation:
            raise ValueError(f"Invalid quantity value: {qty_val}")

    def _normalize_ticker(self, ticker_val: Any) -> str:
        if not ticker_val or not isinstance(ticker_val, str):
            raise ValueError(f"Invalid ticker: {ticker_val}")
        normalized = ticker_val.strip().upper()
        if not normalized:
            raise ValueError("Ticker cannot be empty")
        return normalized

    def _normalize_institution(self, inst_val: Any) -> str:
        if not inst_val or not isinstance(inst_val, str):
            raise ValueError(f"Invalid institution/broker: {inst_val}")
        normalized = inst_val.strip()
        if not normalized:
            raise ValueError("Institution/Broker cannot be empty")
        return normalized

    def _parse_asset_type(self, type_val: Any) -> AssetTypeEnum:
        if not type_val:
            return AssetTypeEnum.UNKNOWN
        type_str = str(type_val).strip().upper()
        try:
            return AssetTypeEnum(type_str)
        except ValueError:
            return AssetTypeEnum.UNKNOWN

    def _parse_trade_type(self, op_val: Any) -> TradeType:
        if not op_val:
            raise ValueError("Operation type cannot be empty")
        op_str = str(op_val).strip().upper()
        if op_str in ("BUY", "COMPRA", "C"):
            return TradeType.BUY
        if op_str in ("SELL", "VENDA", "V"):
            return TradeType.SELL
        raise ValueError(f"Unknown operation type: {op_val}")

    def _generate_position_hash(self, ref_date: date, ticker: str, institution: str) -> str:
        raw_str = f"{ref_date.isoformat()}|{ticker}|{institution}"
        return hashlib.md5(raw_str.encode('utf-8')).hexdigest()

    def _generate_trade_hash(self, t_date: date, broker: str, ticker: str, op_type: TradeType, qty: Decimal, price: Decimal) -> str:
        raw_str = f"{t_date.isoformat()}|{broker}|{ticker}|{op_type.value}|{qty}|{price}"
        return hashlib.md5(raw_str.encode('utf-8')).hexdigest()
