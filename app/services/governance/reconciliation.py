from sqlalchemy.orm import Session
from app.models.governance import RawEvent, EventLink
from datetime import timedelta
from typing import List, Optional
import uuid

class ReconciliationService:
    def __init__(self, db: Session):
        self.db = db

    def find_matches(self, target_event: RawEvent) -> List[RawEvent]:
        """
        Encontra candidatos a match na base de RawEvents.
        Regra:
        - Mesmo valor absoluto (amount_cents)
        - Data exata (Match Perfeito) ou ±3 dias (Fuzzy Match)
        - Tipos diferentes ou complementares (ex: PIERRE despesa vs BANCO débito) -> Para simplificar, focamos no valor absoluto e data, ignorando o próprio evento.
        - Status = 'NEW' ou não processado
        """
        amount = abs(target_event.amount_cents) if target_event.amount_cents else 0
        date_min = target_event.event_date - timedelta(days=3) if target_event.event_date else None
        date_max = target_event.event_date + timedelta(days=3) if target_event.event_date else None

        query = self.db.query(RawEvent).filter(
            RawEvent.id != target_event.id,
            RawEvent.match_status == 'NEW'
        )

        if amount > 0:
            query = query.filter(
                # Tolerância financeira: mesmo valor absoluto
                RawEvent.amount_cents.in_([amount, -amount])
            )
            
        if date_min and date_max:
            query = query.filter(
                RawEvent.event_date >= date_min,
                RawEvent.event_date <= date_max
            )
            
        return query.all()

    def create_link(self, event_a: RawEvent, event_b: RawEvent, confirmed_by: Optional[str] = None) -> EventLink:
        """Cria um EventLink (ligação entre eventos relacionados)."""
        # Verifica tipo de match
        delta_days = abs((event_a.event_date - event_b.event_date).days) if event_a.event_date and event_b.event_date else 0
        match_method = "EXACT" if delta_days == 0 else "FUZZY"
        confidence = 1.0 if match_method == "EXACT" else 0.8
        
        status = 'CONFIRMED' if confirmed_by else 'AUTO_CONFIRMED'
        
        link = EventLink(
            id=str(uuid.uuid4()),
            event_id_a=event_a.id,
            event_id_b=event_b.id,
            link_type="RECONCILIATION",
            confidence=confidence,
            match_method=match_method,
            status=status,
            confirmed_by=confirmed_by
        )
        self.db.add(link)
        
        # Atualiza status dos eventos
        event_a.match_status = 'MATCHED'
        event_b.match_status = 'MATCHED'
        
        self.db.commit()
        self.db.refresh(link)
        return link
