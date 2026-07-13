import hashlib
import logging
from typing import List, Optional
from datetime import datetime, date

from backend.domains.investments.parsers.dto import RawB3Movement
from backend.domains.investments.dto import TradeDTO, TradeType
from backend.domains.investments.repositories.broker_alias_resolver import BrokerAliasResolver

logger = logging.getLogger(__name__)

class B3MovementsNormalizerException(Exception):
    pass

class B3MovementsNormalizer:
    def __init__(self, broker_resolver: Optional[BrokerAliasResolver] = None):
        """
        Args:
            broker_resolver: Resolvedor de aliases de corretoras. 
                Se None, instancia o padrão automaticamente.
        """
        self._broker_resolver = broker_resolver or BrokerAliasResolver()
    def _clean_ticker(self, ticker: str) -> str:
        """Remove 'F' suffix from fractional market tickers."""
        ticker = ticker.strip().upper()
        if ticker.endswith('F'):
            return ticker[:-1]
        return ticker

    def _map_operation_type(self, op_type: str) -> TradeType:
        if not op_type:
            raise ValueError("Tipo de movimentação vazio")
        op = op_type.strip().upper()
        if op == "COMPRA":
            return TradeType.BUY
        elif op == "VENDA":
            return TradeType.SELL
        else:
            raise ValueError(f"Tipo de movimentação desconhecido: {op_type}")

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
        except ValueError:
            raise ValueError(f"Formato de data invalido: {date_str}. Esperado DD/MM/YYYY")

    def _generate_hash(self, trade_date: date, canonical_broker: str, ticker: str,
                       operation_type: TradeType, quantity, unit_price) -> str:
        """
        Gera o MD5 de idempotência usando o broker CANÔNICO (normalizado).
        Garante que o mesmo trade real, mesmo com grafias diferentes da corretora,
        sempre produza o mesmo hash e nunca gere duplicatas financeiras.

        Campos: trade_date | canonical_broker | ticker | operation_type | quantity | unit_price
        """
        base_str = f"{trade_date.isoformat()}|{canonical_broker}|{ticker}|{operation_type.value}|{quantity}|{unit_price}"
        return hashlib.md5(base_str.encode('utf-8')).hexdigest()

    def normalize(self, raw_events: List[RawB3Movement]) -> List[TradeDTO]:
        normalized_trades: List[TradeDTO] = []
        logger.info(f"Normalizando {len(raw_events)} eventos transacionais B3.")
        
        for raw in raw_events:
            trade_date = self._parse_date(raw.data_do_negocio)
            expiration_date = self._parse_date(raw.prazo_vencimento)
            op_type = self._map_operation_type(raw.tipo_de_movimentacao)
            ticker = self._clean_ticker(raw.codigo_de_negociacao)
            
            # Resolve o broker para o nome canônico ANTES de gerar o hash.
            # O campo TradeDTO.broker mantém o nome original (cru) para rastreabilidade.
            canonical_broker = self._broker_resolver.resolve(raw.instituicao)
            
            idempotency_hash = self._generate_hash(
                trade_date=trade_date,
                canonical_broker=canonical_broker,
                ticker=ticker,
                operation_type=op_type,
                quantity=raw.quantidade,
                unit_price=raw.preco
            )
            
            trade = TradeDTO(
                ticker=ticker,
                broker=raw.instituicao,
                operation_type=op_type,
                market_type=raw.mercado,
                expiration_date=expiration_date,
                trade_date=trade_date,
                quantity=raw.quantidade,
                unit_price=raw.preco,
                total_value=raw.valor,
                source="B3_API",
                idempotency_hash=idempotency_hash
            )
            normalized_trades.append(trade)
            
        logger.info(f"Normalizacao concluida. {len(normalized_trades)} DTOs gerados.")
        return normalized_trades
