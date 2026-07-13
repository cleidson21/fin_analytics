import logging
import json
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.domains.investments.dto import PositionSnapshot, AssetTypeEnum
from backend.domains.investments.repositories.broker_alias_resolver import BrokerAliasResolver
from datetime import date, datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

class SnapshotRepository:
    """
    Repositório responsável pela persistência atômica e lookups (asset/account) 
    das instâncias canônicas de custódia (PositionSnapshot) na tabela position_snapshots.
    """
    
    def __init__(self, broker_resolver: Optional[BrokerAliasResolver] = None):
        """Inicializa o repositório, configurando cache interno para minimizar lookups."""
        self._asset_cache: Dict[str, str] = {}
        self._account_cache: Dict[str, str] = {}
        self._broker_resolver = broker_resolver or BrokerAliasResolver()
        
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
            broker (str): Nome da corretora enviado pela fonte de dados.
            
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
        
    def save(self, session: Session, snapshot: PositionSnapshot) -> None:
        """
        Insere ou atualiza (Upsert) um único snapshot no banco de dados.
        
        Args:
            session (Session): Sessão ativa do SQLAlchemy.
            snapshot (PositionSnapshot): Objeto da posição.
        """
        asset_id = self._resolve_asset_id(session, snapshot.ticker)
        account_id = self._resolve_account_id(session, snapshot.institution)
        
        query = text("""
            INSERT INTO position_snapshots (
                id, account_id, asset_id, reference_date, quantity, 
                unit_price, total_value, source_system, metadata
            ) VALUES (
                :id, :account_id, :asset_id, :reference_date, :quantity, 
                :unit_price, :total_value, :source_system, :metadata
            ) ON CONFLICT(id) DO UPDATE SET
                account_id=excluded.account_id,
                asset_id=excluded.asset_id,
                reference_date=excluded.reference_date,
                quantity=excluded.quantity,
                unit_price=excluded.unit_price,
                total_value=excluded.total_value,
                source_system=excluded.source_system,
                metadata=excluded.metadata
        """)
        
        unit_price = int(round(float(snapshot.unit_price) * 100)) if snapshot.unit_price is not None else None
        total_value = int(round(float(snapshot.total_value) * 100)) if snapshot.total_value is not None else None
        metadata_json = json.dumps(snapshot.metadata) if snapshot.metadata else None

        params = {
            "id": snapshot.snapshot_hash,
            "account_id": account_id,
            "asset_id": asset_id,
            "reference_date": snapshot.reference_date.isoformat(),
            "quantity": float(snapshot.quantity),
            "unit_price": unit_price,
            "total_value": total_value,
            "source_system": snapshot.source_system,
            "metadata": metadata_json
        }
        
        session.execute(query, params)

    def save_many(self, session: Session, snapshots: List[PositionSnapshot]) -> int:
        """
        Realiza o upsert massivo de snapshots.
        
        Args:
            session (Session): Sessão ativa do SQLAlchemy.
            snapshots (List[PositionSnapshot]): Lista com os DTOs processados.
            
        Returns:
            int: Quantidade de registros afetados.
        """
        count = 0
        for snapshot in snapshots:
            self.save(session, snapshot)
            count += 1
        return count

    def _row_to_dto(self, row) -> PositionSnapshot:
        created_at = row.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
        unit_price = Decimal(str(row.unit_price)) / Decimal(100) if row.unit_price is not None else None
        total_value = Decimal(str(row.total_value)) / Decimal(100) if row.total_value is not None else None
        
        return PositionSnapshot(
            snapshot_hash=row.id,
            source_system=row.source_system,
            reference_date=date.fromisoformat(row.reference_date) if isinstance(row.reference_date, str) else row.reference_date,
            ticker=row.ticker,
            asset_type=AssetTypeEnum(row.asset_class),
            institution=row.broker,
            quantity=Decimal(str(row.quantity)),
            unit_price=unit_price,
            total_value=total_value,
            metadata=json.loads(row.metadata) if row.metadata else {},
            created_at=created_at
        )

    def list_all(self, session: Session) -> List[PositionSnapshot]:
        query = text("""
            SELECT p.id, p.reference_date, p.quantity, p.unit_price, p.total_value, 
                   p.source_system, p.metadata, p.created_at, a.ticker, a.asset_class, c.name as broker
            FROM position_snapshots p
            JOIN assets a ON p.asset_id = a.id
            JOIN accounts c ON p.account_id = c.id
            ORDER BY p.reference_date ASC
        """)
        results = session.execute(query).fetchall()
        return [self._row_to_dto(row) for row in results]

    def latest_by_asset(self, session: Session, ticker: str) -> List[PositionSnapshot]:
        query = text("""
            SELECT p.id, p.reference_date, p.quantity, p.unit_price, p.total_value, 
                   p.source_system, p.metadata, p.created_at, a.ticker, a.asset_class, c.name as broker
            FROM position_snapshots p
            JOIN assets a ON p.asset_id = a.id
            JOIN accounts c ON p.account_id = c.id
            WHERE a.ticker = :ticker
            AND p.reference_date = (
                SELECT MAX(reference_date) 
                FROM position_snapshots p2 
                WHERE p2.asset_id = a.id
            )
        """)
        results = session.execute(query, {"ticker": ticker}).fetchall()
        return [self._row_to_dto(row) for row in results]

    def latest_by_account(self, session: Session, account_name: str) -> List[PositionSnapshot]:
        canonical_broker = self._broker_resolver.resolve(account_name)
        query = text("""
            SELECT p.id, p.reference_date, p.quantity, p.unit_price, p.total_value, 
                   p.source_system, p.metadata, p.created_at, a.ticker, a.asset_class, c.name as broker
            FROM position_snapshots p
            JOIN assets a ON p.asset_id = a.id
            JOIN accounts c ON p.account_id = c.id
            WHERE c.name LIKE :broker
            AND p.reference_date = (
                SELECT MAX(reference_date) 
                FROM position_snapshots p3 
                WHERE p3.account_id = c.id
            )
        """)
        results = session.execute(query, {"broker": f"%{canonical_broker}%"}).fetchall()
        return [self._row_to_dto(row) for row in results]
