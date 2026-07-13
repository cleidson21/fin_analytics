import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, datetime
from backend.domains.investments.dto import TradeDTO, TradeType
from backend.domains.investments.repositories.broker_alias_resolver import BrokerAliasResolver
from decimal import Decimal

logger = logging.getLogger(__name__)

class TradeRepository:
    """
    Repositório responsável pela persistência atômica e lookups (asset/account) 
    das instâncias canônicas de transações (TradeDTO) na tabela genérica de trades.
    """
    
    def __init__(self):
        """Inicializa o repositório, configurando cache interno para minimizar lookups."""
        self._asset_cache: Dict[str, str] = {}
        self._account_cache: Dict[str, str] = {}
        self._broker_resolver = BrokerAliasResolver()
        
    def _resolve_asset_id(self, session: Session, ticker: str) -> str:
        """
        Busca o ID interno (UUID) do ativo baseado no Ticker fornecido.
        
        Args:
            session (Session): Sessão ativa do SQLAlchemy.
            ticker (str): Ticker canônico da transação.
            
        Returns:
            str: O ID do ativo na tabela assets.
        """
        if ticker in self._asset_cache:
            return self._asset_cache[ticker]
            
        query = text("SELECT id FROM assets WHERE ticker = :ticker")
        result = session.execute(query, {"ticker": ticker}).fetchone()
        
        if not result:
            raise ValueError(f"Asset not found for ticker: {ticker}")
            
        asset_id = result[0]
        self._asset_cache[ticker] = asset_id
        return asset_id
        
    def _resolve_account_id(self, session: Session, broker: str) -> str:
        """
        Busca o ID interno (UUID) da conta baseado no nome da corretora.
        
        Args:
            session (Session): Sessão ativa do SQLAlchemy.
            broker (str): Nome da corretora enviado pela B3.
            
        Returns:
            str: O ID da conta na tabela accounts.
        """
        canonical_broker = self._broker_resolver.resolve(broker)
        
        if canonical_broker in self._account_cache:
            return self._account_cache[canonical_broker]
            
        query = text("SELECT id FROM accounts WHERE name LIKE :broker LIMIT 1")
        result = session.execute(query, {"broker": f"%{canonical_broker}%"}).fetchone()
        
        if not result:
            raise ValueError(f"Account (Broker) not found for name: {broker} (Canonical: {canonical_broker})")
            
        account_id = result[0]
        self._account_cache[canonical_broker] = account_id
        return account_id
        
    def save(self, session: Session, trade: TradeDTO) -> None:
        """
        Insere ou atualiza (Upsert) uma única transação no banco de dados.
        
        Args:
            session (Session): Sessão ativa do SQLAlchemy.
            trade (TradeDTO): Objeto financeiro da transação.
        """
        asset_id = self._resolve_asset_id(session, trade.ticker)
        account_id = self._resolve_account_id(session, trade.broker)
        
        query = text("""
            INSERT INTO trades (
                id, asset_id, account_id, type, trade_date, 
                quantity, unit_price, source
            ) VALUES (
                :id, :asset_id, :account_id, :type, :trade_date, 
                :quantity, :unit_price, :source
            ) ON CONFLICT(id) DO UPDATE SET
                asset_id=excluded.asset_id,
                account_id=excluded.account_id,
                type=excluded.type,
                trade_date=excluded.trade_date,
                quantity=excluded.quantity,
                unit_price=excluded.unit_price,
                source=excluded.source
        """)
        
        params = {
            "id": trade.idempotency_hash,
            "asset_id": asset_id,
            "account_id": account_id,
            "type": trade.operation_type.value,
            "trade_date": trade.trade_date.isoformat(),
            "quantity": float(trade.quantity),
            "unit_price": int(round(float(trade.unit_price) * 100)),
            "source": trade.source
        }
        
        session.execute(query, params)

    def save_many(self, session: Session, trades: List[TradeDTO]) -> int:
        """
        Realiza o upsert massivo da coleção de transações CEI.
        
        Args:
            session (Session): Sessão ativa do SQLAlchemy.
            trades (List[TradeDTO]): Lista com os DTOs processados pelo Normalizer.
            
        Returns:
            int: Quantidade de registros afetados.
        """
        count = 0
        for trade in trades:
            self.save(session, trade)
            count += 1
        return count

    def exists_hash(self, session: Session, idempotency_hash: str) -> bool:
        """
        Verifica fisicamente se o hash já foi processado e salvo na tabela.
        
        Args:
            session (Session): Sessão ativa.
            idempotency_hash (str): Hash gerado via MD5.
            
        Returns:
            bool: True se já existir, False se for novo.
        """
        raise NotImplementedError("Implementação lógica a ser definida.")

    def find_by_hash(self, session: Session, idempotency_hash: str) -> Optional[dict]:
        """
        Retorna o dicionário/registro de um Trade filtrado por seu Hash (ID).
        
        Args:
            session (Session): Sessão ativa.
            idempotency_hash (str): Hash/PK da transação.
            
        Returns:
            Optional[dict]: Representação serializada da linha física, se encontrada.
        """
        raise NotImplementedError("Implementação lógica a ser definida.")

    def _row_to_dto(self, row) -> TradeDTO:
        created_at = row.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        return TradeDTO(
            idempotency_hash=row.id,
            operation_type=TradeType(row.type),
            trade_date=date.fromisoformat(row.trade_date) if isinstance(row.trade_date, str) else row.trade_date,
            quantity=Decimal(str(row.quantity)),
            unit_price=Decimal(str(row.unit_price)) / Decimal(100),
            total_value=Decimal(str(row.gross_value)) / Decimal(100),
            source=row.source,
            ticker=row.ticker,
            broker=row.broker,
            metadata={},
            created_at=created_at
        )

    def list_all(self, session: Session) -> List[TradeDTO]:
        query = text("""
            SELECT 
                t.id, t.type, t.trade_date, t.quantity, t.unit_price, t.gross_value, 
                t.source, t.created_at, a.ticker, c.name as broker 
            FROM trades t 
            JOIN assets a ON t.asset_id = a.id 
            JOIN accounts c ON t.account_id = c.id
            ORDER BY t.trade_date ASC
        """)
        results = session.execute(query).fetchall()
        return [self._row_to_dto(row) for row in results]

    def list_by_account(self, session: Session, account_name: str) -> List[TradeDTO]:
        canonical_broker = self._broker_resolver.resolve(account_name)
        query = text("""
            SELECT 
                t.id, t.type, t.trade_date, t.quantity, t.unit_price, t.gross_value, 
                t.source, t.created_at, a.ticker, c.name as broker 
            FROM trades t 
            JOIN assets a ON t.asset_id = a.id 
            JOIN accounts c ON t.account_id = c.id
            WHERE c.name LIKE :broker
            ORDER BY t.trade_date ASC
        """)
        results = session.execute(query, {"broker": f"%{canonical_broker}%"}).fetchall()
        return [self._row_to_dto(row) for row in results]

    def list_by_asset(self, session: Session, ticker: str) -> List[TradeDTO]:
        query = text("""
            SELECT 
                t.id, t.type, t.trade_date, t.quantity, t.unit_price, t.gross_value, 
                t.source, t.created_at, a.ticker, c.name as broker 
            FROM trades t 
            JOIN assets a ON t.asset_id = a.id 
            JOIN accounts c ON t.account_id = c.id
            WHERE a.ticker = :ticker
            ORDER BY t.trade_date ASC
        """)
        results = session.execute(query, {"ticker": ticker}).fetchall()
        return [self._row_to_dto(row) for row in results]
